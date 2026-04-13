"""
DRF Serializers for the Interactive Teaching Platform API.
"""

from django.templatetags.static import static
from rest_framework import serializers

from teaching.models import Category, SubCategory, Subject, MediaContent, Hotspot


# ─── Hierarchy Serializers ────────────────────────────────────────────────────


class HotspotSerializer(serializers.ModelSerializer):
    media_id = serializers.IntegerField(source="media_content.id", read_only=True)
    media_type = serializers.CharField(source="media_content.media_type", read_only=True)

    class Meta:
        model = Hotspot
        fields = ["id", "term", "media_id", "media_type"]


class MediaContentSerializer(serializers.ModelSerializer):
    """
    Serializer for MediaContent — returns a typed payload so the frontend
    can render the correct modal without any switch logic on the data-access layer.
    """

    file_url = serializers.SerializerMethodField()
    youtube_embed_id = serializers.SerializerMethodField()
    media_type_display = serializers.CharField(source="get_media_type_display", read_only=True)

    class Meta:
        model = MediaContent
        fields = [
            "id",
            "term",
            "media_type",
            "media_type_display",
            "text_content",
            "file_url",
            "youtube_embed_id",
            "youtube_url",
            "caption",
            "is_dashboard",
        ]

    def get_file_url(self, obj: MediaContent) -> str | None:
        request = self.context.get("request")
        if obj.media_file:
            url = obj.media_file.url
            return request.build_absolute_uri(url) if request else url
        if obj.static_path:
            url = static(obj.static_path)
            return request.build_absolute_uri(url) if request else url
        return None

    def get_youtube_embed_id(self, obj: MediaContent) -> str | None:
        return obj.youtube_embed_id


class SubjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing subjects."""

    category = serializers.CharField(source="sub_category.category.name", read_only=True)
    sub_category = serializers.CharField(source="sub_category.name", read_only=True)

    class Meta:
        model = Subject
        fields = ["id", "title", "slug", "category", "sub_category", "created_at", "updated_at"]


class SubjectDetailSerializer(serializers.ModelSerializer):
    """
    Full subject detail including article HTML, sidebar panels,
    hotspot map, and dashboard media items — all in a single response.
    """

    category = serializers.CharField(source="sub_category.category.name", read_only=True)
    category_slug = serializers.CharField(source="sub_category.category.slug", read_only=True)
    sub_category = serializers.CharField(source="sub_category.name", read_only=True)
    sub_category_slug = serializers.CharField(source="sub_category.slug", read_only=True)
    hotspots = HotspotSerializer(many=True, read_only=True)
    dashboard_media = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "category_slug",
            "sub_category",
            "sub_category_slug",
            "body_html",
            "introduction",
            "detailed_explanation",
            "additional_resources",
            "hotspots",
            "dashboard_media",
            "created_at",
            "updated_at",
        ]

    def get_dashboard_media(self, obj: Subject):
        qs = obj.media_contents.filter(is_dashboard=True)
        return MediaContentSerializer(qs, many=True, context=self.context).data


class SubCategorySerializer(serializers.ModelSerializer):
    subjects = SubjectListSerializer(many=True, read_only=True)

    class Meta:
        model = SubCategory
        fields = ["id", "name", "slug", "subjects"]


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "order", "subcategories"]
