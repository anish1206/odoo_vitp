COUNTRY_TO_CURRENCY: dict[str, str] = {
    "IN": "INR",
    "US": "USD",
    "GB": "GBP",
    "EU": "EUR",
    "DE": "EUR",
    "FR": "EUR",
    "IT": "EUR",
    "ES": "EUR",
    "AE": "AED",
    "SG": "SGD",
    "JP": "JPY",
    "AU": "AUD",
    "CA": "CAD",
}


def get_base_currency(country_code: str) -> str | None:
    normalized = country_code.strip().upper()
    return COUNTRY_TO_CURRENCY.get(normalized)
