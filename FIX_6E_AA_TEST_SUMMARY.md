# Fix 422 CHAPTER_OR_TYPE_INVALID pour 6e_AA_TEST - Résumé

## ✅ Corrections implémentées

### Backend
- **Fichier** : `backend/routes/exercises_routes.py`
- **Changement** : Détection des chapitres de test connus (`6E_AA_TEST`, `6E_TESTS_DYN`, `6E_MIXED_QA`) AVANT passage par MathGenerationService
- **Routage** : Chapitres de test connus → pipeline MIXED directement
- **Erreur** : Chapitres de test inconnus → 422 `TEST_CHAPTER_UNKNOWN` avec hint clair

### Tests
- **Fichier** : `backend/tests/test_6e_aa_test_chapter.py` (nouveau)
- **Tests** : 3 tests (success, unknown test chapter, integration)

---

## 🧪 Commandes Docker

```bash
# 1. Rebuild propre (sans cache)
docker compose build --no-cache backend

# 2. Redémarrer le container
docker compose restart backend

# 3. Tests unitaires
docker compose exec backend pytest backend/tests/test_6e_aa_test_chapter.py -v

# 4. Test manuel avec curl
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_AA_TEST", "difficulte": "facile", "offer": "free", "seed": 42}'
```

---

## 📋 Checklist manuelle (5 étapes)

1. **Test 6e_AA_TEST** : Générer avec `code_officiel="6e_AA_TEST"` → 200 OK (ou 422 POOL_EMPTY), pas de `CHAPTER_OR_TYPE_INVALID`
2. **Test chapitre inconnu** : Générer avec `code_officiel="6e_UNKNOWN_TEST"` → 422 `TEST_CHAPTER_UNKNOWN`
3. **Test chapitre normal** : Générer avec `code_officiel="6e_N08"` → Comportement inchangé
4. **Logs backend** : `docker compose logs backend | grep TEST_CHAPTER` → Log détection
5. **Pas de MathGenerationService** : Pas de log `CHAPITRE NON MAPPÉ`

---

## 📁 Fichiers modifiés

1. `backend/routes/exercises_routes.py` - Détection chapitres de test + routage MIXED
2. `backend/tests/test_6e_aa_test_chapter.py` - Tests unitaires (nouveau)
3. `docs/FIX_6E_AA_TEST_CHAPTER_INVALID.md` - Documentation détaillée

---

## ✅ Validation

- ✅ Compilation : OK
- ✅ Chapitres de test connus : Routage direct MIXED
- ✅ Chapitres de test inconnus : 422 `TEST_CHAPTER_UNKNOWN` avec hint
- ✅ Chapitres normaux : Comportement inchangé
- ✅ Tests unitaires créés

---

**Prêt pour validation et déploiement**

