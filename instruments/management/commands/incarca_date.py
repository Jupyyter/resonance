"""python manage.py incarca_date: loads the sample data from date_exemplu/date.json.

Every file in management/commands/ becomes a manage.py command named after the file, like
migrate or runserver. Django runs the class called Command.

Each row goes through full_clean() before saving, the same checks the admin runs, so bad data
stops with the same messages. Rows are matched by name (recordings by instrument and number),
so running the command again updates them instead of adding copies. It all happens in one
transaction: if any row is wrong, nothing is saved.
"""
import json
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from instruments.models import Brand, Category, Distributor, Instrument, Recording, Service

DOSAR = Path(settings.BASE_DIR) / "date_exemplu"


class Command(BaseCommand):
    help = "Loads the sample data from date_exemplu/date.json (can be run again safely)."

    def add_arguments(self, parser):
        parser.add_argument("--fisier", default=DOSAR / "date.json", type=Path, help="Another JSON file to load.")

    def handle(self, *args, **options):
        fisier = options["fisier"]
        try:
            date = json.loads(fisier.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise CommandError(f"Can't find {fisier}.")

        self.raport = []
        with transaction.atomic():
            # The order matters: instruments point to categories, brands, distributors and services.
            for camp, model in [
                ("categories", Category),
                ("brands", Brand),
                ("distributors", Distributor),
                ("services", Service),
            ]:
                for rand in date.get(camp, []):
                    self.salveaza(model, {"name": rand["name"]}, rand)
                self.raporteaza(model, len(date.get(camp, [])))

            for rand in date.get("instruments", []):
                rand = dict(rand)
                servicii = rand.pop("services", [])
                rand["category"] = self.gaseste(Category, rand["category"])
                rand["brand"] = self.gaseste(Brand, rand["brand"])
                rand["distributor"] = self.gaseste(Distributor, rand.get("distributor"))
                instrument = self.salveaza(Instrument, {"name": rand["name"]}, rand)
                # many-to-many links can only be set once the instrument has an id, so after saving
                instrument.services.set([self.gaseste(Service, nume) for nume in servicii])
            self.raporteaza(Instrument, len(date.get("instruments", [])))

            for rand in date.get("recordings", []):
                rand = dict(rand)
                nume_fisier = rand.pop("audio_file")
                rand["instrument"] = self.gaseste(Instrument, rand["instrument"])
                self.salveaza(
                    Recording,
                    {"instrument": rand["instrument"], "number": rand["number"]},
                    rand,
                    fisier_audio=nume_fisier,
                )
            self.raporteaza(Recording, len(date.get("recordings", [])))

        # printed only now: until the transaction ends, nothing is really saved
        for linie in self.raport:
            self.stdout.write(linie)
        self.stdout.write(self.style.SUCCESS("Done. Everything is in the admin now."))

    def salveaza(self, model, cheie, valori, fisier_audio=None):
        """Finds the row by its key (or starts a new one), sets its values, checks it, saves it."""
        obiect = model.objects.filter(**cheie).first() or model(**cheie)
        for camp, valoare in valori.items():
            setattr(obiect, camp, valoare)

        if fisier_audio:
            # where an upload of this file ends up: media/inregistrari/<name>
            destinatie = model._meta.get_field("audio_file").upload_to + fisier_audio
            if obiect.audio_file.name != destinatie:
                if obiect.audio_file.storage.exists(destinatie):
                    obiect.audio_file.name = destinatie  # copied by an earlier run: reuse it
                else:
                    sursa = DOSAR / "inregistrari" / fisier_audio
                    if not sursa.exists():
                        raise CommandError(f"Can't find the audio file {sursa}.")
                    with sursa.open("rb") as f:
                        # copies the file into media/, exactly like an upload in the admin
                        obiect.audio_file.save(fisier_audio, File(f), save=False)

        try:
            obiect.full_clean()
        except ValidationError as eroare:
            # errors that belong to no single field (the constraints) come under "__all__"
            mesaje = "; ".join(
                (f"{camp}: " if camp != "__all__" else "") + " ".join(m) for camp, m in eroare.message_dict.items()
            )
            raise CommandError(f"{model._meta.verbose_name} {cheie}: {mesaje}")
        obiect.save()
        return obiect

    def gaseste(self, model, nume):
        """The row with this name, for a link (None stays None, for an empty distributor)."""
        if nume is None:
            return None
        try:
            return model.objects.get(name=nume)
        except model.DoesNotExist:
            raise CommandError(f"There's no {model._meta.verbose_name} named {nume!r} in the file.")

    def raporteaza(self, model, numar):
        self.raport.append(f"{model._meta.verbose_name_plural.capitalize()}: {numar}")
