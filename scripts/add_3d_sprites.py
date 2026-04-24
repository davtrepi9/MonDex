"""
Aggiunge sprite 3D ufficiali (Pokemon HOME render) per ogni Pokemon.
Campo: sprite_home + sprite_home_shiny.

Per le mega/forme aggiunge anche il loro sprite home se disponibile.
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
        except requests.RequestException:
            time.sleep(1)
    return None


def fetch_home(nome_api):
    p = get_json(f"{BASE}/pokemon/{nome_api}")
    if not p:
        return None, None
    home = p["sprites"].get("other", {}).get("home", {})
    return home.get("front_default"), home.get("front_shiny")


def main():
    with open(FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    aggiornati = 0
    for p in data:
        if p.get("sprite_home"):
            continue
        home, home_shiny = fetch_home(p["nome_api"])
        if home:
            p["sprite_home"] = home
            if home_shiny:
                p["sprite_home_shiny"] = home_shiny
            aggiornati += 1

        # Anche per le forme
        for f_ in p.get("forme") or []:
            if f_.get("sprite_home"):
                continue
            h, hs = fetch_home(f_["nome_api"])
            if h:
                f_["sprite_home"] = h
                if hs:
                    f_["sprite_home_shiny"] = hs

        if p["id"] % 50 == 0:
            with open(FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            print(f"[{p['id']:4d}] checkpoint, {aggiornati} aggiornati")

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(FILE) / 1024 / 1024
    print(f"\nFatto. {aggiornati} sprite_home aggiunti. File: {size:.2f} MB")


if __name__ == "__main__":
    sys.exit(main())
