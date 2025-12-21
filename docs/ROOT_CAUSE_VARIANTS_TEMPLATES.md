# Root Cause — Variants d'énoncés dynamiques non affichés/sauvegardés
**Date :** 2025-01-XX  
**Problèmes signalés :**
1. Variants non affichés lors de l'édition d'un exercice existant
2. Modifications de variant (Direct → Diagnostic) non sauvegardées
3. Templates vides lors de la création (validation échoue)

---

## 🔍 Root Cause Analysis

### Problème 1 : Variants non affichés en édition

**Cause identifiée** :
- `getDynamicTemplates()` ne retourne rien pour `SIMPLIFICATION_FRACTIONS_V2`
- La fonction retourne `{ enonce: '', solution: '' }` pour les générateurs non reconnus
- Quand on charge un exercice depuis l'API, `template_variants` peut être un tableau vide `[]`
- `hasTemplateVariants` est `false` → `shouldShowVariantsSection` est `false` (même pour premium)

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~486)

**Code actuel** :
```javascript
const getDynamicTemplates = (generatorKey) => {
  if (generatorKey === 'THALES_V1' || generatorKey === 'THALES_V2') {
    return { enonce: '...', solution: '...' };
  }
  if (generatorKey === 'SYMETRIE_AXIALE_V2') {
    return { enonce: '...', solution: '...' };
  }
  return { enonce: '', solution: '' }; // ❌ PROBLÈME : retourne vide pour SIMPLIFICATION_FRACTIONS_V2
};
```

---

### Problème 2 : Templates vides lors de l'initialisation

**Cause identifiée** :
- Quand on sélectionne `SIMPLIFICATION_FRACTIONS_V2`, les variants A/B/C sont initialisés avec `templates.enonce` et `templates.solution`
- Mais `getDynamicTemplates('SIMPLIFICATION_FRACTIONS_V2')` retourne `{ enonce: '', solution: '' }`
- Donc les variants sont créés avec des templates vides

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~1318)

**Code actuel** :
```javascript
if (shouldInitVariants) {
  baseUpdate.template_variants = [
    { id: 'A', variant_id: 'A', label: 'Direct', weight: 1, 
      enonce_template_html: templates.enonce || '', // ❌ templates.enonce est vide !
      solution_template_html: templates.solution || '' // ❌ templates.solution est vide !
    },
    // ...
  ];
}
```

---

### Problème 3 : Modifications de variant non sauvegardées

**Cause identifiée** :
- `updateVariantField()` met bien à jour le state local
- Mais le payload envoyé au backend peut ne pas contenir les variants modifiés si la condition n'est pas remplie
- Vérifier que `payload.template_variants` contient bien les modifications

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~653)

**Code actuel** :
```javascript
if (payload.is_dynamic && Array.isArray(payload.template_variants) && payload.template_variants.length > 0) {
  const first = payload.template_variants[0];
  payload.enonce_template_html = first.enonce_template_html || '';
  payload.solution_template_html = first.solution_template_html || '';
}
// ✅ Les variants sont bien dans le payload, mais peut-être que le backend ne les sauvegarde pas ?
```

---

### Problème 4 : Validation échoue (templates vides)

**Cause identifiée** :
- La validation vérifie que chaque variant a `enonce_template_html` et `solution_template_html` non vides
- Si les templates sont vides (problème 2), la validation échoue

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~601)

**Code actuel** :
```javascript
if (!variant.enonce_template_html?.trim()) {
  errors.template_variants[`enonce_${idx}`] = "Le template énoncé est requis pour chaque variant";
}
if (!variant.solution_template_html?.trim()) {
  errors.template_variants[`solution_${idx}`] = "Le template solution est requis pour chaque variant";
}
```

---

## 🔧 Corrections à appliquer

### Correction 1 : Ajouter les templates pour SIMPLIFICATION_FRACTIONS_V2

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~486)

**Modification** :
```javascript
const getDynamicTemplates = (generatorKey) => {
  if (generatorKey === 'THALES_V1' || generatorKey === 'THALES_V2') {
    return { /* ... */ };
  }
  if (generatorKey === 'SYMETRIE_AXIALE_V2') {
    return { /* ... */ };
  }
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
  return { enonce: '', solution: '' };
};
```

---

### Correction 2 : Initialiser les variants A/B/C avec les bons templates

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~1318)

**Modification** :
```javascript
// Initialiser les variants A/B/C pour les générateurs premium
if (shouldInitVariants) {
  // Templates pour chaque variant (depuis le générateur)
  const templateA = {
    enonce: "<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>",
    solution: `<ol>
  <li>{{step1}}</li>
  <li>{{step2}}</li>
  <li>{{step3}}</li>
  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>
</ol>`
  };
  
  const templateB = {
    enonce: `<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>
{{hint_display}}`,
    solution: `<ol>
  <li><strong>Méthode :</strong> {{method_explanation}}</li>
  <li>{{step1}}</li>
  <li>{{step2}}</li>
  <li>{{step3}}</li>
  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>
</ol>`
  };
  
  const templateC = {
    enonce: `<p><strong>Analyse cette simplification :</strong></p>
<p>Fraction initiale : <strong>{{fraction}}</strong></p>
<p>Simplification proposée : <strong>{{wrong_simplification}}</strong></p>
<p><em>Cette simplification est-elle correcte ?</em></p>`,
    solution: `<ol>
  <li><strong>Vérification :</strong> {{check_equivalence_str}}</li>
  <li><strong>Conclusion :</strong> {{diagnostic_explanation}}</li>
  <li><strong>Simplification correcte :</strong> {{fraction_reduite}}</li>
</ol>`
  };
  
  baseUpdate.template_variants = [
    { id: 'A', variant_id: 'A', label: 'Direct', weight: 1, 
      enonce_template_html: templateA.enonce, 
      solution_template_html: templateA.solution 
    },
    { id: 'B', variant_id: 'B', label: 'Guidé', weight: 1, 
      enonce_template_html: templateB.enonce, 
      solution_template_html: templateB.solution 
    },
    { id: 'C', variant_id: 'C', label: 'Diagnostic', weight: 1, 
      enonce_template_html: templateC.enonce, 
      solution_template_html: templateC.solution 
    }
  ];
}
```

---

### Correction 3 : Charger les templates depuis GeneratorVariablesPanel pour les variants

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~1382)

**Modification** :
```javascript
<GeneratorVariablesPanel 
  generatorKey={formData.generator_key}
  onTemplatesLoaded={(templates) => {
    // Pour les générateurs premium, initialiser les variants si absents
    if (formData.generator_key === 'SIMPLIFICATION_FRACTIONS_V2' && 
        (!Array.isArray(formData.template_variants) || formData.template_variants.length === 0)) {
      // Initialiser les variants A/B/C avec les templates du générateur
      const templateA = { /* ... */ };
      const templateB = { /* ... */ };
      const templateC = { /* ... */ };
      
      setFormData(p => ({
        ...p,
        template_variants: [
          { id: 'A', variant_id: 'A', label: 'Direct', weight: 1, ...templateA },
          { id: 'B', variant_id: 'B', label: 'Guidé', weight: 1, ...templateB },
          { id: 'C', variant_id: 'C', label: 'Diagnostic', weight: 1, ...templateC }
        ]
      }));
    } else {
      // Mode legacy : mettre à jour les templates uniques
      if (!formData.enonce_template_html && !formData.solution_template_html) {
        setFormData(p => ({
          ...p,
          enonce_template_html: templates.enonce,
          solution_template_html: templates.solution
        }));
      }
    }
  }}
/>
```

---

### Correction 4 : Vérifier le chargement depuis l'API

**Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js` (ligne ~538)

**Problème potentiel** :
- Si `exercise.template_variants` est `undefined` ou `null`, il devient `[]`
- Pour les générateurs premium, il faut initialiser les variants même si vides en DB

**Modification** :
```javascript
template_variants: (() => {
  // Si template_variants existe et est un tableau non vide, l'utiliser
  if (Array.isArray(exercise.template_variants) && exercise.template_variants.length > 0) {
    return exercise.template_variants;
  }
  // Si c'est un générateur premium, initialiser les variants A/B/C
  if (exercise.generator_key === 'SIMPLIFICATION_FRACTIONS_V2' && exercise.is_dynamic) {
    return [
      { id: 'A', variant_id: 'A', label: 'Direct', weight: 1, 
        enonce_template_html: exercise.enonce_template_html || '', 
        solution_template_html: exercise.solution_template_html || '' 
      },
      { id: 'B', variant_id: 'B', label: 'Guidé', weight: 1, 
        enonce_template_html: '', 
        solution_template_html: '' 
      },
      { id: 'C', variant_id: 'C', label: 'Diagnostic', weight: 1, 
        enonce_template_html: '', 
        solution_template_html: '' 
      }
    ];
  }
  // Sinon, tableau vide
  return [];
})()
```

---

## 📋 Plan d'action

1. ✅ Ajouter `SIMPLIFICATION_FRACTIONS_V2` dans `getDynamicTemplates()`
2. ✅ Initialiser les variants A/B/C avec les bons templates lors de la sélection du générateur
3. ✅ Initialiser les variants A/B/C lors du chargement depuis l'API (si premium et variants vides)
4. ✅ Mettre à jour `onTemplatesLoaded` pour initialiser les variants premium
5. ⚠️ Vérifier que le backend sauvegarde bien `template_variants` (à vérifier côté backend)

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Root cause identifiée, corrections à appliquer


