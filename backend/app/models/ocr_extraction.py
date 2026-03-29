from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OCRExtraction(Base):
    __tablename__ = "ocr_extractions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    receipt_file_id: Mapped[int] = mapped_column(ForeignKey("receipt_files.id"), index=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    engine: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    receipt_file = relationship("ReceiptFile", back_populates="ocr_extractions")