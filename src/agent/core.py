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

def initialize_agent():
    if not SYSTEM_PROMPT:
        print("WARNING: SYSTEM_PROMPT is missing.")
    GLOBAL_MEMORY.set_system_prompt(SYSTEM_PROMPT)
    print("Agent Initialized.")

def run_scam_analyzer(user_input: str) -> str:
    
    if "Analizează vizual Base64:" in user_input:
        router_input = user_input[:50] 
    elif len(user_input) > 500:
        router_input = user_input[:500]
    else:
        router_input = user_input

    GLOBAL_MEMORY.add_message("user", user_input)
    
    intent = classify_user_intent(router_input)
    messages_to_send = []

    try:
        final_response = ""
        
        if intent == "VISUAL_ANALYSIS":
            try:
                base64_data = user_input.split('Base64: ')[-1].strip()
            except:
                return "Error: invalid image format"

            try:
                image_analysis_result = analyze_image(user_input)
                tech_data = image_analysis_result.get('metadata_heuristic', 'Metadata check unavailable')
            except Exception as tool_err:
                tech_data = f"Tool Error: {tool_err}"

            visual_prompt = (
                f"Analyze the visual attributes of this image for technical inconsistencies common in synthetic media (AI generation).\n\n"
                
                f"### TASK:\n"
                f"Identify visual artifacts such as:\n"
                f"- Illogical physics or lighting shadows.\n"
                f"- Anatomical errors (distorted hands, eyes, teeth, ears).\n"
                f"- Text garbling (nonsensical letters in background).\n"
                f"- 'Plastic' or overly smooth skin textures typical of Midjourney/DALL-E.\n"
                f"- Contextual logic errors.\n\n"
                
                f"### RESPONSE RULES:\n"
                f"1. Do NOT state 'I cannot determine authenticity'. Instead, describe the VISUAL ARTIFACTS you see.\n"
                f"2. If you see specific AI artifacts, categorize the image as **VERDICT: HIGH RISK (AI GENERATED)**.\n"
                f"3. If the image appears to be a standard scam attempt (screenshots of texts, fake bank logos), categorize as **VERDICT: CRITICAL RISK**.\n"
                f"4. If no anomalies are found, categorize as **VERDICT: SAFE**.\n\n"
                
                f"INSTRUCTION: Provide the Verdict first, then list the specific visual anomalies found."
            )
            
            messages_to_send = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": visual_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"}}
                    ]
                }
            ]
            
            model_to_use = "gpt-4o" 

        else:
            model_to_use = LLM_MODEL
            messages_to_send = GLOBAL_MEMORY.get_messages()

            if intent == "LINK_ANALYSIS":
                domain_result = get_domain_age(user_input)
                
                if "SKIP" in domain_result:
                    history = GLOBAL_MEMORY.get_messages()
                    found_prev_link = False
                    
                    for msg in reversed(history[:-1]):
                        if msg['role'] == 'user':
                            prev_result = get_domain_age(msg['content'])
                            if "SKIP" not in prev_result:
                                domain_result = f"[CONTEXT RECOVERED from history]: {prev_result}"
                                found_prev_link = True
                                break
                    
                    if not found_prev_link:
                        fail_prompt = (
                            "\n\n[SYSTEM REPORT]: User asked to check a link, but NO URL was found in current or recent messages.\n"
                            "INSTRUCTION: Reply strictly stating you cannot find a link. Do NOT invent a verdict."
                        )
                        messages_to_send[-1]['content'] += fail_prompt
                        response = LLM_CLIENT.chat.completions.create(model=model_to_use, messages=messages_to_send).choices[0].message.content
                        GLOBAL_MEMORY.add_message("assistant", response)
                        return response

                prompt = (
                    f"\n\n[SYSTEM REPORT]: Domain tool result: {domain_result}\n"
                    f"INSTRUCTION: Provide a STRICT VERDICT based on this."
                )
                messages_to_send[-1]['content'] += prompt

            elif intent == "WEB_SEARCH":
                search_result = searching(user_input)
                prompt = (
                    f"\n\n[SYSTEM REPORT]: Web search results: {search_result}\n"
                    f"INSTRUCTION: Determine if this is a known scam/hoax based on search results."
                )
                messages_to_send[-1]['content'] += prompt

            elif intent == "TEXT_ANALYSIS":
                analysis = analyze_text(user_input)
                domain_check = get_domain_age(user_input)
                prompt = (
                    f"\n\n[SYSTEM REPORT]: Text Analysis: {analysis}\nDomain Check: {domain_check}\n"
                    f"INSTRUCTION: Combine insights. Use STRICT VERDICT format.\n{RISK_VERDICT_TEMPLATE}"
                )
                messages_to_send[-1]['content'] += prompt
            
            else:
                rag_context = get_context(user_input)
                rag_data_str = ""
                if rag_context and "RAG ERROR" not in rag_context:
                    rag_data_str = f"INTERNAL KNOWLEDGE BASE (RAG): {rag_context}\n"

                hybrid_prompt = (
                    f"\n\n[SYSTEM INSTRUCTION - CONVERSATION MODE]:\n"
                    f"{rag_data_str}"
                    f"1. IF asking for definition -> Use RAG.\n"
                    f"2. IF asking follow-up ('Why?', 'Explain') -> Answer based on CONVERSATION HISTORY (Previous analysis).\n"
                    f"3. CRITICAL: Do NOT use the 'VERDICT:' format here. Speak naturally."
                )
                messages_to_send[-1]['content'] += hybrid_prompt

        response = LLM_CLIENT.chat.completions.create(
            model=model_to_use,
            messages=messages_to_send,
            max_tokens=800
        ).choices[0].message.content
        
        final_response = response
        
        if intent == "VISUAL_ANALYSIS":
            history_list = GLOBAL_MEMORY.get_messages()
            
            if history_list:
                history_list[-1]["content"] = "[User uploaded an image for analysis]"
            
        GLOBAL_MEMORY.add_message("assistant", final_response)
        return final_response

    except Exception as e:
        print(f"CRITICAL ERROR in core.py: {e}")
        return "An internal system error occurred. Please check logs."