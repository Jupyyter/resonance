from collections import Counter
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from . import accesari as jurnal
from .accesari import COLOANE, cate
from . import contact as mesaje_contact
from .forms import ContactForm, FiltruInstrumenteForm, InstrumentForm, genereaza_cod
from .models import Category, Department, Instrument, MessageType

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




# ---------- The shop's listings (labs 4 and 5) ----------

# ?by=... in the address → the field it sorts by. Only these, so nobody can sort by any column.
SORTARI = {"name": "name", "price": "price", "date": "date_added", "stock": "stock"}
COLOANE_IMPLICITE = 3


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


def _curata_adresa(request, categorie):
    """Tidies the address a submitted filter form produced, and redirects to the tidy one.

    A form sends every field, also the empty ones (?nume=&pret_min=&...), plus two hidden helpers.
    This drops what means nothing, and acts on the rest:
    - resetat: the Reset button. Every filter goes, with an info message.
    - categorie on a category page: it must be that category. Anything else means it was edited
      in the browser: an error message, and the page's own category stays.
    - per_pagina_anterior and pagina_curenta: if the number per page changed while on page 2 or
      later, the same page number now holds other instruments, so a warning says so.
    Returns the redirect, or None when the address is already tidy. Messages survive the redirect:
    the messages framework keeps them until a page shows them.
    """
    parametri = request.GET.copy()
    if "resetat" in parametri:
        messages.info(request, "Filters cleared: showing every instrument" + (f" in {categorie.name}." if categorie else "."))
        return redirect(request.path)

    schimbat = False
    if categorie and "categorie" in parametri:
        trimisa = parametri.pop("categorie")[-1]
        schimbat = True
        if trimisa != categorie.name:
            messages.error(
                request,
                f"The category can't be changed on this page. Still showing {categorie.name}; "
                "for other categories, use Instrument categories in the menu.",
            )

    anterior, curenta = parametri.pop("per_pagina_anterior", [""])[-1], parametri.pop("pagina_curenta", [""])[-1]
    if anterior or curenta:
        schimbat = True
        acum = parametri.get("per_pagina") or str(settings.PROD_PER_PAG)
        if anterior and acum != anterior and curenta.isdigit() and int(curenta) > 1:
            parametri["page"] = curenta  # stay on the same page number, as the warning says
            messages.warning(
                request,
                f"Now showing {acum} instruments per page instead of {anterior}. On page {curenta}, you may have "
                "skipped some instruments, or see again some you've already seen.",
            )

    if parametri.get("by") == "":  # "Newest first": the order (sort) means nothing then
        parametri.pop("sort", None)
    for nume in list(parametri):
        valori = [v for v in parametri.getlist(nume) if v != ""]
        implicita = {"per_pagina": str(settings.PROD_PER_PAG), "coloane": str(COLOANE_IMPLICITE)}.get(nume)
        if implicita and valori == [implicita]:
            valori = []
        if valori != parametri.getlist(nume):
            schimbat = True
            if valori:
                parametri.setlist(nume, valori)
            else:
                del parametri[nume]
    if not schimbat:
        return None
    return redirect(request.path + ("?" + parametri.urlencode() if parametri else ""))


def _numara_taguri(qs):
    """How many instruments have each tag. values_list("tags", flat=True) reads only that column."""
    return Counter(tag for taguri in qs.values_list("tags", flat=True) for tag in taguri)


def _filtreaza(instrumente, date, categorie):
    """The QuerySet with the form's valid filters applied, and the names of those filters."""
    stoc_min = settings.STOC_MIN
    reguli = {
        "nume": lambda v: Q(name__icontains=v),
        "descriere": lambda v: Q(description__icontains=v),
        "pret_min": lambda v: Q(price__gte=v),
        "pret_max": lambda v: Q(price__lte=v),
        "brand": lambda v: Q(brand=v),
        "distribuitor": lambda v: Q(distributor=v),
        "serviciu": lambda v: Q(services=v),
        "stare": lambda v: Q(condition=v),
        "stoc": lambda v: {
            "disponibil": Q(stock__gte=stoc_min),
            "limitat": Q(stock__gt=0, stock__lt=stoc_min),
            "epuizat": Q(stock=0),
        }[v],
        "stangaci": lambda v: Q(left_handed=(v == "da")),
        "greutate_max": lambda v: Q(weight_kg__lte=v),
        "material": lambda v: Q(materials__contains=[v]),  # PostgreSQL: the array contains this value
        "adaugat_de_la": lambda v: Q(date_added__date__gte=v),
        "adaugat_pana_la": lambda v: Q(date_added__date__lte=v),
        "cu_imagine": lambda v: ~Q(image="") & Q(image__isnull=False),
        "tag": lambda v: Q(tags__contains=v),  # all the ticked tags
    }
    if not categorie:
        reguli["categorie"] = lambda v: Q(category=v)
    aplicate = []
    for camp, regula in reguli.items():
        valoare = date.get(camp)
        if valoare not in (None, "", [], False):
            instrumente = instrumente.filter(regula(valoare))
            aplicate.append(camp)
    if "serviciu" in aplicate:
        instrumente = instrumente.distinct()  # the join on services could repeat an instrument
    return instrumente, aplicate


def _listare(request, instrumente, categorie=None):
    """The listing behind /produse and /categorii/<name>: filters, tags, sorting, pages.

    Both pages call it with their own starting QuerySet (all instruments, or one category's)
    and render the same template, so the rules live in one place.
    """
    raspuns = _curata_adresa(request, categorie)
    if raspuns:
        return raspuns

    toate = instrumente
    taguri_pagina = _numara_taguri(toate)
    materiale = sorted({m for lista in toate.values_list("materials", flat=True) for m in lista})
    date_form = request.GET.copy()
    # A form filled in from the address shows what the address says, not the fields' initial values,
    # so the defaults the tidy address leaves out are put back; otherwise a <select> with nothing
    # chosen would show its first option (1 column) while the page shows 3.
    date_form.setdefault("per_pagina", str(settings.PROD_PER_PAG))
    date_form.setdefault("coloane", str(COLOANE_IMPLICITE))
    if categorie:
        # the address doesn't carry the category (the page's own address says it), but the
        # hidden field must, so the form is filled in with it
        date_form["categorie"] = categorie.name
    form = FiltruInstrumenteForm(
        date_form,
        categorie=categorie,
        taguri=sorted(taguri_pagina, key=lambda t: (-taguri_pagina[t], t)),
        materiale=materiale,
    )
    form.is_valid()  # fills form.cleaned_data with the fields that passed, form.errors with the rest
    date = form.cleaned_data
    if form.errors:
        messages.error(request, "Some filters couldn't be used. The filter panel says why, next to each one.")

    instrumente, aplicate = _filtreaza(toate, date, categorie)
    active = date.get("tag", [])

    # Sorting: ?by=price&sort=d. sort alone sorts by name; by alone sorts ascending.
    dupa, sens = date.get("by") or None, date.get("sort") or None
    if dupa or sens:
        dupa, sens = dupa or "name", sens or "a"
        camp = SORTARI[dupa]
        # "id" as a tie-break: instruments with the same price keep a fixed order between pages
        instrumente = instrumente.order_by(camp if sens == "a" else "-" + camp, "id")
    else:
        instrumente = instrumente.order_by("-date_added", "id")  # newest first

    # The panel's tags: always the same list (this page's tags, most common first), each with how
    # many of the instruments shown now have it, which is also how many would stay if you ticked it.
    acum = _numara_taguri(instrumente) if aplicate else taguri_pagina
    taguri_filtru = [(tag, acum.get(tag, 0), tag in active) for tag, _ in form.fields["tag"].choices]
    restul = taguri_filtru[12:]

    # Pagination, on the sorted and filtered QuerySet. get_page() turns a missing, wrong or
    # too large ?page= into the first or last page instead of an error.
    per_pagina = date.get("per_pagina") or settings.PROD_PER_PAG
    paginator = Paginator(instrumente, per_pagina)
    pagina = paginator.get_page(request.GET.get("page"))

    if aplicate:
        etichete = ", ".join(str(form.fields[c].label).lower() for c in aplicate)
        # only shown while developing (settings: MESSAGE_LEVEL is DEBUG when DEBUG is on)
        messages.debug(request, f"Filters applied: {etichete}. {paginator.count} of {toate.count()} instruments match.")
        if not paginator.count:
            messages.warning(request, "No instruments match all these filters. Try a wider price range, or untick a tag.")

    # The links for tags on the cards. Clicking one adds it to the ticked ones and goes back to page 1.
    for instrument in pagina:
        instrument.linkuri_taguri = [
            (tag, _adresa(request, tag=active if tag in active else active + [tag], page=None), tag in active)
            for tag in instrument.tags
        ]
    taguri_active = [(tag, _adresa(request, tag=[t for t in active if t != tag], page=None)) for tag in active]

    context = {
        "categorie": categorie,
        "form": form,
        "pagina": pagina,
        "taguri_active": taguri_active,
        "fara_taguri": _adresa(request, tag=None, page=None),
        "taguri_principale": taguri_filtru[:12],
        "taguri_restul": restul,
        "restul_deschis": any(bifat for _, _, bifat in restul),
        # "More filters" starts open when one of its fields is in use or has an error
        "detalii_deschise": any(c in aplicate or c in form.errors for c in CAMPURI_DETALII),
        "numar_filtre": len(aplicate),
        "per_pagina": per_pagina,
        "coloane": date.get("coloane") or COLOANE_IMPLICITE,
        "stoc_min": settings.STOC_MIN,
    }
    # The filters' JavaScript asks for only the part of the page that changes (header X-Partial).
    # "produse.html#vitrina" renders only the {% partialdef vitrina %} block of the template.
    if request.headers.get("X-Partial") == "vitrina":
        return render(request, "instruments/produse.html#vitrina", context)
    return render(request, "instruments/produse.html", context)


# The less used filters, grouped in the panel under "More filters"
CAMPURI_DETALII = ["descriere", "distribuitor", "serviciu", "stoc", "stangaci", "greutate_max", "material",
                   "adaugat_de_la", "adaugat_pana_la", "cu_imagine"]


def _instrumente():
    # select_related: the category and brand come in the same query (a JOIN), not one query per card
    return Instrument.objects.select_related("category", "brand")


def produse(request):
    """/produse: every instrument, whatever its category."""
    return _listare(request, _instrumente())


def categorie(request, nume):
    """/categorii/<name>: one category's instruments, with the same filters, sorting and pages."""
    try:
        gasita = Category.objects.get(name=nume)
    except Category.DoesNotExist:
        return _negasit(request, "No such category", f"The shop has no category called \u201c{nume}\u201d.")
    return _listare(request, _instrumente().filter(category=gasita), categorie=gasita)


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
    """/contact: the contact form. A valid message is saved as a JSON file (contact.py), not in the database."""
    if request.method == "POST":
        # request.FILES: the uploaded images arrive apart from the text fields
        form = ContactForm(request.POST, request.FILES)
        if form.is_valid():
            cale = mesaje_contact.salveaza(form.cleaned_data, request.ip_client)
            tip, departament = form.cleaned_data["tip_mesaj"], form.cleaned_data["departament"]
            messages.success(
                request,
                f"Thank you, {form.cleaned_data['nume']}. Your {tip.name.lower()} went to {departament.name}; "
                f"expect an answer within {form.cleaned_data['minim_zile_asteptare']} days.",
            )
            messages.debug(request, f"Saved as {cale.relative_to(mesaje_contact.DOSAR.parent)}.")
            # Post/Redirect/Get: after a POST, redirect, so reloading the page doesn't send it twice
            return redirect("instruments:contact")
        messages.error(request, "The message wasn't sent. The notes next to the fields say what to change.")
    else:
        form = ContactForm(initial={"cod_cerere": genereaza_cod()})
    return render(request, "instruments/contact.html", {"form": form, "departamente_pe_tip": form.departamente_pe_tip()})


# Not built yet: shows in_lucru.html for now.
def cos_virtual(request):
    return render(request, "instruments/in_lucru.html", {"pagina": "Cart"})


# ---------- The saved contact messages (lab 5) ----------
# Only for staff: the messages hold personal details. staff_member_required sends anyone else
# to the admin's login page, and back here after logging in.


@staff_member_required
def mesaje_index(request):
    """/mesaje: every department, with its number of messages and links to this year and month."""
    mesaje_contact.pregateste_dosare()
    azi = timezone.localdate()
    departamente = [(d, mesaje_contact.numara(d.slug)) for d in Department.objects.all()]
    return render(request, "instruments/mesaje_index.html", {"departamente": departamente, "azi": azi})


def _text_camp(valoare):
    """A value from a message file as text: a list joined with commas, true/false as yes/no."""
    if isinstance(valoare, bool):
        return "yes" if valoare else "no"
    if isinstance(valoare, list):
        return ", ".join(map(str, valoare))
    return "" if valoare is None else str(valoare)


@staff_member_required
def mesaje(request, departament, an, luna=None, zi=None):
    """/mesaje/<department>/<year>[/<month>[/<day>]]: one department's messages from that date."""
    try:
        dep = Department.objects.get(slug=departament)
    except Department.DoesNotExist:
        raise Http404("No such department")
    try:
        date(an, luna or 1, zi or 1)  # a month 13 or a 31 February stops here
    except ValueError:
        return _negasit(request, "No such date", "Check the year, month and day in the address.")

    gasite = mesaje_contact.citeste(dep.slug, an, luna, zi)
    inceput = date(an, luna or 1, zi or 1)
    # not strftime("%-d"): that format works on Linux but not on Windows
    perioada = f"{inceput.day} {inceput:%B %Y}" if zi else f"{inceput:%B %Y}" if luna else str(an)
    if gasite:
        messages.info(request, f"{len(gasite)} message{'s' if len(gasite) > 1 else ''} for {dep.name} in {perioada}.")
    else:
        messages.info(request, f"No messages for {dep.name} in {perioada}.")
    tipuri = {t.code: t for t in MessageType.objects.all()}
    for m in gasite:
        m["tip"] = tipuri.get(m["date"].get("tip_mesaj"))
        # every field of the file, whatever they are: the page doesn't need to know their names
        m["campuri"] = [(cheie, _text_camp(valoare)) for cheie, valoare in m["date"].items() if cheie != "mesaj"]
    return render(request, "instruments/mesaje.html", {"departament": dep, "perioada": perioada, "mesaje": gasite})


# ---------- Adding an instrument (lab 5) ----------


@staff_member_required
def adauga_instrument(request):
    """/produse/adauga: a ModelForm for a new instrument, whose price is worked out from two inputs."""
    if request.method == "POST":
        form = InstrumentForm(request.POST)
        if form.is_valid():
            # commit=False: the instrument is built from the form but not saved yet,
            # so the price (not one of the form's columns) can be set first
            instrument = form.save(commit=False)
            instrument.price = form.pret_vanzare()
            instrument.save()
            form.save_m2m()  # many-to-many fields need the saved instrument's id
            messages.success(request, f"{instrument.name} is in the shop, at {instrument.price:,.0f} lei.")
            return redirect(instrument)  # an object with get_absolute_url() redirects to its page
        messages.error(request, "The instrument wasn't added. The notes next to the fields say what to change.")
    else:
        form = InstrumentForm()
    return render(request, "instruments/instrument_form.html", {"form": form})


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
