"""
scripts/validate_kangaroo_phase1.py — Phase 1 validation for Math Kangaroo.
Section: Math
Run: python3 scripts/validate_kangaroo_phase1.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "backend" / "data" / "math" / "kangaroo"

EXPECTED = {
    "pre_ecolier_practice_01": ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_practice_02": ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_practice_03": ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_practice_04": ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_practice_05": ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_practice_06": ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_practice_07": ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_practice_08": ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_practice_09": ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_practice_10": ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_practice_11": ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_practice_12": ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_practice_13": ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_practice_14": ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_drill_01":    ("pre_ecolier", 24, 96, 0.70),
    "pre_ecolier_drill_02":    ("pre_ecolier", 24, 96, 0.70),
    "ecolier_practice_01":     ("ecolier",     24, 96, 0.40),
    "ecolier_practice_02":     ("ecolier",     24, 96, 0.40),
    "ecolier_practice_03":     ("ecolier",     24, 96, 0.40),
    "ecolier_practice_04":     ("ecolier",     24, 96, 0.40),
    "ecolier_practice_05":     ("ecolier",     24, 96, 0.40),
    "ecolier_practice_06":     ("ecolier",     24, 96, 0.40),
    "ecolier_practice_07":     ("ecolier",     24, 96, 0.40),
    "ecolier_practice_08":     ("ecolier",     24, 96, 0.40),
    "ecolier_practice_09":     ("ecolier",     24, 96, 0.40),
    "ecolier_practice_10":     ("ecolier",     24, 96, 0.40),
    "ecolier_practice_11":     ("ecolier",     24, 96, 0.40),
    "ecolier_drill_01":        ("ecolier",     24, 96, 0.40),
    "ecolier_drill_02":        ("ecolier",     24, 96, 0.40),
    "benjamin_practice_01":    ("benjamin",    30, 120, 0.35),
    "benjamin_practice_02":    ("benjamin",    30, 120, 0.35),
    "benjamin_practice_03":    ("benjamin",    30, 120, 0.35),
    "benjamin_practice_04":    ("benjamin",    30, 120, 0.35),
    "benjamin_practice_05":    ("benjamin",    30, 120, 0.35),
    "benjamin_practice_06":    ("benjamin",    30, 120, 0.35),
    "benjamin_practice_07":    ("benjamin",    30, 120, 0.35),
    "benjamin_practice_08":    ("benjamin",    30, 120, 0.35),
    "benjamin_practice_09":    ("benjamin",    30, 120, 0.35),
    "benjamin_practice_10":    ("benjamin",    30, 120, 0.35),
    "benjamin_practice_11":    ("benjamin",    30, 120, 0.35),
    "benjamin_drill_01":       ("benjamin",    30, 120, 0.35),
    "benjamin_drill_02":       ("benjamin",    30, 120, 0.35),
}


def load_all():
    out = {}
    for sid in EXPECTED:
        p = DIR / f"{sid}.json"
        if not p.exists():
            out[sid] = ("MISSING", None)
            continue
        try:
            out[sid] = ("OK", json.loads(p.read_text("utf-8")))
        except Exception as e:
            out[sid] = (f"PARSE:{e}", None)
    return out


def main() -> int:
    results = []

    loaded = load_all()

    # 1: JSON parse
    json_ok = all(v[0] == "OK" for v in loaded.values())
    results.append(("JSON parse (all 10 files)", json_ok))

    # Per-level structure
    pre_ok = eco_ok = ben_ok = True
    all_questions = []
    all_ids = []
    all_text = []
    total_q = 0
    for sid, (status, data) in loaded.items():
        if status != "OK":
            continue
        level, n_q, max_score, _ = EXPECTED[sid]
        secs = data.get("sections", [])
        counts = [len(s.get("questions", [])) for s in secs]
        total_in_set = sum(counts)
        target_section = 8 if level != "benjamin" else 10
        ok_sections = (len(secs) == 3 and all(c == target_section for c in counts))
        ok_max = data.get("max_score") == max_score
        ok_total = data.get("total_questions") == n_q and total_in_set == n_q
        if level == "pre_ecolier" and not (ok_sections and ok_max and ok_total):
            pre_ok = False
        if level == "ecolier" and not (ok_sections and ok_max and ok_total):
            eco_ok = False
        if level == "benjamin" and not (ok_sections and ok_max and ok_total):
            ben_ok = False

        for sec in secs:
            for q in sec.get("questions", []):
                all_questions.append((sid, q))
                if q.get("id"):
                    all_ids.append(q["id"])
                txt = (q.get("question_text") or "").strip()
                if txt:
                    all_text.append(txt)
                total_q += 1

    results.append(("Pre-Ecolier structure (16 files × 24 = 384)", pre_ok))
    results.append(("Ecolier structure (13 files × 24 = 312)", eco_ok))
    results.append(("Benjamin structure (13 files × 30 = 390)", ben_ok))

    # 5: options 5 keys A-E
    opts_ok = True
    bad_opts = []
    for sid, q in all_questions:
        opt = q.get("options") or {}
        if set(opt.keys()) != {"A", "B", "C", "D", "E"}:
            opts_ok = False
            bad_opts.append((sid, q.get("id")))
    results.append(("Every question has options A-E", opts_ok))

    # 6: answer is A-E
    ans_ok = all(str((q.get("answer") or "")).upper() in {"A","B","C","D","E"} for _, q in all_questions)
    results.append(("Every answer is A-E", ans_ok))

    # 7: unique ids
    dup_ids = [i for i, c in Counter(all_ids).items() if c > 1]
    results.append(("All problem IDs globally unique", not dup_ids))

    # 8: unique question_text
    dup_text = [t for t, c in Counter(all_text).items() if c > 1]
    results.append(("No duplicate question_text across all sets", not dup_text))

    # 9: SVG ratio by level
    svg_ok = True
    svg_report = {}
    for sid, (status, data) in loaded.items():
        if status != "OK":
            continue
        _, _, _, target = EXPECTED[sid]
        qs = [q for s in data.get("sections", []) for q in s.get("questions", [])]
        n_svg = sum(1 for q in qs if q.get("image_svg"))
        ratio = n_svg / len(qs) if qs else 0
        svg_report[sid] = (n_svg, len(qs), ratio, target)
        if ratio < target - 0.001:
            svg_ok = False
    results.append(("SVG ratio per set meets level target", svg_ok))

    # 11: answer letter <=30% per set
    ans_dist_ok = True
    for sid, (status, data) in loaded.items():
        if status != "OK":
            continue
        qs = [q for s in data.get("sections", []) for q in s.get("questions", [])]
        letters = Counter(str(q.get("answer", "")).upper() for q in qs)
        n = len(qs)
        cap = 0.30 * n
        if any(v > cap for v in letters.values()):
            ans_dist_ok = False
    results.append(("No letter >30% correct per set", ans_dist_ok))

    # 12: No banned characters in text (Hangul + French accents)
    BANNED = set("ÀÁÂÄÇÈÉÊËÎÏÔÙÛÜàáâäçèéêëîïôùûü")
    def _has_banned(s: str) -> bool:
        if any(c in BANNED for c in s):
            return True
        # Hangul syllables / Jamo
        return any(
            '\uac00' <= c <= '\ud7af' or '\u1100' <= c <= '\u11ff' for c in s
        )

    ascii_ok = True
    for sid, (status, data) in loaded.items():
        if status != "OK":
            continue
        for field in ("title", "disclaimer", "level_label"):
            if _has_banned(data.get(field, "") or ""):
                ascii_ok = False
        for sec in data.get("sections", []):
            for q in sec.get("questions", []):
                for field in ("question_text", "solution"):
                    if _has_banned(q.get(field, "") or ""):
                        ascii_ok = False
    results.append(("No Korean or French accents in text", ascii_ok))

    # 13: non-empty solution
    sol_ok = all((q.get("solution") or "").strip() for _, q in all_questions)
    results.append(("Every question has non-empty solution", sol_ok))

    # 14: total count 1086 (Phase 1 + 2 + 3 + 4)
    total_ok = total_q == 1086
    results.append((f"Total problem count = 1086 (got {total_q})", total_ok))

    # Print table
    print("=== Math Kangaroo Phase 1 Validation ===\n")
    max_name = max(len(n) for n, _ in results)
    passed = 0
    for name, ok in results:
        pad = "." * (max_name + 4 - len(name))
        label = "PASS" if ok else "FAIL"
        print(f"{name} {pad} {label}")
        if ok:
            passed += 1
    print(f"\nTotal: {passed}/{len(results)} PASS")

    # Extra detail for failures
    if not opts_ok:
        print(f"\n  bad options in: {bad_opts[:5]}")
    if dup_ids:
        print(f"  duplicate IDs: {dup_ids[:10]}")
    if dup_text:
        print(f"  duplicate texts: {len(dup_text)}")
    if not svg_ok:
        print("\n  SVG ratios (actual / target):")
        for sid, (n, total, r, t) in svg_report.items():
            mark = " " if r >= t else "!"
            print(f"  {mark} {sid}: {n}/{total} = {r*100:.1f}% (target {t*100:.0f}%)")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
