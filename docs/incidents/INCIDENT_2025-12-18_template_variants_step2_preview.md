## INCIDENT – Template variants Étape 2 (moteur & preview admin)

### 1. Métadonnées

- **ID incident** : `INCIDENT_2025-12-18_template_variants_step2_preview`
- **Date de détection** : 2025-12-18
- **Environnement** : local (admin / preview dynamique)
- **Gravité** : P3 (évolution fonctionnelle contrôlée, pas d’impact élève)
- **Statut** : résolu (Étape 2 déployée en local)

### 2. Résumé exécutif

- **Contexte** : après Étape 1 (modèle `TemplateVariant` + validations), il manquait un moteur unique de sélection de variant et un branchement propre sur la preview admin.
- **Objectif** : permettre à la preview admin d’utiliser des variants de templates d’énoncé/solution de manière déterministe par seed, sans impacter les pipelines élèves (GM07/GM08 inclus).
- **Décision** : introduire un service dédié `dynamic_exercise_engine.choose_template_variant` et l’utiliser uniquement dans `preview_dynamic_exercise`, avec support d’un mode éphémère basé sur `template_variants` passés dans la requête.

### 3. Root cause (besoin)

- Avant cette étape :
  - La preview admin n’avait pas de notion de variants : elle rendait toujours un unique couple `enonce_template_html` / `solution_template_html`.
  - Aucune fonction partagée ne permettait de choisir un variant de façon déterministe à partir d’une seed et d’un identifiant d’exercice.
- Le besoin métier/spec :
  - mutualiser la logique de sélection de variant (preview +, plus tard, pipeline élève),
  - garantir que la même seed et le même identifiant logique (stable_key) donnent toujours le même variant.

### 4. Correctifs appliqués

- **Service de sélection de variants** (`backend/services/dynamic_exercise_engine.py`) :
  - Création de `choose_template_variant(variants, seed, exercise_id, mode="seed_random", fixed_variant_id=None)` :
    - `variants` : liste d’objets avec au moins `id` et `weight`.
    - `mode="seed_random"` :
      - construit une clé `base = f"{exercise_id}:{seed or 'no-seed'}"`,
      - calcule `val = int(sha256(base)[:8], 16)`,
      - effectue une sélection pondérée sur les `weight` (>=1) pour obtenir un index `val % total_weight`.
    - `mode="fixed"` :
      - force un variant via `fixed_variant_id`,
      - lève `ValueError` si l’id est introuvable.
    - Aucune utilisation de RNG global (`random`), fonction pure de ses paramètres.

- **Preview admin – extension du contrat** (`backend/routes/generators_routes.py`) :
  - Nouveau modèle `PreviewTemplateVariant` :
    - `id: str`,
    - `enonce_template_html: str`,
    - `solution_template_html: str`,
    - `weight: int = 1` (avec `ge=1`).
  - Évolution de `DynamicPreviewRequest` :
    - champs existants :
      - `generator_key`, `enonce_template_html`, `solution_template_html`, `difficulty`, `seed`, `svg_mode`,
    - nouveaux champs :
      - `template_variants?: List[PreviewTemplateVariant]` (mode multi-variants, éphémère, sans lecture DB),
      - `variant_id?: str` (mode fixed pour forcer un variant),
      - `stable_key?: str` (clé stable logique, ex. `"6e_G07:3"` ; si absente, fallback sur `generator_key`).

- **Preview admin – sélection de variant & rendu** (`preview_dynamic_exercise`) :
  - Après génération des `all_vars` (Factory ou legacy), ajout d’une étape de sélection :
    - `exercise_id = request.stable_key or request.generator_key`,
    - `selection_mode = "fixed"` si `variant_id` présent, sinon `"seed_random"`.
    - Si `template_variants` non vide :
      - appel à `choose_template_variant(variants=request.template_variants, seed=request.seed, exercise_id=exercise_id, mode=selection_mode, fixed_variant_id=request.variant_id)`,
      - en cas de `ValueError` (ex. `variant_id` introuvable) : retour d’un `HTTP 400` JSON explicite :
        - `error_code = "INVALID_TEMPLATE_VARIANT"`,
        - `success = False`, `enonce_html = ""`, `solution_html = ""`, `errors = [str(e)]`.
      - sinon, `template_enonce = chosen.enonce_template_html`, `template_solution = chosen.solution_template_html`.
    - Si `template_variants` vide/absent :
      - fallback sur `request.enonce_template_html` / `request.solution_template_html` (comportement historique).
  - Le rendu final reste assuré par `render_template(template_enonce, all_vars)` et `render_template(template_solution, all_vars)`.

- **Garde-fou placeholders** :
  - La logique existante de détection des `{{var}}` non résolus en preview est conservée :
    - recherche de `{{...}}` dans `enonce_html` et `solution_html`,
    - ajout d’entrées dans `errors` de type `"Variable inconnue: {{var}}"`,
    - `success` à `False` si la liste `errors` n’est pas vide,
    - réponse JSON structurée (`DynamicPreviewResponse`) sans crash backend.

### 5. Tests

- **Tests unitaires sur le moteur** (`backend/tests/test_dynamic_exercise_engine.py`) :
  - `test_choose_template_variant_seed_random_is_deterministic` :
    - même `(variants, seed, exercise_id)` → même `variant.id`.
  - `test_choose_template_variant_changes_with_seed` :
    - vérifie que, pour des seeds différents, on obtient des variants plausiblement différents.
  - `test_choose_template_variant_respects_weights` :
    - sur un grand nombre de seeds, le variant avec `weight=10` est sélectionné plus souvent qu’un variant avec `weight=1`.
  - `test_choose_template_variant_fixed_mode_ok` :
    - en mode `"fixed"` avec `fixed_variant_id="v1"`, le variant `v1` est toujours renvoyé.
  - `test_choose_template_variant_fixed_mode_invalid_id_raises` :
    - en mode `"fixed"` avec un id inexistant, la fonction lève un `ValueError`.

- **Tests preview admin (scénarios attendus)** :
  - Non exécutés automatiquement dans cette étape (pas de test d’intégration HTTP ajouté), mais scénarios ciblés :
    - **Seed déterministe** :
      - même payload `DynamicPreviewRequest` avec `template_variants` + même `seed` + même `stable_key` → même variant choisi (visible via `enonce_html` / `solution_html`).
    - **Mode fixed** :
      - en ajoutant `variant_id="v2"` dans le payload, on force systématiquement le variant `v2`, indépendamment de la seed.

### 6. Contraintes & non-régressions

- **Zéro impact GM07/GM08 / génération élève** :
  - Aucun changement apporté aux endpoints de génération élève (`/api/v1/exercises/generate`, pipelines GM07/GM08, TESTS_DYN).
  - Seuls les fichiers suivants sont touchés :
    - `backend/services/dynamic_exercise_engine.py`,
    - `backend/routes/generators_routes.py` (preview admin uniquement),
    - `backend/tests/test_dynamic_exercise_engine.py`.
- **Pas de RNG global** :
  - `choose_template_variant` n’utilise pas `random` ni `random.seed`, uniquement `hashlib.sha256`.






