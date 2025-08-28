# app/main.py
from __future__ import annotations

import base64
import os
import re
from typing import List

import numpy as np
from sqlalchemy import text
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .schemas import (
    EnrollIn,
    EnrollOut,
    VerifyIn,
    VerifyOut,
    PinRequest,
    PinResponse,
)
from .encryption_utils import encrypt_bytes, decrypt_bytes
from .face_service import euclidean
from .db import engine, Base, get_db
from . import crud

# ---------------- FASTAPI APP ----------------
APP = FastAPI(title="Biometric Auth Backend", version="0.1.0")

# ✅ CORS configuration (Next.js runs on 3000 or 3001)
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

APP.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # 👈 allow your frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables if they don't exist (dev only; use Alembic in prod)
Base.metadata.create_all(bind=engine)

# ---------------- GLOBAL SETTINGS ----------------
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.60"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------- PIN AUTH ----------------
@APP.post("/api/auth/pin", response_model=PinResponse)
def check_pin(req: PinRequest, db: Session = Depends(get_db)):
    employee = crud.get_employee_by_pin(db, req.pin)
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    return {
        "ok": True,
        "employee_id": employee.employee_id,
        "name": employee.name,
    }


# ---------------- HEALTH ----------------
@APP.get("/api/health/db")
def health_db(db: Session = Depends(get_db)):
    try:
        val = db.execute(text("SELECT 1")).scalar_one()
        return {"db": "ok", "result": val}
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"db error: {e.__class__.__name__}: {e}"
        )


@APP.get("/api/health")
def health():
    return {"ok": True, "threshold": MATCH_THRESHOLD}


# ---------------- HELPERS ----------------
def vec_to_bytes(vec: List[float]) -> bytes:
    """Convert a float vector into bytes (little-endian, float32)."""
    arr = np.asarray(vec, dtype=np.float32)
    return arr.tobytes(order="C")


def bytes_to_vec(buf: bytes) -> List[float]:
    """Inverse of vec_to_bytes."""
    arr = np.frombuffer(buf, dtype=np.float32)
    return arr.tolist()


def _save_snapshot(image_data_url: str | None, user_id: str) -> str | None:
    """Save snapshot (base64 → file) to UPLOAD_DIR."""
    if not image_data_url:
        return None
    m = re.match(r"^data:image/(png|jpeg);base64,(.+)$", image_data_url, re.I)
    if not m:
        return None
    ext = "png" if m.group(1).lower() == "png" else "jpg"
    raw = base64.b64decode(m.group(2))
    path = os.path.join(UPLOAD_DIR, f"{user_id}.{ext}")
    with open(path, "wb") as f:
        f.write(raw)
    return path


# ---------------- ENROLL ----------------
@APP.post("/api/biometrics/enroll", response_model=EnrollOut)
def enroll(payload: EnrollIn, db: Session = Depends(get_db)):
    # descriptor → encrypt
    desc_bytes = vec_to_bytes(payload.descriptor)
    ct_b64, nonce_b64 = encrypt_bytes(desc_bytes)

    # optional snapshot save
    snap_path = _save_snapshot(
        payload.snapshot.imageDataUrl if payload.snapshot else None,
        payload.userId,
    )

    row, updated = crud.upsert_enrollment(
        db,
        user_id=payload.userId,
        name=payload.name,
        email=payload.email,
        ct_b64=ct_b64,
        nonce_b64=nonce_b64,
        snapshot_path=snap_path,
    )
    return EnrollOut(ok=True, updated=updated, userId=row.user_id, email=row.email)


# ---------------- VERIFY ----------------
@APP.post("/api/biometrics/verify", response_model=VerifyOut)
def verify(payload: VerifyIn, db: Session = Depends(get_db)):
    rec = None
    if payload.userId:
        rec = crud.get_by_user_id(db, payload.userId)
    if not rec and payload.email:
        rec = crud.get_by_email(db, payload.email)
    if not rec:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    stored_vec = bytes_to_vec(
        decrypt_bytes(rec.embedding_ciphertext, rec.nonce_b64)
    )
    dist = euclidean(stored_vec, payload.descriptor)
    return VerifyOut(
        matched=dist <= MATCH_THRESHOLD, distance=dist, threshold=MATCH_THRESHOLD
    )
