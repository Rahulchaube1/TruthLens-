"""Pydantic schemas for DB models."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ScanResultCreate(BaseModel):
    scan_type: str
    is_fake: bool
    confidence: float
    risk_level: str
    source_url: Optional[str] = None
    raw_result: Optional[str] = None


class ScanResultRead(ScanResultCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
