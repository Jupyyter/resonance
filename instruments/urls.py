from django.urls import path, re_path

from . import views, views_conturi

# The app's own addresses. app_name lets templates and code write "instruments:info"
# instead of "/info", so an address can change without breaking the links to it.
app_name = "instruments"

urlpatterns = [
    path("", views.index, name="index"),
    path("info", views.info, name="info"),
    path("log", views.log, name="log"),
    path("despre", views.despre, name="despre"),
    path("istoric", views.istoric, name="istoric"),
    path("services", views.services, name="services"),
    path("faq", views.faq, name="faq"),
    path("produse", views.produse, name="produse"),
    # <int:id> only matches digits, and hands them to the view already as an int
    path("produse/<int:id>", views.produs, name="produs"),
    path("produse/adauga", views.adauga_instrument, name="adauga_instrument"),
    # <str:nume> matches anything up to the next "/", spaces included (they arrive as %20)
    path("categorii/<str:nume>", views.categorie, name="categorie"),
    path("contact", views.contact, name="contact"),
    # the saved contact messages: a department, then a year, a month or a day
    # Lab 6: accounts
    path("inregistrare", views_conturi.inregistrare, name="inregistrare"),
    path("login", views_conturi.autentificare, name="login"),
    path("logout", views_conturi.iesire, name="logout"),
    path("profil", views_conturi.profil, name="profil"),
    path("profil/date", views_conturi.date_cont, name="date_cont"),
    path("profil/parola", views_conturi.parola, name="parola"),
    path("mesaje", views.mesaje_index, name="mesaje"),
    path("mesaje/<slug:departament>/<int:an>", views.mesaje, name="mesaje_departament"),
    path("mesaje/<slug:departament>/<int:an>/<int:luna>", views.mesaje, name="mesaje_departament"),
    path("mesaje/<slug:departament>/<int:an>/<int:luna>/<int:zi>", views.mesaje, name="mesaje_departament"),
    # Not built yet: shows in_lucru.html for now.
    path("cos_virtual", views.cos_virtual, name="cos_virtual"),
    # A regular expression instead of path()'s simpler syntax: "accesare" followed directly by
    # digits, like /accesare12. The named group (?P<id>...) becomes the view's `id` argument.
    re_path(r"^accesare(?P<id>[0-9]+)$", views.accesare, name="accesare"),
]
