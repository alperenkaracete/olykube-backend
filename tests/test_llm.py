from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOllama(
    model="qwen3.5:9b",
    base_url="http://192.168.1.6:11434"
)

response = llm.invoke("İyiyim ben de ne var ne yok?")
print(response.content)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Sen yardımcı bir asistansın. İngilizce cevap ver."),
    ("human", "{input}")
])

chain = prompt | llm

response = chain.invoke({"input": "Python nedir?"})
print(response.content)