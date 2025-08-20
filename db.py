# db.py
import os, json
from datetime import datetime

DATA_DIR = os.path.join(os.getcwd(), "data")
USERS_DIR = os.path.join(DATA_DIR, "users")
os.makedirs(USERS_DIR, exist_ok=True)

def _path(user_id: str) -> str:
    safe = "".join(c for c in user_id if c.isalnum() or c in "-_.")
    return os.path.join(USERS_DIR, f"{safe}.json")

def save_user(user_id: str, name: str, ct_b64: str, nonce_b64: str):
    with open(_path(user_id), "w", encoding="utf-8") as f:
        json.dump({
            "user_id": user_id, "name": name,
            "embedding_ciphertext": ct_b64, "nonce_b64": nonce_b64,
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }, f, indent=2)

def load_user(user_id: str):
    p = _path(user_id)
    if not os.path.exists(p): return None
    with open(p, "r", encoding="utf-8") as f: return json.load(f)
