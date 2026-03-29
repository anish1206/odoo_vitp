from datetime import datetime

from pydantic import BaseModel


class ExchangeRatePreviewResponse(BaseModel):
    base_currency: str
    foreign_currency: str
    amount: float
    converted_amount: float
    rate: float
    provider: str
    as_of: datetime
