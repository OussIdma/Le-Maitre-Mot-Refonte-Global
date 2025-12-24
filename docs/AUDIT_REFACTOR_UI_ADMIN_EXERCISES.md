# AUDIT & REFACTOR UI ADMIN EXERCICES

## Phase A — AUDIT (État des lieux)

### 1. Sources de données actuelles

#### Onglet "Dynamiques" (activeTab='dynamiques')

**API appelée :**
- `GET /api/admin/chapters/{chapterCode}/exercises`
- Route backend : `backend/routes/admin_exercises_routes.py::list_exercises()`
- Service : `ExercisePersistenceService.get_exercises()`
- Collection MongoDB : `admin_exercises`

**Filtrage côté backend :**
- `chapter_code` (normalisé en uppercase)
- `offer` (optionnel)
- `difficulty` (optionnel)
- **Aucun filtre sur `is_dynamic`** → retourne TOUS les exercices (statiques + dynamiques)

**Filtrage côté frontend :**
- Aucun filtre explicite sur `is_dynamic`
- Affichage de TOUS les exercices retournés par l'API
- Le badge "Pipeline / Usage" indique si l'exercice est dynamique ou statique, mais les deux types sont mélangés

**Types d'exercices affichés :**
- ✅ Exercices dynamiques (`is_dynamic=True`, `generator_key` présent)
- ❌ **PROBLÈME** : Affiche aussi les exercices statiques DB (`is_dynamic=False`)
- ❌ **PROBLÈME** : Affiche aussi les exercices legacy/pseudo-statiques (chargés depuis fichiers Python)

**Champs éditables (modal "Modifier") :**
- Tous les champs (titre, famille, type, difficulté, offre, énoncé, solution, SVG, etc.)
- Champs dynamiques : `generator_key`, `variables`, `template_variants`
- **PROBLÈME** : Le même formulaire sert pour statiques ET dynamiques → confusion

---

#### Onglet "Statiques" (activeTab='statiques')

**API appelée :**
- `GET /api/v1/admin/chapters/{chapterCode}/static-exercises`
- Route backend : `backend/routes/admin_static_exercises_routes.py::list_static_exercises_by_chapter()`
- Service : `ExercisePersistenceService.get_exercises()` puis filtre `is_dynamic is not True`
- Collection MongoDB : `admin_exercises` (même collection que Dynamiques)

**Filtrage côté backend :**
- `chapter_code` (normalisé en uppercase)
- Filtre : `is_dynamic is not True` (inclut `False`, `None`, absent)

**Types d'exercices affichés :**
- ✅ Exercices statiques DB (`is_dynamic=False`, `source="legacy_migration"` ou autre)
- ✅ Exercices legacy/pseudo-statiques (chargés depuis fichiers Python via `_load_from_python_file()`)
- ❌ **PROBLÈME** : Ne distingue pas les statiques DB des legacy

**Champs éditables (modal "Modifier") :**
- Formulaire simplifié : `title`, `difficulty`, `enonce_html`, `solution_html`, `tags`, `order`, `offer`
- **PROBLÈME** : Si l'exercice est legacy (chargé depuis Python), la modification ne persiste pas (écrasée au prochain chargement)

---

### 2. Tableau récapitulatif des problèmes

| Onglet actuel | Source API | Type réel | Champs éditables | Problèmes identifiés |
|---------------|------------|-----------|------------------|---------------------|
| **Dynamiques** | `/api/admin/chapters/{code}/exercises` | Mélange :<br/>- GENERATOR (is_dynamic=True)<br/>- STATIC_DB (is_dynamic=False)<br/>- CATALOG_LEGACY (chargé depuis Python) | Formulaire complexe (tous champs) | ❌ Double affichage (statiques apparaissent aussi dans Statiques)<br/>❌ Formulaire inadapté pour statiques<br/>❌ Pas de distinction visuelle claire |
| **Statiques** | `/api/v1/admin/chapters/{code}/static-exercises` | Mélange :<br/>- STATIC_DB (is_dynamic=False, en DB)<br/>- CATALOG_LEGACY (chargé depuis Python) | Formulaire simplifié | ❌ Pas de distinction legacy vs DB<br/>❌ Modifications legacy non persistantes<br/>❌ Pas de badge visuel pour identifier la source |

---

### 3. Types d'exercices identifiés

#### Type 1 : GENERATOR (Générateur dynamique)
- **Critères** : `is_dynamic=True`, `generator_key` présent
- **Source** : Collection `admin_exercises` (MongoDB)
- **Usage** : Génération via templates avec variables
- **Édition** : Paramètres générateur, templates DB, variables

#### Type 2 : STATIC_DB (Exercice statique en DB)
- **Critères** : `is_dynamic=False`, présent en MongoDB, `source` peut être `"legacy_migration"` ou autre
- **Source** : Collection `admin_exercises` (MongoDB)
- **Usage** : Exercice figé, consommable directement
- **Édition** : Titre, difficulté, ordre, énoncé, solution, tags, locked

#### Type 3 : CATALOG_LEGACY (Exercice legacy/pseudo-statique)
- **Critères** : `is_dynamic=False`, chargé depuis fichier Python (`gm07_exercises.py`, etc.)
- **Source** : Fichiers Python dans `backend/data/`
- **Usage** : Exercice figé, consommable directement (via `ExercisePersistenceService._load_from_python_file()`)
- **Édition** : ❌ Non éditable directement (écrasé au prochain chargement)
- **Note** : Ces exercices sont maintenant aussi en DB (migration P3.2), mais peuvent encore être chargés depuis Python

---

## Phase B — SPÉCIFICATION UI CIBLE

### 1. Nouvelle architecture UI

#### 3 onglets distincts

**📚 Catalogue** (nouveau)
- **Objectif** : Vue unifiée de TOUS les exercices consommables (statiques DB + legacy + dynamiques)
- **Badge** : 📚
- **Contenu** : Liste unifiée avec badges visuels pour distinguer les types
- **Actions** : Consultation, prévisualisation, duplication vers statique DB (si legacy)

**🧩 Générateurs**
- **Objectif** : Gestion des générateurs dynamiques uniquement
- **Badge** : 🧩
- **Contenu** : Liste des exercices avec `is_dynamic=True` + `generator_key`
- **Actions** : CRUD générateurs, paramètres, templates DB

**📄 Statiques DB**
- **Objectif** : CRUD des exercices statiques en MongoDB uniquement
- **Badge** : 📄
- **Contenu** : Liste des exercices avec `is_dynamic=False` ET présents en DB (pas legacy)
- **Actions** : CRUD complet (créer, modifier, supprimer, verrouiller)

---

### 2. Champs éditables par type

#### GENERATOR (🧩 Générateurs)
- `generator_key` (sélection depuis liste)
- `variables` (schéma JSON)
- `enonce_template_html` (template avec variables)
- `solution_template_html` (template avec variables)
- `template_variants` (variants d'énoncés)
- `difficulty`, `offer` (métadonnées)
- **Interdit** : `is_dynamic=False`, champs statiques purs

#### STATIC_DB (📄 Statiques DB)
- `title`
- `difficulty`
- `order`
- `enonce_html` (HTML pur, pas de template)
- `solution_html` (HTML pur)
- `tags` (liste)
- `offer`
- `locked` (booléen)
- **Interdit** : `is_dynamic=True`, `generator_key`, `variables`, templates

#### CATALOG_LEGACY (📚 Catalogue uniquement)
- ❌ **Non éditable directement**
- Actions possibles :
  - "Dupliquer vers Statique DB" (crée une copie éditable)
  - "Prévisualiser"
  - "Voir source" (affiche le fichier Python source)

---

### 3. Décisions P0 (bloquantes)

1. **Séparation stricte des onglets**
   - Aucun exercice STATIC_DB ne doit apparaître dans Générateurs
   - Aucun GENERATOR ne doit apparaître dans Statiques DB
   - Catalogue est la seule vue unifiée

2. **Détection du type d'exercice**
   - Fonction `getExerciseType(exercise)` qui retourne `'GENERATOR' | 'STATIC_DB' | 'CATALOG_LEGACY'`
   - Critères :
     - `GENERATOR` : `is_dynamic === true && generator_key`
     - `STATIC_DB` : `is_dynamic === false && !isLegacySource(exercise)`
     - `CATALOG_LEGACY` : `is_dynamic === false && isLegacySource(exercise)`

3. **Formulaires séparés**
   - Modal "Modifier générateur" : formulaire spécifique générateurs
   - Modal "Modifier statique" : formulaire spécifique statiques
   - Pas de formulaire pour legacy (actions limitées)

4. **Badges visuels**
   - Chaque exercice affiche un badge selon son type
   - Couleurs distinctes : 🧩 bleu, 📄 vert, 📚 orange

---

### 4. Décisions P1 (nice to have)

1. **Section Debug (dev only)**
   - Badge "DEV" repliable
   - Affiche : `item_type`, `source`, `is_dynamic`, `generator_key`, `chapter_code`

2. **Actions contextuelles**
   - "Dupliquer vers Statique DB" pour legacy
   - "Convertir en générateur" pour statiques (si applicable)

3. **Filtres avancés**
   - Filtre par type dans Catalogue
   - Filtre par générateur dans Générateurs

---

## Phase C — IMPLÉMENTATION

### Structure du code

```javascript
// Fonction de détection du type
function getExerciseType(exercise) {
  if (exercise.is_dynamic === true && exercise.generator_key) {
    return 'GENERATOR';
  }
  if (exercise.is_dynamic === false) {
    // Vérifier si legacy (source depuis Python)
    if (exercise.source === 'legacy_migration' || exercise.legacy_ref) {
      return 'CATALOG_LEGACY';
    }
    return 'STATIC_DB';
  }
  return 'UNKNOWN';
}

// Filtrage par type
const generators = exercises.filter(ex => getExerciseType(ex) === 'GENERATOR');
const staticDB = exercises.filter(ex => getExerciseType(ex) === 'STATIC_DB');
const catalogLegacy = exercises.filter(ex => getExerciseType(ex) === 'CATALOG_LEGACY');
```

### Modifications à apporter

1. **Ajouter l'onglet Catalogue**
   - Nouveau `TabsTrigger` et `TabsContent`
   - Affichage unifié avec badges

2. **Séparer les onglets Générateurs et Statiques**
   - Générateurs : filtrer `is_dynamic === true`
   - Statiques : filtrer `is_dynamic === false && !isLegacySource()`

3. **Créer des modals séparés**
   - `GeneratorEditModal` : formulaire générateurs
   - `StaticEditModal` : formulaire statiques (existant, à adapter)

4. **Ajouter la section Debug**
   - Badge "DEV" repliable
   - Affichage conditionnel : `process.env.NODE_ENV === 'development'`

---

## Phase D — VALIDATION (Checklist)

### GM07 (22 statiques migrés)

- [ ] **Statiques DB** : 22 exercices visibles uniquement dans "📄 Statiques DB" et "📚 Catalogue"
- [ ] **Générateurs** : Aucun exercice statique n'apparaît dans "🧩 Générateurs"
- [ ] **Modifier statique** : Le modal affiche uniquement les champs statiques (pas de `generator_key`)
- [ ] **Badges** : Chaque exercice affiche le bon badge (📄 pour statiques DB)

### Générateurs

- [ ] **Liste** : Seuls les exercices avec `is_dynamic=true` et `generator_key` apparaissent
- [ ] **Modifier générateur** : Le modal affiche uniquement les champs générateurs (pas de champs statiques purs)
- [ ] **Templates DB** : Les templates sont éditables et liés au générateur

### Catalogue

- [ ] **Vue unifiée** : Tous les exercices (statiques DB + legacy + générateurs) sont visibles
- [ ] **Badges** : Chaque type a son badge distinct (🧩/📄/📚)
- [ ] **Actions** : Les actions sont adaptées au type (éditer pour DB/générateurs, dupliquer pour legacy)

### Debug (dev only)

- [ ] **Section visible** : Uniquement en mode développement
- [ ] **Informations** : Affiche `item_type`, `source`, `is_dynamic`, etc.

---

## Notes techniques

### API endpoints utilisés

1. **Catalogue** : `GET /api/admin/chapters/{code}/exercises` (tous les exercices)
2. **Générateurs** : `GET /api/admin/chapters/{code}/exercises` + filtre frontend `is_dynamic=true`
3. **Statiques DB** : `GET /api/v1/admin/chapters/{code}/static-exercises` (déjà filtré backend)

### Détection legacy

Un exercice est considéré comme legacy si :
- `source === 'legacy_migration'` OU
- `legacy_ref` est présent (format : `"gm07_exercises.py:id=1"`)

### Normalisation des codes

- Les codes de chapitres sont normalisés en uppercase (`6E_GM07`)
- Le frontend doit utiliser le même format que le backend

---

## Prochaines étapes

1. ✅ Audit terminé
2. ⏳ Implémentation Phase C
3. ⏳ Validation Phase D
4. ⏳ Tests manuels

