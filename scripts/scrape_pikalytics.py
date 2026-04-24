"""
Scraper Playwright per Pikalytics Champions.
Estrae per ogni Pokemon Champions:
- EV spreads con natura e % usage
- Item con %
- Ability con %
- Mosse con %
- Teammate (compagni di team più frequenti) con %

Output: pikalytics_champions.json
"""
import asyncio
import json
import os
import re
import sys
import time

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

POKEMON_LIST = [
    "Aegislash", "Aerodactyl", "Aggron", "Alakazam", "Arcanine",
    "Archaludon", "Azumarill", "Basculegion", "Blastoise",
    "Charizard", "Chesnaught", "Clefable", "Conkeldurr", "Corviknight",
    "Crabominable", "Delphox", "Dragapult", "Dragonite", "Excadrill",
    "Farigiraf", "Floette-Eternal", "Froslass", "Garchomp", "Gardevoir",
    "Gengar", "Glimmora", "Gyarados", "Hatterene", "Heatran",
    "Hippowdon", "Hitmontop", "Hydreigon", "Incineroar", "Iron-Hands",
    "Iron-Valiant", "Jellicent", "Kingambit", "Lapras", "Magnezone",
    "Mewtwo", "Mienshao", "Milotic", "Mimikyu", "Murkrow",
    "Ninetales", "Ninetales-Alola", "Noivern", "Pelipper", "Politoed",
    "Porygon-Z", "Porygon2", "Primarina", "Quagsire", "Reuniclus",
    "Rhyperior", "Rotom-Heat", "Rotom-Wash", "Salamence", "Sceptile",
    "Scizor", "Scrafty", "Sinistcha", "Skeledirge", "Slowking",
    "Sneasler", "Tatsugiri", "Toxapex", "Tsareena", "Tyranitar",
    "Umbreon", "Volcarona", "Weavile", "Whimsicott", "Zoroark",
]

OUT_FILE = "pikalytics_champions.json"
BASE_URL = "https://www.pikalytics.com/pokedex/championstournaments"


async def scrape_pokemon(page, slug):
    """Scrape spreads/items/abilities/moves/teammates per un Pokemon."""
    url = f"{BASE_URL}/{slug}?l=en"
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
    except PWTimeout:
        return None

    # Aspetta che il contenuto si carichi (spreads o "No data yet")
    try:
        await page.wait_for_selector(
            "#dex_spreads_wrapper .pokedex-move-entry-new, .pokedex-empty-state",
            timeout=10000,
        )
    except PWTimeout:
        pass

    risultato = {"slug": slug, "spreads": [], "items": [], "abilities": [],
                 "moves": [], "teammates": []}

    # SPREADS
    spreads = await page.query_selector_all("#dex_spreads_wrapper .pokedex-move-entry-new")
    for s in spreads:
        try:
            nature = await (await s.query_selector(".pokedex-inline-text-offset")).inner_text()
            ev_els = await s.query_selector_all(".pokedex-inline-text")
            evs = [(await e.inner_text()).strip() for e in ev_els]
            pct_el = await s.query_selector(".pokedex-inline-right")
            pct = (await pct_el.inner_text()).strip() if pct_el else ""
            risultato["spreads"].append({
                "natura": nature.strip(),
                "ev": evs,
                "percent": pct,
            })
        except Exception:
            pass

    # Generic selector for sections (items, abilities, moves, teammates)
    async def estrai_sezione(wrapper_id):
        elementi = []
        try:
            entries = await page.query_selector_all(f"#{wrapper_id} .pokedex-move-entry-new")
            for e in entries:
                nome_el = await e.query_selector(".pokedex-inline-text-offset, .pokedex-inline-text")
                pct_el = await e.query_selector(".pokedex-inline-right")
                if nome_el:
                    nome = (await nome_el.inner_text()).strip()
                    pct = (await pct_el.inner_text()).strip() if pct_el else ""
                    if nome:
                        elementi.append({"nome": nome, "percent": pct})
        except Exception:
            pass
        return elementi

    risultato["items"] = await estrai_sezione("dex_items_wrapper")
    risultato["abilities"] = await estrai_sezione("dex_abilities_wrapper")
    risultato["moves"] = await estrai_sezione("dex_moves_wrapper")
    risultato["teammates"] = await estrai_sezione("dex_teammates_wrapper")

    return risultato


async def main():
    risultati = {}
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, "r", encoding="utf-8") as f:
            risultati = json.load(f)
        print(f"Ripreso da {len(risultati)} Pokemon.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await ctx.new_page()

        for i, slug in enumerate(POKEMON_LIST, 1):
            if slug in risultati and risultati[slug].get("spreads"):
                print(f"[{i:3d}/{len(POKEMON_LIST)}] {slug:25s} skip (gia ok)")
                continue

            t0 = time.time()
            try:
                data = await scrape_pokemon(page, slug)
            except Exception as e:
                print(f"[{i:3d}/{len(POKEMON_LIST)}] {slug:25s} ERR: {e}")
                continue

            if not data:
                print(f"[{i:3d}/{len(POKEMON_LIST)}] {slug:25s} FAIL")
                continue

            risultati[slug] = data
            elapsed = time.time() - t0
            print(f"[{i:3d}/{len(POKEMON_LIST)}] {slug:25s} "
                  f"sp={len(data['spreads']):2d} it={len(data['items']):2d} "
                  f"ab={len(data['abilities']):2d} mv={len(data['moves']):2d} "
                  f"tm={len(data['teammates']):2d} ({elapsed:.1f}s)")

            if i % 10 == 0:
                with open(OUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(risultati, f, ensure_ascii=False, separators=(",", ":"))
                print("  -> checkpoint")

        await browser.close()

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(risultati, f, ensure_ascii=False, separators=(",", ":"))

    size = os.path.getsize(OUT_FILE) / 1024
    print(f"\nFatto. {len(risultati)} salvati ({size:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
