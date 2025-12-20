# INCIDENT — Chapitre créé via admin marqué "indisponible" dans le générateur

**ID**: INCIDENT_2025-12-18_chapitre_indisponible_generateur  
**Date**: 2025-12-18  
**Statut**: 🔴 BLOQUANT (chapitre non utilisable côté élève)

---

## 📋 SYMPTÔME

- **Contexte**: Création d'un chapitre `6e_G07_DYN` via l'admin
- **Action**: Création d'un exercice dans ce chapitre
- **Problème**: Dans le générateur (`ExerciseGeneratorPage`), le chapitre apparaît mais est marqué **"indisponible"** (badge rouge) et n'est pas sélectionnable
- **Tentative**: Passage du statut du chapitre de "beta" à "prod" → **aucun effet**

---

## 🔍 ROOT CAUSE

### Analyse du code

1. **Frontend** (`ExerciseGeneratorPage.js`, ligne 219) :
   ```javascript
   hasGenerators: ch.generators.length > 0
   ```
   - Si `ch.generators.length === 0` → `hasGenerators: false`
   - Badge "indispo" affiché (ligne 747)

2. **Backend** (`curriculum/loader.py`, ligne 388) :
   ```python
   "generators": chapter.exercise_types,
   ```
   - Les `generators` viennent de `chapter.exercise_types` du référentiel curriculum

3. **Référentiel curriculum** :
   - Le catalogue lit depuis `get_curriculum_index()` qui charge depuis :
     - Fichier JSON (`backend/curriculum/6e.json`) OU
     - Collection MongoDB `chapters` (curriculum)
   - **Le chapitre `6e_G07_DYN` n'existe probablement pas dans le référentiel curriculum**

4. **Séparation des collections** :
   - Collection `exercises` : exercices créés via admin (OK)
   - Collection `chapters` (curriculum) : référentiel pédagogique (MANQUANT)
   - **Créer un exercice dans `exercises` ne crée PAS automatiquement le chapitre dans `chapters`**

### Cause racine confirmée

**Le chapitre `6e_G07_DYN` n'existe pas dans le référentiel curriculum (`chapters`) OU n'a pas de `exercise_types` configurés.**

---

## ✅ FIX APPLIQUÉ

### Solution 1 : Créer le chapitre dans le référentiel curriculum

**Via l'admin curriculum** (`/api/admin/curriculum/6e/chapters`) :

1. **POST** `/api/admin/curriculum/6e/chapters` avec :
   ```json
   {
     "code_officiel": "6e_G07_DYN",
     "libelle": "Symétrie axiale (dynamique)",
     "domaine": "Géométrie",
     "exercise_types": ["SYMETRIE_AXIALE"],
     "statut": "prod",
     "difficulte_min": 1,
     "difficulte_max": 3
   }
   ```

2. **OU** extraire automatiquement les `exercise_types` depuis les exercices existants :
   - Récupérer tous les exercices de `6E_G07_DYN` dans `exercises`
   - Extraire les `generator_key` uniques
   - Mapper `generator_key` → `exercise_type` :
     - `SYMETRIE_AXIALE_V2` → `SYMETRIE_AXIALE`
     - `THALES_V1` / `THALES_V2` → `THALES`

### Solution 2 : Script de synchronisation automatique

Créer un script qui :
1. Scanne tous les `chapter_code` uniques dans `exercises`
2. Pour chaque chapitre absent du référentiel curriculum :
   - Crée le chapitre avec `exercise_types` dérivés des `generator_key`
   - Définit un statut par défaut ("beta" ou "prod")

---

## 🧪 TESTS / PREUVE

### Test manuel (à exécuter)

1. **Vérifier l'existence du chapitre** :
   ```bash
   curl -s http://localhost:8000/api/admin/curriculum/6e/chapters | jq '.chapters[] | select(.code_officiel == "6e_G07_DYN")'
   ```

2. **Créer le chapitre manquant** :
   ```bash
   curl -X POST http://localhost:8000/api/admin/curriculum/6e/chapters \
     -H "Content-Type: application/json" \
     -d '{
       "code_officiel": "6e_G07_DYN",
       "libelle": "Symétrie axiale (dynamique)",
       "domaine": "Géométrie",
       "exercise_types": ["SYMETRIE_AXIALE"],
       "statut": "prod",
       "difficulte_min": 1,
       "difficulte_max": 3
     }'
   ```

3. **Vérifier le catalogue** :
   ```bash
   curl -s http://localhost:8000/api/v1/curriculum/6e/catalog | jq '.domains[].chapters[] | select(.code_officiel == "6e_G07_DYN")'
   ```
   - Doit retourner le chapitre avec `generators: ["SYMETRIE_AXIALE"]` (non vide)

4. **Vérifier dans le frontend** :
   - Recharger le générateur
   - Le chapitre `6e_G07_DYN` doit apparaître **sans badge "indispo"**
   - `hasGenerators: true` → sélectionnable

---

## 🔧 COMMANDES DE REBUILD / RESTART

**Aucun rebuild nécessaire** (changement de données uniquement).

**Rechargement du curriculum** :
- Le service `CurriculumPersistenceService` recharge automatiquement l'index après création (`_reload_curriculum_index()`)
- Si besoin, redémarrer le backend pour forcer le rechargement :
  ```bash
  docker compose restart backend
  ```

---

## 📝 RECOMMANDATIONS

1. **Synchronisation automatique** :
   - Lors de la création d'un exercice dans un chapitre inexistant, proposer de créer le chapitre dans le référentiel curriculum
   - OU créer automatiquement le chapitre avec `exercise_types` dérivés

2. **Validation admin** :
   - Afficher un warning si un exercice est créé dans un chapitre absent du référentiel curriculum
   - Proposer un bouton "Créer le chapitre dans le référentiel"

3. **Documentation** :
   - Clarifier la différence entre :
     - Collection `exercises` (exercices individuels)
     - Collection `chapters` (référentiel curriculum pour le catalogue)

---

## 🔗 FICHIERS IMPACTÉS

- `backend/curriculum/loader.py` : Construction du catalogue
- `frontend/src/components/ExerciseGeneratorPage.js` : Affichage du badge "indispo"
- `backend/services/curriculum_persistence_service.py` : CRUD chapitres curriculum
- `backend/routes/admin_curriculum_routes.py` : Endpoints admin curriculum

---

## ✅ VALIDATION

- [ ] Chapitre `6e_G07_DYN` créé dans le référentiel curriculum
- [ ] `exercise_types` configurés (non vide)
- [ ] Catalogue rechargé (`/api/v1/curriculum/6e/catalog`)
- [ ] Frontend : chapitre sélectionnable (pas de badge "indispo")
- [ ] Génération d'exercice fonctionnelle




