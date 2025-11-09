import streamlit as st
from rag_query import rag_query, build_context  # tu gardes ton module tel quel
import time

# === CONFIGURATION DE LA PAGE ===
st.set_page_config(page_title="Assistant juridique DeepSeek", page_icon="⚖️", layout="wide")

# === STYLE CHATGPT-LIKE ===
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background-color: #f9f9fb;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        height: 100vh;
        overflow: hidden;
    }

    /* Zone scrollable contenant les messages */
    .chat-container {
        flex-grow: 1;
        overflow-y: auto;
        padding: 1rem 0.5rem 6rem 0.5rem; /* Espace pour l'input */
    }

    /* Barre d’input fixée en bas */
    .stChatInputContainer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #f9f9fb;
        padding: 1rem 0.5rem;
        box-shadow: 0 -3px 6px rgba(0, 0, 0, 0.05);
        z-index: 100;
    }

    /* Style des messages */
    .stChatMessage {
        padding: 1rem 1.5rem;
        border-radius: 1rem;
        max-width: 80%;
        font-family: "Inter", sans-serif;
        font-size: 1rem;
        line-height: 1.5;
        margin: 0.5rem 0;
    }
    .stChatMessage.user {
        background-color: #DCF8C6;
        margin-left: auto;
    }
    .stChatMessage.assistant {
        background-color: #FFFFFF;
        border: 1px solid #E5E5E5;
        margin-right: auto;
    }

    /* Titres */
    h1, h2 {
        text-align: center;
        font-family: "Inter", sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# === TITRES ===
st.markdown("<h1>Assistant – E center</h1>", unsafe_allow_html=True)
st.markdown("<h2>Mission Restructuring X-HEC</h2>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# === LAYOUT CENTRAL ===
col_gauche, col_centre, col_droite = st.columns([0.2, 0.6, 0.2])
with col_centre:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # === INITIALISATION DE LA SESSION ===
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # === AFFICHAGE DE L'HISTORIQUE ===
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.markdown('</div>', unsafe_allow_html=True)

    # === SAISIE UTILISATEUR ===
    if prompt := st.chat_input("Entrez votre question ici..."):

        # Ajout du message utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # === Étape 1 : Construction du contexte avec barre dynamique ===
        with st.chat_message("assistant"):
            status_text = st.empty()
            progress_bar = st.progress(0)
            status_text.markdown("🔎 Construction du contexte en cours...")

            context = build_context(prompt)
            context_length = len(context)

            # Animation de la barre selon la taille du contexte
            max_chars = 20000  # ajustable selon tes cas
            progress_value = min(context_length / max_chars, 1.0)

            for i in range(int(progress_value * 100)):
                progress_bar.progress(i + 1)
                time.sleep(0.01)

            progress_bar.progress(100)
            status_text.markdown(f"✅ Contexte construit ({context_length} caractères)")

            # === Étape 2 : Appel du modèle RAG ===
            with st.spinner("Hélène réfléchit..."):
                response = rag_query(prompt)

            # Nettoyage et affichage
            progress_bar.empty()
            status_text.empty()

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    # === RÉINITIALISATION ===
    st.markdown("---")
    if st.button("🗑️ Réinitialiser la conversation"):
        st.session_state.messages = []
        st.rerun()
