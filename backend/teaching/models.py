"""
Data models for the Interactive Teaching Platform.

Hierarchy:
    Category → SubCategory → Subject
                                 ├── body_html  (with hotspot <span> markers)
                                 ├── MediaContent (polymorphic: text/image/audio/video/youtube)
                                 └── Hotspot    (links a term in body to a MediaContent)
"""

from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """Top-level content category (e.g. 'Education', 'Business')."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=220)
    order = models.PositiveSmallIntegerField(default=0, help_text="Display order (ascending)")

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class SubCategory(models.Model):
    """Second-level content category nested under a Category."""

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="subcategories",
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=220)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Sub-Category"
        verbose_name_plural = "Sub-Categories"

    def __str__(self) -> str:
        return f"{self.category.name} › {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Subject(models.Model):
    """
    A specific content page (e.g. a news article or business case).

    The ``body_html`` field stores rich HTML with hotspot markers:
        <span class="hotspot" data-media-id="<PK>">term<span class="hotspot-icon">🔍</span></span>
    """

    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        related_name="subjects",
    )
    title = models.CharField(max_length=500)
    slug = models.SlugField(unique=True, max_length=520)

    # Main article body — rich HTML with embedded hotspot spans
    body_html = models.TextField(
        blank=True,
        help_text='Rich HTML content. Hotspot terms should be wrapped in '
                  '<span class="hotspot" data-media-id="X">.</span>',
    )

    # Sidebar accordion content (stored as HTML)
    introduction = models.TextField(blank=True, help_text="HTML for the Introduction accordion panel")
    detailed_explanation = models.TextField(blank=True, help_text="HTML for the Detailed Explanation accordion panel")
    additional_resources = models.TextField(blank=True, help_text="HTML for the Additional Resources accordion panel")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sub_category__category__order", "sub_category__order", "title"]
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class MediaContent(models.Model):
    """
    Polymorphic multimedia content unit.

    Each instance represents ONE piece of media that can be shown in a modal
    when its associated hotspot term is clicked in the article.

    Supported types
    ---------------
    text        → text_content
    image       → media_file  OR  static_path
    audio       → media_file  OR  static_path
    local_video → media_file  OR  static_path
    youtube     → youtube_url (stores the full URL; frontend extracts embed ID)
    """

    MEDIA_TYPE_TEXT = "text"
    MEDIA_TYPE_IMAGE = "image"
    MEDIA_TYPE_AUDIO = "audio"
    MEDIA_TYPE_LOCAL_VIDEO = "local_video"
    MEDIA_TYPE_YOUTUBE = "youtube"

    MEDIA_TYPES = [
        (MEDIA_TYPE_TEXT, "Text"),
        (MEDIA_TYPE_IMAGE, "Image"),
        (MEDIA_TYPE_AUDIO, "Audio"),
        (MEDIA_TYPE_LOCAL_VIDEO, "Local Video"),
        (MEDIA_TYPE_YOUTUBE, "YouTube"),
    ]

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="media_contents",
    )
    term = models.CharField(
        max_length=200,
        help_text="Display label shown on the hotspot button (e.g. 'স্বর্ণ', 'Audio')",
    )
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)

    # Content fields — only the relevant one is populated per media_type
    text_content = models.TextField(blank=True, null=True, help_text="Formatted text or definition (TEXT type)")
    media_file = models.FileField(
        upload_to="media_content/%Y/%m/",
        blank=True,
        null=True,
        help_text="Uploaded file for image, audio, or local video",
    )
    static_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path relative to STATIC_URL for bundled demo assets (e.g. 'demo/rose.jpg')",
    )
    youtube_url = models.URLField(
        blank=True,
        null=True,
        help_text="Full YouTube URL (e.g. https://www.youtube.com/watch?v=xxxxx)",
    )
    caption = models.CharField(max_length=500, blank=True, help_text="Optional caption for image/video")

    # Dashboard flag — marks items shown in the 'Multimedia Content Examples' panel
    is_dashboard = models.BooleanField(
        default=False,
        help_text="If True, this item appears as a demo button in the Multimedia Content Examples panel",
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Media Content"
        verbose_name_plural = "Media Contents"

    def __str__(self) -> str:
        return f"[{self.get_media_type_display()}] {self.term}"

    @property
    def youtube_embed_id(self) -> str | None:
        """Extract the video ID from a YouTube URL."""
        if not self.youtube_url:
            return None
        url = self.youtube_url
        if "youtu.be/" in url:
            return url.split("youtu.be/")[-1].split("?")[0]
        if "v=" in url:
            return url.split("v=")[-1].split("&")[0]
        return None


class Hotspot(models.Model):
    """
    Maps a visible term in a Subject's body_html to a MediaContent object.

    The seed command uses Hotspot records to build the body_html string,
    injecting <span class="hotspot" data-media-id="<pk>"> around each term.
    """

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="hotspots",
    )
    term = models.CharField(max_length=200, help_text="Exact term string as it appears in the article")
    media_content = models.ForeignKey(
        MediaContent,
        on_delete=models.CASCADE,
        related_name="hotspot_links",
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Hotspot"
        verbose_name_plural = "Hotspots"

    def __str__(self) -> str:
        return f'Hotspot "{self.term}" → {self.media_content}'
