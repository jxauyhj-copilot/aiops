from config.settings import settings
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import os

class KnowledgeRetriever:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.db = None
        self.load_db()

    def load_db(self):
        path = settings.VECTOR_DB_PATH
        if os.path.exists(path):
            try:
                self.db = FAISS.load_local(path, self.embeddings, allow_dangerous_deserialization=True)
            except Exception as e:
                print(f"Error loading DB: {e}")
        else:
            print("Vector DB not found. Please run ingest.py first.")

    def search(self, query: str, k: int = 3):
        if not self.db:
            return ["Vector DB not initialized."]
        
        docs = self.db.similarity_search(query, k=k)
        results = []
        for doc in docs:
            source = doc.metadata.get('source', 'Unknown Source')
            results.append(f"Source: {source}\nContent: {doc.page_content}")
        return results
