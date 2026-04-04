# OlyKube AI Platform 🚀

Otonom ajanlar ve AIOps süreçleri için tasarlanmış; LangGraph ve RAG (Retrieval-Augmented Generation) destekli, tamamen konteynerize edilmiş yüksek performanslı yapay zeka backend servisi. 

Bu proje, yerel LLM modellerini (Ollama/Qwen) yönetmek ve ileride Kubernetes üzerinde dinamik "resource-aware" ajan pod'ları (Agent-per-Pod) oluşturmak için bir altyapı sunar.

## 🛠 Teknoloji Yığını (Tech Stack)

* **Backend Framework:** FastAPI (Python 3.11)
* **AI & Orkestrasyon:** LangChain, LangGraph, Ollama (Yerel LLM)
* **RAG & Vektör Arama:** ChromaDB, Tavily (Web Search API)
* **Kalıcı Veritabanı:** PostgreSQL 15 (SQLAlchemy ORM, Ajan Geçmişi & Metadata)
* **Önbellek & Rate Limit:** Redis
* **Konteynerizasyon:** Docker, Docker Compose (Multi-stage build, Health Checks)
* **Güvenlik:** JWT Authentication, Pydantic Schema Validation, Non-root Container Execution

## 🏗️ Mimari (Microservices)

Sistem `olykube-network` isimli izole bir bridge ağı üzerinde, birbirleriyle doğrudan DNS isimleriyle haberleşen 4 ana servisten oluşur:
1. `olykube-api`: LangGraph ajan mantığını, yönlendirmeleri ve RAG pipeline'ını yöneten ana backend.
2. `olykube-db`: İlişkisel verileri (Kullanıcılar, Ajan metadataları, sohbet geçmişleri) tutar (Stateful/Volume).
3. `olykube-redis`: Hız limiti (Rate Limiting) ve token doğrulama işlemleri için kullanılır.
4. `olykube-chromadb`: Döküman embedding'leri için bağımsız vektör veritabanı sunucusu (Stateful/Volume).

## ⚙️ Kurulum ve Çalıştırma

Bu projeyi çalıştırmak için iki farklı yöntem tercih edebilirsiniz: İzolasyon ve kolaylık sağlayan **Docker (Önerilen)** yöntemi veya geliştirme aşamasında esneklik sağlayan **Yerel (Manuel) Kurulum** yöntemi.

### Yöntem 1: Docker ile Çalıştırma (Önerilen)
Bu yöntem sisteminizde gereksiz paket kirliliği yaratmaz ve tüm mimariyi (Veritabanı, Redis, API) tek komutla izole bir ağda ayağa kaldırır.

**Gereksinimler:** Docker, Docker Compose ve host makinede kurulu Ollama.

**1. Ortam Değişkenlerini Ayarlayın**
`.env.example` dosyasını kopyalayarak `.env` oluşturun:
```bash
cp .env.example .env
```
*(Not: `.env` dosyasındaki veritabanı host isimlerinin Docker servis adlarıyla (örn: `olykube-db`) ve Ollama adresinin `http://host.docker.internal:11434` şeklinde ayarlandığından emin olun.)*

**2. Konteynerleri Başlatın**
Projeyi çok aşamalı (multi-stage) build mimarisiyle başlatmak için:
```bash
docker compose up -d --build
```
*Tüm servisler ayağa kalktığında `docker ps` komutu ile `(healthy)` durumlarını doğrulayabilirsiniz. API `http://localhost:8000` adresinde yayında olacaktır.*

---

### Yöntem 2: Yerel (Manuel) Kurulum
Kodu doğrudan kendi makinenizde (örneğin WSL/Ubuntu üzerinde) derleyip, anlık geliştirme (hot-reload) yapmak isterseniz bu adımları izleyebilirsiniz.

**Gereksinimler:** Python 3.11+, PostgreSQL, Redis ve Ollama.

**1. Arka Plan Servislerini Başlatın**
Sisteminizdeki PostgreSQL ve Redis sunucularının çalışır durumda olduğundan emin olun:
```bash
sudo service redis-server start
sudo service postgresql start
```

**2. Sanal Ortam ve Bağımlılıkları Kurun**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Ortam Değişkenlerini Ayarlayın**
```bash
cp .env.example .env
```
`.env` dosyasındaki bağlantı adreslerini **localhost**'a göre güncelleyin:
```ini
SQLALCHEMY_DATABASE_URL=postgresql://kullanici:sifre@localhost:5432/olykube_db
REDIS_URL=redis://localhost:6379
OLLAMA_BASE_URL=http://localhost:11434
```

**4. Uygulamayı Başlatın**
```bash
uvicorn main:app --reload
```
*API canlı yenileme özelliğiyle `http://localhost:8000` adresinde çalışmaya başlayacaktır.*

---

## 📡 Temel API Endpoint'leri

Tüm endpoint'leri interaktif olarak denemek için uygulama çalıştıktan sonra `http://localhost:8000/docs` (Swagger UI) adresine gidebilirsiniz.

### 🤖 AI Agent İşlemleri
| Method | Endpoint                           | Açıklama                                   | Auth |
|---------|-----------------------------------|----------|---------------------------------|------|
| POST    | `/agents`                         | Yeni bir LangGraph ajanı oluştur | Evet    |      |
| GET     | `/agents`                         | Mevcut ajanları listele | Evet             |      |
| POST    | `/agents/{id}/chat`               | Ajana mesaj gönder (RAG/Tavily tetiklenir) | Evet |
| GET     | `/agents/{id}/history/{thread_id}`| Ajanın spesifik konuşma geçmişini getir    | Evet |
| DELETE  | `/agents/{id}`                    | Ajanı sistemden sil                        | Evet |

### 📚 RAG & Veri Kaynağı
| Method | Endpoint | Açıklama                                                    | Auth |
|--------|----------|-------------------------------------------------------------|------|
| POST | `/ingest`  | Döküman (txt/pdf) yükle ve ChromaDB'ye vektör olarak kaydet | Evet |

### 🔐 Sistem & Auth
| Method | Endpoint   | Açıklama                                           | Auth  |
|--------|------------|----------------------------------------------------|-------|
| GET    | `/health`  | Sistem sağlık kontrolü (K8s Liveness Probe uyumlu) | Hayır |
| POST   | `/register`| Yeni kullanıcı kaydı                               | Hayır |
| POST   | `/login`   | JWT token al | Hayır                               |       |

---
*Bu proje, otonom agent mimarileri ve kaynak-farkındalıklı (resource-aware) Kubernetes deployment tez çalışmaları kapsamında geliştirilmektedir.*