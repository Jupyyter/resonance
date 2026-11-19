"""Run with:  python manage.py test instruments"""
from contextlib import redirect_stdout
from io import StringIO
from itertools import count

from django.test import TestCase

from . import accesari as jurnal


class PaginiTest(TestCase):
    def setUp(self):
        # Every test starts with an empty log, and ids from 1 again.
        jurnal.accesari.clear()
        jurnal.Accesare._urmatorul_id = count(1)

    def get(self, adresa):
        with redirect_stdout(StringIO()):  # every visit is printed to the terminal; keep tests quiet
            return self.client.get(adresa)

    def test_toate_paginile_raspund(self):
        for adresa in ["/", "/info", "/log", "/despre", "/istoric", "/services", "/faq"]:
            self.assertEqual(self.get(adresa).status_code, 200, adresa)

    def test_paginile_neterminate_arata_in_lucru(self):
        for adresa in ["/produse", "/contact", "/cos_virtual"]:
            self.assertContains(self.get(adresa), "<title>In lucru</title>", html=False)

    def test_fiecare_pagina_e_inregistrata(self):
        self.get("/")
        self.get("/despre?x=1")
        self.assertEqual([a.pagina() for a in jurnal.accesari], ["/", "/despre"])
        self.assertEqual(jurnal.accesari[1].lista_parametri(), [("x", "1")])

    def test_adminul_nu_e_inregistrat(self):
        self.get("/admin/login/")
        self.assertEqual(jurnal.accesari, [])

    def test_accesare_dupa_id(self):
        self.get("/")
        id_ = jurnal.accesari[0].id
        self.assertContains(self.get(f"/accesare{id_}"), f"Accesarea {id_}")
        self.assertEqual(self.get("/accesare999999").status_code, 404)

    def test_ultimele_mai_multe_decat_exista(self):
        self.get("/")
        raspuns = self.get("/log?ultimele=50")  # 2 visits so far: / and this one
        self.assertContains(raspuns, "Există doar 2 accesări față de 50 accesări cerute")
        self.assertEqual(len(raspuns.context["selectie"]), 2)

    def test_ultimele_care_nu_e_numar(self):
        self.assertContains(self.get("/log?ultimele=abc"), "ultimele trebuie să fie un număr natural")

    def test_exemplul_din_laborator(self):
        for _ in range(5):
            self.get("/")  # visits 1 to 5
        adresa = "/log?iduri=2,3&iduri=5&iduri=4,2,1"
        fara = self.get(adresa).context["selectie"]
        cu = self.get(adresa + "&dubluri=true").context["selectie"]
        self.assertEqual([a.id for a in fara], [2, 3, 5, 4, 1])
        self.assertEqual([a.id for a in cu], [2, 3, 5, 4, 2, 1])

    def test_sectiunea_parametri(self):
        raspuns = self.get("/log?iduri=1&iduri=2&tabel=tot")
        self.assertContains(raspuns, "Pagina a primit 2 parametri: iduri, tabel.")

    def test_accesari_detalii_e_lista_neordonata(self):
        self.assertContains(self.get("/log?accesari=detalii"), '<ul class="date-accesari">')

    def test_tabel(self):
        self.get("/")
        tabel = self.get("/log?tabel=id,pagina").context["tabel"]
        self.assertEqual(tabel["antet"], ["Id", "Pagina"])
        self.assertContains(self.get("/log?tabel=nu_exista"), "Coloane necunoscute: nu_exista.")

    def test_pagini_extreme(self):
        self.get("/")
        self.get("/")
        self.get("/despre")
        (minime, _), (maxime, numar_maxim) = jurnal.pagini_extreme()
        self.assertEqual(maxime, ["/"])
        self.assertEqual(numar_maxim, 2)
        self.assertIn("/faq", minime)  # never visited, so 0


class CateTest(TestCase):
    def test_romana(self):
        self.assertEqual(jurnal.cate(1, "accesare", "accesări"), "1 accesare")
        self.assertEqual(jurnal.cate(5, "accesare", "accesări"), "5 accesări")
        self.assertEqual(jurnal.cate(20, "accesare", "accesări"), "20 de accesări")
        self.assertEqual(jurnal.cate(101, "accesare", "accesări"), "101 accesări")
        self.assertEqual(jurnal.cate(100, "accesare", "accesări"), "100 de accesări")


class ModeleTest(TestCase):
    """The rules in models.py, checked both by Django (full_clean) and by PostgreSQL itself."""

    def setUp(self):
        from .models import Brand, Category, Distributor

        self.categorie = Category.objects.create(name="Basses", description="Four strings and more.")
        self.brand = Brand.objects.create(name="Fender", country="USA")
        self.distribuitor = Distributor.objects.create(name="Test Music SRL", email="test@example.com")

    def instrument(self, **campuri):
        from .models import Instrument

        valori = {
            "name": "Precision Bass", "description": "A bass.", "price": 4000,
            "category": self.categorie, "brand": self.brand, "distributor": self.distribuitor,
        }
        valori.update(campuri)
        return Instrument(**valori)

    def test_un_instrument_corect_se_salveaza(self):
        instrument = self.instrument(materials=["alder", "maple"])
        instrument.full_clean()
        instrument.save()
        self.assertEqual(instrument.condition, "new")  # the default
        self.assertEqual(instrument.materials, ["alder", "maple"])

    def test_mesajele_constrangerilor(self):
        from django.core.exceptions import ValidationError

        cazuri = [
            ({"price": 0}, "The price must be greater than 0."),
            ({"condition": "used", "stock": 3, "distributor": None}, "one of a kind"),
            ({"distributor": None}, "A new instrument needs the distributor it came from."),
            ({"weight_kg": 500}, "between 0 and 200 kg"),
        ]
        for campuri, mesaj in cazuri:
            with self.subTest(campuri=campuri):
                with self.assertRaises(ValidationError) as eroare:
                    self.instrument(**campuri).full_clean()
                self.assertIn(mesaj, str(eroare.exception))

    def test_postgresql_respinge_si_el(self):
        """Even skipping Django's checks (save() without full_clean), the database says no."""
        from django.db import IntegrityError, transaction

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.instrument(price=-5).save()

    def test_mesaj_unicitate(self):
        from django.core.exceptions import ValidationError

        from .models import Category

        with self.assertRaises(ValidationError) as eroare:
            Category(name="Basses", description="Again.").full_clean()
        self.assertIn("There's already a category with this name.", str(eroare.exception))

    def test_culoare_categorie(self):
        from django.core.exceptions import ValidationError

        from .models import Category

        with self.assertRaises(ValidationError):
            Category(name="Drums", description="Kits.", color="red").full_clean()

    def test_inregistrarile_sunt_numerotate_unic_pe_instrument(self):
        from django.core.exceptions import ValidationError

        from .models import Recording

        instrument = self.instrument()
        instrument.save()
        Recording.objects.create(instrument=instrument, number=1, title="Clean", audio_file="a.wav", duration_s=5)
        with self.assertRaises(ValidationError) as eroare:
            Recording(instrument=instrument, number=1, title="Again", audio_file="b.wav", duration_s=5).full_clean()
        self.assertIn("already has a recording with this number", str(eroare.exception))


class IncarcaDateTest(TestCase):
    """python manage.py incarca_date, with uploads going to a temporary folder."""

    def setUp(self):
        import tempfile

        from django.test import override_settings

        self.dosar_media = tempfile.TemporaryDirectory()
        self.setari = override_settings(MEDIA_ROOT=self.dosar_media.name)
        self.setari.enable()

    def tearDown(self):
        self.setari.disable()
        self.dosar_media.cleanup()

    def incarca(self, *argumente):
        from django.core.management import call_command

        call_command("incarca_date", *argumente, stdout=StringIO())

    def test_incarca_tot_si_a_doua_oara_nu_dubleaza(self):
        from .models import Brand, Category, Distributor, Instrument, Recording, Service

        self.incarca()
        self.incarca()
        numere = [m.objects.count() for m in (Category, Brand, Distributor, Service, Instrument, Recording)]
        self.assertEqual(numere, [6, 6, 5, 5, 10, 5])
        strat = Instrument.objects.get(name="Fender Player II Stratocaster")
        self.assertEqual(strat.services.count(), 2)
        self.assertEqual(strat.recordings.first().audio_file.name, "inregistrari/chitara-electrica-clean.wav")

    def test_un_rand_gresit_opreste_tot(self):
        import json
        import tempfile

        from django.core.management.base import CommandError

        from .models import Category

        date = {"categories": [{"name": "Ok", "description": "Fine."}, {"name": "Bad", "description": "x", "color": "red"}]}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(date, f)
        with self.assertRaises(CommandError) as eroare:
            self.incarca("--fisier", f.name)
        self.assertIn("The colour must be #", str(eroare.exception))
        self.assertFalse(Category.objects.exists())  # not even the good row was kept
