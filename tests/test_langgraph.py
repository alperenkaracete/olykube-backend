from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain.agents import create_agent

@tool
def multiply(a: int, b: int) -> int:
    """İki sayıyı çarpar."""
    return a * b

@tool
def add(a: int, b: int) -> int:
    """İki sayıyı toplar."""
    return a + b

llm = ChatOllama(
    model="qwen3.5:9b",
    base_url="http://192.168.1.6:11434"
)

agent = create_agent(llm, tools=[multiply, add])

response = agent.invoke({
    "messages": [("human", "15 ile 7'yi çarp, sonra 3 ekle")]
})

print(response["messages"][-1].content)
print(response)