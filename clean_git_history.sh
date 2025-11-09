#!/bin/bash

echo "🧹 Nettoyage des fichiers qui auraient dû être ignorés..."

# Supprimer les fichiers du suivi Git sans les supprimer localement
git rm --cached .DS_Store 2>/dev/null
git rm --cached .env 2>/dev/null
git rm -r --cached __pycache__/ 2>/dev/null
git rm --cached chunks_debug.json 2>/dev/null
git rm --cached index_debug.faiss 2>/dev/null
git rm --cached debug_log.txt 2>/dev/null

echo "✅ Fichiers supprimés du suivi Git (mais conservés localement)"
echo ""
echo "📝 Prochaines étapes:"
echo "1. Vérifiez les changements avec: git status"
echo "2. Commitez les changements: git add .gitignore && git commit -m 'chore: update .gitignore and remove tracked files that should be ignored'"
echo "3. Poussez sur GitHub: git push origin main"
echo ""
echo "⚠️  Note: Les fichiers restent sur votre machine locale, seul le suivi Git est supprimé"
