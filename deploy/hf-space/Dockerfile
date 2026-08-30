# Hugging Face Space (Docker, free CPU) — serves API + built frontend on :7860.
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

# Frontend files are uploaded flat (HF web upload); arrange them where Flask serves them.
RUN mkdir -p static && mv index.html index-*.js index-*.css static/

# Bake the model into the image; make caches readable for the Space runtime user.
ENV HF_HOME=/app/hf-cache
RUN python -c "from transformers import AutoImageProcessor, AutoModelForImageClassification as M; \
    AutoImageProcessor.from_pretrained('nateraw/food'); M.from_pretrained('nateraw/food')" \
 && chmod -R 777 /app/hf-cache

ENV PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "gunicorn --preload -w 1 -b 0.0.0.0:${PORT} --timeout 120 app:app"]
