from src.config import LLM_CLIENT, LLM_MODEL 
from src.prompts.system_prompts import SYSTEM_PROMPT 
from .memory import GLOBAL_MEMORY
from .router import classify_user_intent 
from src.tools.scam_check import get_domain_age 
from src.tools.text_analysis import analyze_text
from src.rag.retriever import get_context
from src.prompts.templates import RISK_VERDICT_TEMPLATE

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
            domain_result = get_domain_age(user_input)
            interpretation_prompt = (
                f"Analyze the following raw domain verification result. "
                f"Formulate a concise security verdict based on the provided data. "
                f"Raw tool result: {domain_result}"
            )
            
        elif intent == "GENERAL_KNOWLEDGE":
            rag_context = get_context(user_input)
            if rag_context and "RAG ERROR" not in rag_context:
                rag_instruction = f"Use the following internal context fragments (RAG) to answer the user's query: "
                messages_to_send[-1]['content'] += f"\n\n{rag_instruction}\n{rag_context}"
            
        elif intent == "TEXT_ANALYSIS":
            analysis_result_dict = analyze_text(user_input)
            scoring_prompt = (
                f"Utilize this raw risk score and the dangerous keywords found to generate a final security verdict. "
                f"STRICTLY adhere to the format: \n\n{RISK_VERDICT_TEMPLATE}\n\n"
                f"Raw scoring data: {analysis_result_dict}"
            )
            messages_to_send[-1]['content'] = scoring_prompt
        
        else:
            pass

        response = LLM_CLIENT.chat.completions.create(
            model=LLM_MODEL,
            messages=messages_to_send,
        ).choices[0].message.content
        
        final_response = response
        GLOBAL_MEMORY.add_message("assistant", final_response)
        return final_response

    except Exception as e:
        error_msg = f"CRITICAL ERROR: Failed to run LLM agent. Exception: {e}"
        print(error_msg)
        
        user_facing_error = "An internal technical issue occurred. Please check the API key or system logs."
        
        GLOBAL_MEMORY.add_message("assistant", f"Internal Error: {e}")
        return user_facing_error
