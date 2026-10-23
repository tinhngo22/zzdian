from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


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