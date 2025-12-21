# Synthèse — Root Cause Variants d'énoncés dynamiques
**Date :** 2025-01-XX

---

## 🔍 Problèmes signalés

1. **Variants non affichés** lors de l'édition d'un exercice existant
2. **Modifications non sauvegardées** : changement Direct → Diagnostic non persisté
3. **Templates vides** lors de la création → validation échoue

---

## 🎯 Root Cause identifiée

### Problème principal : Templates non initialisés pour SIMPLIFICATION_FRACTIONS_V2

**Cause** : `getDynamicTemplates()` ne retournait rien pour `SIMPLIFICATION_FRACTIONS_V2`

**Impact en cascade** :
1. Variants initialisés avec templates vides → validation échoue
2. Section variants non affichée (car `hasTemplateVariants` est `false`)
3. Modifications non sauvegardées (car variants vides → backend peut ignorer)

---

## ✅ Corrections appliquées

### 1. Ajout des templates dans `getDynamicTemplates()`
- ✅ Templates Variant A (Standard) ajoutés pour `SIMPLIFICATION_FRACTIONS_V2`

### 2. Nouvelle fonction `getSimplificationFractionsV2Templates()`
- ✅ Retourne les templates pour les variants A, B, C
- ✅ Utilisée pour initialiser les variants avec les bons templates

### 3. Initialisation des variants A/B/C
- ✅ Lors de la sélection du générateur (création)
- ✅ Lors du chargement depuis l'API (édition, si variants vides)
- ✅ Via `GeneratorVariablesPanel` (chargement du schéma)

### 4. Amélioration du payload
- ✅ S'assurer que `template_variants` est toujours un tableau (même vide)

---

## 🧪 Tests de validation

### Test 1 : Édition exercice existant
- Ouvrir un exercice `SIMPLIFICATION_FRACTIONS_V2`
- **Attendu** : Section variants affichée avec A/B/C

### Test 2 : Modification variant
- Changer de "Direct" à "Diagnostic"
- Modifier le template
- Sauvegarder
- **Attendu** : Modifications persistées

### Test 3 : Création exercice premium
- Créer un exercice `SIMPLIFICATION_FRACTIONS_V2`
- **Attendu** : Variants A/B/C auto-initialisés avec templates remplis

### Test 4 : Validation
- Créer un exercice avec variants remplis
- **Attendu** : Pas d'erreur de validation

---

## 📋 Fichiers modifiés

- `frontend/src/components/admin/ChapterExercisesAdminPage.js` :
  - Ligne ~515 : Ajout templates `SIMPLIFICATION_FRACTIONS_V2`
  - Ligne ~531 : Nouvelle fonction `getSimplificationFractionsV2Templates()`
  - Ligne ~587 : Initialisation variants lors du chargement depuis l'API
  - Ligne ~1305 : Initialisation variants lors de la sélection du générateur
  - Ligne ~1380 : Initialisation variants via `GeneratorVariablesPanel`
  - Ligne ~735 : Amélioration du payload

---

## ⚠️ Points d'attention

### Backend : Sauvegarde de tableau vide

**Problème potentiel** : Si `template_variants` est un tableau vide `[]`, le backend le convertit en `None` (ligne 766 de `exercise_persistence_service.py`).

**Code backend actuel** :
```python
if request.template_variants is not None:
    update_data["template_variants"] = [
        variant.dict() if hasattr(variant, 'dict') else variant
        for variant in request.template_variants
    ] if request.template_variants else None  # ❌ [] devient None
```

**Impact** : Si on envoie `[]`, le backend ne met pas à jour le champ (reste à l'ancienne valeur).

**Solution frontend appliquée** : Toujours envoyer un tableau non vide pour les générateurs premium (variants A/B/C initialisés).

---

## 🔍 Debugging

### Console logs à ajouter (temporairement)

```javascript
// Dans handleSubmit, avant l'envoi
console.log('🔍 Payload template_variants:', payload.template_variants);
console.log('🔍 Payload is_dynamic:', payload.is_dynamic);
console.log('🔍 Payload generator_key:', payload.generator_key);

// Dans handleOpenEdit, après chargement
console.log('🔍 Exercise template_variants:', exercise.template_variants);
console.log('🔍 FormData template_variants:', formData.template_variants);
```

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Root cause identifiée, corrections appliquées


