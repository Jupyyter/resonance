"""The shop's database: one class per entity in the diagram (docs/diagrama-bd.png).

Each class becomes a table, and each field a column. Django adds an "id" primary key to every
model, so the diagram's id attributes don't appear below. A ForeignKey is the "1" side of a
one-to-many relationship, seen from the "N" side; a ManyToManyField creates the join table itself.

Rules are checked in two places:
- by Django, before saving (the admin's forms run full_clean(): required fields, max_length,
  unique, email/URL format, choices, and the constraints below), which gives friendly messages;
- by PostgreSQL itself (NOT NULL, UNIQUE and the CHECK constraints), so even data that doesn't
  go through Django can't break them.
"""
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from django.utils import timezone

HEX_COLOR = r"^#[0-9A-Fa-f]{6}$"


class Category(models.Model):
    """A group of instruments: electric guitars, basses, keyboards..."""

    name = models.CharField(
        max_length=50,
        unique=True,
        error_messages={
            "unique": "There's already a category with this name.",
            "blank": "Give the category a name.",
        },
    )
    description = models.TextField()
    color = models.CharField(
        max_length=7,
        default="#2D6B5D",
        help_text="Hex colour used to style this category's pages, like #2D6B5D.",
    )
    icon = models.CharField(
        max_length=40,
        default="music",
        help_text="Name of a Font Awesome icon, like guitar, drum or music.",
    )
    display_order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Position in menus and lists. Lower numbers come first.",
    )

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"  # Django would write "categorys"
        ordering = ["display_order", "name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(color__regex=HEX_COLOR),
                name="category_color_hex",
                violation_error_message="The colour must be # followed by 6 hex digits, like #2D6B5D.",
            ),
        ]

    def __str__(self):
        return self.name


class Brand(models.Model):
    """The company that makes an instrument."""

    name = models.CharField(
        max_length=60,
        unique=True,
        error_messages={"unique": "This brand already exists."},
    )
    country = models.CharField(max_length=60)
    # null=True: the column may hold NULL ("we don't know"). blank=True: the admin form may be empty.
    website = models.URLField(
        null=True,
        blank=True,
        error_messages={"invalid": "Enter the full address, starting with https://."},
    )
    founded_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Leave empty if you don't know it.",
    )

    class Meta:
        verbose_name = "brand"
        verbose_name_plural = "brands"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(founded_year__isnull=True) | Q(founded_year__gte=1600),
                name="brand_founded_after_1600",
                violation_error_message="The founding year must be 1600 or later.",
            ),
        ]

    def __str__(self):
        return self.name


class Distributor(models.Model):
    """A partner company the shop buys new instruments from."""

    name = models.CharField(max_length=80, unique=True)
    email = models.EmailField(
        unique=True,
        error_messages={
            "invalid": "This isn't a valid email address.",
            "unique": "Another distributor already uses this email address.",
        },
    )
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="With the country code, like +40 21 000 1234.",
    )

    class Meta:
        verbose_name = "distributor"
        verbose_name_plural = "distributors"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(phone__isnull=True) | Q(phone__regex=r"^\+?[0-9 ]{7,20}$"),
                name="distributor_phone_digits",
                violation_error_message="A phone number has only digits and spaces, with an optional + in front.",
            ),
        ]

    def __str__(self):
        return self.name


class Service(models.Model):
    """An extra the shop offers with an instrument: a setup, fret work, a rental..."""

    name = models.CharField(max_length=60, unique=True)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="In lei. For rentals, the price per day.",
    )
    duration_days = models.PositiveSmallIntegerField(
        default=1,
        help_text="Working days the workshop needs. For rentals, the shortest rental.",
    )
    available = models.BooleanField(default=True)

    class Meta:
        verbose_name = "service"
        verbose_name_plural = "services"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="service_price_not_negative",
                violation_error_message="A price can't be negative.",
            ),
            models.CheckConstraint(
                condition=Q(duration_days__gte=1) & Q(duration_days__lte=60),
                name="service_duration_1_to_60_days",
                violation_error_message="The duration must be between 1 and 60 days.",
            ),
        ]

    def __str__(self):
        return self.name


class Instrument(models.Model):
    """The product the shop sells."""

    class Condition(models.TextChoices):
        # value stored in the database, label shown to people
        NEW = "new", "New"
        USED = "used", "Used"
        REFURBISHED = "refurbished", "Refurbished"

    name = models.CharField(
        max_length=100,
        error_messages={
            "blank": "Every instrument needs a name.",
            "max_length": "Keep the name under 100 characters; put the rest in the description.",
        },
    )
    description = models.TextField()
    price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        help_text="In lei, VAT included.",
        error_messages={"null": "Every instrument needs a price."},
    )
    stock = models.PositiveIntegerField(default=0)
    condition = models.CharField(max_length=12, choices=Condition.choices, default=Condition.NEW)
    left_handed = models.BooleanField(
        default=False,
        help_text="Tick it for guitars and basses built for left-handed players.",
    )
    weight_kg = models.FloatField(null=True, blank=True, help_text="Without the case. Leave empty if unknown.")
    # default=timezone.now (no brackets): Django calls it at each new instrument, so the default is
    # the moment it's added. With brackets it would be the moment the server started, for all of them.
    date_added = models.DateTimeField(default=timezone.now)
    materials = ArrayField(
        models.CharField(max_length=30),
        default=list,
        blank=True,
        help_text="Separate them with commas, like: alder, maple, rosewood.",
    )
    image = models.ImageField(upload_to="instrumente/", null=True, blank=True)

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="instruments")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="instruments")
    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instruments",
        help_text="Required for new instruments. Leave empty for used and trade-in ones.",
    )
    services = models.ManyToManyField(
        Service,
        blank=True,
        related_name="instruments",
        help_text="Services a buyer can add to this instrument.",
    )

    class Meta:
        verbose_name = "instrument"
        verbose_name_plural = "instruments"
        ordering = ["-date_added"]  # newest first
        indexes = [
            # columns the shop will search, filter and sort by (labs 4 and 5)
            models.Index(fields=["name"], name="instrument_name_idx"),
            models.Index(fields=["price"], name="instrument_price_idx"),
            models.Index(fields=["condition"], name="instrument_condition_idx"),
            models.Index(fields=["-date_added"], name="instrument_date_added_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gt=0),
                name="instrument_price_positive",
                violation_error_message="The price must be greater than 0.",
            ),
            models.CheckConstraint(
                condition=Q(weight_kg__isnull=True) | (Q(weight_kg__gt=0) & Q(weight_kg__lt=200)),
                name="instrument_weight_realistic",
                violation_error_message="The weight must be between 0 and 200 kg.",
            ),
            models.CheckConstraint(
                # a used or refurbished instrument is one of a kind
                condition=Q(condition="new") | Q(stock__lte=1),
                name="instrument_used_is_single",
                violation_error_message="A used or refurbished instrument is one of a kind: stock 0 or 1.",
            ),
            models.CheckConstraint(
                # ~Q(...) means "not": either it isn't new, or it has a distributor
                condition=~Q(condition="new") | Q(distributor__isnull=False),
                name="instrument_new_has_distributor",
                violation_error_message="A new instrument needs the distributor it came from.",
            ),
        ]

    def __str__(self):
        return self.name


class Recording(models.Model):
    """A sound sample of an instrument (the weak entity).

    It belongs to exactly one instrument and is numbered within it: recording 2 of a guitar.
    The pair (instrument, number) identifies it, so it must be unique; on_delete=CASCADE deletes
    the recordings together with their instrument. Django still adds its own id column, because
    the admin can't work with a key made of two columns.
    """

    class Sound(models.TextChoices):
        CLEAN = "clean", "Clean"
        AMPLIFIED = "amplified", "Amplified"
        EFFECTS = "effects", "With effects"

    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name="recordings")
    number = models.PositiveSmallIntegerField(
        help_text="1 for the instrument's first recording, 2 for its second, and so on.",
    )
    title = models.CharField(max_length=80, error_messages={"blank": "Give the recording a title."})
    audio_file = models.FileField(upload_to="inregistrari/", help_text="A WAV, MP3 or OGG file.")
    duration_s = models.PositiveSmallIntegerField(help_text="Length in seconds.")
    sound = models.CharField(max_length=10, choices=Sound.choices, default=Sound.CLEAN)

    class Meta:
        verbose_name = "recording"
        verbose_name_plural = "recordings"
        ordering = ["instrument", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["instrument", "number"],
                name="recording_number_unique_per_instrument",
                violation_error_message="This instrument already has a recording with this number.",
            ),
            models.CheckConstraint(
                condition=Q(number__gte=1),
                name="recording_number_from_1",
                violation_error_message="Recordings are numbered from 1.",
            ),
            models.CheckConstraint(
                condition=Q(duration_s__gte=1) & Q(duration_s__lte=600),
                name="recording_duration_1s_to_10min",
                violation_error_message="A recording lasts between 1 second and 10 minutes.",
            ),
        ]

    def __str__(self):
        return f"{self.instrument}: {self.number}. {self.title}"
