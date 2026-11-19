"""Fills the department and message type tables, and the links between them.

A data migration: it runs once, with "migrate", like the migrations that create tables.
(Lab 5's 0005_contact_data.py, kept when lab 6 started the migrations over: a new database
still gets the departments the contact form needs. A backup loaded afterwards skips these rows,
since they're already there.)
Each message type goes to its own set of departments; the sets overlap but none is the same.
"""
from django.db import migrations

DEPARTAMENTE = [
    ("Customer service", "customer-service"),
    ("Orders", "orders"),
    ("Workshop", "workshop"),
    ("Quality assurance", "quality-assurance"),
    ("Administration", "administration"),
    ("Hiring", "hiring"),
]

# code, name, minimum days, colour, icon, departments
TIPURI = [
    ("reclamatie", "Complaint", 1, "#9B2C2C", "circle-exclamation", ["customer-service", "quality-assurance", "administration"]),
    ("intrebare", "Question", 2, "#2D6B5D", "circle-question", ["customer-service", "workshop", "orders"]),
    ("review", "Review", 4, "#8A5A12", "star", ["quality-assurance", "administration"]),
    ("cerere", "Request", 4, "#3E5C8A", "paper-plane", ["hiring", "administration", "orders"]),
    ("programare", "Appointment", 1, "#6B4C9A", "calendar-check", ["workshop", "customer-service"]),
]


def adauga(apps, schema_editor):
    # apps.get_model: the models as they were at this point of the migrations, not today's
    Department = apps.get_model("instruments", "Department")
    MessageType = apps.get_model("instruments", "MessageType")
    departamente = {slug: Department.objects.create(name=nume, slug=slug) for nume, slug in DEPARTAMENTE}
    for cod, nume, zile, culoare, icon, ale_lui in TIPURI:
        tip = MessageType.objects.create(code=cod, name=nume, min_days=zile, color=culoare, icon=icon)
        tip.departments.set([departamente[slug] for slug in ale_lui])


def sterge(apps, schema_editor):
    apps.get_model("instruments", "MessageType").objects.all().delete()
    apps.get_model("instruments", "Department").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("instruments", "0001_initial")]
    # the second function undoes the first, so "migrate instruments 0004" can go back
    operations = [migrations.RunPython(adauga, sterge)]
