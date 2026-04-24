"""
Orchestrator: esegue tutti i fetch necessari per aggiornare il dataset MonDex.
Pensato per essere eseguito da GitHub Actions una volta a settimana.

Usage:
    python update_all.py [--quick]   # quick = solo Champions + teams + moves
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Lista step. Ognuno: (nome, script, output_files)
STEPS_FULL = [
    ("Pokémon base 1-1025", "fetch_all_pokemon.py", ["pokedex_data.json"]),
    ("Forme alt (mega/gmax/regional)", "add_all_forms.py", ["pokedex_data.json"]),
    ("Forme cosmetiche", "add_cosmetic_forms.py", ["pokedex_data.json"]),
    ("Sprite shiny mega", "add_mega_shiny.py", ["pokedex_data.json"]),
    ("Sprite 3D HOME", "add_3d_sprites.py", ["pokedex_data.json"]),
    ("Mosse + meta", ("fetch_competitive.py", "moves"), ["moves.json"]),
    ("Items", ("fetch_competitive.py", "items"), ["items.json"]),
    ("Abilità", ("fetch_competitive.py", "abilities"), ["abilities.json"]),
    ("Nature", ("fetch_competitive.py", "natures"), ["natures.json"]),
    ("Movesets per ID", ("fetch_competitive.py", "movesets"), ["pokemon_movesets.json"]),
    ("Champions roster (268)", "fetch_champions.py", ["champions_data.json"]),
    ("Fix icons missing Champions", "fix_missing_icons.py", ["champions_data.json"]),
    ("Teams competitivi", "fetch_teams.py", ["champions_teams.json"]),
    ("EV spreads consigliate", "ev_spreads.py", ["ev_spreads.json"]),
]

STEPS_QUICK = [
    ("Champions roster", "fetch_champions.py", ["champions_data.json"]),
    ("Fix icons missing Champions", "fix_missing_icons.py", ["champions_data.json"]),
    ("Teams competitivi", "fetch_teams.py", ["champions_teams.json"]),
    ("EV spreads consigliate", "ev_spreads.py", ["ev_spreads.json"]),
]


def run_step(nome, script_or_cmd):
    print(f"\n{'='*70}")
    print(f"  {nome}")
    print(f"{'='*70}")
    if isinstance(script_or_cmd, tuple):
        cmd = ["python", script_or_cmd[0], *script_or_cmd[1:]]
    else:
        cmd = ["python", script_or_cmd]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    res = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=False)
    return res.returncode == 0


def copia_in_data():
    """Copia tutti i .json da scripts/ a data/."""
    for f in ROOT.glob("*.json"):
        dest = DATA_DIR / f.name
        dest.write_bytes(f.read_bytes())
        print(f"  -> copied {f.name}")


def aggiorna_meta():
    """Crea meta.json con timestamp + dimensioni file."""
    meta = {
        "updated_at": dt.datetime.utcnow().isoformat() + "Z",
        "files": {},
    }
    for f in DATA_DIR.glob("*.json"):
        if f.name == "meta.json":
            continue
        meta["files"][f.name] = {
            "size": f.stat().st_size,
            "modified": dt.datetime.utcfromtimestamp(f.stat().st_mtime).isoformat() + "Z",
        }
    (DATA_DIR / "meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    print(f"\n  meta.json -> updated_at={meta['updated_at']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true",
                        help="Solo Champions+teams (rapido, ~10 min)")
    args = parser.parse_args()

    steps = STEPS_QUICK if args.quick else STEPS_FULL
    print(f"\nMonDex updater · {'QUICK' if args.quick else 'FULL'} mode")
    print(f"  {len(steps)} step da eseguire\n")

    falliti = []
    for nome, script_or_cmd, _ in steps:
        ok = run_step(nome, script_or_cmd)
        if not ok:
            falliti.append(nome)
            print(f"  ⚠ {nome} FAIL — continuo comunque")

    print("\nCopia dati in data/")
    copia_in_data()

    print("\nAggiorno meta.json")
    aggiorna_meta()

    print(f"\n{'='*70}")
    if falliti:
        print(f"  COMPLETATO con {len(falliti)} errori:")
        for f in falliti:
            print(f"    - {f}")
        sys.exit(1)
    else:
        print(f"  ✅ COMPLETATO senza errori")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
