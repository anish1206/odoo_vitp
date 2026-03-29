from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.models import User
from app.schemas.exchange_rate import ExchangeRatePreviewResponse
from app.services.currency_service import preview_conversion

router = APIRouter(prefix="/exchange_rates", tags=["exchange-rates"])


@router.get("/preview", response_model=ExchangeRatePreviewResponse)
def preview_exchange_rate(
    base_currency: str = Query(min_length=3, max_length=3),
    foreign_currency: str = Query(min_length=3, max_length=3),
    amount: float = Query(gt=0),
    current_user: User = Depends(get_current_user),
):
    del current_user

    try:
        preview = preview_conversion(
            base_currency=base_currency,
            foreign_currency=foreign_currency,
            amount=amount,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ExchangeRatePreviewResponse(
        base_currency=preview.base_currency,
        foreign_currency=preview.foreign_currency,
        amount=preview.amount,
        converted_amount=preview.converted_amount,
        rate=preview.rate,
        provider=preview.provider,
        as_of=preview.as_of,
    )
