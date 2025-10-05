from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.core import security
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


@pytest.fixture(autouse=True)
def fake_password_hash(monkeypatch):
    def _hash(password: str) -> str:
        return f"hashed:{password}"

    def _verify(plain: str, hashed: str) -> bool:
        return hashed == _hash(plain)

    monkeypatch.setattr(security, "get_password_hash", _hash)
    monkeypatch.setattr(security, "verify_password", _verify)
    monkeypatch.setattr("app.services.auth_service.get_password_hash", _hash)
    monkeypatch.setattr("app.services.auth_service.verify_password", _verify)


@pytest.fixture(name="auth_service")
def fixture_auth_service(db_session):
    return AuthService(db_session)


def test_register_user_creates_account(auth_service):
    user_in = UserCreate(email="user@example.com", password="securepass")

    user = auth_service.register_user(user_in)

    assert user.id is not None
    assert user.email == user_in.email
    assert user.password_hash != user_in.password


def test_register_user_duplicate_email_raises(auth_service):
    user_in = UserCreate(email="duplicate@example.com", password="password")
    auth_service.register_user(user_in)

    with pytest.raises(HTTPException) as exc:
        auth_service.register_user(user_in)

    assert exc.value.status_code == 400
    assert "Email already registered" in exc.value.detail


def test_authenticate_with_valid_credentials(auth_service):
    email = "login@example.com"
    password = "password"
    auth_service.register_user(UserCreate(email=email, password=password))

    user = auth_service.authenticate(email, password)

    assert user.email == email


def test_authenticate_with_invalid_credentials_raises(auth_service):
    email = "invalid@example.com"
    password = "password"
    auth_service.register_user(UserCreate(email=email, password=password))

    with pytest.raises(HTTPException) as exc:
        auth_service.authenticate(email, "wrong-password")

    assert exc.value.status_code == 401
    assert "Invalid credentials" in exc.value.detail
