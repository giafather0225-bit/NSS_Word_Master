"""
routers/rewards.py — Legacy Reward CRUD (pre-Phase 5 reward system).
Section: Parent
Dependencies: models.py (Reward)
API: GET /api/rewards, POST /api/rewards, PUT /api/rewards/{id},
     DELETE /api/rewards/{id}, POST /api/rewards/earn_all

Note: this is the older parent-managed reward list. The XP-based shop
(Phase 5) lives in routers/reward_shop.py.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..models import Reward
    from ..schemas_common import Str100, Str300
except ImportError:
    from database import get_db
    from models import Reward
    from schemas_common import Str100, Str300

router = APIRouter()


class RewardCreate(BaseModel):
    title: Str100
    description: Str300

    def clean(self):
        """No-op — Pydantic enforces length (422 on overflow)."""
        return self


# @tag REWARDS
@router.get("/api/rewards")
def get_rewards(db: Session = Depends(get_db)):
    """Return all rewards ordered by id desc."""
    return db.query(Reward).order_by(Reward.id.desc()).all()


# @tag REWARDS
@router.post("/api/rewards")
def create_reward(req: RewardCreate, db: Session = Depends(get_db)):
    """Create a new reward entry."""
    req.clean()
    if not req.title:
        raise HTTPException(status_code=400, detail="title required")
    new_reward = Reward(title=req.title, description=req.description, is_earned=False)
    db.add(new_reward)
    db.commit()
    db.refresh(new_reward)
    return new_reward


# @tag REWARDS
@router.put("/api/rewards/{reward_id}")
def earn_reward(reward_id: int, db: Session = Depends(get_db)):
    """Mark a reward as earned."""
    reward = db.query(Reward).filter(Reward.id == reward_id).first()
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    reward.is_earned = True
    db.commit()
    return {"status": "success"}


# @tag REWARDS
@router.delete("/api/rewards/{reward_id}")
def delete_reward(reward_id: int, db: Session = Depends(get_db)):
    """Delete a reward by id."""
    reward = db.query(Reward).filter(Reward.id == reward_id).first()
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    db.delete(reward)
    db.commit()
    return {"status": "success"}


# @tag REWARDS
@router.post("/api/rewards/earn_all")
def earn_all_rewards(db: Session = Depends(get_db)):
    """Mark all rewards as earned."""
    db.query(Reward).update({"is_earned": True})
    db.commit()
    return {"status": "success"}
