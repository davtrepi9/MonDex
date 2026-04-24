"""Ispeziona la pagina pokebase per trovare filtri/contatori/tab nascosti."""
import asyncio
import sys

from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()

        await page.goto("https://pokebase.app/pokemon-champions/pokemon",
                        wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)

        # Estrai tutti i link rilevanti, contatori, bottoni filtro
        info = await page.evaluate('''
            () => {
                const data = {};
                // Numeri visibili sulla pagina
                const allText = document.body.innerText;
                const numMatches = allText.match(/\\b(\\d{2,4})\\s+(pokemon|Pokemon|Pokémon|results|risultati)/gi) || [];
                data.numbers = numMatches.slice(0, 10);

                // Bottoni di filtro/tab
                const buttons = document.querySelectorAll('button, [role="button"], [class*="tab"], [class*="filter"], [class*="toggle"]');
                data.buttons = Array.from(buttons).slice(0, 30).map(b => b.textContent.trim().substring(0, 50)).filter(t => t);

                // Tutti gli href delle pagine pokemon-champions
                const links = document.querySelectorAll('a[href*="/pokemon-champions/"]');
                const slugs = new Set();
                const fullUrls = new Set();
                links.forEach(a => {
                    fullUrls.add(a.href);
                    const m = a.href.match(/\\/pokemon-champions\\/pokemon\\/([^\\/?#]+)/);
                    if (m) slugs.add(m[1]);
                });
                data.totalLinks = links.length;
                data.uniquePokemonSlugs = slugs.size;
                data.uniqueFullUrls = fullUrls.size;
                data.firstUrls = Array.from(fullUrls).slice(0, 15);

                // Heading h1, h2
                const headings = document.querySelectorAll('h1, h2, h3');
                data.headings = Array.from(headings).slice(0, 10).map(h => h.textContent.trim().substring(0, 80));

                return data;
            }
        ''')

        import json
        print(json.dumps(info, indent=2, ensure_ascii=False))

        await browser.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
