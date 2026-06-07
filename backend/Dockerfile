FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_SYSTEM_PYTHON=1 \
    HF_HOME=/app/cache/huggingface \
    TRANSFORMERS_CACHE=/app/cache/huggingface

# System deps:
#   libmagic1     -> python-magic MIME sniffing
#   tesseract-ocr -> OCR engine (FR-021)
#   poppler-utils -> pdf2image (scanned PDF -> images)
#   ffmpeg        -> yt-dlp audio extraction (transcripts only, but ffmpeg often required)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libmagic1 \
        tesseract-ocr \
        poppler-utils \
        ffmpeg \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml ./
RUN uv pip install --system -r pyproject.toml

COPY app ./app

RUN mkdir -p /app/data/uploads /app/data/storage /app/cache/huggingface

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
