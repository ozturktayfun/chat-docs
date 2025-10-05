from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate

settings = get_settings()


class AuthService:
    """Business logic for authentication and user management."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def register_user(self, user_in: UserCreate) -> User:
        existing = self.db.query(User).filter(User.email == user_in.email).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        user = User(email=user_in.email, password_hash=get_password_hash(user_in.password))
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return user

    def create_token(self, user: User) -> str:
        return create_access_token({"sub": user.email}, expires_delta=timedelta(minutes=settings.access_token_expire_minutes))
