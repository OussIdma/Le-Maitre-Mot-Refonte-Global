# ✅ Résumé: Correction bug NO_EXERCISE_AVAILABLE

## 🎯 Objectif

Corriger définitivement le bug `NO_EXERCISE_AVAILABLE` causé par la désynchronisation entre:
- `admin_exercises` (écrit par l'admin UI)
- `exercise_types` (lu par l'endpoint MathALÉA)

## 📦 Fichiers créés (6)

1. **`backend/constants/collections.py`** - Constantes centralisées
2. **`backend/services/exercise_types_sync_service.py`** - Service de sync
3. **`backend/scripts/sync_admin_to_exercise_types.py`** - Script migration
4. **`backend/tests/test_exercise_types_sync.py`** - Tests pytest
5. **`backend/services/collection_guard_rails.py`** - Guard rails
6. **`docs/sync_exercise_types.md`** - Documentation

## 📝 Fichiers modifiés (3)

1. **`backend/services/exercise_persistence_service.py`**
   - Import `EXERCISES_COLLECTION` depuis constantes

2. **`backend/routes/admin_exercises_routes.py`**
   - Sync auto dans `create_exercise()` (POST)
   - Sync auto dans `update_exercise()` (PUT)
   - Notification dans `delete_exercise()` (DELETE)
   - Endpoint `/api/admin/collections/guard-rails`

3. **`backend/routes/mathalea_routes.py`**
   - Utilisation constantes pour collections

## 🧪 Tests

### Tests unitaires
```bash
docker exec -it le-maitre-mot-backend pytest backend/tests/test_exercise_types_sync.py -v
```

### Test manuel end-to-end

1. **Créer un exercice dynamique**
   ```bash
   curl -X POST "http://localhost:8000/api/admin/chapters/6E_N10/exercises" \
     -H "Content-Type: application/json" \
     -d '{
       "is_dynamic": true,
       "generator_key": "NOMBRES_ENTIERS_V1",
       "difficulty": "facile",
       "offer": "free",
       "enonce_template_html": "<p>{{enonce}}</p>",
       "solution_template_html": "<p>Réponse: {{reponse_finale}}</p>"
     }'
   ```

2. **Vérifier exercise_types**
   ```bash
   docker exec -it le-maitre-mot-mongo mongosh le_maitre_mot --eval '
     db.exercise_types.find(
       {chapter_code: "6E_N10", code_ref: "NOMBRES_ENTIERS_V1"},
       {_id: 0, chapter_code: 1, code_ref: 1, generator_kind: 1}
     ).pretty()
   '
   ```

3. **Vérifier endpoint MathALÉA**
   ```bash
   curl -s "http://localhost:8000/api/mathalea/chapters/6E_N10/exercise-types" | jq '.total'
   # Devrait retourner >= 1
   ```

## 🚀 Migration one-shot (backfill)

```bash
# Dry-run
docker exec -it le-maitre-mot-backend python -m backend.scripts.sync_admin_to_exercise_types --dry-run

# Appliquer
docker exec -it le-maitre-mot-backend python -m backend.scripts.sync_admin_to_exercise_types

# Un chapitre spécifique
docker exec -it le-maitre-mot-backend python -m backend.scripts.sync_admin_to_exercise_types --chapter 6E_N10
```

## 🔍 Guard Rails

```bash
curl -s "http://localhost:8000/api/admin/collections/guard-rails" | jq
```

## ✅ Critères d'acceptation

- ✅ Après POST admin exercise dynamique, GET `/api/mathalea/chapters/6E_N10/exercise-types` retourne l'item
- ✅ Script migration peuple exercise_types sans duplication
- ✅ Tests CI passent
- ✅ Aucun renommage DB "chapter_code -> chaptercode" (on garde snake_case canonique)

## 🔧 Détails techniques

- **Normalisation**: `chapter_code` → `upper()` + remplace `-` par `_`
- **Idempotence**: Pas de doublon (match sur `chapter_code` + `code_ref`)
- **Format canonique**: `chapter_code` (snake_case) partout

## 📊 Impact

- **Avant**: `NO_EXERCISE_AVAILABLE` même avec exercices en DB
- **Après**: Auto-sync automatique, exercices visibles via MathALÉA

