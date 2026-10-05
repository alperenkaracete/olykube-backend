import chromadb
from core.config import CHROMA_HOST, CHROMA_PORT

chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection = chroma_client.get_or_create_collection("olykube_docs")