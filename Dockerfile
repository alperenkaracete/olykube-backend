# ==========================================
# STAGE 1: Builder (Derleme Aşaması)
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

# PostgreSQL veya ChromaDB için gerekli olabilecek derleme araçlarını kur
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Gereksinimleri kopyala ve sanal ortam (venv) içine kur
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# Yavaş bağlantıda büyük paketlerin (onnxruntime, chromadb) indirmesi yarıda kalmasın
RUN pip install --no-cache-dir --default-timeout=120 --retries 10 -r requirements.txt


# ==========================================
# STAGE 2: Runtime (Çalıştırma Aşaması)
# ==========================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Sadece runtime için gereken hafif sistem kütüphanelerini kur (örn: libpq5)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Builder aşamasından SADECE derlenmiş bağımlılıkların olduğu venv klasörünü kopyala
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Güvenlik best-practice: Konteyneri root yetkileriyle çalıştırma (K8s'te çok işine yarayacak)
# /app'in sahibi olmalı: uygulama olykube.log dosyasını buraya yazar
RUN useradd -m olykube_user && chown olykube_user:olykube_user /app
USER olykube_user

# ChromaDB'nin varsayılan embedding modelini (all-MiniLM-L6-v2, ~80 MB) image'a göm.
# Aksi halde her pod/konteyner ilk ingest/aramada modeli internetten indirir.
# Kod kopyalanmadan önce çalışır: katman yalnızca requirements.txt veya script değişince yenilenir.
COPY --chown=olykube_user:olykube_user docker/download_embedding_model.py /tmp/
RUN python /tmp/download_embedding_model.py && rm /tmp/download_embedding_model.py

# Uygulama kodlarını kopyala
COPY --chown=olykube_user:olykube_user . .

EXPOSE 8000
# Her 30 saniyede bir, localhost:8000/health adresine istek at.
# Yanıt alamazsa (veya 200 dönmezse) 3 deneme sonunda 'unhealthy' işaretle.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]