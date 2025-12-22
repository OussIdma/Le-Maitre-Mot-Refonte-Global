## INCIDENT — Catalogue 6e en 500 sur /generate

- **ID** : `INCIDENT_2025-12-19_catalogue_500_bool_db`
- **Date** : 2025-12-19
- **Symptôme** : le frontend `/generate` affiche « Impossible de charger le catalogue » ; l’appel `GET /api/v1/curriculum/6e/catalog` retourne 500.
- **Root Cause (prouvée)** : dans `backend/curriculum/loader.py`, le test `if db:` déclenche `NotImplementedError` car les objets `pymongo.database.Database` ne supportent pas la vérité booléenne (exigence PyMongo). La condition est exécutée à chaque requête de catalogue, provoquant l’erreur systématique.
- **Fix appliqué** : condition corrigée en `if db is not None:` pour ne plus évaluer le booléen de l’objet DB, puis rebuild/restart du backend.
- **Tests / Preuve** :
  - `docker compose ps` → backend/mongo up & healthy.
  - `curl -s -o /tmp/catalog.json -w "%{http_code}" http://localhost:8000/api/v1/curriculum/6e/catalog` → `200`.
  - Contenu `/tmp/catalog.json` contient les chapitres et macro_groups attendus (plus d’erreur JSON).
- **Commande de rebuild / restart** : `docker compose up -d --build backend`
