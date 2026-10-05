import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Kalıcı ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("olykube_docs")

# Test dökümanı — ileride PDF/dosyadan okuyacağız
documents = [
    """
    Kubernetes, container'ları otomatik deploy eden, ölçeklendiren 
    ve yöneten açık kaynaklı bir sistemdir. Pod'lar bir veya daha 
    fazla container barındırır. Deployment'lar pod'ların istenen 
    sayıda çalışmasını garanti eder.
    """,
    """
    Zero Trust mimarisi hiçbir kullanıcıya veya servise varsayılan 
    olarak güvenmez. Her istek doğrulanmalıdır. Kubernetes'te 
    Network Policy ve RBAC ile Zero Trust uygulanabilir.
    """,
    """
    Redis in-memory bir veritabanıdır. Cache, session yönetimi 
    ve rate limiting için kullanılır. Pub/Sub özelliği ile 
    message broker olarak da çalışabilir.
    """
]

# Chunk'lara böl
splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=20
)

chunks = splitter.create_documents(documents)
print(f"Toplam chunk sayısı: {len(chunks)}")

# ChromaDB'ye kaydet
for i, chunk in enumerate(chunks):
    collection.add(
        documents=[chunk.page_content],
        ids=[f"chunk_{i}"]
    )

print("Tüm chunk'lar kaydedildi.")

# Test: semantic search
results = collection.query(
    query_texts=["kubernetes güvenlik"],
    n_results=2
)

print("\nArama sonuçları:")
for doc in results["documents"][0]:
    print(f"- {doc[:100]}...")