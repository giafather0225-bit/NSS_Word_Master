"""
Stage 7 Pilot Learner Data Analysis Script.
==============================================================================
Extract pilot period data from math_attempts table and calculate 5 key metrics.

Usage:
    python3 scripts/stage7_pilot_analyze.py \\
        --start 2026-06-13 --end 2026-06-19 \\
        --grade G3 --output docs/pilot_2026_06_results.md

Output (markdown):
1. Accuracy distribution (by unit/lesson/stage)
2. Misconception match rate
3. Learning effect (PT vs R3)
4. Time distribution (mean/p50/p95)
5. Outlier list (accuracy <20% or >95%)
"""

import argparse
import json
import pathlib
import sqlite3
import statistics
import sys
from collections import defaultdict
from datetime import datetime


ROOT = pathlib.Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "app.db"  # Actual path should be adjusted per environment
DATA_ROOT = ROOT / "backend" / "data" / "math"


def load_attempts(db_path, start, end, grade):
    """Extract pilot period attempts from math_attempts table."""
    if not db_path.exists():
        print(f"⚠️  DB 미존재: {db_path}", file=sys.stderr)
        return []
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("""
        SELECT problem_id, grade, unit, lesson, stage,
               is_correct, user_answer, error_type, time_spent_sec, attempted_at
        FROM math_attempts
        WHERE grade = ? AND attempted_at >= ? AND attempted_at <= ?
        ORDER BY attempted_at
    """, (grade, start, end))
    cols = ["problem_id", "grade", "unit", "lesson", "stage",
            "is_correct", "user_answer", "error_type", "time_spent_sec", "attempted_at"]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return rows


def load_problem_meta(grade):
    """레슨 JSON에서 expected_errors 메타 추출."""
    meta = {}  # problem_id → {expected_errors, lesson, unit}
    grade_dir = DATA_ROOT / grade
    if not grade_dir.exists():
        return meta
    for unit_dir in sorted(grade_dir.iterdir()):
        if not unit_dir.is_dir() or not unit_dir.name.startswith("U"):
            continue
        for lesson_file in sorted(unit_dir.glob("*.json")):
            try:
                d = json.loads(lesson_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            for section in ["pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3"]:
                for item in d.get(section, []):
                    pid = item.get("id", "")
                    if not pid:
                        continue
                    meta[f"{grade}/{unit_dir.name}/{lesson_file.stem}#{pid}"] = {
                        "unit": unit_dir.name,
                        "lesson": lesson_file.stem,
                        "section": section,
                        "expected_errors": item.get("expected_errors", []),
                    }
            # unit_test도 포함
            for p in d.get("problems", []) + d.get("questions", []):
                pid = p.get("id", "")
                if not pid:
                    continue
                meta[f"{grade}/{unit_dir.name}/unit_test#{pid}"] = {
                    "unit": unit_dir.name,
                    "lesson": "unit_test",
                    "section": "unit_test",
                    "expected_errors": p.get("expected_errors", []),
                }
    return meta


def accuracy_distribution(attempts):
    """문항별 정답률 산출."""
    counts = defaultdict(lambda: {"correct": 0, "total": 0})
    for a in attempts:
        key = a["problem_id"]
        counts[key]["total"] += 1
        if a["is_correct"]:
            counts[key]["correct"] += 1
    result = {}
    for k, c in counts.items():
        if c["total"] >= 3:  # 최소 3회 이상 시도된 문항만
            result[k] = c["correct"] / c["total"]
    return result


def misconception_match_rate(attempts, meta):
    """오답의 error_type이 expected_errors와 매칭되는 비율."""
    wrong = [a for a in attempts if not a["is_correct"]]
    matched = 0
    has_expected = 0
    for a in wrong:
        m = meta.get(a["problem_id"])
        if not m:
            continue
        expected = m.get("expected_errors", [])
        if not expected:
            continue
        has_expected += 1
        if isinstance(expected, list) and a.get("error_type") in expected:
            matched += 1
        elif isinstance(expected, dict):
            # U11-U13: expected_errors가 dict 형태 (key=선택지)
            if a.get("user_answer") in expected:
                matched += 1
    rate = matched / has_expected if has_expected else 0.0
    return rate, matched, has_expected


def learning_effect(attempts):
    """레슨별 PT 평균 vs R3 평균 차이."""
    by_lesson = defaultdict(lambda: {"pt": [], "r3": []})
    for a in attempts:
        key = f"{a['grade']}/{a['unit']}/{a['lesson']}"
        stage = (a.get("stage") or "").lower()
        if "pt" in stage or "pretest" in stage:
            by_lesson[key]["pt"].append(1 if a["is_correct"] else 0)
        elif "r3" in stage or "practice_r3" in stage:
            by_lesson[key]["r3"].append(1 if a["is_correct"] else 0)
    effects = {}
    for k, v in by_lesson.items():
        if len(v["pt"]) >= 3 and len(v["r3"]) >= 3:
            pt_avg = statistics.mean(v["pt"])
            r3_avg = statistics.mean(v["r3"])
            effects[k] = (pt_avg, r3_avg, r3_avg - pt_avg)
    return effects


def time_distribution(attempts):
    """단계별 시간 분포 (평균/p50/p95)."""
    by_stage = defaultdict(list)
    for a in attempts:
        t = a.get("time_spent_sec", 0)
        if t and t > 0 and t < 600:  # 0 또는 비정상치 제외
            by_stage[a.get("stage", "?")].append(t)
    result = {}
    for s, ts in by_stage.items():
        if len(ts) < 3:
            continue
        ts_sorted = sorted(ts)
        result[s] = {
            "n": len(ts),
            "mean": statistics.mean(ts),
            "p50": ts_sorted[len(ts) // 2],
            "p95": ts_sorted[int(len(ts) * 0.95)],
        }
    return result


def outliers(acc_dist, low=0.20, high=0.95):
    """이상치 문항 (정답률 <20% 또는 >95%)."""
    lows = [(k, v) for k, v in acc_dist.items() if v < low]
    highs = [(k, v) for k, v in acc_dist.items() if v > high]
    return sorted(lows, key=lambda x: x[1]), sorted(highs, key=lambda x: -x[1])


def write_report(attempts, meta, output_path):
    """모든 지표 산출 후 마크다운 리포트 작성."""
    acc = accuracy_distribution(attempts)
    mc_rate, mc_matched, mc_total = misconception_match_rate(attempts, meta)
    effects = learning_effect(attempts)
    times = time_distribution(attempts)
    lows, highs = outliers(acc)

    avg_acc = statistics.mean(acc.values()) if acc else 0
    avg_effect = statistics.mean([e[2] for e in effects.values()]) if effects else 0

    lines = []
    lines.append(f"# Stage 7 파일럿 결과 — {datetime.now():%Y-%m-%d %H:%M}\n")
    lines.append(f"총 시도: **{len(attempts):,}**\n")
    lines.append(f"분석 대상 문항: **{len(acc)}** (3회 이상 시도)\n")
    lines.append("")
    lines.append("## 1. 정답률 분포\n")
    lines.append(f"- 평균 정답률: **{avg_acc:.1%}**")
    lines.append(f"- 이상치 (낮음 <20%): **{len(lows)}** 문항")
    lines.append(f"- 이상치 (높음 >95%): **{len(highs)}** 문항")
    lines.append("")
    lines.append("## 2. Misconception 매칭률\n")
    lines.append(f"- 매칭: {mc_matched} / {mc_total} = **{mc_rate:.1%}**")
    lines.append(f"- 목표: ≥ 60% → {'✅ 통과' if mc_rate >= 0.6 else '❌ 미달'}")
    lines.append("")
    lines.append("## 3. 학습 효과 (PT → R3)\n")
    lines.append(f"- 분석 레슨: {len(effects)}")
    lines.append(f"- 평균 향상: **+{avg_effect:.1%}pt**")
    lines.append(f"- 목표: ≥ +20%pt → {'✅ 통과' if avg_effect >= 0.20 else '❌ 미달'}")
    lines.append("")
    lines.append("## 4. 시간 분포 (단계별, 초)\n")
    lines.append("| Stage | n | mean | p50 | p95 |")
    lines.append("|---|---|---|---|---|")
    for s, t in sorted(times.items()):
        lines.append(f"| {s} | {t['n']} | {t['mean']:.1f} | {t['p50']} | {t['p95']} |")
    lines.append("")
    lines.append("## 5. 이상치 — 재검토 필요\n")
    lines.append(f"### 정답률 <20% ({len(lows)}건)")
    for pid, rate in lows[:20]:
        lines.append(f"- `{pid}` — {rate:.1%}")
    lines.append("")
    lines.append(f"### 정답률 >95% ({len(highs)}건)")
    for pid, rate in highs[:20]:
        lines.append(f"- `{pid}` — {rate:.1%}")
    lines.append("")
    lines.append("## 합격 기준 체크리스트\n")
    in_range = sum(1 for r in acc.values() if 0.20 <= r <= 0.95)
    in_range_pct = in_range / len(acc) if acc else 0
    lines.append(f"- [{'x' if in_range_pct >= 0.80 else ' '}] 80%+ 정상 범위: {in_range_pct:.1%}")
    lines.append(f"- [{'x' if mc_rate >= 0.60 else ' '}] Misconception 매칭 60%+: {mc_rate:.1%}")
    lines.append(f"- [{'x' if avg_effect >= 0.20 else ' '}] 학습 효과 +20%pt+: +{avg_effect:.1%}pt")

    pathlib.Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ 리포트: {output_path}")
    print(f"   총 시도: {len(attempts)}")
    print(f"   정답률 평균: {avg_acc:.1%}")
    print(f"   매칭률: {mc_rate:.1%}")
    print(f"   학습효과: +{avg_effect:.1%}pt")


def main():
    parser = argparse.ArgumentParser(description="Stage 7 파일럿 분석")
    parser.add_argument("--start", required=True, help="시작일 (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="종료일 (YYYY-MM-DD)")
    parser.add_argument("--grade", default="G3", help="학년 (G3)")
    parser.add_argument("--db", default=str(DB_PATH), help="SQLite DB 경로")
    parser.add_argument("--output", default="docs/pilot_results.md", help="출력 경로")
    args = parser.parse_args()

    attempts = load_attempts(pathlib.Path(args.db), args.start, args.end, args.grade)
    if not attempts:
        print("⚠️  시도 데이터 없음 — 분석 종료.")
        return

    meta = load_problem_meta(args.grade)
    write_report(attempts, meta, args.output)


if __name__ == "__main__":
    main()
