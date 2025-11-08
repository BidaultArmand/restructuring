#!/usr/bin/env python3
# deepseek_table_extractor_folder.py

import os
import re
import json
import requests
from dotenv import load_dotenv

# ==========================
# CONFIG
# ==========================

load_dotenv()
API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not API_KEY:
    raise RuntimeError("⚠️ DEEPSEEK_API_KEY manquante dans le fichier .env")

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

INPUT_FOLDER = "outputs"
OUTPUT_FILE = "all_tables.json"

# ==========================
# OUTILS
# ==========================

def segment_text(text: str, max_pages: int = 6) -> list:
    """
    Coupe le texte en segments d’environ `max_pages` pages
    ou lorsqu'une rupture logique est détectée.
    """
    LINES_PER_PAGE = 50
    lines = text.splitlines()
    segments = []
    current = []

    for i, line in enumerate(lines):
        current.append(line)

        # rupture logique (nouvelle section ou page)
        if re.search(r"Tour\s+CB|Page\s+\d+|du\s+\d{2}/\d{2}/\d{4}", line, re.I):
            if len(current) >= LINES_PER_PAGE * max_pages:
                segments.append("\n".join(current))
                current = []

        # rupture naturelle (tous les ~6 pages)
        elif len(current) >= LINES_PER_PAGE * max_pages:
            segments.append("\n".join(current))
            current = []

    if current:
        segments.append("\n".join(current))

    return segments


def call_deepseek(prompt: str) -> str:
    """Appelle DeepSeek et retourne le contenu brut."""
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
    }
    r = requests.post(DEEPSEEK_URL, headers=HEADERS, json=payload, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"DeepSeek HTTP {r.status_code}: {r.text}")
    return r.json()["choices"][0]["message"]["content"]


def extract_tables_from_text(text: str, source_name: str = "") -> list:
    """
    Extrait tous les tableaux d’un texte segmenté en plusieurs blocs.
    """
    segments = segment_text(text)
    print(f"📄 {len(segments)} segments détectés dans {source_name}")
    tables = []

    for i, segment in enumerate(segments, start=1):
        print(f"→ Traitement segment {i}/{len(segments)} ({source_name})...")

        prompt = f"""
Tu es un assistant qui lit un texte et en extrait tous les tableaux chiffrés ou tabulaires.

Consignes :
- Détecte les tableaux financiers ou structurés.
- Renvoie UNIQUEMENT du JSON valide, format :
  [
    {{
      "source": "{source_name}",
      "titre": "nom du tableau (si identifiable)",
      "unit": "EUR" si mentionné,
      "data": [
        {{ "label": "Chiffre d'affaires net", "2013": 889743, "2014": 742628, "2015": 807635 }},
        ...
      ]
    }},
    ...
  ]
- Supprime les espaces dans les nombres ("1 234" → 1234).
- Si une valeur est absente, mets null.
- Ne renvoie que le JSON.

Texte à traiter :
---
{segment}
---
        """

        try:
            response_text = call_deepseek(prompt)
            try:
                parsed = json.loads(response_text)
                if isinstance(parsed, list):
                    tables.extend(parsed)
                else:
                    tables.append(parsed)
            except json.JSONDecodeError:
                print(f"⚠️ Réponse non JSON pour {source_name} segment {i}, ignorée.")
        except Exception as e:
            print(f"❌ Erreur sur {source_name} segment {i}: {e}")

    return tables


# ==========================
# MAIN
# ==========================

if __name__ == "__main__":
    all_tables = []
    txt_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(".txt")]

    print(f"📂 {len(txt_files)} fichiers trouvés dans {INPUT_FOLDER}/")

    for fname in txt_files:
        path = os.path.join(INPUT_FOLDER, fname)
        print(f"\n▶️ Traitement de {fname}...")
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            tables = extract_tables_from_text(text, source_name=fname)
            all_tables.extend(tables)
        except Exception as e:
            print(f"❌ Erreur sur {fname}: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as fw:
        json.dump(all_tables, fw, indent=2, ensure_ascii=False)

    print(f"\n✅ Tous les tableaux enregistrés dans {OUTPUT_FILE}")
