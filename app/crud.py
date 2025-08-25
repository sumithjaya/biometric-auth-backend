# app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import Enrollment

def get_by_user_id(db: Session, user_id: str):
    return db.execute(select(Enrollment).where(Enrollment.user_id == user_id)).scalar_one_or_none()

def get_by_email(db: Session, email: str):
    return db.execute(select(Enrollment).where(Enrollment.email == email)).scalar_one_or_none()

def upsert_enrollment(
    db: Session,
    *,
    user_id: str,
    name: str | None,
    email: str,
    ct_b64: str,
    nonce_b64: str,
    snapshot_path: str | None
):
    row = get_by_user_id(db, user_id) or get_by_email(db, email)
    updated = False
    if row:
        # update in place
        row.user_id = user_id
        row.name = name
        row.email = email
        row.embedding_ciphertext = ct_b64
        row.nonce_b64 = nonce_b64
        if snapshot_path:
            row.snapshot_path = snapshot_path
        updated = True
    else:
        row = Enrollment(
            user_id=user_id,
            name=name,
            email=email,
            embedding_ciphertext=ct_b64,
            nonce_b64=nonce_b64,
            snapshot_path=snapshot_path,
        )
        db.add(row)

    db.commit()
    db.refresh(row)
    return row, updated
