from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

from .schemas import EnrollIn, EnrollOut, VerifyIn, VerifyOut
from .encryption_utils import encrypt_bytes, decrypt_bytes
from .face_service import euclidean
from .db import save_user, load_user, find_user_by_email

import base64, re

from app.db import engine, Base, get_db
from app import crud
from sqlalchemy.orm import Session

APP = FastAPI(title="Biometric Auth Backend", version="0.1.0")
Base.metadata.create_all(bind=engine)
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
APP.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.6"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@APP.get("/api/health")
def health():
    return {"ok": True, "threshold": MATCH_THRESHOLD}

def _save_snapshot(image_data_url: str | None, user_id: str) -> str | None:
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

@APP.post("/api/biometrics/enroll", response_model=EnrollOut)
def enroll(payload: EnrollIn):
     # descriptor -> bytes -> encrypt
    desc_bytes = vec_to_bytes(payload.descriptor)
    ct_b64, nonce_b64 = encrypt_bytes(desc_bytes)

    # optional snapshot save
    snap_path = _save_snapshot(payload.snapshot.imageDataUrl if payload.snapshot else None,
                               payload.userId)

    row, updated = crud.upsert_enrollment(
        db,
        user_id=payload.userId,
        name=payload.name,
        email=payload.email,
        ct_b64=ct_b64,
        nonce_b64=nonce_b64,
        snapshot_path=snap_path
    )
    return EnrollOut(ok=True, updated=updated, userId=row.user_id, email=row.email)


@APP.post("/api/biometrics/verify", response_model=VerifyOut)
def verify(payload: VerifyIn, db: Session = Depends(get_db)):
    rec = None
    if payload.userId:
        rec = crud.get_by_user_id(db, payload.userId)
    if not rec and payload.email:
        rec = crud.get_by_email(db, payload.email)
    if not rec:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    stored_vec = bytes_to_vec(decrypt_bytes(rec.embedding_ciphertext, rec.nonce_b64))
    dist = euclidean(stored_vec, payload.descriptor)
    return VerifyOut(matched=dist <= float(os.getenv("MATCH_THRESHOLD", "0.60")),
                     distance=dist,
                     threshold=float(os.getenv("MATCH_THRESHOLD", "0.60")))

