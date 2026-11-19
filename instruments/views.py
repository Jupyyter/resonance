from django.shortcuts import render

from . import accesari as jurnal
from .accesari import COLOANE, cate

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


def produse(request):
    return render(request, "instruments/in_lucru.html", {"pagina": "Products"})


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
