# Incident : Généralisation template_variants — Phase A (Allowlist)

**ID** : INCIDENT_2025-12-18_variants_allowlist_phaseA  
**Date** : 2025-12-18  
**Type** : Évolution (feature flag)

---

## Symptôme

**Contexte** : Les `template_variants` fonctionnent sur le pilote `6e_TESTS_DYN`. Besoin de généraliser à d'autres chapitres dynamiques template-based, mais avec un contrôle strict (allowlist explicite).

**Problème** : Aucun mécanisme pour autoriser/interdire les `template_variants` par chapitre. Risque de :
- Utilisation accidentelle sur des chapitres non compatibles (spec-based via `MathGenerationService`)
- Pas de contrôle sur l'activation progressive

---

## Reproduction

**Avant le fix** :
- Aucune vérification : un exercice avec `template_variants` non vide serait traité même sur un chapitre non autorisé
- Pas de feature flag pour contrôler l'activation

**Après le fix** :
- Allowlist explicite : `VARIANTS_ALLOWED_CHAPTERS = {"6E_TESTS_DYN"}`
- Enforcement dans `format_dynamic_exercise()` : si `template_variants` non vide et chapitre non autorisé → erreur JSON `VARIANTS_NOT_ALLOWED`

---

## Root Cause (prouvée)

### Chaîne d'appel template-based (pilote `6e_TESTS_DYN`)

**Point d'entrée API** :
- `POST /api/v1/exercises/generate` avec `code_officiel="6e_TESTS_DYN"`

**Fichiers impliqués** :
1. `backend/routes/exercises_routes.py` (lignes 688-736) : intercept `is_tests_dyn_request()`
2. `backend/services/tests_dyn_handler.py` :
   - `generate_tests_dyn_exercise()` (ligne 333) : sélection template
   - `format_dynamic_exercise()` (ligne 77) : **CŒUR DU PIPELINE**
     - Ligne 209 : lecture `template_variants`
     - Lignes 232-236 : sélection variant via `choose_template_variant()`
     - Lignes 263-264 : rendu templates
     - Lignes 269-299 : garde anti-{{...}}

**Workflow** :
```
exercises_routes.py::generate_exercise()
  └─> is_tests_dyn_request("6e_TESTS_DYN") → True
  └─> generate_tests_dyn_exercise(offer, difficulty, seed)
      └─> get_random_tests_dyn_exercise() : sélection template (seed-based)
      └─> format_dynamic_exercise(template, timestamp, seed)
          └─> Ligne 209 : template_variants = exercise_template.get("template_variants") or []
          └─> Ligne 232 : choose_template_variant() si variants présents
          └─> Ligne 263 : render_template() avec variables générées
```

### Chapitres dynamiques non compatibles (spec-based)

**Pipeline** : `MathGenerationService` (lignes 34-110 dans `backend/services/math_generation_service.py`)

**Caractéristiques** :
- Génère des **specs structurées** (`MathExerciseSpec`) directement
- Pas de templates HTML avec placeholders `{{variable}}`
- Conversion specs → HTML final (pas de rendu template)
- Exemples : `6e_G07` (Symétrie axiale), `6e_N08` (Fractions), etc.

**Pourquoi non compatible** :
- Pas de `enonce_template_html` / `solution_template_html` avec placeholders
- Pas de générateur de variables (`generator_key`)
- Refonte majeure nécessaire pour supporter variants

---

## Fix appliqué

### 1. Nouveau module config

**Fichier** : `backend/services/variants_config.py` (NOUVEAU)

```python
VARIANTS_ALLOWED_CHAPTERS: Set[str] = {
    "6E_TESTS_DYN",  # Pilote (déjà fonctionnel)
}

def is_variants_allowed(chapter_code: str) -> bool:
    """Vérifie si un chapitre est autorisé (normalisation uppercase/trim)."""
    normalized = chapter_code.strip().upper()
    return normalized in VARIANTS_ALLOWED_CHAPTERS
```

### 2. Enforcement côté élève (runtime)

**Fichier** : `backend/services/tests_dyn_handler.py` (MODIFIÉ)

**Lignes** : 209-243 (ajout vérification allowlist avant sélection variant)

```python
# Ligne 207 : Calcul stable_key
stable_key = exercise_template.get("stable_key") or f"6E_TESTS_DYN:{exercise_template.get('id')}"

# Ligne 208 : Extraction chapter_code
chapter_code = exercise_template.get("chapter_code") or "6E_TESTS_DYN"

# Ligne 209 : Lecture template_variants
template_variants = exercise_template.get("template_variants") or []

# Lignes 210-234 : NOUVEAU — Enforcement allowlist
if template_variants:
    if not is_variants_allowed(chapter_code):
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "VARIANTS_NOT_ALLOWED",
                "error": "variants_not_allowed",
                "message": f"Les template_variants ne sont pas autorisés pour le chapitre '{chapter_code}'...",
                "chapter_code": chapter_code,
                "exercise_template_id": exercise_template.get("id"),
                "stable_key": stable_key,
                "allowed_chapters": sorted(list(VARIANTS_ALLOWED_CHAPTERS)),
                "hint": "Contactez l'équipe technique pour activer les variants sur ce chapitre."
            }
        )
    # Suite : sélection variant (lignes 232-236)
```

**Comportement** :
- Si `template_variants` non vide ET chapitre non autorisé → erreur JSON `VARIANTS_NOT_ALLOWED`
- Si `template_variants` vide → pas de vérification (compatibilité legacy)
- Si chapitre autorisé → traitement normal

### 3. Tests unitaires

**Fichier** : `backend/tests/test_variants_allowlist.py` (NOUVEAU)

**Tests** :
- `test_is_variants_allowed_normalization()` : normalisation uppercase/trim
- `test_format_dynamic_exercise_variants_not_allowed()` : erreur si chapitre non autorisé
- `test_format_dynamic_exercise_variants_allowed()` : OK si chapitre autorisé
- `test_format_dynamic_exercise_no_variants()` : pas de vérification si variants vides

---

## Tests / Preuve

### Tests unitaires

```bash
cd backend
pytest tests/test_variants_allowlist.py -v
```

**Résultats attendus** :
- ✅ `test_is_variants_allowed_normalization` : passe
- ✅ `test_format_dynamic_exercise_variants_not_allowed` : lève `HTTPException(422)` avec `error_code="VARIANTS_NOT_ALLOWED"`
- ✅ `test_format_dynamic_exercise_variants_allowed` : pas d'erreur `VARIANTS_NOT_ALLOWED`
- ✅ `test_format_dynamic_exercise_no_variants` : pas d'erreur `VARIANTS_NOT_ALLOWED`

### Non-régression

**Test `6e_TESTS_DYN` (chapitre autorisé)** :
```bash
curl -X POST "http://localhost:8000/api/v1/exercises/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_TESTS_DYN",
    "difficulte": "moyen",
    "seed": 42
  }'
```

**Résultat attendu** : Exercice généré normalement (pas d'erreur `VARIANTS_NOT_ALLOWED`)

**Test chapitre non autorisé (simulation)** :
- Créer un exercice avec `template_variants` non vide et `chapter_code="6E_G07"` dans MongoDB
- Appeler `format_dynamic_exercise()` avec ce template
- **Résultat attendu** : `HTTPException(422)` avec `error_code="VARIANTS_NOT_ALLOWED"`

---

## Commande de rebuild / restart

```bash
# Rebuild backend (si nécessaire)
docker compose build backend

# Restart backend
docker compose up -d backend

# Vérifier les logs
docker compose logs -f backend
```

---

## Impact

- ✅ **Sécurité** : Contrôle strict sur l'activation des variants par chapitre
- ✅ **Non-régression** : `6e_TESTS_DYN` fonctionne toujours (chapitre autorisé)
- ✅ **Évolutivité** : Ajout facile de nouveaux chapitres dans l'allowlist
- ✅ **Rollback** : Retrait facile d'un chapitre de l'allowlist

---

## Notes

- **Phase B (option)** : Capability DB `supports_template_variants: bool` non implémentée (Phase A suffisante pour l'instant)
- **Admin preview** : Pas d'enforcement (pas de `chapter_code` dans le contrat preview éphémère)
- **GM07/GM08** : Non impactés (intercepts en priorité, pas de variants)





