# 🔍 INVESTIGATION ROOT CAUSE - Placeholders {{...}} visibles côté élève (THALES_V1 / TESTS_DYN)

## Symptôme
**Côté élève** : Génération d'exercices `6e_TESTS_DYN` affiche des placeholders non résolus dans `enonce_html` et `solution_html` :
- `{{longueur_initiale}}`
- `{{largeur_initiale}}`
- `{{longueur_finale}}`
- `{{largeur_finale}}`

---

## 📍 CHAÎNE COMPLÈTE DU PIPELINE

### 1. **ENTRÉE - Route API**

**Fichier** : `backend/routes/exercises_routes.py`
- **Ligne 688** : Vérification `is_tests_dyn_request(request.code_officiel)`
- **Ligne 694-698** : Appel à `generate_tests_dyn_exercise(offer, difficulty, seed)`
- **Ligne 713** : Retour direct de `dyn_exercise` (pas de post-traitement)

---

### 2. **SÉLECTION DU TEMPLATE**

**Fichier** : `backend/services/tests_dyn_handler.py`
- **Ligne 135-163** : Fonction `generate_tests_dyn_exercise()`
- **Ligne 156-160** : Appel à `get_random_tests_dyn_exercise(offer, difficulty, seed)`
  - Source : `backend/data/tests_dyn_exercises.py`
  - Retourne un template d'exercice depuis la constante `TESTS_DYN_EXERCISES`

**Fichier** : `backend/data/tests_dyn_exercises.py`
- **Ligne 50-83** : Template ID 2 (difficulty="moyen", offer="free")
- **Ligne 57-58** : `enonce_template_html` contient `{{longueur_initiale}}` et `{{largeur_initiale}}`
- **Ligne 61-72** : `solution_template_html` contient également ces placeholders
- **Ligne 73-80** : `variables_schema` déclare que le template attend :
  - `longueur_initiale`, `largeur_initiale`
  - `longueur_finale`, `largeur_finale`

**Résultat** : Le template est **figé** et attend toujours des variables de type **rectangle**.

---

### 3. **GÉNÉRATION DES VARIABLES**

**Fichier** : `backend/services/tests_dyn_handler.py`
- **Ligne 37-132** : Fonction `format_dynamic_exercise()`
- **Ligne 57** : Récupère `generator_key` depuis le template (généralement "THALES_V1")
- **Ligne 61-65** : Appel à `generate_dynamic_exercise(generator_key="THALES_V1", seed, difficulty)`

**Fichier** : `backend/generators/thales_generator.py`
- **Ligne 433-446** : Fonction `generate_dynamic_exercise()` qui crée une instance et appelle `generate()`
- **Ligne 51-91** : Méthode `generate()` de `ThalesV1Generator`
- **Ligne 64** : **PROBLÈME IDENTIFIÉ** - Sélection aléatoire du type de figure :
  ```python
  figure_type = random.choice(ThalesV1Config.FIGURE_TYPES)
  # ThalesV1Config.FIGURE_TYPES = ["rectangle", "triangle", "carre"]
  ```
- **Ligne 156-199** : Méthode `_build_variables()` qui crée les variables selon le type :
  - **Lignes 182-189** : Si `figure_type == "rectangle"` → crée `longueur_initiale`, `largeur_initiale`
  - **Lignes 190-197** : Si `figure_type == "triangle"` → crée `base_initiale`, `hauteur_initiale`
  - **Lignes 176-181** : Si `figure_type == "carre"` → crée `cote_initial`, `cote_final`

**Résultat** : Le générateur peut produire **3 types différents** de figures, mais le template attend **toujours un rectangle**.

---

### 4. **MERGE VARIABLES + RESULTS**

**Fichier** : `backend/services/tests_dyn_handler.py`
- **Ligne 67-68** : Extraction de `variables` et `results` depuis `gen_result`
- **Ligne 75** : Merge : `all_vars = {**variables, **results}`

**État à ce point** :
- Si générateur produit **rectangle** : `all_vars` contient `longueur_initiale`, `largeur_initiale` ✅
- Si générateur produit **triangle** : `all_vars` contient `base_initiale`, `hauteur_initiale` ❌
- Si générateur produit **carré** : `all_vars` contient `cote_initial`, `cote_final` ❌

---

### 5. **MAPPING TEMPLATE/GÉNÉRATEUR**

**Fichier** : `backend/services/tests_dyn_handler.py`
- **Lignes 77-98** : Mapping bidirectionnel triangle ↔ rectangle
- **Lignes 81-88** : Mapping triangle → rectangle :
  ```python
  if "base_initiale" in all_vars and "longueur_initiale" not in all_vars:
      all_vars["longueur_initiale"] = all_vars["base_initiale"]
  if "hauteur_initiale" in all_vars and "largeur_initiale" not in all_vars:
      all_vars["largeur_initiale"] = all_vars["hauteur_initiale"]
  # ... (même logique pour _finale)
  ```

**Problème potentiel** :
- Le mapping s'applique **APRÈS** le merge ligne 75
- Les conditions sont correctes (`if "base_initiale" in all_vars and "longueur_initiale" not in all_vars`)
- **MAIS** : Si le générateur produit un **carré**, le mapping ne couvre pas ce cas (pas de mapping carré → rectangle)

---

### 6. **RENDU DES TEMPLATES**

**Fichier** : `backend/services/tests_dyn_handler.py`
- **Ligne 100-101** : Appel à `render_template(enonce_template, all_vars)` et `render_template(solution_template, all_vars)`

**Fichier** : `backend/services/template_renderer.py`
- **Ligne 17-62** : Fonction `render_template()`
- **Ligne 40-57** : Fonction `replace_placeholder()` :
  - Si variable trouvée → remplace par la valeur
  - **Ligne 56-57** : Si variable **non trouvée** → **laisse le placeholder intact**
  ```python
  if var_name in variables:
      # ... remplace
  # Variable non trouvée - laisser le placeholder
  return match.group(0)  # ❌ Retourne {{longueur_initiale}} tel quel
  ```

**Résultat** : Si `longueur_initiale` n'existe pas dans `all_vars`, le placeholder reste visible.

---

## 🎯 ROOT CAUSE IDENTIFIÉE

### Scénario 1 : Générateur produit un TRIANGLE
1. **Ligne 64** (`thales_generator.py`) : `figure_type = "triangle"` (aléatoire)
2. **Lignes 190-197** (`thales_generator.py`) : Variables créées = `base_initiale`, `hauteur_initiale`
3. **Ligne 75** (`tests_dyn_handler.py`) : `all_vars = {base_initiale: 5, hauteur_initiale: 4, ...}`
4. **Lignes 81-88** (`tests_dyn_handler.py`) : Mapping appliqué → `longueur_initiale = base_initiale` ✅
5. **Résultat** : Placeholders résolus ✅

### Scénario 2 : Générateur produit un CARRÉ
1. **Ligne 64** (`thales_generator.py`) : `figure_type = "carre"` (aléatoire)
2. **Lignes 176-181** (`thales_generator.py`) : Variables créées = `cote_initial`, `cote_final`
3. **Ligne 75** (`tests_dyn_handler.py`) : `all_vars = {cote_initial: 5, cote_final: 10, ...}`
4. **Lignes 81-98** (`tests_dyn_handler.py`) : **AUCUN mapping carré → rectangle** ❌
5. **Ligne 100** (`tests_dyn_handler.py`) : `render_template()` appelé avec `all_vars` sans `longueur_initiale`
6. **Ligne 56** (`template_renderer.py`) : Placeholder `{{longueur_initiale}}` laissé intact ❌
7. **Résultat** : Placeholders visibles dans le HTML ❌

### Scénario 3 : Générateur produit un RECTANGLE
1. **Ligne 64** (`thales_generator.py`) : `figure_type = "rectangle"` (aléatoire)
2. **Lignes 182-189** (`thales_generator.py`) : Variables créées = `longueur_initiale`, `largeur_initiale` ✅
3. **Résultat** : Placeholders résolus ✅

---

## 📊 PREMIER POINT DE RUPTURE

**Fichier** : `backend/services/tests_dyn_handler.py`
- **Lignes 81-98** : Le mapping ne couvre que **triangle ↔ rectangle**
- **Manque** : Mapping **carré → rectangle** (ou carré → triangle)

**Fichier** : `backend/generators/thales_generator.py`
- **Ligne 64** : Sélection aléatoire parmi 3 types (`["rectangle", "triangle", "carre"]`)
- **Problème** : Le générateur peut produire un **carré**, mais le template attend toujours un **rectangle**

**Fichier** : `backend/data/tests_dyn_exercises.py`
- **Ligne 57-58** : Template figé qui attend `{{longueur_initiale}}` et `{{largeur_initiale}}`
- **Problème** : Pas d'adaptation selon le type de figure généré

---

## 🔗 CHAÎNE DE FONCTIONS COMPLÈTE

```
POST /api/v1/exercises/generate
  └─> backend/routes/exercises_routes.py:688
      └─> is_tests_dyn_request()
      └─> backend/services/tests_dyn_handler.py:135
          └─> generate_tests_dyn_exercise()
              └─> backend/data/tests_dyn_exercises.py:147
                  └─> get_random_tests_dyn_exercise() → Template ID 2
              └─> backend/services/tests_dyn_handler.py:37
                  └─> format_dynamic_exercise()
                      └─> backend/generators/thales_generator.py:433
                          └─> generate_dynamic_exercise()
                              └─> ThalesV1Generator.generate()
                                  └─> random.choice(["rectangle", "triangle", "carre"]) ← PROBLÈME
                                  └─> _build_variables()
                                      └─> Variables selon figure_type
                      └─> backend/services/tests_dyn_handler.py:75
                          └─> all_vars = {**variables, **results}
                      └─> backend/services/tests_dyn_handler.py:81-98
                          └─> Mapping triangle ↔ rectangle (mais PAS carré) ← PROBLÈME
                      └─> backend/services/tests_dyn_handler.py:100
                          └─> render_template(enonce_template, all_vars)
                              └─> backend/services/template_renderer.py:17
                                  └─> Si variable absente → placeholder intact ← RÉSULTAT VISIBLE
```

---

## ✅ POINT DE RUPTURE PRÉCIS

**Fichier** : `backend/services/tests_dyn_handler.py`
- **Lignes 81-98** : Mapping incomplet
- **Manque** : Gestion du cas `figure_type == "carre"`

**Fichier** : `backend/generators/thales_generator.py`
- **Ligne 64** : Sélection aléatoire qui peut produire un carré
- **Lignes 176-181** : Variables créées pour carré = `cote_initial`, `cote_final`
- **Pas de correspondance** avec les variables attendues par le template (`longueur_initiale`, `largeur_initiale`)

---

## 📝 VARIABLES DISPONIBLES vs ATTENDUES

### Template attend (ID 2, difficulty="moyen")
- `longueur_initiale` ✅
- `largeur_initiale` ✅
- `longueur_finale` ✅
- `largeur_finale` ✅

### Générateur produit (selon figure_type)

**Si rectangle** :
- `longueur_initiale` ✅
- `largeur_initiale` ✅
- `longueur_finale` ✅
- `largeur_finale` ✅
→ **Match parfait** ✅

**Si triangle** :
- `base_initiale` → mappé vers `longueur_initiale` ✅
- `hauteur_initiale` → mappé vers `largeur_initiale` ✅
- `base_finale` → mappé vers `longueur_finale` ✅
- `hauteur_finale` → mappé vers `largeur_finale` ✅
→ **Match après mapping** ✅

**Si carré** :
- `cote_initial` ❌ (pas mappé)
- `cote_final` ❌ (pas mappé)
→ **Pas de match** ❌ → **Placeholders visibles**

---

## 🎯 CONCLUSION

**Root cause** : Le mapping dans `tests_dyn_handler.py` (lignes 81-98) ne couvre que le cas **triangle ↔ rectangle**, mais le générateur peut aussi produire un **carré** (ligne 64 de `thales_generator.py`). Quand un carré est généré, les variables `cote_initial`/`cote_final` ne sont pas mappées vers `longueur_initiale`/`largeur_initiale`, donc les placeholders restent visibles.

**Premier point de rupture** : `backend/services/tests_dyn_handler.py:81-98` - Mapping incomplet (manque carré → rectangle).

