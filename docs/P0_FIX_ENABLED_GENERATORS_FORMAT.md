# P0 - Fix : enabled_generators format (List[dict] vs List[str])

## Cause exacte

**Bug** : Le code traite `enabled_generators` comme `List[str]` mais en DB c'est `List[dict]`

### Preuve DB

```javascript
// Dans MongoDB
db.curriculum_chapters.findOne({code_officiel: "6e_G07"}, {enabled_generators: 1})

// Résultat:
{
  code_officiel: "6e_G07",
  pipeline: "MIXED",
  enabled_generators: [
    {
      generator_key: "CALCUL_NOMBRES_V1",
      is_enabled: true,
      min_offer: "free",
      difficulty_presets: ["facile", "moyen", "difficile"]
    },
    {
      generator_key: "SYMETRIE_AXIALE_V2",
      is_enabled: true,
      min_offer: "free",
      difficulty_presets: ["facile", "moyen"]
    }
  ]
}
```

### Preuve code (avant fix)

**Fichier** : `backend/routes/exercises_routes.py` (ligne ~147)

```python
enabled_generators_for_chapter = ctx.get("enabled_generators", [])

# ⚠️ BUG : Traite comme List[str]
if enabled_generators_for_chapter:
    dynamic_exercises = [
        ex for ex in dynamic_exercises
        if ex.get("generator_key") and ex.get("generator_key").upper() in [eg.upper() for eg in enabled_generators_for_chapter]
        #                                                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        #                                                                  Erreur : eg est un dict, pas un str
    ]
```

**Résultat** :
- `enabled_generators_for_chapter` = `[{"generator_key": "CALCUL_NOMBRES_V1", ...}, ...]`
- `[eg.upper() for eg in enabled_generators_for_chapter]` → `AttributeError: 'dict' object has no attribute 'upper'`
- OU si géré silencieusement : le filtre élimine tout → `dynamic_exercises` vide → fallback statique

### Preuve exercice dynamique existe

```javascript
// Dans MongoDB
db.admin_exercises.find({chapter_code: "6E_G07", is_dynamic: true})

// Résultat:
{
  id: 2,
  chapter_code: "6E_G07",
  is_dynamic: true,
  generator_key: "CALCUL_NOMBRES_V1",
  offer: "free",
  difficulty: "facile"
}
```

## Fix minimal

### Fonction de normalisation

**Fichier** : `backend/routes/exercises_routes.py` (ligne ~536)

```python
def normalize_enabled_generators(raw: Any) -> List[str]:
    """
    Normalise enabled_generators depuis différents formats possibles.
    
    Formats supportés:
    - List[str]: ["CALCUL_NOMBRES_V1", "SYMETRIE_AXIALE_V2"]
    - List[dict]: [{"generator_key": "CALCUL_NOMBRES_V1", "is_enabled": True, ...}, ...]
    - None ou autre: []
    
    Returns:
        Liste de generator_key (strings) normalisés
    """
    if not raw:
        return []
    
    if isinstance(raw, list):
        if len(raw) == 0:
            return []
        
        # Cas 1: List[str]
        if isinstance(raw[0], str):
            return [g.upper() for g in raw if g]
        
        # Cas 2: List[dict]
        if isinstance(raw[0], dict):
            return [
                d["generator_key"].upper()
                for d in raw
                if isinstance(d, dict) and d.get("is_enabled") and d.get("generator_key")
            ]
    
    return []
```

### Utilisation dans generate_exercise_with_fallback

**Fichier** : `backend/routes/exercises_routes.py` (ligne ~146)

```python
# AVANT
enabled_generators_for_chapter = ctx.get("enabled_generators", [])

# APRÈS
enabled_generators_raw = ctx.get("enabled_generators", [])
enabled_generators_for_chapter = normalize_enabled_generators(enabled_generators_raw)

logger.info(
    f"[PIPELINE_DEBUG]   enabled_generators_raw_type={type(enabled_generators_raw).__name__}"
)
logger.info(
    f"[PIPELINE_DEBUG]   enabled_generators_raw={enabled_generators_raw}"
)
logger.info(
    f"[PIPELINE_DEBUG]   enabled_generator_keys (normalisés)={enabled_generators_for_chapter}"
)
```

### Filtre corrigé

```python
if enabled_generators_for_chapter:
    dynamic_exercises = [
        ex for ex in dynamic_exercises
        if ex.get("generator_key") and ex.get("generator_key").upper() in enabled_generators_for_chapter
        #                                                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        #                                                                  Maintenant c'est List[str] normalisé
    ]
```

## Test manuel (3 étapes)

### a) Générer 6e_G07 facile free

1. Ouvrir `/generer`
2. Sélectionner chapitre **6e_G07** (Symétrie axiale)
3. Difficulté : **facile**
4. Offre : **free** (ou laisser par défaut)
5. Générer un exercice

### b) Logs montrent dynamic_after_enabled_generators > 0

```bash
docker logs le-maitre-mot-backend --tail 100 | grep -E "PIPELINE_DEBUG|enabled_generators"
```

**Résultat attendu** :
```
[PIPELINE_DEBUG] enabled_generators_raw_type=list
[PIPELINE_DEBUG] enabled_generators_raw=[{'generator_key': 'CALCUL_NOMBRES_V1', 'is_enabled': True, ...}, ...]
[PIPELINE_DEBUG] enabled_generator_keys (normalisés)=['CALCUL_NOMBRES_V1', 'SYMETRIE_AXIALE_V2']
[PIPELINE_DEBUG]   dynamic_count=3
[PIPELINE_DEBUG]   Filtrant selon enabled_generators=['CALCUL_NOMBRES_V1', 'SYMETRIE_AXIALE_V2'] (avant filtre: 3 exercices dynamiques)
[PIPELINE_DEBUG]   dynamic_after_enabled_generators=3
```

### c) Exercice choisi is_dynamic=true (id=2 / generator_key=CALCUL_NOMBRES_V1)

**Vérifier dans les logs** :
```bash
docker logs le-maitre-mot-backend --tail 100 | grep -E "GENERATOR_OK|dynamic_generated|exercise_id"
```

**Résultat attendu** :
```
[GENERATOR_OK] ✅ Exercice DYNAMIQUE généré: chapter=6E_G07, id=2, generator=CALCUL_NOMBRES_V1
```

**OU vérifier dans la réponse JSON** :
- L'exercice généré doit avoir `metadata.generator_key = "CALCUL_NOMBRES_V1"`
- L'exercice généré doit avoir `metadata.is_dynamic = true` (ou équivalent)

## Diff complet

```diff
--- a/backend/routes/exercises_routes.py
+++ b/backend/routes/exercises_routes.py
@@ -536,6 +536,35 @@ def build_solution_html(etapes: list, resultat_final: str, svg_correction: Opti
     return html
 
 
+def normalize_enabled_generators(raw: Any) -> List[str]:
+    """
+    Normalise enabled_generators depuis différents formats possibles.
+    
+    Formats supportés:
+    - List[str]: ["CALCUL_NOMBRES_V1", "SYMETRIE_AXIALE_V2"]
+    - List[dict]: [{"generator_key": "CALCUL_NOMBRES_V1", "is_enabled": True, ...}, ...]
+    - None ou autre: []
+    
+    Returns:
+        Liste de generator_key (strings) normalisés
+    """
+    if not raw:
+        return []
+    
+    if isinstance(raw, list):
+        if len(raw) == 0:
+            return []
+        
+        # Cas 1: List[str]
+        if isinstance(raw[0], str):
+            return [g.upper() for g in raw if g]
+        
+        # Cas 2: List[dict]
+        if isinstance(raw[0], dict):
+            return [
+                d["generator_key"].upper()
+                for d in raw
+                if isinstance(d, dict) and d.get("is_enabled") and d.get("generator_key")
+            ]
+    
+    return []
+
+
 def generate_exercise_id(niveau: str, chapitre: str) -> str:
@@ -146,7 +175,13 @@ async def generate_exercise_with_fallback(
         # P4.D - Filtrer selon enabled_generators si disponible (passé via ctx)
-        enabled_generators_for_chapter = ctx.get("enabled_generators", [])
+        enabled_generators_raw = ctx.get("enabled_generators", [])
         dynamic_count_before_filter = len(dynamic_exercises)
         
+        # P0 - FIX : Normaliser enabled_generators (peut être List[str] ou List[dict])
+        enabled_generators_for_chapter = normalize_enabled_generators(enabled_generators_raw)
+        
+        logger.info(
+            f"[PIPELINE_DEBUG]   enabled_generators_raw_type={type(enabled_generators_raw).__name__}"
+        )
+        logger.info(
+            f"[PIPELINE_DEBUG]   enabled_generators_raw={enabled_generators_raw}"
+        )
+        logger.info(
+            f"[PIPELINE_DEBUG]   enabled_generator_keys (normalisés)={enabled_generators_for_chapter}"
+        )
+        
         if enabled_generators_for_chapter:
             logger.info(
                 f"[PIPELINE_DEBUG]   Filtrant selon enabled_generators={enabled_generators_for_chapter} "
                 f"(avant filtre: {dynamic_count_before_filter} exercices dynamiques)"
             )
             dynamic_exercises = [
                 ex for ex in dynamic_exercises
-                if ex.get("generator_key") and ex.get("generator_key").upper() in [eg.upper() for eg in enabled_generators_for_chapter]
+                if ex.get("generator_key") and ex.get("generator_key").upper() in enabled_generators_for_chapter
             ]
```

## Résumé

**Cause** : `enabled_generators` est `List[dict]` en DB mais le code le traite comme `List[str]`

**Fix** : Fonction `normalize_enabled_generators()` qui gère les deux formats

**Impact** : Les exercices dynamiques sont correctement filtrés selon `enabled_generators` → plus de fallback statique intempestif



