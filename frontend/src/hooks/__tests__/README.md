# Tests useAuth

## Exécution

```bash
cd frontend
npm test -- useAuth.test.js
# ou
yarn test useAuth.test.js
```

## Couverture

- Token invalide (401) → nettoyage localStorage
- Anti-réentrance (isClearingRef)
- Gestion événements auth-changed
- Token valide → mise à jour état
- Pas de token → état null

