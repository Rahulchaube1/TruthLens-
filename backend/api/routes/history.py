"""Scan history endpoint."""
import csv
import io
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
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


@router.get("/export")
async def export_history(
    format: str = Query("csv", pattern="^(csv|json)$"),
    limit: int = Query(200, le=1000),
    current_user: dict = Depends(get_current_user),
):
    """Export scan history as CSV or JSON for reporting and audit purposes."""
    uid = current_user["id"]
    records = [r for r in _history if r["user_id"] == uid][-limit:]

    if format == "json":
        import json

        def _serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        payload = json.dumps([dict(r) for r in records], default=_serial, indent=2)
        return StreamingResponse(
            io.BytesIO(payload.encode()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=truthlens_history.json"},
        )

    # CSV export
    output = io.StringIO()
    fieldnames = ["id", "user_id", "scan_type", "is_fake", "confidence", "risk_level", "timestamp", "source_url"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for r in records:
        row = dict(r)
        if isinstance(row.get("timestamp"), datetime):
            row["timestamp"] = row["timestamp"].isoformat()
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=truthlens_history.csv"},
    )
