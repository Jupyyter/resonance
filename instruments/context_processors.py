"""Context processors: functions whose result is added to the context of EVERY template.

Django calls each one listed in settings.TEMPLATES[...]["OPTIONS"]["context_processors"] when it
renders a template with a request (render() does), and merges the dicts they return. That's how
the footer in baza.html can show the company's details without every view passing them.
"""
from django.conf import settings
from django.db.models import Count
from django.utils import timezone

from .models import Category

# Which top-level menu entry each page belongs to, so the menu can mark where the visitor is.
SECTIUNI_MENIU = {
    "index": "acasa",
    "produse": "categorii",
    "produs": "categorii",
    "categorie": "categorii",
    "services": "despre",
    "despre": "despre",
    "istoric": "despre",
    "faq": "despre",
    "contact": "contact",
    "cos_virtual": "cos",
    "info": "site",
    "log": "site",
    "accesare": "site",
    "login": "cont",
    "inregistrare": "inregistrare",
    "profil": "cont",
    "date_cont": "cont",
    "parola": "cont",
}


def companie(request):
    """The company's details from settings.COMPANY_INFO ({{ companie.name }} etc.)
    and the copyright line built from them ({{ copyright }})."""
    firma = settings.COMPANY_INFO
    an_curent = timezone.localdate().year
    ani = f"{firma['founded']}–{an_curent}" if an_curent > firma["founded"] else str(an_curent)
    return {
        "companie": firma,
        "copyright": f"© {ani} {firma['name']}. All rights reserved.",
    }


def meniu(request):
    """For the menu: the entry to mark as current ({{ sectiune_activa }}) and the categories
    of the Categories submenu ({{ categorii_meniu }}).

    The categories come from the database, so a new one appears in the menu by itself. Only
    those with at least one instrument: Count() adds a column with each one's number of
    instruments, and filter() keeps the rows where it's over 0. A QuerySet is lazy: the query
    only runs if a template actually loops over it (the admin's pages never do).
    """
    potrivire = getattr(request, "resolver_match", None)
    return {
        "sectiune_activa": SECTIUNI_MENIU.get(potrivire.url_name) if potrivire else None,
        # order_by again: Django leaves out the model's Meta.ordering in queries that group rows (Count)
        "categorii_meniu": Category.objects.annotate(numar=Count("instruments"))
        .filter(numar__gt=0)
        .order_by("display_order", "name"),
    }
