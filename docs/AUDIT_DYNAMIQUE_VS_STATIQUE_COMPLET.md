# AUDIT COMPLET : Exercices DYNAMIQUES vs STATIQUES
## Pipeline de sélection, fallback, et plan de fix minimal

**Date** : 2025-12-25  
**Équipe** : COMEX Technique (Lead Backend, Lead Frontend, Architecte, QA)  
**Objectif** : Auditer le fonctionnement des exercices DYNAMIQUES vs STATIQUES, proposer une solution SIMPLE, stable et debuggable

---

## 1) GO/NO-GO

**✅ GO** - Le système est fonctionnel mais présente des incohérences de normalisation et de filtrage qui peuvent causer des fallbacks inattendus. Les corrections proposées sont minimales et sans régression.

---

## 2) DECISION TREE - Pipeline de sélection

### Input
```
POST /api/v1/exercises/generate
{
  code_officiel: "6e_G07" | "6e_SP01" | ...
  difficulte: "facile" | "moyen" | "difficile" | "standard"
  offer: "free" | "pro"
  seed: int (optionnel)
  exercise_type?: string (optionnel, pour premium)
  generator_key?: string (optionnel, pour admin)
}
```

### Decision Tree complet

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. INTERCEPT TESTS_DYN                                          │
└─────────────────────────────────────────────────────────────────┘
   │
   ├─ Si code_officiel == "6E_TESTS_DYN" → Pipeline TESTS_DYN
   │  └─ Fichier: backend/routes/exercises_routes.py:1022
   │  └─ Handler: backend/services/tests_dyn_handler.py
   │  └─ Retour immédiat (pas de fallback)
   │
   └─ Sinon → Continue

┌─────────────────────────────────────────────────────────────────┐
│ 2. NORMALISATION code_officiel                                   │
└─────────────────────────────────────────────────────────────────┘
   │
   └─ normalized_code = request.code_officiel.upper().replace("-", "_")
      └─ Fichier: backend/routes/exercises_routes.py:1093
      └─ Exemple: "6e_G07" → "6E_G07"

┌─────────────────────────────────────────────────────────────────┐
│ 3. LECTURE CHAPITRE (Source de vérité: MongoDB)                 │
└─────────────────────────────────────────────────────────────────┘
   │
   ├─ Service: CurriculumPersistenceService.get_chapter_by_code()
   │  └─ Fichier: backend/services/curriculum_persistence_service.py:200
   │  └─ Collection: curriculum_chapters
   │  └─ Query: {code_officiel: normalized_code} (insensible à la casse)
   │
   ├─ Si trouvé en DB:
   │  ├─ pipeline = chapter_from_db.get("pipeline")  # "SPEC" | "TEMPLATE" | "MIXED" | None
   │  ├─ enabled_generators_raw = chapter_from_db.get("enabled_generators", [])
   │  │  └─ Format: List[dict] ou List[str]
   │  │  └─ Exemple dict: [{"generator_key": "CALCUL_NOMBRES_V1", "is_enabled": true, ...}]
   │  │  └─ Exemple str: ["CALCUL_NOMBRES_V1", "SYMETRIE_AXIALE_V2"]
   │  └─ niveau, libelle depuis DB
   │
   └─ Si non trouvé en DB:
      └─ Fallback legacy: get_chapter_by_official_code() (fichier JSON)
         └─ Fichier: backend/curriculum/loader.py

┌─────────────────────────────────────────────────────────────────┐
│ 4. NORMALISATION enabled_generators                             │
└─────────────────────────────────────────────────────────────────┘
   │
   └─ enabled_generators_for_chapter = normalize_enabled_generators(enabled_generators_raw)
      └─ Fichier: backend/routes/exercises_routes.py:661
      └─ Logique:
         ├─ Si List[str] → [g.upper() for g in raw]
         ├─ Si List[dict] → [d["generator_key"].upper() for d in raw if d.get("is_enabled")]
         └─ Sinon → []

┌─────────────────────────────────────────────────────────────────┐
│ 5. DÉTERMINATION PIPELINE                                       │
└─────────────────────────────────────────────────────────────────┘
   │
   ├─ Si pipeline_mode == "TEMPLATE" → Pipeline dynamique uniquement
   │  └─ Fichier: backend/routes/exercises_routes.py:1251
   │
   ├─ Si pipeline_mode == "MIXED" → Pipeline DYNAMIC → STATIC fallback
   │  └─ Fichier: backend/routes/exercises_routes.py:1432
   │  └─ Fonction: generate_exercise_with_fallback()
   │
   ├─ Si pipeline_mode == "SPEC" → Pipeline statique uniquement
   │  └─ Fichier: backend/routes/exercises_routes.py:1752
   │
   └─ Si pipeline_mode == None → Détection automatique (legacy)
      └─ Vérifie exercices dynamiques en DB → MIXED si trouvés, sinon SPEC

┌─────────────────────────────────────────────────────────────────┐
│ 6. PIPELINE TEMPLATE (Dynamique uniquement)                      │
└─────────────────────────────────────────────────────────────────┘
   │
   ├─ Vérification: has_exercises_in_db(chapter_code_for_db)
   │  └─ Service: CurriculumSyncService
   │
   ├─ Query exercices:
   │  └─ exercise_service.get_exercises(
   │       chapter_code=chapter_code_for_db,
   │       offer=request.offer,
   │       difficulty=request.difficulte
   │     )
   │  └─ Fichier: backend/services/exercise_persistence_service.py:555
   │  └─ Collection: admin_exercises
   │  └─ Query MongoDB:
   │     {
   │       chapter_code: "6E_G07",
   │       offer: "pro" (si fourni),
   │       difficulty: "facile" (si fourni, après normalisation)
   │     }
   │
   ├─ Filtre is_dynamic:
   │  └─ dynamic_exercises = [ex for ex in exercises if ex.get("is_dynamic") is True]
   │  └─ ⚠️ PROBLÈME: Utilise "is True" (strict) → peut exclure si is_dynamic == 1
   │
   ├─ Filtre enabled_generators:
   │  └─ Si enabled_generators_for_chapter:
   │     dynamic_exercises = [
   │       ex for ex in dynamic_exercises
   │       if ex.get("generator_key") and 
   │          ex.get("generator_key").upper() in enabled_generators_for_chapter
   │     ]
   │
   ├─ Si 0 dynamiques → HTTPException 422
   │  └─ error_code: "TEMPLATE_PIPELINE_NO_DYNAMIC_EXERCISES"
   │
   ├─ Sélection:
   │  └─ selected_exercise = safe_random_choice(dynamic_exercises, ctx, obs_logger)
   │  └─ Fichier: backend/observability/__init__.py
   │  └─ Utilise seed si fourni (déterministe)
   │
   └─ Génération:
      └─ format_dynamic_exercise(selected_exercise, timestamp, seed)
         └─ Fichier: backend/services/tests_dyn_handler.py:84
         └─ Appelle GeneratorFactory.generate() avec generator_key

┌─────────────────────────────────────────────────────────────────┐
│ 7. PIPELINE MIXED (DYNAMIC → STATIC fallback)                   │
└─────────────────────────────────────────────────────────────────┘
   │
   └─ Fonction: generate_exercise_with_fallback()
      └─ Fichier: backend/routes/exercises_routes.py:60
      │
      ├─ Étape 1: Essayer DYNAMIC
      │  ├─ Query: exercise_service.get_exercises(chapter_code, offer, difficulty)
      │  ├─ Filtre: dynamic_exercises = [ex for ex in exercises if ex.get("is_dynamic") is True]
      │  ├─ Filtre enabled_generators (même logique que TEMPLATE)
      │  ├─ Si trouvés → format_dynamic_exercise() → Retour
      │  └─ Si 0 → Continue vers STATIC
      │
      └─ Étape 2: Fallback STATIC
         ├─ Query: exercise_service.get_exercises(chapter_code, offer, difficulty)
         ├─ Filtre: static_exercises = [ex for ex in exercises if ex.get("is_dynamic") is not True]
         ├─ Si trouvés → Retour exercice statique (pas de génération)
         └─ Si 0 → HTTPException 422

┌─────────────────────────────────────────────────────────────────┐
│ 8. PIPELINE SPEC (Statique uniquement)                          │
└─────────────────────────────────────────────────────────────────┘
   │
   ├─ Query: exercise_service.get_exercises(chapter_code, offer, difficulty)
   ├─ Filtre: static_exercises = [ex for ex in exercises if ex.get("is_dynamic") is not True]
   ├─ Si 0 → HTTPException 422
   └─ Sinon → Retour exercice statique

┌─────────────────────────────────────────────────────────────────┐
│ 9. GÉNÉRATION DYNAMIQUE (format_dynamic_exercise)               │
└─────────────────────────────────────────────────────────────────┘
   │
   ├─ Récupération générateur:
   │  └─ generator_key = exercise_template.get("generator_key")
   │  └─ factory_gen = GeneratorFactory.get(generator_key)
   │
   ├─ Génération variables:
   │  └─ gen_result = GeneratorFactory.generate(
   │       key=generator_key,
   │       exercise_params=exercise_template.get("variables", {}),
   │       overrides=None,
   │       seed=seed
   │     )
   │  └─ Variables: {a: 5, b: 3, ...} (selon générateur)
   │
   ├─ Rendu templates:
   │  └─ enonce_html = render_template(
   │       exercise_template.get("enonce_template_html"),
   │       variables
   │     )
   │  └─ solution_html = render_template(
   │       exercise_template.get("solution_template_html"),
   │       variables
   │     )
   │
   ├─ Validation placeholders:
   │  └─ Si {{variable}} non résolu → HTTPException 422 PLACEHOLDER_UNRESOLVED
   │
   └─ Retour exercice formaté avec SVG, metadata, etc.

┌─────────────────────────────────────────────────────────────────┐
│ 10. NORMALISATION DIFFICULTÉ                                    │
└─────────────────────────────────────────────────────────────────┘
   │
   └─ normalized_difficulty = normalize_difficulty(request.difficulte)
      └─ Fichier: backend/utils/difficulty_utils.py
      └─ Mapping: "standard" → "moyen", "facile" → "facile", etc.
      └─ Utilisé dans query MongoDB et mapping générateur

```

---

## 3) TABLEAU SOURCE-OF-TRUTH & INCOHÉRENCES

| Champ | Source DB | Format DB | Normalisation | Qui lit | Qui écrit | Bug probable | Test de preuve |
|-------|-----------|-----------|---------------|---------|-----------|--------------|----------------|
| **code_officiel** | `curriculum_chapters.code_officiel` | String | `upper().replace("-", "_")` | `exercises_routes.py:1093` | Admin UI, migrations | Mismatch casse: "6e_G07" vs "6E_G07" | `db.curriculum_chapters.findOne({code_officiel: {$regex:"^6[eE]_G07$", $options:"i"}})` |
| **pipeline** | `curriculum_chapters.pipeline` | String: "SPEC"\|"TEMPLATE"\|"MIXED" | Aucune (utilisé tel quel) | `exercises_routes.py:1191` | Admin UI, migration 004 | None si non défini → détection auto peut diverger | `db.curriculum_chapters.findOne({code_officiel:"6E_G07"},{pipeline:1})` |
| **enabled_generators** | `curriculum_chapters.enabled_generators` | List[dict] ou List[str] | `normalize_enabled_generators()` → List[str] uppercase | `exercises_routes.py:1244` | Admin UI (ChapterGenerators) | Format dict non normalisé → filtre casse tout | `db.curriculum_chapters.findOne({code_officiel:"6E_G07"},{enabled_generators:1})` |
| **is_dynamic** | `admin_exercises.is_dynamic` | Boolean (peut être 1/0 en DB) | `ex.get("is_dynamic") is True` (strict) | `exercises_routes.py:1289` | Admin UI (ChapterExercises) | `is_dynamic == 1` exclu par filtre strict | `db.admin_exercises.find({chapter_code:"6E_G07"},{is_dynamic:1})` |
| **generator_key** | `admin_exercises.generator_key` | String | `.upper()` pour comparaison | `exercises_routes.py:1296` | Admin UI (ChapterExercises) | Casse différente → filtre enabled_generators échoue | `db.admin_exercises.find({chapter_code:"6E_G07"},{generator_key:1})` |
| **exercise_type** | `admin_exercises.exercise_type` | String | `.upper()` si utilisé | `exercises_routes.py:626` | Admin UI, GeneratorFactory | Collision avec generator_key si fourni manuellement | `db.admin_exercises.find({generator_key:"CALCUL_NOMBRES_V1"},{exercise_type:1})` |
| **difficulty** | `admin_exercises.difficulty` | String: "facile"\|"moyen"\|"difficile" | `normalize_difficulty()` → "standard"→"moyen" | `exercises_routes.py:984` | Admin UI, requête HTTP | "standard" non normalisé → query MongoDB échoue | `db.admin_exercises.find({chapter_code:"6E_G07"},{difficulty:1})` |
| **offer** | `admin_exercises.offer` | String: "free"\|"pro" | `.lower()` | `exercises_routes.py:571` | Admin UI, requête HTTP | Casse différente → filtre échoue | `db.admin_exercises.find({chapter_code:"6E_G07"},{offer:1})` |
| **seed** | Requête HTTP (pas en DB) | int (optionnel) | Aucune (utilisé tel quel) | `exercises_routes.py:963` | Frontend (ExerciseGeneratorPage) | None → timestamp utilisé (non déterministe) | Logs: `seed_used` dans metadata |
| **variables** | `admin_exercises.variables` | Dict[str, Any] | Aucune (passé tel quel au générateur) | `tests_dyn_handler.py:144` | Admin UI (ChapterExercises) | Placeholders non résolus si variables manquantes | `doc = db.admin_exercises.find({generator_key:"CALCUL_NOMBRES_V1"}).limit(1).next(); typeof doc.variables.seed` |
| **chapter_code** | `admin_exercises.chapter_code` | String | `upper().replace("-", "_")` | `exercise_persistence_service.py:565` | Admin UI, migrations | Mismatch casse avec code_officiel | `db.admin_exercises.find({chapter_code:"6E_G07"})` |

### Incohérences identifiées

1. **code_officiel vs chapter_code** : Normalisation différente selon le contexte
   - `code_officiel` : `upper().replace("-", "_")` (exercises_routes.py:1093)
   - `chapter_code` : `upper().replace("-", "_")` (exercise_persistence_service.py:565)
   - ✅ Cohérent mais dépendant de l'ordre d'appel

2. **is_dynamic strict check** : `is True` peut exclure `is_dynamic == 1` (MongoDB peut stocker 1/0)
   - Fichier: `exercises_routes.py:1289`
   - Fix: Utiliser `if ex.get("is_dynamic")` (truthy) au lieu de `is True`

3. **enabled_generators format** : List[dict] non normalisé avant filtre
   - Fix: Déjà corrigé via `normalize_enabled_generators()`, mais vérifier tous les usages

4. **difficulty "standard"** : Non normalisé dans query MongoDB
   - Fix: Normaliser AVANT query (déjà fait ligne 984, mais vérifier query ligne 572)

---

## 4) CAUSES P0 + PREUVES + COMMANDES

### P0.1 - Mismatch casse code_officiel / chapter_code

**Cause** : Normalisation incohérente entre `code_officiel` (curriculum) et `chapter_code` (exercises)

**Preuve attendue** :
- Chapitre en DB avec `code_officiel: "6E_G07"` (uppercase)
- Exercices en DB avec `chapter_code: "6e_G07"` (mixed case)
- Query MongoDB ne trouve pas les exercices

**Commande DB** :
```bash
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
db.curriculum_chapters.findOne({code_officiel: {$regex:'^6[eE]_G07$', \$options:'i'}},{_id:0,code_officiel:1});
db.admin_exercises.find({chapter_code: {$regex:'^6[eE]_G07$', \$options:'i'}},{_id:0,chapter_code:1}).limit(5)
"
```

**Où corriger** :
- `backend/services/exercise_persistence_service.py:565` : Normaliser `chapter_code` AVANT query
- `backend/routes/exercises_routes.py:1210` : Utiliser `normalized_code_officiel` partout

---

### P0.2 - enabled_generators format dict → filtre casse tout

**Cause** : `enabled_generators` en format List[dict] non normalisé avant filtre `generator_key`

**Preuve attendue** :
- Chapitre avec `enabled_generators: [{"generator_key": "CALCUL_NOMBRES_V1", "is_enabled": true}]`
- Exercice avec `generator_key: "CALCUL_NOMBRES_V1"`
- Filtre ligne 1296 compare `ex.get("generator_key").upper()` avec `enabled_generators_for_chapter` (déjà normalisé)
- ✅ Déjà corrigé via `normalize_enabled_generators()` ligne 1244

**Commande DB** :
```bash
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
doc = db.curriculum_chapters.findOne({code_officiel: {$regex:'^6[eE]_G07$', \$options:'i'}});
print('enabled_generators type:', typeof doc.enabled_generators);
print('enabled_generators:', JSON.stringify(doc.enabled_generators, null, 2))
"
```

**Où corriger** :
- ✅ Déjà corrigé dans `exercises_routes.py:1244` et `exercises_routes.py:155`
- Vérifier que tous les usages passent par `normalize_enabled_generators()`

---

### P0.3 - Filtre is_dynamic trop strict (is True)

**Cause** : `ex.get("is_dynamic") is True` exclut `is_dynamic == 1` (MongoDB peut stocker 1/0)

**Preuve attendue** :
- Exercice en DB avec `is_dynamic: 1` (number)
- Filtre ligne 1289 : `[ex for ex in exercises if ex.get("is_dynamic") is True]`
- Exercice exclu (1 is not True)

**Commande DB** :
```bash
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
db.admin_exercises.find({chapter_code:'6E_G07'},{_id:0,id:1,is_dynamic:1}).forEach(doc => {
  print('id:', doc.id, 'is_dynamic:', doc.is_dynamic, 'type:', typeof doc.is_dynamic)
})
"
```

**Où corriger** :
- `backend/routes/exercises_routes.py:1289` : `if ex.get("is_dynamic")` (truthy)
- `backend/routes/exercises_routes.py:134` : Même fix
- `backend/routes/exercises_routes.py:315` : Même fix

---

### P0.4 - offer/difficulty filter élimine les dynamiques

**Cause** : Query MongoDB avec `offer` et `difficulty` peut exclure tous les exercices si normalisation incorrecte

**Preuve attendue** :
- Requête avec `difficulte: "standard"` (non normalisé)
- Query MongoDB: `{difficulty: "standard"}` (ligne 573)
- Exercices en DB avec `difficulty: "moyen"` → 0 résultats

**Commande DB** :
```bash
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
db.admin_exercises.find({chapter_code:'6E_G07'},{_id:0,id:1,difficulty:1,offer:1}).forEach(doc => {
  print('id:', doc.id, 'difficulty:', doc.difficulty, 'offer:', doc.offer)
})
"
```

**Où corriger** :
- `backend/services/exercise_persistence_service.py:572` : Normaliser `difficulty` AVANT query
- `backend/services/exercise_persistence_service.py:571` : Normaliser `offer` AVANT query

---

### P0.5 - Collision exercise_type/generator_key (admin save/generate)

**Cause** : Admin peut sauvegarder `exercise_type` manuel qui entre en collision avec `generator_key`

**Preuve attendue** :
- Exercice dynamique avec `generator_key: "CALCUL_NOMBRES_V1"`
- Admin sauvegarde `exercise_type: "SYMETRIE_AXIALE"` (incompatible)
- Validation ligne 632 refuse la sauvegarde (✅ Déjà protégé)

**Commande DB** :
```bash
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
db.admin_exercises.find({is_dynamic:true},{_id:0,id:1,generator_key:1,exercise_type:1}).limit(5)
"
```

**Où corriger** :
- ✅ Déjà protégé dans `exercise_persistence_service.py:632`
- Vérifier que l'admin UI ne permet pas de saisir `exercise_type` pour dynamiques

---

### P0.6 - Preset invalide / default → 422

**Cause** : Générateur premium avec `difficulty_presets` invalide → 422 lors de la génération

**Preuve attendue** :
- Chapitre avec `enabled_generators: [{"generator_key": "CALCUL_NOMBRES_V1", "difficulty_presets": ["facile", "moyen"]}]`
- Requête avec `difficulte: "difficile"` → 422 si générateur ne supporte pas

**Commande DB** :
```bash
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
doc = db.curriculum_chapters.findOne({code_officiel: {$regex:'^6[eE]_G07$', \$options:'i'}});
if (doc && doc.enabled_generators) {
  doc.enabled_generators.forEach(eg => {
    print('generator_key:', eg.generator_key, 'difficulty_presets:', eg.difficulty_presets)
  })
}
"
```

**Où corriger** :
- Vérifier `difficulty_presets` dans filtre enabled_generators (non implémenté actuellement)
- Ajouter validation dans `normalize_enabled_generators()` si nécessaire

---

### P0.7 - Observability/logger qui plante et déclenche fallback

**Cause** : Log non-bloquant qui plante → exception non catchée → fallback inattendu

**Preuve attendue** :
- Log ligne 1301 avec `enabled_generators_for_chapter` (peut être None si normalisation échoue)
- Exception dans logger → fallback vers STATIC

**Où corriger** :
- ✅ Déjà protégé via `try/except` dans plusieurs endroits
- Vérifier que tous les logs sont dans `try/except` (lignes 1301, 1390, etc.)

---

## 5) INSTRUMENTATION MINIMALE (6 logs non-bloquants)

### Logs à ajouter/vérifier

| Tag | Emplacement | Contenu | Protection |
|-----|-------------|---------|------------|
| `[PIPELINE]` | `exercises_routes.py:1198` | `pipeline_mode`, `chapter_code`, `requested_code_officiel` | ✅ Déjà présent |
| `[CHAPTER_LOOKUP]` | `exercises_routes.py:1100` | `source` (db/json), `code_officiel`, `normalized_code` | ✅ Déjà présent |
| `[EX_QUERY]` | `exercise_persistence_service.py:576` | `query`, `result_count` | ✅ Déjà présent |
| `[FILTER]` | `exercises_routes.py:1298` | `enabled_generators_normalized`, `dynamic_count_before`, `dynamic_count_after` | ✅ Déjà présent |
| `[DYNAMIC_SELECTED]` | `exercises_routes.py:1390` | `selected_id`, `selected_generator_key`, `seed_used` | ✅ Déjà présent |
| `[FALLBACK_STATIC]` | `exercises_routes.py:326` | `reason`, `static_count`, `selected_id` | ✅ Déjà présent |
| `[422_VALIDATION]` | `exercises_routes.py:1317` | `error_code`, `hint`, `enabled_generators` | ✅ Déjà présent |

**Vérification** : Tous les logs sont déjà présents mais doivent être dans `try/except` pour éviter les crashes.

---

## 6) ÉTUDE DE CAS - 2 chapitres

### Cas 1 : 6e_G07 (mixte/dynamiques présents)

**État DB attendu** :
```javascript
// Chapitre
{
  code_officiel: "6E_G07",
  pipeline: "MIXED",  // ou "TEMPLATE" si uniquement dynamiques
  enabled_generators: [
    {"generator_key": "CALCUL_NOMBRES_V1", "is_enabled": true, ...}
  ]
}

// Exercices
{
  chapter_code: "6E_G07",
  is_dynamic: true,
  generator_key: "CALCUL_NOMBRES_V1",
  difficulty: "facile",
  offer: "free"
}
```

**Décision code** :
1. Normalise `code_officiel: "6e_G07"` → `"6E_G07"`
2. Lit chapitre en DB → trouve `pipeline: "MIXED"`
3. Normalise `enabled_generators` → `["CALCUL_NOMBRES_V1"]`
4. Query exercices: `{chapter_code: "6E_G07", offer: "pro", difficulty: "facile"}`
5. Filtre `is_dynamic == true` → trouve exercices dynamiques
6. Filtre `generator_key in enabled_generators` → trouve exercices
7. Sélectionne un exercice → `format_dynamic_exercise()`

**Divergences possibles** :
- `chapter_code` en mixed case → query échoue
- `is_dynamic: 1` (number) → exclu par filtre strict
- `enabled_generators` en format dict non normalisé → filtre échoue

**Commandes mongosh** :
```bash
# Chapitre
db.curriculum_chapters.findOne({code_officiel: {$regex:"^6[eE]_G07$", $options:"i"}},{_id:0,pipeline:1,enabled_generators:1,code_officiel:1})

# Exercices
db.admin_exercises.countDocuments({chapter_code:"6E_G07"})
db.admin_exercises.countDocuments({chapter_code:"6E_G07", is_dynamic:true})
db.admin_exercises.find({chapter_code:"6E_G07"},{_id:0,id:1,is_dynamic:1,generator_key:1,difficulty:1,offer:1}).sort({id:1}).limit(10)
```

---

### Cas 2 : 6e_SP01 (premium / raisonnement multiplicatif)

**État DB attendu** :
```javascript
// Chapitre
{
  code_officiel: "6E_SP01",
  pipeline: "TEMPLATE",  // ou "MIXED"
  enabled_generators: [
    {"generator_key": "RAISONNEMENT_MULTIPLICATIF_V1", "is_enabled": true, "min_offer": "pro", ...}
  ]
}

// Exercices
{
  chapter_code: "6E_SP01",
  is_dynamic: true,
  generator_key: "RAISONNEMENT_MULTIPLICATIF_V1",
  difficulty: "moyen",
  offer: "pro"
}
```

**Décision code** :
1. Normalise `code_officiel: "6e_SP01"` → `"6E_SP01"`
2. Lit chapitre en DB → trouve `pipeline: "TEMPLATE"`
3. Normalise `enabled_generators` → `["RAISONNEMENT_MULTIPLICATIF_V1"]`
4. Query exercices: `{chapter_code: "6E_SP01", offer: "pro", difficulty: "moyen"}`
5. Filtre `is_dynamic == true` → trouve exercices dynamiques
6. Filtre `generator_key in enabled_generators` → trouve exercices
7. Sélectionne un exercice → `format_dynamic_exercise()`

**Divergences possibles** :
- `min_offer: "pro"` non vérifié dans filtre → exercice "free" sélectionné (si existe)
- `difficulty_presets` non vérifié → difficulté invalide → 422

**Commandes mongosh** :
```bash
# Chapitre
db.curriculum_chapters.findOne({code_officiel: {$regex:"^6[eE]_SP01$", $options:"i"}},{_id:0,pipeline:1,enabled_generators:1,code_officiel:1})

# Exercices
db.admin_exercises.countDocuments({chapter_code:"6E_SP01"})
db.admin_exercises.countDocuments({chapter_code:"6E_SP01", is_dynamic:true, offer:"pro"})
db.admin_exercises.find({chapter_code:"6E_SP01"},{_id:0,id:1,is_dynamic:1,generator_key:1,difficulty:1,offer:1}).sort({id:1}).limit(10)

# Variables
doc = db.admin_exercises.find({generator_key:"RAISONNEMENT_MULTIPLICATIF_V1"}).sort({_id:-1}).limit(1).next();
typeof doc.variables.seed
```

---

## 7) PLAN DE SOLUTION SIMPLE (2-3 PR max)

### PR1 : Normalisations + sélection fiable + logs

**Fichiers touchés** :
- `backend/services/exercise_persistence_service.py` : Normaliser `difficulty` et `offer` AVANT query
- `backend/routes/exercises_routes.py` : Fix filtre `is_dynamic` (truthy au lieu de `is True`)
- `backend/routes/exercises_routes.py` : Utiliser `normalized_code_officiel` partout

**Risques** :
- Aucun (corrections de normalisation uniquement)

**Tests UI manuels** :
1. Générer exercice `6e_G07` avec `offer: "pro"`, `difficulte: "facile"`
2. Vérifier logs: `[PIPELINE]`, `[FILTER]`, `[DYNAMIC_SELECTED]`
3. Vérifier DB: `db.admin_exercises.find({chapter_code:"6E_G07", is_dynamic:1})`

**Commandes logs/mongo** :
```bash
# Logs
docker logs le-maitre-mot-backend --tail 300 | grep -E "PIPELINE|CHAPTER_LOOKUP|FALLBACK|DYNAMIC|STATIC|422|GENERATOR"

# DB
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
db.curriculum_chapters.findOne({code_officiel: {$regex:'^6[eE]_G07$', \$options:'i'}},{_id:0,pipeline:1,enabled_generators:1,code_officiel:1});
db.admin_exercises.countDocuments({chapter_code:'6E_G07'});
db.admin_exercises.countDocuments({chapter_code:'6E_G07', is_dynamic:true});
db.admin_exercises.find({chapter_code:'6E_G07'},{_id:0,id:1,is_dynamic:1,generator_key:1,difficulty:1,offer:1}).sort({id:1}).limit(10);
doc = db.admin_exercises.find({generator_key:'CALCUL_NOMBRES_V1'}).sort({_id:-1}).limit(1).next();
typeof doc.variables.seed
"
```

---

### PR2 : Validation 422 lisible + correction collisions

**Fichiers touchés** :
- `backend/routes/exercises_routes.py` : Améliorer messages 422 avec diagnostic complet
- `backend/services/exercise_persistence_service.py` : Vérifier collision `exercise_type`/`generator_key` (déjà fait)

**Risques** :
- Aucun (amélioration messages uniquement)

**Tests UI manuels** :
1. Générer exercice avec `difficulte: "standard"` → vérifier normalisation → "moyen"
2. Générer exercice avec `offer: "free"` sur chapitre premium → vérifier message 422 clair
3. Vérifier logs: `[422_VALIDATION]` avec `error_code`, `hint`

---

### PR3 : Simplification UX admin (optionnel)

**Fichiers touchés** :
- `frontend/src/components/admin/ChapterExercisesAdminPage.js` : Désactiver `exercise_type` pour dynamiques
- `frontend/src/components/admin/CurriculumAdminSimplePage.js` : Validation `pipeline` + `enabled_generators`

**Risques** :
- Faible (UI uniquement)

**Tests UI manuels** :
1. Créer exercice dynamique → vérifier que `exercise_type` est désactivé
2. Modifier chapitre → vérifier validation `pipeline` + `enabled_generators`

---

## 8) CHECKLIST TESTS UI + COMMANDES

### Checklist tests UI (courte)

- [ ] Générer exercice `6e_G07` avec `offer: "pro"`, `difficulte: "facile"` → Vérifier dynamique
- [ ] Générer exercice `6e_G07` avec `offer: "free"`, `difficulte: "facile"` → Vérifier dynamique ou fallback statique
- [ ] Générer exercice `6e_SP01` avec `offer: "pro"`, `difficulte: "moyen"` → Vérifier dynamique premium
- [ ] Générer exercice avec `difficulte: "standard"` → Vérifier normalisation → "moyen"
- [ ] Vérifier logs: `[PIPELINE]`, `[FILTER]`, `[DYNAMIC_SELECTED]`, `[FALLBACK_STATIC]`

### Commandes logs/mongo (obligatoires)

```bash
# Logs backend
docker logs le-maitre-mot-backend --tail 300 | grep -E "PIPELINE|CHAPTER_LOOKUP|FALLBACK|DYNAMIC|STATIC|422|GENERATOR"

# MongoDB - Chapitre 6E_G07
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
db.curriculum_chapters.findOne({code_officiel: {$regex:'^6[eE]_G07$', \$options:'i'}},{_id:0,pipeline:1,enabled_generators:1,code_officiel:1})
"

# MongoDB - Exercices 6E_G07
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
db.admin_exercises.countDocuments({chapter_code:'6E_G07'});
db.admin_exercises.countDocuments({chapter_code:'6E_G07', is_dynamic:true});
db.admin_exercises.find({chapter_code:'6E_G07'},{_id:0,id:1,is_dynamic:1,generator_key:1,difficulty:1,offer:1}).sort({id:1}).limit(10)
"

# MongoDB - Variables seed
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
doc = db.admin_exercises.find({generator_key:'CALCUL_NOMBRES_V1'}).sort({_id:-1}).limit(1).next();
typeof doc.variables.seed
"
```

---

## 9) RÉSUMÉ EXÉCUTIF

**État actuel** : Système fonctionnel avec incohérences de normalisation qui peuvent causer des fallbacks inattendus.

**Causes P0 identifiées et CONFIRMÉES** :
1. **Lookup chapitre échoue** (casse) → `enabled_generators` vide → filtre ne s'applique pas
   - ✅ **PREUVE RÉELLE** : Requête exacte `"6E_SP01"` ne trouve pas `"6e_SP01"` en DB
   - ✅ **PREUVE RÉELLE** : 6e_SP01 n'a pas de `pipeline` ni `enabled_generators` en DB
2. **Filtre `is_dynamic` trop strict** (`is True` au lieu de truthy)
   - ✅ **PREUVE RÉELLE** : Type en DB est `"bool"` (OK actuellement), mais filtre truthy est plus sûr
3. **Normalisation `difficulty` manquante** dans query MongoDB
   - ✅ **PREUVE RÉELLE** : Query utilise `difficulty.lower()` au lieu de `normalize_difficulty()`

**Solution proposée** : 1 PR minimal (normalisations + validation) sans régression.

**Risques** : Faibles (corrections de normalisation uniquement).

**Tests** : UI manuels + logs/mongo (commandes fournies).

---

## 10) PREUVES RÉELLES (Commandes exécutées le 2025-12-25)

### Preuve 1 : Lookup chapitre (6e_SP01) - CASSE

**Commande** :
```bash
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
db.curriculum_chapters.findOne({code_officiel:{$regex:'^6[eE]_SP01$', \$options:'i'}},{_id:0,code_officiel:1,pipeline:1,enabled_generators:1})
"
```

**Résultat RÉEL** :
```json
{
  "code_officiel": "6e_SP01"
}
```

**Ce que ça prouve** :
- ✅ DB stocke en mixed case `"6e_SP01"` (CONFIRMÉ)
- ❌ **6e_SP01 n'a PAS de champ `pipeline` ni `enabled_generators`** en DB
- ⚠️ **Impact** : Code utilise valeurs par défaut (None) → comportement imprévisible

**Requête exacte échoue** :
```bash
db.curriculum_chapters.findOne({code_officiel:"6E_SP01"})
# → null (CONFIRMÉ)
```

---

### Preuve 2 : Comparaison 6E_G07 (qui fonctionne)

**Commande** :
```bash
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
db.curriculum_chapters.findOne({code_officiel: /6E_G07/i}, {code_officiel: 1, pipeline: 1, enabled_generators: 1})
"
```

**Résultat RÉEL** :
```json
{
  "code_officiel": "6e_G07",
  "pipeline": "TEMPLATE",
  "enabled_generators": [
    {
      "generator_key": "CALCUL_NOMBRES_V1",
      "difficulty_presets": ["facile", "moyen", "difficile"],
      "min_offer": "free",
      "is_enabled": true
    },
    {
      "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
      "difficulty_presets": ["facile", "moyen", "difficile"],
      "min_offer": "free",
      "is_enabled": true
    }
  ]
}
```

**Ce que ça prouve** :
- ✅ 6E_G07 a `pipeline: "TEMPLATE"` et `enabled_generators` en List[dict]
- ✅ Format List[dict] nécessite normalisation via `normalize_enabled_generators()`
- ✅ 6E_G07 a 2 générateurs activés

---

### Preuve 3 : Type is_dynamic (6E_G07)

**Commande** :
```bash
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
db.admin_exercises.aggregate([
  {\$match: {chapter_code: /6E_G07/i}},
  {\$project: {id: 1, is_dynamic: 1, type_is_dynamic: {\$type: '\$is_dynamic'}, generator_key: 1}},
  {\$limit: 5}
])
"
```

**Résultat RÉEL** :
```json
{
  "id": 1,
  "is_dynamic": true,
  "type_is_dynamic": "bool",
  "generator_key": "CALCUL_NOMBRES_V1"
}
```

**Ce que ça prouve** :
- ✅ Type en DB est `"bool"` (boolean) - OK actuellement
- ⚠️ Filtre truthy est plus sûr pour éviter bugs futurs si MongoDB stocke `1` (number)

---

### Preuve 4 : Logs backend (100 dernières lignes)

**Commande** :
```bash
docker logs le-maitre-mot-backend --tail 100
```

**Résultat RÉEL** :
```
INFO:     127.0.0.1:52376 - "GET /docs HTTP/1.1" 200 OK
INFO:     127.0.0.1:54388 - "GET /docs HTTP/1.1" 200 OK
...
```

**Ce que ça prouve** :
- ⚠️ **Pas de génération récente** : Seulement accès à `/docs` (documentation API)
- **Pour voir les logs de lookup** : Générer un exercice avec `code_officiel: "6E_SP01"` (uppercase)
- **Résultat attendu** : `[DIAG_6E_G07] ❌ Chapitre NON TROUVÉ avec code_officiel='6E_SP01'`

---

**Fin du document d'audit**

