import streamlit as st
import time
import re  # <--- IMPORT NOU: Biblioteca pentru căutare avansată (Regex)

# --- IMPORTURILE DIN BACKEND ---
try:
    from src.agent.core import run_scam_analyzer, initialize_agent
    BACKEND_LOADED = True
except ImportError as e:
    st.error(f"Critical Error: Could not import backend. Details: {e}")
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
    /* Stiluri Badge */
    .risk-badge-high {
        background-color: #ff4b4b; /* Rosu */
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: bold;
    }
    .risk-badge-safe {
        background-color: #00cc66; /* Verde */
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: bold;
    }
    .risk-badge-medium {
        background-color: #ffcc00; /* Galben */
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
if "agent_initialized" not in st.session_state and BACKEND_LOADED:
    with st.spinner("Booting up AI Sentinel Core..."):
        initialize_agent()
    st.session_state.agent_initialized = True

# Inițializăm istoricul
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am **Sentinel**. 🛡️\n\nPaste any suspicious text, link, or email content here."}
    ]

# --- 4. AFIȘARE ISTORIC ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# --- 5. LOGICA PRINCIPALĂ ---
if prompt := st.chat_input("Paste suspicious text here..."):
    
    # 5.1. Afișăm User Input
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 5.2. Procesare Backend
    with st.chat_message("assistant"):
        
        # A. Status
        with st.status("Sentinel is analyzing...", expanded=True) as status:
            st.write("⚙️ Classifying intent...")
            if BACKEND_LOADED:
                try:
                    full_response_text = run_scam_analyzer(prompt)
                except Exception as e:
                    full_response_text = f"❌ Error: {e}"
            else:
                full_response_text = "Backend not loaded."
            status.update(label="Analysis Complete!", state="complete", expanded=False)

        # B. Determinarea Culorii cu REGEX (Soluția Supremă)
        header_html = ""
        text_for_search = full_response_text.lower() # Doar lowercase, fara replace-uri complicate
        
        # EXPLICATIE REGEX:
        # r"verdict"  -> Cauta cuvantul verdict
        # .* -> Orice caractere intre ele (spatii, doua puncte, stelute)
        # (high|...)  -> Unul dintre cuvintele tinta
        
        # 1. Cautam HIGH / CRITICAL
        if re.search(r"verdict.*(?:high|critical|scam|phishing|dangerous)", text_for_search):
            header_html = '## <span class="risk-badge-high">⚠️ HIGH RISK DETECTED</span>'
        
        # 2. Cautam SAFE / LOW
        elif re.search(r"verdict.*(?:safe|low|legit)", text_for_search):
            header_html = '## <span class="risk-badge-safe">✅ SAFE</span>'
        
        # 3. Cautam MEDIUM
        elif re.search(r"verdict.*(?:medium|suspicious)", text_for_search):
            header_html = '## <span class="risk-badge-medium">⚠️ SUSPICIOUS / MEDIUM RISK</span>'
            
        else:
            # Daca nu gasim cuvantul "Verdict", nu afisam badge (e doar chat)
            pass

        # C. Afișare
        if header_html:
            st.markdown(header_html, unsafe_allow_html=True)
        
        # D. Streaming
        def stream_data():
            # split(' ') e important ca sa pastram Enter-urile (\n)
            for word in full_response_text.split(" "):
                yield word + " "
                time.sleep(0.015) 

        st.write_stream(stream_data)

    # 5.3. Salvare
    combined_response = f"{header_html}\n\n{full_response_text}"
    st.session_state.messages.append({"role": "assistant", "content": combined_response})