# OlyKube API 🚀

Otonom ajanlar ve AIOps süreçleri için tasarlanmış, Zero Trust (Sıfır Güven) mimarisine uygun, yüksek performanslı backend servisi.

## 🛠 Teknoloji Yığını (Tech Stack)
* **Framework:** FastAPI (Python)
* **Veritabanı (Kalıcı):** PostgreSQL & SQLAlchemy (ORM)
* **Veritabanı (Geçici/RAM):** Redis
* **Güvenlik:** JWT Authentication, Pydantic Schema Validation
* **Mimari:** Separation of Concerns (Modüler Klasör Yapısı)

## ⚙️ Kurulum ve Çalıştırma (Lokal Geliştirme)

Bu proje **WSL (Ubuntu)** üzerinde çalışacak şekilde optimize edilmiştir.

### 1. Gereksinimler
Sisteminizde PostgreSQL ve Redis sunucularının kurulu ve çalışıyor olması gerekmektedir.
```bash
# Redis servisini başlatmak için:
sudo service redis-server start

# PostgreSQL servisini başlatmak için:
sudo service postgresql start

### 2. Projeyi Klonla ve Bağımlılıkları Yükle
```bash
git clone https://github.com/kullaniciadi/olykube-api
cd olykube-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Ortam Değişkenlerini Ayarla
`.env.example` dosyasını kopyala:
```bash
cp .env.example .env
```
İçini doldur:
```
DATABASE_URL=postgresql://kullanici:sifre@localhost:5432/todo_db
SECRET_KEY=gizli-anahtar
```

### 4. Uygulamayı Başlat
```bash
uvicorn main:app --reload
```

## 📡 Endpoints
| Method | Endpoint | Açıklama | Auth |
|---|---|---|---|
| POST | /register | Kullanıcı kaydı | Hayır |
| POST | /login | JWT token al | Hayır |
| GET | /protected | Token doğrula | Evet |
| POST | /todos | Todo oluştur | Evet |
| GET | /todos | Tüm todolar | Evet |