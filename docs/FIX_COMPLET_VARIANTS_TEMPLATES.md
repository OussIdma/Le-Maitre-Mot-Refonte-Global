# Fix complet — Variants d'énoncés dynamiques
**Date :** 2025-01-XX  
**Statut :** ✅ Toutes les corrections appliquées

---

## 🔍 Root Cause identifiée

### Problème principal
**`getDynamicTemplates()` ne retournait rien pour `SIMPLIFICATION_FRACTIONS_V2`**

**Impact en cascade** :
1. Variants initialisés avec templates vides → validation échoue
2. Section variants non affichée (car `hasTemplateVariants` est `false`)
3. Modifications non sauvegardées (variants vides ou mal chargés)

---

## ✅ Corrections appliquées

### 1. Ajout des templates pour SIMPLIFICATION_FRACTIONS_V2

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~515)

**Modification** :
```javascript
if (generatorKey === 'SIMPLIFICATION_FRACTIONS_V2') {
  // Templates Variant A (Standard) par défaut
  return {
    enonce: "<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>",
    solution: `<ol>
  <li>{{step1}}</li>
  <li>{{step2}}</li>
  <li>{{step3}}</li>
  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>
</ol>`
  };
}
```

---

### 2. Nouvelle fonction `getSimplificationFractionsV2Templates()`

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~531)

**Fonctionnalité** :
- Retourne les templates pour les variants A, B, C
- Utilisée pour initialiser les variants avec les bons templates

**Templates** :
- **Variant A (Direct)** : Simplification directe
- **Variant B (Guidé)** : Avec `{{hint_display}}` et `{{method_explanation}}`
- **Variant C (Diagnostic)** : Avec `{{wrong_simplification}}`, `{{check_equivalence_str}}`, `{{diagnostic_explanation}}`

---

### 3. Initialisation des variants A/B/C lors du chargement depuis l'API

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~587)

**Logique améliorée** :
- Si variants existent en DB mais incomplets (B ou C manquants/vides) → compléter avec templates par défaut
- Si variants vides en DB mais générateur premium → initialiser A/B/C avec templates par défaut
- S'assurer que tous les variants A/B/C ont des templates non vides

**Code** :
```javascript
// Pour les générateurs premium, s'assurer que tous les variants A/B/C sont présents
if (exercise.generator_key === 'SIMPLIFICATION_FRACTIONS_V2' && exercise.is_dynamic) {
  const variantTemplates = getSimplificationFractionsV2Templates();
  const existingVariants = exercise.template_variants;
  const variantMap = {};
  existingVariants.forEach(v => {
    const key = v.variant_id || v.id;
    if (key) variantMap[key] = v;
  });
  
  // S'assurer que A, B, C existent avec leurs templates par défaut si absents ou vides
  return ['A', 'B', 'C'].map(variantId => {
    const existing = variantMap[variantId];
    if (existing) {
      // Variant existe : utiliser les templates existants, ou les templates par défaut si vides
      return {
        ...existing,
        enonce_template_html: existing.enonce_template_html?.trim() || variantTemplates[variantId].enonce,
        solution_template_html: existing.solution_template_html?.trim() || variantTemplates[variantId].solution
      };
    } else {
      // Variant absent : créer avec templates par défaut
      return {
        id: variantId,
        variant_id: variantId,
        label: variantId === 'A' ? 'Direct' : variantId === 'B' ? 'Guidé' : 'Diagnostic',
        weight: 1,
        enonce_template_html: variantTemplates[variantId].enonce,
        solution_template_html: variantTemplates[variantId].solution
      };
    }
  });
}
```

---

### 4. Initialisation lors de la sélection du générateur

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~1305)

**Modification** :
- Utilise `getSimplificationFractionsV2Templates()` pour obtenir les templates A/B/C
- Initialise chaque variant avec son template spécifique

---

### 5. Initialisation via GeneratorVariablesPanel

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~1380)

**Modification** :
- `onTemplatesLoaded` initialise les variants A/B/C pour les générateurs premium
- Utilise `getSimplificationFractionsV2Templates()` pour obtenir les templates corrects
- Corrige la closure (utilise `p` au lieu de `formData`)

---

### 6. Amélioration du payload

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~735)

**Modification** :
- S'assurer que `template_variants` est toujours un tableau (même vide) pour les exercices dynamiques
- Garantit que le backend reçoit toujours `template_variants` pour pouvoir le sauvegarder

---

## 🧪 Tests de validation

### Test 1 : Édition d'un exercice existant

**Actions** :
1. Aller sur `/admin/curriculum/6e_AA_TEST/exercises`
2. Cliquer sur "Modifier" pour un exercice avec `generator_key=SIMPLIFICATION_FRACTIONS_V2`

**Résultat attendu** :
- ✅ La section "Variants d'énoncés dynamiques" s'affiche
- ✅ Les boutons A/B/C sont visibles et cliquables
- ✅ Les templates énoncé/solution sont remplis pour chaque variant (même si vides en DB)

**Vérification** :
```javascript
// Dans la console du navigateur
console.log('Variants chargés:', formData.template_variants);
// Doit afficher 3 variants avec templates remplis
```

---

### Test 2 : Modification d'un variant (Direct → Diagnostic)

**Actions** :
1. Ouvrir un exercice avec variants A/B/C
2. Cliquer sur "Diagnostic" (variant C)
3. Modifier le template énoncé (ex: ajouter du texte)
4. Sauvegarder

**Résultat attendu** :
- ✅ Message de confirmation "Exercice modifié avec succès"
- ✅ Les modifications sont persistées en DB
- ✅ Après rechargement, le variant C contient les modifications

**Vérification backend** :
```bash
docker compose exec backend mongosh le_maitre_mot_db --eval "db.admin_exercises.findOne({chapter_code:'6E_AA_TEST', generator_key:'SIMPLIFICATION_FRACTIONS_V2'}, {template_variants:1})" | jq '.template_variants[] | select(.variant_id=="C") | .enonce_template_html'
```

**Résultat attendu** : Le template modifié est présent

---

### Test 3 : Création d'un nouvel exercice premium

**Actions** :
1. Cliquer sur "+ Ajouter"
2. Activer "Exercice dynamique"
3. Sélectionner `SIMPLIFICATION_FRACTIONS_V2` dans le sélecteur

**Résultat attendu** :
- ✅ La section "Variants d'énoncés dynamiques" s'affiche immédiatement
- ✅ Les variants A/B/C sont automatiquement initialisés avec les bons templates
- ✅ Les templates énoncé/solution sont remplis pour chaque variant
- ✅ Pas d'erreur de validation

**Vérification** :
- Cliquer sur chaque variant (A, B, C) → les templates doivent être différents
- Variant A : template simple
- Variant B : contient `{{hint_display}}`
- Variant C : contient `{{wrong_simplification}}` et `{{check_equivalence_str}}`

---

### Test 4 : Validation avec templates remplis

**Actions** :
1. Créer un exercice premium avec variants A/B/C
2. Vérifier que tous les templates sont remplis
3. Cliquer sur "Sauvegarder"

**Résultat attendu** :
- ✅ Pas d'erreur "Certains variants contiennent des erreurs"
- ✅ Message de confirmation "Exercice créé avec succès"
- ✅ L'exercice est visible dans la liste

---

### Test 5 : Pas de régression sur exercice statique

**Actions** :
1. Créer un exercice statique (is_dynamic=false)

**Résultat attendu** :
- ✅ La section "Variants d'énoncés dynamiques" ne s'affiche PAS
- ✅ Seuls les champs statiques (énoncé/solution HTML) sont visibles

---

## 📋 Checklist de validation

- [x] Templates ajoutés pour `SIMPLIFICATION_FRACTIONS_V2` dans `getDynamicTemplates()`
- [x] Fonction `getSimplificationFractionsV2Templates()` créée
- [x] Initialisation des variants A/B/C lors de la sélection du générateur
- [x] Initialisation des variants A/B/C lors du chargement depuis l'API (avec complétion si incomplets)
- [x] Initialisation via `GeneratorVariablesPanel` pour les générateurs premium
- [x] Amélioration du payload (s'assurer que `template_variants` est toujours un tableau)
- [ ] **Test édition** : variants affichés avec templates remplis
- [ ] **Test modification** : modifications sauvegardées et persistées
- [ ] **Test création** : variants auto-initialisés avec templates remplis
- [ ] **Test validation** : pas d'erreur avec templates remplis
- [ ] **Test statique** : pas de régression

---

## 🔍 Points de vérification

### Si les variants ne s'affichent toujours pas

1. **Vérifier la console** :
   ```javascript
   console.log('formData.is_dynamic:', formData.is_dynamic);
   console.log('formData.generator_key:', formData.generator_key);
   console.log('formData.template_variants:', formData.template_variants);
   console.log('shouldShowVariantsSection:', shouldShowVariantsSection);
   console.log('isPremiumGenerator:', isPremiumGenerator);
   ```

2. **Vérifier le chargement depuis l'API** :
   - Ouvrir DevTools → Network → Filtrer `/api/admin/chapters/.../exercises`
   - Vérifier que la réponse contient `template_variants` (même si vide)
   - Vérifier que `generator_key` est bien `SIMPLIFICATION_FRACTIONS_V2`

3. **Vérifier l'initialisation** :
   - Si `template_variants` est vide mais `generator_key === 'SIMPLIFICATION_FRACTIONS_V2'`, les variants doivent être initialisés
   - Si `template_variants` existe mais incomplet (B ou C manquants), ils doivent être complétés

### Si les modifications ne sont pas sauvegardées

1. **Vérifier le payload envoyé** :
   ```javascript
   // Dans handleSubmit, avant l'envoi
   console.log('🔍 Payload template_variants:', JSON.stringify(payload.template_variants, null, 2));
   console.log('🔍 Payload is_dynamic:', payload.is_dynamic);
   console.log('🔍 Payload generator_key:', payload.generator_key);
   ```

2. **Vérifier la réponse backend** :
   - Ouvrir DevTools → Network → Filtrer `PUT /api/admin/chapters/.../exercises/...`
   - Vérifier que la réponse est 200 OK
   - Vérifier le body de la requête : `template_variants` doit être présent

3. **Vérifier en DB** :
   ```bash
   docker compose exec backend mongosh le_maitre_mot_db --eval "db.admin_exercises.findOne({chapter_code:'6E_AA_TEST', generator_key:'SIMPLIFICATION_FRACTIONS_V2'}, {template_variants:1})" | jq '.template_variants'
   ```

4. **Vérifier que `updateVariantField` fonctionne** :
   ```javascript
   // Dans updateVariantField, ajouter un log
   console.log('🔍 updateVariantField:', { index, field, value, updated: updated.length });
   ```

---

## 🐛 Problèmes connus / Limitations

### Backend : Sauvegarde de tableau vide

**Problème** : Si `template_variants` est un tableau vide `[]`, le backend le convertit en `None` (ligne 766 de `exercise_persistence_service.py`).

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

**Solution backend recommandée** (future amélioration) :
```python
if request.template_variants is not None:
    update_data["template_variants"] = [
        variant.dict() if hasattr(variant, 'dict') else variant
        for variant in request.template_variants
    ]  # ✅ Sauvegarder [] si tableau vide
```

---

## 📝 Fichiers modifiés

- `frontend/src/components/admin/ChapterExercisesAdminPage.js` :
  - Ligne ~515 : Ajout templates `SIMPLIFICATION_FRACTIONS_V2` dans `getDynamicTemplates()`
  - Ligne ~531 : Nouvelle fonction `getSimplificationFractionsV2Templates()`
  - Ligne ~340 : Détection premium + condition d'affichage `shouldShowVariantsSection`
  - Ligne ~587 : Initialisation variants lors du chargement depuis l'API (avec complétion)
  - Ligne ~1305 : Initialisation variants lors de la sélection du générateur
  - Ligne ~1380 : Initialisation variants via `GeneratorVariablesPanel` (closure corrigée)
  - Ligne ~735 : Amélioration du payload (s'assurer que `template_variants` est toujours un tableau)

---

## 🎯 Résumé des corrections

1. ✅ **Templates ajoutés** : `SIMPLIFICATION_FRACTIONS_V2` retourne maintenant des templates
2. ✅ **Fonction dédiée** : `getSimplificationFractionsV2Templates()` pour les variants A/B/C
3. ✅ **Initialisation complète** : Variants A/B/C initialisés avec templates remplis dans tous les cas
4. ✅ **Chargement amélioré** : Complétion des variants manquants/vides lors du chargement depuis l'API
5. ✅ **Payload amélioré** : `template_variants` toujours présent dans le payload

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Toutes les corrections appliquées, prêtes pour validation


