from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Bağlantı Cümlesi (Connection String) - .env'deki SQLALCHEMY_DATABASE_URL
from core.config import SQLALCHEMY_DATABASE_URL

# 2. Motor (Engine) - Veritabanı ile Python arasındaki fiziksel köprü (TCP bağlantı havuzu)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. Oturum Fabrikası (Session Factory)
# Her bir API isteği geldiğinde veritabanında yeni bir "işlem" (transaction) başlatmak için kullanılır.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Temel Sınıf (Base Class)
# Birazdan oluşturacağımız tüm veritabanı tabloları (Modeller) bu sınıftan miras (inherit) alacak.
Base = declarative_base()