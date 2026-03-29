from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CompanyOut(BaseModel):
    id: int
    name: str
    country_code: str
    base_currency: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
