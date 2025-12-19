# INCIDENT — Chapitre "indisponible" et mauvais pipeline de génération

**ID**: INCIDENT_2025-12-18_chapitre_indisponible_pipeline_incorrect  
**Date**: 2025-12-18  
**Type**: 🐛 Bug fix (catalogue + pipeline génération)

---

## 📋 SYMPTÔME

- **Contexte**: Chapitre créé avec des exercices dynamiques en DB (collection `exercises`)
- **Problème 1**: Le chapitre apparaît "indisponible" dans le générateur (badge "indispo")
- **Problème 2**: Si on force un générateur dans le curriculum, la génération part sur le mauvais pipeline (statique au lieu de dynamique)
- **Comportement observé**: 
  - Chapitre ancien créé/testé par l'agent apparaît dispo car il a un `generator`/`exercise_type` renseigné dans le curriculum
  - Chapitre nouveau avec exercices dynamiques en DB reste "indisponible" tant qu'on ne force pas un générateur dans le curriculum
  - Si on force un générateur, la génération utilise le pipeline statique (`MathGenerationService`) au lieu du pipeline dynamique (exercises collection)

---

## 🔍 ROOT CAUSE

### Problème 1 : Catalogue "indisponible"

**Source de vérité incomplète** : Le catalogue (`get_catalog()`) utilisait uniquement `curriculum.exercise_types` pour déterminer si un chapitre a des générateurs (`hasGenerators: true`).

**Fichier** : `backend/curriculum/loader.py::get_catalog()`

**Ligne 388** : `"generators": chapter.exercise_types`

**Problème** :
- Si un chapitre a des exercices en DB mais pas d'`exercise_types` dans le curriculum → `generators: []` → `hasGenerators: false` → badge "indisponible"
- Le catalogue ne vérifiait pas la collection `exercises` pour enrichir les `generators`

### Problème 2 : Mauvais pipeline de génération

**Ordre de vérification incorrect** : La route `/generate` ne vérifiait pas les exercices dynamiques en DB avant de passer au pipeline statique.

**Fichier** : `backend/routes/exercises_routes.py::generate_exercise()`

**Problème** :
- La route vérifiait d'abord GM07, GM08, TESTS_DYN (handlers spécifiques)
- Puis passait directement au pipeline statique (`MathGenerationService`)
- Ne vérifiait jamais si des exercices dynamiques existaient en DB pour le chapitre demandé
- Résultat : si on forçait un générateur dans le curriculum, la génération utilisait le pipeline statique au lieu du pipeline dynamique

---

## ✅ FIX APPLIQUÉ

### 1. Enrichissement du catalogue depuis la DB

**Fichier** : `backend/curriculum/loader.py`

**Modification** : `get_catalog()` est maintenant `async` et accepte un paramètre `db` optionnel.

**Stratégie** :
1. **Source principale** : `curriculum.exercise_types` (comme avant)
2. **Enrichissement DB** : Si `db` est fourni, vérifier si des exercices existent en DB pour chaque chapitre
3. **Fusion** : Si des exercices existent, extraire les `exercise_types` depuis la DB et fusionner avec le curriculum (sans doublons)
4. **Logging explicite** : Log `INFO` quand un chapitre est enrichi depuis la DB

**Code clé** :
```python
# Enrichissement depuis DB si exercices existent
if sync_service:
    has_exercises = await sync_service.has_exercises_in_db(chapter.code_officiel)
    if has_exercises:
        exercise_types_from_db = await sync_service.get_exercise_types_from_db(chapter.code_officiel)
        if exercise_types_from_db:
            # Fusion : curriculum + DB (sans doublons)
            generators_final = sorted(list(set(generators_from_curriculum) | exercise_types_from_db))
```

**Avantages** :
- ✅ Chapitres avec exercices en DB deviennent automatiquement disponibles
- ✅ Plus besoin de forcer un générateur dans le curriculum
- ✅ Source de vérité enrichie : curriculum + DB

### 2. Vérification exercices dynamiques avant pipeline statique

**Fichier** : `backend/routes/exercises_routes.py`

**Modification** : Ajout d'une vérification **avant** la résolution du mode (code_officiel vs legacy).

**Stratégie** :
1. **Vérifier d'abord** : Si des exercices dynamiques existent en DB pour le chapitre
2. **Si oui** : Utiliser le pipeline dynamique (`format_dynamic_exercise` depuis la collection `exercises`)
3. **Si non** : Continuer avec le pipeline statique (`MathGenerationService`)

**Code clé** :
```python
# Vérifier si des exercices dynamiques existent en DB
has_dynamic_exercises = False
if chapter_code_for_db:
    has_exercises = await sync_service.has_exercises_in_db(chapter_code_for_db)
    if has_exercises:
        exercises = await exercise_service.get_exercises(...)
        dynamic_exercises = [ex for ex in exercises if ex.get("is_dynamic") is True]
        has_dynamic_exercises = len(dynamic_exercises) > 0
        
        if has_dynamic_exercises:
            # Utiliser le pipeline DYNAMIQUE
            selected_exercise = random.choice(dynamic_exercises)
            dyn_exercise = format_dynamic_exercise(...)
            return dyn_exercise
```

**Avantages** :
- ✅ Pipeline dynamique utilisé automatiquement si exercices dynamiques existent en DB
- ✅ Plus de confusion entre pipeline statique et dynamique
- ✅ Logging explicite sur la décision (statique vs dynamique)

### 3. Logs explicites

**Ajouts** :
- `[CATALOG]` : Logs sur l'enrichissement depuis DB
- `[GENERATE]` : Logs sur la décision pipeline (statique vs dynamique)
- Logs `INFO` pour les cas normaux, `WARNING` pour les erreurs (fallback)

**Exemples** :
```
[CATALOG] Chapitre 6E_G07_DYN enrichi depuis DB: curriculum=[] → final=['SYMETRIE_AXIALE']
[GENERATE] Chapitre 6E_G07_DYN a 3 exercices dynamiques en DB. Utilisation du pipeline DYNAMIQUE.
[GENERATE] ✅ Exercice dynamique généré depuis DB: chapter_code=6E_G07_DYN, exercise_id=1, generator_key=SYMETRIE_AXIALE_V2
```

### 4. Fonctions utilitaires ajoutées

**Fichier** : `backend/services/curriculum_sync_service.py`

**Nouvelles fonctions** :
- `has_exercises_in_db(chapter_code)` : Vérifie si au moins un exercice existe en DB
- `get_exercise_types_from_db(chapter_code)` : Extrait les `exercise_types` depuis la DB (réutilise `extract_exercise_types_from_chapter`)

---

## 🧪 TESTS / PREUVE

### Test 1 : Catalogue enrichi depuis DB

1. **Créer un exercice dynamique dans un nouveau chapitre** :
   ```bash
   curl -X POST http://localhost:8000/api/admin/chapters/6e_G07_DYN/exercises \
     -H "Content-Type: application/json" \
     -d '{
       "is_dynamic": true,
       "generator_key": "SYMETRIE_AXIALE_V2",
       "enonce_template_html": "<p>Test</p>",
       "solution_template_html": "<p>Solution</p>",
       "difficulty": "facile",
       "offer": "free"
     }'
   ```

2. **Vérifier le catalogue** :
   ```bash
   curl -s http://localhost:8000/api/v1/curriculum/6e/catalog | jq '.domains[].chapters[] | select(.code_officiel == "6e_G07_DYN")'
   ```
   - Doit retourner `generators: ["SYMETRIE_AXIALE"]` (non vide, même si curriculum vide)
   - Doit avoir `_debug_source: "curriculum+db"` (ou `"curriculum+db (identique)"`)

3. **Vérifier dans le frontend** :
   - Recharger le générateur
   - Le chapitre `6e_G07_DYN` doit apparaître **sans badge "indispo"**
   - `hasGenerators: true` → sélectionnable

### Test 2 : Pipeline dynamique utilisé automatiquement

1. **Générer un exercice pour le chapitre** :
   ```bash
   curl -X POST http://localhost:8000/api/v1/exercises/generate \
     -H "Content-Type: application/json" \
     -d '{
       "code_officiel": "6e_G07_DYN",
       "difficulte": "facile",
       "offer": "free",
       "seed": 12345
     }'
   ```

2. **Vérifier les logs backend** :
   ```bash
   docker compose logs backend | grep -i "GENERATE.*6E_G07_DYN"
   ```
   - Doit afficher : `[GENERATE] Chapitre 6E_G07_DYN a X exercices dynamiques en DB. Utilisation du pipeline DYNAMIQUE.`
   - Doit afficher : `[GENERATE] ✅ Exercice dynamique généré depuis DB: ...`

3. **Vérifier la réponse** :
   - Doit contenir `metadata.generator_key: "SYMETRIE_AXIALE_V2"` (ou autre selon l'exercice)
   - Doit contenir `metadata.source: "dynamic"` (ou équivalent)
   - **Ne doit PAS** utiliser le pipeline statique (`MathGenerationService`)

### Test 3 : Pipeline statique pour chapitres sans exercices dynamiques

1. **Générer un exercice pour un chapitre sans exercices dynamiques** :
   ```bash
   curl -X POST http://localhost:8000/api/v1/exercises/generate \
     -H "Content-Type: application/json" \
     -d '{
       "code_officiel": "6e_N08",
       "difficulte": "moyen",
       "offer": "free"
     }'
   ```

2. **Vérifier les logs** :
   ```bash
   docker compose logs backend | grep -i "GENERATE.*6E_N08"
   ```
   - Doit afficher : `[GENERATE] Chapitre 6E_N08 a des exercices en DB mais aucun dynamique. Utilisation du pipeline STATIQUE.`
   - Ou : Pas de log `[GENERATE]` (chapitre sans exercices en DB) → pipeline statique normal

---

## 🔧 COMMANDES DE REBUILD / RESTART

**Rebuild backend requis** :
```bash
docker compose build backend
docker compose restart backend
```

**Vérification** :
```bash
# Vérifier que le service est bien chargé
docker compose logs backend | grep -i "CATALOG\|GENERATE"
```

---

## 📝 RECOMMANDATIONS

1. **Performance** :
   - Le catalogue enrichit depuis DB à chaque requête (pas de cache)
   - Si performance dégradée, ajouter un cache TTL pour l'enrichissement DB

2. **Monitoring** :
   - Surveiller les logs `[CATALOG]` pour détecter les enrichissements
   - Surveiller les logs `[GENERATE]` pour vérifier que le bon pipeline est utilisé

3. **Documentation** :
   - Documenter que le catalogue utilise maintenant curriculum + DB comme source de vérité
   - Documenter que le pipeline dynamique a priorité sur le pipeline statique si exercices dynamiques existent en DB

---

## 🔗 FICHIERS IMPACTÉS

- `backend/curriculum/loader.py` : Enrichissement catalogue depuis DB
- `backend/routes/curriculum_catalog_routes.py` : Passage de `db` à `get_catalog()`
- `backend/routes/exercises_routes.py` : Vérification exercices dynamiques avant pipeline statique
- `backend/services/curriculum_sync_service.py` : Fonctions utilitaires `has_exercises_in_db()` et `get_exercise_types_from_db()`
- `docs/incidents/INCIDENT_2025-12-18_chapitre_indisponible_pipeline_incorrect.md` : Ce document
- `docs/CHANGELOG_TECH.md` : Entrée ajoutée

---

## ✅ VALIDATION

- [x] Catalogue enrichi depuis DB si exercices existent
- [x] Pipeline dynamique utilisé automatiquement si exercices dynamiques en DB
- [x] Logs explicites sur la décision (curriculum vs exercises, statique vs dynamique)
- [x] Tests manuels documentés
- [x] Document d'incident créé
- [x] Changelog mis à jour

---

## 🎯 EFFET ATTENDU

**Chapitres disponibles automatiquement** :
- Création d'exercices dynamiques en DB → extraction automatique des `exercise_types` → chapitre disponible dans le catalogue
- Plus besoin de forcer un générateur dans le curriculum

**Pipeline correct** :
- Exercices dynamiques en DB → pipeline dynamique utilisé automatiquement
- Pas d'exercices dynamiques → pipeline statique utilisé (comportement normal)
- Plus de confusion entre pipeline statique et dynamique

**Source de vérité enrichie** :
- Curriculum (source principale) + DB (enrichissement)
- Logs explicites pour le debugging


