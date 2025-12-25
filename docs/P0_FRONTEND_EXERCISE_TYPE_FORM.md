# P0 Frontend — Mini-form exercise_type pour générateurs premium

## Objectif
Ajouter un select "Type d'exercice" uniquement pour les 2 générateurs premium (CALCUL_NOMBRES_V1 et RAISONNEMENT_MULTIPLICATIF_V1) dans `ExerciseGeneratorPage.js`.

---

## 1. Diff Frontend

### 1.1 Ajout des états (`frontend/src/components/ExerciseGeneratorPage.js`)

**Ligne ~150** :
```javascript
// P0 - État pour exercise_type (générateurs premium uniquement)
const [exerciseType, setExerciseType] = useState("");
const [detectedGenerator, setDetectedGenerator] = useState(null); // CALCUL_NOMBRES_V1 ou RAISONNEMENT_MULTIPLICATIF_V1
```

### 1.2 Détection automatique du générateur

**Ligne ~350** (après `fetchCatalog`) :
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
        // Défaut: operations_simples (seulement si pas déjà défini)
        setExerciseType(prev => prev || "operations_simples");
      } else if (raisonnementMulti) {
        setDetectedGenerator("RAISONNEMENT_MULTIPLICATIF_V1");
        // Défaut: proportionnalite_tableau (seulement si pas déjà défini)
        setExerciseType(prev => prev || "proportionnalite_tableau");
      } else {
        setDetectedGenerator(null);
        setExerciseType("");
      }
    } catch (error) {
      // Si l'endpoint debug n'existe pas ou erreur, ne pas bloquer
      console.log("Impossible de détecter le générateur (endpoint debug peut être indisponible):", error);
      setDetectedGenerator(null);
      setExerciseType("");
    }
  };
  
  detectGenerator();
}, [selectedItem]);
```

### 1.3 Ajout du select dans le formulaire

**Ligne ~1158** (après le select "Difficulté") :
```javascript
{/* P0 - Type d'exercice (générateurs premium uniquement) */}
{detectedGenerator === "CALCUL_NOMBRES_V1" && (
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-2">
      Type d&apos;exercice
    </label>
    <Select value={exerciseType} onValueChange={setExerciseType}>
      <SelectTrigger>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="operations_simples">Opérations simples</SelectItem>
        <SelectItem value="priorites_operatoires">Priorités opératoires</SelectItem>
        <SelectItem value="decimaux">Décimaux</SelectItem>
      </SelectContent>
    </Select>
  </div>
)}

{detectedGenerator === "RAISONNEMENT_MULTIPLICATIF_V1" && (
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-2">
      Type d&apos;exercice
    </label>
    <Select value={exerciseType} onValueChange={setExerciseType}>
      <SelectTrigger>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="proportionnalite_tableau">Proportionnalité (tableau)</SelectItem>
        <SelectItem value="pourcentage">Pourcentages</SelectItem>
        <SelectItem value="vitesse">Vitesse</SelectItem>
        <SelectItem value="echelle">Échelle</SelectItem>
      </SelectContent>
    </Select>
  </div>
)}
```

### 1.4 Adaptation du grid (4 ou 5 colonnes)

**Ligne ~1084** :
```javascript
<div className={`grid grid-cols-1 ${detectedGenerator ? 'md:grid-cols-5' : 'md:grid-cols-4'} gap-4 mb-4`}>
```

### 1.5 Inclusion de `exercise_type` dans le payload de génération

**Ligne ~583** (dans `generateExercises`) :
```javascript
// Construire le payload avec offer: "pro" si utilisateur PRO
const payload = {
  code_officiel: codeOfficiel,
  difficulte: difficulte,
  seed: seed
};

// P0 - Ajouter exercise_type si générateur premium détecté
if (detectedGenerator && exerciseType) {
  payload.exercise_type = exerciseType;
  payload.ui_params = {
    exercise_type: exerciseType
  };
}

// Ajouter offer: "pro" pour les utilisateurs PRO
if (isPro) {
  payload.offer = "pro";
  console.log(`🌟 Mode PRO activé pour ${codeOfficiel}`);
}
```

### 1.6 Variante : garde `exercise_type` + difficulté, change uniquement seed

**Ligne ~898** (dans `handleVariation`) :
```javascript
// Construire le payload
const payload = {
  code_officiel: codeOfficiel,
  difficulte: difficulte,
  seed: seed
};

// P0 - Ajouter exercise_type si générateur premium détecté (variante garde exercise_type + difficulté, change uniquement seed)
if (detectedGenerator && exerciseType) {
  payload.exercise_type = exerciseType;
  payload.ui_params = {
    exercise_type: exerciseType
  };
}
```

---

## 2. Checklist Tests Manuels

### Test 1 : Affichage du select pour CALCUL_NOMBRES_V1

- [ ] **Prérequis** : Chapitre avec CALCUL_NOMBRES_V1 activé (ex: "6e_N04")
- [ ] Ouvrir `/generer`
- [ ] Sélectionner le chapitre avec CALCUL_NOMBRES_V1
- [ ] **VÉRIFIER** : Le select "Type d'exercice" s'affiche
- [ ] **VÉRIFIER** : Le select contient 3 options :
  - [ ] "Opérations simples" (valeur: `operations_simples`)
  - [ ] "Priorités opératoires" (valeur: `priorites_operatoires`)
  - [ ] "Décimaux" (valeur: `decimaux`)
- [ ] **VÉRIFIER** : La valeur par défaut est "Opérations simples"
- [ ] **VÉRIFIER** : Le grid passe à 5 colonnes (au lieu de 4)

### Test 2 : Affichage du select pour RAISONNEMENT_MULTIPLICATIF_V1

- [ ] **Prérequis** : Chapitre avec RAISONNEMENT_MULTIPLICATIF_V1 activé
- [ ] Ouvrir `/generer`
- [ ] Sélectionner le chapitre avec RAISONNEMENT_MULTIPLICATIF_V1
- [ ] **VÉRIFIER** : Le select "Type d'exercice" s'affiche
- [ ] **VÉRIFIER** : Le select contient 4 options :
  - [ ] "Proportionnalité (tableau)" (valeur: `proportionnalite_tableau`)
  - [ ] "Pourcentages" (valeur: `pourcentage`)
  - [ ] "Vitesse" (valeur: `vitesse`)
  - [ ] "Échelle" (valeur: `echelle`)
- [ ] **VÉRIFIER** : La valeur par défaut est "Proportionnalité (tableau)"
- [ ] **VÉRIFIER** : Le grid passe à 5 colonnes (au lieu de 4)

### Test 3 : Select masqué pour autres générateurs

- [ ] Ouvrir `/generer`
- [ ] Sélectionner un chapitre SANS générateur premium (ex: chapitre avec THALES_V2)
- [ ] **VÉRIFIER** : Le select "Type d'exercice" n'est PAS affiché
- [ ] **VÉRIFIER** : Le grid reste à 4 colonnes

### Test 4 : `exercise_type` inclus dans le payload POST

- [ ] Ouvrir `/generer`
- [ ] Sélectionner chapitre avec CALCUL_NOMBRES_V1
- [ ] Choisir Type: "Priorités opératoires"
- [ ] Générer un exercice
- [ ] Ouvrir DevTools → Network → Requête POST `/api/v1/exercises/generate`
- [ ] **VÉRIFIER** dans le payload :
  ```json
  {
    "code_officiel": "6e_N04",
    "difficulte": "moyen",
    "seed": 123456,
    "exercise_type": "priorites_operatoires",
    "ui_params": {
      "exercise_type": "priorites_operatoires"
    }
  }
  ```
- [ ] **VÉRIFIER** : Pas de champ "Niveau" dans le payload (seulement `code_officiel`)

### Test 5 : Variante garde `exercise_type` + difficulté, change seed

- [ ] Ouvrir `/generer`
- [ ] Sélectionner chapitre avec RAISONNEMENT_MULTIPLICATIF_V1
- [ ] Choisir Type: "Pourcentages", Difficulté: "Facile"
- [ ] Générer un exercice → noter le seed et le rendu
- [ ] Cliquer sur "Varier" (bouton RefreshCw) pour cet exercice
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

### Test 6 : Détection automatique au changement de chapitre

- [ ] Ouvrir `/generer`
- [ ] Sélectionner chapitre avec CALCUL_NOMBRES_V1
- [ ] **VÉRIFIER** : Select "Type d'exercice" apparaît avec défaut "operations_simples"
- [ ] Changer pour chapitre avec RAISONNEMENT_MULTIPLICATIF_V1
- [ ] **VÉRIFIER** : Select "Type d'exercice" change avec défaut "proportionnalite_tableau"
- [ ] Changer pour chapitre sans générateur premium
- [ ] **VÉRIFIER** : Select "Type d'exercice" disparaît

### Test 7 : Gestion d'erreur endpoint debug

- [ ] **Simuler** : Désactiver l'endpoint `/api/debug/chapters/{code}/generators` (ou erreur 404)
- [ ] Ouvrir `/generer`
- [ ] Sélectionner chapitre avec CALCUL_NOMBRES_V1
- [ ] **VÉRIFIER** : Pas d'erreur dans la console (fallback silencieux)
- [ ] **VÉRIFIER** : Select "Type d'exercice" ne s'affiche pas (comportement dégradé acceptable)

---

## 3. Points d'attention

### 3.1 Endpoint debug requis

L'endpoint `/api/debug/chapters/{code}/generators` doit être disponible pour que la détection fonctionne. Si l'endpoint n'existe pas ou retourne une erreur, le select ne s'affichera pas (fallback silencieux).

### 3.2 Pas de champ "Niveau"

Conformément à la demande, **aucun champ "Niveau" n'est ajouté**. Le niveau est déduit automatiquement depuis `code_officiel` (ex: "6e_N04" → niveau "6e").

### 3.3 Grid adaptatif

Le grid s'adapte automatiquement :
- **4 colonnes** : Domaine (si mode Standard) + Chapitre + Difficulté + Nombre d'exercices
- **5 colonnes** : Domaine (si mode Standard) + Chapitre + Difficulté + **Type d'exercice** + Nombre d'exercices

### 3.4 Valeurs par défaut

- **CALCUL_NOMBRES_V1** : `operations_simples`
- **RAISONNEMENT_MULTIPLICATIF_V1** : `proportionnalite_tableau`

Ces valeurs sont définies automatiquement lors de la détection du générateur, mais seulement si `exerciseType` n'est pas déjà défini (pour éviter d'écraser une sélection utilisateur).

---

## 4. Résumé des modifications

### Fichiers modifiés
- ✅ `frontend/src/components/ExerciseGeneratorPage.js`

### Ajouts
- ✅ État `exerciseType` et `detectedGenerator`
- ✅ `useEffect` pour détection automatique du générateur
- ✅ Select conditionnel pour CALCUL_NOMBRES_V1 (3 options)
- ✅ Select conditionnel pour RAISONNEMENT_MULTIPLICATIF_V1 (4 options)
- ✅ Inclusion de `exercise_type` dans payload de génération
- ✅ Inclusion de `exercise_type` dans payload de variation
- ✅ Grid adaptatif (4 ou 5 colonnes)

### Non ajouté (conformément à la demande)
- ❌ Champ "Niveau" (le niveau est déduit depuis `code_officiel`)



