## INCIDENT – Fiche récapitulative (TEMPLATE)

> Duplique ce fichier pour chaque incident (`docs/incidents/INCIDENT_YYYY-MM-DD_slug.md` par exemple) et remplis toutes les sections.

### 1. Métadonnées

- **ID incident** : `INCIDENT_YYYY-MM-DD_xxx`
- **Date de détection** : __À REMPLIR__
- **Période d’impact** : __À REMPLIR__ (ex. `2025-12-17 09:12 → 09:26 CET`)
- **Environnement** : __À REMPLIR__ (local / staging / prod / autre)
- **Gravité** : __À REMPLIR__ (P0 / P1 / P2)
- **Statut** : __À REMPLIR__ (ouvert / mitigé / résolu / post-mortem validé)
- **Auteur de la fiche** : __À REMPLIR__

### 2. Résumé exécutif (3–5 lignes max)

- **Contexte** : __À REMPLIR__  
- **Symptôme visible** : __À REMPLIR__  
- **Impact utilisateur** : __À REMPLIR__ (qui, quoi, combien)  
- **Cause technique (résumée)** : __À REMPLIR__  
- **État actuel** : __À REMPLIR__ (corrigé / workaround / en cours d’analyse)

### 3. Contexte détaillé

- **Fonctionnalité concernée** : __À REMPLIR__ (ex. Génération élève 6e_TESTS_DYN, Preview admin, GM07/GM08…)  
- **Endpoints / pages impactés** : __À REMPLIR__ (URL API + URL frontend)  
- **Version / build backend** : __À REMPLIR__ (ex. retour `/api/debug/build`)  
- **Hypothèses initiales** : __À REMPLIR__ (facultatif mais utile pour éviter les biais de confirmation)

### 4. Symptômes & impact

- **Symptômes observés** :
  - __À REMPLIR__ (messages d’erreur exacts, stack trace, captures d’écran…)
- **Impact utilisateur** :
  - __À REMPLIR__ (élèves impactés, admins, data corrompue ou non, perte de fonction ou simple dégradation)
- **Scope** :
  - __À REMPLIR__ (tous les chapitres / seulement 6e_TESTS_DYN / seulement premium, etc.)

### 5. Chronologie (timeline)

> Horodatage en UTC ou fuseau précisé. Un événement par ligne.

- `YYYY-MM-DD HH:MM` — __À REMPLIR__ (détection de l’incident)
- `YYYY-MM-DD HH:MM` — __À REMPLIR__ (première analyse / mitigation)
- `YYYY-MM-DD HH:MM` — __À REMPLIR__ (identification de la cause racine)
- `YYYY-MM-DD HH:MM` — __À REMPLIR__ (déploiement du correctif)
- `YYYY-MM-DD HH:MM` — __À REMPLIR__ (retour à la normale confirmé)

### 6. Diagnostic & cause racine

- **Fichiers / modules impliqués** :
  - __À REMPLIR__ (ex. `backend/routes/exercises_routes.py`, `backend/services/tests_dyn_handler.py`, `frontend/src/components/ExerciseGeneratorPage.js`)
- **Comportement attendu** :
  - __À REMPLIR__
- **Comportement observé** :
  - __À REMPLIR__
- **Cause racine (prouvée, pas hypothétique)** :
  - __À REMPLIR__ (décrire la chaîne exacte de conditions + la ligne ou le bloc fautif)

### 7. Correctifs appliqués (technique)

- **Backend** :
  - __À REMPLIR__ (routes, services, handlers, validations, schémas…)
- **Frontend** :
  - __À REMPLIR__ (composants, parsing d’erreurs, UX de fallback…)
- **Infra / config** :
  - __À REMPLIR__ (Docker, env vars, Git, scripts…)

> Joindre les références Git (commits, PR) :
- **Commits** : __À REMPLIR__ (hash + message)
- **Branches / tags** : __À REMPLIR__

### 8. Validation & tests

- **Tests manuels** :
  - __À REMPLIR__ (scénarios précis + résultats)
- **Scripts / commandes** :
  - __À REMPLIR__ (ex. `./scripts/healthcheck.sh`, `curl` de reproduction…)
- **Tests automatiques** (si existants) :
  - __À REMPLIR__ (nom des tests, fichiers, statut)

### 9. Risques résiduels & actions de suivi

- **Risques résiduels connus** :
  - __À REMPLIR__ (ex. autres chapitres non testés, cas limites sur d’autres niveaux…)
- **Actions de durcissement** (prévention) :
  - __À REMPLIR__ (tests automatiques à ajouter, garde-fous, monitoring…)
- **Actions de documentation** :
  - __À REMPLIR__ (docs à mettre à jour : `README.md`, `docs/*.md`, runbooks…)
- **Owners & échéances** :
  - __À REMPLIR__ (qui fait quoi, pour quand)

### 10. Annexes & références

- **Logs / traces** :
  - __À REMPLIR__ (chemins de fichiers, extraits anonymisés si nécessaire)
- **Liens externes** :
  - __À REMPLIR__ (tickets, Slack, Notion, etc.)
- **Autres** :
  - __À REMPLIR__





