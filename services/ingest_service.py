from langchain_text_splitters import RecursiveCharacterTextSplitter
from services.chroma_client import collection

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

def ingest_document(text: str, doc_id: str) -> int:
    chunks = splitter.create_documents([text])
    
    documents = []
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(chunks):
        documents.append(chunk.page_content)
        
        metadatas.append({
            "source": doc_id,
            "chunk_index": i,
            "bootcamp": "olykube" 
        })
        
        ids.append(f"{doc_id}_chunk_{i}")
        
    if documents:
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    return len(chunks)