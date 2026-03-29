from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import settings


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


def _normalize_currency(code: str) -> str:
    return code.strip().upper()


def _parse_as_of(payload: dict) -> datetime:
    timestamp = payload.get("timestamp")
    if isinstance(timestamp, int | float):
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    raw_date = payload.get("date")
    if isinstance(raw_date, str):
        try:
            return datetime.fromisoformat(f"{raw_date}T00:00:00+00:00")
        except ValueError:
            return datetime.now(timezone.utc)

    return datetime.now(timezone.utc)


def _static_cross_rate(base_currency: str, foreign_currency: str) -> Decimal:
    if base_currency == foreign_currency:
        return Decimal("1")

    if base_currency not in USD_TO_CURRENCY or foreign_currency not in USD_TO_CURRENCY:
        raise ValueError("Exchange rate unavailable for the provided currency pair")

    # Cross-rate derived from static USD anchor rates.
    return (USD_TO_CURRENCY[base_currency] / USD_TO_CURRENCY[foreign_currency]).quantize(
        Decimal("0.000001"),
        rounding=ROUND_HALF_UP,
    )


def _live_cross_rate(base_currency: str, foreign_currency: str) -> tuple[Decimal, datetime]:
    query = urlencode({"base": foreign_currency, "symbols": base_currency})
    url = f"{settings.currency_api_url}?{query}"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "ReimburseFlow/1.0"})

    with urlopen(request, timeout=settings.currency_timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))

    rates = payload.get("rates")
    if not isinstance(rates, dict):
        raise ValueError("Invalid exchange rate response")

    live_rate = rates.get(base_currency)
    if not isinstance(live_rate, int | float):
        raise ValueError("Missing exchange rate for requested pair")

    return Decimal(str(live_rate)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP), _parse_as_of(payload)


def preview_conversion(
    *,
    base_currency: str,
    foreign_currency: str,
    amount: float,
) -> CurrencyConversionPreview:
    normalized_base = _normalize_currency(base_currency)
    normalized_foreign = _normalize_currency(foreign_currency)

    if amount <= 0:
        raise ValueError("Amount must be greater than 0")

    provider_mode = settings.currency_provider.strip().lower()
    provider = "static-demo-rates"
    as_of = datetime.now(timezone.utc)

    if provider_mode == "static":
        rate = _static_cross_rate(normalized_base, normalized_foreign)
    else:
        try:
            rate, as_of = _live_cross_rate(normalized_base, normalized_foreign)
            provider = "live-exchangerate-host"
        except (ValueError, URLError, TimeoutError):
            rate = _static_cross_rate(normalized_base, normalized_foreign)
            provider = "static-demo-rates-fallback"
            as_of = datetime.now(timezone.utc)

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
        provider=provider,
        as_of=as_of,
    )
