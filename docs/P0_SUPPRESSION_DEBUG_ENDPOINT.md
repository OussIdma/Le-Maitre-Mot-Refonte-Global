# P0 — Suppression de la dépendance au debug endpoint

## Contexte

`ExerciseGeneratorPage.js` détectait le générateur premium via un appel à :
```
GET /api/debug/chapters/{code}/generators
```

**Problème** : Cet endpoint est interdit en production (non fiable + surface debug).

## Objectif

Afficher le select "Type d'exercice" pour :
- `CALCUL_NOMBRES_V1`
- `RAISONNEMENT_MULTIPLICATIF_V1`

**sans AUCUN endpoint `/api/debug`**.

## Solution : OPTION A (via le catalogue)

Le catalogue déjà chargé (`/api/v1/curriculum/{grade}/catalog`) contient pour chaque chapitre :
```json
{
  "domains": [
    {
      "name": "Nombres et calculs",
      "chapters": [
        {
          "code_officiel": "6e_N04",
          "libelle": "Calculs numériques",
          "generators": ["CALCUL_NOMBRES_V1", "THALES_V2", ...]
        }
      ]
    }
  ]
}
```

**Détection** : Chercher dans `catalog.domains[].chapters[]` le chapitre avec `code_officiel === selectedItem`, puis vérifier si `generators` contient `CALCUL_NOMBRES_V1` ou `RAISONNEMENT_MULTIPLICATIF_V1`.

---

## Diff complet

### Fichier : `frontend/src/components/ExerciseGeneratorPage.js`

#### Suppression (lignes ~322-361)

**AVANT** :
```javascript
// P0 - Détecter le générateur pour le chapitre sélectionné
useEffect(() => {
  const detectGenerator = async () => {
    if (!selectedItem || selectedItem.startsWith("macro:")) {
      setDetectedGenerator(null);
      setExerciseType("");
      return;
    }
    
    try {
      // Appeler l'API debug pour obtenir les générateurs activés pour ce chapitre
      const response = await axios.get(`${BACKEND_URL}/api/debug/chapters/${selectedItem}/generators`);
      const enabledGenerators = response.data.enabled_generators_in_db || [];
      
      // Vérifier si CALCUL_NOMBRES_V1 ou RAISONNEMENT_MULTIPLICATIF_V1 est activé
      const calculNombres = enabledGenerators.find(g => g.generator_key === "CALCUL_NOMBRES_V1" && g.is_enabled);
      const raisonnementMulti = enabledGenerators.find(g => g.generator_key === "RAISONNEMENT_MULTIPLICATIF_V1" && g.is_enabled);
      
      if (calculNombres) {
        setDetectedGenerator("CALCUL_NOMBRES_V1");
        setExerciseType(prev => prev || "operations_simples");
      } else if (raisonnementMulti) {
        setDetectedGenerator("RAISONNEMENT_MULTIPLICATIF_V1");
        setExerciseType(prev => prev || "proportionnalite_tableau");
      } else {
        setDetectedGenerator(null);
        setExerciseType("");
      }
    } catch (error) {
      console.log("Impossible de détecter le générateur (endpoint debug peut être indisponible):", error);
      setDetectedGenerator(null);
      setExerciseType("");
    }
  };
  
  detectGenerator();
}, [selectedItem]);
```

#### Remplacement (lignes ~322-361)

**APRÈS** :
```javascript
// P0 - Détecter le générateur pour le chapitre sélectionné via le catalogue (sans endpoint debug)
useEffect(() => {
  // Si pas de chapitre sélectionné ou mode macro, masquer le select
  if (!selectedItem || selectedItem.startsWith("macro:")) {
    setDetectedGenerator(null);
    setExerciseType("");
    return;
  }
  
  // Si le catalogue n'est pas encore chargé, attendre
  if (!catalog || !catalog.domains) {
    setDetectedGenerator(null);
    setExerciseType("");
    return;
  }
  
  // Chercher le chapitre dans le catalogue
  let foundChapter = null;
  for (const domain of catalog.domains) {
    foundChapter = domain.chapters?.find(ch => ch.code_officiel === selectedItem);
    if (foundChapter) break;
  }
  
  // Si le chapitre n'est pas trouvé, masquer le select
  if (!foundChapter || !foundChapter.generators || !Array.isArray(foundChapter.generators)) {
    setDetectedGenerator(null);
    setExerciseType("");
    return;
  }
  
  // Vérifier si CALCUL_NOMBRES_V1 ou RAISONNEMENT_MULTIPLICATIF_V1 est présent dans les générateurs
  const generators = foundChapter.generators;
  const hasCalculNombres = generators.includes("CALCUL_NOMBRES_V1");
  const hasRaisonnementMulti = generators.includes("RAISONNEMENT_MULTIPLICATIF_V1");
  
  if (hasCalculNombres) {
    setDetectedGenerator("CALCUL_NOMBRES_V1");
    // Défaut: operations_simples (seulement si pas déjà défini)
    setExerciseType(prev => prev || "operations_simples");
  } else if (hasRaisonnementMulti) {
    setDetectedGenerator("RAISONNEMENT_MULTIPLICATIF_V1");
    // Défaut: proportionnalite_tableau (seulement si pas déjà défini)
    setExerciseType(prev => prev || "proportionnalite_tableau");
  } else {
    setDetectedGenerator(null);
    setExerciseType("");
  }
}, [selectedItem, catalog]);
```

### Changements clés

1. ✅ **Suppression complète** de l'appel à `/api/debug/chapters/{code}/generators`
2. ✅ **Suppression** de `try/catch` et gestion d'erreur liée à l'endpoint debug
3. ✅ **Utilisation du catalogue** déjà chargé (`catalog` dans les dépendances du `useEffect`)
4. ✅ **Recherche synchrone** dans `catalog.domains[].chapters[]`
5. ✅ **Vérification** si `generators` contient `CALCUL_NOMBRES_V1` ou `RAISONNEMENT_MULTIPLICATIF_V1`
6. ✅ **Gestion des cas limites** : catalogue non chargé, chapitre non trouvé, `generators` manquant

---

## Checklist Tests Manuels

### Test 1 : Changement de chapitre => detectedGenerator mis à jour (sans debug call)

- [ ] Ouvrir `/generer`
- [ ] Ouvrir DevTools → Network
- [ ] Sélectionner chapitre avec CALCUL_NOMBRES_V1 (ex: "6e_N04")
- [ ] **VÉRIFIER** : Aucun appel à `/api/debug/chapters/...` dans Network
- [ ] **VÉRIFIER** : Select "Type d'exercice" apparaît avec défaut "Opérations simples"
- [ ] **VÉRIFIER** : `detectedGenerator = "CALCUL_NOMBRES_V1"` (via console ou React DevTools)
- [ ] Changer pour chapitre avec RAISONNEMENT_MULTIPLICATIF_V1
- [ ] **VÉRIFIER** : Aucun appel à `/api/debug/chapters/...` dans Network
- [ ] **VÉRIFIER** : Select change avec défaut "Proportionnalité (tableau)"
- [ ] **VÉRIFIER** : `detectedGenerator = "RAISONNEMENT_MULTIPLICATIF_V1"`
- [ ] Changer pour chapitre sans générateur premium
- [ ] **VÉRIFIER** : Select disparaît
- [ ] **VÉRIFIER** : `detectedGenerator = null`

### Test 2 : Select visible pour les chapitres premium concernés

- [ ] Ouvrir `/generer`
- [ ] Sélectionner chapitre avec CALCUL_NOMBRES_V1
- [ ] **VÉRIFIER** : Select "Type d'exercice" visible
- [ ] **VÉRIFIER** : Select contient 3 options (Opérations simples, Priorités opératoires, Décimaux)
- [ ] **VÉRIFIER** : Grid passe à 5 colonnes
- [ ] Sélectionner chapitre avec RAISONNEMENT_MULTIPLICATIF_V1
- [ ] **VÉRIFIER** : Select "Type d'exercice" visible
- [ ] **VÉRIFIER** : Select contient 4 options (Proportionnalité, Pourcentages, Vitesse, Échelle)
- [ ] **VÉRIFIER** : Grid passe à 5 colonnes

### Test 3 : Select masqué pour les autres chapitres

- [ ] Ouvrir `/generer`
- [ ] Sélectionner chapitre SANS générateur premium (ex: chapitre avec THALES_V2 uniquement)
- [ ] **VÉRIFIER** : Select "Type d'exercice" n'est PAS affiché
- [ ] **VÉRIFIER** : Grid reste à 4 colonnes
- [ ] Sélectionner mode "macro:" (groupe macro)
- [ ] **VÉRIFIER** : Select "Type d'exercice" n'est PAS affiché
- [ ] **VÉRIFIER** : Grid reste à 4 colonnes

### Test 4 : Aucune erreur console si données manquantes

- [ ] Ouvrir `/generer`
- [ ] Ouvrir DevTools → Console
- [ ] Sélectionner chapitre normal
- [ ] **VÉRIFIER** : Aucune erreur dans la console
- [ ] Sélectionner chapitre avec `generators` vide `[]`
- [ ] **VÉRIFIER** : Aucune erreur dans la console
- [ ] **VÉRIFIER** : Select masqué (comportement attendu)
- [ ] Sélectionner chapitre avec `generators` manquant (undefined)
- [ ] **VÉRIFIER** : Aucune erreur dans la console
- [ ] **VÉRIFIER** : Select masqué (comportement attendu)
- [ ] Changer de niveau (ex: 6e → 5e) pendant que le catalogue se charge
- [ ] **VÉRIFIER** : Aucune erreur dans la console
- [ ] **VÉRIFIER** : Select masqué jusqu'à ce que le catalogue soit chargé

### Test 5 : Détection après chargement du catalogue

- [ ] Ouvrir `/generer` (page fraîche)
- [ ] **VÉRIFIER** : Select "Type d'exercice" masqué (catalogue pas encore chargé)
- [ ] Attendre le chargement du catalogue
- [ ] Sélectionner chapitre avec CALCUL_NOMBRES_V1
- [ ] **VÉRIFIER** : Select apparaît immédiatement
- [ ] Recharger la page
- [ ] Sélectionner chapitre avec CALCUL_NOMBRES_V1 AVANT que le catalogue soit chargé
- [ ] **VÉRIFIER** : Select masqué
- [ ] Attendre le chargement du catalogue
- [ ] **VÉRIFIER** : Select apparaît automatiquement (useEffect se déclenche)

### Test 6 : Variante conserve exercise_type + difficulté, change seed

- [ ] Ouvrir `/generer`
- [ ] Sélectionner chapitre avec RAISONNEMENT_MULTIPLICATIF_V1
- [ ] Choisir Type: "Pourcentages", Difficulté: "Facile"
- [ ] Générer un exercice → noter le seed et le rendu
- [ ] Cliquer sur "Varier" pour cet exercice
- [ ] Ouvrir DevTools → Network → Requête POST `/api/v1/exercises/generate`
- [ ] **VÉRIFIER** dans le payload de variation :
  ```json
  {
    "code_officiel": "...",
    "difficulte": "facile",  // ✅ Conservé
    "seed": 789012,  // ✅ Différent
    "exercise_type": "pourcentage",  // ✅ Conservé
    "ui_params": {
      "exercise_type": "pourcentage"  // ✅ Conservé
    }
  }
  ```
- [ ] **VÉRIFIER** : Le nouvel exercice est toujours "Pourcentages" mais avec des valeurs différentes

---

## Points d'attention

### 1. Dépendances du useEffect

Le `useEffect` dépend maintenant de `[selectedItem, catalog]` au lieu de `[selectedItem]` uniquement. Cela garantit que :
- La détection se déclenche quand le catalogue est chargé
- La détection se met à jour si le catalogue change (changement de niveau)

### 2. Gestion des cas limites

- **Catalogue non chargé** : Select masqué (pas d'erreur)
- **Chapitre non trouvé** : Select masqué (pas d'erreur)
- **`generators` manquant ou vide** : Select masqué (pas d'erreur)
- **Mode macro** : Select masqué (comportement attendu)

### 3. Performance

- **Recherche synchrone** : Pas d'appel réseau, recherche directe dans le catalogue en mémoire
- **Pas de re-render inutile** : Le `useEffect` ne se déclenche que si `selectedItem` ou `catalog` change

### 4. Compatibilité

- **Structure du catalogue** : Supposons que `catalog.domains[].chapters[]` contient `generators` (array de strings)
- **Si la structure change** : Le code gère gracieusement (`foundChapter.generators` peut être undefined)

---

## Résumé des modifications

### Fichier modifié
- ✅ `frontend/src/components/ExerciseGeneratorPage.js`

### Supprimé
- ❌ Appel à `/api/debug/chapters/{code}/generators`
- ❌ `try/catch` et gestion d'erreur liée à l'endpoint debug
- ❌ Logique asynchrone pour la détection

### Ajouté
- ✅ Détection synchrone via le catalogue déjà chargé
- ✅ Recherche dans `catalog.domains[].chapters[]`
- ✅ Vérification de présence dans `generators` array
- ✅ Gestion robuste des cas limites

### Non modifié
- ✅ Select conditionnel (déjà présent)
- ✅ Grid adaptatif (déjà présent)
- ✅ Inclusion de `exercise_type` dans payload (déjà présent)
- ✅ Variante conserve `exercise_type` + difficulté (déjà présent)

---

## Statut

- ✅ Code modifié
- ✅ Linters OK
- ⏳ Tests manuels : À effectuer

**Prêt pour les tests !** 🎉



