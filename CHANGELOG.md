# Changelog

Bu dosya, OlyKube projesindeki tüm önemli değişiklikleri belgelemek içindir.
Format [Keep a Changelog](https://keepachangelog.com/tr/1.0.0/) standardına dayanmaktadır.

## [Unreleased]

## [0.1.0] - 2026-03-30

### Eklenenler (Added)
- **AI Engine Integration:** Entegre LangGraph otonom ajan mimarisi (`create_react_agent`).
- **Dynamic Chat Endpoint:** Kullanıcıların ajanlarla spesifik kimliklerine (`system_prompt`) göre konuşabilmesini sağlayan `POST /agents/{agent_id}/chat` uç noktası.
- **Web Search Tool:** Ajanlara internet üzerinden gerçek zamanlı veri çekme ve araştırma yapma yeteneği kazandıran Tavily API entegrasyonu.
- **Fail-Fast Health Check:** Ollama servisi kapalıyken API'nin kilitlenmesini önleyen ve anında `503 Service Unavailable` dönen asenkron ping mekanizması.
- Kapsamlı proje klasör mimarisi (core, services, models, auth).
- PostgreSQL veritabanı bağlantısı ve ORM (SQLAlchemy) altyapısı.
- Redis tabanlı rate limiting middleware.
- JWT tabanlı kimlik doğrulama (register, login, protected endpoint).
- Global logger entegrasyonu (RotatingFileHandler).
- Ajan yönetimi için Agent modeli ve tam CRUD endpointleri.
- Listeleme endpointine sayfalama (skip/limit) eklendi.
- Pydantic şemaları ile veri doğrulama (AgentCreate, AgentResponse).
- Proje dokümantasyonu (README.md, CHANGELOG.md).

### Düzeltilenler (Fixed)
- Mükerrer ajan isimlerinde IntegrityError yakalanarak 400 döndürüldü.
- Aynı isimde ajan eklenmesini engellemek için UNIQUE kısıtlaması eklendi.