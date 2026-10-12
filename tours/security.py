import os
import base64
import hashlib
import hmac


def hash_password(password: str) -> tuple[str, str]:
    """
    Generates a secure PBKDF2-SHA256 hash and salt matching the original C# .NET hasher.
    """
    salt_bytes = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, 100000, dklen=32)
    return base64.b64encode(hash_bytes).decode('utf-8'), base64.b64encode(salt_bytes).decode('utf-8')


def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    """
    Verifies a password against the stored PBKDF2-SHA256 hash and salt.
    """
    try:
        salt_bytes = base64.b64decode(stored_salt)
        stored_hash_bytes = base64.b64decode(stored_hash)
        computed_hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, 100000, dklen=32)
        return hmac.compare_digest(computed_hash_bytes, stored_hash_bytes)
    except Exception:
        return False
