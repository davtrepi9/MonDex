"""
Aggiunge TUTTE le forme alternative al pokedex_data.json:
- Mega (X/Y se applicabile)
- Gigamax / G-Max
- Regionali (Alola, Galar, Hisui, Paldea)
- Forme cosmetiche/alternative (Vivillon patterns, Unown letters, Deoxys, Rotom appliances, ecc.)

Per ogni varietà salviamo: nome, nome_api, sprite, sprite_shiny, tipi, stats, abilita, altezza, peso, categoria_forma.
"""
import json
import os
import sys
import time

import requests

BASE = "https://pokeapi.co/api/v2"
SESSION = requests.Session()
FILE = "pokedex_data.json"


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


def categoria_forma(nome_api: str) -> str:
    """Determina categoria della forma dal nome_api."""
    n = nome_api.lower()
    if "-mega-x" in n or "-mega-y" in n: return "mega"
    if "-mega" in n: return "mega"
    if "-gmax" in n: return "gmax"
    if "-alola" in n: return "alola"
    if "-galar" in n: return "galar"
    if "-hisui" in n: return "hisui"
    if "-paldea" in n: return "paldea"
    if "-totem" in n: return "totem"
    if "-primal" in n: return "primal"
    return "alt"


def estrai_forma(v_data, default_descrizione=""):
    """Da risposta /pokemon/{id} ad oggetto forma."""
    pid = v_data["id"]
    sprite = (
        v_data["sprites"].get("other", {}).get("official-artwork", {}).get("front_default")
        or v_data["sprites"].get("front_default")
        or f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png"
    )
    sprite_shiny = (
        v_data["sprites"].get("other", {}).get("official-artwork", {}).get("front_shiny")
        or v_data["sprites"].get("front_shiny")
    )
    return {
        "nome": v_data["name"].replace("-", " ").title(),
        "nome_api": v_data["name"],
        "sprite": sprite,
        "sprite_shiny": sprite_shiny,
        "stats": {s["stat"]["name"]: s["base_stat"] for s in v_data["stats"]},
        "tipi": [t["type"]["name"] for t in v_data["types"]],
        "abilita": [a["ability"]["name"] for a in v_data["abilities"]],
        "altezza": v_data["height"] / 10,
        "peso": v_data["weight"] / 10,
        "categoria": categoria_forma(v_data["name"]),
    }


def main():
    with open(FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Pokemon nel JSON: {len(data)}")
    aggiornate = 0

    for p in data:
        # Se ha già "forme" non vuoto, skip (idempotente)
        if "forme" in p and isinstance(p["forme"], list) and p["forme"]:
            continue

        species = get_json(f"{BASE}/pokemon-species/{p['id']}")
        if not species:
            p["forme"] = []
            continue

        forme = []
        for var in species.get("varieties", []):
            v_name = var["pokemon"]["name"]
            # Skippo la forma base (è il pokemon stesso)
            if v_name == p["nome_api"]:
                continue
            v_data = get_json(var["pokemon"]["url"])
            if not v_data:
                continue
            forme.append(estrai_forma(v_data))

        p["forme"] = forme
        if forme:
            cats = ", ".join(set(f["categoria"] for f in forme))
            print(f"[{p['id']:4d}] {p['nome']:18s} +{len(forme)} forme ({cats})")
            aggiornate += 1

        # Migra "mega" legacy se esistente in nuovo "forme"
        # (mantenuto per retrocompat, ma se vogliamo possiamo rimuoverlo)

        if p["id"] % 50 == 0:
            with open(FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            print(f"  -> checkpoint @ id={p['id']}")

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(FILE) / 1024 / 1024
    print(f"\nFatto. {aggiornate} Pokemon aggiornati con forme. File: {size:.2f} MB")


if __name__ == "__main__":
    sys.exit(main())
