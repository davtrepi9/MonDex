"""Re-scrape SOLO i Pokemon Champions senza icona, per beccare quelli 'preview'."""
import json
import sys

sys.path.insert(0, '.')
from fetch_champions import fetch, parse_pagina, BASE


def main():
    with open("champions_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    senza = [k for k, v in data.items() if not v.get("icona")]
    print(f"Pokemon senza icona: {len(senza)}")

    fixed = 0
    for i, slug in enumerate(senza, 1):
        html = fetch(f"{BASE}/pokemon/{slug}")
        if not html:
            print(f"  [{i:3d}/{len(senza)}] {slug:30s} FAIL")
            continue
        info = parse_pagina(html, slug)
        if info.get("icona"):
            data[slug] = info  # aggiorna anche tutto il resto
            fixed += 1
            print(f"  [{i:3d}/{len(senza)}] {slug:30s} OK icona={info['icona'][:60]}")
        else:
            print(f"  [{i:3d}/{len(senza)}] {slug:30s} no icon found")

        if i % 25 == 0:
            with open("champions_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            print("  -> checkpoint")

    with open("champions_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"\nFatto. {fixed}/{len(senza)} icone aggiunte")


if __name__ == "__main__":
    sys.exit(main())
