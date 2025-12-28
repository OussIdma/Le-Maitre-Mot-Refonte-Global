# Synchronisation admin_exercises → exercise_types

## Problème résolu

Les exercices créés via l'admin UI étaient écrits dans `admin_exercises`, mais l'endpoint MathALÉA `/api/mathalea/chapters/{chapter_code}/exercise-types` lit dans `exercise_types`. 

Résultat: `NO_EXERCISE_AVAILABLE` même si des exercices existaient.

## Solution

Auto-sync automatique: quand un exercice dynamique est créé/modifié dans `admin_exercises`, un document correspondant est automatiquement synchronisé dans `exercise_types`.

## Architecture

### Service de synchronisation

**Fichier**: `backend/services/exercise_types_sync_service.py`

- `sync_admin_exercise_to_exercise_types()`: Synchronise un exercice admin vers exercise_types
- Idempotent: ne crée pas de doublon si le document existe déjà
- Normalise `chapter_code`: `upper()` + remplace `-` par `_`

### Intégration dans les routes admin

**Fichier**: `backend/routes/admin_exercises_routes.py`

- **POST** `/api/admin/chapters/{chapter_code}/exercises`: Sync automatique après création
- **PUT** `/api/admin/chapters/{chapter_code}/exercises/{exercise_id}`: Sync automatique après mise à jour
- **DELETE**: Notification (pas de suppression pour compatibilité)

### Script de migration one-shot

**Fichier**: `backend/scripts/sync_admin_to_exercise_types.py`

Backfill tous les exercices dynamiques existants.

## Utilisation

### Migration one-shot (backfill)

```bash
# Dry-run (voir ce qui serait fait)
docker exec -it le-maitre-mot-backend python -m backend.scripts.sync_admin_to_exercise_types --dry-run

# Appliquer la migration
docker exec -it le-maitre-mot-backend python -m backend.scripts.sync_admin_to_exercise_types

# Limiter à un chapitre spécifique
docker exec -it le-maitre-mot-backend python -m backend.scripts.sync_admin_to_exercise_types --chapter 6E_N10
```

### Vérification

```bash
# Vérifier que exercise_types contient les exercices
docker exec -it le-maitre-mot-mongo mongosh le_maitre_mot --eval '
  db.exercise_types.find(
    {chapter_code: "6E_N10"},
    {_id: 0, chapter_code: 1, code_ref: 1, generator_kind: 1}
  ).pretty()
'

# Tester l'endpoint MathALÉA
curl -s "http://localhost:8000/api/mathalea/chapters/6E_N10/exercise-types" | jq '.total'
```

### Tests

```bash
# Lancer les tests de synchronisation
docker exec -it le-maitre-mot-backend pytest backend/tests/test_exercise_types_sync.py -v
```

## Structure des documents

### admin_exercises

```json
{
  "chapter_code": "6E_N10",
  "id": 1,
  "is_dynamic": true,
  "generator_key": "NOMBRES_ENTIERS_V1",
  "needs_svg": false,
  ...
}
```

### exercise_types (synchronisé)

```json
{
  "id": "6E_N10_NOMBRES_ENTIERS_V1_abc12345",
  "code_ref": "NOMBRES_ENTIERS_V1",
  "chapter_code": "6E_N10",
  "chapitre_id": "6E_N10",
  "niveau": "6e",
  "domaine": "Nombres et calculs",
  "generator_kind": "DYNAMIC",
  "difficulty_levels": ["facile", "moyen", "difficile"],
  "min_questions": 1,
  "max_questions": 10,
  "default_questions": 5,
  "requires_svg": false,
  "source": "admin_exercises_auto_sync",
  "created_at": "2025-12-28T...",
  "updated_at": "2025-12-28T..."
}
```

## Guard Rails

Le système détecte automatiquement les typos dans les noms de collections:

- Collection `adminexercises` (sans underscore) → Warning
- Collection `admin_exercises` (correct) → OK

Les guard rails sont loggés au démarrage du serveur.

## Constantes centralisées

**Fichier**: `backend/constants/collections.py`

Tous les noms de collections sont centralisés pour éviter les typos:

- `EXERCISES_COLLECTION = "admin_exercises"`
- `EXERCISE_TYPES_COLLECTION = "exercise_types"`

## Critères d'acceptation

✅ Après POST admin exercise dynamique, GET `/api/mathalea/chapters/6E_N10/exercise-types` retourne l'item  
✅ Script migration peuple exercise_types sans duplication  
✅ Tests CI passent  
✅ Aucun renommage DB "chapter_code -> chaptercode" (on garde snake_case canonique)

