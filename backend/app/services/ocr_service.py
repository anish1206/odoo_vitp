from __future__ import annotations

import base64
import json
import mimetypes
import re
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.core.config import settings

CURRENCY_SYMBOL_TO_CODE = {
    "$": "USD",
    "USD": "USD",
    "EUR": "EUR",
    "GBP": "GBP",
    "AED": "AED",
    "INR": "INR",
    "JPY": "JPY",
}

SUPPORTED_CURRENCIES = {"USD", "INR", "EUR", "GBP", "AED", "SGD", "JPY", "AUD", "CAD"}

GEMINI_ENGINE = "gemini-vision"
FALLBACK_ENGINE = "heuristic-fallback"

GEMINI_PROMPT = """Extract structured fields from this expense receipt.
Return JSON only (no markdown) using this exact schema:
{
  \"merchant_name\": string | null,
  \"date\": \"YYYY-MM-DD\" | null,
  \"currency\": \"USD|INR|EUR|GBP|AED|SGD|JPY|AUD|CAD\" | null,
  \"amount\": number | null,
  \"raw_text\": string | null,
  \"confidence\": number | null
}

Rules:
- amount must be the final payable/total amount.
- date must be normalized to YYYY-MM-DD.
- currency must be one of the allowed 3-letter codes.
- confidence must be between 0 and 1.
"""

AMOUNT_PATTERN = re.compile(
    r"(?:(?P<currency>[A-Z]{3}|USD|EUR|GBP|AED)\s*)?(?P<amount>\d{1,7}(?:\.\d{1,2})?)",
    flags=re.IGNORECASE,
)
AMOUNT_KEYWORD_PATTERN = re.compile(
    r"(?:amount|total)\s*[:=-]?\s*(?:[A-Z]{3}\s*)?(?P<amount>\d{1,7}(?:\.\d{1,2})?)",
    flags=re.IGNORECASE,
)
DATE_ISO_PATTERN = re.compile(r"\b(?P<date>\d{4}-\d{2}-\d{2})\b")
DATE_SLASH_PATTERN = re.compile(r"\b(?P<date>\d{2}/\d{2}/\d{4})\b")
MERCHANT_PATTERN = re.compile(r"merchant\s*[:=-]\s*(?P<merchant>[^\n\r]+)", flags=re.IGNORECASE)


@dataclass(frozen=True)
class OCRExtractionResult:
    raw_text: str | None
    parsed_fields: dict[str, object] | None
    confidence: float | None
    engine: str


def _guess_mime_type(path: Path) -> str:
    detected, _ = mimetypes.guess_type(path.name)
    return detected or "application/octet-stream"


def _safe_float(value: object) -> float | None:
    def _parse_number_text(number_text: str) -> float | None:
        token = number_text.strip()
        token = re.sub(r"[^0-9,.-]", "", token)
        if not token:
            return None

        token = token.replace(" ", "")

        has_comma = "," in token
        has_dot = "." in token

        if has_comma and has_dot:
            # If comma appears after dot, assume decimal comma format: 1.234,56 -> 1234.56
            if token.rfind(",") > token.rfind("."):
                token = token.replace(".", "")
                token = token.replace(",", ".")
            else:
                # Decimal point format: 1,234.56 -> 1234.56
                token = token.replace(",", "")
        elif has_comma:
            # Distinguish decimal comma from grouping comma.
            if token.count(",") == 1 and len(token.split(",")[-1]) in (1, 2):
                token = token.replace(",", ".")
            else:
                token = token.replace(",", "")

        # Keep only one leading minus if present.
        if token.count("-") > 1:
            token = token.replace("-", "")

        try:
            return float(token)
        except ValueError:
            return None

    if isinstance(value, (int, float)):
        parsed = float(value)
        return parsed if parsed > 0 else None

    if isinstance(value, str):
        parsed = _parse_number_text(value)
        return parsed if parsed is not None and parsed > 0 else None

    return None


def _normalize_currency(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    candidate = value.strip().upper()
    if not candidate:
        return None

    if candidate in CURRENCY_SYMBOL_TO_CODE:
        candidate = CURRENCY_SYMBOL_TO_CODE[candidate]

    if candidate in SUPPORTED_CURRENCIES:
        return candidate

    symbol_match = re.search(r"(USD|INR|EUR|GBP|AED|SGD|JPY|AUD|CAD)", candidate)
    if symbol_match:
        return symbol_match.group(1)

    return None


def _to_iso_date(date_text: str) -> str:
    if "-" in date_text:
        return date_text

    day, month, year = date_text.split("/")
    return f"{year}-{month}-{day}"


def _normalize_date(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    candidate = value.strip()
    if not candidate:
        return None

    iso_match = DATE_ISO_PATTERN.search(candidate)
    if iso_match:
        return _to_iso_date(iso_match.group("date"))

    slash_match = DATE_SLASH_PATTERN.search(candidate)
    if slash_match:
        return _to_iso_date(slash_match.group("date"))

    alt_match = re.search(r"\b(?P<date>\d{2}-\d{2}-\d{4})\b", candidate)
    if alt_match:
        day, month, year = alt_match.group("date").split("-")
        return f"{year}-{month}-{day}"

    return None


def _extract_json_candidate(text: str) -> dict[str, object] | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        payload = json.loads(cleaned)
        return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        payload = json.loads(cleaned[start : end + 1])
        return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        return None


def _extract_total_from_text(raw_text: str) -> float | None:
    total_patterns = [
        re.compile(
            r"(?:grand\s*total|total\s*amount|amount\s*due|net\s*payable|amount\s*payable|total)\s*[:=-]?\s*(?:[A-Z]{3}|USD|INR|EUR|GBP|AED|SGD|JPY|AUD|CAD|[$€£])?\s*(?P<value>[0-9][0-9,\.\-]*)",
            flags=re.IGNORECASE,
        ),
        re.compile(
            r"(?:[A-Z]{3}|USD|INR|EUR|GBP|AED|SGD|JPY|AUD|CAD|[$€£])\s*(?P<value>[0-9][0-9,\.\-]*)\s*(?:total|grand\s*total)",
            flags=re.IGNORECASE,
        ),
    ]

    matches: list[float] = []
    for pattern in total_patterns:
        for match in pattern.finditer(raw_text):
            parsed = _safe_float(match.group("value"))
            if parsed is not None:
                matches.append(parsed)

    if not matches:
        return None

    # Multiple totals can appear (subtotal + total). Prefer the largest positive total.
    return max(matches)


def _extract_text_for_fallback(raw_bytes: bytes) -> str:
    return raw_bytes[:250_000].decode("utf-8", errors="ignore").strip()


def _extract_currency(raw_text: str) -> str | None:
    uppercase_text = raw_text.upper()
    for symbol, code in CURRENCY_SYMBOL_TO_CODE.items():
        if symbol in uppercase_text:
            return code

    currency_match = re.search(r"\b(USD|INR|EUR|GBP|AED|SGD|JPY|AUD|CAD)\b", uppercase_text)
    if currency_match:
        return currency_match.group(1)

    return None


def _extract_amount(raw_text: str) -> float | None:
    keyword_match = AMOUNT_KEYWORD_PATTERN.search(raw_text)
    if keyword_match:
        try:
            keyword_value = float(keyword_match.group("amount"))
        except (TypeError, ValueError):
            keyword_value = 0

        if keyword_value > 0:
            return keyword_value

    candidates: list[float] = []
    decimal_candidates: list[float] = []
    for amount_match in AMOUNT_PATTERN.finditer(raw_text):
        try:
            value = float(amount_match.group("amount"))
        except (TypeError, ValueError):
            continue

        if value > 0:
            candidates.append(value)
            if "." in amount_match.group("amount"):
                decimal_candidates.append(value)

    if decimal_candidates:
        return max(decimal_candidates)

    if not candidates:
        return None

    return max(candidates)


def _heuristic_extract(decoded: str) -> OCRExtractionResult:
    if not decoded:
        return OCRExtractionResult(
            raw_text=None,
            parsed_fields=None,
            confidence=0.15,
            engine=FALLBACK_ENGINE,
        )

    parsed_fields: dict[str, object] = {}

    merchant_match = MERCHANT_PATTERN.search(decoded)
    if merchant_match:
        parsed_fields["merchant_name"] = merchant_match.group("merchant").strip()
    else:
        first_line = decoded.splitlines()[0].strip() if decoded.splitlines() else ""
        if first_line and len(first_line) <= 80:
            parsed_fields["merchant_name"] = first_line

    amount = _extract_amount(decoded)
    if amount is not None:
        parsed_fields["amount"] = amount

    currency = _extract_currency(decoded)
    if currency is not None:
        parsed_fields["currency"] = currency

    date_match = DATE_ISO_PATTERN.search(decoded)
    if date_match:
        parsed_fields["date"] = _to_iso_date(date_match.group("date"))
    else:
        slash_match = DATE_SLASH_PATTERN.search(decoded)
        if slash_match:
            parsed_fields["date"] = _to_iso_date(slash_match.group("date"))

    confidence = 0.25
    if parsed_fields:
        confidence = min(0.92, 0.35 + (0.15 * len(parsed_fields)))

    return OCRExtractionResult(
        raw_text=decoded[:4000],
        parsed_fields=parsed_fields or None,
        confidence=confidence,
        engine=FALLBACK_ENGINE,
    )


def _gemini_extract(raw_bytes: bytes, mime_type: str) -> OCRExtractionResult | None:
    api_key = (settings.gemini_api_key or "").strip()
    if not api_key:
        return OCRExtractionResult(
            raw_text="Gemini API key not configured",
            parsed_fields=None,
            confidence=0.0,
            engine="gemini-no-key",
        )

    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    )

    inline_data_b64 = base64.b64encode(raw_bytes).decode("ascii")

    request_payloads = [
        {
            "contents": [
                {
                    "parts": [
                        {"text": GEMINI_PROMPT},
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": inline_data_b64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
            },
        },
        {
            "contents": [
                {
                    "parts": [
                        {"text": GEMINI_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": inline_data_b64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
            },
        },
    ]

    response_json: dict[str, object] | None = None
    last_http_error: str | None = None
    for request_payload in request_payloads:
        for attempt in range(3):
            try:
                response = httpx.post(
                    endpoint,
                    params={"key": api_key},
                    json=request_payload,
                    timeout=settings.gemini_ocr_timeout_seconds,
                )
                response.raise_for_status()
                response_json = response.json()
                break
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                last_http_error = f"HTTP {status_code}"
                if status_code == 429 and attempt < 2:
                    time.sleep(1.0 * (2**attempt))
                    continue
                break
            except httpx.HTTPError as exc:
                last_http_error = str(exc)
                break
            except json.JSONDecodeError:
                last_http_error = "Non-JSON response"
                break

        if response_json is not None:
            break

    if response_json is None:
        return OCRExtractionResult(
            raw_text=last_http_error,
            parsed_fields=None,
            confidence=0.0,
            engine="gemini-http-error",
        )

    candidates = response_json.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return OCRExtractionResult(
            raw_text="Gemini returned no candidates",
            parsed_fields=None,
            confidence=0.0,
            engine="gemini-empty-response",
        )

    content = candidates[0].get("content", {})
    parts = content.get("parts", []) if isinstance(content, dict) else []
    text_part = None
    for part in parts:
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            text_part = part["text"]
            break

    if not text_part:
        return OCRExtractionResult(
            raw_text="Gemini response missing text part",
            parsed_fields=None,
            confidence=0.0,
            engine="gemini-empty-response",
        )

    parsed = _extract_json_candidate(text_part)
    if parsed is None:
        return OCRExtractionResult(
            raw_text=text_part[:4000],
            parsed_fields=None,
            confidence=0.0,
            engine="gemini-non-json-response",
        )

    parsed_fields: dict[str, object] = {}

    merchant_name = parsed.get("merchant_name")
    if isinstance(merchant_name, str) and merchant_name.strip():
        parsed_fields["merchant_name"] = merchant_name.strip()[:120]

    amount = _safe_float(parsed.get("amount"))
    if amount is not None:
        parsed_fields["amount"] = amount

    currency = _normalize_currency(parsed.get("currency"))
    if currency is not None:
        parsed_fields["currency"] = currency

    date_text = _normalize_date(parsed.get("date"))
    if date_text is not None:
        parsed_fields["date"] = date_text

    confidence = parsed.get("confidence")
    if isinstance(confidence, (int, float)):
        normalized_confidence = max(0.0, min(1.0, float(confidence)))
    else:
        normalized_confidence = min(0.95, 0.55 + (0.1 * len(parsed_fields))) if parsed_fields else 0.3

    raw_text = parsed.get("raw_text")
    normalized_raw_text = raw_text[:4000] if isinstance(raw_text, str) and raw_text.strip() else None

    if normalized_raw_text:
        total_from_text = _extract_total_from_text(normalized_raw_text)
        if total_from_text is not None and (
            amount is None
            or abs(total_from_text - amount) / max(total_from_text, 1.0) > 0.03
        ):
            parsed_fields["amount"] = total_from_text

    return OCRExtractionResult(
        raw_text=normalized_raw_text,
        parsed_fields=parsed_fields or None,
        confidence=normalized_confidence,
        engine=GEMINI_ENGINE,
    )


def extract_receipt_data(file_path: str | Path) -> OCRExtractionResult:
    path = Path(file_path)
    raw_bytes = path.read_bytes()
    mime_type = _guess_mime_type(path)

    if mime_type == "text/plain":
        return _heuristic_extract(_extract_text_for_fallback(raw_bytes))

    gemini_result = _gemini_extract(raw_bytes, mime_type)
    if gemini_result is not None:
        return gemini_result

    # For binary/image files, avoid parsing random bytes as text when Gemini is unavailable.
    return OCRExtractionResult(
        raw_text=None,
        parsed_fields=None,
        confidence=0.1,
        engine="gemini-unavailable",
    )
