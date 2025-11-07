import sys
import os
from pdf_extract import extract_pdfs  


def main():
    """
    Point d'entrée principal du script.
    - Vérifie la présence du dossier 'pdfs'
    - Lance l'extraction
    """
    print("🚀 Lancement de l’extraction PDF vers texte/tableaux...\n")
    
    # Appel de ta fonction d'extraction
    extract_pdfs(pdf_folder="pdfs", output_folder="outputs")

    print("\n🎯 Extraction terminée. Les fichiers sont disponibles dans le dossier 'outputs/'.")


# ------------------------------------------------------
# 🏁 Exécution directe
# ------------------------------------------------------
if __name__ == "__main__":
    main()