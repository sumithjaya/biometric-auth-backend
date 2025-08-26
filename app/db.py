# app/db.py
from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv


load_dotenv()

# Use env var; fallback to local Postgres dev DB.
# Format: postgresql+psycopg://USER:PASS@HOST:PORT/DBNAME
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/biometric_auth",
)

try:
    from urllib.parse import urlsplit
    parts = urlsplit(DATABASE_URL)
    safe = f"{parts.scheme}://{parts.username}:***@{parts.hostname}:{parts.port}{parts.path}"
    print("[DB] Using:", safe)
except Exception:
    pass

# For Postgres we don't pass SQLite-only args like check_same_thread.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
    pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
