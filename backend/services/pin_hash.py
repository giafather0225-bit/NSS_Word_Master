"""
services/pin_hash.py — PIN hashing + transparent legacy-plaintext migration.
Section: System / Security
Dependencies: stdlib only (hashlib, hmac, secrets)
API: called by routers/parent.py, routers/reward_shop.py

Background:
  AppConfig.value for the "pin" key used to store the 4-digit PIN as plain
  text. A `sqlite3 voca.db 'SELECT * FROM app_config'` dump would leak it,
  and any backup or accidental log copy carried the cleartext forward.

Strategy:
  - Store pbkdf2_hmac(sha256) hashes with a per-PIN 16-byte salt.
  - A 4-digit PIN has only 10⁴ possibilities, so a fast hash is pointless —
    the rate limiter in pin_guard.py is the real defense. We still use
    pbkdf2 (120 000 iterations) so a stolen DB dump can't be scanned with
    trivial `sha256(pin)` lookups.
  - Format:  pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
  - On successful verify of a legacy plaintext value, callers should call
    upgrade_stored_pin() so the row is rewritten as a hash. That keeps the
    migration path automatic — no manual step, no downtime.

Never log PIN values or the stored hash; treat both as secrets.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets as _secrets

_ALGO        = "pbkdf2_sha256"
_ITERATIONS  = 120_000
_SALT_BYTES  = 16
_HASH_BYTES  = 32


def is_hashed(value: str) -> bool:
    """Return True if `value` looks like our hash format (vs legacy plaintext)."""
    return isinstance(value, str) and value.startswith(_ALGO + "$")


def hash_pin(pin: str) -> str:
    """Hash a PIN with a fresh random salt. Returns the encoded string."""
    salt = _secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", pin.encode("utf-8"), salt, _ITERATIONS, dklen=_HASH_BYTES
    )
    return f"{_ALGO}${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_pin(candidate: str, stored: str) -> bool:
    """
    Constant-time verify. Accepts both hashed and legacy plaintext `stored`
    values so the migration window can accept existing PINs without forcing
    the user to re-enter one.
    """
    if not stored:
        return False
    if not is_hashed(stored):
        # Legacy plaintext row. Still use compare_digest for timing safety.
        return hmac.compare_digest(candidate or "", stored)
    try:
        algo, iters_s, salt_hex, hash_hex = stored.split("$", 3)
        if algo != _ALGO:
            return False
        iters = int(iters_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, TypeError):
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", (candidate or "").encode("utf-8"), salt, iters, dklen=len(expected)
    )
    return hmac.compare_digest(digest, expected)


def needs_upgrade(stored: str) -> bool:
    """True if a verified PIN is still stored as plaintext and should be rewritten."""
    return bool(stored) and not is_hashed(stored)
