## INCIDENT – Template variants Étape 3 (pilotage élève TESTS_DYN)

### 1. Métadonnées

- **ID incident** : `INCIDENT_2025-12-18_template_variants_step3_pilot`
- **Date de détection** : 2025-12-18
- **Environnement** : local (élève, chapitre 6e_TESTS_DYN)
- **Gravité** : P3 (évolution contrôlée, scope pilote)
- **Statut** : résolu (Étape 3 déployée en local)

### 2. Résumé exécutif

- **Contexte** : après l’introduction du modèle `TemplateVariant` (Étape 1) et du moteur de sélection + preview admin (Étape 2), aucun pipeline élève n’utilisait encore les variants.
- **Objectif** : brancher le moteur de sélection de variants sur un pipeline élève pilote, sans impacter GM07/GM08 ni les chapitres legacy.
- **Choix du pilote** : le chapitre dynamique `6e_TESTS_DYN` (handler `tests_dyn_handler`) a été retenu comme pipeline élève pilote, car isolé et déjà équipé d’un garde-fou anti-placeholders.

### 3. Détails techniques – Pipeline pilote

- **Fichier handler** : `backend/services/tests_dyn_handler.py`
- **Fonction clé** : `format_dynamic_exercise(exercise_template, timestamp, seed=None)`
- **Comportement avant Étape 3** :
  - Sélection d’un exercice template depuis `backend/data/tests_dyn_exercises.py` (un seul couple `enonce_template_html` / `solution_template_html`).
  - Génération des variables via `generate_dynamic_exercise` (THALES_V1).
  - Mappings d’alias (triangle/rectangle/carré).
  - Rendu du template unique via `render_template`.
  - Garde-fou : si des `{{...}}` subsistent après rendu → `HTTP 422 UNRESOLVED_PLACEHOLDERS`.

### 4. Correctifs appliqués – Intégration des variants côté élève

- **Imports** :
  - Ajout de `from types import SimpleNamespace` et `from backend.services.dynamic_exercise_engine import choose_template_variant` en haut de `tests_dyn_handler.py`.

- **Sélection de variant dans `format_dynamic_exercise`** :
  - Calcul d’une `stable_key` métier pour le hash :
    - `stable_key = exercise_template.get("stable_key") or f"6E_TESTS_DYN:{exercise_template.get('id')}"`.
  - Lecture éventuelle des variants :
    - `template_variants = exercise_template.get("template_variants") or []`.
  - Si `template_variants` non vide :
    - Construction d’une liste de `SimpleNamespace` :
      - `id`, `enonce_template_html`, `solution_template_html`, `weight` (avec defaults) à partir de chaque dict.
    - Appel au moteur :
      - `chosen_variant = choose_template_variant(variants=variant_objs, seed=seed, exercise_id=stable_key)`.
    - Sélection des templates :
      - `enonce_template = chosen_variant.enonce_template_html`,
      - `solution_template = chosen_variant.solution_template_html`.
  - Sinon (aucun variant) :
    - Fallback sur le comportement legacy :
      - `enonce_template = exercise_template.get("enonce_template_html", "")`,
      - `solution_template = exercise_template.get("solution_template_html", "")`.

- **Garde-fou anti-placeholders** :
  - Inchangé et toujours appliqué APRÈS la sélection de variant :
    - extraction des placeholders attendus via `_extract_placeholders(enonce_template/solution_template)`,
    - rendu HTML,
    - détection de `{{...}}` résiduels,
    - en cas de placeholders non résolus → `HTTP 422` avec `error_code="UNRESOLVED_PLACEHOLDERS"` et détails (placeholders, clés fournies, id_exercice, figure_type…).

### 5. Tests

- **Fichier de tests dédié** : `backend/tests/test_tests_dyn_variants_step3.py`

- **Cas couverts** :
  - `test_tests_dyn_variant_selection_is_deterministic_for_seed` :
    - Injecte deux variants artificiels dans un exercice TESTS_DYN “facile” existant (`template_variants`),
    - pour un même `seed` et `timestamp`, `format_dynamic_exercise` produit le même `enonce_html`,
    - vérifie l’absence de `{{` dans l’énoncé.
  - `test_tests_dyn_variant_distribution_with_weights` :
    - Injecte deux variants avec labels “RARE” (weight=1) et “FREQUENT” (weight=10),
    - pour une grille de seeds, compte le nombre d’énoncés contenant chaque label,
    - vérifie que `"FREQUENT"` apparaît plus souvent que `"RARE"`.
  - `test_tests_dyn_no_unresolved_placeholders_with_variants` :
    - Assure que, avec des variants injectés, `enonce_html` et `solution_html` ne contiennent pas de `{{...}}` résiduels.

- **Non-régression GM07/GM08** :
  - Aucun changement n’a été apporté aux handlers GM07/GM08 ni au `MathGenerationService`.
  - Les tests de non-régression GM07/GM08 existants restent la référence (ex. `backend/tests/test_dynamic_exercises_p1.py` pour le scope historique).

### 6. Risques & suivi

- **Risques** :
  - Introduire des `template_variants` “réels” dans `tests_dyn_exercises.py` sans respecter les placeholders attendus pourrait déclencher le garde-fou 422 (comportement voulu).
  - Toute évolution future de `choose_template_variant` devra être testée à la fois côté preview admin (Étape 2) et côté élève (Étape 3).
- **Suivi** :
  - Étendre, après validation métier, l’usage de `template_variants` à d’autres chapitres dynamiques (via `ExercisePersistenceService`), en réutilisant exactement le même moteur et la même stratégie de garde-fou.





