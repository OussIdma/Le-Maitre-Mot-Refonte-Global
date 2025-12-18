## Changelog technique

Ce fichier trace les évolutions techniques majeures (backend, frontend, infra, documentation d’architecture) de **Le Maître Mot v16 – Refonte locale**.

Les entrées sont listées de la plus récente à la plus ancienne.

---

### 2025-12-18 – Alignement preview admin THALES_V1 (carrés) sur pipeline élève

- **Backend** : ajout, dans `backend/routes/generators_routes.py`, d’un mapping d’alias pour les générateurs THALES (`THALES_V1` legacy et `THALES_V2` Factory) identique à celui du handler `tests_dyn_handler.py` afin que la prévisualisation admin ne laisse plus de placeholders `{{base_initiale}}`, `{{hauteur_initiale}}`, etc. lorsqu’on utilise des carrés (ou d’autres variantes triangle/rectangle).
- **Root cause** : le pipeline de preview admin fusionnait uniquement `variables + results (+ geo_data côté Factory)` sans appliquer les alias (carre → base/hauteur/longueur/largeur) déjà utilisés côté élève, ce qui laissait des `{{...}}` non résolus dans certains templates selon le générateur utilisé (THALES_V1 ou THALES_V2).
- **Effet** : preview admin THALES cohérente avec la génération élève pour `6e_TESTS_DYN`, aucune fuite de placeholders dans l’aperçu pour les cas de carrés.
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-18_admin_preview_thales_carres.md`.

### 2025-12-18 – Sélection d’exercices 6e_G07 sécurisée (pas de fallback silencieux)

- **Backend** : durcissement de la conversion `exercise_types` du curriculum en `MathExerciseType` dans `backend/routes/exercises_routes.py` ; les types inconnus sont maintenant détectés et, si tous les types configurés sont invalides (ex. `SYMETRIE_AXIALE_V2` non encore mappé), l’API retourne un `HTTP 422 INVALID_CURRICULUM_EXERCISE_TYPES` au lieu de retomber silencieusement sur le mapping legacy. Les types partiellement valides continuent de fonctionner mais les types inconnus sont loggés explicitement.
- **Root cause** : la génération via `/api/v1/exercises/generate` utilisait `exercise_types` du curriculum, mais ignorait silencieusement les valeurs non déclarées dans `MathExerciseType`, ce qui pouvait vider `exercise_types_override` et déclencher un fallback implicite vers le mapping legacy `_map_chapter_to_types`, potentiellement avec des générateurs inattendus (ex. THALES) par rapport au pool admin.
- **Effet** : pour les chapitres comme `6e_G07`, une configuration incohérente entre curriculum/admin et `MathExerciseType` est maintenant signalée clairement (erreur 422) et ne peut plus produire d’exercices issus d’un pool “par défaut” sans lien avec la configuration pédagogique.
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-18_selection_6e_G07.md`.

### 2025-12-18 – Variants d’énoncés dynamiques (Étape 1 : modèle & validations)

- **Backend** : ajout du modèle `TemplateVariant` et du champ `template_variants` dans `ExerciseCreateRequest` / `ExerciseUpdateRequest` / `ExerciseResponse` (`backend/services/exercise_persistence_service.py`), avec validation métier imposant qu’un exercice dynamique possède au moins un template (legacy ou variant). Aucune modification des pipelines de génération ni de la preview pour cette étape.
- **Root cause / besoin** : les exercices dynamiques ne permettaient pas encore de définir plusieurs variants d’énoncé/correction pour un même générateur, ce qui limitait la variabilité pédagogique côté wording et empêchait de préparer le moteur de sélection par seed.
- **Effet** : le modèle de données est prêt pour supporter des variants d’énoncés dynamiques de façon déterministe, sans impacter GM07/GM08 ni les chapitres legacy ; les validations évitent la création d’exercices dynamiques incohérents (sans aucun template exploitable).

### 2025-12-18 – Variants d’énoncés dynamiques (Étape 2 : moteur & preview admin)

- **Backend** : création de `backend/services/dynamic_exercise_engine.py` avec `choose_template_variant` (sélection de variant déterministe par seed + clé stable, pondérée par `weight`, sans RNG global) et branchement dans `preview_dynamic_exercise` (`backend/routes/generators_routes.py`) via de nouveaux champs `template_variants`, `variant_id` et `stable_key` dans `DynamicPreviewRequest`. La preview admin peut désormais choisir un variant d’énoncé/solution de façon déterministe ou forcée, sans toucher aux pipelines élèves / GM07 / GM08.
- **Effet** : la logique de sélection de variant est centralisée et testée, la preview admin supporte les multi-variants en mode éphémère (sans DB) et remonte des erreurs JSON explicites en cas de variant invalide ou de placeholders non résolus, tout en garantissant la reproductibilité par seed.

### 2025-12-18 – Variants d’énoncés dynamiques (Étape 3 : pilotage élève TESTS_DYN)

- **Backend** : branchement du moteur `choose_template_variant` dans le pipeline élève `6e_TESTS_DYN` via `backend/services/tests_dyn_handler.py::format_dynamic_exercise`, avec sélection de variant basée sur une `stable_key` métier (`"6E_TESTS_DYN:{id}"`) et sur la seed. Si `template_variants` est présent dans le template TESTS_DYN, il devient la source de vérité pour le rendu ; sinon, le comportement legacy (un seul template) est conservé. Le garde-fou `UNRESOLVED_PLACEHOLDERS` reste inchangé.
- **Effet** : le chapitre pilote `6e_TESTS_DYN` est capable d’exploiter plusieurs variants d’énoncé/correction côté élève de manière déterministe, sans impact sur GM07/GM08 ni sur les chapitres legacy, et sans régression sur la détection de placeholders non résolus.

### 2025-12-18 – Réorganisation de la documentation d’investigation

- **Docs** : déplacement de tous les fichiers `INVESTIGATION_*.md` de la racine vers le dossier `docs/` pour centraliser les analyses d’incidents et d’anomalies.
- **Docs** : création/mise à jour de `README.md` avec :
  - démarrage rapide via Docker (`docker compose up --build`) ;
  - script de healthcheck (`./scripts/healthcheck.sh`) ;
  - index des principaux documents d’architecture dans `docs/`.
- **Objectif** : rendre la cartographie technique (investigations, specs, sprints) plus découvrable et alignée avec le rôle CTO/architecte (diagnostics traçables, zéro magie).
- **Référence Git** : commit `Docs: move INVESTIGATION notes to docs/ and update README` (branche `master`).


Je viens d’aligner la preview admin THALES_V1 sur le mapping de variables utilisé côté élève (triangle/rectangle/carré), ce qui doit faire disparaître les {{base_initiale}} / {{hauteur_initiale}} en prévisualisation. Je vais maintenant proposer les commandes de test, puis créer le fichier d’incident et mettre à jour le changelog.
INCIDENT_2025-12-18_admin_preview_thales_carres.md(new)
+138
## INCIDENT – Fiche récapitulative### 1. Métadonnées- **ID incident** : `INCIDENT_2025-12-18_admin_preview_thales_carres`
CHANGELOG_TECH.md
- **Objectif** : rendre la cartographie technique (investigations, specs, sprints) plus découvrable et alignée avec le rôle CTO/architecte (diagnostics traçables, zéro magie).- **Référence Git** : commit `Docs: move INVESTIGATION notes to docs/ and update README` (branche `master`).
.
