# Changelog

Bu dosya, OlyKube projesindeki tüm önemli değişiklikleri belgelemek içindir.
Format [Keep a Changelog](https://keepachangelog.com/tr/1.0.0/) standardına dayanmaktadır.

## [Unreleased]

## [0.1.0] - 2026-03-30

### Added
**Yapay Zeka ve Ajan Mimarisi**
- **Otonom ReAct Ajanı:** LangGraph mimarisi kullanılarak hem yerel veritabanında arama yapabilen (`search_knowledge_base`) hem de internete çıkabilen (`tavily`) karar verebilen ajan altyapısı (`create_react_agent`) kuruldu.
- **Dinamik Sohbet Endpoint'i:** Kullanıcıların ajanlarla spesifik kimliklerine (`system_prompt`) göre konuşabilmesini sağlayan `POST /agents/{agent_id}/chat` uç noktası eklendi.
- **Geçmiş Endpoint'i:** LangGraph checkpointer üzerinden sohbet geçmişini (chat history) okuyan yeni bir API uç noktası eklendi.
- **Fail-Fast Sağlık Kontrolü:** Ajan motoru tetiklenmeden önce Ollama servisine asenkron ping atılarak, sunucu kapalıyken API kilitlenmelerini önleyen (`503 Service Unavailable` dönen) mekanizma eklendi.

**RAG ve Veri Entegrasyonu**
- **Web Arama Aracı:** Ajanlara internet üzerinden gerçek zamanlı veri çekme yeteneği kazandıran Tavily API entegrasyonu.
- **ChromaDB Vektör Veritabanı:** Kalıcı istemci (persistent client) ve embedding pipeline (gömme boru hattı) entegrasyonu.
- **RAG Altyapısı:** Uzun metinleri parçalayarak (recursive text splitting) vektör veritabanına işleyen döküman yükleme uç noktası (ingestion endpoint).

**Temel API Altyapısı**
- Kapsamlı proje klasör mimarisi (core, services, models, auth).
- PostgreSQL veritabanı bağlantısı ve ORM (SQLAlchemy) altyapısı.
- Redis tabanlı rate limiting middleware.
- JWT tabanlı kimlik doğrulama (register, login, protected endpoint).
- Global logger entegrasyonu (RotatingFileHandler).
- Ajan yönetimi için Agent modeli, tam CRUD endpointleri ve sayfalama (skip/limit).
- Pydantic şemaları ile veri doğrulama (AgentCreate, AgentResponse).
- Proje dokümantasyonu (README.md, CHANGELOG.md).

### Changed
- **Kalıcı Hafıza Mimarisi:** Ajanların sohbet geçmişini anlık RAM'de tutan geçici `MemorySaver`, PostgreSQL üzerinde kalıcı depolama sağlayan `AsyncPostgresSaver` ile değiştirildi. Sistem artık uçucu (volatile) bellek yerine endüstri standardı kalıcı checkpointer kullanıyor.

### Fixed
- Mükerrer ajan isimlerinde `IntegrityError` yakalanarak 400 hatası döndürüldü ve aynı isimde ajan eklenmesini engellemek için `UNIQUE` kısıtlaması eklendi.
- Veritabanı bağlantısının aniden kopmasına (`Connection closed`) sebep olan asenkron context manager (kapsam/scope) mantık hatası çözüldü.
- `chat_histories` tablosundaki `agent_id` sütununda yaşanan veri tipi uyuşmazlığı (type mismatch) giderilerek veri bütünlüğü sağlandı.