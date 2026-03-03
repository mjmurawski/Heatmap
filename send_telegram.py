"""Wysyłka screenshotu na Telegram (Bot API)."""
import logging
from pathlib import Path
from datetime import datetime
from typing import Iterable, Sequence
import json

import requests

from config import SEND_TELEGRAM, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

TELEGRAM_SEND_PHOTO_API = "https://api.telegram.org/bot{token}/sendPhoto"
TELEGRAM_MEDIA_GROUP_API = "https://api.telegram.org/bot{token}/sendMediaGroup"


def send_screenshot_telegram(
    image_paths: Sequence[Path] | Path,
    caption: str | None = None,
) -> bool:
    """
    Wysyła jeden lub wiele screenshotów na Telegram.

    - Jeśli podana jest pojedyncza ścieżka, używa sendPhoto.
    - Jeśli lista ≥ 2 ścieżek, używa sendMediaGroup (caption tylko przy pierwszym).

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

    # Ujednolicenie: zawsze traktuj wejście jako listę ścieżek.
    if isinstance(image_paths, Path):
        paths: Iterable[Path] = [image_paths]
    else:
        paths = list(image_paths)

    paths_list = list(paths)
    if not paths_list:
        logger.warning("Brak ścieżek obrazów do wysłania na Telegram.")
        return False

    # Przypadek 1: jedno zdjęcie – klasyczne sendPhoto.
    if len(paths_list) == 1:
        image_path = paths_list[0]
        url = TELEGRAM_SEND_PHOTO_API.format(token=TELEGRAM_BOT_TOKEN)
        try:
            with open(image_path, "rb") as f:
                files = {"photo": (image_path.name, f, "image/png")}
                data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
                r = requests.post(url, data=data, files=files, timeout=30)
            r.raise_for_status()
            logger.info("Screenshot wysłany na Telegram (sendPhoto).")
            return True
        except (requests.RequestException, OSError) as e:
            logger.exception("Błąd wysyłki na Telegram (sendPhoto): %s", e)
            return False

    # Przypadek 2: wiele zdjęć – sendMediaGroup.
    url = TELEGRAM_MEDIA_GROUP_API.format(token=TELEGRAM_BOT_TOKEN)
    media = []
    files = {}
    for idx, path in enumerate(paths_list):
        attach_name = f"file{idx}"
        media_item = {
            "type": "photo",
            "media": f"attach://{attach_name}",
        }
        if idx == 0 and caption:
            media_item["caption"] = caption
        media.append(media_item)
        try:
            files[attach_name] = (path.name, open(path, "rb"), "image/png")
        except OSError as e:
            logger.error("Nie można odczytać pliku screenshot: %s", e)
            # Zamknij już otwarte pliki.
            for _, fh in files.values():
                try:
                    fh.close()
                except Exception:
                    pass
            return False

    data = {"chat_id": TELEGRAM_CHAT_ID, "media": json.dumps(media)}

    try:
        r = requests.post(url, data=data, files=files, timeout=30)
        r.raise_for_status()
        logger.info("Screenshoty wysłane na Telegram (sendMediaGroup).")
        return True
    except (requests.RequestException, OSError) as e:
        logger.exception("Błąd wysyłki na Telegram (sendMediaGroup): %s", e)
        return False
    finally:
        # files ma strukturę: {attach_name: (filename, fh, mime_type)}
        for _attach_name, (_filename, fh, _mime) in files.items():
            try:
                fh.close()
            except Exception:
                pass
