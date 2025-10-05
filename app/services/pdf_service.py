from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from typing import Any, List

import PyPDF2
from loguru import logger
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings
from app.schemas.pdf import PDFMetadata

settings = get_settings()


class PDFService:
    """Handle PDF storage and parsing operations."""

    def __init__(self, db: Any, grid_fs: Any) -> None:
        self.db = db
        self.grid_fs = grid_fs

    async def upload_pdf(self, file: UploadFile, user_id: int) -> PDFMetadata:
        logger.info("PDF upload requested filename={} user_id={}", file.filename, user_id)
        if file.content_type not in settings.allowed_file_types:
            logger.warning(
                "Rejected upload due to content type filename={} user_id={} content_type={} allowed={}",
                file.filename,
                user_id,
                file.content_type,
                settings.allowed_file_types,
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed")

        contents = await file.read()
        file_size = len(contents)
        if file_size > settings.max_file_size:
            logger.warning(
                "Rejected upload exceeding size limit filename={} user_id={} size={} limit={}",
                file.filename,
                user_id,
                file_size,
                settings.max_file_size,
            )
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
            "upload_date": datetime.now(timezone.utc),
            "is_parsed": False,
        }
        await self.db.pdf_metadata.insert_one(metadata)
        logger.info(
            "Stored PDF pdf_id={} filename={} user_id={} size={} bytes",
            metadata["pdf_id"],
            metadata["filename"],
            user_id,
            file_size,
        )
        return PDFMetadata(**metadata)

    async def list_pdfs(self, user_id: int) -> List[PDFMetadata]:
        cursor = self.db.pdf_metadata.find({"user_id": user_id})
        results: List[PDFMetadata] = []
        async for doc in cursor:
            doc.pop("_id", None)
            results.append(PDFMetadata(**doc))
        logger.info("Retrieved {} PDFs for user_id={}", len(results), user_id)
        return results

    async def parse_pdf(self, pdf_id: str, user_id: int) -> str:
        metadata = await self.db.pdf_metadata.find_one({"pdf_id": pdf_id, "user_id": user_id})
        if not metadata:
            logger.warning("Parse requested for missing PDF pdf_id={} user_id={}", pdf_id, user_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found")

        try:
            object_id = ObjectId(pdf_id)
        except InvalidId as exc:
            logger.warning("Invalid PDF identifier provided pdf_id={} user_id={}", pdf_id, user_id)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PDF identifier") from exc

        stream = await self.grid_fs.open_download_stream(object_id)
        contents = await stream.read()
        reader = PyPDF2.PdfReader(BytesIO(contents))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        await self.db.pdf_texts.update_one(
            {"pdf_id": pdf_id, "user_id": user_id},
            {"$set": {"text": text, "parsed_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
        await self.db.pdf_metadata.update_one({"pdf_id": pdf_id}, {"$set": {"is_parsed": True}})
        logger.info("Parsed PDF successfully pdf_id={} user_id={} text_length={}", pdf_id, user_id, len(text))
        return text

    async def get_parsed_text(self, pdf_id: str, user_id: int) -> str:
        doc = await self.db.pdf_texts.find_one({"pdf_id": pdf_id, "user_id": user_id})
        if not doc:
            logger.warning("Parsed text requested before parsing pdf_id={} user_id={}", pdf_id, user_id)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF not parsed yet")
        logger.debug("Retrieved parsed text for pdf_id={} user_id={}", pdf_id, user_id)
        return doc["text"]

    async def ensure_pdf_owned_by_user(self, pdf_id: str, user_id: int) -> PDFMetadata:
        doc = await self.db.pdf_metadata.find_one({"pdf_id": pdf_id, "user_id": user_id})
        if not doc:
            logger.warning("Ownership check failed pdf_id={} user_id={}", pdf_id, user_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found")
        doc.pop("_id", None)
        logger.debug("Verified PDF ownership pdf_id={} user_id={}", pdf_id, user_id)
        return PDFMetadata(**doc)
