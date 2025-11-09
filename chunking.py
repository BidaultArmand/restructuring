import os
import json
import gc
import psutil
import numpy as np
import faiss
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import time

# === CONFIG ===
TEXT_DIR = "data/texts"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
INDEX_PATH = "index_debug.faiss"
CHUNKS_PATH = "chunks_debug.json"
DEBUG_LOG = "debug_log.txt"
BATCH_SIZE = 64  # ⚙️ encode plusieurs chunks à la fois (optimisation RAM + vitesse)

# === UTILS ===
def log_debug(message):
    """Écrit les logs dans un fichier + console"""
    timestamp = time.strftime("[%H:%M:%S]")
    print(f"{timestamp} {message}")
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {message}\n")

def show_mem(prefix=""):
    """Affiche la mémoire utilisée"""
    mem = psutil.virtual_memory()
    used = mem.used / (1024**3)
    total = mem.total / (1024**3)
    log_debug(f"{prefix} 💾 RAM utilisée: {used:.2f} Go / {total:.2f} Go")

def chunk_text(text, max_chars=500, overlap=80):
    """Découpe un texte en petits morceaux avec chevauchement"""
    for start in range(0, len(text), max_chars - overlap):
        yield text[start:start + max_chars]


# === MAIN ===
if __name__ == "__main__":
    open(DEBUG_LOG, "w").close()  # reset log
    log_debug("🚀 Démarrage du script RAG DEBUG")

    # ⚙️ Initialiser le modèle AVANT lecture (évite pics mémoire plus tard)
    log_debug("⚙️ Initialisation du modèle...")
    model = SentenceTransformer(MODEL_NAME)
    dim = model.get_sentence_embedding_dimension()
    index = faiss.IndexFlatL2(dim)
    show_mem("Après chargement du modèle")

    # Liste pour écrire les chunks progressivement
    all_chunks = []
    chunk_counter = 0

    # 1️⃣ Parcours fichier par fichier pour éviter surcharge RAM
    for filename in os.listdir(TEXT_DIR):
        if not filename.endswith(".txt"):
            continue

        path = os.path.join(TEXT_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()

        log_debug(f"📄 Chargé {filename} ({len(text)} caractères)")

        # 2️⃣ Découpage en chunks + encodage par batch
        chunk_batch = []
        meta_batch = []

        for i, c in enumerate(chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)):
            meta_batch.append({"doc_id": filename, "chunk_id": f"{filename}_{i}", "text": c})
            chunk_batch.append(c)

            # Quand on atteint la taille de batch → encodage
            if len(chunk_batch) >= BATCH_SIZE:
                embeddings = model.encode(chunk_batch, convert_to_numpy=True, show_progress_bar=False)
                index.add(embeddings)
                all_chunks.extend(meta_batch)
                chunk_counter += len(chunk_batch)
                log_debug(f"🔹 Ajout de {len(chunk_batch)} chunks (total: {chunk_counter})")
                show_mem(f"Après encodage batch {chunk_counter // BATCH_SIZE}")
                # Nettoyage mémoire
                del embeddings, chunk_batch, meta_batch
                gc.collect()
                chunk_batch, meta_batch = [], []

        # 🔚 Dernier batch du fichier
        if chunk_batch:
            embeddings = model.encode(chunk_batch, convert_to_numpy=True, show_progress_bar=False)
            index.add(embeddings)
            all_chunks.extend(meta_batch)
            chunk_counter += len(chunk_batch)
            del embeddings
            gc.collect()

        show_mem(f"Fin traitement {filename}")

    # 3️⃣ Sauvegarde
    log_debug(f"✅ {chunk_counter} chunks encodés au total")
    show_mem("Avant sauvegarde")

    log_debug("💾 Sauvegarde de l'index...")
    faiss.write_index(index, INDEX_PATH)

    log_debug("💾 Sauvegarde des métadonnées chunks...")
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    log_debug("✅ Terminé sans crash !")
    show_mem("Fin du traitement")
