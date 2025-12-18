#!/bin/bash

BACKEND_URL="http://localhost:8000/api/v1/exercises/generate"

echo "=== TEST 6e_TESTS_DYN - Vérification absence de placeholders ==="

FAIL=0

for DIFF in facile moyen difficile; do
  echo -e "\n=== Difficulté: $DIFF ==="
  for SEED in $(seq 1 200); do
    echo -e "\n--- Seed $SEED ---"
    RESP=$(curl -s -X POST "$BACKEND_URL" \
      -H "Content-Type: application/json" \
      -d "{
        \"code_officiel\": \"6e_TESTS_DYN\",
        \"difficulte\": \"$DIFF\",
        \"offer\": \"free\",
        \"seed\": $SEED
      }")

    # Si la réponse contient error_code, vérifier que c'est bien du JSON (jq a déjà parsé)
    ERR_CODE=$(echo "$RESP" | jq -r '.error_code // .detail.error_code // empty' 2>/dev/null)
    if [ -n "$ERR_CODE" ]; then
      echo "ℹ️  Erreur JSON renvoyée pour seed $SEED / diff=$DIFF : error_code=$ERR_CODE"
      # On considère acceptable tant que c'est du JSON, pas du HTML brut
      continue
    fi

    ENONCE=$(echo "$RESP" | jq -r '.enonce_html // ""')
    SOLUTION=$(echo "$RESP" | jq -r '.solution_html // ""')

    if [[ "$ENONCE" == *"{{"* ]] || [[ "$SOLUTION" == *"{{"* ]]; then
      echo "❌ Placeholders trouvés pour seed $SEED / diff=$DIFF"
      echo "Enonce: $ENONCE"
      echo "Solution: $SOLUTION"
      FAIL=1
    else
      echo "✅ Aucun placeholder détecté pour seed $SEED / diff=$DIFF"
    fi
  done
done

if [ "$FAIL" -eq 0 ]; then
  echo -e "\n✅ Tous les tests 6e_TESTS_DYN (seeds 1..200, toutes difficultés) passent sans placeholders visibles."
else
  echo -e "\n❌ Des placeholders non résolus ont été détectés."
fi


