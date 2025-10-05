from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

import pytest
from bson import ObjectId
from fastapi import HTTPException
from PyPDF2 import PdfWriter

from app.services.pdf_service import PDFService


@dataclass
class FakeDownloadStream:
    data: bytes

    async def read(self) -> bytes:
        return self.data


class FakeGridFSBucket:
    def __init__(self) -> None:
        self._storage: dict[ObjectId, bytes] = {}

    async def upload_from_stream(self, filename: str, stream: BytesIO, metadata: dict[str, Any]) -> ObjectId:
        data = stream.read()
        file_id = ObjectId()
        self._storage[file_id] = data
        return file_id

    async def open_download_stream(self, file_id: ObjectId) -> FakeDownloadStream:
        if file_id not in self._storage:
            raise KeyError("Unknown file id")
        return FakeDownloadStream(self._storage[file_id])


class FakeAsyncCursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._documents = documents

    def __aiter__(self):
        self._iterator = iter(self._documents)
        return self

    async def __anext__(self):
        try:
            return next(self._iterator)
        except StopIteration as exc:  # pragma: no cover - standard async iteration ending
            raise StopAsyncIteration from exc


class FakeCollection:
    def __init__(self) -> None:
        self.docs: list[dict[str, Any]] = []

    async def insert_one(self, doc: dict[str, Any]) -> None:
        self.docs.append(doc.copy())

    def find(self, query: dict[str, Any]) -> FakeAsyncCursor:
        matched = [doc.copy() for doc in self.docs if all(doc.get(k) == v for k, v in query.items())]
        return FakeAsyncCursor(matched)

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc.copy()
        return None

    async def update_one(self, query: dict[str, Any], update: dict[str, Any], upsert: bool = False) -> None:
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(update.get("$set", {}))
                return
        if upsert:
            new_doc = query.copy()
            new_doc.update(update.get("$set", {}))
            self.docs.append(new_doc)


class FakeDatabase:
    def __init__(self) -> None:
        self.pdf_metadata = FakeCollection()
        self.pdf_texts = FakeCollection()


class DummyUploadFile:
    def __init__(self, filename: str, content_type: str, data: bytes) -> None:
        self.filename = filename
        self.content_type = content_type
        self._data = data

    async def read(self) -> bytes:
        return self._data


@pytest.fixture()
def pdf_service_setup():
    fake_db = FakeDatabase()
    fake_grid = FakeGridFSBucket()
    service = PDFService(fake_db, fake_grid)
    return service, fake_db, fake_grid


def _make_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buffer = BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    return buffer.read()


@pytest.mark.asyncio
async def test_upload_pdf_rejects_non_pdf(pdf_service_setup):
    service, _, _ = pdf_service_setup
    fake_file = DummyUploadFile(filename="notes.txt", content_type="text/plain", data=b"hello")

    with pytest.raises(HTTPException) as exc:
        await service.upload_pdf(fake_file, user_id=1)

    assert exc.value.status_code == 400
    assert "Only PDF files are allowed" in exc.value.detail


@pytest.mark.asyncio
async def test_upload_and_parse_pdf(pdf_service_setup):
    service, fake_db, _ = pdf_service_setup
    pdf_bytes = _make_pdf_bytes()
    fake_file = DummyUploadFile(filename="document.pdf", content_type="application/pdf", data=pdf_bytes)

    metadata = await service.upload_pdf(fake_file, user_id=1)

    assert metadata.filename == "document.pdf"
    assert metadata.is_parsed is False
    assert metadata.upload_date <= datetime.now(timezone.utc)

    text = await service.parse_pdf(metadata.pdf_id, user_id=1)

    assert isinstance(text, str)
    stored_metadata = await fake_db.pdf_metadata.find_one({"pdf_id": metadata.pdf_id, "user_id": 1})
    assert stored_metadata is not None
    assert stored_metadata.get("user_id") == 1
    assert stored_metadata.get("is_parsed") is True
    stored_text = await fake_db.pdf_texts.find_one({"pdf_id": metadata.pdf_id, "user_id": 1})
    assert stored_text is not None
    assert stored_text.get("text") == text
