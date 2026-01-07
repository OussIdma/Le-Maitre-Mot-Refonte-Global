# REPORT_STATUS.md - Le Maitre Mot V1

**Date**: 2026-01-04
**Objectif**: Stabiliser V1 pour livraison rapide
**Statut**: CORRIGE - Backend opérationnel

---

## 1. Architecture

```
le-maitre-mot/
├── backend/                 # FastAPI Python 3.11
│   ├── server.py           # Point d'entrée principal (~7100 lignes)
│   ├── routes/             # Endpoints API modulaires
│   │   ├── exercises_routes.py      # POST /generate, /reroll-data, /new-exercise
│   │   ├── user_sheets_routes.py    # CRUD fiches utilisateur
│   │   ├── curriculum_catalog_routes.py  # Catalogue curriculum
│   │   └── admin_*.py               # Endpoints admin
│   ├── services/           # Logique métier
│   ├── generators/         # Générateurs d'exercices (factory pattern)
│   └── engine/pdf_engine/  # Export PDF WeasyPrint
├── frontend/               # React (Create React App)
│   └── src/components/     # Pages et composants UI
├── docker-compose.yml      # Orchestration Docker
└── Dockerfile (backend)    # Image Python + dépendances système
```

**Base de données**: MongoDB 7.0 (container `le-maitre-mot-mongo`)

---

## 2. Endpoints Clés V1 - Statut APRES CORRECTIONS

| Endpoint | Méthode | Statut | Notes |
|----------|---------|--------|-------|
| `/api/health` | GET | **OK** | Backend healthy |
| `/api/v1/curriculum/6e/catalog` | GET | **OK** | Catalogue 6e fonctionnel |
| `/api/v1/exercises/generate` | POST | **OK** | Génération OK (fallback si pas d'exercices DB) |
| `/api/v1/exercises/reroll-data` | POST | **OK** | Régénération avec même template |
| `/api/v1/exercises/new-exercise` | POST | **OK** | Nouveau exercice |
| `/api/user/sheets/create-from-selection` | POST | **OK** | Requiert auth (401 sans token) |
| `/api/v1/sheets/export-selection` | POST | **OK** | Requiert auth (401 sans token) |

---

## 3. Bugs Corrigés (P0)

### FIX A - Docker Build Backend
**Fichier**: `backend/Dockerfile`
**Correction appliquée**:
- Remplacé `libgdk-pixbuf2.0-0` par `libgdk-pixbuf-2.0-0`
- Supprimé doublon `libpangoft2-1.0-0`

**Résultat**: `docker compose build backend` ✅

---

### FIX B - Code Diagnostic Mal Placé
**Fichier**: `backend/routes/exercises_routes.py`
**Correction appliquée**:
- Supprimé bloc de retours tuples (lignes 1254-1270 originales)
- Créé fonction helper `_execute_generation_pipeline()` avec vraie logique
- `generate_exercise` appelle maintenant ce helper

**Résultat**: `/api/v1/exercises/generate` retourne JSON valide ✅

---

### FIX C - Routes Dupliquées
**Fichier**: `backend/routes/exercises_routes.py`
**Correction appliquée**:
- Supprimé les définitions dupliquées de `/reroll-data` et `/new-exercise`
- Fichier réduit de 4461 à 4127 lignes

**Résultat**: Plus de conflits de routes ✅

---

### FIX D - ensure_system_dependencies.py
**Statut**: Déjà fonctionnel
- Détection Docker + no-op dans container

---

### FIX E - Fonction resolve_pipeline manquante
**Fichier**: `backend/routes/exercises_routes.py`
**Correction appliquée**:
- Ajouté la fonction `resolve_pipeline()` qui était appelée mais non définie
- Fonction copiée depuis `admin_diagnostics_routes.py`
- Ajouté `await` à l'appel de `resolve_pipeline` (fonction async)

**Résultat**: Pipeline résolu correctement pour chaque requête ✅

---

### FIX F - Appels async GM07/GM08 mal formés
**Fichier**: `backend/routes/exercises_routes.py`
**Correction appliquée**:
- Ajouté `await` et `db=db` aux appels de `generate_gm07_exercise()` et `generate_gm08_exercise()`
- Importé `db` en début de `generate_exercise_wrapper()`

**Résultat**: Génération GM07/GM08 fonctionnelle ✅

---

### FIX G - Imports HTTPException locaux
**Fichier**: `backend/routes/exercises_routes.py`
**Correction appliquée**:
- Supprimé tous les `from fastapi import HTTPException` locaux (déjà importé globalement)
- Corrige l'erreur "cannot access local variable 'HTTPException'"

**Résultat**: Gestion des exceptions propre ✅

---

### FIX H - Fallback pour exercices non disponibles
**Fichier**: `backend/routes/exercises_routes.py`
**Correction appliquée**:
- Ajouté try-except autour de l'appel à `generate_exercise_wrapper`
- Si `NO_EXERCISE_AVAILABLE`, retourne un exercice fallback avec message clair

**Résultat**: Plus d'erreurs 422, fallback gracieux ✅

---

## 4. Commandes de Validation

```bash
# Vérifier que tout est up
docker compose ps

# Test health
curl http://localhost:8000/api/health
# {"status":"healthy"...}

# Test catalogue
curl http://localhost:8000/api/v1/curriculum/6e/catalog | head -c 200
# {"level":"6e","domains":[...]}

# Test génération (chapitre avec exercices dynamiques)
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel":"6e_TESTS_DYN","difficulte":"facile","seed":123}'
# {"id_exercice":"ex_6e_tests_dyn_...", "enonce_html":"<p><strong>Agrandissement d'un carré...</p>"}

# Test génération (chapitre sans exercices - fallback)
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel":"6e_N10","difficulte":"facile","seed":123}'
# {"id_exercice":"fallback_6E_N10_...", "metadata":{"is_fallback":true}}

# Test reroll-data
curl -X POST http://localhost:8000/api/v1/exercises/reroll-data \
  -H "Content-Type: application/json" \
  -d '{"generator_key":"THALES_V1","template_id":"default","seed":456}'
# {"id_exercice":"reroll_THALES_V1_...", "enonce_html":"..."}

# Test new-exercise
curl -X POST http://localhost:8000/api/v1/exercises/new-exercise \
  -H "Content-Type: application/json" \
  -d '{"generator_key":"THALES_V1","seed":789}'
# {"id_exercice":"new_THALES_V1_...", "enonce_html":"..."}

# Test auth required pour export
curl -X POST http://localhost:8000/api/v1/sheets/export-selection \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","layout":"classic","include_correction":true,"exercises":[]}'
# {"detail":{"error":"AUTH_REQUIRED_EXPORT"...}}
```

---

## 5. Fichiers Modifiés

| Fichier | Modification |
|---------|--------------|
| `backend/Dockerfile` | Fix packages apt (libgdk-pixbuf-2.0-0) |
| `backend/routes/exercises_routes.py` | Suppression code mort, création helper `_execute_generation_pipeline`, déduplication routes |
| `REPORT_STATUS.md` | Ce fichier - rapport d'état |

---

## 6. Checklist Tests V1

### Tests Automatisés Recommandés
```bash
# Smoke tests API
pytest backend/tests/test_smoke_api_p0.py -v

# Tests E2E
pytest backend/tests/test_e2e_v1_flow.py -v

# Tests reroll
pytest backend/tests/test_reroll_endpoints.py -v
```

### Tests Manuels UX
1. [x] Backend démarre: `docker compose up -d backend`
2. [x] Health OK: `curl http://localhost:8000/api/health`
3. [x] Catalogue OK: `/api/v1/curriculum/6e/catalog`
4. [x] Génération OK: `/api/v1/exercises/generate`
5. [x] Reroll OK: `/api/v1/exercises/reroll-data`
6. [x] New Exercise OK: `/api/v1/exercises/new-exercise`
7. [x] Sauvegarde fiche requiert auth: `/api/user/sheets/create-from-selection`
8. [x] Export PDF requiert auth: `/api/v1/sheets/export-selection`

---

## 7. Notes pour la Suite

### À faire ultérieurement (non bloquant V1)
- Nettoyer les imports dupliqués dans le code (plusieurs `from backend.server import db`)
- Supprimer `GenerateExerciseRequestWithQueryParams` (classe non utilisée)
- Ajouter des exercices en DB pour les chapitres `6e_N10`, `6e_GM07`, `6e_GM08`

### Points d'attention
- **Chapitres avec vrais exercices**: `6e_TESTS_DYN` génère des exercices dynamiques complets avec SVG
- **Fallback gracieux**: Les chapitres sans exercices retournent un message clair au lieu d'une erreur
- L'authentification est requise pour export PDF et sauvegarde fiches

### Générateurs disponibles
- `THALES_V1` : Agrandissement/réduction de figures (carré, rectangle, triangle)
- Plus de générateurs disponibles via `GeneratorFactory`

---

*Rapport mis à jour: 2026-01-04 - Backend V1 stabilisé et testé*
