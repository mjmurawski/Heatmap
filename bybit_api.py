import logging
from typing import Any, Dict, Optional

import requests

from config import BYBIT_SYMBOL, BYBIT_CATEGORY

logger = logging.getLogger(__name__)

BASE_URL = "https://api.bybit.com"
DEFAULT_HEADERS = {
    "User-Agent": "coinglass-liquidation-agent/1.0 (+https://github.com/mjmurawski/Heatmap)",
}


class BybitAPIError(Exception):
    pass


def fetch_bybit_ticker(
    symbol: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    GET /v5/market/tickers

    Publiczny endpoint Bybit – bez klucza API.
    Zwraca m.in.: lastPrice, price24hPcnt, highPrice24h, lowPrice24h,
    volume24h, turnover24h, openInterest, fundingRate itd.
    """
    symbol = symbol or BYBIT_SYMBOL
    category = category or BYBIT_CATEGORY

    url = f"{BASE_URL}/v5/market/tickers"
    params = {"category": category, "symbol": symbol}
    logger.info("Pobieram dane z Bybit ticker: %s params=%s", url, params)

    try:
        r = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=15)
        r.raise_for_status()
    except requests.RequestException as e:
        raise BybitAPIError(f"Błąd HTTP przy pobieraniu Bybit ticker: {e}") from e

    data = r.json()
    if str(data.get("retCode")) != "0":
        raise BybitAPIError(f"Błąd API Bybit ticker: {data}")

    result = data.get("result") or {}
    tickers = result.get("list") or []
    if not tickers:
        raise BybitAPIError("Brak danych w odpowiedzi Bybit ticker.")

    # Dla jednego symbolu bierzemy pierwszy element.
    return tickers[0]

