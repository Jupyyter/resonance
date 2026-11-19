"""What happens to a contact message after the form accepts it (lab 5, task 3).

Messages aren't stored in the database: each one is a JSON file in
instruments/Mesaje_nerezolvate/<department slug>/mesaj_<timestamp>[_urgent].json,
with its images next to it. git ignores the folder: the messages hold personal data.
"""
import json
import re
from datetime import datetime
from datetime import timezone as utc_zone
from html import escape
from pathlib import Path

from django.utils import timezone

from .models import Department
from .validatori import varsta

DOSAR = Path(__file__).resolve().parent / "Mesaje_nerezolvate"
FISIER = re.compile(r"^mesaj_(\d+)(_urgent)?\.json$")


# ---------- folders ----------


def dosar(slug=None):
    """The messages folder, or one department's folder in it, created if it doesn't exist yet."""
    cale = DOSAR / slug if slug else DOSAR
    try:
        cale.stat()  # raises FileNotFoundError if the folder isn't there
    except FileNotFoundError:
        cale.mkdir(parents=True)
    return cale


def pregateste_dosare():
    """A folder for every department in the database."""
    for slug in Department.objects.values_list("slug", flat=True):
        dosar(slug)


# ---------- preprocessing ----------


def text_varsta(nascut, azi=None):
    """ "34 years and 8 months": the age that's saved instead of the date of birth.
    It reuses varsta(), the function the over-18 check uses."""
    ani, luni = varsta(nascut, azi)
    return f"{ani} year{'s' if ani != 1 else ''} and {luni} month{'s' if luni != 1 else ''}"


def majuscule_dupa_punct(text):
    """A capital letter after the end of a sentence (. ? ! or ...) and the space after it:
    "ok. thanks... see you" → "ok. Thanks... See you"."""
    return re.sub(r"([.?!]\s+)([^\W\d_])", lambda m: m.group(1) + m.group(2).upper(), text)


def mesaj_html(text):
    """The message as HTML: each line a <p> paragraph, runs of spaces as one space.

    Every paragraph is escaped first, so a < typed in the message stays text and can't become
    a tag on the page that shows it."""
    text = majuscule_dupa_punct(text.replace("\r\n", "\n"))
    paragrafe = [re.sub(r"\s+", " ", linie).strip() for linie in text.split("\n")]
    return "".join(f"<p>{escape(p)}</p>" for p in paragrafe if p)


# ---------- saving ----------


def salveaza(date, ip):
    """Writes a valid message to its department's folder and returns the file's path.

    date is the form's cleaned_data. Every field goes in the file except the email confirmation,
    with the date of birth replaced by the age, and the IP and arrival time added."""
    tip, departament = date["tip_mesaj"], date["departament"]
    urgent = date["minim_zile_asteptare"] == tip.min_days  # they'll wait only as long as they must
    destinatie = dosar(departament.slug)

    sosit = timezone.localtime()
    secunde = int(sosit.timestamp())
    sufix = "_urgent" if urgent else ""
    # two messages in the same second: the second one takes the next second (urgent or not,
    # so that their images, named after the second, can't overwrite each other either)
    while any((destinatie / f"mesaj_{secunde}{s}.json").exists() for s in ("", "_urgent")):
        secunde += 1
    nume_fisier = f"mesaj_{secunde}{sufix}.json"

    imagini = []
    for i in (1, 2, 3):
        imagine = date.get(f"imagine{i}")
        if imagine:
            nume = f"mesaj_{secunde}_imagine{i}{Path(imagine.name).suffix.lower()}"
            with open(destinatie / nume, "wb") as f:
                for bucata in imagine.chunks():  # an upload can be large: copy it in pieces
                    f.write(bucata)
            imagini.append(nume)

    continut = {
        "nume": date["nume"],
        "prenume": date["prenume"],
        "cnp": date["cnp"],
        "varsta": text_varsta(date["data_nasterii"]),
        "email": date["email"],
        "telefon": date["telefon"],
        "tip_mesaj": tip.code,
        "departament": departament.slug,
        "subiect": date["subiect"],
        "minim_zile_asteptare": date["minim_zile_asteptare"],
        "mesaj": mesaj_html(date["mesaj"]),
        "imagini": imagini,
        "gdpr": date["gdpr"],
        "cod_cerere": date["cod_cerere"],
        "urgent": urgent,
        "ip": ip,
        "primit_la": sosit.isoformat(timespec="seconds"),
    }
    cale = destinatie / nume_fisier
    cale.write_text(json.dumps(continut, ensure_ascii=False, indent=2), encoding="utf-8")
    return cale


# ---------- reading, for /mesaje ----------


def citeste(slug, an, luna=None, zi=None):
    """One department's messages from a year, a month or a day, newest first.
    The date comes from the timestamp in each file's name."""
    rezultat = []
    for cale in dosar(slug).iterdir():
        potrivire = FISIER.match(cale.name)
        if not potrivire:
            continue  # images, and anything else that isn't a message
        cand = timezone.localtime(datetime.fromtimestamp(int(potrivire.group(1)), tz=utc_zone.utc))
        if cand.year != an or (luna and cand.month != luna) or (zi and cand.day != zi):
            continue
        try:
            continut = json.loads(cale.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue  # a damaged file shouldn't take the whole page down
        rezultat.append({"fisier": cale.name, "sosit": cand, "urgent": bool(potrivire.group(2)), "date": continut})
    return sorted(rezultat, key=lambda m: m["sosit"], reverse=True)


def numara(slug):
    """How many messages a department has, all dates together."""
    return sum(1 for cale in dosar(slug).iterdir() if FISIER.match(cale.name))
