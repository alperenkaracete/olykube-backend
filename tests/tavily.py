import os
from langchain_ollama import ChatOllama
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

# Güvenlik: Tavily API anahtarını sisteme tanıtıyoruz
os.environ["TAVILY_API_KEY"] = "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"

# 1. Ajanın Kullanacağı Araçları (Tools) Tanımla
# max_results=2: Ajan internette arama yaptığında en iyi 2 siteyi okusun (Token tasarrufu)
search_tool = TavilySearchResults(max_results=2)
tools = [search_tool]

# 2. Motoru (Beyni) Tanımla
llm = ChatOllama(
    model="qwen3.5:9b", # Qwen, araç kullanma (Tool Calling) konusunda çok zekidir
    base_url="http://192.168.1.6:11434"
)

# 3. LangGraph ReAct Ajanını Derle (Sihir Burada Gerçekleşiyor)
# Bu fonksiyon arka planda ToolNode'ları ve yönlendirmeleri senin yerine çizer.
memory = MemorySaver()
app = create_agent(llm, tools, checkpointer=memory)

# 4. Test Döngüsü
while True:
    user_input = input("Sen: ")
    if user_input.lower() in ["exit", "quit"]:
        break
        
    new_message = {"messages": [HumanMessage(content=user_input)]}
    
    # Motoru çalıştır (thread_id hafızayı tutar)
    final_state = app.invoke(new_message, config={"thread_id": "olykube-test-1"})
    
    # AI'nin son cevabını ekrana bas
    print(f"OlyKube Ajanı: {final_state['messages'][-1].content}")