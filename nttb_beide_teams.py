

import json
import sys
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

TEAMS = [
    ("TIOS Dames 1", "5021894", "nttb_tios.json"),
    ("Markiezaat 11", "5022143", "nttb_markiezaat.json"),
]

def ophalen(browser, team, poule, bestand):
    print(f"\nOphalen: {team} (poule {poule})", flush=True)

    pagina = browser.new_page(
        viewport={"width": 1280, "height": 900},
        locale="nl-NL"
    )

    try:
        url = f"https://ttapp.nl/poule/{poule}"
        pagina.goto(url, wait_until="domcontentloaded", timeout=60000)
        pagina.wait_for_timeout(12000)

        print("DIAGNOSE - URL:", pagina.url, flush=True)
        print("DIAGNOSE - titel:", pagina.title(), flush=True)

        tekst = pagina.locator("body").inner_text(timeout=10000)
        print("DIAGNOSE - lengte zichtbare tekst:", len(tekst), flush=True)

        wedstrijden = pagina.get_by_text("wedstrijden", exact=True)
        stand = pagina.get_by_text("stand", exact=True)

        print("DIAGNOSE - wedstrijden zichtbaar:",
              wedstrijden.count(), flush=True)
        print("DIAGNOSE - stand zichtbaar:",
              stand.count(), flush=True)

        if wedstrijden.count() == 0 or stand.count() == 0:
            print("DIAGNOSE - melding:",
                  repr(tekst[:500]), flush=True)
            raise RuntimeError("TTapp tabbladen niet gevonden")

        wedstrijden.first.click(timeout=15000)
        pagina.wait_for_timeout(3000)
        wedstrijden_tekst = pagina.locator("body").inner_text()

        stand.first.click(timeout=15000)
        pagina.wait_for_timeout(3000)
        stand_tekst = pagina.locator("body").inner_text()

        gegevens = {
            "team": team,
            "poule": poule,
            "bijgewerkt": datetime.now().isoformat(timespec="seconds"),
            "wedstrijden_tekst": wedstrijden_tekst,
            "stand_tekst": stand_tekst
        }

        Path(bestand).write_text(
            json.dumps(gegevens, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        print(f"GELUKT: {bestand}", flush=True)
        return True

    except Exception as fout:
        print(f"FOUT bij {team}: {type(fout).__name__}: {fout}",
              flush=True)
        return False

    finally:
        pagina.close()


def main():
    mislukt = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        try:
            for team, poule, bestand in TEAMS:
                if not ophalen(browser, team, poule, bestand):
                    mislukt.append(team)
        finally:
            browser.close()

    if mislukt:
        print("Niet gelukt:", ", ".join(mislukt))
        sys.exit(1)

    print("Beide NTTB-poules succesvol opgehaald!")


if __name__ == "__main__":
    main()
