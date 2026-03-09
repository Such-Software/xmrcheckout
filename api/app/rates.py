from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import threading
import time
from typing import Any

import requests

KRAKEN_TICKER_URL = "https://api.kraken.com/0/public/Ticker"
KRAKEN_SOURCE = "kraken"
RATE_TTL_SECONDS = 60

# Kraken pair names for XMR against common fiat currencies
_KRAKEN_PAIRS: dict[str, str] = {
    "usd": "XXMRZUSD",
    "eur": "XXMRZEUR",
}


@dataclass(frozen=True)
class QuoteResult:
    rate: Decimal
    currency: str
    source: str
    quoted_at: datetime


_cache_lock = threading.Lock()
_cached_quote: QuoteResult | None = None
_cached_at: float | None = None


def get_xmr_rate(currency: str) -> QuoteResult:
    global _cached_quote, _cached_at
    normalized_currency = currency.strip().lower()

    pair = _KRAKEN_PAIRS.get(normalized_currency)
    if pair is None:
        raise ValueError(f"Unsupported fiat currency: {currency} (supported: {', '.join(_KRAKEN_PAIRS)})")

    with _cache_lock:
        if _cached_quote and _cached_at:
            if time.monotonic() - _cached_at < RATE_TTL_SECONDS:
                return _cached_quote

    response = requests.get(KRAKEN_TICKER_URL, params={"pair": pair}, timeout=5)
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    if data.get("error"):
        raise RuntimeError(f"Kraken API error: {data['error']}")
    result = data.get("result", {})
    ticker = result.get(pair, {})
    # 'c' is the last trade closed: [price, lot-volume]
    last_price = ticker.get("c", [None])[0]
    if last_price is None:
        raise ValueError("Could not get XMR rate from Kraken")
    rate = Decimal(str(last_price))
    quote = QuoteResult(
        rate=rate,
        currency=normalized_currency.upper(),
        source=KRAKEN_SOURCE,
        quoted_at=datetime.now(timezone.utc),
    )
    with _cache_lock:
        _cached_quote = quote
        _cached_at = time.monotonic()
    return quote
