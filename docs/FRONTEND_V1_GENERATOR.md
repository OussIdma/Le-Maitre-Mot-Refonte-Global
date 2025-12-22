# Frontend V1 - Générateur d'exercice simplifié

## 📋 Vue d'ensemble

Le **Générateur d'exercice** est une nouvelle interface utilisateur créée pour exploiter l'API V1 `/api/v1/exercises/generate`. Elle offre un moyen simple et rapide de générer 1, 3 ou 5 exercices d'un chapitre spécifique.

---

## 🎯 Objectifs

### Problème résolu

Les enseignants ont deux usages distincts :
1. **Génération rapide** : Créer 1 à 5 exercices pour un DM, des révisions ou préparer un cours
2. **Composition complète** : Créer un contrôle avec plusieurs exercices de différents chapitres

Le générateur V1 répond au **premier besoin** avec une interface épurée et rapide.

### Différence avec le legacy

| Caractéristique | Générateur V1 (`/generate`) | Legacy (`/` - DocumentWizard) |
|-----------------|------------------------------|-------------------------------|
| **API utilisée** | `/api/v1/exercises/generate` | `/api/generate` (legacy) |
| **Nombre d'exercices** | 1, 3 ou 5 | 1 à 10 (configurable) |
| **Interface** | Page unique, simple | Wizard multi-étapes |
| **Pagination** | Oui (1/3, 2/3, 3/3) | Non |
| **Variation** | Oui (par exercice) | Non |
| **Statut** | ✅ Nouvelle architecture | ⚠️ Legacy (à déprécier) |

---

## 🏗️ Architecture technique

### Fichier principal

```
/app/frontend/src/components/ExerciseGeneratorPage.js
```

### Route

```
/generate
```

### Dépendances

- **React** : 18.x
- **axios** : Appels API
- **Shadcn UI** : Composants UI (Button, Card, Select, Badge, Alert)
- **Lucide React** : Icônes

### API utilisée

```
POST /api/v1/exercises/generate
```

**Paramètres** :
```json
{
  "niveau": "5e",
  "chapitre": "Symétrie centrale",
  "difficulte": "moyen",
  "seed": 1702401234
}
```

**Réponse** :
```json
{
  "id_exercice": "ex_5e_symetrie-centrale_1702401234",
  "niveau": "5e",
  "chapitre": "Symétrie centrale",
  "enonce_html": "<div>...</div>",
  "svg": "<svg>...</svg>",
  "solution_html": "<div>...</div>",
  "pdf_token": "ex_5e_symetrie-centrale_1702401234",
  "metadata": {
    "difficulte": "moyen",
    "duree_estimee": 5,
    "points": 2.0
  }
}
```

---

## 🎨 Interface utilisateur

### Section 1 : Formulaire de configuration

**Composants** :
- **Sélecteur de niveau** : Dropdown (CP, CE1, 6e, 5e, etc.)
- **Sélecteur de chapitre** : Dropdown (dépendant du niveau)
- **Nombre d'exercices** : Select (1, 3 ou 5)
- **Bouton Générer** : Déclenche la génération

**Comportement** :
1. L'utilisateur sélectionne un niveau
2. Les chapitres se chargent automatiquement
3. L'utilisateur choisit un chapitre et le nombre d'exercices
4. Clic sur "Générer" → Appels API parallèles

### Section 2 : Affichage des exercices

**Pagination** :
- Badge "Exercice 1/3" au centre
- Boutons de navigation (◀ et ▶)

**Contenu** :
- **Badges** : Niveau, Chapitre, Difficulté
- **Énoncé** : HTML rendu avec `dangerouslySetInnerHTML`
- **Figure SVG** : Si disponible (exercices géométriques)
- **Solution** : Repliable avec `<details>`

**Actions** :
- **Variation** : Regénère uniquement l'exercice actuel avec un nouveau seed
- **PDF** : Export PDF (fonctionnalité placeholder en V1)

---

## 🔄 Comportement détaillé

### 1. Chargement initial

```javascript
useEffect(() => {
  fetchCurriculumData();
}, []);
```

**Action** :
- Appel à `/api/v1/exercises/health`
- Récupération des niveaux disponibles
- Stockage dans `state.niveaux`

### 2. Sélection du niveau

```javascript
useEffect(() => {
  if (selectedNiveau) {
    fetchChapitres(selectedNiveau);
    setSelectedChapitre(""); // Reset
  }
}, [selectedNiveau]);
```

**Action** :
- Appel à `/api/catalog` (API legacy pour récupérer les chapitres)
- Filtrage par niveau
- Stockage dans `state.chapitres`

### 3. Génération des exercices

```javascript
const generateExercises = async () => {
  const promises = [];
  for (let i = 0; i < nbExercices; i++) {
    const seed = Date.now() + i;
    promises.push(axios.post(`${API_V1}/generate`, {
      niveau, chapitre, difficulte: "moyen", seed
    }));
  }
  
  const responses = await Promise.all(promises);
  setExercises(responses.map(r => r.data));
};
```

**Action** :
- Création de N promesses (N = 1, 3 ou 5)
- Exécution en parallèle avec `Promise.all()`
- Seed différent pour chaque exercice (`Date.now() + i`)
- Stockage des résultats dans `state.exercises`

### 4. Pagination

```javascript
const goToNext = () => {
  if (currentIndex < exercises.length - 1) {
    setCurrentIndex(currentIndex + 1);
  }
};
```

**Action** :
- Navigation avec `state.currentIndex`
- Boutons désactivés aux extrémités

### 5. Variation d'un exercice

```javascript
const generateVariation = async (index) => {
  const seed = Date.now() + Math.random() * 1000;
  const response = await axios.post(`${API_V1}/generate`, {
    niveau, chapitre, difficulte: "moyen", seed
  });
  
  const newExercises = [...exercises];
  newExercises[index] = response.data;
  setExercises(newExercises);
};
```

**Action** :
- Nouvel appel API avec seed aléatoire
- Remplacement de l'exercice à l'index spécifié
- Pas de navigation automatique (reste sur l'exercice varié)

---

## 📊 États React

| État | Type | Description |
|------|------|-------------|
| `niveaux` | `string[]` | Liste des niveaux disponibles |
| `chapitres` | `string[]` | Liste des chapitres du niveau sélectionné |
| `selectedNiveau` | `string` | Niveau actuellement sélectionné |
| `selectedChapitre` | `string` | Chapitre actuellement sélectionné |
| `nbExercices` | `number` | Nombre d'exercices à générer (1, 3 ou 5) |
| `loading` | `boolean` | Chargement de la génération |
| `error` | `string \| null` | Message d'erreur |
| `exercises` | `object[]` | Exercices générés |
| `currentIndex` | `number` | Index de l'exercice affiché (pagination) |
| `loadingVariation` | `boolean` | Chargement de la variation |

---

## 🔌 Appels API

### 1. Health check (chargement des niveaux)

```http
GET /api/v1/exercises/health
```

**Utilisation** : Au chargement de la page

**Réponse** :
```json
{
  "status": "healthy",
  "service": "exercises_v1",
  "curriculum": {
    "total_niveaux": 9,
    "niveaux": ["CP", "CE1", "6e", "5e", ...],
    "total_chapitres": 127
  }
}
```

### 2. Catalog (chargement des chapitres)

```http
GET /api/catalog
```

**Utilisation** : Quand un niveau est sélectionné

**Réponse** :
```json
{
  "catalog": [
    {
      "name": "Mathématiques",
      "levels": [
        {
          "name": "5e",
          "chapters": ["Symétrie centrale", "Triangles", ...]
        }
      ]
    }
  ]
}
```

### 3. Génération d'exercice

```http
POST /api/v1/exercises/generate
```

**Utilisation** : 
- Génération initiale (N appels parallèles)
- Variation d'un exercice (1 appel)

**Body** :
```json
{
  "niveau": "5e",
  "chapitre": "Symétrie centrale",
  "difficulte": "moyen",
  "seed": 1702401234
}
```

---

## 🎯 Gestion des erreurs

### Erreur 422 : Niveau ou chapitre invalide

```javascript
if (error.response?.status === 422) {
  const detail = error.response.data.detail;
  setError(detail.message);
}
```

**Affichage** : Alert rouge avec message pédagogique

### Erreur 500 : Erreur serveur

```javascript
setError("Erreur lors de la génération des exercices");
```

**Affichage** : Alert rouge générique

### Erreur réseau

```javascript
setError("Impossible de communiquer avec le serveur");
```

---

## 🧪 Tests manuels

### Test 1 : Génération simple (1 exercice)

1. Accéder à `/generate`
2. Sélectionner "5e" → "Symétrie centrale"
3. Nombre : 1
4. Cliquer "Générer"

**Résultat attendu** :
- ✅ 1 exercice affiché
- ✅ Énoncé HTML visible
- ✅ SVG de symétrie visible
- ✅ Solution repliable

### Test 2 : Génération multiple (3 exercices)

1. Sélectionner "6e" → "Fractions"
2. Nombre : 3
3. Cliquer "Générer"

**Résultat attendu** :
- ✅ Badge "Exercice 1/3"
- ✅ Navigation avec ◀ ▶
- ✅ 3 exercices différents

### Test 3 : Variation

1. Générer 1 exercice
2. Cliquer "Variation"

**Résultat attendu** :
- ✅ Nouvel exercice similaire mais différent
- ✅ Même chapitre, même niveau
- ✅ Valeurs numériques différentes

### Test 4 : Erreur niveau invalide

1. Modifier le code pour forcer un niveau invalide
2. Générer

**Résultat attendu** :
- ✅ Alert rouge
- ✅ Message : "Le niveau 'xxx' n'est pas reconnu..."

---

## 🚀 Déploiement et intégration

### Étapes d'intégration

1. ✅ **Créer le composant** : `ExerciseGeneratorPage.js`
2. ✅ **Ajouter l'import** dans `App.js`
3. ✅ **Ajouter la route** : `/generate`
4. ⏳ **Tester en local**
5. ⏳ **Tests utilisateurs**
6. ⏳ **Migration progressive** : Faire de `/generate` la nouvelle home
7. ⏳ **Dépréciation** : Marquer `/` (DocumentWizard) comme legacy

### Pas d'impact sur l'existant

✅ **Aucune modification** de :
- Page d'accueil `/` (DocumentWizard)
- SheetBuilder `/builder`
- APIs legacy `/api/generate`
- Base de données

✅ **Architecture isolée** :
- Nouveau composant séparé
- Nouvelle route séparée
- Utilise uniquement l'API V1

---

## 📝 Évolutions futures (V2)

### Priorité 1 : Export PDF fonctionnel

**Problème actuel** : Le bouton "PDF" affiche un placeholder

**Solution** :
- Implémenter `/api/v1/exercises/{id}/pdf`
- Générer un PDF côté backend
- Téléchargement direct

### Priorité 2 : Ajout à ma collection

**Objectif** : Permettre de sauvegarder des exercices favoris

**Implémentation** :
- Bouton "Ajouter à ma collection"
- Stockage en DB (table `user_exercises`)
- Page `/my-exercises` pour voir la collection

### Priorité 3 : Personnalisation

**Fonctionnalités** :
- Choix de la difficulté (facile/moyen/difficile)
- Choix du type d'exercice (standard/avancé/simplifié)
- Paramètres avancés (points, durée estimée)

### Priorité 4 : Export multi-exercices

**Objectif** : Exporter les 3 ou 5 exercices en un seul PDF

**Implémentation** :
- Nouveau bouton "Exporter tout en PDF"
- Compilation backend de tous les exercices

---

## 🔗 Liens utiles

- **Spécification API V1** : `/app/docs/API_EXERCISES.md`
- **Backend V1** : `/app/backend/routes/exercises_routes.py`
- **Tests backend** : `/app/backend/tests/test_api_exercises.py`
- **Composant React** : `/app/frontend/src/components/ExerciseGeneratorPage.js`

---

## ✅ Checklist de validation

- [x] Composant créé et fonctionnel
- [x] Route `/generate` intégrée dans App.js
- [x] Appels API V1 fonctionnels
- [x] Génération 1/3/5 exercices OK
- [x] Pagination fluide
- [x] Variation d'exercice OK
- [ ] Tests manuels complets
- [ ] Export PDF fonctionnel (V2)
- [ ] Tests utilisateurs
- [ ] Documentation complète

---

**Auteur** : E1 Agent (Emergent AI)  
**Date** : 2024-12-10  
**Version** : 1.0 (Frontend V1)
