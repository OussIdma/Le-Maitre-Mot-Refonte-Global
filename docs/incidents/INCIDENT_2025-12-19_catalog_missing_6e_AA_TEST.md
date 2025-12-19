## INCIDENT — Chapitres 6e_AA_TEST / 6e_AA_TEST_STAT absents du catalogue

- **ID** : `INCIDENT_2025-12-19_catalog_missing_6e_AA_TEST`
- **Date** : 2025-12-19
- **Symptôme** : Les chapitres `6e_AA_TEST` et `6e_AA_TEST_STAT` n’apparaissent pas dans les choix de la page `/generate` (catalogue vide pour ces codes).
- **Root Cause (prouvée)** : `get_catalog()` construit son index uniquement depuis le fichier `backend/curriculum/curriculum_6e.json` (source de vérité chargée en cache). Les deux chapitres avaient été créés en base Mongo (`curriculum_chapters`) mais jamais synchronisés dans le JSON. Le backend n’étant pas monté en volume, le rebuild continuait de servir un JSON sans ces chapitres.
- **Fix appliqué** : Ajout des entrées `6e_AA_TEST` (SPEC, prod, sans générateurs) et `6e_AA_TEST_STAT` (SPEC, beta, exercise_types=["AIRE_TRIANGLE"]) dans `backend/curriculum/curriculum_6e.json` et rattachement au macro group « Tests Dynamiques ». Rebuild/restart du backend pour embarquer le JSON mis à jour.
- **Tests / Preuve** :
  - `docker compose ps` → backend/mongo up & healthy.
  - `curl -s http://localhost:8000/api/v1/curriculum/6e/catalog | jq '.domains[].chapters[] | select(.code_officiel|test(\"6e_AA_TEST\"))'` → retourne les deux chapitres (status prod/beta, generators [] / ["AIRE_TRIANGLE"]).
- **Commande de rebuild / restart** : `docker compose up -d --build backend`
