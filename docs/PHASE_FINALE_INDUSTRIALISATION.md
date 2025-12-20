# Phase Finale — Industrialisation template_variants

**Date** : 2025-12-18  
**Objectif** : Supprimer l'allowlist manuelle et activer automatiquement `template_variants` sur tous les chapitres template-based.

---

## 🎯 Objectif métier

**Avant** : Allowlist explicite (`VARIANTS_ALLOWED_CHAPTERS`) nécessitant une validation manuelle pour chaque chapitre.

**Après** : Détection automatique basée sur des critères techniques. Activation automatique sur les chapitres template-based, interdiction automatique sur les chapitres spec-based.

---

## 🔍 Analyse technique — Distinction template-based vs spec-based

### Critères de détection automatique

#### **Template-based** (compatible `template_variants`)
Un chapitre est **template-based** si **AU MOINS UN** de ces critères est vrai :

1. **Critère DB (MongoDB)** :
   - Le chapitre a au moins un exercice avec :
     - `is_dynamic=True`
     - `generator_key` non vide (ex: `THALES_V1`, `SYMETRIE_AXIALE_V2`)
     - `enonce_template_html` non vide (présence de placeholders `{{variable}}`)

2. **Critère Handler dédié** :
   - Le chapitre utilise un handler dédié (ex: `tests_dyn_handler.py`)
   - Pipeline : `format_dynamic_exercise` → rendu template → génération SVG

3. **Critère Pipeline** :
   - Le chapitre passe par `tests_dyn_handler` ou équivalent
   - Utilise `render_template` avec placeholders

#### **Spec-based** (incompatible `template_variants`)
Un chapitre est **spec-based** si :

1. **Pipeline MathGenerationService** :
   - Utilise `MathGenerationService.generate_math_exercise_specs`
   - Génère des `MathExerciseSpec` structurées (géométrie, calculs, etc.)
   - Conversion specs → HTML via `_build_fallback_enonce` ou équivalent

2. **Pas de templates HTML** :
   - Aucun exercice avec `is_dynamic=True` + `generator_key` + `enonce_template_html`
   - Génération procédurale (pas de placeholders)

3. **Chapitres exclus** :
   - `6E_GM07` (statique, handler dédié)
   - `6E_GM08` (statique, handler dédié)
   - Tous les chapitres via `code_officiel` non interceptés par `tests_dyn_handler`

---

## 📊 Cartographie actuelle

### Chapitres template-based identifiés

| Chapitre | Critère | Handler | Pipeline |
|----------|---------|---------|----------|
| `6E_TESTS_DYN` | DB + Handler | `tests_dyn_handler.py` | `format_dynamic_exercise` → `render_template` |
| `6E_G07` (potentiel) | DB (si exercices dynamiques créés via admin) | `tests_dyn_handler` (si intercepté) | À vérifier |

### Chapitres spec-based (exclus)

| Chapitre | Pipeline | Raison exclusion |
|----------|----------|------------------|
| `6E_GM07` | `gm07_handler.py` | Statique, pas de templates |
| `6E_GM08` | `gm08_handler.py` | Statique, pas de templates |
| Tous autres via `code_officiel` | `MathGenerationService` | Spec-based, pas de templates |

---

## 🏗️ Architecture proposée

### 1. Fonction de détection automatique

**Fichier** : `backend/services/variants_config.py`

```python
async def is_chapter_template_based(chapter_code: str, exercise_service: ExercisePersistenceService) -> bool:
    """
    Détecte automatiquement si un chapitre est template-based.
    
    Critères (AU MOINS UN doit être vrai) :
    1. DB : au moins un exercice avec is_dynamic=True + generator_key + enonce_template_html
    2. Handler : chapitre intercepté par tests_dyn_handler (ou équivalent)
    
    Returns:
        True si template-based (compatible template_variants)
        False si spec-based ou statique (incompatible)
    """
    # Normalisation
    chapter_upper = chapter_code.upper().replace("-", "_")
    
    # Exclusion explicite (GM07/GM08)
    if chapter_upper in ["6E_GM07", "6E_GM08"]:
        return False
    
    # Critère 1 : Vérifier en DB
    exercises = await exercise_service.get_exercises(chapter_code)
    for ex in exercises:
        if (
            ex.get("is_dynamic") is True
            and ex.get("generator_key")
            and ex.get("enonce_template_html")
        ):
            return True
    
    # Critère 2 : Handler dédié (tests_dyn_handler)
    from backend.services.tests_dyn_handler import is_tests_dyn_request
    if is_tests_dyn_request(chapter_code):
        return True
    
    # Par défaut : spec-based (incompatible)
    return False
```

### 2. Suppression de l'allowlist

**Fichier** : `backend/services/variants_config.py`

- ❌ Supprimer `VARIANTS_ALLOWED_CHAPTERS`
- ❌ Supprimer `is_variants_allowed` (remplacé par `is_chapter_template_based`)

### 3. Intégration dans `tests_dyn_handler.py`

**Fichier** : `backend/services/tests_dyn_handler.py`

**Lignes 213-275** : Remplacer la logique allowlist par la détection automatique

```python
# AVANT (Phase A)
if not is_variants_allowed(chapter_code):
    raise HTTPException(422, detail={"error_code": "VARIANTS_NOT_ALLOWED", ...})

# APRÈS (Phase Finale)
from backend.services.variants_config import is_chapter_template_based
from backend.services.exercise_persistence_service import get_exercise_service

exercise_service = get_exercise_service()
is_template_based = await is_chapter_template_based(chapter_code, exercise_service)

if not is_template_based:
    raise HTTPException(
        status_code=422,
        detail={
            "error_code": "VARIANTS_NOT_SUPPORTED",
            "error": "variants_not_supported",
            "message": (
                f"Les template_variants ne sont pas supportés pour le chapitre '{chapter_code}'. "
                f"Ce chapitre utilise une génération spec-based (MathGenerationService) "
                f"et non template-based."
            ),
            "chapter_code": chapter_code,
            "hint": "Les template_variants sont uniquement disponibles pour les chapitres template-based (avec is_dynamic=True + generator_key + enonce_template_html)."
        },
    )
```

---

## ⚠️ Risques et garde-fous

### Risques identifiés

1. **Performance** : Requête MongoDB à chaque appel `format_dynamic_exercise`
   - **Mitigation** : Cache en mémoire (dict `_template_based_cache`) avec TTL ou invalidation à la création/modification d'exercice

2. **Faux positifs** : Chapitre avec 1 exercice dynamique mais majoritairement spec-based
   - **Mitigation** : Critère strict : au moins 1 exercice avec `is_dynamic=True` + `generator_key` + `enonce_template_html` non vide

3. **Faux négatifs** : Chapitre template-based sans exercices en DB (création future)
   - **Mitigation** : Critère Handler dédié (`is_tests_dyn_request`) comme fallback

4. **GM07/GM08** : Exclusion explicite (statique, pas de templates)
   - **Mitigation** : Hardcode dans `is_chapter_template_based` (ligne 1)

### Garde-fous

- ✅ Exclusion explicite GM07/GM08 (intouchables)
- ✅ Erreur JSON explicite si chapitre non template-based
- ✅ Pas de fallback silencieux vers spec-based
- ✅ Log structuré pour audit

---

## 📝 Plan d'implémentation

### Étape 1 : Refactor `variants_config.py`
- Supprimer `VARIANTS_ALLOWED_CHAPTERS` et `is_variants_allowed`
- Implémenter `is_chapter_template_based` (async, requête DB)
- Ajouter cache optionnel (performance)

### Étape 2 : Mise à jour `tests_dyn_handler.py`
- Remplacer `is_variants_allowed` par `is_chapter_template_based`
- Adapter l'erreur `VARIANTS_NOT_ALLOWED` → `VARIANTS_NOT_SUPPORTED`
- Gérer l'async (injection `exercise_service`)

### Étape 3 : Tests non-régression
- `6E_TESTS_DYN` : doit toujours fonctionner
- `6E_GM07` / `6E_GM08` : doivent être exclus (erreur si `template_variants` fourni)
- Chapitre spec-based : erreur explicite

### Étape 4 : Documentation
- Incident report : `docs/incidents/INCIDENT_YYYY-MM-DD_variants_auto_detection.md`
- Changelog : `docs/CHANGELOG_TECH.md`

---

## 🧪 Tests de validation

### Test 1 : Chapitre template-based existant
```bash
curl -X POST "http://localhost:8000/api/v1/exercises/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_TESTS_DYN",
    "difficulte": "facile",
    "seed": 12345
  }'
```
**Attendu** : ✅ Fonctionne (comme avant)

### Test 2 : Chapitre spec-based (erreur explicite)
```bash
curl -X POST "http://localhost:8000/api/v1/exercises/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_G07",
    "difficulte": "facile",
    "seed": 12345
  }'
```
**Attendu** : ✅ Fonctionne (génération spec-based normale)

Si `template_variants` fourni dans un exercice spec-based :
**Attendu** : ❌ HTTP 422 `VARIANTS_NOT_SUPPORTED`

### Test 3 : GM07/GM08 (exclusion explicite)
**Attendu** : ❌ HTTP 422 si `template_variants` fourni

---

## 📌 Décisions techniques

1. **Cache** : Optionnel (performance), TTL 5 min ou invalidation à la création/modification
2. **Async** : `is_chapter_template_based` doit être async (requête MongoDB)
3. **Erreur** : `VARIANTS_NOT_SUPPORTED` (plus explicite que `VARIANTS_NOT_ALLOWED`)
4. **Exclusion** : GM07/GM08 hardcodés (pas de détection, exclusion explicite)

---

## ✅ Definition of Done

- [ ] `variants_config.py` : Suppression allowlist + implémentation détection auto
- [ ] `tests_dyn_handler.py` : Remplacement logique allowlist par détection auto
- [ ] Tests non-régression : 6E_TESTS_DYN, GM07, GM08, chapitre spec-based
- [ ] Documentation : Incident + Changelog
- [ ] Rebuild/restart backend
- [ ] Validation curl : template-based OK, spec-based erreur explicite

---

**Statut** : 📋 Analyse terminée — En attente validation avant implémentation




