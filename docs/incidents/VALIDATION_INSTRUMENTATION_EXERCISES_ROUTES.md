# Validation Post-Instrumentation — exercises_routes.py
**Date :** 2025-01-XX  
**Objectif :** Valider l'instrumentation des logs structurés dans `backend/routes/exercises_routes.py`

---

## ✅ Vérifications préalables (déjà effectuées)

- [x] **Compilation Python** : `python3 -m py_compile backend/routes/exercises_routes.py` → OK
- [x] **Syntaxe AST** : Analyse syntaxique → Valide
- [x] **Imports observability** : Tous présents
- [x] **Remplacement random.choice** : 9 occurrences `safe_random_choice`, 0 `random.choice` restant
- [x] **Logs structurés** : 20 événements instrumentés

---

## 🔧 Tâches manuelles à exécuter

### 1. Rebuild/Restart Backend

```bash
cd /Users/oussamaidamhane/Desktop/Projet\ local\ LMM/Le-Maitre-Mot-v16-Refonte-Sauvegarde

# Rebuild backend
docker compose build backend

# Restart backend
docker compose restart backend

# Vérifier que le backend démarre sans erreur
docker compose ps
```

**Résultat attendu** :
- Backend `Up` et `healthy`
- Aucune erreur dans les logs de démarrage

---

### 2. Vérifier les logs pipeline au démarrage

```bash
docker compose logs --tail=50 backend | grep -E "\[PIPELINE\]|event="
```

**Résultat attendu** :
- Aucune erreur liée à l'instrumentation
- Si des requêtes sont en cours, voir les logs structurés

---

### 3. Test runtime — Pipeline MIXED (6e_AA_TEST)

#### Test 3.1 : Difficulté "facile"

```bash
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_AA_TEST", "difficulte": "facile", "offer": "free", "seed": 42}' \
  | jq '.'
```

**Logs attendus** :
```
[PIPELINE] event=request_in chapter_code=6e_AA_TEST niveau=6e difficulty=facile offer=free
[PIPELINE] event=mixed_decision chosen_path=MIXED chapter=6E_AA_TEST pipeline=MIXED
[PIPELINE] event=request_complete outcome=success duration_ms=XXX chosen_path=MIXED_dynamic_filtered|MIXED_dynamic_degraded|MIXED_static_fallback
```

**Résultat attendu** :
- HTTP 200 OK
- Exercice généré avec `enonce_html` et `solution_html`
- Aucun placeholder `{{...}}` visible

#### Test 3.2 : Difficulté "difficile"

```bash
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_AA_TEST", "difficulte": "difficile", "offer": "free", "seed": 42}' \
  | jq '.'
```

**Logs attendus** :
```
[PIPELINE] event=request_in chapter_code=6e_AA_TEST niveau=6e difficulty=difficile offer=free
[PIPELINE] event=mixed_decision chosen_path=MIXED chapter=6E_AA_TEST pipeline=MIXED
[PIPELINE] event=fallback reason=no_filtered_dynamic|no_dynamic_fallback_static (si dégradé)
[PIPELINE] event=request_complete outcome=success duration_ms=XXX chosen_path=MIXED_...
```

**Résultat attendu** :
- HTTP 200 OK ou HTTP 422 si aucun exercice disponible
- Si 422, vérifier que le message d'erreur est explicite
- Logs de fallback si applicable

---

### 4. Test runtime — Pipeline TEMPLATE

**Prérequis** : Identifier un chapitre avec `pipeline="TEMPLATE"` et des exercices dynamiques en DB.

```bash
# Remplacer CHAPITRE_TEMPLATE par un code_officiel réel avec pipeline TEMPLATE
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "CHAPITRE_TEMPLATE", "difficulte": "moyen", "offer": "free"}' \
  | jq '.'
```

**Logs attendus** :
```
[PIPELINE] event=request_in chapter_code=CHAPITRE_TEMPLATE niveau=6e difficulty=moyen offer=free
[PIPELINE] event=mixed_decision chosen_path=TEMPLATE chapter=CHAPITRE_TEMPLATE pipeline=TEMPLATE
[PIPELINE] event=request_complete outcome=success duration_ms=XXX chosen_path=TEMPLATE exercise_id=XXX generator_key=XXX
```

**Résultat attendu** :
- HTTP 200 OK
- Exercice dynamique généré
- `generator_key` présent dans les metadata

**Si erreur 422** :
```
[PIPELINE] event=request_error reason=http_exception error_code=TEMPLATE_PIPELINE_NO_DYNAMIC_EXERCISES
```

---

### 5. Test runtime — Pipeline SPEC

**Prérequis** : Identifier un chapitre avec `pipeline="SPEC"` et des exercices statiques en DB.

```bash
# Remplacer CHAPITRE_SPEC par un code_officiel réel avec pipeline SPEC
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "CHAPITRE_SPEC", "difficulte": "moyen", "offer": "free"}' \
  | jq '.'
```

**Logs attendus** :
```
[PIPELINE] event=request_in chapter_code=CHAPITRE_SPEC niveau=6e difficulty=moyen offer=free
[PIPELINE] event=mixed_decision chosen_path=SPEC chapter=CHAPITRE_SPEC pipeline=SPEC
[PIPELINE] event=request_complete outcome=success duration_ms=XXX chosen_path=SPEC_static exercise_id=XXX
```

---

### 6. Test runtime — Erreur de validation

```bash
# Test avec un chapitre inexistant ou invalide
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_INEXISTANT", "difficulte": "moyen", "offer": "free"}' \
  | jq '.'
```

**Logs attendus** :
```
[PIPELINE] event=request_in chapter_code=6e_INEXISTANT niveau=6e difficulty=moyen offer=free
[PIPELINE] event=request_error reason=http_exception|validation_error error_code=XXX
```

**Résultat attendu** :
- HTTP 422 ou 404
- Message d'erreur explicite
- Log d'erreur structuré

---

## 📊 Checklist de validation

### Compilation et syntaxe
- [x] `python3 -m py_compile` → OK
- [x] Analyse AST → Valide
- [x] Imports observability → Présents

### Docker
- [ ] `docker compose build backend` → OK
- [ ] `docker compose restart backend` → OK
- [ ] `docker compose ps` → Backend `Up` et `healthy`
- [ ] Logs démarrage → Aucune erreur

### Tests runtime — MIXED
- [ ] Test facile → HTTP 200, logs `event=request_in` + `event=mixed_decision` + `event=request_complete`
- [ ] Test difficile → HTTP 200 ou 422, logs avec fallback si applicable
- [ ] Aucun placeholder `{{...}}` dans les réponses

### Tests runtime — TEMPLATE
- [ ] Test TEMPLATE → HTTP 200, logs `event=request_in` + `event=mixed_decision` + `event=request_complete`
- [ ] `generator_key` présent dans les metadata

### Tests runtime — SPEC
- [ ] Test SPEC → HTTP 200, logs `event=request_in` + `event=mixed_decision` + `event=request_complete`

### Tests runtime — Erreurs
- [ ] Erreur 422 → Logs `event=request_error` avec `error_code`
- [ ] Erreur 500 → Logs `event=request_exception` avec `exception_type`

### Logs structurés
- [ ] `event=request_in` → Présent au début de chaque requête
- [ ] `event=mixed_decision` → Présent pour chaque décision pipeline
- [ ] `event=fallback` → Présent si dégradé (MIXED)
- [ ] `event=request_complete` → Présent en succès avec `duration_ms`
- [ ] `event=request_error` → Présent en erreur HTTP/validation
- [ ] `event=request_exception` → Présent en exception inattendue

---

## 🔍 Commandes de diagnostic

### Voir tous les logs pipeline
```bash
docker compose logs --tail=100 backend | grep -E "\[PIPELINE\]|event="
```

### Voir uniquement les erreurs
```bash
docker compose logs --tail=100 backend | grep -E "event=request_error|event=request_exception"
```

### Voir les décisions pipeline
```bash
docker compose logs --tail=100 backend | grep "event=mixed_decision"
```

### Voir les fallbacks
```bash
docker compose logs --tail=100 backend | grep "event=fallback"
```

### Voir les durées de génération
```bash
docker compose logs --tail=100 backend | grep "event=request_complete" | grep -o "duration_ms=[0-9]*"
```

---

## 📝 Résultats attendus par scénario

### Scénario 1 : MIXED avec exercices dynamiques disponibles
- **HTTP** : 200 OK
- **Logs** : `event=request_in` → `event=mixed_decision chosen_path=MIXED` → `event=request_complete chosen_path=MIXED_dynamic_filtered`
- **Durée** : `duration_ms` < 1000ms (généralement)

### Scénario 2 : MIXED sans exercices dynamiques (fallback statique)
- **HTTP** : 200 OK
- **Logs** : `event=request_in` → `event=mixed_decision` → `event=fallback reason=no_dynamic_fallback_static` → `event=request_complete chosen_path=MIXED_static_fallback`
- **Durée** : `duration_ms` < 1000ms

### Scénario 3 : MIXED sans exercices du tout
- **HTTP** : 422 Unprocessable Entity
- **Logs** : `event=request_in` → `event=mixed_decision` → `event=request_error reason=http_exception error_code=NO_EXERCISE_AVAILABLE`
- **Message** : Erreur explicite avec `error_code` et `hint`

### Scénario 4 : TEMPLATE avec exercices dynamiques
- **HTTP** : 200 OK
- **Logs** : `event=request_in` → `event=mixed_decision chosen_path=TEMPLATE` → `event=request_complete chosen_path=TEMPLATE`
- **Metadata** : `generator_key` présent

### Scénario 5 : TEMPLATE sans exercices dynamiques
- **HTTP** : 422 Unprocessable Entity
- **Logs** : `event=request_in` → `event=mixed_decision` → `event=request_error error_code=TEMPLATE_PIPELINE_NO_DYNAMIC_EXERCISES`
- **Message** : Erreur explicite avec `hint` pour créer des exercices dynamiques

---

## ⚠️ Problèmes potentiels et solutions

### Problème 1 : Backend ne démarre pas
**Symptôme** : `docker compose ps` montre backend `Exit` ou `Restarting`

**Solution** :
```bash
docker compose logs backend | tail -50
# Vérifier les erreurs d'import ou de syntaxe
```

### Problème 2 : Logs `[PIPELINE]` absents
**Symptôme** : Les logs structurés n'apparaissent pas

**Solution** :
- Vérifier que `obs_logger = get_obs_logger('PIPELINE')` est présent
- Vérifier que les imports `backend.observability` sont corrects
- Vérifier les variables d'environnement `LOG_LEVEL`, `LOG_VERBOSE`

### Problème 3 : Erreur `NameError: name 'ctx' is not defined`
**Symptôme** : Erreur runtime dans les logs

**Solution** :
- Vérifier que `ctx = get_request_context()` est appelé avant utilisation
- Vérifier l'indentation des blocs `if pipeline_mode == "..."`

### Problème 4 : `safe_random_choice` non trouvé
**Symptôme** : `NameError: name 'safe_random_choice' is not defined`

**Solution** :
- Vérifier l'import : `from backend.observability import safe_random_choice`
- Rebuild Docker : `docker compose build backend`

---

## ✅ Définition of Done

L'instrumentation est validée si :
- [x] Compilation Python OK
- [ ] Backend démarre sans erreur
- [ ] Tests MIXED (facile/difficile) → HTTP 200 ou 422 explicite
- [ ] Tests TEMPLATE → HTTP 200 avec `generator_key`
- [ ] Logs `event=request_in` présents
- [ ] Logs `event=mixed_decision` présents pour chaque décision
- [ ] Logs `event=request_complete` présents en succès
- [ ] Logs `event=request_error` présents en erreur
- [ ] Aucun placeholder `{{...}}` dans les réponses
- [ ] `duration_ms` présent dans tous les logs de complétion

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Checklist prête pour validation manuelle


