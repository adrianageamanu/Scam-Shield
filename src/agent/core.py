from src.config import LLM_CLIENT, LLM_MODEL 
from src.prompts.system_prompts import SYSTEM_PROMPT 
from .memory import GLOBAL_MEMORY
from .router import classify_user_intent 
from src.tools.scam_check import get_domain_age 
from src.tools.text_analysis import analyze_text
from src.tools.web_search import searching
from src.rag.retriever import get_context
from src.prompts.templates import RISK_VERDICT_TEMPLATE
from src.tools.image_analysis import analyze_image

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

    if "Analizează vizual Base64:" in user_input:
        # Dacă este analiză vizuală, trimitem doar primele 30 de caractere
        router_input = user_input[:30]
    elif len(user_input) > 200:
        # Logica veche de trunchiere pentru TEXT_ANALYSIS lung
        router_input = " ".join(user_input.split()[:5])
    else:
        # Input scurt sau conversație
        router_input = user_input

    # 2. Adăugarea inputului COMPLET (inclusiv Base64) în Memorie
    GLOBAL_MEMORY.add_message("user", user_input)
    
    # 3. Clasificarea Intentului (Folosind inputul SCURT)
    intent = classify_user_intent(router_input)
    
    # 4. Preluarea/Izolarea Mesajelor (Logica ta de izolare de memorie)
    if intent in ["LINK_ANALYSIS", "TEXT_ANALYSIS", "VISUAL_ANALYSIS"]:
        # Izolare: Pentru ANALIZĂ, trimite doar promptul SISTEM și mesajul curent (care conține Base64)
        system_prompt = GLOBAL_MEMORY.get_system_prompt()
        messages_to_send = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input} # user_input este Base64-ul complet!
        ]
    else:
        # Pentru CONVERSAȚIE, trimite TOT istoricul.
        messages_to_send = GLOBAL_MEMORY.get_messages()

    try:
        final_response = ""
        
        if intent == "LINK_ANALYSIS":
            # 1. Încercăm să luăm domeniul din mesajul curent
            domain_result = get_domain_age(user_input)
            
            # 2. LOGICA DE CONTEXT (Dacă nu am găsit link acum, căutăm în spate)
            if "SKIP" in domain_result:
                # Luăm tot istoricul
                history = GLOBAL_MEMORY.get_messages()
                
                found_prev_link = False
                
                # Căutăm înapoi (fără ultimul mesaj care e cel curent)
                # reversed() ne ajută să găsim cel mai recent mesaj
                for msg in reversed(history[:-1]):
                    if msg['role'] == 'user':
                        # Încercăm să extragem un link din mesajul vechi
                        prev_result = get_domain_age(msg['content'])
                        
                        # Dacă mesajul vechi NU dă SKIP, înseamnă că avea link!
                        if "SKIP" not in prev_result:
                            domain_result = f"[CONTEXT RECOVERED from previous message]: {prev_result}"
                            found_prev_link = True
                            break
                
                if not found_prev_link:
                    failure_prompt = (
                        "\n\n[SYSTEM REPORT]: The user asked to analyze a link, but NO URL was found in the current message OR the recent conversation history.\n"
                        "INSTRUCTION: Reply directly to the user stating that you cannot find a link to analyze. Do NOT invent a verdict. Do NOT use the Verdict format."
                    )
                    messages_to_send[-1]['content'] += failure_prompt
                    
                    # Facem apelul și returnăm imediat (scurtcircuităm restul logicii)
                    response = LLM_CLIENT.chat.completions.create(
                        model=LLM_MODEL, messages=messages_to_send
                    ).choices[0].message.content
                    GLOBAL_MEMORY.add_message("assistant", response)
                    return response

            # 3. Construim prompt-ul pentru Agent
            prompt = (
                f"\n\n[SYSTEM REPORT]: Domain tool result: {domain_result}\n"
                f"INSTRUCTION: Provide a STRICT VERDICT based on this."
            )
            messages_to_send[-1]['content'] += prompt
            
        elif intent == "GENERAL_KNOWLEDGE":
            # 1. Încercăm să luăm context din RAG (ca înainte)
            rag_context = get_context(user_input)
            rag_data_str = ""
            
            if rag_context and "RAG ERROR" not in rag_context:
                rag_data_str = f"INTERNAL KNOWLEDGE BASE (RAG): {rag_context}\n"

            # 2. Construim un prompt HIBRID (RAG + Chat History)
            # Aici este cheia: Îi spunem explicit cum să trateze întrebările de clarificare.
            hybrid_prompt = (
                f"\n\n[SYSTEM INSTRUCTION - CONVERSATION MODE]:\n"
                f"{rag_data_str}" # Inserăm contextul RAG doar dacă există
                f"1. IF the user asks for a definition or general info (e.g., 'What is phishing?'), use the RAG context above.\n"
                f"2. IF the user asks a FOLLOW-UP question regarding the previous analysis (e.g., 'Why?', 'Are you sure?', 'Explain'), IGNORE RAG and answer based on CONVERSATION HISTORY.\n"
                f"3. CRITICAL: Do NOT use the 'VERDICT:' format in this response. Speak naturally."
            )
            
            messages_to_send[-1]['content'] += hybrid_prompt

        elif intent == "WEB_SEARCH":
            # 1. Agentul executa cautarea pe net
            search_result = searching(user_input)
            
            # 2. Ii dam rezultatul contextului
            web_prompt = (
                f"\n\n[SYSTEM REPORT]: I have performed a web search for: '{user_input}'.\n"
                f"SEARCH RESULTS: {search_result}\n"
                f"INSTRUCTION: Based on these search results, determine if this is a scam/hoax.\n"
                f"If confirmed as a scam, use the STRICT VERDICT format."
            )
            messages_to_send[-1]['content'] += web_prompt
            
        elif intent == "TEXT_ANALYSIS":
            analysis_result_dict = analyze_text(user_input)
            scoring_prompt = (
                f"Utilize this raw risk score and the dangerous keywords found to generate a final security verdict. "
                f"STRICTLY adhere to the format: \n\n{RISK_VERDICT_TEMPLATE}\n\n"
                f"Raw scoring data: {analysis_result_dict}"
            )
            messages_to_send[-1]['content'] = scoring_prompt
        
        elif intent == "VISUAL_ANALYSIS": 
            
            # ⬇️ FIX CRITIC: EXTRAGEREA BASE64-ULUI DIN user_input ⬇️
            try:
                # Extragem Base64-ul complet din șirul de input (după separatorul 'Base64: ')
                base64_data = user_input.split('Base64: ')[-1].strip()
            except:
                # Fallback in caz ca inputul e corupt
                base64_data = "" 
                
            image_analysis_result = analyze_image(user_input)
            
            visual_scoring_prompt = (
                f"You are a digital forensics expert. Strictly analyze the attached image (or URL) to determine whether it was GENERATED BY AI or if it is a real photo modified for phishing purposes. "
                f"Search for AI ARTIFACTS: deformed fingers, strange eyes, abstract backgrounds, and missing metadata. "
                f"Technical tool data: {image_analysis_result['metadata_heuristic']}"
                f"VERIFY VISUAL ACCESS: Start your response with a brief (5-word maximum) description of the image's subject before providing the verdict."
            )
            
            multimodal_content = [
                # Componenta 1: Text (Instrucțiunile)
                {"type": "text", "text": visual_scoring_prompt},
                
                # Componenta 2: Imagine (Datele Base64, acum corect referențiate)
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"}}
            ]
            
            # 2. Reconstruim messages_to_send cu noul conținut:
            system_prompt = GLOBAL_MEMORY.get_system_prompt()
            messages_to_send = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": multimodal_content} # Punem lista de obiecte aici
            ]
        
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
