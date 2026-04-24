"""Cerca i filtri attivi e tutte le opzioni disponibili."""
import asyncio
import sys

from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 1800},
        )
        page = await ctx.new_page()

        await page.goto("https://pokebase.app/pokemon-champions/pokemon",
                        wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(8000)  # lascia tempo al JS di renderizzare

        # Estrai info filtri
        info = await page.evaluate('''
            () => {
                const data = {};

                // Cerca tutti i select e le opzioni
                const selects = document.querySelectorAll('select');
                data.selects = Array.from(selects).map(s => ({
                    id: s.id, name: s.name,
                    value: s.value,
                    options: Array.from(s.options).map(o => ({val: o.value, text: o.text}))
                }));

                // Cerca text "results" o "shown"
                const allText = document.body.innerText;
                const numMatches = [...allText.matchAll(/(\\d+)\\s+(results|shown|of\\s+\\d+)/gi)];
                data.counters = numMatches.map(m => m[0]).slice(0, 10);

                // Headings nelle filter sections
                const filterSections = document.querySelectorAll('h2, h3');
                data.sections = Array.from(filterSections).map(h => h.textContent.trim()).slice(0, 15);

                // Tutti gli A href con conteggio (potrebbe essere paginazione)
                const all = document.querySelectorAll('a, button');
                const numericTexts = Array.from(all)
                    .map(a => a.textContent.trim())
                    .filter(t => /^\\d+$/.test(t))
                    .slice(0, 30);
                data.numericButtons = numericTexts;

                // Cerca div con scrollHeight maggiore
                const scrollables = [];
                document.querySelectorAll('div').forEach(d => {
                    if (d.scrollHeight > d.clientHeight + 200) {
                        scrollables.push({
                            sh: d.scrollHeight,
                            ch: d.clientHeight,
                            cls: (d.className || '').substring(0, 60),
                        });
                    }
                });
                data.scrollableDivs = scrollables.slice(0, 10);

                return data;
            }
        ''')

        import json
        print(json.dumps(info, indent=2, ensure_ascii=False))
        await browser.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
