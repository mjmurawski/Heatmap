# Agent: CoinGlass Liquidation Heatmap → screenshot → e-mail / Telegram

Agent wchodzi na stronę [CoinGlass BTC Liquidation Heatmap](https://www.coinglass.com/pro/futures/LiquidationHeatMap?coin=BTC&type=symbol), robi screenshot mapy likwidacji i wysyła go e-mailem i/lub na Telegrama.

## Wymagania

- Python 3.10+
- Konto e-mail z SMTP (np. Gmail) i/lub bot Telegram

## Instalacja

```bash
cd coinglass-liquidation-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## Konfiguracja

1. Skopiuj plik konfiguracyjny:
   ```bash
   copy .env.example .env
   ```
2. Edytuj `.env`:
   - **E-mail:** ustaw `SEND_EMAIL=true`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_TO`. Dla Gmaila użyj [hasła aplikacji](https://support.google.com/accounts/answer/185833).
   - **Telegram:** ustaw `SEND_TELEGRAM=true`, `TELEGRAM_BOT_TOKEN` (od [@BotFather](https://t.me/BotFather)), `TELEGRAM_CHAT_ID` (np. z [@userinfobot](https://t.me/userinfobot)).

## Uruchomienie

**Jednorazowo:**
```bash
python run_agent.py
```

**Co godzinę (w pętli – zostaw okno otwarte):**
```bash
python run_agent.py --every-hour
```
Agent zrobi screenshot i wyśle od razu, potem co 60 minut powtórzy. Zatrzymanie: Ctrl+C.

Screenshot zostanie zapisany w katalogu `screenshots/` i – w zależności od ustawień – wysłany e-mailem i/lub na Telegrama.

## GitHub Actions (darmowo, 7:00–23:00)

Workflow wysyła heatmapę **co godzinę**, ale **tylko między 7:00 a 23:00** (strefa Europe/Warsaw). Zero kosztów, działa w chmurze GitHub.

**Konfiguracja:**

1. **Repozytorium na GitHubie**  
   Załóż nowe repo (np. `coinglass-heatmap`), może być prywatne.

2. **Sekrety**  
   W repozytorium: **Settings → Secrets and variables → Actions → New repository secret**  
   Dodaj:
   - `TELEGRAM_BOT_TOKEN` — token bota z @BotFather  
   - `TELEGRAM_CHAT_ID` — Twój chat ID  

3. **Wypchnij kod** (w katalogu projektu):
   ```bash
   git init
   git add .
   git commit -m "Initial"
   git remote add origin https://github.com/TWOJ_LOGIN/NAZWA_REPO.git
   git branch -M main
   git push -u origin main
   ```
   Do repo **nie** dodawaj pliku `.env` (jest w `.gitignore` albo go nie commituj).

4. **Włączenie workflow**  
   Po pierwszym pushu workflow jest włączony. Uruchomienia: **Actions → „Heatmap co godzinę (7–23)”**.  
   Możesz też uruchomić go ręcznie: **Run workflow**.

Domyślnie workflow ustawia w jobie: `SEND_TELEGRAM=true`, interwał 12 h, BTC. Aby zmienić (np. inna moneta), edytuj plik `.github/workflows/heatmap-hourly.yml` (sekcja „Konfiguracja .env”).

## Harmonogram (Windows Task Scheduler)

**Co godzinę:** utwórz zadanie z wyzwalaczem „Co 1 godzinę” i akcją: program `…\venv\Scripts\python.exe`, argumenty `…\run_agent.py`, katalog startowy: `…\coinglass-liquidation-agent`.

**Comiesięcznie (np. 1. dzień o 9:00):**

1. Otwórz **Harmonogram zadań** (Task Scheduler).
2. Utwórz nowe zadanie:
   - **Wyzwalacz:** miesięcznie, np. 1. dzień miesiąca o 9:00.
   - **Akcja:** uruchom program: `C:\ścieżka\do\venv\Scripts\python.exe`, argumenty: `C:\ścieżka\do\coinglass-liquidation-agent\run_agent.py`, katalog startowy: `C:\ścieżka\do\coinglass-liquidation-agent`.

## Zmienne środowiskowe (.env)

| Zmienna | Opis |
|--------|------|
| `HEATMAP_URL` | URL strony (domyślnie BTC; można zmienić na ETH itd.) |
| `WAIT_AFTER_LOAD_MS` | Czekanie po załadowaniu strony (ms) |
| `HEADLESS` | `true` = przeglądarka w tle |
| `SEND_EMAIL` | `true` = włącz wysyłkę e-mail |
| `SMTP_*`, `EMAIL_*` | Ustawienia SMTP i adresy |
| `SEND_TELEGRAM` | `true` = włącz wysyłkę na Telegram |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Dane bota Telegram |

## Licencja / regulamin

Używaj zgodnie z regulaminem CoinGlass i polityką Twojej organizacji. Hasła i tokeny trzymaj tylko w `.env` (nie commituj do repozytorium).
