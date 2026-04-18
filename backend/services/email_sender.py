"""
services/email_sender.py — Minimal SMTP email sender for parent notifications.
Section: System
Dependencies: stdlib (smtplib, ssl, email)

Reads SMTP credentials from environment variables. If any required variable
is missing the helper logs a warning and returns False — callers should treat
email sending as best-effort and never raise on failure.

Required env:
  SMTP_HOST       e.g. "smtp.gmail.com"
  SMTP_USER       e.g. "you@gmail.com"
  SMTP_PASS       e.g. Gmail app password (NOT your account password)

Optional env:
  SMTP_PORT       default 587 (STARTTLS); use 465 for implicit SSL
  SMTP_FROM       defaults to SMTP_USER
  SMTP_USE_SSL    "1" to use SMTP_SSL on port 465
"""

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def _smtp_config() -> dict | None:
    """Return SMTP config dict if all required vars set, else None."""
    host = os.environ.get("SMTP_HOST", "").strip()
    user = os.environ.get("SMTP_USER", "").strip()
    pwd  = os.environ.get("SMTP_PASS", "").strip()
    if not (host and user and pwd):
        return None
    return {
        "host":     host,
        "port":     int(os.environ.get("SMTP_PORT", "587")),
        "user":     user,
        "password": pwd,
        "from":     os.environ.get("SMTP_FROM", "").strip() or user,
        "use_ssl":  os.environ.get("SMTP_USE_SSL", "0").strip() == "1",
    }


def send_email(to: str, subject: str, body: str) -> bool:
    """
    Send a plain-text email. Returns True on success, False otherwise.

    Designed to be called in a background thread; any exception is caught
    and logged so the calling request flow is unaffected.
    """
    if not to or "@" not in to:
        logger.warning("send_email: invalid recipient %r", to)
        return False

    cfg = _smtp_config()
    if cfg is None:
        logger.info("send_email: SMTP env not configured; skipping send to %s", to)
        return False

    msg = EmailMessage()
    msg["From"]    = cfg["from"]
    msg["To"]      = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        if cfg["use_ssl"]:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=ctx, timeout=10) as smtp:
                smtp.login(cfg["user"], cfg["password"])
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as smtp:
                smtp.ehlo()
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
                smtp.login(cfg["user"], cfg["password"])
                smtp.send_message(msg)
    except Exception as exc:
        logger.warning("send_email failed (to=%s): %s", to, exc)
        return False

    logger.info("send_email: sent to %s (subject=%s)", to, subject)
    return True
