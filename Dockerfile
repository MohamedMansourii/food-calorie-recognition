# One-URL deployment: builds the React frontend, then serves API + static
# frontend from a single Flask/gunicorn process. Fits free tiers (Render/Railway).

# --- stage 1: frontend build ---------------------------------------------
FROM node:20-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- stage 2: python runtime ---------------------------------------------
FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
 && pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY data/ data/
COPY --from=frontend /build/dist frontend/dist

# Bake the model into the image so the first request doesn't download 350 MB.
RUN python -c "from transformers import AutoImageProcessor, AutoModelForImageClassification as M; \
    AutoImageProcessor.from_pretrained('nateraw/food'); M.from_pretrained('nateraw/food')"

ENV PORT=8000
EXPOSE 8000
WORKDIR /app/backend
# Single worker: one model copy in RAM. --preload loads it before serving.
CMD ["sh", "-c", "gunicorn --preload -w 1 -b 0.0.0.0:${PORT} --timeout 120 app:app"]
