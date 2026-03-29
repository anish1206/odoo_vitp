from app.core.country_currency import get_base_currency


def test_get_base_currency_known_country():
    assert get_base_currency("IN") == "INR"
    assert get_base_currency("US") == "USD"


def test_get_base_currency_normalizes_input():
    assert get_base_currency(" in ") == "INR"
    assert get_base_currency("gb") == "GBP"


def test_get_base_currency_unknown_country_returns_none():
    assert get_base_currency("ZZ") is None
