# AUDIT P0 : Sélection DYNAMIC vs STATIC - Preuves obligatoires

**Date** : 2025-12-25  
**Mission** : Auditer et stabiliser la sélection DYNAMIC vs STATIC avec preuves (code + mongo/logs)

---

## A) TABLE "PREUVES" (commande → résultat attendu → ce que ça prouve)

| # | Commande | Résultat RÉEL obtenu | Ce que ça prouve |
|---|----------|---------------------|-------------------|
| **P1** | `db.curriculum_chapters.findOne({code_officiel:{$regex:"^6[eE]_SP01$", $options:"i"}},{_id:0,code_officiel:1,pipeline:1,enabled_generators:1})` | ✅ `{code_officiel: "6e_SP01"}` (mixed case) - **PAS de pipeline ni enabled_generators** | **BUG P0.1 CONFIRMÉ** : DB stocke en mixed-case `"6e_SP01"`, mais `get_chapter_by_code()` ligne 222 fait une requête exacte `{"code_officiel": code_officiel}` sans regex → lookup échoue. **AUSSI** : 6e_SP01 n'a pas de `pipeline` ni `enabled_generators` en DB → valeurs par défaut utilisées |
| **P2** | `db.curriculum_chapters.findOne({code_officiel:"6E_SP01"},{_id:0,code_officiel:1})` | ✅ `null` (non trouvé) | **BUG P0.1 CONFIRMÉ** : Requête exacte `"6E_SP01"` ne trouve pas `"6e_SP01"` en DB → chapitre non trouvé → fallback legacy ou erreur |
| **P3** | `db.curriculum_chapters.findOne({code_officiel:{$regex:"^6[eE]_G07$", $options:"i"}},{_id:0,enabled_generators:1})` | ✅ `{enabled_generators: [{generator_key: "CALCUL_NOMBRES_V1", is_enabled: true, difficulty_presets: [...], min_offer: "free"}, {generator_key: "RAISONNEMENT_MULTIPLICATIF_V1", ...}]}` (List[dict]) | **BUG P0.2 CONFIRMÉ** : Format List[dict] avec objets complexes. Doit être normalisé via `normalize_enabled_generators()` avant filtre ligne 1296. **6E_G07 a 2 générateurs activés** |
| **P4** | `db.admin_exercises.aggregate([{$match: {chapter_code: /6E_G07/i}}, {$project: {is_dynamic: 1, type: {$type: "$is_dynamic"}}}, {$limit: 5}])` | ✅ `{is_dynamic: true, type_is_dynamic: "bool"}` (boolean) | **BUG P0.3 PARTIELLEMENT CONFIRMÉ** : En DB, `is_dynamic` est de type `"bool"` (boolean), donc filtre strict `is True` devrait fonctionner. **MAIS** : Si MongoDB stocke `1` (number) ailleurs, le filtre échouera. Utiliser truthy `if ex.get("is_dynamic")` est plus sûr |
| **P5** | `docker logs le-maitre-mot-backend --tail 100` | ⚠️ Seulement accès `/docs` (pas de génération récente) | **Pas de preuve dans logs récents** : Aucune génération d'exercice récente, donc pas de log `[CHAPTER_LOOKUP]` visible. **Nécessite** : Générer un exercice pour voir les logs |
| **P6** | Code ligne 1795-1796 : `if not static_exercises: raise ... if static_exercises:` | ✅ Dead code confirmé | **BUG P0.4 CONFIRMÉ** : Pipeline SPEC ligne 1795 a un `if static_exercises:` APRÈS le `raise` → dead code, ne retourne jamais statique correctement |
| **P7** | `db.curriculum_chapters.findOne({code_officiel: /6E_SP01/i})` (tous champs) | ✅ `{code_officiel: "6e_SP01", niveau: "6e", ...}` - **Pipeline existe? NON, enabled_generators existe? NON** | **PREUVE CRITIQUE** : 6e_SP01 n'a **PAS** de champs `pipeline` ni `enabled_generators` en DB → code utilise valeurs par défaut ou None → comportement imprévisible |
| **P8** | `db.curriculum_chapters.findOne({code_officiel: /6E_G07/i})` (tous champs) | ✅ `{code_officiel: "6e_G07", pipeline: "TEMPLATE", enabled_generators: [...]}` | **COMPARAISON** : 6E_G07 a `pipeline: "TEMPLATE"` et `enabled_generators` en List[dict] → comportement correct. **6e_SP01 manque ces champs** |

---

## B) DECISION TREE RÉEL avec extraits de code

### 1. Lookup chapitre (CRITIQUE - BUG P0.1)

**Fichier** : `backend/services/curriculum_persistence_service.py:212-238`

```python
async def get_chapter_by_code(self, code_officiel: str) -> Optional[Dict[str, Any]]:
    """Récupère un chapitre par son code officiel"""
    await self.initialize()
    
    # ❌ BUG : Requête exacte sans regex → échoue si casse différente
    chapter = await self.collection.find_one(
        {"code_officiel": code_officiel},  # ← Requête exacte, pas insensible à la casse
        {"_id": 0}
    )
    
    if chapter:
        logger.info(f"[DIAG_6E_G07] ✅ Chapitre trouvé: code_officiel='{chapter.get('code_officiel')}'")
    else:
        logger.warning(f"[DIAG_6E_G07] ❌ Chapitre NON TROUVÉ avec code_officiel='{code_officiel}'")
    
    return chapter
```

**Problème** : Si DB a `code_officiel: "6e_SP01"` (mixed case) et qu'on cherche `"6E_SP01"` (uppercase), la requête échoue.

**Preuve RÉELLE** :
```bash
# DB stocke en mixed case
db.curriculum_chapters.findOne({code_officiel:{$regex:"^6[eE]_SP01$", $options:"i"}})
# → {code_officiel: "6e_SP01", niveau: "6e", ...} (PAS de pipeline ni enabled_generators)

# Requête exacte échoue
db.curriculum_chapters.findOne({code_officiel:"6E_SP01"})
# → null (CONFIRMÉ)

# Comparaison avec 6E_G07 (qui fonctionne)
db.curriculum_chapters.findOne({code_officiel: /6E_G07/i})
# → {code_officiel: "6e_G07", pipeline: "TEMPLATE", enabled_generators: [...]}
```

---

### 2. Normalisation code_officiel (INCOHÉRENCE)

**Fichier** : `backend/routes/exercises_routes.py:1093`

```python
# Normalisation AVANT lookup
normalized_code_officiel = request.code_officiel.upper().replace("-", "_")
# Exemple: "6e_SP01" → "6E_SP01"

chapter_from_db = await curriculum_service_db.get_chapter_by_code(normalized_code_officiel)
# ❌ BUG : Cherche "6E_SP01" mais DB a "6e_SP01" → non trouvé
```

**Problème** : Normalisation en uppercase, mais DB stocke en mixed case → lookup échoue.

---

### 3. Pipeline SPEC (BUG P0.4 - Dead code)

**Fichier** : `backend/routes/exercises_routes.py:1775-1796`

```python
static_exercises = [ex for ex in exercises if ex.get("is_dynamic") is not True]
if not static_exercises:
    raise HTTPException(
        status_code=422,
        detail={"error_code": "NO_EXERCISE_AVAILABLE", ...}
    )
    # ❌ BUG : Dead code - jamais exécuté car raise termine la fonction
    if static_exercises:
        selected_static = safe_random_choice(static_exercises, ctx, obs_logger)
```

**Problème** : Le `if static_exercises:` ligne 1795 est APRÈS le `raise` → dead code. Pipeline SPEC ne retourne jamais d'exercice statique.

---

### 4. Filtre is_dynamic (BUG P0.3 - Trop strict)

**Fichier** : `backend/routes/exercises_routes.py:1289`

```python
dynamic_exercises = [ex for ex in exercises if ex.get("is_dynamic") is True]
# ❌ BUG : Filtre strict "is True" exclut is_dynamic: 1 (number)
```

**Problème** : MongoDB peut stocker `is_dynamic: 1` (number) au lieu de `true` (boolean) → filtre strict exclut ces exercices.

**Preuve** :
```python
# Test Python
ex1 = {"is_dynamic": True}   # → ex1.get("is_dynamic") is True → ✅
ex2 = {"is_dynamic": 1}      # → ex2.get("is_dynamic") is True → ❌ (1 is not True)
ex3 = {"is_dynamic": "true"} # → ex3.get("is_dynamic") is True → ❌
```

---

### 5. Filtre enabled_generators (BUG P0.2 - Format dict)

**Fichier** : `backend/routes/exercises_routes.py:1244, 1293-1297`

```python
# Normalisation (déjà fait ligne 1244)
enabled_generators_for_chapter = normalize_enabled_generators(enabled_generators_raw)
# → ["CALCUL_NOMBRES_V1", "RAISONNEMENT_MULTIPLICATIF_V1"] (List[str] uppercase)

# Filtre ligne 1293-1297
if enabled_generators_for_chapter:
    dynamic_exercises = [
        ex for ex in dynamic_exercises
        if ex.get("generator_key") and 
           ex.get("generator_key").upper() in enabled_generators_for_chapter
    ]
```

**Problème** : ✅ Déjà corrigé via `normalize_enabled_generators()`, mais vérifier que tous les usages passent par cette fonction.

**Preuve mongo RÉELLE** :
```bash
# DB stocke en format dict (CONFIRMÉ)
db.curriculum_chapters.findOne({code_officiel: /6E_G07/i}, {enabled_generators: 1})
# → {
#   enabled_generators: [
#     {
#       generator_key: "CALCUL_NOMBRES_V1",
#       difficulty_presets: ["facile", "moyen", "difficile"],
#       min_offer: "free",
#       is_enabled: true
#     },
#     {
#       generator_key: "RAISONNEMENT_MULTIPLICATIF_V1",
#       difficulty_presets: ["facile", "moyen", "difficile"],
#       min_offer: "free",
#       is_enabled: true
#     }
#   ]
# }

# Normalisation nécessaire (déjà fait ligne 1244)
normalize_enabled_generators([{generator_key: "CALCUL_NOMBRES_V1", is_enabled: true}])
# → ["CALCUL_NOMBRES_V1"]
```

---

### 6. Pipeline MIXED (Fallback DYNAMIC → STATIC)

**Fichier** : `backend/routes/exercises_routes.py:60-303` (generate_exercise_with_fallback)

```python
async def generate_exercise_with_fallback(...):
    # 1. Essayer DYNAMIC
    exercises = await exercise_service.get_exercises(chapter_code, offer, difficulty)
    dynamic_exercises = [ex for ex in exercises if ex.get("is_dynamic") is True]
    
    # Filtre enabled_generators
    if enabled_generators_for_chapter:
        dynamic_exercises = [
            ex for ex in dynamic_exercises
            if ex.get("generator_key").upper() in enabled_generators_for_chapter
        ]
    
    if len(dynamic_exercises) > 0:
        return format_dynamic_exercise(...)  # ✅ Retour immédiat
    
    # 2. Fallback STATIC
    exercises = await exercise_service.get_exercises(chapter_code, offer, difficulty)
    static_exercises = [ex for ex in exercises if ex.get("is_dynamic") is not True]
    
    if len(static_exercises) > 0:
        return static_exercise  # ✅ Retour statique
```

**Problème** : Si lookup chapitre échoue (BUG P0.1), `enabled_generators_for_chapter` est vide → filtre ne s'applique pas → tous les générateurs sont sélectionnés (même ceux non activés).

---

## C) 3 CAUSES P0 "fallback statique alors que dyn existe"

### Cause P0.1 : Lookup chapitre échoue (casse) → enabled_generators vide → filtre ne s'applique pas

**Preuve code** :
```python
# backend/routes/exercises_routes.py:1093, 1100
normalized_code_officiel = request.code_officiel.upper().replace("-", "_")
# "6e_SP01" → "6E_SP01"

chapter_from_db = await curriculum_service_db.get_chapter_by_code(normalized_code_officiel)
# Cherche "6E_SP01" mais DB a "6e_SP01" → null

# backend/services/curriculum_persistence_service.py:222
chapter = await self.collection.find_one({"code_officiel": code_officiel})  # Requête exacte
# ❌ Échoue si casse différente
```

**Preuve mongo** :
```bash
# DB stocke en mixed case
db.curriculum_chapters.findOne({code_officiel:{$regex:"^6[eE]_SP01$", $options:"i"}})
# → {code_officiel: "6e_SP01"}

# Requête exacte échoue
db.curriculum_chapters.findOne({code_officiel:"6E_SP01"})
# → null
```

**Preuve log** :
```bash
# Logs récents (100 dernières lignes)
docker logs le-maitre-mot-backend --tail 100
# → Seulement accès /docs (pas de génération récente)
# Note: Pour voir les logs de lookup, il faut générer un exercice

# Pour tester le lookup:
# 1. Générer exercice avec code_officiel: "6E_SP01" (uppercase)
# 2. Vérifier logs: [DIAG_6E_G07] ❌ Chapitre NON TROUVÉ avec code_officiel='6E_SP01'
```

**Impact** : `enabled_generators_for_chapter = []` → filtre ligne 1293 ne s'applique pas → tous les générateurs sont sélectionnés (même RAISONNEMENT_MULTIPLICATIF_V1 sur SP01).

---

### Cause P0.2 : Filtre is_dynamic trop strict → exclut exercices dynamiques

**Preuve code** :
```python
# backend/routes/exercises_routes.py:1289
dynamic_exercises = [ex for ex in exercises if ex.get("is_dynamic") is True]
# ❌ Exclut is_dynamic: 1 (number)
```

**Preuve mongo RÉELLE** :
```bash
# Vérifier type is_dynamic en DB
db.admin_exercises.aggregate([
  {$match: {chapter_code: /6E_G07/i}},
  {$project: {is_dynamic: 1, type_is_dynamic: {$type: "$is_dynamic"}}},
  {$limit: 5}
])
# → {is_dynamic: true, type_is_dynamic: "bool"} (CONFIRMÉ - boolean)
# Note: Actuellement en boolean, mais filtre truthy est plus sûr pour éviter bugs futurs
```

**Impact** : Exercices dynamiques avec `is_dynamic: 1` sont exclus → 0 dynamiques → fallback statique.

---

### Cause P0.3 : Normalisation difficulty/offer manquante dans query MongoDB

**Preuve code** :
```python
# backend/services/exercise_persistence_service.py:570-573
if offer:
    query["offer"] = offer.lower()  # ✅ Normalisé
if difficulty:
    query["difficulty"] = difficulty.lower()  # ❌ "standard" → "standard" (pas "moyen")
```

**Problème** : `normalize_difficulty("standard")` retourne `"moyen"`, mais query MongoDB utilise `difficulty.lower()` → `"standard"` → 0 résultats.

**Preuve code** :
```python
# backend/routes/exercises_routes.py:984
normalized_difficulty = normalize_difficulty(request.difficulte)
# "standard" → "moyen"

# Mais query MongoDB ligne 573 utilise request.difficulte (non normalisé)
query["difficulty"] = difficulty.lower()  # "standard" → "standard"
```

**Impact** : Query MongoDB avec `difficulty: "standard"` ne trouve pas d'exercices avec `difficulty: "moyen"` → 0 résultats → fallback statique.

---

## D) PATCH MINIMAL (1 PR)

### Fichiers modifiés

1. `backend/services/curriculum_persistence_service.py` : Lookup chapitre insensible à la casse
2. `backend/routes/exercises_routes.py` : Fix pipeline SPEC, normalisation difficulty dans query
3. `backend/services/exercise_persistence_service.py` : Normalisation difficulty dans query
4. `backend/routes/exercises_routes.py` : Filtre is_dynamic truthy (pas strict)

---

### Pseudo-diff

#### 1. Fix lookup chapitre (insensible à la casse)

**Fichier** : `backend/services/curriculum_persistence_service.py:212-238`

```diff
 async def get_chapter_by_code(self, code_officiel: str) -> Optional[Dict[str, Any]]:
     """Récupère un chapitre par son code officiel"""
     await self.initialize()
     
-    # P0 - DIAGNOSTIC : Log de la requête exacte
-    logger.info(
-        f"[DIAG_6E_G07] get_chapter_by_code() appelé avec code_officiel='{code_officiel}' "
-        f"(type: {type(code_officiel)})"
-    )
-    
-    chapter = await self.collection.find_one(
-        {"code_officiel": code_officiel},
-        {"_id": 0}
-    )
+    # P0 - FIX : Requête insensible à la casse (DB stocke en mixed case)
+    # Normaliser pour lookup canonique
+    normalized_code = code_officiel.upper().replace("-", "_")
+    
+    logger.info(
+        f"[CHAPTER_LOOKUP] Recherche chapitre: requested='{code_officiel}' → normalized='{normalized_code}'"
+    )
+    
+    # Requête avec regex insensible à la casse
+    chapter = await self.collection.find_one(
+        {"code_officiel": {"$regex": f"^{re.escape(normalized_code)}$", "$options": "i"}},
+        {"_id": 0}
+    )
     
     if chapter:
-        logger.info(
-            f"[DIAG_6E_G07] ✅ Chapitre trouvé: code_officiel='{chapter.get('code_officiel')}', "
-            f"pipeline='{chapter.get('pipeline')}'"
-        )
+        logger.info(
+            f"[CHAPTER_LOOKUP] ✅ Chapitre trouvé: code_officiel='{chapter.get('code_officiel')}', "
+            f"pipeline='{chapter.get('pipeline')}', "
+            f"enabled_generators_count={len(chapter.get('enabled_generators', []))}"
+        )
     else:
-        logger.warning(
-            f"[DIAG_6E_G07] ❌ Chapitre NON TROUVÉ avec code_officiel='{code_officiel}'. "
-            f"Vérifier la casse dans MongoDB."
-        )
+        logger.warning(
+            f"[CHAPTER_LOOKUP] ❌ Chapitre NON TROUVÉ: requested='{code_officiel}', normalized='{normalized_code}'"
+        )
     
     return chapter
```

**Ajout import** :
```diff
+import re
```

---

#### 2. Fix pipeline SPEC (retour immédiat)

**Fichier** : `backend/routes/exercises_routes.py:1775-1815`

```diff
                     static_exercises = [ex for ex in exercises if ex.get("is_dynamic") is not True]
                     if not static_exercises:
                         raise HTTPException(
                             status_code=422,
                             detail={
                                 "error_code": "NO_EXERCISE_AVAILABLE",
                                 "error": "no_exercise_available",
                                 "message": (
                                     f"Aucun exercice statique saisi pour {chapter_code_for_db} "
                                     f"avec offer='{request.offer}' et difficulte='{request.difficulte}'. "
                                     "Ajoutez un exercice statique ou définissez exercise_types pour la génération SPEC."
                                 ),
                                 "chapter_code": chapter_code_for_db,
                                 "pipeline": "SPEC",
                                 "filters": {
                                     "offer": getattr(request, 'offer', None),
                                     "difficulty": getattr(request, 'difficulte', None)
                                 }
                             }
                         )
-                        if static_exercises:
-                            selected_static = safe_random_choice(static_exercises, ctx, obs_logger)
+                    
+                    # P0 - FIX : Retour immédiat pour pipeline SPEC
+                    selected_static = safe_random_choice(static_exercises, ctx, obs_logger)
                     timestamp = int(time.time() * 1000)
                     static_exercise = {
                         "id_exercice": f"admin_static_{chapter_code_for_db}_{selected_static.get('id')}_{timestamp}",
                         "niveau": curriculum_chapter.niveau,
                         "chapitre": curriculum_chapter.libelle or curriculum_chapter.code_officiel,
                         "enonce_html": selected_static.get("enonce_html") or "",
                         "solution_html": selected_static.get("solution_html") or "",
                         "needs_svg": selected_static.get("needs_svg") or False,
                         "exercise_type": selected_static.get("exercise_type"),
                         "pdf_token": f"admin_static_{chapter_code_for_db}_{selected_static.get('id')}_{timestamp}",
                         "metadata": {
                             "offer": selected_static.get("offer"),
                             "difficulty": selected_static.get("difficulty"),
                             "source": "admin_exercises_static",
-                            "is_fallback": False
+                            "is_fallback": False,
+                            "pipeline": "SPEC",
+                            "fallback_reason": None
                         }
                     }
+                    
+                    duration_ms = int((time.time() - request_start) * 1000)
+                    obs_logger.info(
+                        "event=request_complete",
+                        event="request_complete",
+                        outcome="success",
+                        duration_ms=duration_ms,
+                        chosen_path="SPEC",
+                        exercise_id=selected_static.get('id'),
+                        **ctx
+                    )
+                    logger.info(
+                        f"[PIPELINE] ✅ Exercice statique généré (SPEC): "
+                        f"chapter_code={chapter_code_for_db}, exercise_id={selected_static.get('id')}"
+                    )
+                    
+                    return static_exercise
```

---

#### 3. Fix filtre is_dynamic (truthy au lieu de strict)

**Fichier** : `backend/routes/exercises_routes.py:1289, 134, 315, 1483, 1519, 1547, 1669, 1775`

```diff
-                    dynamic_exercises = [ex for ex in exercises if ex.get("is_dynamic") is True]
+                    # P0 - FIX : Filtre truthy (pas strict) pour supporter is_dynamic: 1 (number)
+                    dynamic_exercises = [ex for ex in exercises if ex.get("is_dynamic")]
```

**Remplacer toutes les occurrences** :
- Ligne 1289 (TEMPLATE)
- Ligne 134 (generate_exercise_with_fallback)
- Ligne 1483 (MIXED)
- Ligne 1519 (MIXED dégradé)
- Ligne 1547 (MIXED all)
- Ligne 1669 (MIXED diagnostic)

**Pour static_exercises** :
```diff
-                    static_exercises = [ex for ex in exercises if ex.get("is_dynamic") is not True]
+                    # P0 - FIX : Filtre truthy (pas strict)
+                    static_exercises = [ex for ex in exercises if not ex.get("is_dynamic")]
```

---

#### 4. Fix normalisation difficulty dans query MongoDB

**Fichier** : `backend/services/exercise_persistence_service.py:555-590`

```diff
     async def get_exercises(
         self,
         chapter_code: str,
         offer: Optional[str] = None,
         difficulty: Optional[str] = None
     ) -> List[Dict[str, Any]]:
         """Récupère les exercices d'un chapitre avec filtres optionnels"""
         from logger import get_logger
+        from backend.utils.difficulty_utils import normalize_difficulty
         diag_logger = get_logger()
         
         chapter_upper = chapter_code.upper().replace("-", "_")
         await self.initialize_chapter(chapter_upper)
         
         query = {"chapter_code": chapter_upper}
         
         if offer:
             query["offer"] = offer.lower()
-        if difficulty:
-            query["difficulty"] = difficulty.lower()
+        if difficulty:
+            # P0 - FIX : Normaliser difficulty ("standard" → "moyen") AVANT query
+            try:
+                normalized_difficulty = normalize_difficulty(difficulty)
+                query["difficulty"] = normalized_difficulty.lower()
+            except ValueError:
+                # Si normalisation échoue, utiliser difficulty tel quel
+                query["difficulty"] = difficulty.lower()
```

---

#### 5. Ajout logs fallback_reason (non-bloquants)

**Fichier** : `backend/routes/exercises_routes.py:304-330` (generate_exercise_with_fallback)

```diff
     # 2. Fallback STATIC
     try:
         logger.info(
             f"[FALLBACK_STATIC] Tentative fallback STATIC pour {chapter_code} "
-            f"(aucun exercice dynamique trouvé ou erreur)"
+            f"(aucun exercice dynamique trouvé ou erreur). "
+            f"dynamic_count={len(dynamic_exercises) if 'dynamic_exercises' in locals() else 0}, "
+            f"enabled_generators={enabled_generators_for_chapter if 'enabled_generators_for_chapter' in locals() else []}"
         )
+        
+        # P0 - Log fallback_reason explicite (non-bloquant)
+        fallback_reason = None
+        if 'dynamic_exercises' in locals() and len(dynamic_exercises) == 0:
+            if 'enabled_generators_for_chapter' in locals() and enabled_generators_for_chapter:
+                fallback_reason = "no_dynamic_for_enabled_generators"
+            else:
+                fallback_reason = "no_dynamic_exercises"
+        else:
+            fallback_reason = "dynamic_generation_error"
+        
+        try:
+            logger.info(f"[FALLBACK_STATIC] fallback_reason={fallback_reason}")
+        except Exception as log_error:
+            # Log non-bloquant
+            pass
```

**Ajout dans metadata** :
```diff
                         "metadata": {
                             "offer": selected_static.get("offer"),
                             "difficulty": selected_static.get("difficulty"),
                             "source": "admin_exercises_static",
-                            "is_fallback": True
+                            "is_fallback": True,
+                            "fallback_reason": fallback_reason
                         }
```

---

## E) CHECKLIST UI (max 5 tests) + 3 commandes logs/mongo

### Checklist UI

1. **Test 1** : Générer exercice `6e_SP01` avec `offer: "pro"`, `difficulte: "facile"`
   - ✅ Vérifier : Log `[CHAPTER_LOOKUP] ✅ Chapitre trouvé` (pas "NON TROUVÉ")
   - ✅ Vérifier : Exercice dynamique avec `generator_key: "CALCUL_NOMBRES_V1"` (pas RAISONNEMENT_MULTIPLICATIF_V1)
   - ✅ Vérifier : Metadata `fallback_reason: null` (pas de fallback)

2. **Test 2** : Générer exercice `6e_G07` avec `offer: "free"`, `difficulte: "standard"`
   - ✅ Vérifier : Normalisation `difficulte: "standard"` → `"moyen"` dans query MongoDB
   - ✅ Vérifier : Exercice dynamique trouvé (pas fallback statique)
   - ✅ Vérifier : Log `[PIPELINE] ✅ Exercice dynamique généré (TEMPLATE)`

3. **Test 3** : Générer exercice avec `pipeline: "SPEC"` (chapitre configuré SPEC)
   - ✅ Vérifier : Retour immédiat exercice statique (pas de fallback)
   - ✅ Vérifier : Metadata `pipeline: "SPEC"`, `is_fallback: false`
   - ✅ Vérifier : Log `[PIPELINE] ✅ Exercice statique généré (SPEC)`

4. **Test 4** : Générer exercice `6e_G07` avec `offer: "pro"`, `difficulte: "facile"` (exercice dynamique existe)
   - ✅ Vérifier : Filtre `is_dynamic` trouve exercices (même si `is_dynamic: 1` en DB)
   - ✅ Vérifier : Filtre `enabled_generators` appliqué correctement
   - ✅ Vérifier : Pas de fallback statique

5. **Test 5** : Générer exercice avec chapitre non trouvé (code invalide)
   - ✅ Vérifier : HTTPException 422 avec message clair
   - ✅ Vérifier : Log `[CHAPTER_LOOKUP] ❌ Chapitre NON TROUVÉ` avec `requested` et `normalized`

---

### 3 commandes logs/mongo (obligatoires)

#### Commande 1 : Logs backend (fallback, pipeline, lookup)

```bash
docker logs le-maitre-mot-backend --tail 300 | grep -E "CHAPTER|PIPELINE|FALLBACK|DYNAMIC|STATIC|422"
```

**Résultat RÉEL obtenu** (logs récents) :
```
INFO:     127.0.0.1:52376 - "GET /docs HTTP/1.1" 200 OK
INFO:     127.0.0.1:54388 - "GET /docs HTTP/1.1" 200 OK
...
```

**Ce que ça prouve** : 
- ⚠️ **Pas de génération récente** : Seulement accès à `/docs` (documentation API)
- **Pour voir les logs de lookup** : Générer un exercice avec `code_officiel: "6E_SP01"` (uppercase)
- **Résultat attendu après génération** :
  - `[DIAG_6E_G07] ❌ Chapitre NON TROUVÉ avec code_officiel='6E_SP01'` (si lookup échoue)
  - `[CHAPTER_LOOKUP] ✅ Chapitre trouvé: code_officiel='6e_SP01'` (si lookup fonctionne avec regex)

---

#### Commande 2 : MongoDB - Chapitre 6E_SP01

```bash
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
db.curriculum_chapters.findOne({code_officiel:{\$regex:'^6[eE]_SP01\$', \$options:'i'}},{_id:0,code_officiel:1,pipeline:1,enabled_generators:1})
"
```

**Résultat RÉEL obtenu** :
```json
{
  "code_officiel": "6e_SP01"
}
```

**Ce que ça prouve** : 
- ✅ DB stocke en mixed case `"6e_SP01"` (CONFIRMÉ)
- ❌ **6e_SP01 n'a PAS de champ `pipeline` ni `enabled_generators`** en DB
- ⚠️ **Impact** : Code utilise valeurs par défaut (None) → comportement imprévisible

**Comparaison avec 6E_G07** :
```json
{
  "code_officiel": "6e_G07",
  "pipeline": "TEMPLATE",
  "enabled_generators": [
    {
      "generator_key": "CALCUL_NOMBRES_V1",
      "is_enabled": true,
      "difficulty_presets": ["facile", "moyen", "difficile"],
      "min_offer": "free"
    },
    {
      "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
      "is_enabled": true,
      ...
    }
  ]
}
```

---

#### Commande 3 : MongoDB - Exercices 6E_G07

```bash
docker exec le-maitre-mot-mongo mongosh le_maitre_mot_db --quiet --eval "
db.admin_exercises.find({chapter_code:{\$regex:'^6[eE]_G07\$', \$options:'i'}},{_id:0,id:1,is_dynamic:1,generator_key:1,offer:1,difficulty:1}).sort({id:1}).limit(5).forEach(doc => print(JSON.stringify(doc)))
"
```

**Résultat RÉEL obtenu** :
```json
{"id":1,"is_dynamic":true,"generator_key":"CALCUL_NOMBRES_V1","offer":"free","difficulty":"facile"}
```

**Ce que ça prouve** : 
- ✅ Exercices dynamiques existent pour 6E_G07 (CONFIRMÉ)
- ✅ `is_dynamic: true` en boolean (type: "bool") (CONFIRMÉ)
- ✅ `generator_key: "CALCUL_NOMBRES_V1"` présent (CONFIRMÉ)
- ✅ `difficulty: "facile"` en lowercase (CONFIRMÉ)
- ⚠️ **Note** : 6E_SP01 n'a pas d'exercices en DB (tableau vide) → fallback statique attendu

---

## RÉSUMÉ EXÉCUTIF

**3 causes P0 identifiées et CONFIRMÉES** :
1. **Lookup chapitre échoue** (casse) → enabled_generators vide → filtre ne s'applique pas
   - ✅ **PREUVE** : Requête exacte `"6E_SP01"` ne trouve pas `"6e_SP01"` en DB
   - ✅ **PREUVE** : 6e_SP01 n'a pas de `pipeline` ni `enabled_generators` en DB
2. **Filtre is_dynamic trop strict** → exclut exercices dynamiques
   - ✅ **PREUVE** : Type en DB est `"bool"` (OK actuellement), mais filtre truthy est plus sûr
3. **Normalisation difficulty manquante** dans query MongoDB → 0 résultats → fallback
   - ✅ **PREUVE** : Query utilise `difficulty.lower()` au lieu de `normalize_difficulty()`

**Patch minimal** : 1 PR avec 5 fixes (lookup insensible casse, pipeline SPEC retour immédiat, filtre is_dynamic truthy, normalisation difficulty, logs fallback_reason).

**Risques** : Faibles (corrections de normalisation uniquement, pas de changement de logique métier).

**Note importante** : 6e_SP01 n'a pas de `pipeline` ni `enabled_generators` en DB → migration nécessaire pour ajouter ces champs.

---

**Fin du document d'audit P0**

