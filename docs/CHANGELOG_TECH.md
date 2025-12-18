## Changelog technique

Ce fichier trace les évolutions techniques majeures (backend, frontend, infra, documentation d’architecture) de **Le Maître Mot v16 – Refonte locale**.

Les entrées sont listées de la plus récente à la plus ancienne.

---

### 2025-12-18 – Alignement preview admin THALES_V1 (carrés) sur pipeline élève

- **Backend** : ajout, dans `backend/routes/generators_routes.py`, d’un mapping d’alias pour les générateurs THALES (`THALES_V1` legacy et `THALES_V2` Factory) identique à celui du handler `tests_dyn_handler.py` afin que la prévisualisation admin ne laisse plus de placeholders `{{base_initiale}}`, `{{hauteur_initiale}}`, etc. lorsqu’on utilise des carrés (ou d’autres variantes triangle/rectangle).
- **Root cause** : le pipeline de preview admin fusionnait uniquement `variables + results (+ geo_data côté Factory)` sans appliquer les alias (carre → base/hauteur/longueur/largeur) déjà utilisés côté élève, ce qui laissait des `{{...}}` non résolus dans certains templates selon le générateur utilisé (THALES_V1 ou THALES_V2).
- **Effet** : preview admin THALES cohérente avec la génération élève pour `6e_TESTS_DYN`, aucune fuite de placeholders dans l’aperçu pour les cas de carrés.
- **Référence incident** : `docs/incidents/INCIDENT_2025-12-18_admin_preview_thales_carres.md`.

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
