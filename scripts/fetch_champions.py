"""
Scraper pokebase.app/pokemon-champions con SCOPING corretto.

La pagina di un Pokemon contiene anche dati di altri Pokemon (team partners,
matchups). Per attribuire correttamente builds/mosse/abilità/items al Pokemon
principale, usiamo la posizione: ogni elemento appartiene al blocco
"name+slug+iconUrl" che lo precede.

Output: champions_data.json
"""
import json
import os
import re
import sys
import time

import requests

BASE = "https://pokebase.app/pokemon-champions"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebKit/537.36"}
OUT_FILE = "champions_data.json"


def fetch(url):
    for _ in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                return r.text
        except requests.RequestException:
            time.sleep(2)
    return None


def estrai_lista():
    """Estrae tutti gli slug da tutte le pagine di pokebase (1, 2, 3, ...)."""
    tutti = set()
    for p in range(1, 6):
        html = fetch(f"{BASE}/pokemon?page={p}")
        if not html:
            break
        slugs = set(re.findall(r'href="/pokemon-champions/pokemon/([^"]+)"', html))
        nuovi = slugs - tutti
        tutti.update(slugs)
        if not nuovi and p > 1:
            break
    return sorted(tutti)


# Pattern blocco Pokemon: nome+slug+iconUrl (definizione canonica)
_PKMN_BLOCK = re.compile(
    r'\\"name\\":\\"([A-Z][a-zA-Z\' .-]{1,40})\\",'
    r'\\"slug\\":\\"([a-z0-9-]+)\\",'
    r'\\"iconUrl\\":\\"https://i\.pokebase\.app/pokemon-champions/'
)


def trova_blocchi_pokemon(html):
    """Lista di (posizione, slug) per ogni blocco Pokemon nella pagina."""
    return [(m.start(), m.group(2)) for m in _PKMN_BLOCK.finditer(html)]


def trova_owner(pos, blocks):
    """Ritorna lo slug del Pokemon che possiede l'elemento alla posizione `pos`."""
    last = None
    for bs, slug in blocks:
        if bs < pos:
            last = slug
        else:
            break
    return last


def parse_pagina(html, slug_principale):
    """Estrae solo i dati che appartengono a slug_principale."""
    blocks = trova_blocchi_pokemon(html)

    # baseStats: appare una sola volta nella pagina e si riferisce al pokemon principale
    base_stats = {}
    bs = re.search(
        r'\\"baseStats\\":\{\\"hp\\":(\d+),\\"attack\\":(\d+),\\"defense\\":(\d+),'
        r'\\"specialAttack\\":(\d+),\\"specialDefense\\":(\d+),\\"speed\\":(\d+)\}',
        html,
    )
    if bs:
        base_stats = {
            "hp": int(bs.group(1)), "attack": int(bs.group(2)), "defense": int(bs.group(3)),
            "specialAttack": int(bs.group(4)), "specialDefense": int(bs.group(5)), "speed": int(bs.group(6)),
        }

    # iconUrl del Pokemon principale (primo match con quel slug)
    icon_match = re.search(
        rf'\\"slug\\":\\"{re.escape(slug_principale)}\\",\\"iconUrl\\":\\"([^"\\]+)\\"',
        html,
    )
    icon = icon_match.group(1) if icon_match else ""

    # Fallback: cerca singola immagine pokemon-champions/<id>.png nella pagina
    # (pagine "preview" senza dati di builds)
    if not icon:
        img_match = re.search(
            r'(?:https?://i\.pokebase\.app/)?pokemon-champions/([A-Za-z0-9_-]{15,30}\.png)',
            html,
        )
        if img_match:
            icon = "https://i.pokebase.app/pokemon-champions/" + img_match.group(1)

    # Tipi del Pokemon (dalla baseStats area)
    tipi = []
    types_section = re.search(
        r'\\"types\\":\[((?:\\"[a-z]+\\"(?:,)?)+)\]',
        html,
    )
    if types_section:
        tipi = re.findall(r'\\"([a-z]+)\\"', types_section.group(1))

    # Helper: estrai elementi e filtra per owner
    def estrai_filtrato(pattern, parser):
        risultati = []
        for m in re.finditer(pattern, html):
            if trova_owner(m.start(), blocks) == slug_principale:
                risultati.append(parser(m))
        return risultati

    # Mosse (deduplicate per slug, ordine di apparizione)
    mosse_map = {}
    move_pat = (
        r'\\"name\\":\\"([^"\\]+)\\",\\"slug\\":\\"([^"\\]+)\\",'
        r'\\"typeName\\":\\"([^"\\]+)\\",\\"damageClass\\":\\"([^"\\]+)\\",'
        r'\\"power\\":(\d+|null),\\"accuracy\\":(\d+|null),\\"pp\\":(\d+),'
        r'\\"description\\":\\"([^"\\]*)\\"'
    )
    for m in re.finditer(move_pat, html):
        if trova_owner(m.start(), blocks) != slug_principale:
            continue
        s = m.group(2)
        if s in mosse_map:
            continue
        mosse_map[s] = {
            "nome": m.group(1), "slug": s,
            "tipo": m.group(3).lower(), "categoria": m.group(4),
            "potenza": None if m.group(5) == "null" else int(m.group(5)),
            "accuratezza": None if m.group(6) == "null" else int(m.group(6)),
            "pp": int(m.group(7)),
            "descrizione": m.group(8),
        }

    # Abilità (deduplicate per nome)
    abilita_map = {}
    for m in re.finditer(r'\\"ability\\":\\"([^"\\]+)\\",\\"abilityDescription\\":\\"([^"\\]*)\\"', html):
        if trova_owner(m.start(), blocks) != slug_principale:
            continue
        n = m.group(1)
        if n not in abilita_map:
            abilita_map[n] = {"nome": n, "descrizione": m.group(2)}

    # Items (deduplicate per nome)
    items_map = {}
    for m in re.finditer(
        r'\\"item\\":\\"([^"\\]+)\\",\\"itemIconUrl\\":\\"([^"\\]*)\\",\\"itemDescription\\":\\"([^"\\]*)\\"',
        html,
    ):
        if trova_owner(m.start(), blocks) != slug_principale:
            continue
        n = m.group(1)
        if n not in items_map:
            items_map[n] = {"nome": n, "icona": m.group(2), "descrizione": m.group(3)}

    # Builds: ability+item insieme con conteggio (più appare = più popolare)
    builds_count = {}  # (ability, item) -> {"count": n, "data": {...}}
    build_pat = (
        r'\\"ability\\":\\"([^"\\]+)\\",\\"abilityDescription\\":\\"[^"\\]*\\",'
        r'\\"item\\":\\"([^"\\]+)\\",\\"itemIconUrl\\":\\"([^"\\]*)\\",'
        r'\\"itemDescription\\":\\"[^"\\]*\\",\\"nature\\":(?:\\"([^"\\]+)\\"|null),'
        r'\\"stats\\":\{\\"hp\\":(\d+),\\"attack\\":(\d+),\\"defense\\":(\d+),'
        r'\\"specialAttack\\":(\d+),\\"specialDefense\\":(\d+),\\"speed\\":(\d+)\}'
    )
    for m in re.finditer(build_pat, html):
        if trova_owner(m.start(), blocks) != slug_principale:
            continue
        ability, item, item_icon, nature, hp, atk, deff, spa, spd, spe = m.groups()
        key = (ability, item, nature or "")
        if key in builds_count:
            builds_count[key]["count"] += 1
        else:
            builds_count[key] = {
                "count": 1,
                "data": {
                    "abilita": ability,
                    "oggetto": item,
                    "oggetto_icona": item_icon,
                    "natura": nature,
                    "ev": {
                        "hp": int(hp), "attack": int(atk), "defense": int(deff),
                        "specialAttack": int(spa), "specialDefense": int(spd), "speed": int(spe),
                    },
                },
            }

    # Ordina per count discendente (più popolare prima)
    builds = sorted(builds_count.values(), key=lambda x: x["count"], reverse=True)
    builds_finali = [{**b["data"], "popolarita": b["count"]} for b in builds[:8]]

    return {
        "slug": slug_principale,
        "icona": icon,
        "tipi": tipi,
        "base_stats": base_stats,
        "mosse": list(mosse_map.values()),
        "abilita": list(abilita_map.values()),
        "items": list(items_map.values()),
        "builds": builds_finali,
    }


def main():
    risultati = {}
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, "r", encoding="utf-8") as f:
            risultati = json.load(f)

    slugs = estrai_lista()
    print(f"Trovati {len(slugs)} Pokemon Champions.")

    for i, slug in enumerate(slugs, 1):
        print(f"[{i:3d}/{len(slugs)}] {slug}", end=" ", flush=True)
        html = fetch(f"{BASE}/pokemon/{slug}")
        if not html:
            print("FAIL")
            continue
        data = parse_pagina(html, slug)
        risultati[slug] = data
        print(f"OK m={len(data['mosse'])} a={len(data['abilita'])} "
              f"i={len(data['items'])} b={len(data['builds'])}")

        if i % 20 == 0:
            with open(OUT_FILE, "w", encoding="utf-8") as f:
                json.dump(risultati, f, ensure_ascii=False, separators=(",", ":"))

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(risultati, f, ensure_ascii=False, separators=(",", ":"))
    size_kb = os.path.getsize(OUT_FILE) / 1024
    print(f"\nFatto. {len(risultati)} salvati ({size_kb:.1f} KB)")


if __name__ == "__main__":
    sys.exit(main())
