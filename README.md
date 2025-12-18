## Le Maître Mot v16 – Refonte locale

Ce dépôt contient l’implémentation backend/frontend de la refonte locale de **Le Maître Mot** (FastAPI + React + MongoDB), ainsi que l’infrastructure Docker et la documentation d’architecture/pédagogie.

### Démarrage rapide (local)

- Prérequis : Docker + Docker Compose installés.
- Depuis la racine du projet :

```bash
docker compose up --build
```

- Vérifier que tout est OK :

```bash
./scripts/healthcheck.sh
```

Ce script appelle automatiquement :

1. `GET /api/debug/build` – pour vérifier le build backend.
2. `POST /api/admin/exercises/preview-dynamic` (THALES_V1) – preview admin JSON-safe.
3. `POST /api/v1/exercises/generate` (`code_officiel=6e_TESTS_DYN`) – génération élève sans placeholders.

### Documentation (dossier `docs/`)

Les documents d’architecture et d’investigation ont été déplacés dans `docs/` pour centraliser la connaissance. En particulier :

- **Investigations** (analyse de bugs / racines) :
  - `docs/INVESTIGATION_PREVIEW_JSON.md` – Crash “Unexpected token 'I' … is not valid JSON” en preview admin.
  - `docs/INVESTIGATION_PREVIEW_THALES_V1.md` – Analyse du preview THALES_V1 côté admin.
  - `docs/INVESTIGATION_PREVIEW_SYMETRIE_AXIALE_V2.md` – Preview SYMETRIE_AXIALE_V2 et intégration avec la Factory.
  - `docs/INVESTIGATION_PLACEHOLDERS_TESTS_DYN.md` – Placeholders `{{...}}` visibles pour 6e_TESTS_DYN (THALES_V1).
  - `docs/INVESTIGATION_VARIATION_ERROR.md` – Bouton “Variation” 6e_TESTS_DYN et gestion des seeds/offers.
  - `docs/INVESTIGATION_SELECTION_SCALE.md` – Sélection de pool pour SYMÉTRIE vs THALES (mauvais type d’exercice).

- **Spécifications / contexte** :
  - `docs/ENVIRONMENT_SETUP.md` – Installation locale (Docker, dépendances système, WeasyPrint, etc.).
  - `docs/ADMIN_CURRICULUM_6E.md` – Gestion du curriculum 6e dans l’admin.
  - `docs/API_EXERCISES.md` – Contrat de l’API `/api/v1/exercises/**`.
  - `docs/FIGURES_FUSION_*` – spécifications de fusion des figures de géométrie.
  - `docs/SPRINT_*` – comptes-rendus de sprints et corrections métier.

Consulte ces fichiers pour le détail des décisions d’architecture et des corrections déjà apportées.

