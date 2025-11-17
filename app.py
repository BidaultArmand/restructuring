import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import time
import re
from rag_query import rag_query, build_context
from diagnostic_agents import DiagnosticRouter, generate_full_report, answer_question

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
    ["🧠 Assistant juridique", "📋 Diagnostics professionnels", "📊 Dashboard financier"],
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
# 📋 PAGE 2 — DIAGNOSTICS PROFESSIONNELS
# -------------------------------------------------------------------
elif page == "📋 Diagnostics professionnels":
    st.title("📋 Diagnostics professionnels – E-Center")
    st.caption("Mission Restructuring X-HEC")

    # Initialisation du routeur
    if "router" not in st.session_state:
        st.session_state.router = DiagnosticRouter()

    # Onglets pour les différentes fonctionnalités
    tab1, tab2, tab3 = st.tabs(["📊 Tous les diagnostics", "🎯 Diagnostic spécifique", "❓ Question ciblée"])

    # TAB 1: Générer tous les diagnostics
    with tab1:
        st.markdown("### Génération complète de tous les diagnostics")
        st.info("Cette fonction génère un rapport complet avec les 7 diagnostics : Marché, Produit, Concurrence, Histoire, Process, Chiffre, et Juridique.")

        if st.button("🚀 Générer tous les diagnostics", type="primary", use_container_width=True):
            with st.spinner("Génération en cours... Cela peut prendre quelques minutes."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                diagnostics = {}
                domains = list(st.session_state.router.agents.keys())

                for i, (domain, agent) in enumerate(st.session_state.router.agents.items()):
                    status_text.text(f"Génération du diagnostic : {agent.domain}")
                    progress_bar.progress((i + 1) / len(domains))

                    try:
                        diagnostics[domain] = agent.run()
                    except Exception as e:
                        diagnostics[domain] = f"Erreur lors de la génération : {str(e)}"

                progress_bar.empty()
                status_text.empty()

                st.session_state["all_diagnostics"] = diagnostics
                st.success("✅ Tous les diagnostics ont été générés avec succès !")

        # Afficher les diagnostics générés
        if "all_diagnostics" in st.session_state:
            st.markdown("---")
            st.markdown("## 📑 Rapport complet")

            # Bouton pour télécharger le rapport complet
            full_report = ""
            for domain, content in st.session_state["all_diagnostics"].items():
                agent = st.session_state.router.agents[domain]
                full_report += f"\n\n# {agent.domain.upper()}\n\n{content}\n\n{'='*80}\n"

            st.download_button(
                label="📥 Télécharger le rapport complet (Markdown)",
                data=full_report,
                file_name="diagnostic_complet_ecenter.md",
                mime="text/markdown",
                use_container_width=True
            )

            # Affichage des diagnostics avec expanders
            for domain, content in st.session_state["all_diagnostics"].items():
                agent = st.session_state.router.agents[domain]
                with st.expander(f"📌 {agent.domain}", expanded=False):
                    st.markdown(content)

    # TAB 2: Générer un diagnostic spécifique
    with tab2:
        st.markdown("### Générer un diagnostic spécifique")

        domain_labels = {
            "marche": "🌐 Marché actuel",
            "produit": "🎁 Produit",
            "concurrence": "⚔️ Concurrence",
            "histoire": "📜 Histoire",
            "process": "⚙️ Process",
            "chiffre": "💰 Chiffre",
            "juridique": "⚖️ Juridique"
        }

        selected_domain = st.selectbox(
            "Sélectionnez un domaine de diagnostic :",
            options=list(domain_labels.keys()),
            format_func=lambda x: domain_labels[x]
        )

        if st.button("🎯 Générer ce diagnostic", use_container_width=True):
            agent = st.session_state.router.agents[selected_domain]

            with st.spinner(f"Génération du diagnostic {agent.domain}..."):
                try:
                    diagnostic = agent.run()
                    st.session_state[f"diagnostic_{selected_domain}"] = diagnostic
                    st.success(f"✅ Diagnostic {agent.domain} généré avec succès !")
                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération : {str(e)}")

        # Afficher le diagnostic généré
        if f"diagnostic_{selected_domain}" in st.session_state:
            st.markdown("---")
            agent = st.session_state.router.agents[selected_domain]
            st.markdown(f"## 📋 {agent.domain}")
            st.markdown(st.session_state[f"diagnostic_{selected_domain}"])

            st.download_button(
                label=f"📥 Télécharger le diagnostic {agent.domain}",
                data=st.session_state[f"diagnostic_{selected_domain}"],
                file_name=f"diagnostic_{selected_domain}_ecenter.md",
                mime="text/markdown",
                use_container_width=True
            )

    # TAB 3: Poser une question ciblée
    with tab3:
        st.markdown("### Poser une question ciblée")
        st.info("Posez une question sur un sujet spécifique et l'agent approprié y répondra automatiquement.")

        # Zone de saisie de question
        question = st.text_area(
            "Votre question :",
            placeholder="Ex: Quelle est la situation financière de E-Center ? Qui sont les concurrents principaux ?",
            height=100
        )

        if st.button("🔍 Obtenir une réponse", use_container_width=True):
            if question.strip():
                with st.spinner("Analyse de la question et génération de la réponse..."):
                    # Identifier le domaine
                    domain = st.session_state.router.identify_domain(question)
                    agent = st.session_state.router.agents[domain]

                    st.info(f"🎯 Question routée vers l'agent : **{agent.domain}**")

                    try:
                        # Générer la réponse
                        response = agent.run(custom_query=question)

                        st.markdown("---")
                        st.markdown(f"## 💡 Réponse de l'agent {agent.domain}")
                        st.markdown(response)

                        # Bouton de téléchargement
                        st.download_button(
                            label="📥 Télécharger la réponse",
                            data=f"# Question\n\n{question}\n\n# Réponse ({agent.domain})\n\n{response}",
                            file_name=f"reponse_{domain}_ecenter.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la génération de la réponse : {str(e)}")
            else:
                st.warning("⚠️ Veuillez saisir une question.")

# -------------------------------------------------------------------
# 📊 PAGE 3 — DASHBOARD FINANCIER
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
