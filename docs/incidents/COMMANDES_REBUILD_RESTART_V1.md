# Commandes Rebuild/Restart — SIMPLIFICATION_FRACTIONS_V1
**Date** : 2025-01-XX  
**Objectif** : Appliquer les corrections P0 au backend

---

## 🔍 ÉTAPE 1 : Vérification de l'infrastructure

```bash
cd /Users/oussamaidamhane/Desktop/Projet\ local\ LMM/Le-Maitre-Mot-v16-Refonte-Sauvegarde

# Vérifier l'état des services
docker compose ps
```

**Résultat attendu** : Tous les services doivent être `Up` (backend, frontend, mongo)

---

## 🔧 ÉTAPE 2 : Rebuild du backend

```bash
# Rebuild le backend pour prendre en compte les modifications
docker compose build backend
```

**Durée estimée** : 1-3 minutes

---

## 🔄 ÉTAPE 3 : Restart du backend

```bash
# Redémarrer le backend
docker compose restart backend
```

**Alternative** (si restart ne suffit pas) :
```bash
docker compose up -d --build backend
```

---

## ✅ ÉTAPE 4 : Vérification

### 4.1 Vérifier que le backend démarre correctement

```bash
# Vérifier les logs (pas d'erreur d'import ou de syntaxe)
docker compose logs --tail=50 backend | grep -i error
```

**Résultat attendu** : Aucune erreur d'import ou de syntaxe

### 4.2 Vérifier que le générateur est accessible

```bash
# Tester l'import du générateur
docker compose exec backend python3 -c "
from backend.generators.simplification_fractions_v1 import SimplificationFractionsV1Generator
gen = SimplificationFractionsV1Generator(seed=42)
result = gen.safe_generate({
    'difficulty': 'difficile',
    'max_denominator': 6,
    'force_reducible': True,
    'show_svg': False,
    'representation': 'none'
})
print('✅ Génération réussie')
print(f'   d={result[\"variables\"][\"d\"]}, pgcd={result[\"variables\"][\"pgcd\"]}')
"
```

**Résultat attendu** :
```
✅ Génération réussie
   d=X, pgcd=Y (avec Y in [2, 3] pour max_denominator=6)
```

### 4.3 Vérifier l'API (optionnel)

```bash
# Tester l'endpoint de génération (si l'API est accessible)
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{
    "code_officiel": "6e_AA_TEST",
    "difficulte": "difficile",
    "offer": "free",
    "seed": 42
  }' | jq '.metadata.generator_key // "N/A"'
```

---

## 🐛 DÉPANNAGE

### Problème : Backend ne démarre pas

```bash
# Vérifier les erreurs de syntaxe
docker compose exec backend python3 -m py_compile backend/generators/simplification_fractions_v1.py

# Vérifier les imports
docker compose exec backend python3 -c "
import sys
sys.path.insert(0, 'backend')
from generators.simplification_fractions_v1 import SimplificationFractionsV1Generator
print('✅ Import OK')
"
```

### Problème : Erreur "ModuleNotFoundError"

```bash
# Vérifier que les fichiers sont bien dans le conteneur
docker compose exec backend ls -la backend/generators/simplification_fractions_v1.py
docker compose exec backend ls -la backend/observability/__init__.py
```

### Problème : Erreur de compilation

```bash
# Vérifier la syntaxe Python
docker compose exec backend python3 -m py_compile backend/generators/simplification_fractions_v1.py
docker compose exec backend python3 -m py_compile backend/tests/test_simplification_fractions_v1.py
```

---

## 📋 CHECKLIST DE VALIDATION

- [ ] `docker compose ps` → tous les services `Up`
- [ ] `docker compose build backend` → build réussi sans erreur
- [ ] `docker compose restart backend` → restart réussi
- [ ] `docker compose logs backend` → pas d'erreur au démarrage
- [ ] Test d'import du générateur → OK
- [ ] Test de génération avec `max_denominator=6` → OK
- [ ] Vérification que `pgcd` est valide (dans [2, 3] pour max_denominator=6)

---

## 📝 NOTES

- Les modifications sont dans `backend/generators/simplification_fractions_v1.py`
- Les tests sont dans `backend/tests/test_simplification_fractions_v1.py`
- Le rebuild est nécessaire car le code Python a été modifié
- Le restart est nécessaire pour recharger le code dans le conteneur

---

**Une fois validé** : Les corrections P0 sont en production et prêtes pour les tests fonctionnels.

