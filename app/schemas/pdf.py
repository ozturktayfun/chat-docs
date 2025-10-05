from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PDFMetadata(BaseModel):
    pdf_id: str
    filename: str
    upload_date: datetime
    is_parsed: bool = False


class PDFParseRequest(BaseModel):
    pdf_id: str = Field(..., description="MongoDB ObjectId of the PDF")


class PDFSelectRequest(BaseModel):
    pdf_id: str = Field(..., description="MongoDB ObjectId of the PDF to select")
