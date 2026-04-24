"""
Scraper per i team competitivi Pokemon Champions da pokebase.app.
Estrae team da tornei reali con W/L e composizioni.

Visita ogni pagina di Pokemon Champions, estrae i team che lo includono,
deduplica per id, salva tutto.

Output: champions_teams.json
"""
import json
import os
import re
import sys
import time

import requests

BASE = "https://pokebase.app/pokemon-champions"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebKit/537.36"}
OUT_FILE = "champions_teams.json"


def fetch(url):
    for _ in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                return r.text
        except requests.RequestException:
            time.sleep(2)
    return None


def estrai_lista_pokemon():
    html = fetch(f"{BASE}/pokemon")
    if not html:
        return []
    return sorted(set(re.findall(r'href="/pokemon-champions/pokemon/([^"]+)"', html)))


def estrai_team(html):
    """Estrae lista team dalla pagina. Ogni team è un dict."""
    # Trova ogni inizio team
    starts = [m.start() for m in re.finditer(r'\\"team\\":\{\\"id\\":\\"', html)]
    teams = []

    for s in starts:
        chunk = html[s:s + 8000]
        # Estrai metadata
        meta = re.match(
            r'\\"team\\":\{\\"id\\":\\"([^"]+)\\",\\"name\\":\\"([^"]+?)\\",'
            r'\\"limitlessPlayer\\":\\"([^"]*)\\",\\"placing\\":(\d+),'
            r'\\"wins\\":(\d+),\\"losses\\":(\d+),\\"ties\\":(\d+)',
            chunk,
        )
        if not meta:
            continue
        team_id, name, player, placing, wins, losses, ties = meta.groups()

        # Estrai i 6 pokemon (slug) - cerca nei prossimi ~6000 char
        # Pattern: "name":"X","slug":"x","iconUrl":"..."
        pkmn_data = []
        # Cerca solo all'interno del blocco pokemon[...]
        pkmn_section_match = re.search(r'\\"pokemon\\":\[(.{0,7000})', chunk)
        if not pkmn_section_match:
            continue

        pkmn_blob = pkmn_section_match.group(1)
        # Trova ogni pokemon: name+slug+iconUrl... e ability+item
        # I pokemon hanno una struttura ripetuta. Conto fino a 6 per team.
        for pm in re.finditer(
            r'\\"name\\":\\"([A-Z][A-Za-z\' .-]+?)\\",\\"slug\\":\\"([a-z0-9-]+)\\",'
            r'\\"iconUrl\\":\\"([^"\\]+)\\"',
            pkmn_blob,
        ):
            if len(pkmn_data) >= 6:
                break
            slug = pm.group(2)
            # Cerca ability+item nella sezione successiva (max 2000 char)
            inizio = pm.end()
            sezione = pkmn_blob[inizio:inizio + 2500]
            ability_m = re.search(r'\\"ability\\":\\"([^"\\]+)\\"', sezione)
            item_m = re.search(r'\\"item\\":\\"([^"\\]+)\\"', sezione)

            pkmn_data.append({
                "nome": pm.group(1),
                "slug": slug,
                "icona": pm.group(3),
                "abilita": ability_m.group(1) if ability_m else None,
                "oggetto": item_m.group(1) if item_m else None,
            })

        if len(pkmn_data) >= 4:  # team validi (almeno 4 pokemon)
            teams.append({
                "id": team_id,
                "nome_torneo": name,
                "player": player,
                "placing": int(placing),
                "wins": int(wins),
                "losses": int(losses),
                "ties": int(ties),
                "pokemon": pkmn_data,
            })

    return teams


def main():
    risultati = {}  # team_id -> team data
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, "r", encoding="utf-8") as f:
            risultati = json.load(f)
        print(f"Ripreso da {len(risultati)} team.")

    slugs = estrai_lista_pokemon()
    print(f"Pokemon Champions: {len(slugs)}")

    nuovi_visti = 0
    for i, slug in enumerate(slugs, 1):
        html = fetch(f"{BASE}/pokemon/{slug}")
        if not html:
            print(f"[{i:3d}] {slug} FAIL")
            continue

        teams = estrai_team(html)
        nuovi = 0
        for t in teams:
            if t["id"] not in risultati:
                risultati[t["id"]] = t
                nuovi += 1
                nuovi_visti += 1
        print(f"[{i:3d}/{len(slugs)}] {slug}: +{nuovi} nuovi (totale: {len(risultati)})")

        if i % 20 == 0:
            with open(OUT_FILE, "w", encoding="utf-8") as f:
                json.dump(risultati, f, ensure_ascii=False, separators=(",", ":"))

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(risultati, f, ensure_ascii=False, separators=(",", ":"))

    size = os.path.getsize(OUT_FILE) / 1024
    print(f"\nFatto. {len(risultati)} team unici salvati ({size:.1f} KB)")


if __name__ == "__main__":
    sys.exit(main())
