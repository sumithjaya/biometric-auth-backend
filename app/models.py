# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from .db import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    pin = Column(String(10), nullable=False)  # hash this in prod!


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(128), nullable=False, index=True)
    name = Column(String(256), nullable=True)
    email = Column(String(256), nullable=False, index=True)

    # store your AES-GCM output as base64 strings
    embedding_ciphertext = Column(String, nullable=False)  # base64 text
    nonce_b64 = Column(String(64), nullable=False)         # base64 12B nonce
    snapshot_path = Column(String(512), nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_enroll_user"),
        UniqueConstraint("email", name="uq_enroll_email"),
    )
