# src/rag/retriever.py
import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
# Importăm cheia din config-ul tău final
from src.config import OPENAI_API_KEY

DB_PATH = "./data/vector_store"

def get_context(query_text):
    """
    Funcția de căutare pentru Agent.
    Returnează cele mai relevante fragmente de text găsite.
    """
    
    # Verificare de siguranță
    if not os.path.exists(DB_PATH):
        return "Eroare RAG: Baza de date nu există. Rulează ingest.py."

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
        return f"Eroare la căutarea în RAG: {str(e)}"

# Test local
if __name__ == "__main__":
    print(get_context("Mesaj despre cont blocat"))