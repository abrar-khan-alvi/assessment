"""
Management command: seed_data

Populates the database with a full demo dataset:
  - Category: Education
  - SubCategory: Current Affairs
  - Subject: News Article with Interactive Elements (Bengali gold-theft story)
  - 9 MediaContent objects (4 article hotspots + 5 dashboard buttons)
  - Demo static assets: audio WAV (generated), rose image (copied from artifacts)

Usage:
    python manage.py seed_data
    python manage.py seed_data --reset   # clears existing demo data first
"""

import io
import math
import os
import shutil
import struct
import wave
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from teaching.models import Category, SubCategory, Subject, MediaContent, Hotspot


class Command(BaseCommand):
    help = "Seed the database with the demo Bengali news article and multimedia content."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing teaching content before seeding.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write(self.style.WARNING("Resetting existing data..."))
            Subject.objects.all().delete()
            SubCategory.objects.all().delete()
            Category.objects.all().delete()

        self.stdout.write(self.style.MIGRATE_HEADING("=== Interactive Teaching Platform - Seeding ==="))

        # ── 1. Ensure demo asset directory exists ────────────────────────────
        demo_dir = Path(settings.BASE_DIR) / "static" / "demo"
        demo_dir.mkdir(parents=True, exist_ok=True)
        self._create_audio(demo_dir)
        self._copy_rose_image(demo_dir)
        self._create_or_download_video(demo_dir)

        # ── 2. Content hierarchy ─────────────────────────────────────────────
        category, _ = Category.objects.get_or_create(
            slug="education",
            defaults={"name": "Education", "order": 1},
        )
        self.stdout.write(f"  [OK] Category: {category.name}")

        sub_category, _ = SubCategory.objects.get_or_create(
            slug="current-affairs",
            defaults={
                "name": "Current Affairs",
                "category": category,
                "order": 1,
            },
        )
        self.stdout.write(f"  [OK] SubCategory: {sub_category.name}")

        subject, created = Subject.objects.get_or_create(
            slug="gold-theft-news-article",
            defaults={
                "sub_category": sub_category,
                "title": "News Article with Interactive Elements",
                "body_html": "",  # Will be set after MediaContent IDs are known
                "introduction": (
                    "<p><strong>Overview:</strong> This article covers the investigation by the Dhaka Metropolitan "
                    "Detective Branch (DB) into the theft of 500 gold ornaments from Fortune Shopping Mall's "
                    "Shasha Jewellers store.</p>"
                    "<p>The case demonstrates advanced detective work, with DB teams conducting a 72-hour "
                    "nationwide operation resulting in multiple arrests and partial recovery of stolen goods.</p>"
                ),
                "detailed_explanation": (
                    "<p><strong>Investigation Details:</strong></p>"
                    "<ul>"
                    "<li>DB deployed three specialized teams simultaneously across Bangladesh</li>"
                    "<li><strong>Chittagong:</strong> First arrest — Shahin Matbar</li>"
                    "<li><strong>Faridpur:</strong> Gold recovered from hiding location</li>"
                    "<li><strong>Barisal:</strong> Two additional suspects arrested</li>"
                    "<li><strong>Dhaka:</strong> Ring coordinator Nurul Islam arrested</li>"
                    "</ul>"
                    "<p>Total gold recovered: 190 tola (out of 500 missing). Investigation is ongoing "
                    "with one suspect still at large.</p>"
                ),
                "additional_resources": (
                    "<ul>"
                    "<li><a href='#'>DB Press Conference Report (Bangla)</a></li>"
                    "<li><a href='#'>Fortune Shopping Mall CCTV Analysis</a></li>"
                    "<li><a href='#'>Jewelry Theft Statistics — Bangladesh Police 2025</a></li>"
                    "<li><a href='#'>How Detective Branches Operate in Urban Bangladesh</a></li>"
                    "</ul>"
                ),
            },
        )
        if not created:
            self.stdout.write(self.style.WARNING(f"  -> Subject already exists, updating..."))

        self.stdout.write(f"  [OK] Subject: {subject.title}")

        # ── 3. MediaContent — Article hotspots ───────────────────────────────
        mc_sandeh, _ = MediaContent.objects.get_or_create(
            subject=subject,
            term="সন্দেহ",
            media_type=MediaContent.MEDIA_TYPE_TEXT,
            defaults={
                "text_content": (
                    "This is a sample text content that appears in the modal when clicked. "
                    "You can add explanations, definitions, or additional information here."
                ),
                "is_dashboard": False,
            },
        )

        mc_shomonnoy, _ = MediaContent.objects.get_or_create(
            subject=subject,
            term="সমন্বয়কারী",
            media_type=MediaContent.MEDIA_TYPE_TEXT,
            defaults={
                "text_content": "কেন এমন টা বলা হল ?",
                "is_dashboard": False,
            },
        )

        mc_shorno_img, _ = MediaContent.objects.get_or_create(
            subject=subject,
            term="স্বর্ণ",
            media_type=MediaContent.MEDIA_TYPE_IMAGE,
            defaults={
                "static_path": "demo/rose.jpg",
                "caption": "সোনার অলংকার — Gold Ornaments",
                "is_dashboard": False,
            },
        )

        mc_audio_inline, _ = MediaContent.objects.get_or_create(
            subject=subject,
            term="Audio",
            media_type=MediaContent.MEDIA_TYPE_AUDIO,
            defaults={
                "static_path": "demo/audio.wav",
                "caption": "Audio evidence recording",
                "is_dashboard": False,
            },
        )

        # ── 4. MediaContent — Dashboard buttons ─────────────────────────────
        mc_dash_text, _ = MediaContent.objects.get_or_create(
            subject=subject,
            term="A Text",
            media_type=MediaContent.MEDIA_TYPE_TEXT,
            defaults={
                "text_content": (
                    "This is a sample text content that appears in the modal when clicked. "
                    "You can add explanations, definitions, or additional information here."
                ),
                "is_dashboard": True,
            },
        )

        mc_dash_image, _ = MediaContent.objects.get_or_create(
            subject=subject,
            term="Image",
            media_type=MediaContent.MEDIA_TYPE_IMAGE,
            defaults={
                "static_path": "demo/rose.jpg",
                "caption": "Beautiful red roses",
                "is_dashboard": True,
            },
        )

        mc_dash_audio, _ = MediaContent.objects.get_or_create(
            subject=subject,
            term="Audio",
            media_type=MediaContent.MEDIA_TYPE_AUDIO,
            defaults={
                "static_path": "demo/audio.wav",
                "caption": "Sample audio clip",
                "is_dashboard": True,
            },
        )

        mc_dash_video, _ = MediaContent.objects.get_or_create(
            subject=subject,
            term="MyVid",
            media_type=MediaContent.MEDIA_TYPE_LOCAL_VIDEO,
            defaults={
                "static_path": "demo/video.mp4",
                "caption": "Sample local video",
                "is_dashboard": True,
            },
        )

        mc_dash_youtube, _ = MediaContent.objects.get_or_create(
            subject=subject,
            term="YouTube",
            media_type=MediaContent.MEDIA_TYPE_YOUTUBE,
            defaults={
                "youtube_url": "https://www.youtube.com/watch?v=fS5z7-0mY_Y",
                "caption": "Django in 100 Seconds",
                "is_dashboard": True,
            },
        )

        self.stdout.write(f"  [OK] Created {MediaContent.objects.filter(subject=subject).count()} MediaContent objects")

        # ── 5. Create Hotspot records ────────────────────────────────────────
        Hotspot.objects.get_or_create(
            subject=subject, term="সন্দেহ",
            defaults={"media_content": mc_sandeh},
        )
        Hotspot.objects.get_or_create(
            subject=subject, term="সমন্বয়কারী",
            defaults={"media_content": mc_shomonnoy},
        )
        Hotspot.objects.get_or_create(
            subject=subject, term="স্বর্ণ",
            defaults={"media_content": mc_shorno_img},
        )
        Hotspot.objects.get_or_create(
            subject=subject, term="Audio",
            defaults={"media_content": mc_audio_inline},
        )
        self.stdout.write(f"  [OK] Created hotspot links")

        # ── 6. Build and save body_html with real MediaContent IDs ───────────
        body_html = self._build_body_html(
            mc_sandeh.pk,
            mc_audio_inline.pk,
            mc_shomonnoy.pk,
            mc_shorno_img.pk,
        )
        subject.body_html = body_html
        subject.save()
        self.stdout.write(f"  [OK] Body HTML injected with {len(Hotspot.objects.filter(subject=subject))} hotspot spans")

        # ── 7. Create superuser for admin if not exists ──────────────────────
        self._ensure_superuser()

        self.stdout.write(self.style.SUCCESS("\n[DONE] Seeding complete!"))
        self.stdout.write(self.style.SUCCESS("   -> Visit http://localhost:8000/ to view the platform"))
        self.stdout.write(self.style.SUCCESS("   -> Visit http://localhost:8000/admin/ (admin / admin123)"))
        self.stdout.write(self.style.SUCCESS("   -> Visit http://localhost:8000/api/docs/ for Swagger UI"))

    # ── Private helpers ──────────────────────────────────────────────────────

    def _build_body_html(self, id_sandeh, id_audio, id_shomonnoy, id_shorno) -> str:
        """
        Constructs the Bengali article body HTML with proper hotspot <span> markers.
        IDs are injected at runtime after MediaContent PKs are known.
        """
        return f"""
<p>রাজধানীর ফরচুন শপিং মেলার শশা জুয়েলার্স থেকে ৫০০ স্বর্ণালংকার চুরির চাঞ্চল্যকর ঘটনায় রহস্য উদঘাটন করেছে ঢাকা
মহানগর গোয়েন্দা পুলিশ (ডিবি)। দুর্ধষ এই চুরির ঘটনায় জড়িত
<span class="hotspot" data-media-id="{id_sandeh}">সন্দেহে<span class="hotspot-icon">🔍</span></span>
চার জনকে গ্রেফতার করা হয়েছে এবং তাদের কাছ থেকে বিপুল পরিমাণ চোরাই স্বর্ণালংকার উদ্ধার করা হয়েছে বলে জানিয়েছে ডিবি।</p>

<!-- Requirement: Inline Media Demonstration -->
<div style="margin: 20px 0; text-align: center;">
    <img src="/static/demo/rose.jpg" alt="Inline Demo" style="max-width: 100%; border-radius: 8px; border: 1px solid #e2e8f0;">
    <p style="font-size: 0.85rem; color: #64748b; margin-top: 5px;"><em>চিত্র: তদন্ত চলাকালীন উদ্ধারকৃত আলামত (Inline Media Example)</em></p>
</div>

<p>ডিবির তিনটি টিম টানা ৭২ ঘন্টা দেশের বিভিন্ন স্থানে অভিযান চালায়। প্রথমে চট্টগ্রাম থেকে শাহিন মাতব্বরকে গ্রেফতার ও
ফরিদপুর <span class="hotspot audio-hotspot" data-media-id="{id_audio}">🔊 Audio<span class="hotspot-icon">🔍</span></span>
থেকে স্বর্ণ উদ্ধার করা হয়। পরে বরিশাল থেকে আরও দুই জনকে গ্রেফতার করা হয়েছে। ঢাকা থেকে ডিবি গ্রেফতার করে এই চক্রের
<span class="hotspot" data-media-id="{id_shomonnoy}">সমন্বয়কারী<span class="hotspot-icon">🔍</span></span>
নুরুল ইসলামকে, যে মোটরসাইকেল ব্যবহার করে মার্কেটের রেকি করতো।</p>

<!-- Requirement: Standard Styling (Bold, Italic, Underline) -->
<p style="background: #f1f5f9; padding: 10px; border-radius: 4px; font-size: 0.95rem;">
    <strong>বিশেষ দ্রষ্টব্য:</strong> তদন্তের স্বার্থে <em>সকল তথ্য</em> গোপন রাখা হয়েছে এবং <u>শীঘ্রই</u> বিস্তারিত প্রতিবেদন প্রকাশ করা হবে।
</p>

<p>উদ্ধার ১৯০ ভরি, বাকি স্বর্ণের কোথায় আছে প্রশ্নে তিনি বলেন, চুরি যাওয়া স্বর্ণের মালিক দাবি করেছেন, তার দোকানে মোট
৫০০ ভরি স্বর্ণ ছিল। তবে উদ্ধার হয়েছে ১৯০ ভরি। বাকি
<span class="hotspot image-hotspot" data-media-id="{id_shorno}">🖼️ স্বর্ণ<span class="hotspot-icon">🔍</span></span>
কোথায় আছে, তা জানতে ডিবি তদন্ত অব্যাহত রেখেছে। একজন আসামি এখনও পলাতক। তাকে গ্রেফতার করতে পারলে বাকি স্বর্ণের অবস্থান জানা যাবে।</p>
""".strip()

    def _create_audio(self, demo_dir: Path):
        """Generate a 1-second 440 Hz sine wave WAV file using Python's built-in wave module."""
        audio_path = demo_dir / "audio.wav"
        if audio_path.exists():
            self.stdout.write(f"  -> audio.wav already exists, skipping")
            return
        sample_rate = 44100
        frequency = 440  # Hz (concert A)
        duration = 1  # seconds
        num_samples = int(sample_rate * duration)
        samples = [
            int(32767 * math.sin(2 * math.pi * frequency * t / sample_rate))
            for t in range(num_samples)
        ]
        with wave.open(str(audio_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            packed = struct.pack(f"<{num_samples}h", *samples)
            wf.writeframes(packed)
        self.stdout.write(f"  [OK] Generated demo audio: {audio_path.name}")

    def _copy_rose_image(self, demo_dir: Path):
        """Copy the bundled rose image to the demo static directory."""
        rose_path = demo_dir / "rose.jpg"
        if rose_path.exists():
            self.stdout.write(f"  -> rose.jpg already exists, skipping")
            return

        # Try to find it in the project's bundled assets
        candidates = [
            Path(settings.BASE_DIR) / "static" / "assets" / "rose.jpg",
            Path(settings.BASE_DIR).parent / "assets" / "rose.jpg",
        ]
        for src in candidates:
            if src.exists():
                shutil.copy2(src, rose_path)
                self.stdout.write(f"  [OK] Copied rose.jpg from {src}")
                return

        # Try to download as a fallback
        try:
            import requests
            resp = requests.get(
                "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/"
                "Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg"
                "/402px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg",
                timeout=10,
            )
            # Use a simple stock rose image from a public API
            resp2 = requests.get(
                "https://images.unsplash.com/photo-1612817288484-6f916006741a?w=400",
                timeout=10,
            )
            if resp2.status_code == 200:
                rose_path.write_bytes(resp2.content)
                self.stdout.write(f"  [OK] Downloaded rose image")
                return
        except Exception:
            pass

        self.stdout.write(
            self.style.WARNING(
                f"  [!] Could not find rose.jpg. "
                f"Please place a rose image at: {rose_path}"
            )
        )

    def _create_or_download_video(self, demo_dir: Path):
        """Download a small sample video or warn the user."""
        video_path = demo_dir / "video.mp4"
        if video_path.exists():
            self.stdout.write(f"  -> video.mp4 already exists, skipping")
            return

        sample_urls = [
            "https://www.w3schools.com/html/mov_bbb.mp4",
            "https://sample-videos.com/video321/mp4/240/big_buck_bunny_240p_1mb.mp4",
        ]
        try:
            import requests
            for url in sample_urls:
                try:
                    resp = requests.get(url, timeout=15, stream=True)
                    if resp.status_code == 200:
                        with open(video_path, "wb") as f:
                            for chunk in resp.iter_content(chunk_size=8192):
                                f.write(chunk)
                        self.stdout.write(f"  [OK] Downloaded sample video from {url}")
                        return
                except Exception:
                    continue
        except ImportError:
            pass

        self.stdout.write(
            self.style.WARNING(
                f"  [!] Could not download sample video. "
                f"Please place an MP4 at: {video_path}\n"
                f"    Any short MP4 file will work (e.g. from https://www.w3schools.com/html/mov_bbb.mp4)"
            )
        )

    def _ensure_superuser(self):
        """Create a default superuser for the admin panel if none exists."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username="admin",
                email="admin@example.com",
                password="admin123",
            )
            self.stdout.write(f"  [OK] Superuser created: admin / admin123")
        else:
            self.stdout.write(f"  -> Superuser already exists")
