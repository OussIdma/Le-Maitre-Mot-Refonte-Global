# P0 - Validation Fix: POST /api/auth/verify-login

## Problème initial
- **Erreur 500** : `'Request' object has no attribute 'device_id'`
- **Cause** : Le code tentait d'accéder à `request.device_id` alors que `device_id` doit venir du body JSON
- **Impact** : Crash lors de la vérification du token de connexion

## Corrections appliquées

### 1. Modèle Pydantic (`VerifyLoginRequest`)
- `device_id` rendu optionnel : `device_id: str | None = None`
- Permet de recevoir des requêtes avec ou sans `device_id`

### 2. Lecture de `device_id`
- **Avant** : `request.device_id` (incorrect, `Request` n'a pas cet attribut)
- **Après** : `request_body.device_id` (lecture depuis le body JSON)
- Fallback : `device_id = request_body.device_id or "unknown"`

### 3. Ordre des opérations (sécurité)
- **Avant** : Token marqué comme utilisé AVANT la création de session
- **Après** : Token marqué comme utilisé APRÈS la création réussie de la session et le set_cookie
- **Raison** : Si la création de session échoue, le token reste utilisable

### 4. Gestion d'erreur
- Pydantic valide automatiquement le modèle
- Si `token` manquant → 422 avec message clair
- Si `device_id` manquant → OK (optionnel, utilise "unknown")

## Tests

### Commande curl de test
```bash
# Test avec token et device_id
curl -i -X POST http://localhost:8000/api/auth/verify-login \
  -H "Content-Type: application/json" \
  -d '{"token":"<NEW_TOKEN>","device_id":"device_test"}'

# Test sans device_id (optionnel)
curl -i -X POST http://localhost:8000/api/auth/verify-login \
  -H "Content-Type: application/json" \
  -d '{"token":"<NEW_TOKEN>"}'

# Test sans token (doit retourner 422)
curl -i -X POST http://localhost:8000/api/auth/verify-login \
  -H "Content-Type: application/json" \
  -d '{"device_id":"device_test"}'
```

### Vérification des logs
```bash
# Vérifier qu'il n'y a plus d'erreur "no attribute 'device_id'"
docker-compose logs backend --tail=200 | grep -E "verify-login|Error in verify login|device_id"

# Vérifier que le token est marqué comme utilisé APRÈS la création de session
docker-compose logs backend --tail=200 | grep -E "Token marked as used|Login session created"
```

### Résultats attendus
- ✅ **200/204** : Connexion réussie avec Set-Cookie
- ✅ **422** : Si `token` manquant (validation Pydantic)
- ✅ **400** : Si token invalide ou expiré
- ✅ **403** : Si abonnement Pro expiré
- ✅ **500** : Plus d'erreur "no attribute 'device_id'"

## Fichiers modifiés
- `backend/server.py` :
  - Ligne 725 : `device_id` rendu optionnel
  - Lignes 3831-3863 : Réorganisation (mark token used déplacé à la fin)
  - Ligne 3840 : Correction `request.device_id` → `request_body.device_id`

## Commit
- Fix: POST /api/auth/verify-login - device_id from body + mark token after success
