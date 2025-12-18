## INCIDENT – Template variants Étape 1 (modèle & validations)

### 1. Métadonnées

- **ID incident** : `INCIDENT_2025-12-18_template_variants_step1`
- **Date de détection** : 2025-12-18
- **Environnement** : local (admin API)
- **Gravité** : P3 (cohérence modèle / spec, pas d’impact élève en production)
- **Statut** : résolu

### 2. Résumé exécutif

- **Contexte** : introduction de `TemplateVariant` et du champ `template_variants` pour préparer les variants d’énoncés dynamiques (Étape 1 de la SPEC).
- **Symptôme** : la spec validée indiquait qu’un exercice dynamique pouvait être défini soit par des templates legacy (`enonce_template_html` / `solution_template_html`), soit par une liste de `template_variants`. La première implémentation n’appliquait pas encore cette règle de manière stricte.
- **Décision** : aligner la validation métier sur la SPEC (OR logique entre legacy et variants) et isoler cette évolution dans un incident dédié (sans polluer l’incident THALES).

### 3. Reproduction / Comportement

- **Cas visé** : création d’un exercice dynamique via l’API admin avec :
  - `is_dynamic = true`,
  - `generator_key` renseigné,
  - `template_variants` non vide,
  - `enonce_template_html` et `solution_template_html` vides ou `null`.
- **Comportement attendu (SPEC)** :
  - ce cas doit être **accepté** : les variants deviennent la source de vérité.
- **Comportement après correctif** :
  - le service accepte bien ce type de requête, tout en refusant toujours les exercices dynamiques sans aucun template (legacy ou variant).

### 4. Root cause (côté code)

- **Fichier** : `backend/services/exercise_persistence_service.py`
- **Zone concernée** : méthode `ExercisePersistenceService._validate_exercise_data` :
  - La logique de validation dynamique ne tenait initialement compte que des templates legacy (`enonce_template_html` / `solution_template_html`), sans OR explicite avec `template_variants`.
  - Après ajustement, la validation applique maintenant :
    - `has_legacy = enonce_template_html non vide ET solution_template_html non vide`,
    - `has_variants = template_variants non vide`,
    - `has_legacy OR has_variants` requis pour tout exercice dynamique.

### 5. Correctif appliqué

- **Backend – validations** (`backend/services/exercise_persistence_service.py`) :
  - Ajout d’un calcul explicite :
    - `has_variants = request.template_variants and len(request.template_variants) > 0`.
    - `has_legacy_templates = ...` (énoncé + solution legacy non vides).
  - Nouvelle règle :
    - si `not has_legacy_templates and not has_variants` → `ValueError("Au moins un template (legacy ou variant) est requis pour un exercice dynamique")`.
  - Validation renforcée des variants lorsque `template_variants` est fourni :
    - `id` non vide,
    - `weight` >= 1,
    - `enonce_template_html` non vide,
    - `solution_template_html` non vide.
- **Backend – modèles Pydantic** (`backend/services/exercise_persistence_service.py`) :
  - Confirmation de la présence de `template_variants: Optional[List[TemplateVariant]]` dans :
    - `ExerciseCreateRequest`,
    - `ExerciseUpdateRequest`,
    - `ExerciseResponse`.
  - Sérialisation de `template_variants` dans MongoDB à la création (`create_exercise`).

### 6. Tests

- **Fichier de tests** : `backend/tests/test_exercise_persistence_models_variants.py`
- **Cas couverts** :
  - Exercice statique sans `enonce_html` / `solution_html` → `ValidationError` (comportement inchangé).
  - Exercice dynamique avec **templates legacy seuls** (sans variants) → OK.
  - Exercice dynamique avec **variants seuls** (`template_variants` non vide, templates legacy vides) → OK.
  - Exercice dynamique **sans legacy et sans variants** → `_validate_exercise_data` lève un `ValueError`.
- **Commande de test recommandée** (dans l’env backend) :
  ```bash
  cd backend
  pytest backend/tests/test_exercise_persistence_models_variants.py
  ```

### 7. Risques & suivi

- **Risques** :
  - Évolution future des endpoints admin (création / mise à jour d’exercices dynamiques) devra respecter ce contrat (OR entre legacy et variants).
  - Nécessité de ne pas modifier `_validate_exercise_data` sans mettre à jour les tests associés.
- **Suivi** :
  - Étape 2 de la SPEC “variants d’énoncés dynamiques” consistera à introduire le moteur de sélection de variant (preview + élève) en s’appuyant sur ce modèle.
  - GM07/GM08 restent non impactés (modèle réservé aux exercices dynamiques).


