"""
URL routing for the teaching app API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from teaching.views import api_root, CategoryViewSet, SubjectViewSet, MediaContentRetrieveView

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"subjects", SubjectViewSet, basename="subject")

urlpatterns = [
    path("", api_root, name="api-root"),
    path("", include(router.urls)),
    path("media/<int:pk>/", MediaContentRetrieveView.as_view(), name="media-content-detail"),
]
