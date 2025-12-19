#!/usr/bin/env bash
set -euo pipefail

# Simple healthcheck script for local Le Maitre Mot backend
# Usage: ./scripts/healthcheck.sh [base_url]
# Example: ./scripts/healthcheck.sh http://localhost:8000

BASE_URL="${1:-http://localhost:8000}"

echo "=== Healthcheck against ${BASE_URL} ==="

echo
echo "1) GET /api/debug/build"
curl -s -w "\nHTTP %{http_code}\n\n" "${BASE_URL}/api/debug/build" || {
  echo "❌ /api/debug/build failed"
  exit 1
}

echo "2) POST /api/admin/exercises/preview-dynamic (THALES_V1)"
curl -s -w "\nHTTP %{http_code}\n\n" \
  -H "Content-Type: application/json" \
  -d '{
    "generator_key": "THALES_V1",
    "enonce_template_html": "<p>Test THALES_V1 coefficient {{coefficient_str}}</p>",
    "solution_template_html": "<p>Solution de test</p>",
    "difficulty": "moyen",
    "seed": 1,
    "svg_mode": "AUTO"
  }' \
  "${BASE_URL}/api/admin/exercises/preview-dynamic" || {
    echo "❌ /api/admin/exercises/preview-dynamic (THALES_V1) failed"
    exit 1
  }

echo "3) POST /api/v1/exercises/generate (6e_TESTS_DYN)"
curl -s -w "\nHTTP %{http_code}\n\n" \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_TESTS_DYN",
    "difficulte": "moyen",
    "offer": "free",
    "seed": 1
  }' \
  "${BASE_URL}/api/v1/exercises/generate" || {
    echo "❌ /api/v1/exercises/generate (6e_TESTS_DYN) failed"
    exit 1
  }

echo "✅ Healthcheck completed successfully"





