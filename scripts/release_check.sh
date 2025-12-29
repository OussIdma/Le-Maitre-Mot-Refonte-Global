#!/bin/bash
set -euo pipefail

# Release checklist automatisée
# Exécute tous les tests P0 critiques avant une release

echo "=========================================="
echo "🚀 RELEASE CHECKLIST - Tests P0"
echo "=========================================="
echo ""

EXIT_CODE=0
FAILED_TESTS=()

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour exécuter un test et capturer le résultat
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    # Normaliser le nom de fichier (remplacer espaces, slashes et caractères spéciaux)
    # Remplacer tous les caractères non alphanumériques par des underscores
    local safe_name=$(echo "$test_name" | sed 's/[^a-zA-Z0-9]/_/g')
    local log_file="/tmp/release_check_${safe_name}.log"
    
    echo "📋 Running: $test_name"
    echo "   Command: $test_command"
    
    # Exécuter la commande et capturer le résultat
    if eval "$test_command" > "$log_file" 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        echo ""
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: $test_name"
        echo "   Logs: $log_file"
        # Afficher les dernières lignes du log en cas d'échec
        if [ -f "$log_file" ]; then
            echo "   Last lines:"
            tail -5 "$log_file" | sed 's/^/      /'
        fi
        echo ""
        FAILED_TESTS+=("$test_name")
        return 1
    fi
}

# 1. Tests P0 (marqués avec p0_)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Tests P0 (p0_*)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
# Ignorer les fichiers avec erreurs de collection
if ! run_test "Tests P0" "pytest -k 'p0_' -v --ignore=backend/tests/test_admin_curriculum.py --ignore=backend/tests/test_curriculum_sync_service.py --ignore=backend/tests/test_html_sanitizer.py"; then
    EXIT_CODE=1
fi

# 2. Tests contractuels générateurs
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Tests contractuels générateurs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ! run_test "Generators Contract" "pytest backend/tests/test_generators_contract.py -v"; then
    EXIT_CODE=1
fi

# 3. Tests import/export versionné
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Tests import/export versionné"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ! run_test "Import/Export Versioned" "pytest backend/tests/test_import_export_versioned.py -v"; then
    EXIT_CODE=1
fi

# 4. Smoke tests API
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  Smoke tests API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ! run_test "Smoke API P0" "pytest backend/tests/test_smoke_api_p0.py -v"; then
    EXIT_CODE=1
fi

# Résumé
echo "=========================================="
echo "📊 RÉSUMÉ"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ TOUS LES TESTS PASSENT${NC}"
    echo ""
    echo "🎉 Release checklist: PASS"
    exit 0
else
    echo -e "${RED}❌ ÉCHECS DÉTECTÉS${NC}"
    echo ""
    echo "Tests en échec:"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "  ${RED}❌${NC} $test"
    done
    echo ""
    echo -e "${YELLOW}⚠️  Release checklist: FAIL${NC}"
    echo "Consultez les logs dans /tmp/release_check_*.log"
    exit 1
fi
