import os
import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI  # DeepSeek utilise une interface OpenAI-compatible
from dotenv import load_dotenv

load_dotenv()


# === CONFIG ===
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
INDEX_PATH = "index_debug.faiss"
CHUNKS_PATH = "chunks_debug.json"
TABLES_PATH = "data/all_tables.json"
TOP_K = 10  # Réduit de 20 à 10 pour éviter le dépassement de contexte


API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not API_KEY:
    raise ValueError("⚠️ DEEPSEEK_API_KEY non définie.")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com"  # ✅ pas de /v1 ici
)

LLM_MODEL = "deepseek-chat"

# === INITIALISATION ===
print("🔹 Chargement du modèle d'embedding et de l'index...")
model = SentenceTransformer(MODEL_NAME)
index = faiss.read_index(INDEX_PATH)

with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

with open(TABLES_PATH, "r", encoding="utf-8") as f:
    tables = json.load(f)

print(f"✅ Index chargé ({len(chunks)} chunks, {len(tables)} entrées tabulaires)")

# Initialisation du client DeepSeek
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com/v1"  # endpoint officiel DeepSeek
)

# === FONCTIONS ===
def retrieve(query, top_k=TOP_K):
    """Recherche les chunks les plus proches de la requête."""
    q_emb = model.encode([query], convert_to_numpy=True)
    distances, indices = index.search(q_emb, top_k)
    return [chunks[i] for i in indices[0]]

import os

def get_tabular_info(doc_id):
    """Associe les infos tabulaires au document, en tolérant les variations de nom."""
    results = []
    doc_id_clean = os.path.splitext(doc_id.lower().strip())[0]
    for t in tables:
        src_clean = os.path.splitext(t.get("source", "").lower().strip())[0]
        if src_clean == doc_id_clean:
            results.append(t)
    return results

def build_context(query):
    """Construit le contexte complet à envoyer au LLM."""
    results = retrieve(query)
    context = ""
    for r in results:
        context += f"\n---\n📄 {r['doc_id']}\n{r['text']}\n"
        tab = get_tabular_info(r["doc_id"])
        if tab:
            context += f"\n📊 Données tabulaires : {json.dumps(tab, ensure_ascii=False, indent=2)}\n"
    return context.strip()



def ask_deepseek(query, context):
    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un assistant juridique expert en restructuration d'entreprise. "
                "Utilise uniquement les informations du contexte fourni pour répondre précisément."
            )
        },
        {
            "role": "user",
            "content": f"Contexte :\n{context}\n\nQuestion : {query}"
        }
    ]

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.2,
    )

    return response.choices[0].message.content


# === PIPELINE RAG COMPLET ===
def rag_query(query):
    """Exécute une requête RAG complète."""
    print(f"\n🔍 Requête : {query}")
    context = build_context(query)
    print(f"📚 Contexte construit ({len(context)} caractères)")
    answer = ask_deepseek(query, context)
    print("\n🧠 Réponse DeepSeek :\n")
    print(answer)
    return answer

# === TEST ===
if __name__ == "__main__":
    query = "donne moi toutn les débits du compte n° 23074642462, fais moin le détaéils de chaque débits"
    rag_query(query)
