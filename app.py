import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import time
import re 
from rag_query import rag_query, build_context

# === CONFIGURATION GLOBALE ===
st.set_page_config(page_title="E-Center App", page_icon="⚖️", layout="wide")

# === PROTECTION PAR MOT DE PASSE ===
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False
            st.warning("❌ Mot de passe incorrect.")

    if "authenticated" not in st.session_state:
        st.text_input("Entrez le mot de passe :", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["authenticated"]:
        st.text_input("Entrez le mot de passe :", type="password", on_change=password_entered, key="password")
        return False
    return True

if not check_password():
    st.stop()

# === MENU LATÉRAL (natif Streamlit) ===
st.sidebar.title("📂 Navigation")
page = st.sidebar.radio(
    "Choisis une page :",
    ["🧠 Assistant juridique", "📊 Dashboard financier"],
)

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Réinitialiser la conversation"):
    if "messages" in st.session_state:
        st.session_state.messages = []
    st.rerun()

# -------------------------------------------------------------------
# 🧠 PAGE 1 — ASSISTANT JURIDIQUE
# -------------------------------------------------------------------
if page == "🧠 Assistant juridique":
    st.title("🧠 Assistant – E-Center")
    st.caption("Mission Restructuring X-HEC")

    # Zone de discussion
    chat_container = st.container()
    input_container = st.container()

    with chat_container:
        st.markdown("---")
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    with input_container:
        st.markdown("#### 💬 Pose ta question :")
        prompt = st.text_area(
            "Entrer votre question ici :",
            placeholder="Ex : Quelles sont les étapes d'une procédure de sauvegarde ?",
            label_visibility="collapsed",
            height=100,
        )

        send = st.button("Envoyer", use_container_width=True)

        if send and prompt.strip():
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container.chat_message("user"):
                st.markdown(prompt)

            with chat_container.chat_message("assistant"):
                status_text = st.empty()
                progress_bar = st.progress(0)
                status_text.markdown("🔎 Construction du contexte en cours...")

                context = build_context(prompt)
                context_length = len(context)
                max_chars = 20000
                progress_value = min(context_length / max_chars, 1.0)

                for i in range(int(progress_value * 100)):
                    progress_bar.progress(i + 1)
                    time.sleep(0.01)

                progress_bar.progress(100)
                status_text.markdown(f"✅ Contexte construit ({context_length} caractères)")

                with st.spinner("L'assistant réfléchit..."):
                    response = rag_query(prompt)

                progress_bar.empty()
                status_text.empty()

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# -------------------------------------------------------------------
# 📊 PAGE 2 — DASHBOARD FINANCIER
# -------------------------------------------------------------------
else:
    st.title("📊 Dashboard intelligent – E-Center")

    try:
        with open("data/all_tables.json", "r", encoding="utf-8") as f:
            tables = json.load(f)
    except FileNotFoundError:
        st.error("Fichier 'all_tables.json' introuvable.")
        st.stop()

    question = st.text_input("❓ Pose ta question :", placeholder="Ex : Quelle est l'évolution du chiffre d'affaires ?")

    def ask_agent(question, tables, api_key):
        subset = [{"titre": t["titre"], "extrait": str(t["data"][:2])} for t in tables]
        system_prompt = (
            "Tu es un assistant de data visualisation. "
            "Tu reçois une question utilisateur et une liste de tableaux extraits d'un rapport financier. "
            "Ta tâche : renvoyer les titres des graphiques les plus pertinents pour répondre à la question, "
            "et pour chacun, le type de visualisation le plus adapté parmi : "
            "'bar' (comparaison de valeurs), 'pie' (répartition d'une somme) ou 'line' (évolution temporelle). "
            "Réponds uniquement en JSON sous la forme : "
            "[{'titre': '...', 'pertinence': 1 à 5, 'type': 'bar'|'pie'|'line'}]."
        )

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {question}\n\nDonnées:\n{json.dumps(subset, ensure_ascii=False)}"},
            ],
        }
        headers = {
            "Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"]
            return json.loads(text)
        except Exception as e:
            st.error(f"Erreur agent: {e}")
            return []

    if question:
        if st.button("🔍 Trouver les graphiques pertinents"):
            with st.spinner("Analyse de la question..."):
                priorities = ask_agent(question, tables, st.secrets["DEEPSEEK_API_KEY"])
                if priorities:
                    sorted_titles = [p["titre"] for p in sorted(priorities, key=lambda x: x["pertinence"])]
                    filtered = [t for t in tables if t["titre"] in sorted_titles[:5]]

                    st.success("✅ Graphiques identifiés comme pertinents :")
                    for table in filtered:
                        st.markdown(f"### {table['titre']}")
                        df = pd.DataFrame(table["data"])
                        graph_type = next((p["type"] for p in priorities if p["titre"] == table["titre"]), "bar")

                        df_melt = df.melt(id_vars="label", var_name="variable", value_name="valeur")

                        try:
                            if graph_type == "pie":
                                # === Graphique en camembert ===
                                fig = px.pie(df_melt, names="label", values="valeur", title=table["titre"])
                                fig.update_traces(textinfo="percent+label+value")

                            elif graph_type == "line":
                                # === Graphique d’évolution ===
                                fig = px.line(
                                    df_melt, x="label", y="valeur", color="variable",
                                    markers=True, title=table["titre"]
                                )
                                fig.update_traces(mode="lines+markers+text", text="valeur", textposition="top center")

                            else:
                                # === Graphique en barres par défaut ===
                                fig = px.bar(
                                    df_melt, x="label", y="valeur", color="variable",
                                    text="valeur", title=table["titre"]
                                )
                                fig.update_traces(textposition="outside", texttemplate="%{text:.0f}")
                                fig.update_layout(uniformtext_minsize=8, uniformtext_mode="hide")

                            st.plotly_chart(fig, use_container_width=True)

                        except Exception as e:
                            st.warning(f"Erreur d'affichage pour '{table['titre']}' : {e}")
                            st.dataframe(df)

                else:
                    st.warning("Aucun graphique pertinent trouvé.")
