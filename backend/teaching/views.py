"""
API views and frontend template view for the Interactive Teaching Platform.
"""

from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from teaching.models import Category, Subject, MediaContent
from teaching.serializers import (
    CategorySerializer,
    SubjectListSerializer,
    SubjectDetailSerializer,
    MediaContentSerializer,
)


# ─── Frontend Template View ───────────────────────────────────────────────────


def index_view(request, subject_slug: str | None = None):
    """
    Renders the main Interactive Teaching Platform page.

    Loads the first subject by default (or the one identified by ``subject_slug``).
    Passes the subject, categories, and dashboard media to the template context.
    """
    if subject_slug:
        subject = get_object_or_404(Subject, slug=subject_slug)
    else:
        subject = Subject.objects.select_related(
            "sub_category__category"
        ).prefetch_related("hotspots", "media_contents").first()

    categories = Category.objects.prefetch_related(
        "subcategories__subjects"
    ).order_by("order", "name")

    dashboard_media = []
    if subject:
        dashboard_media = subject.media_contents.filter(is_dashboard=True)

    return render(request, "index.html", {
        "subject": subject,
        "categories": categories,
        "dashboard_media": dashboard_media,
    })


# ─── API Root ─────────────────────────────────────────────────────────────────


@extend_schema(tags=["Root"])
@api_view(["GET"])
def api_root(request, format=None):
    """
    Interactive Teaching Platform — API Root.

    Navigate the full content hierarchy: Category → SubCategory → Subject → Media.
    """
    return Response({
        "categories": reverse("category-list", request=request, format=format),
        "subjects": reverse("subject-list", request=request, format=format),
        "docs_swagger": reverse("swagger-ui", request=request, format=format),
        "docs_redoc": reverse("redoc", request=request, format=format),
    })


# ─── Categories ───────────────────────────────────────────────────────────────


@extend_schema_view(
    list=extend_schema(
        tags=["Categories"],
        summary="List all categories with nested sub-categories and subjects",
    ),
    retrieve=extend_schema(
        tags=["Categories"],
        summary="Retrieve a single category by slug",
    ),
)
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Provides GET /api/categories/ and GET /api/categories/{slug}/.

    Each category includes its sub-categories, and each sub-category
    includes a lightweight list of its subjects.
    """

    queryset = Category.objects.prefetch_related(
        "subcategories__subjects"
    ).order_by("order", "name")
    serializer_class = CategorySerializer
    lookup_field = "slug"


# ─── Subjects ─────────────────────────────────────────────────────────────────


@extend_schema_view(
    list=extend_schema(
        tags=["Subjects"],
        summary="List all subjects (lightweight)",
        parameters=[
            OpenApiParameter("category", str, description="Filter by category slug"),
            OpenApiParameter("sub_category", str, description="Filter by sub-category slug"),
        ],
    ),
    retrieve=extend_schema(
        tags=["Subjects"],
        summary="Full subject detail — article body, hotspots, sidebar, and dashboard media",
    ),
)
class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/subjects/          — list all subjects
    GET /api/subjects/{slug}/   — full detail (body_html + hotspots + sidebar + dashboard_media)
    """

    lookup_field = "slug"

    def get_queryset(self):
        qs = Subject.objects.select_related(
            "sub_category__category"
        ).prefetch_related("hotspots__media_content", "media_contents")

        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(sub_category__category__slug=category)

        sub_category = self.request.query_params.get("sub_category")
        if sub_category:
            qs = qs.filter(sub_category__slug=sub_category)

        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SubjectDetailSerializer
        return SubjectListSerializer


# ─── Media Lookup ──────────────────────────────────────────────────────────────


class MediaContentRetrieveView(generics.RetrieveAPIView):
    """
    GET /api/media/{id}/

    Returns the full typed media payload for the given MediaContent ID.
    The frontend uses this endpoint on hotspot click to determine which
    modal type to render (text, image, audio, local_video, or youtube).
    """

    queryset = MediaContent.objects.all()
    serializer_class = MediaContentSerializer

    @extend_schema(
        tags=["Media"],
        summary="Retrieve media content by ID for modal rendering",
        description=(
            "Returns a typed payload. The `media_type` field tells the frontend "
            "which modal to render:\n"
            "- `text` → render `text_content`\n"
            "- `image` → render `<img>` with `file_url`\n"
            "- `audio` → render `<audio>` with `file_url`\n"
            "- `local_video` → render `<video>` with `file_url`\n"
            "- `youtube` → render `<iframe>` with `youtube_embed_id`\n"
        ),
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
