"""
Pokebase ha 268 Pokemon su 3 pagine (?page=1,2,3). Scarica tutti gli slug.
"""
import re
import sys
import urllib.request


def fetch_page(p: int) -> set:
    url = f"https://pokebase.app/pokemon-champions/pokemon?page={p}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")
    return set(re.findall(r'href="/pokemon-champions/pokemon/([^"]+)"', html))


def main():
    tutti = set()
    for p in range(1, 5):  # ne provo fino a 4
        slugs = fetch_page(p)
        if not slugs:
            print(f"  pagina {p} vuota")
            break
        nuovi = slugs - tutti
        tutti.update(slugs)
        print(f"  pagina {p}: {len(slugs)} totali ({len(nuovi)} nuovi) - cumulativo {len(tutti)}")
        if not nuovi and p > 1:
            print("  nessun nuovo, fine paginazione")
            break

    print(f"\nTotale unici: {len(tutti)}")
    with open("champions_all_slugs.txt", "w", encoding="utf-8") as f:
        for s in sorted(tutti):
            f.write(s + "\n")
    print("Salvato in champions_all_slugs.txt")


if __name__ == "__main__":
    sys.exit(main())
