"""The site's forms (lab 5): the instrument filters, the contact form, and adding an instrument.

A form class lists its fields; each field turns what the browser sent (always text) into a Python
value and checks it. form.is_valid() runs, in order: each field's own checks and validators=[...],
then the form's clean_<field>() methods, then clean() for checks that need several fields.
Every error lands in form.errors, which the templates show next to the field.
"""
import re
import secrets
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django import forms
from django.conf import settings
from django.core import signing
from django.core.validators import RegexValidator

from .models import Brand, Category, Department, Distributor, Instrument, MessageType, Service
from .validatori import (
    cnp_valid,
    cuvinte,
    data_din_cnp,
    fara_email_temporar,
    fara_linkuri,
    fara_strigat,
    major,
    majuscula_dupa_separator,
    majuscula_si_litere,
)

# =====================================================================================
# Task 2: the filters on /produse and the category pages
# =====================================================================================

SORTARI = [("name", "Name"), ("price", "Price"), ("date", "Date added"), ("stock", "Stock")]
PER_PAGINA = [6, 12, 18, 24]  # each divides by 1, 2 and 3, so every row of the grid is full
COLOANE = [1, 2, 3]


class FiltruInstrumenteForm(forms.Form):
    """A filter for every column of the instruments table. Every field is optional: left empty,
    it doesn't filter, so the empty form shows every instrument.

    The field names are the names in the address (?nume=strat&pret_max=5000), so a filtered list
    can be bookmarked or shared, and the older parameters (tag, by, sort, page) keep working.
    """

    nume = forms.CharField(
        label="Name",
        required=False,
        max_length=60,
        widget=forms.TextInput(attrs={"type": "search", "placeholder": "Stratocaster"}),
        error_messages={"max_length": "Keep the name under 60 characters."},
    )
    descriere = forms.CharField(
        label="Description mentions",
        required=False,
        max_length=60,
        widget=forms.TextInput(attrs={"type": "search", "placeholder": "maple"}),
        error_messages={"max_length": "Keep it under 60 characters."},
    )
    pret_min = forms.DecimalField(
        label="Price from",
        required=False,
        min_value=0,
        max_digits=9,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "1", "placeholder": "0"}),
        error_messages={
            "min_value": "Prices start at 0.",
            "invalid": "Write the price as a number, like 1500.",
            "max_digits": "That's more than any instrument costs.",
            "max_whole_digits": "That's more than any instrument costs.",
            "max_decimal_places": "Bani go to 2 decimals at most.",
        },
    )
    pret_max = forms.DecimalField(
        label="to",
        required=False,
        min_value=0,
        max_digits=9,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "1", "placeholder": "any"}),
        error_messages={
            "min_value": "Prices start at 0.",
            "invalid": "Write the price as a number, like 5000.",
            "max_digits": "That's more than any instrument costs.",
            "max_whole_digits": "That's more than any instrument costs.",
            "max_decimal_places": "Bani go to 2 decimals at most.",
        },
    )
    # to_field_name="name": the address says ?categorie=Basses, not ?categorie=3
    categorie = forms.ModelChoiceField(
        label="Category",
        queryset=Category.objects.order_by("display_order", "name"),
        to_field_name="name",
        required=False,
        empty_label="All categories",
        error_messages={"invalid_choice": "There's no such category."},
    )
    brand = forms.ModelChoiceField(
        label="Brand",
        queryset=Brand.objects.all(),
        to_field_name="name",
        required=False,
        empty_label="Any brand",
        error_messages={"invalid_choice": "There's no such brand in the shop."},
    )
    distribuitor = forms.ModelChoiceField(
        label="Supplied by",
        queryset=Distributor.objects.all(),
        to_field_name="name",
        required=False,
        empty_label="Any supplier",
        error_messages={"invalid_choice": "There's no such supplier."},
    )
    serviciu = forms.ModelChoiceField(
        label="Offers the service",
        queryset=Service.objects.all(),
        to_field_name="name",
        required=False,
        empty_label="Any service",
        error_messages={"invalid_choice": "There's no such service."},
    )
    stare = forms.ChoiceField(
        label="Condition",
        required=False,
        choices=[("", "Any condition"), *Instrument.Condition.choices],
        error_messages={"invalid_choice": "Condition is new, used or refurbished."},
    )
    stoc = forms.ChoiceField(
        label="Stock",
        required=False,
        choices=[("", "Any"), ("disponibil", "In stock"), ("limitat", "Only a few left"), ("epuizat", "Sold out")],
        error_messages={"invalid_choice": "Pick one of the stock options."},
    )
    stangaci = forms.ChoiceField(
        label="Left-handed",
        required=False,
        choices=[("", "Either"), ("da", "Left-handed only"), ("nu", "Right-handed only")],
        error_messages={"invalid_choice": "Pick left-handed, right-handed or either."},
    )
    greutate_max = forms.FloatField(
        label="Weighs at most (kg)",
        required=False,
        min_value=0.5,
        max_value=200,
        widget=forms.NumberInput(attrs={"step": "0.5", "placeholder": "any"}),
        error_messages={
            "min_value": "No instrument weighs under half a kilogram.",
            "max_value": "Our heaviest instruments weigh well under 200 kg.",
            "invalid": "Write the weight as a number, like 4.5.",
        },
    )
    material = forms.ChoiceField(
        label="Made of",
        required=False,
        error_messages={"invalid_choice": "None of these instruments is made of %(value)s."},
    )
    adaugat_de_la = forms.DateField(
        label="Added from",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        error_messages={"invalid": "Pick a date from the calendar."},
    )
    adaugat_pana_la = forms.DateField(
        label="to",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        error_messages={"invalid": "Pick a date from the calendar."},
    )
    cu_imagine = forms.BooleanField(label="Only with a photo", required=False)
    tag = forms.MultipleChoiceField(
        label="Tags",
        required=False,
        widget=forms.CheckboxSelectMultiple,
        error_messages={"invalid_choice": "No instrument on this page is tagged %(value)s."},
    )
    by = forms.ChoiceField(
        label="Sort by",
        required=False,
        choices=[("", "Newest first"), *SORTARI],
        error_messages={"invalid_choice": "Instruments sort by name, price, date added or stock, not by %(value)s."},
    )
    sort = forms.ChoiceField(
        label="Order",
        required=False,
        choices=[("a", "Ascending"), ("d", "Descending")],
        error_messages={"invalid_choice": "The order is a (ascending) or d (descending), not %(value)s."},
    )
    per_pagina = forms.TypedChoiceField(
        label="Per page",
        required=False,
        coerce=int,
        empty_value=None,
        choices=[(n, str(n)) for n in PER_PAGINA],
        error_messages={"invalid_choice": "A page shows 6, 12, 18 or 24 instruments."},
    )
    coloane = forms.TypedChoiceField(
        label="Columns",
        required=False,
        coerce=int,
        empty_value=None,
        choices=[(n, str(n)) for n in COLOANE],
        error_messages={"invalid_choice": "The grid has 1, 2 or 3 columns."},
    )

    def __init__(self, *args, categorie=None, taguri=(), materiale=(), **kwargs):
        kwargs.setdefault("label_suffix", "")  # labels without a ":" at the end
        super().__init__(*args, **kwargs)
        self.categorie = categorie
        # choices that depend on the page: its own tags and materials
        self.fields["tag"].choices = [(t, t) for t in taguri]
        self.fields["material"].choices = [("", "Any material"), *((m, m) for m in materiale)]
        self.fields["per_pagina"].initial = settings.PROD_PER_PAG
        self.fields["coloane"].initial = 3
        if categorie:
            # On a category page the category is fixed: a hidden, read-only field set to it.
            # The view still checks what comes back, in case someone edits it in the browser.
            camp = self.fields["categorie"]
            camp.widget = forms.HiddenInput(attrs={"readonly": True})
            camp.initial = categorie.name

    def clean_nume(self):
        nume = self.cleaned_data["nume"].strip()
        if nume and len(nume) < 2:
            raise forms.ValidationError("Type at least 2 letters of the name.", code="prea_scurt")
        return nume

    def clean_descriere(self):
        text = self.cleaned_data["descriere"].strip()
        if text and not cuvinte(text):
            raise forms.ValidationError("Type a word to look for, not only punctuation.", code="fara_cuvinte")
        return text

    def clean_adaugat_de_la(self):
        zi = self.cleaned_data["adaugat_de_la"]
        if zi and zi > date.today():
            raise forms.ValidationError("No instrument was added in the future: pick today or earlier.", code="viitor")
        return zi

    def clean(self):
        date_ = super().clean()
        pret_min, pret_max = date_.get("pret_min"), date_.get("pret_max")
        if pret_min is not None and pret_max is not None and pret_min > pret_max:
            self.add_error("pret_max", "The highest price can't be lower than the lowest one.")
        de_la, pana_la = date_.get("adaugat_de_la"), date_.get("adaugat_pana_la")
        if de_la and pana_la and de_la > pana_la:
            self.add_error("adaugat_pana_la", "This date comes before the first one: swap them.")
        return date_


# =====================================================================================
# Task 3: the contact form
# =====================================================================================

NESELECTAT = "neselectat"
COD_SARE = "resonance.contact.cod"  # "salt": codes signed for this form are useless anywhere else
COD_VALABIL = timedelta(hours=3)


def genereaza_cod():
    """The request code: 8 random hex characters, signed together with the current time.

    django.core.signing adds the time and an HMAC-SHA256 signature made with SECRET_KEY:
    "3fa9c2e1:1vZ1aB:Wq...". Nobody without the key can make a code that passes verifica_cod(),
    and a code expires after COD_VALABIL, so old or invented requests are rejected.
    """
    return signing.TimestampSigner(salt=COD_SARE).sign(secrets.token_hex(4))


def verifica_cod(cod):
    """The random part of a valid code; raises ValidationError for an invented or expired one."""
    try:
        aleator = signing.TimestampSigner(salt=COD_SARE).unsign(cod, max_age=COD_VALABIL)
    except signing.SignatureExpired:
        raise forms.ValidationError("This form was opened too long ago. Reload the page and send it again.", code="expirat")
    except signing.BadSignature:
        raise forms.ValidationError("This request code wasn't made by our site.", code="cod_invalid")
    if not re.fullmatch(r"[0-9a-f]{8}", aleator):
        raise forms.ValidationError("This request code wasn't made by our site.", code="cod_invalid")
    return aleator


def eticheta_zile():
    """The label of the days field, from the message types table: what it says is what's checked."""
    pe_minim = {}
    for tip in MessageType.objects.order_by("-min_days", "name"):
        pe_minim.setdefault(tip.min_days, []).append(tip.name.lower() + "s")
    parti = [f"at least {zile} for {' and '.join(nume)}" for zile, nume in pe_minim.items()]
    return "Days you can wait for an answer: " + "; ".join(parti) + ". At most 30."


class ContactForm(forms.Form):
    """The contact form. Nothing is saved to the database: a valid message becomes a JSON file
    in Mesaje_nerezolvate/<department>/ (see contact.py)."""

    required_css_class = "camp-obligatoriu"

    nume = forms.CharField(
        label="Family name",
        max_length=10,
        validators=[majuscula_si_litere, majuscula_dupa_separator],
        error_messages={"required": "Tell us your family name.", "max_length": "The family name fits in 10 characters here."},
    )
    prenume = forms.CharField(
        label="Given names",
        required=False,
        max_length=30,
        validators=[majuscula_si_litere, majuscula_dupa_separator],  # validators don't run on an empty field
        help_text="Separate several given names with a space or a hyphen: Ana Maria or Ana-Maria.",
        error_messages={"max_length": "Given names fit in 30 characters here."},
    )
    cnp = forms.CharField(
        label="CNP",
        required=False,
        max_length=13,
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off"}),
        help_text="Optional. Your personal numeric code, 13 digits.",
        error_messages={"max_length": "A CNP has exactly 13 digits."},
    )
    data_nasterii = forms.DateField(
        label="Date of birth",
        widget=forms.DateInput(attrs={"type": "date"}),  # the browser's calendar
        validators=[major],
        error_messages={"required": "Tell us your date of birth.", "invalid": "Pick the date from the calendar."},
    )
    email = forms.EmailField(
        label="Email",
        validators=[fara_email_temporar],
        error_messages={"required": "We need an email address to answer you.", "invalid": "This isn't a valid email address."},
    )
    confirmare_email = forms.EmailField(
        label="Email again",
        error_messages={"required": "Type your email address a second time.", "invalid": "This isn't a valid email address."},
    )
    telefon = forms.CharField(
        label="Phone",
        required=False,
        max_length=20,
        help_text="Optional. Romanian numbers as 0721 000 000; others with the country code: +44 20 0000 0000.",
        validators=[
            RegexValidator(r"^(\+[1-9][0-9 ]{7,17}|0[0-9 ]{9,12})$", "Write the number as 0721 000 000, or with + and the country code."),
        ],
        error_messages={"max_length": "A phone number fits in 20 characters."},
    )
    tip_mesaj = forms.ChoiceField(
        label="Kind of message",
        initial=NESELECTAT,
        error_messages={"invalid_choice": "Pick a kind of message from the list."},
    )
    departament = forms.ChoiceField(
        label="Send it to",
        initial=NESELECTAT,
        error_messages={"invalid_choice": "Pick a department from the list."},
    )
    subiect = forms.CharField(
        label="Subject",
        max_length=100,
        validators=[majuscula_si_litere, fara_linkuri],
        error_messages={"required": "Give your message a subject.", "max_length": "Keep the subject under 100 characters."},
    )
    minim_zile_asteptare = forms.IntegerField(
        min_value=1,
        max_value=30,
        error_messages={
            "required": "Tell us how many days you can wait for an answer.",
            "invalid": "Write a whole number of days.",
            "min_value": "Wait at least 1 day.",
            "max_value": "We answer within 30 days, so choose 30 at most.",
        },
    )
    mesaj = forms.CharField(
        label="Your message. Sign it: end it with your family name.",
        widget=forms.Textarea(attrs={"rows": 7}),
        validators=[fara_linkuri],
        error_messages={"required": "Write your message."},
    )
    imagine1 = forms.ImageField(label="Image", required=False, error_messages={"invalid_image": "This file isn't an image we can open."})
    imagine2 = forms.ImageField(label="Second image", required=False, error_messages={"invalid_image": "This file isn't an image we can open."})
    imagine3 = forms.ImageField(label="Third image", required=False, error_messages={"invalid_image": "This file isn't an image we can open."})
    gdpr = forms.BooleanField(
        label="I agree that Resonance stores these details to answer my message.",
        error_messages={"required": "We can only answer if you agree that we store your details."},
    )
    cod_cerere = forms.CharField(widget=forms.HiddenInput, error_messages={"required": "This form is missing its request code. Reload the page."})

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        # The choices come from the database, so a new message type or department appears by itself.
        self.tipuri = {t.code: t for t in MessageType.objects.prefetch_related("departments")}
        self.fields["tip_mesaj"].choices = [(NESELECTAT, "Not selected"), *((c, t.name) for c, t in self.tipuri.items())]
        self.fields["departament"].choices = [(NESELECTAT, "Not selected"), *Department.objects.values_list("slug", "name")]
        self.fields["minim_zile_asteptare"].label = eticheta_zile()

    def departamente_pe_tip(self):
        """{type code: [[slug, name], ...]}: the page sends it to the JavaScript that filters the
        departments list as the kind of message changes."""
        return {c: [[d.slug, d.name] for d in t.departments.all()] for c, t in self.tipuri.items()}

    # ---- one field at a time ----

    def clean_cnp(self):
        cnp = self.cleaned_data["cnp"].strip()
        if cnp:
            cnp_valid(cnp)
        return cnp

    def clean_email(self):
        return self.cleaned_data["email"].lower()

    def clean_confirmare_email(self):
        return self.cleaned_data["confirmare_email"].lower()

    def clean_tip_mesaj(self):
        cod = self.cleaned_data["tip_mesaj"]
        if cod == NESELECTAT:
            raise forms.ValidationError("Choose what kind of message this is.", code="neselectat")
        if cod not in self.tipuri:  # checked against the table, not only against the list sent to the browser
            raise forms.ValidationError("Pick a kind of message from the list.", code="tip_necunoscut")
        return self.tipuri[cod]

    def clean_departament(self):
        slug = self.cleaned_data["departament"]
        if slug == NESELECTAT:
            raise forms.ValidationError("Choose the department your message is for.", code="neselectat")
        try:
            return Department.objects.get(slug=slug)
        except Department.DoesNotExist:
            raise forms.ValidationError("Pick a department from the list.", code="departament_necunoscut")

    def clean_mesaj(self):
        text = self.cleaned_data["mesaj"]
        lista = cuvinte(text)
        if not 5 <= len(lista) <= 100:
            raise forms.ValidationError(
                f"Write between 5 and 100 words; this message has {len(lista)}.", code="numar_cuvinte"
            )
        lungi = [c for c in lista if len(c) > 15]
        if lungi:
            raise forms.ValidationError(
                f"Words are 15 characters at most here; “{lungi[0][:20]}” is longer.", code="cuvant_lung"
            )
        return text

    def clean_gdpr(self):
        # The page keeps the send button disabled until this is ticked, but a request can be
        # sent without the page, so the server checks again.
        if self.cleaned_data.get("gdpr") is not True:
            raise forms.ValidationError("We can only answer if you agree that we store your details.", code="fara_acord")
        return True

    def clean_cod_cerere(self):
        cod = self.cleaned_data["cod_cerere"]
        verifica_cod(cod)
        return cod

    # ---- several fields together ----

    def clean(self):
        date_ = super().clean()
        email, confirmare = date_.get("email"), date_.get("confirmare_email")
        if email and confirmare and email != confirmare:
            self.add_error("confirmare_email", "The two email addresses are different.")

        nume, mesaj = date_.get("nume"), date_.get("mesaj")
        if nume and mesaj:
            semnatura = cuvinte(nume)
            if [c.casefold() for c in cuvinte(mesaj)[-len(semnatura):]] != [c.casefold() for c in semnatura]:
                self.add_error("mesaj", f"Sign your message: end it with your family name, {nume}.")

        tip, zile = date_.get("tip_mesaj"), date_.get("minim_zile_asteptare")
        if tip and zile is not None and zile < tip.min_days:
            self.add_error(
                "minim_zile_asteptare",
                f"For a {tip.name.lower()}, choose at least {tip.min_days} day{'s' if tip.min_days > 1 else ''}.",
            )

        cnp, nascut = date_.get("cnp"), date_.get("data_nasterii")
        if cnp and nascut and data_din_cnp(cnp) != nascut:
            self.add_error("cnp", "This CNP doesn't match your date of birth.")

        # The page only offers the departments of the chosen kind, but the browser could be made to
        # send any pair, so the link table decides.
        departament = date_.get("departament")
        if tip and departament and not tip.departments.filter(pk=departament.pk).exists():
            self.add_error("departament", f"{departament.name} doesn't handle {tip.name.lower()}s. Pick one from the list.")
        return date_


# =====================================================================================
# Task 4: adding an instrument
# =====================================================================================


def la_9(pret):
    """A price rounded to whole lei ending in 9, the way shops write them: 4,583.20 → 4,589."""
    intreg = int(pret.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return Decimal(intreg // 10 * 10 + 9)


class InstrumentForm(forms.ModelForm):
    """A new instrument for the shop. The price isn't typed: it's worked out from two inputs that
    aren't columns, the purchase price and the markup, in the view (see adauga_instrument)."""

    pret_achizitie = forms.DecimalField(
        label="Purchase price (lei)",
        max_digits=9,
        decimal_places=2,
        help_text="What the distributor charges us for one, VAT included.",
        error_messages={
            "required": "Type what we pay for it.",
            "invalid": "Write the price as a number, like 3200.",
            "max_digits": "That's more than we'd ever pay for one instrument.",
            "max_whole_digits": "That's more than we'd ever pay for one instrument.",
            "max_decimal_places": "Bani go to 2 decimals at most.",
        },
    )
    adaos = forms.IntegerField(
        label="Markup (%)",
        help_text="The selling price is the purchase price plus this percentage, rounded to end in 9.",
        error_messages={"required": "Type the markup, like 30.", "invalid": "Write the markup as a whole number."},
    )

    class Meta:
        model = Instrument
        # the columns the form shows; price, date_added, weight, materials, image and services aren't here
        fields = ["name", "description", "category", "brand", "condition", "distributor", "stock", "tags"]
        labels = {
            "name": "Instrument name",
            "description": "Description for the product page",
            "stock": "Units in the shop",
        }
        help_texts = {"tags": "Keywords for the filters, separated by commas: vintage, beginner."}
        error_messages = {
            "name": {"required": "Every instrument needs a name.", "max_length": "Keep the name under 100 characters."},
            "description": {"required": "Write a description for the product page."},
            "category": {"required": "Choose its category.", "invalid_choice": "Choose a category from the list."},
            "brand": {"required": "Choose its brand.", "invalid_choice": "Choose a brand from the list."},
            "distributor": {"invalid_choice": "Choose a distributor from the list."},
            "condition": {"invalid_choice": "Condition is new, used or refurbished."},
            "stock": {"required": "Type how many are in the shop, even if 0.", "invalid": "Write a whole number."},
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        # Two functions defined outside the form, applied in this order: first the links check
        # (also used on the description), then the capitals check.
        self.fields["name"].validators = [fara_linkuri, fara_strigat]
        self.fields["description"].validators = [fara_linkuri]
        # tags: a list typed as text; each tag is checked on its own, and its error starts with its number
        self.fields["tags"].error_messages["item_invalid"] = "Tag %(nth)s:"
        self.fields["tags"].base_field.error_messages["max_length"] = "a tag fits in 30 characters."

    def clean_pret_achizitie(self):
        pret = self.cleaned_data["pret_achizitie"]
        if not Decimal("10") <= pret <= Decimal("100000"):
            raise forms.ValidationError("A purchase price is between 10 and 100,000 lei.", code="pret_achizitie")
        return pret

    def clean_adaos(self):
        adaos = self.cleaned_data["adaos"]
        if not 5 <= adaos <= 150:
            raise forms.ValidationError("The markup is between 5% and 150%.", code="adaos")
        return adaos

    def clean_stock(self):
        stoc = self.cleaned_data["stock"]
        if stoc > 200:
            raise forms.ValidationError("We don't keep more than 200 of one instrument.", code="stoc_mare")
        return stoc

    def clean(self):
        date_ = super().clean()
        # Two fields together: a second-hand instrument is sold with a smaller markup.
        stare, adaos = date_.get("condition"), date_.get("adaos")
        if stare and stare != Instrument.Condition.NEW and adaos is not None and adaos > 60:
            self.add_error("adaos", "Used and refurbished instruments get a markup of 60% at most.")
        return date_

    def pret_vanzare(self):
        """The selling price, from the two extra inputs."""
        date_ = self.cleaned_data
        return la_9(date_["pret_achizitie"] * (1 + Decimal(date_["adaos"]) / 100))
