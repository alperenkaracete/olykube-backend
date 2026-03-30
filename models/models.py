from sqlalchemy import Boolean, Column, Integer, String
from database import Base # Az önce yazdığımız Base sınıfını içeri alıyoruz

class Todo(Base):
    # 1. Tablo Adı: Veritabanında (PostgreSQL içinde) bu tablonun adı ne olacak?
    __tablename__ = "todos"

    # 2. Sütunlar (Columns): Tablonun kolonlarını ve veri tiplerini tanımlıyoruz
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, default="")
    completed = Column(Boolean, default=False)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)    