import os
import time

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.environ["JWT_SECRET"]
if len(JWT_SECRET.encode("utf-8")) < 32 or JWT_SECRET.lower() in {
    "change-me", "replace-with-a-random-secret-of-at-least-32-bytes",
}:
    raise RuntimeError("JWT_SECRET must be a random secret of at least 32 bytes")
ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 60 * 60 * 24  

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """One-way hash with a random salt built in. Never store the password itself."""
    return _hasher.hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False

def create_access_token(user_id: str, token_version: int = 0) -> str:
    now = int(time.time())
    payload = {"sub": user_id, "iat": now, "exp": now + TOKEN_TTL_SECONDS, "ver": token_version}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def decode_access_claims(token: str) -> dict | None:
    """Require expiry and session version on every token; reject legacy tokens."""
    try:
        payload = jwt.decode(
            token, JWT_SECRET, algorithms=[ALGORITHM],
            options={"require": ["sub", "iat", "exp", "ver"]},
        )
    except jwt.PyJWTError:
        return None
    if not isinstance(payload["sub"], str) or type(payload["ver"]) is not int or payload["ver"] < 0:
        return None
    return payload


def decode_access_token(token: str) -> str | None:
    """Return the subject of a valid token (database revocation is checked in deps)."""
    payload = decode_access_claims(token)
    return payload["sub"] if payload else None
