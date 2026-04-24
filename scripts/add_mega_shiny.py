"""
Aggiunge sprite_shiny alle mega forme già presenti in pokedex_data.json
"""
import json
import os
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


def fetch_shiny(nome_api):
    p = get_json(f"{BASE}/pokemon/{nome_api}")
    if not p:
        return None
    return (
        p["sprites"].get("other", {}).get("official-artwork", {}).get("front_shiny")
        or p["sprites"].get("front_shiny")
    )


def main():
    with open(FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    aggiornate = 0
    for p in data:
        for m in p.get("mega") or []:
            if m.get("sprite_shiny"):
                continue
            shiny = fetch_shiny(m["nome_api"])
            if shiny:
                m["sprite_shiny"] = shiny
                aggiornate += 1
                print(f"  + {m['nome']} shiny aggiunto")

        if aggiornate > 0 and aggiornate % 10 == 0:
            with open(FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(FILE) / 1024 / 1024
    print(f"\nFatto. {aggiornate} mega shiny aggiunte. File: {size:.2f} MB")


if __name__ == "__main__":
    main()
