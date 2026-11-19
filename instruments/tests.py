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
        for adresa in ["/cos_virtual"]:
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


class CuInstrumente(TestCase):
    """Four instruments in three categories, for the tests of the listings. No tests of its own."""

    @classmethod
    def setUpTestData(cls):
        # made once for the whole class; every test still runs inside its own transaction
        from .models import Brand, Category, Distributor, Instrument

        cls.chitare = Category.objects.create(name="Guitars", description="Six strings.", icon="guitar", display_order=2)
        cls.tobe = Category.objects.create(name="Drums", description="Kits.", icon="drum", display_order=1)
        cls.goala = Category.objects.create(name="Empty", description="For testing: no instruments.", display_order=3)
        brand = Brand.objects.create(name="Fender", country="USA")
        distribuitor = Distributor.objects.create(name="Test SRL", email="t@example.com")

        def instrument(nume, pret, categorie, taguri, stoc=5):
            return Instrument.objects.create(
                name=nume, description="x", price=pret, stock=stoc, category=categorie, brand=brand,
                distributor=distribuitor, tags=taguri,
            )

        cls.ieftin = instrument("A cheap one", 100, cls.chitare, ["beginner", "compact"], stoc=1)
        cls.scump = instrument("B dear one", 900, cls.chitare, ["stage"])
        cls.mijlociu = instrument("C middle one", 500, cls.chitare, ["beginner"])
        cls.toba = instrument("D drum", 300, cls.tobe, ["beginner", "compact"])

    def get(self, adresa):
        with redirect_stdout(StringIO()):
            return self.client.get(adresa)

    def nume(self, raspuns):
        return [i.name for i in raspuns.context["pagina"]]


class ProduseTest(CuInstrumente):
    """Lab 4: the listings, product pages, category pages and the menu."""

    def test_sortare_dupa_pret(self):
        self.assertEqual(self.nume(self.get("/produse?by=price&sort=a")), ["A cheap one", "D drum", "C middle one", "B dear one"])
        self.assertEqual(self.nume(self.get("/produse?by=price&sort=d"))[0], "B dear one")

    def test_sortare_gresita_arata_mesaj(self):
        self.assertContains(self.get("/produse?by=colour"), "not by")

    def test_taguri_le_cer_pe_toate(self):
        self.assertEqual(sorted(self.nume(self.get("/produse?tag=beginner&tag=compact"))), ["A cheap one", "D drum"])
        self.assertEqual(self.nume(self.get("/produse?tag=stage")), ["B dear one"])

    def test_paginare_pastreaza_parametrii(self):
        with self.settings(PROD_PER_PAG=2):
            raspuns = self.get("/produse?by=price&sort=a&tag=beginner")
        self.assertContains(raspuns, "Showing instruments 1 to 2 of 3.")
        self.assertContains(raspuns, "Page 1 of 2")
        self.assertContains(raspuns, 'href="?by=price&amp;sort=a&amp;tag=beginner&amp;page=2"')

    def test_pagina_produsului_si_eroarea(self):
        raspuns = self.get(self.scump.get_absolute_url())
        self.assertContains(raspuns, "B dear one")
        self.assertContains(raspuns, "From the same category")
        asemanatoare = list(raspuns.context["asemanatoare"])
        self.assertTrue(asemanatoare)
        self.assertTrue(all(a.category == self.chitare and a != self.scump for a in asemanatoare))
        self.assertEqual(self.get("/produse/999999").status_code, 404)

    def test_stoc_limitat(self):
        self.assertContains(self.get(self.ieftin.get_absolute_url()), "Only 1 left")

    def test_pagina_categoriei(self):
        raspuns = self.get(self.tobe.get_absolute_url())
        self.assertEqual(self.nume(raspuns), ["D drum"])
        self.assertContains(raspuns, "Kits.")
        self.assertEqual(self.get("/categorii/Nothing").status_code, 404)

    def test_meniul_are_doar_categoriile_cu_instrumente_in_ordine(self):
        meniu = list(self.get("/").context["categorii_meniu"])
        self.assertEqual([c.name for c in meniu], ["Drums", "Guitars"])  # "Empty" is left out

    def test_actiunea_export_csv(self):
        from django.contrib.auth.models import User

        User.objects.create_superuser("admin", "a@example.com", "parola")
        self.client.login(username="admin", password="parola")
        raspuns = self.client.post(
            "/admin/instruments/instrument/",
            {"action": "export_csv", "_selected_action": [self.ieftin.pk, self.toba.pk]},
        )
        self.assertEqual(raspuns["Content-Type"], "text/csv; charset=utf-8")
        text = raspuns.content.decode("utf-8-sig")
        self.assertIn("A cheap one", text)
        self.assertNotIn("B dear one", text)


class PanouFiltreTest(CuInstrumente):
    """The filter panel (several tags at once, sorting) and the menu."""

    def test_mai_multe_taguri_deodata(self):
        raspuns = self.get("/produse?tag=beginner&tag=compact")
        self.assertEqual(sorted(self.nume(raspuns)), ["A cheap one", "D drum"])

    def test_pe_pagina_categoriei_tagurile_raman_in_categorie(self):
        raspuns = self.get("/categorii/Guitars?tag=beginner")
        self.assertEqual(sorted(self.nume(raspuns)), ["A cheap one", "C middle one"])  # not the drum
        self.assertContains(raspuns, 'action="/categorii/Guitars"')

    def test_cele_mai_noi_curata_adresa(self):
        # "Newest first" sends an empty by= and a sort= that means nothing; both are dropped
        for pagina in ("/produse", "/categorii/Guitars"):
            raspuns = self.get(pagina + "?tag=beginner&by=&sort=a")
            self.assertRedirects(raspuns, pagina + "?tag=beginner", fetch_redirect_response=False)

    def taguri(self, adresa):
        context = self.get(adresa).context
        return [(tag, numar, bifat) for tag, numar, bifat in context["taguri_principale"] + context["taguri_restul"]]

    def test_numerele_din_panou(self):
        taguri = {tag: (numar, bifat) for tag, numar, bifat in self.taguri("/produse?tag=beginner")}
        self.assertEqual(taguri["beginner"], (3, True))  # all 3 results have it
        self.assertEqual(taguri["compact"], (2, False))  # ticking it too would leave 2
        self.assertEqual(taguri["stage"], (0, False))  # no result has it: still offered, with 0

    def test_lista_de_taguri_nu_se_schimba_cand_bifezi(self):
        inainte = [tag for tag, _, _ in self.taguri("/produse")]
        dupa = [tag for tag, _, _ in self.taguri("/produse?tag=stage")]
        self.assertEqual(inainte, dupa)  # same tags, same order

    def test_pe_pagina_categoriei_doar_tagurile_ei(self):
        taguri = [tag for tag, _, _ in self.taguri("/categorii/Drums")]
        self.assertEqual(sorted(taguri), ["beginner", "compact"])  # not "stage": no drum has it

    def test_meniul(self):
        raspuns = self.get("/")
        self.assertContains(raspuns, ">Instrument categories</a>")
        self.assertContains(raspuns, "All instruments")
        self.assertContains(raspuns, 'href="/services"')  # Setup and repairs, now under About
        self.assertNotContains(raspuns, ">Shop</a>")


# =====================================================================================
# Lab 5
# =====================================================================================


class FiltreFormularTest(CuInstrumente):
    """Task 2: the filter form on /produse and the category pages."""

    def test_interval_de_pret(self):
        raspuns = self.get("/produse?pret_min=200&pret_max=600&by=price&sort=a")
        self.assertEqual(self.nume(raspuns), ["D drum", "C middle one"])

    def test_pret_minim_peste_maxim(self):
        raspuns = self.get("/produse?pret_min=600&pret_max=200")
        self.assertContains(raspuns, "The highest price can&#x27;t be lower than the lowest one.")
        self.assertContains(raspuns, "mesaj-error")  # and the error message at the top of the results
        self.assertEqual(self.nume(raspuns), ["B dear one"])  # the wrong maximum is ignored; the minimum applies

    def test_mesajele_campurilor_sunt_ale_noastre(self):
        raspuns = self.get("/produse?nume=x&pret_min=abc&adaugat_de_la=2999-01-01")
        for text in ("Type at least 2 letters of the name.", "Write the price as a number, like 1500.", "No instrument was added in the future"):
            self.assertContains(raspuns, text)

    def test_filtru_dupa_cheie_straina(self):
        self.assertEqual(self.get("/produse?brand=Fender").context["pagina"].paginator.count, 4)
        self.assertContains(self.get("/produse?brand=Gibson"), "There&#x27;s no such brand in the shop.")

    def test_fara_rezultate(self):
        self.assertContains(self.get("/produse?nume=zzz"), "No instruments match all these filters.")
        self.assertContains(self.get("/produse?nume=zzz"), "mesaj-warning")

    def test_pe_pagina_si_coloane(self):
        raspuns = self.get("/produse?per_pagina=12&coloane=2")
        self.assertEqual(raspuns.context["pagina"].paginator.per_page, 12)
        self.assertContains(raspuns, 'class="grila-produse coloane-2"')
        self.assertContains(self.get("/produse?per_pagina=7"), "A page shows 6, 12, 18 or 24 instruments.")
        # with nothing in the address, the lists show the defaults the page uses
        self.assertContains(self.get("/produse"), '<option value="3" selected>3</option>', html=True)
        self.assertContains(self.get("/produse"), '<option value="6" selected>6</option>', html=True)

    def test_schimbarea_paginarii_avertizeaza(self):
        with self.settings(PROD_PER_PAG=2):
            raspuns = self.client.get("/produse?per_pagina=6&per_pagina_anterior=2&pagina_curenta=2", follow=True)
        self.assertRedirects(raspuns, "/produse?per_pagina=6&page=2", fetch_redirect_response=False)
        self.assertContains(raspuns, "Now showing 6 instruments per page instead of 2.")
        # on page 1 nothing is skipped, so no warning
        raspuns = self.client.get("/produse?per_pagina=12&per_pagina_anterior=6&pagina_curenta=1", follow=True)
        self.assertNotContains(raspuns, "instead of")

    def test_categoria_nu_se_poate_schimba(self):
        raspuns = self.client.get("/categorii/Drums?categorie=Guitars&tag=beginner", follow=True)
        self.assertRedirects(raspuns, "/categorii/Drums?tag=beginner")
        self.assertContains(raspuns, "The category can&#x27;t be changed on this page.")
        self.assertEqual(self.nume(raspuns), ["D drum"])
        # the page's own category, as the hidden field sends it, is fine
        raspuns = self.client.get("/categorii/Drums?categorie=Drums", follow=True)
        self.assertNotContains(raspuns, "can&#x27;t be changed")
        self.assertContains(raspuns, '<input type="hidden" name="categorie" value="Drums" readonly id="id_categorie">', html=True)

    def test_resetare(self):
        raspuns = self.client.get("/produse?tag=stage&resetat=1", follow=True)
        self.assertRedirects(raspuns, "/produse")
        self.assertContains(raspuns, "Filters cleared")
        self.assertContains(raspuns, 'id="confirma-reset"')  # the question asked before

    def test_parametrii_vechi_merg_inca(self):
        raspuns = self.get("/produse?tag=beginner&by=name&sort=d&page=1")
        self.assertEqual(self.nume(raspuns), ["D drum", "C middle one", "A cheap one"])

    def test_doar_partea_care_se_schimba(self):
        with redirect_stdout(StringIO()):
            raspuns = self.client.get("/produse?tag=stage", headers={"X-Partial": "vitrina"})
        text = raspuns.content.decode()
        self.assertTrue(text.lstrip().startswith('<div class="vitrina" id="vitrina">'))
        self.assertNotIn("<html", text)
        self.assertIn("B dear one", text)


class ContactTest(TestCase):
    """Task 3: the contact form, the saved JSON files and /mesaje."""

    def setUp(self):
        import tempfile
        from pathlib import Path
        from unittest import mock

        from . import contact

        dosar = tempfile.TemporaryDirectory()
        self.addCleanup(dosar.cleanup)
        self.dosar = Path(dosar.name)
        # the messages go to a temporary folder, not the real Mesaje_nerezolvate
        patch = mock.patch.object(contact, "DOSAR", self.dosar)
        patch.start()
        self.addCleanup(patch.stop)

    def date(self, **schimbari):
        from .forms import genereaza_cod

        date_ = {
            "nume": "Popescu",
            "prenume": "Ana-Maria",
            "cnp": "2900515123456",
            "data_nasterii": "1990-05-15",
            "email": "Ana@Example.com",
            "confirmare_email": "ana@example.com",
            "telefon": "0721 000 000",
            "tip_mesaj": "intrebare",
            "departament": "workshop",
            "subiect": "Guitar setup",
            "minim_zile_asteptare": "5",
            "mesaj": "hello.   is the   setup included?\nthanks, Popescu",
            "gdpr": "on",
            "cod_cerere": genereaza_cod(),
        }
        date_.update(schimbari)
        return date_

    def trimite(self, **schimbari):
        with redirect_stdout(StringIO()):
            return self.client.post("/contact", self.date(**schimbari))

    def erori(self, **schimbari):
        raspuns = self.trimite(**schimbari)
        self.assertEqual(raspuns.status_code, 200)
        return raspuns.context["form"].errors

    def fisiere(self, slug="workshop"):
        return sorted(p.name for p in (self.dosar / slug).glob("*.json"))

    def test_un_mesaj_bun_se_salveaza(self):
        import json

        raspuns = self.trimite()
        self.assertRedirects(raspuns, "/contact", fetch_redirect_response=False)
        [nume] = self.fisiere()
        self.assertRegex(nume, r"^mesaj_\d+\.json$")  # 5 days is more than a question's 2: not urgent
        continut = json.loads((self.dosar / "workshop" / nume).read_text(encoding="utf-8"))
        self.assertNotIn("confirmare_email", continut)
        self.assertNotIn("data_nasterii", continut)
        self.assertRegex(continut["varsta"], r"^\d+ years and \d+ months?$")
        self.assertEqual(continut["email"], "ana@example.com")
        # a capital after each sentence end, one space for many, a paragraph per line
        self.assertEqual(continut["mesaj"], "<p>hello. Is the setup included?</p><p>Thanks, Popescu</p>")
        for cheie in ("ip", "primit_la", "cod_cerere"):
            self.assertIn(cheie, continut)

    def test_urgent_cand_asteapta_cat_minimul(self):
        self.trimite(minim_zile_asteptare="2")  # a question's minimum
        [nume] = self.fisiere()
        self.assertTrue(nume.endswith("_urgent.json"))

    def test_mesajul_de_succes(self):
        with redirect_stdout(StringIO()):
            raspuns = self.client.post("/contact", self.date(), follow=True)
        self.assertContains(raspuns, "Thank you, Popescu.")
        self.assertContains(raspuns, "mesaj-success")

    def test_validari(self):
        cazuri = [
            ({"confirmare_email": "alta@example.com"}, "confirmare_email", "The two email addresses are different."),
            ({"mesaj": "Hello there, is the setup included? Thanks"}, "mesaj", "Sign your message"),
            ({"mesaj": "Too short. Popescu"}, "mesaj", "between 5 and 100 words"),
            ({"mesaj": "See https://example.com for the photos please Popescu"}, "mesaj", "Links aren't allowed"),
            ({"minim_zile_asteptare": "1"}, "minim_zile_asteptare", "For a question, choose at least 2 days."),
            ({"tip_mesaj": "review"}, "departament", "Workshop doesn't handle reviews."),
            ({"tip_mesaj": "neselectat"}, "tip_mesaj", "Choose what kind of message this is."),
            ({"nume": "popescu"}, "nume", "Start with a capital letter."),
            ({"prenume": "Ana-maria"}, "prenume", "“maria” too"),
            ({"cnp": "2900516123456"}, "cnp", "doesn't match your date of birth"),
            ({"cnp": "29005151234"}, "cnp", "exactly 13 digits"),
            ({"data_nasterii": "2015-01-01", "cnp": ""}, "data_nasterii", "at least 18"),
            ({"email": "x@yopmail.com", "confirmare_email": "x@yopmail.com"}, "email", "Temporary email"),
            ({"subiect": "Visit shop.example.com"}, "subiect", "Words joined by dots"),
            ({"telefon": "12345"}, "telefon", "0721 000 000"),
            ({"gdpr": ""}, "gdpr", "agree that we store"),
            ({"cod_cerere": "inventat:1abc:xyz"}, "cod_cerere", "wasn't made by our site"),
        ]
        for schimbari, camp, text in cazuri:
            with self.subTest(camp=camp, text=text):
                erori = self.erori(**schimbari)
                self.assertIn(camp, erori)
                self.assertIn(text, " ".join(erori[camp]))
        self.assertFalse(self.dosar.exists() and any(self.dosar.rglob("*.json")))  # nothing was saved

    def test_codul_expirat(self):
        from datetime import timedelta
        from unittest import mock

        from . import forms

        with mock.patch.object(forms, "COD_VALABIL", timedelta(seconds=-1)):
            erori = self.erori()
        self.assertIn("opened too long ago", " ".join(erori["cod_cerere"]))

    def test_mesaje_doar_pentru_personal(self):
        from django.contrib.auth.models import User

        self.trimite(minim_zile_asteptare="2")
        self.assertEqual(self.client.get("/mesaje").status_code, 302)  # to the admin's login page
        User.objects.create_user("personal", password="parola", is_staff=True)
        self.client.login(username="personal", password="parola")
        from django.utils import timezone

        azi = timezone.localdate()
        with redirect_stdout(StringIO()):
            raspuns = self.client.get(f"/mesaje/workshop/{azi.year}/{azi.month}")
            self.assertContains(raspuns, "Guitar setup")
            self.assertContains(raspuns, "eticheta-urgent")
            self.assertContains(raspuns, "<p>hello. Is the setup included?</p>", html=False)
            self.assertContains(self.client.get(f"/mesaje/workshop/{azi.year - 1}"), "No messages for Workshop")
            self.assertEqual(self.client.get(f"/mesaje/workshop/{azi.year}/13").status_code, 404)
            self.assertEqual(self.client.get(f"/mesaje/nowhere/{azi.year}").status_code, 404)
            self.assertContains(self.client.get("/mesaje"), "Quality assurance")


class InstrumentFormTest(CuInstrumente):
    """Task 4: adding an instrument with a ModelForm."""

    def setUp(self):
        from django.contrib.auth.models import User

        User.objects.create_user("personal", password="parola", is_staff=True)
        self.client.login(username="personal", password="parola")

    def date(self, **schimbari):
        date_ = {
            "name": "Telecaster Thinline", "description": "A semi-hollow Telecaster.",
            "category": self.chitare.pk, "brand": self.ieftin.brand.pk, "condition": "new",
            "distributor": self.ieftin.distributor.pk, "stock": "4", "tags": "Vintage, beginner, vintage",
            "pret_achizitie": "3500", "adaos": "30",
        }
        date_.update(schimbari)
        return date_

    def trimite(self, **schimbari):
        with redirect_stdout(StringIO()):
            return self.client.post("/produse/adauga", self.date(**schimbari))

    def test_pretul_se_calculeaza(self):
        from .models import Instrument

        raspuns = self.trimite()
        instrument = Instrument.objects.get(name="Telecaster Thinline")
        self.assertRedirects(raspuns, instrument.get_absolute_url(), fetch_redirect_response=False)
        self.assertEqual(instrument.price, 4559)  # 3500 + 30% = 4550, ending in 9
        self.assertEqual(instrument.tags, ["vintage", "beginner"])  # the model's clean() ran too

    def test_validari(self):
        cazuri = [
            ({"name": "TELECASTER"}, "name", "all in capitals"),
            ({"name": "See www.fender.com"}, "name", "Words joined by dots"),
            ({"description": "Details at https://fender.com"}, "description", "Links aren't allowed"),
            ({"pret_achizitie": "5"}, "pret_achizitie", "between 10 and 100,000"),
            ({"adaos": "200"}, "adaos", "between 5% and 150%"),
            ({"stock": "500"}, "stock", "more than 200"),
            ({"condition": "used", "adaos": "80"}, "adaos", "60% at most"),
            ({"tags": "ok, " + "x" * 31}, "tags", "Tag 2: a tag fits in 30 characters."),
        ]
        for schimbari, camp, text in cazuri:
            with self.subTest(camp=camp, text=text):
                raspuns = self.trimite(**schimbari)
                self.assertEqual(raspuns.status_code, 200)
                self.assertIn(text, " ".join(raspuns.context["form"].errors[camp]))

    def test_doar_pentru_personal(self):
        self.client.logout()
        self.assertEqual(self.client.get("/produse/adauga").status_code, 302)
