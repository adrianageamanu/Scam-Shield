from src.config import LLM_CLIENT, LLM_MODEL 
from src.prompts.system_prompts import SYSTEM_PROMPT 
from .memory import GLOBAL_MEMORY
from .router import classify_user_intent 

# Lista de unelte (tools) disponibile Agentului.
AVAILABLE_TOOLS = [] 


def initialize_agent():
    if not SYSTEM_PROMPT:
        print("WARNING: SYSTEM_PROMPT is missing. Agent behavior will be undefined.")
    
    GLOBAL_MEMORY.set_system_prompt(SYSTEM_PROMPT)
    print("Agent Initialized. Memory Set.")


def run_scam_analyzer(user_input: str) -> str:
    
    GLOBAL_MEMORY.add_message("user", user_input)
    
    intent = classify_user_intent(user_input)
    messages_to_send = GLOBAL_MEMORY.get_messages()

    try:
        final_response = ""
        
        if intent == "LINK_ANALYSIS":
            # Optiunea 1: Necesita o unealta (tool) pentru verificare externa
            # TODO: Aici se va integra logica de Tool Calling reală
            final_response = (
                f"Detected intent: **{intent}**. Running URL security check..."
            )
            
        elif intent == "GENERAL_KNOWLEDGE":
            final_response = LLM_CLIENT.chat.completions.create(
                model=LLM_MODEL,
                messages=messages_to_send,
            ).choices[0].message.content
            
        else:
            final_response = LLM_CLIENT.chat.completions.create(
                model=LLM_MODEL,
                messages=messages_to_send,
            ).choices[0].message.content

        GLOBAL_MEMORY.add_message("assistant", final_response)
        
        return final_response

    except Exception as e:
        error_msg = f"CRITICAL ERROR: Failed to run LLM agent. Exception: {e}"
        print(error_msg)
        
        user_facing_error = "An internal technical issue occurred. Please check the API key or system logs."
        
        GLOBAL_MEMORY.add_message("assistant", f"Internal Error: {e}")
        return user_facing_error
