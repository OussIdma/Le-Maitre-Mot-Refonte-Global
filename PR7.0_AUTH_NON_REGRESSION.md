# PR7.0 - Auth Non-Régression: Tests + Contrat + Release Gate

## 🎯 Objectif

Verrouiller le comportement d'authentification pour éviter la régression du bug "email fantôme" (affichage d'un email alors que l'utilisateur n'est pas connecté).

## 📋 Modifications

### A) Contrat d'état auth
**Fichier**: `frontend/src/auth/authStateContract.js`

- `isLoggedIn({ sessionToken, userEmail })`: Vérifie si un utilisateur est connecté
- `normalizeEmail(email)`: Normalise un email (trim + validation)

**Utilisation dans NavBar**: Remplace les checks dispersés par une fonction centralisée.

### B) Tests unitaires NavBar
**Fichier**: `frontend/src/components/__tests__/NavBar.test.js`

**Cas couverts**:
- ✅ `userEmail = null` => affiche "Se connecter"
- ✅ `userEmail = ""` => affiche "Se connecter"
- ✅ `userEmail = "   "` => affiche "Se connecter"
- ✅ `userEmail = "test@mail.com" + token` => affiche "test@mail.com"
- ✅ État de chargement
- ✅ Après auth-changed avec userEmail null

### C) Tests unitaires useAuth
**Fichier**: `frontend/src/hooks/__tests__/useAuth.test.js`

**Cas couverts**:
- ✅ Token invalide (401) => nettoyage localStorage complet
- ✅ Anti-réentrance (isClearingRef empêche relecture pendant cleanup)
- ✅ handleAuthChanged avec token absent => force state null
- ✅ Token valide => mise à jour état
- ✅ Pas de token => état null

### D) Release Gate
**Fichier**: `scripts/release_check.sh`

Ajout d'une étape 5 qui exécute les tests frontend ciblés:
```bash
npm test -- --runInBand --testPathPattern='NavBar.test|useAuth.test' --watchAll=false
```

## 🚀 Comment lancer les tests

### Tests individuels

```bash
# Tests NavBar uniquement
cd frontend
npm test -- NavBar.test.js --watchAll=false

# Tests useAuth uniquement
npm test -- useAuth.test.js --watchAll=false

# Tous les tests auth/navbar
npm test -- --testPathPattern='NavBar.test|useAuth.test' --watchAll=false
```

### Release check complet

```bash
./scripts/release_check.sh
```

## ✅ DoD (Definition of Done)

- ✅ Tests verts (NavBar + useAuth)
- ✅ `release_check.sh` échoue si régression
- ✅ Aucun retour possible du bug "email fantôme"
- ✅ Tests rapides (<10s)

## 🔍 Impact

**Avant**: Bug "email fantôme" pouvait réapparaître après modifications
**Après**: Tests verrouillent le comportement, régression impossible

**Fichiers modifiés**:
- `frontend/src/auth/authStateContract.js` (nouveau)
- `frontend/src/components/NavBar.js` (utilise le contrat)
- `frontend/src/components/__tests__/NavBar.test.js` (nouveau)
- `frontend/src/hooks/__tests__/useAuth.test.js` (nouveau)
- `scripts/release_check.sh` (ajout gate frontend)
- `frontend/src/setupTests.js` (nouveau, config Jest)

## 📝 Notes

- Les tests utilisent React Testing Library et Jest (inclus avec react-scripts)
- Les mocks sont configurés pour localStorage, axios, et les hooks React
- Le release gate est léger et ciblé (seulement les tests auth/navbar)

