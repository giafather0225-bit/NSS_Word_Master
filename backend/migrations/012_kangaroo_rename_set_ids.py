"""
012_kangaroo_rename_set_ids.py
================================
MathKangarooProgress.set_id 마이그레이션
  usa_YYYY_gr34 → usa_YYYY_ecolier
  usa_YYYY_gr56 → usa_YYYY_benjamin
  usa_YYYY_gr78 → usa_YYYY_cadet

배경: 파일 명칭 통일 (grXX 표기 → 레벨명 표기)
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "NSS_Learning" / "database" / "voca.db"

RENAMES = {
    "gr34": "ecolier",
    "gr56": "benjamin",
    "gr78": "cadet",
}


def run(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # MathKangarooProgress 테이블 존재 확인
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='mathkangarooprogress'"
    )
    if not cur.fetchone():
        print("  ⏭  mathkangarooprogress table not found — skipping")
        conn.close()
        return

    total = 0
    for grade, level in RENAMES.items():
        # usa_YYYY_grXX 패턴 찾기
        cur.execute(
            "SELECT set_id FROM mathkangarooprogress WHERE set_id LIKE ?",
            (f"usa_%_{grade}",),
        )
        rows = cur.fetchall()
        for (old_set_id,) in rows:
            parts = old_set_id.rsplit("_", 1)  # ['usa_YYYY', 'gr34']
            new_set_id = f"{parts[0]}_{level}"
            cur.execute(
                "UPDATE mathkangarooprogress SET set_id = ? WHERE set_id = ?",
                (new_set_id, old_set_id),
            )
            print(f"  ✅ {old_set_id} → {new_set_id}")
            total += 1

    conn.commit()
    conn.close()
    print(f"  💾 Updated {total} rows in mathkangarooprogress")


if __name__ == "__main__":
    run()
