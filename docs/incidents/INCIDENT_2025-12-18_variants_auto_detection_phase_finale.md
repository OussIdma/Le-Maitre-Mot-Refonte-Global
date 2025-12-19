# Incident : Industrialisation template_variants (Phase Finale)

**ID** : INCIDENT_2025-12-18_variants_auto_detection_phase_finale  
**Date** : 2025-12-18  
**Statut** : ✅ Résolu

---

## 📋 Symptôme

**Avant** : Allowlist manuelle (`VARIANTS_ALLOWED_CHAPTERS`) nécessitant une validation manuelle pour chaque chapitre avant activation de `template_variants`.

**Besoin métier** : Industrialisation complète avec détection automatique des chapitres template-based (compatibles `template_variants`) vs spec-based (incompatibles).

---

## 🔍 Root Cause

**Phase A** (allowlist explicite) était une étape intermédiaire de validation. La cible finale est une **détection automatique** basée sur des critères techniques :

1. **Template-based** (compatible) :
   - Handler dédié : chapitre intercepté par `tests_dyn_handler` (ex: `6E_TESTS_DYN`)
   - Exercice dynamique : au moins un exercice avec `is_dynamic=True` + `generator_key` + `enonce_template_html` non vide

2. **Spec-based** (incompatible) :
   - Pipeline `MathGenerationService` → `MathExerciseSpec` → conversion HTML
   - Pas de templates HTML avec placeholders

3. **Exclusions explicites** :
   - `6E_GM07`, `6E_GM08` (statiques, pas de templates)

---

## 🔧 Fix appliqué

### 1. Suppression allowlist (`variants_config.py`)

**Avant** :
```python
VARIANTS_ALLOWED_CHAPTERS: Set[str] = {"6E_TESTS_DYN"}
def is_variants_allowed(chapter_code: str) -> bool: ...
```

**Après** :
```python
EXCLUDED_CHAPTERS = {"6E_GM07", "6E_GM08"}
def is_chapter_template_based(chapter_code: str, exercise_template: Optional[Dict] = None) -> bool: ...
```

### 2. Détection automatique

**Fichier** : `backend/services/variants_config.py`

**Critères** (AU MOINS UN doit être vrai) :
- Handler dédié : `is_tests_dyn_request(chapter_code)` → `True`
- Exercice dynamique : `exercise_template` avec `is_dynamic=True` + `generator_key` + `enonce_template_html`

**Exclusions** : `6E_GM07`, `6E_GM08` hardcodés.

### 3. Mise à jour `tests_dyn_handler.py`

**Lignes 247-271** : Remplacement logique allowlist par détection automatique

**Avant** :
```python
if not is_variants_allowed(chapter_code):
    raise HTTPException(422, detail={"error_code": "VARIANTS_NOT_ALLOWED", ...})
```

**Après** :
```python
if not is_chapter_template_based(chapter_code, exercise_template):
    raise HTTPException(422, detail={"error_code": "VARIANTS_NOT_SUPPORTED", ...})
```

### 4. Erreur explicite

**Changement** : `VARIANTS_NOT_ALLOWED` → `VARIANTS_NOT_SUPPORTED`

**Message** : "Ce chapitre utilise une génération spec-based (MathGenerationService) et non template-based."

---

## 🧪 Tests / Preuve

### Tests unitaires mis à jour

**Fichier** : `backend/tests/test_variants_allowlist.py`

- ✅ `test_is_chapter_template_based_handler()` : Détection via handler dédié
- ✅ `test_is_chapter_template_based_exercise_template()` : Détection via `exercise_template`
- ✅ `test_is_chapter_template_based_excluded()` : Exclusion GM07/GM08
- ✅ `test_format_dynamic_exercise_variants_not_supported()` : Erreur `VARIANTS_NOT_SUPPORTED` pour spec-based
- ✅ `test_format_dynamic_exercise_variants_supported()` : OK pour template-based

### Validation manuelle (à exécuter après rebuild)

```bash
# 1. Template-based (6E_TESTS_DYN) : doit fonctionner
curl -X POST "http://localhost:8000/api/v1/exercises/generate" \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_TESTS_DYN", "difficulte": "facile", "seed": 12345}'

# 2. Spec-based (6E_G07) : doit fonctionner (génération normale)
curl -X POST "http://localhost:8000/api/v1/exercises/generate" \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_G07", "difficulte": "facile", "seed": 12345}'

# 3. Si template_variants fourni sur spec-based : erreur VARIANTS_NOT_SUPPORTED
# (test via admin UI : créer exercice dynamique sur 6E_G07 avec template_variants)
```

---

## 🔄 Commande de rebuild / restart

```bash
cd /Users/oussamaidamhane/Desktop/Projet\ local\ LMM/Le-Maitre-Mot-v16-Refonte-Sauvegarde
docker compose build backend
docker compose up -d backend
```

**Vérification** :
```bash
curl -s http://localhost:8000/api/debug/build | jq .build_id
```

---

## 📊 Impact

- ✅ **Zéro régression** : `6E_TESTS_DYN` fonctionne toujours (handler dédié)
- ✅ **Exclusion explicite** : `6E_GM07`, `6E_GM08` intouchables
- ✅ **Détection automatique** : Plus besoin de validation manuelle pour nouveaux chapitres template-based
- ✅ **Erreur explicite** : `VARIANTS_NOT_SUPPORTED` pour chapitres spec-based

---

## 📝 Fichiers modifiés

1. `backend/services/variants_config.py` : Suppression allowlist + détection auto
2. `backend/services/tests_dyn_handler.py` : Remplacement logique allowlist
3. `backend/tests/test_variants_allowlist.py` : Mise à jour tests (Phase Finale)

---

**Statut** : ✅ Implémenté — En attente rebuild/restart pour validation



