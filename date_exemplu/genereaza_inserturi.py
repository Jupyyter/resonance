"""Bonus (lab 4): writes INSERT statements for random but valid instruments.

    python date_exemplu/genereaza_inserturi.py            50 instruments
    python date_exemplu/genereaza_inserturi.py -n 80      80 instruments
    python date_exemplu/genereaza_inserturi.py --seed 3   a different (but repeatable) random set

It writes date_exemplu/inserturi_instrumente.sql. It doesn't need Django or the database: it only
writes text. Every row respects the rules in models.py, so PostgreSQL accepts all of them:
  price > 0; weight empty or between 0 and 200 kg; condition one of new/used/refurbished;
  used and refurbished instruments: stock 0 or 1; new instruments: a distributor.

The category, brand and distributor are written by name, as subqueries that look up their id:
  (SELECT id FROM instruments_category WHERE name = 'Basses')
so the file works whatever ids those rows got. They must exist first (python manage.py incarca_date).
"Studio and live gear" gets no instruments: the lab wants one category without products, for testing.
"""
import argparse
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

DESTINATIE = Path(__file__).resolve().parent / "inserturi_instrumente.sql"

# For each category: which brands make it, their model lines, price range (lei), weight range (kg),
# materials and tags to pick from.
CATEGORII = {
    "Electric guitars": {
        "modele": {
            "Fender": ["Player II Telecaster", "Player II Jazzmaster", "Vintera II 60s Stratocaster",
                       "American Professional II Stratocaster", "Player Mustang"],
            "Gibson": ["Les Paul Studio", "SG Special", "ES-335", "Les Paul Junior", "Flying V"],
            "Yamaha": ["Pacifica 112V", "Pacifica Standard Plus", "Revstar RSE20", "Revstar RSP20"],
        },
        "pret": (1400, 16000), "greutate": (2.6, 4.6),
        "materiale": ["alder", "ash", "mahogany", "maple", "rosewood", "ebony", "basswood", "pau ferro"],
        "taguri": ["single-coil", "humbucker", "tremolo", "vintage", "stage", "lightweight", "beginner", "hollow body"],
    },
    "Acoustic guitars": {
        "modele": {
            "Yamaha": ["FG830", "FS800", "LL16", "CG192S", "APX600", "JR2"],
            "Gibson": ["J-45 Standard", "Hummingbird Studio", "L-00 Standard"],
            "Fender": ["CD-60S", "Newporter Player", "Paramount PD-220E"],
        },
        "pret": (450, 14000), "greutate": (1.6, 2.6),
        "materiale": ["spruce", "cedar", "mahogany", "rosewood", "nato", "walnut", "ovangkol", "maple"],
        "taguri": ["solid top", "dreadnought", "classical", "electro-acoustic", "travel", "beginner", "nylon strings"],
    },
    "Basses": {
        "modele": {
            "Fender": ["Player II Jazz Bass", "Player Mustang Bass", "Vintera II 60s Precision Bass",
                       "American Professional II Jazz Bass V"],
            "Yamaha": ["TRBX174", "TRBX505", "BB234", "BB434"],
            "Gibson": ["SG Standard Bass", "Thunderbird IV", "EB Bass"],
        },
        "pret": (1200, 11000), "greutate": (3.4, 5.2),
        "materiale": ["alder", "ash", "mahogany", "maple", "rosewood", "pau ferro"],
        "taguri": ["active", "passive", "fretless", "5-string", "short scale", "stage", "beginner"],
    },
    "Keyboards and synthesizers": {
        "modele": {
            "Yamaha": ["P-225", "CK61", "PSR-E383", "Reface CP", "MODX6+", "CP73"],
            "Roland": ["FP-30X", "JUNO-D6", "GO:KEYS 3", "RD-88", "FANTOM-06", "JD-Xi"],
        },
        "pret": (900, 16000), "greutate": (2.0, 20.0),
        "materiale": [],
        "taguri": ["88 keys", "61 keys", "weighted keys", "synth", "workstation", "portable", "compact", "beginner"],
    },
    "Drums and percussion": {
        "modele": {
            "Roland": ["TD-02KV", "TD-17KVX2", "TD-27KV2", "SPD-SX PRO", "Octapad SPD-30"],
            "Pearl": ["Roadshow five-piece kit", "Decade Maple kit", "Masters Maple kit", "Sensitone snare",
                      "Export snare"],
            "Yamaha": ["Stage Custom Birch kit", "Rydeen five-piece kit", "DTX6K2-X"],
            "Zildjian": ["A Custom 18in Crash", "K Sweet 16in Crash", "S Series 20in Ride", "A New Beat 14in Hi-Hats"],
        },
        "pret": (700, 14000), "greutate": (1.0, 40.0),
        "materiale": ["birch", "maple", "poplar", "mahogany", "steel", "bronze"],
        "taguri": ["electronic", "mesh heads", "five-piece", "cymbal", "hardware included", "compact", "beginner"],
    },
}

FINISAJE = ["Black", "Sunburst", "Olympic White", "Natural", "Cherry", "Sea Foam Green", "Candy Apple Red",
            "Vintage White", "Ocean Blue", "Walnut"]

DISTRIBUITORI = {  # who supplies which brands (names from date.json)
    "Fender": ["Carpathia Music Supply", "Danube Audio Distribution"],
    "Gibson": ["Danube Audio Distribution", "Baltic Sound Trading"],
    "Yamaha": ["Danube Audio Distribution", "Adriatic Instruments"],
    "Roland": ["Adriatic Instruments", "Euro Percussion Partners"],
    "Pearl": ["Euro Percussion Partners"],
    "Zildjian": ["Euro Percussion Partners"],
}


def text_sql(valoare):
    """A Python string as an SQL string: in quotes, with any ' written twice."""
    return "'" + valoare.replace("'", "''") + "'"


def lista_sql(valori):
    """A Python list as a PostgreSQL array: ARRAY['a','b'], or '{}' when empty."""
    if not valori:
        return "'{}'"
    return "ARRAY[" + ", ".join(text_sql(v) for v in valori) + "]"


def id_dupa_nume(tabel, nume):
    return f"(SELECT id FROM instruments_{tabel} WHERE name = {text_sql(nume)})"


def instrument(rnd, folosite):
    categorie = rnd.choice(list(CATEGORII))
    date = CATEGORII[categorie]
    brand = rnd.choice(list(date["modele"]))
    model = rnd.choice(date["modele"][brand])
    # a finish makes the name unique; drums and cymbals get none
    finisaj = rnd.choice(FINISAJE) if categorie != "Drums and percussion" else None
    nume = f"{brand} {model}" + (f", {finisaj}" if finisaj else "")
    if nume in folosite:
        return None
    folosite.add(nume)

    # condition: mostly new; used and refurbished ones are one of a kind
    stare = rnd.choices(["new", "used", "refurbished"], weights=[75, 15, 10])[0]
    if stare == "new":
        stoc = rnd.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15])
        distribuitor = id_dupa_nume("distributor", rnd.choice(DISTRIBUITORI[brand]))
    else:
        stoc = rnd.choice([0, 1, 1])
        distribuitor = "NULL"  # bought from a player, not from a distributor

    pret = round(rnd.uniform(*date["pret"]) / 10) * 10 - 1  # prices like 4,599
    if stare != "new":
        pret = round(pret * rnd.uniform(0.55, 0.8)) // 10 * 10
    greutate = "NULL" if rnd.random() < 0.2 else f"{rnd.uniform(*date['greutate']):.1f}"
    materiale = rnd.sample(date["materiale"], k=min(len(date["materiale"]), rnd.randint(1, 3)))
    taguri = rnd.sample(date["taguri"], k=rnd.randint(1, 3))
    stangaci = categorie in ("Electric guitars", "Acoustic guitars", "Basses") and rnd.random() < 0.1
    adaugat = datetime.now(timezone.utc) - timedelta(days=rnd.randint(0, 720), minutes=rnd.randint(0, 1440))

    descriere = {
        "new": f"New {model}" + (f" in {finisaj.lower()}" if finisaj else "") + ", set up in our workshop before it ships.",
        "used": f"Second-hand {model} in good playing condition, checked and set up in our workshop.",
        "refurbished": f"Refurbished {model}: repaired and fully checked, with new strings and a fresh setup.",
    }[stare]

    coloane = {
        "name": text_sql(nume),
        "description": text_sql(descriere),
        "price": f"{pret:.2f}",
        "stock": str(stoc),
        "condition": text_sql(stare),
        "left_handed": "TRUE" if stangaci else "FALSE",
        "weight_kg": greutate,
        "date_added": text_sql(adaugat.strftime("%Y-%m-%d %H:%M:%S+00")),
        "materials": lista_sql(materiale),
        "image": "NULL",
        "tags": lista_sql(taguri),
        "category_id": id_dupa_nume("category", categorie),
        "brand_id": id_dupa_nume("brand", brand),
        "distributor_id": distribuitor,
    }
    return (
        f"INSERT INTO instruments_instrument ({', '.join(coloane)})\n"
        f"VALUES ({', '.join(coloane.values())});"
    )


def main():
    parser = argparse.ArgumentParser(description="Writes INSERT statements for random valid instruments.")
    parser.add_argument("-n", type=int, default=50, help="how many instruments (default 50)")
    parser.add_argument("--seed", type=int, default=2026, help="the same seed always gives the same file")
    args = parser.parse_args()

    rnd = random.Random(args.seed)
    folosite, comenzi = set(), []
    while len(comenzi) < args.n:
        comanda = instrument(rnd, folosite)
        if comanda:
            comenzi.append(comanda)

    DESTINATIE.write_text(
        f"-- {args.n} random instruments, made by genereaza_inserturi.py (seed {args.seed}).\n"
        "-- One transaction: if any row breaks a rule, none of them is saved.\n\n"
        "BEGIN;\n\n" + "\n\n".join(comenzi) + "\n\nCOMMIT;\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.n} INSERT statements to {DESTINATIE.name}")


if __name__ == "__main__":
    main()
