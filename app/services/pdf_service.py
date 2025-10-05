from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import List

import PyPDF2
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket

from app.core.config import get_settings
from app.schemas.pdf import PDFMetadata

settings = get_settings()


class PDFService:
    """Handle PDF storage and parsing operations."""

    def __init__(self, db: AsyncIOMotorDatabase, grid_fs: AsyncIOMotorGridFSBucket) -> None:
        self.db = db
        self.grid_fs = grid_fs

    async def upload_pdf(self, file: UploadFile, user_id: int) -> PDFMetadata:
        if file.content_type not in settings.allowed_file_types:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed")

        contents = await file.read()
        if len(contents) > settings.max_file_size:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds size limit")

        file_id = await self.grid_fs.upload_from_stream(
            file.filename,
            BytesIO(contents),
            metadata={"user_id": user_id, "filename": file.filename},
        )

        metadata = {
            "pdf_id": str(file_id),
            "user_id": user_id,
            "filename": file.filename,
            "upload_date": datetime.utcnow(),
            "is_parsed": False,
        }
        await self.db.pdf_metadata.insert_one(metadata)
        return PDFMetadata(**metadata)

    async def list_pdfs(self, user_id: int) -> List[PDFMetadata]:
        cursor = self.db.pdf_metadata.find({"user_id": user_id})
        results: List[PDFMetadata] = []
        async for doc in cursor:
            doc.pop("_id", None)
            results.append(PDFMetadata(**doc))
        return results

    async def parse_pdf(self, pdf_id: str, user_id: int) -> str:
        metadata = await self.db.pdf_metadata.find_one({"pdf_id": pdf_id, "user_id": user_id})
        if not metadata:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found")

        try:
            object_id = ObjectId(pdf_id)
        except InvalidId as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PDF identifier") from exc

        stream = await self.grid_fs.open_download_stream(object_id)
        contents = await stream.read()
        reader = PyPDF2.PdfReader(BytesIO(contents))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        await self.db.pdf_texts.update_one(
            {"pdf_id": pdf_id, "user_id": user_id},
            {"$set": {"text": text, "parsed_at": datetime.utcnow()}},
            upsert=True,
        )
        await self.db.pdf_metadata.update_one({"pdf_id": pdf_id}, {"$set": {"is_parsed": True}})
        return text

    async def get_parsed_text(self, pdf_id: str, user_id: int) -> str:
        doc = await self.db.pdf_texts.find_one({"pdf_id": pdf_id, "user_id": user_id})
        if not doc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF not parsed yet")
        return doc["text"]

    async def ensure_pdf_owned_by_user(self, pdf_id: str, user_id: int) -> PDFMetadata:
        doc = await self.db.pdf_metadata.find_one({"pdf_id": pdf_id, "user_id": user_id})
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found")
        doc.pop("_id", None)
        return PDFMetadata(**doc)
