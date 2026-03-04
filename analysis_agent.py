import logging
from pathlib import Path
from typing import List, Optional, Sequence

from google import genai
from google.genai import types

from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "Jesteś doświadczonym traderem i analitykiem rynków kryptowalutowych z "
    "głęboką ekspertyzą w interpretacji heatmap likwidacji oraz danych o "
    "przepływach kapitału wielorybów (whale flow). Odbiorca analizy to "
    "ekspert – trader z doświadczeniem w liquidation maps i whale tracking – "
    "więc pomijaj wyjaśnienia podstawowych pojęć i operuj bezpośrednio na "
    "poziomie zaawansowanym."
)


def _build_user_prompt(basic_report: str) -> str:
    """
    Pełna instrukcja użytkownika, dokładnie wg specyfikacji:
    Dane Wejściowe / Zadanie Analityczne / Format Wyniku.
    """
    return (
        "Jesteś doświadczonym traderem i analitykiem rynków kryptowalutowych z "
        "głęboką ekspertyzą w interpretacji heatmap likwidacji oraz danych o "
        "przepływach kapitału wielorybów (whale flow). Odbiorca analizy to ekspert "
        "– trader z doświadczeniem w liquidation maps i whale tracking – więc "
        "pomijaj wyjaśnienia podstawowych pojęć i operuj bezpośrednio na poziomie "
        "zaawansowanym.\n\n"
        "## Dane Wejściowe\n\n"
        "Użytkownik dostarcza następujące materiały (traktuj je jako komplet danych, "
        "nie zakładaj niczego poza nimi):\n"
        "- Zrzuty ekranu heatmapy likwidacji BTCUSDT z CoinGlass.\n"
        "- Zrzuty ekranu Hyperliquid Whale Tracker (Real-Time).\n"
        "- Pliki eksportowe z platform (CSV/JSON) – w tej implementacji "
        "zastąpione liczbowym podsumowaniem z Bybit API:\n\n"
        f"{basic_report}\n\n"
        "Opieraj analizę wyłącznie na dostarczonych danych. Nie zakładaj z góry "
        "kierunku – podążaj za tym, co pokazują heatmapy i whale flow.\n\n"
        "## Zadanie Analityczne\n\n"
        "Przeprowadź analizę krótkookresową BTCUSDT w horyzoncie 4 godzin, "
        "obejmującą:\n"
        "- Poziomy likwidacyjne: zidentyfikuj skupiska zleceń likwidacyjnych "
        "(long i short) z największą koncentracją. Wskaż, które poziomy stanowią "
        "najbliższe cele magnetyczne dla ceny i w jakiej kolejności "
        "prawdopodobnie zostaną zaadresowane.\n"
        "- Pozycje wielorybów: oceń dominujący kierunek (long/short), agresywność "
        "pozycjonowania, sygnały akumulacji lub dystrybucji, rozmiary i poziomy "
        "wejść największych graczy.\n"
        "- Relacja wieloryby vs. likwidacje: określ, czy rynek jest ustawiony pod "
        "short squeeze, long liquidation cascade, czy strukturę neutralną – "
        "i uzasadnij to relacją między obiema warstwami danych.\n\n"
        "## Format Wyniku\n\n"
        "Zakończ analizę dokładnie w poniższej strukturze (po polsku, bez "
        "dodawania innych sekcji):\n\n"
        "**Scenariusz Bazowy** (bardziej prawdopodobny):\n"
        "- Kierunek i opis mechaniki ruchu\n"
        "- Konkretne poziomy cenowe: cel / TP / SL\n"
        "- Prawdopodobieństwo: X%\n\n"
        "**Scenariusz Alternatywny:**\n"
        "- Kierunek i opis mechaniki ruchu\n"
        "- Konkretne poziomy cenowe: cel / TP / SL\n"
        "- Prawdopodobieństwo: X%\n\n"
        "**Synteza:**\n"
        "- Kierunek: wzrost / spadek / konsolidacja\n"
        "- Kluczowe poziomy do obserwacji\n"
        "- Główne czynniki ryzyka unieważniające prognozę\n\n"
        "To jest twarde wymaganie: jeśli pominiesz choć jedną z powyższych "
        "sekcji lub podpunktów, odpowiedź jest błędna. Zawsze wypisz wszystkie "
        "sekcje (Bazowy, Alternatywny, Synteza) oraz wszystkie podpunkty, nawet "
        "jeśli w którymś miejscu musisz napisać, że dane są niejednoznaczne.\n\n"
        "Ogranicz rozwlekłość: maksymalnie 4–6 zdań w każdej sekcji (Bazowy, "
        "Alternatywny, Synteza), bez dygresji spoza zakresu zadania."
    )


def run_advanced_analysis(
    image_paths: Sequence[Path],
    basic_report: str,
    model_name: str = "gemini-2.5-flash",
) -> Optional[str]:
    """
    Wywołuje Gemini API (SDK google-genai) z wejściem obrazowym (heatmapy)
    oraz raportem liczbowym z Bybit i zwraca gotową analizę w zadanym formacie.

    Klucz API pobierany jest ze zmiennej środowiskowej GEMINI_API_KEY.
    Zwraca None, jeśli brak klucza lub wystąpi błąd.
    """
    if not GEMINI_API_KEY:
        logger.info("Brak GEMINI_API_KEY – pomijam zaawansowaną analizę Gemini.")
        return None

    # Klient pobiera GEMINI_API_KEY z env (można też: genai.Client(api_key=GEMINI_API_KEY))
    client = genai.Client()

    # contents: najpierw obrazy (Part.from_bytes), na końcu tekst
    contents: List[types.Part] = []
    for path in image_paths:
        try:
            img_bytes = path.read_bytes()
        except OSError as e:
            logger.warning("Nie udało się odczytać pliku obrazu do analizy: %s", e)
            continue
        contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))

    if not contents:
        logger.warning("Brak obrazów do analizy, pomijam Gemini.")
        return None

    contents.append(_build_user_prompt(basic_report))

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=8192,  # Pełna analiza (Bazowy + Alternatywny + Synteza) – 2048 ucinało w połowie
    )

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )
    except Exception as e:
        logger.exception("Błąd podczas wywołania Gemini dla analizy: %s", e)
        return None

    text = getattr(response, "text", None) or ""
    analysis = text.strip()
    return analysis or None
