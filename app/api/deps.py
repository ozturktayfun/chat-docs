from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Any

from app.core.security import get_current_user
from app.db.mongodb import get_database, get_grid_fs
from app.db.postgres import get_db
from app.models.user import User
from app.services.chat_service import ChatService
from app.services.pdf_service import PDFService


def get_mongo_database() -> Any:
    """Return the active MongoDB database instance."""
    return get_database()


def get_gridfs_bucket() -> Any:
    """Return the GridFS bucket used for storing PDF binaries."""
    return get_grid_fs()


def get_pdf_service(
    db: Any = Depends(get_mongo_database),
    grid_fs: Any = Depends(get_gridfs_bucket),
) -> PDFService:
    """Provide a PDFService wired with MongoDB database and GridFS."""
    return PDFService(db=db, grid_fs=grid_fs)


def get_chat_service(
    db: Session = Depends(get_db),
    pdf_service: PDFService = Depends(get_pdf_service),
) -> ChatService:
    """Provide a ChatService that persists history in PostgreSQL."""
    return ChatService(db=db, pdf_service=pdf_service)


def get_authenticated_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the current request is authenticated and return the user model."""
    return current_user
