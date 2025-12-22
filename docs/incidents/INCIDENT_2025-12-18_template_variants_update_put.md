## INCIDENT – Persistance des `template_variants` en mise à jour (PUT admin)

### 1. Métadonnées
- **ID incident** : `INCIDENT_2025-12-18_template_variants_update_put`
- **Date** : 2025-12-18
- **Environnement** : local (API admin)
- **Gravité** : P2 (perte de config, UX admin)
- **Statut** : résolu

### 2. Symptôme
- En admin, après avoir ajouté des `template_variants` puis cliqué sur “Enregistrer”, la réouverture de l’exercice ne montre plus les variants : l’exercice revient en mode legacy.

### 3. Root cause
- **Fichier** : `backend/services/exercise_persistence_service.py`
- **Méthode** : `ExercisePersistenceService.update_exercise`
- **Cause exacte** : `update_data` ignorait tous les champs dynamiques (`enonce_template_html`, `solution_template_html`, `is_dynamic`, `generator_key`, `template_variants`). Lors d’un PUT, les variants envoyés par l’UI n’étaient jamais stockés en base.

### 4. Correctif appliqué
- **Backend** (`exercise_persistence_service.py`) :
  - `update_exercise` renseigne désormais :
    - `enonce_template_html`, `solution_template_html`
    - `is_dynamic`, `generator_key`
    - `template_variants` (liste de dicts ou `None` si vide)
  - Aucun changement de logique côté élève (GM07/GM08/TESTS_DYN inchangés).

### 5. Tests
- **Unitaire** : `backend/tests/test_exercise_persistence_models_variants.py`
  - Crée un exercice sans variants.
  - Appelle `update_exercise` avec `template_variants=[...]`.
  - Vérifie que l’exercice mis à jour contient bien `template_variants` et les champs dynamiques.
- **Commande** :
  - `cd backend && pytest backend/tests/test_exercise_persistence_models_variants.py::test_update_persists_template_variants`

### 6. Résultat
- Les PUT admin créent/màj correctement `template_variants` ; les GET suivants renvoient ces variants, permettant à l’UI de se réhydrater en mode variants.

### 7. Risques / Suivi
- Si d’autres champs dynamiques sont ajoutés à l’avenir, ils doivent être traités à la fois en création **et** en mise à jour. Respecter la DoD UI/CRUD (Create + Read + Update + Re-open). 
