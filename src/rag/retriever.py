import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from src.config import OPENAI_API_KEY

DB_PATH = "./data/vector_store"

def get_context(query_text):
    if not os.path.exists(DB_PATH):
        return "RAG Error: Database does not exist. Run ingest.py."

    try:
        # Conectare la DB
        embedding_function = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=OPENAI_API_KEY
        )
        db = Chroma(persist_directory=DB_PATH, embedding_function=embedding_function)
        
        # Căutare
        results = db.similarity_search(query_text, k=3)
        
        if not results:
            return ""

        # Formatare text pentru AI
        context_text = ""
        for doc in results:
            context_text += f"{doc.page_content}\n---\n"
            
        return context_text

    except Exception as e:
        return f"Error during RAG search: {str(e)}"

# Test local
if __name__ == "__main__":
    print(get_context("Message about blocked account"))