# Système de Logging Professionnel — Le Maître Mot

## Vue d'ensemble

Système de logging structuré, déterministe et peu coûteux pour diagnostiquer rapidement les problèmes, tracer les décisions et détecter les anomalies.

## Configuration ENV

### Variables d'environnement

| Variable | Valeur par défaut | Description |
|----------|-------------------|-------------|
| `LOG_LEVEL` | `INFO` | Niveau de log: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_VERBOSE` | `0` | Active les logs DEBUG ciblés (pipeline/tests_dyn/generators) si `1` |
| `LOG_MODULES` | (vide) | Liste de modules à logger (ex: `PIPELINE,TESTS_DYN,GENERATOR`) |
| `LOG_AUDIT` | `0` | Active uniquement les logs "diagnostic prod" (sans DEBUG) si `1` |

### Comportement par défaut

- **Logs désactivés par défaut** : `LOG_LEVEL=INFO`, `LOG_VERBOSE=0`
- **Format** : 1 ligne, key=value, pas de PII, pas de dumps énormes (truncate listes >20)
- **Pas de double logs** : propagation root désactivée

## Architecture

### 1. Contexte partagé

Le contexte est partagé automatiquement via `contextvars` (thread-safe pour async) :

```python
from backend.observability import set_request_context, get_request_context

# Définir le contexte
set_request_context(
    request_id="abc123",
    chapter_code="6E_AA_TEST",
    pipeline="MIXED",
    difficulty="moyen",
    offer="free",
    seed=42,
    generator_key="SIMPLIFICATION_FRACTIONS_V2"
)
```

**Champs de contexte automatiques** :
- `request_id` / `correlation_id` (uuid si absent)
- `chapter_code` / `code_officiel`
- `pipeline` (SPEC/TEMPLATE/MIXED)
- `difficulty` / `offer` / `seed`
- `generator_key` / `template_id` / `variant_id`
- `exercise_type` / `exercise_id` / `admin_exercise_id`
- `chapter_backend`

### 2. Tags/prefixes par module

| Module | Tag | Usage |
|--------|-----|-------|
| Pipeline | `[PIPELINE]` | Routage, décisions pipeline, fallbacks |
| Tests Dyn | `[TESTS_DYN]` | Handler exercices dynamiques, placeholders |
| Generator | `[GENERATOR]` | Génération variables, SVG, pools |
| Cache | `[CACHE]` | Hits/misses, invalidation |
| Persist | `[PERSIST]` | DB operations, counts |
| HTTP | `[HTTP]` | Requêtes HTTP entrantes |

### 3. Niveaux de log

- **INFO** : flux normal, décisions clés, variant
- **DEBUG** : détails (pools, listes, keys manquantes) uniquement si `LOG_VERBOSE=1`
- **WARNING** : fallback, incohérence, pool vide évité
- **ERROR** : exceptions/422 avec contexte complet

## Utilisation

### Logger de base

```python
from backend.observability import get_logger

logger = get_logger('PIPELINE')

# INFO (toujours visible)
logger.info(
    "event=mixed_decision",
    event="mixed_decision",
    outcome="success",
    duration_ms=150,
    pipeline="MIXED",
    chapter_code="6E_AA_TEST"
)

# DEBUG (uniquement si LOG_VERBOSE=1)
logger.debug(
    "pool_details",
    event="pool_analysis",
    pool_size=18,
    pool_type="dynamic_exercises"
)

# WARNING (fallback, incohérence)
logger.warning(
    "event=fallback",
    event="fallback",
    outcome="fallback",
    reason="list_empty",
    pool_size=0
)

# ERROR (exception)
logger.error(
    "event=exception",
    event="generation_failed",
    outcome="error",
    reason="unresolved_placeholders",
    exception_type="ValueError",
    exc_info=True
)
```

### Prévention pool vide

```python
from backend.observability import safe_random_choice, safe_randrange

# Au lieu de random.choice()
items = [1, 2, 3]
context = {'chapter_code': '6E_AA_TEST', 'pipeline': 'MIXED'}
selected = safe_random_choice(items, context, logger)
# → WARNING si liste vide, DEBUG si LOG_VERBOSE=1

# Au lieu de random.randrange()
value = safe_randrange(0, 10, context=context, logger=logger)
# → WARNING si range vide, DEBUG si LOG_VERBOSE=1
```

## Format des logs

### Format standard

```
[LEVEL][TAG] key=value key=value ... message
```

### Exemples

#### 1. Requête normale (INFO)

```
[INFO][PIPELINE] request_id=abc123 chapter_code=6E_AA_TEST pipeline=MIXED difficulty=moyen offer=free seed=42 event=request_in outcome=in_progress
[INFO][PIPELINE] request_id=abc123 chapter_code=6E_AA_TEST pipeline=MIXED event=mixed_decision outcome=success duration_ms=150
[INFO][PIPELINE] request_id=abc123 chapter_code=6E_AA_TEST event=request_complete outcome=success duration_ms=250 exercise_id=ex_6e_aa_test_123
```

#### 2. Fallback (WARNING)

```
[WARNING][PIPELINE] request_id=abc123 chapter_code=6E_AA_TEST pipeline=MIXED event=fallback outcome=fallback reason=list_empty pool_size=0
```

#### 3. Placeholders non résolus (ERROR)

```
[ERROR][TESTS_DYN] request_id=abc123 chapter_code=6E_AA_TEST generator_key=THALES_V1 template_id=3 event=unresolved_placeholders outcome=error reason=placeholders_422 missing_placeholders=question,answer available_keys_count=8
```

#### 4. Exception (ERROR)

```
[ERROR][PIPELINE] request_id=abc123 chapter_code=6E_AA_TEST pipeline=TEMPLATE event=template_pipeline_exception outcome=error reason=generation_failed exception_type=ValueError exception_message=random.choice() called on empty list exception=Traceback (most recent call last):...
```

## Activation

### Mode développement (DEBUG complet)

```bash
export LOG_LEVEL=DEBUG
export LOG_VERBOSE=1
docker compose restart backend
```

### Mode production (diagnostic uniquement)

```bash
export LOG_LEVEL=INFO
export LOG_AUDIT=1
docker compose restart backend
```

### Mode production (modules spécifiques)

```bash
export LOG_LEVEL=INFO
export LOG_MODULES=PIPELINE,TESTS_DYN
docker compose restart backend
```

## Zones instrumentées

### A) Pipeline (`routes/exercises_routes.py`)

- `event=request_in` : début de requête
- `event=mixed_decision` : décision pipeline MIXED
- `event=fallback` : fallback avec `reason=...`
- `event=request_complete` : fin avec `outcome=success|error`
- `event=request_exception` : exception inattendue

### B) Tests Dyn Handler (`services/tests_dyn_handler.py`)

- `event=handler_in` : début handler
- `event=render_prepare` : préparation rendu (DEBUG)
- `event=unresolved_placeholders` : placeholders non résolus (WARNING/ERROR)
- `event=alias_applied` : alias appliqués (INFO)
- `event=variant_selected` : variant sélectionné (INFO)

### C) Generators (`generators/*.py`)

- `event=generate_in` : début génération
- `event=params` : paramètres (DEBUG)
- `event=pedagogy` : mode pédagogique (INFO)
- `event=pool_empty_prevented` : pool vide évité (WARNING)
- `event=svg_ids_stable` : IDs SVG stables (DEBUG)

### D) Cache/Persistence

- `event=cache_hit` / `event=cache_miss` : cache
- `event=db_count` : comptage DB
- `event=cache_invalidate` : invalidation cache

## Garde-fous

1. **Jamais d'exception avalée sans ERROR + contexte**
2. **Placeholders non résolus → WARNING/ERROR explicite**
3. **Fallbacks toujours avec `reason=...`** (list_empty|randrange_empty|no_dyn|placeholders_422|generator_unknown)
4. **Un seul stacktrace au point de capture** (en amont seulement WARNING)
5. **Pour placeholders : loguer uniquement `missing_placeholders` + `available_keys_count`** (pas de valeurs)

## Durations

Tous les événements importants incluent `duration_ms` :
- Requête complète
- Routing pipeline
- Génération générateur
- Rendu template
- Fetch DB

## Outcomes

Tous les événements importants incluent `outcome` :
- `success` : opération réussie
- `fallback` : fallback effectué
- `error` : erreur/exception
- `in_progress` : en cours

