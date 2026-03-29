from datetime import datetime
from typing import Any

from pydantic import BaseModel


class OCRExtractionOut(BaseModel):
    id: int
    receipt_file_id: int
    raw_text: str | None
    parsed_fields: dict[str, Any] | None
    confidence: float | None
    engine: str | None
    created_at: datetime


class ReceiptFileOut(BaseModel):
    id: int
    company_id: int
    employee_id: int
    file_path: str
    original_filename: str
    file_mime_type: str
    file_size_bytes: int
    uploaded_at: datetime


class ReceiptUploadResponse(BaseModel):
    receipt_file_id: int
    receipt: ReceiptFileOut
    ocr_extraction: OCRExtractionOut | None
