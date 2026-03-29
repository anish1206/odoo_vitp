from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP


USD_TO_CURRENCY: dict[str, Decimal] = {
    "USD": Decimal("1"),
    "INR": Decimal("83.20"),
    "EUR": Decimal("0.92"),
    "GBP": Decimal("0.78"),
    "AED": Decimal("3.67"),
    "SGD": Decimal("1.35"),
    "JPY": Decimal("150.00"),
    "AUD": Decimal("1.50"),
    "CAD": Decimal("1.36"),
}


@dataclass(frozen=True)
class CurrencyConversionPreview:
    base_currency: str
    foreign_currency: str
    amount: float
    converted_amount: float
    rate: float
    provider: str
    as_of: datetime


def preview_conversion(
    *,
    base_currency: str,
    foreign_currency: str,
    amount: float,
) -> CurrencyConversionPreview:
    normalized_base = base_currency.strip().upper()
    normalized_foreign = foreign_currency.strip().upper()

    if amount <= 0:
        raise ValueError("Amount must be greater than 0")

    if normalized_base == normalized_foreign:
        rate = Decimal("1")
    else:
        if normalized_base not in USD_TO_CURRENCY or normalized_foreign not in USD_TO_CURRENCY:
            raise ValueError("Exchange rate unavailable for the provided currency pair")

        # Cross-rate derived from static USD anchor rates.
        rate = (USD_TO_CURRENCY[normalized_base] / USD_TO_CURRENCY[normalized_foreign]).quantize(
            Decimal("0.000001"),
            rounding=ROUND_HALF_UP,
        )

    converted = (Decimal(str(amount)) * rate).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return CurrencyConversionPreview(
        base_currency=normalized_base,
        foreign_currency=normalized_foreign,
        amount=float(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        converted_amount=float(converted),
        rate=float(rate),
        provider="static-demo-rates",
        as_of=datetime.now(timezone.utc),
    )
