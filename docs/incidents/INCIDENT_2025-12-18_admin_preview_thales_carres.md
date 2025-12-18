## INCIDENT – Fiche récapitulative

### 1. Métadonnées

- **ID incident** : `INCIDENT_2025-12-18_admin_preview_thales_carres`
- **Date de détection** : 2025-12-18
- **Période d’impact** : 2025-12-18 (env. local admin)
- **Environnement** : local (admin / preview dynamique)
- **Gravité** : P2 (bug d’aperçu admin, pas d’impact élève)
- **Statut** : résolu
- **Auteur de la fiche** : Emergent AI (agent), validation Oussama

### 2. Résumé exécutif

- **Contexte** : Dans l’admin, la prévisualisation dynamique d’un exercice `6e_TESTS_DYN` basé sur `THALES_V1` (figure de type carré) affiche des placeholders `{{base_initiale}}` / `{{hauteur_initiale}}` non résolus.
+- **Symptôme visible** : Bandeau “Variables non reconnues” + énoncé contenant littéralement `{{base_initiale}}` et `{{hauteur_initiale}}`.
- **Impact utilisateur** : L’admin voit des gabarits non rendus pour certains cas (carré), ce qui dégrade la confiance dans le template, mais n’impacte pas les élèves.
- **Cause technique (résumée)** : Le pipeline de preview admin n’appliquait pas les mappings d’alias de variables (carre → base/hauteur/longueur/largeur) déjà présents dans le pipeline élève `TESTS_DYN`.
- **État actuel** : Alignement des mappings THALES_V1 entre pipeline preview admin et pipeline élève ; preview admin ne montre plus de `{{...}}` pour ce cas.

### 3. Contexte détaillé

- **Fonctionnalité concernée** : Prévisualisation dynamique dans l’admin pour les exercices 6e, famille `AGRANDISSEMENT_REDUCTION`, générateur `THALES_V1`.
- **Endpoints / pages impactés** :
  - Frontend admin : `/admin/curriculum/6e_TESTS_DYN/exercises` (modal “Prévisualisation dynamique”).
  - Backend : `POST /api/admin/exercises/preview-dynamic`.
- **Version / build backend** :
  - `GET /api/debug/build` → build du 2025-12-18 (hash incluant le commit de fix).
- **Hypothèses initiales** :
  - Mismatch entre gabarit (base/hauteur) et générateur (cote).
  - Divergence entre pipeline élève (TESTS_DYN) et pipeline preview admin.

### 4. Symptômes & impact

- **Symptômes observés** :
  - En admin, pour un exercice THALES_V1 “carré rectangle”, la prévisualisation affiche :
    - `Variables non reconnues : {{base_initiale}}, {{base_finale}}, {{hauteur_initiale}}, {{hauteur_finale}}`.
    - L’énoncé contient encore les `{{...}}` dans le texte.
- **Impact utilisateur** :
  - L’admin ne peut pas valider visuellement son template : le rendu ne reflète pas les valeurs calculées.
  - Pas d’impact direct sur la génération élève (pipeline différent déjà protégé).
- **Scope** :
  - Limité au **preview admin** pour THALES_V1 lorsque `figure_type = "carre"` (et, plus généralement, aux cas nécessitant des alias).

### 5. Chronologie

- 2025-12-18 – Constat par Oussama de placeholders visibles en preview admin pour un carré THALES_V1.
- 2025-12-18 – Analyse du code côté `tests_dyn_handler` (élève) vs `preview-dynamic` (admin).
- 2025-12-18 – Identification de l’absence de mapping d’alias dans `preview-dynamic`.
- 2025-12-18 – Ajout du mapping THALES (triangle/rectangle/carré) dans `backend/routes/generators_routes.py`.

### 6. Diagnostic & cause racine

- **Fichiers / modules impliqués** :
  - Backend :
    - `backend/services/tests_dyn_handler.py`
    - `backend/routes/generators_routes.py`
    - `backend/generators/thales_generator.py`
- **Comportement attendu** :
  - Pour un carré THALES_V1, même si le générateur ne produit que `cote_initial` / `cote_final`, les templates peuvent utiliser `base_initiale`, `hauteur_initiale`, `longueur_initiale`, etc.  
  - Le pipeline doit ajouter **des alias** pour couvrir ces variantes, côté élève **et** côté admin preview.
- **Comportement observé** :
  - Côté élève (TESTS_DYN) : `format_dynamic_exercise` applique déjà des mappings :
    - carre → base/hauteur/longueur/largeur via `cote_initial` / `cote_final`.
  - Côté admin : `preview_dynamic_exercise` se contente de fusionner `variables` + `results` sans ces mappings, puis rend les templates ; les placeholders restent donc vides.
- **Cause racine (prouvée)** :
  - Le code de `preview_dynamic_exercise` ne réutilisait pas la logique d’alias définie dans `tests_dyn_handler.py` pour THALES_V1 :
    - pas de normalisation de `figure_type`,
    - pas de mapping `carre → base/hauteur/longueur/largeur`.

### 7. Correctifs appliqués

- **Backend** :
  - `backend/routes/generators_routes.py` :
    - Ajout de `_normalize_figure_type` (équivalent à la version du handler TESTS_DYN).
    - Ajout de `_apply_thales_alias_mappings(all_vars)` qui :
      - normalise `figure_type` ;
      - pour `triangle` : mappe base/hauteur vers longueur/largeur ;
      - pour `rectangle` : mappe longueur/largeur vers base/hauteur ;
      - pour `carre` : mappe `cote_(initial|final)` vers toutes les variantes (`base_*`, `hauteur_*`, `longueur_*`, `largeur_*`).
    - Application de ce mapping dans `preview_dynamic_exercise` :
      - **branche Factory** : pour tout générateur THALES (ex. `THALES_V2`) via `factory_generate`, juste après la fusion `variables + results + geo_data` ;
      - **branche legacy** : pour le générateur `THALES_V1` historique, après `all_vars = {**variables, **results}`.
- **Frontend** :
  - Aucun changement requis : le frontend se contente d’afficher les `errors[]` renvoyés par l’API et l’HTML rendu.
- **Infra / config** :
  - Aucun changement.

- **Commits** :
  - Commit backend (local) : `Fix: align admin preview THALES_V1 variable mapping (carres)` (hash correspondant à la modif dans `generators_routes.py`).

### 8. Validation & tests

- **Tests manuels recommandés** :
  - Admin UI :
    1. Aller sur `/admin/curriculum/6e_TESTS_DYN/exercises`.
    2. Ouvrir l’exercice THALES_V1 concerné (carré).
    3. Cliquer sur “Prévisualisation dynamique”.
    4. Vérifier :
       - l’énoncé ne contient plus de `{{base_initiale}}` / `{{hauteur_initiale}}` ;
       - la zone “Variables non reconnues” est vide pour ce cas ou ne contient pas ces clés.
- **Tests API (curl)** :
  - Preview direct :
    ```bash
    curl -s -X POST "http://localhost:8000/api/admin/exercises/preview-dynamic" \
      -H "Content-Type: application/json" \
      -d '{
        "generator_key": "THALES_V1",
        "enonce_template_html": "<p>Base {{base_initiale}} cm, hauteur {{hauteur_initiale}} cm.</p>",
        "solution_template_html": "<p>Base finale {{base_finale}} cm, hauteur finale {{hauteur_finale}} cm.</p>",
        "difficulty": "difficile",
        "seed": 51846,
        "svg_mode": "AUTO"
      }' | jq .
    ```
    Attendu :
    - `success: true` (ou `errors` ne contenant pas de variables manquantes liées à ces placeholders).
    - `enonce_html` et `solution_html` sans `{{...}}`.

### 9. Risques résiduels & actions de suivi

- **Risques résiduels** :
  - D’autres générateurs legacy utilisant des schémas similaires (triangle/rectangle/carré) peuvent nécessiter des mappings analogues.
  - La logique d’alias est dupliquée entre `tests_dyn_handler.py` et `generators_routes.py` (risque de divergence future).
- **Actions recommandées** :
  - Extraire à terme la logique d’alias dans un module utilitaire partagé (ex. `backend/services/thales_aliases.py`) pour éviter la duplication.
  - Ajouter un test automatisé de non-présence de `{{...}}` dans les préviews admin pour THALES_V1 (cas rectangle/triangle/carre).
- **Documentation** :
  - Mentionner dans `docs/CHANGELOG_TECH.md` que la preview admin THALES_V1 réutilise désormais les mêmes mappings que le pipeline élève.

### 10. Annexes & références

- **Code clé** :
  - `backend/routes/generators_routes.py` : fonctions `_normalize_figure_type`, `_apply_thales_alias_mappings`, et application dans `preview_dynamic_exercise`.
- **Liens internes** :
  - `docs/INVESTIGATION_PLACEHOLDERS_TESTS_DYN.md` – historique des placeholders côté élève.


