import chromadb

chroma_client = chromadb.HttpClient(host="chromadb", port=8000)
collection = chroma_client.get_or_create_collection("olykube_docs")