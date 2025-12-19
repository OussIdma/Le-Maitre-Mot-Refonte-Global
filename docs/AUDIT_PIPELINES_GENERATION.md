# AUDIT COMPLET — PIPELINES DE GÉNÉRATION / CURRICULUM / ADMIN

**Date**: 2025-12-18  
**Type**: 🔍 Analyse architecturale (ZÉRO CODE)  
**Objectif**: Cartographier les flows, identifier les problèmes, proposer une simplification industrialisable

---

## 📊 RÉSUMÉ EXÉCUTIF

### Diagnostic global

Le système de génération d'exercices fonctionne, mais souffre d'un **manque de clarté architecturale** qui le rend :
- **Incompréhensible** : Les décisions sont implicites, l'ordre d'exécution n'est pas visible
- **Non déterministe** : Même configuration peut donner des résultats différents
- **Non industrialisable** : Impossible de confier à un admin non-technique
- **Source d'erreurs silencieuses** : Les incohérences ne sont pas détectées à la configuration

### Problèmes identifiés

**4 ambiguïtés fonctionnelles** (impact utilisateur direct):
1. **"Disponible" ≠ "génère correctement"** → élèves obtiennent des erreurs
2. **Sélection admin ≠ comportement réel** → admins confus sur le comportement
3. **Statique vs dynamique flou dans l'UX** → admins ne savent pas ce qu'ils créent
4. **Sources de vérité multiples et contradictoires** → comportement non déterministe

**4 incohérences techniques** (impact maintenance):
1. **`exercise_types` curriculum vs `MathExerciseType` enum** → erreurs ou fallback silencieux
2. **Mapping `generator_key` → `exercise_type` non unifié** → sync curriculum incompatible
3. **Priorité DB > Curriculum pour génération, mais Curriculum > DB pour disponibilité** → incohérence
4. **Cache mémoire non invalidé après modifs DB** → données obsolètes

**3 points legacy problématiques** (impact évolutivité):
1. **Fichiers Python comme source de vérité** → désynchronisation possible
2. **Intercepts hardcodés** → impossible d'ajouter de nouveaux chapitres "spéciaux"
3. **Mapping chapitre → types hardcodé** → maintenance difficile

### Risques si rien n'est changé

| Risque | Probabilité | Gravité | Impact |
|--------|-------------|---------|--------|
| **Impossibilité d'industrialiser** | ÉLEVÉE | BLOQUANT | Admins ne peuvent pas utiliser le système |
| **Dégradation UX élève** | MOYENNE | CRITIQUE | Élèves obtiennent des erreurs, perte de confiance |
| **Dette technique croissante** | ÉLEVÉE | ÉLEVÉE | Maintenance de plus en plus difficile |
| **Impossibilité d'ouvrir aux enseignants** | ÉLEVÉE | MOYENNE | Système trop complexe pour non-techniciens |

### Recommandation principale

**✅ OPTION 1 — Pipeline explicite au niveau chapitre**

**Principe**: Ajouter un champ `pipeline: "SPEC" | "TEMPLATE" | "MIXED"` au niveau chapitre pour forcer un choix explicite.

**Avantages**:
- ✅ Résout toutes les ambiguïtés fonctionnelles
- ✅ Résout toutes les incohérences techniques
- ✅ Réduit les risques legacy
- ✅ Industrialisable (règles claires, déterministe, testable)

**Coût**: 1-2 jours (migration DB, backend, frontend, tests)

**Alternative rejetée**: Routage par capacité détectée (non déterministe, confusion)

---

## 📋 TABLE DES MATIÈRES

1. [Cartographie "Qui appelle quoi"](#1-cartographie-qui-appelle-quoi)
2. [Sources de vérité](#2-sources-de-vérité)
3. [Problèmes constatés](#3-problèmes-constatés)
4. [Options de simplification](#4-options-de-simplification)
5. [Plan de migration](#5-plan-de-migration)
6. [TODO list priorisée](#6-todo-list-priorisée)
7. [Ambiguïtés fonctionnelles identifiées](#10-ambiguïtés-fonctionnelles-identifiées)
8. [Incohérences techniques identifiées](#11-incohérences-techniques-identifiées)
9. [Points legacy problématiques](#12-points-legacy-problématiques)
10. [Risques si rien n'est changé](#13-risques-si-rien-nest-changé)
11. [Recommandation principale](#14-recommandation-principale)
12. [Conclusion](#15-conclusion)

---

## 1. CARTOGRAPHIE "QUI APPELLE QUOI"

### SCHÉMA FLOW GLOBAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GÉNÉRATION ÉLÈVE (PARCOURS A)                       │
└─────────────────────────────────────────────────────────────────────────────┘

UI (ExerciseGeneratorPage.js)
  │
  ├─ POST /api/v1/exercises/generate
  │  Payload: {code_officiel, difficulte, offer, seed}
  │
  ▼
Backend (exercises_routes.py::generate_exercise)
  │
  ├─ [1] is_gm07_request(code_officiel)?
  │  │  YES → gm07_handler → data/gm07_exercises.py (STATIQUE)
  │  │  NO  ↓
  │  │
  │  ├─ [2] is_gm08_request(code_officiel)?
  │  │  │  YES → gm08_handler → data/gm08_exercises.py (STATIQUE)
  │  │  │  NO  ↓
  │  │  │
  │  │  ├─ [3] is_tests_dyn_request(code_officiel)?
  │  │  │  │  YES → tests_dyn_handler → data/tests_dyn_exercises.py (DYNAMIQUE)
  │  │  │  │  NO  ↓
  │  │  │  │
  │  │  │  ├─ [4] has_exercises_in_db(chapter_code)?
  │  │  │  │  │  YES → has_dynamic_exercises?
  │  │  │  │  │  │  YES → format_dynamic_exercise() → DB exercises (DYNAMIQUE)
  │  │  │  │  │  │  NO  ↓
  │  │  │  │  │  NO  ↓
  │  │  │  │  │
  │  │  │  │  └─ [5] Pipeline STATIQUE
  │  │  │  │     │
  │  │  │  │     ├─ get_chapter_by_official_code(code_officiel)
  │  │  │  │     │  → curriculum_6e.json (CurriculumChapter)
  │  │  │  │     │
  │  │  │  │     ├─ Extract: curriculum_chapter.exercise_types
  │  │  │  │     │  → Convert: exercise_types → MathExerciseType enum
  │  │  │  │     │
  │  │  │  │     └─ MathGenerationService.generate_math_exercise_specs_with_types()
  │  │  │  │        → Génération spec-based (Python pur, pas de DB)
  │
  └─ Output: Exercice formaté (HTML, SVG, solution)


┌─────────────────────────────────────────────────────────────────────────────┐
│                    ADMIN CURRICULUM (PARCOURS B)                             │
└─────────────────────────────────────────────────────────────────────────────┘

UI (Curriculum6eAdminPage.js)
  │
  ├─ Formulaire: code_officiel, libelle, domaine, exercise_types, ...
  │
  ├─ POST /api/admin/curriculum/6e/chapters
  │  ou PUT /api/admin/curriculum/6e/chapters/{code_officiel}
  │
  ▼
Backend (admin_curriculum_routes.py)
  │
  ├─ create_chapter() / update_chapter()
  │  │
  │  ▼
  │  CurriculumPersistenceService
  │  │
  │  ├─ Validation: code_officiel unique
  │  │
  │  ├─ Insert/Update: MongoDB collection "curriculum_chapters"
  │  │
  │  ├─ Sync: _sync_to_json() → curriculum_6e.json
  │  │
  │  └─ Reload: _reload_curriculum_index() (cache mémoire)
  │
  └─ Output: Chapitre créé/modifié


┌─────────────────────────────────────────────────────────────────────────────┐
│                      ADMIN EXERCISES (PARCOURS C)                            │
└─────────────────────────────────────────────────────────────────────────────┘

UI (ChapterExercisesAdminPage.js)
  │
  ├─ Formulaire: family, exercise_type, is_dynamic, generator_key, ...
  │
  ├─ POST /api/admin/chapters/{chapter_code}/exercises
  │  ou PUT /api/admin/chapters/{chapter_code}/exercises/{id}
  │
  ▼
Backend (admin_exercises_routes.py)
  │
  ├─ create_exercise() / update_exercise()
  │  │
  │  ▼
  │  ExercisePersistenceService
  │  │
  │  ├─ Validation: ExerciseCreateRequest (Pydantic)
  │  │
  │  ├─ Insert/Update: MongoDB collection "admin_exercises"
  │  │
  │  ├─ Sync: _sync_to_python_file() → data/gm07_exercises.py, etc.
  │  │
  │  └─ Auto-sync Curriculum (NON-BLOQUANT)
  │     │
  │     ▼
  │     CurriculumSyncService.sync_chapter_to_curriculum()
  │     │
  │     ├─ Extract: exercise_types depuis exercices DB
  │     │  - Dynamique: generator_key → exercise_type (mapping)
  │     │  - Statique: exercise_type directement
  │     │
  │     └─ Create/Update: chapitre dans curriculum_chapters
  │        (fusion additive: ne supprime pas exercise_types existants)
  │
  └─ Output: Exercice créé/modifié (+ sync curriculum si succès)
```

### PARCOURS A — Génération côté élève (frontend "Generate")

#### Flow complet (UI → Backend → Pipeline → Output)

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: ExerciseGeneratorPage.js                              │
│ - Utilisateur sélectionne chapitre (code_officiel)              │
│ - Clic "Générer"                                                 │
│ - Appel: POST /api/v1/exercises/generate                        │
│   Payload: {code_officiel, difficulte, offer, seed}             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: routes/exercises_routes.py::generate_exercise()        │
│ Ligne 551                                                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ DÉCISION PIPELINE (ordre de priorité)                           │
│                                                                  │
│ 1. INTERCEPT GM07 (ligne 566)                                    │
│    Condition: is_gm07_request(code_officiel)                    │
│    → Pipeline: gm07_handler::generate_gm07_exercise()          │
│    → Source: data/gm07_exercises.py (fichier Python)          │
│    → Output: Exercice figé depuis liste statique                │
│                                                                  │
│ 2. INTERCEPT GM08 (ligne 628)                                    │
│    Condition: is_gm08_request(code_officiel)                    │
│    → Pipeline: gm08_handler::generate_gm08_exercise()           │
│    → Source: data/gm08_exercises.py (fichier Python)            │
│    → Output: Exercice figé depuis liste statique                 │
│                                                                  │
│ 3. INTERCEPT TESTS_DYN (ligne 688)                              │
│    Condition: is_tests_dyn_request(code_officiel)               │
│    → Pipeline: tests_dyn_handler::generate_tests_dyn_exercise() │
│    → Source: data/tests_dyn_exercises.py (fichier Python)       │
│    → Output: Exercice dynamique (template + générateur)          │
│                                                                  │
│ 4. VÉRIFICATION EXERCICES DYNAMIQUES EN DB (ligne 738)          │
│    Condition: chapter_code_for_db existe                        │
│    → Vérifie: sync_service.has_exercises_in_db()                │
│    → Si exercices dynamiques trouvés:                            │
│      → Pipeline: tests_dyn_handler::format_dynamic_exercise()   │
│      → Source: collection MongoDB "exercises"                    │
│      → Output: Exercice dynamique depuis DB                     │
│    → Sinon: continue vers pipeline statique                     │
│                                                                  │
│ 5. PIPELINE STATIQUE (ligne 814+)                               │
│    Condition: Pas intercepté + pas d'exercices dynamiques DB   │
│    → Résolution: get_chapter_by_official_code()                  │
│    → Source: curriculum_6e.json (via curriculum/loader.py)      │
│    → Extraction: curriculum_chapter.exercise_types               │
│    → Conversion: exercise_types → MathExerciseType enum         │
│    → Pipeline: MathGenerationService::generate_math_exercise_  │
│                specs_with_types()                                │
│    → Source: Génération spec-based (Python pur, pas de DB)      │
│    → Output: MathExerciseSpec → Exercice formaté                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Ordre de décision critique (le problème fondamental)

**Le problème** : L'ordre de vérification détermine quel pipeline est utilisé, mais cet ordre n'est **pas visible** pour l'admin.

**Ordre actuel** (déterminé par le code, ligne 566-814) :

1. **Intercepts hardcodés** (priorité absolue)
   - GM07 → Pipeline figé (fichier Python)
   - GM08 → Pipeline figé (fichier Python)
   - TESTS_DYN → Pipeline dynamique (fichier Python)

2. **Vérification DB exercices dynamiques** (priorité haute)
   - Si exercices dynamiques trouvés → Pipeline dynamique (DB)
   - Sinon → Continue

3. **Pipeline statique** (fallback)
   - Utilise `exercise_types` du curriculum
   - Convertit vers `MathExerciseType` enum
   - Génère via `MathGenerationService`

**Conséquence** : Un chapitre peut avoir `exercise_types: ["AGRANDISSEMENT_REDUCTION"]` dans le curriculum, mais si des exercices dynamiques existent en DB, le pipeline dynamique est utilisé (priorité DB > curriculum).

**Fichier**: `backend/routes/exercises_routes.py`

**Lignes clés**:
- **566**: `if is_gm07_request(request.code_officiel)` → Handler GM07
- **628**: `if is_gm08_request(request.code_officiel)` → Handler GM08
- **688**: `if is_tests_dyn_request(request.code_officiel)` → Handler TESTS_DYN
- **738-812**: Vérification exercices dynamiques en DB (NOUVEAU, ajouté récemment)
- **814+**: Pipeline statique (MathGenerationService)

**Fonctions de détection**:
- `is_gm07_request()`: `backend/services/gm07_handler.py:28` → `code_officiel.upper() == "6E_GM07"`
- `is_gm08_request()`: `backend/services/gm08_handler.py:28` → `code_officiel.upper() == "6E_GM08"`
- `is_tests_dyn_request()`: `backend/services/tests_dyn_handler.py:41` → `code_officiel.upper() in ["6E_TESTS_DYN", "TESTS_DYN"]`

**Vérification exercices dynamiques DB** (ligne 760-812):
```python
# Normaliser chapter_code
chapter_code_for_db = request.code_officiel.upper().replace("-", "_")

# Vérifier si exercices existent
has_exercises = await sync_service.has_exercises_in_db(chapter_code_for_db)
if has_exercises:
    exercises = await exercise_service.get_exercises(...)
    dynamic_exercises = [ex for ex in exercises if ex.get("is_dynamic") is True]
    
    if has_dynamic_exercises:
        # Pipeline DYNAMIQUE
        selected_exercise = random.choice(dynamic_exercises)
        dyn_exercise = format_dynamic_exercise(...)
        return dyn_exercise
```

**Pipeline statique** (ligne 814+):
- Résolution `code_officiel` → `CurriculumChapter` via `get_chapter_by_official_code()`
- Extraction `curriculum_chapter.exercise_types` (liste de strings)
- Conversion vers `MathExerciseType` enum (ligne 863-869)
- Génération via `MathGenerationService.generate_math_exercise_specs_with_types()`
- **Source**: Pas de DB, génération pure Python (spec-based)

#### Quand `generators[]` du chapitre est utilisé

**Fichier**: `backend/routes/exercises_routes.py`, ligne 844-906

**Condition**: Si `curriculum_chapter.exercise_types` est non vide

**Utilisation**:
1. **Filtrage premium** (ligne 847-858): Exclut `DUREES_PREMIUM` si `offer != "pro"`
2. **Conversion vers enum** (ligne 863-869): `hasattr(MathExerciseType, et)` → `MathExerciseType[et]`
3. **Génération** (ligne 931-936): `_math_service.generate_math_exercise_specs_with_types(exercise_types_override)`

**⚠️ PROBLÈME IDENTIFIÉ**: Si `exercise_types` contient des valeurs qui ne sont PAS dans `MathExerciseType` enum (ex: `"AGRANDISSEMENT_REDUCTION"`), elles sont ignorées (ligne 867) ou lève une erreur si TOUS sont invalides (ligne 882-901).

#### Quand la DB `exercises` est utilisée

**Fichier**: `backend/routes/exercises_routes.py`, ligne 760-812

**Condition**: 
- `chapter_code_for_db` existe (normalisé depuis `code_officiel`)
- `sync_service.has_exercises_in_db(chapter_code_for_db)` retourne `True`
- Au moins un exercice avec `is_dynamic == True` existe

**Utilisation**:
- Récupération: `exercise_service.get_exercises(chapter_code, offer, difficulty)`
- Filtrage: `[ex for ex in exercises if ex.get("is_dynamic") is True]`
- Sélection: `random.choice(dynamic_exercises)` (avec seed)
- Génération: `format_dynamic_exercise(exercise_template, timestamp, seed)`

**⚠️ PROBLÈME IDENTIFIÉ**: Cette vérification se fait APRÈS les intercepts GM07/GM08/TESTS_DYN, mais AVANT le pipeline statique. Si un chapitre a `exercise_types` dans le curriculum ET des exercices dynamiques en DB, le pipeline dynamique est utilisé (priorité DB > curriculum).

#### Qu'est-ce qui décide "dynamique vs statique"

**Décision actuelle** (ordre de priorité):

1. **Hardcodé**: GM07, GM08, TESTS_DYN → Pipeline dédié (statique pour GM07/GM08, dynamique pour TESTS_DYN)
2. **DB**: Si exercices dynamiques en DB → Pipeline dynamique (`format_dynamic_exercise`)
3. **Curriculum**: Si `exercise_types` dans curriculum → Pipeline statique (`MathGenerationService`)

**⚠️ PROBLÈME IDENTIFIÉ**: Un chapitre peut avoir `exercise_types: ["AGRANDISSEMENT_REDUCTION"]` dans le curriculum, mais si des exercices dynamiques existent en DB, le pipeline dynamique est utilisé. L'admin peut donc sélectionner un générateur dans le curriculum, mais la génération utilise un autre pipeline.

---

### PARCOURS B — Admin Curriculum (création/édition chapitre)

#### Flow complet

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: Curriculum6eAdminPage.js                              │
│ - Clic "Créer chapitre" ou "Modifier"                           │
│ - Formulaire: code_officiel, libellé, domaine, statut,          │
│   exercise_types (générateurs), schema_requis, etc.             │
│ - Appel: POST /api/admin/curriculum/6e/chapters                 │
│   ou PUT /api/admin/curriculum/6e/chapters/{code_officiel}      │
│   Payload: {code_officiel, libelle, domaine, exercise_types,   │
│             schema_requis, difficulte_min, difficulte_max,      │
│             statut, tags}                                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: routes/admin_curriculum_routes.py                      │
│ - create_chapter() (ligne 385)                                  │
│ - update_chapter() (ligne 429)                                  │
│ - Service: CurriculumPersistenceService                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ SERVICE: curriculum_persistence_service.py                      │
│ - create_chapter() (ligne 188)                                  │
│   → Validation: code_officiel unique                            │
│   → Insertion: collection MongoDB "curriculum_chapters"          │
│   → Sync: _sync_to_json() → curriculum_6e.json                 │
│   → Reload: _reload_curriculum_index() (cache mémoire)          │
│                                                                  │
│ - update_chapter() (ligne 230)                                  │
│   → Update: collection MongoDB                                  │
│   → Sync: _sync_to_json() → curriculum_6e.json                 │
│   → Reload: _reload_curriculum_index()                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ SOURCES DE VÉRITÉ                                                │
│ - MongoDB: collection "curriculum_chapters" (source principale)  │
│ - Fichier: curriculum/curriculum_6e.json (synchronisé)           │
│ - Cache: CurriculumIndex (en mémoire, rechargé après modif)     │
└─────────────────────────────────────────────────────────────────┘
```

#### Champs stockés

**Fichier**: `backend/services/curriculum_persistence_service.py`, modèle `ChapterCreateRequest` (ligne 50-62)

**Champs**:
- `code_officiel`: String (ex: "6e_N08")
- `libelle`: String (ex: "Fractions")
- `domaine`: String (ex: "Nombres et calculs")
- `chapitre_backend`: String (ex: "Fractions") - nom pour MathGenerationService
- `exercise_types`: `List[str]` (ex: `["CALCUL_FRACTIONS", "FRACTION_REPRESENTATION"]`)
- `schema_requis`: Boolean
- `difficulte_min`: Integer (1-3)
- `difficulte_max`: Integer (1-3)
- `statut`: String ("prod", "beta", "hidden")
- `tags`: `List[str]`
- `contexts`: `List[str]` (optionnel)

**Stockage**:
- **MongoDB**: Collection `curriculum_chapters` (ligne 216)
- **Fichier**: `curriculum/curriculum_6e.json` (ligne 219, `_sync_to_json()`)
- **Cache**: `CurriculumIndex` en mémoire (ligne 222, `_reload_curriculum_index()`)

#### Comment est construit `hasGenerators` / "indisponible"

**Fichier**: `backend/curriculum/loader.py`, fonction `get_catalog()` (ligne 325)

**Flow**:
1. **Source principale**: `chapter.exercise_types` depuis `CurriculumIndex` (ligne 399)
2. **Enrichissement DB** (ligne 404-429):
   - Si `db` fourni → vérifie `sync_service.has_exercises_in_db()`
   - Si exercices existent → extrait `exercise_types_from_db` via `sync_service.get_exercise_types_from_db()`
   - Fusion: `set(generators_from_curriculum) | exercise_types_from_db` (ligne 411)
3. **Frontend** (ligne 219): `hasGenerators: ch.generators.length > 0`
4. **Affichage** (ligne 746-748): Si `!item.hasGenerators` → badge "indispo"

**⚠️ PROBLÈME IDENTIFIÉ**: 
- Si `exercise_types` est vide dans le curriculum ET aucun exercice en DB → `generators: []` → `hasGenerators: false` → "indisponible"
- Si exercices en DB mais `exercise_types` vide dans curriculum → enrichissement DB → `hasGenerators: true` → disponible
- **Incohérence**: Le chapitre peut être "disponible" mais utiliser le pipeline statique si `exercise_types` est rempli dans le curriculum (même si exercices dynamiques en DB)

---

### PARCOURS C — Admin Exercises (création/édition exercice)

#### Flow complet

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: ChapterExercisesAdminPage.js                          │
│ - Sélection chapitre (chapterCode)                              │
│ - Clic "Créer exercice" ou "Modifier"                           │
│ - Formulaire: family, exercise_type, difficulty, offer,         │
│   is_dynamic, generator_key, enonce_template_html, etc.          │
│ - Appel: POST /api/admin/chapters/{chapter_code}/exercises       │
│   ou PUT /api/admin/chapters/{chapter_code}/exercises/{id}      │
│   Payload: {family, exercise_type, difficulty, offer,           │
│             is_dynamic, generator_key, enonce_template_html,    │
│             solution_template_html, template_variants, ...}      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: routes/admin_exercises_routes.py                       │
│ - create_exercise() (ligne 169)                                 │
│ - update_exercise() (ligne 215)                                 │
│ - Service: ExercisePersistenceService                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ SERVICE: exercise_persistence_service.py                        │
│ - create_exercise() (ligne ~600+)                               │
│   → Validation: ExerciseCreateRequest (Pydantic)               │
│   → Insertion: collection MongoDB "admin_exercises"              │
│   → Sync: _sync_to_python_file() (génère fichier Python)        │
│                                                                  │
│ - update_exercise() (ligne ~700+)                               │
│   → Update: collection MongoDB                                  │
│   → Sync: _sync_to_python_file()                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ AUTO-SYNC CURRICULUM (ligne 183-194)                            │
│ - Service: CurriculumSyncService                                │
│ - Appel: sync_chapter_to_curriculum(chapter_code)               │
│ - Extraction: exercise_types depuis exercices (DB)              │
│ - Création/Mise à jour: chapitre dans curriculum                │
│ - Source: collection "exercises"                                │
│ - Cible: collection "curriculum_chapters" + curriculum_6e.json   │
└─────────────────────────────────────────────────────────────────┘
```

#### Où vont les exercices

**Fichier**: `backend/services/exercise_persistence_service.py`

**Collection MongoDB**: `admin_exercises` (ligne 22, constante `EXERCISES_COLLECTION`)

**Modèle**: `ExerciseCreateRequest` (ligne 58-107)

**Champs stockés**:
- `chapter_code`: String (ex: "6E_G07_DYN")
- `id`: Integer (unique par chapitre)
- `family`: String (ex: "CONVERSION")
- `exercise_type`: Optional[String] (ex: "LECTURE_HORLOGE") - pour exercices statiques
- `difficulty`: String ("facile", "moyen", "difficile")
- `offer`: String ("free", "pro")
- `is_dynamic`: Boolean
- `generator_key`: Optional[String] (ex: "THALES_V1") - pour exercices dynamiques
- `enonce_html`: Optional[String] - pour exercices statiques
- `solution_html`: Optional[String] - pour exercices statiques
- `enonce_template_html`: Optional[String] - pour exercices dynamiques
- `solution_template_html`: Optional[String] - pour exercices dynamiques
- `template_variants`: Optional[List[TemplateVariant]] - variantes de templates
- `variables`: Optional[Dict] - variables pour SVG
- `svg_enonce_brief`: Optional[String]
- `svg_solution_brief`: Optional[String]

**Synchronisation**:
- **MongoDB → Fichier Python**: `_sync_to_python_file()` (ligne 305) génère `data/gm07_exercises.py`, `data/gm08_exercises.py`, etc. (pour compatibilité avec handlers)

#### Comment `is_dynamic/generator_key/templates/template_variants` sont interprétés

**Fichier**: `backend/services/tests_dyn_handler.py`, fonction `format_dynamic_exercise()` (ligne 78)

**Interprétation**:
1. **`is_dynamic`**: Flag principal (ligne 128 dans `extract_exercise_types_from_chapter`)
   - Si `True` → utilise `generator_key` pour extraire `exercise_type`
   - Si `False` → utilise `exercise_type` directement

2. **`generator_key`**: Clé du générateur Factory (ex: "THALES_V1", "SYMETRIE_AXIALE_V2")
   - Mappé vers `exercise_type` via `_get_exercise_type_from_generator()` (ligne 131)
   - Mapping: `backend/services/curriculum_sync_service.py:22-29` (GENERATOR_TO_EXERCISE_TYPE)

3. **`enonce_template_html` / `solution_template_html`**: Templates avec placeholders `{{variable}}`
   - Rendu via `render_template()` (ligne ~300+ dans `format_dynamic_exercise`)
   - Variables générées par le générateur (ex: `THALES_V1` génère `coefficient`, `figure_type`, etc.)

4. **`template_variants`**: Liste de variantes de templates (optionnel)
   - Si présent → devient la SEULE source de vérité (ligne 210-298)
   - Sélection via `choose_template_variant()` (ligne 293)
   - Détection chapitre template-based via `is_chapter_template_based()` (ligne 251)

**⚠️ PROBLÈME IDENTIFIÉ**: 
- `template_variants` nécessite que le chapitre soit "template-based" (détecté automatiquement ou handler dédié)
- Si chapitre spec-based (ex: 6e_G07 sans handler) → erreur `VARIANTS_NOT_SUPPORTED` (ligne 256-271)
- Mais l'admin peut créer un exercice avec `template_variants` sans savoir si le chapitre est compatible

#### Comment (et si) ça synchronise le curriculum

**Fichier**: `backend/routes/admin_exercises_routes.py`, ligne 183-194

**Auto-sync**:
- **Déclenchement**: Après création/modification d'exercice (ligne 184)
- **Service**: `CurriculumSyncService.sync_chapter_to_curriculum()` (ligne 184)
- **Extraction**: `extract_exercise_types_from_chapter()` (ligne 96-153 dans `curriculum_sync_service.py`)
  - Exercices dynamiques → `generator_key` → `exercise_type` via mapping
  - Exercices statiques → `exercise_type` directement
- **Création/Mise à jour**: Chapitre dans `curriculum_chapters` (ligne 144-180)
- **Fusion**: Additive (ne supprime pas les `exercise_types` existants, ligne 150-151)

**⚠️ PROBLÈME IDENTIFIÉ**: 
- La sync est non-bloquante (ligne 189-194): si elle échoue, l'exercice est quand même créé
- La sync extrait les `exercise_types` depuis les exercices, mais ne garantit pas que ces `exercise_types` correspondent aux `MathExerciseType` enum utilisés par le pipeline statique
- Exemple: `generator_key: "THALES_V1"` → `exercise_type: "AGRANDISSEMENT_REDUCTION"` (via mapping), mais `"AGRANDISSEMENT_REDUCTION"` n'est pas dans `MathExerciseType` enum → le pipeline statique ne peut pas l'utiliser

---

## 2. SOURCES DE VÉRITÉ

### Tableau "Source de vérité"

| **Qu'est-ce qui fait foi pour...** | **Fichier** | **Fonction/Collection** | **Condition** |
|-------------------------------------|-------------|-------------------------|---------------|
| **Disponibilité d'un chapitre** | `backend/curriculum/loader.py` | `get_catalog()` (ligne 325) | `ch.generators.length > 0` (frontend ligne 219) OU enrichissement DB si exercices existent (ligne 406-411) |
| **Liste des générateurs possibles** | `backend/services/curriculum_persistence_service.py` | `get_available_generators()` (ligne 335) | Fusion: `MathExerciseType` enum + `GeneratorFactory.list_all()` → mapping `GENERATOR_TO_EXERCISE_TYPE` |
| **Choix du pipeline (spec-based vs template-based)** | `backend/routes/exercises_routes.py` | `generate_exercise()` (ligne 551) | Ordre: 1) Intercepts (GM07/GM08/TESTS_DYN), 2) Vérification DB exercices dynamiques (ligne 760), 3) Pipeline statique (ligne 814+) |
| **Génération effective d'un exercice** | **Multiple** | Voir détails ci-dessous | Dépend du pipeline choisi |
| **Mix statique + dynamique dans un même chapitre** | **NON SUPPORTÉ** | - | Un chapitre utilise UN SEUL pipeline à la fois (celui détecté en premier) |

#### Détails "Génération effective d'un exercice"

**Pipeline GM07**:
- **Fichier**: `backend/services/gm07_handler.py`
- **Fonction**: `generate_gm07_exercise()` (ligne ~50+)
- **Source**: `data/gm07_exercises.py` (fichier Python, liste statique)
- **Sélection**: `get_random_gm07_exercise(offer, difficulty, seed)`

**Pipeline GM08**:
- **Fichier**: `backend/services/gm08_handler.py`
- **Fonction**: `generate_gm08_exercise()` (ligne ~50+)
- **Source**: `data/gm08_exercises.py` (fichier Python, liste statique)
- **Sélection**: `get_random_gm08_exercise(offer, difficulty, seed)`

**Pipeline TESTS_DYN**:
- **Fichier**: `backend/services/tests_dyn_handler.py`
- **Fonction**: `generate_tests_dyn_exercise()` (ligne ~250+)
- **Source**: `data/tests_dyn_exercises.py` (fichier Python, templates)
- **Génération**: `format_dynamic_exercise()` (ligne 78) → `generate_dynamic_exercise(generator_key, seed, difficulty)`

**Pipeline Dynamique (DB)**:
- **Fichier**: `backend/routes/exercises_routes.py` + `backend/services/tests_dyn_handler.py`
- **Fonction**: `format_dynamic_exercise()` (ligne 790)
- **Source**: Collection MongoDB `admin_exercises` (ligne 767)
- **Génération**: Template + générateur Factory (ligne 790-794)

**Pipeline Statique (MathGenerationService)**:
- **Fichier**: `backend/services/math_generation_service.py`
- **Fonction**: `generate_math_exercise_specs_with_types()` (ligne 64)
- **Source**: Génération pure Python (pas de DB, pas de fichiers)
- **Génération**: Spec mathématique structurée → conversion vers format Exercise

---

## 3. PROBLÈMES CONSTATÉS

### H1 — Si un chapitre a `generators[]` non vide, la génération utilise le pipeline legacy spec-based et ignore les exercices dynamiques DB

**✅ CONFIRMÉ (avec nuance)**

**Preuve**:
- **Fichier**: `backend/routes/exercises_routes.py`, ligne 738-812
- **Ordre de vérification**:
  1. Vérification exercices dynamiques DB (ligne 760) → **AVANT** résolution curriculum
  2. Résolution curriculum (ligne 821) → **APRÈS** vérification DB
  3. Pipeline statique (ligne 997+) → **APRÈS** résolution curriculum

**Comportement actuel**:
- Si exercices dynamiques en DB → Pipeline dynamique utilisé (ligne 802)
- Si pas d'exercices dynamiques en DB → Pipeline statique utilisé (ligne 997+)
- **⚠️ PROBLÈME**: Si un chapitre a `exercise_types: ["AGRANDISSEMENT_REDUCTION"]` dans le curriculum mais pas d'exercices dynamiques en DB, le pipeline statique est utilisé, mais `"AGRANDISSEMENT_REDUCTION"` n'est pas dans `MathExerciseType` enum → erreur ou fallback silencieux

**Nuance**: La vérification DB se fait AVANT le pipeline statique, donc si des exercices dynamiques existent, ils sont utilisés. Mais si le curriculum a `exercise_types` rempli et pas d'exercices dynamiques en DB, le pipeline statique est utilisé.

---

### H2 — `exercise_types` / `generators` / `generator_key` ont des noms proches mais ne pointent pas vers la même chose (legacy vs dyn)

**✅ CONFIRMÉ**

**Preuve**:

1. **`exercise_types` (curriculum)**:
   - **Fichier**: `backend/curriculum/loader.py`, modèle `CurriculumChapter` (ligne 53)
   - **Type**: `List[str]` (ex: `["CALCUL_FRACTIONS", "FRACTION_REPRESENTATION"]`)
   - **Usage**: Pipeline statique → conversion vers `MathExerciseType` enum (ligne 863-869 dans `exercises_routes.py`)
   - **Source**: `curriculum_6e.json` ou MongoDB `curriculum_chapters`

2. **`generators` (catalogue frontend)**:
   - **Fichier**: `backend/curriculum/loader.py`, `get_catalog()` (ligne 438)
   - **Type**: `List[str]` (alias de `exercise_types` du curriculum, enrichi depuis DB)
   - **Usage**: Frontend → `hasGenerators: ch.generators.length > 0` (ligne 219)
   - **Source**: `chapter.exercise_types` (curriculum) + enrichissement DB

3. **`generator_key` (exercices dynamiques)**:
   - **Fichier**: `backend/services/exercise_persistence_service.py`, modèle `ExerciseCreateRequest` (ligne 90)
   - **Type**: `Optional[str]` (ex: `"THALES_V1"`, `"SYMETRIE_AXIALE_V2"`)
   - **Usage**: Pipeline dynamique → mapping vers `exercise_type` via `GENERATOR_TO_EXERCISE_TYPE` (ligne 131 dans `curriculum_sync_service.py`)
   - **Source**: Collection MongoDB `admin_exercises`

4. **`exercise_type` (exercices statiques)**:
   - **Fichier**: `backend/services/exercise_persistence_service.py`, modèle `ExerciseCreateRequest` (ligne 65)
   - **Type**: `Optional[str]` (ex: `"LECTURE_HORLOGE"`)
   - **Usage**: Pipeline statique (si exercice statique) ou extraction pour sync curriculum
   - **Source**: Collection MongoDB `admin_exercises`

**Mapping**:
- `generator_key: "THALES_V1"` → `exercise_type: "AGRANDISSEMENT_REDUCTION"` (via `GENERATOR_TO_EXERCISE_TYPE`, ligne 25 dans `curriculum_sync_service.py`)
- `generator_key: "SYMETRIE_AXIALE_V2"` → `exercise_type: "SYMETRIE_AXIALE"` (ligne 23)
- Mais `"AGRANDISSEMENT_REDUCTION"` n'est PAS dans `MathExerciseType` enum → ne peut pas être utilisé par le pipeline statique

**⚠️ PROBLÈME**: Confusion entre:
- `exercise_types` du curriculum (pour pipeline statique, doit être dans `MathExerciseType` enum)
- `exercise_type` extrait depuis `generator_key` (pour pipeline dynamique, peut être différent, ex: `"AGRANDISSEMENT_REDUCTION"`)

---

### H3 — La "disponibilité" dépend du curriculum/catalogue, pas des exercices créés en DB

**⚠️ PARTIELLEMENT CONFIRMÉ (enrichissement DB récent)**

**Preuve**:
- **Fichier**: `backend/curriculum/loader.py`, `get_catalog()` (ligne 325)
- **Source principale**: `chapter.exercise_types` depuis `CurriculumIndex` (ligne 399)
- **Enrichissement DB** (ligne 404-429): Si exercices existent en DB, extraction `exercise_types_from_db` et fusion avec curriculum
- **Frontend**: `hasGenerators: ch.generators.length > 0` (ligne 219)

**Comportement actuel**:
- Si `exercise_types` vide dans curriculum ET pas d'exercices en DB → `generators: []` → "indisponible"
- Si `exercise_types` vide dans curriculum MAIS exercices en DB → enrichissement DB → `generators: [...]` → disponible
- Si `exercise_types` rempli dans curriculum → `generators: [...]` → disponible (même sans exercices en DB)

**⚠️ PROBLÈME**: 
- Un chapitre peut être "disponible" avec `exercise_types` dans le curriculum, mais si ces `exercise_types` ne sont pas dans `MathExerciseType` enum, le pipeline statique échoue
- Un chapitre peut être "disponible" grâce à l'enrichissement DB, mais si le curriculum a aussi `exercise_types` rempli, le pipeline statique est utilisé (priorité curriculum > DB pour la génération, mais DB > curriculum pour la disponibilité)

---

### H4 — L'admin permet de sélectionner des générateurs qui produisent un comportement opposé au but (ex: vouloir du dynamique, obtenir du statique)

**✅ CONFIRMÉ**

**Preuve**:

1. **Admin Curriculum**:
   - **Fichier**: `frontend/src/components/admin/Curriculum6eAdminPage.js`, ligne 77-78
   - **Options**: `availableOptions.generators` (ligne 923)
   - **Source**: `GET /api/admin/curriculum/options` → `get_available_generators()` (ligne 335 dans `curriculum_persistence_service.py`)
   - **Contenu**: Fusion `MathExerciseType` enum + générateurs dynamiques (via mapping)

2. **Sélection**:
   - L'admin peut sélectionner `"AGRANDISSEMENT_REDUCTION"` (générateur dynamique)
   - Stocké dans `exercise_types: ["AGRANDISSEMENT_REDUCTION"]` (curriculum)

3. **Génération**:
   - **Fichier**: `backend/routes/exercises_routes.py`, ligne 844-906
   - **Conversion**: `hasattr(MathExerciseType, "AGRANDISSEMENT_REDUCTION")` → **FALSE** (ligne 864)
   - **Résultat**: `invalid_types.append("AGRANDISSEMENT_REDUCTION")` (ligne 867)
   - **Si tous invalides**: Erreur `INVALID_CURRICULUM_EXERCISE_TYPES` (ligne 882-901)
   - **Si certains valides**: Warning + continue avec types valides (ligne 874-878)

**⚠️ PROBLÈME**: 
- L'admin peut sélectionner `"AGRANDISSEMENT_REDUCTION"` (générateur dynamique)
- Mais `"AGRANDISSEMENT_REDUCTION"` n'est pas dans `MathExerciseType` enum
- Résultat: Erreur ou fallback silencieux vers pipeline statique avec types valides uniquement
- **Comportement opposé**: L'admin veut du dynamique, obtient du statique (ou erreur)

**Autre cas**:
- L'admin peut sélectionner `"SYMETRIE_AXIALE"` (disponible dans `MathExerciseType` enum ET comme générateur dynamique)
- Si exercices dynamiques en DB → Pipeline dynamique utilisé (correct)
- Si pas d'exercices dynamiques en DB → Pipeline statique utilisé (correct aussi, mais confusion possible)

---

## 4. OPTIONS DE SIMPLIFICATION

### OPTION 1 (RECOMMANDÉE) — Pipeline explicite au niveau chapitre

#### Principe

Ajouter un champ **explicite** `pipeline` au niveau chapitre pour forcer le choix du pipeline, sans ambiguïté.

#### Règles exactes (if/else)

**Fichier**: `backend/curriculum/loader.py`, modèle `CurriculumChapter` (ligne 30)

**Ajout**:
```python
pipeline: Literal["SPEC", "TEMPLATE", "MIXED"] = Field(
    default="SPEC",
    description="Pipeline de génération: SPEC (statique), TEMPLATE (dynamique), MIXED (les deux)"
)
```

**Fichier**: `backend/routes/exercises_routes.py`, `generate_exercise()` (ligne 551)

**Nouvelle logique** (remplace ligne 738-812):
```python
# 1. Résolution curriculum (AVANT vérification DB)
curriculum_chapter = get_chapter_by_official_code(request.code_officiel)

if curriculum_chapter:
    pipeline_mode = curriculum_chapter.pipeline  # "SPEC" | "TEMPLATE" | "MIXED"
    
    if pipeline_mode == "TEMPLATE":
        # Pipeline dynamique uniquement
        # Vérifier exercices dynamiques en DB
        # Si aucun → erreur explicite
        # Si trouvés → format_dynamic_exercise()
        
    elif pipeline_mode == "SPEC":
        # Pipeline statique uniquement
        # Utiliser exercise_types → MathExerciseType enum
        # Si invalides → erreur explicite
        # Générer via MathGenerationService
        
    elif pipeline_mode == "MIXED":
        # Priorité: exercices dynamiques DB > pipeline statique
        # Si exercices dynamiques → format_dynamic_exercise()
        # Sinon → MathGenerationService
```

#### Impacts DB

**Collection**: `curriculum_chapters`

**Migration**:
- Ajouter champ `pipeline: "SPEC"` par défaut pour tous les chapitres existants
- Chapitres GM07/GM08 → `pipeline: "SPEC"` (déjà statiques)
- Chapitre TESTS_DYN → `pipeline: "TEMPLATE"` (déjà dynamique)
- Nouveaux chapitres → choix explicite dans l'admin

**Validation**:
- Si `pipeline: "TEMPLATE"` → vérifier qu'au moins un exercice dynamique existe en DB
- Si `pipeline: "SPEC"` → vérifier que tous les `exercise_types` sont dans `MathExerciseType` enum

#### Impacts UI

**Admin Curriculum** (`Curriculum6eAdminPage.js`):
- Ajouter champ `pipeline` dans le formulaire (ligne 87-98)
- Options: "Statique (SPEC)", "Dynamique (TEMPLATE)", "Mixte (MIXED)"
- **Contraintes**:
  - Si `pipeline: "TEMPLATE"` → désactiver sélection `exercise_types` (ou les utiliser uniquement pour info)
  - Si `pipeline: "SPEC"` → désactiver création exercices dynamiques (ou les ignorer)
  - Si `pipeline: "MIXED"` → permettre les deux

**Admin Exercises** (`ChapterExercisesAdminPage.js`):
- Si chapitre `pipeline: "SPEC"` → désactiver `is_dynamic` (ou warning)
- Si chapitre `pipeline: "TEMPLATE"` → désactiver création exercices statiques (ou warning)

#### Risques

1. **Migration**: Chapitres existants doivent être migrés (ajout `pipeline: "SPEC"` par défaut)
2. **Compatibilité**: Chapitres sans `pipeline` → fallback sur comportement actuel (détection automatique)
3. **Erreurs**: Si `pipeline: "TEMPLATE"` mais pas d'exercices dynamiques → erreur explicite (bon comportement)

#### Coût de migration

- **Backend**: ~200 lignes (modèle, route, validation)
- **Frontend**: ~100 lignes (champ formulaire, contraintes)
- **Migration DB**: Script one-shot (~50 lignes)
- **Tests**: ~5 tests unitaires
- **Total estimé**: 1-2 jours

---

### OPTION 2 — Routage par capacité détectée (déterministe)

#### Principe

Détection automatique déterministe basée sur les capacités réelles du chapitre (exercices en DB + curriculum).

#### Règles exactes (if/else)

**Fichier**: `backend/routes/exercises_routes.py`, `generate_exercise()` (ligne 551)

**Nouvelle logique** (remplace ligne 738-812):
```python
# 1. Résolution curriculum
curriculum_chapter = get_chapter_by_official_code(request.code_officiel)

# 2. Détection capacité
has_dynamic_in_db = await sync_service.has_exercises_in_db(chapter_code) and 
                    await has_dynamic_exercises(chapter_code)
has_static_in_curriculum = curriculum_chapter and 
                          len(curriculum_chapter.exercise_types) > 0 and
                          all(et in MathExerciseType for et in curriculum_chapter.exercise_types)

# 3. Routage déterministe
if has_dynamic_in_db and has_static_in_curriculum:
    # MIXED: Priorité dynamique
    # Utiliser exercices dynamiques DB
elif has_dynamic_in_db:
    # TEMPLATE uniquement
    # Utiliser exercices dynamiques DB
elif has_static_in_curriculum:
    # SPEC uniquement
    # Utiliser MathGenerationService
else:
    # Erreur: Aucune capacité détectée
    raise HTTPException(422, "Chapitre sans générateurs disponibles")
```

#### Impacts DB

**Aucun**: Pas de nouveau champ, détection à la volée.

**Validation**:
- Si exercices dynamiques en DB → vérifier que `generator_key` est valide
- Si `exercise_types` dans curriculum → vérifier que tous sont dans `MathExerciseType` enum

#### Impacts UI

**Admin Curriculum**:
- Afficher "Capacités détectées": "Dynamique", "Statique", "Mixte", "Aucune"
- Warning si `exercise_types` contient des valeurs non-`MathExerciseType`

**Admin Exercises**:
- Afficher "Pipeline actuel": "Dynamique", "Statique", "Mixte"
- Warning si création exercice incompatible avec pipeline détecté

#### Risques

1. **Non-déterministe**: La détection peut changer si exercices ajoutés/supprimés
2. **Performance**: Vérification DB à chaque génération (mais déjà fait actuellement)
3. **Confusion**: L'admin ne contrôle pas explicitement le pipeline

#### Coût de migration

- **Backend**: ~150 lignes (logique de détection, validation)
- **Frontend**: ~50 lignes (affichage capacités)
- **Tests**: ~5 tests unitaires
- **Total estimé**: 1 jour

---

## 5. PLAN DE MIGRATION

### Étape 1 — Préparation (P0)

**Objectif**: Préparer la migration sans casser l'existant

**Actions**:
1. **Audit complet** (ce document) ✅
2. **Backup DB**: Exporter `curriculum_chapters` et `admin_exercises`
3. **Tests de non-régression**: Curls pour GM07, GM08, TESTS_DYN, chapitres statiques, chapitres dynamiques

**Livrables**:
- Script de backup DB
- Suite de tests curl (fichier `tests/migration_validation.sh`)

**Durée**: 2 heures

---

### Étape 2 — Migration modèle (P0)

**Objectif**: Ajouter le champ `pipeline` au modèle sans casser l'existant

**Actions**:
1. **Backend**: Modifier `CurriculumChapter` (ligne 30 dans `curriculum/loader.py`)
   - Ajouter `pipeline: Literal["SPEC", "TEMPLATE", "MIXED"] = "SPEC"`
   - Rendre optionnel pour compatibilité (fallback sur détection automatique si absent)

2. **Migration DB**: Script pour ajouter `pipeline: "SPEC"` à tous les chapitres existants
   - GM07, GM08 → `"SPEC"`
   - TESTS_DYN → `"TEMPLATE"`
   - Autres → `"SPEC"` (par défaut)

3. **Validation**: Vérifier que tous les chapitres ont `pipeline` après migration

**Livrables**:
- Modèle modifié
- Script de migration DB (`backend/scripts/migrate_pipeline_field.py`)
- Tests unitaires pour le modèle

**Durée**: 4 heures

---

### Étape 3 — Migration logique génération (P0)

**Objectif**: Utiliser le champ `pipeline` dans la route de génération

**Actions**:
1. **Backend**: Modifier `generate_exercise()` (ligne 551 dans `exercises_routes.py`)
   - Lire `curriculum_chapter.pipeline` (si présent)
   - Appliquer la logique selon `pipeline` (SPEC/TEMPLATE/MIXED)
   - Fallback sur détection automatique si `pipeline` absent (compatibilité)

2. **Tests**: Tests unitaires pour chaque mode (SPEC, TEMPLATE, MIXED)

**Livrables**:
- Route modifiée
- Tests unitaires (`backend/tests/test_pipeline_routing.py`)

**Durée**: 6 heures

---

### Étape 4 — Migration UI Admin (P1)

**Objectif**: Permettre à l'admin de sélectionner le pipeline

**Actions**:
1. **Frontend**: Modifier `Curriculum6eAdminPage.js`
   - Ajouter champ `pipeline` dans le formulaire (ligne 87-98)
   - Options: "Statique (SPEC)", "Dynamique (TEMPLATE)", "Mixte (MIXED)"
   - Contraintes: Désactiver `exercise_types` si `pipeline: "TEMPLATE"`

2. **Backend**: Modifier `ChapterCreateRequest` / `ChapterUpdateRequest`
   - Ajouter `pipeline: Optional[Literal["SPEC", "TEMPLATE", "MIXED"]]`

3. **Validation**: Vérifier que les contraintes sont respectées (ex: `pipeline: "TEMPLATE"` → pas de `exercise_types` non-`MathExerciseType`)

**Livrables**:
- UI modifiée
- Validation backend
- Tests manuels

**Durée**: 4 heures

---

### Étape 5 — Nettoyage et documentation (P2)

**Objectif**: Supprimer la détection automatique (optionnel, peut rester en fallback)

**Actions**:
1. **Backend**: Supprimer la logique de détection automatique (ligne 760-812 dans `exercises_routes.py`)
   - Ou la garder en fallback si `pipeline` absent (compatibilité)

2. **Documentation**: Mettre à jour les guides admin

**Livrables**:
- Code nettoyé
- Documentation mise à jour

**Durée**: 2 heures

---

### Compatibilité rétroactive

**Stratégie**: Fallback sur détection automatique si `pipeline` absent

**Code**:
```python
pipeline = curriculum_chapter.pipeline if hasattr(curriculum_chapter, 'pipeline') else None

if pipeline:
    # Utiliser pipeline explicite
elif has_dynamic_in_db:
    # Fallback: détection automatique (comportement actuel)
else:
    # Fallback: pipeline statique
```

**Avantage**: Chapitres existants continuent de fonctionner sans migration immédiate

---

### Comment éviter de casser GM07/GM08 et les chapitres existants

**Stratégie**:
1. **Intercepts GM07/GM08**: Garder les intercepts hardcodés (ligne 566, 628) → **PRIORITÉ ABSOLUE**
2. **Intercept TESTS_DYN**: Garder l'intercept (ligne 688) → **PRIORITÉ ABSOLUE**
3. **Migration DB**: Ajouter `pipeline: "SPEC"` pour GM07/GM08, `pipeline: "TEMPLATE"` pour TESTS_DYN
4. **Tests**: Vérifier que GM07, GM08, TESTS_DYN fonctionnent toujours après migration

**Tests de non-régression**:
```bash
# GM07
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_GM07", "difficulte": "facile", "offer": "free"}'

# GM08
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_GM08", "difficulte": "moyen", "offer": "free"}'

# TESTS_DYN
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_TESTS_DYN", "difficulte": "facile", "offer": "free"}'
```

---

### Comment tester

**Tests unitaires ciblés**:
1. `test_pipeline_spec()`: Chapitre avec `pipeline: "SPEC"` → utilise `MathGenerationService`
2. `test_pipeline_template()`: Chapitre avec `pipeline: "TEMPLATE"` → utilise `format_dynamic_exercise()`
3. `test_pipeline_mixed()`: Chapitre avec `pipeline: "MIXED"` → priorité dynamique
4. `test_pipeline_fallback()`: Chapitre sans `pipeline` → détection automatique (compatibilité)
5. `test_pipeline_validation()`: `pipeline: "TEMPLATE"` sans exercices dynamiques → erreur explicite

**Tests curl**:
- Voir section "Comment éviter de casser GM07/GM08" ci-dessus

---

## 6. TODO LIST PRIORISÉE

### P0 — CRITIQUE (bloquant pour industrialisation)

- [ ] **P0.1**: Ajouter champ `pipeline` au modèle `CurriculumChapter`
  - Fichier: `backend/curriculum/loader.py`, ligne 30
  - Type: `Literal["SPEC", "TEMPLATE", "MIXED"]`
  - Default: `"SPEC"` (compatibilité)

- [ ] **P0.2**: Migration DB — Script pour ajouter `pipeline` à tous les chapitres
  - GM07, GM08 → `"SPEC"`
  - TESTS_DYN → `"TEMPLATE"`
  - Autres → `"SPEC"`

- [ ] **P0.3**: Modifier route génération pour utiliser `pipeline` explicite
  - Fichier: `backend/routes/exercises_routes.py`, ligne 551
  - Logique: Lire `curriculum_chapter.pipeline` → routage selon valeur
  - Fallback: Détection automatique si `pipeline` absent

- [ ] **P0.4**: Validation — Vérifier que `pipeline: "TEMPLATE"` nécessite exercices dynamiques
  - Erreur explicite si `pipeline: "TEMPLATE"` mais pas d'exercices dynamiques en DB

- [ ] **P0.5**: Validation — Vérifier que `pipeline: "SPEC"` nécessite `exercise_types` valides
  - Erreur explicite si `exercise_types` contient des valeurs non-`MathExerciseType`

- [ ] **P0.6**: Tests de non-régression — GM07, GM08, TESTS_DYN
  - Curls + tests unitaires

---

### P1 — IMPORTANT (améliore UX admin)

- [ ] **P1.1**: Ajouter champ `pipeline` dans UI Admin Curriculum
  - Fichier: `frontend/src/components/admin/Curriculum6eAdminPage.js`
  - Options: "Statique (SPEC)", "Dynamique (TEMPLATE)", "Mixte (MIXED)"
  - Contraintes: Désactiver `exercise_types` si `pipeline: "TEMPLATE"`

- [ ] **P1.2**: Validation UI — Afficher warning si `exercise_types` incompatible avec `pipeline`
  - Ex: `pipeline: "TEMPLATE"` mais `exercise_types: ["CALCUL_FRACTIONS"]` (statique)

- [ ] **P1.3**: Afficher "Pipeline actuel" dans Admin Exercises
  - Fichier: `frontend/src/components/admin/ChapterExercisesAdminPage.js`
  - Afficher le pipeline du chapitre (depuis curriculum)

- [ ] **P1.4**: Contraintes UI — Désactiver création exercices incompatibles
  - Si `pipeline: "SPEC"` → désactiver `is_dynamic` (ou warning)
  - Si `pipeline: "TEMPLATE"` → désactiver création exercices statiques (ou warning)

---

### P2 — AMÉLIORATION (optionnel)

- [ ] **P2.1**: Nettoyage — Supprimer détection automatique (garder en fallback uniquement)
  - Fichier: `backend/routes/exercises_routes.py`, ligne 760-812
  - Garder uniquement si `pipeline` absent (compatibilité)

- [ ] **P2.2**: Documentation — Guide admin "Créer un chapitre dynamique"
  - Expliquer la différence SPEC vs TEMPLATE vs MIXED
  - Exemples concrets

- [ ] **P2.3**: Amélioration mapping — Unifier `exercise_types` dynamiques et statiques
  - Créer un mapping unique `generator_key` → `exercise_type` → `MathExerciseType` (si applicable)
  - Ou séparer complètement les deux systèmes

---

## 7. RECOMMANDATION FINALE

### ✅ OPTION 1 — Pipeline explicite au niveau chapitre (RECOMMANDÉE)

**Raisons**:
1. **Simplicité UX**: L'admin choisit explicitement le pipeline → pas de surprise
2. **Déterministe**: Même configuration = même comportement, toujours
3. **Testable**: Facile à tester (vérifier `pipeline` → comportement attendu)
4. **Industrialisable**: Règles claires, contraintes UI, validation backend

**Risques acceptables**:
- Migration DB nécessaire (mais script one-shot)
- Champs supplémentaires (mais clarifie l'intention)

**Alternatives rejetées**:
- **Option 2**: Trop de détection automatique → comportements surprenants
- **Status quo**: Incompréhensible et inutilisable (problèmes H1-H4 confirmés)

---

## 8. QUESTIONS OUVERTES / INCERTITUDES

1. **Mix statique + dynamique**: L'option "MIXED" est proposée, mais est-ce vraiment nécessaire ? Ou vaut-il mieux forcer un seul pipeline par chapitre ?

2. **Mapping `exercise_types`**: Faut-il unifier les `exercise_types` dynamiques (ex: `"AGRANDISSEMENT_REDUCTION"`) avec les `MathExerciseType` enum, ou les garder séparés ?

3. **Compatibilité rétroactive**: Garder la détection automatique en fallback indéfiniment, ou la supprimer après migration complète ?

4. **Performance**: La vérification DB à chaque génération est-elle acceptable, ou faut-il un cache ?

---

## 9. PREUVES PAR FICHIERS

### Fichiers clés analysés

1. **Génération élève**:
   - `backend/routes/exercises_routes.py` (ligne 551-1162)
   - `backend/services/math_generation_service.py` (ligne 18+)
   - `backend/services/tests_dyn_handler.py` (ligne 78+)
   - `backend/services/gm07_handler.py` (ligne 28+)
   - `backend/services/gm08_handler.py` (ligne 28+)

2. **Catalogue / Disponibilité**:
   - `backend/curriculum/loader.py` (ligne 325-513)
   - `frontend/src/components/ExerciseGeneratorPage.js` (ligne 219)

3. **Admin Curriculum**:
   - `backend/routes/admin_curriculum_routes.py` (ligne 385-462)
   - `backend/services/curriculum_persistence_service.py` (ligne 188-280)
   - `frontend/src/components/admin/Curriculum6eAdminPage.js` (ligne 295-335)

4. **Admin Exercises**:
   - `backend/routes/admin_exercises_routes.py` (ligne 169-253)
   - `backend/services/exercise_persistence_service.py` (ligne 58-107)
   - `backend/services/curriculum_sync_service.py` (ligne 88-233)

5. **Modèles / Types**:
   - `backend/models/math_models.py` (ligne 16+) — `MathExerciseType` enum
   - `backend/curriculum/loader.py` (ligne 30-67) — `CurriculumChapter`
   - `backend/services/exercise_persistence_service.py` (ligne 58-107) — `ExerciseCreateRequest`

---

## 10. AMBIGUÏTÉS FONCTIONNELLES IDENTIFIÉES

### Ambiguïté 1 : "Disponible" ne signifie pas "génère correctement"

**Symptôme observé**:
- Un chapitre apparaît "disponible" dans le générateur (`hasGenerators: true`)
- Mais la génération échoue ou produit un exercice inattendu

**Cause racine**:
- La disponibilité est calculée depuis `exercise_types` (curriculum) OU enrichissement DB
- Mais la génération utilise un pipeline différent selon la détection automatique
- **Exemple concret**: Chapitre avec `exercise_types: ["AGRANDISSEMENT_REDUCTION"]` (dynamique) → disponible, mais si pas d'exercices dynamiques en DB → pipeline statique utilisé → `"AGRANDISSEMENT_REDUCTION"` n'est pas dans `MathExerciseType` enum → erreur ou fallback

**Impact utilisateur**:
- L'élève voit un chapitre "disponible" mais obtient une erreur à la génération
- L'enseignant ne comprend pas pourquoi un chapitre disponible ne fonctionne pas

---

### Ambiguïté 2 : Sélection admin ≠ comportement réel

**Symptôme observé**:
- L'admin sélectionne un générateur dans le formulaire de création de chapitre
- Mais la génération utilise un autre pipeline (statique vs dynamique)

**Cause racine**:
- L'admin sélectionne `exercise_types: ["AGRANDISSEMENT_REDUCTION"]` (générateur dynamique)
- Mais `"AGRANDISSEMENT_REDUCTION"` n'est pas dans `MathExerciseType` enum
- Résultat: Erreur `INVALID_CURRICULUM_EXERCISE_TYPES` ou fallback silencieux vers types valides uniquement
- **Comportement opposé**: L'admin veut du dynamique, obtient du statique (ou erreur)

**Impact utilisateur**:
- L'admin configure un chapitre dynamique mais obtient un comportement statique
- Confusion sur ce que fait réellement le système

---

### Ambiguïté 3 : Statique vs dynamique flou dans l'UX

**Symptôme observé**:
- L'admin ne sait pas clairement s'il crée un exercice statique ou dynamique
- Les champs se chevauchent (`exercise_type` vs `generator_key`)

**Cause racine**:
- Un exercice peut être statique (`is_dynamic: false`, `enonce_html`) OU dynamique (`is_dynamic: true`, `generator_key`, `enonce_template_html`)
- Mais un chapitre peut avoir les deux types d'exercices
- Le pipeline utilisé dépend de la détection automatique (ordre de vérification)
- **Pas de visibilité**: L'admin ne voit pas quel pipeline sera utilisé pour un chapitre

**Impact utilisateur**:
- L'admin crée des exercices sans savoir s'ils seront utilisés
- Risque de créer des exercices dynamiques pour un chapitre qui utilise le pipeline statique

---

### Ambiguïté 4 : Sources de vérité multiples et contradictoires

**Symptôme observé**:
- Un chapitre peut avoir `exercise_types` dans le curriculum
- ET des exercices dynamiques en DB
- Mais le pipeline utilisé dépend de l'ordre de vérification (non déterministe pour l'admin)

**Cause racine**:
- **Source 1**: Curriculum (`curriculum_6e.json` ou MongoDB `curriculum_chapters`) → `exercise_types`
- **Source 2**: DB (`admin_exercises`) → exercices dynamiques
- **Source 3**: Fichiers Python (`data/gm07_exercises.py`, etc.) → exercices figés
- **Source 4**: Cache mémoire (`CurriculumIndex`) → rechargé après modifs
- **Décision**: Détection automatique (ordre: intercepts → DB → curriculum)

**Impact utilisateur**:
- L'admin modifie le curriculum mais le comportement ne change pas (cache ou DB prioritaire)
- Incompréhension de "quelle source fait foi"

---

## 11. INCOHÉRENCES TECHNIQUES IDENTIFIÉES

### Incohérence 1 : `exercise_types` curriculum vs `MathExerciseType` enum

**Problème**:
- Le curriculum stocke `exercise_types: List[str]` (ex: `["AGRANDISSEMENT_REDUCTION"]`)
- Mais le pipeline statique nécessite `MathExerciseType` enum
- `"AGRANDISSEMENT_REDUCTION"` n'est PAS dans `MathExerciseType` enum
- **Résultat**: Erreur ou fallback silencieux (ligne 867 dans `exercises_routes.py`)

**Preuve**:
- Fichier: `backend/routes/exercises_routes.py`, ligne 863-869
- Conversion: `hasattr(MathExerciseType, et)` → `False` pour `"AGRANDISSEMENT_REDUCTION"`
- Gestion: `invalid_types.append(et)` → warning ou erreur si tous invalides

**Impact technique**:
- Le curriculum peut contenir des valeurs invalides pour le pipeline statique
- Pas de validation au moment de la création/modification du chapitre

---

### Incohérence 2 : Mapping `generator_key` → `exercise_type` non unifié

**Problème**:
- Les exercices dynamiques utilisent `generator_key: "THALES_V1"` → mappé vers `exercise_type: "AGRANDISSEMENT_REDUCTION"`
- Mais `"AGRANDISSEMENT_REDUCTION"` n'est pas dans `MathExerciseType` enum
- **Résultat**: La sync curriculum ajoute `exercise_types: ["AGRANDISSEMENT_REDUCTION"]`, mais le pipeline statique ne peut pas l'utiliser

**Preuve**:
- Fichier: `backend/services/curriculum_sync_service.py`, ligne 25-29
- Mapping: `"THALES_V1"` → `"AGRANDISSEMENT_REDUCTION"` (via `GENERATOR_TO_EXERCISE_TYPE`)
- Sync: `extract_exercise_types_from_chapter()` (ligne 131) → ajoute `"AGRANDISSEMENT_REDUCTION"` au curriculum
- Pipeline statique: `MathExerciseType["AGRANDISSEMENT_REDUCTION"]` → **ERREUR** (pas dans enum)

**Impact technique**:
- La sync curriculum peut créer des `exercise_types` incompatibles avec le pipeline statique
- Pas de validation de compatibilité entre générateurs dynamiques et `MathExerciseType` enum

---

### Incohérence 3 : Priorité DB > Curriculum pour génération, mais Curriculum > DB pour disponibilité

**Problème**:
- **Génération** (ligne 760-812): Vérifie DB exercices dynamiques AVANT résolution curriculum → priorité DB
- **Disponibilité** (ligne 404-429): Enrichit curriculum avec DB → priorité curriculum (fusion)
- **Résultat**: Un chapitre peut être "disponible" grâce au curriculum, mais utiliser le pipeline DB (ou vice versa)

**Preuve**:
- Génération: `backend/routes/exercises_routes.py`, ligne 760 (DB vérifié en premier)
- Disponibilité: `backend/curriculum/loader.py`, ligne 404 (curriculum enrichi avec DB)

**Impact technique**:
- Comportement non déterministe: même configuration peut donner des résultats différents selon l'ordre de vérification
- L'admin ne peut pas prévoir quel pipeline sera utilisé

---

### Incohérence 4 : Cache mémoire non invalidé après modifs DB

**Problème**:
- Le `CurriculumIndex` est mis en cache en mémoire (ligne 222 dans `curriculum_persistence_service.py`)
- Rechargé après modif curriculum (ligne 222: `_reload_curriculum_index()`)
- **MAIS**: Pas de rechargement après création/modification d'exercices en DB
- **Résultat**: Le catalogue peut afficher des données obsolètes

**Preuve**:
- Cache: `backend/curriculum/loader.py`, `get_curriculum_index()` (singleton)
- Rechargement: `backend/services/curriculum_persistence_service.py`, ligne 222 (uniquement après modif curriculum)
- Pas de rechargement: Après création exercice en DB (ligne 180 dans `admin_exercises_routes.py`)

**Impact technique**:
- Le catalogue peut afficher "indisponible" alors que des exercices existent en DB
- Nécessite redémarrage backend pour voir les changements

---

## 12. POINTS LEGACY PROBLÉMATIQUES

### Legacy 1 : Fichiers Python comme source de vérité (GM07, GM08, TESTS_DYN)

**Problème**:
- GM07, GM08, TESTS_DYN utilisent des fichiers Python (`data/gm07_exercises.py`, etc.)
- Ces fichiers sont générés depuis MongoDB (`_sync_to_python_file()`)
- **MAIS**: Les handlers lisent directement les fichiers Python, pas MongoDB
- **Résultat**: Double source de vérité (MongoDB + fichiers Python)

**Preuve**:
- Sync: `backend/services/exercise_persistence_service.py`, ligne 305 (`_sync_to_python_file()`)
- Lecture: `backend/services/gm07_handler.py`, ligne 18 (`from data.gm07_exercises import ...`)

**Risque à moyen/long terme**:
- Désynchronisation possible entre MongoDB et fichiers Python
- Nécessite sync manuelle après chaque modif
- Non scalable: Impossible d'ajouter de nouveaux chapitres "figés" facilement

---

### Legacy 2 : Intercepts hardcodés (GM07, GM08, TESTS_DYN)

**Problème**:
- Les chapitres GM07, GM08, TESTS_DYN sont interceptés hardcodés (ligne 566, 628, 688)
- Pas de configuration pour ajouter de nouveaux chapitres "spéciaux"
- **Résultat**: Impossible d'ajouter un nouveau chapitre avec handler dédié sans modifier le code

**Preuve**:
- Intercepts: `backend/routes/exercises_routes.py`, ligne 566 (`is_gm07_request()`), 628 (`is_gm08_request()`), 688 (`is_tests_dyn_request()`)

**Risque à moyen/long terme**:
- Chaque nouveau chapitre "spécial" nécessite une modification de code
- Pas de système générique pour gérer les chapitres avec handlers dédiés
- Maintenance difficile: code dispersé, pas de pattern clair

---

### Legacy 3 : Mapping chapitre → types d'exercices (MathGenerationService)

**Problème**:
- `MathGenerationService` utilise un mapping hardcodé `_map_chapter_to_types()` (ligne 47)
- Ce mapping est basé sur le nom du chapitre (`chapitre_backend`)
- **Résultat**: Impossible d'ajouter de nouveaux types d'exercices sans modifier le code

**Preuve**:
- Mapping: `backend/services/math_generation_service.py`, ligne 47 (`_map_chapter_to_types()`)
- Utilisation: Ligne 47-48 (mapping chapitre → types)

**Risque à moyen/long terme**:
- Chaque nouveau chapitre nécessite une modification du mapping
- Pas de configuration externe (DB ou JSON)
- Maintenance difficile: mapping dispersé dans le code

---

## 13. RISQUES SI RIEN N'EST CHANGÉ

### Risque 1 : Impossibilité d'industrialiser (BLOQUANT)

**Description**:
- Le système actuel est incompréhensible pour les admins
- Les comportements sont non déterministes (détection automatique)
- Les erreurs sont silencieuses ou cryptiques

**Impact**:
- **Court terme**: Les admins ne peuvent pas créer/modifier des chapitres sans erreurs
- **Moyen terme**: Impossible d'ajouter de nouveaux chapitres dynamiques facilement
- **Long terme**: Le système devient inmaintenable, nécessite refonte complète

**Probabilité**: **ÉLEVÉE** (symptômes déjà observés)

**Gravité**: **CRITIQUE** (bloque l'évolution du produit)

---

### Risque 2 : Dégradation de l'expérience utilisateur (élève)

**Description**:
- Les chapitres apparaissent "disponibles" mais génèrent des erreurs
- Les exercices générés ne correspondent pas aux attentes (pipeline incorrect)
- Les erreurs sont cryptiques (`INVALID_CURRICULUM_EXERCISE_TYPES`)

**Impact**:
- **Court terme**: Frustration des élèves, perte de confiance
- **Moyen terme**: Abandon du produit, mauvais retours utilisateurs
- **Long terme**: Impact sur la réputation du produit

**Probabilité**: **MOYENNE** (symptômes observés mais pas systématiques)

**Gravité**: **ÉLEVÉE** (impact direct sur l'expérience utilisateur)

---

### Risque 3 : Dette technique croissante

**Description**:
- Les incohérences techniques s'accumulent (mapping non unifié, cache non invalidé, etc.)
- Les points legacy deviennent de plus en plus difficiles à maintenir
- Chaque ajout de fonctionnalité aggrave les problèmes existants

**Impact**:
- **Court terme**: Temps de développement augmenté (debug, workarounds)
- **Moyen terme**: Impossibilité d'ajouter de nouvelles fonctionnalités sans casser l'existant
- **Long terme**: Refonte complète nécessaire (coût élevé)

**Probabilité**: **ÉLEVÉE** (dette technique déjà présente)

**Gravité**: **MOYENNE** (impact sur la vélocité, pas bloquant immédiatement)

---

### Risque 4 : Impossibilité d'ouvrir aux enseignants

**Description**:
- Le système actuel est trop complexe pour des non-techniciens
- Les ambiguïtés fonctionnelles rendent l'UX admin inutilisable
- Pas de visibilité sur le comportement réel du système

**Impact**:
- **Court terme**: Impossible d'ouvrir l'admin aux enseignants
- **Moyen terme**: Nécessité de créer une interface simplifiée (coût élevé)
- **Long terme**: Perte d'opportunité (enseignants ne peuvent pas créer leurs propres exercices)

**Probabilité**: **ÉLEVÉE** (système actuel inadapté)

**Gravité**: **MOYENNE** (bloque une évolution souhaitée, pas bloquant immédiatement)

---

## 14. RECOMMANDATION PRINCIPALE

### ✅ OPTION 1 — Pipeline explicite au niveau chapitre (RECOMMANDÉE)

#### Principe architectural

**Idée centrale** : Remplacer la **détection automatique implicite** par un **choix explicite** au niveau chapitre.

**Champ ajouté** : `pipeline: "SPEC" | "TEMPLATE" | "MIXED"`

**Valeurs** :
- `"SPEC"` : Pipeline statique uniquement (MathGenerationService)
- `"TEMPLATE"` : Pipeline dynamique uniquement (format_dynamic_exercise depuis DB)
- `"MIXED"` : Les deux pipelines (priorité dynamique si exercices en DB)

#### Pourquoi cette solution résout les problèmes

| Problème | Comment la solution le résout |
|----------|-------------------------------|
| **Ambiguïté 1** (disponible ≠ génère) | Le pipeline force un choix explicite → validation au moment de la création → erreur si incompatible |
| **Ambiguïté 2** (sélection ≠ comportement) | L'admin choisit le pipeline → comportement déterministe, prévisible |
| **Ambiguïté 3** (statique vs dynamique flou) | Le pipeline est visible dans l'UI → clarté immédiate |
| **Ambiguïté 4** (sources multiples) | Le pipeline est la source de vérité unique pour le routage → pas de conflit |
| **Incohérence 1** (exercise_types vs enum) | Validation au moment de la création → erreur explicite si incompatible |
| **Incohérence 2** (mapping non unifié) | Le pipeline sépare clairement les deux systèmes → pas de confusion |
| **Incohérence 3** (priorité DB vs curriculum) | Le pipeline force un choix → pas d'ambiguïté |
| **Incohérence 4** (cache non invalidé) | Le pipeline est dans le curriculum → rechargement automatique |
| **Legacy 1** (fichiers Python) | Le pipeline peut être configuré pour utiliser MongoDB directement (évolution future) |
| **Legacy 2** (intercepts hardcodés) | Le pipeline remplace les intercepts par configuration (évolution future) |
| **Legacy 3** (mapping hardcodé) | Le pipeline force l'utilisation du curriculum → mapping externalisé |

#### Avantages produit

**Pour l'admin** :
- ✅ Choix explicite et visible dans l'UI
- ✅ Validation immédiate (erreur si configuration incompatible)
- ✅ Comportement prévisible (même configuration = même résultat)

**Pour l'élève** :
- ✅ Pas d'erreur surprise (validation au moment de la configuration)
- ✅ Comportement cohérent (chapitre disponible = génère correctement)

**Pour l'équipe technique** :
- ✅ Règles claires et déterministes
- ✅ Facile à tester (vérifier `pipeline` → comportement attendu)
- ✅ Scalable (ajout de nouveaux chapitres sans modification de code)

#### Contraintes et limites

**Contraintes techniques**:
- Migration DB nécessaire (script one-shot, ~50 lignes)
- Champ supplémentaire dans le modèle (mais clarifie l'intention)
- Validation backend nécessaire (vérifier compatibilité pipeline/exercise_types)

**Limites fonctionnelles**:
- Ne résout pas les problèmes legacy immédiatement (nécessite évolution future)
- Nécessite formation des admins (nouveau champ à comprendre)
- Compatibilité rétroactive nécessaire (fallback sur détection automatique si `pipeline` absent)

**Risques**:
- **Faible** : Migration DB peut échouer si chapitres corrompus → script de rollback nécessaire
- **Faible** : Admins peuvent mal configurer → validation backend empêche les erreurs

#### Alternative rejetée : Option 2 (Routage par capacité détectée)

**Principe** : Détection automatique basée sur les capacités réelles (exercices en DB + curriculum).

**Pourquoi rejetée** :
- ❌ **Non déterministe** : La détection peut changer si exercices ajoutés/supprimés
- ❌ **Confusion** : L'admin ne contrôle pas explicitement le pipeline
- ❌ **Risque** : Comportements surprenants si configuration change
- ❌ **Non industrialisable** : Pas de règles claires, difficile à tester

**Comparaison** :

| Critère | Option 1 (Pipeline explicite) | Option 2 (Détection automatique) |
|---------|-------------------------------|-----------------------------------|
| **Déterministe** | ✅ Oui (choix explicite) | ❌ Non (dépend de la DB) |
| **Contrôle admin** | ✅ Total | ❌ Aucun |
| **Testable** | ✅ Facile | ❌ Difficile |
| **Industrialisable** | ✅ Oui | ❌ Non |
| **Complexité** | Moyenne (migration DB) | Faible (pas de migration) |

---

## 15. CONCLUSION

Le système actuel est **incompréhensible et inutilisable** pour les raisons suivantes :

1. **Multiplicité des sources de vérité**: Curriculum, DB, fichiers Python, cache mémoire
2. **Décisions implicites**: Routage par détection automatique → comportements surprenants
3. **Confusion des concepts**: `exercise_types`, `generators`, `generator_key` se chevauchent
4. **Incohérences**: Chapitre "disponible" mais génère du statique, ou erreur si générateur dynamique sélectionné

**La solution recommandée (Option 1)** clarifie le système en :
- Forçant un choix explicite du pipeline au niveau chapitre
- Séparant clairement les pipelines (SPEC vs TEMPLATE vs MIXED)
- Ajoutant des contraintes UI pour éviter les configurations invalides
- Rendant le système testable et industrialisable

**Risques si rien n'est changé**:
- **BLOQUANT**: Impossibilité d'industrialiser (admins ne peuvent pas utiliser le système)
- **CRITIQUE**: Dégradation de l'expérience utilisateur (élèves obtiennent des erreurs)
- **ÉLEVÉE**: Dette technique croissante (maintenance de plus en plus difficile)
- **MOYENNE**: Impossibilité d'ouvrir aux enseignants (système trop complexe)

**Prochaine étape**: Validation de cette recommandation avant implémentation.

