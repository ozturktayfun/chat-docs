from typing import cast

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_authenticated_user, get_pdf_service
from app.db.postgres import get_db
from app.models.user import User
from app.schemas import PDFMetadata, PDFParseRequest, PDFSelectRequest
from app.services.pdf_service import PDFService

router = APIRouter(tags=["pdf"])


@router.post("/pdf-upload", response_model=PDFMetadata, status_code=201)
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_authenticated_user),
    pdf_service: PDFService = Depends(get_pdf_service),
) -> PDFMetadata:
    """Store a PDF in GridFS and persist associated metadata."""
    user_id = cast(int, current_user.id)
    return await pdf_service.upload_pdf(file, user_id)


@router.get("/pdf-list", response_model=list[PDFMetadata])
async def list_pdfs(
    current_user: User = Depends(get_authenticated_user),
    pdf_service: PDFService = Depends(get_pdf_service),
) -> list[PDFMetadata]:
    """Return all PDF records owned by the authenticated user."""
    user_id = cast(int, current_user.id)
    return await pdf_service.list_pdfs(user_id)


@router.post("/pdf-select")
async def select_pdf(
    payload: PDFSelectRequest,
    current_user: User = Depends(get_authenticated_user),
    pdf_service: PDFService = Depends(get_pdf_service),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Mark a PDF as the user's active document for subsequent chats."""
    user_id = cast(int, current_user.id)
    await pdf_service.ensure_pdf_owned_by_user(payload.pdf_id, user_id)
    user_record = db.get(User, user_id)
    if user_record is None:
        raise HTTPException(status_code=404, detail="User not found")
    setattr(user_record, "selected_pdf_id", payload.pdf_id)
    db.commit()
    db.refresh(user_record)
    return {"message": "PDF selected", "pdf_id": payload.pdf_id}


@router.post("/pdf-parse")
async def parse_pdf(
    payload: PDFParseRequest,
    current_user: User = Depends(get_authenticated_user),
    pdf_service: PDFService = Depends(get_pdf_service),
) -> dict[str, int | str | bool]:
    """Trigger parsing for the selected PDF and report its text length."""
    user_id = cast(int, current_user.id)
    text = await pdf_service.parse_pdf(payload.pdf_id, user_id)
    return {"pdf_id": payload.pdf_id, "parsed": True, "text_length": len(text)}
