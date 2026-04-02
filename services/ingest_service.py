import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("olykube_docs")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=20
)

def ingest_document(text: str, doc_id: str) -> int:
    chunks = splitter.create_documents([text])
    
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk.page_content],
            ids=[f"{doc_id}_chunk_{i}"]
        )
    
    return len(chunks)