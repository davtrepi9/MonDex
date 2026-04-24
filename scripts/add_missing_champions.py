"""Aggiunge i Champions Pokemon mancanti dal champions_data.json."""
import json
import sys

sys.path.insert(0, '.')
from fetch_champions import fetch, parse_pagina, BASE

MISSING = ["hawlucha", "meowstic", "rotom-frost", "maushold"]

OUT_FILE = "champions_data.json"


def main():
    with open(OUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Rimuovi vecchi Pokemon non più nel meta
    REMOVED = ["tinkaton", "espathra", "pinsir"]
    for r in REMOVED:
        if r in data:
            del data[r]
            print(f"  - rimosso {r}")

    for slug in MISSING:
        if slug in data and data[slug].get("builds"):
            print(f"  ~ {slug} gia presente, skip")
            continue
        print(f"  Fetching {slug}...")
        html = fetch(f"{BASE}/pokemon/{slug}")
        if not html:
            print(f"  ! {slug} FAIL")
            continue
        info = parse_pagina(html, slug)
        data[slug] = info
        print(f"  + {slug}: m={len(info['mosse'])} a={len(info['abilita'])} "
              f"i={len(info['items'])} b={len(info['builds'])}")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"\nFatto. {len(data)} Champions totali.")


if __name__ == "__main__":
    main()
