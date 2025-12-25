# P0 - Fix : Erreur "got multiple values for keyword argument 'generator_key'"

## Cause exacte

**Erreur** : `backend.observability.logger.ObservabilityLogger.info() got multiple values for keyword argument 'generator_key'`

### Preuve dans les logs

```
[WARNING][lemaitremot][] [GENERATOR_FAIL] ❌ Erreur génération DYNAMIC pour 6E_G07: backend.observability.logger.ObservabilityLogger.info() got multiple values for keyword argument 'generator_key'. Fallback STATIC activé.
```

### Analyse du code

**Fichier** : `backend/routes/exercises_routes.py` (ligne ~257)

```python
# Ligne 206 : generator_key est ajouté dans ctx
ctx['generator_key'] = generator_key

# Ligne 257 : generator_key est passé explicitement ET via **ctx
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

**Problème** :
- `ctx['generator_key'] = generator_key` (ligne 206)
- `obs_logger.info(..., generator_key=..., **ctx)` (ligne 257)
- Python reçoit `generator_key` deux fois → erreur

## Fix minimal

**Fichier** : `backend/routes/exercises_routes.py` (ligne ~257)

```python
# AVANT
obs_logger.info(
    "event=dynamic_generated",
    event="dynamic_generated",
    outcome="success",
    duration_ms=duration_ms,
    exercise_id=selected_exercise.get('id'),
    generator_key=selected_exercise.get('generator_key'),
    **ctx
)

# APRÈS
# P0 - FIX : Retirer generator_key de ctx avant de le passer explicitement
ctx_for_log = {k: v for k, v in ctx.items() if k != 'generator_key'}
obs_logger.info(
    "event=dynamic_generated",
    event="dynamic_generated",
    outcome="success",
    duration_ms=duration_ms,
    exercise_id=selected_exercise.get('id'),
    generator_key=selected_exercise.get('generator_key'),
    **ctx_for_log
)
```

## Test manuel

1. Générer un exercice pour **6e_G07**
2. Vérifier les logs :
```bash
docker logs le-maitre-mot-backend --tail 50 | grep -E "GENERATOR_FAIL|GENERATOR_OK|dynamic_generated"
```

**Résultat attendu** :
- ❌ Plus d'erreur `got multiple values for keyword argument 'generator_key'`
- ✅ Log `[GENERATOR_OK] ✅ Exercice DYNAMIQUE généré` au lieu de `[GENERATOR_OK] ✅ Exercice STATIQUE (fallback)`

## Résumé

**Cause** : `generator_key` est passé deux fois à `obs_logger.info()` (explicite + via `**ctx`)

**Fix** : Retirer `generator_key` de `ctx` avant de le passer avec `**ctx_for_log`

**Impact** : Plus d'erreur lors de la génération dynamique → les exercices dynamiques sont correctement générés



