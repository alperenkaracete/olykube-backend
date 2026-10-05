from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from auth.hashing import hash_password, verify_password
from auth.token import create_access_token
from auth.token import get_current_user
from fastapi import Request
from services.agents_service import run_olykube_agent
from services.chat_history_service import save_chat_history, get_chat_history
from services.rate_limiter import check_rate_limit
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from core.logger import logger
from services.ingest_service import ingest_document
import time
import traceback


from models.user import UserRegister
from services.user_service import get_user_by_email

# Kendi yazdığımız dosyaları (modülleri) içeri alıyoruz
import models
import schemas
from database import engine, SessionLocal

# 1. BÜYÜK AN: Tabloları Yaratma Komutu
# Bu satır, models.py içindeki sınıfları okur ve PostgreSQL'e gidip 
# "Eğer tablolar (users, agents, ...) yoksa hemen CREATE TABLE ile yarat" der.
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 2. Veritabanı Oturumu (Session) Yönetimi
# Her bir API isteği (Request) geldiğinde yeni bir veritabanı bağlantısı açar 
# ve işlem bitince bağlantıyı güvenli bir şekilde kapatır.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() # C++'taki 'delete' veya destructor (yıkıcı) mantığı. Bellek sızıntısını (Memory Leak) önler!

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time() # Kronometreyi başlat
    
    # İsteği bir alt katmana (rate_limit_middleware'e) gönder ve cevabı bekle
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000 # Kaç milisaniye sürdü?
    
    # Her nefesi logla (AIOps için altın değerinde veri)
    logger.info(f"{request.client.host} - {request.method} {request.url.path} - Status: {response.status_code} - Süre: {process_time:.2f}ms")
    
    return response        

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # K8s veya Load Balancer'ın sağlık kontrolüne sınırsız izin ver!
    if request.url.path in ["/health", "/docs", "/openapi.json"]:
        return await call_next(request)
    ip = request.client.host
    if not check_rate_limit(ip):
        logger.warning(f"RATE LIMIT AŞILDI! Olası DDOS veya Spam. IP: {ip}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Çok fazla istek attınız, 1 dakika bekleyin."}
        )
    response = await call_next(request)
    return response

@app.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user.email)
    if existing_user :
        raise HTTPException(status_code=400, detail="Bu email zaten kayıtlı")
    else :
        hashed_pw = hash_password(user.password)
        db_user = models.User(email = user.email, hashed_password = hashed_pw)       
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

async def get_login_credentials(request: Request) -> UserRegister:
    # JSON: {"email", "password"} — API istemcileri için
    # Form: username/password — Swagger'daki "Authorize" butonu (OAuth2 password flow) bunu gönderir
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
        if not isinstance(data, dict):
            data = {}
    else:
        form = await request.form()
        data = {"email": form.get("username"), "password": form.get("password")}
    try:
        return UserRegister(**data)
    except ValidationError as e:
        raise RequestValidationError(e.errors(include_url=False, include_context=False))

@app.post("/login")
def login(user: UserRegister = Depends(get_login_credentials), db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user.email)
    if not existing_user:
        raise HTTPException(status_code=404, detail="Email bulunamadı")
    
    if not verify_password(user.password, existing_user.hashed_password):
        raise HTTPException(status_code=401, detail="Yanlış şifre")
    
    token = create_access_token(data={"sub": existing_user.email})
    return {"access_token": token, "token_type": "bearer"}      

@app.get("/protected")
def protected(current_user = Depends(get_current_user)):
    return {"email": current_user}

@app.post("/agents/", response_model = schemas.AgentCreate, dependencies=[Depends(get_current_user)])
def create_agents(agent : schemas.AgentCreate,db: Session = Depends(get_db)):
    db_agent = models.Agent(**agent.model_dump())
    try:
        db.add(db_agent)
        db.commit() # PostgreSQL'in UNIQUE duvarına çarptığı an burasıdır!
        db.refresh(db_agent)
        return db_agent
            
    except IntegrityError:
        # ÇOK KRİTİK: Eğer hata alırsak, RAM'deki o hatalı işlemi geri almalıyız.
        # Yoksa veritabanı oturumu (Session) zehirlenir ve sonraki istekler de çöker.
        db.rollback() 
        
        # Kullanıcıya 500 yerine, şık bir 400 Bad Request dönüyoruz:
        raise HTTPException(
            status_code=400, 
            detail=f"'{agent.name}' isminde bir ajan zaten mevcut. Lütfen farklı bir isim seçin."
        )

@app.get("/agents/name/{agent_name}", response_model=schemas.AgentResponse, dependencies=[Depends(get_current_user)])
def get_agent_by_name(agent_name: str, db: Session = Depends(get_db)):
    db_agent = db.query(models.Agent).filter(models.Agent.name == agent_name).first()
    
    if not db_agent:
        raise HTTPException(status_code=404, detail="Bu isimde bir ajan bulunamadı!")
        
    return db_agent

@app.get("/agents/{agent_id}", response_model=schemas.AgentResponse, dependencies=[Depends(get_current_user)])
def get_agent_by_id(agent_id: int, db: Session = Depends(get_db)):
    db_agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    
    if not db_agent:
        raise HTTPException(status_code=404, detail="Ajan bulunamadı!")
        
    return db_agent

@app.get("/agents/", response_model=list[schemas.AgentResponse], dependencies=[Depends(get_current_user)])
def get_all_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    agents = db.query(models.Agent).offset(skip).limit(limit).all()
    return agents 

@app.delete("/agents/", dependencies=[Depends(get_current_user)])
def delete_agent(agent_name: str, db: Session = Depends(get_db)):
    # 1. Önce silinecek hedefi ismine göre bul
    db_agent = db.query(models.Agent).filter(models.Agent.name == agent_name).first()
    
    # 2. Eğer hedef yoksa 404 fırlat
    if not db_agent:
        raise HTTPException(status_code=404, detail="Silinecek ajan bulunamadı!")
        
    # 3. Hedefi veritabanından sil ve diske yaz (Commit)
    db.delete(db_agent)
    db.commit()
    
    return {"message": f"'{db_agent.name}' isimli ajan (ID: {db_agent.id}) sistemden başarıyla silindi."}

@app.post("/agents/{agent_id}/chat", dependencies=[Depends(get_current_user)])
async def chat_with_agent(agent_id: int, request: schemas.ChatRequest, db: Session = Depends(get_db)):
    # 1. Veritabanından ajanı çek (Ajanın kimliğini burada öğreniyoruz)
    db_agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    
    if not db_agent:
        raise HTTPException(status_code=404, detail="Ajan bulunamadı!")
    try:
        # 2. Servisi çağır ve yanıtı bekle
        # (Şu an senkron bekliyoruz, 10. haftada Celery ile bunu asenkrona çekeceğiz)
        result = await run_olykube_agent(
            user_message=request.message,
            thread_id=request.thread_id,
            model_name=db_agent.model_name,
            system_prompt=db_agent.system_prompt
        )
        # Geçmişi kaydet
        save_chat_history(
            db=db,
            agent_id=agent_id,
            thread_id=request.thread_id,
            messages=[
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": result["reply"]}
            ]
        )
        return {
            "agent_name": db_agent.name,
            "response": result["reply"],
            "actions_taken": result["actions_taken"],
            "cited_sources": result["cited_sources"],
            "new_knowledge_saved": result["new_knowledge_saved"]
        }
    except HTTPException:
        # Ollama kapalıyken dönen 503'ü 500'e çevirmeden olduğu gibi ilet
        raise
    except Exception as e:
        # Yapay zeka tarafında oluşabilecek hataları yakalıyoruz
        print("--- KRİTİK HATA DETAYI ---")
        traceback.print_exc() 
        print("--------------------------")
        raise HTTPException(status_code=500, detail=f"Ajan yanıt verirken bir hata oluştu: {str(e)}")
    
@app.post("/ingest", dependencies=[Depends(get_current_user)])
def ingest(request: schemas.IngestRequest):
    chunk_count = ingest_document(request.text, request.doc_id)
    return {"message": f"{chunk_count} chunk kaydedildi.", "doc_id": request.doc_id}    

@app.get("/agents/{agent_id}/history/{thread_id}", dependencies=[Depends(get_current_user)])
def get_history(agent_id: int, thread_id: str, db: Session = Depends(get_db)):
    history = get_chat_history(db, agent_id, thread_id)
    
    if not history:
        raise HTTPException(status_code=404, detail="Bu thread'e ait geçmiş bulunamadı.")
    
    return {
        "agent_id": agent_id,
        "thread_id": thread_id,
        "messages": history
    }

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok"}
