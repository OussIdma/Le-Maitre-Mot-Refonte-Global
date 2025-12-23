# P1 - Templates Éditables : Plan Complet (12-15h)

## 🎯 Vision

Permettre aux **admins** de modifier la **rédaction pédagogique** (énoncés/solutions) **sans toucher au code**, avec validation temps réel et preview.

---

## 📊 Phases

### ✅ **Phase 1+2 : Backend MVP (6h)** — COMPLET

**Livrables :**
- ✅ Modèle MongoDB `GeneratorTemplate`
- ✅ Service CRUD complet
- ✅ Routes admin (CRUD + validation/preview)
- ✅ Tests backend (21 tests)
- ✅ Doc API

**Statut :** ✅ **LIVRÉ 2025-12-23**

---

### ⏸️ **Phase 3 : Intégration dans /generate (2-3h)**

**Objectif :** Utiliser les templates DB dans l'API de génération

**Tâches :**

1. **Modifier `/api/v1/exercises/generate` (1h)**
   - Ajouter `await get_template_service(db).get_best_template(...)`
   - Si template DB trouvé → utiliser `enonce_template_html` / `solution_template_html`
   - Sinon → fallback sur templates hardcodés legacy (ChapterExercisesAdminPage.js)
   - Ordre de priorité :
     1. Template DB (generator + variant + grade + difficulty)
     2. Template DB (generator + variant + grade)
     3. Template DB (generator + variant)
     4. Template DB (generator + default)
     5. Fallback legacy hardcodé

2. **Render avec variables (30min)**
   - Utiliser `render_template(template_html, variables)`
   - Gérer triple moustaches `{{{var}}}`
   - Gérer double moustaches `{{var}}`

3. **Tests intégration (1h)**
   - Test nominal : template DB trouvé → HTML correct
   - Test fallback : pas de template DB → legacy fonctionne
   - Test priorité : plusieurs templates → sélection correcte
   - Test sécurité : triple moustaches non autorisées → HTML échappé

4. **Log observabilité (30min)**
   - `template_source: "db" | "legacy"`
   - `template_id` si DB
   - `template_fallback_reason` si legacy

**Fichiers modifiés :**
- `backend/routes/exercises_routes.py`
- `backend/tests/test_exercises_integration_templates.py` (nouveau)

**Validation :**
```bash
# Créer un template DB pour RAISONNEMENT_MULTIPLICATIF_V1
curl -X POST http://localhost:8000/api/v1/admin/generator-templates -d '...'

# Générer un exercice → doit utiliser le template DB
curl -X POST http://localhost:8000/api/v1/exercises/generate -d '{
  "chapter_code": "6e_SP03",
  "offer": "pro",
  "seed": 42
}'

# Vérifier metadata.template_source == "db"
```

---

### ⏸️ **Phase 4 : UI Admin (4-5h)**

**Objectif :** Interface admin pour créer/modifier les templates

**Tâches :**

1. **Page Admin Templates (2h)**
   - Route : `/admin/generator-templates`
   - Liste des templates (table avec filtres)
   - Colonnes : Générateur, Variant, Niveau, Difficulté, Date, Actions
   - Boutons : Créer, Éditer, Dupliquer, Supprimer
   - Filtres : generator_key, variant_id, grade

2. **Modal Rédaction (2h)**
   - Formulaire :
     - Générateur (dropdown, liste depuis `/api/v1/exercises/generators`)
     - Variant (A/B/C/default)
     - Niveau (6e/5e/null)
     - Difficulté (facile/moyen/difficile/null)
     - Énoncé HTML (éditeur CodeMirror ou Monaco)
     - Solution HTML (éditeur CodeMirror ou Monaco)
     - Variables HTML autorisées (multi-select)
   - Bouton "Prévisualiser" → appelle `/validate` → affiche preview
   - Bouton "Sauvegarder" → appelle `POST /templates`

3. **Prévisualisation Live (1h)**
   - Zone preview à droite (split-screen)
   - Affiche `enonce_html` et `solution_html`
   - Met à jour en temps réel (debounce 500ms)
   - Affiche erreurs de validation (placeholders manquants, HTML non autorisé)

4. **Dupliquer Template (30min)**
   - Bouton "Dupliquer depuis..." dans le formulaire
   - Liste des templates existants
   - Pré-remplit le formulaire avec le template sélectionné
   - L'admin peut modifier avant sauvegarde

**Fichiers nouveaux :**
- `frontend/src/components/admin/GeneratorTemplatesAdminPage.js`
- `frontend/src/components/admin/TemplateEditorModal.js`
- `frontend/src/components/admin/TemplatePreview.js`

**Validation :**
1. Ouvrir `/admin/generator-templates`
2. Créer un template pour `RAISONNEMENT_MULTIPLICATIF_V1` variant A
3. Prévisualiser → voir HTML rendu
4. Sauvegarder
5. Dupliquer pour variant B
6. Modifier et sauvegarder
7. Filtrer par générateur → voir 2 templates

---

### ⏸️ **Phase 5 : Migration Progressive (1h)**

**Objectif :** Migrer les templates hardcodés vers MongoDB

**Tâches :**

1. **Script de migration (30min)**
   - Lire `ChapterExercisesAdminPage.js` (fonction `getDynamicTemplates`)
   - Extraire templates pour chaque générateur
   - Insérer en DB via `/api/v1/admin/generator-templates`

2. **Validation post-migration (30min)**
   - Comparer rendu avant/après migration
   - Vérifier que tous les générateurs ont un template default
   - Supprimer templates hardcodés frontend (optionnel, après validation)

**Fichiers :**
- `scripts/migrate_templates_to_db.py` (nouveau)

**Validation :**
```bash
python scripts/migrate_templates_to_db.py

# Vérifier que les templates sont en DB
curl http://localhost:8000/api/v1/admin/generator-templates

# Générer exercices → doit fonctionner comme avant
```

---

### ⏸️ **Phase 6 : Améliorations (2-3h, optionnel)**

**Tâches :**

1. **Historique des modifications (1h)**
   - Ajouter collection `generator_template_history`
   - Stocker chaque version lors d'une mise à jour
   - UI : bouton "Historique" → liste des versions
   - Bouton "Restaurer" pour revenir à une version antérieure

2. **Permissions (30min)**
   - Ajouter `created_by` (user ID)
   - Limiter édition aux super-admins ou créateur
   - Log actions (création, modification, suppression)

3. **Import/Export (1h)**
   - Bouton "Exporter" → JSON téléchargeable
   - Bouton "Importer" → upload JSON → création en masse
   - Format standardisé pour partage entre environnements

4. **Recherche full-text (30min)**
   - Index MongoDB sur `enonce_template_html` et `solution_template_html`
   - Barre de recherche admin : "Trouver templates contenant 'proportionnalité'"

---

## 📈 Estimation Totale

| Phase | Temps | Statut |
|-------|-------|--------|
| **Phase 1+2 : Backend MVP** | 6h | ✅ COMPLET |
| **Phase 3 : Intégration /generate** | 2-3h | ⏸️ Pending |
| **Phase 4 : UI Admin** | 4-5h | ⏸️ Pending |
| **Phase 5 : Migration** | 1h | ⏸️ Pending |
| **Phase 6 : Améliorations** | 2-3h | ⏸️ Optionnel |
| **TOTAL** | **12-15h** | 6h/15h (40%) |

---

## 🎯 Priorités

### P0 (Bloquant)
- ✅ Phase 1+2 : Backend MVP

### P1 (Important)
- ⏸️ Phase 3 : Intégration /generate
- ⏸️ Phase 4 : UI Admin

### P2 (Nice to Have)
- ⏸️ Phase 5 : Migration
- ⏸️ Phase 6 : Améliorations

---

## 🚀 Déploiement

### Prérequis
- ✅ MongoDB accessible
- ✅ Backend Docker build OK
- ✅ Tests backend passants

### Étapes
1. ✅ **Phase 1+2** : Backend MVP (FAIT)
2. ⏸️ **Phase 3** : Intégration /generate → tests E2E
3. ⏸️ **Phase 4** : UI Admin → tests manuels
4. ⏸️ **Phase 5** : Migration → validation rendu identique
5. ⏸️ **Phase 6** : Améliorations (si temps)

---

## 📝 Documentation

**Disponible :**
- ✅ `docs/P1_TEMPLATES_EDITABLES_BACKEND_MVP.md` : Doc API
- ✅ `docs/P1_TEMPLATES_BACKEND_LIVRAISON.md` : Livraison Phase 1+2
- ✅ `docs/P1_TEMPLATES_EDITABLES_PLAN.md` : Ce document

**À créer :**
- ⏸️ `docs/P1_TEMPLATES_INTEGRATION_GENERATE.md` (Phase 3)
- ⏸️ `docs/P1_TEMPLATES_UI_ADMIN.md` (Phase 4)

---

## ✅ Validation Finale

### Critères de Succès

**Phase 1+2 (Backend MVP) :**
- [x] 21 tests passants
- [x] CRUD fonctionnel
- [x] Validation/preview opérationnelle
- [x] Sécurité HTML garantie

**Phase 3 (Intégration) :**
- [ ] `/generate` utilise templates DB
- [ ] Fallback legacy fonctionne
- [ ] Metadata `template_source` correct
- [ ] Tests E2E passants

**Phase 4 (UI Admin) :**
- [ ] Page admin accessible
- [ ] Créer/modifier templates OK
- [ ] Preview temps réel fonctionne
- [ ] Dupliquer templates OK

**Phase 5 (Migration) :**
- [ ] Tous templates legacy en DB
- [ ] Rendu identique avant/après
- [ ] Zero downtime

---

**Date :** 2025-12-23  
**Statut :** ✅ Phase 1+2 COMPLET (6h/15h)  
**Prochaine Phase :** Phase 3 (Intégration /generate)
