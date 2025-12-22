## INCIDENT — Champ pipeline ignoré en édition admin (chapitre 6e_AA_TEST bloqué en SPEC)

- **ID** : `INCIDENT_2025-12-19_pipeline_admin_not_persisted`
- **Date** : 2025-12-19
- **Symptôme** : En admin curriculum, la sauvegarde du pipeline `TEMPLATE` pour `6e_AA_TEST` n'est pas prise en compte ; le catalogue reste en `SPEC`, chapitre indisponible.
- **Root Cause (prouvée)** :
  1. Le modèle `ChapterUpdateRequest` ne contenait pas le champ `pipeline` → FastAPI ignorait la valeur envoyée par le formulaire (`extra` silencieux).
  2. Les réponses admin (`AdminChapterResponse`) ne renvoyaient pas `pipeline`, donc le formulaire se pré-remplissait toujours à `SPEC`.
  3. Aucune entrée dynamique dans `db.exercises` pour `chapter_code = "6E_AA_TEST"`, donc même avec pipeline `TEMPLATE` la disponibilité resterait bloquée (validation pipeline).
- **Fix appliqué** :
  - Backend admin curriculum :
    - Ajout de `pipeline` dans `ChapterUpdateRequest` pour accepter la mise à jour.
    - Ajout de `pipeline` dans `AdminChapterResponse` et mapping de réponse pour remonter la valeur réelle au frontend.
  - Rebuild backend.
- **Tests / Preuve** :
  - `docker compose ps` → backend/mongo up & healthy.
  - `curl -s http://localhost:8000/api/admin/curriculum/6e/6e_AA_TEST | jq '{code_officiel,pipeline,generateurs}'` → `{ "code_officiel": "6e_AA_TEST", "pipeline": "SPEC", ... }` (le champ est bien présent).
- **Action restante** :
  - Créer au moins un exercice dynamique en DB (`is_dynamic=true`, `generator_key` valide) puis repasser le pipeline à `TEMPLATE` (ou `MIXED`) pour que le chapitre devienne disponible. Sans exercice dynamique, la validation `TEMPLATE` restera bloquante.
- **Commande de rebuild / restart** : `docker compose up -d --build backend`
