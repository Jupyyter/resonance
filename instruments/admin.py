from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import Brand, Category, Distributor, Instrument, Recording, Service

admin.site.site_header = "Resonance administration"
admin.site.site_title = "Resonance admin"
admin.site.index_title = "Shop data"


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
    search_fields = ["name"]

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
    list_display = ["name", "country", "founded_year", "website"]
    list_filter = ["country"]
    search_fields = ["name"]


@admin.register(Distributor)
class DistributorAdmin(MesajeDinModel, admin.ModelAdmin):
    list_display = ["name", "email", "phone"]
    search_fields = ["name", "email"]


@admin.register(Service)
class ServiceAdmin(MesajeDinModel, admin.ModelAdmin):
    list_display = ["name", "price", "duration_days", "available"]
    list_filter = ["available"]
    search_fields = ["name"]


class RecordingInline(MesajeDinModel, admin.TabularInline):
    """A weak entity is edited inside the entity it depends on: recordings on their instrument's page."""

    model = Recording
    extra = 1
    fields = ["number", "title", "audio_file", "duration_s", "sound"]


@admin.register(Instrument)
class InstrumentAdmin(MesajeDinModel, admin.ModelAdmin):
    list_display = ["name", "category", "brand", "condition", "price", "stock", "date_added"]
    list_filter = ["category", "brand", "condition", "left_handed"]
    search_fields = ["name", "description"]
    date_hierarchy = "date_added"
    filter_horizontal = ["services"]
    inlines = [RecordingInline]
    fieldsets = [
        (None, {"fields": ["name", "description", "category", "brand", "image"]}),
        ("Price and stock", {"fields": ["price", "stock", "condition", "distributor"]}),
        ("Details", {"fields": ["left_handed", "weight_kg", "materials", "date_added"]}),
        ("Services", {"fields": ["services"]}),
    ]


@admin.register(Recording)
class RecordingAdmin(MesajeDinModel, admin.ModelAdmin):
    list_display = ["instrument", "number", "title", "sound", "duration_s"]
    list_display_links = ["title"]
    list_filter = ["sound"]
    search_fields = ["title", "instrument__name"]
    autocomplete_fields = ["instrument"]
