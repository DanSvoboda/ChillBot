import os
from datetime import datetime, timezone
from pathlib import Path
from textwrap import fill

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

KNOWLEDGE_DIR = Path(os.getenv("KNOWLEDGE_PATH", "data/knowledge"))
VECTOR_STORE_DIR = Path(os.getenv("VECTOR_STORE_PATH", "data/vector_store"))

client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
collection = client.get_or_create_collection("chilli_collection")


class DocumentDB:
    def __init__(self):
        self.collection = collection
        if collection.count() == 0:
            self.start_db()
        
    def create_document(self, document, metadata, doc_id):
        self.collection.upsert(
            documents=[document],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
    def start_db(self):
        if not KNOWLEDGE_DIR.is_dir():
            raise FileNotFoundError(
                f"Knowledge directory does not exist: {KNOWLEDGE_DIR}"
            )

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

        pdf_files = sorted(KNOWLEDGE_DIR.rglob("*.pdf"))
        if not pdf_files:
            raise FileNotFoundError(
                f"No PDF files found in knowledge directory: {KNOWLEDGE_DIR}"
            )

        indexed_at = datetime.now(timezone.utc).isoformat()

        for pdf_path in pdf_files:
            reader = PdfReader(str(pdf_path))
            relative_source = pdf_path.relative_to(KNOWLEDGE_DIR).as_posix()

            for page_number, page in enumerate(reader.pages, start=1):
                page_text = " ".join((page.extract_text() or "").split())
                chunks = text_splitter.split_text(page_text)

                for chunk_index, chunk in enumerate(chunks):
                    chunk_id = (
                        f"{relative_source}:{page_number}:"
                        f"{chunk_index}:{indexed_at}"
                    )
                    self.create_document(
                        document=chunk,
                        metadata={
                            "source": relative_source,
                            "page": page_number,
                            "chunk": chunk_index,
                            "indexed_at": indexed_at,
                        },
                        doc_id=chunk_id,
                    )
                    
    def get_documents(self, query):
        results = self.collection.query(
            query_texts=[query],
            n_results=5
        )
        return results["documents"]

if __name__ == "__main__":
    db = DocumentDB()
    query = "What is the capital of France?"
    results = db.get_documents(query)
    print(f"Results for query '{query}':")
    for i, result in enumerate(results):
        print(f"{i + 1}. {fill(result.strip(), width=88)}")
