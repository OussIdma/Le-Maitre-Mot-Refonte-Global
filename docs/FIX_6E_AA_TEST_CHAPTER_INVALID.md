# Fix 422 CHAPTER_OR_TYPE_INVALID pour code_officiel="6e_AA_TEST"

**Date :** 2025-01-XX  
**Statut :** ✅ Implémenté

---

## Objectif

Corriger l'erreur 422 `CHAPTER_OR_TYPE_INVALID` pour `code_officiel="6e_AA_TEST"` (chapitre de test) en implémentant une règle déterministe qui route directement les chapitres de test connus vers le pipeline MIXED, sans passer par `MathGenerationService`.

---

## Problème identifié

**Cause** : Quand `code_officiel="6e_AA_TEST"` est fourni :
1. Le code extrait `curriculum_chapter.libelle` qui est "AA TEST" (ligne 790)
2. Si `pipeline_mode` n'est pas détecté ou est `None`, le code passe par le mode legacy
3. Le mode legacy appelle `_math_service.generate_math_exercise_specs()` qui utilise `_map_chapter_to_types()`
4. `_map_chapter_to_types()` cherche "AA TEST" dans le mapping, ne le trouve pas
5. Lève `ValueError` → transformé en `HTTPException(422)` avec `error_code="CHAPTER_OR_TYPE_INVALID"`

**Solution** : Détecter les chapitres de test connus AVANT de passer par `MathGenerationService` et les router directement vers le pipeline MIXED.

---

## Corrections backend

### Fichier modifié : `backend/routes/exercises_routes.py` (ligne ~787)

**Code ajouté** :
```python
# ============================================================================
# DÉTECTION CHAPITRES DE TEST - Routage déterministe pour chapitres de test
# ============================================================================
# Chapitres de test connus qui utilisent le pipeline MIXED (exercices dynamiques)
TEST_CHAPTER_CODES = ["6E_AA_TEST", "6E_TESTS_DYN", "6E_MIXED_QA"]
normalized_code = request.code_officiel.upper().replace("-", "_")

if normalized_code in TEST_CHAPTER_CODES:
    # Chapitre de test connu : utiliser directement le pipeline MIXED
    logger.info(f"[TEST_CHAPTER] Chapitre de test détecté: {request.code_officiel} → pipeline=MIXED")
    pipeline_mode = "MIXED"
else:
    # Vérifier si c'est un chapitre de test inconnu (pattern AA_* ou *_TEST)
    if "_AA_" in normalized_code or normalized_code.endswith("_TEST") or "_TESTS_" in normalized_code:
        # Chapitre de test inconnu : retourner 422 avec hint clair
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "TEST_CHAPTER_UNKNOWN",
                "error": "test_chapter_unknown",
                "message": f"Le code officiel '{request.code_officiel}' semble être un chapitre de test mais n'est pas configuré.",
                "hint": f"Chapitres de test connus: {', '.join(TEST_CHAPTER_CODES)}. Ajoutez '{normalized_code}' à la liste TEST_CHAPTER_CODES dans exercises_routes.py si c'est un nouveau chapitre de test.",
                "context": {
                    "code_officiel": request.code_officiel,
                    "normalized_code": normalized_code,
                    "known_test_chapters": TEST_CHAPTER_CODES
                }
            }
        )
    
    # Pipeline explicite du curriculum (comportement normal)
    pipeline_mode = curriculum_chapter.pipeline if hasattr(curriculum_chapter, 'pipeline') and curriculum_chapter.pipeline else None
```

**Logique** :
1. **Chapitres de test connus** : Si `normalized_code` est dans `TEST_CHAPTER_CODES`, forcer `pipeline_mode = "MIXED"`
2. **Chapitres de test inconnus** : Si le pattern ressemble à un chapitre de test (`_AA_`, `_TEST`, `_TESTS_`), retourner 422 `TEST_CHAPTER_UNKNOWN` avec hint clair
3. **Chapitres normaux** : Comportement inchangé (pipeline du curriculum ou fallback legacy)

---

## Tests

### Fichier créé : `backend/tests/test_6e_aa_test_chapter.py`

**Tests inclus** :
1. `test_6e_aa_test_generation_success` : Vérifie que `code_officiel="6e_AA_TEST"` retourne 200 (ou au minimum ne plus être `chapter_not_mapped`)
2. `test_6e_aa_test_unknown_test_chapter` : Test qu'un chapitre de test inconnu retourne 422 `TEST_CHAPTER_UNKNOWN`
3. `test_6e_aa_test_integration` : Test d'intégration avec client FastAPI

**Exécution** :
```bash
pytest backend/tests/test_6e_aa_test_chapter.py -v
```

---

## Format d'erreur pour chapitre de test inconnu

```json
{
  "error_code": "TEST_CHAPTER_UNKNOWN",
  "error": "test_chapter_unknown",
  "message": "Le code officiel '6e_UNKNOWN_TEST' semble être un chapitre de test mais n'est pas configuré.",
  "hint": "Chapitres de test connus: 6E_AA_TEST, 6E_TESTS_DYN, 6E_MIXED_QA. Ajoutez '6E_UNKNOWN_TEST' à la liste TEST_CHAPTER_CODES dans exercises_routes.py si c'est un nouveau chapitre de test.",
  "context": {
    "code_officiel": "6e_UNKNOWN_TEST",
    "normalized_code": "6E_UNKNOWN_TEST",
    "known_test_chapters": ["6E_AA_TEST", "6E_TESTS_DYN", "6E_MIXED_QA"]
  }
}
```

---

## Commandes Docker

```bash
# 1. Rebuild propre (sans cache)
docker compose build --no-cache backend

# 2. Redémarrer le container
docker compose restart backend

# 3. Tests unitaires
docker compose exec backend pytest backend/tests/test_6e_aa_test_chapter.py -v

# 4. Test d'intégration (nécessite exercices en DB)
docker compose exec backend pytest backend/tests/test_6e_aa_test_chapter.py::test_6e_aa_test_integration -v

# 5. Test manuel avec curl
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_AA_TEST", "difficulte": "facile", "offer": "free", "seed": 42}'
```

---

## Checklist de vérification manuelle (5 étapes)

### 1. Test 6e_AA_TEST (chapitre de test connu)
- Générer un exercice avec `code_officiel="6e_AA_TEST"`
- **Attendu** : 200 OK (ou 422 POOL_EMPTY si aucun exercice en DB), pas de 422 `CHAPTER_OR_TYPE_INVALID`

### 2. Test chapitre de test inconnu
- Générer un exercice avec `code_officiel="6e_UNKNOWN_TEST"`
- **Attendu** : 422 `TEST_CHAPTER_UNKNOWN` avec hint clair

### 3. Test chapitre normal (non-test)
- Générer un exercice avec `code_officiel="6e_N08"` (chapitre normal)
- **Attendu** : Comportement inchangé (pipeline du curriculum ou legacy)

### 4. Vérification logs backend
```bash
docker compose logs backend | grep TEST_CHAPTER
```
- **Attendu** : Log `[TEST_CHAPTER] Chapitre de test détecté: 6e_AA_TEST → pipeline=MIXED`

### 5. Vérification que MathGenerationService n'est pas appelé
- Générer avec `6e_AA_TEST`
- **Attendu** : Pas de log `CHAPITRE NON MAPPÉ` de `MathGenerationService`

---

## Fichiers modifiés

1. **backend/routes/exercises_routes.py**
   - Ajout détection chapitres de test connus
   - Routage direct vers pipeline MIXED pour chapitres de test
   - Erreur 422 `TEST_CHAPTER_UNKNOWN` pour chapitres de test inconnus

2. **backend/tests/test_6e_aa_test_chapter.py** (nouveau)
   - Tests unitaires pour chapitres de test

---

## Validation

- ✅ Compilation : `python3 -m py_compile` → OK
- ✅ Chapitres de test connus : Routage direct vers MIXED, pas de passage par MathGenerationService
- ✅ Chapitres de test inconnus : 422 `TEST_CHAPTER_UNKNOWN` avec hint clair
- ✅ Chapitres normaux : Comportement inchangé
- ✅ Tests unitaires créés

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Implémenté, prêt pour validation

