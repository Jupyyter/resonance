"""Middleware: code that runs for every request, before the view (and could also run after it).

Django calls the middlewares listed in settings.MIDDLEWARE in order, each wrapping the next,
like layers of an onion around the view.
"""
from .accesari import Accesare


def get_ip(request):
    """The visitor's IP address (the function from the lab).

    Behind a proxy or load balancer (like on a real server), REMOTE_ADDR is the proxy's address
    and the visitor's real address is in the X-Forwarded-For header. Each proxy appends to it,
    so the last entry is the one added by the proxy closest to us. (Anyone can send this
    header themselves, so on a real server you only trust it when your own proxy sets it.)
    """
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR")


class IpMiddleware:
    """Stores the visitor's IP on the request, so every view can read request.ip_client."""

    def __init__(self, get_response):
        self.get_response = get_response  # the next layer (another middleware, or the view)

    def __call__(self, request):
        request.ip_client = get_ip(request)
        return self.get_response(request)


class AccesariMiddleware:
    """Records a visit (an Accesare) for every request to one of the shop's pages.

    process_view runs after Django has found which view will answer, right before calling it,
    so request.resolver_match tells us whose page this is. Only the shop's pages (namespace
    "instruments") are logged: not the admin, and not addresses that match no page at all.
    The visit is left on the request, so a view can use it (request.accesare).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.resolver_match.namespace == "instruments":
            request.accesare = Accesare.din_cerere(request)
        return None  # None means "carry on": Django goes on to call the view
