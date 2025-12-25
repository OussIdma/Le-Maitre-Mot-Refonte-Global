# P0 - Analyse Parcours Prof (Générer → Variante → Sauvegarder → Builder → Export PDF)

**Date**: 2024  
**Auteur**: Lead Product + Lead Dev + QA  
**Objectif**: Valider et corriger le parcours Prof de bout en bout, clarifier frontière Freemium/Pro  
**Contrainte non négociable**: "Sujet ≠ Corrigé" (enonce_html et solution_html séparés partout)

---

## 1. CARTOGRAPHIE DU PARCOURS ACTUEL

### Diagramme textuel du flux

```
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAT INITIAL: ExerciseGeneratorPage.js                         │
│ - Guest ou Pro (détection via localStorage)                    │
│ - Catalogue chargé depuis /api/v1/curriculum/{grade}/catalog  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ ACTION: Sélection chapitre + difficulté + clic "Générer"      │
│ API: POST /api/v1/exercises/generate                           │
│ Payload: {code_officiel, difficulte, seed?, offer?}           │
│ Response: {id_exercice, enonce_html, solution_html, svg, ...} │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ AFFICHAGE: Exercice généré                                     │
│ - Énoncé: MathHtmlRenderer(html={enonce_html})              │
│ - Solution: MathHtmlRenderer(html={solution_html})            │
│ - Bouton "Variante" (refresh avec nouveau seed)               │
│ - Bouton "Sauvegarder" (si Pro)                                │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ├─► VARIANTE (même code_officiel, seed différent)
                            │   └─► Retour à AFFICHAGE
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ ACTION: Clic "Sauvegarder" (si Pro)                           │
│ GUARD: if (!isPro) → PremiumUpsellModal ou UpgradeProModal     │
│ API: POST /api/user/exercises                                  │
│ Headers: {X-Session-Token, withCredentials: true}              │
│ Payload: {                                                     │
│   exercise_uid, generator_key, code_officiel, difficulty,    │
│   seed, variables, enonce_html, solution_html, metadata       │
│ }                                                              │
│ Backend: sanitize_html() sur enonce_html et solution_html     │
│ Response: {success: true, exercise_uid}                      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ REDIRECTION: /mes-exercices (MyExercisesPage.js)              │
│ - Liste des exercices sauvegardés                              │
│ - Filtres: code_officiel, difficulty                           │
│ - Actions: Voir, Dupliquer, Supprimer                          │
│ - Modal visualisation: Tabs "Énoncé" / "Solution"              │
│   └─► showSolution=false par défaut (BUG-010)                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ ACTION: Navigation vers SheetBuilderPage.js                    │
│ - Catalogue d'exercices (niveau, chapitre, domaine)            │
│ - Panier (sheetItems)                                          │
│ - Actions: Ajouter exercice, Réorganiser, Supprimer           │
│ - Bouton "Prévisualiser" → SheetPreviewModal                  │
│ - Bouton "Exporter PDF" → handleGeneratePDF()                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ ACTION: Export PDF (SheetBuilderPage.js)                     │
│ 1. saveSheet() → POST /api/user/sheets (création/mise à jour) │
│ 2. POST /api/mathalea/sheets/{sheetId}/export-standard        │
│    Response: {student_pdf, correction_pdf, base_filename}     │
│ 3. PdfDownloadModal affiche 2 boutons:                        │
│    - "Télécharger version élève" (student_pdf)                │
│    - "Télécharger version corrigée" (correction_pdf)          │
└─────────────────────────────────────────────────────────────────┘
```

### Points de friction identifiés

1. **Reset d'état après login**: Pas de rechargement automatique des exercices sauvegardés après connexion
2. **Guards Pro incohérents**: Certaines actions affichent des modals, d'autres échouent silencieusement
3. **Export PDF**: Deux endpoints différents (`/api/user/sheets/{uid}/export-pdf` vs `/api/mathalea/sheets/{id}/export-standard`)
4. **Séparation Sujet/Corrigé**: Vérification nécessaire dans tous les exports

---

## 2. VÉRIFICATION DES GUARDS PRO

### Matrice des actions Guest vs Pro

| Action | Guest | Pro | Guard Location | Issue |
|--------|-------|-----|----------------|-------|
| **Générer exercice** | ✅ Oui | ✅ Oui | - | - |
| **Voir variante** | ✅ Oui | ✅ Oui | - | - |
| **Sauvegarder exercice** | ❌ Modal PremiumUpsellModal | ✅ Oui | ExerciseGeneratorPage.js:226 | ⚠️ Modal non bloquante |
| **Voir bibliothèque** | ❌ Redirige vers login | ✅ Oui | MyExercisesPage.js:147 | ✅ OK |
| **Dupliquer exercice** | ❌ Nécessite Pro | ✅ Oui | MyExercisesPage.js:241 | ✅ OK |
| **Créer fiche** | ✅ Oui (limité) | ✅ Oui | SheetBuilderPage.js | ⚠️ Limites non claires |
| **Exporter PDF** | ❌ Limité (3/mois) | ✅ Illimité | Backend quota | ⚠️ Pas de feedback clair si quota dépassé |
| **Export Pro (templates)** | ❌ Nécessite Pro | ✅ Oui | ProExportModal.js | ✅ OK |

### Points de friction UX

1. **Sauvegarde exercice (Guest)**:
   - **Fichier**: `ExerciseGeneratorPage.js:226`
   - **Problème**: Modal `PremiumUpsellModal` s'ouvre mais n'est pas bloquante
   - **Impact**: Utilisateur peut fermer la modal et continuer sans comprendre pourquoi il ne peut pas sauvegarder

2. **Export PDF (Guest)**:
   - **Fichier**: `SheetBuilderPage.js:440`
   - **Problème**: Pas de vérification de quota avant export
   - **Impact**: Erreur 429/403 silencieuse ou message générique

3. **Reset après login**:
   - **Fichier**: `ExerciseGeneratorPage.js:190`, `MyExercisesPage.js:135`
   - **Problème**: `loadSavedExercises()` n'est pas appelé après connexion réussie
   - **Impact**: L'utilisateur doit recharger la page manuellement

---

## 3. ANALYSE BACKEND ET CONTRATS

### Endpoints clés

#### POST /api/v1/exercises/generate
- **Fichier**: `backend/routes/exercises_routes.py`
- **Payload**: `{code_officiel, difficulte, seed?, offer?}`
- **Response**: `{id_exercice, enonce_html, solution_html, svg, ...}`
- **✅ Séparation Sujet/Corrigé**: OK (champs séparés)

#### POST /api/user/exercises
- **Fichier**: `backend/server.py:6023`
- **Payload**: `{exercise_uid, enonce_html, solution_html, ...}`
- **Sanitisation**: `sanitize_html()` appliqué sur les deux champs
- **✅ Séparation Sujet/Corrigé**: OK (stockage séparé en DB)

#### POST /api/user/sheets/{sheet_uid}/export-pdf
- **Fichier**: `backend/routes/user_sheets_routes.py:390`
- **Paramètre**: `include_solutions: bool = False`
- **✅ Séparation Sujet/Corrigé**: OK (condition `if include_solutions`)

#### POST /api/mathalea/sheets/{sheetId}/export-standard
- **Fichier**: `backend/routes/mathalea_routes.py` (à vérifier)
- **Response**: `{student_pdf, correction_pdf, base_filename}`
- **✅ Séparation Sujet/Corrigé**: OK (2 PDFs séparés)

### Vérification "Sujet ≠ Corrigé"

| Endpoint | Enonce | Solution | Séparation | Issue |
|----------|--------|----------|------------|-------|
| `/api/v1/exercises/generate` | `enonce_html` | `solution_html` | ✅ OK | - |
| `/api/user/exercises` (save) | `enonce_html` | `solution_html` | ✅ OK | - |
| `/api/user/exercises` (get) | `enonce_html` | `solution_html` | ✅ OK | - |
| `/api/user/sheets/{uid}/export-pdf` | `enonce_html` | `solution_html` (si `include_solutions`) | ✅ OK | - |
| `/api/mathalea/sheets/{id}/export-standard` | `student_pdf` | `correction_pdf` | ✅ OK | - |

**✅ Aucune fuite détectée côté backend**

### Cas potentiels de fuite côté frontend

1. **MyExercisesPage.js - Modal visualisation**:
   - **Ligne 518**: Tabs "Énoncé" / "Solution" avec `showSolution` state
   - **Ligne 129**: `showSolution=false` par défaut (BUG-010)
   - **✅ OK**: Séparation respectée

2. **ExerciseGeneratorPage.js - Affichage exercice**:
   - **Ligne 1353**: `<MathHtmlRenderer html={exercise.enonce_html} />`
   - **Ligne 1392**: `<MathHtmlRenderer html={exercise.solution_html} />`
   - **✅ OK**: Séparation respectée

3. **SheetBuilderPage.js - Export PDF**:
   - **Ligne 468**: `{student_pdf, correction_pdf}` séparés
   - **Ligne 477-479**: Stockage séparé dans `pdfResult`
   - **✅ OK**: Séparation respectée

4. **PdfDownloadModal.js - Téléchargement**:
   - **Ligne 117**: Bouton "version élève" → `student_pdf`
   - **Ligne 127**: Bouton "version corrigée" → `correction_pdf`
   - **✅ OK**: Séparation respectée

**✅ Aucune fuite détectée côté frontend**

---

## 4. LISTE D'ISSUES PRIORISÉES

### P0 - Blocage tunnel ou mélange Sujet/Corrigé

#### P0-1: Reset d'état après login - exercices sauvegardés non rechargés
- **IMPACT**: User/Business - Frustration utilisateur, perte de confiance
- **CAUSE**: `ExerciseGeneratorPage.js:190` - `loadSavedExercises()` appelé uniquement au mount, pas après login
- **FIX PROPOSÉ**: 
  - Écouter les changements de `isPro` et `sessionToken` dans un `useEffect`
  - Appeler `loadSavedExercises()` quand `isPro` passe de `false` à `true`
  - Fichiers: `ExerciseGeneratorPage.js`

#### P0-2: Export PDF - Pas de vérification quota avant appel API
- **IMPACT**: User - Erreur silencieuse ou message générique
- **CAUSE**: `SheetBuilderPage.js:440` - `handleGeneratePDF()` ne vérifie pas le quota
- **FIX PROPOSÉ**:
  - Vérifier le quota avant l'appel API (GET `/api/user/quota` ou similaire)
  - Afficher un message clair si quota dépassé
  - Proposer upgrade si Guest
  - Fichiers: `SheetBuilderPage.js`

#### P0-3: Sauvegarde exercice (Guest) - Modal non bloquante
- **IMPACT**: User - Confusion, utilisateur ne comprend pas pourquoi il ne peut pas sauvegarder
- **CAUSE**: `ExerciseGeneratorPage.js:226` - `PremiumUpsellModal` s'ouvre mais peut être fermée
- **FIX PROPOSÉ**:
  - Rendre la modal bloquante (pas de fermeture facile)
  - Message clair: "Sauvegarde réservée aux utilisateurs Pro"
  - CTA vers pricing
  - Fichiers: `ExerciseGeneratorPage.js`, `PremiumUpsellModal.js`

### P1 - Friction UX importante

#### P1-1: Export PDF - Deux endpoints différents, logique incohérente
- **IMPACT**: Dev/Maintenance - Complexité, bugs potentiels
- **CAUSE**: 
  - `SheetBuilderPage.js:462` utilise `/api/mathalea/sheets/{id}/export-standard`
  - `SheetEditPageP31.js:306` utilise `/api/user/sheets/{uid}/export-pdf?include_solutions={bool}`
- **FIX PROPOSÉ**:
  - Unifier sur un seul endpoint (préférer `/api/user/sheets/{uid}/export-pdf`)
  - Ou documenter clairement quand utiliser chaque endpoint
  - Fichiers: `SheetBuilderPage.js`, `SheetEditPageP31.js`

#### P1-2: Export PDF - Pas de feedback de progression
- **IMPACT**: User - Incertitude pendant la génération
- **CAUSE**: `SheetBuilderPage.js:440` - Pas de loader ou message pendant la génération
- **FIX PROPOSÉ**:
  - Afficher un loader avec message "Génération du PDF en cours..."
  - Désactiver le bouton pendant la génération
  - Fichiers: `SheetBuilderPage.js`

#### P1-3: MyExercisesPage - Duplication exercice ne recharge pas la liste
- **IMPACT**: User - Confusion, l'exercice dupliqué n'apparaît pas immédiatement
- **CAUSE**: `MyExercisesPage.js:265` - `loadExercises()` appelé mais peut échouer silencieusement
- **FIX PROPOSÉ**:
  - Vérifier que `loadExercises()` réussit après duplication
  - Afficher un toast de confirmation
  - Fichiers: `MyExercisesPage.js`

### P2 - Améliorations mineures

#### P2-1: ExerciseGeneratorPage - Bouton "Sauvegarder" reste actif même si déjà sauvegardé
- **IMPACT**: User - Confusion mineure
- **CAUSE**: `ExerciseGeneratorPage.js:1301` - Le bouton est désactivé mais pas assez visible
- **FIX PROPOSÉ**:
  - Améliorer le style du bouton désactivé (icône CheckCircle, texte "Déjà sauvegardé")
  - Fichiers: `ExerciseGeneratorPage.js`

#### P2-2: SheetBuilderPage - Pas de validation avant export PDF
- **IMPACT**: User - Erreur si fiche vide ou mal configurée
- **CAUSE**: `SheetBuilderPage.js:441` - Vérification basique (`sheetItems.length === 0`)
- **FIX PROPOSÉ**:
  - Vérifier que tous les exercices de la fiche existent encore
  - Afficher un message d'erreur clair si des exercices sont manquants
  - Fichiers: `SheetBuilderPage.js`

---

## 5. PLAN DE PATCH

### PR #1: Fix reset état après login + Guards Pro cohérents
**Scope**: P0-1, P0-3  
**Fichiers touchés**:
- `frontend/src/components/ExerciseGeneratorPage.js`
- `frontend/src/components/PremiumUpsellModal.js`

**Changements**:
1. Ajouter `useEffect` dans `ExerciseGeneratorPage.js` pour recharger les exercices sauvegardés après login
2. Rendre `PremiumUpsellModal` bloquante avec message clair
3. Améliorer le CTA vers pricing

**Tests manuels**:
1. En tant que Guest, générer un exercice → cliquer "Sauvegarder" → vérifier que la modal est bloquante
2. Se connecter en Pro → vérifier que les exercices sauvegardés se rechargent automatiquement
3. Vérifier que le bouton "Sauvegarder" devient actif après connexion

---

### PR #2: Fix export PDF - Vérification quota + Feedback
**Scope**: P0-2, P1-2  
**Fichiers touchés**:
- `frontend/src/components/SheetBuilderPage.js`

**Changements**:
1. Ajouter vérification de quota avant export PDF
2. Afficher loader avec message pendant la génération
3. Gérer les erreurs de quota avec message clair

**Tests manuels**:
1. En tant que Guest, créer une fiche → exporter PDF → vérifier que le quota est vérifié
2. Si quota dépassé, vérifier que le message est clair et propose upgrade
3. Vérifier que le loader s'affiche pendant la génération
4. Vérifier que les 2 PDFs (élève + corrigé) sont bien séparés

---

### PR #3: Unification endpoints export PDF
**Scope**: P1-1  
**Fichiers touchés**:
- `frontend/src/components/SheetBuilderPage.js`
- `frontend/src/components/SheetEditPageP31.js` (si existe)

**Changements**:
1. Unifier sur `/api/user/sheets/{uid}/export-pdf?include_solutions={bool}`
2. Adapter la logique pour générer 2 PDFs séparés côté backend si nécessaire
3. Ou documenter clairement l'usage de chaque endpoint

**Tests manuels**:
1. Exporter PDF depuis SheetBuilderPage → vérifier que les 2 PDFs sont générés
2. Exporter PDF depuis SheetEditPage → vérifier cohérence
3. Vérifier que "Sujet ≠ Corrigé" est respecté dans tous les cas

---

### PR #4: Améliorations UX mineures
**Scope**: P1-3, P2-1, P2-2  
**Fichiers touchés**:
- `frontend/src/components/MyExercisesPage.js`
- `frontend/src/components/ExerciseGeneratorPage.js`
- `frontend/src/components/SheetBuilderPage.js`

**Changements**:
1. Améliorer le feedback après duplication d'exercice
2. Améliorer le style du bouton "Sauvegarder" désactivé
3. Ajouter validation avant export PDF (exercices manquants)

**Tests manuels**:
1. Dupliquer un exercice → vérifier que la liste se recharge et affiche le nouvel exercice
2. Vérifier que le bouton "Sauvegarder" désactivé est clairement visible
3. Créer une fiche avec un exercice supprimé → vérifier que l'export affiche un message d'erreur clair

---

### PR #5: Tests E2E parcours complet
**Scope**: Validation finale  
**Fichiers touchés**:
- `backend/tests/test_prof_parcours_e2e.py` (nouveau)
- Documentation

**Changements**:
1. Créer tests E2E pour le parcours complet
2. Vérifier "Sujet ≠ Corrigé" à chaque étape
3. Vérifier les guards Pro

**Tests manuels**:
1. Parcours complet Guest: Générer → Variante → Tentative sauvegarde → Login → Sauvegarde → Bibliothèque → Builder → Export
2. Parcours complet Pro: Générer → Variante → Sauvegarde → Bibliothèque → Builder → Export
3. Vérifier que les PDFs exportés respectent "Sujet ≠ Corrigé"

---

## RÉSUMÉ

### Issues par priorité
- **P0**: 3 issues (blocage tunnel)
- **P1**: 3 issues (friction UX importante)
- **P2**: 2 issues (améliorations mineures)

### Séparation "Sujet ≠ Corrigé"
- **✅ Backend**: Aucune fuite détectée
- **✅ Frontend**: Aucune fuite détectée
- **✅ Export PDF**: Séparation respectée (2 PDFs distincts)

### Plan de patch
- **5 PRs séquentielles** avec scope clair
- **Tests manuels** définis pour chaque PR
- **Pas de refonte globale** - corrections ciblées uniquement



