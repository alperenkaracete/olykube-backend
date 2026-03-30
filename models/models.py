from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
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

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    system_prompt = Column(Text, nullable=False)
    model_name = Column(String, default="llama3") # Varsayılan bir model atayabilirsin
    status = Column(String, default="idle")
    created_at = Column(DateTime(timezone=True), server_default=func.now())    