# 🔍 INVESTIGATION ROOT CAUSE - "Thales en génération au lieu de Symétrie" / Mauvaise sélection de pool

## Symptôme
**Côté élève** : Création d'un exercice SYMETRIE en difficulté "difficile", mais la génération retourne un exercice THALES (mauvaise famille sélectionnée).

---

## 📍 CHAÎNE COMPLÈTE DE SÉLECTION

### 1. **ENTRÉE - Route API**

**Fichier** : `backend/routes/exercises_routes.py`
- **Ligne 551** : Endpoint `POST /api/v1/exercises/generate`
- **Ligne 744-792** : Résolution du mode (`code_officiel` vs legacy)
- **Ligne 746** : Appel à `get_chapter_by_official_code(request.code_officiel)`
- **Ligne 764-783** : Extraction des `exercise_types` depuis le curriculum
  ```python
  if curriculum_chapter.exercise_types:
      filtered_types = curriculum_chapter.exercise_types  # ou filtré selon offer
      exercise_types_override = [
          MathExerciseType[et] for et in filtered_types
          if hasattr(MathExerciseType, et)
      ]
  ```

**Résultat** : `exercise_types_override` contient la liste des types d'exercices autorisés pour le chapitre.

---

### 2. **RÉFÉRENTIEL CURRICULUM**

**Fichier** : `backend/curriculum/curriculum_6e.json`
- **Ligne 234-254** : Chapitre `6e_G07` (Symétrie axiale)
  ```json
  {
    "code_officiel": "6e_G07",
    "chapitre_backend": "Symétrie axiale",
    "exercise_types": [
      "SYMETRIE_AXIALE",
      "SYMETRIE_PROPRIETES"
    ]
  }
  ```

**Résultat** : Le chapitre `6e_G07` a **2 types d'exercices** : `SYMETRIE_AXIALE` et `SYMETRIE_PROPRIETES`.

---

### 3. **SÉLECTION ALÉATOIRE DU TYPE**

**Fichier** : `backend/routes/exercises_routes.py`
- **Ligne 881-889** : Si `exercise_types_override` existe, appel à `generate_math_exercise_specs_with_types()`
  ```python
  if exercise_types_override and len(exercise_types_override) > 0:
      specs = _math_service.generate_math_exercise_specs_with_types(
          niveau=request.niveau,
          chapitre=request.chapitre,
          difficulte=request.difficulte,
          exercise_types=exercise_types_override,  # [SYMETRIE_AXIALE, SYMETRIE_PROPRIETES]
          nb_exercices=1
      )
  ```

**Fichier** : `backend/services/math_generation_service.py`
- **Ligne 64-110** : Méthode `generate_math_exercise_specs_with_types()`
- **Ligne 97-100** : **PROBLÈME IDENTIFIÉ** - Sélection aléatoire :
  ```python
  specs = []
  for i in range(nb_exercices):
      # Choisir un type d'exercice parmi ceux spécifiés
      exercise_type = random.choice(exercise_types)  # ❌ ALÉATOIRE
      
      # Générer la spec selon le type
      spec = self._generate_spec_by_type(
          niveau, chapitre, exercise_type, difficulte
      )
  ```

**Résultat** : Le type d'exercice est sélectionné **aléatoirement** parmi `[SYMETRIE_AXIALE, SYMETRIE_PROPRIETES]`.

---

### 4. **GÉNÉRATION DE LA SPEC**

**Fichier** : `backend/services/math_generation_service.py`
- **Ligne 103-105** : Appel à `_generate_spec_by_type()`
- **Ligne 314-315** : Mapping des types vers les générateurs :
  ```python
  MathExerciseType.SYMETRIE_AXIALE: self._gen_symetrie_axiale,
  MathExerciseType.SYMETRIE_PROPRIETES: self._gen_symetrie_proprietes,
  ```

**Fichier** : `backend/services/math_generation_service.py`
- **Ligne 1772-2160** : Méthode `_gen_symetrie_axiale()`
- **Ligne 1784** : Types d'exercices internes :
  ```python
  types_exercices = ["trouver_symetrique", "verifier_symetrie", "completer_figure"]
  ```

**Résultat** : Si `SYMETRIE_AXIALE` est sélectionné, la génération fonctionne correctement.

---

## 🎯 ROOT CAUSE IDENTIFIÉE

### Scénario 1 : Sélection aléatoire normale
1. **Ligne 100** (`math_generation_service.py`) : `exercise_type = random.choice([SYMETRIE_AXIALE, SYMETRIE_PROPRIETES])`
2. Si `SYMETRIE_AXIALE` est sélectionné → génération OK ✅
3. Si `SYMETRIE_PROPRIETES` est sélectionné → génération OK ✅

### Scénario 2 : Problème de mapping ou fallback
1. **Ligne 100** (`math_generation_service.py`) : Sélection aléatoire parmi les types
2. **Ligne 103** (`math_generation_service.py`) : Appel à `_generate_spec_by_type()`
3. **Ligne 314** (`math_generation_service.py`) : Mapping vers `_gen_symetrie_axiale` ou `_gen_symetrie_proprietes`
4. **Si le générateur échoue ou retourne None** :
   - **Ligne 107-108** (`math_generation_service.py`) : `if spec: specs.append(spec)`
   - **Si `spec` est `None`, l'exercice n'est pas ajouté**
   - **Ligne 899** (`exercises_routes.py`) : `if not specs or len(specs) == 0: raise ValueError(...)`
   - **MAIS** : Il n'y a pas de fallback automatique vers un autre type

### Scénario 3 : Problème de conversion des types
1. **Ligne 780-783** (`exercises_routes.py`) : Conversion des types depuis le curriculum :
   ```python
   exercise_types_override = [
       MathExerciseType[et] for et in filtered_types
       if hasattr(MathExerciseType, et)  # ❌ Si le type n'existe pas, il est ignoré
   ]
   ```
2. **Si `SYMETRIE_AXIALE` n'existe pas dans `MathExerciseType`** :
   - Le type est **ignoré silencieusement**
   - `exercise_types_override` peut être vide ou ne contenir que `SYMETRIE_PROPRIETES`
3. **Si `exercise_types_override` est vide** :
   - **Ligne 890-897** (`exercises_routes.py`) : Fallback sur `generate_math_exercise_specs()` (mode legacy)
   - **Ligne 47** (`math_generation_service.py`) : Mapping par chapitre :
     ```python
     exercise_types = self._map_chapter_to_types(chapitre, niveau)
     ```
   - **Ligne 143** (`math_generation_service.py`) : Mapping "Symétrie axiale" :
     ```python
     "Symétrie axiale": [MathExerciseType.SYMETRIE_AXIALE, MathExerciseType.SYMETRIE_PROPRIETES],
     ```
   - **MAIS** : Si le mapping legacy contient d'autres types (ex: THALES), ils peuvent être sélectionnés

---

## 📊 PREMIER POINT DE RUPTURE

**Fichier** : `backend/routes/exercises_routes.py`
- **Ligne 780-783** : Conversion des types depuis le curriculum
- **Problème** : Si un type n'existe pas dans `MathExerciseType`, il est **ignoré silencieusement**
- **Résultat** : `exercise_types_override` peut être incomplet ou vide

**Fichier** : `backend/services/math_generation_service.py`
- **Ligne 100** : Sélection aléatoire **sans vérification** que le type peut être généré
- **Ligne 103-108** : Si `_generate_spec_by_type()` retourne `None`, l'exercice n'est pas ajouté
- **Problème** : Pas de retry ou fallback vers un autre type si la génération échoue

**Fichier** : `backend/routes/exercises_routes.py`
- **Ligne 890-897** : Fallback sur le mode legacy si `exercise_types_override` est vide
- **Problème** : Le mapping legacy peut contenir des types différents de ceux du curriculum

---

## 🔗 CHAÎNE DE FONCTIONS COMPLÈTE

```
POST /api/v1/exercises/generate?code_officiel=6e_G07&difficulte=difficile
  └─> backend/routes/exercises_routes.py:551
      └─> backend/routes/exercises_routes.py:746
          └─> curriculum/loader.py:get_chapter_by_official_code()
              └─> curriculum_6e.json:234-254
                  └─> exercise_types: ["SYMETRIE_AXIALE", "SYMETRIE_PROPRIETES"]
      └─> backend/routes/exercises_routes.py:780-783
          └─> Conversion en MathExerciseType
              └─> Si type n'existe pas → ignoré silencieusement ← PROBLÈME POTENTIEL
      └─> backend/routes/exercises_routes.py:881-889
          └─> backend/services/math_generation_service.py:64
              └─> generate_math_exercise_specs_with_types()
                  └─> backend/services/math_generation_service.py:100
                      └─> exercise_type = random.choice(exercise_types) ← ALÉATOIRE
                  └─> backend/services/math_generation_service.py:103
                      └─> _generate_spec_by_type()
                          └─> Si génération échoue → spec = None
                  └─> backend/services/math_generation_service.py:107
                      └─> if spec: specs.append(spec) ← Si None, pas ajouté
      └─> backend/routes/exercises_routes.py:899
          └─> Si specs vide → ValueError
          └─> Sinon → specs[0] utilisé
```

---

## ✅ POINT DE RUPTURE PRÉCIS

**Fichier** : `backend/services/math_generation_service.py`
- **Ligne 100** : Sélection aléatoire **sans seed fixe** → non déterministe
- **Ligne 103-108** : Si la génération échoue (`spec = None`), pas de retry ou fallback

**Fichier** : `backend/routes/exercises_routes.py`
- **Ligne 780-783** : Conversion des types depuis le curriculum
- **Problème** : Si un type n'existe pas dans `MathExerciseType`, il est ignoré
- **Résultat** : `exercise_types_override` peut être vide ou incomplet

**Fichier** : `backend/routes/exercises_routes.py`
- **Ligne 890-897** : Fallback sur le mode legacy
- **Problème** : Le mapping legacy peut contenir des types différents (ex: THALES) si le chapitre backend correspond à plusieurs chapitres

---

## 📝 CHAMPS DB UTILISÉS POUR LA SÉLECTION

### Champs utilisés dans `exercise_persistence_service.py` :
- **`chapter_code`** : Code du chapitre (ex: "6E_GM07", "6E_GM08", "6E_TESTS_DYN")
- **`offer`** : "free" ou "pro"
- **`difficulty`** : "facile", "moyen", "difficile"
- **`family`** : Famille d'exercices (ex: "CONVERSION", "LECTURE_HORLOGE")
- **`generator_key`** : Clé du générateur (ex: "THALES_V1") - **PAS utilisé pour la sélection côté élève**
- **`exercise_type`** : Type d'exercice (ex: "LECTURE_HEURE") - **PAS utilisé pour la sélection côté élève**

### Champs utilisés dans la génération côté élève :
- **`code_officiel`** : Code officiel du chapitre (ex: "6e_G07")
- **`difficulte`** : Niveau de difficulté
- **`offer`** : "free" ou "pro"
- **`exercise_types`** (depuis curriculum) : Liste des types d'exercices autorisés
- **`MathExerciseType`** : Enum des types d'exercices disponibles

**Résultat** : La sélection côté élève **ne filtre PAS par `family` ou `generator_key`**. Elle utilise uniquement :
1. Le `code_officiel` pour récupérer les `exercise_types` depuis le curriculum
2. Un `random.choice()` parmi ces types
3. La génération via `_generate_spec_by_type()`

---

## 🎯 CONCLUSION

**Root cause** : La sélection du type d'exercice est **aléatoire** (ligne 100 de `math_generation_service.py`) parmi les types autorisés par le curriculum. Si la génération d'un type échoue (`spec = None`), il n'y a pas de retry ou fallback, et si tous les types échouent, le système peut :
1. Lever une exception (`ValueError` si `specs` est vide)
2. Ou utiliser le fallback legacy qui peut contenir des types différents (ex: THALES)

**Premier point de rupture** : `backend/services/math_generation_service.py:100` - Sélection aléatoire sans garantie de succès, et `backend/routes/exercises_routes.py:780-783` - Conversion des types qui ignore silencieusement les types inexistants.

**Pourquoi SYMETRIE n'est pas sélectionné** :
1. Si `SYMETRIE_AXIALE` n'existe pas dans `MathExerciseType`, il est ignoré lors de la conversion
2. Si `exercise_types_override` est vide, fallback sur le mode legacy
3. Le mapping legacy peut contenir d'autres types (ex: THALES) selon le chapitre backend
4. La sélection aléatoire peut choisir THALES au lieu de SYMETRIE

