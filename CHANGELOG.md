# Changelog

Bu dosya, OlyKube projesindeki tüm önemli değişiklikleri belgelemek içindir.
Format [Keep a Changelog](https://keepachangelog.com/tr/1.0.0/) standardına dayanmaktadır.

## [Unreleased]

## [0.1.0] - 2026-03-30

### Eklenenler (Added)
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