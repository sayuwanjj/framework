"""Корневая маршрутизация URL проекта layout_service.

Корневой urls.py распределяет адреса между приложениями: функция
include() передаёт оставшуюся часть адреса в urls.py приложения.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("layouts/", include("layouts.urls")),
    path("comments/", include("comments.urls")),
]

handler404 = "homepage.views.page_not_found"


if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += debug_toolbar_urls()
