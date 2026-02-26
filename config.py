"""Konfiguracja z zmiennych środowiskowych."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# URL mapy likwidacji (można zmienić coin w query)
HEATMAP_URL = os.getenv(
    "HEATMAP_URL",
    "https://www.coinglass.com/pro/futures/LiquidationHeatMap?coin=BTC&type=symbol",
)

# Katalog na screenshoty (tymczasowe)
SCREENSHOT_DIR = Path(os.getenv("SCREENSHOT_DIR", "screenshots"))

# --- E-mail ---
SEND_EMAIL = os.getenv("SEND_EMAIL", "false").lower() == "true"
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_TO = os.getenv("EMAIL_TO", "")  # może być lista oddzielona przecinkami
EMAIL_SUBJECT_PREFIX = os.getenv("EMAIL_SUBJECT_PREFIX", "CoinGlass Liquidation Heatmap")

# --- Telegram ---
SEND_TELEGRAM = os.getenv("SEND_TELEGRAM", "false").lower() == "true"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Przeglądarka
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
WAIT_AFTER_LOAD_MS = int(os.getenv("WAIT_AFTER_LOAD_MS", "2500"))
