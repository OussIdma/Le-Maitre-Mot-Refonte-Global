## INCIDENT – Template variants Étape 4 (UI admin & CRUD)

### 1. Métadonnées

- **ID incident** : `INCIDENT_2025-12-18_template_variants_step4_admin_ui`
- **Date de détection** : 2025-12-18
- **Environnement** : local (admin UI, API admin)
- **Gravité** : P3 (évolution fonctionnelle contrôlée)
- **Statut** : résolu (Étape 4 implémentée en local)

### 2. Résumé exécutif

- **Contexte** : après les Étapes 1–3 (modèle, moteur, preview admin, pipeline élève TESTS_DYN), l’admin ne disposait pas encore d’une UI pour créer/éditer des `template_variants` ni d’un flux CRUD complet.
- **Objectif** : permettre à l’admin de gérer des variants d’énoncés/corrections pour les exercices dynamiques, avec un comportement clair :
  - `template_variants` comme source de vérité dès qu’ils sont présents,
  - preview admin en mode Auto (seed) ou Forcé (variant_id),
  - persistance en DB via l’API admin existante,
  - aucun impact sur GM07/GM08 ni sur les pipelines élèves.

### 3. Root cause (fonctionnelle)

- **Avant Étape 4** :
  - `ChapterExercisesAdminPage` ne gérait qu’un seul couple `enonce_template_html` / `solution_template_html` pour les exercices dynamiques.
  - `DynamicPreviewModal` ne connaissait pas les variants ni la notion de `variant_id` / `stable_key`.
  - Les appels `fetch` de création/mise à jour ne transportaient pas `template_variants`, même lorsque le backend les supportait.
- **Conséquence** :
  - Impossible, côté admin, de configurer des variants sans passer par des manipulations manuelles en DB.
  - Preview admin incapable de tester des variants avant sauvegarde.

### 4. Correctifs appliqués – UI & payloads

#### 4.1. UI admin – `ChapterExercisesAdminPage`

- **Fichier** : `frontend/src/components/admin/ChapterExercisesAdminPage.js`

- **État & chargement** :
  - Extension de `formData` avec :
    - `template_variants: []` par défaut.
  - Lors de l’ouverture en édition :
    - `template_variants` initialisé depuis `exercise.template_variants || []`.
  - Ajout d’un état local `activeVariantIndex` pour suivre le variant sélectionné dans l’UI.

- **Bloc “Variants d’énoncés dynamiques”** (dans la section exercice dynamique) :
  - Détection du mode variants :
    - `isVariantMode = formData.is_dynamic && template_variants.length > 0`.
  - Construction de `effectiveVariants` :
    - si `isVariantMode` : `template_variants`,
    - sinon : un variant virtuel unique dérivé des champs legacy (`enonce_template_html` / `solution_template_html`).
  - Actions :
    - **Ajouter** :
      - si aucun variant existant :
        - crée deux variants : `v1` (copie du legacy), `v2` (copie identique) → passage en mode variants.
      - sinon :
        - duplique le dernier variant et lui donne un nouvel `id` (`v{n+1}`) et un label par défaut.
    - **Dupliquer** :
      - duplique le variant actif (id / label adaptés) et le sélectionne.
    - **Supprimer** :
      - supprime le variant actif **uniquement si** plus d’un variant est présent (garde-fou : jamais supprimer le dernier).
  - Édition d’un variant actif :
    - champs éditables :
      - `id` (obligatoire),
      - `label` (optionnel),
      - `weight` (>= 1),
      - `enonce_template_html`,
      - `solution_template_html`.
    - Les textareas de template énoncé/solution sont désormais liés :
      - au variant actif en mode variants,
      - aux champs legacy en mode single.

- **Validation frontend** :
  - Si `is_dynamic` :
    - `generator_key` requis.
    - Si `template_variants` non vide :
      - pour chaque variant :
        - `id` non vide,
        - `weight` entier >= 1,
        - `enonce_template_html` non vide,
        - `solution_template_html` non vide.
      - les erreurs sont regroupées sous `formErrors.template_variants[...]`.
    - Sinon (pas de variants) :
      - on conserve l’ancienne validation sur `enonce_template_html` et `solution_template_html`.

- **Soumission (create/update) – payload** :
  - Avant l’envoi :
    - calcul d’un `payload` dérivé de `formData`.
    - si `is_dynamic` et `template_variants` non vide :
      - on recopie le 1er variant dans les champs legacy pour compat backend :
        - `payload.enonce_template_html = firstVariant.enonce_template_html`,
        - `payload.solution_template_html = firstVariant.solution_template_html`.
  - Envoi du payload via `fetch` vers les routes :
    - `POST /api/admin/chapters/{chapter_code}/exercises`,
    - `PUT /api/admin/chapters/{chapter_code}/exercises/{id}`.

- **Preview dynamique depuis le formulaire** :
  - Appel à `DynamicPreviewModal` enrichi avec :
    - `templateVariants={formData.is_dynamic ? formData.template_variants : null}`,
    - `stableKey={editingExercise ? \`${chapterCode}:${editingExercise.id}\` : null}`.

#### 4.2. Preview admin – `DynamicPreviewModal`

- **Fichier** : `frontend/src/components/admin/DynamicPreviewModal.js`

- **Props étendues** :
  - Ajout de :
    - `templateVariants` (liste de variants pour la preview),
    - `stableKey` (clé stable métier, ex. `"6e_G07:3"`).

- **Contrôles de variante** :
  - Nouveaux états :
    - `variantMode` : `"auto"` ou `"fixed"`,
    - `selectedVariantId` : identifiant du variant forcé.
  - UI :
    - Select “Variant” :
      - **Auto (seed)** : `variantMode="auto"`,
      - **Forcé** : `variantMode="fixed"` + dropdown des `id` disponibles dans `templateVariants`.

- **Payload preview** :
  - Construction de `payload` de base (inchangé) :
    - `generator_key`, `enonce_template_html`, `solution_template_html`, `difficulty`, `seed`, `svg_mode`.
  - Si `templateVariants` non vide :
    - `payload.template_variants = templateVariants`,
    - `payload.stable_key = stableKey` (si fourni),
    - si `variantMode === "fixed"` et qu’un id effectif est disponible :
      - `payload.variant_id = selectedVariantId || templateVariants[0].id`.

- **Affichage résultat** :
  - En plus de la seed utilisée :
    - Si le backend renvoie `variant_id_used`, affichage de `Variant: {variant_id_used}` à côté de la seed.

#### 4.3. Backend – enrichissement de la preview (rappel)

- **Fichier** : `backend/routes/generators_routes.py`

- **Modèle `DynamicPreviewResponse`** :
  - Ajout de `variant_id_used: Optional[str] = None`.

- **Logique de preview** :
  - Après sélection d’un variant (`choose_template_variant`) :
    - stockage de `chosen_variant_id = chosen.id`,
    - retour dans la réponse JSON via `variant_id_used=chosen_variant_id`.
  - Comportement en cas d’erreur `INVALID_TEMPLATE_VARIANT` inchangé (HTTP 400 JSON structuré).

### 5. Tests & commandes

- **Tests manuels admin suggérés** :
  - Créer un exercice dynamique avec 2 variants (weights différents).
  - Vérifier :
    - en mode **Auto** :
      - même seed → même variant en preview,
      - seeds multiples → répartition conforme aux weights.
    - en mode **Forcé** avec un `variant_id` donné :
      - toujours le même variant choisi, quelle que soit la seed.
  - Sauvegarder puis rouvrir l’exercice :
    - les `template_variants` sont bien persistés,
    - l’édition ultérieure reflète correctement les variants.

- **Commandes techniques recommandées** :
  - Lancer le frontend :
    ```bash
    cd frontend
    npm install   # si nécessaire
    npm start
    ```
  - Tester la preview via l’API directement (mode éphémère) :
    ```bash
    curl -s -X POST "http://localhost:8000/api/admin/exercises/preview-dynamic" \
      -H "Content-Type: application/json" \
      -d '{
        "generator_key": "THALES_V1",
        "difficulty": "moyen",
        "seed": 12345,
        "svg_mode": "AUTO",
        "stable_key": "6e_TESTS_DYN:1",
        "template_variants": [
          {
            "id": "v1",
            "enonce_template_html": "<p>Variant 1: {{cote_initial}}</p>",
            "solution_template_html": "<p>Sol 1: {{cote_final}}</p>",
            "weight": 1
          },
          {
            "id": "v2",
            "enonce_template_html": "<p>Variant 2: {{cote_initial}}</p>",
            "solution_template_html": "<p>Sol 2: {{cote_final}}</p>",
            "weight": 10
          }
        ]
      }' | jq .
    ```
  - Cas d’erreur `INVALID_TEMPLATE_VARIANT` (variant_id inconnu) :
    ```bash
    curl -s -X POST "http://localhost:8000/api/admin/exercises/preview-dynamic" \
      -H "Content-Type: application/json" \
      -d '{
        "generator_key": "THALES_V1",
        "difficulty": "moyen",
        "seed": 12345,
        "svg_mode": "AUTO",
        "stable_key": "6e_TESTS_DYN:1",
        "variant_id": "inconnu",
        "template_variants": [
          {
            "id": "v1",
            "enonce_template_html": "<p>Variant 1: {{cote_initial}}</p>",
            "solution_template_html": "<p>Sol 1: {{cote_final}}</p>",
            "weight": 1
          }
        ]
      }' | jq .
    ```

### 6. Risques & suivi

- **Risques** :
  - Mauvaise configuration des `template_variants` (id dupliqué, poids 0, placeholders invalides) conduira à des erreurs de validation (frontend, backend) ou à des 422 `UNRESOLVED_PLACEHOLDERS` côté pipeline élève.
  - Toute évolution de la structure des templates devra rester alignée entre :
    - UI admin (`ChapterExercisesAdminPage`),
    - preview admin (`DynamicPreviewModal`),
    - backend (modèles Pydantic + `tests_dyn_handler`).
- **Suivi** :
  - Étendre progressivement cette UI de variants à d’autres chapitres dynamiques pilotés par `ExercisePersistenceService`.
  - Ajouter ultérieurement des tests E2E (frontend + backend) pour automatiser la vérification du comportement Auto/Forcé des variants.






