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
from report import generate_liquidation_report, build_telegram_caption
from analysis_agent import run_advanced_analysis
from config import HEATMAP_URL, LIQUIDATION_HEATMAP_URL, RUN_ADVANCED_ANALYSIS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

INTERVAL_SECONDS = 3600  # 1 godzina


def run_once() -> int:
    """Jedno wykonanie: screenshoty + raport z Bybit + wysyłka.
    Zwraca 0 = OK, 1 = błąd.
    """
    image_paths: list[Path] = []

    # 1) „Czysta” mapa likwidacji BTC z klasycznej strony (przycisk aparatu).
    btc_heatmap_path = capture_heatmap(url=LIQUIDATION_HEATMAP_URL)
    if not btc_heatmap_path or not Path(btc_heatmap_path).exists():
        logger.error("Nie udało się pobrać BTC heatmapy z klasycznej strony.")
        return 1
    image_paths.append(Path(btc_heatmap_path))

    # 2) Screenshot z dashboardu Hyperliquid (lub innego URL z HEATMAP_URL).
    hyperliquid_path = capture_heatmap(url=HEATMAP_URL)
    if not hyperliquid_path or not Path(hyperliquid_path).exists():
        logger.warning("Nie udało się zrobić screenshotu z HEATMAP_URL – pominę ten załącznik.")
    else:
        image_paths.append(Path(hyperliquid_path))

    # 3) Raport z Bybit – jeśli wystąpi błąd, funkcja zwróci None.
    basic_report = generate_liquidation_report()

    # 4) Opcjonalnie: zaawansowana analiza z użyciem obrazów + raportu liczbowego.
    # Jeśli Bybit nie zadziała (basic_report = None), nadal spróbuj analizy
    # opartej wyłącznie na obrazach, z jasną adnotacją w promptcie.
    report_text = basic_report
    if RUN_ADVANCED_ANALYSIS:
        context_for_ai = (
            basic_report
            if basic_report
            else "Uwaga: nie udało się pobrać żadnych danych liczbowych z Bybit "
            "(np. błąd HTTP 403 lub ograniczenie IP). Oprzyj analizę wyłącznie "
            "na dostarczonych zrzutach ekranu (heatmapy + whale tracker)."
        )
        advanced = run_advanced_analysis(image_paths=image_paths, basic_report=context_for_ai)
        if advanced:
            report_text = advanced

    ok_email = send_screenshot_email(image_paths, report_text=report_text)

    # Na Telegram wysyłamy oba screenshoty (heatmapa + Hyperliquid),
    # z podpisem tylko przy pierwszym.
    base_caption = f"CoinGlass BTC Liquidation Heatmap – {time.strftime('%Y-%m-%d %H:%M')}"
    caption = build_telegram_caption(base_caption, report_text)
    ok_telegram = send_screenshot_telegram(image_paths, caption=caption)

    if not ok_email or not ok_telegram:
        if ok_email is False or ok_telegram is False:
            logger.warning("Jeden z kanałów wysyłki zwrócił błąd (sprawdź logi).")
    logger.info("Zakończono. Screenshoty: %s", ", ".join(str(p) for p in image_paths))
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
