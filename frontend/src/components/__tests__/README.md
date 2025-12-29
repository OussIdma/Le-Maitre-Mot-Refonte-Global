# Tests NavBar

## Exécution

```bash
cd frontend
npm test -- NavBar.test.js
# ou
yarn test NavBar.test.js
```

## Couverture

- Affichage "Se connecter" si userEmail null/undefined/""
- Affichage email si userEmail valide
- État de chargement
- Après auth-changed avec userEmail null → "Se connecter"

