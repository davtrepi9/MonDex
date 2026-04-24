"""
Scarica dati competitivi da PokéAPI per supporto giocatori:
- Tutte le mosse (potenza, accuratezza, PP, effetto)
- Tutti gli oggetti (descrizione, categoria, effetto)
- Tutte le abilità (descrizione, nascosta sì/no)
- Nature (bonus/malus stats)
- Learnset per ogni Pokémon (mosse imparabili e come)

Output:
- moves.json
- items.json
- abilities.json
- natures.json
- pokemon_movesets.json (mappa pokemon_id -> mosse imparabili)

Riprende automaticamente da checkpoint.
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE = "https://pokeapi.co/api/v2"
SESSION = requests.Session()


def get_json(url, retry=3):
    for tentativo in range(retry):
        try:
            r = SESSION.get(url, timeout=20)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
        except requests.RequestException:
            time.sleep(1)
    return None


def estrai_testo_en(entries, key="flavor_text", lang_key="language"):
    """Estrae testo inglese, prova 'flavor_text' poi 'text' se manca."""
    for e in entries:
        if e[lang_key]["name"] != "en":
            continue
        valore = e.get(key) or e.get("text") or e.get("flavor_text") or e.get("short_effect") or e.get("effect")
        if valore:
            return valore.replace("\n", " ").replace("\f", " ").strip()
    return ""


_ROMAN_TO_INT = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5,
                 "vi": 6, "vii": 7, "viii": 8, "ix": 9}


def parse_gen(gen_obj):
    """Restituisce numero gen 1-9 da {'name': 'generation-iii'} o 0."""
    if not gen_obj or "name" not in gen_obj:
        return 0
    parti = gen_obj["name"].split("-")
    if len(parti) < 2:
        return 0
    return _ROMAN_TO_INT.get(parti[-1].lower(), 0)


# ── MOSSE ───────────────────────────────────────────────────────────
def fetch_mossa(mid):
    m = get_json(f"{BASE}/move/{mid}")
    if not m:
        return None

    meta = m.get("meta") or {}
    ailment = meta.get("ailment", {})
    ailment_name = ailment.get("name") if ailment else None
    if ailment_name == "none":
        ailment_name = None

    return {
        "id": m["id"],
        "nome": m["name"].replace("-", " ").title(),
        "nome_api": m["name"],
        "tipo": m["type"]["name"],
        "categoria": m["damage_class"]["name"] if m.get("damage_class") else "status",
        "potenza": m["power"],
        "precisione": m["accuracy"],
        "pp": m["pp"],
        "priorita": m["priority"],
        "effetto": estrai_testo_en(m.get("effect_entries", []), key="short_effect"),
        "descrizione": estrai_testo_en(m.get("flavor_text_entries", [])),
        "target": m["target"]["name"] if m.get("target") else "",
        "generazione": parse_gen(m.get("generation")),
        # Effect chance (es. 30% per Body Slam paralisi, 100% per Will-O-Wisp)
        "effect_chance": m.get("effect_chance"),
        # Meta: dettagli su effetti secondari
        "ailment": ailment_name,            # paralysis, burn, freeze, sleep, poison, confusion, ...
        "ailment_chance": meta.get("ailment_chance", 0) or 0,
        "flinch_chance": meta.get("flinch_chance", 0) or 0,
        "stat_chance": meta.get("stat_chance", 0) or 0,
        "crit_rate": meta.get("crit_rate", 0) or 0,
        "drain": meta.get("drain", 0) or 0,        # negativo = recoil; positivo = drain
        "healing": meta.get("healing", 0) or 0,
        "min_hits": meta.get("min_hits"),
        "max_hits": meta.get("max_hits"),
        "min_turns": meta.get("min_turns"),
        "max_turns": meta.get("max_turns"),
        # Stat changes che la mossa applica (es. Swords Dance +2 Atk)
        "stat_changes": [
            {"stat": s["stat"]["name"], "change": s["change"]}
            for s in m.get("stat_changes", [])
        ],
    }


def fetch_tutte_mosse(out_file="moves.json"):
    print("=== Scaricamento mosse ===")
    risultati = []
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            risultati = json.load(f)
        print(f"Ripreso da {len(risultati)} mosse.")

    fatti = {m["id"] for m in risultati}
    elenco = get_json(f"{BASE}/move?limit=2000")
    if not elenco:
        print("Errore lista mosse")
        return
    totale = elenco["count"]
    print(f"Totale mosse disponibili: {totale}")

    for ref in elenco["results"]:
        mid = int(ref["url"].rstrip("/").split("/")[-1])
        if mid in fatti:
            continue
        info = fetch_mossa(mid)
        if info:
            risultati.append(info)
            print(f"[{len(risultati):4d}] {info['nome']:30s} {info['tipo']:10s} {info.get('potenza','-')}")
        if len(risultati) % 50 == 0:
            risultati.sort(key=lambda x: x["id"])
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(risultati, f, ensure_ascii=False, separators=(",", ":"))

    risultati.sort(key=lambda x: x["id"])
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(risultati, f, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(out_file) / 1024 / 1024
    print(f"OK: {len(risultati)} mosse in {out_file} ({size:.2f} MB)")


# ── OGGETTI ─────────────────────────────────────────────────────────
def fetch_oggetto(iid):
    it = get_json(f"{BASE}/item/{iid}")
    if not it:
        return None
    return {
        "id": it["id"],
        "nome": it["name"].replace("-", " ").title(),
        "nome_api": it["name"],
        "costo": it.get("cost", 0),
        "fling_power": it.get("fling_power"),
        "categoria": it["category"]["name"] if it.get("category") else "",
        "sprite": it["sprites"].get("default") if it.get("sprites") else None,
        "effetto": estrai_testo_en(it.get("effect_entries", []), key="short_effect"),
        "descrizione": estrai_testo_en(it.get("flavor_text_entries", [])),
        "attributi": [a["name"] for a in it.get("attributes", [])],
    }


def fetch_tutti_oggetti(out_file="items.json"):
    print("\n=== Scaricamento oggetti ===")
    risultati = []
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            risultati = json.load(f)
        print(f"Ripreso da {len(risultati)} oggetti.")

    fatti = {x["id"] for x in risultati}
    elenco = get_json(f"{BASE}/item?limit=3000")
    if not elenco:
        return
    print(f"Totale oggetti disponibili: {elenco['count']}")

    for ref in elenco["results"]:
        iid = int(ref["url"].rstrip("/").split("/")[-1])
        if iid in fatti:
            continue
        info = fetch_oggetto(iid)
        if info:
            risultati.append(info)
            print(f"[{len(risultati):4d}] {info['nome']:35s} ({info['categoria']})")
        if len(risultati) % 50 == 0:
            risultati.sort(key=lambda x: x["id"])
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(risultati, f, ensure_ascii=False, separators=(",", ":"))

    risultati.sort(key=lambda x: x["id"])
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(risultati, f, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(out_file) / 1024 / 1024
    print(f"OK: {len(risultati)} oggetti ({size:.2f} MB)")


# ── ABILITÀ ─────────────────────────────────────────────────────────
def fetch_abilita(aid):
    a = get_json(f"{BASE}/ability/{aid}")
    if not a:
        return None
    return {
        "id": a["id"],
        "nome": a["name"].replace("-", " ").title(),
        "nome_api": a["name"],
        "effetto": estrai_testo_en(a.get("effect_entries", []), key="short_effect"),
        "descrizione": estrai_testo_en(a.get("flavor_text_entries", [])),
        "generazione": parse_gen(a.get("generation")),
        "is_main_series": a.get("is_main_series", True),
    }


def fetch_tutte_abilita(out_file="abilities.json"):
    print("\n=== Scaricamento abilità ===")
    risultati = []
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            risultati = json.load(f)
        print(f"Ripreso da {len(risultati)} abilità.")

    fatti = {x["id"] for x in risultati}
    elenco = get_json(f"{BASE}/ability?limit=500")
    if not elenco:
        return
    print(f"Totale abilità disponibili: {elenco['count']}")

    for ref in elenco["results"]:
        aid = int(ref["url"].rstrip("/").split("/")[-1])
        if aid in fatti:
            continue
        info = fetch_abilita(aid)
        if info:
            risultati.append(info)
            print(f"[{len(risultati):4d}] {info['nome']}")
        if len(risultati) % 30 == 0:
            risultati.sort(key=lambda x: x["id"])
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(risultati, f, ensure_ascii=False, separators=(",", ":"))

    risultati.sort(key=lambda x: x["id"])
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(risultati, f, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(out_file) / 1024 / 1024
    print(f"OK: {len(risultati)} abilità ({size:.2f} MB)")


# ── NATURE ──────────────────────────────────────────────────────────
def fetch_tutte_nature(out_file="natures.json"):
    print("\n=== Scaricamento nature ===")
    elenco = get_json(f"{BASE}/nature?limit=30")
    risultati = []
    for ref in elenco["results"]:
        n = get_json(ref["url"])
        if not n:
            continue
        risultati.append({
            "id": n["id"],
            "nome": n["name"].title(),
            "stat_aumentata": n["increased_stat"]["name"] if n.get("increased_stat") else None,
            "stat_diminuita": n["decreased_stat"]["name"] if n.get("decreased_stat") else None,
            "gusto_preferito": n["likes_flavor"]["name"] if n.get("likes_flavor") else None,
            "gusto_odiato": n["hates_flavor"]["name"] if n.get("hates_flavor") else None,
        })
        print(f"[{len(risultati):2d}] {risultati[-1]['nome']}")

    risultati.sort(key=lambda x: x["id"])
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(risultati, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(risultati)} nature")


# ── LEARNSETS POKÉMON ───────────────────────────────────────────────
def fetch_learnset(pid):
    """Restituisce il learnset di un Pokémon: mosse + come si imparano."""
    p = get_json(f"{BASE}/pokemon/{pid}")
    if not p:
        return None
    mosse = []
    for m in p["moves"]:
        nome_mossa = m["move"]["name"]
        # Prendi la versione più recente (ultima nel version_group_details)
        if not m["version_group_details"]:
            continue
        ultima = m["version_group_details"][-1]
        mosse.append({
            "mossa": nome_mossa,
            "metodo": ultima["move_learn_method"]["name"],  # level-up, machine, egg, tutor
            "livello": ultima["level_learned_at"],
            "version_group": ultima["version_group"]["name"],
        })
    return {
        "pokemon_id": p["id"],
        "abilita": [
            {"nome": a["ability"]["name"], "nascosta": a["is_hidden"], "slot": a["slot"]}
            for a in p["abilities"]
        ],
        "mosse": mosse,
    }


def fetch_tutti_learnset(out_file="pokemon_movesets.json", totale=1025):
    print(f"\n=== Scaricamento learnsets ({totale} Pokémon) ===")
    risultati = {}
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            risultati = json.load(f)
        print(f"Ripreso da {len(risultati)} learnset.")

    for pid in range(1, totale + 1):
        if str(pid) in risultati:
            continue
        info = fetch_learnset(pid)
        if info:
            risultati[str(pid)] = info
            print(f"[{pid:4d}/{totale}] {len(info['mosse'])} mosse, {len(info['abilita'])} abilita")
        if pid % 50 == 0:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(risultati, f, ensure_ascii=False, separators=(",", ":"))
            print(f"  -> checkpoint")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(risultati, f, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(out_file) / 1024 / 1024
    print(f"OK: {len(risultati)} learnset ({size:.2f} MB)")


def main():
    if len(sys.argv) < 2:
        print("Uso: python fetch_competitive.py [moves|items|abilities|natures|movesets|all]")
        return 1

    cmd = sys.argv[1]
    if cmd == "moves":
        fetch_tutte_mosse()
    elif cmd == "items":
        fetch_tutti_oggetti()
    elif cmd == "abilities":
        fetch_tutte_abilita()
    elif cmd == "natures":
        fetch_tutte_nature()
    elif cmd == "movesets":
        fetch_tutti_learnset()
    elif cmd == "all":
        fetch_tutte_nature()
        fetch_tutte_abilita()
        fetch_tutte_mosse()
        fetch_tutti_oggetti()
        fetch_tutti_learnset()
    else:
        print(f"Comando sconosciuto: {cmd}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
