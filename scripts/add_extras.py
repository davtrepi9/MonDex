"""
Aggiunge dati extra al pokedex_data.json:
- sprite_shiny (URL official artwork shiny)
- mega_evolutions: lista di {nome, nome_api, sprite, stats, abilita} per le mega del Pokémon

Uso: python add_extras.py
"""
import json
import os
import sys
import time

import requests

BASE = "https://pokeapi.co/api/v2"
SESSION = requests.Session()
IN_FILE = "pokedex_data.json"
OUT_FILE = "pokedex_data.json"


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


def fetch_shiny_e_mega(pid, nome_api):
    """Ritorna (sprite_shiny_url, lista_mega) per un Pokémon."""
    p = get_json(f"{BASE}/pokemon/{pid}")
    if not p:
        return None, []

    shiny = (
        p["sprites"].get("other", {}).get("official-artwork", {}).get("front_shiny")
        or p["sprites"].get("front_shiny")
        or f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{pid}.png"
    )

    # Mega: cerca nelle varietà della specie
    species = get_json(f"{BASE}/pokemon-species/{pid}")
    mega_list = []
    if species:
        for var in species.get("varieties", []):
            v_name = var["pokemon"]["name"]
            if "mega" in v_name and v_name != nome_api:
                v_data = get_json(var["pokemon"]["url"])
                if not v_data:
                    continue
                mega_list.append({
                    "nome": v_data["name"].replace("-", " ").title(),
                    "nome_api": v_data["name"],
                    "sprite": (
                        v_data["sprites"].get("other", {}).get("official-artwork", {}).get("front_default")
                        or v_data["sprites"].get("front_default")
                    ),
                    "stats": {s["stat"]["name"]: s["base_stat"] for s in v_data["stats"]},
                    "tipi": [t["type"]["name"] for t in v_data["types"]],
                    "abilita": [a["ability"]["name"] for a in v_data["abilities"]],
                    "altezza": v_data["height"] / 10,
                    "peso": v_data["weight"] / 10,
                })
    return shiny, mega_list


def main():
    with open(IN_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Aggiornamento di {len(data)} Pokémon...")
    n_aggiornati = 0
    for p in data:
        if p.get("sprite_shiny") and "mega" in p:
            continue
        shiny, megas = fetch_shiny_e_mega(p["id"], p["nome_api"])
        if shiny:
            p["sprite_shiny"] = shiny
        p["mega"] = megas

        if p["id"] % 25 == 0:
            with open(OUT_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            print(f"[{p['id']:4d}/{len(data)}] checkpoint salvato")
        n_aggiornati += 1

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(OUT_FILE) / 1024 / 1024
    print(f"\nFatto. {n_aggiornati} aggiornati. File: {size:.2f} MB")


if __name__ == "__main__":
    sys.exit(main())
