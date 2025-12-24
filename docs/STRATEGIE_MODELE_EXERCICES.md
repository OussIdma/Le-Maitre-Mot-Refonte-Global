# STRATÉGIE MODÈLE EXERCICES — Recommandation Lead Dev + CPO

**Date** : 2025-12-24  
**Auteur** : Lead Dev + CPO  
**Objectif** : Clarifier définitivement le modèle d'exercices pour simplifier et robustifier le produit

---

## 1. ÉTAT DES LIEUX PRÉCIS

### 1.1 Types d'exercices actuellement en production

| Type | Source | Stockage | Usage | Pipeline | État |
|------|--------|----------|-------|----------|------|
| **Dynamique (Template)** | MongoDB `admin_exercises` | DB | Génération avec variables | TEMPLATE / MIXED | ✅ Production |
| **Statique DB** | MongoDB `admin_exercises` | DB | Exercice figé direct | SPEC / MIXED (fallback) | ✅ Production (migration P3.2) |
| **Legacy Python** | Fichiers Python (`gm07_exercises.py`, etc.) | Fichiers | Exercice figé direct | SPEC (via handlers) | ⚠️ À migrer |
| **Génération pure** | `MathGenerationService` | Aucun (généré à la volée) | Génération algorithmique | SPEC (si `exercise_types` dans curriculum) | ✅ Production |

### 1.2 Flux de génération actuel

```
Requête PROF → POST /api/v1/exercises/generate
    ↓
Détection pipeline (TEMPLATE / SPEC / MIXED)
    ↓
┌─────────────────────────────────────────┐
│ Pipeline TEMPLATE                       │
│ → Cherche exercices dynamiques DB      │
│ → Génère avec variables via Factory    │
└─────────────────────────────────────────┘
    ↓ (si échec ou MIXED)
┌─────────────────────────────────────────┐
│ Pipeline SPEC                           │
│ → Cherche exercices statiques DB       │
│ → OU génère via MathGenerationService   │
│ → OU charge depuis fichiers Python      │
└─────────────────────────────────────────┘
```

### 1.3 Problèmes identifiés

1. **Confusion conceptuelle** : 4 sources différentes pour "un exercice"
2. **Complexité pipeline** : 3 modes (TEMPLATE/SPEC/MIXED) avec fallbacks multiples
3. **Legacy non migré** : Fichiers Python encore utilisés (GM07, GM08)
4. **UI Admin confuse** : Mélange des types dans les onglets
5. **Règle pédagogique** : "Sujet ≠ Corrigé" pas toujours respectée (templates partagés)

---

## 2. ARCHITECTURE CIBLE SIMPLE

### 2.1 Principe directeur

> **"Un exercice = un template dynamique OU un exercice statique figé"**

**Règle pédagogique absolue** : Chaque exercice généré doit avoir un sujet unique et un corrigé unique. Pas de partage de templates entre sujet et corrigé.

### 2.2 Modèle cible (2 types seulement)

#### Type 1 : **EXERCICE DYNAMIQUE** (principal pour les maths)

**Définition** : Template avec variables générant un exercice unique à chaque génération.

**Caractéristiques** :
- `is_dynamic = true`
- `generator_key` présent (ex: `THALES_V1`, `SYMETRIE_AXIALE_V2`)
- `enonce_template_html` : Template avec variables `{{variable}}`
- `solution_template_html` : Template avec variables (peut utiliser les mêmes variables)
- `variables` : Schéma JSON des variables générées
- **Règle** : Chaque génération produit un sujet ET un corrigé uniques (même seed → même exercice)

**Source** : MongoDB `admin_exercises`

**Usage** : 95% des exercices de maths (géométrie, calculs, problèmes)

**Pipeline** : `TEMPLATE` (dynamique uniquement) ou `MIXED` (priorité dynamique)

---

#### Type 2 : **EXERCICE STATIQUE** (fallback / cas spéciaux)

**Définition** : Exercice figé, sans génération de variables.

**Caractéristiques** :
- `is_dynamic = false`
- `generator_key = null`
- `enonce_html` : HTML figé (pas de template)
- `solution_html` : HTML figé
- **Règle** : Toujours le même énoncé et la même solution

**Source** : MongoDB `admin_exercises`

**Usage** : 
- Fallback si aucun dynamique disponible
- Cas spéciaux nécessitant un contenu fixe (ex: exercices de référence)
- Exercices legacy migrés (transition)

**Pipeline** : `SPEC` (statique uniquement) ou `MIXED` (fallback si dynamique échoue)

---

### 2.3 Plan de sortie du legacy

**Phase 1 (P0 - Immédiat)** :
- ✅ Migration P3.2 terminée : 43 exercices legacy → DB (GM07, GM08)
- ✅ Les exercices migrés sont maintenant en DB avec `source="legacy_migration"`

**Phase 2 (P1 - Court terme)** :
- Désactiver le chargement depuis fichiers Python dans `ExercisePersistenceService._load_from_python_file()`
- Vérifier que tous les exercices legacy sont bien en DB
- Supprimer les handlers hardcodés (GM07, GM08) dans `exercises_routes.py`

**Phase 3 (P2 - Moyen terme)** :
- Supprimer les fichiers Python (`gm07_exercises.py`, `gm08_exercises.py`)
- Nettoyer le code legacy dans les handlers

---

## 3. DÉFINITION CLAIRE : PROF vs ADMIN

### 3.1 Ce que voit le PROF (UX finale)

**Interface** : `ExerciseGeneratorPage.js`

**Expérience** :
1. Sélectionne un chapitre dans le catalogue
2. Clique sur "Générer un exercice"
3. Reçoit un exercice unique avec :
   - Énoncé HTML (avec SVG si nécessaire)
   - Solution HTML (avec SVG si nécessaire)
   - PDF téléchargeable

**Ce que le PROF NE VOIT PAS** :
- ❌ Type d'exercice (dynamique vs statique)
- ❌ Source (DB vs legacy)
- ❌ Pipeline utilisé
- ❌ Variables générées
- ❌ Générateur utilisé

**Règle UX** : Le PROF voit un "exercice", point. Pas de distinction technique.

---

### 3.2 Ce que voit l'ADMIN (outils internes)

**Interface** : `ChapterExercisesAdminPage.js`

**Expérience** : 2 onglets distincts

#### Onglet 1 : 🧩 **Générateurs dynamiques**

**Contenu** :
- Liste des exercices avec `is_dynamic = true`
- Affichage : `generator_key`, nombre de variables, aperçu template

**Actions** :
- Créer un générateur : Sélectionner `generator_key`, définir templates énoncé/solution, configurer variables
- Modifier un générateur : Éditer templates, ajuster variables
- Supprimer un générateur

**Champs éditables** :
- `generator_key` (sélection depuis liste)
- `enonce_template_html` (template avec `{{variable}}`)
- `solution_template_html` (template avec `{{variable}}`)
- `variables` (schéma JSON)
- `template_variants` (variants d'énoncés si applicable)
- `difficulty`, `offer` (métadonnées)

**Interdit** : `is_dynamic = false`, champs statiques purs

---

#### Onglet 2 : 📄 **Exercices statiques**

**Contenu** :
- Liste des exercices avec `is_dynamic = false`
- Affichage : Titre, difficulté, aperçu énoncé

**Actions** :
- Créer un exercice statique : Saisir énoncé et solution HTML
- Modifier un exercice statique : Éditer énoncé/solution
- Supprimer un exercice statique
- Verrouiller/déverrouiller (pour les exercices migrés)

**Champs éditables** :
- `title`
- `difficulty`
- `order` (ordre d'affichage)
- `enonce_html` (HTML pur, pas de template)
- `solution_html` (HTML pur)
- `tags` (liste)
- `offer`
- `locked` (booléen)

**Interdit** : `is_dynamic = true`, `generator_key`, `variables`, templates

---

### 3.3 Suppression de l'onglet "Catalogue"

**Décision** : ❌ **Ne pas créer d'onglet "Catalogue" unifié**

**Raison** : 
- Ajoute de la complexité sans valeur
- L'ADMIN doit gérer les types séparément (workflows différents)
- Le PROF voit déjà un catalogue unifié (c'est son interface)

**Alternative** : Si besoin de vue globale, ajouter un badge "Type" dans chaque onglet pour identifier la source.

---

## 4. CHANGEMENTS MINIMAUX (Sans casser l'existant)

### 4.1 P0 — Bloquant (Immédiat)

#### 4.1.1 Simplifier les pipelines

**Action** : Réduire à 2 pipelines seulement

**Avant** :
- `TEMPLATE` : Dynamique uniquement
- `SPEC` : Statique uniquement  
- `MIXED` : Dynamique prioritaire, statique fallback

**Après** :
- `DYNAMIC` : Dynamique uniquement (renommer TEMPLATE)
- `STATIC` : Statique uniquement (renommer SPEC)
- ❌ **Supprimer MIXED** : Remplacer par logique simple "essayer dynamique, si échec → statique"

**Code** :
```python
# Dans exercises_routes.py
if pipeline_mode == "DYNAMIC":
    # Chercher exercices dynamiques uniquement
    exercises = await get_dynamic_exercises(...)
    if not exercises:
        raise HTTPException(422, "Aucun exercice dynamique disponible")
    
elif pipeline_mode == "STATIC":
    # Chercher exercices statiques uniquement
    exercises = await get_static_exercises(...)
    if not exercises:
        raise HTTPException(422, "Aucun exercice statique disponible")
    
else:
    # Pipeline par défaut : essayer dynamique, fallback statique
    exercises = await get_dynamic_exercises(...)
    if not exercises:
        exercises = await get_static_exercises(...)
        if not exercises:
            raise HTTPException(422, "Aucun exercice disponible")
```

**Impact** : Simplifie la logique, réduit les fallbacks multiples

---

#### 4.1.2 Séparer strictement les onglets ADMIN

**Action** : Modifier `ChapterExercisesAdminPage.js`

**Changements** :
1. Supprimer l'onglet "Catalogue" (s'il existe)
2. Garder 2 onglets : "Générateurs" et "Statiques"
3. Filtrer strictement :
   - Générateurs : `is_dynamic === true && generator_key`
   - Statiques : `is_dynamic === false && !isLegacySource()`

**Code** :
```javascript
// Filtrer strictement
const generatorExercises = exercises.filter(ex => 
  ex.is_dynamic === true && ex.generator_key
);

const staticDBExercises = staticExercises.filter(ex => 
  ex.is_dynamic === false && !isLegacySource(ex)
);
```

**Impact** : Plus de confusion, workflows clairs

---

#### 4.1.3 Désactiver le chargement legacy depuis Python

**Action** : Commenter `_load_from_python_file()` dans `ExercisePersistenceService`

**Code** :
```python
async def _load_from_python_file(self, chapter_code: str) -> None:
    """DÉSACTIVÉ : Les exercices legacy sont maintenant en DB (migration P3.2)"""
    # TODO: Supprimer cette méthode après vérification complète
    logger.warning(f"Chargement depuis Python désactivé pour {chapter_code}. Utiliser DB uniquement.")
    return
    # ... code commenté ...
```

**Impact** : Force l'utilisation de la DB, évite la désynchronisation

---

### 4.2 P1 — Important (Court terme)

#### 4.2.1 Ajouter validation "Sujet ≠ Corrigé"

**Action** : Valider que les templates énoncé et solution sont différents

**Code** :
```python
# Dans admin_static_exercises_routes.py et admin_exercises_routes.py
def validate_exercise_templates(enonce_template, solution_template):
    """Valide que l'énoncé et la solution sont différents"""
    if enonce_template == solution_template:
        raise ValueError("L'énoncé et la solution ne peuvent pas être identiques")
    return True
```

**Impact** : Respecte la règle pédagogique

---

#### 4.2.2 Ajouter badge "Legacy" dans ADMIN

**Action** : Afficher un badge pour les exercices migrés

**Code** :
```javascript
{exercise.source === 'legacy_migration' && (
  <Badge variant="outline" className="text-xs">
    📚 Legacy (verrouillé)
  </Badge>
)}
```

**Impact** : Visibilité sur l'origine des exercices

---

#### 4.2.3 Nettoyer les handlers hardcodés

**Action** : Supprimer les intercepts GM07/GM08 dans `exercises_routes.py`

**Code** :
```python
# Supprimer ces lignes :
# if is_gm07_request(request):
#     return generate_gm07_exercise(...)
# if is_gm08_request(request):
#     return generate_gm08_exercise(...)
```

**Impact** : Simplifie le code, utilise uniquement la DB

---

### 4.3 P2 — Nice to have (Moyen terme)

- Supprimer les fichiers Python legacy
- Nettoyer le code obsolète
- Ajouter des tests de non-régression

---

## 5. SCHÉMA MENTAL CLARIFIÉ

### 5.1 Pour le PROF

```
Catalogue → Sélection chapitre → Générer → Exercice unique
```

**Pas de distinction** : Dynamique vs Statique = transparent

---

### 5.2 Pour l'ADMIN

```
ADMIN → Chapitre
    ├─ 🧩 Générateurs (is_dynamic=true)
    │   └─ Créer/Modifier templates avec variables
    │
    └─ 📄 Statiques (is_dynamic=false)
        └─ Créer/Modifier exercices figés
```

**Distinction claire** : 2 workflows séparés, pas de mélange

---

### 5.3 Pour le SYSTÈME

```
Requête → Pipeline
    ├─ DYNAMIC → Cherche dynamiques DB → Génère avec Factory
    ├─ STATIC → Cherche statiques DB → Retourne figé
    └─ AUTO → Essaie dynamique, fallback statique
```

**Logique simple** : 2 types, 3 pipelines (dont 1 auto)

---

## 6. ROADMAP COURTE

### P0 — Bloquant (1-2 jours)

- [ ] Simplifier pipelines : DYNAMIC / STATIC / AUTO
- [ ] Séparer strictement les onglets ADMIN (Générateurs / Statiques)
- [ ] Désactiver chargement legacy depuis Python
- [ ] Tests de non-régression

**Livrable** : Système fonctionnel avec 2 types clairs

---

### P1 — Important (1 semaine)

- [ ] Validation "Sujet ≠ Corrigé"
- [ ] Badge "Legacy" dans ADMIN
- [ ] Nettoyer handlers hardcodés (GM07/GM08)
- [ ] Documentation mise à jour

**Livrable** : Système robuste, règles pédagogiques respectées

---

### P2 — Nice to have (1 mois)

- [ ] Supprimer fichiers Python legacy
- [ ] Nettoyer code obsolète
- [ ] Tests complets

**Livrable** : Code propre, legacy complètement supprimé

---

## 7. RECOMMANDATION TRANCHÉE

### ✅ ADOPTER : Modèle 2 types (Dynamique / Statique)

**Raisons** :
1. **Simplicité** : 2 concepts au lieu de 4
2. **Clarté** : Séparation nette PROF vs ADMIN
3. **Robustesse** : Moins de fallbacks, moins d'erreurs
4. **Maintenabilité** : Code plus simple à comprendre

### ❌ NE PAS ADOPTER : Onglet "Catalogue" unifié

**Raisons** :
1. Ajoute de la complexité sans valeur
2. Mélange des workflows (générateurs vs statiques)
3. Le PROF a déjà son catalogue

### ✅ ADOPTER : Suppression progressive du legacy

**Raisons** :
1. Migration P3.2 terminée (43 exercices en DB)
2. Évite la désynchronisation
3. Simplifie le code

---

## 8. MÉTRIQUES DE SUCCÈS

- ✅ 0 confusion dans l'UI ADMIN (onglets séparés)
- ✅ 0 exercice legacy chargé depuis Python
- ✅ 100% des exercices respectent "Sujet ≠ Corrigé"
- ✅ Temps de génération < 500ms (pas de fallbacks multiples)

---

## CONCLUSION

**Modèle cible** : 2 types (Dynamique / Statique), 2 pipelines (DYNAMIC / STATIC), 2 onglets ADMIN (Générateurs / Statiques).

**Complexité réduite** : De 4 sources à 2 types, de 3 pipelines à 2 (+ auto), de 3 onglets à 2.

**Robustesse** : Moins de fallbacks, règles claires, validation pédagogique.

**Prochaine étape** : Implémenter P0 (1-2 jours) pour valider l'approche.

