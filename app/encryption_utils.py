# encryption_utils.py
import base64, os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SECRET_PASSWORD = os.getenv("SECRET_PASSWORD", "change_me_please")
PBKDF2_SALT_BASE64 = os.getenv("PBKDF2_SALT_BASE64", "bm90LWEtcmVhbC1zYWx0LWNoYW5nZS1tZQ==")

def _derive_key(password: str, salt_b64: str) -> bytes:
    salt = base64.b64decode(salt_b64)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=200_000)
    return kdf.derive(password.encode())

def encrypt_bytes(plaintext: bytes) -> tuple[str, str]:
    key = _derive_key(SECRET_PASSWORD, PBKDF2_SALT_BASE64)
    aes = AESGCM(key); nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext, None)
    return base64.b64encode(ct).decode(), base64.b64encode(nonce).decode()

def decrypt_bytes(ciphertext_b64: str, nonce_b64: str) -> bytes:
    key = _derive_key(SECRET_PASSWORD, PBKDF2_SALT_BASE64)
    aes = AESGCM(key)
    return aes.decrypt(base64.b64decode(nonce_b64), base64.b64decode(ciphertext_b64), None)
