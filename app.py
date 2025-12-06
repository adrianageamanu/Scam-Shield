import streamlit as st
import time

# --- IMPORTURILE DIN BACKEND ---
# Aici facem legătura cu logica colegilor tăi
try:
    from src.agent.core import run_scam_analyzer, initialize_agent
    BACKEND_LOADED = True
except ImportError as e:
    st.error(f"Critical Error: Could not import backend. Make sure you are running from the root folder. Details: {e}")
    BACKEND_LOADED = False

# --- 1. CONFIGURARE PAGINĂ ---
st.set_page_config(
    page_title="Sentinel AI - Public Defender",
    page_icon="🛡️",
    layout="centered"
)

# CSS Custom
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .stChatMessage[data-testid="stChatMessageAvatarUser"] {
        background-color: #2b313e;
    }
    .risk-badge-high {
        background-color: #ff4b4b;
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: bold;
    }
    .risk-badge-safe {
        background-color: #00cc66;
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: bold;
    }
    .risk-badge-medium {
        background-color: #ffcc00;
        color: #1e1e1e;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Sentinel Control")
    st.success("🟢 System Online")
    st.markdown("Connected to **Sentinel Core**.")
    
    if st.button("🗑️ Clear History", type="primary"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.caption("Powered by OpenAI GPT-4o & LangChain")

# --- 3. INITIALIZARE AGENT ---
# Rulăm funcția de start a agentului o singură dată
if "agent_initialized" not in st.session_state and BACKEND_LOADED:
    with st.spinner("Booting up AI Sentinel Core..."):
        initialize_agent()
    st.session_state.agent_initialized = True
    
# Inițializăm istoricul chat-ului
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am **Sentinel**. 🛡️\n\nPaste any suspicious text, link, or email content here. I will analyze it using my cybersecurity tools."}
    ]

# --- 4. AFIȘARE ISTORIC ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# --- 5. LOGICA PRINCIPALĂ (CHAT) ---
if prompt := st.chat_input("Paste suspicious text here..."):
    
    # 5.1. Afișăm User Input
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 5.2. Procesare Backend
    with st.chat_message("assistant"):
        
        # A. Animație de Gândire (Reală acum!)
        with st.status("Sentinel is analyzing...", expanded=True) as status:
            st.write("⚙️ Classifying intent...")
            # Aici apelăm funcția reală din backend!
            # Aceasta poate dura 2-5 secunde
            if BACKEND_LOADED:
                try:
                    # --- APELUL CĂTRE BACKEND ---
                    full_response_text = run_scam_analyzer(prompt)
                    # ----------------------------
                except Exception as e:
                    full_response_text = f"❌ Error contacting AI Core: {e}"
            else:
                full_response_text = "Backend not loaded."
            
            status.update(label="Analysis Complete!", state="complete", expanded=False)

       # B. Determinarea Culorii (LOGICĂ ULTRA-ROBUSTĂ)
        header_html = ""
        # Curățăm textul de caractere markdown care pot încurca căutarea (*, #)
        clean_text = full_response_text.lower().replace("*", "").replace("#", "")
        
        # 1. Definim declanșatorii (Triggers)
        # Căutăm expresii specifice
        critical_triggers = ["verdict: critical", "verdict: high", "high risk detected", "phishing attempt"]
        safe_triggers = ["verdict: safe", "verdict: low", "safe to open", "legitimate message"]
        medium_triggers = ["verdict: medium", "verdict: suspicious", "suspicious activity"]

        # 2. Verificăm prioritatea (Roșu -> Verde -> Galben)
        if any(trig in clean_text for trig in critical_triggers):
            header_html = '## <span class="risk-badge-high">⚠️ HIGH RISK DETECTED</span>'
            
        elif any(trig in clean_text for trig in safe_triggers):
            header_html = '## <span class="risk-badge-safe">✅ PROBABLY SAFE</span>'
            
        elif any(trig in clean_text for trig in medium_triggers):
            header_html = '## <span class="risk-badge-medium">⚠️ SUSPICIOUS / MEDIUM RISK</span>'
            
        else:
            # Fallback inteligent: Dacă textul e lung și nu are verdict, e probabil Chat simplu
            # Dar dacă userul a dat un link, poate vrem să arătăm "Analizat"
            pass

        # C. Afișare Header Static (fără glitch)
        st.markdown(header_html, unsafe_allow_html=True)
        
        # D. Streaming pentru corpul mesajului
        message_placeholder = st.empty()
        displayed_text = ""
        
        # Curățăm textul: Uneori LLM-ul repetă titlul "VERDICT: HIGH RISK". 
        # Putem să-l afișăm direct totuși, e mai sigur.
        for chunk in full_response_text.split():
            displayed_text += chunk + " "
            message_placeholder.markdown(displayed_text + "▌")
            time.sleep(0.02) # Viteza de scriere
            
        message_placeholder.markdown(displayed_text)

    # 5.3. Salvare în Istoric (Header + Text)
    # Salvăm totul ca un singur string Markdown pentru simplitate la redesenare
    combined_response = f"{header_html}\n\n{full_response_text}"
    st.session_state.messages.append({"role": "assistant", "content": combined_response})