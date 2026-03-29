from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models import OCRExtraction, ReceiptFile, User, UserRole
from app.schemas.receipt import OCRExtractionOut, ReceiptFileOut, ReceiptUploadResponse
from app.services.ocr_service import extract_receipt_data

router = APIRouter(prefix="/receipts", tags=["receipts"])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/bmp",
    "text/plain",
}
MAX_RECEIPT_SIZE_BYTES = 10 * 1024 * 1024


def _sanitize_filename(filename: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    return sanitized[:120] or "receipt"


def _receipt_to_out(receipt: ReceiptFile) -> ReceiptFileOut:
    return ReceiptFileOut(
        id=receipt.id,
        company_id=receipt.company_id,
        employee_id=receipt.employee_id,
        file_path=receipt.file_path,
        original_filename=receipt.original_filename,
        file_mime_type=receipt.file_mime_type,
        file_size_bytes=receipt.file_size_bytes,
        uploaded_at=receipt.uploaded_at,
    )


def _ocr_to_out(extraction: OCRExtraction) -> OCRExtractionOut:
    return OCRExtractionOut(
        id=extraction.id,
        receipt_file_id=extraction.receipt_file_id,
        raw_text=extraction.raw_text,
        parsed_fields=extraction.parsed_fields,
        confidence=extraction.confidence,
        engine=extraction.engine,
        created_at=extraction.created_at,
    )


def _assert_can_access_receipt(receipt: ReceiptFile, current_user: User) -> None:
    if receipt.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

    if (
        receipt.employee_id != current_user.id
        and current_user.role != UserRole.ADMIN
        and not current_user.is_approver
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this receipt",
        )


@router.post("", response_model=ReceiptUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing file name")

    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_MIME_TYPES and not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported receipt file type",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    if len(file_bytes) > MAX_RECEIPT_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Receipt file is too large (max 10 MB)",
        )

    uploads_root = Path(settings.uploads_dir)
    receipt_dir = uploads_root / str(current_user.company_id) / str(current_user.id)
    receipt_dir.mkdir(parents=True, exist_ok=True)

    sanitized_name = _sanitize_filename(file.filename)
    stored_name = f"{uuid4().hex}_{sanitized_name}"
    stored_path = receipt_dir / stored_name
    stored_path.write_bytes(file_bytes)

    receipt = ReceiptFile(
        company_id=current_user.company_id,
        employee_id=current_user.id,
        file_path=str(stored_path),
        original_filename=file.filename,
        file_mime_type=content_type,
        file_size_bytes=len(file_bytes),
    )
    db.add(receipt)
    db.flush()

    ocr_result = extract_receipt_data(stored_path)
    extraction = OCRExtraction(
        receipt_file_id=receipt.id,
        raw_text=ocr_result.raw_text,
        parsed_fields=ocr_result.parsed_fields,
        confidence=ocr_result.confidence,
        engine=ocr_result.engine,
    )
    db.add(extraction)

    db.commit()
    db.refresh(receipt)
    db.refresh(extraction)

    return ReceiptUploadResponse(
        receipt_file_id=receipt.id,
        receipt=_receipt_to_out(receipt),
        ocr_extraction=_ocr_to_out(extraction),
    )


@router.get("/{receipt_id}", response_model=ReceiptFileOut)
def get_receipt_metadata(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    receipt = db.scalar(select(ReceiptFile).where(ReceiptFile.id == receipt_id))
    if receipt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

    _assert_can_access_receipt(receipt, current_user)
    return _receipt_to_out(receipt)


@router.get("/{receipt_id}/ocr", response_model=OCRExtractionOut)
def get_receipt_ocr_result(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    receipt = db.scalar(select(ReceiptFile).where(ReceiptFile.id == receipt_id))
    if receipt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

    _assert_can_access_receipt(receipt, current_user)

    extraction = db.scalar(
        select(OCRExtraction)
        .where(OCRExtraction.receipt_file_id == receipt_id)
        .order_by(OCRExtraction.created_at.desc(), OCRExtraction.id.desc())
    )
    if extraction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OCR result not available yet",
        )

    return _ocr_to_out(extraction)
