"""
routers/calendar_api.py — Monthly calendar view API
Section: Diary
Dependencies: models.py (DiaryEntry, StreakLog, DayOffRequest)
API: GET /api/calendar/{year}/{month}
"""

# ================================================================
# calendar_api.py — Calendar day markers for the monthly view
# Section: Diary
# Dependencies: models.py (DiaryEntry, StreakLog, DayOffRequest)
# API endpoints:
#   GET /api/calendar/{year}/{month}
# ================================================================

import calendar
from datetime import date as _date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import DiaryEntry, StreakLog, DayOffRequest
except ImportError:
    from database import get_db
    from models import DiaryEntry, StreakLog, DayOffRequest

router = APIRouter()


# ── Route ──────────────────────────────────────────────────────

# @tag CALENDAR @tag DIARY
@router.get("/api/calendar/{year}/{month}")
def get_calendar_month(year: int, month: int, db: Session = Depends(get_db)):
    """
    Return a list of day objects for every day in the requested month.

    Each object shape:
      {
        "date":    "YYYY-MM-DD",
        "streak":  bool,
        "journal": bool,
        "day_off": bool,
        "marker":  "🔥" | "🏖️" | "📝" | "⬜" | ""
      }

    Marker priority (first match wins):
      1. Approved day-off request for that date → "🏖️"
      2. StreakLog.streak_maintained == True     → "🔥"
      3. DiaryEntry exists for that date         → "📝"
      4. Past date with StreakLog but streak_maintained == False → "⬜"
      5. Today or future                         → ""
    """
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="month must be 1–12")
    if not (2000 <= year <= 2100):
        raise HTTPException(status_code=400, detail="year out of range")

    days_in_month = calendar.monthrange(year, month)[1]
    today = _date.today()

    # Build sets/maps for O(1) lookups — avoid N+1 queries
    month_prefix  = f"{year:04d}-{month:02d}-"

    approved_days: set[str] = {
        row.request_date
        for row in db.query(DayOffRequest.request_date)
        .filter(
            DayOffRequest.request_date.like(f"{month_prefix}%"),
            DayOffRequest.status == "approved",
        )
        .all()
    }

    streak_map: dict[str, bool] = {
        row.date: row.streak_maintained
        for row in db.query(StreakLog.date, StreakLog.streak_maintained)
        .filter(StreakLog.date.like(f"{month_prefix}%"))
        .all()
    }

    journal_days: set[str] = {
        row.entry_date
        for row in db.query(DiaryEntry.entry_date)
        .filter(DiaryEntry.entry_date.like(f"{month_prefix}%"))
        .all()
    }

    result = []
    for day_num in range(1, days_in_month + 1):
        date_str    = f"{year:04d}-{month:02d}-{day_num:02d}"
        is_past     = _date(year, month, day_num) < today

        day_off_flag = date_str in approved_days
        streak_flag  = streak_map.get(date_str, False)
        journal_flag = date_str in journal_days

        # Marker priority
        if day_off_flag:
            marker = "🏖️"
        elif streak_flag:
            marker = "🔥"
        elif journal_flag:
            marker = "📝"
        elif is_past and date_str in streak_map and not streak_map[date_str]:
            marker = "⬜"
        else:
            marker = ""

        result.append({
            "date":    date_str,
            "streak":  streak_flag,
            "journal": journal_flag,
            "day_off": day_off_flag,
            "marker":  marker,
        })

    return result
