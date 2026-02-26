"""Prosty test wysyłki wiadomości na Telegram (sendMessage). Uruchom z katalogu projektu."""
import sys
import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def get_chat_id():
    """Pobiera ostatnie rozmowy z bota (getUpdates) i wypisuje chat_id. Najpierw napisz do bota w Telegramie."""
    if not TELEGRAM_BOT_TOKEN:
        print("Ustaw TELEGRAM_BOT_TOKEN w .env")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    r = requests.get(url, timeout=15)
    data = r.json()
    if not data.get("ok"):
        print("Błąd API:", data)
        return
    results = data.get("result", [])
    if not results:
        print("Brak wiadomości. Najpierw napisz do bota w Telegramie (np. /start), potem uruchom ponownie:")
        print("  python test_telegram.py --get-chat-id")
        return
    seen = set()
    for u in results:
        msg = u.get("message") or u.get("edited_message") or {}
        chat = msg.get("chat", {})
        cid = chat.get("id")
        if cid is not None and cid not in seen:
            seen.add(cid)
            title = chat.get("title") or chat.get("first_name") or f"Chat {cid}"
            print(f"  chat_id = {cid}  ({title})")
    if seen:
        print("\nSkopiuj jedną z powyższych liczb do .env jako TELEGRAM_CHAT_ID=")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--get-chat-id", "-g"):
        get_chat_id()
        return
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Ustaw TELEGRAM_BOT_TOKEN i TELEGRAM_CHAT_ID w pliku .env")
        print("Nie znasz chat_id? Napisz do bota w Telegramie, potem:  python test_telegram.py --get-chat-id")
        return
    try:
        chat_id = int(TELEGRAM_CHAT_ID.strip())
    except ValueError:
        chat_id = TELEGRAM_CHAT_ID.strip()
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": "Test z coinglass-liquidation-agent – działa."}
    r = requests.post(url, json=payload, timeout=15)
    if not r.ok:
        print("Błąd Telegram:", r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text)
        if r.status_code == 400 and "chat not found" in str(r.json().get("description", "")):
            print("\n→ Prawdopodobnie zły TELEGRAM_CHAT_ID. Napisz do bota w Telegramie, potem uruchom:")
            print("  python test_telegram.py --get-chat-id")
        r.raise_for_status()
    print("Wysłano. Sprawdź Telegram.")


if __name__ == "__main__":
    main()
