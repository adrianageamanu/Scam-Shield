from src.config import LLM_CLIENT, LLM_MODEL 
from src.prompts.system_prompts import ROUTER_PROMPT 

def classify_user_intent(user_input: str) -> str:

    if "Analizează vizual Base64:" in user_input:
        return "VISUAL_ANALYSIS"
    
    VALID_INTENTS = ["LINK_ANALYSIS", "TEXT_ANALYSIS", "GENERAL_KNOWLEDGE", "VISUAL_ANALYSIS", "WEB_SEARCH"]
    
    messages_to_send = [
        {"role": "system", "content": ROUTER_PROMPT},
        {"role": "user", "content": user_input}
    ]

    try:
        response = LLM_CLIENT.chat.completions.create(
            model=LLM_MODEL,
            messages=messages_to_send,
            max_tokens=20,
            temperature=0.0
        )
        
        intent = response.choices[0].message.content.strip().upper()
        
        if intent in VALID_INTENTS:
            return intent
        else:
            return "GENERAL_KNOWLEDGE" 

    except Exception as e:
        print(f"Eroare la rutarea intentiei (Fall-back la cunoștințe generale): {e}")
        return "GENERAL_KNOWLEDGE"