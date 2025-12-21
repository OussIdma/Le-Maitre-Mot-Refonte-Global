# Proof Pack Complet — Système de Logging P0

## Commandes d'activation

### 1. Mode développement (DEBUG complet)

```bash
export LOG_LEVEL=DEBUG
export LOG_VERBOSE=1
docker compose build backend
docker compose restart backend
```

### 2. Mode production (diagnostic uniquement)

```bash
export LOG_LEVEL=INFO
export LOG_AUDIT=1
docker compose build backend
docker compose restart backend
```

## Cas 1 : Requête normale (succès)

**Commande de test** :
```bash
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_AA_TEST",
    "difficulte": "moyen",
    "offer": "free",
    "seed": 42
  }'
```

**Logs attendus** (avec `LOG_VERBOSE=1`) :
```
[INFO][PIPELINE] request_id=a1b2c3d4 chapter_code=6E_AA_TEST code_officiel=6e_AA_TEST pipeline=MIXED difficulty=moyen offer=free seed=42 event=request_in outcome=in_progress
[INFO][PIPELINE] request_id=a1b2c3d4 chapter_code=6E_AA_TEST pipeline=MIXED event=mixed_decision outcome=success duration_ms=150
[INFO][TESTS_DYN] request_id=a1b2c3d4 chapter_code=6E_AA_TEST generator_key=THALES_V1 template_id=3 event=handler_in outcome=in_progress
[DEBUG][TESTS_DYN] request_id=a1b2c3d4 generator_key=THALES_V1 event=render_prepare available_keys_count=8
[INFO][TESTS_DYN] request_id=a1b2c3d4 generator_key=THALES_V1 event=alias_applied outcome=success alias_count=2
[INFO][TESTS_DYN] request_id=a1b2c3d4 generator_key=THALES_V1 event=variant_selected outcome=success variant_id=A variants_count=3
[INFO][TESTS_DYN] request_id=a1b2c3d4 chapter_code=6E_AA_TEST event=handler_complete outcome=success duration_ms=85
[INFO][PIPELINE] request_id=a1b2c3d4 chapter_code=6E_AA_TEST event=request_complete outcome=success duration_ms=250 exercise_id=ex_6e_aa_test_123
```

## Cas 2 : Placeholders non résolus (422) — UNRESOLVED_PLACEHOLDERS

**Commande de test** :
```bash
# Nécessite un exercice avec template utilisant {{question}} mais générateur ne fournissant pas cette variable
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_AA_TEST",
    "difficulte": "moyen"
  }'
```

**Logs attendus** :
```
[INFO][PIPELINE] request_id=b2c3d4e5 chapter_code=6E_AA_TEST pipeline=MIXED event=request_in outcome=in_progress
[INFO][TESTS_DYN] request_id=b2c3d4e5 chapter_code=6E_AA_TEST generator_key=THALES_V1 template_id=10 event=handler_in outcome=in_progress
[DEBUG][TESTS_DYN] request_id=b2c3d4e5 generator_key=THALES_V1 event=render_prepare available_keys_count=6
[WARNING][TESTS_DYN] request_id=b2c3d4e5 generator_key=THALES_V1 template_id=10 event=unresolved_placeholders outcome=error reason=placeholders_422 missing_placeholders=question,answer available_keys_count=6 expected_count=8
[ERROR][TESTS_DYN] request_id=b2c3d4e5 chapter_code=6E_AA_TEST generator_key=THALES_V1 event=handler_error outcome=error reason=unresolved_placeholders
[ERROR][PIPELINE] request_id=b2c3d4e5 chapter_code=6E_AA_TEST event=request_error outcome=error duration_ms=120 reason=http_exception error_code=UNRESOLVED_PLACEHOLDERS
```

## Cas 3 : Pool vide évité (WARNING)

**Commande de test** :
```bash
# Nécessite un chapitre avec pipeline MIXED mais aucun exercice dynamique pour la difficulté demandée
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_AA_TEST",
    "difficulte": "difficile",
    "offer": "free"
  }'
```

**Logs attendus** :
```
[INFO][PIPELINE] request_id=c3d4e5f6 chapter_code=6E_AA_TEST pipeline=MIXED difficulty=difficile offer=free event=request_in outcome=in_progress
[INFO][PIPELINE] request_id=c3d4e5f6 chapter_code=6E_AA_TEST pipeline=MIXED event=mixed_decision outcome=in_progress
[INFO][PIPELINE] request_id=c3d4e5f6 chapter_code=6E_AA_TEST pipeline=MIXED event=mixed_decision outcome=in_progress
[WARNING][PIPELINE] request_id=c3d4e5f6 chapter_code=6E_AA_TEST pipeline=MIXED event=pool_empty_prevented outcome=error reason=list_empty pool_size=0 pool_type=dynamic_exercises_filtered
[INFO][PIPELINE] request_id=c3d4e5f6 chapter_code=6E_AA_TEST event=request_complete outcome=fallback duration_ms=180
```

## Cas 4 : Exception inattendue

**Commande de test** :
```bash
# Nécessite un cas où une exception se produit (ex: générateur crash)
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_AA_TEST",
    "difficulte": "moyen"
  }'
```

**Logs attendus** :
```
[INFO][PIPELINE] request_id=d4e5f6g7 chapter_code=6E_AA_TEST pipeline=TEMPLATE event=request_in outcome=in_progress
[INFO][TESTS_DYN] request_id=d4e5f6g7 chapter_code=6E_AA_TEST generator_key=SIMPLIFICATION_FRACTIONS_V1 template_id=5 event=handler_in outcome=in_progress
[INFO][GENERATOR] request_id=d4e5f6g7 generator_key=SIMPLIFICATION_FRACTIONS_V1 event=generate_in outcome=in_progress
[WARNING][GENERATOR] request_id=d4e5f6g7 generator_key=SIMPLIFICATION_FRACTIONS_V1 event=pool_empty_prevented outcome=error reason=list_empty pool_size=0 pool_type=pgcd_options
[ERROR][GENERATOR] request_id=d4e5f6g7 generator_key=SIMPLIFICATION_FRACTIONS_V1 event=generate_exception outcome=error reason=generation_failed exception_type=ValueError exception_message=pgcd_options est vide pour difficulty=moyen
[ERROR][TESTS_DYN] request_id=d4e5f6g7 chapter_code=6E_AA_TEST generator_key=SIMPLIFICATION_FRACTIONS_V1 event=handler_exception outcome=error reason=generator_failed
[ERROR][PIPELINE] request_id=d4e5f6g7 chapter_code=6E_AA_TEST event=request_exception outcome=error duration_ms=95 reason=unexpected_exception exception_type=ValueError
```

## Validation

### Vérifier que les logs sont désactivés par défaut

```bash
# Sans ENV, vérifier qu'il n'y a pas de logs DEBUG
docker compose logs backend --tail 100 | grep -E "\[DEBUG\]" | wc -l
# → Devrait être 0
```

### Vérifier que LOG_VERBOSE active les DEBUG

```bash
# Avec LOG_VERBOSE=1
export LOG_VERBOSE=1
docker compose restart backend

# Vérifier qu'il y a des logs DEBUG
docker compose logs backend --tail 100 | grep -E "\[DEBUG\]" | wc -l
# → Devrait être > 0
```

## Fichiers modifiés

1. `backend/observability/logger.py` : Système de logging amélioré
2. `backend/observability/__init__.py` : Exports du module
3. `backend/routes/exercises_routes.py` : Instrumentation Pipeline
4. `backend/services/tests_dyn_handler.py` : Instrumentation Tests Dyn
5. `backend/generators/simplification_fractions_v1.py` : Instrumentation Generator
6. `backend/services/math_generation_service.py` : Remplacement de toutes les occurrences random.choice/randrange
7. `backend/generators/thales_generator.py` : Remplacement random.choice/randrange
8. `backend/data/tests_dyn_exercises.py` : Remplacement random.choice/randrange
9. `backend/data/gm07_exercises.py` : Remplacement random.choice/randrange
10. `backend/data/gm08_exercises.py` : Remplacement random.choice/randrange
11. `backend/gabarit_loader.py` : Remplacement random.choice/randrange
12. `backend/services/durees_premium_generator.py` : Remplacement random.choice/randrange

## Commandes de rebuild/restart

```bash
# Rebuild complet
docker compose build backend

# Restart
docker compose restart backend

# Vérifier les logs
docker compose logs backend --tail 50 --follow
```

