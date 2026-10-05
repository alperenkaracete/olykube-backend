import os
from dotenv import load_dotenv

# Yerelde .env dosyasını okur. Docker/K8s'te değişkenler zaten ortamdan gelir
# (env_file / secretRef); load_dotenv mevcut değerleri ezmez.
load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"'{name}' ortam değişkeni tanımlı değil. .env.example dosyasına bakın.")
    return value


SQLALCHEMY_DATABASE_URL = _required("SQLALCHEMY_DATABASE_URL")
SECRET_KEY = _required("SECRET_KEY")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# TavilySearch anahtarı doğrudan TAVILY_API_KEY ortam değişkeninden okur
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
