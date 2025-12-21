## Changelog technique

Ce fichier trace les évolutions techniques majeures (backend, frontend, infra, documentation d'architecture) de **Le Maître Mot v16 – Refonte locale**.

Les entrées sont listées de la plus récente à la plus ancienne.

---

### 2025-12-21 – Fix P0 : "CHAPITRE NON MAPPÉ" pour pipeline MIXED sans exercise_types

- **Backend** : blocage du fallback statique pour les chapitres avec `pipeline=MIXED` et `exercise_types=[]`. Retour d'une erreur explicite `MIXED_PIPELINE_NO_DYNAMIC_EXERCISES` à la place d'un fallback silencieux vers le mapping legacy.
- **Root cause / besoin** : le chapitre `6e_AA_TEST` (pipeline MIXED, `exercise_types=[]`) générait l'erreur "CHAPITRE NON MAPPÉ" lors de la génération de plusieurs exercices avec difficulté "difficile". Le pipeline MIXED capturait les exceptions `randrange` et faisait un fallback statique vers `_map_chapter_to_types()`, mais "AA TEST" n'était pas mappé dans le legacy (libellé utilisé comme clé).
- **Effet** : plus de fallback silencieux pour les chapitres MIXED sans `exercise_types`. Erreur explicite si aucun exercice dynamique disponible, respectant le principe "pas de fallback silencieux". La génération de plusieurs exercices fonctionne maintenant correctement.
- **Tests** : `curl` avec `code_officiel=6e_AA_TEST` et `difficulte=difficile` → fonctionne pour 1 et plusieurs exercices. Si aucun exercice dynamique disponible → erreur explicite (pas de "CHAPITRE NON MAPPÉ").
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-21_chapitre_non_mappe_aa_test.md`.

---

### 2025-12-21 – Ajout des paramètres de générateur dans l'admin UI

- **Frontend** : ajout du composant `GeneratorParamsForm` dans le formulaire de création/édition d'exercices dynamiques (`ChapterExercisesAdminPage.js`). Le formulaire permet maintenant de configurer les paramètres du générateur (ex: `allow_negative`, `max_denominator`, `show_svg`, etc.) directement depuis l'interface admin, avec support des presets pédagogiques.
- **Documentation** : mise à jour de `docs/PROCEDURE_AJOUT_TEMPLATE_DYNAMIQUE.md` pour documenter l'utilisation des paramètres du générateur dans l'admin UI.
- **Root cause / besoin** : les générateurs dynamiques (comme `SIMPLIFICATION_FRACTIONS_V1`) définissent des paramètres configurables via `get_schema()`, mais ces paramètres n'étaient pas exposés dans l'interface admin, rendant impossible leur modification sans intervention directe en DB.
- **Effet** : les administrateurs peuvent maintenant configurer les paramètres du générateur lors de la création d'un exercice dynamique, permettant une personnalisation fine du comportement de génération (limites, options visuelles, etc.). Les paramètres sont stockés dans le champ `variables` de l'exercice en DB.
- **Tests** : interface testée avec `SIMPLIFICATION_FRACTIONS_V1`, tous les paramètres sont correctement affichés et sauvegardés.
- **Référence** : `frontend/src/components/admin/ChapterExercisesAdminPage.js`, `docs/PROCEDURE_AJOUT_TEMPLATE_DYNAMIQUE.md`.

---

### 2025-12-21 – Procédure complète d'ajout de template dynamique

- **Documentation** : création de `docs/PROCEDURE_AJOUT_TEMPLATE_DYNAMIQUE.md`, procédure exhaustive pour créer un exercice dynamique sans bug, utilisable par un agent IA. La procédure couvre : identification du générateur, extraction des templates de référence, validation des placeholders, tests de génération, et dépannage.
- **Script de validation** : création de `backend/scripts/validate_template_placeholders.py`, script Python pour valider automatiquement que tous les placeholders des templates sont générés par le générateur correspondant. Le script peut valider depuis des templates fournis en ligne de commande ou depuis un exercice en DB.
- **Root cause / besoin** : éviter les erreurs `UNRESOLVED_PLACEHOLDERS` lors de la création d'exercices dynamiques en fournissant une procédure claire et des outils de validation automatique.
- **Effet** : les futurs exercices dynamiques peuvent être créés en suivant une procédure validée, avec validation automatique des placeholders avant sauvegarde, réduisant drastiquement les risques d'erreur.
- **Tests** : procédure testée avec `SIMPLIFICATION_FRACTIONS_V1`, script de validation testé avec succès sur exercices en DB et templates fournis.
- **Référence** : `docs/PROCEDURE_AJOUT_TEMPLATE_DYNAMIQUE.md`, `backend/scripts/validate_template_placeholders.py`.

---

### 2025-12-21 – Fix templates incorrects pour SIMPLIFICATION_FRACTIONS_V1

- **Backend** : création du script de migration `backend/migrations/005_fix_simplification_fractions_templates.py` pour corriger automatiquement les templates des exercices dynamiques avec `generator_key=SIMPLIFICATION_FRACTIONS_V1` qui utilisaient des placeholders incorrects (SYMETRIE_AXIALE au lieu de SIMPLIFICATION_FRACTIONS_V1).
- **Root cause / besoin** : les exercices du chapitre `6e_AA_TEST` avec `SIMPLIFICATION_FRACTIONS_V1` avaient des templates contenant des placeholders de SYMETRIE_AXIALE (`axe_equation`, `axe_label`, etc.) qui ne sont pas générés par le générateur, provoquant une erreur `UNRESOLVED_PLACEHOLDERS` → fallback pipeline statique → "CHAPITRE NON MAPPÉ".
- **Effet** : les templates sont corrigés avec les placeholders corrects (`{{fraction}}`, `{{step1}}`, `{{step2}}`, `{{step3}}`, `{{fraction_reduite}}`, etc.), la génération fonctionne correctement, le pipeline MIXED génère des exercices dynamiques sans erreur.
- **Tests** : `curl -X POST http://localhost:8000/api/v1/exercises/generate -d '{"code_officiel": "6e_AA_TEST", "difficulte": "difficile", "offer": "free", "seed": 42}'` → exercice généré avec succès, logs montrent `[PIPELINE] ✅ Exercice dynamique généré (MIXED, priorité dynamique)`.
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-21_templates_simplification_fractions.md`.

---

### 2025-12-19 – Admin curriculum: pipeline désormais persistant

- **Backend** : le champ `pipeline` est maintenant exposé et accepté en édition admin (`AdminChapterResponse` inclut `pipeline` ; `ChapterUpdateRequest` accepte `pipeline`). La valeur saisie dans le formulaire n’est plus ignorée.
- **Root cause / besoin** : le modèle d’update n’acceptait pas `pipeline` et les réponses ne le renvoyaient pas, d’où un fallback silencieux à `SPEC` et impossibilité de configurer un chapitre dynamique (ex: `6e_AA_TEST`).
- **Effet** : l’admin peut lire/écrire le pipeline explicite ; le frontend se pré-remplit avec la vraie valeur. Rappel : pipeline `TEMPLATE` exige au moins un exercice dynamique en DB, sinon validation bloquante.
- **Tests** : `curl -s http://localhost:8000/api/admin/curriculum/6e/6e_AA_TEST | jq '{code_officiel,pipeline,generateurs}'` → le champ `pipeline` est présent.
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-19_pipeline_admin_not_persisted.md`.

---

### 2025-12-19 – Chapitres 6e_AA_TEST visibles dans le catalogue

- **Backend** : ajout des chapitres `6e_AA_TEST` (SPEC, prod) et `6e_AA_TEST_STAT` (SPEC, beta, exercise_types=["AIRE_TRIANGLE"]) dans `backend/curriculum/curriculum_6e.json` et rattachement au macro group « Tests Dynamiques » pour qu’ils soient servis par `get_catalog()`.
- **Root cause / besoin** : les chapitres existaient en Mongo (`curriculum_chapters`) mais n’avaient jamais été synchronisés dans le JSON embarqué (backend non monté en volume). `get_catalog()` se base sur le JSON pour lister les chapitres, d’où leur absence dans l’UI `/generate`.
- **Effet** : les deux chapitres apparaissent désormais dans le catalogue (mode officiel et simple via le macro group), prêts à être sélectionnés ; note : `6e_AA_TEST` reste sans générateur pour l’instant.
- **Tests** : `curl -s http://localhost:8000/api/v1/curriculum/6e/catalog | jq '.domains[].chapters[] | select(.code_officiel|test(\"6e_AA_TEST\"))'` → retourne les deux chapitres.
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-19_catalog_missing_6e_AA_TEST.md`.

---

### 2025-12-19 – Fix 500 catalogue (bool() sur objet DB)

- **Backend** : `backend/curriculum/loader.py::get_catalog()` n’évalue plus `if db:` (bool interdit sur `pymongo.database.Database`) mais `if db is not None`, supprimant l’exception `NotImplementedError` qui faisait tomber le catalogue dès l’appel.
- **Root cause / besoin** : le test de vérité sur l’objet DB, introduit pour l’enrichissement du catalogue depuis Mongo, lève systématiquement `NotImplementedError`, provoquant un 500 sur `/api/v1/curriculum/6e/catalog` et le message frontend « Impossible de charger le catalogue ».
- **Effet** : le catalogue se charge à nouveau (200 OK), le frontend `/generate` récupère les chapitres/macro_groups sans erreur ; enrichissement DB conservé.
- **Tests** : `docker compose ps` (backend/mongo up & healthy), `curl -s -o /tmp/catalog.json -w "%{http_code}" http://localhost:8000/api/v1/curriculum/6e/catalog` → `200`.
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-19_catalogue_500_bool_db.md`.

---

### 2025-12-18 – Fix générateurs dynamiques manquants dans l'admin

- **Backend** : correction de `backend/services/curriculum_persistence_service.py::get_available_generators()` pour inclure les générateurs dynamiques en plus des générateurs statiques. La fonction récupère maintenant tous les générateurs depuis `GeneratorFactory` et extrait leurs `exercise_types` via `_get_exercise_type_from_generator()`, puis fusionne avec les générateurs statiques (`MathExerciseType`) pour retourner une liste complète. Ajout de logs explicites pour tracer l'extraction des générateurs dynamiques.
- **Root cause / besoin** : lors de la création/modification d'un chapitre dynamique dans l'admin, la liste des générateurs proposés ne contenait que des générateurs statiques (ex: "TRIANGLE_QUELCONQUE", "RECTANGLE"), rendant impossible la sélection d'un générateur dynamique (comme "AGRANDISSEMENT_REDUCTION" utilisé pour "Tests Dynamiques"). Le chapitre restait "indisponible" car il n'avait pas de générateur dans le curriculum.
- **Effet** : les générateurs dynamiques sont maintenant disponibles dans l'admin, l'admin peut créer/modifier un chapitre dynamique avec un générateur dynamique, le chapitre devient disponible dans le catalogue, plus besoin de modifier manuellement le curriculum_6e.json pour ajouter un générateur dynamique.
- **Tests** : tests manuels documentés (vérification que les générateurs dynamiques sont disponibles, création d'un chapitre dynamique avec un générateur dynamique).
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-18_generateurs_dynamiques_manquants_admin.md`.

---

### 2025-12-18 – Fix chapitre "indisponible" et mauvais pipeline de génération

- **Backend** : correction de `backend/curriculum/loader.py::get_catalog()` pour enrichir le catalogue depuis la collection `exercises` en plus du curriculum. Le catalogue vérifie maintenant si des exercices existent en DB pour chaque chapitre et enrichit les `generators` avec les `exercise_types` extraits depuis la DB. Modification de `backend/routes/exercises_routes.py::generate_exercise()` pour vérifier les exercices dynamiques en DB **avant** de passer au pipeline statique. Si des exercices dynamiques existent, le pipeline dynamique (`format_dynamic_exercise` depuis la collection `exercises`) est utilisé automatiquement au lieu du pipeline statique (`MathGenerationService`). Ajout de fonctions utilitaires dans `backend/services/curriculum_sync_service.py` : `has_exercises_in_db()` et `get_exercise_types_from_db()`. Ajout de logs explicites `[CATALOG]` et `[GENERATE]` pour tracer la décision (curriculum vs exercises, statique vs dynamique).
- **Root cause / besoin** : les chapitres créés avec des exercices dynamiques en DB apparaissaient "indisponibles" dans le générateur car le catalogue utilisait uniquement `curriculum.exercise_types` (source de vérité incomplète). Si on forçait un générateur dans le curriculum, la génération utilisait le mauvais pipeline (statique au lieu de dynamique) car la route `/generate` ne vérifiait pas les exercices dynamiques en DB avant de passer au pipeline statique.
- **Effet** : chapitres avec exercices dynamiques en DB deviennent automatiquement disponibles dans le catalogue (plus besoin de forcer un générateur dans le curriculum), pipeline dynamique utilisé automatiquement si exercices dynamiques existent en DB (plus de confusion entre pipeline statique et dynamique), source de vérité enrichie : curriculum (source principale) + DB (enrichissement), logs explicites pour le debugging.
- **Tests** : tests manuels documentés (catalogue enrichi depuis DB, pipeline dynamique utilisé automatiquement, pipeline statique pour chapitres sans exercices dynamiques).
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-18_chapitre_indisponible_pipeline_incorrect.md`.

---

### 2025-12-18 – Correction extraction exercise_type depuis generator_key (chapitres dynamiques indisponibles)

- **Backend** : amélioration de `backend/services/curriculum_sync_service.py` pour extraire automatiquement l'`exercise_type` depuis les métadonnées du générateur (`GeneratorMeta.exercise_type`) au lieu de se fier uniquement au mapping statique. Nouvelle fonction `_get_exercise_type_from_generator()` qui essaie d'abord via `GeneratorFactory` (métadonnées), puis fallback sur le mapping statique, puis dernier fallback sur le `generator_key` normalisé. Amélioration du logging (INFO/ERROR/DEBUG) pour diagnostiquer les problèmes d'extraction. Ajout d'un endpoint `POST /api/admin/chapters/{chapter_code}/sync-curriculum` pour forcer la re-synchronisation manuelle d'un chapitre "indisponible".
- **Root cause / besoin** : les chapitres créés avec uniquement des exercices dynamiques n'étaient pas sélectionnables dans le générateur (badge "indisponible") car l'extraction de l'`exercise_type` depuis le `generator_key` ne fonctionnait pas correctement. Le mapping statique `GENERATOR_TO_EXERCISE_TYPE` était incomplet et ne couvrait pas tous les générateurs, et le service n'utilisait pas les métadonnées disponibles dans `GeneratorMeta.exercise_type`.
- **Effet** : chapitres dynamiques sélectionnables dès la création d'un exercice (extraction correcte depuis métadonnées), plus besoin d'ajouter un exercice statique pour rendre le chapitre sélectionnable, fonctionne pour tous les générateurs Factory (métadonnées) et legacy (mapping statique), endpoint de synchronisation manuelle pour corriger les chapitres "indisponibles" existants.
- **Tests** : tests manuels documentés (création exercice dynamique → vérification logs → vérification curriculum → vérification catalogue → vérification frontend).
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-18_auto_sync_exercise_type_extraction.md`.

---

### 2025-12-18 – Auto-synchronisation Curriculum ⇄ Exercises (suppression script manuel)

- **Backend** : création du service `backend/services/curriculum_sync_service.py` pour synchroniser automatiquement les chapitres depuis la collection `exercises` vers le référentiel curriculum (`chapters`). Intégration de hooks automatiques dans `create_exercise()` et `update_exercise()` (`backend/routes/admin_exercises_routes.py`) pour appeler la synchronisation après chaque création/mise à jour d'exercice. Extraction automatique des `exercise_types` depuis `generator_key` (dynamique) et `exercise_type` (statique), avec mapping `generator_key` → `exercise_type` (ex: `SYMETRIE_AXIALE_V2` → `SYMETRIE_AXIALE`). Mise à jour additive (fusion des `exercise_types`, ne supprime pas l'existant), création idempotente, gestion d'erreur non-bloquante (log warning si sync échoue, exercice créé quand même).
- **Root cause / besoin** : les chapitres créés via l'admin (collection `exercises`) n'apparaissaient pas automatiquement dans le référentiel curriculum (`chapters`), nécessitant l'exécution manuelle du script `sync_chapter_from_exercises.py` après chaque création/modification. Risque d'oubli → chapitres "indisponibles" dans le générateur.
- **Effet** : plus jamais de chapitre "indisponible" (synchronisation automatique transparente), suppression du script manuel (obsolète), amélioration UX admin (zéro étape manuelle supplémentaire), compatible statique + dynamique.
- **Tests** : création de `backend/tests/test_curriculum_sync_service.py` (6 scénarios : extraction dynamique/statique/mixte, création, mise à jour additive, pas de changement si identique).
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-18_auto_sync_curriculum_exercises.md`.

---

### 2025-12-18 – Amélioration protocole : Infrastructure Health Check (prévention faux positifs)

- **Protocole** : ajout d'une section "INFRASTRUCTURE HEALTH CHECK" obligatoire dans `.cursorrules` (Phase 2) pour vérifier l'état Docker/Mongo avant toute validation backend. Règles strictes : jamais valider un fix si `docker compose ps` montre des services down, toujours inspecter les logs infra en cas d'erreur HTTP 500, bloquer si erreurs DNS/connexion détectées.
- **Root cause / besoin** : l'agent validait des fixes code alors que l'infrastructure Docker/Mongo était down, causant des faux positifs et une confusion entre bug code vs bug infra (ex: `mongo:27017 Temporary failure in name resolution` interprété comme bug application).
- **Effet** : prévention des faux positifs (validation uniquement si infrastructure saine), distinction claire erreur infra vs erreur application, messages explicites "NON VALIDÉ — Infrastructure Docker/Mongo non disponible" avec diagnostic fourni.
- **Tests** : scénario de test avec panne infra simulée (`docker compose stop mongo`) → agent doit bloquer la validation.
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-18_infra_health_check_protocol.md`.

---

### 2025-12-18 – Chapitre créé via admin marqué "indisponible" dans le générateur

- **Backend** : création du script `backend/scripts/sync_chapter_from_exercises.py` pour synchroniser automatiquement un chapitre depuis la collection `exercises` vers le référentiel curriculum (`chapters`). Le script extrait les `exercise_types` depuis les `generator_key` des exercices dynamiques et crée/met à jour le chapitre dans le référentiel curriculum.
- **Root cause / besoin** : un chapitre créé via l'admin (collection `exercises`) n'apparaît pas automatiquement dans le référentiel curriculum (`chapters`). Le catalogue lit depuis le référentiel curriculum, donc si le chapitre n'existe pas ou n'a pas de `exercise_types` → `hasGenerators: false` → badge "indisponible" dans le générateur.
- **Effet** : les chapitres créés via admin peuvent être synchronisés dans le référentiel curriculum pour apparaître dans le catalogue avec `hasGenerators: true` (sélectionnable).
- **Tests** : script exécutable manuellement avec `python scripts/sync_chapter_from_exercises.py <chapter_code>`.
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-18_chapitre_indisponible_generateur.md`.

---

### 2025-12-18 – Fix admin GM08 (500 + lenteur) + cache performance

- **Backend** : correction de l'erreur 500 sur `/api/admin/chapters/6e_GM08/exercises` et optimisation de la performance via cache TTL 5 minutes pour `get_stats` dans `backend/services/exercise_persistence_service.py`. Ajout de logs `[CACHE HIT]` / `[CACHE MISS]` pour observabilité. Remplacement de l'import dynamique dans `is_chapter_template_based` (`backend/services/variants_config.py`) par un import lazy (`_get_is_tests_dyn_request`) pour éviter le coût per-call. Gestion d'erreur explicite dans `_load_from_python_file` (remontée `ValueError` au lieu de logger silencieux) et HTTPException JSON structurée dans `backend/routes/admin_exercises_routes.py` (error_code `EXERCISE_LOAD_ERROR` / `INTERNAL_SERVER_ERROR`).
- **Root cause / besoin** : après modifications Phase Finale (variants auto-detection), la route admin GM08 renvoyait HTTP 500 et le site était très lent. Causes identifiées : (1) import dynamique coûteux dans `is_chapter_template_based` (fait à chaque appel), (2) requêtes MongoDB per-request dans `initialize_chapter` et `get_stats` (4-5 requêtes par requête admin, pas de cache), (3) exception silencieuse dans `_load_from_python_file` causant HTTP 500.
- **Effet** : GM08 fonctionne (HTTP 200 ou 422 explicite, pas de 500), performance améliorée (cache réduit 4 requêtes DB → 0 après première requête), observabilité (logs cache HIT/MISS), zéro régression GM07/TESTS_DYN.
- **Tests** : création de `backend/tests/test_admin_gm08_perf.py` (test 500, test cache HIT/MISS, test TTL expiry).
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-18_admin_GM08_500_and_perf.md`.

---

### 2025-12-18 – Industrialisation template_variants (Phase Finale : Détection automatique)

- **Backend** : suppression de l'allowlist manuelle (`VARIANTS_ALLOWED_CHAPTERS`) et implémentation d'une détection automatique des chapitres template-based via `is_chapter_template_based()` dans `backend/services/variants_config.py`. Critères de détection : handler dédié (`tests_dyn_handler`) OU exercice dynamique avec `is_dynamic=True` + `generator_key` + `enonce_template_html`. Exclusion explicite hardcodée pour `6E_GM07` et `6E_GM08` (statiques). Remplacement de `is_variants_allowed()` par `is_chapter_template_based()` dans `format_dynamic_exercise()` (`backend/services/tests_dyn_handler.py`), avec erreur `VARIANTS_NOT_SUPPORTED` (au lieu de `VARIANTS_NOT_ALLOWED`) pour les chapitres spec-based.
- **Root cause / besoin** : l'allowlist manuelle (Phase A) nécessitait une validation manuelle pour chaque nouveau chapitre template-based. La cible finale est une industrialisation complète avec détection automatique basée sur des critères techniques (template-based vs spec-based).
- **Effet** : activation automatique des `template_variants` sur tous les chapitres template-based (plus besoin de validation manuelle), interdiction automatique sur les chapitres spec-based (erreur explicite), zéro régression `6E_TESTS_DYN` (handler dédié), exclusion explicite `6E_GM07`/`6E_GM08` (intouchables).
- **Tests** : mise à jour de `backend/tests/test_variants_allowlist.py` (détection automatique, exclusion GM07/GM08, erreur `VARIANTS_NOT_SUPPORTED`).
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-18_variants_auto_detection_phase_finale.md`.

### 2025-12-18 – Généralisation template_variants (Phase A : Allowlist)

- **Backend** : création de `backend/services/variants_config.py` avec allowlist explicite `VARIANTS_ALLOWED_CHAPTERS = {"6E_TESTS_DYN"}` et fonction `is_variants_allowed()` pour contrôler l'activation des `template_variants` par chapitre. Enforcement dans `format_dynamic_exercise()` (`backend/services/tests_dyn_handler.py`) : si `template_variants` non vide et chapitre non autorisé → erreur JSON `VARIANTS_NOT_ALLOWED` (HTTP 422), zéro fallback silencieux.
- **Root cause / besoin** : les `template_variants` fonctionnent sur le pilote `6e_TESTS_DYN`, mais aucun mécanisme n'existait pour autoriser/interdire leur utilisation sur d'autres chapitres dynamiques template-based, avec risque d'utilisation accidentelle sur des chapitres non compatibles (spec-based via `MathGenerationService`).
- **Effet** : contrôle strict sur l'activation progressive des variants par chapitre (feature flag), non-régression `6e_TESTS_DYN` (chapitre autorisé), évolutivité (ajout facile dans l'allowlist), rollback facile (retrait d'un chapitre).
- **Tests** : création de `backend/tests/test_variants_allowlist.py` (normalisation, enforcement, non-régression).
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-18_variants_allowlist_phaseA.md`.

### 2025-12-18 – Variants d'énoncés dynamiques (Étape 5 : réhydratation admin & CRUD)

- **Frontend** : renforcement de la réhydratation des `template_variants` dans `ChapterExercisesAdminPage` (les variants deviennent la source de vérité dès qu’ils sont présents, même en cas d’incohérence sur `is_dynamic`) et centralisation des appels CRUD admin (create/update/delete) via `adminApi` (`frontend/src/lib/adminApi.js`) pour bénéficier d’un parsing JSON défensif et d’erreurs structurées lors de la gestion des exercices dynamiques.
- **Effet** : les variants créés en admin restent visibles et éditables à la réouverture des exercices, sans “retour” silencieux au mode legacy, et les erreurs réseau/serveur sont homogènes sur l’ensemble du backoffice.
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-18_template_variants_step5_rehydrate.md`.

### 2025-12-18 – Persistance des `template_variants` en mise à jour (fix update_exercise)

- **Backend** : `ExercisePersistenceService.update_exercise` persiste désormais les champs dynamiques `enonce_template_html`, `solution_template_html`, `is_dynamic`, `generator_key` et surtout `template_variants` (convertis en liste de dicts ou `None`), évitant la perte de variants lors des PUT admin.
- **Tests** : ajout d’un test de persistance (update avec `template_variants` puis lecture) dans `backend/tests/test_exercise_persistence_models_variants.py`.
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-18_template_variants_update_put.md`.

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

### 2025-12-18 – Variants d’énoncés dynamiques (Étape 4 : UI admin & preview)

- **Frontend** : ajout d’un bloc de gestion des `template_variants` dans `ChapterExercisesAdminPage` (création/édition/duplication/suppression de variants, validation des champs id/weight/templates) et extension de `DynamicPreviewModal` pour supporter un mode Auto (seed) ou Forcé (`variant_id`), en envoyant `template_variants`, `variant_id` et `stable_key` au backend. L’UI bascule automatiquement en mode variants dès qu’au moins deux variants sont définis et persiste `template_variants` via l’API admin existante.
- **Backend** : enrichissement léger de `DynamicPreviewResponse` avec `variant_id_used` pour tracer le variant effectivement utilisé en preview ; aucun changement côté génération élève ni sur GM07/GM08.

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
