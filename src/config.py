import os
from dotenv import load_dotenv
from openai import OpenAI
from openai import APIError

load_dotenv() 

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_llm_client():
    if not OPENAI_API_KEY:
        raise ValueError(
            "Configuration Error: The OPENAI_API_KEY variable was not found. "
            "Verify the .env file and set the correct key."
        )
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
         
        return client
    except APIError as e:
        raise ConnectionError(f"Error connecting to the OpenAI API. Verify the key: {e}")

LLM_CLIENT = get_llm_client()
LLM_MODEL = "gpt-4o-mini"