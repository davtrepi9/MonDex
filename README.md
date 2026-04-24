# MonDex Data

Repository dei dati JSON per l'app **MonDex** (companion competitivo fan-made, non ufficiale, non affiliato a Nintendo / Game Freak / The Pokémon Company).

I dati vengono aggiornati automaticamente da GitHub Actions ogni settimana e consumati dall'app via raw URL.

## Struttura

```
data/
  meta.json              # timestamp ultimo update + size dei file
  pokedex_data.json      # 1025 mon (stats, abilità, sprite URL, mega/gmax/regional forms)
  champions_data.json    # 268 mon Champions roster con build/mosse/abilità/items
  champions_teams.json   # 462 team competitivi da tornei
  moves.json             # 937 mosse + meta (paralisi%, flinch%, drain, ecc.)
  items.json             # 2175 item con descrizioni
  abilities.json         # 371 abilità
  pokemon_movesets.json  # learnsets per ogni mon
  natures.json           # 25 nature
  ev_spreads.json        # 24 EV spread VGC consigliate (curate manualmente)

scripts/
  update_all.py          # orchestrator (quick / full mode)
  fetch_*.py             # scraper individuali per ogni dataset

.github/workflows/
  update-data.yml        # cron settimanale + dispatch manuale
```

## Aggiornamento

### Automatico
- **Ogni Lunedì 03:00 UTC**: GitHub Actions esegue `update_all.py --quick` (Champions + teams + EV spreads)
- Commit automatico se ci sono cambi
- L'app legge i nuovi dati al prossimo avvio

### Manuale
1. Vai su [Actions](../../actions) → "Update MonDex data" → "Run workflow"
2. Scegli mode:
   - `quick` (~10 min) — Champions, teams, EV spreads
   - `full` (~30 min) — Tutto, incluso refetch PokéAPI

### Locale
```bash
cd scripts
pip install requests
python update_all.py --quick
```

## Fonti dati

| Fonte | Licenza | Cosa |
|---|---|---|
| [PokéAPI](https://pokeapi.co) | CC BY-NC-SA 2.5 | Stats, mosse, abilità, item, sprite URL |
| [Pokebase.app](https://pokebase.app) | Public web data | Roster Champions, team da tornei |
| Curato manualmente | — | EV spreads consigliate |

## Disclaimer

Progetto fan-made non ufficiale. Pokémon™, Pokédex™, Pokémon Champions™ e i nomi dei singoli personaggi sono marchi registrati di Nintendo / Game Freak / The Pokémon Company. Tutti i diritti dei loro rispettivi proprietari sono riconosciuti.

Uso consentito: personale, non commerciale.

Per richieste di rimozione da parte dei detentori dei marchi, aprire una issue.
