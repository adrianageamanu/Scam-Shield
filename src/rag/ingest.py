# src/rag/ingest.py
import os
import shutil
# Importăm cheia din configurația pe care ai stabilit-o
from src.config import OPENAI_API_KEY 
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# Definim căile presupunând că rulăm scriptul din rădăcina proiectului
# (Comanda python -m src.rag.ingest)
DATA_PATH = "./data/raw"
DB_PATH = "./data/vector_store"

def create_vector_db():
    print("Starting RAG Ingestion...")

    # 1. Validare Config
    if not OPENAI_API_KEY:
        print("EROARE: OPENAI_API_KEY nu este încărcat în config.py")
        return

    # 2. Încărcare Date
    if not os.path.exists(DATA_PATH):
        print(f"Eroare: Folderul {DATA_PATH} nu există.")
        return

    print(f"Citesc fișiere din: {DATA_PATH}")
    loader = DirectoryLoader(DATA_PATH, glob="*.txt", loader_cls=TextLoader)
    documents = loader.load()

    if not documents:
        print("Nu am găsit documente .txt! Asigură-te că ai fișiere în data/raw/")
        return
        
    print(f"Am încărcat {len(documents)} documente.")

    # 3. Procesare (Split)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    
    # 4. Generare Embeddings
    print("Generez embeddings cu OpenAI...")
    
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)

    embedding_function = OpenAIEmbeddings(
        model="text-embedding-3-small", 
        api_key=OPENAI_API_KEY
    )
    
    db = Chroma.from_documents(
        documents=chunks, 
        embedding=embedding_function, 
        persist_directory=DB_PATH
    )
    
    print(f"SUCCES! Baza de date salvată în {DB_PATH}")

if __name__ == "__main__":
    create_vector_db()