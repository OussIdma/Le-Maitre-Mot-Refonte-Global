#!/bin/bash

# P0 BUNDLE - Tests de validation rapides
# Usage: ./scripts/test_p0_security.sh

API_URL="${API_URL:-http://localhost:8000/api}"

echo "🔐 P0 BUNDLE - Tests de sécurité"
echo "================================"
echo ""

# Test 1: Rate limiting sur /auth/request-login
echo "📊 Test 1: Rate limiting (5/15min)"
echo "Envoi de 6 requêtes consécutives..."
for i in {1..6}; do
  response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/request-login" \
    -H "Content-Type: application/json" \
    -d '{"email": "test-spam@example.com"}' 2>&1)
  
  status_code=$(echo "$response" | tail -n1)
  
  if [ $i -le 5 ]; then
    if [ "$status_code" = "200" ]; then
      echo "  ✅ Tentative $i/6: 200 OK (attendu)"
    else
      echo "  ❌ Tentative $i/6: $status_code (erreur, 200 attendu)"
    fi
  else
    if [ "$status_code" = "429" ]; then
      echo "  ✅ Tentative $i/6: 429 Too Many Requests (attendu)"
    else
      echo "  ❌ Tentative $i/6: $status_code (erreur, 429 attendu)"
    fi
  fi
done

echo ""

# Test 2: Réponse neutre (anti-énumération)
echo "🕵️  Test 2: Réponse neutre (anti-énumération)"
echo "Test avec email inexistant..."
response1=$(curl -s -X POST "$API_URL/auth/request-login" \
  -H "Content-Type: application/json" \
  -d '{"email": "nexistepas@test.com"}')

message1=$(echo "$response1" | grep -o "Si un compte Pro existe" | head -1)

if [ -n "$message1" ]; then
  echo "  ✅ Message neutre retourné (anti-énumération OK)"
else
  echo "  ❌ Message non-neutre détecté (RISQUE)"
fi

echo ""

# Test 3: Checkout sans session → 401
echo "🔒 Test 3: Checkout sans session (401 attendu)"
response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/checkout/session" \
  -H "Content-Type: application/json" \
  -d '{"package_id": "monthly", "origin_url": "http://localhost:3000"}' 2>&1)

status_code=$(echo "$response" | tail -n1)

if [ "$status_code" = "401" ]; then
  echo "  ✅ 401 Unauthorized (attendu, session requise)"
else
  echo "  ❌ $status_code (erreur, 401 attendu)"
fi

echo ""

# Test 4: Endpoint /auth/me accessible
echo "🔍 Test 4: Endpoint /auth/me existe"
response=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/auth/me" 2>&1)
status_code=$(echo "$response" | tail -n1)

if [ "$status_code" = "401" ]; then
  echo "  ✅ Endpoint accessible (401 car pas de session, normal)"
elif [ "$status_code" = "404" ]; then
  echo "  ❌ Endpoint introuvable (404)"
else
  echo "  ℹ️  Status: $status_code"
fi

echo ""

# Test 5: Pre-checkout endpoint existe
echo "📧 Test 5: Endpoint /auth/pre-checkout existe"
response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/pre-checkout" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "package_id": "monthly"}' 2>&1)

status_code=$(echo "$response" | tail -n1)

if [ "$status_code" = "200" ]; then
  echo "  ✅ 200 OK (endpoint fonctionne)"
else
  echo "  ❌ $status_code (erreur, 200 attendu)"
fi

echo ""
echo "================================"
echo "🎉 Tests P0 terminés"
echo ""
echo "Note: Pour un test complet, consulter P0_BUNDLE_SECURITY_VALIDATION.md"







