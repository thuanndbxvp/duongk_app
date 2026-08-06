"""
Encryption wrapper — dùng Fernet (AES-128-CBC + HMAC SHA-256).
ENCRYPTION_KEY phải được set trong env (44-char base64).
"""
import os
import base64
import hashlib
from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    """
    Lấy Fernet instance. Key được derive từ ENCRYPTION_KEY env.
    Nếu chưa có → derive từ SECRET_KEY (fallback cho dev).
    """
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        # Fallback: dùng SECRET_KEY (đã có) làm base, hash SHA-256 → 32 bytes → base64
        secret = os.environ.get('SECRET_KEY', 'dev-fallback-secret-change-me')
        key_bytes = hashlib.sha256(secret.encode()).digest()
        key = base64.urlsafe_b64encode(key_bytes).decode()
    
    return Fernet(key.encode())


def encrypt(plaintext: str) -> bytes:
    """Encrypt string → bytes. Lưu vào BYTEA column."""
    if not plaintext:
        raise ValueError('Cannot encrypt empty value')
    return _get_fernet().encrypt(plaintext.encode())


def decrypt(ciphertext: bytes) -> str:
    """Decrypt bytes → string. Chỉ dùng khi cần gọi provider."""
    if not ciphertext:
        raise ValueError('Cannot decrypt empty value')
    return _get_fernet().decrypt(ciphertext).decode()


def generate_key() -> str:
    """Generate random Fernet key. Tier 2 dùng để tạo ENCRYPTION_KEY mới."""
    return Fernet.generate_key().decode()