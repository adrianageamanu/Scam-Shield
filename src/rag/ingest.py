import os
import shutil
from src.config import OPENAI_API_KEY 
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

DATA_PATH = "./data/raw"
DB_PATH = "./data/vector_store"

def create_vector_db():
    print("Starting RAG Ingestion...")

    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY is not loaded in config.py")
        return

    if not os.path.exists(DATA_PATH):
        print(f"Error: Folder {DATA_PATH} does not exist.")
        return

    print(f"Reading files from:: {DATA_PATH}")
    loader = DirectoryLoader(DATA_PATH, glob="*.txt", loader_cls=TextLoader)
    documents = loader.load()

    if not documents:
        print("No .txt documents found! Make sure you have files in data/raw/")
        return
        
    print(f"Loaded {len(documents)} documents.")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    
    print("Generating embeddings with OpenAI...")
    
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
    
    print(f"SUCCESS! Database saved to {DB_PATH}")

if __name__ == "__main__":
    create_vector_db()