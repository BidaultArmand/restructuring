import pdfplumber
from unstructured.partition.pdf import partition_pdf
from typing import Union, List, Dict


def detect_table(sample_text: str) -> bool:
    """
    Détecte si un extrait de texte contient une structure de type tableau.
    Heuristique simple : présence de séparateurs, chiffres alignés ou multiples colonnes.
    """
    lines = sample_text.split("\n")
    table_like = 0
    for l in lines:
        if "|" in l or "\t" in l:
            table_like += 1
        elif len(l.split()) > 8 and any(char.isdigit() for char in l):
            table_like += 1
    # si plus de 3 lignes ont une structure tabulaire, on considère que c’est un tableau
    return table_like >= 3


def extract_text_from_pdf(path: str) -> str:
    """
    Extraction classique du texte d’un PDF.
    """
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def extract_tables_with_unstructured(path: str) -> List[Dict]:
    """
    Extraction des tableaux à l’aide de la librairie Unstructured.
    Renvoie une liste de dictionnaires représentant les tables.
    """
    elements = partition_pdf(path)
    tables = []
    for el in elements:
        if el.category == "Table":
            tables.append({
                "type": el.category,
                "text": el.text,
                "metadata": el.metadata.to_dict() if el.metadata else {}
            })
    return tables


def smart_extract(pdf_path: str) -> Union[str, List[Dict]]:
    """
    Fonction principale :
    - Détecte si le PDF contient majoritairement du texte ou des tableaux
    - Route vers la bonne méthode d’extraction
    """
    # Étape 1 : échantillonner une page
    with pdfplumber.open(pdf_path) as pdf:
        sample_text = pdf.pages[0].extract_text() or ""

    # Étape 2 : détection du type de contenu
    if detect_table(sample_text):
        print("🔍 Tableau détecté → utilisation de Unstructured / LayoutLM")
        return extract_tables_with_unstructured(pdf_path)
    else:
        print("🧾 Texte détecté → extraction simple")


        return extract_text_from_pdf(pdf_path)


if __name__ == "__main__":
    pdf_path = "data/e - center projet de plan de sauvegarde.pdf"
    result = smart_extract(pdf_path)

    if isinstance(result, str):
        print("Texte extrait :\n", result[:500])  # aperçu
    else:
        print(f"{len(result)} tableau(x) détecté(s). Exemple :\n", result[0])