import os
import pdfplumber
from unstructured.partition.pdf import partition_pdf
from typing import List, Dict, Union


def detect_table(sample_text: str) -> bool:
    """Détecte si le texte ressemble à un tableau."""
    lines = sample_text.split("\n")
    table_like = 0
    for l in lines:
        if "|" in l or "\t" in l:
            table_like += 1
        elif len(l.split()) > 8 and any(char.isdigit() for char in l):
            table_like += 1
    return table_like >= 3


def extract_text_from_pdf(path: str) -> str:
    """Extraction classique du texte d’un PDF."""
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
    return text.strip()


def extract_tables_with_unstructured(path: str) -> List[Dict]:
    """Extraction des tableaux via Unstructured."""
    elements = partition_pdf(path)
    tables = []
    for el in elements:
        if el.category == "Table":
            tables.append(el.text)
    return tables


def smart_extract(pdf_path: str) -> str:
    """Extrait tout le contenu d’un PDF (texte + tableaux) en texte structuré."""
    combined_output = ""

    # 1️⃣ Détection du type
    with pdfplumber.open(pdf_path) as pdf:
        sample_text = pdf.pages[0].extract_text() or ""

    # 2️⃣ Extraction texte
    text_content = extract_text_from_pdf(pdf_path)
    combined_output += "===== TEXTE EXTRAIT =====\n\n"
    combined_output += text_content + "\n\n"

    # 3️⃣ Extraction tableaux
    if detect_table(sample_text):
        tables = extract_tables_with_unstructured(pdf_path)
        if tables:
            combined_output += "===== TABLEAUX EXTRAITS =====\n\n"
            for i, t in enumerate(tables, start=1):
                combined_output += f"[Tableau {i}]\n{t}\n\n"

    return combined_output.strip()


def process_folder(input_folder: str, output_folder: str):
    """Parcourt tous les PDF d’un dossier et crée un .txt pour chacun."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename.replace(".pdf", ".txt"))
            print(f"📄 Extraction de {filename}...")

            try:
                extracted = smart_extract(pdf_path)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(extracted)
                print(f"✅ Fichier extrait → {output_path}")
            except Exception as e:
                print(f"❌ Erreur sur {filename}: {e}")


if __name__ == "__main__":
    input_folder = "data"
    output_folder = "outputs"

    process_folder(input_folder, output_folder)
