"""Context processors: functions whose result is added to the context of EVERY template.

Django calls each one listed in settings.TEMPLATES[...]["OPTIONS"]["context_processors"] when it
renders a template with a request (render() does), and merges the dicts they return. That's how
the footer in baza.html can show the company's details without every view passing them.
"""
from django.conf import settings
from django.utils import timezone

# Which top-level menu entry each page belongs to, so the menu can mark where the visitor is.
SECTIUNI_MENIU = {
    "index": "acasa",
    "produse": "magazin",
    "services": "magazin",
    "despre": "despre",
    "istoric": "despre",
    "faq": "despre",
    "contact": "contact",
    "cos_virtual": "cos",
    "info": "site",
    "log": "site",
    "accesare": "site",
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
    """The menu entry to mark as current: {{ sectiune_activa }}."""
    potrivire = getattr(request, "resolver_match", None)
    return {"sectiune_activa": SECTIUNI_MENIU.get(potrivire.url_name) if potrivire else None}
