import os
from langchain_tavily import TavilySearch
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import httpx
from fastapi import HTTPException
import chromadb
from langchain_core.tools import tool
from database import SQLALCHEMY_DATABASE_URL
from services.chroma_client import collection

# Tavily anahtarını çevresel değişkenlerden okumak en sağlıklısıdır
os.environ["TAVILY_API_KEY"] = "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"

memory = MemorySaver()

async def run_agent_chat(model_name: str, system_prompt: str, user_message: str, thread_id: str):
    
    # 0. Ollama Health Check
    try:
        async with httpx.AsyncClient() as client:
            await client.get("http://192.168.1.6:11434/", timeout=2.0)
    except httpx.RequestError:
        raise HTTPException(
            status_code=503, 
            detail="Kritik Hata: OlyKube Yapay Zeka (Ollama) motoruna ulaşılamıyor."
        )
    
    # 1. PostgreSQL checkpointer
    async with AsyncPostgresSaver.from_conn_string(SQLALCHEMY_DATABASE_URL) as checkpointer:
        await checkpointer.setup()
        
        search_tool = TavilySearch(max_results=2)
        tools = [search_knowledge_base, search_tool]
        
        llm = ChatOllama(
            model=model_name,
            base_url="http://192.168.1.6:11434"
        )

        agent_app = create_agent(
            llm, 
            tools, 
            checkpointer=checkpointer,
            system_prompt=system_prompt,
            debug=True
        )

        config = {"configurable": {"thread_id": thread_id}}
        input_message = {"messages": [HumanMessage(content=user_message)]}
        
        result = await agent_app.ainvoke(input_message, config=config)
        
        return result["messages"][-1].content

@tool
def search_knowledge_base(query: str) -> str:
    """Yerel bilgi tabanında arama yapar. Önce buraya bak."""
    results = collection.query(
        query_texts=[query],
        n_results=2
    )
    
    docs = results["documents"][0]
    if not docs:
        return "Bilgi tabanında ilgili bilgi bulunamadı."
    
    return "\n".join(docs)