# Smoke Tests - Parcours Gratuit

## Vue d'ensemble

Le script `scripts/smoke_free_flow.sh` permet de tester automatiquement le parcours gratuit sans modifier le comportement runtime. Il vérifie que les endpoints critiques répondent correctement.

## Exécution

### Local (sans Docker)

```bash
./scripts/smoke_free_flow.sh
```

### Avec Docker

```bash
# Depuis la racine du projet
docker compose exec backend bash -c "cd /app && BACKEND_URL=http://localhost:8000 ./scripts/smoke_free_flow.sh"
```

### Variables d'environnement

- `BACKEND_URL` (défaut: `http://localhost:8000`) : URL du backend
- `FRONTEND_URL` (défaut: `http://localhost:3000`) : URL du frontend (non utilisée actuellement)

Exemple :

```bash
BACKEND_URL=http://localhost:8000 ./scripts/smoke_free_flow.sh
```

## Tests effectués

### Test 1: Catalog (GET)

- **Endpoint**: `GET /api/v1/curriculum/6e/catalog`
- **Timeout**: 10 secondes
- **Attendu**: HTTP 200 avec JSON valide contenant `level`

### Test 2: Generate (POST)

- **Endpoint**: `POST /api/v1/exercises/generate`
- **Timeout**: 30 secondes
- **Paramètres**:
  - `code_officiel`: `6e_N08` (chapitre non-test)
  - `difficulte`: `moyen`
  - `offer`: `free`
  - `seed`: `42` (déterministe)

**Résultats acceptés**:
- ✅ HTTP 200 : Exercice généré avec succès
- ✅ HTTP 422 structuré : Erreur métier avec `detail.error_code` (ex: `POOL_EMPTY`, `PLACEHOLDER_UNRESOLVED`)

**Résultats refusés**:
- ❌ HTTP 500 : Erreur serveur
- ❌ HTTP 422 non-structuré : Erreur sans `error_code` dans `detail`
- ❌ Timeout : Pas de réponse dans les 30 secondes

## Interprétation des résultats

### Sortie OK

```
==========================================
  Smoke Test - Parcours Gratuit
==========================================
Backend URL: http://localhost:8000
Frontend URL: http://localhost:3000
jq disponible: true

Test 1: GET /api/v1/curriculum/6e/catalog
----------------------------------------
✓ Catalog endpoint répond avec HTTP 200
✓ Réponse JSON valide (vérifiée avec jq)

Test 2: POST /api/v1/exercises/generate
----------------------------------------
  Chapitre: 6e_N08 (Fractions - chapitre non-test)
  Seed: 42 (déterministe)
  Offer: free
✓ Generate endpoint répond avec HTTP 200
✓ Exercice généré: ex_6e_fractions_1234567890

==========================================
  Résumé
==========================================
Tests réussis: 4
Tests échoués: 0
✓ Tous les tests sont passés
```

### Sortie avec erreur 422 structurée (acceptable)

```
Test 2: POST /api/v1/exercises/generate
----------------------------------------
  Chapitre: 6e_N08 (Fractions - chapitre non-test)
  Seed: 42 (déterministe)
  Offer: free
✓ HTTP 422 accepté (erreur structurée: error_code=POOL_EMPTY)
  Message: Aucun exercice disponible pour ce chapitre avec les critères demandés.
```

### Sortie avec erreur (non acceptable)

```
Test 2: POST /api/v1/exercises/generate
----------------------------------------
✗ HTTP 500 - Erreur serveur (attendu: HTTP 200 ou 422 structuré)
  Réponse: {"detail": "Erreur interne du serveur"}
```

## Détection de jq

Le script détecte automatiquement si `jq` est installé :
- **Avec jq** : Validation JSON stricte et extraction de champs
- **Sans jq** : Validation basique avec `grep`

## Codes de sortie

- `0` : Tous les tests sont passés
- `1` : Au moins un test a échoué

## Notes

- Le script utilise un seed fixe (42) pour garantir la reproductibilité
- Le chapitre testé (`6e_N08`) est un chapitre non-test du curriculum
- Les timeouts sont configurés pour éviter les blocages (10s pour catalog, 30s pour generate)
- Le script ne modifie pas le comportement runtime du backend






