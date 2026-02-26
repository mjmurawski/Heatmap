"""Wysyłka screenshotu na Telegram (Bot API)."""
import logging
from pathlib import Path
from datetime import datetime

import requests

from config import SEND_TELEGRAM, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendPhoto"


def send_screenshot_telegram(image_path: Path, caption: str | None = None) -> bool:
    """
    Wysyła zdjęcie do czatu Telegram przez Bot API.
    Wymaga: SEND_TELEGRAM=true, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID w .env.
    """
    if not SEND_TELEGRAM:
        logger.info("SEND_TELEGRAM=false, pomijam wysyłkę na Telegram.")
        return True

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Brak TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID — pomijam Telegram.")
        return False

    if caption is None:
        caption = f"CoinGlass BTC Liquidation Heatmap – {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    url = TELEGRAM_API.format(token=TELEGRAM_BOT_TOKEN)

    try:
        with open(image_path, "rb") as f:
            files = {"photo": (image_path.name, f, "image/png")}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
            r = requests.post(url, data=data, files=files, timeout=30)
        r.raise_for_status()
        logger.info("Screenshot wysłany na Telegram.")
        return True
    except (requests.RequestException, OSError) as e:
        logger.exception("Błąd wysyłki na Telegram: %s", e)
        return False
