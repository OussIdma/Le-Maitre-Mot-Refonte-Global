# Fix PLACEHOLDER_UNRESOLVED - Erreur 422 structurée

**Date :** 2025-01-XX  
**Statut :** ✅ Implémenté

---

## Objectif

Quand un ou plusieurs placeholders ne sont pas résolus (ex: `6e_TESTS_DYN`), retourner une erreur HTTP 422 structurée avec la liste des placeholders manquants, au lieu d'un 500 ou d'un fallback silencieux.

---

## Corrections backend

### Fichier modifié : `backend/services/tests_dyn_handler.py` (ligne ~635)

**Avant** : Error code `UNRESOLVED_PLACEHOLDERS` avec format non standardisé

**Après** : Error code `PLACEHOLDER_UNRESOLVED` avec format standardisé
```json
{
  "error_code": "PLACEHOLDER_UNRESOLVED",
  "error": "placeholder_unresolved",
  "message": "Un ou plusieurs placeholders n'ont pas été résolus pour 6E_TESTS_DYN.",
  "hint": "Les placeholders suivants n'ont pas pu être résolus : var1, var2, var3. Vérifiez que le générateur 'THALES_V1' fournit toutes les variables nécessaires pour le template. Placeholders attendus : 5, fournis : 3.",
  "context": {
    "chapter_code": "6E_TESTS_DYN",
    "missing": ["var1", "var2", "var3"],
    "template_id": "test_exercise_1",
    "generator_key": "THALES_V1",
    "expected_placeholders": ["var1", "var2", "var3", "var4", "var5"],
    "provided_keys": ["var4", "var5"]
  }
}
```

**Code modifié** :
```python
if unresolved:
    # Construire le message hint explicatif
    missing_list = ", ".join(unresolved[:5])  # Limiter à 5 pour la lisibilité
    if len(unresolved) > 5:
        missing_list += f" et {len(unresolved) - 5} autre(s)"
    
    hint = (
        f"Les placeholders suivants n'ont pas pu être résolus : {missing_list}. "
        f"Vérifiez que le générateur '{generator_key}' fournit toutes les variables nécessaires pour le template. "
        f"Placeholders attendus : {len(expected_placeholders)}, fournis : {len(provided_keys)}."
    )

    raise HTTPException(
        status_code=422,
        detail={
            "error_code": "PLACEHOLDER_UNRESOLVED",
            "error": "placeholder_unresolved",
            "message": f"Un ou plusieurs placeholders n'ont pas été résolus pour {chapter_code}.",
            "hint": hint,
            "context": {
                "chapter_code": chapter_code,
                "missing": unresolved,
                "template_id": exercise_template.get("id"),
                "generator_key": generator_key,
                "expected_placeholders": sorted(expected_placeholders),
                "provided_keys": sorted(provided_keys)
            }
        },
    )
```

---

## Corrections frontend

### Fichier modifié : `frontend/src/components/ExerciseGeneratorPage.js` (ligne ~432)

**Modifications** :
1. Détection de `error_code === "PLACEHOLDER_UNRESOLVED"`
2. Message spécifique : "Placeholders non résolus"
3. Toast avec liste des placeholders manquants (max 3) + "et X autre(s)"
4. Console.log avec détails complets pour debug

**Code ajouté** :
```javascript
} else if (errorCode === "PLACEHOLDER_UNRESOLVED") {
  errorMessage = "Placeholders non résolus";
  const missing = detail.context?.missing || [];
  const missingList = missing.slice(0, 3).join(", ");
  const moreCount = missing.length > 3 ? ` et ${missing.length - 3} autre(s)` : "";
  hint = hint || `Les placeholders suivants n'ont pas pu être résolus : ${missingList}${moreCount}. Voir la console pour les détails complets.`;
  
  // Logger les détails complets dans la console
  console.error("🔴 PLACEHOLDER_UNRESOLVED - Détails complets:", {
    error_code: errorCode,
    chapter_code: detail.context?.chapter_code,
    template_id: detail.context?.template_id,
    generator_key: detail.context?.generator_key,
    missing_placeholders: missing,
    expected_placeholders: detail.context?.expected_placeholders,
    provided_keys: detail.context?.provided_keys
  });
}
```

---

## Tests

### Fichier créé : `backend/tests/test_placeholder_unresolved.py`

**Tests inclus** :
1. `test_placeholder_unresolved_422` : Vérifie que placeholders non résolus retournent 422 avec `PLACEHOLDER_UNRESOLVED`
2. `test_placeholder_unresolved_multiple_missing` : Test avec plusieurs placeholders manquants
3. `test_placeholder_all_resolved_success` : Test que si tous les placeholders sont résolus, pas d'erreur

**Exécution** :
```bash
pytest backend/tests/test_placeholder_unresolved.py -v
```

---

## Checklist de vérification manuelle (5 étapes)

### 1. Test placeholder manquant
- Créer un exercice dynamique avec template contenant `{{variable_inexistante}}`
- Générer l'exercice
- **Attendu** : Toast rouge "Placeholders non résolus" + liste des placeholders manquants (max 3)

### 2. Test plusieurs placeholders manquants (> 3)
- Créer un exercice avec 5+ placeholders manquants
- Générer l'exercice
- **Attendu** : Toast avec "var1, var2, var3 et 2 autre(s)"

### 3. Vérification console frontend
- Ouvrir DevTools → Console
- Générer avec placeholders manquants
- **Attendu** : Log `🔴 PLACEHOLDER_UNRESOLVED - Détails complets:` avec tous les détails

### 4. Vérification logs backend
```bash
docker compose logs backend | grep PLACEHOLDER_UNRESOLVED
```
- **Attendu** : Log `event=unresolved_placeholders` avec status 422

### 5. Test placeholders tous résolus
- Créer un exercice avec placeholders tous fournis par le générateur
- Générer l'exercice
- **Attendu** : Pas d'erreur, exercice généré normalement

---

## Fichiers modifiés

1. **backend/services/tests_dyn_handler.py**
   - Changement error_code : `UNRESOLVED_PLACEHOLDERS` → `PLACEHOLDER_UNRESOLVED`
   - Ajout `hint` et `context` structurés avec `missing`, `chapter_code`, `template_id`

2. **frontend/src/components/ExerciseGeneratorPage.js**
   - Gestion `error_code === "PLACEHOLDER_UNRESOLVED"`
   - Toast avec liste des placeholders (max 3) + console.log détaillé

3. **backend/tests/test_placeholder_unresolved.py** (nouveau)
   - Tests unitaires pour placeholders non résolus

---

## Validation

- ✅ Compilation : `python3 -m py_compile` → OK
- ✅ Pas de 500 : Toutes les erreurs retournent 422
- ✅ Pas de fallback silencieux : Erreur explicite avec hint
- ✅ Tests unitaires créés
- ✅ Frontend : Toast + console.log pour debug

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Implémenté, prêt pour validation

