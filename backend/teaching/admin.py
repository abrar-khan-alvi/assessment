"""
Django admin configuration for the Interactive Teaching Platform.

Provides inline editing for MediaContent and Hotspots directly
within the Subject admin page.
"""

from django.contrib import admin
from django.utils.html import format_html

from teaching.models import Category, SubCategory, Subject, MediaContent, Hotspot

admin.site.site_header = "Interactive Teaching Platform"
admin.site.site_title = "ITP Admin"
admin.site.index_title = "Content Management"


# ─── Inlines ─────────────────────────────────────────────────────────────────


class MediaContentInline(admin.TabularInline):
    model = MediaContent
    extra = 1
    fields = ("term", "media_type", "is_dashboard", "text_content", "media_file", "static_path", "youtube_url", "caption")
    show_change_link = True


class HotspotInline(admin.TabularInline):
    model = Hotspot
    extra = 1
    fields = ("term", "media_content")
    autocomplete_fields = ["media_content"]


# ─── Model Admins ─────────────────────────────────────────────────────────────


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "subcategory_count")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")
    search_fields = ("name",)

    @admin.display(description="Sub-categories")
    def subcategory_count(self, obj):
        return obj.subcategories.count()


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "slug", "order", "subject_count")
    list_filter = ("category",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "category__name")

    @admin.display(description="Subjects")
    def subject_count(self, obj):
        return obj.subjects.count()


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("title", "sub_category", "category_name", "media_count", "updated_at")
    list_filter = ("sub_category__category", "sub_category")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "sub_category__name", "sub_category__category__name")
    readonly_fields = ("created_at", "updated_at", "body_preview")
    fieldsets = (
        ("Content", {
            "fields": ("title", "slug", "sub_category", "body_html", "body_preview"),
        }),
        ("Sidebar Panels", {
            "fields": ("introduction", "detailed_explanation", "additional_resources"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    inlines = [MediaContentInline, HotspotInline]

    @admin.display(description="Category")
    def category_name(self, obj):
        return obj.sub_category.category.name

    @admin.display(description="Media items")
    def media_count(self, obj):
        return obj.media_contents.count()

    @admin.display(description="Body preview")
    def body_preview(self, obj):
        return format_html(
            '<div style="max-height:200px;overflow:auto;border:1px solid #ccc;padding:8px">{}</div>',
            obj.body_html[:500] + "..." if len(obj.body_html) > 500 else obj.body_html,
        )


@admin.register(MediaContent)
class MediaContentAdmin(admin.ModelAdmin):
    list_display = ("term", "media_type", "subject", "is_dashboard", "has_file", "has_text")
    list_filter = ("media_type", "is_dashboard", "subject__sub_category__category")
    search_fields = ("term", "subject__title", "text_content")
    search_help_text = "Search by term, subject title, or text content"
    fieldsets = (
        ("Identity", {
            "fields": ("subject", "term", "media_type", "is_dashboard"),
        }),
        ("Content", {
            "fields": ("text_content", "media_file", "static_path", "youtube_url", "caption"),
        }),
    )

    @admin.display(boolean=True, description="Has file")
    def has_file(self, obj):
        return bool(obj.media_file or obj.static_path)

    @admin.display(boolean=True, description="Has text")
    def has_text(self, obj):
        return bool(obj.text_content)


@admin.register(Hotspot)
class HotspotAdmin(admin.ModelAdmin):
    list_display = ("term", "subject", "media_content", "media_type")
    list_filter = ("subject", "media_content__media_type")
    search_fields = ("term", "subject__title")
    autocomplete_fields = ["media_content"]

    @admin.display(description="Media type")
    def media_type(self, obj):
        return obj.media_content.get_media_type_display()
