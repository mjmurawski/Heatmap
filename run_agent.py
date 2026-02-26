#!/usr/bin/env python3
"""
Agent: wejście na CoinGlass Liquidation Heatmap → screenshot → wysyłka e-mail / Telegram.

Uruchomienie:
  python run_agent.py              — jeden raz
  python run_agent.py --every-hour — co godzinę w pętli (trzymaj okno otwarte)

Wymaga pliku .env (skopiuj z .env.example) z ustawieniem przynajmniej jednego kanału:
  SEND_EMAIL=true lub SEND_TELEGRAM=true.
"""
import argparse
import logging
import sys
import time
from pathlib import Path

from capture import capture_heatmap
from send_email import send_screenshot_email
from send_telegram import send_screenshot_telegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

INTERVAL_SECONDS = 3600  # 1 godzina


def run_once() -> int:
    """Jedno wykonanie: screenshot + wysyłka. Zwraca 0 = OK, 1 = błąd."""
    filepath = capture_heatmap()
    if not filepath or not Path(filepath).exists():
        logger.error("Nie udało się zrobić screenshotu.")
        return 1

    ok_email = send_screenshot_email(filepath)
    ok_telegram = send_screenshot_telegram(filepath)

    if not ok_email or not ok_telegram:
        if ok_email is False or ok_telegram is False:
            logger.warning("Jeden z kanałów wysyłki zwrócił błąd (sprawdź logi).")
    logger.info("Zakończono. Screenshot: %s", filepath)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CoinGlass Liquidation Heatmap – screenshot i wysyłka")
    parser.add_argument(
        "--every-hour",
        action="store_true",
        help="Wysyłaj heatmapę co godzinę w pętli (uruchom i zostaw włączone)",
    )
    args = parser.parse_args()

    if args.every_hour:
        logger.info("Tryb co godzinę włączony. Następna wysyłka za %s s.", INTERVAL_SECONDS)
        while True:
            run_once()
            logger.info("Odczekuję %s s do następnej wysyłki...", INTERVAL_SECONDS)
            time.sleep(INTERVAL_SECONDS)
    else:
        return run_once()


if __name__ == "__main__":
    sys.exit(main())
