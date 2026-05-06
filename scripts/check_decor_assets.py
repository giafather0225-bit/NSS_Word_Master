#!/usr/bin/env python3
"""
scripts/check_decor_assets.py — Verify Island decoration PNG coverage.
Section: Island

Reads the canonical (zone, slug) list from migration 023 and reports which
PNGs exist in `frontend/static/img/island/decor/` and which are still
missing. Designed so Gia (or another AI) can drop generated PNGs in batches
and re-run this to track progress.

Usage:
    python3 scripts/check_decor_assets.py            # human-readable report
    python3 scripts/check_decor_assets.py --missing  # only list missing slugs
    python3 scripts/check_decor_assets.py --json     # machine-readable

Exit code: 0 when all 46 PNGs are present, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DECOR_DIR = REPO_ROOT / "frontend" / "static" / "img" / "island" / "decor"
MIGRATION_PATH = REPO_ROOT / "backend" / "migrations" / "023_island_decor_image_paths.py"


def load_canonical_list() -> list[tuple[int, str, str]]:
    """Import migration 023 and return its `_DECOR_PATHS` tuple list."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_mig023", MIGRATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {MIGRATION_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module._DECOR_PATHS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--missing", action="store_true", help="Only print missing filenames.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    if not DECOR_DIR.exists():
        print(f"[error] decor folder missing: {DECOR_DIR}", file=sys.stderr)
        return 1

    items = load_canonical_list()
    by_zone: dict[str, dict[str, list[str]]] = {}
    present_total = 0
    missing_total = 0

    for _id, zone, slug in items:
        filename = f"{zone}_{slug}.png"
        exists = (DECOR_DIR / filename).is_file()
        bucket = by_zone.setdefault(zone, {"present": [], "missing": []})
        if exists:
            bucket["present"].append(filename)
            present_total += 1
        else:
            bucket["missing"].append(filename)
            missing_total += 1

    if args.json:
        print(json.dumps({
            "decor_dir": str(DECOR_DIR.relative_to(REPO_ROOT)),
            "total": len(items),
            "present": present_total,
            "missing": missing_total,
            "by_zone": by_zone,
        }, indent=2))
        return 0 if missing_total == 0 else 1

    if args.missing:
        for zone, bucket in by_zone.items():
            for fn in bucket["missing"]:
                print(fn)
        return 0 if missing_total == 0 else 1

    # Human-readable report
    total = len(items)
    print(f"Island decoration assets — {present_total}/{total} present "
          f"({missing_total} missing)")
    print(f"Folder: {DECOR_DIR.relative_to(REPO_ROOT)}\n")

    for zone in ("forest", "ocean", "savanna", "space", "legend"):
        bucket = by_zone.get(zone)
        if not bucket:
            continue
        p = len(bucket["present"])
        m = len(bucket["missing"])
        status = "OK" if m == 0 else f"{m} missing"
        print(f"  [{zone:<7}] {p}/{p + m}  {status}")
        for fn in bucket["missing"]:
            print(f"      - {fn}")

    print()
    if missing_total == 0:
        print("All decoration PNGs are in place.")
        return 0
    print(f"Next step: generate {missing_total} PNG(s) and drop them in {DECOR_DIR.name}/.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
