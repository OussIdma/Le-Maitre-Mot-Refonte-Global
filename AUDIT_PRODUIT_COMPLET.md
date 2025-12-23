# 🔍 AUDIT PRODUIT COMPLET - Le Maître Mot
**Date**: 2024-12-19  
**Mode**: Analyse statique + trace logique  
**Périmètre**: Frontend (`frontend/src`), Backend (`backend`), Routes API

---

## 1️⃣ CARTE DU PRODUIT

### 1.1 Routes Frontend (React Router)

| Route | Composant | Auth Requise | Description |
|-------|-----------|--------------|-------------|
| `/` | `LandingPage` | Non | Page d'accueil |
| `/generer` | `ExerciseGeneratorPage` | Non (Pro pour sauvegarde) | Générateur d'exercices |
| `/mes-exercices` | `MyExercisesPage` | **Oui (Pro)** | Bibliothèque d'exercices sauvegardés |
| `/builder` | `SheetBuilderPage` | Non (Pro pour certaines features) | Créateur de fiches |
| `/builder/:sheetId` | `SheetBuilderPage` | Non | Édition de fiche existante |
| `/sheets` | `MySheetsPage` | Non | Liste des fiches |
| `/pro/settings` | `ProSettingsPage` | **Oui (Pro)** | Paramètres Pro |
| `/pricing` | `PricingPage` | Non | Page tarifs |
| `/checkout` | `CheckoutPage` | Non | Paiement Stripe |
| `/success` | `PaymentSuccess` | Non | Confirmation paiement |
| `/cancel` | `PaymentCancel` | Non | Annulation paiement |
| `/login/verify` | `LoginVerify` | Non | Vérification magic link |
| `/reset-password` | `ResetPasswordPage` | Non | Réinitialisation mot de passe |
| `/admin/curriculum` | `CurriculumAdminSimplePage` | Admin | Admin curriculum |
| `/admin/templates` | `GeneratorTemplatesAdminPage` | Admin | Admin templates |

### 1.2 Composants Clés + États

#### `ExerciseGeneratorPage` (`/generer`)
- **États**: `catalog`, `selectedGrade`, `selectedItem`, `exercises`, `isPro`, `savedExercises`
- **API**: 
  - `GET /api/v1/curriculum/{grade}/catalog`
  - `POST /api/v1/exercises/generate`
  - `POST /api/v1/exercises/generate/batch/gm07`
  - `POST /api/v1/exercises/generate/batch/gm08`
  - `GET /api/user/exercises` (Pro)
  - `POST /api/user/exercises` (Pro)

#### `MyExercisesPage` (`/mes-exercices`)
- **États**: `exercises`, `loading`, `userEmail`, `isPro`, `sessionToken`, `filterCodeOfficiel`, `filterDifficulty`
- **API**:
  - `GET /api/user/exercises?code_officiel=...&difficulty=...`
  - `DELETE /api/user/exercises/{exercise_uid}`
  - `POST /api/user/exercises` (duplication)

#### `SheetBuilderPage` (`/builder`)
- **États**: `sheetItems`, `sheetTitle`, `sheetId`, `isPro`, `sessionToken`
- **API**:
  - `GET /api/mathalea/sheets/{sheetId}`
  - `POST /api/mathalea/sheets`
  - `PUT /api/mathalea/sheets/{sheetId}`
  - `GET /api/v1/curriculum/{level}/catalog`
  - `POST /api/v1/exercises/generate`

#### `GlobalLoginModal` (Contexte global)
- **États**: `showLoginModal`, `loginEmail`, `loginPassword`, `loginTab`, `loginEmailSent`
- **API**:
  - `POST /api/auth/request-login`
  - `POST /api/auth/login-password`

### 1.3 Endpoints Backend (FastAPI)

#### Auth (`/api/auth/*`)
- `POST /api/auth/request-login` - Magic link request
- `POST /api/auth/verify-login` - Magic link verification
- `POST /api/auth/login-password` - Password login
- `POST /api/auth/set-password` - Set password (session required)
- `POST /api/auth/reset-password-request` - Reset request
- `POST /api/auth/reset-password-confirm` - Reset confirmation
- `POST /api/auth/logout` - Logout
- `GET /api/auth/session/validate` - Validate session
- `GET /api/auth/me` - Get current user
- `GET /api/auth/sessions` - List sessions (Pro)
- `DELETE /api/auth/sessions/{session_id}` - Revoke session

#### Exercices (`/api/user/exercises`)
- `POST /api/user/exercises` - Save exercise (session required)
- `GET /api/user/exercises` - List exercises (session required)
- `DELETE /api/user/exercises/{exercise_uid}` - Delete exercise (ownership verified)

#### Génération (`/api/v1/exercises/*`)
- `POST /api/v1/exercises/generate` - Generate single exercise
- `POST /api/v1/exercises/generate/batch/gm07` - Batch GM07
- `POST /api/v1/exercises/generate/batch/gm08` - Batch GM08

#### Catalogue (`/api/v1/curriculum/*`)
- `GET /api/v1/curriculum/{level}/catalog` - Get curriculum catalog

#### Export (`/api/export`)
- `POST /api/export` - Export PDF (quota checked)

### 1.4 Schéma MongoDB

#### Collections principales:
- `pro_users` - Utilisateurs Pro (email, subscription_expires, password_hash, password_set_at)
- `login_sessions` - Sessions actives (session_token, user_email, device_id, created_at, expires_at)
- `magic_tokens` - Tokens magic link (token_hash, user_email, action, expires_at, used)
- `user_exercises` - Exercices sauvegardés (user_email, exercise_uid UNIQUE, generator_key, code_officiel, enonce_html, solution_html)
- `exports` - Historique exports (user_email/guest_id, created_at, document_id)
- `documents` - Documents générés (user_id/guest_id, exercises, created_at)

#### Index critiques:
- `user_exercises`: `(user_email, created_at DESC)`, `(user_email, exercise_uid UNIQUE)`
- `login_sessions`: `(session_token UNIQUE)`, `(user_email, created_at DESC)`
- `magic_tokens`: `(token_hash UNIQUE)`, `(user_email, expires_at)`

---

## 2️⃣ USER STORIES PAR PERSONA

### Persona 1: Visiteur (Non connecté)

#### US-V1: Générer des exercices en mode gratuit
**En tant que** visiteur, **je veux** générer des exercices mathématiques **afin de** tester le produit avant de m'abonner.

**Given**:
- Je suis sur `/generer`
- Je ne suis pas connecté
- Le catalogue est chargé

**When**:
- Je sélectionne un niveau (ex: 6e)
- Je sélectionne un chapitre
- Je clique sur "Générer"

**Then**:
- Des exercices sont générés et affichés
- Je peux voir l'énoncé et la solution
- Je ne peux pas sauvegarder (bouton caché ou désactivé)
- Je peux exporter (limité à 3/mois)

**États UI**: loading → success/error, empty state si aucun exercice

**Dépendances**: Catalogue API, Génération API, Quota API

---

#### US-V2: Accéder à "Mes exercices" sans être connecté
**En tant que** visiteur, **je veux** accéder à "Mes exercices" **afin de** voir ce qui m'attend en Pro.

**Given**:
- Je ne suis pas connecté
- Je clique sur "Mes exercices" dans la navbar

**When**:
- Je suis redirigé vers `/mes-exercices`

**Then**:
- Le modal de login s'ouvre automatiquement
- Après connexion, je suis redirigé vers `/mes-exercices`
- OU je vois un message "Accès Pro requis"

**États UI**: redirect → login modal → success redirect

**Dépendances**: Route guard, LoginContext, sessionStorage

---

### Persona 2: Prof/Créateur (Pro connecté)

#### US-P1: Sauvegarder un exercice généré
**En tant que** prof Pro, **je veux** sauvegarder un exercice généré **afin de** le réutiliser plus tard.

**Given**:
- Je suis connecté (session active)
- J'ai généré des exercices sur `/generer`
- L'exercice n'est pas déjà sauvegardé

**When**:
- Je clique sur "💾 Sauvegarder" sur un exercice

**Then**:
- L'exercice est sauvegardé dans ma bibliothèque
- Le bouton devient "Sauvegardé ✅" et est désactivé
- Un toast confirme la sauvegarde
- L'exercice apparaît dans `/mes-exercices`

**États UI**: button enabled → loading → success (disabled) / error toast

**Dépendances**: Session validation, `POST /api/user/exercises`, ownership check

**"Sujet ≠ Corrigé"**: ✅ Vérifié - `enonce_html` et `solution_html` sont séparés

---

#### US-P2: Consulter ma bibliothèque d'exercices
**En tant que** prof Pro, **je veux** voir tous mes exercices sauvegardés **afin de** les retrouver facilement.

**Given**:
- Je suis connecté
- J'ai sauvegardé au moins un exercice

**When**:
- Je vais sur `/mes-exercices`

**Then**:
- La liste de mes exercices s'affiche (triés par date DESC)
- Je vois: chapitre, générateur, date, difficulté
- Je peux filtrer par `code_officiel` et `difficulty`
- Je peux voir, dupliquer ou supprimer chaque exercice

**États UI**: loading → list / empty state

**Dépendances**: `GET /api/user/exercises`, session validation

---

#### US-P3: Dupliquer un exercice avec nouveau seed
**En tant que** prof Pro, **je veux** dupliquer un exercice **afin de** générer une variante pour un autre groupe.

**Given**:
- Je suis sur `/mes-exercices`
- J'ai un exercice sauvegardé

**When**:
- Je clique sur "Dupliquer" sur un exercice

**Then**:
- Un nouvel exercice est créé avec:
  - Nouveau `exercise_uid` (format: `copy_{timestamp}_{original_uid}`)
  - Nouveau `seed` (aléatoire)
  - Même `generator_key`, `code_officiel`, `variables`, `enonce_html`, `solution_html`
- La liste se recharge
- Un toast confirme la duplication

**États UI**: button → loading → success toast → list refresh

**Dépendances**: `POST /api/user/exercises`, ownership check

**"Sujet ≠ Corrigé"**: ✅ Vérifié - duplication préserve la séparation

---

#### US-P4: Se connecter depuis une page protégée
**En tant que** prof Pro, **je veux** me connecter depuis `/mes-exercices` **afin de** accéder à ma bibliothèque.

**Given**:
- Je ne suis pas connecté
- Je suis sur `/mes-exercices`

**When**:
- Je clique sur "Connexion"

**Then**:
- Le modal de login s'ouvre
- Après connexion réussie (magic link OU password), je suis redirigé vers `/mes-exercices`
- Ma session est active
- Mes exercices se chargent automatiquement

**États UI**: redirect → login modal → loading → success redirect → list load

**Dépendances**: LoginContext, `sessionStorage.postLoginRedirect`, session validation

---

### Persona 3: Admin

#### US-A1: Gérer le curriculum
**En tant que** admin, **je veux** modifier le curriculum **afin de** ajouter/modifier des chapitres.

**Given**:
- Je suis sur `/admin/curriculum`
- Je suis authentifié en tant qu'admin

**When**:
- Je modifie un chapitre

**Then**:
- Les modifications sont sauvegardées
- Le catalogue est mis à jour

**Dépendances**: Admin auth, Curriculum API

---

## 3️⃣ PARCOURS & POINTS DE TEST

### Parcours 1: Génération → Sauvegarde → Consultation

**Happy Path**:
1. UI: `/generer` → Sélection niveau/chapitre → Clic "Générer"
2. State: `setExercises([...])`
3. API: `POST /api/v1/exercises/generate` → `200 OK` → `{exercise: {...}}`
4. DB: (pas de write pour génération)
5. Response: `{enonce_html, solution_html, metadata, ...}`
6. UI: Affichage exercices + bouton "Sauvegarder" (si Pro)

**Sauvegarde**:
1. UI: Clic "💾 Sauvegarder" sur exercice
2. State: `setSavingExerciseId(id)`
3. API: `POST /api/user/exercises` avec `X-Session-Token`
4. Backend: Validation session → Vérification doublon (`exercise_uid` unique)
5. DB: `db.user_exercises.insert_one({...})`
6. Response: `{success: true, exercise_uid: "..."}`
7. UI: `setSavedExercises(prev => new Set([...prev, id]))` + toast success

**Consultation**:
1. UI: Navigation vers `/mes-exercices`
2. State: `useEffect` → `loadExercises()`
3. API: `GET /api/user/exercises` avec `X-Session-Token`
4. Backend: Validation session → Query `{user_email: email}`
5. DB: `db.user_exercises.find(query).sort("created_at", -1)`
6. Response: `{exercises: [...], count: N}`
7. UI: `setExercises(response.data.exercises)`

**Edge Cases**:
- ❌ Session expirée → 401 → Toast "Session expirée" → Redirect login
- ❌ Doublon → 409 → Toast "Déjà sauvegardé" → Marquer comme sauvegardé
- ❌ Réseau lent → Loading state → Timeout → Error toast
- ❌ Data vide → Empty state UI
- ❌ Refresh page → Session perdue → Redirect login
- ❌ Navigation retour → État préservé (localStorage)

---

### Parcours 2: Login → Redirect vers page protégée

**Happy Path**:
1. UI: Non connecté → Clic "Mes exercices" → `sessionStorage.setItem('postLoginRedirect', '/mes-exercices')`
2. State: `openLogin('/mes-exercices')` → `setShowLoginModal(true)`
3. UI: Modal login → Onglet "Mot de passe" → Email + Password → Clic "Se connecter"
4. API: `POST /api/auth/login-password` avec `withCredentials: true`
5. Backend: Vérification email → Vérification `password_hash` → Vérification password → Création session
6. DB: `db.login_sessions.insert_one({session_token, user_email, ...})`
7. Response: `{session_token: "...", email: "..."}`
8. UI: `localStorage.setItem('lemaitremot_session_token', token)` → `closeLogin()` → `sessionStorage.getItem('postLoginRedirect')` → `navigate('/mes-exercices')` → `window.location.reload()`

**Edge Cases**:
- ❌ Password incorrect → 401 → Toast "Email ou mot de passe incorrect"
- ❌ Password non défini → 400 → Toast "Mot de passe non défini"
- ❌ Session invalide après redirect → 401 → Redirect login (loop potentiel)
- ❌ `postLoginRedirect` manquant → Redirect `/`
- ❌ `window.location.reload()` après navigate → Perte de state

---

## 4️⃣ LISTE DES DYSFONCTIONNEMENTS

### A) BLOQUANTS

#### BUG-001: Double `/api/api/` dans ProSettingsPage
**Gravité**: Bloquant  
**Persona impacté**: Prof Pro  
**User story liée**: US-P5 (Accéder aux paramètres Pro)  
**Impact business**: Impossible d'accéder aux paramètres Pro, fonctionnalité critique cassée

**Étapes de reproduction**:
1. Se connecter en tant que Pro
2. Aller sur `/pro/settings`
3. Ouvrir la console réseau
4. Observer les requêtes vers `/api/api/auth/session/validate`, `/api/api/mathalea/pro/config`, etc.

**Attendu**: Requêtes vers `/api/auth/session/validate`, `/api/mathalea/pro/config`  
**Observé**: Requêtes vers `/api/api/auth/session/validate`, `/api/api/mathalea/pro/config` → 404

**Cause racine probable**:
- `ProSettingsPage.js` ligne 37: `const API = process.env.REACT_APP_BACKEND_URL` (contient déjà `/api`)
- Lignes 105, 133, 159, 220, 247, 274, 315, 367, 974: Utilisation `${API}/api/...` → double `/api/api/`

**Points de code**:
- `frontend/src/components/ProSettingsPage.js:37` - Définition `API`
- `frontend/src/components/ProSettingsPage.js:105` - `${API}/api/auth/session/validate`
- `frontend/src/components/ProSettingsPage.js:133` - `${API}/api/mathalea/pro/config`
- `frontend/src/components/ProSettingsPage.js:159` - `${API}/api/template/styles`
- `frontend/src/components/ProSettingsPage.js:220` - `${API}/api/mathalea/pro/config` (upload logo)
- `frontend/src/components/ProSettingsPage.js:247` - `${API}/api/mathalea/pro/config` (save config)
- `frontend/src/components/ProSettingsPage.js:274` - `${API}/api/auth/sessions`
- `frontend/src/components/ProSettingsPage.js:315` - `${API}/api/auth/sessions/${sessionId}`
- `frontend/src/components/ProSettingsPage.js:367` - `${API}/api/auth/sessions/${session.session_id}`
- `frontend/src/components/ProSettingsPage.js:974` - `${API}/api/auth/set-password`

**Patch proposé**:
```javascript
// Minimal (hotfix)
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`; // S'assurer que BACKEND_URL ne contient pas déjà /api

// Puis remplacer toutes les occurrences de `${API}/api/...` par `${API}/...`
```

**Risques / effets de bord**: Aucun si `BACKEND_URL` ne contient pas déjà `/api`

**Test(s) à ajouter**:
- Unit: Vérifier que `API` ne contient pas `/api/api`
- Integration: Tester toutes les requêtes depuis `/pro/settings`
- E2E: Scénario complet "Connexion → Paramètres Pro → Modifier config → Sauvegarder"

---

#### BUG-002: `window.location.reload()` après login casse le redirect
**Gravité**: Bloquant  
**Persona impacté**: Prof Pro  
**User story liée**: US-P4 (Se connecter depuis page protégée)  
**Impact business**: Impossible de revenir sur la page demandée après login, UX frustrante

**Étapes de reproduction**:
1. Non connecté → Aller sur `/mes-exercices`
2. Modal login s'ouvre → Se connecter (password)
3. Observer: `navigate(returnTo)` puis `window.location.reload()`

**Attendu**: Redirection vers `/mes-exercices` puis chargement de la page  
**Observé**: `navigate()` est appelé, puis `reload()` recharge `/` (perte du navigate)

**Cause racine probable**:
- `GlobalLoginModal.js:119`: `window.location.reload()` après `navigate(returnTo)`
- Le `reload()` annule la navigation React Router et recharge la page depuis l'URL actuelle

**Points de code**:
- `frontend/src/components/GlobalLoginModal.js:108-119` - Redirection + reload
- `frontend/src/App.js:222-224` - Même pattern dans `LoginVerify`

**Patch proposé**:
```javascript
// Minimal (hotfix)
// Supprimer window.location.reload() et utiliser un state refresh à la place
closeLogin();
const returnTo = sessionStorage.getItem('postLoginRedirect');
if (returnTo) {
  sessionStorage.removeItem('postLoginRedirect');
  navigate(returnTo);
  // Ne PAS reload, laisser React Router gérer
}

// Propre (refactor)
// Utiliser un contexte AuthContext qui met à jour l'état global
// Les composants s'abonnent et se re-rendent automatiquement
```

**Risques / effets de bord**: 
- Si d'autres composants dépendent du reload pour mettre à jour l'état, il faudra les adapter
- Vérifier que `validateSession` est appelé après navigation

**Test(s) à ajouter**:
- Integration: Test "Login → Redirect → Vérifier session active sur page cible"
- E2E: Scénario "Non connecté → /mes-exercices → Login → Vérifier présence sur /mes-exercices"

---

#### BUG-003: `MyExercisesPage` ne recharge pas après login si déjà monté
**Gravité**: Bloquant  
**Persona impacté**: Prof Pro  
**User story liée**: US-P2 (Consulter bibliothèque)  
**Impact business**: Page vide après login, nécessite refresh manuel

**Étapes de reproduction**:
1. Non connecté → Aller sur `/mes-exercices`
2. `useEffect` ligne 133-148: Pas de session → `setLoading(false)` sans appeler `loadExercises()`
3. Modal login s'ouvre → Se connecter
4. Redirection vers `/mes-exercices` (déjà monté)
5. `useEffect` ne se re-déclenche pas car dépendances `[filterCodeOfficiel, filterDifficulty]` ne changent pas

**Attendu**: Après login, `loadExercises()` est appelé automatiquement  
**Observé**: Page reste vide, `loading=false`, `exercises=[]`

**Cause racine probable**:
- `MyExercisesPage.js:133-148`: `useEffect` initial vérifie la session mais ne recharge pas si session devient disponible après
- Pas de listener sur `sessionToken` dans les dépendances du `useEffect` principal

**Points de code**:
- `frontend/src/components/MyExercisesPage.js:133-148` - `useEffect` initial
- `frontend/src/components/MyExercisesPage.js:194-198` - `useEffect` pour filtres (ne se déclenche que si `sessionToken` existe)

**Patch proposé**:
```javascript
// Minimal (hotfix)
useEffect(() => {
  const storedSessionToken = localStorage.getItem('lemaitremot_session_token');
  const storedEmail = localStorage.getItem('lemaitremot_user_email');
  const loginMethod = localStorage.getItem('lemaitremot_login_method');
  
  if (storedSessionToken && storedEmail && loginMethod === 'session') {
    setSessionToken(storedSessionToken);
    setUserEmail(storedEmail);
    setIsPro(true);
    loadExercises(); // ✅ Appeler ici
  } else {
    sessionStorage.setItem('postLoginRedirect', '/mes-exercices');
    setLoading(false);
  }
}, []); // Dépendances vides pour montage initial

// Ajouter un useEffect pour détecter les changements de sessionToken
useEffect(() => {
  if (sessionToken && isPro) {
    loadExercises();
  }
}, [sessionToken, isPro]); // ✅ Se déclenche quand sessionToken change
```

**Risques / effets de bord**: 
- Double appel possible si `sessionToken` change plusieurs fois (mitigé par `loadExercises` qui gère le loading)

**Test(s) à ajouter**:
- Integration: Test "Montage page → Login → Vérifier chargement automatique"
- E2E: Scénario "Non connecté → /mes-exercices → Login → Vérifier liste chargée"

---

### B) MAJEURS

#### BUG-004: Pas de vérification d'ownership sur `DELETE /api/user/exercises/{exercise_uid}`
**Gravité**: Majeur  
**Persona impacté**: Tous les utilisateurs Pro  
**User story liée**: US-P6 (Supprimer un exercice)  
**Impact business**: Risque sécurité - un utilisateur pourrait supprimer les exercices d'un autre (si `exercise_uid` deviné)

**Étapes de reproduction**:
1. User A sauvegarde exercice avec `exercise_uid = "abc123"`
2. User B devine ou découvre `exercise_uid = "abc123"`
3. User B appelle `DELETE /api/user/exercises/abc123` avec son propre token
4. Backend vérifie seulement que le token est valide, pas que `user_email` correspond

**Attendu**: Backend vérifie `user_email` du token = `user_email` de l'exercice  
**Observé**: Backend vérifie seulement la session, pas l'ownership

**Cause racine probable**:
- `backend/server.py:6024-6080`: `delete_user_exercise` valide la session mais ne vérifie pas que `user_email` du token = `user_email` de l'exercice avant suppression

**Points de code**:
- `backend/server.py:6024-6080` - Fonction `delete_user_exercise`

**Patch proposé**:
```python
# Minimal (hotfix)
@api_router.delete("/user/exercises/{exercise_uid}")
async def delete_user_exercise(exercise_uid: str, http_request: Request):
    session_token = http_request.headers.get("X-Session-Token")
    user_email = await validate_session_token(session_token)
    
    # ✅ Vérifier ownership AVANT suppression
    exercise = await db.user_exercises.find_one({
        "exercise_uid": exercise_uid,
        "user_email": user_email  # ✅ Filtre par ownership
    })
    
    if not exercise:
        raise HTTPException(
            status_code=404,
            detail="Exercice non trouvé ou vous n'avez pas les droits"
        )
    
    await db.user_exercises.delete_one({
        "exercise_uid": exercise_uid,
        "user_email": user_email  # ✅ Double vérification dans delete
    })
```

**Risques / effets de bord**: Aucun si correctement implémenté

**Test(s) à ajouter**:
- Unit: Test "User A ne peut pas supprimer exercice de User B"
- Integration: Test "DELETE avec token valide mais mauvais user_email → 404"

---

#### BUG-005: Pas de validation de `exercise_uid` format dans `POST /api/user/exercises`
**Gravité**: Majeur  
**Persona impacté**: Prof Pro  
**User story liée**: US-P1 (Sauvegarder exercice)  
**Impact business**: Risque de corruption de données, doublons non détectés si format inconsistant

**Étapes de reproduction**:
1. Sauvegarder exercice avec `exercise_uid = "ex1"`
2. Sauvegarder même exercice avec `exercise_uid = "ex1 "` (espace)
3. Backend ne détecte pas le doublon car comparaison exacte

**Attendu**: Validation et normalisation de `exercise_uid` (trim, lowercase si nécessaire)  
**Observé**: Pas de validation, format libre

**Cause racine probable**:
- `backend/server.py:5879-5953`: `save_user_exercise` ne valide pas le format de `exercise_uid`
- Pas de normalisation (trim, validation UUID si requis)

**Points de code**:
- `backend/server.py:5879-5953` - Fonction `save_user_exercise`
- `backend/server.py:5904-5914` - Vérification doublon (comparaison exacte)

**Patch proposé**:
```python
# Minimal (hotfix)
exercise_uid = request.exercise_uid.strip()  # ✅ Trim
if not exercise_uid:
    raise HTTPException(status_code=400, detail="exercise_uid invalide")

# Vérification doublon avec uid normalisé
existing = await db.user_exercises.find_one({
    "user_email": user_email,
    "exercise_uid": exercise_uid  # ✅ Déjà normalisé
})

# Propre (refactor)
# Créer un modèle Pydantic avec validator
class UserExerciseSaveRequest(BaseModel):
    exercise_uid: str = Field(..., min_length=1, max_length=200)
    
    @validator('exercise_uid')
    def normalize_uid(cls, v):
        return v.strip()
```

**Risques / effets de bord**: 
- Si des `exercise_uid` avec espaces existent déjà, ils ne seront pas détectés comme doublons des versions sans espaces

**Test(s) à ajouter**:
- Unit: Test "exercise_uid avec espaces → normalisé"
- Integration: Test "Sauvegarde avec uid 'abc ' et 'abc' → détecte doublon"

---

#### BUG-006: `solution_html` exposé dans `GET /api/user/exercises` sans contrôle d'accès
**Gravité**: Majeur (Pédagogie)  
**Persona impacté**: Prof Pro  
**User story liée**: US-P2 (Consulter bibliothèque)  
**Impact business**: Violation "Sujet ≠ Corrigé" - les solutions sont toujours visibles, même si l'utilisateur veut seulement voir les énoncés

**Étapes de reproduction**:
1. Appeler `GET /api/user/exercises`
2. Observer: `solution_html` est toujours présent dans la réponse
3. Frontend affiche toujours la solution dans le modal de visualisation

**Attendu**: Option pour masquer les solutions (paramètre `?include_solutions=false`)  
**Observé**: Solutions toujours exposées

**Cause racine probable**:
- `backend/server.py:5955-6022`: `get_user_exercises` retourne toujours `solution_html`
- Pas de paramètre pour contrôler l'inclusion des solutions
- Frontend affiche toujours `solution_html` dans le modal

**Points de code**:
- `backend/server.py:5955-6022` - Fonction `get_user_exercises`
- `frontend/src/components/MyExercisesPage.js:400-450` - Modal de visualisation (affiche toujours solution)

**Patch proposé**:
```python
# Minimal (hotfix)
@api_router.get("/user/exercises")
async def get_user_exercises(
    http_request: Request,
    code_officiel: Optional[str] = None,
    difficulty: Optional[str] = None,
    include_solutions: bool = True,  # ✅ Nouveau paramètre
    limit: int = 50
):
    # ... validation session ...
    
    exercises = await cursor.to_list(length=limit)
    
    # ✅ Filtrer solutions si demandé
    if not include_solutions:
        for ex in exercises:
            ex.pop("solution_html", None)
            ex["has_solution"] = "solution_html" in ex  # Indicateur
```

**Risques / effets de bord**: 
- Si le frontend dépend de `solution_html` toujours présent, il faudra adapter
- Vérifier que la duplication fonctionne toujours (nécessite `solution_html`)

**Test(s) à ajouter**:
- Unit: Test "GET avec include_solutions=false → solution_html absent"
- Integration: Test "Liste sans solutions → Duplication nécessite re-fetch avec solutions"

---

### C) UX

#### BUG-007: Pas de feedback visuel pendant `loadExercises()` dans `MyExercisesPage`
**Gravité**: Mineur (UX)  
**Persona impacté**: Prof Pro  
**User story liée**: US-P2 (Consulter bibliothèque)  
**Impact business**: UX confuse - l'utilisateur ne sait pas si la page charge ou est vide

**Étapes de reproduction**:
1. Aller sur `/mes-exercices`
2. Changer un filtre (`code_officiel` ou `difficulty`)
3. Observer: Pas de spinner/loading pendant le fetch

**Attendu**: Spinner ou skeleton pendant `loadExercises()`  
**Observé**: État `loading` existe mais n'est pas utilisé dans le rendu pendant les filtres

**Cause racine probable**:
- `MyExercisesPage.js:194-198`: `useEffect` appelle `loadExercises()` mais `loading` est géré seulement dans `loadExercises()` lui-même
- Le rendu vérifie `loading` seulement au montage initial (ligne 330)

**Points de code**:
- `frontend/src/components/MyExercisesPage.js:150-191` - Fonction `loadExercises`
- `frontend/src/components/MyExercisesPage.js:330-340` - Rendu conditionnel sur `loading`

**Patch proposé**:
```javascript
// Minimal (hotfix)
// S'assurer que loading est affiché pendant les filtres aussi
{loading ? (
  <div className="text-center py-12">
    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
    <p>Chargement de vos exercices...</p>
  </div>
) : exercises.length === 0 ? (
  // Empty state
) : (
  // List
)}
```

**Risques / effets de bord**: Aucun

**Test(s) à ajouter**:
- E2E: Test "Changement filtre → Vérifier spinner visible"

---

#### BUG-008: Toast "Déjà sauvegardé" s'affiche même si l'exercice n'est pas dans `savedExercises`
**Gravité**: Mineur (UX)  
**Persona impacté**: Prof Pro  
**User story liée**: US-P1 (Sauvegarder exercice)  
**Impact business**: Confusion - l'utilisateur pense que l'exercice est sauvegardé alors qu'il ne l'est pas

**Étapes de reproduction**:
1. Générer des exercices
2. Sauvegarder un exercice → Succès
3. Refresh la page (ou changer de chapitre)
4. `savedExercises` est vide (pas rechargé)
5. Cliquer "Sauvegarder" sur le même exercice
6. Backend retourne 409 (déjà sauvegardé)
7. Frontend affiche toast "Déjà sauvegardé" et marque comme sauvegardé localement

**Attendu**: Si 409, recharger `savedExercises` depuis le backend pour synchroniser  
**Observé**: État local désynchronisé, toast peut être trompeur

**Cause racine probable**:
- `ExerciseGeneratorPage.js:286-300`: Gestion erreur 409 met à jour `savedExercises` localement mais ne recharge pas depuis le backend
- `loadSavedExercises()` n'est appelé qu'au montage initial

**Points de code**:
- `frontend/src/components/ExerciseGeneratorPage.js:286-300` - Gestion erreur 409
- `frontend/src/components/ExerciseGeneratorPage.js:207-222` - Fonction `loadSavedExercises`

**Patch proposé**:
```javascript
// Minimal (hotfix)
} else if (error.response?.status === 409) {
  // Déjà sauvegardé - recharger depuis backend pour synchroniser
  await loadSavedExercises(sessionToken);
  toast({
    title: "Déjà sauvegardé",
    description: "Cet exercice est déjà dans votre bibliothèque",
    variant: "default"
  });
}
```

**Risques / effets de bord**: 
- Si `loadSavedExercises` échoue, l'utilisateur voit quand même le toast (acceptable)

**Test(s) à ajouter**:
- Integration: Test "409 → Vérifier rechargement savedExercises"

---

#### BUG-009: Pas de gestion d'erreur réseau dans `loadExercises()` de `MyExercisesPage`
**Gravité**: Mineur (UX)  
**Persona impacté**: Prof Pro  
**User story liée**: US-P2 (Consulter bibliothèque)  
**Impact business**: UX frustrante - pas de feedback en cas d'erreur réseau

**Étapes de reproduction**:
1. Aller sur `/mes-exercices`
2. Couper la connexion réseau
3. Observer: Toast "Session expirée" s'affiche même si c'est une erreur réseau

**Attendu**: Distinction entre erreur 401 (session) et erreur réseau (timeout, 500, etc.)  
**Observé**: Toute erreur est traitée comme 401

**Cause racine probable**:
- `MyExercisesPage.js:179-187`: Gestion erreur vérifie seulement `status === 401`
- Pas de gestion pour `error.code === 'NETWORK_ERROR'` ou timeout

**Points de code**:
- `frontend/src/components/MyExercisesPage.js:179-187` - Gestion erreur dans `loadExercises`

**Patch proposé**:
```javascript
// Minimal (hotfix)
} catch (error) {
  console.error('Erreur chargement exercices:', error);
  
  if (error.response?.status === 401) {
    toast({
      title: "Session expirée",
      description: "Veuillez vous reconnecter",
      variant: "destructive"
    });
  } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    toast({
      title: "Erreur réseau",
      description: "La connexion est lente ou interrompue. Veuillez réessayer.",
      variant: "destructive"
    });
  } else {
    toast({
      title: "Erreur de chargement",
      description: "Impossible de charger vos exercices. Veuillez réessayer.",
      variant: "destructive"
    });
  }
}
```

**Risques / effets de bord**: Aucun

**Test(s) à ajouter**:
- Integration: Test "Timeout → Vérifier toast réseau"
- E2E: Test "Déconnexion réseau → Vérifier message adapté"

---

### D) MÉTIER/PÉDAGO

#### BUG-010: `solution_html` toujours visible dans le modal de visualisation
**Gravité**: Majeur (Pédagogie)  
**Persona impacté**: Prof Pro  
**User story liée**: US-P2 (Consulter bibliothèque)  
**Impact business**: Violation "Sujet ≠ Corrigé" - le prof voit toujours la solution même s'il veut seulement vérifier l'énoncé

**Étapes de reproduction**:
1. Aller sur `/mes-exercices`
2. Cliquer "Voir" sur un exercice
3. Observer: Modal affiche énoncé ET solution côte à côte

**Attendu**: Option pour masquer/afficher la solution (toggle ou onglet)  
**Observé**: Solution toujours visible

**Cause racine probable**:
- `MyExercisesPage.js:400-450`: Modal affiche toujours `selectedExercise.solution_html`
- Pas de toggle ou onglet pour masquer la solution

**Points de code**:
- `frontend/src/components/MyExercisesPage.js:400-450` - Modal de visualisation

**Patch proposé**:
```javascript
// Minimal (hotfix)
// Ajouter un état pour masquer/afficher la solution
const [showSolution, setShowSolution] = useState(false);

// Dans le modal:
<Tabs>
  <TabsList>
    <TabsTrigger value="enonce">Énoncé</TabsTrigger>
    <TabsTrigger value="solution">Solution</TabsTrigger>
  </TabsList>
  <TabsContent value="enonce">
    <MathHtmlRenderer html={selectedExercise.enonce_html} />
  </TabsContent>
  <TabsContent value="solution">
    <MathHtmlRenderer html={selectedExercise.solution_html} />
  </TabsContent>
</Tabs>
```

**Risques / effets de bord**: 
- Changement UX - certains profs pourraient préférer voir les deux en même temps
- Solution: Option de préférence utilisateur (localStorage)

**Test(s) à ajouter**:
- E2E: Test "Voir exercice → Vérifier solution masquée par défaut"

---

### E) TECH

#### BUG-TECH-011: Pas de typage TypeScript/Pydantic pour `exercise_uid` format
**Gravité**: Mineur (Tech)  
**Persona impacté**: Développeurs  
**User story liée**: Toutes  
**Impact business**: Risque de bugs silencieux si format inconsistant

**Étapes de reproduction**:
1. Frontend envoie `exercise_uid = 123` (number)
2. Backend attend `str`
3. MongoDB stocke comme `Number` ou `String` selon conversion
4. Recherche par `exercise_uid` peut échouer si types différents

**Attendu**: Validation stricte du format (UUID v4 ou format défini)  
**Observé**: Pas de validation, format libre

**Cause racine probable**:
- `backend/server.py:5879`: `UserExerciseSaveRequest` n'a pas de validator pour `exercise_uid`
- Frontend peut envoyer n'importe quel type/format

**Points de code**:
- `backend/server.py` - Modèle `UserExerciseSaveRequest` (à trouver)
- `frontend/src/components/ExerciseGeneratorPage.js:252` - Envoi `exercise_uid`

**Patch proposé**:
```python
# Propre (refactor)
from pydantic import BaseModel, Field, validator
import re

class UserExerciseSaveRequest(BaseModel):
    exercise_uid: str = Field(..., min_length=1, max_length=200)
    
    @validator('exercise_uid')
    def validate_uid_format(cls, v):
        v = v.strip()
        # Format attendu: UUID ou "copy_timestamp_original_uid"
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('exercise_uid format invalide')
        return v
```

**Risques / effets de bord**: 
- Si des `exercise_uid` avec format invalide existent déjà, ils seront rejetés (nécessite migration)

**Test(s) à ajouter**:
- Unit: Test "exercise_uid invalide → 422"
- Integration: Test "Sauvegarde avec uid valide → 200"

---

#### BUG-TECH-012: `savedExercises` est un `Set` mais utilise `exercise.id_exercice` qui peut changer
**Gravité**: Mineur (Tech)  
**Persona impacté**: Prof Pro  
**User story liée**: US-P1 (Sauvegarder exercice)  
**Impact business**: Bouton "Sauvegarder" peut rester actif même si exercice déjà sauvegardé

**Étapes de reproduction**:
1. Générer exercices → `exercise.id_exercice = "ex1"`
2. Sauvegarder → `savedExercises.add("ex1")`
3. Regénérer avec même seed → `exercise.id_exercice = "ex2"` (nouveau ID)
4. `savedExercises` contient "ex1" mais pas "ex2"
5. Bouton "Sauvegarder" est actif alors que c'est le même exercice

**Attendu**: Utiliser un identifiant stable (ex: hash des variables + seed) pour détecter les doublons  
**Observé**: Utilisation de `id_exercice` qui peut changer entre générations

**Cause racine probable**:
- `ExerciseGeneratorPage.js:215`: `savedUids = new Set(response.data.exercises.map(ex => ex.exercise_uid))`
- `ExerciseGeneratorPage.js:238`: Vérification `savedExercises.has(exercise.id_exercice)` mais `id_exercice` ≠ `exercise_uid`

**Points de code**:
- `frontend/src/components/ExerciseGeneratorPage.js:215` - Construction `savedExercises`
- `frontend/src/components/ExerciseGeneratorPage.js:238` - Vérification doublon
- `frontend/src/components/ExerciseGeneratorPage.js:252` - Envoi `exercise_uid`

**Patch proposé**:
```javascript
// Minimal (hotfix)
// S'assurer que exercise.id_exercice === exercise_uid envoyé au backend
// Si non, utiliser exercise_uid pour la vérification

const isAlreadySaved = savedExercises.has(exercise.exercise_uid || exercise.id_exercice);

// Propre (refactor)
// Créer une fonction de génération d'UID stable basée sur metadata
const generateStableUid = (exercise) => {
  // Utiliser generator_key + code_officiel + seed + variables hash
  const stable = `${exercise.metadata?.generator_key}_${exercise.metadata?.code_officiel}_${exercise.metadata?.seed}`;
  return stable;
};
```

**Risques / effets de bord**: 
- Si `exercise_uid` n'existe pas dans l'exercice généré, il faudra le générer côté frontend (risque d'incohérence)

**Test(s) à ajouter**:
- Unit: Test "Même exercice regénéré → Détecte comme déjà sauvegardé"
- Integration: Test "Sauvegarde → Regénération → Vérifier bouton désactivé"

---

#### BUG-TECH-013: Pas de gestion de `limit` dans `GET /api/user/exercises` côté frontend
**Gravité**: Mineur (Tech)  
**Persona impacté**: Prof Pro avec beaucoup d'exercices  
**User story liée**: US-P2 (Consulter bibliothèque)  
**Impact business**: Performance dégradée si utilisateur a > 50 exercices

**Étapes de reproduction**:
1. Sauvegarder 100 exercices
2. Aller sur `/mes-exercices`
3. Observer: Seulement 50 exercices chargés (limite backend)
4. Pas de pagination ou "Charger plus"

**Attendu**: Pagination ou "Charger plus" pour afficher tous les exercices  
**Observé**: Limite fixe de 50, pas de pagination

**Cause racine probable**:
- `backend/server.py:5960`: `limit: int = 50` (fixe)
- `frontend/src/components/MyExercisesPage.js:169`: Pas de paramètre `limit` dans la requête
- Pas de pagination UI

**Points de code**:
- `backend/server.py:5960` - Paramètre `limit`
- `frontend/src/components/MyExercisesPage.js:169` - Requête sans `limit`

**Patch proposé**:
```javascript
// Minimal (hotfix)
// Ajouter pagination simple
const [page, setPage] = useState(1);
const limit = 50;

const url = `${API}/user/exercises?limit=${limit}&skip=${(page - 1) * limit}${params}`;

// Afficher "Charger plus" si count === limit
{exercises.length === limit && (
  <Button onClick={() => setPage(page + 1)}>Charger plus</Button>
)}
```

**Risques / effets de bord**: 
- Backend doit supporter `skip` (vérifier)

**Test(s) à ajouter**:
- Integration: Test "100 exercices → Pagination → Vérifier chargement progressif"

---

## 5️⃣ PLAN DE PATCH (PRIORISÉ)

### Sprint 0 (Hotfix - 1-2 jours)

1. **BUG-001**: Corriger double `/api/api/` dans `ProSettingsPage` (S)
   - Impact: Bloquant pour fonctionnalité Pro
   - Dépendances: Aucune
   - Effort: 30 min

2. **BUG-002**: Supprimer `window.location.reload()` après login (S)
   - Impact: Bloquant pour UX login
   - Dépendances: Aucune
   - Effort: 1h

3. **BUG-003**: Recharger `MyExercisesPage` après login (S)
   - Impact: Bloquant pour bibliothèque
   - Dépendances: BUG-002
   - Effort: 1h

4. **BUG-004**: Vérifier ownership sur DELETE (M)
   - Impact: Sécurité critique
   - Dépendances: Aucune
   - Effort: 1h

5. **BUG-010**: Masquer solution par défaut dans modal (M)
   - Impact: Pédagogie
   - Dépendances: Aucune
   - Effort: 2h

**Total Sprint 0**: ~5-6h

---

### Sprint 1 (Stabilisation - 1 semaine)

1. **BUG-005**: Valider format `exercise_uid` (M)
2. **BUG-006**: Paramètre `include_solutions` dans GET (M)
3. **BUG-007**: Feedback loading dans `MyExercisesPage` (S)
4. **BUG-008**: Recharger `savedExercises` après 409 (S)
5. **BUG-009**: Gestion erreur réseau (S)
6. **BUG-TECH-011**: Typage `exercise_uid` (M)
7. **BUG-TECH-012**: UID stable pour détection doublons (M)
8. **BUG-TECH-013**: Pagination exercices (M)

**Total Sprint 1**: ~3-4 jours

---

### Sprint 2 (Qualité + Croissance - 2 semaines)

- Tests E2E complets
- Amélioration UX globale
- Performance optimizations
- Documentation API

---

## 6️⃣ PLAN DE TESTS

### Matrice Tests

| Scénario | Unit | Integration | E2E | Priorité |
|----------|------|------------|-----|----------|
| Login → Redirect | ❌ | ✅ | ✅ | Haute |
| Sauvegarde exercice | ✅ | ✅ | ✅ | Haute |
| Consultation bibliothèque | ❌ | ✅ | ✅ | Haute |
| Duplication exercice | ✅ | ✅ | ❌ | Moyenne |
| Suppression exercice | ✅ | ✅ | ✅ | Haute |
| Filtres bibliothèque | ❌ | ✅ | ❌ | Moyenne |
| Session expirée | ✅ | ✅ | ✅ | Haute |
| Erreur réseau | ❌ | ✅ | ❌ | Moyenne |

### Pack E2E Minimal (5-10 scénarios)

1. **E2E-001**: Non connecté → Clic "Mes exercices" → Login → Vérifier présence sur `/mes-exercices`
2. **E2E-002**: Générer exercice → Sauvegarder → Vérifier dans bibliothèque
3. **E2E-003**: Bibliothèque → Voir exercice → Vérifier solution masquée par défaut
4. **E2E-004**: Bibliothèque → Dupliquer exercice → Vérifier nouveau dans liste
5. **E2E-005**: Bibliothèque → Supprimer exercice → Vérifier retrait de liste
6. **E2E-006**: Session expirée → Action protégée → Vérifier redirect login
7. **E2E-007**: Paramètres Pro → Modifier config → Sauvegarder → Vérifier persistence
8. **E2E-008**: Générer → Sauvegarder → Refresh → Vérifier bouton "Sauvegardé" désactivé
9. **E2E-009**: Bibliothèque → Filtrer par chapitre → Vérifier liste filtrée
10. **E2E-010**: Login password → Erreur → Vérifier message adapté

### Checklist Release "10 minutes"

- [ ] Tous les tests E2E passent
- [ ] Aucune erreur console (sauf logs normaux)
- [ ] Login magic link fonctionne
- [ ] Login password fonctionne
- [ ] Sauvegarde exercice fonctionne
- [ ] Bibliothèque se charge correctement
- [ ] Paramètres Pro accessibles
- [ ] Pas de double `/api/api/` dans les requêtes
- [ ] Redirect après login fonctionne
- [ ] Session validation fonctionne

---

## 7️⃣ NOTES COMPLÉMENTAIRES

### Points positifs identifiés

- ✅ Séparation claire `enonce_html` / `solution_html` (respect "Sujet ≠ Corrigé")
- ✅ Validation session sur endpoints protégés
- ✅ Gestion doublons avec `exercise_uid` unique
- ✅ Rate limiting actif (P0)
- ✅ Neutral responses pour anti-enumeration

### Ambiguïtés / Hypothèses

1. **Format `exercise_uid`**: Hypothèse = UUID v4 ou format libre ? À valider avec équipe.
2. **Pagination**: Backend supporte-t-il `skip` ? À vérifier dans code.
3. **`window.location.reload()`**: Est-ce intentionnel pour forcer refresh d'état ? À confirmer avec équipe.

### Recommandations

1. **Migration données**: Si correction BUG-005, vérifier `exercise_uid` existants et normaliser si nécessaire.
2. **Monitoring**: Ajouter logs pour détecter erreurs 404 sur `/api/api/*` (indicateur BUG-001).
3. **Tests automatisés**: Prioriser E2E pour parcours login → bibliothèque (couverture critique).

---

**FIN DU RAPPORT**



