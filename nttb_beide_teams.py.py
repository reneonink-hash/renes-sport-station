"""Haal openbare TTapp-poulepagina's op via Playwright (ook in GitHub Actions)."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

POULES = [
    ("TIOS Dames 1", "5021894", "tios", "TIOS '51 1"),
    ("Markiezaat 11", "5022143", "markiezaat", "Het Markiezaat 11"),
]
UITVOERMAP = Path(__file__).resolve().parent


def lees_tab(pagina, tabnaam, herkenning):
    tab = pagina.get_by_text(tabnaam, exact=True).first
    tab.wait_for(state="visible", timeout=25000)
    tab.click(timeout=15000)
    pagina.wait_for_function(
        "([naam, tab]) => document.body.innerText.includes(naam) && "
        "(tab === 'stand' ? document.body.innerText.includes('punten') : "
        "document.body.innerText.includes('week '))",
        arg=[herkenning, tabnaam],
        timeout=30000,
    )
    tekst = pagina.locator("body").inner_text(timeout=15000)
    if herkenning.lower() not in tekst.lower():
        raise RuntimeError(f"Team {herkenning} ontbreekt in tab {tabnaam}")
    return tekst


def main():
    fouten = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            for team, poule, naam, herkenning in POULES:
                print(f"Ophalen: {team} (poule {poule})", flush=True)
                pagina = browser.new_page(locale="nl-NL")
                try:
                    pagina.goto(f"https://ttapp.nl/poule/{poule}", wait_until="domcontentloaded", timeout=60000)
                    wedstrijden = lees_tab(pagina, "wedstrijden", herkenning)
                    stand = lees_tab(pagina, "stand", herkenning)
                    gegevens = {
                        "team": team,
                        "poule": poule,
                        "bijgewerkt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "wedstrijden_tekst": wedstrijden,
                        "stand_tekst": stand,
                    }
                    bestand = UITVOERMAP / f"nttb_{naam}.json"
                    bestand.write_text(json.dumps(gegevens, ensure_ascii=False, indent=2), encoding="utf-8")
                    print(f"GELUKT: {bestand.name}", flush=True)
                except Exception as fout:
                    fouten.append(team)
                    print(f"FOUT bij {team}: {type(fout).__name__}: {fout}", file=sys.stderr, flush=True)
                finally:
                    pagina.close()
        finally:
            browser.close()
    if fouten:
        print("Niet alle poules konden worden opgehaald: " + ", ".join(fouten), file=sys.stderr)
        sys.exit(1)
    print("Beide NTTB-bestanden bijgewerkt.")


if __name__ == "__main__":
    main()
