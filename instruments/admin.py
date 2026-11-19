import csv
import json

from django.contrib import admin, messages
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.html import format_html

from .models import Brand, Category, Distributor, Instrument, Recording, Service

# The admin's own texts. The look (colours, logo) is in templates/admin/base_site.html and css/admin.css.
admin.site.site_title = "Resonance back office"  # the browser tab
admin.site.site_header = "Resonance back office"  # the header of every admin page
admin.site.index_title = "Catalogue and workshop"  # the admin's main page
# "View site" opens the shop's home page. reverse_lazy: the URLs aren't loaded yet when this file runs.
admin.site.site_url = reverse_lazy("instruments:index")


class MesajeDinModel:
    """Shows the error messages written in models.py also in the admin's forms.

    A form checks "required" and the email/URL format itself, before the model gets a say,
    so without this its generic messages would win. A model's "blank" or "null" message
    becomes the form's "required" message.
    """

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        mesaje = dict(getattr(db_field, "_error_messages", None) or {})  # only the ones we wrote
        if formfield is not None and mesaje:
            for cheie in ("blank", "null"):
                if cheie in mesaje:
                    mesaje.setdefault("required", mesaje[cheie])
            formfield.error_messages.update(mesaje)
        return formfield


@admin.register(Category)
class CategoryAdmin(MesajeDinModel, admin.ModelAdmin):
    list_display = ["name", "swatch", "icon", "display_order", "instrument_count"]
    list_editable = ["display_order"]
    search_fields = ["name", "description"]
    search_help_text = "Searches category names and descriptions. Part of a word is enough."

    def get_queryset(self, request):
        # counts each category's instruments in the same query as the list
        return super().get_queryset(request).annotate(numar_instrumente=Count("instruments"))

    @admin.display(description="colour")
    def swatch(self, obj):
        return format_html(
            '<span style="display:inline-block;width:1.1em;height:1.1em;border-radius:3px;'
            'vertical-align:middle;background:{}"></span> {}',
            obj.color,
            obj.color,
        )

    @admin.display(description="instruments", ordering="numar_instrumente")
    def instrument_count(self, obj):
        return obj.numar_instrumente


@admin.register(Brand)
class BrandAdmin(MesajeDinModel, admin.ModelAdmin):
    # The form's fields in a different order from models.py (there: name, country, website, founded_year).
    fields = ["name", "founded_year", "country", "website"]
    list_display = ["name", "country", "founded_year", "website"]
    list_filter = ["country"]
    search_fields = ["name", "country"]
    search_help_text = "Searches brand names and countries, like Fender or Japan."


@admin.register(Distributor)
class DistributorAdmin(MesajeDinModel, admin.ModelAdmin):
    list_display = ["name", "email", "phone"]
    search_fields = ["name", "email"]
    search_help_text = "Searches distributor names and email addresses."


@admin.register(Service)
class ServiceAdmin(MesajeDinModel, admin.ModelAdmin):
    # The description moves to the end of the form, after the fields people change most often.
    fields = ["name", "price", "duration_days", "available", "description"]
    list_display = ["name", "price", "duration_days", "available"]
    list_filter = ["available"]
    search_fields = ["name", "description"]
    search_help_text = "Searches service names and descriptions, like setup or frets."


class RecordingInline(MesajeDinModel, admin.TabularInline):
    """A weak entity is edited inside the entity it depends on: recordings on their instrument's page."""

    model = Recording
    extra = 1
    fields = ["number", "title", "audio_file", "duration_s", "sound"]


@admin.register(Instrument)
class InstrumentAdmin(MesajeDinModel, admin.ModelAdmin):
    list_display = ["name", "category_name", "brand", "brand_country", "condition", "price", "stock_status", "date_added"]
    list_select_related = ["category", "brand"]  # one query with joins, instead of one more per row
    list_filter = ["category", "brand", "condition", "left_handed", "date_added"]
    search_fields = ["name", "description"]
    search_help_text = "Searches instrument names and descriptions, like Stratocaster or maple."
    ordering = ["-price"]  # the list starts with the most expensive; a column title still re-sorts it
    list_per_page = 5
    date_hierarchy = "date_added"
    filter_horizontal = ["services"]
    inlines = [RecordingInline]
    fieldsets = [
        (None, {"fields": ["name", "description", "category", "brand"]}),
        ("Price and stock", {"fields": ["price", "stock", "condition", "distributor", "date_added"]}),
        (
            "Details",
            {
                # "collapse": a section that starts closed and opens on click; only optional fields here
                "classes": ["collapse"],
                "description": "All optional. They fill the product page and the tag filters.",
                "fields": ["image", "tags", "materials", "weight_kg", "left_handed", "services"],
            },
        ),
    ]
    actions = ["export_csv", "export_json", "mark_sold_out"]

    @admin.display(description="category", ordering="category__name")
    def category_name(self, obj):
        # bold, in the colour the category has in the database
        return format_html('<b style="color:{}">{}</b>', obj.category.color, obj.category.name)

    @admin.display(description="brand country", ordering="brand__country")
    def brand_country(self, obj):
        # a field of the brand, the "1" side of the one-to-many relationship
        return obj.brand.country

    @admin.display(description="stock", ordering="stock")
    def stock_status(self, obj):
        if obj.out_of_stock:
            return format_html('<b style="color:#9b2c2c">sold out</b>')
        if obj.limited_stock:
            return format_html('<b style="color:#8a5a12"><i>only {} left</i></b>', obj.stock)
        return obj.stock

    @admin.action(description="Export the selected instruments as CSV")
    def export_csv(self, request, queryset):
        raspuns = HttpResponse(content_type="text/csv; charset=utf-8")
        raspuns["Content-Disposition"] = f'attachment; filename="instruments-{timezone.localdate()}.csv"'
        raspuns.write("﻿")  # tells Excel the file is UTF-8
        scriitor = csv.writer(raspuns)
        scriitor.writerow(["id", "name", "category", "brand", "condition", "price", "stock", "tags"])
        for i in queryset.select_related("category", "brand"):
            scriitor.writerow([
                i.id, i.name, i.category.name, i.brand.name, i.get_condition_display(),
                i.price, i.stock, ", ".join(i.tags),
            ])
        return raspuns  # an action that returns a response sends it instead of reloading the list

    @admin.action(description="Export the selected instruments as JSON")
    def export_json(self, request, queryset):
        randuri = list(
            queryset.values(
                "id", "name", "category__name", "brand__name", "condition", "price", "stock", "tags", "date_added"
            )
        )
        raspuns = HttpResponse(
            json.dumps(randuri, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2),
            content_type="application/json; charset=utf-8",
        )
        raspuns["Content-Disposition"] = f'attachment; filename="instruments-{timezone.localdate()}.json"'
        return raspuns

    @admin.action(description="Mark the selected instruments as sold out")
    def mark_sold_out(self, request, queryset):
        numar = queryset.update(stock=0)  # one UPDATE for all of them
        self.message_user(request, f"{numar} instruments marked as sold out.", messages.SUCCESS)


@admin.register(Recording)
class RecordingAdmin(MesajeDinModel, admin.ModelAdmin):
    list_display = ["instrument", "number", "title", "sound", "duration_s"]
    list_display_links = ["title"]
    list_filter = ["sound"]
    search_fields = ["title", "instrument__name"]
    search_help_text = "Searches recording titles and the names of their instruments."
    autocomplete_fields = ["instrument"]
