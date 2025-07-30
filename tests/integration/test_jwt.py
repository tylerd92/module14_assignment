import pytest
from app.auth.jwt import get_password_hash, verify_password
from datetime import timedelta, datetime, timezone
from jose import jwt as jose_jwt
from fastapi import HTTPException
from app.auth.jwt import decode_token, create_token, settings
from app.schemas.token import TokenType

def test_get_password_hash_returns_hash():
    password = "mysecretpassword"
    hashed = get_password_hash(password)
    assert isinstance(hashed, str)
    assert hashed != password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$")

def test_get_password_hash_and_verify_password():
    password = "anotherpassword"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)
