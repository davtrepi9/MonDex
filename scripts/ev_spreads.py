"""
EV spreads consigliate per Pokemon CHAMPIONS.

Sistema EV Champions REALE:
- Totale max 66 EV (somma di TUTTE le stat)
- Ogni stat può ricevere fino al budget rimanente

Conversione lineare: champions_ev = round(vgc_ev * 66 / 508)
- Es. 252 HP = ~33 in Champions
- Es. 4 Spe = ~1 in Champions

Output: ev_spreads.json
"""
import json
import sys


def cv(vgc_ev: int) -> int:
    """Converti EV da scala VGC (max 252, totale 508) a Champions (totale 66)."""
    if vgc_ev == 0:
        return 0
    if vgc_ev <= 4:
        return 1
    return round(vgc_ev * 66 / 508)


def make_ev(hp=0, atk=0, df=0, spa=0, spd=0, spe=0):
    return {
        "hp": cv(hp), "attack": cv(atk), "defense": cv(df),
        "specialAttack": cv(spa), "specialDefense": cv(spd), "speed": cv(spe),
    }


SPREADS = {
    "azumarill": [
        {"nome": "Belly Drum Sweep", "item": "Sitrus Berry", "ability": "Huge Power",
         "natura": "Adamant", "ev": make_ev(hp=252, atk=252, spe=4),
         "nota": "Belly Drum + Sitrus per recovery e sweep con Aqua Jet/Play Rough"},
        {"nome": "Bulky Trick Room", "item": "Assault Vest", "ability": "Huge Power",
         "natura": "Brave", "ev": make_ev(hp=244, atk=252, df=12),
         "nota": "Slow attacker per TR, Aqua Jet utile anche fuori TR"},
    ],
    "incineroar": [
        {"nome": "Bulky Pivot", "item": "Sitrus Berry", "ability": "Intimidate",
         "natura": "Careful", "ev": make_ev(hp=252, df=4, spd=252),
         "nota": "Intimidate + Fake Out + Parting Shot, supporto pivot"},
        {"nome": "Tank Offensivo", "item": "Safety Goggles", "ability": "Intimidate",
         "natura": "Careful", "ev": make_ev(hp=244, atk=76, df=4, spd=180, spe=4),
         "nota": "Bilanciato attacco/difesa, immune a spore"},
    ],
    "garchomp": [
        {"nome": "Scarf Sweeper", "item": "Choice Scarf", "ability": "Rough Skin",
         "natura": "Jolly", "ev": make_ev(hp=4, atk=252, spe=252),
         "nota": "Outspeed con Scarf, Earthquake/Dragon Claw spam"},
        {"nome": "Mixed Tank", "item": "Life Orb", "ability": "Rough Skin",
         "natura": "Adamant", "ev": make_ev(hp=252, atk=100, df=4, spd=100, spe=52),
         "nota": "Bulky Earthquake support, sopravvive a hit comuni"},
    ],
    "dragapult": [
        {"nome": "Choice Specs", "item": "Choice Specs", "ability": "Cursed Body",
         "natura": "Timid", "ev": make_ev(hp=4, spa=252, spe=252),
         "nota": "Specs Shadow Ball/Draco Meteor, max speed"},
        {"nome": "Mixed Sweeper", "item": "Life Orb", "ability": "Clear Body",
         "natura": "Jolly", "ev": make_ev(hp=4, atk=252, spe=252),
         "nota": "Dragon Darts + U-turn, pivot offensivo"},
    ],
    "tyranitar": [
        {"nome": "Trick Room AD", "item": "Life Orb", "ability": "Sand Stream",
         "natura": "Brave", "ev": make_ev(hp=252, atk=252, spd=4),
         "nota": "Slow physical attacker sotto TR + sand support"},
        {"nome": "Sand Bulky", "item": "Assault Vest", "ability": "Sand Stream",
         "natura": "Sassy", "ev": make_ev(hp=252, atk=4, spd=252),
         "nota": "Special wall in sandstorm"},
    ],
    "sneasler": [
        {"nome": "Unburden Sweeper", "item": "White Herb", "ability": "Unburden",
         "natura": "Jolly", "ev": make_ev(hp=4, atk=252, spe=252),
         "nota": "Close Combat consuma White Herb -> Unburden raddoppia Speed"},
    ],
    "kingambit": [
        {"nome": "Bulky Defiant", "item": "Black Glasses", "ability": "Defiant",
         "natura": "Adamant", "ev": make_ev(hp=252, atk=252, spd=4),
         "nota": "Sucker Punch + Kowtow Cleave, baits Intimidate per +2 Atk"},
    ],
    "sinistcha": [
        {"nome": "Trick Room Tank", "item": "Sitrus Berry", "ability": "Hospitality",
         "natura": "Quiet", "ev": make_ev(hp=252, df=4, spa=252),
         "nota": "Matcha Gotcha sotto TR, Hospitality cura partner"},
    ],
    "farigiraf": [
        {"nome": "TR Setter", "item": "Mental Herb", "ability": "Armor Tail",
         "natura": "Quiet", "ev": make_ev(hp=252, df=4, spa=252),
         "nota": "Armor Tail blocca priority, Mental Herb anti-Taunt"},
    ],
    "delphox": [
        {"nome": "Special Sweeper", "item": "Life Orb", "ability": "Magician",
         "natura": "Timid", "ev": make_ev(hp=4, spa=252, spe=252),
         "nota": "Heat Wave + Psyshock spam con max speed"},
    ],
    "whimsicott": [
        {"nome": "Prankster Support", "item": "Mental Herb", "ability": "Prankster",
         "natura": "Calm", "ev": make_ev(hp=252, df=4, spd=252),
         "nota": "Tailwind + Encore + Helping Hand con priority"},
    ],
    "basculegion": [
        {"nome": "Adaptability Wave Crash", "item": "Mystic Water", "ability": "Adaptability",
         "natura": "Adamant", "ev": make_ev(hp=4, atk=252, spe=252),
         "nota": "Last Respects/Wave Crash con STAB raddoppiato"},
    ],
    "corviknight": [
        {"nome": "Defensive Pivot", "item": "Leftovers", "ability": "Mirror Armor",
         "natura": "Impish", "ev": make_ev(hp=252, df=252, spd=4),
         "nota": "Bulky physical wall, Roost + U-turn"},
    ],
    "dragonite": [
        {"nome": "Multiscale Setup", "item": "Heavy-Duty Boots", "ability": "Multiscale",
         "natura": "Adamant", "ev": make_ev(hp=252, atk=252, spd=4),
         "nota": "Dragon Dance + Extreme Speed, Multiscale dimezza primo hit"},
    ],
    "excadrill": [
        {"nome": "Sand Rush Sweeper", "item": "Focus Sash", "ability": "Sand Rush",
         "natura": "Jolly", "ev": make_ev(hp=4, atk=252, spe=252),
         "nota": "Sand Rush raddoppia Speed in sandstorm"},
    ],
    "hatterene": [
        {"nome": "Magic Bounce TR", "item": "Sitrus Berry", "ability": "Magic Bounce",
         "natura": "Quiet", "ev": make_ev(hp=252, df=4, spa=252),
         "nota": "TR + Dazzling Gleam, Magic Bounce blocca status"},
    ],
    "gengar": [
        {"nome": "Special Sweeper", "item": "Choice Specs", "ability": "Cursed Body",
         "natura": "Timid", "ev": make_ev(hp=4, spa=252, spe=252),
         "nota": "Sludge Bomb + Shadow Ball spam, max speed"},
    ],
    "gardevoir": [
        {"nome": "Mega Glass Cannon", "item": "Gardevoirite", "ability": "Pixilate",
         "natura": "Timid", "ev": make_ev(hp=4, spa=252, spe=252),
         "nota": "Pixilate Hyper Voice spread, Mega per Pixilate"},
    ],
    "alakazam": [
        {"nome": "Magic Guard Sweeper", "item": "Life Orb", "ability": "Magic Guard",
         "natura": "Timid", "ev": make_ev(hp=4, spa=252, spe=252),
         "nota": "Magic Guard ignora recoil di Life Orb"},
    ],
    "aerodactyl": [
        {"nome": "Tailwind Setter", "item": "Focus Sash", "ability": "Pressure",
         "natura": "Jolly", "ev": make_ev(hp=4, atk=252, spe=252),
         "nota": "Tailwind + Stone Edge + Wide Guard, Sash sopravvive a 1 hit"},
    ],
    "aegislash": [
        {"nome": "Stance Change", "item": "Spooky Plate", "ability": "Stance Change",
         "natura": "Brave", "ev": make_ev(hp=252, atk=252, spd=4),
         "nota": "King's Shield + Iron Head, switch automatico Blade/Shield"},
    ],
    "chesnaught": [
        {"nome": "Bulletproof Tank", "item": "Rocky Helmet", "ability": "Bulletproof",
         "natura": "Adamant", "ev": make_ev(hp=252, atk=252, spd=4),
         "nota": "Spiky Shield + Body Press, immune a Shadow Ball/Sludge Bomb"},
    ],
    "clefable": [
        {"nome": "Magic Guard Wall", "item": "Leftovers", "ability": "Magic Guard",
         "natura": "Modest", "ev": make_ev(hp=252, df=4, spa=252),
         "nota": "Moonblast spam, Magic Guard immune a status damage"},
    ],
    "conkeldurr": [
        {"nome": "Drain Punch Tank", "item": "Flame Orb", "ability": "Guts",
         "natura": "Brave", "ev": make_ev(hp=252, atk=252, spd=4),
         "nota": "Flame Orb + Guts boosta Atk, Drain Punch recupera HP"},
    ],
}


def main():
    with open("ev_spreads.json", "w", encoding="utf-8") as f:
        json.dump(SPREADS, f, ensure_ascii=False, indent=2)
    tot_spreads = sum(len(v) for v in SPREADS.values())
    azu = SPREADS["azumarill"][0]
    print(f"Spread Champions (max 66 TOTALI): {tot_spreads} per {len(SPREADS)} Pokemon")
    print(f"Azumarill {azu['nome']}: {azu['ev']} -> totale {sum(azu['ev'].values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
