from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

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

llm_with_tools = llm.bind_tools([multiply, add])

response = llm_with_tools.invoke("15 ile 7'yi çarp")
print(response.tool_calls)

tools_map = {
    "multiply": multiply,
    "add": add
}

tool_call = response.tool_calls[0]
tool_fn = tools_map[tool_call["name"]]
result = tool_fn.invoke(tool_call["args"])
print(f"Sonuç: {result}")