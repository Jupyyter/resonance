"""{% icoana "guitar" %} draws an icon from instruments/icoane.py as inline SVG.

A template tag is a Python function templates can call. This file is found because it's in the
app's templatetags/ folder; a template loads it with {% load icoane %}.
"""
from django import template
from django.utils.html import format_html

from ..icoane import ICOANE

register = template.Library()


@register.simple_tag
def icoana(nume):
    eticheta, viewbox, cale = ICOANE.get(nume, ICOANE["music"])  # an unknown name gets the music note
    # aria-hidden: the text next to the icon already says what it is
    return format_html(
        '<svg class="icoana" viewBox="{}" aria-hidden="true" focusable="false"><path fill="currentColor" d="{}"/></svg>',
        viewbox,
        cale,
    )
