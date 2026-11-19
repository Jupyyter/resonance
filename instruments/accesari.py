"""The site's visit log: the Accesare class (lab 1) and what the /log page needs (lab 2).

Visits are kept in the `accesari` list, in memory, so they disappear when the server restarts
(a database comes in lab 3). They're recorded by AccesariMiddleware (middleware.py), once per
request to one of the shop's pages, so the views don't have to remember to do it.
"""
from collections import Counter
from itertools import count
from urllib.parse import urlsplit

from django.urls import URLPattern, reverse
from django.utils import timezone
from django.utils.html import format_html

from .dates import FORMAT_DATA, FORMAT_ORA, formateaza_data


class Accesare:
    """One visit to a page of the site."""

    # A counter shared by the whole class: next() gives 1, 2, 3 ... one number per new visit.
    _urmatorul_id = count(1)

    def __init__(self, ip_client, url, parametri=None):
        self.id = next(Accesare._urmatorul_id)
        self.ip_client = ip_client
        self.url = url  # the full address, query string included
        # Not "parametri={}" in the line above: a {} written there is created ONCE and then shared
        # by every Accesare made without parameters, so changing one would change them all.
        self.parametri = parametri if parametri is not None else {}
        self.data = timezone.localtime()  # a datetime: this moment, in the shop's time zone

    @classmethod
    def din_cerere(cls, request):
        """Records a visit from a Django request: creates it, keeps it and prints it."""
        accesare = cls(
            ip_client=getattr(request, "ip_client", None),  # set by IpMiddleware
            url=request.build_absolute_uri(),
            parametri=dict(request.GET.lists()),  # {"a": ["1", "2"]}: a name can appear several times
        )
        accesari.append(accesare)
        print(accesare, end="\n\n")  # shows in the terminal where "runserver" is running
        return accesare

    def lista_parametri(self):
        """[(name, value), ...]: the value is None if the parameter was given without a value
        (?a or ?a=), a list if it appeared several times, otherwise the single value."""
        lista = []
        for nume, valoare in self.parametri.items():
            valori = [v for v in (valoare if isinstance(valoare, list) else [valoare]) if v not in ("", None)]
            if not valori:
                lista.append((nume, None))
            elif len(valori) == 1:
                lista.append((nume, valori[0]))
            else:
                lista.append((nume, valori))
        return lista

    def parametri_text(self):
        """lista_parametri() as readable text, for the pages: [("data", "zi"), ("a", "1, 2")]."""
        return [
            (nume, "(fără valoare)" if valoare is None else ", ".join(valoare) if isinstance(valoare, list) else valoare)
            for nume, valoare in self.lista_parametri()
        ]

    def string_url(self):
        """The whole address, with the query string: http://127.0.0.1:8000/info?data=zi"""
        return self.url

    def pagina(self):
        """Only the page inside the app, without domain or parameters: "/" or "/info"."""
        return pagina_din_cale(urlsplit(self.url).path)

    def data_text(self):
        """Date and time of the visit, as text: "Joi, 19 Noiembrie 2026, 14:03:51"."""
        return formateaza_data(self.data, f"{FORMAT_DATA}, {FORMAT_ORA}")

    def calculeaza_data(self, ce="", format=FORMAT_DATA):
        """The HTML of the "Data și ora" section, for the moment of this visit.

        ce = "zi"   → only the date (day, month, year), written with `format`
        ce = "timp" → only the time (hours, minutes, seconds)
        anything else, or nothing → both

        format_html escapes the text it inserts and marks the result as safe HTML, so a template
        can show it as it is (a plain string with tags in it would be escaped by the template).
        """
        zi = formateaza_data(self.data, format)
        ora = formateaza_data(self.data, FORMAT_ORA)
        if ce == "zi":
            text = zi
        elif ce == "timp":
            text = ora
        else:
            text = f"{zi}, ora {ora}"
        return format_html("<section><h2>Data și ora</h2><p>{}</p></section>", text)

    def __str__(self):
        campuri = {
            "id": self.id,
            "ip_client": self.ip_client,
            "string_url": self.string_url(),
            "pagina": self.pagina(),
            "data": self.data_text(),
            "lista_parametri": self.lista_parametri(),
        }
        return "\n".join(f"{camp}: {valoare}" for camp, valoare in campuri.items())


# Every visit since the server started, oldest first.
accesari = []


def pagina_din_cale(cale):
    """"/info" from "/info", also when the app is mounted lower, e.g. "/shop/info" → "/info"."""
    radacina = reverse("instruments:index")  # where the app starts: "/" now
    if cale.startswith(radacina):
        cale = "/" + cale[len(radacina):]
    return cale


def gaseste(id_accesare):
    """The visit with this id, or None."""
    return next((a for a in accesari if a.id == id_accesare), None)


def pagini_fara_parametri():
    """Every page of the app that has a fixed address ("/", "/info", ...), visited or not.

    It reads the app's own urlpatterns, so a page added there is counted here too.
    /accesare<id> is left out: it's a family of pages, not one page.
    """
    from . import urls  # imported here: urls.py imports the views, which import this module

    pagini = []
    for model in urls.urlpatterns:
        if isinstance(model, URLPattern) and model.name and model.pattern.regex.groups == 0:
            pagini.append(pagina_din_cale(reverse(f"{urls.app_name}:{model.name}")))
    return pagini


def pagini_extreme():
    """The least and the most visited pages: ((pages, visits), (pages, visits)).

    Pages nobody has visited count with 0 visits. Several pages can share first or last place,
    so each side is a list.
    """
    vizite = Counter({pagina: 0 for pagina in pagini_fara_parametri()})
    vizite.update(a.pagina() for a in accesari)
    if not vizite:
        return ([], 0), ([], 0)
    minim, maxim = min(vizite.values()), max(vizite.values())
    return (
        (sorted(p for p, n in vizite.items() if n == minim), minim),
        (sorted(p for p, n in vizite.items() if n == maxim), maxim),
    )


def cate(numar, singular, plural):
    """A number with its noun, the Romanian way: "1 accesare", "5 accesări", "20 de accesări"."""
    if numar == 1:
        return f"1 {singular}"
    rest = numar % 100
    de = " de" if rest >= 20 or (rest == 0 and numar != 0) else ""
    return f"{numar}{de} {plural}"


# The columns /log?tabel=... can show: name in the address → (column title, how to get the value).
COLOANE = {
    "id": ("Id", lambda a: a.id),
    "ip_client": ("IP client", lambda a: a.ip_client or "necunoscut"),
    "url": ("URL", lambda a: a.string_url()),
    "pagina": ("Pagina", lambda a: a.pagina()),
    "data": ("Data", lambda a: a.data_text()),
    "parametri": ("Parametri", lambda a: "; ".join(f"{n} = {v}" for n, v in a.parametri_text()) or "—"),
}
