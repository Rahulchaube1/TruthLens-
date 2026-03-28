"""Scan history endpoint."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.routes.auth import get_current_user

router = APIRouter()

# In-memory history store (replace with PostgreSQL in production)
_history: list = []


class ScanRecord(BaseModel):
    id: str
    user_id: str
    scan_type: str
    is_fake: bool
    confidence: float
    risk_level: str
    timestamp: datetime
    source_url: Optional[str] = None


def _add_record(user_id: str, scan_type: str, is_fake: bool, confidence: float,
                risk_level: str, source_url: Optional[str] = None):
    _history.append({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "scan_type": scan_type,
        "is_fake": is_fake,
        "confidence": confidence,
        "risk_level": risk_level,
        "timestamp": datetime.now(timezone.utc),
        "source_url": source_url,
    })


@router.get("", response_model=List[ScanRecord])
async def get_history(
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    current_user: dict = Depends(get_current_user),
):
    uid = user_id or current_user["id"]
    records = [r for r in _history if r["user_id"] == uid]
    return records[-limit:]
