import re
import httpx
from fastapi import HTTPException
from typing import Dict, Any

from langchain_tavily import TavilySearch
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from core.config import SQLALCHEMY_DATABASE_URL, OLLAMA_BASE_URL
from services.chroma_client import collection

# ── 1. ARAÇLAR (TOOLS) ─────────────────────────────────────────────────────────

@tool
def search_knowledge_base(query: str) -> str:
    """
    OlyKube sistem konfigürasyonları, bilinen hatalar ve daha önce çözülmüş sorunlar için YEREL BİLGİ TABANINDA arama yapar.
    Bir hata ile karşılaşıldığında İLK OLARAK buraya bakılmalıdır.
    """
    results = collection.query(
        query_texts=[query],
        n_results=3
    )
    docs = results.get("documents", [[]])[0]
    if not docs:
        return "Yerel bilgi tabanında (KB) ilgili hata/çözüm bulunamadı."
    
    # Kaynakları da dönerek hocanın kodundaki gibi 'citation' (atıf) yapısını koruyoruz
    metadatas = results.get("metadatas", [[]])[0]
    response = []
    for doc, meta in zip(docs, metadatas):
        source = meta.get("source", "unknown")
        response.append(f"[source: {source}]\n{doc}")
    return "\n\n".join(response)

@tool
def search_web_for_error(query: str) -> str:
    """
    Eğer 'search_knowledge_base' sonuç vermezse, bu aracı kullanarak hatanın çözümünü 
    StackOverflow, GitHub Issues veya resmi dokümanlarda ara.
    """
    search = TavilySearch(max_results=2)
    return search.invoke({"query": f"Kubernetes Docker {query} solution error fix"})

@tool
def fetch_service_logs(service_name: str, tail_lines: int = 50) -> str:
    """
    OlyKube üzerindeki bir servisin (örn: 'fastapi-backend', 'redis', 'postgres') 
    son log kayıtlarını getirir. Hatanın kök nedenini analiz etmek için kullanılır.
    """
    # Gerçek senaryoda burada Kubernetes API (kubernetes_asyncio) kullanılabilir.
    # Şimdilik mock bir yanıt dönüyoruz.
    mock_logs = {
        "fastapi-backend": "ERROR: sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at 'postgres' failed.",
        "redis": "WARNING: Memory limit reached. Evicting keys.",
    }
    return mock_logs.get(service_name, f"No active logs found for pod/service: {service_name}.")

@tool
def save_error_solution(error_summary: str, root_cause: str, solution_steps: str) -> str:
    """
    ÖNEMLİ: Yeni bir hata başarılı bir şekilde çözüldüğünde bu aracı çağır.
    Bu araç, çözümü vektör veritabanına kaydeder ki sistem gelecekte aynı hatayı kendi başına çözebilsin (Sürekli Öğrenme).
    """
    content = f"Hata Özeti: {error_summary}\nKök Neden: {root_cause}\nÇözüm Adımları:\n{solution_steps}"
    doc_id = f"solved_error_{hash(error_summary)}"
    
    collection.upsert(
        documents=[content],
        ids=[doc_id],
        metadatas=[{"source": "agent_learned_solutions", "type": "bugfix"}]
    )
    return f"Çözüm başarıyla bilgi tabanına eklendi (ID: {doc_id}). Artık sistem bu hatayı hatırlıyor."


# ── 2. AGENT MİMARİSİ ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sen OlyKube projesinin Kıdemli DevOps ve AI Sistemleri Orkestratörüsün.
Görevin sistem hatalarını teşhis etmek, logları analiz etmek ve kalıcı çözümler üretmektir.

Zorunlu İşlem Sıran (Asla Atlama):
1. ANLAMA: 'fetch_service_logs' ile ilgili servisin loglarını çekip hatayı gör.
2. ARAŞTIRMA (İç): 'search_knowledge_base' ile hatanın daha önce çözülüp çözülmediğine bak.
3. ARAŞTIRMA (Dış): Eğer yerelde çözüm yoksa, 'search_web_for_error' ile internette çözüm ara.
4. ÇÖZÜM: Kullanıcıya adım adım hatanın nedenini ve çözümünü açıkla.
5. KAYIT: Eğer yeni bir çözüm ürettiysen, MUTLAKA 'save_error_solution' aracını kullanarak çözümü sisteme öğret.

Her cevabında profesyonel, net ve çözüme odaklı ol."""

async def run_olykube_agent(
    user_message: str,
    thread_id: str,
    model_name: str = "llama3",
    system_prompt: str | None = None,
) -> Dict[str, Any]:
    """Hocanın kodundaki gibi deterministik ve yapılandırılmış (structured) yanıt döner."""

    # Ajanın DB'deki kişiliği, ortak DevOps iş akışının üzerine eklenir
    prompt = SYSTEM_PROMPT
    if system_prompt:
        prompt = f"{SYSTEM_PROMPT}\n\nAjana Özel Talimatlar:\n{system_prompt}"

    # 1. Sağlık Kontrolü
    try:
        async with httpx.AsyncClient() as client:
            await client.get(OLLAMA_BASE_URL, timeout=2.0)
    except httpx.RequestError:
        raise HTTPException(
            status_code=503, 
            detail="Kritik Hata: OlyKube Yapay Zeka (Ollama) motoruna ulaşılamıyor."
        )

    # 2. Agent Hazırlığı
    tools = [fetch_service_logs, search_knowledge_base, search_web_for_error, save_error_solution]
    
    llm = ChatOllama(
        model=model_name,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1 # DevOps işlerinde halüsinasyonu azaltmak için düşük sıcaklık
    )

    async with AsyncPostgresSaver.from_conn_string(SQLALCHEMY_DATABASE_URL) as checkpointer:
        await checkpointer.setup()
        
        agent_app = create_agent(
            llm,
            tools,
            checkpointer=checkpointer,
            system_prompt=prompt
        )

        config = {"configurable": {"thread_id": thread_id}}
        input_message = {"messages": [HumanMessage(content=user_message)]}
        
        # Agent'ı çalıştır
        result = await agent_app.ainvoke(input_message, config=config)
        msgs = result["messages"]

        # 3. HOCANIN YÖNTEMİ: Agent'ın ne yaptığını LLM'e sormak yerine, trace (iz) üzerinden okuyoruz.
        actions = []
        sources = set()
        learned_something = False

        for m in msgs:
            # Yapılan tool çağrılarını (actions) topla
            if getattr(m, "tool_calls", None):
                for call in m.tool_calls:
                    actions.append({"name": call["name"], "args": call.get("args", {})})
            
            # Tool yanıtlarını inceleyerek kaynakları (sources) veya kayıt durumlarını belirle
            if isinstance(m, ToolMessage):
                if m.name == "search_knowledge_base" and isinstance(m.content, str):
                    # İçinde "[source: ...]" geçen yerleri ayıkla
                    found_sources = re.findall(r"\[source: (.*?)\]", m.content)
                    sources.update(found_sources)
                
                if m.name == "save_error_solution":
                    learned_something = True

        return {
            "reply": msgs[-1].content,          # LLM'in son cevabı
            "actions_taken": actions,           # Gerçekte hangi toolları hangi argümanlarla çağırdığı
            "cited_sources": list(sources),     # RAG'den okuduğu dosyalar (örn: "agent_learned_solutions")
            "new_knowledge_saved": learned_something # Bu session'da DB'ye yeni bir çözüm kaydedildi mi?
        }