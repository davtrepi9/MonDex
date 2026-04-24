"""Test parser Pikalytics su un singolo Pokemon - cerca SPREADS."""
import asyncio
import sys

from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await ctx.new_page()

        await page.goto("https://www.pikalytics.com/pokedex/championstournaments/Azumarill?l=en",
                        wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000)

        # Trova il wrapper che contiene "EV Spread" o ev structure
        result = await page.evaluate('''
            () => {
                // Cerca un titolo "Best EV Spread"
                const titles = document.querySelectorAll('.pokedex-section-title-inline, h2, h3');
                const spreadTitle = Array.from(titles).find(t =>
                    t.textContent.toLowerCase().includes('spread'));
                if (!spreadTitle) return {found: false};

                // Risali al parent comune
                let container = spreadTitle.parentElement;
                while (container && !container.querySelector('.pokedex-move-entry-new')) {
                    container = container.parentElement;
                    if (!container) break;
                }
                if (!container) return {found: 'title-only', title: spreadTitle.textContent};

                // Estrai entries
                const entries = container.querySelectorAll('.pokedex-move-entry-new');
                const data = [];
                entries.forEach(e => {
                    const offset = e.querySelector('.pokedex-inline-text-offset');
                    const evs = e.querySelectorAll('.pokedex-inline-text');
                    const right = e.querySelector('.pokedex-inline-right');
                    data.push({
                        nature: offset ? offset.textContent.trim() : '',
                        evs: Array.from(evs).map(x => x.textContent.trim()),
                        percent: right ? right.textContent.trim() : '',
                    });
                });
                return {
                    found: true,
                    containerId: container.id,
                    containerClass: container.className,
                    entriesCount: entries.length,
                    sample: data.slice(0, 5),
                };
            }
        ''')
        print("=== SPREADS DETECTION ===")
        import json
        print(json.dumps(result, indent=2))

        # Cerca tutti i titoli
        titles = await page.evaluate('''
            () => {
                const ts = document.querySelectorAll('.pokedex-section-title-inline, .pokedex-section-title');
                return Array.from(ts).map(t => ({text: t.textContent.trim(), parentId: t.closest('[id]')?.id || ''}));
            }
        ''')
        print("\n=== SECTION TITLES ===")
        for t in titles[:20]:
            print(f"  parent={t['parentId']:25s} title={t['text'][:60]}")

        await browser.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
