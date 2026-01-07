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
# TEST 4: Génération exercice 6e_GM07
# ============================================================================
echo "4) POST /api/v1/exercises/generate (6e_GM07)"
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
# TEST 5: Pas de placeholders non résolus
# ============================================================================
echo "5) Check no {{placeholders}} in output"
if echo "$RESULT" | grep -q '{{'; then
    fail "Placeholders non résolus trouvés dans l'output!"
    echo "      Exemple: $(echo "$RESULT" | grep -o '{{[^}]*}}' | head -1)"
else
    pass "Aucun placeholder non résolu"
fi

# ============================================================================
# TEST 6: Génération exercice 6e_GM08 (géométrie)
# ============================================================================
echo "6) POST /api/v1/exercises/generate (6e_GM08)"
GEOM_RESULT=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"code_officiel":"6e_GM08","difficulte":"facile","offer":"free","seed":42}' \
  "${BASE_URL}/api/v1/exercises/generate" 2>/dev/null || echo '{"error":"failed"}')

if echo "$GEOM_RESULT" | jq -e '.enonce_html' > /dev/null 2>&1; then
    pass "Génération 6e_GM08 OK"
    
    # Check SVG si needs_svg=true
    NEEDS_SVG=$(echo "$GEOM_RESULT" | jq -r '.needs_svg // false' 2>/dev/null)
    HAS_SVG=$(echo "$GEOM_RESULT" | jq -r '.figure_svg_enonce // ""' 2>/dev/null)
    
    if [ "$NEEDS_SVG" = "true" ] && [ -z "$HAS_SVG" ]; then
        warn "SVG attendu mais absent pour exercice géométrique"
    fi
else
    fail "Génération 6e_GM08 échouée"
fi

# ============================================================================
# TEST 7: Génération exercice 6e_TESTS_DYN (dynamique)
# ============================================================================
echo "7) POST /api/v1/exercises/generate (6e_TESTS_DYN)"
DYN_RESULT=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"code_officiel":"6e_TESTS_DYN","difficulte":"moyen","offer":"free","seed":123}' \
  "${BASE_URL}/api/v1/exercises/generate" 2>/dev/null || echo '{"error":"failed"}')

if echo "$DYN_RESULT" | jq -e '.enonce_html' > /dev/null 2>&1; then
    pass "Génération 6e_TESTS_DYN OK"
    
    # Vérifier pas de placeholders
    if echo "$DYN_RESULT" | grep -q '{{'; then
        fail "Placeholders non résolus dans 6e_TESTS_DYN!"
    fi
else
    ERROR_MSG=$(echo "$DYN_RESULT" | jq -r '.detail.message // .error // "unknown"' 2>/dev/null)
    fail "Génération 6e_TESTS_DYN échouée: $ERROR_MSG"
fi

# ============================================================================
# TEST 8: Preview admin dynamique
# ============================================================================
echo "8) POST /api/admin/exercises/preview-dynamic"
PREVIEW_RESULT=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"generator_key":"THALES_V2","difficulty":"facile","seed":1}' \
  "${BASE_URL}/api/admin/exercises/preview-dynamic" 2>/dev/null || echo '{"error":"failed"}')

if echo "$PREVIEW_RESULT" | jq -e '.enonce_html' > /dev/null 2>&1; then
    pass "Preview admin THALES_V2 OK"
else
    fail "Preview admin THALES_V2 échoué"
fi

# ============================================================================
# TEST 9: Liste des générateurs
# ============================================================================
echo "9) GET /api/v1/exercises/generators"
GENERATORS=$(curl -s "${BASE_URL}/api/v1/exercises/generators" 2>/dev/null || echo '[]')
GEN_COUNT=$(echo "$GENERATORS" | jq -r 'length' 2>/dev/null || echo "0")

if [ "$GEN_COUNT" -ge 10 ]; then
    pass "Liste des générateurs OK ($GEN_COUNT générateurs)"
else
    warn "Seulement $GEN_COUNT générateurs (attendu >=10)"
fi

# ============================================================================
# TEST 10: Catalog API
# ============================================================================
echo "10) GET /api/v1/curriculum/6e/catalog"
CATALOG=$(curl -s "${BASE_URL}/api/v1/curriculum/6e/catalog" 2>/dev/null || echo '{}')
TOTAL_CHAPTERS=$(echo "$CATALOG" | jq -r '.total_chapters // 0' 2>/dev/null)

if [ "$TOTAL_CHAPTERS" -gt 0 ]; then
    pass "Catalog 6e OK ($TOTAL_CHAPTERS chapitres)"
else
    fail "Catalog 6e vide ou erreur"
fi

# ============================================================================
# TEST 11: Export PDF (sans auth - devrait échouer ou limiter)
# ============================================================================
echo "11) POST /api/mathalea/sheets/export (no auth)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" \
  -d '{"items":[],"title":"Test","layout":"academique"}' \
  "${BASE_URL}/api/mathalea/sheets/export" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    pass "Export PDF nécessite auth (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "422" ]; then
    warn "Export PDF retourne 422 (validation) - vérifier si auth est requis"
elif [ "$HTTP_CODE" = "200" ]; then
    warn "Export PDF sans auth accepté - paywall manquant?"
else
    fail "Export PDF erreur inattendue (HTTP $HTTP_CODE)"
fi

# ============================================================================
# TEST 12: Chapitres pilotes disponibles
# ============================================================================
echo "12) GET /api/admin/exercises/pilot-chapters"
PILOTS=$(curl -s "${BASE_URL}/api/admin/exercises/pilot-chapters" 2>/dev/null || echo '{}')
PILOT_COUNT=$(echo "$PILOTS" | jq -r '.pilot_chapters | length' 2>/dev/null || echo "0")

if [ "$PILOT_COUNT" -ge 3 ]; then
    pass "Chapitres pilotes OK ($PILOT_COUNT)"
else
    warn "Seulement $PILOT_COUNT chapitres pilotes (attendu >=3)"
fi

# ============================================================================
# TEST 13: Exercices d'un chapitre pilote
# ============================================================================
echo "13) GET /api/admin/chapters/6e_GM07/exercises"
EXERCISES=$(curl -s "${BASE_URL}/api/admin/chapters/6e_GM07/exercises" 2>/dev/null || echo '{}')
EX_COUNT=$(echo "$EXERCISES" | jq -r '.total // 0' 2>/dev/null)

if [ "$EX_COUNT" -gt 0 ]; then
    pass "Exercices 6e_GM07 en DB ($EX_COUNT)"
else
    warn "Aucun exercice 6e_GM07 en DB"
fi

# ============================================================================
# TEST 14: Pas d'exercices avec placeholders non résolus en DB
# ============================================================================
echo "14) Check no broken exercises in DB"
# Ce test nécessite accès MongoDB - skip si non disponible
if command -v mongosh &> /dev/null; then
    BROKEN=$(mongosh --quiet --eval 'db.admin_exercises.find({enonce_html: /\{\{/}).count()' le_maitre_mot_db 2>/dev/null || echo "-1")
    if [ "$BROKEN" = "0" ]; then
        pass "Aucun exercice cassé en DB"
    elif [ "$BROKEN" = "-1" ]; then
        warn "Impossible de vérifier DB (mongosh indisponible)"
    else
        fail "$BROKEN exercices avec placeholders en DB"
    fi
else
    warn "mongosh non disponible - skip vérification DB"
fi

# ============================================================================
# TEST 15: Vérifier reproductibilité (même seed = même résultat)
# ============================================================================
echo "15) Check seed reproducibility"
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
    pass "Seed reproductibilité OK"
else
    fail "Seed reproductibilité KO - résultats différents pour seed=$SEED"
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
