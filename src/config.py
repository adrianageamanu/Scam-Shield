import os
from dotenv import load_dotenv
from openai import OpenAI
from openai import APIError

load_dotenv() 

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

def get_llm_client():
    if not OPENAI_KEY:
        raise ValueError(
            "Eroare de configurare: Variabila OPENAI_API_KEY nu a fost gasita. "
            "Verificati .env si setati cheia corecta."
        )
    
    try:
        client = OpenAI(api_key=OPENAI_KEY)
         
        return client
    except APIError as e:
        raise ConnectionError(f"Eroare la conectarea cu OpenAI API. Verifica cheia: {e}")

LLM_CLIENT = get_llm_client()
LLM_MODEL = "gpt-4o-mini"