# AUDIT P0 - Routes Auth et Rate Limiting

Date: 2025-12-27

## 1. Endpoints Auth identifiés

| Path | Method | Rate Limit | Description |
|------|--------|------------|-------------|
| `/api/auth/request-login` | POST | 5/15min | Demande magic link |
| `/api/auth/verify-login` | POST | 10/15min | Vérifie magic link + crée session |
| `/api/auth/verify-checkout-token` | POST | 10/15min | Vérifie token pre-checkout |
| `/api/auth/login-password` | POST | - | Login par mot de passe |
| `/api/auth/logout` | POST | - | Déconnexion (invalide session) |
| `/api/auth/me` | GET | - | Info user connecté (cookie/header) |
| `/api/auth/session/validate` | POST | - | Valide session (legacy) |
| `/api/auth/sessions` | GET | - | Liste sessions actives user |
| `/api/auth/sessions/{session_id}` | DELETE | - | Supprime une session |
| `/api/auth/pre-checkout` | POST | - | Pre-checkout flow |
| `/api/auth/reset-password-request` | POST | 3/15min | Demande reset password |
| `/api/auth/reset-password-confirm` | POST | - | Confirme reset password |
| `/api/auth/set-password` | POST | - | Définit mot de passe |

## 2. Route appelée par /login/verify côté front

**Frontend:** `frontend/src/App.js` ligne 185-297 - composant `LoginVerify`

**Appel réseau:**
```javascript
// App.js:222-227
const response = await axios.post(`${API}/auth/verify-login`, {
  token: token,
  device_id: deviceId
}, {
  withCredentials: true  // P0 UX: Inclure les cookies httpOnly
});
```

**Route backend:** `POST /api/auth/verify-login` (server.py:3789-3874)

## 3. Configuration Rate Limit

### Librairie
- **slowapi** (backend/requirements.txt)
- Import: `from slowapi import Limiter, _rate_limit_exceeded_handler`

### Configuration (server.py:447-455)
```python
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### Scope par route
| Route | Limite | Ligne |
|-------|--------|-------|
| verify-login | 10/15minutes | 3790 |
| request-login | 5/15minutes | 3699 |
| verify-checkout-token | 10/15minutes | 3877 |
| reset-password-request | 3/15minutes | 5599 |

### Pas de bypass pour localhost/dev
Aucune configuration `DISABLE_RATE_LIMIT` trouvée.

## 4. Analyse Front: appels multiples verify-login

### Code actuel (App.js:193-205)
```javascript
useEffect(() => {
  const token = searchParams.get('token');
  if (!token) { ... }

  if (!isVerifying) {
    verifyLogin(token);
  }
}, [searchParams, isVerifying]);  // <-- BUG: isVerifying dans deps!
```

### PROBLEME IDENTIFIE

**Bug:** `isVerifying` est dans les dépendances du useEffect.

1. Premier render: `isVerifying=false` -> appelle `verifyLogin(token)`
2. `verifyLogin` fait `setIsVerifying(true)`
3. Le useEffect se re-déclenche car `isVerifying` a changé
4. Avec React StrictMode en dev: useEffect peut s'exécuter 2x
5. Le guard `useState` n'est pas fiable car async

### SOLUTION REQUISE
Utiliser `useRef` au lieu de `useState` pour le guard:
```javascript
const didCallRef = useRef(false);
useEffect(() => {
  if (didCallRef.current) return;
  didCallRef.current = true;
  verifyLogin(token);
}, []); // deps vides
```

## 5. Problèmes secondaires identifiés

### 5.1 Logout ne supprime pas le cookie
```python
# server.py:3992-4014 - logout actuel
# Attend X-Session-Token header, ne supprime PAS le cookie httpOnly
```
**Fix requis:** `response.delete_cookie("session_token")`

### 5.2 Token stocké en localStorage
```javascript
// App.js:230
localStorage.setItem('lemaitremot_session_token', response.data.session_token);
```
Le session_token est retourné dans la réponse ET stocké en localStorage.
Ceci est pour backward compat mais moins sécurisé que cookie-only.

## 6. Commandes de test

```bash
# Test rate limit
docker-compose logs -f backend | grep -iE "verify-login|429|rate"

# Test /me
curl -i -s http://localhost:8000/api/auth/me | head

# Test logout
curl -i -s -X POST http://localhost:8000/api/auth/logout | head
```

## 7. Résumé des fixes P0-A requis

| ID | Fix | Fichier | Priorité |
|----|-----|---------|----------|
| A1 | Guard useRef pour empêcher appels multiples | App.js:185-252 | CRITIQUE |
| A2 | Augmenter rate limit verify-login ou bypass dev | server.py:3790 | HIGH |
| A3 | Logout: delete_cookie + support cookie | server.py:3992-4023 | MEDIUM |
