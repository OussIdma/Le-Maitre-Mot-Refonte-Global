# Quick Start - Tests Docker

## ✅ Vérification rapide

```bash
# 1. Vérifier que les fichiers de tests existent
ls backend/tests/test_p0_fixes.py backend/tests/test_pool_empty_variant_errors.py backend/tests/test_smoke.py

# 2. Rebuild l'image (les tests sont inclus via COPY backend)
docker compose build --no-cache backend

# 3. Redémarrer
docker compose restart backend

# 4. Smoke test (vérifie l'environnement)
docker compose exec backend pytest backend/tests/test_smoke.py -v

# 5. Tests P0
docker compose exec backend pytest backend/tests/test_p0_fixes.py -v

# 6. Tests pool/variant
docker compose exec backend pytest backend/tests/test_pool_empty_variant_errors.py -v
```

---

## 📋 Résumé

**Problème** : Les volumes sont commentés dans docker-compose.yml, donc les nouveaux fichiers de tests ne sont pas montés automatiquement.

**Solution** : Rebuild l'image (COPY backend inclut déjà les tests).

**Fichiers ajoutés** :
- `backend/tests/test_smoke.py` - Smoke test simple
- `pytest-asyncio==0.24.0` ajouté dans requirements.txt

**Pas de modification Dockerfile/docker-compose.yml nécessaire** : Le COPY backend existant inclut déjà les tests.

---

**Commandes essentielles** :
```bash
docker compose build --no-cache backend
docker compose restart backend
docker compose exec backend pytest backend/tests/test_smoke.py -v
```

