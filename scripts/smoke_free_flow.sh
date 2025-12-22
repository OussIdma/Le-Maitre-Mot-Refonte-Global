#!/usr/bin/env bash
set -euo pipefail

# Smoke test pour le parcours gratuit
# Teste les endpoints critiques sans modifier le comportement runtime
#
# Usage:
#   ./scripts/smoke_free_flow.sh
#   BACKEND_URL=http://localhost:8000 FRONTEND_URL=http://localhost:3000 ./scripts/smoke_free_flow.sh

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

# Détection de jq (optionnel)
HAS_JQ=false
if command -v jq &> /dev/null; then
    HAS_JQ=true
fi

# Couleurs pour la sortie
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Compteur de tests
TESTS_PASSED=0
TESTS_FAILED=0

# Fonction pour afficher les résultats
print_result() {
    local status=$1
    local message=$2
    set +e
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✓${NC} $message"
        ((TESTS_PASSED++)) || true
    else
        echo -e "${RED}✗${NC} $message"
        ((TESTS_FAILED++)) || true
    fi
    set -e
}

# Fonction pour vérifier si un JSON contient error_code
check_error_code() {
    local json_response=$1
    if [ "$HAS_JQ" = true ]; then
        # Avec jq: vérifier si detail.error_code existe
        if echo "$json_response" | jq -e '.detail.error_code' > /dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    else
        # Sans jq: vérification basique avec grep
        if echo "$json_response" | grep -q '"error_code"' || echo "$json_response" | grep -q 'error_code'; then
            return 0
        else
            return 1
        fi
    fi
}

echo "=========================================="
echo "  Smoke Test - Parcours Gratuit"
echo "=========================================="
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo "jq disponible: $HAS_JQ"
echo ""

# ============================================================================
# TEST 1: GET /api/v1/curriculum/6e/catalog
# ============================================================================
echo "Test 1: GET /api/v1/curriculum/6e/catalog"
echo "----------------------------------------"

HTTP_CODE=$(curl -s -o /tmp/catalog_response.json -w "%{http_code}" --max-time 10 \
    "${BACKEND_URL}/api/v1/curriculum/6e/catalog" || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    print_result "OK" "Catalog endpoint répond avec HTTP 200"
    
    # Vérification basique du contenu JSON
    set +e
    if [ "$HAS_JQ" = true ]; then
        if jq -e '.level' /tmp/catalog_response.json > /dev/null 2>&1; then
            print_result "OK" "Réponse JSON valide (vérifiée avec jq)"
        else
            print_result "FAIL" "Réponse JSON invalide"
        fi
    else
        if grep -q '"level"' /tmp/catalog_response.json 2>/dev/null; then
            print_result "OK" "Réponse JSON valide (vérification basique)"
        else
            print_result "FAIL" "Réponse JSON invalide"
        fi
    fi
    set -e
else
    if [ "$HTTP_CODE" = "000" ]; then
        print_result "FAIL" "Timeout ou erreur de connexion (attendu: HTTP 200)"
    else
        print_result "FAIL" "HTTP $HTTP_CODE (attendu: HTTP 200)"
    fi
    echo "  Réponse: $(cat /tmp/catalog_response.json 2>/dev/null | head -c 200)"
    exit 1
fi

echo ""

# ============================================================================
# TEST 2: POST /api/v1/exercises/generate
# ============================================================================
echo "Test 2: POST /api/v1/exercises/generate"
echo "----------------------------------------"
echo "  Chapitre: 6e_N08 (Fractions - chapitre non-test)"
echo "  Seed: 42 (déterministe)"
echo "  Offer: free"

# Requête avec seed fixe et chapitre non-test
REQUEST_BODY=$(cat <<EOF
{
  "code_officiel": "6e_N08",
  "difficulte": "moyen",
  "offer": "free",
  "seed": 42
}
EOF
)

HTTP_CODE=$(curl -s -o /tmp/generate_response.json -w "%{http_code}" --max-time 30 \
    -H "Content-Type: application/json" \
    -d "$REQUEST_BODY" \
    "${BACKEND_URL}/api/v1/exercises/generate" || echo "000")

RESPONSE_BODY=$(cat /tmp/generate_response.json 2>/dev/null || echo "")

# Analyse de la réponse
if [ "$HTTP_CODE" = "200" ]; then
    print_result "OK" "Generate endpoint répond avec HTTP 200"
    
    # Vérification basique du contenu JSON
    set +e
    if [ "$HAS_JQ" = true ]; then
        if jq -e '.id_exercice' /tmp/generate_response.json > /dev/null 2>&1; then
            EXERCISE_ID=$(jq -r '.id_exercice' /tmp/generate_response.json 2>/dev/null || echo "N/A")
            print_result "OK" "Exercice généré: $EXERCISE_ID"
        else
            print_result "FAIL" "Réponse JSON invalide (id_exercice manquant)"
        fi
    else
        if echo "$RESPONSE_BODY" | grep -q '"id_exercice"' 2>/dev/null; then
            print_result "OK" "Exercice généré (vérification basique)"
        else
            print_result "FAIL" "Réponse JSON invalide"
        fi
    fi
    set -e
    
elif [ "$HTTP_CODE" = "422" ]; then
    # 422 est acceptable UNIQUEMENT si structuré avec error_code
    if check_error_code "$RESPONSE_BODY"; then
        ERROR_CODE=""
        if [ "$HAS_JQ" = true ]; then
            ERROR_CODE=$(jq -r '.detail.error_code // "unknown"' /tmp/generate_response.json 2>/dev/null || echo "unknown")
        else
            ERROR_CODE=$(echo "$RESPONSE_BODY" | grep -o '"error_code"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | cut -d'"' -f4 || echo "unknown")
        fi
        
        print_result "OK" "HTTP 422 accepté (erreur structurée: error_code=$ERROR_CODE)"
        echo "  Message: $(echo "$RESPONSE_BODY" | grep -o '"message"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | cut -d'"' -f4 || echo "N/A")"
    else
        print_result "FAIL" "HTTP 422 non-structuré (pas de error_code dans detail)"
        echo "  Réponse: $(echo "$RESPONSE_BODY" | head -c 300)"
        exit 1
    fi
    
elif [ "$HTTP_CODE" = "000" ]; then
    print_result "FAIL" "Timeout ou erreur de connexion (attendu: HTTP 200 ou 422 structuré)"
    echo "  Vérifiez que le backend est démarré et accessible"
    exit 1
    
elif [ "$HTTP_CODE" = "500" ]; then
    print_result "FAIL" "HTTP 500 - Erreur serveur (attendu: HTTP 200 ou 422 structuré)"
    echo "  Réponse: $(echo "$RESPONSE_BODY" | head -c 300)"
    exit 1
    
else
    print_result "FAIL" "HTTP $HTTP_CODE (attendu: HTTP 200 ou 422 structuré)"
    echo "  Réponse: $(echo "$RESPONSE_BODY" | head -c 300)"
    exit 1
fi

echo ""

# ============================================================================
# RÉSUMÉ
# ============================================================================
echo "=========================================="
echo "  Résumé"
echo "=========================================="
echo "Tests réussis: $TESTS_PASSED"
echo "Tests échoués: $TESTS_FAILED"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Tous les tests sont passés${NC}"
    exit 0
else
    echo -e "${RED}✗ Certains tests ont échoué${NC}"
    exit 1
fi

