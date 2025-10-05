from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.postgres import get_db
from app.models.user import User

settings = get_settings()
security = HTTPBearer()


def _ensure_password_length(password: str) -> bytes:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be 72 bytes or fewer")
    return password_bytes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bool(bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8")))
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    password_bytes = _ensure_password_length(password)
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    token_data: dict[str, Any] = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    token_data["exp"] = expire
    return jwt.encode(token_data, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, str]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:  # pragma: no cover - network edge
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    return payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
