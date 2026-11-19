from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # The shop lives at the site's root, so its pages are /, /info, ...
    path("", include("instruments.urls")),
]

# While developing (DEBUG=true), Django itself serves the uploaded files from /media/.
# static() returns nothing when DEBUG is off: on a real server, the web server does it.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
