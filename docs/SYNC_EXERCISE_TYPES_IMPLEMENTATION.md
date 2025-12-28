# Implémentation: Synchronisation admin_exercises → exercise_types

## 📋 Résumé

Correction définitive du bug `NO_EXERCISE_AVAILABLE` causé par la désynchronisation entre `admin_exercises` et `exercise_types`.

## 📁 Fichiers créés

1. **`backend/constants/collections.py`**
   - Constantes centralisées pour les noms de collections
   - Guard rails contre les typos

2. **`backend/services/exercise_types_sync_service.py`**
   - Service de synchronisation automatique
   - Fonction `sync_admin_exercise_to_exercise_types()`
   - Idempotent (pas de doublon)

3. **`backend/scripts/sync_admin_to_exercise_types.py`**
   - Script de migration one-shot (backfill)
   - Support `--dry-run` et `--chapter`

4. **`backend/tests/test_exercise_types_sync.py`**
   - Tests pytest pour la synchronisation
   - Tests end-to-end avec l'API

5. **`backend/services/collection_guard_rails.py`**
   - Détection des typos dans les noms de collections
   - Vérification au démarrage

6. **`docs/sync_exercise_types.md`**
   - Documentation utilisateur

## 📝 Fichiers modifiés

1. **`backend/services/exercise_persistence_service.py`**
   - Import de `EXERCISES_COLLECTION` depuis `backend.constants.collections`

2. **`backend/routes/admin_exercises_routes.py`**
   - Ajout de la sync dans `create_exercise()` (POST)
   - Ajout de la sync dans `update_exercise()` (PUT)
   - Ajout de la notification dans `delete_exercise()` (DELETE)
   - Nouvel endpoint `/api/admin/collections/guard-rails`

3. **`backend/routes/mathalea_routes.py`**
   - Utilisation de `EXERCISE_TYPES_COLLECTION` depuis les constantes

## 🧪 Tests

### Tests unitaires

```bash
# Lancer les tests de synchronisation
docker exec -it le-maitre-mot-backend pytest backend/tests/test_exercise_types_sync.py -v
```

### Tests manuels

1. **Créer un exercice dynamique via l'admin**
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

2. **Vérifier que exercise_types est synchronisé**
   ```bash
   docker exec -it le-maitre-mot-mongo mongosh le_maitre_mot --eval '
     db.exercise_types.find(
       {chapter_code: "6E_N10", code_ref: "NOMBRES_ENTIERS_V1"},
       {_id: 0, chapter_code: 1, code_ref: 1, generator_kind: 1, source: 1}
     ).pretty()
   '
   ```

3. **Vérifier l'endpoint MathALÉA**
   ```bash
   curl -s "http://localhost:8000/api/mathalea/chapters/6E_N10/exercise-types" | jq '.total'
   # Devrait retourner >= 1
   ```

## 🚀 Migration one-shot

### Dry-run (recommandé)

```bash
docker exec -it le-maitre-mot-backend python -m backend.scripts.sync_admin_to_exercise_types --dry-run
```

### Appliquer la migration

```bash
docker exec -it le-maitre-mot-backend python -m backend.scripts.sync_admin_to_exercise_types
```

### Limiter à un chapitre

```bash
docker exec -it le-maitre-mot-backend python -m backend.scripts.sync_admin_to_exercise_types --chapter 6E_N10
```

## 🔍 Guard Rails

### Vérifier les guard rails

```bash
curl -s "http://localhost:8000/api/admin/collections/guard-rails" | jq
```

### Résultat attendu

```json
{
  "warnings": [],
  "errors": [],
  "status": "ok"
}
```

Si des warnings/errors sont présents, vérifier les collections MongoDB.

## ✅ Critères d'acceptation

- [x] Après POST admin exercise dynamique, GET `/api/mathalea/chapters/6E_N10/exercise-types` retourne l'item
- [x] Script migration peuple exercise_types sans duplication
- [x] Tests CI passent
- [x] Aucun renommage DB "chapter_code -> chaptercode" (on garde snake_case canonique)

## 🔧 Détails techniques

### Normalisation chapter_code

- Format canonique: `chapter_code` (snake_case)
- Normalisation: `upper()` + remplace `-` par `_`
- Exemple: `"6e-n10"` → `"6E_N10"`

### Structure exercise_type

- `id`: `"{chapter_code}_{generator_key}_{uuid8}"`
- `code_ref`: `generator_key`
- `chapter_code`: Normalisé
- `chapitre_id`: Fallback legacy (même valeur que chapter_code)
- `generator_kind`: `"DYNAMIC"`
- `source`: `"admin_exercises_auto_sync"`

### Idempotence

La synchronisation est idempotente:
- Si un document existe déjà (match sur `chapter_code` + `code_ref`), il est mis à jour
- Pas de doublon créé

## 📊 Impact

- **Avant**: `NO_EXERCISE_AVAILABLE` même avec des exercices en DB
- **Après**: Les exercices admin sont automatiquement visibles via l'endpoint MathALÉA

## 🔄 Rétrocompatibilité

- Les exercices existants continuent de fonctionner
- La migration est optionnelle (backfill)
- L'auto-sync fonctionne pour les nouveaux exercices même sans migration

