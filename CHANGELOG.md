# Changelog

## [0.1.0] - 2026-03-30
Bu dosya, OlyKube projesindeki tüm önemli değişiklikleri belgelemek içindir.
Format [Keep a Changelog](https://keepachangelog.com/tr/1.0.0/) standardına dayanmaktadır.

## [Unreleased] - Geliştirme Aşamasında
### Eklenenler (Added)
- Kapsamlı proje klasör mimarisi (core, api, services, models).
- PostgreSQL veritabanı bağlantısı ve ORM (SQLAlchemy) altyapısı.
- Redis tabanlı "Rate Limiting" (Hız Sınırlandırma) kalkanı.
- Güvenlik için Pydantic şemaları.
- JWT tabanlı kimlik doğrulama (register, login, protected endpoint).
- Sistemin her nefesini ve hataları kaydeden global Logger (RotatingFileHandler) entegrasyonu.
- Proje başlangıç dokümantasyonu (README.md).