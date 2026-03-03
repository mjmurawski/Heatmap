import logging
from typing import Any, Dict, List, Optional

import requests

from config import (
    COINGLASS_API_KEY,
    COINGLASS_SYMBOL,
    COINGLASS_EXCHANGES,
    COINGLASS_EXCHANGE_RANGE,
    COINGLASS_HISTORY_INTERVAL,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://open-api-v4.coinglass.com"


class CoinglassAPIError(Exception):
    pass


def _get_headers() -> Dict[str, str]:
    if not COINGLASS_API_KEY:
        raise CoinglassAPIError("Brak COINGLASS_API_KEY – ustaw w pliku .env, aby korzystać z API CoinGlass.")
    return {"CG-API-KEY": COINGLASS_API_KEY}


def fetch_liquidation_exchange_list(
    symbol: Optional[str] = None,
    range_: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    /api/futures/liquidation/exchange-list

    Zwraca listę słowników z polami:
      exchange, liquidation_usd, long_liquidation_usd, short_liquidation_usd.
    """
    headers = _get_headers()
    params: Dict[str, Any] = {
        "symbol": symbol or COINGLASS_SYMBOL,
        "range": range_ or COINGLASS_EXCHANGE_RANGE,
    }
    url = f"{BASE_URL}/api/futures/liquidation/exchange-list"
    logger.info("Pobieram liquidation exchange-list z CoinGlass API: %s params=%s", url, params)
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
    except requests.RequestException as e:
        raise CoinglassAPIError(f"Błąd HTTP przy pobieraniu exchange-list: {e}") from e

    data = r.json()
    if str(data.get("code")) != "0":
        raise CoinglassAPIError(f"Błąd API exchange-list: {data}")

    return data.get("data", []) or []


def fetch_aggregated_liquidation_history(
    symbol: Optional[str] = None,
    exchanges: Optional[str] = None,
    interval: Optional[str] = None,
    limit: int = 30,
) -> List[Dict[str, Any]]:
    """
    /api/futures/liquidation/aggregated-history

    Zwraca listę słowników z polami:
      time, aggregated_long_liquidation_usd, aggregated_short_liquidation_usd.
    """
    headers = _get_headers()
    params: Dict[str, Any] = {
        "exchange_list": exchanges or COINGLASS_EXCHANGES,
        "symbol": symbol or COINGLASS_SYMBOL,
        "interval": interval or COINGLASS_HISTORY_INTERVAL,
        "limit": limit,
    }
    url = f"{BASE_URL}/api/futures/liquidation/aggregated-history"
    logger.info("Pobieram aggregated-liquidation-history z CoinGlass API: %s params=%s", url, params)
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
    except requests.RequestException as e:
        raise CoinglassAPIError(f"Błąd HTTP przy pobieraniu aggregated-history: {e}") from e

    data = r.json()
    if str(data.get("code")) != "0":
        raise CoinglassAPIError(f"Błąd API aggregated-history: {data}")

    return data.get("data", []) or []

