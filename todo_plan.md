# Le Maître Mot — todo_plan.md (pilotage Qwen Code)
Objectif: sortir une V1 monétisable rapidement, puis stabiliser (P2), sécuriser (P3), préparer V2 (P4).
Règles de travail:
- 1 tâche = 1 PR (scope petit, testable)
- À la fin de chaque tâche: l’IA doit lister les fichiers modifiés + commandes de test
- Ignore totalement: node_modules, dist, build, .next, venv, __pycache__
- Ne pas refactoriser “pour faire joli” : uniquement ce qui est demandé

## Architecture cible (résumé)
- DB (Mongo) = source unique de vérité pour curriculum, chapitres, mapping, templates, exercices.
- Frontend sans fallback silencieux (si mode dégradé, afficher un warning).
- Génération: pipeline explicite et observable (diagnostic endpoint).
- V1: paywall PDF (compte requis), quotas free, premium illimité, fiches export sujet/corrigé.

---

# P0 — Stabilisation (déjà fait)
- [x] P0.1 Fix HTML wrapping <p> dans backend/routes/exercises_routes.py (build_enonce_html) + tests
- [x] P0.2 Supprimer fallback silencieux DB->catalogue dans frontend hook + warning explicite
- [x] P0.3 Rendre exercise_type schema-driven (plus de hardcode de 2 générateurs)
- [x] P0.4 Ajouter scripts/smoke_tests_v1.sh + doc README

---

# P1 — V1 monétisable (paywall PDF + compte + mes exercices + mes fiches)
## P1.1 Quotas free exports PDF (3/jour) + erreurs structurées
- [x] Fait (ajusté dans backend/server.py et backend/routes/mathalea_routes.py + front messages)

## P1.2 Débloquer “Mes exercices” + “Mes fiches” pour comptes gratuits (plus Pro-only)
- [ ] PROMPT QWEN:
  Objectif: les users Free connectés peuvent accéder à /mes-exercices et /mes-fiches.
  Modifier:
  - frontend/src/App.js: enlever ProFeatureGuard sur /mes-exercices, /mes-fiches et /mes-fiches/:sheet_uid
  - ajouter/mettre un guard "AuthRequiredGuard": si pas connecté -> ouvrir login modal (useLogin) et rester sur page génération.
  - frontend/src/components/NavBar.js: afficher liens “Mes exercices” et “Mes fiches” pour isLoggedIn (pas seulement isPro)
  - frontend/src/components/MyExercisesPage.js: autoriser si sessionToken (pas isPro)
  - frontend/src/components/ExerciseGeneratorPage.js: “Sauvegarder” => compte requis (Free OK). Si pas connecté, ouvrir modal login.
  Tests:
  - Se connecter en free, vérifier accès pages + sauvegarde exercice.

## P1.3 Import automatique du panier local vers le compte après login/signup
- [ ] PROMPT QWEN:
  Objectif: au login/signup, importer le panier local (SelectionContext/localStorage) vers la bibliothèque user_exercises.
  Backend:
  - Ajouter endpoint batch idempotent POST /api/user/exercises/import-batch dans backend/server.py (près des routes /user/exercises):
    Body: { exercises: [ {exercise_uid,generator_key,code_officiel,difficulty,seed,variables,enonce_html,solution_html,metadata} ] }
    Auth: X-Session-Token obligatoire.
    Comportement: upsert/skip si déjà existant (user_email + exercise_uid).
    Retour: { imported, skipped, errors[] } (ne pas crasher si un item invalide).
  Frontend:
  - frontend/src/context/SelectionContext.js: fonction importSelectionToAccount(sessionToken)
  - frontend/src/components/GlobalLoginModal.js: après auth success -> si panier non vide -> appeler importSelectionToAccount
  - éviter double import: flag sessionStorage "selection_imported_for_token:<token>"
  Tests:
  - guest ajoute 3 exos au panier -> signup -> voir 3 exos dans /mes-exercices (sans duplication si relogin)

## P1.4 Sauvegarder le panier en “fiche” (Mes fiches) depuis Composer
- [ ] PROMPT QWEN:
  Objectif: depuis frontend/src/components/SheetComposerPage.js, un user connecté (free ou pro) peut créer une fiche à partir de la sélection.
  Backend:
  - Ajouter endpoint POST /api/user/sheets/create-from-selection dans backend/routes/user_sheets_routes.py:
    Body: { title, description?, exercises: [UserExerciseSaveRequest] }
    Auth requise (réutiliser get_user_email ou validate_session_token).
    Steps:
      1) Importer/sauvegarder les exercices dans user_exercises (skip duplicates)
      2) Créer la fiche user_sheets avec order
      3) Retourner sheet_uid
  Frontend:
  - Ajouter bouton “Sauvegarder dans Mes fiches” dans SheetComposerPage.js visible si connecté
  - Au clic: appeler create-from-selection, toast, navigate /mes-fiches/:sheet_uid
  Tests:
  - créer fiche depuis composer, vérifier qu’elle apparaît dans /mes-fiches et export fonctionne.

---

# P2 — Reprendre le contrôle (DB unique + pipeline explicite + pas de comportements fantômes)
## P2.1 Diagnostic pipeline + option “DB only”
- [ ] PROMPT QWEN:
  Objectif: rendre observable quel pipeline sert quel chapitre.
  Backend:
  - Ajouter GET /api/admin/diagnostics/chapter/{code_officiel} (nouveau fichier backend/routes/admin_diagnostics_routes.py ou dans admin routes existantes)
    Retour: {code_officiel, pipeline_used, reason, db_exercises_count, fallback_used}
  - Dans backend/routes/exercises_routes.py generate_exercise():
    - logs structurés: request_id, code_officiel, pipeline_used
    - ajouter env DISABLE_FILE_PIPELINES=true pour désactiver les pipelines file-based (TESTS_DYN etc.) et forcer DB.
  Tests:
  - appeler diagnostics endpoint et vérifier réponse.

## P2.2 Mode READONLY_CODEBASE + migration fichiers -> DB
- [ ] PROMPT QWEN:
  Objectif: interdire toute écriture sur backend/data/*.py en staging/prod et préparer migration.
  Backend:
  - Ajouter env READONLY_CODEBASE=true: toute tentative d’écriture fichier -> HTTP 503 {code:"READONLY_MODE"}
  - Ajouter script backend/scripts/migrate_data_files_to_db.py:
    - lit backend/data/*.py (gm07/gm08/tests_dyn si présents)
    - upsert dans Mongo admin_exercises
    - imprime inserted/updated/skipped
  Doc:
  - docs/architecture/migrations.md: procédure et backup mongo avant
  Tests:
  - exécuter script en local; vérifier résumé.

---

# P3 — Qualité / anti-régression (tests E2E + CI)
## P3.1 Tests E2E backend V1
- [ ] PROMPT QWEN:
  Créer backend/tests/test_e2e_v1_flow.py:
  - test_generate_exercise_no_placeholders: POST /api/v1/exercises/generate (chapitre stable) -> assert 200 + pas de '{{'
  - test_export_requires_auth_and_quota: export-selection sans token => 401 (code AUTH_REQUIRED_EXPORT) ; avec free => ok jusqu’à 3/jour puis 429 FREE_DAILY_EXPORT_LIMIT
  Commande: pytest -q backend/tests/test_e2e_v1_flow.py

## P3.2 CI minimale “signal vert/rouge”
- [ ] PROMPT QWEN:
  Ajouter .github/workflows/ci_v1.yml:
  - docker compose up --build -d
  - run ./scripts/healthcheck.sh
  - run ./scripts/smoke_tests_v1.sh
  - run pytest (au moins export_access_control + e2e_v1_flow)
  Le workflow échoue si un test échoue.

---

# P4 — Préparer V2 (2 boutons / identité stable / multi-matières)
## P4.1 Identité exercice + endpoints “reroll data” vs “new exercise”
- [ ] PROMPT QWEN:
  Objectif: formaliser 2 actions:
  - reroll data: même generator_key + template_id, seed change
  - new exercise: template_id peut changer + seed change
  Backend:
  - garantir metadata: generator_key, template_id, seed, generator_version
  - POST /api/v1/exercises/reroll-data
  - POST /api/v1/exercises/new-exercise
  Frontend:
  - ajouter 2 boutons sur chaque exercice: “Changer les valeurs” et “Nouvel énoncé”
  Tests:
  - reroll conserve template_id ; new-exercise peut changer template_id.

## P4.2 Multi-matières (architecture minimale)
- [ ] PROMPT QWEN:
  Objectif: préparer subject="math" par défaut, extensible.
  Backend:
  - ajouter champ subject dans modèles/collections pertinentes (défaut "math")
  - routes catalogue acceptent subject: /api/catalogue/{subject}/levels/{level}/chapters (backward compatible)
  Frontend:
  - introduire sélection matière (même si une seule option "Maths" en V1)
  Tests:
  - rien ne casse pour maths, mais structure prête.
