"""Lab 6: signing up, logging in and out, the profile page, and changing the details or password.

Django's auth app does the hard parts: login() remembers the user in the session, logout()
forgets everything in it, and the password forms check and hash passwords. These views put the
site's forms and pages around them.
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import dateformat, timezone
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views.decorators.http import require_POST

from .forms import DateContForm, InregistrareForm, LoginForm, ParolaForm
from .models import Profile

# The key of the user's details in the session
CHEIE_SESIUNE = "cont"


def _data(zi):
    return dateformat.format(zi, "j F Y") if zi else ""


def date_sesiune(utilizator):
    """The user's details as the profile page shows them, ready to be kept in the session.

    The session is stored as JSON (in the django_session table), so only text, numbers, lists
    and dicts: the dates are turned into text here, and the profile is None when there isn't one.
    """
    # Read from the table, not from utilizator.profile: Django keeps the profile it loaded once on
    # the user object, so right after saving the form that copy could be the old one.
    profil = Profile.objects.filter(user=utilizator).select_related("favorite_category").first()  # None: no row
    return {
        "id": utilizator.pk,
        "utilizator": {
            "username": utilizator.username,
            "first_name": utilizator.first_name,
            "last_name": utilizator.last_name,
            "email": utilizator.email,
            "phone": utilizator.phone,
            "street": utilizator.street,
            "city": utilizator.city,
            "county": utilizator.county,
            "country": utilizator.country,
            "date_joined": _data(timezone.localtime(utilizator.date_joined)),
        },
        "profil": profil
        and {
            "date_of_birth": _data(profil.date_of_birth),
            "level": profil.get_level_display(),
            "favorite_category": profil.favorite_category.name if profil.favorite_category else "",
            "bio": profil.bio,
        },
        "salvat_la": timezone.localtime().strftime("%H:%M"),
    }


def _salveaza_in_sesiune(request, utilizator):
    request.session[CHEIE_SESIUNE] = date_sesiune(utilizator)
    return request.session[CHEIE_SESIUNE]


def inregistrare(request):
    if request.user.is_authenticated:
        return redirect("instruments:profil")
    if request.method == "POST":
        form = InregistrareForm(request.POST)
        if form.is_valid():
            utilizator = form.save()  # the user's row, and the profile's only if it was filled in
            messages.success(request, f"Your account is ready, {utilizator.first_name}. Log in to start.")
            # the login form opens with the username already typed in
            return redirect(f"{reverse('instruments:login')}?{urlencode({'username': utilizator.username})}")
        messages.error(request, "The account wasn't created. The notes next to the fields say what to change.")
    else:
        form = InregistrareForm()
    return render(request, "instruments/inregistrare.html", {"form": form})


def autentificare(request):
    if request.user.is_authenticated:
        return redirect("instruments:profil")
    # where to go after logging in: a page that asked for it (?next=/profil), or the profile
    urmatoarea = request.POST.get("next") or request.GET.get("next", "")
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            utilizator = form.get_user()
            prima_data = utilizator.last_login is None  # login() is about to fill it in
            login(request, utilizator)  # puts the user's id in the session, under a new session key
            if form.cleaned_data["pastreaza"]:
                # the session cookie lasts a day, even after the browser is closed
                request.session.set_expiry(settings.SESIUNE_PASTRATA)
            else:
                # 0: a cookie without an end date, which the browser deletes when it closes
                request.session.set_expiry(0)
            _salveaza_in_sesiune(request, utilizator)
            salut = "Welcome" if prima_data else "Welcome back"
            messages.success(request, f"{salut}, {utilizator.first_name or utilizator.username}.")
            # only an address of this site: ?next=https://elsewhere.example would send people away
            if url_has_allowed_host_and_scheme(urmatoarea, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(urmatoarea)
            return redirect("instruments:profil")
        messages.error(request, "You aren't logged in. Check the username and password.")
    else:
        form = LoginForm(request, initial={"username": request.GET.get("username", "")})
    return render(request, "instruments/login.html", {"form": form, "next": urmatoarea})


@require_POST  # only a form's button logs out: a link could be followed by a prefetching browser
def iesire(request):
    logout(request)  # deletes the session: the user's id and the details kept in it
    messages.info(request, "You're logged out.")
    return redirect("instruments:index")


@login_required
def profil(request):
    date_ = request.session.get(CHEIE_SESIUNE)
    if not date_ or date_.get("id") != request.user.pk:
        # logged in some other way (through the admin): the session doesn't have them yet
        date_ = _salveaza_in_sesiune(request, request.user)
    return render(
        request,
        "instruments/profil.html",
        {
            "cont": date_,
            "pana_la_inchidere": request.session.get_expire_at_browser_close(),
            "expira": timezone.localtime(request.session.get_expiry_date()),
        },
    )


@login_required
def date_cont(request):
    if request.method == "POST":
        form = DateContForm(request.POST, instance=request.user)
        if form.is_valid():
            utilizator = form.save()  # and the profile: added, updated, or removed if emptied
            _salveaza_in_sesiune(request, utilizator)  # the page shows the session's copy
            messages.success(request, "Your details are saved.")
            return redirect("instruments:profil")
        messages.error(request, "Nothing was saved. The notes next to the fields say what to change.")
    else:
        form = DateContForm(instance=request.user)
    return render(request, "instruments/date_cont.html", {"form": form})


@login_required
def parola(request):
    if request.method == "POST":
        form = ParolaForm(request.user, request.POST)
        if form.is_valid():
            utilizator = form.save()
            # A new password logs the user out everywhere, this browser included, unless the
            # session is told about it: then only the other browsers are logged out.
            update_session_auth_hash(request, utilizator)
            messages.success(request, "Your password is changed. Any other browser you were logged in on is now logged out.")
            return redirect("instruments:profil")
        messages.error(request, "The password wasn't changed. The notes next to the fields say why.")
    else:
        form = ParolaForm(request.user)
    return render(request, "instruments/parola.html", {"form": form})
