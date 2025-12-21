# Fix SIMPLIFICATION_FRACTIONS_V2 - Placeholders toujours fournis

**Date :** 2025-01-XX  
**Statut :** ✅ Implémenté

---

## Objectif

Supprimer les erreurs `PLACEHOLDER_UNRESOLVED` pour `generator_key=SIMPLIFICATION_FRACTIONS_V2` en s'assurant que les variables `check_equivalence_str`, `diagnostic_explanation`, `wrong_simplification` sont **TOUJOURS** fournies, même pour les variants A (standard) et B (guidé).

---

## Corrections backend

### Fichier modifié : `backend/generators/simplification_fractions_v2.py`

**Problème** : Les variables `check_equivalence_str`, `diagnostic_explanation`, `wrong_simplification` n'étaient fournies que pour le variant C (diagnostic).

**Solution** : Ajout d'une méthode `_build_variables_diagnostic_deterministic()` qui fournit ces variables de manière déterministe pour tous les variants (A, B, C).

**Code ajouté** :
```python
# TOUJOURS fournir les variables diagnostic (même pour variants A/B)
# Ces variables sont nécessaires pour les templates qui peuvent les utiliser
if variant_id != "C":
    # Pour variants A/B, fournir des valeurs déterministes basées sur la fraction
    variables.update(self._build_variables_diagnostic_deterministic(n, d, n_red, d_red, pgcd))
```

**Nouvelle méthode** :
```python
def _build_variables_diagnostic_deterministic(
    self,
    n: int,
    d: int,
    n_red: int,
    d_red: int,
    pgcd: int
) -> Dict[str, Any]:
    """
    Construit les variables diagnostic de manière déterministe pour variants A/B.
    Ces variables sont toujours fournies pour éviter les erreurs PLACEHOLDER_UNRESOLVED.
    """
    # Générer une simplification incorrecte plausible (toujours la même logique)
    # Erreur type : diviser seulement le numérateur
    wrong_n = n // pgcd
    wrong_d = d  # Dénominateur non divisé
    
    wrong_simplification = f"{wrong_n}/{wrong_d}"
    
    # Vérifier si la simplification est correcte (normalement non pour A/B)
    diagnostic_is_correct = (wrong_n == n_red and wrong_d == d_red)
    
    # Produit en croix pour vérifier l'équivalence
    check_equivalence_str = (
        f"{n} × {wrong_d} = {n * wrong_d} et "
        f"{d} × {wrong_n} = {d * wrong_n}. "
        f"Les produits sont {'égaux' if n * wrong_d == d * wrong_n else 'différents'}, "
        f"donc la simplification est {'correcte' if diagnostic_is_correct else 'incorrecte'}."
    )
    
    # Explication pédagogique déterministe
    if diagnostic_is_correct:
        diagnostic_explanation = (
            f"La simplification {wrong_simplification} est correcte. "
            f"On a bien divisé le numérateur et le dénominateur par le PGCD."
        )
    else:
        diagnostic_explanation = (
            f"La simplification {wrong_simplification} est incorrecte. "
            f"On doit diviser le numérateur ET le dénominateur par le PGCD, "
            f"pas seulement l'un des deux. La bonne simplification est {n_red}/{d_red}."
        )
    
    return {
        "wrong_simplification": wrong_simplification,
        "diagnostic_is_correct": diagnostic_is_correct,
        "diagnostic_explanation": diagnostic_explanation,
        "check_equivalence_str": check_equivalence_str
    }
```

---

## Normalisation erreur PLACEHOLDER_UNRESOLVED

### Fichier modifié : `backend/services/tests_dyn_handler.py`

**Changement** : Mise à jour du commentaire pour refléter le changement d'error_code.

**Avant** : `422 UNRESOLVED_PLACEHOLDERS`  
**Après** : `422 PLACEHOLDER_UNRESOLVED`

**Code** : Déjà normalisé dans le code précédent (ligne ~669).

---

## Tests

### Fichier modifié : `backend/tests/test_placeholder_unresolved.py`

**Tests ajoutés** :

1. **`test_simplification_fractions_v2_all_variants`** :
   - Test que `SIMPLIFICATION_FRACTIONS_V2` fournit toujours `check_equivalence_str`, `diagnostic_explanation`, `wrong_simplification` pour tous les variants (A, B, C)
   - Vérifie qu'aucune erreur `PLACEHOLDER_UNRESOLVED` n'est levée

2. **`test_simplification_fractions_v2_missing_diagnostic_vars`** :
   - Test que si `check_equivalence_str` est manquant, on obtient `PLACEHOLDER_UNRESOLVED`
   - Vérifie que l'erreur contient bien `check_equivalence_str` dans `context.missing`

**Exécution** :
```bash
pytest backend/tests/test_placeholder_unresolved.py::test_simplification_fractions_v2_all_variants -v
pytest backend/tests/test_placeholder_unresolved.py::test_simplification_fractions_v2_missing_diagnostic_vars -v
```

---

## Commandes Docker

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

## Checklist de vérification manuelle (5 étapes)

### 1. Test variant A (standard)
- Créer un exercice `SIMPLIFICATION_FRACTIONS_V2` avec `variant_id="A"`
- Générer l'exercice
- **Attendu** : Pas d'erreur `PLACEHOLDER_UNRESOLVED`, exercice généré avec succès

### 2. Test variant B (guidé)
- Créer un exercice `SIMPLIFICATION_FRACTIONS_V2` avec `variant_id="B"`
- Générer l'exercice
- **Attendu** : Pas d'erreur `PLACEHOLDER_UNRESOLVED`, exercice généré avec succès

### 3. Test variant C (diagnostic)
- Créer un exercice `SIMPLIFICATION_FRACTIONS_V2` avec `variant_id="C"`
- Générer l'exercice
- **Attendu** : Pas d'erreur `PLACEHOLDER_UNRESOLVED`, exercice généré avec succès

### 4. Vérification variables fournies
- Vérifier dans les logs ou la réponse API que `check_equivalence_str`, `diagnostic_explanation`, `wrong_simplification` sont présents dans `variables`
- **Attendu** : Ces 3 variables sont toujours présentes, même pour variant A/B

### 5. Test template avec placeholder diagnostic
- Créer un template qui utilise `{{check_equivalence_str}}` pour variant A
- Générer l'exercice
- **Attendu** : Placeholder résolu, pas d'erreur `PLACEHOLDER_UNRESOLVED`

---

## Fichiers modifiés

1. **backend/generators/simplification_fractions_v2.py**
   - Ajout méthode `_build_variables_diagnostic_deterministic()`
   - Modification `generate()` pour toujours fournir les variables diagnostic

2. **backend/services/tests_dyn_handler.py**
   - Mise à jour commentaire (UNRESOLVED_PLACEHOLDERS → PLACEHOLDER_UNRESOLVED)

3. **backend/tests/test_placeholder_unresolved.py**
   - Ajout `test_simplification_fractions_v2_all_variants`
   - Ajout `test_simplification_fractions_v2_missing_diagnostic_vars`

---

## Validation

- ✅ Compilation : `python3 -m py_compile` → OK
- ✅ Variables toujours fournies : `check_equivalence_str`, `diagnostic_explanation`, `wrong_simplification` pour tous les variants
- ✅ Pas d'erreur PLACEHOLDER_UNRESOLVED : Tests unitaires passent
- ✅ Normalisation erreur : Error code `PLACEHOLDER_UNRESOLVED` partout

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Implémenté, prêt pour validation

