# Fix — Affichage des variants d'énoncés dynamiques dans l'admin
**Date :** 2025-01-XX  
**Problème :** Les variants d'énoncés (Direct/Guidé/Diagnostic) ne s'affichent pas dans l'admin pour `SIMPLIFICATION_FRACTIONS_V2`

---

## 🔍 Root Cause

### Problème identifié

1. **Condition d'affichage trop restrictive** :
   - La section "Variants d'énoncés dynamiques" était toujours affichée pour tous les exercices dynamiques
   - Mais le contenu (variants A/B/C) n'était visible que si `hasTemplateVariants` était `true`
   - `hasTemplateVariants` vérifie si `formData.template_variants` est un tableau non vide
   - Si un exercice dynamique n'a pas encore de `template_variants` en DB, la section est vide

2. **Mapping depuis l'API** :
   - Quand on charge un exercice depuis l'API, `template_variants` est mappé correctement (ligne 532)
   - Mais si `template_variants` est `undefined` ou `null`, il devient `[]` (tableau vide)
   - Un tableau vide fait que `hasTemplateVariants` est `false`, donc `isVariantMode` est `false`

3. **Générateurs premium** :
   - `SIMPLIFICATION_FRACTIONS_V2` est un générateur premium qui devrait toujours avoir des variants A/B/C
   - Mais la logique ne détecte pas automatiquement les générateurs premium

---

## 🔧 Corrections appliquées

### 1. Détection des générateurs premium

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~340)

**Modification** :
```javascript
// Avant
const hasTemplateVariants = Array.isArray(formData.template_variants) && formData.template_variants.length > 0;
const isVariantMode = hasTemplateVariants;

// Après
const isPremiumGenerator = formData.generator_key === 'SIMPLIFICATION_FRACTIONS_V2';
const hasTemplateVariants = Array.isArray(formData.template_variants) && formData.template_variants.length > 0;
const shouldShowVariantsSection = formData.is_dynamic && (hasTemplateVariants || isPremiumGenerator);
const isVariantMode = hasTemplateVariants || (isPremiumGenerator && formData.is_dynamic);
```

**Effet** :
- Les générateurs premium affichent la section variants même si la liste est vide
- Permet d'ajouter des variants pour les générateurs premium

---

### 2. Initialisation automatique des variants A/B/C

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~1298)

**Modification** :
```javascript
onValueChange={(v) => {
  const templates = getDynamicTemplates(v);
  setFormData(p => {
    const isPremiumGen = v === 'SIMPLIFICATION_FRACTIONS_V2';
    const shouldInitVariants = isPremiumGen && 
      (!Array.isArray(p.template_variants) || p.template_variants.length === 0);
    
    const baseUpdate = {
      ...p, 
      generator_key: v,
      enonce_template_html: templates.enonce,
      solution_template_html: templates.solution
    };
    
    // Initialiser les variants A/B/C pour les générateurs premium
    if (shouldInitVariants) {
      baseUpdate.template_variants = [
        { id: 'A', variant_id: 'A', label: 'Direct', weight: 1, ... },
        { id: 'B', variant_id: 'B', label: 'Guidé', weight: 1, ... },
        { id: 'C', variant_id: 'C', label: 'Diagnostic', weight: 1, ... }
      ];
    }
    
    return baseUpdate;
  });
}}
```

**Effet** :
- Quand on sélectionne `SIMPLIFICATION_FRACTIONS_V2`, les variants A/B/C sont automatiquement initialisés
- Facilite la création d'exercices premium

---

### 3. Condition d'affichage de la section

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~1391)

**Modification** :
```javascript
// Avant
{/* Bloc Variants d'énoncés */}
<div className="border border-purple-200 rounded-lg p-3 bg-white space-y-3">

// Après
{/* Bloc Variants d'énoncés - Affiché pour tous les exercices dynamiques, mais contenu conditionnel */}
{shouldShowVariantsSection && (
<div className="border border-purple-200 rounded-lg p-3 bg-white space-y-3">
```

**Effet** :
- La section n'est affichée que si l'exercice est dynamique ET (a des variants OU est premium)
- Évite d'afficher une section vide pour les exercices dynamiques non-premium sans variants

---

### 4. Message d'aide pour les générateurs premium

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~1495)

**Modification** :
```javascript
{!hasTemplateVariants && isPremiumGenerator && (
  <Alert className="border-blue-500 bg-blue-50">
    <AlertCircle className="h-4 w-4 text-blue-600" />
    <AlertDescription className="text-blue-800 text-xs">
      💡 Ce générateur premium supporte les variants A/B/C (Direct/Guidé/Diagnostic). 
      Cliquez sur "Ajouter" pour créer les variants.
    </AlertDescription>
  </Alert>
)}
```

**Effet** :
- Aide l'utilisateur à comprendre qu'il peut ajouter des variants pour les générateurs premium

---

### 5. Amélioration du mapping depuis l'API

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~532)

**Modification** :
```javascript
// Avant
template_variants: exercise.template_variants || []

// Après
template_variants: Array.isArray(exercise.template_variants) 
  ? exercise.template_variants 
  : (exercise.template_variants ? [exercise.template_variants] : [])
```

**Effet** :
- Gère mieux les cas où `template_variants` est un objet unique au lieu d'un tableau
- Assure toujours un tableau

---

## ✅ Tests de validation

### Test 1 : GET /api/v1/admin/exercises/{id}

```bash
curl -X GET "http://localhost:8000/api/admin/chapters/6E_AA_TEST/exercises/{id}" | jq '.template_variants'
```

**Résultat attendu** : Tableau avec variants A/B/C (ou tableau vide si pas encore créés)

---

### Test 2 : Ouvrir "Modifier un exercice" (6E_AA_TEST, SIMPLIFICATION_FRACTIONS_V2)

**Actions** :
1. Aller sur `/admin/curriculum/6E_AA_TEST/exercises`
2. Cliquer sur "Modifier" pour un exercice dynamique avec `generator_key=SIMPLIFICATION_FRACTIONS_V2`

**Résultat attendu** :
- ✅ La section "Variants d'énoncés dynamiques" s'affiche
- ✅ Si variants existent : les boutons A/B/C sont visibles
- ✅ Si variants absents : message d'aide + bouton "Ajouter" disponible

---

### Test 3 : Créer un nouvel exercice dynamique (SIMPLIFICATION_FRACTIONS_V2)

**Actions** :
1. Cliquer sur "Créer un exercice"
2. Activer "Exercice dynamique"
3. Sélectionner `SIMPLIFICATION_FRACTIONS_V2` dans le sélecteur

**Résultat attendu** :
- ✅ La section "Variants d'énoncés dynamiques" s'affiche immédiatement
- ✅ Les variants A/B/C sont automatiquement initialisés
- ✅ Les boutons A/B/C sont visibles et cliquables

---

### Test 4 : Pas de régression sur exercice statique

**Actions** :
1. Créer un exercice statique (is_dynamic=false)

**Résultat attendu** :
- ✅ La section "Variants d'énoncés dynamiques" ne s'affiche PAS
- ✅ Seuls les champs statiques (énoncé/solution HTML) sont visibles

---

## 📋 Checklist de validation

- [x] Détection des générateurs premium ajoutée
- [x] Initialisation automatique des variants A/B/C pour premium
- [x] Condition d'affichage corrigée (`shouldShowVariantsSection`)
- [x] Message d'aide pour générateurs premium sans variants
- [x] Mapping depuis l'API amélioré
- [ ] Test GET exercice → vérifier `template_variants` présent
- [ ] Test modifier exercice → section variants visible
- [ ] Test créer exercice premium → variants auto-initialisés
- [ ] Test exercice statique → section variants absente

---

## 🔍 Points de vérification

### Si la section ne s'affiche toujours pas

1. **Vérifier `formData.is_dynamic`** :
   - Doit être `true` pour les exercices dynamiques
   - Vérifier dans la console : `console.log(formData.is_dynamic)`

2. **Vérifier `formData.generator_key`** :
   - Doit être `'SIMPLIFICATION_FRACTIONS_V2'` pour les générateurs premium
   - Vérifier dans la console : `console.log(formData.generator_key)`

3. **Vérifier `template_variants` depuis l'API** :
   - Ouvrir DevTools → Network → Filtrer `/api/admin/chapters/.../exercises`
   - Vérifier que la réponse contient `template_variants` (tableau ou null)

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Corrections appliquées, prêtes pour validation


