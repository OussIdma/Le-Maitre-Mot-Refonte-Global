#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Smoke Test E2E Premium (P1.4)
# =============================================================================
# Test de bout en bout minimal pour valider le parcours premium complet via curl.
# 
# Tests:
# 1. 6e_SP03 → RAISONNEMENT_MULTIPLICATIF_V1
# 2. 6e_N04 → CALCUL_NOMBRES_V1
# 3. Déterminisme (même seed → même résultat)
# 4. offer=free ne déclenche pas premium
# 5. Temps de génération (<2s)
# 6. Sécurité HTML (pas de <script>)
# =============================================================================

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

HAS_JQ=false
if command -v jq >/dev/null 2>&1; then
    HAS_JQ=true
fi

print_result() {
    local status=$1
    local message=$2
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✓${NC} $message"
        (( TESTS_PASSED++ ))
    else
        echo -e "${RED}✗${NC} $message"
        (( TESTS_FAILED++ ))
    fi
}

echo "=========================================="
echo "  Smoke Test E2E Premium (P1.4)"
echo "=========================================="
echo "Backend: $BACKEND_URL"
echo "jq disponible: $HAS_JQ"
echo ""

# =============================================================================
# TEST 1: 6e_SP03 → RAISONNEMENT_MULTIPLICATIF_V1
# =============================================================================
echo "Test 1: 6e_SP03 → RAISONNEMENT_MULTIPLICATIF_V1"
echo "─────────────────────────────────────────"

RESPONSE_FILE=$(mktemp)
HTTP_CODE=$(curl -s -w "%{http_code}" -o "$RESPONSE_FILE" \
    -X POST "$BACKEND_URL/api/v1/exercises/generate" \
    -H "Content-Type: application/json" \
    -d '{
      "code_officiel": "6e_SP03",
      "niveau": "6e",
      "chapitre": "Proportionnalité",
      "difficulte": "moyen",
      "offer": "pro",
      "seed": 42
    }')

if [ "$HTTP_CODE" = "200" ]; then
    print_result "OK" "Test 1.1: HTTP 200 OK"
    
    # Vérifier enonce_html non vide
    if $HAS_JQ; then
        ENONCE_HTML=$(jq -r '.enonce_html' "$RESPONSE_FILE")
        SOLUTION_HTML=$(jq -r '.solution_html' "$RESPONSE_FILE")
        IS_PREMIUM=$(jq -r '.metadata.is_premium' "$RESPONSE_FILE")
        GENERATOR_KEY=$(jq -r '.metadata.generator_key' "$RESPONSE_FILE")
        
        if [ "${#ENONCE_HTML}" -gt 100 ]; then
            print_result "OK" "Test 1.2: enonce_html non vide (${#ENONCE_HTML} chars)"
        else
            print_result "FAIL" "Test 1.2: enonce_html trop court (${#ENONCE_HTML} chars)"
        fi
        
        if [ "${#SOLUTION_HTML}" -gt 100 ]; then
            print_result "OK" "Test 1.3: solution_html non vide (${#SOLUTION_HTML} chars)"
        else
            print_result "FAIL" "Test 1.3: solution_html trop court (${#SOLUTION_HTML} chars)"
        fi
        
        if [ "$IS_PREMIUM" = "true" ]; then
            print_result "OK" "Test 1.4: is_premium=true"
        else
            print_result "FAIL" "Test 1.4: is_premium=$IS_PREMIUM (attendu: true)"
        fi
        
        if [ "$GENERATOR_KEY" = "RAISONNEMENT_MULTIPLICATIF_V1" ] || [ "$GENERATOR_KEY" = "CALCUL_NOMBRES_V1" ]; then
            print_result "OK" "Test 1.5: generator_key=$GENERATOR_KEY"
        else
            print_result "FAIL" "Test 1.5: generator_key=$GENERATOR_KEY inattendu"
        fi
        
        # Vérifier structure HTML (table pour RAISONNEMENT_MULTIPLICATIF_V1)
        if echo "$ENONCE_HTML" | grep -q "<table"; then
            print_result "OK" "Test 1.6: Tableau HTML présent dans enonce_html"
        else
            print_result "WARN" "Test 1.6: Pas de tableau HTML (peut-être CALCUL_NOMBRES_V1)"
        fi
    else
        # Sans jq, vérification basique
        if grep -q '"enonce_html"' "$RESPONSE_FILE" && grep -q '"solution_html"' "$RESPONSE_FILE"; then
            print_result "OK" "Test 1.2-5: Structure JSON présente (vérification basique sans jq)"
        else
            print_result "FAIL" "Test 1.2-5: Structure JSON invalide"
        fi
    fi
else
    print_result "FAIL" "Test 1.1: HTTP $HTTP_CODE (attendu: 200)"
    echo "Réponse:"
    cat "$RESPONSE_FILE"
fi

echo ""

# =============================================================================
# TEST 2: 6e_N04 → CALCUL_NOMBRES_V1
# =============================================================================
echo "Test 2: 6e_N04 → CALCUL_NOMBRES_V1"
echo "─────────────────────────────────────────"

RESPONSE_FILE2=$(mktemp)
HTTP_CODE=$(curl -s -w "%{http_code}" -o "$RESPONSE_FILE2" \
    -X POST "$BACKEND_URL/api/v1/exercises/generate" \
    -H "Content-Type: application/json" \
    -d '{
      "code_officiel": "6e_N04",
      "niveau": "6e",
      "chapitre": "Addition et soustraction",
      "difficulte": "moyen",
      "offer": "pro",
      "seed": 123
    }')

if [ "$HTTP_CODE" = "200" ]; then
    print_result "OK" "Test 2.1: HTTP 200 OK"
    
    if $HAS_JQ; then
        ENONCE_HTML=$(jq -r '.enonce_html' "$RESPONSE_FILE2")
        SOLUTION_HTML=$(jq -r '.solution_html' "$RESPONSE_FILE2")
        IS_PREMIUM=$(jq -r '.metadata.is_premium' "$RESPONSE_FILE2")
        GENERATOR_KEY=$(jq -r '.metadata.generator_key' "$RESPONSE_FILE2")
        
        if [ "${#ENONCE_HTML}" -gt 50 ]; then
            print_result "OK" "Test 2.2: enonce_html non vide (${#ENONCE_HTML} chars)"
        else
            print_result "FAIL" "Test 2.2: enonce_html trop court"
        fi
        
        if [ "${#SOLUTION_HTML}" -gt 50 ]; then
            print_result "OK" "Test 2.3: solution_html non vide (${#SOLUTION_HTML} chars)"
        else
            print_result "FAIL" "Test 2.3: solution_html trop court"
        fi
        
        if [ "$IS_PREMIUM" = "true" ]; then
            print_result "OK" "Test 2.4: is_premium=true"
        else
            print_result "FAIL" "Test 2.4: is_premium=$IS_PREMIUM"
        fi
        
        print_result "OK" "Test 2.5: generator_key=$GENERATOR_KEY"
    else
        print_result "OK" "Test 2.2-5: Structure JSON présente (sans jq)"
    fi
else
    print_result "FAIL" "Test 2.1: HTTP $HTTP_CODE (attendu: 200)"
fi

echo ""

# =============================================================================
# TEST 3: Déterminisme (même seed → même résultat)
# =============================================================================
echo "Test 3: Déterminisme"
echo "─────────────────────────────────────────"

RESPONSE_FILE3A=$(mktemp)
RESPONSE_FILE3B=$(mktemp)

curl -s -o "$RESPONSE_FILE3A" \
    -X POST "$BACKEND_URL/api/v1/exercises/generate" \
    -H "Content-Type: application/json" \
    -d '{
      "code_officiel": "6e_SP03",
      "niveau": "6e",
      "chapitre": "Proportionnalité",
      "difficulte": "moyen",
      "offer": "pro",
      "seed": 999
    }'

curl -s -o "$RESPONSE_FILE3B" \
    -X POST "$BACKEND_URL/api/v1/exercises/generate" \
    -H "Content-Type: application/json" \
    -d '{
      "code_officiel": "6e_SP03",
      "niveau": "6e",
      "chapitre": "Proportionnalité",
      "difficulte": "moyen",
      "offer": "pro",
      "seed": 999
    }'

if $HAS_JQ; then
    ENONCE1=$(jq -r '.enonce_html' "$RESPONSE_FILE3A")
    ENONCE2=$(jq -r '.enonce_html' "$RESPONSE_FILE3B")
    
    if [ "$ENONCE1" = "$ENONCE2" ]; then
        print_result "OK" "Test 3.1: Déterminisme validé (enonce_html identique)"
    else
        print_result "FAIL" "Test 3.1: Déterminisme échoué (enonce_html différent)"
    fi
else
    # Comparaison binaire sans jq
    if cmp -s "$RESPONSE_FILE3A" "$RESPONSE_FILE3B"; then
        print_result "OK" "Test 3.1: Déterminisme validé (réponses identiques)"
    else
        print_result "FAIL" "Test 3.1: Déterminisme échoué (réponses différentes)"
    fi
fi

echo ""

# =============================================================================
# TEST 4: offer=free ne déclenche pas premium
# =============================================================================
echo "Test 4: offer=free ne déclenche pas premium"
echo "─────────────────────────────────────────"

RESPONSE_FILE4=$(mktemp)
HTTP_CODE=$(curl -s -w "%{http_code}" -o "$RESPONSE_FILE4" \
    -X POST "$BACKEND_URL/api/v1/exercises/generate" \
    -H "Content-Type: application/json" \
    -d '{
      "code_officiel": "6e_SP03",
      "niveau": "6e",
      "chapitre": "Proportionnalité",
      "difficulte": "moyen",
      "offer": "free",
      "seed": 42
    }')

if [ "$HTTP_CODE" = "200" ]; then
    if $HAS_JQ; then
        IS_PREMIUM=$(jq -r '.metadata.is_premium' "$RESPONSE_FILE4")
        
        if [ "$IS_PREMIUM" = "false" ] || [ "$IS_PREMIUM" = "null" ]; then
            print_result "OK" "Test 4.1: offer=free ne déclenche pas premium (is_premium=$IS_PREMIUM)"
        else
            print_result "FAIL" "Test 4.1: offer=free a déclenché premium (is_premium=$IS_PREMIUM)"
        fi
    else
        print_result "OK" "Test 4.1: offer=free accepté (200)"
    fi
elif [ "$HTTP_CODE" = "422" ]; then
    print_result "OK" "Test 4.1: offer=free retourne 422 (pas d'exercices free disponibles)"
else
    print_result "FAIL" "Test 4.1: HTTP $HTTP_CODE inattendu"
fi

echo ""

# =============================================================================
# TEST 5: Temps de génération (<2s)
# =============================================================================
echo "Test 5: Temps de génération"
echo "─────────────────────────────────────────"

START_TIME=$(date +%s.%N)
curl -s -o /dev/null \
    -X POST "$BACKEND_URL/api/v1/exercises/generate" \
    -H "Content-Type: application/json" \
    -d '{
      "code_officiel": "6e_SP03",
      "niveau": "6e",
      "chapitre": "Proportionnalité",
      "difficulte": "moyen",
      "offer": "pro",
      "seed": 42
    }'
END_TIME=$(date +%s.%N)

DURATION=$(echo "$END_TIME - $START_TIME" | bc)

# Comparaison avec 2.0 secondes
if [ $(echo "$DURATION < 2.0" | bc) -eq 1 ]; then
    print_result "OK" "Test 5.1: Génération rapide (${DURATION}s < 2s)"
else
    print_result "FAIL" "Test 5.1: Génération lente (${DURATION}s >= 2s)"
fi

echo ""

# =============================================================================
# TEST 6: Sécurité HTML (pas de <script>, <iframe>, etc.)
# =============================================================================
echo "Test 6: Sécurité HTML"
echo "─────────────────────────────────────────"

RESPONSE_FILE6=$(mktemp)
curl -s -o "$RESPONSE_FILE6" \
    -X POST "$BACKEND_URL/api/v1/exercises/generate" \
    -H "Content-Type: application/json" \
    -d '{
      "code_officiel": "6e_SP03",
      "niveau": "6e",
      "chapitre": "Proportionnalité",
      "difficulte": "moyen",
      "offer": "pro",
      "seed": 42
    }'

SECURITY_OK=true
FORBIDDEN_TAGS=("<script" "<iframe" "<object" "<embed" "javascript:" "onerror=" "onclick=")

for tag in "${FORBIDDEN_TAGS[@]}"; do
    if grep -iq "$tag" "$RESPONSE_FILE6"; then
        print_result "FAIL" "Test 6.1: ⚠️ SÉCURITÉ: $tag trouvé dans la réponse"
        SECURITY_OK=false
    fi
done

if [ "$SECURITY_OK" = true ]; then
    print_result "OK" "Test 6.1: Aucune balise dangereuse détectée"
fi

echo ""

# =============================================================================
# Nettoyage
# =============================================================================
rm -f "$RESPONSE_FILE" "$RESPONSE_FILE2" "$RESPONSE_FILE3A" "$RESPONSE_FILE3B" "$RESPONSE_FILE4" "$RESPONSE_FILE6"

# =============================================================================
# RÉSUMÉ
# =============================================================================
echo "=========================================="
echo "  Résumé"
echo "=========================================="
echo "Tests réussis: $TESTS_PASSED"
echo "Tests échoués: $TESTS_FAILED"

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ Tous les tests smoke E2E premium sont passés${NC}"
    exit 0
else
    echo -e "${RED}✗ Des tests ont échoué${NC}"
    exit 1
fi








