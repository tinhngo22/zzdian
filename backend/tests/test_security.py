from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

import time
import os
import subprocess
import sys
import jwt
import pytest
from app.security import JWT_SECRET


def test_password_roundtrip():
    h = hash_password("correct-horse-battery")
    assert h != "correct-horse-battery"
    assert verify_password(h, "correct-horse-battery")
    assert not verify_password(h, "wrong")
    assert not verify_password("not-a-hash", "anything")


def test_token_roundtrip():
    token = create_access_token("11111111-1111-1111-1111-111111111111")
    assert decode_access_token(token) == "11111111-1111-1111-1111-111111111111"
    assert decode_access_token(token + "x") is None


@pytest.mark.parametrize("patch", [
    {"exp": int(time.time()) - 1}, {"ver": -1}, {"ver": True},
    {"ver": "0"}, {"sub": None},
])
def test_invalid_claims_are_rejected(patch):
    claims = {"sub": "11111111-1111-1111-1111-111111111111", "iat": int(time.time()), "exp": int(time.time()) + 60, "ver": 0}
    claims.update(patch)
    assert decode_access_token(jwt.encode(claims, JWT_SECRET, algorithm="HS256")) is None


@pytest.mark.parametrize("missing", ["sub", "iat", "exp", "ver"])
def test_required_claims(missing):
    claims = {"sub": "11111111-1111-1111-1111-111111111111", "iat": int(time.time()), "exp": int(time.time()) + 60, "ver": 0}
    del claims[missing]
    assert decode_access_token(jwt.encode(claims, JWT_SECRET, algorithm="HS256")) is None


@pytest.mark.parametrize("secret", ["", "change-me", "a" * 31])
def test_weak_secret_prevents_startup(secret):
    result = subprocess.run(
        [sys.executable, "-c", "import app.security"],
        env={**os.environ, "JWT_SECRET": secret}, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "JWT_SECRET must be" in result.stderr
