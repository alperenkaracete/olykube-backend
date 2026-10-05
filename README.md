# OlyKube AI Platform 🚀

[![Tests](https://github.com/alperenkaracete/olykube-backend/actions/workflows/tests.yml/badge.svg)](https://github.com/alperenkaracete/olykube-backend/actions/workflows/tests.yml)

> **What is this?** OlyKube is the backend of an LLM-based AIOps agent: a LangGraph ReAct agent running on a local model (Ollama) diagnoses service errors by searching a ChromaDB knowledge base and the web (Tavily), then saves the solutions it finds so the same error can be solved locally next time. It is built with FastAPI, PostgreSQL (users, agents and persistent agent memory), Redis rate limiting and JWT auth, and runs with Docker Compose or on Kubernetes (kind + Cilium). Dynamic Agent-per-Pod scheduling on Kubernetes and Prometheus metrics are planned as part of an ongoing thesis project and are not implemented yet. The rest of this README is in Turkish.

Otonom ajanlar ve AIOps süreçleri için geliştirilen, LangGraph ve RAG (Retrieval-Augmented Generation) destekli, konteynerize bir yapay zeka backend servisi.

Ajanlar yerel LLM'ler (Ollama) üzerinde çalışır; hataları teşhis etmek için yerel bilgi tabanında (ChromaDB) ve internette (Tavily) arama yapar, çözdükleri hataları bilgi tabanına geri yazarak zamanla "öğrenir". Uzun vadeli hedef, Kubernetes üzerinde her ajan için dinamik ve kaynak-farkındalıklı pod'lar (Agent-per-Pod) oluşturmaktır; bkz. [Durum / Yol Haritası](#-durum--yol-haritası).

## 🛠 Teknoloji Yığını

* **Backend:** FastAPI (Python 3.11)
* **AI & Orkestrasyon:** LangChain, LangGraph, Ollama (yerel LLM)
* **RAG & Arama:** ChromaDB (vektör veritabanı), Tavily (web arama)
* **Veritabanı:** PostgreSQL 15 (SQLAlchemy ORM + LangGraph `AsyncPostgresSaver` ile kalıcı ajan hafızası)
* **Rate Limiting:** Redis
* **Konteyner & Orkestrasyon:** Docker (multi-stage build, non-root kullanıcı, healthcheck), Docker Compose, Kubernetes (kind + Cilium)
* **Güvenlik:** JWT (OAuth2 password flow), bcrypt, Pydantic doğrulama

## 🏗️ Mimari

```mermaid
flowchart LR
    client(["İstemci / Swagger UI"]) -->|"HTTP + JWT"| api

    subgraph stack["Docker Compose / Kubernetes"]
        api["olykube-api<br/>FastAPI + LangGraph"]
        db[("olykube-db<br/>PostgreSQL")]
        redis[("olykube-redis<br/>Redis")]
        chroma[("olykube-chromadb<br/>ChromaDB")]
    end

    subgraph tools["Ajan araçları"]
        logs["fetch_service_logs<br/>(şimdilik mock)"]
        kb["search_knowledge_base"]
        web["search_web_for_error"]
        save["save_error_solution"]
    end

    ollama["Ollama<br/>(host makinede)"]
    tavily["Tavily API"]

    api -->|"rate limit"| redis
    api -->|"kullanıcılar, ajanlar,<br/>ajan hafızası"| db
    api -->|"/ingest"| chroma
    api -->|"LLM çağrıları"| ollama
    api -.->|"ReAct döngüsü"| tools
    kb -->|"arama"| chroma
    save -->|"çözümü kaydet"| chroma
    web --> tavily
```

| Servis | Görev |
|---|---|
| `olykube-api` | FastAPI uygulaması: kimlik doğrulama, ajan yönetimi, LangGraph ajan çalıştırma, RAG ingest |
| `olykube-db` | PostgreSQL: kullanıcılar, ajanlar, sohbet geçmişi ve LangGraph checkpoint'leri (volume ile kalıcı) |
| `olykube-redis` | IP bazlı rate limiting sayaçları |
| `olykube-chromadb` | Döküman ve öğrenilmiş çözümlerin embedding'leri (volume ile kalıcı) |
| Ollama (host'ta) | LLM motoru; konteynerlerin dışında, host makinede çalışır |

### AIOps Ajanı

`POST /agents/{id}/chat` çağrıldığında ajan şu araçlarla bir ReAct döngüsü çalıştırır:

| Araç | Ne yapar |
|---|---|
| `fetch_service_logs` | Servis loglarını getirir. **Şu an sabit (mock) veri döner**; gerçek K8s log entegrasyonu planlanıyor |
| `search_knowledge_base` | ChromaDB'de arama yapar, sonuçları `[source: ...]` atfıyla döner |
| `search_web_for_error` | Yerelde çözüm yoksa Tavily ile internette arar |
| `save_error_solution` | Çözülen hatayı ChromaDB'ye yazar; sistem sonraki seferde aynı hatayı yerelden bulur |

- Ajanın talimatı, ortak DevOps iş akışı ile ajanın kendi `system_prompt`'unun birleşimidir; LLM olarak ajanın `model_name` alanındaki Ollama modeli kullanılır.
- Konuşma hafızası `thread_id` bazında PostgreSQL'de tutulur (LangGraph checkpointer).
- Ollama'ya ulaşılamazsa ajan hiç başlatılmaz, istek `503` ile döner.
- Yanıt, son cevabın yanında ajanın çağırdığı araçları (`actions_taken`), kullandığı kaynakları (`cited_sources`) ve yeni bilgi kaydedip kaydetmediğini (`new_knowledge_saved`) içerir.

## ⚙️ Kurulum ve Çalıştırma

Tüm yöntemler için önce ortam değişkenlerini hazırlayın:

```bash
cp .env.example .env
```

| Değişken | Zorunlu | Açıklama |
|---|---|---|
| `SQLALCHEMY_DATABASE_URL` | ✅ | PostgreSQL bağlantı adresi |
| `SECRET_KEY` | ✅ | JWT imzalama anahtarı. Üretmek için: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `TAVILY_API_KEY` | Web araması için | [tavily.com](https://tavily.com) API anahtarı |
| `OLLAMA_BASE_URL` | | Varsayılan `http://localhost:11434` |
| `REDIS_HOST` / `REDIS_PORT` | | Varsayılan `localhost` / `6379` |
| `CHROMA_HOST` / `CHROMA_PORT` | | Varsayılan `chromadb` / `8000` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Compose için | `olykube-db` konteyneri bu değerlerle kurulur |

Zorunlu bir değişken eksikse uygulama açılışta hangi değişkenin eksik olduğunu söyleyerek durur. `.env` dosyası git'e eklenmez; sırları yalnızca orada tutun.

Ajanın kullanacağı modeli Ollama'ya önceden indirin (ajanların varsayılan modeli `llama3`):

```bash
ollama pull llama3
```

### Yöntem 1: Docker Compose (Önerilen)

**Gereksinimler:** Docker, Docker Compose ve host makinede çalışan Ollama.

`.env.example` içindeki değerler Compose'a göre hazırdır (host adları konteyner adlarıdır, Ollama `http://host.docker.internal:11434`).

```bash
docker compose up -d --build
```

API `http://localhost:8000` adresinde, Swagger UI `http://localhost:8000/docs` adresinde açılır. `olykube-api` konteyneri `/health` üzerinden healthcheck yapar; durumunu `docker ps` ile `(healthy)` olarak görebilirsiniz (diğer servislerde henüz healthcheck tanımlı değildir).

### Yöntem 2: Yerel (Manuel) Kurulum

**Gereksinimler:** Python 3.11+, PostgreSQL, Ollama ve bir ChromaDB sunucusu. Redis opsiyoneldir: erişilemezse rate limiting geçici olarak devre dışı kalır, istekler engellenmez.

```bash
# ChromaDB sunucusu (API ile çakışmaması için 8001 portunda)
docker run -d -p 8001:8000 chromadb/chroma

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`.env` içindeki host'ları yerel ortama göre güncelleyin:

```ini
SQLALCHEMY_DATABASE_URL=postgresql://kullanici:sifre@localhost:5432/olykube
REDIS_HOST=localhost
CHROMA_HOST=localhost
CHROMA_PORT=8001
OLLAMA_BASE_URL=http://localhost:11434
```

```bash
uvicorn main:app --reload
```

Uygulama `.env` dosyasını otomatik okur. Docker image'ında ChromaDB'nin embedding modeli (all-MiniLM-L6-v2, ~80 MB) hazır gelir; yerel kurulumda ise ilk `/ingest` veya bilgi tabanı aramasında bir kez indirilir, bu ilk istek bağlantı hızına göre birkaç dakika sürebilir.

### Yöntem 3: Kubernetes (kind + Cilium)

Manifest'ler `k8s/` klasöründedir:

| Dosya | İçerik |
|---|---|
| `k8s/kind-cilium-config.yaml` | Varsayılan CNI'ı kapatan kind cluster tanımı (Cilium sonradan kurulur) |
| `k8s/infrastructure-deployment.yaml` | PostgreSQL (`db`) ve Redis (`redis`) Deployment + Service |
| `k8s/chromadb-deployment.yaml` | ChromaDB (`chromadb`) Deployment + Service |
| `k8s/api-deployment.yaml` | API Deployment (2 replika) + ClusterIP Service (`olykube-api-service`, port 80 → 8000) |

**1. Cluster'ı kurun ve Cilium'u yükleyin** ([cilium CLI](https://docs.cilium.io/en/stable/gettingstarted/k8s-install-default/) gerekir):

```bash
kind create cluster --config k8s/kind-cilium-config.yaml
cilium install
cilium status --wait
```

**2. API image'ını build edip cluster'a yükleyin.** Tag, `k8s/api-deployment.yaml` içindeki `image` alanıyla aynı olmalıdır:

```bash
docker build -t olykube-api:v5 .
kind load docker-image olykube-api:v5
```

**3. Secret'ları oluşturun.** Şifreler ve anahtarlar repoda tutulmaz; iki Secret elle oluşturulur.

PostgreSQL şifresi (`olykube-db`): `db` Deployment'ı şifreyi bu Secret'tan okur. Şifreyi komut satırına yazmak yerine sorarak alın, böylece shell geçmişinde kalmaz:

```bash
read -rsp "PostgreSQL şifresi: " DB_PASSWORD; echo
kubectl create secret generic olykube-db --from-literal=POSTGRES_PASSWORD="$DB_PASSWORD"
```

> PostgreSQL şifreyi yalnızca veritabanı ilk kez oluşturulurken uygular. Şifreyi sonradan değiştirirseniz `db` pod'unun verisini sıfırlamanız ya da şifreyi veritabanında da (`ALTER USER`) güncellemeniz gerekir.

API ortam değişkenleri (`olykube-env`): API pod'u tüm değişkenleri bu Secret'tan alır. Cluster içi için ayrı bir env dosyası hazırlayın (örn. `.env.k8s`, git'e eklemeyin); host adları Service adlarıdır ve veritabanı şifresi yukarıdakiyle aynı olmalıdır:

```ini
SQLALCHEMY_DATABASE_URL=postgresql://postgres:<şifre>@db:5432/olykube
REDIS_HOST=redis
CHROMA_HOST=chromadb
OLLAMA_BASE_URL=http://<host-makinenin-IP-adresi>:11434
SECRET_KEY=...
TAVILY_API_KEY=...
```

```bash
kubectl create secret generic olykube-env --from-env-file=.env.k8s
```

**4. Servisleri ayağa kaldırın ve API'ye erişin:**

```bash
kubectl apply -f k8s/infrastructure-deployment.yaml -f k8s/chromadb-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl port-forward svc/olykube-api-service 8000:80
```

> **Bilinen kısıtlar:** Manifest'lerde henüz PersistentVolume yoktur (pod yeniden başlarsa PostgreSQL ve ChromaDB verisi kaybolur), ve liveness/readiness probe tanımlı değildir. Bunlar yol haritasındadır.

## 📡 API Endpoint'leri

Tüm endpoint'leri `http://localhost:8000/docs` (Swagger UI) üzerinden deneyebilirsiniz. Korumalı endpoint'ler için Swagger'daki **Authorize** butonuna e-posta (username alanına) ve şifrenizi girmeniz yeterlidir.

### 🔐 Kimlik Doğrulama & Sistem

| Method | Endpoint | Açıklama | Auth |
|---|---|---|---|
| POST | `/register` | Yeni kullanıcı kaydı. Gövde: `{"email", "password"}` | Hayır |
| POST | `/login` | JWT token al (30 dk geçerli). JSON `{"email", "password"}` veya form `username` / `password` kabul eder | Hayır |
| GET | `/health` | Sağlık kontrolü, `{"status": "ok"}` döner | Hayır |
| GET | `/protected` | Token'ın sahibi olan kullanıcının e-postasını döner | Evet |

### 🤖 Ajan İşlemleri

| Method | Endpoint | Açıklama | Auth |
|---|---|---|---|
| POST | `/agents/` | Ajan oluştur. Gövde: `name`, `system_prompt`, opsiyonel `description`, `model_name` (varsayılan `llama3`). Aynı isim tekrar kullanılırsa `400` | Evet |
| GET | `/agents/` | Ajanları listele (`?skip=0&limit=100`) | Evet |
| GET | `/agents/{agent_id}` | ID ile ajan getir | Evet |
| GET | `/agents/name/{agent_name}` | İsim ile ajan getir | Evet |
| DELETE | `/agents/?agent_name=<isim>` | Ajanı isme göre sil | Evet |
| POST | `/agents/{agent_id}/chat` | Ajanla konuş. Gövde: `{"message", "thread_id"}` (`thread_id` varsayılan `default_session`) | Evet |
| GET | `/agents/{agent_id}/history/{thread_id}` | Thread'in kayıtlı sohbet geçmişi (şu an yalnızca son soru-cevap çifti saklanır) | Evet |

### 📚 RAG

| Method | Endpoint | Açıklama | Auth |
|---|---|---|---|
| POST | `/ingest` | Metni parçalara (800 karakter, 100 örtüşme) bölüp ChromaDB'ye kaydeder. Gövde: `{"text", "doc_id"}`. Aynı `doc_id` tekrar gönderilirse parçalar güncellenir | Evet |

### Rate Limiting

Her IP adresi 60 saniyede en fazla **10 istek** atabilir; aşılırsa `429` döner. `/health`, `/docs` ve `/openapi.json` bu sınırın dışındadır. Redis'e ulaşılamazsa sınırlama 30 saniyeliğine devre dışı kalır, istekler engellenmez ve durum loglanır.

## 🧪 Testler

```bash
pip install -r requirements-dev.txt
pytest
```

Testler harici servis gerektirmez: veritabanı olarak in-memory SQLite, Redis ve ChromaDB yerine sahte (fake) nesneler kullanılır. Her push ve pull request'te GitHub Actions üzerinde otomatik çalışır.

| Dosya | Kapsam |
|---|---|
| `tests/test_auth.py` | Kayıt, JSON ve form (Swagger) ile login, hatalı giriş, tüm korumalı endpoint'lerin token'sız/geçersiz token'la `401` dönmesi, token ile ajan CRUD |
| `tests/test_rate_limit.py` | 10 istekten sonra `429`, IP bazlı sayım, Redis kapalıyken isteklerin geçmesi ve Redis'in bekleme süresinde tekrar denenmemesi |
| `tests/test_health.py` | `/health` yanıtı ve rate limit dışında tutulması |

Ajan sohbeti (Ollama, Tavily, ChromaDB) henüz otomatik testlerle kapsanmıyor; bunlar için `scripts/` altındaki elle çalıştırılan deneme script'leri kullanılıyor.

## 📁 Proje Yapısı

```
├── main.py               # FastAPI uygulaması, middleware'ler ve endpoint'ler
├── core/                 # Ayarlar (.env okuma) ve logger
├── auth/                 # Şifre hash'leme ve JWT
├── models/, schemas.py   # SQLAlchemy modelleri ve Pydantic şemaları
├── services/             # Ajan, RAG ingest, ChromaDB, rate limiter, kullanıcı ve geçmiş servisleri
├── tests/                # pytest testleri
├── k8s/                  # Kubernetes manifest'leri
├── scripts/              # Elle çalıştırılan deneme script'leri (LLM, Tavily, ChromaDB)
├── Dockerfile            # Multi-stage, non-root image
└── docker-compose.yml
```

## 🗺️ Durum / Yol Haritası

**Tamamlananlar ✅**

- JWT kimlik doğrulama; ajan ve ingest endpoint'lerinin korunması
- Ajan CRUD işlemleri ve PostgreSQL ile kalıcı ajan hafızası (LangGraph checkpointer)
- 4 araçlı AIOps ajanı: yerel bilgi tabanı, web araması, çözümleri bilgi tabanına kaydetme
- RAG ingest (ChromaDB)
- Redis ile rate limiting (Redis kapalıyken istekleri engellemez)
- Docker Compose ile tam konteynerize çalışma; multi-stage, non-root image ve healthcheck
- kind + Cilium üzerinde temel Kubernetes deployment'ı
- Auth, rate limiting ve health için pytest testleri ve GitHub Actions CI

**Planlananlar 🔜**

- **Dinamik Agent-per-Pod:** Her ajan için Kubernetes API üzerinden, kaynak kullanımına göre boyutlandırılan pod'ların dinamik olarak oluşturulması
- **Prometheus metrikleri:** `/metrics` endpoint'i (istek sayısı/süresi, ajan çağrıları, araç kullanımı) ve Grafana panoları
- **Gerçek log toplama:** `fetch_service_logs` aracının Kubernetes API'den gerçek pod loglarını okuması
- **Sohbet geçmişi:** Geçmiş endpoint'inin tüm konuşmayı LangGraph checkpointer'dan okuması
- **Dosya yükleme:** `/ingest` için txt/pdf dosya yükleme desteği
- **Asenkron ajan çalıştırma:** Uzun süren ajan çağrılarının kuyruk (Celery) üzerinden çalıştırılması
- **Kubernetes sağlamlaştırma:** PersistentVolume, liveness/readiness probe'ları
- **Veritabanı migration'ları:** Alembic

---
*Bu proje, otonom ajan mimarileri ve kaynak-farkındalıklı (resource-aware) Kubernetes deployment tez çalışması kapsamında geliştirilmektedir.*
