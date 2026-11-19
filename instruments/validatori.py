"""Validation functions shared by the forms in forms.py.

A validator is a function that receives a value and raises ValidationError if it doesn't like it.
A form field runs the ones in its validators=[...] list, in that order, after its own checks,
and only when the value isn't empty. Written once here, each is used on several fields.
"""
import re
import unicodedata
from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

# A "word": letters and digits only. [^\W_] is "a word character, but not _", so any Unicode letter
# (ă, ș, é...) counts, and everything else (spaces, punctuation, _) separates words.
CUVANT = re.compile(r"[^\W_]+")
# Three or more words joined by dots without spaces, like site.example.com.
CUVINTE_CU_PUNCTE = re.compile(r"[^\W_]+(?:\.[^\W_]+){2,}")
EMAIL_TEMPORAR = ("guerillamail.com", "yopmail.com")


def cuvinte(text):
    """The words in a text, as defined above: "Hi, it's me!" → ["Hi", "it", "s", "me"]."""
    return CUVANT.findall(text)


# ---------- names and subjects ----------


def majuscula_si_litere(text):
    """Starts with a capital letter and has only letters, spaces and hyphens."""
    if not text[0].isupper():
        raise ValidationError("Start with a capital letter.", code="fara_majuscula")
    if not all(c.isalpha() or c in " -" for c in text):
        raise ValidationError("Use only letters, spaces and hyphens.", code="caractere_nepermise")


def majuscula_dupa_separator(text):
    """Every part after a space or a hyphen starts with a capital letter: Ana-Maria, not Ana-maria.
    The first part is majuscula_si_litere's job, so a name gets one error for it, not two."""
    for parte in re.split(r"[ -]+", text.strip(" -"))[1:]:
        if parte and not parte[0].isupper():
            raise ValidationError(
                f"Each part of the name starts with a capital letter, “{parte}” too.",
                code="parte_fara_majuscula",
            )


# ---------- texts that mustn't carry links ----------


def fara_linkuri(text):
    """No word starting with http:// or https://, and no three words joined by dots (a.b.c)."""
    for bucata in text.split():
        if bucata.lower().startswith(("http://", "https://")):
            raise ValidationError("Links aren't allowed here.", code="link")
    if CUVINTE_CU_PUNCTE.search(text):
        raise ValidationError(
            "Words joined by dots, like an address (shop.example.com), aren't allowed here.", code="adresa"
        )


def fara_strigat(text):
    """Not written all in capitals (more than 3 letters and none of them lowercase)."""
    litere = [c for c in text if c.isalpha()]
    if len(litere) > 3 and all(c.isupper() for c in litere):
        raise ValidationError("Please don't write it all in capitals.", code="majuscule")


# ---------- email, birth date, CNP ----------


def fara_email_temporar(email):
    domeniu = email.rsplit("@", 1)[-1].lower()
    if any(domeniu == d or domeniu.endswith("." + d) for d in EMAIL_TEMPORAR):
        raise ValidationError("Temporary email addresses can't receive our answer. Use your usual one.", code="temporar")


def varsta(nascut, azi=None):
    """(years, months) between a birth date and today, counting only months that have fully passed:
    someone 34 years, 8 months and 25 days old gets (34, 8)."""
    azi = azi or date.today()
    luni = (azi.year - nascut.year) * 12 + (azi.month - nascut.month)
    if azi.day < nascut.day:
        luni -= 1  # this month's birthday-day hasn't come yet
    return luni // 12, luni % 12


def major(nascut):
    """At least 18 years old. Uses varsta(), the same function that saves the sender's age."""
    if nascut > date.today():
        raise ValidationError("The birth date can't be in the future.", code="viitor")
    if varsta(nascut)[0] < 18:
        raise ValidationError("You need to be at least 18 to send us a message.", code="minor")


def data_din_cnp(cnp):
    """The birth date written in a CNP, or None if those digits aren't a real date.
    The first digit gives the century: 1 and 2 for 1900–1999, 5 and 6 for 2000–2099."""
    secol = 1900 if cnp[0] in "12" else 2000
    try:
        return date(secol + int(cnp[1:3]), int(cnp[3:5]), int(cnp[5:7]))
    except ValueError:
        return None


def cnp_valid(cnp):
    """13 digits, starting with 1, 2, 5 or 6, and the next 6 digits are a real date (YYMMDD)."""
    if not cnp.isdigit():
        raise ValidationError("A CNP has only digits.", code="cnp_cifre")
    if len(cnp) != 13:
        raise ValidationError(f"A CNP has exactly 13 digits; this one has {len(cnp)}.", code="cnp_lungime")
    if cnp[0] not in "1256":
        raise ValidationError("A CNP starts with 1, 2, 5 or 6.", code="cnp_inceput")
    if data_din_cnp(cnp) is None:
        raise ValidationError("Digits 2 to 7 of a CNP are a birth date (YYMMDD), and these aren't a real date.", code="cnp_data")


# ---------- accounts and addresses (lab 6) ----------

# A Romanian number (0721 000 000) or one with + and the country code (+44 20 0000 0000).
# Used by the contact form and by the users' phone column.
telefon_valid = RegexValidator(
    r"^(\+[1-9][0-9 ]{7,17}|0[0-9 ]{9,12})$",
    "Write the number as 0721 000 000, or with + and the country code.",
    code="telefon_invalid",
)

# The 41 counties, and Bucharest, which has the same standing
JUDETE = (
    "Alba", "Arad", "Argeș", "Bacău", "Bihor", "Bistrița-Năsăud", "Botoșani", "Brăila", "Brașov",
    "București", "Buzău", "Călărași", "Caraș-Severin", "Cluj", "Constanța", "Covasna", "Dâmbovița",
    "Dolj", "Galați", "Giurgiu", "Gorj", "Harghita", "Hunedoara", "Ialomița", "Iași", "Ilfov",
    "Maramureș", "Mehedinți", "Mureș", "Neamț", "Olt", "Prahova", "Sălaj", "Satu Mare", "Sibiu",
    "Suceava", "Teleorman", "Timiș", "Tulcea", "Vâlcea", "Vaslui", "Vrancea",
)


def fara_diacritice(text):
    """"Iași" → "iasi", and "Iaşi" (ş with a cedilla, from older keyboards) too: NFD splits each
    letter from its accent, and the accents (category Mn) are dropped."""
    descompus = unicodedata.normalize("NFD", text.strip())
    return "".join(c for c in descompus if unicodedata.category(c) != "Mn").casefold()


def e_romania(tara):
    return fara_diacritice(tara) == "romania"


def judet_roman(text):
    """The county named by text, written properly ("iasi" → "Iași"); an error if there's none."""
    cautat = fara_diacritice(text)
    if cautat in ("bucharest", "bucuresti"):
        return "București"
    for judet in JUDETE:
        if fara_diacritice(judet) == cautat:
            return judet
    raise ValidationError(
        "“%(judet)s” isn't a Romanian county. Write it like Cluj, Iași or București.",
        code="judet_necunoscut",
        params={"judet": text},
    )


def strada_cu_numar(text):
    """A street address has the street's name and a number: Strada Rezonanței 7."""
    if not any(c.isalpha() for c in text):
        raise ValidationError("Write the street's name too, like Strada Rezonanței 7.", code="fara_nume_strada")
    if not any(c.isdigit() for c in text):
        raise ValidationError("Add the number too, like Strada Rezonanței 7.", code="fara_numar")


def data_nasterii_plauzibila(nascut):
    """Not in the future, and not before 1900."""
    if nascut > date.today():
        raise ValidationError("That date is in the future.", code="in_viitor")
    if nascut.year < 1900:
        raise ValidationError("Check the year: it's before 1900.", code="prea_vechi")
