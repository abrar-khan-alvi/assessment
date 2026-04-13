"""
URL configuration for the Interactive Teaching Platform project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from teaching.views import index_view

urlpatterns = [
    # ── Frontend ──────────────────────────────────────────────────────────────
    path("", index_view, name="index"),
    path("subject/<slug:subject_slug>/", index_view, name="subject-detail"),

    # ── Django Admin ──────────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── REST API ──────────────────────────────────────────────────────────────
    path("api/", include("teaching.urls")),

    # ── API Schema & Docs ─────────────────────────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
