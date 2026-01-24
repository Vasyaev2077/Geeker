from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("profile/", include("apps.profiles.urls")),
    path("library/", include("apps.library.urls")),
    path("blog/", include("apps.blog.urls")),
    path("communities/", include("apps.communities.urls")),
    path("chat/", include("apps.chat.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)






