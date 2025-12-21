# Fix ADMIN_TEMPLATE_MISMATCH - Validation des placeholders en admin

**Date :** 2025-01-XX  
**Statut :** ✅ Implémenté

---

## Objectif

Empêcher qu'un exercice dynamique soit enregistrable s'il peut produire `PLACEHOLDER_UNRESOLVED`. La validation compare les placeholders attendus du template vs les clés fournies par le générateur pour chaque difficulté (facile/moyen/difficile).

---

## Corrections backend

### Fichier modifié : `backend/services/exercise_persistence_service.py`

**Fonction ajoutée** : `_validate_template_placeholders()`

**Fonctionnalités** :
1. Extrait tous les placeholders des templates (énoncé, solution, variants)
2. Teste pour chaque difficulté (facile, moyen, difficile)
3. Génère un exercice de test avec le générateur
4. Compare placeholders attendus vs clés fournies
5. Lève `HTTPException(422)` avec `error_code="ADMIN_TEMPLATE_MISMATCH"` si mismatch

**Code ajouté** :
```python
def _validate_template_placeholders(
    self,
    generator_key: str,
    enonce_template_html: Optional[str],
    solution_template_html: Optional[str],
    template_variants: Optional[List[Dict[str, Any]]],
    exercise_params: Dict[str, Any]
) -> None:
    """
    Valide que tous les placeholders des templates peuvent être résolus par le générateur.
    Teste pour chaque difficulté (facile, moyen, difficile).
    
    Lève HTTPException(422) avec error_code="ADMIN_TEMPLATE_MISMATCH" si mismatch.
    """
    # Extraire tous les placeholders attendus
    placeholders_expected = set()
    
    # Templates principaux
    if enonce_template_html:
        placeholders_expected.update(_extract_placeholders(enonce_template_html))
    if solution_template_html:
        placeholders_expected.update(_extract_placeholders(solution_template_html))
    
    # Templates variants
    if template_variants:
        for variant in template_variants:
            if isinstance(variant, dict):
                if variant.get("enonce_template_html"):
                    placeholders_expected.update(_extract_placeholders(variant["enonce_template_html"]))
                if variant.get("solution_template_html"):
                    placeholders_expected.update(_extract_placeholders(variant["solution_template_html"]))
    
    # Tester pour chaque difficulté
    difficulties = ["facile", "moyen", "difficile"]
    all_mismatches = []
    
    for difficulty in difficulties:
        # Générer un exercice de test
        generator = gen_class(seed=42)
        result = generator.generate(gen_params)
        keys_provided = set(result.get("variables", {}).keys())
        
        # Comparer
        missing = sorted(placeholders_expected - keys_provided)
        if missing:
            all_mismatches.append({
                "difficulty": difficulty,
                "missing": missing,
                "extra": extra,
                "placeholders_expected": sorted(placeholders_expected),
                "keys_provided": sorted(keys_provided)
            })
    
    # Si des mismatches sont détectés, lever une erreur
    if all_mismatches:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "ADMIN_TEMPLATE_MISMATCH",
                "error": "admin_template_mismatch",
                "message": f"Les templates contiennent des placeholders qui ne peuvent pas être résolus par le générateur '{generator_key}'.",
                "hint": hint,
                "context": {
                    "generator_key": generator_key,
                    "mismatches": all_mismatches,
                    "missing_summary": sorted(missing_summary),
                    "placeholders_expected": sorted(placeholders_expected)
                }
            }
        )
```

**Intégration** :
- Appelée dans `create_exercise()` si `is_dynamic=True` et `generator_key` présent
- Appelée dans `update_exercise()` si template ou `generator_key` modifié

---

## Corrections frontend

### Fichier modifié : `frontend/src/components/ExerciseGeneratorPage.js`

**Modifications** :
1. Détection de `error_code === "ADMIN_TEMPLATE_MISMATCH"`
2. Message spécifique : "Placeholders incompatibles avec le générateur"
3. Toast avec liste des placeholders manquants (max 3) + "et X autre(s)"
4. Console.error avec détails complets pour debug

**Code ajouté** :
```javascript
} else if (errorCode === "ADMIN_TEMPLATE_MISMATCH") {
  errorMessage = "Placeholders incompatibles avec le générateur";
  const missingSummary = detail.context?.missing_summary || [];
  const missingList = missingSummary.slice(0, 3).join(", ");
  const moreCount = missingSummary.length > 3 ? ` et ${missingSummary.length - 3} autre(s)` : "";
  hint = hint || `Les placeholders suivants ne peuvent pas être résolus par le générateur : ${missingList}${moreCount}. Vérifiez que le générateur fournit toutes les variables nécessaires.`;
  
  // Logger les détails complets dans la console
  console.error("🔴 ADMIN_TEMPLATE_MISMATCH - Détails complets:", {
    error_code: errorCode,
    generator_key: detail.context?.generator_key,
    missing_summary: missingSummary,
    mismatches: detail.context?.mismatches,
    placeholders_expected: detail.context?.placeholders_expected
  });
}
```

---

## Tests

### Fichier créé : `backend/tests/test_admin_template_mismatch.py`

**Tests inclus** :
1. `test_admin_template_mismatch_create` : Vérifie que la création avec mismatch retourne 422
2. `test_admin_template_mismatch_update` : Vérifie que la mise à jour avec mismatch retourne 422
3. `test_admin_template_match_success` : Test que si tous les placeholders sont fournis, pas d'erreur

**Exécution** :
```bash
pytest backend/tests/test_admin_template_mismatch.py -v
```

---

## Format d'erreur

```json
{
  "error_code": "ADMIN_TEMPLATE_MISMATCH",
  "error": "admin_template_mismatch",
  "message": "Les templates contiennent des placeholders qui ne peuvent pas être résolus par le générateur 'SIMPLIFICATION_FRACTIONS_V2'.",
  "hint": "Les placeholders suivants ne peuvent pas être résolus par le générateur 'SIMPLIFICATION_FRACTIONS_V2': check_equivalence_str, diagnostic_explanation. Vérifiez que le générateur fournit toutes les variables nécessaires pour les templates. Difficultés affectées: facile, moyen, difficile.",
  "context": {
    "generator_key": "SIMPLIFICATION_FRACTIONS_V2",
    "mismatches": [
      {
        "difficulty": "facile",
        "missing": ["check_equivalence_str", "diagnostic_explanation"],
        "extra": [],
        "placeholders_expected": ["fraction", "check_equivalence_str", "diagnostic_explanation"],
        "keys_provided": ["fraction", "fraction_reduite"]
      },
      {
        "difficulty": "moyen",
        "missing": ["check_equivalence_str", "diagnostic_explanation"],
        "extra": [],
        "placeholders_expected": ["fraction", "check_equivalence_str", "diagnostic_explanation"],
        "keys_provided": ["fraction", "fraction_reduite"]
      },
      {
        "difficulty": "difficile",
        "missing": ["check_equivalence_str", "diagnostic_explanation"],
        "extra": [],
        "placeholders_expected": ["fraction", "check_equivalence_str", "diagnostic_explanation"],
        "keys_provided": ["fraction", "fraction_reduite"]
      }
    ],
    "missing_summary": ["check_equivalence_str", "diagnostic_explanation"],
    "placeholders_expected": ["fraction", "check_equivalence_str", "diagnostic_explanation"]
  }
}
```

---

## Checklist de vérification manuelle (5 étapes)

### 1. Test création avec mismatch
- Créer un exercice dynamique avec template contenant `{{check_equivalence_str}}` (non fourni par générateur)
- Cliquer "Enregistrer"
- **Attendu** : Toast rouge "Placeholders incompatibles avec le générateur" + liste des placeholders manquants

### 2. Test mise à jour avec mismatch
- Modifier un exercice dynamique existant pour ajouter un placeholder non fourni
- Cliquer "Enregistrer"
- **Attendu** : Toast rouge avec erreur ADMIN_TEMPLATE_MISMATCH

### 3. Test création sans mismatch
- Créer un exercice dynamique avec templates compatibles
- Cliquer "Enregistrer"
- **Attendu** : Pas d'erreur, exercice créé avec succès

### 4. Vérification console frontend
- Ouvrir DevTools → Console
- Créer avec mismatch
- **Attendu** : Log `🔴 ADMIN_TEMPLATE_MISMATCH - Détails complets:` avec tous les détails

### 5. Vérification logs backend
```bash
docker compose logs backend | grep ADMIN_TEMPLATE_MISMATCH
```
- **Attendu** : Logs de validation avec status 422

---

## Fichiers modifiés

1. **backend/services/exercise_persistence_service.py**
   - Ajout fonction `_extract_placeholders()`
   - Ajout fonction `_validate_template_placeholders()`
   - Intégration dans `create_exercise()` et `update_exercise()`

2. **frontend/src/components/ExerciseGeneratorPage.js**
   - Gestion `error_code === "ADMIN_TEMPLATE_MISMATCH"`
   - Toast avec liste des placeholders manquants + console.log détaillé

3. **backend/tests/test_admin_template_mismatch.py** (nouveau)
   - Tests unitaires pour création et mise à jour avec mismatch

---

## Validation

- ✅ Compilation : `python3 -m py_compile` → OK
- ✅ Validation proactive : Empêche l'enregistrement d'exercices avec placeholders incompatibles
- ✅ Tests pour toutes les difficultés : facile, moyen, difficile
- ✅ Tests unitaires créés
- ✅ Frontend : Toast + console.log pour debug

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Implémenté, prêt pour validation

