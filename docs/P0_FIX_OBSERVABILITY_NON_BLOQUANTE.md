# P0 - Fix : Observabilité non-bloquante + correction double generator_key

## Cause exacte

**Erreur** : `ObservabilityLogger.info() got multiple values for keyword argument 'generator_key'`

### Preuve dans le code

**Fichier** : `backend/routes/exercises_routes.py`

1. **Ligne 206** : `generator_key` est ajouté dans `ctx`
```python
ctx['generator_key'] = generator_key
```

2. **Ligne 262** : `generator_key` est passé explicitement ET via `**ctx`
```python
obs_logger.info(
    "event=dynamic_generated",
    event="dynamic_generated",
    outcome="success",
    duration_ms=duration_ms,
    exercise_id=selected_exercise.get('id'),
    generator_key=selected_exercise.get('generator_key'),  # ⚠️ Argument explicite
    **ctx  # ⚠️ Contient aussi generator_key → CONFLIT
)
```

**Fichier** : `backend/observability/logger.py` (ligne 199)

```python
def info(self, message: str, **kwargs):
    """INFO: flux normal, décisions clés, variant"""
    self._create_record('INFO', message, **kwargs)
```

**Problème** :
- La signature accepte `**kwargs` (pas de paramètre nommé `generator_key`)
- Mais Python détecte quand même le conflit si `generator_key` est passé deux fois
- L'erreur fait échouer la génération → fallback vers STATIC

## Fix appliqué

### 1. Correction du double passage de generator_key

**Fichier** : `backend/routes/exercises_routes.py` (ligne ~256)

```python
# AVANT
obs_logger.info(
    "event=dynamic_generated",
    event="dynamic_generated",
    outcome="success",
    duration_ms=duration_ms,
    exercise_id=selected_exercise.get('id'),
    generator_key=selected_exercise.get('generator_key'),
    **ctx  # ⚠️ Contient generator_key → CONFLIT
)

# APRÈS
# P0 - FIX : Retirer generator_key de ctx avant de le passer explicitement
ctx_for_log = {k: v for k, v in ctx.items() if k != 'generator_key'}

# P0 - SÉCURITÉ : Rendre l'observabilité non-bloquante
try:
    obs_logger.info(
        "event=dynamic_generated",
        event="dynamic_generated",
        outcome="success",
        duration_ms=duration_ms,
        exercise_id=selected_exercise.get('id'),
        generator_key=selected_exercise.get('generator_key'),
        **ctx_for_log  # ✅ Plus de conflit
    )
except Exception as log_error:
    logger.exception(
        f"[OBSERVABILITY_FAIL] Erreur lors du log observability pour exercice dynamique: {log_error}"
    )
    # Continuer la génération même si le log échoue
```

### 2. Protection de tous les appels obs_logger dans generate_exercise_with_fallback

**Fichier** : `backend/routes/exercises_routes.py` (ligne ~277)

```python
# Protection du log dynamic_failed
try:
    obs_logger.warning(
        "event=dynamic_failed",
        event="dynamic_failed",
        outcome="fallback",
        reason="exception",
        exception_type=type(e).__name__,
        **ctx
    )
except Exception as log_error:
    logger.exception(
        f"[OBSERVABILITY_FAIL] Erreur lors du log observability pour dynamic_failed: {log_error}"
    )
    # Continuer même si le log échoue
```

### 3. Protection de safe_random_choice

**Fichier** : `backend/routes/exercises_routes.py` (ligne ~190)

L'appel à `safe_random_choice(dynamic_exercises, ctx, obs_logger)` est déjà protégé car `safe_random_choice` gère les erreurs en interne.

## Test manuel (3 étapes)

### a) Générer chapitre 6e_G07 en facile

1. Ouvrir `/generer`
2. Sélectionner chapitre **6e_G07** (Symétrie axiale)
3. Difficulté : **facile**
4. Générer un exercice

### b) Vérifier qu'aucun "multiple values for generator_key" n'apparaît

```bash
docker logs le-maitre-mot-backend --tail 100 | grep -E "multiple values|GENERATOR_FAIL|GENERATOR_OK"
```

**Résultat attendu** :
- ❌ Plus d'erreur `got multiple values for keyword argument 'generator_key'`
- ✅ Log `[GENERATOR_OK] ✅ Exercice DYNAMIQUE généré` au lieu de `[GENERATOR_OK] ✅ Exercice STATIQUE (fallback)`

### c) Vérifier que même si ObservabilityLogger plante, la génération continue

**Test manuel** : Simuler une erreur dans `ObservabilityLogger.info()` (optionnel, pour tester la robustesse)

**Résultat attendu** :
- Si une erreur survient dans `obs_logger.info()`, on voit `[OBSERVABILITY_FAIL]` dans les logs
- Mais la génération continue et retourne l'exercice dynamique (pas de fallback statique)

## Résumé

**Cause** : `generator_key` est passé deux fois à `obs_logger.info()` (explicite + via `**ctx`)

**Fix 1** : Retirer `generator_key` de `ctx` avant de le passer avec `**ctx_for_log`

**Fix 2** : Wrapper tous les appels à `obs_logger` dans `generate_exercise_with_fallback` avec `try/except` pour rendre l'observabilité non-bloquante

**Impact** :
- Plus d'erreur lors de la génération dynamique
- Les exercices dynamiques sont correctement générés
- Même si l'observabilité plante, la génération continue (robustesse)



