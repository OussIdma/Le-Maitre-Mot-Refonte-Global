# P0 - Traçabilité et Stabilisation UX Générateurs PREMIUM

## Objectif
Stabiliser et simplifier l'UX des générateurs PREMIUM "Calculs numériques" (CALCUL_NOMBRES_V1) et "Raisonnement multiplicatif" (RAISONNEMENT_MULTIPLICATIF_V1) en garantissant que chaque saisie utilisateur est réellement rattachée au rendu final + sauvegarde + builder + export.

---

## 1. Identification des champs UI et flux de données

### 1.1 CALCUL_NOMBRES_V1

#### Schéma de paramètres (backend)
```python
# backend/generators/calcul_nombres_v1.py
ParamSchema(
    name="exercise_type",      # ENUM: operations_simples, priorites_operatoires, decimaux
    name="difficulty",         # ENUM: facile, standard
    name="grade",              # ENUM: 6e, 5e
    name="preset",             # ENUM: simple, standard
    name="variant_id",         # ENUM: A, B, C
    name="seed",               # INT (obligatoire)
)
```

#### Où sont définis les champs UI côté frontend ?
- **Aucun formulaire spécifique** : Le frontend `ExerciseGeneratorPage.js` n'affiche **PAS** de formulaire de paramètres pour ces générateurs.
- Les paramètres sont générés automatiquement via le pipeline `/api/v1/exercises/generate` avec seulement :
  - `code_officiel` (sélectionné dans le catalogue)
  - `difficulte` (facile/moyen/difficile - sélecteur global)
  - `seed` (généré automatiquement : `Date.now() + i`)

#### Payload envoyé au backend
```javascript
// frontend/src/components/ExerciseGeneratorPage.js:583-587
const payload = {
  code_officiel: codeOfficiel,  // Ex: "6e_N04"
  difficulte: difficulte,        // "facile", "moyen", "difficile"
  seed: seed                     // Date.now() + i
};
if (isPro) {
  payload.offer = "pro";
}
```

#### Où ces champs sont consommés côté backend
1. **`backend/routes/exercises_routes.py:755`** : `generate_exercise()` reçoit la requête
2. **`backend/routes/exercises_routes.py:1594`** : Appelle `generate_exercise_with_fallback()`
3. **`backend/routes/exercises_routes.py:100-200`** : Pipeline DYNAMIC → STATIC fallback
4. **`backend/generators/factory.py`** : `GeneratorFactory.generate()` est appelé avec les paramètres
5. **`backend/generators/calcul_nombres_v1.py:689`** : `generate()` reçoit `params` et génère l'exercice

#### Où c'est sauvegardé
- **Sauvegarde utilisateur** : `backend/server.py:6037` → `save_user_exercise()`
  - Sauvegarde : `exercise_uid`, `generator_key`, `code_officiel`, `difficulty`, `seed`, `variables`, `enonce_html`, `solution_html`, `metadata`
- **DB exercices** : Les exercices dynamiques sont dans `curriculum_exercises` avec `generator_key`, `enonce_template_html`, `solution_template_html`, `variables_schema`

#### Où c'est relu dans builder/export
- **SheetBuilderPage.js** : Charge les exercices depuis `/api/mathalea/chapters/{code}/exercise-types`
- **Export PDF** : `backend/routes/user_sheets_routes.py:export_sheet_pdf()` lit `enonce_html` et `solution_html` depuis la DB

---

### 1.2 RAISONNEMENT_MULTIPLICATIF_V1

#### Schéma de paramètres (backend)
```python
# backend/generators/raisonnement_multiplicatif_v1.py
ParamSchema(
    name="exercise_type",      # ENUM: proportionnalite_tableau, pourcentage, vitesse, echelle
    name="difficulty",         # ENUM: facile, moyen, difficile
    name="grade",              # ENUM: 6e, 5e
    name="preset",             # ENUM: simple, standard
    name="variant_id",         # ENUM: A, B, C
    name="seed",               # INT (obligatoire)
)
```

#### Où sont définis les champs UI côté frontend ?
- **Même situation** : Aucun formulaire spécifique dans `ExerciseGeneratorPage.js`
- Les paramètres sont générés automatiquement via le pipeline avec seulement `code_officiel`, `difficulte`, `seed`

#### Payload envoyé au backend
- **Identique à CALCUL_NOMBRES_V1** : `code_officiel`, `difficulte`, `seed`, `offer` (si Pro)

#### Où ces champs sont consommés
- **Même flux** : `exercises_routes.py` → `generate_exercise_with_fallback()` → `GeneratorFactory.generate()` → `raisonnement_multiplicatif_v1.py:793`

#### Où c'est sauvegardé
- **Identique** : `save_user_exercise()` sauvegarde les mêmes champs

#### Où c'est relu dans builder/export
- **Identique** : SheetBuilderPage et export PDF lisent depuis la DB

---

## 2. Tableau de traçabilité

### CALCUL_NOMBRES_V1

| Input UI | Nom affiché UI | Clé envoyée au backend | Où utilisé (backend) | Où sauvegardé | Où relu (builder/export) | Statut |
|----------|----------------|------------------------|----------------------|---------------|--------------------------|--------|
| **Chapitre** | Sélecteur de chapitre | `code_officiel` | `exercises_routes.py:755` → `generate_exercise()` | `user_exercises.code_officiel` | SheetBuilder charge par `code_officiel` | ✅ **OK** |
| **Difficulté** | "Facile", "Moyen", "Difficile" | `difficulte` | `exercises_routes.py:772` → normalisé → `GeneratorFactory.generate()` → `calcul_nombres_v1.py:689` | `user_exercises.difficulty` | Export PDF lit `difficulty` | ⚠️ **PARTIEL** : Backend accepte "facile"/"standard" mais UI envoie "facile"/"moyen"/"difficile" |
| **Seed** | (Non affiché) | `seed` | `calcul_nombres_v1.py:703` → utilisé pour RNG | `user_exercises.seed` | Non relu (seed pour régénération) | ✅ **OK** |
| **exercise_type** | ❌ **NON AFFICHÉ** | ❌ **NON ENVOYÉ** | `calcul_nombres_v1.py:700` → défaut: `"operations_simples"` | Non sauvegardé explicitement | Non relu | 🐛 **BUG** : Paramètre important ignoré |
| **grade** | ❌ **NON AFFICHÉ** | ❌ **NON ENVOYÉ** | `calcul_nombres_v1.py:702` → défaut: `"6e"` | Non sauvegardé explicitement | Non relu | 🐛 **BUG** : Déduit de `code_officiel` mais pas garanti |
| **preset** | ❌ **NON AFFICHÉ** | ❌ **NON ENVOYÉ** | `calcul_nombres_v1.py` → non utilisé dans `generate()` | Non sauvegardé | Non relu | ⚠️ **IGNORÉ** : Paramètre défini mais non utilisé |
| **variant_id** | ❌ **NON AFFICHÉ** | ❌ **NON ENVOYÉ** | `calcul_nombres_v1.py` → non utilisé dans `generate()` | Non sauvegardé | Non relu | ⚠️ **IGNORÉ** : Paramètre défini mais non utilisé |

### RAISONNEMENT_MULTIPLICATIF_V1

| Input UI | Nom affiché UI | Clé envoyée au backend | Où utilisé (backend) | Où sauvegardé | Où relu (builder/export) | Statut |
|----------|----------------|------------------------|----------------------|---------------|--------------------------|--------|
| **Chapitre** | Sélecteur de chapitre | `code_officiel` | `exercises_routes.py:755` → `generate_exercise()` | `user_exercises.code_officiel` | SheetBuilder charge par `code_officiel` | ✅ **OK** |
| **Difficulté** | "Facile", "Moyen", "Difficile" | `difficulte` | `exercises_routes.py:772` → normalisé → `GeneratorFactory.generate()` → `raisonnement_multiplicatif_v1.py:793` | `user_exercises.difficulty` | Export PDF lit `difficulty` | ⚠️ **PARTIEL** : Backend accepte "facile"/"moyen"/"difficile" mais mapping UI→backend non garanti |
| **Seed** | (Non affiché) | `seed` | `raisonnement_multiplicatif_v1.py:807` → utilisé pour RNG | `user_exercises.seed` | Non relu (seed pour régénération) | ✅ **OK** |
| **exercise_type** | ❌ **NON AFFICHÉ** | ❌ **NON ENVOYÉ** | `raisonnement_multiplicatif_v1.py:804` → défaut: `"proportionnalite_tableau"` | Non sauvegardé explicitement | Non relu | 🐛 **BUG** : Paramètre critique ignoré (4 types différents) |
| **grade** | ❌ **NON AFFICHÉ** | ❌ **NON ENVOYÉ** | `raisonnement_multiplicatif_v1.py:806` → défaut: `"6e"` | Non sauvegardé explicitement | Non relu | 🐛 **BUG** : Déduit de `code_officiel` mais pas garanti |
| **preset** | ❌ **NON AFFICHÉ** | ❌ **NON ENVOYÉ** | `raisonnement_multiplicatif_v1.py` → non utilisé dans `generate()` | Non sauvegardé | Non relu | ⚠️ **IGNORÉ** : Paramètre défini mais non utilisé |
| **variant_id** | ❌ **NON AFFICHÉ** | ❌ **NON ENVOYÉ** | `raisonnement_multiplicatif_v1.py` → non utilisé dans `generate()` | Non sauvegardé | Non relu | ⚠️ **IGNORÉ** : Paramètre défini mais non utilisé |

---

## 3. Simplification UX

### 3.1 Inputs à supprimer (inutile/ignoré/complexité)

| Paramètre | Raison | Action |
|-----------|--------|--------|
| `preset` | Défini dans le schéma mais jamais utilisé dans `generate()` | ✅ **SUPPRIMER** du schéma |
| `variant_id` | Défini dans le schéma mais jamais utilisé dans `generate()` | ✅ **SUPPRIMER** du schéma |

### 3.2 Inputs à déplacer en "Options avancées"

| Paramètre | Raison | Action |
|-----------|--------|--------|
| `seed` | Technique, utilisé pour reproductibilité mais pas besoin d'être visible | ✅ **DÉPLACER** en options avancées (ou auto-généré uniquement) |

### 3.3 UX minimale proposée (max 3 inputs visibles)

#### CALCUL_NOMBRES_V1
1. **Type d'exercice** (obligatoire) : 
   - Radio buttons ou Select : "Opérations simples" / "Priorités opératoires" / "Décimaux"
   - Mapping : `operations_simples` / `priorites_operatoires` / `decimaux`
2. **Niveau** (obligatoire) :
   - Radio buttons : "6e" / "5e"
   - Mapping : `6e` / `5e`
3. **Difficulté** (obligatoire) :
   - Radio buttons : "Facile" / "Standard"
   - Mapping : `facile` / `standard` (corriger le mapping UI)

#### RAISONNEMENT_MULTIPLICATIF_V1
1. **Type d'exercice** (obligatoire) :
   - Select : "Proportionnalité (tableau)" / "Pourcentages" / "Vitesse" / "Échelle"
   - Mapping : `proportionnalite_tableau` / `pourcentage` / `vitesse` / `echelle`
2. **Niveau** (obligatoire) :
   - Radio buttons : "6e" / "5e"
   - Mapping : `6e` / `5e`
3. **Difficulté** (obligatoire) :
   - Radio buttons : "Facile" / "Moyen" / "Difficile"
   - Mapping : `facile` / `moyen` / `difficile`

**Options avancées** (collapsible) :
- Seed (auto-généré par défaut, modifiable pour reproductibilité)

---

## 4. Bugs identifiés et corrections

### P0 - Bugs critiques

#### Bug #1 : `exercise_type` non envoyé → toujours défaut
- **Impact** : L'utilisateur ne peut pas choisir le type d'exercice (ex: toujours "operations_simples" pour CALCUL_NOMBRES_V1)
- **Cause** : `ExerciseGeneratorPage.js` n'affiche pas de formulaire de paramètres pour les générateurs premium
- **Fix** : 
  1. Ajouter un formulaire de paramètres dans `ExerciseGeneratorPage.js` quand un générateur premium est détecté
  2. Envoyer `exercise_type` dans le payload vers `/api/v1/exercises/generate`
  3. Sauvegarder `exercise_type` dans `metadata` lors de la sauvegarde

#### Bug #2 : `grade` non envoyé → déduit de `code_officiel` (non garanti)
- **Impact** : Si `code_officiel` ne contient pas le niveau (ex: "N04"), le défaut "6e" est utilisé même pour un chapitre 5e
- **Cause** : `grade` n'est pas extrait de `code_officiel` de manière fiable
- **Fix** :
  1. Extraire `grade` de `code_officiel` (format: `{grade}_{code}`) dans `exercises_routes.py`
  2. OU afficher un input `grade` dans le formulaire UI
  3. Sauvegarder `grade` dans `metadata`

#### Bug #3 : Mapping difficulté UI → backend incohérent
- **Impact** : UI envoie "moyen" mais backend attend "standard" pour CALCUL_NOMBRES_V1
- **Cause** : `map_ui_difficulty_to_generator()` existe mais n'est pas utilisé partout
- **Fix** :
  1. Utiliser `map_ui_difficulty_to_generator()` dans `exercises_routes.py` avant d'appeler `GeneratorFactory.generate()`
  2. Normaliser "moyen" → "standard" pour CALCUL_NOMBRES_V1

#### Bug #4 : Paramètres non sauvegardés dans `metadata`
- **Impact** : Lors de la régénération ou export, les paramètres originaux sont perdus
- **Cause** : `save_user_exercise()` ne sauvegarde pas `exercise_type`, `grade`, `preset`, `variant_id`
- **Fix** :
  1. Sauvegarder tous les paramètres du générateur dans `metadata.generator_params` lors de la sauvegarde
  2. Relire ces paramètres lors de la régénération

### P1 - Améliorations

#### Issue #1 : `preset` et `variant_id` définis mais non utilisés
- **Action** : Supprimer du schéma ou les utiliser réellement dans `generate()`

#### Issue #2 : Pas de formulaire UI pour les générateurs premium
- **Action** : Intégrer `GeneratorParamsForm` dans `ExerciseGeneratorPage.js` quand un générateur premium est sélectionné

---

## 5. Patch plan (max 3 PRs)

### PR #1 : Bugfix minimal - Chainage UI → Backend → Sauvegarde

**Fichiers modifiés** :
- `frontend/src/components/ExerciseGeneratorPage.js`
  - Ajouter un formulaire de paramètres pour les générateurs premium
  - Envoyer `exercise_type`, `grade` dans le payload
- `backend/routes/exercises_routes.py`
  - Extraire `grade` de `code_officiel` si non fourni
  - Utiliser `map_ui_difficulty_to_generator()` avant `GeneratorFactory.generate()`
- `backend/server.py` (`save_user_exercise`)
  - Sauvegarder `exercise_type`, `grade` dans `metadata.generator_params`

**Tests manuels** :
1. Générer un exercice CALCUL_NOMBRES_V1 avec `exercise_type="priorites_operatoires"`
2. Vérifier que l'exercice généré correspond au type choisi
3. Sauvegarder l'exercice
4. Vérifier que `metadata.generator_params.exercise_type` est sauvegardé
5. Régénérer avec les mêmes paramètres → même résultat

### PR #2 : Simplification UX - Formulaire minimal (3 inputs)

**Fichiers modifiés** :
- `frontend/src/components/ExerciseGeneratorPage.js`
  - Afficher un formulaire compact avec 3 inputs : Type, Niveau, Difficulté
  - Masquer `seed` (auto-généré) sauf en mode "Options avancées"
- `backend/generators/calcul_nombres_v1.py`
  - Supprimer `preset` et `variant_id` du schéma
- `backend/generators/raisonnement_multiplicatif_v1.py`
  - Supprimer `preset` et `variant_id` du schéma

**Tests manuels** :
1. Ouvrir `/generer` et sélectionner un chapitre avec CALCUL_NOMBRES_V1
2. Vérifier que seuls 3 inputs sont visibles : Type, Niveau, Difficulté
3. Générer un exercice → vérifier que les paramètres sont appliqués
4. Sauvegarder → vérifier que les paramètres sont sauvegardés

### PR #3 : Stabilisation Builder/Export - Relire les paramètres sauvegardés

**Fichiers modifiés** :
- `frontend/src/components/SheetBuilderPage.js`
  - Afficher les paramètres du générateur pour les exercices sauvegardés
- `backend/routes/user_sheets_routes.py` (`export_sheet_pdf`)
  - Vérifier que `metadata.generator_params` est présent dans les exercices exportés
  - Log si paramètres manquants

**Tests manuels** :
1. Sauvegarder un exercice avec paramètres spécifiques
2. Ouvrir SheetBuilder et ajouter l'exercice sauvegardé
3. Vérifier que les paramètres sont affichés
4. Exporter en PDF → vérifier que l'exercice correspond aux paramètres sauvegardés

---

## 6. Tests manuels

### CALCUL_NOMBRES_V1

#### Test 1 : Même seed + mêmes inputs = même rendu
1. Ouvrir `/generer`
2. Sélectionner chapitre avec CALCUL_NOMBRES_V1 (ex: "6e_N04")
3. Choisir Type: "Priorités opératoires", Niveau: "6e", Difficulté: "Standard"
4. Noter le seed affiché (ou utiliser seed fixe: 12345)
5. Générer l'exercice → noter le rendu (énoncé, solution)
6. Régénérer avec les mêmes paramètres et le même seed
7. ✅ **VÉRIFIER** : Même énoncé, même solution

#### Test 2 : Seed différent (variante) = rendu différent mais même objectif
1. Même setup que Test 1
2. Générer avec seed=12345 → noter le rendu
3. Générer avec seed=12346 → noter le rendu
4. ✅ **VÉRIFIER** : Énoncés différents (nombres différents) mais même type d'exercice (priorités opératoires)

#### Test 3 : Sauvegarde puis export PDF = rendu identique, sujet ≠ corrigé
1. Générer un exercice CALCUL_NOMBRES_V1
2. Sauvegarder l'exercice
3. Ouvrir SheetBuilder
4. Ajouter l'exercice sauvegardé
5. Exporter en PDF (sujet + corrigé séparés)
6. ✅ **VÉRIFIER** : 
   - Sujet contient l'énoncé (sans solution)
   - Corrigé contient la solution
   - Rendu identique à la génération initiale

#### Test 4 : Changer un input UI modifie réellement l'exercice (preuve)
1. Générer avec Type="Opérations simples", Niveau="6e", Difficulté="Facile"
2. Noter le rendu (ex: "5 + 3")
3. Changer Type="Priorités opératoires" (garder Niveau et Difficulté)
4. Générer → noter le rendu (ex: "5 + 3 × 2")
5. ✅ **VÉRIFIER** : Rendu différent (priorités vs opérations simples)

#### Test 5 : Mapping difficulté UI → backend
1. Générer avec Difficulté="Moyen" (UI)
2. Vérifier dans les logs backend que "moyen" est mappé vers "standard" pour CALCUL_NOMBRES_V1
3. ✅ **VÉRIFIER** : Pas d'erreur 422, exercice généré avec difficulté "standard"

### RAISONNEMENT_MULTIPLICATIF_V1

#### Test 1 : Même seed + mêmes inputs = même rendu
1. Ouvrir `/generer`
2. Sélectionner chapitre avec RAISONNEMENT_MULTIPLICATIF_V1 (ex: "6e_SP03")
3. Choisir Type: "Pourcentages", Niveau: "6e", Difficulté: "Facile"
4. Noter le seed (ex: 12345)
5. Générer → noter le rendu
6. Régénérer avec mêmes paramètres et seed
7. ✅ **VÉRIFIER** : Même énoncé, même solution

#### Test 2 : Seed différent = rendu différent mais même objectif
1. Même setup que Test 1
2. Générer avec seed=12345 → noter le rendu
3. Générer avec seed=12346 → noter le rendu
4. ✅ **VÉRIFIER** : Énoncés différents (pourcentages différents) mais même type (pourcentages)

#### Test 3 : Sauvegarde puis export PDF = rendu identique, sujet ≠ corrigé
1. Générer un exercice RAISONNEMENT_MULTIPLICATIF_V1
2. Sauvegarder
3. Ouvrir SheetBuilder
4. Ajouter l'exercice sauvegardé
5. Exporter en PDF
6. ✅ **VÉRIFIER** : Sujet ≠ Corrigé, rendu identique

#### Test 4 : Changer un input UI modifie réellement l'exercice
1. Générer avec Type="Proportionnalité (tableau)", Niveau="6e", Difficulté="Facile"
2. Noter le rendu (tableau de proportionnalité)
3. Changer Type="Pourcentages" (garder Niveau et Difficulté)
4. Générer → noter le rendu (problème de pourcentage)
5. ✅ **VÉRIFIER** : Rendu différent (tableau vs pourcentage)

#### Test 5 : Mapping difficulté UI → backend
1. Générer avec Difficulté="Moyen" (UI)
2. Vérifier dans les logs que "moyen" est accepté pour RAISONNEMENT_MULTIPLICATIF_V1
3. ✅ **VÉRIFIER** : Pas d'erreur 422, exercice généré avec difficulté "moyen"

---

## 7. Résumé des issues

### P0 - Bugs critiques (à corriger immédiatement)

| Issue | Impact | Cause | Fix |
|-------|--------|-------|-----|
| `exercise_type` non envoyé | L'utilisateur ne peut pas choisir le type d'exercice | Pas de formulaire UI | Ajouter formulaire, envoyer dans payload, sauvegarder |
| `grade` non envoyé | Déduit de `code_officiel` (non garanti) | Pas extrait de manière fiable | Extraire de `code_officiel` ou afficher input |
| Mapping difficulté incohérent | UI envoie "moyen" mais backend attend "standard" | `map_ui_difficulty_to_generator()` non utilisé partout | Utiliser la fonction de mapping |
| Paramètres non sauvegardés | Perte des paramètres lors de la régénération | `save_user_exercise()` ne sauvegarde pas tous les paramètres | Sauvegarder dans `metadata.generator_params` |

### P1 - Améliorations (à faire après P0)

| Issue | Impact | Action |
|-------|--------|--------|
| `preset` et `variant_id` non utilisés | Schéma encombré | Supprimer du schéma |
| Pas de formulaire UI pour premium | UX confuse | Intégrer `GeneratorParamsForm` |

---

## 8. Prochaines étapes

1. ✅ **Créer PR #1** : Bugfix minimal (chainage UI → Backend → Sauvegarde)
2. ✅ **Tester PR #1** : 5 tests manuels par générateur
3. ✅ **Créer PR #2** : Simplification UX (formulaire minimal)
4. ✅ **Tester PR #2** : Vérifier que seuls 3 inputs sont visibles
5. ✅ **Créer PR #3** : Stabilisation Builder/Export
6. ✅ **Tester PR #3** : Vérifier que les paramètres sont relus correctement

---

## 9. Notes techniques

### Extraction de `grade` depuis `code_officiel`
Format attendu : `{grade}_{code}` (ex: "6e_N04", "5e_SP03")
```python
# backend/routes/exercises_routes.py
if request.code_officiel:
    parts = request.code_officiel.split('_', 1)
    if len(parts) == 2:
        grade = parts[0]  # "6e" ou "5e"
    else:
        grade = "6e"  # Fallback
```

### Mapping difficulté UI → Backend
```python
# backend/routes/exercises_routes.py
from backend.utils.difficulty_utils import map_ui_difficulty_to_generator

# Avant d'appeler GeneratorFactory.generate()
mapped_difficulty = map_ui_difficulty_to_generator(
    ui_difficulty=request.difficulte,  # "moyen"
    generator_key="CALCUL_NOMBRES_V1",
    supported_difficulties=["facile", "standard"]
)
# mapped_difficulty = "standard" pour CALCUL_NOMBRES_V1
```

### Sauvegarde des paramètres
```python
# backend/server.py (save_user_exercise)
metadata = {
    "generator_params": {
        "exercise_type": request_body.exercise_type,
        "grade": request_body.grade,
        "difficulty": request_body.difficulty,
        "seed": request_body.seed
    },
    ...existing_metadata...
}
```




