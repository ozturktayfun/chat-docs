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
    return await pdf_service.upload_pdf(file, current_user.id)


@router.get("/pdf-list", response_model=list[PDFMetadata])
async def list_pdfs(
    current_user: User = Depends(get_authenticated_user),
    pdf_service: PDFService = Depends(get_pdf_service),
) -> list[PDFMetadata]:
    return await pdf_service.list_pdfs(current_user.id)


@router.post("/pdf-select")
async def select_pdf(
    payload: PDFSelectRequest,
    current_user: User = Depends(get_authenticated_user),
    pdf_service: PDFService = Depends(get_pdf_service),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    await pdf_service.ensure_pdf_owned_by_user(payload.pdf_id, current_user.id)
    user_record = db.get(User, current_user.id)
    if user_record is None:
        raise HTTPException(status_code=404, detail="User not found")
    user_record.selected_pdf_id = payload.pdf_id
    db.commit()
    db.refresh(user_record)
    return {"message": "PDF selected", "pdf_id": payload.pdf_id}


@router.post("/pdf-parse")
async def parse_pdf(
    payload: PDFParseRequest,
    current_user: User = Depends(get_authenticated_user),
    pdf_service: PDFService = Depends(get_pdf_service),
) -> dict[str, int | str | bool]:
    text = await pdf_service.parse_pdf(payload.pdf_id, current_user.id)
    return {"pdf_id": payload.pdf_id, "parsed": True, "text_length": len(text)}
