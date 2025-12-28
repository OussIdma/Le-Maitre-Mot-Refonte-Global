# Build frontend (CRACO) - runbook rapide

⚠️ Recommandé : utiliser npm (overrides). Pour Yarn, une résolution est aussi fournie.

1) Nettoyage et permissions si node_modules appartient à root :
```
cd frontend
sudo chown -R $(whoami) node_modules || true
rm -rf node_modules package-lock.json yarn.lock
npm cache verify
```

2) Installation (résout date-fns en ^3.6.x, compatible react-day-picker 8.10.x) :
```
npm install
# (optionnel yarn) : yarn install --check-files
```

3) Build :
```
npm run build
# (optionnel yarn) : yarn build
```

4) Diagnostic si encore un conflit :
```
npm ls date-fns react-day-picker @craco/craco
# (optionnel yarn) : yarn list date-fns react-day-picker @craco/craco
```
