"""
Scarica tutti i 1025 Pokémon da PokéAPI e crea un JSON unico.
Output: pokedex_data.json (~2-3 MB)

Uso:
    python fetch_all_pokemon.py
"""
import json
import os
import sys
import time

import requests

BASE = "https://pokeapi.co/api/v2"
OUT_FILE = "pokedex_data.json"
TOTALE_POKEMON = 1025  # Tutte le 9 generazioni


# Mappa offset → generazione (basata sugli ID PokéAPI)
def gen_da_id(pid):
    if pid <= 151: return 1
    if pid <= 251: return 2
    if pid <= 386: return 3
    if pid <= 493: return 4
    if pid <= 649: return 5
    if pid <= 721: return 6
    if pid <= 809: return 7
    if pid <= 905: return 8
    return 9


def get_json(url, retry=3):
    for tentativo in range(retry):
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
        except requests.RequestException:
            time.sleep(1)
    return None


def fetch_pokemon(pid):
    """Restituisce dict con dati essenziali, oppure None."""
    p = get_json(f"{BASE}/pokemon/{pid}")
    if not p:
        return None

    # Dati di specie (descrizione, colore, abitat)
    species = get_json(f"{BASE}/pokemon-species/{pid}")
    descrizione = ""
    if species:
        for entry in species.get("flavor_text_entries", []):
            if entry["language"]["name"] == "en":
                descrizione = entry["flavor_text"].replace("\n", " ").replace("\f", " ")
                break

    sprite = (
        p["sprites"].get("other", {}).get("official-artwork", {}).get("front_default")
        or p["sprites"].get("front_default")
        or f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png"
    )
    sprite_pixel = (
        p["sprites"].get("front_default")
        or f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pid}.png"
    )

    return {
        "id": p["id"],
        "nome": p["name"].capitalize(),
        "nome_api": p["name"],
        "tipi": [t["type"]["name"] for t in p["types"]],
        "altezza": p["height"] / 10,  # m
        "peso": p["weight"] / 10,     # kg
        "sprite": sprite,
        "sprite_pixel": sprite_pixel,
        "stats": {s["stat"]["name"]: s["base_stat"] for s in p["stats"]},
        "abilita": [a["ability"]["name"] for a in p["abilities"]],
        "descrizione": descrizione,
        "gen": gen_da_id(p["id"]),
    }


def main():
    risultati = []

    # Riprendi da cache se esiste
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, "r", encoding="utf-8") as f:
            risultati = json.load(f)
        print(f"Ripreso da {len(risultati)} Pokémon già salvati.")

    ids_fatti = {p["id"] for p in risultati}

    for pid in range(1, TOTALE_POKEMON + 1):
        if pid in ids_fatti:
            continue

        info = fetch_pokemon(pid)
        if info:
            risultati.append(info)
            print(f"[{pid:4d}/{TOTALE_POKEMON}] {info['nome']:20s} (Gen {info['gen']})")
        else:
            print(f"[{pid:4d}] FALLITO, salto")

        # Salva ogni 50 per non perdere progressi
        if pid % 50 == 0:
            risultati.sort(key=lambda p: p["id"])
            with open(OUT_FILE, "w", encoding="utf-8") as f:
                json.dump(risultati, f, ensure_ascii=False, indent=None, separators=(",", ":"))
            print(f"  -> checkpoint salvato ({len(risultati)} Pokemon)")

    # Salvataggio finale ordinato
    risultati.sort(key=lambda p: p["id"])
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(risultati, f, ensure_ascii=False, indent=None, separators=(",", ":"))

    size_mb = os.path.getsize(OUT_FILE) / (1024 * 1024)
    print(f"\nFatto. {len(risultati)} Pokemon salvati in {OUT_FILE} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    sys.exit(main())
