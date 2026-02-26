"""Wysyłka screenshotu e-mailem (SMTP)."""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path
from datetime import datetime

from config import (
    SEND_EMAIL,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    EMAIL_FROM,
    EMAIL_TO,
    EMAIL_SUBJECT_PREFIX,
)

logger = logging.getLogger(__name__)


def send_screenshot_email(image_path: Path) -> bool:
    """
    Wysyła e-mail z załączonym screenshotem mapy likwidacji.
    Wymaga: SEND_EMAIL=true oraz SMTP_* i EMAIL_TO w .env.
    """
    if not SEND_EMAIL:
        logger.info("SEND_EMAIL=false, pomijam wysyłkę e-mail.")
        return True

    if not EMAIL_TO or not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("Brak EMAIL_TO / SMTP_USER / SMTP_PASSWORD — pomijam e-mail.")
        return False

    subject = f"{EMAIL_SUBJECT_PREFIX} – {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    recipients = [r.strip() for r in EMAIL_TO.split(",") if r.strip()]

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText("Załączam aktualny screenshot mapy likwidacji BTC (CoinGlass).", "plain"))

    try:
        with open(image_path, "rb") as f:
            img = MIMEImage(f.read(), name=image_path.name)
        msg.attach(img)
    except OSError as e:
        logger.error("Nie można odczytać pliku screenshot: %s", e)
        return False

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, recipients, msg.as_string())
        logger.info("E-mail wysłany do %s", recipients)
        return True
    except Exception as e:
        logger.exception("Błąd wysyłki e-mail: %s", e)
        return False
