#!/bin/bash

BACKEND_URL="http://localhost:8000/api/v1/exercises/generate"

echo "=== TEST 6e_TESTS_DYN - Vérification absence de placeholders ==="

FAIL=0

for SEED in $(seq 1 30); do
  echo -e "\n--- Seed $SEED ---"
  RESP=$(curl -s -X POST "$BACKEND_URL" \
    -H "Content-Type: application/json" \
    -d "{
      \"code_officiel\": \"6e_TESTS_DYN\",
      \"difficulte\": \"moyen\",
      \"offer\": \"free\",
      \"seed\": $SEED
    }")

  # Vérifier erreur JSON
  if echo "$RESP" | jq -e '.detail.error_code == "UNRESOLVED_PLACEHOLDERS"' >/dev/null 2>&1; then
    echo "❌ UNRESOLVED_PLACEHOLDERS pour seed $SEED"
    echo "$RESP" | jq '.detail'
    FAIL=1
    continue
  fi

  ENONCE=$(echo "$RESP" | jq -r '.enonce_html // ""')
  SOLUTION=$(echo "$RESP" | jq -r '.solution_html // ""')

  if [[ "$ENONCE" == *"{{"* ]] || [[ "$SOLUTION" == *"{{"* ]]; then
    echo "❌ Placeholders trouvés pour seed $SEED"
    echo "Enonce: $ENONCE"
    echo "Solution: $SOLUTION"
    FAIL=1
  else
    echo "✅ Aucun placeholder détecté pour seed $SEED"
  fi
done

if [ "$FAIL" -eq 0 ]; then
  echo -e "\n✅ Tous les tests 6e_TESTS_DYN passent sans placeholders visibles."
else
  echo -e "\n❌ Des placeholders non résolus ont été détectés."
fi


