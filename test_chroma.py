import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.create_collection("test")

# Birkaç döküman ekle
collection.add(
    documents=[
        "Kubernetes pod'ları container'ları gruplar.",
        "Docker image'ları katmanlardan oluşur.",
        "Redis in-memory bir veritabanıdır.",
        "FastAPI Python ile yazılmış modern bir web framework'üdür."
    ],
    ids=["doc1", "doc2", "doc3", "doc4"]
)

# Semantic search yap
results = collection.query(
    query_texts=["container orkestrasyon"],
    n_results=2
)

print(results["documents"])