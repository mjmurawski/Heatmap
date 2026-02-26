"""Otwiera stronę CoinGlass Liquidation Heatmap i robi screenshot (zamyka consent, klika ikonę aparatu)."""
import logging
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from config import HEATMAP_URL, SCREENSHOT_DIR, HEADLESS, WAIT_AFTER_LOAD_MS

logger = logging.getLogger(__name__)


def _close_consent_popup(page) -> None:
    """Zamyka okno zgody na cookies/consent (Consent lub Do not consent)."""
    for label in ["Consent", "Do not consent", "Accept", "Accept All"]:
        try:
            btn = page.get_by_role("button", name=label).first
            if btn.is_visible(timeout=1500):
                btn.click(timeout=2000)
                page.wait_for_timeout(400)
                logger.info("Zamknięto popup zgody (przycisk: %s).", label)
                return
        except Exception:
            continue
    try:
        el = page.locator('button:has-text("Consent"), button:has-text("Do not consent")').first
        if el.is_visible(timeout=1000):
            el.click(timeout=2000)
            page.wait_for_timeout(400)
            logger.info("Zamknięto popup zgody.")
    except Exception:
        pass


def _scroll_chart_into_view(page) -> None:
    """Przewija do obszaru wykresu, żeby pasek z ikoną aparatu był widoczny."""
    selectors = [
        "canvas",
        "[class*='heatmap']",
        "[class*='liquidation']",
    ]
    for selector in selectors:
        try:
            el = page.locator(selector).first
            if el.count() > 0:
                el.scroll_into_view_if_needed(timeout=2000)
                page.wait_for_timeout(250)
                return
        except Exception:
            continue
    try:
        page.get_by_text("Liquidity Threshold", exact=False).first.scroll_into_view_if_needed(timeout=1500)
        page.wait_for_timeout(250)
        return
    except Exception:
        pass
    page.evaluate("window.scrollBy(0, 400)")
    page.wait_for_timeout(200)


def _click_camera_and_get_download(page, filepath: Path) -> bool:
    """
    Klika ikonę aparatu (eksportu) przy heatmapie – dostajemy samą mapę bez Print/camera/down-arrow.
    Na CoinGlass w rzędzie jest: Print (1.), aparat (2.), strzałka (3.) – szukamy tego, który daje download.
    """
    # 1) Przyciski z ikoną (SVG) w głównej treści – pomijamy "Print", próbujemy 2. i 3. (aparat / download)
    try:
        # Wszystkie przyciski z SVG (Print, aparat, strzałka są w tym samym rzędzie)
        all_icon_btns = page.locator("button:has(svg)")
        n = all_icon_btns.count()
        for idx in range(min(n, 5)):
            btn = all_icon_btns.nth(idx)
            if not btn.is_visible():
                continue
            # Pomiń przycisk z tekstem "Print"
            if btn.get_attribute("aria-label") == "Print" or "print" in (btn.get_attribute("aria-label") or "").lower():
                continue
            try:
                btn.scroll_into_view_if_needed(timeout=1500)
                page.wait_for_timeout(150)
                with page.expect_download(timeout=12000) as download_info:
                    btn.click(timeout=3000)
                download_info.value.save_as(str(filepath))
                logger.info("Pobrano heatmapę (przycisk z ikoną nr %s): %s", idx + 1, filepath)
                return True
            except Exception:
                continue
    except Exception:
        pass

    # 2) Konkretne selektory na eksport (camera / screenshot)
    for selector in [
        '[class*="camera"]',
        '[class*="screenshot"]',
        '[aria-label*="screenshot" i]',
        '[aria-label*="camera" i]',
        '[title*="screenshot" i]',
        '[title*="camera" i]',
    ]:
        try:
            loc = page.locator(selector).first
            loc.wait_for(state="visible", timeout=2000)
            loc.scroll_into_view_if_needed(timeout=1500)
            page.wait_for_timeout(100)
            with page.expect_download(timeout=12000) as download_info:
                loc.click(timeout=3000)
            download_info.value.save_as(str(filepath))
            logger.info("Pobrano heatmapę (selektor %s): %s", selector[:30], filepath)
            return True
        except Exception:
            continue
    return False


def capture_heatmap(
    url: str = HEATMAP_URL,
    output_dir: Path = SCREENSHOT_DIR,
    headless: bool = HEADLESS,
    wait_ms: int = WAIT_AFTER_LOAD_MS,
) -> Path | None:
    """
    Otwiera stronę z mapą likwidacji, zamyka popup zgody, klika ikonę aparatu
    (jeśli znajdzie) i zapisuje pobraną heatmapę; w przeciwnym razie robi screenshot.
    Zwraca ścieżkę do pliku PNG lub None przy błędzie.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"liquidation_heatmap_{timestamp}.png"
    filepath = output_dir / filename

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()

            logger.info("Otwieram %s", url)
            page.goto(url, wait_until="domcontentloaded", timeout=25000)

            page.wait_for_timeout(wait_ms)

            # Zamknij okno zgody (Consent), żeby nie zasłaniało mapy
            _close_consent_popup(page)
            page.wait_for_timeout(500)

            # Opcjonalnie: czekaj na element mapy
            heatmap_selectors = [
                "[class*='heatmap']",
                "[class*='liquidation']",
                "canvas",
                "main",
            ]
            for selector in heatmap_selectors:
                try:
                    page.wait_for_selector(selector, timeout=2000)
                    break
                except PlaywrightTimeout:
                    continue

            # Przewiń do wykresu, żeby pasek z ikoną aparatu był widoczny i mapa nie ucięta
            _scroll_chart_into_view(page)
            page.wait_for_timeout(300)

            # Spróbuj kliknąć ikonę aparatu – wtedy dostajemy pełną heatmapę (jak załącznik 2)
            if _click_camera_and_get_download(page, filepath):
                return filepath

            # Fallback: pełna strona (scroll w dół + zrzut całej strony, żeby mapa nie była ucięta)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(200)
            page.screenshot(path=str(filepath), full_page=True)
            logger.info("Zapisano screenshot pełnej strony (fallback): %s", filepath)
            return filepath

        except Exception as e:
            logger.exception("Błąd podczas capture: %s", e)
            return None
        finally:
            browser.close()

    return None
