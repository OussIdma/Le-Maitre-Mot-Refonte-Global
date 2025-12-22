# Fix Network Error - Pool vide et variant_id invalide

**Date :** 2025-01-XX  
**Statut :** ✅ Implémenté

---

## Objectif

Supprimer les "Network Error" génériques quand :
- Le pool MIXED est vide (aucun exercice dynamique disponible)
- Le variant_id est invalide (n'existe pas dans template_variants)

Remplacer par des erreurs HTTP 422 structurées avec messages UI clairs.

---

## Corrections backend

### 1. Pool vide (MIXED pipeline)

**Fichier** : `backend/routes/exercises_routes.py` (ligne ~1056)

**Avant** : Fallback silencieux ou erreur générique

**Après** : HTTP 422 avec JSON structuré
```json
{
  "error_code": "POOL_EMPTY",
  "error": "pool_empty",
  "message": "Aucun exercice dynamique disponible pour ce chapitre avec les critères demandés.",
  "hint": "Vérifiez que des exercices dynamiques existent pour le chapitre '6E_AA_TEST' avec difficulty='facile' et offer='free'. Vous pouvez essayer une autre difficulté ou contacter l'administrateur.",
  "context": {
    "chapter": "6E_AA_TEST",
    "difficulty": "facile",
    "offer": "free",
    "pipeline": "MIXED"
  }
}
```

**Code ajouté** :
```python
# Pool vide : aucun exercice dynamique disponible
obs_logger.error(
    "event=pool_empty",
    event="pool_empty",
    outcome="error",
    reason="no_dynamic_exercises_available",
    pool_size=0,
    **ctx
)
raise HTTPException(
    status_code=422,
    detail={
        "error_code": "POOL_EMPTY",
        "error": "pool_empty",
        "message": f"Aucun exercice dynamique disponible pour ce chapitre avec les critères demandés.",
        "hint": f"Vérifiez que des exercices dynamiques existent pour le chapitre '{chapter_code_for_db}' avec difficulty='{request.difficulte}' et offer='{request.offer}'. Vous pouvez essayer une autre difficulté ou contacter l'administrateur.",
        "context": {
            "chapter": chapter_code_for_db,
            "difficulty": request.difficulte,
            "offer": request.offer,
            "pipeline": "MIXED"
        }
    }
)
```

---

### 2. Variant_id invalide

**Fichier** : `backend/services/tests_dyn_handler.py` (ligne ~502)

**Avant** : HTTP 422 mais sans `hint` et `context` structuré

**Après** : HTTP 422 avec `hint` et `context` enrichis
```json
{
  "error_code": "VARIANT_ID_NOT_FOUND",
  "error": "variant_id_not_found",
  "message": "Le variant_id 'Z' n'a pas été trouvé dans les template_variants.",
  "hint": "Les variants disponibles sont : A, B, C. Vérifiez que le variant_id demandé existe pour cet exercice.",
  "context": {
    "exercise_id": "test_exercise_1",
    "variant_id_requested": "Z",
    "variants_present": ["A", "B", "C"]
  }
}
```

**Code modifié** :
```python
available_variant_ids = [getattr(v, 'id', None) for v in variant_objs]
raise HTTPException(
    status_code=422,
    detail={
        "error_code": "VARIANT_ID_NOT_FOUND",
        "error": "variant_id_not_found",
        "message": f"Le variant_id '{variant_id_from_params}' n'a pas été trouvé dans les template_variants.",
        "hint": f"Les variants disponibles sont : {', '.join(map(str, available_variant_ids))}. Vérifiez que le variant_id demandé existe pour cet exercice.",
        "context": {
            "exercise_id": exercise_template.get("id"),
            "variant_id_requested": variant_id_from_params,
            "variants_present": available_variant_ids
        }
    }
)
```

---

## Corrections frontend

### Gestion des erreurs 422 avec error_code

**Fichier** : `frontend/src/components/ExerciseGeneratorPage.js` (ligne ~404)

**Modifications** :
1. Import de `useToast` pour afficher des notifications
2. Détection de `error_code` dans la réponse 422
3. Messages spécifiques selon `error_code` :
   - `POOL_EMPTY` → "Aucun exercice disponible" + hint
   - `VARIANT_ID_NOT_FOUND` → "Variant d'exercice introuvable" + hint
4. Toast avec titre et description

**Code ajouté** :
```javascript
import { useToast } from "../hooks/use-toast";

const ExerciseGeneratorPage = () => {
  const { toast } = useToast();
  
  // ... dans le catch ...
  if (error.response?.data) {
    const data = error.response.data;
    const detail = data.detail || data;
    
    // Format FastAPI avec error_code structuré
    if (detail.error_code) {
      errorCode = detail.error_code;
      errorMessage = detail.message || errorMessage;
      hint = detail.hint;
      
      // Messages spécifiques selon error_code
      if (errorCode === "POOL_EMPTY") {
        errorMessage = "Aucun exercice disponible";
        hint = hint || `Aucun exercice dynamique trouvé pour ce chapitre avec les critères demandés. Essayez une autre difficulté.`;
      } else if (errorCode === "VARIANT_ID_NOT_FOUND") {
        errorMessage = "Variant d'exercice introuvable";
        hint = hint || `Le variant demandé n'existe pas pour cet exercice.`;
      }
      
      // Afficher toast avec message spécifique
      toast({
        title: errorMessage,
        description: hint || "Veuillez réessayer avec d'autres paramètres.",
        variant: "destructive"
      });
    }
  }
}
```

---

## Tests

### Tests backend

**Fichier** : `backend/tests/test_pool_empty_variant_errors.py` (nouveau)

**Tests inclus** :
1. `test_pool_empty_mixed_pipeline` : Vérifie que pool vide retourne 422 avec `POOL_EMPTY`
2. `test_variant_id_not_found` : Vérifie que variant_id invalide retourne 422 avec `VARIANT_ID_NOT_FOUND`
3. `test_pool_empty_integration` : Test d'intégration avec client FastAPI

**Exécution** :
```bash
pytest backend/tests/test_pool_empty_variant_errors.py -v
```

---

## Checklist de vérification manuelle

### 1. Test pool vide
- [ ] Aller sur la page de génération d'exercices
- [ ] Sélectionner un chapitre sans exercices dynamiques (ex: `6E_AA_TEST` en difficulté `facile`)
- [ ] Cliquer sur "Générer"
- [ ] **Attendu** : Toast rouge avec "Aucun exercice disponible" + message explicatif, pas de "Network Error"

### 2. Test variant_id invalide
- [ ] Créer un exercice dynamique avec variants A/B/C
- [ ] Modifier manuellement le `variant_id` dans la requête pour utiliser "Z" (inexistant)
- [ ] Générer l'exercice
- [ ] **Attendu** : Toast rouge avec "Variant d'exercice introuvable" + liste des variants disponibles

### 3. Test erreur générique (non 422)
- [ ] Simuler une erreur réseau (déconnecter le backend)
- [ ] Générer un exercice
- [ ] **Attendu** : Toast générique "Erreur" avec message d'erreur réseau

### 4. Vérification logs backend
- [ ] Vérifier les logs : `event=pool_empty` ou `event=variant_fixed_error` doivent apparaître
- [ ] Vérifier que le status code est bien 422 (pas 500)

### 5. Vérification console frontend
- [ ] Ouvrir DevTools → Console
- [ ] Générer un exercice avec pool vide
- [ ] **Attendu** : Log `error_code: "POOL_EMPTY"` dans la console, pas d'erreur réseau générique

---

## Fichiers modifiés

1. **backend/routes/exercises_routes.py**
   - Ajout gestion pool vide avec HTTP 422 structuré (ligne ~1056)

2. **backend/services/tests_dyn_handler.py**
   - Enrichissement erreur variant_id avec `hint` et `context` (ligne ~502)

3. **frontend/src/components/ExerciseGeneratorPage.js**
   - Import `useToast` (ligne ~37)
   - Gestion erreurs 422 avec `error_code` (ligne ~404-450)
   - Messages spécifiques pour `POOL_EMPTY` et `VARIANT_ID_NOT_FOUND`

4. **backend/tests/test_pool_empty_variant_errors.py** (nouveau)
   - Tests unitaires pour pool vide et variant_id invalide

---

## Résultat attendu

✅ **Avant** : "Network Error" générique, pas d'information utile  
✅ **Après** : Toast avec message clair + hint explicatif + contexte technique dans les logs

✅ **Pas de 500** : Toutes les erreurs de pool/variant retournent 422

✅ **UX améliorée** : L'utilisateur comprend pourquoi la génération a échoué et comment corriger

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Implémenté, prêt pour validation

