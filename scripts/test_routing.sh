#!/bin/bash
# Test de routing - vérifie que les redirections fonctionnent

BASE_URL="${1:-http://localhost:3000}"

echo "🧪 Test de routing sur $BASE_URL..."
echo ""

# Test 1: Landing page
echo "1. Test / → Landing page"
if curl -s "$BASE_URL/" | grep -q "Générer des exercices"; then
  echo "   ✅ Landing OK"
else
  echo "   ❌ Landing KO"
fi

# Test 2: Redirection /generate → /generer
echo "2. Test /generate → /generer"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -L "$BASE_URL/generate")
if [ "$STATUS" = "200" ]; then
  echo "   ✅ Redirection /generate OK"
else
  echo "   ❌ Redirection /generate KO (status: $STATUS)"
fi

# Test 3: Redirection /Générer → /generer
echo "3. Test /Générer → /generer"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -L "$BASE_URL/Générer")
if [ "$STATUS" = "200" ]; then
  echo "   ✅ Redirection /Générer OK"
else
  echo "   ❌ Redirection /Générer KO (status: $STATUS)"
fi

# Test 4: Route inconnue → /generer
echo "4. Test route inconnue → /generer"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -L "$BASE_URL/route-inexistante")
if [ "$STATUS" = "200" ]; then
  echo "   ✅ Redirection route inconnue OK"
else
  echo "   ❌ Redirection route inconnue KO (status: $STATUS)"
fi

# Test 5: Page /generer accessible
echo "5. Test /generer accessible"
if curl -s "$BASE_URL/generer" | grep -q "Générateur\|Exercice"; then
  echo "   ✅ Page /generer accessible"
else
  echo "   ❌ Page /generer non accessible"
fi

echo ""
echo "✅ Tests terminés"
echo ""
echo "💡 Pour tester manuellement :"
echo "   - Ouvrir $BASE_URL/"
echo "   - Cliquer sur 'Générer des exercices'"
echo "   - Vérifier la NavBar en haut"
echo "   - Tester les redirections : /Générer, /generate, /route-inexistante"

