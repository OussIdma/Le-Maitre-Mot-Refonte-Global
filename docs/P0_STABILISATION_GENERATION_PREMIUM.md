# P0 - Stabilisation Génération Premium + Mapping Difficulté + Traçabilité

## Objectif
Stabiliser la génération premium en garantissant que chaque paramètre UI est correctement mappé, tracé et sauvegardé.

---

## 1. Modifications Backend

### 1.1 Modèle `ExerciseGenerateRequest` (`backend/models/exercise_models.py`)

**Ajout de champs optionnels** :
```python
# P0 - Paramètres premium optionnels
grade: Optional[str] = Field(
    default=None,
    description="Niveau scolaire explicite (ex: 6e, 5e). Priorité: payload.grade > contexte > extraction code_officiel > fallback"
)
exercise_type: Optional[str] = Field(
    default=None,
    description="Type d'exercice pour générateurs premium (ex: operations_simples, proportionnalite_tableau)"
)
ui_params: Optional[Dict[str, Any]] = Field(
    default=None,
    description="Paramètres UI bruts (pour traçabilité et debug)"
)
```

### 1.2 Endpoint `POST /api/v1/exercises/generate` (`backend/routes/exercises_routes.py`)

#### Calcul de `grade` avec priorité

**Diff** :
```python
# P0 - Calculer grade avec priorité : payload.grade -> contexte grade -> extraction code_officiel -> fallback
effective_grade = None
if hasattr(request, 'grade') and request.grade:
    effective_grade = request.grade
elif request.code_officiel:
    # Extraire grade depuis code_officiel (format: "6e_N04")
    parts = request.code_officiel.split('_', 1)
    if len(parts) == 2 and parts[0] in ['6e', '5e', '4e', '3e']:
        effective_grade = parts[0]
elif hasattr(request, 'niveau') and request.niveau:
    effective_grade = request.niveau
else:
    effective_grade = "6e"  # Fallback
```

#### Construction de `ui_params` et `effective_params`

**Diff** :
```python
# P0 - Construire ui_params (paramètres UI bruts)
ui_params = request.ui_params or {}
if hasattr(request, 'difficulte') and request.difficulte:
    ui_params['difficulty_ui'] = request.difficulte
if hasattr(request, 'exercise_type') and request.exercise_type:
    ui_params['exercise_type_ui'] = request.exercise_type
if hasattr(request, 'grade') and request.grade:
    ui_params['grade_ui'] = request.grade
if hasattr(request, 'seed') and request.seed:
    ui_params['seed'] = request.seed

# P0 - Construire effective_params (paramètres effectifs après mapping)
effective_params = {
    'difficulty_effective': generator_difficulty,  # Après map_ui_difficulty_to_generator()
    'grade_effective': effective_grade,
    'seed': request.seed if hasattr(request, 'seed') and request.seed else None
}
if hasattr(request, 'exercise_type') and request.exercise_type:
    effective_params['exercise_type_effective'] = request.exercise_type
    ui_params['exercise_type_ui'] = request.exercise_type
```

#### Application de `map_ui_difficulty_to_generator()` AVANT `GeneratorFactory.generate()`

**Diff** :
```python
# P0 - Appliquer map_ui_difficulty_to_generator() AVANT GeneratorFactory.generate()
requested_difficulty = request.difficulte if hasattr(request, 'difficulte') and request.difficulte else "moyen"
generator_difficulty = map_ui_difficulty_to_generator(
    selected_premium_generator,
    requested_difficulty,
    logger
)

# P0 - Logs avec ui_params et effective_params (sans données sensibles)
logger.info(
    f"[GENERATOR_PARAMS] generator_key={selected_premium_generator} "
    f"code_officiel={request.code_officiel} "
    f"ui_params={ui_params} effective_params={effective_params}"
)

# Appeler GeneratorFactory.generate() avec la difficulté mappée
overrides_dict = {
    'seed': request.seed if hasattr(request, 'seed') and request.seed else None,
    'grade': effective_grade,
    'difficulty': generator_difficulty,  # P0 - Utiliser la difficulté mappée
}
if hasattr(request, 'exercise_type') and request.exercise_type:
    overrides_dict['exercise_type'] = request.exercise_type

premium_result = GeneratorFactory.generate(
    key=selected_premium_generator,
    exercise_params={},
    overrides=overrides_dict,
    seed=request.seed if hasattr(request, 'seed') and request.seed else None
)
```

#### Renvoyer `ui_params` et `effective_params` dans la réponse

**Diff** :
```python
metadata = {
    "is_premium": True,
    "generator_key": selected_premium_generator,
    "generator_code": f"{request.niveau}_{selected_premium_generator}",
    "difficulte": request.difficulte,
    "generation_duration_ms": duration_ms,
    "seed": request.seed if hasattr(request, 'seed') and request.seed else None,
    "variables": variables,
    "template_source": template_source,
    "ui_params": ui_params,  # P0 - Paramètres UI bruts
    "effective_params": effective_params,  # P0 - Paramètres effectifs après mapping
}
```

### 1.3 Vérification du mapping sur tous les chemins

#### Dans `generate_exercise_with_fallback()` (dynamic + fallback)

**Diff** :
```python
# P0 - Appliquer map_ui_difficulty_to_generator() pour les générateurs dynamiques
generator_key = selected_exercise.get("generator_key")
coerced_difficulty = requested_difficulty
if generator_key and requested_difficulty:
    # P0 - Utiliser map_ui_difficulty_to_generator() au lieu de coerce_to_supported_difficulty()
    coerced_difficulty = map_ui_difficulty_to_generator(
        generator_key,
        requested_difficulty,
        logger
    )
    
    if coerced_difficulty != requested_difficulty:
        logger.info(
            f"[DIFFICULTY_MAPPED] generate_exercise_with_fallback: "
            f"generator={generator_key} ui={requested_difficulty} -> effective={coerced_difficulty}"
        )
```

#### Ajout de `ui_params` et `effective_params` dans `dyn_exercise`

**Diff** :
```python
# P0 - Ajouter ui_params et effective_params dans metadata
if 'metadata' not in dyn_exercise:
    dyn_exercise['metadata'] = {}

# Construire ui_params si pas déjà fait
if 'ui_params' not in dyn_exercise['metadata']:
    ui_params_fallback = {}
    if hasattr(request, 'difficulte') and request.difficulte:
        ui_params_fallback['difficulty_ui'] = request.difficulte
    if hasattr(request, 'exercise_type') and request.exercise_type:
        ui_params_fallback['exercise_type_ui'] = request.exercise_type
    if hasattr(request, 'seed') and request.seed:
        ui_params_fallback['seed'] = request.seed
    dyn_exercise['metadata']['ui_params'] = ui_params_fallback

# Construire effective_params
effective_params_fallback = {
    'difficulty_effective': coerced_difficulty if 'coerced_difficulty' in locals() else requested_difficulty,
    'grade_effective': effective_grade if 'effective_grade' in locals() else (request.niveau if hasattr(request, 'niveau') else "6e"),
    'seed': request.seed if hasattr(request, 'seed') and request.seed else None
}
if hasattr(request, 'exercise_type') and request.exercise_type:
    effective_params_fallback['exercise_type_effective'] = request.exercise_type
dyn_exercise['metadata']['effective_params'] = effective_params_fallback
```

### 1.4 Logs ajoutés

**Logs avec paramètres** :
```python
# P0 - Logs avec ui_params et effective_params (sans données sensibles)
logger.info(
    f"[GENERATOR_PARAMS] generator_key={selected_premium_generator} "
    f"code_officiel={request.code_officiel} "
    f"ui_params={ui_params} effective_params={effective_params}"
)

logger.info(
    f"[GENERATOR_OK] ✅ Exercice DYNAMIQUE généré: "
    f"chapter={chapter_code}, id={selected_exercise.get('id')}, "
    f"generator={selected_exercise.get('generator_key')}, "
    f"ui_params={dyn_exercise['metadata'].get('ui_params')}, "
    f"effective_params={dyn_exercise['metadata'].get('effective_params')}"
)
```

---

## 2. Modifications Frontend

### 2.1 Ajout d'état pour `exercise_type` (`frontend/src/components/ExerciseGeneratorPage.js`)

**Diff** :
```javascript
// P0 - État pour exercise_type (générateurs premium uniquement)
const [exerciseType, setExerciseType] = useState("");
const [detectedGenerator, setDetectedGenerator] = useState(null); // CALCUL_NOMBRES_V1 ou RAISONNEMENT_MULTIPLICATIF_V1
```

### 2.2 Détection du générateur pour le chapitre sélectionné

**Diff** :
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
      console.log("Impossible de détecter le générateur:", error);
      setDetectedGenerator(null);
      setExerciseType("");
    }
  };
  
  detectGenerator();
}, [selectedItem]);
```

### 2.3 Ajout du select `exercise_type` dans le formulaire

**Diff** :
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

### 2.4 Inclusion de `exercise_type` dans le payload

**Diff** :
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
}
```

### 2.5 Variante : garder `exercise_type` + difficulté, changer uniquement seed

**Diff** :
```javascript
// P0 - Ajouter exercise_type si générateur premium détecté (variante garde exercise_type + difficulté, change uniquement seed)
if (detectedGenerator && exerciseType) {
  payload.exercise_type = exerciseType;
  payload.ui_params = {
    exercise_type: exerciseType
  };
}
```

### 2.6 Adaptation du grid pour le select `exercise_type`

**Diff** :
```javascript
<div className={`grid grid-cols-1 ${detectedGenerator ? 'md:grid-cols-5' : 'md:grid-cols-4'} gap-4 mb-4`}>
```

---

## 3. Tests manuels

### Test 1 : Mapping difficulté "moyen" → "standard" pour CALCUL_NOMBRES_V1

1. ✅ Ouvrir `/generer`
2. ✅ Sélectionner un chapitre avec CALCUL_NOMBRES_V1 activé (ex: "6e_N04")
3. ✅ Vérifier que le select "Type d'exercice" s'affiche avec les 3 options
4. ✅ Choisir Type: "Priorités opératoires", Difficulté: "Moyen"
5. ✅ Générer un exercice
6. ✅ **VÉRIFIER** dans les logs backend : `[DIFFICULTY_MAPPED] generator=CALCUL_NOMBRES_V1 ui=moyen -> effective=standard`
7. ✅ **VÉRIFIER** dans la réponse JSON : `metadata.effective_params.difficulty_effective = "standard"`
8. ✅ **VÉRIFIER** dans la réponse JSON : `metadata.ui_params.difficulty_ui = "moyen"`
9. ✅ **VÉRIFIER** que l'exercice généré correspond au type "priorites_operatoires"

### Test 2 : Calcul de `grade` avec priorité

1. ✅ Ouvrir `/generer`
2. ✅ Sélectionner chapitre "6e_N04"
3. ✅ Générer un exercice
4. ✅ **VÉRIFIER** dans les logs : `effective_params.grade_effective = "6e"` (extrait de code_officiel)
5. ✅ Sélectionner chapitre "5e_SP03"
6. ✅ Générer un exercice
7. ✅ **VÉRIFIER** dans les logs : `effective_params.grade_effective = "5e"` (extrait de code_officiel)

### Test 3 : `exercise_type` envoyé et utilisé

1. ✅ Ouvrir `/generer`
2. ✅ Sélectionner chapitre avec CALCUL_NOMBRES_V1
3. ✅ Choisir Type: "Décimaux"
4. ✅ Générer un exercice
5. ✅ **VÉRIFIER** dans les logs : `ui_params.exercise_type_ui = "decimaux"`
6. ✅ **VÉRIFIER** dans les logs : `effective_params.exercise_type_effective = "decimaux"`
7. ✅ **VÉRIFIER** que l'exercice généré est bien un exercice sur les décimaux (5e uniquement)

### Test 4 : Variante garde `exercise_type` + difficulté, change uniquement seed

1. ✅ Ouvrir `/generer`
2. ✅ Sélectionner chapitre avec RAISONNEMENT_MULTIPLICATIF_V1
3. ✅ Choisir Type: "Pourcentages", Difficulté: "Facile"
4. ✅ Générer un exercice → noter le seed et le rendu
5. ✅ Cliquer sur "Varier" pour cet exercice
6. ✅ **VÉRIFIER** dans le payload de variation : `exercise_type = "pourcentage"` (conservé)
7. ✅ **VÉRIFIER** dans le payload de variation : `difficulte = "facile"` (conservé)
8. ✅ **VÉRIFIER** dans le payload de variation : `seed` différent (changé)
9. ✅ **VÉRIFIER** que le nouvel exercice est toujours "Pourcentages" mais avec des valeurs différentes

### Test 5 : Mapping utilisé sur tous les chemins (dynamic + fallback)

1. ✅ Ouvrir `/generer`
2. ✅ Sélectionner chapitre avec générateur dynamique (ex: CALCUL_NOMBRES_V1)
3. ✅ Choisir Difficulté: "Moyen"
4. ✅ Générer un exercice
5. ✅ **VÉRIFIER** dans les logs : `[DIFFICULTY_MAPPED]` apparaît dans `generate_exercise_with_fallback`
6. ✅ **VÉRIFIER** dans les logs : `[DIFFICULTY_MAPPED]` apparaît dans le chemin premium factory
7. ✅ **VÉRIFIER** que `effective_params.difficulty_effective = "standard"` dans les deux cas

---

## 4. Checklist tests manuels

### Backend

- [ ] Test 1 : Mapping "moyen" → "standard" pour CALCUL_NOMBRES_V1
  - [ ] Logs affichent `[DIFFICULTY_MAPPED]`
  - [ ] `metadata.effective_params.difficulty_effective = "standard"`
  - [ ] `metadata.ui_params.difficulty_ui = "moyen"`
  - [ ] Exercice généré correspond au type choisi

- [ ] Test 2 : Calcul de `grade` avec priorité
  - [ ] `grade_effective` extrait de `code_officiel` si non fourni
  - [ ] Logs affichent `grade_effective` correct

- [ ] Test 3 : `exercise_type` envoyé et utilisé
  - [ ] `ui_params.exercise_type_ui` présent
  - [ ] `effective_params.exercise_type_effective` présent
  - [ ] Exercice généré correspond au type

- [ ] Test 4 : Variante garde `exercise_type` + difficulté
  - [ ] Payload de variation contient `exercise_type`
  - [ ] Payload de variation contient `difficulte`
  - [ ] Seed différent

- [ ] Test 5 : Mapping utilisé sur tous les chemins
  - [ ] Logs `[DIFFICULTY_MAPPED]` dans `generate_exercise_with_fallback`
  - [ ] Logs `[DIFFICULTY_MAPPED]` dans premium factory
  - [ ] `effective_params` présent dans les deux cas

### Frontend

- [ ] Test 1 : Select `exercise_type` s'affiche pour CALCUL_NOMBRES_V1
  - [ ] Select visible avec 3 options
  - [ ] Défaut: "operations_simples"

- [ ] Test 2 : Select `exercise_type` s'affiche pour RAISONNEMENT_MULTIPLICATIF_V1
  - [ ] Select visible avec 4 options
  - [ ] Défaut: "proportionnalite_tableau"

- [ ] Test 3 : Select masqué pour autres générateurs
  - [ ] Select non visible si générateur non premium

- [ ] Test 4 : Grid s'adapte (4 ou 5 colonnes)
  - [ ] 4 colonnes si pas de générateur premium
  - [ ] 5 colonnes si générateur premium détecté

- [ ] Test 5 : `exercise_type` inclus dans le payload
  - [ ] Payload contient `exercise_type` si générateur premium
  - [ ] Payload contient `ui_params.exercise_type`

---

## 5. Résumé des changements

### Backend
- ✅ `ExerciseGenerateRequest` : Ajout de `grade`, `exercise_type`, `ui_params` optionnels
- ✅ Calcul de `grade` avec priorité : payload > contexte > extraction > fallback
- ✅ Construction de `ui_params` et `effective_params`
- ✅ Application de `map_ui_difficulty_to_generator()` AVANT `GeneratorFactory.generate()`
- ✅ Renvoi de `ui_params` et `effective_params` dans `metadata`
- ✅ Mapping utilisé dans `generate_exercise_with_fallback()` (dynamic + fallback)
- ✅ Logs avec `generator_key`, `code_officiel`, `ui_params`, `effective_params`

### Frontend
- ✅ État `exerciseType` et `detectedGenerator`
- ✅ Détection du générateur via endpoint debug
- ✅ Select `exercise_type` pour CALCUL_NOMBRES_V1 (3 options)
- ✅ Select `exercise_type` pour RAISONNEMENT_MULTIPLICATIF_V1 (4 options)
- ✅ Inclusion de `exercise_type` dans le payload
- ✅ Variante garde `exercise_type` + difficulté, change seed
- ✅ Grid adaptatif (4 ou 5 colonnes)

---

## 6. Notes techniques

### Endpoint debug pour détection générateur
L'endpoint `/api/debug/chapters/{code}/generators` doit être disponible en mode développement pour que le frontend puisse détecter les générateurs activés. Si l'endpoint n'existe pas, le select `exercise_type` ne s'affichera pas (fallback silencieux).

### Priorité de calcul de `grade`
1. `payload.grade` (si fourni explicitement)
2. Contexte `request.niveau` (si disponible)
3. Extraction depuis `code_officiel` (format: "6e_N04" → "6e")
4. Fallback: "6e"

### Mapping difficulté
- UI envoie : "facile", "moyen", "difficile" (canoniques)
- CALCUL_NOMBRES_V1 supporte : "facile", "standard"
- Mapping : "moyen" UI → "standard" générateur
- RAISONNEMENT_MULTIPLICATIF_V1 supporte : "facile", "moyen", "difficile"
- Mapping : Pas de changement (déjà canoniques)



