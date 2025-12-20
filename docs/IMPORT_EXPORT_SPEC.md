# 📦 Import / Export — Chapitres & Exercices (Spécification)

Version: 1.0  
Périmètre: Curriculum 6e (extensible autres niveaux)

## 1. Principes
- Format pivot: JSON (un ou plusieurs chapitres).
- `code_officiel` = clé unique pour tous les chapitres (y compris tests, domaine "Tests").
- Pipelines explicites: `SPEC` | `TEMPLATE` | `MIXED`.
- Source de vérité generator_key → exercise_type: `GeneratorFactory` (aliases inclus).
- `family` déprécié: toléré en lecture, jamais requis en écriture.

## 2. Schéma JSON proposé
```json
{
  "niveau": "6e",
  "chapters": [
    {
      "code_officiel": "6e_N08",
      "domaine": "Nombres et calculs",
      "libelle": "Fractions comme partage et quotient",
      "pipeline": "SPEC",
      "statut": "prod",
      "exercise_types": ["CALCUL_FRACTIONS", "FRACTION_REPRESENTATION"],
      "exercises": [
        {
          "id": 1,
          "title": "Test statique",
          "is_dynamic": false,
          "exercise_type": "CALCUL_FRACTIONS",
          "offer": "free",
          "difficulty": "facile",
          "enonce_html": "<p>...</p>",
          "solution_html": "<p>...</p>",
          "needs_svg": false
        }
      ]
    },
    {
      "code_officiel": "6e_TESTS_DYN",
      "domaine": "Tests",
      "libelle": "Tests dynamiques",
      "pipeline": "TEMPLATE",
      "statut": "prod",
      "exercises": [
        {
          "id": 1,
          "title": "Thalès dynamique",
          "is_dynamic": true,
          "generator_key": "THALES_V1",
          "offer": "free",
          "difficulty": "moyen",
          "enonce_template_html": "<p>...</p>",
          "solution_template_html": "<p>...</p>",
          "template_variants": []
        }
      ]
    }
  ]
}
```

## 3. Règles de validation
- `pipeline=SPEC` : `exercise_types` ⊂ `MathExerciseType` OU statiques fournis. Sinon 422 `SPEC_PIPELINE_INVALID_EXERCISE_TYPES`.
- `pipeline=TEMPLATE` : ≥1 exercice dynamique (`is_dynamic=true`, `generator_key` connu). Sinon 422 `TEMPLATE_PIPELINE_NO_DYNAMIC_EXERCISES`.
- `pipeline=MIXED` : dyn prioritaires, statiques fallback ; sinon 422 `NO_EXERCISE_AVAILABLE`.
- `generator_key` : doit exister dans Factory ; `exercise_type` déduit, collision refusée (400).
- `family` : ignoré si absent, warning si présent ; ne bloque pas l’import.
- `offer` ∈ {free, pro}, `difficulty` ∈ {facile, moyen, difficile}.
- Unicité `code_officiel` : collision → 409.

## 4. Import (à implémenter)
- Endpoint suggéré: `POST /api/admin/chapters/import`.
- Étapes:
  1) Validation structure (niveau, chapters).
  2) Validation pipeline + prérequis (voir règles).
  3) Validation générateurs via `GeneratorFactory` (aliases inclus).
  4) Transaction DB: upsert chapitre + exercices.
  5) Validation post-import: TEMPLATE → check dyn ≥1 ; SPEC → types valides ou statiques.
  6) Invalidation caches: stats, catalogue (`invalidate_catalog_cache("6e")`), index curriculum si nécessaire.
- Erreurs normalisées (422): `TEMPLATE_PIPELINE_NO_DYNAMIC_EXERCISES`, `SPEC_PIPELINE_INVALID_EXERCISE_TYPES`, `INVALID_GENERATOR_KEY`, `NO_EXERCISE_AVAILABLE`.

## 5. Export (à implémenter)
- Endpoints suggérés:
  - `GET /api/admin/chapters/{code_officiel}/export` (chapitre complet).
  - `GET /api/admin/chapters/{code_officiel}/exercises/export?pipeline=TEMPLATE|SPEC` (filtre dyn/stat).
- Comportement:
  - Retourne métadonnées chapitre + exercices filtrés (dyn seuls si pipeline=TEMPLATE, statiques si pipeline=SPEC, sinon tous).
  - `family` inclus en lecture seule pour compat legacy.

## 6. Caches
- Catalogue (`/api/v1/catalog`) cache TTL 5 min, déjà invalidé en create/update/delete exercices (6e). Refaire après import pour refléter les changements.

## 7. Points de contrôle avant import
- Cohérence `offer` / `difficulty`.
- Chapitres de test: domaine “Tests”, statut prod/beta, `code_officiel` format 6e_XXX.
- `family` à vide si non nécessaire.
- `generator_key` présent dans Factory (aliases gérés).

## 8. Plan de tests (post-implémentation)
- Import SPEC valide → OK (exercise_types connus).
- Import TEMPLATE sans dyn → 422.
- Import MIXED dyn+stat → génération dyn prioritaire, stat fallback.
- Import avec generator_key inconnu → 422.
- Export chapitre MIXED avec filtre TEMPLATE → dyn seuls ; filtre SPEC → statiques.
- Catalogue rafraîchi après import (cache invalidé).

## 9. Décisions
- Format pivot JSON unique, pipelines explicites.
- `code_officiel` unique pour tous les chapitres (incl. tests).
- Factory = source unique generator_key → exercise_type.
- `family` déprécié (lecture tolérée, jamais exigé).

## 10. Points à compléter avant implémentation
1) Validation pipeline (pré vs post)  
   - Pré-validation : vérifier la structure et les prérequis (ex: TEMPLATE doit déclarer au moins un exo dyn dans le payload).  
   - Post-validation : après insertion, re-check en DB (ex: dyn réellement présents pour TEMPLATE ; exercise_types valides ou statiques présents pour SPEC).

2) Migration family → exercise_type  
   - Documenter la stratégie : family en lecture seule (warning), ne jamais l’exiger ; encourager exercise_type (statique) ou generator_key (dynamique) comme source unique.

3) Validation generator_key stricte  
   - Refuser tout generator_key inconnu ou sans exercise_type dans la Factory (aliases compris) ; collision exercise_type/generator_key → erreur explicite.

4) Format TSV vs JSON  
   - Garder JSON comme pivot (structuré, validable).  
   - Si TSV souhaité : le considérer comme un format dérivé/annexe, avec conversion → JSON pivot avant import.

5) Invalidation des caches (détailler)  
   - Après import : invalider caches stats, catalogue (`invalidate_catalog_cache("6e")`), index curriculum en mémoire si nécessaire.  
   - Après export : aucun impact cache.

6) Filtre pipeline à l’export  
   - Endpoint export doit accepter `?pipeline=TEMPLATE|SPEC` pour MIXED afin d’exporter dyn ou stat séparément.
