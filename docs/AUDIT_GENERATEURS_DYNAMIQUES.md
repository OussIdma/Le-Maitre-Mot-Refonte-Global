# AUDIT GÉNÉRATEURS DYNAMIQUES — INVENTAIRE COMPLET

**Date :** 2025-01-XX  
**Objectif :** État des lieux exhaustif des générateurs dynamiques pour stabilisation P4

---

## 📋 RÉSUMÉ EXÉCUTIF

**Total générateurs identifiés :** 7  
**Générateurs enregistrés dans Factory :** 6  
**Générateurs legacy (non-Factory) :** 1 (THALES_V1)

### Répartition par statut (préliminaire)
- ✅ **GOLD (à confirmer par tests) :** 0
- 🟠 **AMÉLIORABLE :** 0
- 🔴 **À DÉSACTIVER :** 0
- ⚠️ **À ÉVALUER :** 7

---

## 🧩 INVENTAIRE DÉTAILLÉ

### 1. THALES_V2

**Fichier :** `backend/generators/thales_v2.py`  
**Clé :** `THALES_V2`  
**Version :** 2.0.0  
**Statut Factory :** ✅ Enregistré

#### Métadonnées
- **Label :** Agrandissements/Réductions
- **Description :** Exercices sur les transformations de figures (proportionnalité)
- **Niveaux :** 6e, 5e
- **Exercise Type :** `THALES`
- **SVG Mode :** `AUTO`
- **Supports Double SVG :** ✅ Oui

#### Chapitres utilisateurs (curriculum)
- `6e_TESTS_DYN` (via `exercise_types: ["AGRANDISSEMENT_REDUCTION"]`)

#### Inputs attendus
- `figure_type` (ENUM) : `["rectangle", "triangle", "carre"]` → default: `"carre"`
- `difficulty` (ENUM) : `["facile", "moyen", "difficile"]` → default: `"moyen"`
- `force_coefficient` (FLOAT, optionnel) : min=0.5, max=10
- `force_agrandissement` (BOOL, optionnel)

#### Outputs
- `variables` : dict avec toutes les valeurs pour templates
- `geo_data` : dict JSON-safe (figure_type, base_dimensions, final_dimensions, coefficient, is_agrandissement)
- `figure_svg_enonce` : SVG de la figure initiale
- `figure_svg_solution` : SVG de la figure agrandie/réduite
- `meta` : exercise_type, svg_mode, figure_type, coefficient, difficulty
- `results` : valeurs calculées

#### Dépendances
- **Legacy :** `ThalesV1Generator` (via `backend/generators/thales_generator.py`)
- **Templates :** Utilise templates DB (via `format_dynamic_exercise`)
- **RNG :** `random.Random(seed)` local + monkeypatch `random.choice` (⚠️ fragile)

#### Fallback existant
- ❌ Non explicite dans le générateur
- ✅ Fallback STATIC via pipeline P0 (`generate_exercise_with_fallback`)

#### Points d'attention
- ⚠️ **Monkeypatch de `random.choice`** : fragile, peut causer des effets de bord
- ⚠️ **Dépendance legacy** : utilise `ThalesV1Generator` qui n'est pas dans Factory
- ✅ **Déterministe** : utilise seed local

---

### 2. SYMETRIE_AXIALE_V2

**Fichier :** `backend/generators/symetrie_axiale_v2.py`  
**Clé :** `SYMETRIE_AXIALE_V2`  
**Version :** 2.0.0  
**Statut Factory :** ✅ Enregistré

#### Métadonnées
- **Label :** Symétrie Axiale
- **Description :** Exercices sur la symétrie axiale: identification, tracé, axes de symétrie
- **Niveaux :** 6e, 5e
- **Exercise Type :** `SYMETRIE_AXIALE`
- **SVG Mode :** `AUTO`
- **Supports Double SVG :** ✅ Oui

#### Chapitres utilisateurs (curriculum)
- `6e_G07` (via `exercise_types: ["SYMETRIE_AXIALE", "SYMETRIE_PROPRIETES"]`)

#### Inputs attendus
- `figure_type` (ENUM) : `["point", "segment", "triangle", "rectangle"]` → default: `"point"`
- `axe_type` (ENUM) : `["vertical", "horizontal", "oblique"]` → default: `"vertical"`
- `show_grid` (BOOL) : default: `True`
- `difficulty` (ENUM) : `["facile", "moyen", "difficile"]` → default: `"moyen"`
- `show_solution_steps` (BOOL) : default: `True`
- `label_points` (BOOL) : default: `True`

#### Outputs
- `variables` : dict avec valeurs pour templates
- `geo_data` : dict JSON-safe (figure, axe, symmetric, grid_size, scale)
- `figure_svg_enonce` : SVG avec figure initiale + axe
- `figure_svg_solution` : SVG avec figure symétrique
- `meta` : exercise_type, svg_mode, figure_type, axe_type, difficulty

#### Dépendances
- **Templates :** Utilise templates DB (via `format_dynamic_exercise`)
- **RNG :** `safe_random_choice`, `safe_randrange` (via observability)
- **SVG :** `create_svg_wrapper` (via base_generator)

#### Fallback existant
- ❌ Non explicite dans le générateur
- ✅ Fallback STATIC via pipeline P0

#### Points d'attention
- ✅ **RNG sécurisé** : utilise `safe_random_choice` (évite pool vide)
- ✅ **Déterministe** : utilise seed local
- ✅ **Validation pools** : vérifie que les ranges ne sont pas vides avant choix

---

### 3. CALCUL_NOMBRES_V1

**Fichier :** `backend/generators/calcul_nombres_v1.py`  
**Clé :** `CALCUL_NOMBRES_V1`  
**Version :** 1.0.0  
**Statut Factory :** ✅ Enregistré

#### Métadonnées
- **Label :** Calculs numériques
- **Description :** Exercices de calcul numérique pour 6e et 5e
- **Niveaux :** 6e, 5e
- **Exercise Type :** `CALCUL_NOMBRES` (à vérifier)
- **SVG Mode :** `NONE`
- **Supports Double SVG :** ❌ Non

#### Chapitres utilisateurs (curriculum)
- `6e_N04` (via `exercise_types: ["CALCUL_NOMBRES_V1"]`)
- `6e_N05` (via `exercise_types: ["CALCUL_NOMBRES_V1"]`)
- `6e_N06` (via `exercise_types: ["CALCUL_NOMBRES_V1"]`)

#### Inputs attendus
- `exercise_type` (ENUM) : `["operations_simples", "priorites_operatoires", "decimaux"]` → default: `"operations_simples"`
- `difficulty` (ENUM) : `["facile", "standard"]` → default: `"standard"`
- `grade` (ENUM) : `["6e", "5e"]` → default: `"6e"`
- `preset` (ENUM) : `["simple", "standard"]` → default: `"standard"`
- `variant_id` (ENUM) : `["A", "B", "C"]` → default: `"A"`
- `seed` (INT) : **OBLIGATOIRE**

#### Outputs
- `variables` : dict avec expression, resultat, etapes, etc.
- `meta` : exercise_type, difficulty, grade, variant_id
- **Pas de SVG** (svg_mode=NONE)

#### Dépendances
- **Templates :** Utilise templates DB avec variants (A, B, C)
- **RNG :** `safe_random_choice`, `safe_randrange` (via observability)
- **Variabilité :** Pool de formulations alternatives (`_ENONCE_VARIANTS`, `_CONSIGNE_VARIANTS`)

#### Fallback existant
- ❌ Non explicite dans le générateur
- ✅ Fallback STATIC via pipeline P0

#### Points d'attention
- ⚠️ **Seed obligatoire** : peut causer des erreurs 422 si non fourni
- ✅ **Variabilité** : pools de formulations pour éviter répétition
- ✅ **Validation stricte** : `_validate_exercise_type`, `_validate_grade`, `_validate_difficulty`

---

### 4. RAISONNEMENT_MULTIPLICATIF_V1

**Fichier :** `backend/generators/raisonnement_multiplicatif_v1.py`  
**Clé :** `RAISONNEMENT_MULTIPLICATIF_V1`  
**Version :** 1.0.0  
**Statut Factory :** ✅ Enregistré  
**Statut Premium :** ✅ Oui (`min_offer="pro"`)

#### Métadonnées
- **Label :** Raisonnement multiplicatif (PREMIUM)
- **Description :** Exercices de raisonnement multiplicatif : proportionnalité, pourcentages, vitesse, échelle
- **Niveaux :** 6e, 5e
- **Exercise Type :** `RAISONNEMENT_MULTIPLICATIF`
- **SVG Mode :** `NONE`
- **Supports Double SVG :** ❌ Non

#### Chapitres utilisateurs (curriculum)
- `6e_SP01` (via `exercise_types: ["RAISONNEMENT_MULTIPLICATIF_V1"]`)
- `6e_SP03` (via `exercise_types: ["RAISONNEMENT_MULTIPLICATIF_V1"]`)

#### Inputs attendus
- `exercise_type` (ENUM) : `["proportionnalite_tableau", "pourcentage", "vitesse", "echelle"]` → default: `"proportionnalite_tableau"`
- `difficulty` (ENUM) : `["facile", "moyen", "difficile"]` → default: `"moyen"`
- `grade` (ENUM) : `["6e", "5e"]` → default: `"6e"`
- `preset` (ENUM) : `["simple", "standard"]` → default: `"standard"`
- `variant_id` (ENUM) : `["A", "B", "C"]` → default: `"A"`
- `seed` (INT) : **OBLIGATOIRE**

#### Outputs
- `variables` : dict avec données du tableau/pourcentage/vitesse/échelle, solution, étapes
- `meta` : exercise_type, difficulty, grade, variant_id
- **Pas de SVG** (svg_mode=NONE)
- **Solutions "prof" :** étapes numérotées + justifications

#### Dépendances
- **Templates :** Utilise templates DB avec variants (A, B, C)
- **RNG :** `safe_random_choice`, `safe_randrange` (via observability)
- **Variabilité :** Pools de formulations alternatives
- **Tables HTML :** Génère des tableaux HTML pour proportionnalité

#### Fallback existant
- ❌ Non explicite dans le générateur
- ✅ Fallback STATIC via pipeline P0

#### Points d'attention
- ⚠️ **Seed obligatoire** : peut causer des erreurs 422 si non fourni
- ✅ **Premium** : vérification offer nécessaire côté API
- ✅ **Solutions détaillées** : étapes numérotées pour prof

---

### 5. SIMPLIFICATION_FRACTIONS_V1

**Fichier :** `backend/generators/simplification_fractions_v1.py`  
**Clé :** `SIMPLIFICATION_FRACTIONS_V1`  
**Version :** 1.0.0  
**Statut Factory :** ✅ Enregistré

#### Métadonnées
- **Label :** Simplification de fractions
- **Description :** Simplifier des fractions à l'aide du PGCD
- **Niveaux :** CM2, 6e, 5e
- **Exercise Type :** `FRACTIONS`
- **SVG Mode :** `AUTO`
- **Supports Double SVG :** ✅ Oui

#### Chapitres utilisateurs (curriculum)
- Aucun chapitre ne référence explicitement ce générateur dans `curriculum_6e.json`

#### Inputs attendus
- `difficulty` (ENUM) : `["facile", "moyen", "difficile"]` → default: `"moyen"`
- `allow_negative` (BOOL) : default: `False`
- `max_denominator` (INT) : default: 60, min=6, max=500
- `force_reducible` (BOOL) : default: `True`
- `show_svg` (BOOL) : default: `True`

#### Outputs
- `variables` : dict avec fraction, fraction_reduite, pgcd, step1, step2, step3
- `figure_svg_enonce` : SVG avec droite graduée (optionnel)
- `figure_svg_solution` : SVG avec fraction réduite (optionnel)
- `meta` : exercise_type, svg_mode, difficulty

#### Dépendances
- **Templates :** Templates inline (`ENONCE_TEMPLATE`, `SOLUTION_TEMPLATE`)
- **RNG :** `safe_random_choice`, `safe_randrange` (via observability)
- **SVG :** `create_svg_wrapper` (via base_generator)
- **Math :** `math.gcd` pour PGCD

#### Fallback existant
- ❌ Non explicite dans le générateur
- ✅ Fallback STATIC via pipeline P0

#### Points d'attention
- ⚠️ **Templates inline** : pas de templates DB, utilise templates hardcodés
- ✅ **SVG optionnel** : peut désactiver SVG si `show_svg=False`

---

### 6. SIMPLIFICATION_FRACTIONS_V2

**Fichier :** `backend/generators/simplification_fractions_v2.py`  
**Clé :** `SIMPLIFICATION_FRACTIONS_V2`  
**Version :** 2.0.0  
**Statut Factory :** ✅ Enregistré  
**Statut Premium :** ⚠️ À vérifier (non explicitement marqué)

#### Métadonnées
- **Label :** Simplification de fractions (PREMIUM)
- **Description :** Simplifier des fractions à l'aide du PGCD avec variants pédagogiques, indices et feedback
- **Niveaux :** CM2, 6e, 5e
- **Exercise Type :** `FRACTIONS`
- **SVG Mode :** `AUTO`
- **Supports Double SVG :** ✅ Oui

#### Chapitres utilisateurs (curriculum)
- Aucun chapitre ne référence explicitement ce générateur dans `curriculum_6e.json`

#### Inputs attendus
- `difficulty` (ENUM) : `["facile", "moyen", "difficile"]` → default: `"moyen"`
- `variant_id` (ENUM) : `["A", "B", "C"]` → default: `"A"`
- `hint_level` (INT) : default: 0, min=0, max=3
- `allow_negative` (BOOL) : default: `False`
- `max_denominator` (INT) : default: 60, min=6, max=500
- `force_reducible` (BOOL) : default: `True`
- `show_svg` (BOOL) : default: `True`

#### Outputs
- `variables` : dict avec fraction, fraction_reduite, pgcd, step1, step2, step3, hint_display, method_explanation, wrong_simplification (variant C), diagnostic_explanation
- `figure_svg_enonce` : SVG avec droite graduée (optionnel)
- `figure_svg_solution` : SVG avec fraction réduite + flèche + encadré (optionnel)
- `meta` : exercise_type, svg_mode, difficulty, variant_id, hint_level

#### Dépendances
- **Templates :** Templates inline par variant (`ENONCE_TEMPLATE_A/B/C`, `SOLUTION_TEMPLATE_A/B/C`)
- **RNG :** `safe_random_choice`, `safe_randrange` (via observability)
- **SVG :** `create_svg_wrapper` (via base_generator)
- **Math :** `math.gcd` pour PGCD
- **Variants :** A (standard), B (guidé), C (diagnostic)

#### Fallback existant
- ❌ Non explicite dans le générateur
- ✅ Fallback STATIC via pipeline P0

#### Points d'attention
- ⚠️ **Templates inline** : pas de templates DB, utilise templates hardcodés
- ✅ **Variants pédagogiques** : A, B, C avec comportements différents
- ✅ **Indices gradués** : `hint_level` 0→3 pour guidage progressif
- ✅ **Feedback erreurs** : variant C pour diagnostic d'erreurs typiques
- ✅ **Non-régression V1** : si aucun nouveau paramètre, comportement V1 strictement inchangé

---

### 7. THALES_V1 (LEGACY)

**Fichier :** `backend/generators/thales_generator.py`  
**Clé :** `THALES_V1` (non enregistré dans Factory, utilisé par THALES_V2)  
**Version :** 1.0.0 (legacy)  
**Statut Factory :** ❌ Non enregistré (utilisé indirectement via THALES_V2)

#### Métadonnées
- **Label :** Agrandissements et Réductions (Legacy)
- **Description :** Générateur legacy utilisé par THALES_V2
- **Niveaux :** 6e
- **Exercise Type :** `AGRANDISSEMENT_REDUCTION` (via mapping)

#### Chapitres utilisateurs (curriculum)
- Utilisé indirectement via `THALES_V2` dans `6e_TESTS_DYN`

#### Inputs attendus
- `seed` (int) : pour reproductibilité
- `difficulty` (str) : `["facile", "moyen", "difficile"]`

#### Outputs
- `variables` : dict avec toutes les valeurs
- `results` : dict avec valeurs calculées
- `svg_params` : dict pour génération SVG
- `figure_svg_enonce` : SVG de la figure initiale
- `figure_svg_solution` : SVG de la figure agrandie/réduite

#### Dépendances
- **RNG :** `random.Random(seed)` local
- **SVG :** Génération SVG inline

#### Fallback existant
- ❌ Non explicite
- ✅ Fallback STATIC via pipeline P0

#### Points d'attention
- ⚠️ **Legacy** : non enregistré dans Factory, utilisé uniquement via THALES_V2
- ⚠️ **RNG global** : peut avoir des effets de bord (monkeypatch dans THALES_V2)

---

## 📊 TABLEAU RÉCAPITULATIF

| Générateur | Clé | Version | Factory | SVG | Chapitres | Seed Req | Fallback | Statut |
|------------|-----|---------|---------|-----|-----------|----------|----------|--------|
| THALES_V2 | `THALES_V2` | 2.0.0 | ✅ | ✅ | 1 | ❌ | ✅ | ⚠️ À évaluer |
| SYMETRIE_AXIALE_V2 | `SYMETRIE_AXIALE_V2` | 2.0.0 | ✅ | ✅ | 1 | ❌ | ✅ | ⚠️ À évaluer |
| CALCUL_NOMBRES_V1 | `CALCUL_NOMBRES_V1` | 1.0.0 | ✅ | ❌ | 3 | ✅ | ✅ | ⚠️ À évaluer |
| RAISONNEMENT_MULTIPLICATIF_V1 | `RAISONNEMENT_MULTIPLICATIF_V1` | 1.0.0 | ✅ | ❌ | 2 | ✅ | ✅ | ⚠️ À évaluer |
| SIMPLIFICATION_FRACTIONS_V1 | `SIMPLIFICATION_FRACTIONS_V1` | 1.0.0 | ✅ | ✅ | 0 | ❌ | ✅ | ⚠️ À évaluer |
| SIMPLIFICATION_FRACTIONS_V2 | `SIMPLIFICATION_FRACTIONS_V2` | 2.0.0 | ✅ | ✅ | 0 | ❌ | ✅ | ⚠️ À évaluer |
| THALES_V1 | `THALES_V1` | 1.0.0 | ❌ | ✅ | 0 (indirect) | ❌ | ✅ | ⚠️ Legacy |

**Légende :**
- **Factory :** Enregistré dans `GeneratorFactory`
- **SVG :** Génère des SVG (énoncé et/ou solution)
- **Chapitres :** Nombre de chapitres utilisant ce générateur dans `curriculum_6e.json`
- **Seed Req :** Seed obligatoire pour génération
- **Fallback :** Fallback STATIC disponible via pipeline P0

---

## 🔍 DÉPENDANCES COMMUNES

### Services backend
- `backend/services/template_renderer.py` : `render_template()` pour templates HTML
- `backend/services/tests_dyn_handler.py` : `format_dynamic_exercise()` pour formatage final
- `backend/services/exercise_persistence_service.py` : Stockage en DB
- `backend/generators/base_generator.py` : `BaseGenerator`, `create_svg_wrapper()`

### Observability
- `backend/observability.py` : `safe_random_choice()`, `safe_randrange()`, `get_request_context()`

### Pipeline de génération
- `backend/routes/exercises_routes.py` : `generate_exercise_with_fallback()` (P0)
- `backend/generators/factory.py` : `GeneratorFactory`, `generate_exercise()`

---

## ⚠️ POINTS D'ATTENTION GLOBAUX

### 1. Seed obligatoire
- **CALCUL_NOMBRES_V1** et **RAISONNEMENT_MULTIPLICATIF_V1** requièrent un `seed` obligatoire
- **Impact :** Erreur 422 si seed non fourni
- **Recommandation :** Générer seed automatiquement si absent

### 2. Templates inline vs DB
- **SIMPLIFICATION_FRACTIONS_V1/V2** : Templates inline (hardcodés)
- **Autres générateurs :** Templates DB (via `format_dynamic_exercise`)
- **Impact :** Incohérence dans la gestion des templates
- **Recommandation :** Migrer tous les templates vers DB

### 3. Monkeypatch RNG (THALES_V2)
- **Problème :** Monkeypatch de `random.choice` peut causer des effets de bord
- **Impact :** Comportement non déterministe si d'autres threads utilisent `random.choice`
- **Recommandation :** Utiliser RNG local uniquement

### 4. Générateurs non utilisés
- **SIMPLIFICATION_FRACTIONS_V1/V2** : Aucun chapitre ne les référence dans le curriculum
- **Impact :** Générateurs "morts" non testés en production
- **Recommandation :** Soit les activer, soit les désactiver

### 5. Fallback pipeline
- **Tous les générateurs :** Fallback STATIC disponible via `generate_exercise_with_fallback()`
- **Impact :** Aucun générateur ne gère explicitement ses propres erreurs
- **Recommandation :** Ajouter try/except dans chaque générateur + logs clairs

---

## 📝 PROCHAINES ÉTAPES

1. **Tests techniques systématiques** (Étape 2)
   - Génération simple pour chaque générateur
   - Sauvegarde dans "Mes exercices"
   - Réouverture depuis "Mes exercices"
   - Ajout à une fiche
   - Export PDF (Sujet + Corrigé)

2. **Classification PRODUIT** (Étape 3)
   - Classer en GOLD / AMÉLIORABLE / À DÉSACTIVER
   - Créer `docs/CLASSIFICATION_GENERATEURS.md`

3. **Sécurisation pipeline** (Étape 4)
   - Vérifier fallback DYNAMIC → STATIC
   - Ajouter logs `[GENERATOR_OK]` / `[GENERATOR_FAIL]`

4. **Nettoyage & garde-fous** (Étape 5)
   - Empêcher appel de générateurs classés 🔴
   - Ajouter assertions sur variables critiques

---

**Document généré automatiquement le :** 2025-01-XX  
**Dernière mise à jour :** 2025-01-XX




