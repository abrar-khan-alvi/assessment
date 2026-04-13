"""
Unit tests for the Interactive Teaching Platform.

Covers:
- Content hierarchy (Category → SubCategory → Subject) creation and retrieval
- MediaContent for all 5 media types
- API response shapes (/api/subjects/{slug}/ and /api/media/{id}/)
- Hotspot linking logic
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from teaching.models import Category, SubCategory, Subject, MediaContent, Hotspot


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def category(db):
    return Category.objects.create(name="Education", slug="education")


@pytest.fixture
def sub_category(db, category):
    return SubCategory.objects.create(
        name="Current Affairs", slug="current-affairs", category=category
    )


@pytest.fixture
def subject(db, sub_category):
    return Subject.objects.create(
        sub_category=sub_category,
        title="Test Article",
        slug="test-article",
        body_html="<p>Hello <span class='hotspot' data-media-id='1'>world</span></p>",
        introduction="<p>Intro content</p>",
        detailed_explanation="<p>Detailed content</p>",
        additional_resources="<p>Resources</p>",
    )


@pytest.fixture
def media_text(db, subject):
    return MediaContent.objects.create(
        subject=subject,
        term="world",
        media_type=MediaContent.MEDIA_TYPE_TEXT,
        text_content="This is the definition of world.",
    )


@pytest.fixture
def media_image(db, subject):
    return MediaContent.objects.create(
        subject=subject,
        term="Image Demo",
        media_type=MediaContent.MEDIA_TYPE_IMAGE,
        static_path="demo/rose.jpg",
        is_dashboard=True,
    )


@pytest.fixture
def media_audio(db, subject):
    return MediaContent.objects.create(
        subject=subject,
        term="Audio Demo",
        media_type=MediaContent.MEDIA_TYPE_AUDIO,
        static_path="demo/audio.wav",
        is_dashboard=True,
    )


@pytest.fixture
def media_video(db, subject):
    return MediaContent.objects.create(
        subject=subject,
        term="MyVid",
        media_type=MediaContent.MEDIA_TYPE_LOCAL_VIDEO,
        static_path="demo/video.mp4",
        is_dashboard=True,
    )


@pytest.fixture
def media_youtube(db, subject):
    return MediaContent.objects.create(
        subject=subject,
        term="YouTube",
        media_type=MediaContent.MEDIA_TYPE_YOUTUBE,
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        is_dashboard=True,
    )


@pytest.fixture
def hotspot(db, subject, media_text):
    return Hotspot.objects.create(
        subject=subject,
        term="world",
        media_content=media_text,
    )


# ─── Hierarchy Tests ──────────────────────────────────────────────────────────


class TestContentHierarchy:
    """Tests the Category → SubCategory → Subject hierarchy."""

    def test_category_creation(self, db, category):
        assert category.name == "Education"
        assert category.slug == "education"

    def test_subcategory_belongs_to_category(self, db, sub_category, category):
        assert sub_category.category == category
        assert sub_category in category.subcategories.all()

    def test_subject_belongs_to_subcategory(self, db, subject, sub_category):
        assert subject.sub_category == sub_category
        assert subject in sub_category.subjects.all()

    def test_full_hierarchy_traversal(self, db, subject, category, sub_category):
        """Traverse from category down to subject's content."""
        fetched_cat = Category.objects.prefetch_related("subcategories__subjects").get(
            slug="education"
        )
        fetched_sub = fetched_cat.subcategories.first()
        fetched_subject = fetched_sub.subjects.first()

        assert fetched_cat.name == "Education"
        assert fetched_sub.name == "Current Affairs"
        assert fetched_subject.title == "Test Article"

    def test_auto_slug_on_save(self, db, sub_category):
        """Subjects without a slug auto-generate one from the title."""
        s = Subject(sub_category=sub_category, title="My New Topic")
        s.save()
        assert s.slug == "my-new-topic"


# ─── MediaContent Tests ───────────────────────────────────────────────────────


class TestMediaContent:
    """Tests for all 5 media types."""

    def test_text_media_has_content(self, db, media_text):
        assert media_text.media_type == "text"
        assert "definition" in media_text.text_content

    def test_image_media_has_static_path(self, db, media_image):
        assert media_image.media_type == "image"
        assert media_image.static_path == "demo/rose.jpg"

    def test_audio_media_has_static_path(self, db, media_audio):
        assert media_audio.media_type == "audio"
        assert "audio" in media_audio.static_path

    def test_video_media_has_static_path(self, db, media_video):
        assert media_video.media_type == "local_video"
        assert media_video.static_path.endswith(".mp4")

    def test_youtube_embed_id_extraction(self, db, media_youtube):
        assert media_youtube.media_type == "youtube"
        assert media_youtube.youtube_embed_id == "dQw4w9WgXcQ"

    def test_youtube_embed_id_short_url(self, db, subject):
        mc = MediaContent(
            subject=subject,
            term="Short URL",
            media_type="youtube",
            youtube_url="https://youtu.be/dQw4w9WgXcQ",
        )
        assert mc.youtube_embed_id == "dQw4w9WgXcQ"

    def test_dashboard_flag_filter(self, db, subject, media_image, media_audio, media_text):
        dashboard = subject.media_contents.filter(is_dashboard=True)
        assert media_image in dashboard
        assert media_audio in dashboard
        assert media_text not in dashboard  # is_dashboard=False by default


# ─── Hotspot Tests ────────────────────────────────────────────────────────────


class TestHotspot:
    """Tests for hotspot → media_content linking."""

    def test_hotspot_links_term_to_media(self, db, hotspot, media_text):
        assert hotspot.term == "world"
        assert hotspot.media_content == media_text

    def test_subject_has_hotspot(self, db, subject, hotspot):
        assert hotspot in subject.hotspots.all()

    def test_hotspot_str(self, db, hotspot):
        assert "world" in str(hotspot)


# ─── API Tests ────────────────────────────────────────────────────────────────


class TestCategoryAPI:
    def test_list_categories(self, db, api_client, category, sub_category):
        url = reverse("category-list")
        response = api_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Education"
        assert data[0]["subcategories"][0]["name"] == "Current Affairs"

    def test_retrieve_category_by_slug(self, db, api_client, category):
        url = reverse("category-detail", kwargs={"slug": "education"})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json()["slug"] == "education"


class TestSubjectAPI:
    def test_list_subjects(self, db, api_client, subject):
        url = reverse("subject-list")
        response = api_client.get(url)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_subject_list_filter_by_category(self, db, api_client, subject, category):
        url = reverse("subject-list") + "?category=education"
        response = api_client.get(url)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_subject_detail_has_body_html(self, db, api_client, subject):
        url = reverse("subject-detail", kwargs={"slug": "test-article"})
        response = api_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert "body_html" in data
        assert "hotspot" in data["body_html"]

    def test_subject_detail_has_sidebar_panels(self, db, api_client, subject):
        url = reverse("subject-detail", kwargs={"slug": "test-article"})
        data = api_client.get(url).json()
        assert "introduction" in data
        assert "detailed_explanation" in data
        assert "additional_resources" in data

    def test_subject_detail_has_hotspots(self, db, api_client, subject, hotspot):
        url = reverse("subject-detail", kwargs={"slug": "test-article"})
        data = api_client.get(url).json()
        assert len(data["hotspots"]) == 1
        assert data["hotspots"][0]["term"] == "world"

    def test_subject_detail_has_dashboard_media(self, db, api_client, subject, media_image):
        url = reverse("subject-detail", kwargs={"slug": "test-article"})
        data = api_client.get(url).json()
        dashboard = data["dashboard_media"]
        assert len(dashboard) == 1
        assert dashboard[0]["term"] == "Image Demo"


class TestMediaAPI:
    def test_retrieve_text_media(self, db, api_client, media_text):
        url = reverse("media-content-detail", kwargs={"pk": media_text.pk})
        response = api_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["media_type"] == "text"
        assert data["text_content"] is not None

    def test_retrieve_image_media_has_file_url(self, db, api_client, media_image):
        url = reverse("media-content-detail", kwargs={"pk": media_image.pk})
        data = api_client.get(url).json()
        assert data["media_type"] == "image"
        assert data["file_url"] is not None
        assert "rose" in data["file_url"]

    def test_retrieve_audio_media(self, db, api_client, media_audio):
        url = reverse("media-content-detail", kwargs={"pk": media_audio.pk})
        data = api_client.get(url).json()
        assert data["media_type"] == "audio"
        assert data["file_url"] is not None

    def test_retrieve_video_media(self, db, api_client, media_video):
        url = reverse("media-content-detail", kwargs={"pk": media_video.pk})
        data = api_client.get(url).json()
        assert data["media_type"] == "local_video"
        assert data["file_url"] is not None

    def test_retrieve_youtube_media(self, db, api_client, media_youtube):
        url = reverse("media-content-detail", kwargs={"pk": media_youtube.pk})
        data = api_client.get(url).json()
        assert data["media_type"] == "youtube"
        assert data["youtube_embed_id"] == "dQw4w9WgXcQ"

    def test_media_not_found_returns_404(self, db, api_client):
        url = reverse("media-content-detail", kwargs={"pk": 99999})
        assert api_client.get(url).status_code == 404
