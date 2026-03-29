from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExchangeRateSnapshot(Base):
    __tablename__ = "exchange_rate_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    foreign_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(14, 6), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    claims = relationship("ExpenseClaim", back_populates="exchange_rate_snapshot")