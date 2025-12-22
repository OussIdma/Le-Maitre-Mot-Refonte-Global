# Corrections appliquées — Variants d'énoncés dynamiques
**Date :** 2025-01-XX  
**Statut :** ✅ Corrections appliquées, prêtes pour validation

---

## 🔍 Root Cause identifiée

### Problème 1 : Variants non affichés en édition
- **Cause** : `getDynamicTemplates()` ne retournait rien pour `SIMPLIFICATION_FRACTIONS_V2`
- **Impact** : Les variants étaient initialisés avec des templates vides → validation échoue

### Problème 2 : Templates vides lors de l'initialisation
- **Cause** : Quand on sélectionne `SIMPLIFICATION_FRACTIONS_V2`, les variants A/B/C étaient initialisés avec `templates.enonce` et `templates.solution` qui étaient vides
- **Impact** : Validation échoue car templates requis mais vides

### Problème 3 : Variants non chargés depuis l'API
- **Cause** : Si `template_variants` est vide en DB, les variants n'étaient pas initialisés pour les générateurs premium
- **Impact** : Section variants non affichée même pour les générateurs premium

### Problème 4 : Modifications non sauvegardées
- **Cause** : Le backend sauvegarde bien `template_variants`, mais le frontend peut ne pas envoyer les modifications si la condition n'est pas remplie
- **Impact** : Modifications de variant (Direct → Diagnostic) non persistées

---

## ✅ Corrections appliquées

### Correction 1 : Ajout des templates pour SIMPLIFICATION_FRACTIONS_V2

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

**Nouvelle fonction** : `getSimplificationFractionsV2Templates()` (ligne ~531)
- Retourne les templates pour les variants A, B, C
- Utilisée pour initialiser les variants avec les bons templates

---

### Correction 2 : Initialisation des variants A/B/C avec les bons templates

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~1305)

**Modification** :
- Utilise `getSimplificationFractionsV2Templates()` pour obtenir les templates A/B/C
- Initialise chaque variant avec son template spécifique (A=Direct, B=Guidé, C=Diagnostic)

**Avant** :
```javascript
enonce_template_html: templates.enonce || '' // ❌ vide
```

**Après** :
```javascript
enonce_template_html: variantTemplates.A.enonce // ✅ Template correct
```

---

### Correction 3 : Chargement depuis l'API avec initialisation premium

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~587)

**Modification** :
- Si `template_variants` est vide en DB mais que c'est un générateur premium → initialise les variants A/B/C
- Utilise les templates existants en DB si présents, sinon utilise les templates par défaut

**Logique** :
```javascript
if (exercise.generator_key === 'SIMPLIFICATION_FRACTIONS_V2' && exercise.is_dynamic) {
  const variantTemplates = getSimplificationFractionsV2Templates();
  return [
    { id: 'A', ..., enonce_template_html: exercise.enonce_template_html || variantTemplates.A.enonce },
    { id: 'B', ..., enonce_template_html: variantTemplates.B.enonce },
    { id: 'C', ..., enonce_template_html: variantTemplates.C.enonce }
  ];
}
```

---

### Correction 4 : Initialisation via GeneratorVariablesPanel

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~1380)

**Modification** :
- `onTemplatesLoaded` initialise les variants A/B/C pour les générateurs premium
- Utilise `getSimplificationFractionsV2Templates()` pour obtenir les templates corrects

---

## 🧪 Tests de validation

### Test 1 : Édition d'un exercice existant avec variants

**Actions** :
1. Aller sur `/admin/curriculum/6e_AA_TEST/exercises`
2. Cliquer sur "Modifier" pour un exercice avec `generator_key=SIMPLIFICATION_FRACTIONS_V2`

**Résultat attendu** :
- ✅ La section "Variants d'énoncés dynamiques" s'affiche
- ✅ Les boutons A/B/C sont visibles et cliquables
- ✅ Les templates énoncé/solution sont remplis pour chaque variant

---

### Test 2 : Modification d'un variant (Direct → Diagnostic)

**Actions** :
1. Ouvrir un exercice avec variants A/B/C
2. Cliquer sur "Diagnostic" (variant C)
3. Modifier le template énoncé ou solution
4. Sauvegarder

**Résultat attendu** :
- ✅ Message de confirmation "Exercice modifié avec succès"
- ✅ Les modifications sont persistées en DB
- ✅ Après rechargement, le variant C contient les modifications

**Vérification backend** :
```bash
docker compose exec backend mongosh le_maitre_mot_db --eval "db.admin_exercises.findOne({chapter_code:'6E_AA_TEST', generator_key:'SIMPLIFICATION_FRACTIONS_V2'}, {template_variants:1})"
```

**Résultat attendu** : `template_variants` contient les 3 variants avec les modifications

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
- [x] Initialisation des variants A/B/C avec les bons templates lors de la sélection du générateur
- [x] Initialisation des variants A/B/C lors du chargement depuis l'API (si premium et variants vides)
- [x] Initialisation via `GeneratorVariablesPanel` pour les générateurs premium
- [ ] Test édition : variants affichés ✅
- [ ] Test modification : modifications sauvegardées ✅
- [ ] Test création : variants auto-initialisés ✅
- [ ] Test validation : pas d'erreur avec templates remplis ✅
- [ ] Test statique : pas de régression ✅

---

## 🔍 Points de vérification

### Si les variants ne s'affichent toujours pas

1. **Vérifier la console** :
   ```javascript
   console.log('formData.is_dynamic:', formData.is_dynamic);
   console.log('formData.generator_key:', formData.generator_key);
   console.log('formData.template_variants:', formData.template_variants);
   console.log('shouldShowVariantsSection:', shouldShowVariantsSection);
   ```

2. **Vérifier le chargement depuis l'API** :
   - Ouvrir DevTools → Network → Filtrer `/api/admin/chapters/.../exercises`
   - Vérifier que la réponse contient `template_variants` (même si vide)

3. **Vérifier l'initialisation** :
   - Si `template_variants` est vide mais `generator_key === 'SIMPLIFICATION_FRACTIONS_V2'`, les variants doivent être initialisés

### Si les modifications ne sont pas sauvegardées

1. **Vérifier le payload envoyé** :
   ```javascript
   console.log('Payload avant envoi:', payload);
   console.log('template_variants dans payload:', payload.template_variants);
   ```

2. **Vérifier la réponse backend** :
   - Ouvrir DevTools → Network → Filtrer `PUT /api/admin/chapters/.../exercises/...`
   - Vérifier que la réponse est 200 OK

3. **Vérifier en DB** :
   ```bash
   docker compose exec backend mongosh le_maitre_mot_db --eval "db.admin_exercises.findOne({chapter_code:'6E_AA_TEST', generator_key:'SIMPLIFICATION_FRACTIONS_V2'}, {template_variants:1})"
   ```

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Corrections appliquées, prêtes pour validation


