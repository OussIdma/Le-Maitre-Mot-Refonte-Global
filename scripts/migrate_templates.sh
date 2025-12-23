#!/bin/bash
# Script de migration des templates legacy → DB
# Usage: ./scripts/migrate_templates.sh [--dry-run]

set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

echo "================================================================================"
echo "MIGRATION DES TEMPLATES LEGACY → MONGODB"
echo "================================================================================"
echo ""
echo "Backend URL: $BACKEND_URL"
echo "Mode: $([ "$DRY_RUN" = true ] && echo 'DRY-RUN (aucune création)' || echo 'PRODUCTION (création réelle)')"
echo ""

TOTAL=0
CREATED=0
SKIPPED=0
ERRORS=0

# Template RAISONNEMENT_MULTIPLICATIF_V1
echo "────────────────────────────────────────────────────────────────────────────────"
echo "📦 RAISONNEMENT_MULTIPLICATIF_V1"
echo "────────────────────────────────────────────────────────────────────────────────"

TOTAL=$((TOTAL + 1))

PAYLOAD=$(cat <<'EOF'
{
  "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
  "variant_id": "default",
  "grade": null,
  "difficulty": null,
  "enonce_template_html": "<div class=\"exercise-enonce\">\n  <p><strong>{{consigne}}</strong></p>\n  <p>{{enonce}}</p>\n  {{{tableau_html}}}\n</div>",
  "solution_template_html": "<div class=\"exercise-solution\">\n  <h4 style=\"color: #2563eb; margin-bottom: 1rem;\">Méthode : {{methode}}</h4>\n  <div class=\"calculs\" style=\"background: #f1f5f9; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;\">\n    <pre style=\"white-space: pre-line; font-family: inherit; margin: 0;\">{{calculs_intermediaires}}</pre>\n  </div>\n  <div class=\"solution-text\" style=\"margin-bottom: 1rem;\">\n    <p>{{solution}}</p>\n  </div>\n  <div class=\"reponse-finale\" style=\"background: #dcfce7; padding: 0.75rem; border-left: 4px solid #22c55e; border-radius: 0.25rem;\">\n    <p style=\"margin: 0;\"><strong>Réponse finale :</strong> {{reponse_finale}}</p>\n  </div>\n</div>",
  "allowed_html_vars": ["tableau_html"]
}
EOF
)

if [ "$DRY_RUN" = false ]; then
  RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/admin/generator-templates" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    -w "\n%{http_code}")
  
  HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
  
  if [[ "$HTTP_CODE" == "201" ]]; then
    echo "✅ Template créé"
    CREATED=$((CREATED + 1))
  elif [[ "$HTTP_CODE" == "409" ]] || [[ "$HTTP_CODE" == "400" ]]; then
    echo "⏭️  Template existe déjà → SKIP"
    SKIPPED=$((SKIPPED + 1))
  else
    echo "❌ Erreur HTTP $HTTP_CODE"
    ERRORS=$((ERRORS + 1))
  fi
else
  echo "✅ Template serait créé (dry-run)"
  CREATED=$((CREATED + 1))
fi

# Template CALCUL_NOMBRES_V1
echo ""
echo "────────────────────────────────────────────────────────────────────────────────"
echo "📦 CALCUL_NOMBRES_V1"
echo "────────────────────────────────────────────────────────────────────────────────"

TOTAL=$((TOTAL + 1))

PAYLOAD=$(cat <<'EOF'
{
  "generator_key": "CALCUL_NOMBRES_V1",
  "variant_id": "default",
  "grade": null,
  "difficulty": null,
  "enonce_template_html": "<div class=\"exercise-enonce\">\n  <p><strong>{{consigne}}</strong></p>\n  <div class=\"enonce-content\" style=\"font-size: 1.125rem; margin-top: 0.5rem;\">{{enonce}}</div>\n</div>",
  "solution_template_html": "<div class=\"exercise-solution\">\n  <h4 style=\"color: #2563eb; margin-bottom: 1rem;\">Correction</h4>\n  <div class=\"calculs\" style=\"background: #f1f5f9; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;\">\n    <pre style=\"white-space: pre-line; font-family: inherit; margin: 0;\">{{calculs_intermediaires}}</pre>\n  </div>\n  <div class=\"solution-text\" style=\"margin-bottom: 1rem;\">\n    <p>{{solution}}</p>\n  </div>\n  <div class=\"reponse-finale\" style=\"background: #dcfce7; padding: 0.75rem; border-left: 4px solid #22c55e; border-radius: 0.25rem;\">\n    <p style=\"margin: 0;\"><strong>Résultat :</strong> {{reponse_finale}}</p>\n  </div>\n</div>",
  "allowed_html_vars": []
}
EOF
)

if [ "$DRY_RUN" = false ]; then
  RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/admin/generator-templates" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    -w "\n%{http_code}")
  
  HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
  
  if [[ "$HTTP_CODE" == "201" ]]; then
    echo "✅ Template créé"
    CREATED=$((CREATED + 1))
  elif [[ "$HTTP_CODE" == "409" ]] || [[ "$HTTP_CODE" == "400" ]]; then
    echo "⏭️  Template existe déjà → SKIP"
    SKIPPED=$((SKIPPED + 1))
  else
    echo "❌ Erreur HTTP $HTTP_CODE"
    ERRORS=$((ERRORS + 1))
  fi
else
  echo "✅ Template serait créé (dry-run)"
  CREATED=$((CREATED + 1))
fi

# Template SIMPLIFICATION_FRACTIONS_V2
echo ""
echo "────────────────────────────────────────────────────────────────────────────────"
echo "📦 SIMPLIFICATION_FRACTIONS_V2"
echo "────────────────────────────────────────────────────────────────────────────────"

TOTAL=$((TOTAL + 1))

PAYLOAD=$(cat <<'EOF'
{
  "generator_key": "SIMPLIFICATION_FRACTIONS_V2",
  "variant_id": "default",
  "grade": null,
  "difficulty": null,
  "enonce_template_html": "<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>",
  "solution_template_html": "<ol>\n  <li>{{step1}}</li>\n  <li>{{step2}}</li>\n  <li>{{step3}}</li>\n  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>\n</ol>",
  "allowed_html_vars": []
}
EOF
)

if [ "$DRY_RUN" = false ]; then
  RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/admin/generator-templates" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    -w "\n%{http_code}")
  
  HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
  
  if [[ "$HTTP_CODE" == "201" ]]; then
    echo "✅ Template créé"
    CREATED=$((CREATED + 1))
  elif [[ "$HTTP_CODE" == "409" ]] || [[ "$HTTP_CODE" == "400" ]]; then
    echo "⏭️  Template existe déjà → SKIP"
    SKIPPED=$((SKIPPED + 1))
  else
    echo "❌ Erreur HTTP $HTTP_CODE"
    ERRORS=$((ERRORS + 1))
  fi
else
  echo "✅ Template serait créé (dry-run)"
  CREATED=$((CREATED + 1))
fi

# Résumé
echo ""
echo "================================================================================"
echo "RÉSUMÉ DE LA MIGRATION"
echo "================================================================================"
echo "Total templates: $TOTAL"
echo "✅ Créés: $CREATED"
echo "⏭️  Skippés: $SKIPPED"
echo "❌ Erreurs: $ERRORS"
echo ""

if [ "$DRY_RUN" = true ]; then
  echo "ℹ️  Mode DRY-RUN : Aucun template n'a été créé"
  echo "   Relancez sans --dry-run pour effectuer la migration réelle"
else
  if [ "$CREATED" -gt 0 ]; then
    echo "✅ Migration terminée avec succès"
    echo "   Les templates sont maintenant disponibles en DB"
    echo "   L'API /generate utilisera automatiquement ces templates (template_source='db')"
  else
    echo "⚠️  Aucun template créé (tous skippés ou erreurs)"
  fi
fi

echo ""

if [ "$ERRORS" -gt 0 ]; then
  exit 1
else
  exit 0
fi

