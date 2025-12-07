import streamlit as st
import time
import re  # <--- IMPORT NOU: Biblioteca pentru căutare avansată (Regex)
import base64
from PIL import Image # NOU
import io # NOU
import uuid

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
    .risk-badge-high { background-color: #ff4b4b; color: white; padding: 4px 12px; border-radius: 16px; font-weight: bold; }
    .risk-badge-safe { background-color: #00cc66; color: white; padding: 4px 12px; border-radius: 16px; font-weight: bold; }
    .risk-badge-medium { background-color: #ffcc00; color: #1e1e1e; padding: 4px 12px; border-radius: 16px; font-weight: bold; }
    
    /* Stil pentru butoanele din sidebar */
    .chat-btn { width: 100%; text-align: left; }
</style>
""", unsafe_allow_html=True)

# --- 2. GESTIONAREA STĂRII (MULTIPLE CHATS) ---

# Funcție pentru a crea un chat nou
def create_new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.all_chats[new_id] = [
        {"role": "assistant", "content": "Hello! I am **Sentinel**. 🛡️\n\nPaste any suspicious text, link, or email content here."}
    ]
    st.session_state.chat_titles[new_id] = "New Chat"
    st.session_state.active_chat_id = new_id

# Funcție pentru a șterge chat-ul curent
def delete_current_chat():
    current_id = st.session_state.active_chat_id
    if current_id in st.session_state.all_chats:
        del st.session_state.all_chats[current_id]
        del st.session_state.chat_titles[current_id]
    
    # Dacă mai există chat-uri, selectăm ultimul, altfel creăm unul nou
    if st.session_state.all_chats:
        st.session_state.active_chat_id = list(st.session_state.all_chats.keys())[0]
    else:
        create_new_chat()

# Inițializare stări globale
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}
if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {}
if "active_chat_id" not in st.session_state:
    create_new_chat() # Creăm primul chat default

# Selectăm chat-ul activ
active_chat_id = st.session_state.active_chat_id
current_messages = st.session_state.all_chats[active_chat_id]

# --- 3. SIDEBAR (ISTORIC & CONTROL) ---
with st.sidebar:
    st.title("🛡️ Sentinel Control")
    st.markdown("Connected to **Sentinel Core**.")
    
    # Buton mare de "New Chat"
    if st.button("➕ New Analysis", type="primary", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.divider()
    st.markdown("### 🗂️ Recent Scans")

    # Listăm toate chat-urile ca butoane
    # Folosim reversed() ca să apară cele mai noi sus
    for chat_id in reversed(list(st.session_state.all_chats.keys())):
        title = st.session_state.chat_titles.get(chat_id, "New Chat")
        
        # Dacă este chat-ul activ, îl evidențiem
        if chat_id == active_chat_id:
            if st.button(f"📂 {title}", key=chat_id, use_container_width=True, type="secondary"):
                pass # E deja selectat
        else:
            if st.button(f"📄 {title}", key=chat_id, use_container_width=True):
                st.session_state.active_chat_id = chat_id
                st.rerun()

    st.divider()
    
    # Buton de Ștergere pentru chat-ul ACTIV
    if st.button("🗑️ Delete Current Chat", type="primary"):
        delete_current_chat()
        st.rerun()

# --- 4. INITIALIZARE AGENT ---
if "agent_initialized" not in st.session_state and BACKEND_LOADED:
    with st.spinner("Booting up AI Sentinel Core..."):
        initialize_agent()
    st.session_state.agent_initialized = True

# --- 5. AFIȘARE ISTORIC (Din chat-ul curent) ---
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

if 'image_is_new' not in st.session_state:
    st.session_state['image_is_new'] = False
if 'last_image_name' not in st.session_state:
    st.session_state['last_image_name'] = None

uploaded_file = st.file_uploader("🖼️ Încarcă imaginea (pentru analiza AI/Deepfake):", 
                                 type=["png", "jpg", "jpeg"], 
                                 key="image_uploader")

if uploaded_file is not None and uploaded_file.name != st.session_state.get('last_image_name'):
    st.session_state['image_is_new'] = True

if uploaded_file is not None and BACKEND_LOADED and st.session_state['image_is_new']:
    
    image_bytes = uploaded_file.read()
    
    try:
        original_image = Image.open(io.BytesIO(image_bytes))
        max_size = 1024 
        original_image.thumbnail((max_size, max_size))
        
        buffer = io.BytesIO()
        original_image.save(buffer, format="JPEG", quality=75)
        
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
    except Exception as e:
        st.error(f"Eroare la redimensionare: {e}. Asigură-te că imaginea este validă.")
        st.session_state['image_is_new'] = False
        st.rerun() 
        base64_image = None
        
    if base64_image:
        special_agent_prompt = f"Analizează vizual Base64: {base64_image}" 
        
        user_message_content = f"Imaginea **{uploaded_file.name}** a fost încărcată pentru analiză."
        st.session_state.messages.append({"role": "user", "content": user_message_content})
        
        with st.chat_message("user"):
            st.markdown(user_message_content)
            # Afișăm imaginea compresată pentru UX
            st.image(original_image, caption=uploaded_file.name, width=250)
            
        # 4. Procesare Agent
        with st.chat_message("assistant"):
            with st.spinner("Analiză Multimodală în curs..."):
                try:
                    full_response_text = run_scam_analyzer(special_agent_prompt)
                except Exception as e:
                    # Dacă LLM-ul dă eroare, o prindem aici
                    full_response_text = f"❌ Eroare Agent LLM: Analiza a eșuat. {e}"
            
            # 5. Afișare răspuns și salvare
            # (Aici trebuie să incluzi și logica ta de Regex pentru badge-uri)
            st.markdown(full_response_text)
            st.session_state.messages.append({"role": "assistant", "content": full_response_text})
            
        # 6. CURĂȚAREA STĂRII: Oprește bucla și marchează ca procesat
        st.session_state['image_is_new'] = False
        st.session_state['last_image_name'] = uploaded_file.name
        
        # Forțează reîncărcarea finală pentru a actualiza corect UI-ul
        st.rerun()

if prompt := st.chat_input("Paste suspicious text here..."):
    
    # A. Actualizăm titlul chat-ului dacă e primul mesaj
    if len(current_messages) == 1: # Doar mesajul de bun venit
        # Luăm primele 4 cuvinte din mesajul user-ului ca titlu
        short_title = " ".join(prompt.split()[:4]) + "..."
        st.session_state.chat_titles[active_chat_id] = short_title

    # B. Afișăm User Input
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # C. Salvăm în Chat-ul ACTIV
    st.session_state.all_chats[active_chat_id].append({"role": "user", "content": prompt})

    # D. Procesare Backend
    with st.chat_message("assistant"):
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

        # Logica Regex pentru Culori
        header_html = ""
        text_for_search = full_response_text.lower()
        
        if re.search(r"verdict.*(?:high|critical|scam|phishing|dangerous)", text_for_search):
            header_html = '## <span class="risk-badge-high">⚠️ HIGH RISK DETECTED</span>'
        elif re.search(r"verdict.*(?:safe|low|legit)", text_for_search):
            header_html = '## <span class="risk-badge-safe">✅ SAFE</span>'
        elif re.search(r"verdict.*(?:medium|suspicious)", text_for_search):
            header_html = '## <span class="risk-badge-medium">⚠️ SUSPICIOUS / MEDIUM RISK</span>'

        if header_html:
            st.markdown(header_html, unsafe_allow_html=True)
        
        def stream_data():
            for word in full_response_text.split(" "):
                yield word + " "
                time.sleep(0.015) 

        st.write_stream(stream_data)

    # E. Salvare Răspuns în Chat-ul ACTIV
    combined_response = f"{header_html}\n\n{full_response_text}"
    st.session_state.all_chats[active_chat_id].append({"role": "assistant", "content": combined_response})
    
    # Forțăm refresh la sidebar ca să se actualizeze titlul
    st.rerun()