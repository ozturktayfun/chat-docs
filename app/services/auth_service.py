from __future__ import annotations

from datetime import timedelta
from typing import cast

from loguru import logger

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
        logger.info("Registering user email={}", user_in.email)
        existing = self.db.query(User).filter(User.email == user_in.email).first()
        if existing:
            logger.warning("Registration denied for existing email={}", user_in.email)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        user = User(email=user_in.email, password_hash=get_password_hash(user_in.password))
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        logger.info("User registered id={} email={}", user.id, user.email)
        return user

    def authenticate(self, email: str, password: str) -> User:
        logger.info("Authenticating user email={}", email)
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, cast(str, user.password_hash)):
            logger.warning("Authentication failed for email={}", email)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        logger.info("Authentication succeeded for user_id={} email={}", user.id, email)
        return user

    def create_token(self, user: User) -> str:
        logger.debug("Issuing access token for user_id={} email={}", user.id, user.email)
        return create_access_token({"sub": user.email}, expires_delta=timedelta(minutes=settings.access_token_expire_minutes))
