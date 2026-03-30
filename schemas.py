from pydantic import BaseModel

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