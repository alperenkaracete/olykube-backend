from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Kullanıcının bize POST yaparken göndermesine İZİN VERDİĞİMİZ alanlar
class TodoCreate(BaseModel):
    title: str
    description: str | None = None
    
# Veritabanından okuyup dışarıya (GET) DÖNDÜRECEĞİMİZ alanlar
class TodoResponse(TodoCreate):
    id: int
    completed: bool

    class Config:
        from_attributes = True # Bu sihirli satır, Pydantic'in SQLAlchemy objesini anlamasını sağlar

# 1. Ortak Alanlar (Hem girişte hem çıkışta olanlar)
class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    model_name: Optional[str] = "llama3"

# 2. POST İstekleri İçin (Sadece bu veriler kullanıcıdan istenecek)
class AgentCreate(AgentBase):
    pass

# 3. GET Yanıtları İçin (Veritabanından dönen tüm veriler eklendi)
class AgentResponse(AgentBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True # Çok Kritik: SQLAlchemy objesini JSON'a çeviren sihirli köprü!

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_session" # Hafıza takibi için        