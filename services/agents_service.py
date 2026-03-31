import os
from langchain_tavily import TavilySearch
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
import httpx
from fastapi import HTTPException

# Tavily anahtarını çevresel değişkenlerden okumak en sağlıklısıdır
os.environ["TAVILY_API_KEY"] = "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"

memory = MemorySaver()

async def run_agent_chat(model_name: str, system_prompt: str, user_message: str, thread_id: str):
    # 1. Araçları ve LLM'i hazırla
# 0. KORUMA KALKANI (Ollama Health Check)
    # Ajanı derlemeden önce Ollama ayakta mı diye 2 saniyelik ufak bir ping atıyoruz
    try:
        async with httpx.AsyncClient() as client:
            await client.get("http://192.168.1.6:11434/", timeout=2.0)
    except httpx.RequestError:
        # Ollama kapalıysa veya ağ bağlantısı yoksa anında işlemi kes!
        raise HTTPException(
            status_code=503, 
            detail="Kritik Hata: OlyKube Yapay Zeka (Ollama) motoruna ulaşılamıyor. Lütfen yerel sunucunun açık olduğundan emin olun."
        )
        
    search_tool = TavilySearch(max_results=2)
    tools = [search_tool]
    
    # Senin yerel Ollama adresin
    llm = ChatOllama(
        model=model_name,
        base_url="http://192.168.1.6:11434"
    )

    # 2. Ajanı o anki sistem istemiyle (System Prompt) oluştur
    # state_modifier: Ajanın kimliğini belirleyen en kritik parametre
    agent_app = create_agent(
        llm, 
        tools, 
        checkpointer=memory,
        system_prompt= system_prompt
    )

    # 3. Mesajı gönder ve yanıtı al
    config = {"configurable": {"thread_id": thread_id}}
    input_message = {"messages": [HumanMessage(content=user_message)]}
    
    result = await agent_app.ainvoke(input_message, config=config)
    
    # Son mesajı döndür
    return result["messages"][-1].content