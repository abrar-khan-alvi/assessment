# ─── Stage 1: builder ───────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ─── Stage 2: runtime ───────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Install curl for downloading demo assets
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project source
COPY backend/ /app/

# Create required directories
RUN mkdir -p /app/media /app/staticfiles /app/static/demo

# Download sample video for the MyVid demo (soft failure: continues if unavailable)
RUN curl -L --max-time 30 -o /app/static/demo/video.mp4 \
    "https://www.w3schools.com/html/mov_bbb.mp4" || \
    echo "WARNING: Could not download sample video — MyVid modal will show an error"

# Environment
ENV DJANGO_SETTINGS_MODULE=core.settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False

EXPOSE 8000

# Entrypoint: migrate, seed, collect static, then run gunicorn
CMD ["sh", "-c", "\
    python manage.py migrate --noinput && \
    python manage.py seed_data && \
    python manage.py collectstatic --noinput --clear && \
    gunicorn core.wsgi:application --bind 0.0.0.0:8000 \
"]
