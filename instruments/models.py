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
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from .icoane import ALEGERI as ICOANE_CATEGORII
from .validatori import (
    e_romania,
    judet_roman,
    majuscula_si_litere,
    strada_cu_numar,
    telefon_valid,
)

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
        choices=ICOANE_CATEGORII,  # the icons in icoane.py, so every choice can be drawn
        default="music",
        help_text="The icon shown next to the category's name, in a circle of its colour.",
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

    def get_absolute_url(self):
        """The category's own page: /categorii/<name>."""
        return reverse("instruments:categorie", args=[self.name])


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
    tags = ArrayField(
        models.CharField(max_length=30),
        default=list,
        blank=True,
        help_text="Keywords for filtering on the shop's pages, separated by commas, like: vintage, beginner.",
    )

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
            # a GIN index looks inside arrays: it serves "tags contain all of these" filters
            GinIndex(fields=["tags"], name="instrument_tags_gin"),
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

    def clean(self):
        # run by full_clean(), before saving from the admin: tags in lowercase, without repeats,
        # so a filter for "vintage" also finds a tag typed as "Vintage "
        self.tags = list(dict.fromkeys(t.strip().lower() for t in self.tags if t.strip()))

    def get_absolute_url(self):
        """The instrument's own page: /produse/<id>. Templates and the admin's "View on site" use it."""
        return reverse("instruments:produs", args=[self.id])

    @property
    def out_of_stock(self):
        return self.stock == 0

    @property
    def limited_stock(self):
        """Still in stock, but fewer than settings.STOC_MIN."""
        return 0 < self.stock < settings.STOC_MIN


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


# ---------- The contact form (lab 5) ----------


class Department(models.Model):
    """Who in the shop a contact message goes to. Its slug names its folder in Mesaje_nerezolvate."""

    name = models.CharField(max_length=60, unique=True, error_messages={"unique": "This department already exists."})
    slug = models.SlugField(
        max_length=60,
        unique=True,
        help_text="Lowercase letters, digits and hyphens. Names the department's message folder and its address in /mesaje.",
    )
    # Lab 6: who leads it. "Employee" in quotes, because that class comes further down the file.
    head = models.ForeignKey(
        "Employee",
        on_delete=models.SET_NULL,  # if the head leaves, the department stays, without a head
        null=True,
        blank=True,
        related_name="departments_led",
        help_text="Someone who works in this department. Can stay empty.",
    )

    class Meta:
        verbose_name = "department"
        verbose_name_plural = "departments"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        # The head must be one of the department's own employees.
        if self.head_id and self.head.department_id != self.pk:
            raise ValidationError({"head": f"{self.head} works in {self.head.department}, not in this department."})


class MessageType(models.Model):
    """A kind of contact message: complaint, question, review, request, appointment.

    departments is a many-to-many relationship, so Django creates the link table
    (instruments_messagetype_departments) between message types and departments.
    """

    code = models.SlugField(max_length=20, unique=True, help_text="The value the contact form sends, like review.")
    name = models.CharField(max_length=40)
    min_days = models.PositiveSmallIntegerField(
        help_text="The fewest days a sender may choose to wait for an answer to this kind of message."
    )
    color = models.CharField(max_length=7, default="#2D6B5D", help_text="Hex colour that marks these messages in /mesaje.")
    icon = models.CharField(max_length=40, default="envelope", help_text="Name of a Font Awesome icon, like star.")
    departments = models.ManyToManyField(Department, related_name="message_types")

    class Meta:
        verbose_name = "message type"
        verbose_name_plural = "message types"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(min_days__gte=1) & Q(min_days__lte=30),
                name="messagetype_min_days_1_to_30",
                violation_error_message="The minimum wait is between 1 and 30 days.",
            ),
        ]

    def __str__(self):
        return self.name


# =====================================================================================
# Lab 6: users, their orders and what they write about instruments
# =====================================================================================


class User(AbstractUser):
    """The site's account. settings.AUTH_USER_MODEL points Django to it instead of its own User.

    AbstractUser already has id, username, first_name, last_name, email, password (stored as a
    salted hash, never as typed), is_staff, is_superuser, is_active, last_login and date_joined.
    Added here: the delivery details, which every account has. The optional details live in
    Profile, and only for the users who fill them in.
    """

    # AbstractUser's email may be empty and repeated; an account here needs its own.
    email = models.EmailField(
        "email",
        unique=True,
        error_messages={"unique": "There's already an account with this email."},
    )
    phone = models.CharField(max_length=20, validators=[telefon_valid])
    country = models.CharField(max_length=60, default="Romania", validators=[majuscula_si_litere])
    county = models.CharField(
        max_length=60,
        validators=[majuscula_si_litere],
        help_text="For Romania, the county, or București. Elsewhere, the region or state.",
    )
    city = models.CharField(max_length=60, validators=[majuscula_si_litere])
    street = models.CharField(
        max_length=120,
        validators=[strada_cu_numar],
        help_text="Street and number, then the building and apartment if there are any.",
    )

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["username"]

    def clean(self):
        super().clean()
        # Django lowercases only the part after @; the whole address, so Ana@ and ana@ are one account
        self.email = self.email.lower()
        # In Romania, the county must be a real one, and is stored spelled properly.
        if self.county and e_romania(self.country):
            try:
                self.county = judet_roman(self.county)
            except ValidationError as eroare:
                raise ValidationError({"county": eroare})

    def adresa(self):
        return ", ".join(p for p in (self.street, self.city, self.county, self.country) if p)


class Profile(models.Model):
    """The optional details of an account. A user has a row here only if they filled in at least
    one of these, so the table has no rows full of empty values.

    primary_key=True on the one-to-one: the profile's id is its user's id, so a user can't have two.
    """

    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        PROFESSIONAL = "professional", "Professional"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name="profile")
    date_of_birth = models.DateField(null=True, blank=True)
    level = models.CharField(
        max_length=12,
        choices=Level.choices,
        blank=True,
        help_text="How well the user plays, so the shop can suggest instruments that fit.",
    )
    favorite_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,  # deleting a category doesn't delete profiles
        null=True,
        blank=True,
        related_name="fans",
    )
    bio = models.TextField("about", max_length=500, blank=True)

    class Meta:
        verbose_name = "profile"
        verbose_name_plural = "profiles"

    def __str__(self):
        return f"Profile of {self.user}"


class Employee(models.Model):
    """A user who works for the shop. Only what being an employee adds: the name, email and the
    rest are in the user's own row, reached through the one-to-one link."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name="employee"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,  # a department with employees can't be deleted
        related_name="employees",
    )
    job_title = models.CharField(max_length=80)
    hired_on = models.DateField(default=timezone.localdate)
    salary = models.DecimalField(max_digits=8, decimal_places=2, help_text="Gross, in lei per month.")

    class Meta:
        verbose_name = "employee"
        verbose_name_plural = "employees"
        ordering = ["department", "user__last_name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(salary__gt=0),
                name="employee_salary_positive",
                violation_error_message="The salary must be more than 0.",
            ),
        ]

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Order(models.Model):
    """An order: who placed it, when, how it's delivered and paid, and where it is now.

    products is a many-to-many relationship through OrderItem: an order has several instruments,
    an instrument is in several orders, and each pair also has a quantity and a price.
    """

    class Status(models.TextChoices):
        PLACED = "placed", "Placed"
        PAID = "paid", "Paid"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class Payment(models.TextChoices):
        CARD = "card", "Card"
        CASH_ON_DELIVERY = "cash_on_delivery", "Cash on delivery"
        BANK_TRANSFER = "bank_transfer", "Bank transfer"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # orders are kept for the accounts: a user with orders can't be deleted
        related_name="orders",
    )
    placed_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PLACED)
    by_courier = models.BooleanField(default=True, help_text="Unticked: collected from the shop.")
    payment_method = models.CharField(max_length=16, choices=Payment.choices, default=Payment.CARD)
    products = models.ManyToManyField(Instrument, through="OrderItem", related_name="orders")

    class Meta:
        verbose_name = "order"
        verbose_name_plural = "orders"
        ordering = ["-placed_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["placed", "paid", "shipped", "delivered", "cancelled"]),
                name="order_status_valid",
                violation_error_message="The status is placed, paid, shipped, delivered or cancelled.",
            ),
            models.CheckConstraint(
                # the courier collects the money, so cash on delivery needs a courier
                condition=~Q(payment_method="cash_on_delivery") | Q(by_courier=True),
                name="order_cash_needs_courier",
                violation_error_message="Cash on delivery only works with a courier.",
            ),
        ]

    def __str__(self):
        return f"Order {self.pk} by {self.user}"

    def total(self):
        return sum((i.unit_price * i.quantity for i in self.items.all()), 0)


class OrderItem(models.Model):
    """One instrument in one order: the link table of the many-to-many, with its own columns."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    instrument = models.ForeignKey(Instrument, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveSmallIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        help_text="The price when the order was placed. Later price changes don't touch it.",
    )

    class Meta:
        verbose_name = "order item"
        verbose_name_plural = "order items"
        constraints = [
            models.UniqueConstraint(
                fields=["order", "instrument"],
                name="orderitem_once_per_order",
                violation_error_message="This instrument is already in the order: change its quantity instead.",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=1), name="orderitem_quantity_positive",
                violation_error_message="The quantity is at least 1.",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gt=0), name="orderitem_price_positive",
                violation_error_message="The price must be more than 0.",
            ),
        ]

    def __str__(self):
        return f"{self.quantity} × {self.instrument}"


class Review(models.Model):
    """A user's stars and words about an instrument. One per user and instrument."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(help_text="From 1 to 5 stars.")
    text = models.TextField(max_length=2000, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "review"
        verbose_name_plural = "reviews"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "instrument"],
                name="review_once_per_instrument",
                violation_error_message="This user has already reviewed this instrument.",
            ),
            models.CheckConstraint(
                condition=Q(rating__gte=1) & Q(rating__lte=5),
                name="review_rating_1_to_5",
                violation_error_message="The rating is from 1 to 5 stars.",
            ),
        ]

    def __str__(self):
        return f"{self.rating}★ for {self.instrument} by {self.user}"


class Favorite(models.Model):
    """An instrument on a user's wish list."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name="favorited_by")
    added_at = models.DateTimeField(default=timezone.now)
    price_alert = models.BooleanField(default=False, help_text="Email the user when the price drops.")

    class Meta:
        verbose_name = "favorite"
        verbose_name_plural = "favorites"
        ordering = ["-added_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "instrument"],
                name="favorite_once_per_instrument",
                violation_error_message="This instrument is already on the list.",
            ),
        ]

    def __str__(self):
        return f"{self.instrument} on {self.user}'s list"


class Question(models.Model):
    """A user's question about an instrument, and an employee's answer once there is one."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="questions")
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField(max_length=1000)
    asked_at = models.DateTimeField(default=timezone.now)
    answer = models.TextField(max_length=2000, blank=True)
    answered_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="answers"
    )
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "question"
        verbose_name_plural = "questions"
        ordering = ["-asked_at"]
        constraints = [
            models.CheckConstraint(
                # an answer has a date, and a date has an answer
                condition=(Q(answer="") & Q(answered_at__isnull=True)) | (~Q(answer="") & Q(answered_at__isnull=False)),
                name="question_answer_has_date",
                violation_error_message="An answer needs the date it was given, and a date needs an answer.",
            ),
        ]

    def __str__(self):
        return f"{self.user} about {self.instrument}"
