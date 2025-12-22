# Fix SIMPLIFICATION_FRACTIONS_V2 - Résumé

## ✅ Corrections implémentées

### Backend
- **Fichier** : `backend/generators/simplification_fractions_v2.py`
- **Changement** : Ajout méthode `_build_variables_diagnostic_deterministic()` pour toujours fournir `check_equivalence_str`, `diagnostic_explanation`, `wrong_simplification` même pour variants A/B
- **Normalisation** : Error code `PLACEHOLDER_UNRESOLVED` partout (commentaire mis à jour)

### Tests
- **Fichier** : `backend/tests/test_placeholder_unresolved.py`
- **Tests ajoutés** :
  - `test_simplification_fractions_v2_all_variants` : Vérifie que tous les variants fournissent les variables diagnostic
  - `test_simplification_fractions_v2_missing_diagnostic_vars` : Test erreur si variables manquantes

---

## 🧪 Commandes Docker

```bash
# 1. Rebuild propre (sans cache)
docker compose build --no-cache backend

# 2. Redémarrer le container
docker compose restart backend

# 3. Tests unitaires
docker compose exec backend pytest backend/tests/test_placeholder_unresolved.py -v

# 4. Test spécifique SIMPLIFICATION_FRACTIONS_V2
docker compose exec backend pytest backend/tests/test_placeholder_unresolved.py::test_simplification_fractions_v2_all_variants -v
docker compose exec backend pytest backend/tests/test_placeholder_unresolved.py::test_simplification_fractions_v2_missing_diagnostic_vars -v
```

---

## 📋 Checklist manuelle (5 étapes)

1. **Test variant A** : Générer exercice `SIMPLIFICATION_FRACTIONS_V2` variant A → Pas d'erreur `PLACEHOLDER_UNRESOLVED`
2. **Test variant B** : Générer exercice `SIMPLIFICATION_FRACTIONS_V2` variant B → Pas d'erreur `PLACEHOLDER_UNRESOLVED`
3. **Test variant C** : Générer exercice `SIMPLIFICATION_FRACTIONS_V2` variant C → Pas d'erreur `PLACEHOLDER_UNRESOLVED`
4. **Vérification variables** : Vérifier que `check_equivalence_str`, `diagnostic_explanation`, `wrong_simplification` sont présents dans `variables`
5. **Test template diagnostic** : Template avec `{{check_equivalence_str}}` pour variant A → Placeholder résolu

---

## 📁 Fichiers modifiés

1. `backend/generators/simplification_fractions_v2.py` - Ajout méthode `_build_variables_diagnostic_deterministic()`
2. `backend/services/tests_dyn_handler.py` - Mise à jour commentaire
3. `backend/tests/test_placeholder_unresolved.py` - Tests unitaires ajoutés
4. `docs/FIX_SIMPLIFICATION_FRACTIONS_V2_PLACEHOLDERS.md` - Documentation détaillée

---

## ✅ Validation

- ✅ Compilation : OK
- ✅ Variables toujours fournies : `check_equivalence_str`, `diagnostic_explanation`, `wrong_simplification` pour tous les variants
- ✅ Pas d'erreur PLACEHOLDER_UNRESOLVED : Tests unitaires passent
- ✅ Normalisation erreur : Error code `PLACEHOLDER_UNRESOLVED` partout

---

**Prêt pour validation et déploiement**

