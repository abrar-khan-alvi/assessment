# Interactive Teaching Platform — Implementation Plan

## Overview

Build a full-stack **Interactive Teaching Platform** using **Django** (backend) + **Vanilla HTML/CSS/JS** (frontend), containerized with Docker. The platform transforms structured text into a multi-layered educational experience with clickable "hotspot" terms that open rich multimedia modals.

---

## Architecture Decision

| Layer | Technology | Rationale |
|---|---|---|
| Backend Framework | Django 5 + Django REST Framework | Rapid admin panel, ORM for hierarchy, Swagger via drf-spectacular |
| Database | SQLite (dev) / PostgreSQL (prod, via Docker) | Portable dev, scalable prod |
| Rich Text | django-ckeditor or stored HTML | Renders Word-like formatting |
| Media Storage | Django FileField (local) + YouTube ID field | Covers all 5 media types |
| Frontend | Vanilla HTML/CSS/JS (single-page feel) | No heavy framework needed |
| Containerization | Docker + docker-compose | Easy reviewer setup |
| API Docs | drf-spectacular (Swagger/ReDoc) | Auto-generated |
| Testing | pytest-django | Unit tests for hierarchy + media retrieval |

---

## Content Hierarchy

```
Category (e.g. "Education")
  └── SubCategory (e.g. "Current Affairs")
        └── Subject (e.g. "News Article with Interactive Elements")
              ├── Article Body (rich HTML with hotspot markers)
              └── MediaContent items (Text, Image, Audio, LocalVideo, YouTube)
                    └── Hotspot → links term in body to a MediaContent ID
```

---

## Database Schema

### Category
- `id`, `name`, `slug`, `order`

### SubCategory
- `id`, `name`, `slug`, `category` (FK), `order`

### Subject
- `id`, `title`, `slug`, `sub_category` (FK)
- `body_html` — rich HTML content with `<span data-hotspot-id="X">term</span>` markers
- `introduction`, `detailed_explanation`, `additional_resources` (HTML fields for sidebar)

### MediaContent (Polymorphic via `media_type` field)
- `id`, `subject` (FK), `term` (the display word)
- `media_type`: choices = TEXT | IMAGE | AUDIO | LOCAL_VIDEO | YOUTUBE
- `text_content` (TextField, nullable)
- `media_file` (FileField, nullable — for Image/Audio/Video)
- `youtube_url` (URLField, nullable)
- `caption` (optional)

### Hotspot
- `id`, `subject` (FK), `term` (the phrase in body), `media_content` (FK to MediaContent)

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/categories/` | List all categories |
| GET | `/api/categories/{slug}/subcategories/` | Subcategories under a category |
| GET | `/api/subjects/` | List all subjects |
| GET | `/api/subjects/{slug}/` | Subject detail: body_html + hotspots + sidebar |
| GET | `/api/media/{id}/` | Media lookup — returns typed payload for modal |
| GET | `/api/` | API root |
| GET | `/api/docs/` | Swagger UI |
| GET | `/api/redoc/` | ReDoc |

---

## Frontend UI (Served by Django)

### Layout (Two-Panel + Sidebar)
```
┌─────────────────────────────────────────────────────────┐
│  HEADER: "Interactive Teaching Platform"                 │
├────────────────────────────┬────────────────────────────┤
│  Section A: Media Buttons  │  Section B: Article Text   │
│  [A Text] [Image] [Audio]  │  (Bengali text with 🔍     │
│  [MyVid]  [YouTube]        │   hotspot highlights)      │
│                            │                             │
└────────────────────────────┴────────────────────────────┘
                                    │
                              RIGHT SIDEBAR:
                         "Content" accordion
                         - Introduction
                         - Detailed Explanation
                         - Additional Resources
```

### Modal Types (all centered overlay)
1. **Text** — styled definition/explanation panel
2. **Image** — `<img>` with caption
3. **Audio** — `<audio controls>` with volume slider
4. **Local Video** — `<video controls>` HTML5 player
5. **YouTube** — `<iframe>` embed

### Hotspot Rendering
- Backend injects `<span class="hotspot" data-media-id="X" data-term="word">word <i class="icon-search">🔍</i></span>`
- JS event delegation fetches `/api/media/{id}/` and opens the correct modal

---

## Project File Structure

```
d:\Assesment\
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── core/                    # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── teaching/                # Main app
│   │   ├── models.py            # Category, SubCategory, Subject, MediaContent, Hotspot
│   │   ├── serializers.py       # DRF serializers
│   │   ├── views.py             # API ViewSets
│   │   ├── urls.py
│   │   ├── admin.py             # Rich admin panel
│   │   └── tests.py             # Unit tests
│   └── templates/
│       └── index.html           # Single-page frontend
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md                    # Comprehensive documentation
```

---

## Proposed Changes

### [NEW] `backend/requirements.txt`
Django, DRF, drf-spectacular, pytest-django, Pillow, python-dotenv

### [NEW] `backend/core/settings.py`
Full Django settings with media file handling, CORS, static files, CKEditor

### [NEW] `backend/teaching/models.py`
Category, SubCategory, Subject, MediaContent (polymorphic), Hotspot

### [NEW] `backend/teaching/serializers.py`
Nested serializers: SubjectDetailSerializer, MediaContentSerializer

### [NEW] `backend/teaching/views.py`
ViewSets + custom endpoints for subject detail and media lookup

### [NEW] `backend/teaching/admin.py`
Inline admin for Hotspots and MediaContent under Subject

### [NEW] `backend/teaching/tests.py`
Unit tests: hierarchy traversal, media API response shape, hotspot linking

### [NEW] `backend/teaching/management/commands/seed_data.py`
Seeds demo Bengali article, 5 media types, hotspots

### [NEW] `backend/templates/index.html`
Full frontend: header, two panels, sidebar accordion, 5 modal types, JS fetch logic

### [NEW] `Dockerfile` + `docker-compose.yml`
Multi-stage build, Postgres service, volume mounts, env config

### [MODIFY] `README.md`
Complete rewrite: setup instructions, API docs, feature list, Docker usage

---

## Verification Plan

### Automated Tests
```bash
cd backend
pytest teaching/tests.py -v
```
Tests cover:
- Category → SubCategory → Subject hierarchy retrieval
- `/api/subjects/{slug}/` returns correct hotspots
- `/api/media/{id}/` returns correct typed payload for each of 5 media types
- Admin can create/edit subjects inline

### Manual Browser Verification
1. Run `docker-compose up`
2. Navigate to `http://localhost:8000` — verify two-panel layout
3. Click each of the 5 demo buttons (A Text, Image, Audio, MyVid, YouTube) — verify modals
4. Click Bengali hotspot terms (সন্দেহ, স্বর্ণ, etc.) — verify 🔍 icon and correct modal
5. Open sidebar accordion — verify Introduction/Detailed/Additional Resources expand
6. Visit `http://localhost:8000/api/docs/` — verify Swagger UI
7. Visit `http://localhost:8000/admin/` — verify admin panel with inline editing
