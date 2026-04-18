"""
routers/schedules.py — Test schedule CRUD (parent-set test dates).
Section: Parent
Dependencies: models.py (Schedule)
API: GET /api/schedules, POST /api/schedules, DELETE /api/schedules/{id}
"""

import re as _re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import Schedule
except ImportError:
    from database import get_db
    from models import Schedule

router = APIRouter()

_DATE_RE = _re.compile(r'^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$')


class ScheduleCreate(BaseModel):
    test_date: str
    memo: str

    def clean(self):
        self.memo = self.memo.strip()[:200]
        if not _DATE_RE.match(self.test_date):
            raise HTTPException(status_code=400, detail="test_date must be YYYY-MM-DD")
        return self


# @tag SCHEDULES
@router.get("/api/schedules")
def get_schedules(db: Session = Depends(get_db)):
    """Return all schedules ordered by id desc."""
    return db.query(Schedule).order_by(Schedule.id.desc()).all()


# @tag SCHEDULES
@router.post("/api/schedules")
def create_schedule(req: ScheduleCreate, db: Session = Depends(get_db)):
    """Create a new test schedule entry."""
    req.clean()
    new_sch = Schedule(test_date=req.test_date, memo=req.memo)
    db.add(new_sch)
    db.commit()
    db.refresh(new_sch)
    return new_sch


# @tag SCHEDULES
@router.delete("/api/schedules/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Delete a schedule by id."""
    db.query(Schedule).filter(Schedule.id == schedule_id).delete()
    db.commit()
    return {"status": "success"}
