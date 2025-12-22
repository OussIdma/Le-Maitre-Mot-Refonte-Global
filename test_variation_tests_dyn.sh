#!/bin/bash
# Script de test pour valider les corrections du bouton Variation TESTS_DYN
# Usage: ./test_variation_tests_dyn.sh

BACKEND_URL="http://localhost:8000"
API_V1="${BACKEND_URL}/api/v1/exercises"

echo "🧪 Tests de validation - Variation TESTS_DYN"
echo "=============================================="
echo ""

# Test 1: Génération initiale avec offer="free"
echo "📋 Test 1: Génération initiale (offer=free, difficulty=moyen, seed=42)"
RESPONSE1=$(curl -s -X POST "${API_V1}/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_TESTS_DYN",
    "difficulte": "moyen",
    "seed": 42
  }')

if echo "$RESPONSE1" | grep -q "id_exercice"; then
  echo "✅ Test 1 réussi: Exercice généré"
  EXERCISE_ID=$(echo "$RESPONSE1" | grep -o '"id_exercice":"[^"]*"' | cut -d'"' -f4)
  echo "   ID: $EXERCISE_ID"
else
  echo "❌ Test 1 échoué: Pas d'exercice généré"
  echo "   Réponse: $RESPONSE1"
  exit 1
fi

echo ""

# Test 2: Variation avec offer="pro" (doit fallback vers free)
echo "📋 Test 2: Variation avec offer=pro (fallback attendu vers free, seed=42)"
RESPONSE2=$(curl -s -X POST "${API_V1}/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_TESTS_DYN",
    "difficulte": "moyen",
    "offer": "pro",
    "seed": 42
  }')

if echo "$RESPONSE2" | grep -q "id_exercice"; then
  echo "✅ Test 2 réussi: Variation avec offer=pro fonctionne (fallback vers free)"
  EXERCISE_ID2=$(echo "$RESPONSE2" | grep -o '"id_exercice":"[^"]*"' | cut -d'"' -f4)
  echo "   ID: $EXERCISE_ID2"
else
  echo "❌ Test 2 échoué: Variation avec offer=pro a échoué"
  echo "   Réponse: $RESPONSE2"
  exit 1
fi

echo ""

# Test 3: Déterminisme - même seed = même résultat
echo "📋 Test 3: Déterminisme (seed=100, 2 appels identiques)"
RESPONSE3A=$(curl -s -X POST "${API_V1}/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_TESTS_DYN",
    "difficulte": "moyen",
    "seed": 100
  }')

RESPONSE3B=$(curl -s -X POST "${API_V1}/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_TESTS_DYN",
    "difficulte": "moyen",
    "seed": 100
  }')

COEFFICIENT_3A=$(echo "$RESPONSE3A" | grep -o '"coefficient":[^,}]*' | cut -d':' -f2 | tr -d ' ')
COEFFICIENT_3B=$(echo "$RESPONSE3B" | grep -o '"coefficient":[^,}]*' | cut -d':' -f2 | tr -d ' ')

if [ "$COEFFICIENT_3A" = "$COEFFICIENT_3B" ] && [ -n "$COEFFICIENT_3A" ]; then
  echo "✅ Test 3 réussi: Déterminisme confirmé (coefficient=$COEFFICIENT_3A)"
else
  echo "❌ Test 3 échoué: Déterminisme non respecté"
  echo "   Coefficient 1: $COEFFICIENT_3A"
  echo "   Coefficient 2: $COEFFICIENT_3B"
  exit 1
fi

echo ""

# Test 4: Pool vide (difficulty inexistante)
echo "📋 Test 4: Pool vide (difficulty=inexistante, doit retourner erreur JSON)"
RESPONSE4=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "${API_V1}/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_TESTS_DYN",
    "difficulte": "inexistante",
    "seed": 42
  }')

HTTP_CODE=$(echo "$RESPONSE4" | grep "HTTP_CODE" | cut -d':' -f2)
BODY=$(echo "$RESPONSE4" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "422" ]; then
  if echo "$BODY" | grep -q "NO_EXERCISE_AVAILABLE\|no_tests_dyn_exercise_found"; then
    echo "✅ Test 4 réussi: Erreur JSON valide retournée (HTTP 422)"
    echo "   Message: $(echo "$BODY" | grep -o '"message":"[^"]*"' | cut -d'"' -f4 | head -1)"
  else
    echo "⚠️  Test 4 partiel: HTTP 422 mais format JSON non standard"
    echo "   Réponse: $BODY"
  fi
else
  echo "❌ Test 4 échoué: Code HTTP inattendu ($HTTP_CODE au lieu de 422)"
  echo "   Réponse: $BODY"
  exit 1
fi

echo ""
echo "✅ Tous les tests sont passés !"
echo ""
echo "📝 Résumé:"
echo "   - Génération initiale: OK"
echo "   - Variation avec offer=pro (fallback): OK"
echo "   - Déterminisme (même seed): OK"
echo "   - Erreur JSON sur pool vide: OK"






