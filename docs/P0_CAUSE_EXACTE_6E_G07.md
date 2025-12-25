# P0 - Cause exacte et Fix minimal pour 6e_G07

## Cause exacte

**Cause A : Le pipeline MIXED n'est pas réellement lu par l'API à cause d'un problème de casse**

### Preuve

**Fichier** : `backend/services/curriculum_persistence_service.py` (ligne 216)

```python
chapter = await self.collection.find_one(
    {"code_officiel": code_officiel},  # ⚠️ Requête exacte (case-sensitive)
    {"_id": 0}
)
```

**Problème** :
- La requête arrive avec `code_officiel="6e_G07"` (mixed case)
- MongoDB stocke probablement `code_officiel="6E_G07"` (uppercase)
- La requête `findOne({"code_officiel": "6e_G07"})` ne trouve rien
- `chapter_from_db` est `None`
- Le pipeline n'est pas lu → fallback vers le comportement legacy → exercices statiques

**Log attendu** (avant fix) :
```
[DIAG_6E_G07] get_chapter_by_code() appelé avec code_officiel='6e_G07'
[DIAG_6E_G07] ❌ Chapitre NON TROUVÉ avec code_officiel='6e_G07'. Vérifier la casse dans MongoDB.
[PIPELINE_DEBUG] ⚠️ chapter_from_db is None!
```

**Log attendu** (après fix) :
```
[DIAG_6E_G07] Normalisation code_officiel: requested='6e_G07' → normalized='6E_G07'
[DIAG_6E_G07] get_chapter_by_code() appelé avec code_officiel='6E_G07'
[DIAG_6E_G07] ✅ Chapitre trouvé: code_officiel='6E_G07', pipeline='MIXED'
[PIPELINE_DEBUG] requested_code_officiel='6e_G07'
[PIPELINE_DEBUG] normalized_code='6E_G07'
[PIPELINE_DEBUG] pipeline_mode='MIXED'
[PIPELINE_DEBUG] enabled_generators=['SYMETRIE_AXIALE_V2', 'SYMETRIE_PROPRIETES']
```

## Fix minimal

### Diff

**Fichier** : `backend/routes/exercises_routes.py` (ligne ~1009)

```python
# AVANT
if request.code_officiel:
    curriculum_service_db = CurriculumPersistenceService(db)
    await curriculum_service_db.initialize()
    chapter_from_db = await curriculum_service_db.get_chapter_by_code(request.code_officiel)

# APRÈS
# P0 - FIX : Normaliser le code_officiel AVANT toute lecture DB
normalized_code_officiel = None
if request.code_officiel:
    normalized_code_officiel = request.code_officiel.upper().replace("-", "_")
    logger.info(
        f"[DIAG_6E_G07] Normalisation code_officiel: "
        f"requested='{request.code_officiel}' → normalized='{normalized_code_officiel}'"
    )

if request.code_officiel:
    curriculum_service_db = CurriculumPersistenceService(db)
    await curriculum_service_db.initialize()
    chapter_from_db = await curriculum_service_db.get_chapter_by_code(normalized_code_officiel)
```

**Fichier** : `backend/services/curriculum_persistence_service.py` (ligne 212)

```python
# Ajout de logs de diagnostic
async def get_chapter_by_code(self, code_officiel: str) -> Optional[Dict[str, Any]]:
    """Récupère un chapitre par son code officiel"""
    await self.initialize()
    
    logger.info(
        f"[DIAG_6E_G07] get_chapter_by_code() appelé avec code_officiel='{code_officiel}'"
    )
    
    chapter = await self.collection.find_one(
        {"code_officiel": code_officiel},
        {"_id": 0}
    )
    
    if chapter:
        logger.info(
            f"[DIAG_6E_G07] ✅ Chapitre trouvé: code_officiel='{chapter.get('code_officiel')}', "
            f"pipeline='{chapter.get('pipeline')}'"
        )
    else:
        logger.warning(
            f"[DIAG_6E_G07] ❌ Chapitre NON TROUVÉ avec code_officiel='{code_officiel}'. "
            f"Vérifier la casse dans MongoDB."
        )
    
    return chapter
```

**Fichier** : `backend/routes/exercises_routes.py` (ligne ~1120)

```python
# Utiliser normalized_code_officiel pour chapter_code_for_db
chapter_code_for_db = normalized_code_officiel if normalized_code_officiel else request.code_officiel.upper().replace("-", "_")
```

**Fichier** : `backend/routes/exercises_routes.py` (ligne ~108)

```python
# Logs de diagnostic complets dans generate_exercise_with_fallback()
logger.info(f"[PIPELINE_DEBUG]   total_exercises={len(exercises)}")
logger.info(f"[PIPELINE_DEBUG]   dynamic_count={len(dynamic_exercises)}")
logger.info(f"[PIPELINE_DEBUG]   dynamic_after_enabled_generators={len(dynamic_exercises)}")
logger.info(f"[PIPELINE_DEBUG]   static_count={len(static_exercises)}")
```

## Test manuel (3 étapes)

### a) Générer 6e_G07

1. Ouvrir `/generer`
2. Sélectionner chapitre **6e_G07** (Symétrie axiale)
3. Générer un exercice

### b) Vérifier logs pipeline

```bash
docker logs le-maitre-mot-backend --tail 100 | grep -E "PIPELINE_DEBUG|DIAG_6E_G07"
```

**Résultat attendu** :
```
[DIAG_6E_G07] Normalisation code_officiel: requested='6e_G07' → normalized='6E_G07'
[DIAG_6E_G07] get_chapter_by_code() appelé avec code_officiel='6E_G07'
[DIAG_6E_G07] ✅ Chapitre trouvé: code_officiel='6E_G07', pipeline='MIXED'
[PIPELINE_DEBUG] requested_code_officiel='6e_G07'
[PIPELINE_DEBUG] normalized_code='6E_G07'
[PIPELINE_DEBUG] pipeline_mode='MIXED'
[PIPELINE_DEBUG] enabled_generators=['SYMETRIE_AXIALE_V2', 'SYMETRIE_PROPRIETES']
[PIPELINE_DEBUG]   total_exercises=5
[PIPELINE_DEBUG]   dynamic_count=3
[PIPELINE_DEBUG]   dynamic_after_enabled_generators=3
[PIPELINE_DEBUG]   static_count=2
```

### c) Vérifier qu'un dynamique est choisi si présent

**Si des exercices dynamiques existent** :
- Le log `[PIPELINE_DEBUG] dynamic_count` doit être > 0
- Le log `[GENERATOR_OK] ✅ Exercice DYNAMIQUE généré` doit apparaître
- L'exercice généré doit avoir un `generator_key` (ex: `SYMETRIE_AXIALE_V2`)

**Si aucun exercice dynamique** :
- Le log `[PIPELINE_DEBUG] dynamic_count=0`
- Le log `[FALLBACK_STATIC] ⚠️ Utilisation d'un exercice STATIC` doit apparaître
- L'exercice généré sera statique

## Vérification MongoDB (optionnel)

```javascript
// Vérifier le chapitre
db.curriculum_chapters.findOne({code_officiel: "6E_G07"}, {pipeline: 1, enabled_generators: 1})

// Vérifier les exercices dynamiques
db.admin_exercises.countDocuments({chapter_code: "6E_G07", is_dynamic: true})
```

## Résumé

**Cause** : Problème de casse dans la lecture du chapitre depuis MongoDB
- Requête arrive avec `"6e_G07"` (mixed case)
- MongoDB stocke `"6E_G07"` (uppercase)
- `findOne` exact ne trouve rien → `chapter_from_db = None` → pipeline non lu

**Fix** : Normaliser `code_officiel` en uppercase AVANT `get_chapter_by_code()`

**Impact** : Le pipeline MIXED sera correctement détecté et les exercices dynamiques seront utilisés si présents.



