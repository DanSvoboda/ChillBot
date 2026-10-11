import chromadb
import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

client = chromadb.PersistentClient("/data/chroma_db")
collection = client.get_or_create_collection("chilli_collection")

class DocumentDB:
    def __init__(self):
        if collection.count() == 0:
            self.start_db(collection)
        
    def create_document(self, document, metadata, doc_id):
        self.collection.add(
            documents=[document],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
    def start_db(self, collection):
        if collection.count() == 0:
            loader = PyPDFDirectoryLoader("/data/knowledge")
            raw_documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            for doc in raw_documents:
                chunks = text_splitter.split_text(doc.page_content)
                for i, chunk in enumerate(chunks):
                    self.create_document(
                        document=chunk,
                        metadata={"source": "knowledge"},
                        doc_id=f"{doc.metadata['source']}_{i}"
                    )
                    
    def get_documents(self, query):
        results = self.collection.query(
            query_texts=[query],
            n_results=5
        )
        return results['documents']

    
