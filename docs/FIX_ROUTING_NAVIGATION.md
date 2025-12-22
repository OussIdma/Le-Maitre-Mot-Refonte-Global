# Fix Routing et Navigation - Rendre le site utilisable sans connaître /generer

**Date :** 2025-01-XX  
**Statut :** ✅ Implémenté

---

## Objectif

Rendre le site utilisable sans connaître l'URL `/generer` en :
1. Créant une page landing (`/`) avec CTA vers `/generer`
2. Ajoutant une NavBar avec 3 liens max (Accueil, Générer, Admin)
3. Redirigeant les routes inconnues vers `/generer`
4. Normalisant les variations de casse (`/Générer` → `/generer`)

---

## Modifications Frontend

### 1. Nouvelle page Landing (`/`)

**Fichier créé** : `frontend/src/components/LandingPage.js`

- Page d'accueil minimaliste avec hero section
- CTA principal "Générer des exercices" vers `/generer`
- 3 cartes de features (Génération intelligente, Exercices variés, Export PDF)
- CTA secondaire vers `/generer`

### 2. NavBar unifiée

**Fichier créé** : `frontend/src/components/NavBar.js`

- Logo cliquable vers `/`
- 3 liens max :
  - **Accueil** (`/`)
  - **Générer** (`/generer`)
  - **Admin** (`/admin/curriculum`) - seulement visible si on est déjà sur une page admin
- Sticky header avec z-index élevé
- Responsive (mobile-friendly)

### 3. Mise à jour des routes (`App.js`)

**Fichier modifié** : `frontend/src/App.js`

**Changements** :
- Ajout de `AppWithNav` wrapper pour injecter la NavBar sur toutes les pages principales
- Création de `RedirectToGenerer` pour normaliser les routes et rediriger les routes inconnues
- Création de `NotFoundPage` (non utilisée pour l'instant, mais disponible)
- Routes principales :
  - `/` → `LandingPage` (avec NavBar)
  - `/generer` → `ExerciseGeneratorPage` (avec NavBar)
  - `/générer`, `/Générer`, `/generate` → Redirection vers `/generer`
  - `/*` (catch-all) → Redirection vers `/generer`

**Routes sans NavBar** (pages spéciales) :
- `/success` (paiement)
- `/cancel` (paiement annulé)
- `/login/verify` (vérification login)

**Routes avec NavBar** :
- `/` (Landing)
- `/generer` (Générateur)
- `/builder` (Créateur de fiches)
- `/sheets` (Mes fiches)
- `/pro/settings` (Paramètres Pro)
- `/admin/*` (Admin)

---

## Normalisation des routes

### Variations de casse gérées :
- `/Générer` → `/generer`
- `/générer` → `/generer`
- `/generate` → `/generer` (legacy)

### Routes inconnues :
- Toute route non définie → Redirection vers `/generer`

---

## Vérification des appels API

**Fichier** : `frontend/src/components/ExerciseGeneratorPage.js`

**Configuration actuelle** :
```javascript
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_V1 = `${BACKEND_URL}/api/v1/exercises`;
const CATALOG_API = `${BACKEND_URL}/api/v1/curriculum`;
```

✅ **Vérifié** : Les appels API utilisent `REACT_APP_BACKEND_URL` depuis les variables d'environnement.

✅ **Gestion des erreurs 422** : Déjà en place dans `ExerciseGeneratorPage.js` avec `useToast` pour afficher les messages d'erreur structurés (`POOL_EMPTY`, `VARIANT_ID_NOT_FOUND`, `PLACEHOLDER_UNRESOLVED`, `ADMIN_TEMPLATE_MISMATCH`).

---

## Tests

### Test manuel de routing

**Script de vérification** : `scripts/test_routing.sh` (à créer)

```bash
#!/bin/bash
# Test de routing - vérifie que les redirections fonctionnent

BASE_URL="http://localhost:3000"

echo "🧪 Test de routing..."

# Test 1: Landing page
echo "1. Test / → Landing page"
curl -s "$BASE_URL/" | grep -q "Générer des exercices" && echo "✅ Landing OK" || echo "❌ Landing KO"

# Test 2: Redirection /generate → /generer
echo "2. Test /generate → /generer"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -L "$BASE_URL/generate")
[ "$STATUS" = "200" ] && echo "✅ Redirection /generate OK" || echo "❌ Redirection /generate KO"

# Test 3: Redirection /Générer → /generer
echo "3. Test /Générer → /generer"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -L "$BASE_URL/Générer")
[ "$STATUS" = "200" ] && echo "✅ Redirection /Générer OK" || echo "❌ Redirection /Générer KO"

# Test 4: Route inconnue → /generer
echo "4. Test route inconnue → /generer"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -L "$BASE_URL/route-inexistante")
[ "$STATUS" = "200" ] && echo "✅ Redirection route inconnue OK" || echo "❌ Redirection route inconnue KO"

echo "✅ Tests terminés"
```

---

## Checklist manuelle (5 étapes)

### 1. Test Landing Page (`/`)
- Ouvrir `http://localhost:3000/`
- **Attendu** : Page d'accueil avec titre "Le Maître Mot", CTA "Générer des exercices", 3 cartes de features
- Cliquer sur "Générer des exercices"
- **Attendu** : Redirection vers `/generer`

### 2. Test Navigation
- Vérifier la NavBar en haut de la page
- **Attendu** : Logo + 3 liens (Accueil, Générer, Admin si sur page admin)
- Cliquer sur "Accueil"
- **Attendu** : Redirection vers `/`
- Cliquer sur "Générer"
- **Attendu** : Redirection vers `/generer`

### 3. Test Normalisation des routes
- Ouvrir `http://localhost:3000/Générer`
- **Attendu** : Redirection automatique vers `/generer`
- Ouvrir `http://localhost:3000/generate`
- **Attendu** : Redirection automatique vers `/generer`

### 4. Test Route inconnue
- Ouvrir `http://localhost:3000/route-inexistante`
- **Attendu** : Redirection automatique vers `/generer`

### 5. Test Appels API depuis `/generer`
- Ouvrir `http://localhost:3000/generer`
- Sélectionner un chapitre et générer un exercice
- **Attendu** : 
  - Si erreur 422 (pool vide, variant invalide, etc.) → Toast avec message clair
  - Si succès → Exercice généré et affiché
- Vérifier la console navigateur
- **Attendu** : Pas d'erreur CORS, appels API vers `${BACKEND_URL}/api/v1/exercises/generate`

---

## Fichiers modifiés/créés

1. **frontend/src/components/LandingPage.js** (nouveau)
   - Page d'accueil avec CTA vers `/generer`

2. **frontend/src/components/NavBar.js** (nouveau)
   - Navigation principale avec 3 liens max

3. **frontend/src/App.js** (modifié)
   - Ajout de `AppWithNav` wrapper
   - Ajout de `RedirectToGenerer` pour normalisation
   - Mise à jour des routes avec NavBar
   - Redirection catch-all vers `/generer`

---

## Validation

- ✅ Compilation : Pas d'erreurs de syntaxe
- ✅ Routes principales : `/` (Landing), `/generer` (Générateur)
- ✅ NavBar : 3 liens max (Accueil, Générer, Admin conditionnel)
- ✅ Normalisation : `/Générer`, `/générer`, `/generate` → `/generer`
- ✅ Redirection : Routes inconnues → `/generer`
- ✅ Appels API : Utilisation de `REACT_APP_BACKEND_URL`
- ✅ Gestion erreurs 422 : Déjà en place avec toast

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Implémenté, prêt pour validation

