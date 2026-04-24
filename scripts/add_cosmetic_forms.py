"""
Aggiunge forme cosmetiche speciali (Vivillon patterns, Unown letters, ecc.)
che non sono in pokemon-species/varieties.

Per questi Pokemon usiamo /pokemon-form per ottenere tutte le varianti grafiche.
"""
import json
import os
import sys
import time

import requests

BASE = "https://pokeapi.co/api/v2"
SESSION = requests.Session()
FILE = "pokedex_data.json"

# Pokemon con tante forme cosmetiche (stessa stat, sprite diversi)
# {nome_api: [lista form names]}
FORME_COSMETICHE = {
    "vivillon": [
        "vivillon-meadow", "vivillon-archipelago", "vivillon-continental",
        "vivillon-elegant", "vivillon-fancy", "vivillon-garden", "vivillon-high-plains",
        "vivillon-icy-snow", "vivillon-jungle", "vivillon-marine", "vivillon-modern",
        "vivillon-monsoon", "vivillon-ocean", "vivillon-poke-ball", "vivillon-polar",
        "vivillon-river", "vivillon-sandstorm", "vivillon-savanna", "vivillon-sun",
        "vivillon-tundra",
    ],
    "unown": [f"unown-{c}" for c in "abcdefghijklmnopqrstuvwxyz"] + ["unown-question", "unown-exclamation"],
    "spinda": [],  # 1 sprite, RNG
    "furfrou": [
        "furfrou-natural", "furfrou-heart", "furfrou-star", "furfrou-diamond",
        "furfrou-debutante", "furfrou-matron", "furfrou-dandy",
        "furfrou-la-reine", "furfrou-kabuki", "furfrou-pharaoh",
    ],
    "pumpkaboo": ["pumpkaboo-small", "pumpkaboo-large", "pumpkaboo-super"],
    "gourgeist": ["gourgeist-small", "gourgeist-large", "gourgeist-super"],
    "minior": [
        "minior-red-meteor", "minior-orange-meteor", "minior-yellow-meteor",
        "minior-green-meteor", "minior-blue-meteor", "minior-indigo-meteor",
        "minior-violet-meteor", "minior-red", "minior-orange", "minior-yellow",
        "minior-green", "minior-blue", "minior-indigo", "minior-violet",
    ],
    "alcremie": [
        "alcremie-vanilla-cream", "alcremie-ruby-cream", "alcremie-matcha-cream",
        "alcremie-mint-cream", "alcremie-lemon-cream", "alcremie-salted-cream",
        "alcremie-ruby-swirl", "alcremie-caramel-swirl", "alcremie-rainbow-swirl",
    ],
}


def get_json(url, retry=3):
    for _ in range(retry):
        try:
            r = SESSION.get(url, timeout=15)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
        except requests.RequestException:
            time.sleep(1)
    return None


def fetch_form_pokemon(slug):
    """Prova /pokemon/{slug} (per varietà numerate >10000)."""
    p = get_json(f"{BASE}/pokemon/{slug}")
    if not p:
        return None
    pid = p["id"]
    sprite = (
        p["sprites"].get("other", {}).get("official-artwork", {}).get("front_default")
        or p["sprites"].get("front_default")
        or f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png"
    )
    sprite_shiny = (
        p["sprites"].get("other", {}).get("official-artwork", {}).get("front_shiny")
        or p["sprites"].get("front_shiny")
    )
    return {
        "nome": p["name"].replace("-", " ").title(),
        "nome_api": p["name"],
        "sprite": sprite,
        "sprite_shiny": sprite_shiny,
        "stats": {s["stat"]["name"]: s["base_stat"] for s in p["stats"]},
        "tipi": [t["type"]["name"] for t in p["types"]],
        "abilita": [a["ability"]["name"] for a in p["abilities"]],
        "altezza": p["height"] / 10,
        "peso": p["weight"] / 10,
        "categoria": "alt",
    }


def main():
    with open(FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    map_pkmn = {p["nome_api"]: p for p in data}

    aggiornati = 0
    for nome_api, forme_list in FORME_COSMETICHE.items():
        if not forme_list:
            continue
        # Cerca prima nome esatto, poi prefisso (es. pumpkaboo -> pumpkaboo-average)
        p = map_pkmn.get(nome_api)
        if not p:
            p = next((x for x in data if x["nome_api"].startswith(nome_api + "-")), None)
        if not p:
            print(f"  {nome_api} non trovato in pokedex_data")
            continue

        existing = {f["nome_api"] for f in p.get("forme", [])}
        new_forme = []
        for slug in forme_list:
            if slug in existing:
                continue
            info = fetch_form_pokemon(slug)
            if info:
                new_forme.append(info)
                print(f"  + {slug}")

        if new_forme:
            p.setdefault("forme", [])
            p["forme"].extend(new_forme)
            aggiornati += 1
            print(f"[{p['nome']}] +{len(new_forme)} forme cosmetiche")

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(FILE) / 1024 / 1024
    print(f"\nFatto. {aggiornati} aggiornati. File: {size:.2f} MB")


if __name__ == "__main__":
    sys.exit(main())
