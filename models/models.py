from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from database import Base # Az önce yazdığımız Base sınıfını içeri alıyoruz
from sqlalchemy import JSON

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

class ChatHistory(Base):    
    __tablename__ = "chat_histories"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, index=True, nullable=False)
    thread_id = Column(String, index=True)
    messages = Column(JSON)
    created_at = Column(String, default="")    