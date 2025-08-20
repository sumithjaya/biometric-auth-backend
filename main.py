# main.py
from config import ALLOW_ORIGINS, MATCH_METHOD, COSINE_THRESHOLD, EUCLIDEAN_THRESHOLD, MODEL_NAME
from encryption_utils import encrypt_bytes, decrypt_bytes
from db import save_user_record, get_user_record
from face_service import image_to_embedding, cosine_similarity, euclidean_distance
from schemas import VerifyResponse, LivenessResponse
from middleware import LoggingMiddleware

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
from PIL import Image
import numpy as np
import io, os

# ---- InsightFace (no TF needed; works on Python 3.13) ----
from insightface.app import FaceAnalysis

app = FastAPI(title="Biometric Auth API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

DATA_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Lazy init so import is fast
_face_app: Optional[FaceAnalysis] = None
def get_face_app() -> FaceAnalysis:
    global _face_app
    if _face_app is None:
        _face_app = FaceAnalysis(name="buffalo_l")
        _face_app.prepare(ctx_id=-1)  # CPU
    return _face_app

def image_to_embedding(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_np = np.array(img)
    app = get_face_app()
    faces = app.get(img_np)
    if not faces:
        raise ValueError("No face detected")
    # pick largest face
    face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
    emb = face.normed_embedding.astype(np.float32)  # L2-normalized
    return emb

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0: return 0.0
    return float(np.dot(a, b) / denom)

def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/register_face")
async def register_face(user_id: str = Query(...), file: UploadFile = File(...)):
    data = await file.read()
    try:
        emb = image_to_embedding(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Face not detected: {e}")
    # Save embedding to disk (MVP). We’ll add AES encryption next.
    path = os.path.join(DATA_DIR, f"{user_id}.npy")
    np.save(path, emb)
    return {"ok": True, "user_id": user_id, "stored": path}

@app.post("/verify_face")
async def verify_face(
    user_id: str = Query(...),
    method: str = Query("cosine"),  # "cosine" or "euclidean"
    file: UploadFile = File(...),
):
    path = os.path.join(DATA_DIR, f"{user_id}.npy")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="User not registered")
    stored = np.load(path).astype(np.float32)

    data = await file.read()
    try:
        probe = image_to_embedding(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Face not detected: {e}")

    cos = cosine_similarity(probe, stored)
    euc = euclidean_distance(probe, stored)

    if method.lower() == "cosine":
        threshold = 0.6  # tune later
        match = cos >= threshold
        score = cos
    elif method.lower() == "euclidean":
        threshold = 0.8  # tune later
        match = euc <= threshold
        score = euc
    else:
        raise HTTPException(status_code=400, detail="method must be 'cosine' or 'euclidean'")

    return JSONResponse({
        "match": match,
        "method": method.lower(),
        "score": float(score),
        "cosine": float(cos),
        "euclidean": float(euc),
    })
