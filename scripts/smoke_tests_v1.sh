#!/usr/bin/env bash
# ============================================================================
# SMOKE TESTS ÉTENDUS - LE MAÎTRE MOT V1
# ============================================================================
# Usage: ./scripts/smoke_tests_v1.sh [base_url]
# Example: ./scripts/smoke_tests_v1.sh http://localhost:8000
# ============================================================================

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
PASSED=0
FAILED=0
WARNINGS=0

echo "=============================================="
echo "🧪 SMOKE TESTS ÉTENDUS V1 - Le Maître Mot"
echo "=============================================="
echo "Target: ${BASE_URL}"
echo "Date: $(date)"
echo "=============================================="
echo ""

# Helper functions
pass() {
    echo "  ✅ PASS: $1"
    ((PASSED++))
}

fail() {
    echo "  ❌ FAIL: $1"
    ((FAILED++))
}

warn() {
    echo "  ⚠️  WARN: $1"
    ((WARNINGS++))
}

# ============================================================================
# TEST 1: API Health - OpenAPI docs
# ============================================================================
echo "1) GET /docs (OpenAPI)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/docs" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    pass "OpenAPI docs accessible"
else
    fail "OpenAPI docs inaccessible (HTTP $HTTP_CODE)"
fi

# ============================================================================
# TEST 2: Debug build endpoint
# ============================================================================
echo "2) GET /api/debug/build"
RESULT=$(curl -s "${BASE_URL}/api/debug/build" 2>/dev/null || echo '{"error":"connection failed"}')
if echo "$RESULT" | jq -e '.version' > /dev/null 2>&1; then
    pass "Debug build accessible"
else
    fail "Debug build failed: $RESULT"
fi

# ============================================================================
# TEST 3: Catalogue chapitres 6e
# ============================================================================
echo "3) GET /api/admin/curriculum/6e"
RESULT=$(curl -s "${BASE_URL}/api/admin/curriculum/6e" 2>/dev/null || echo '{}')
CHAPTER_COUNT=$(echo "$RESULT" | jq -r '.chapitres | length' 2>/dev/null || echo "0")
if [ "$CHAPTER_COUNT" -gt 0 ]; then
    pass "Curriculum 6e chargé ($CHAPTER_COUNT chapitres)"
else
    fail "Curriculum 6e vide ou erreur"
fi

# ============================================================================
# TEST 4: Liste des générateurs
# ============================================================================
echo "4) GET /api/v1/exercises/generators"
GENERATORS=$(curl -s "${BASE_URL}/api/v1/exercises/generators" 2>/dev/null || echo '{}')
GEN_COUNT=$(echo "$GENERATORS" | jq -r '.generators | length' 2>/dev/null || echo "0")

if [ "$GEN_COUNT" -ge 10 ]; then
    pass "Liste des générateurs OK ($GEN_COUNT générateurs)"
else
    warn "Seulement $GEN_COUNT générateurs (attendu >=10)"
fi

# ============================================================================
# TEST 5: Preview admin dynamique
# ============================================================================
echo "5) POST /api/admin/exercises/preview-dynamic"
PREVIEW_RESULT=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{
    "generator_key": "THALES_V1",
    "enonce_template_html": "<p>Test THALES_V1 coefficient {{coefficient_str}}</p>",
    "solution_template_html": "<p>Solution de test</p>",
    "difficulty": "moyen",
    "seed": 1,
    "svg_mode": "AUTO"
  }' \
  "${BASE_URL}/api/admin/exercises/preview-dynamic" 2>/dev/null || echo '{"error":"failed"}')

if echo "$PREVIEW_RESULT" | jq -e '.enonce_html' > /dev/null 2>&1; then
    pass "Preview admin THALES_V1 OK"
    
    # Vérifier placeholders non résolus
    ENONCE_HTML=$(echo "$PREVIEW_RESULT" | jq -r '.enonce_html // ""' 2>/dev/null)
    SOLUTION_HTML=$(echo "$PREVIEW_RESULT" | jq -r '.solution_html // ""' 2>/dev/null)
    
    if echo "$ENONCE_HTML" | grep -q '{{' || echo "$SOLUTION_HTML" | grep -q '{{'; then
        fail "Placeholders non résolus dans preview admin!"
        echo "      Exemple: $(echo "$ENONCE_HTML$SOLUTION_HTML" | grep -o '{{[^}]*}}' | head -1)"
    else
        pass "Aucun placeholder non résolu dans preview admin"
    fi
else
    fail "Preview admin THALES_V1 échoué"
fi

# ============================================================================
# TEST 6: Génération exercice 6e_GM07
# ============================================================================
echo "6) POST /api/v1/exercises/generate (6e_GM07)"
RESULT=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"code_officiel":"6e_GM07","difficulte":"facile","offer":"free","seed":42}' \
  "${BASE_URL}/api/v1/exercises/generate" 2>/dev/null || echo '{"error":"failed"}')

if echo "$RESULT" | jq -e '.enonce_html' > /dev/null 2>&1; then
    ENONCE_LEN=$(echo "$RESULT" | jq -r '.enonce_html | length' 2>/dev/null || echo "0")
    if [ "$ENONCE_LEN" -gt 10 ]; then
        pass "Génération 6e_GM07 OK (énoncé: ${ENONCE_LEN} chars)"
    else
        fail "Énoncé trop court: ${ENONCE_LEN} chars"
    fi
else
    fail "Génération 6e_GM07 échouée: $(echo "$RESULT" | jq -r '.detail // .error // "unknown"')"
fi

# ============================================================================
# TEST 7: Pas de placeholders non résolus
# ============================================================================
echo "7) Check no {{placeholders}} in output"
ENONCE_HTML=$(echo "$RESULT" | jq -r '.enonce_html // ""' 2>/dev/null)
SOLUTION_HTML=$(echo "$RESULT" | jq -r '.solution_html // ""' 2>/dev/null)

if echo "$ENONCE_HTML" | grep -q '{{' || echo "$SOLUTION_HTML" | grep -q '{{'; then
    fail "Placeholders non résolus trouvés dans l'output!"
    echo "      Exemple: $(echo "$ENONCE_HTML$SOLUTION_HTML" | grep -o '{{[^}]*}}' | head -1)"
else
    pass "Aucun placeholder non résolu"
fi

# ============================================================================
# TEST 8: Vérifier reproductibilité (même seed = même résultat) - 6e_GM07
# ============================================================================
echo "8) Check seed reproducibility (6e_GM07)"
SEED=99999

RESULT1=$(curl -s -X POST -H "Content-Type: application/json" \
  -d "{\"code_officiel\":\"6e_GM07\",\"difficulte\":\"moyen\",\"offer\":\"free\",\"seed\":$SEED}" \
  "${BASE_URL}/api/v1/exercises/generate" 2>/dev/null || echo '{}')

RESULT2=$(curl -s -X POST -H "Content-Type: application/json" \
  -d "{\"code_officiel\":\"6e_GM07\",\"difficulte\":\"moyen\",\"offer\":\"free\",\"seed\":$SEED}" \
  "${BASE_URL}/api/v1/exercises/generate" 2>/dev/null || echo '{}')

ENONCE1=$(echo "$RESULT1" | jq -r '.enonce_html // ""' 2>/dev/null)
ENONCE2=$(echo "$RESULT2" | jq -r '.enonce_html // ""' 2>/dev/null)

if [ "$ENONCE1" = "$ENONCE2" ] && [ -n "$ENONCE1" ]; then
    pass "Seed reproductibilité OK (6e_GM07)"
else
    fail "Seed reproductibilité KO - résultats différents pour seed=$SEED"
fi

# ============================================================================
# TEST 9: Catalog API
# ============================================================================
echo "9) GET /api/v1/curriculum/6e/catalog"
CATALOG=$(curl -s "${BASE_URL}/api/v1/curriculum/6e/catalog" 2>/dev/null || echo '{}')
TOTAL_CHAPTERS=$(echo "$CATALOG" | jq -r '.total_chapters // 0' 2>/dev/null)

if [ "$TOTAL_CHAPTERS" -gt 0 ]; then
    pass "Catalog 6e OK ($TOTAL_CHAPTERS chapitres)"
else
    fail "Catalog 6e vide ou erreur"
fi

# ============================================================================
# RÉSUMÉ
# ============================================================================
echo ""
echo "=============================================="
echo "📊 RÉSUMÉ DES TESTS"
echo "=============================================="
echo "  ✅ Passed:  $PASSED"
echo "  ❌ Failed:  $FAILED"
echo "  ⚠️  Warnings: $WARNINGS"
echo "=============================================="

if [ "$FAILED" -gt 0 ]; then
    echo "❌ TESTS ÉCHOUÉS - Voir les détails ci-dessus"
    exit 1
else
    echo "✅ TOUS LES TESTS CRITIQUES PASSENT"
    exit 0
fi

