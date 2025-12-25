# P0 - Analyse complète : 6e_G07 génère des exercices statiques

## Mission

Comprendre POURQUOI le chapitre 6e_G07 (pipeline MIXED) génère encore des exercices STATIQUES au lieu des dynamiques.

## Chemin de code tracé

### 1. Endpoint : `POST /api/v1/exercises/generate`

**Fichier** : `backend/routes/exercises_routes.py` (ligne 836)

**Flux** :
1. `generate_exercise(request: ExerciseGenerateRequest)` reçoit `code_officiel="6e_G07"`
2. Récupère le chapitre depuis MongoDB via `curriculum_service.get_chapter_by_code(code_officiel)`
3. Détermine le `pipeline_mode` depuis `chapter_from_db.get("pipeline")`
4. Si `pipeline_mode == "MIXED"`, appelle `generate_exercise_with_fallback()`

### 2. Lecture du chapitre

**Fichier** : `backend/routes/exercises_routes.py` (ligne ~920)

```python
# Récupération du chapitre depuis MongoDB
curriculum_service = CurriculumPersistenceService(db)
chapter_from_db = await curriculum_service.get_chapter_by_code(request.code_officiel)
```

**Requête MongoDB** :
```javascript
db.curriculum_chapters.findOne(
  {"code_officiel": "6e_G07"},  // ⚠️ ATTENTION : casse exacte
  {"_id": 0}
)
```

**Fichier service** : `backend/services/curriculum_persistence_service.py` (ligne 212)

### 3. Détermination du pipeline

**Fichier** : `backend/routes/exercises_routes.py` (ligne 1105)

```python
if chapter_from_db:
    pipeline_mode = chapter_from_db.get("pipeline")
elif curriculum_chapter:
    pipeline_mode = curriculum_chapter.pipeline if hasattr(curriculum_chapter, 'pipeline') else None
else:
    pipeline_mode = None
```

### 4. Pipeline MIXED → `generate_exercise_with_fallback()`

**Fichier** : `backend/routes/exercises_routes.py` (ligne 1270)

```python
elif pipeline_mode == "MIXED":
    ctx["enabled_generators"] = enabled_generators_for_chapter
    return await generate_exercise_with_fallback(
        chapter_code=chapter_code_for_db,  # ⚠️ "6E_G07" (uppercase)
        exercise_service=exercise_service,
        request=request,
        ctx=ctx,
        request_start=request_start,
        effective_grade=effective_grade
    )
```

**Normalisation** : `chapter_code_for_db = request.code_officiel.upper().replace("-", "_")` → `"6E_G07"`

### 5. Récupération des exercices

**Fichier** : `backend/routes/exercises_routes.py` (ligne 84)

```python
exercises = await exercise_service.get_exercises(
    chapter_code=chapter_code,  # "6E_G07"
    offer=request.offer if hasattr(request, 'offer') else None,
    difficulty=requested_difficulty
)
```

**Fichier service** : `backend/services/exercise_persistence_service.py` (ligne 555)

**Requête MongoDB** :
```python
chapter_upper = chapter_code.upper().replace("-", "_")  # "6E_G07"
query = {"chapter_code": chapter_upper}  # {"chapter_code": "6E_G07"}
exercises = await self.collection.find(query, {"_id": 0}).sort("id", 1).to_list(1000)
```

**Collection** : `admin_exercises` (EXERCISES_COLLECTION = "admin_exercises")

### 6. Filtrage des exercices dynamiques

**Fichier** : `backend/routes/exercises_routes.py` (ligne 108)

```python
dynamic_exercises = [ex for ex in exercises if ex.get("is_dynamic") is True]
```

**⚠️ CRITIQUE** : Le filtre utilise `is True` (comparaison stricte), donc :
- `is_dynamic: true` → ✅ inclus
- `is_dynamic: false` → ❌ exclu
- `is_dynamic: null` ou absent → ❌ exclu

### 7. Filtrage par `enabled_generators`

**Fichier** : `backend/routes/exercises_routes.py` (ligne 92)

```python
enabled_generators_for_chapter = ctx.get("enabled_generators", [])
if enabled_generators_for_chapter:
    dynamic_exercises = [
        ex for ex in dynamic_exercises
        if ex.get("generator_key") and ex.get("generator_key").upper() in [eg.upper() for eg in enabled_generators_for_chapter]
    ]
```

### 8. Fallback vers STATIC

**Fichier** : `backend/routes/exercises_routes.py` (ligne 232)

Si `len(dynamic_exercises) == 0`, le code fait un fallback vers les exercices statiques :

```python
static_exercises = [ex for ex in exercises if ex.get("is_dynamic") is not True]
```

## Causes possibles (A/B/C/D/E)

### A) Le pipeline MIXED n'est pas réellement lu par l'API

**Vérification** :
```javascript
// Dans MongoDB
db.curriculum_chapters.findOne(
  {code_officiel: "6e_G07"},
  {pipeline: 1, code_officiel: 1}
)
```

**Problème possible** :
- Le champ `pipeline` est `null` ou absent
- Le champ `pipeline` est une chaîne différente ("SPEC", "TEMPLATE", etc.)
- Le `code_officiel` ne correspond pas exactement (casse : "6E_G07" vs "6e_G07")

### B) Des exercices dynamiques existent mais sont filtrés

**Vérification** :
```javascript
// Total exercices
db.admin_exercises.countDocuments({chapter_code: "6E_G07"})

// Exercices dynamiques
db.admin_exercises.countDocuments({chapter_code: "6E_G07", is_dynamic: true})

// Exercices avec generator_key SYMETRIE*
db.admin_exercises.find(
  {chapter_code: "6E_G07", generator_key: {$regex: "SYMETRIE", $options: "i"}},
  {id: 1, generator_key: 1, is_dynamic: 1}
).pretty()
```

**Problème possible** :
- Filtre `enabled_generators` élimine tous les exercices dynamiques
- Filtre `offer` ou `difficulty` élimine tous les exercices dynamiques
- Les exercices dynamiques ont `is_dynamic: false` ou `null` au lieu de `true`

### C) Les exercices dynamiques n'existent pas pour chapter_code

**Vérification** :
```javascript
// Tester différentes variantes de casse
db.admin_exercises.countDocuments({chapter_code: "6E_G07", is_dynamic: true})
db.admin_exercises.countDocuments({chapter_code: "6e_G07", is_dynamic: true})
db.admin_exercises.countDocuments({chapter_code: "6e_g07", is_dynamic: true})

// Chercher avec regex (insensible à la casse)
db.admin_exercises.countDocuments({
  chapter_code: {$regex: "^6[Ee]_G07$", $options: "i"},
  is_dynamic: true
})
```

**Problème possible** :
- Les exercices dynamiques ont un `chapter_code` différent (ex: "6E_G07_DYN")
- Les exercices dynamiques ont un `chapter_code` avec une casse différente

### D) Dynamiques existent mais la requête DB ne les récupère pas

**Vérification** :
```javascript
// Vérifier la collection exacte
db.getCollectionNames()  // Doit contenir "admin_exercises"

// Vérifier la requête exacte
db.admin_exercises.find(
  {chapter_code: "6E_G07"},
  {_id: 0, id: 1, is_dynamic: 1, generator_key: 1, chapter_code: 1}
).pretty()
```

**Problème possible** :
- Mauvaise collection (ex: `exercises` au lieu de `admin_exercises`)
- Le champ `chapter_code` a une valeur différente dans les documents

### E) Dynamiques existent mais la génération plante et fallback en statique

**Vérification** : Voir les logs backend avec les tags `[DIAG_6E_G07]` et `[FALLBACK_DEBUG]`

**Problème possible** :
- Exception lors de `format_dynamic_exercise()` → fallback vers STATIC
- Erreur de génération du générateur → fallback vers STATIC

## Logs de diagnostic ajoutés

### Tags de logs

1. `[DIAG_6E_G07]` : Diagnostic complet pour 6e_G07
2. `[FALLBACK_DEBUG]` : Détails du fallback
3. `[PIPELINE_DEBUG]` : Pipeline et enabled_generators
4. `[FALLBACK_STATIC]` : ⚠️ Avertissement quand un exercice statique est utilisé

### Emplacements des logs

1. **Lecture du chapitre** : `backend/routes/exercises_routes.py` (ligne ~1095)
2. **Pipeline MIXED** : `backend/routes/exercises_routes.py` (ligne ~1270)
3. **Récupération exercices** : `backend/services/exercise_persistence_service.py` (ligne ~577)
4. **Filtrage dynamiques** : `backend/routes/exercises_routes.py` (ligne ~90)
5. **Fallback STATIC** : `backend/routes/exercises_routes.py` (ligne ~250)

## Script de diagnostic MongoDB

**Fichier** : `scripts/diagnostic_6e_g07.py`

**Usage** :
```bash
python scripts/diagnostic_6e_g07.py
```

Le script vérifie :
1. Le chapitre dans `curriculum_chapters` (pipeline, enabled_generators)
2. Les exercices dans `admin_exercises` (total, dynamiques, statiques)
3. Les générateurs SYMETRIE_AXIALE
4. Recommandations selon les résultats

## Commandes MongoDB pour diagnostic manuel

### 1. Vérifier le chapitre

```javascript
// Variantes de casse
db.curriculum_chapters.findOne({code_officiel: "6E_G07"}, {pipeline: 1, enabled_generators: 1})
db.curriculum_chapters.findOne({code_officiel: "6e_G07"}, {pipeline: 1, enabled_generators: 1})

// Recherche insensible à la casse
db.curriculum_chapters.findOne(
  {code_officiel: {$regex: "^6[Ee]_G07$", $options: "i"}},
  {pipeline: 1, enabled_generators: 1, code_officiel: 1}
)
```

### 2. Vérifier les exercices

```javascript
// Total
db.admin_exercises.countDocuments({chapter_code: "6E_G07"})

// Dynamiques
db.admin_exercises.countDocuments({chapter_code: "6E_G07", is_dynamic: true})

// Statiques
db.admin_exercises.countDocuments({
  chapter_code: "6E_G07",
  $or: [{is_dynamic: false}, {is_dynamic: {$exists: false}}]
})

// Détails dynamiques
db.admin_exercises.find(
  {chapter_code: "6E_G07", is_dynamic: true},
  {_id: 0, id: 1, generator_key: 1, is_dynamic: 1, offer: 1, difficulty: 1}
).pretty()

// Détails statiques (premiers 3)
db.admin_exercises.find(
  {
    chapter_code: "6E_G07",
    $or: [{is_dynamic: false}, {is_dynamic: {$exists: false}}]
  },
  {_id: 0, id: 1, is_dynamic: 1, generator_key: 1, enonce_html: 1}
).limit(3).pretty()
```

### 3. Vérifier les générateurs SYMETRIE

```javascript
db.admin_exercises.find(
  {
    chapter_code: {$regex: "^6[Ee]_G07$", $options: "i"},
    generator_key: {$regex: "SYMETRIE", $options: "i"}
  },
  {_id: 0, id: 1, generator_key: 1, is_dynamic: 1, chapter_code: 1}
).pretty()
```

## Prochaines étapes

1. **Exécuter le script de diagnostic** : `python scripts/diagnostic_6e_g07.py`
2. **Générer un exercice** pour 6e_G07 et vérifier les logs `[DIAG_6E_G07]`
3. **Vérifier MongoDB** avec les commandes ci-dessus
4. **Identifier la cause exacte** (A/B/C/D/E)
5. **Appliquer le fix minimal** selon la cause



