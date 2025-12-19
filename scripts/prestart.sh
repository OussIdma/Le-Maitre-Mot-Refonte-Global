#!/bin/bash
set -e

echo "========================================"
echo "🚀 BACKEND PRE-START SCRIPT"
echo "========================================"
echo ""

# Fonction pour afficher le temps écoulé
start_time=$(date +%s)

echo "📦 Étape 1/3 : Installation des dépendances système..."
python3 /app/scripts/ensure_system_dependencies.py
if [ $? -ne 0 ]; then
    echo "❌ Échec de l'installation des dépendances système"
    exit 1
fi
echo ""

echo "🔍 Étape 2/3 : Vérification de l'environnement PDF..."
python3 /app/backend/scripts/check_pdf_env.py
if [ $? -ne 0 ]; then
    echo "⚠️  L'environnement PDF a des problèmes, mais on continue..."
fi
echo ""

echo "✅ Étape 3/3 : Pre-start terminé"
end_time=$(date +%s)
elapsed=$((end_time - start_time))
echo "⏱️  Temps d'exécution : ${elapsed}s"
echo ""
echo "========================================"
echo "🎯 Prêt à démarrer le backend !"
echo "========================================"
