from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any

class Snapshot(BaseModel):
    imageDataUrl: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    deviceInfo: Optional[Dict[str, Any]] = None
    consentVersion: Optional[str] = None
    capturedAt: Optional[int] = None

class EnrollIn(BaseModel):
    userId: str = Field(min_length=1)
    name: Optional[str] = None
    email: EmailStr
    descriptor: List[float] = Field(min_length=64)  # 128 is typical
    createdAt: Optional[str] = None
    snapshot: Optional[Snapshot] = None

class EnrollOut(BaseModel):
    ok: bool
    updated: bool
    userId: str
    email: EmailStr

class VerifyIn(BaseModel):
    userId: Optional[str] = None
    email: Optional[EmailStr] = None
    descriptor: List[float] = Field(min_length=64)

class VerifyOut(BaseModel):
    matched: bool
    distance: float
    threshold: float

    
class PinRequest(BaseModel):
    pin: str

class PinResponse(BaseModel):
    ok: bool
    employee_id: str
    name: str
