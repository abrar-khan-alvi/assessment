# Interactive Teaching Platform

A full-stack educational platform that transforms static text into an interactive, multi-layered multimedia experience. Users can click on **highlighted terms** in a Bengali news article to trigger rich modal overlays containing text definitions, images, audio, local video, or YouTube embeds.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Hierarchical Content** | Category → SubCategory → Subject tree |
| **5 Modal Media Types** | Text, Image, Audio, Local Video, YouTube |
| **Hotspot System** | Clickable terms in articles linked to MediaContent |
| **Rich Admin Panel** | Django Admin with inline editing for all models |
| **REST API** | Full DRF API with Swagger/ReDoc documentation |
| **Accordion Sidebar** | Dynamic Introduction / Detailed Explanation / Resources |
| **Docker** | One-command `docker-compose up` setup |
| **Unit Tests** | pytest suite covering hierarchy + all 5 media types |

---

## 🚀 Quick Start (Docker — Recommended)

```bash
# Clone and start
git clone <repo-url>
cd Assesment

docker-compose up --build
```

Then open:

| URL | Description |
|---|---|
| http://localhost:8000/ | The interactive platform |
| http://localhost:8000/admin/ | Django Admin (`admin` / `admin123`) |
| http://localhost:8000/api/ | DRF API Browser |
| http://localhost:8000/api/docs/ | Swagger UI |
| http://localhost:8000/api/redoc/ | ReDoc |

> The container automatically runs migrations, seeds demo data, and starts the development server.

---

## 🛠 Local Development Setup

### Prerequisites
- Python 3.12+
- pip

### Steps

```bash
# 1. Create virtual environment
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and configure environment
cd ..
copy .env.example .env
# (Edit .env if needed — defaults work fine for local dev)

# 4. Run migrations
cd backend
python manage.py migrate

# 5. Seed demo data (creates Bengali article, media, hotspots, admin user)
python manage.py seed_data

# 6. Start development server
python manage.py runserver
```

Visit **http://localhost:8000/**

---

## 🗄 Database Schema

```
Category
  └── SubCategory
        └── Subject
              ├── body_html          ← Rich HTML with <span class="hotspot"> markers
              ├── introduction       ← HTML for sidebar accordion
              ├── detailed_explanation
              ├── additional_resources
              ├── MediaContent[]     ← Polymorphic media items
              └── Hotspot[]          ← term → MediaContent mappings
```

### MediaContent Types

| `media_type` | Active Fields | Modal Rendered |
|---|---|---|
| `text` | `text_content` | Text panel |
| `image` | `media_file` or `static_path` | `<img>` |
| `audio` | `media_file` or `static_path` | `<audio controls>` |
| `local_video` | `media_file` or `static_path` | `<video controls>` |
| `youtube` | `youtube_url` | `<iframe>` embed |

---

## 🔌 REST API Reference

### Base URL: `/api/`

#### Categories

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/categories/` | List all categories with nested sub-categories |
| `GET` | `/api/categories/{slug}/` | Single category detail |

**Example response:**
```json
[
  {
    "id": 1,
    "name": "Education",
    "slug": "education",
    "subcategories": [
      {
        "id": 1,
        "name": "Current Affairs",
        "slug": "current-affairs",
        "subjects": [...]
      }
    ]
  }
]
```

#### Subjects

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/subjects/` | List all subjects |
| `GET` | `/api/subjects/?category={slug}` | Filter by category |
| `GET` | `/api/subjects/{slug}/` | Full subject detail |

**Full subject response includes:**
- `body_html` — article with hotspot `<span>` markers
- `hotspots` — array of `{ term, media_id, media_type }`
- `dashboard_media` — the 5 dashboard button media items
- `introduction`, `detailed_explanation`, `additional_resources`

#### Media Lookup

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/media/{id}/` | Media content detail for modal rendering |

**Example (text):**
```json
{
  "id": 1,
  "term": "সন্দেহ",
  "media_type": "text",
  "media_type_display": "Text",
  "text_content": "This is a sample text content...",
  "file_url": null,
  "youtube_embed_id": null
}
```

**Example (YouTube):**
```json
{
  "id": 9,
  "term": "YouTube",
  "media_type": "youtube",
  "youtube_embed_id": "9bZkp7q19f0",
  "youtube_url": "https://www.youtube.com/watch?v=9bZkp7q19f0"
}
```

---

## 🧪 Running Tests

```bash
cd backend
pytest teaching/tests.py -v
```

**Test coverage:**
- `TestContentHierarchy` — Category/SubCategory/Subject creation, traversal, auto-slug
- `TestMediaContent` — all 5 media types, YouTube embed ID extraction, dashboard filter
- `TestHotspot` — hotspot-to-media linking
- `TestCategoryAPI` — list and retrieve endpoints
- `TestSubjectAPI` — list, filter, detail (body, sidebar, hotspots, dashboard)
- `TestMediaAPI` — all 5 media type API responses, 404 handling

---

## 📂 Project Structure

```
Assesment/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── core/                       # Django project config
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── teaching/                   # Main application
│   │   ├── models.py               # Category, SubCategory, Subject, MediaContent, Hotspot
│   │   ├── serializers.py          # DRF serializers (nested, typed media)
│   │   ├── views.py                # API viewsets + template view
│   │   ├── urls.py                 # API routing
│   │   ├── admin.py                # Rich admin with inline editing
│   │   ├── tests.py                # pytest unit tests
│   │   └── management/
│   │       └── commands/
│   │           └── seed_data.py    # Demo data seeder
│   ├── static/
│   │   └── demo/                   # Bundled demo assets
│   │       ├── rose.jpg            # Demo image
│   │       ├── audio.wav           # Generated 440Hz tone
│   │       └── video.mp4           # Downloaded sample video
│   └── templates/
│       └── index.html              # Full frontend (vanilla HTML/CSS/JS)
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── .env.example
└── README.md
```

---

## 🔧 Management Commands

```bash
# Seed demo data (idempotent — safe to run multiple times)
python manage.py seed_data

# Reset and re-seed from scratch
python manage.py seed_data --reset

# Standard Django commands
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

---

## 🐳 Docker Details

The `Dockerfile` uses a **multi-stage build**:

1. **Builder stage** — installs Python dependencies
2. **Runtime stage** — copies packages, downloads sample video via `curl`, sets entrypoint

The startup `CMD` runs automatically:
1. `python manage.py migrate`
2. `python manage.py seed_data`
3. `python manage.py collectstatic`
4. `python manage.py runserver 0.0.0.0:8000`

To switch to **PostgreSQL**, uncomment the `db` service in `docker-compose.yml` and set `DATABASE_URL`.

---

## 🏗 Architecture Decisions

| Decision | Rationale |
|---|---|
| **Django + DRF** | Rapid admin panel, mature ORM, first-class REST support |
| **Polymorphic via `media_type` field** | Simple, no multi-table-inheritance complexity |
| **`static_path` field** | Allows bundled demo assets to be served without requiring upload |
| **Hotspot HTML injection at seed time** | IDs known after object creation; clean separation of data and presentation |
| **Vanilla JS frontend** | No build tool needed; purely demonstrative prototype |
| **SQLite default** | Zero-config for reviewers; one ENV var switches to Postgres |

---

## 📝 Admin Panel

Access at `/admin/` with credentials `admin` / `admin123`.

- **Subject** page shows inline panels for both `MediaContent` and `Hotspot` records
- **MediaContent** list supports filtering by type, subject, and dashboard flag
- All slugs auto-generate from names

---

## 🔒 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure dev key | Django secret key |
| `DEBUG` | `True` | Debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `DATABASE_URL` | (empty → SQLite) | PostgreSQL connection string |
| `CORS_ALLOWED_ORIGINS` | localhost origins | Allowed CORS origins |
