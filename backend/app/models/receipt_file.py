from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReceiptFile(Base):
    __tablename__ = "receipt_files"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    company = relationship("Company", back_populates="receipts")
    employee = relationship("User", back_populates="uploaded_receipts")
    claim = relationship("ExpenseClaim", back_populates="receipt_file", uselist=False)
    ocr_extractions = relationship("OCRExtraction", back_populates="receipt_file")