# P0: Standardisation 422 - Résumé des modifications

**Date** : 2025-12-26  
**Mission** : Stopper les 422 "inexpliqués" + ajouter diagnostic gold minimal

---

## ✅ Modifications réalisées

### 1. Fonctions helper créées

**Fichier** : `backend/routes/exercises_routes.py` (lignes ~56-200)

- `build_diagnostic_context()` : Construit le contexte de diagnostic obligatoire
- `raise_422_with_diagnostic()` : Lève un HTTPException(422) standardisé avec logs

### 2. Logs ajoutés

- **[DIAG_FLOW]** : 
  - Entrée de `/generate` (ligne ~1129)
  - Après filtrage dynamique/statique (ligne ~1485)

- **[DIAG_422]** : 
  - Avant chaque `raise_422_with_diagnostic()` (dans la fonction helper)

### 3. 422 standardisés (partiels)

Les 422 suivants ont été remplacés par `raise_422_with_diagnostic()` :

1. ✅ `CODE_OFFICIEL_INVALID` (ligne ~1300)
2. ✅ `TEST_CHAPTER_FORBIDDEN` (ligne ~1331)
3. ✅ `TEST_CHAPTER_UNKNOWN` (ligne ~1360)
4. ✅ `TEMPLATE_PIPELINE_NO_DYNAMIC_EXERCISES` (lignes ~1461, ~1510)
5. ✅ `MIXED_PIPELINE_NO_EXERCISES_OR_TYPES` (ligne ~1917)
6. ✅ `NO_EXERCISE_AVAILABLE` (ligne ~2001) - **À compléter**

### 4. Test minimal créé

**Fichier** : `backend/tests/test_diag_422.py`

- Test format standardisé
- Test présence context
- Instructions pour vérifier logs

---

## ⚠️ 422 restants à standardiser

Les 422 suivants doivent encore être remplacés (liste non exhaustive) :

1. `NO_TESTS_DYN_EXERCISE_FOUND` (ligne ~1091)
2. `POOL_EMPTY` (ligne ~1638)
3. `SPEC_PIPELINE_INVALID_EXERCISE_TYPES` (ligne ~1952)
4. `INVALID_CURRICULUM_EXERCISE_TYPES` (ligne ~1973)
5. `NIVEAU_INVALID` (ligne ~2024)
6. `CHAPITRE_INVALID` (ligne ~2048)
7. `CHAPTER_OR_TYPE_INVALID` (ligne ~2526)
8. `ADMIN_TEMPLATE_MISMATCH` (dans `exercise_persistence_service.py`)

---

## Format standard appliqué

```python
{
  "error_code": "ERROR_CODE_NAME",
  "message": "Message lisible",
  "hint": "Action concrète",
  "context": {
    "code_officiel": "...",
    "chapter_code": "...",
    "pipeline_mode": "...",
    "offer_input": "...",
    "difficulty_input": "...",
    "total_exercises": 0,
    "dynamic_count": 0,
    "static_count": 0,
    "enabled_generators_count": 0,
    "enabled_generators_sample": [],
    "generator_key_selected": "...",
    "preset": "...",
    "seed": 123
  },
  "error": "error_legacy"  // Si déjà utilisé par le front
}
```

---

## Commandes de test

### Vérifier les logs
```bash
docker logs le-maitre-mot-backend --tail 300 | grep -E "DIAG_422|DIAG_FLOW"
```

### Lancer le test
```bash
python backend/tests/test_diag_422.py
# ou
pytest backend/tests/test_diag_422.py -v
```

### Tester un 422 réel
```bash
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6E_INVALID", "offer": "free", "difficulte": "facile"}' \
  | jq '.detail.context'
```

---

## Prochaines étapes

1. ✅ Compléter le remplacement de `NO_EXERCISE_AVAILABLE` (ligne ~2001)
2. ⚠️ Standardiser les 422 restants dans `exercises_routes.py`
3. ⚠️ Standardiser `ADMIN_TEMPLATE_MISMATCH` dans `exercise_persistence_service.py`
4. ⚠️ Vérifier que tous les 422 ont le format standardisé

---

## Liste des error_code

Voir `docs/P0_ERROR_CODES_422.md` pour la liste complète des error_code documentés.

