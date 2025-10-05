from __future__ import annotations

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.mongodb import get_database, get_grid_fs
from app.db.postgres import get_db
from app.models.user import User
from app.services.chat_service import ChatService
from app.services.pdf_service import PDFService


def get_mongo_database() -> AsyncIOMotorDatabase:
    return get_database()


def get_gridfs_bucket() -> AsyncIOMotorGridFSBucket:
    return get_grid_fs()


def get_pdf_service(
    db: AsyncIOMotorDatabase = Depends(get_mongo_database),
    grid_fs: AsyncIOMotorGridFSBucket = Depends(get_gridfs_bucket),
) -> PDFService:
    return PDFService(db=db, grid_fs=grid_fs)


def get_chat_service(
    db: Session = Depends(get_db),
    pdf_service: PDFService = Depends(get_pdf_service),
) -> ChatService:
    return ChatService(db=db, pdf_service=pdf_service)


def get_authenticated_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
