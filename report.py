import logging
from datetime import datetime
from typing import Optional

from config import BYBIT_SYMBOL, BYBIT_CATEGORY
from bybit_api import BybitAPIError, fetch_bybit_ticker

logger = logging.getLogger(__name__)


def _fmt_usd(value: float) -> str:
    return f"${value:,.0f}"


def generate_liquidation_report() -> Optional[str]:
    """
    Pobiera dane rynkowe z publicznego API Bybit i buduje krótki raport
    tekstowy (cena, zmiana 24h, wolumen, open interest, funding).
    Zwraca None, jeśli wystąpi błąd – w takim przypadku
    agent dalej działa (wysyła sam screenshot).
    """
    try:
        ticker = fetch_bybit_ticker()
    except BybitAPIError as e:
        logger.warning("Nie udało się pobrać danych z Bybit API: %s", e)
        return None

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    symbol = ticker.get("symbol", BYBIT_SYMBOL)

    last_price = float(ticker.get("lastPrice") or 0.0)
    change_24h = float(ticker.get("price24hPcnt") or 0.0) * 100  # Bybit zwraca w ułamku (np. 0.0123)
    high_24h = float(ticker.get("highPrice24h") or 0.0)
    low_24h = float(ticker.get("lowPrice24h") or 0.0)
    vol_24h = float(ticker.get("volume24h") or 0.0)
    turnover_24h = float(ticker.get("turnover24h") or 0.0)
    oi = float(ticker.get("openInterest") or 0.0)
    funding_rate = float(ticker.get("fundingRate") or 0.0)

    lines: list[str] = []
    lines.append(f"Raport Bybit {symbol} ({BYBIT_CATEGORY})")
    lines.append(f"Czas generacji: {now_str}")
    lines.append("")
    lines.append(f"Aktualna cena: {_fmt_usd(last_price)}")
    lines.append(f"Zmiana 24h: {change_24h:+.2f}%")
    lines.append(f"Zakres 24h: {_fmt_usd(low_24h)} – {_fmt_usd(high_24h)}")
    lines.append(f"Wolumen 24h (kontrakty): {vol_24h:,.0f}")
    lines.append(f"Obrót 24h (USD, przybliżony): {_fmt_usd(turnover_24h)}")
    lines.append(f"Open interest: {oi:,.0f}")
    lines.append(f"Funding rate: {funding_rate:.6f}")

    return "\n".join(lines)


def build_telegram_caption(base_caption: str, report: Optional[str]) -> str:
    """
    Skraca raport do krótkiego opisu pod obrazkiem (Telegram ma limit długości podpisu).
    """
    if not report:
        return base_caption

    # Weź 2–3 pierwsze linie z raportu, żeby nie „zalać” podpisu.
    report_lines = report.splitlines()
    extra = [ln for ln in report_lines if ln.strip()][:3]
    short = base_caption
    if extra:
        short += "\n" + "\n".join(extra)
    # Telegram caption limit ~1024 znaków – utnij dla pewności.
    if len(short) > 900:
        short = short[:897] + "..."
    return short

