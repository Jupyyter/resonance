from collections import Counter

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import urlencode

from . import accesari as jurnal
from .accesari import COLOANE, cate
from .models import Category, Instrument

DESCRIERE = (
    "Resonance is an online shop for musical instruments: electric and acoustic guitars, basses, "
    "keyboards and synthesizers, drums and studio gear. Every product has its own page with full "
    "specifications and an interactive 3D model you can rotate and zoom, and you can hear how the "
    "instrument sounds right in the browser. Visitors can browse by category, filter and sort by "
    "brand, price and specifications, save favourites and order online, while the shop's staff "
    "manage products, stock and orders from an administration panel."
)

# Every view below gets its visit already recorded, as request.accesare (AccesariMiddleware).
# render() fills a template with a context dict and returns the HttpResponse. The context
# processors in settings add more to every template: companie, sectiune_activa, request ...


def index(request):
    return render(request, "instruments/index.html", {"descriere": DESCRIERE})


def info(request):
    ce = request.GET.get("data", "")  # /info?data=zi or /info?data=timp
    return render(request, "instruments/info.html", {"sectiune_data": request.accesare.calculeaza_data(ce)})


def despre(request):
    return render(request, "instruments/despre.html")


def istoric(request):
    return render(request, "instruments/istoric.html")


def services(request):
    return render(request, "instruments/services.html")


def faq(request):
    return render(request, "instruments/faq.html")


# Not built yet: each has its own view, which for now shows in_lucru.html.
# In later labs these views get their real content (products from the database, the contact form).


# ---------- The shop's listings (lab 4) ----------

# ?by=... in the address → the field it sorts by. Only these, so nobody can sort by any column.
SORTARI = {"name": "name", "price": "price", "date": "date_added", "stock": "stock"}
ETICHETE_SORTARI = {"name": "Name", "price": "Price", "date": "Date added", "stock": "Stock"}


def _adresa(request, **schimbari):
    """The current address's query string with some parameters changed: a value of None removes
    the parameter, a list sets it several times (?tag=a&tag=b). Every other parameter stays."""
    parametri = request.GET.copy()
    for nume, valoare in schimbari.items():
        if valoare is None:
            parametri.pop(nume, None)
        elif isinstance(valoare, list):
            parametri.setlist(nume, valoare)
        else:
            parametri[nume] = valoare
    text = parametri.urlencode()
    return "?" + text if text else request.path


def _listare(request, instrumente, categorie=None):
    """Sorting, tag filtering and pagination, shared by /produse and /categorii/<name>.

    Both pages call it with their own starting QuerySet (all instruments, or one category's)
    and render the same template, so the rules live in one place.
    """
    mesaje = []

    # Tags: ?tag=vintage&tag=stage keeps only instruments that have ALL of them.
    # __contains on an ArrayField is PostgreSQL's @> operator: "the array contains these values".
    active = list(dict.fromkeys(t.strip().lower() for t in request.GET.getlist("tag") if t.strip()))
    toate = instrumente  # this page's instruments before the tags: all of them, or one category's
    if active:
        instrumente = instrumente.filter(tags__contains=active)

    # The filter panel's tags. Always the same list: every tag of this page's instruments, most
    # common first, so ticking one never makes others disappear or move. The number next to each:
    # how many of the instruments shown now have it, which is also how many would stay if you
    # ticked it too (0: none would). values_list("tags", flat=True) reads only that column.
    def numara(qs):
        return Counter(tag for taguri in qs.values_list("tags", flat=True) for tag in taguri)

    in_pagina = numara(toate)
    acum = numara(instrumente) if active else in_pagina
    ordine = [tag for tag, _ in sorted(in_pagina.items(), key=lambda p: (-p[1], p[0]))]
    ordine += [tag for tag in active if tag not in in_pagina]  # a tag from the address that this page doesn't have
    taguri_filtru = [(tag, acum.get(tag, 0), tag in active) for tag in ordine]
    restul = taguri_filtru[12:]

    # Sorting: ?by=price&sort=d. Either one alone uses a default for the other.
    # An empty by= is the panel's "Newest first", which ignores sort=.
    dupa, sens = request.GET.get("by") or None, request.GET.get("sort") or None
    if request.GET.get("by") == "":
        sens = None
    if dupa is not None and dupa not in SORTARI:
        mesaje.append(f"Instruments can be sorted by {', '.join(SORTARI)}, not by \u201c{dupa}\u201d.")
        dupa = None
    if sens is not None and sens not in ("a", "d"):
        mesaje.append(f"The order is a (ascending) or d (descending), not \u201c{sens}\u201d.")
        sens = None
    if dupa or sens:
        dupa, sens = dupa or "name", sens or "a"
        camp = SORTARI[dupa]
        # "id" as a tie-break: instruments with the same price keep a fixed order between pages
        instrumente = instrumente.order_by(camp if sens == "a" else "-" + camp, "id")
    else:
        instrumente = instrumente.order_by("-date_added", "id")  # newest first

    # Pagination, on the sorted and filtered QuerySet. get_page() turns a missing, wrong or
    # too large ?page= into the first or last page instead of an error.
    paginator = Paginator(instrumente, settings.PROD_PER_PAG)
    pagina = paginator.get_page(request.GET.get("page"))

    # The links for tags. Clicking a tag adds it to the active ones and goes back to page 1.
    for instrument in pagina:
        instrument.linkuri_taguri = [
            (tag, _adresa(request, tag=active if tag in active else active + [tag], page=None), tag in active)
            for tag in instrument.tags
        ]
    taguri_active = [(tag, _adresa(request, tag=[t for t in active if t != tag], page=None)) for tag in active]

    return render(request, "instruments/produse.html", {
        "categorie": categorie,
        "pagina": pagina,
        "taguri_active": taguri_active,
        "fara_taguri": _adresa(request, tag=None, page=None),
        "taguri_principale": taguri_filtru[:12],
        "taguri_restul": restul,
        # the "more tags" part starts open if one of its tags is ticked
        "restul_deschis": any(bifat for _, _, bifat in restul),
        "numar_filtre": len(active),
        "dupa": dupa or "",
        "sens": sens or "",
        "sortari": ETICHETE_SORTARI,
        "mesaje": mesaje,
        "stoc_min": settings.STOC_MIN,
    })


def _instrumente():
    # select_related: the category and brand come in the same query (a JOIN), not one query per card
    return Instrument.objects.select_related("category", "brand")


def _fara_sortare_goala(request):
    """The panel's "Newest first" sends an empty by= (and a sort= that means nothing then).
    Returns a redirect to the same page without them, so addresses stay short, or None."""
    if request.GET.get("by") != "":
        return None
    parametri = request.GET.copy()
    for nume in ("by", "sort", "page"):
        parametri.pop(nume, None)
    return redirect(request.path + ("?" + parametri.urlencode() if parametri else ""))


def produse(request):
    """/produse: every instrument, whatever its category."""
    return _fara_sortare_goala(request) or _listare(request, _instrumente())


def categorie(request, nume):
    """/categorii/<name>: one category's instruments, with the same sorting, filters and pages."""
    try:
        gasita = Category.objects.get(name=nume)
    except Category.DoesNotExist:
        return _negasit(request, "No such category", f"The shop has no category called \u201c{nume}\u201d.")
    return _fara_sortare_goala(request) or _listare(request, _instrumente().filter(category=gasita), categorie=gasita)


def produs(request, id):
    """/produse/<id>: one instrument, with all its details (the address get_absolute_url() gives)."""
    try:
        instrument = (
            Instrument.objects.select_related("category", "brand", "distributor")
            .prefetch_related("services", "recordings")  # two more queries for these, instead of one per item
            .get(pk=id)
        )
    except Instrument.DoesNotExist:
        return _negasit(
            request,
            "Instrument not found",
            f"There's no instrument number {id} in the shop. It may have been sold and taken off the site.",
        )
    # order_by("?") lets the database pick them at random
    asemanatoare = (
        Instrument.objects.filter(category=instrument.category)
        .exclude(pk=instrument.pk)
        .order_by("?")[: settings.PRODUSE_ASEMANATOARE]
    )
    return render(request, "instruments/produs.html", {
        "instrument": instrument,
        "asemanatoare": asemanatoare,
        # from the product page, a tag opens the full listing filtered by it ("solid top" → ?tag=solid+top)
        "taguri": [(tag, reverse("instruments:produse") + "?" + urlencode({"tag": tag})) for tag in instrument.tags],
    })


def _negasit(request, titlu, text):
    """The error page for an instrument or category that doesn't exist, with the 404 status."""
    return render(request, "instruments/eroare.html", {"titlu": titlu, "text": text}, status=404)


def contact(request):
    return render(request, "instruments/in_lucru.html", {"pagina": "Contact"})


def cos_virtual(request):
    return render(request, "instruments/in_lucru.html", {"pagina": "Cart"})


def accesare(request, id):
    """/accesare<id>: one visit in detail. `id` arrives as text, because it comes from the URL."""
    id_cerut = int(id)
    gasita = jurnal.gaseste(id_cerut)
    return render(
        request,
        "instruments/accesare.html",
        {"a": gasita, "id_cerut": id_cerut},
        status=200 if gasita else 404,  # "not found" for an id that doesn't exist
    )


def _valori(request, nume):
    """Every value of a parameter, whether repeated or comma separated:
    ?iduri=1,3&iduri=5 → ["1", "3", "5"]."""
    return [bucata.strip() for valoare in request.GET.getlist(nume) for bucata in valoare.split(",") if bucata.strip()]


def log(request):
    """/log: the visits since the server started. The parameters choose what's shown:

    iduri=1,3 (or iduri=1&iduri=3)  only these visits, in this order
    dubluri=true                    with iduri: a repeated id is shown every time (default false: once)
    ultimele=n                      only the last n visits (of those chosen by iduri, if given)
    tabel=tot or tabel=id,pagina    a table with all columns, or with these columns
    accesari=nr                     how many visits there have been
    accesari=detalii                the date and time of every visit
    """
    mesaje = []  # (kind, text) shown at the top: kind "eroare" (bad parameter) or "atentie"
    selectie = list(jurnal.accesari)

    # --- iduri and dubluri
    if "iduri" in request.GET:
        dubluri_text = request.GET.get("dubluri", "false").lower()
        if dubluri_text not in ("true", "false"):
            mesaje.append(("eroare", f"dubluri poate fi true sau false, nu „{dubluri_text}”; am folosit false."))
        dubluri = dubluri_text == "true"

        valori = _valori(request, "iduri")
        gresite = [v for v in valori if not v.isdecimal()]
        if gresite:
            mesaje.append(("eroare", f"Id-urile sunt numere naturale; am ignorat: {', '.join(gresite)}."))
        iduri = [int(v) for v in valori if v.isdecimal()]
        if not dubluri:
            iduri = list(dict.fromkeys(iduri))  # keeps the first of each id, in order

        dupa_id = {a.id: a for a in jurnal.accesari}
        lipsa = [i for i in dict.fromkeys(iduri) if i not in dupa_id]
        if lipsa:
            mesaje.append(("atentie", f"Nu există accesări cu id-ul: {', '.join(map(str, lipsa))}."))
        selectie = [dupa_id[i] for i in iduri if i in dupa_id]

    # --- ultimele
    mesaj_final = None  # shown at the end of the list, as the lab asks
    if "ultimele" in request.GET:
        text = request.GET.get("ultimele", "")
        if text.isdecimal():
            n = int(text)
            if n > len(selectie):
                # The lab's exact wording, with k and n filled in.
                mesaj_final = f"Există doar {len(selectie)} accesări față de {n} accesări cerute"
            selectie = selectie[-n:] if n else []  # careful: selectie[-0:] would be the whole list
        else:
            mesaje.append(("eroare", f"ultimele trebuie să fie un număr natural, nu „{text}”."))

    # --- accesari=nr / accesari=detalii (about all the visits, not only the ones shown)
    total = date = None
    ce = request.GET.get("accesari")
    if ce == "nr":
        total = cate(len(jurnal.accesari), "accesare", "accesări")
    elif ce == "detalii":
        date = [(a.id, a.data_text()) for a in jurnal.accesari]
    elif ce is not None:
        mesaje.append(("eroare", f"accesari poate fi nr sau detalii, nu „{ce}”."))

    # --- tabel
    tabel = None
    if "tabel" in request.GET:
        coloane = _valori(request, "tabel")
        if "tot" in coloane:
            coloane = list(COLOANE)
        necunoscute = [c for c in coloane if c not in COLOANE]
        if necunoscute or not coloane:
            mesaje.append((
                "eroare",
                (f"Coloane necunoscute: {', '.join(necunoscute)}. " if necunoscute else "")
                + f"Coloanele posibile sunt: tot, {', '.join(COLOANE)}.",
            ))
        coloane = [c for c in dict.fromkeys(coloane) if c in COLOANE]
        if coloane:
            tabel = {
                "antet": [COLOANE[c][0] for c in coloane],
                "randuri": [[COLOANE[c][1](a) for c in coloane] for a in selectie],
            }

    (pagini_min, vizite_min), (pagini_max, vizite_max) = jurnal.pagini_extreme()
    return render(request, "instruments/log.html", {
        "parametri": request.accesare.parametri_text(),
        # repeated names (?iduri=1&iduri=2) count once: it's one parameter with several values
        "numar_parametri": cate(len(request.GET), "parametru", "parametri"),
        "mesaje": mesaje,
        "mesaj_final": mesaj_final,
        "selectie": selectie,
        "tabel": tabel,
        "total": total,
        "date": date,
        "pagini_min": pagini_min,
        "vizite_min": cate(vizite_min, "accesare", "accesări"),
        "pagini_max": pagini_max,
        "vizite_max": cate(vizite_max, "accesare", "accesări"),
    })
