from langchain_text_splitters import RecursiveCharacterTextSplitter
from services.chroma_client import collection

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