#!/bin/bash
# Script de vérification des générateurs (P4.2)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔍 Vérification des générateurs..."
echo ""

cd "$ROOT_DIR"

# Exécuter le quality gate en mode check
python backend/scripts/run_generators_quality_gate.py --check

echo ""
echo "✅ Vérification terminée avec succès"




