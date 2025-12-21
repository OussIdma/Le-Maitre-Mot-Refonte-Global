# Commandes Docker pour exécuter les tests

## ✅ Vérification initiale

### 1. Vérifier que les fichiers de tests existent dans le repo
```bash
ls -la backend/tests/test_p0_fixes.py
ls -la backend/tests/test_pool_empty_variant_errors.py
ls -la backend/tests/test_smoke.py
```

### 2. Vérifier la configuration Docker
```bash
# Vérifier que COPY backend inclut les tests
grep "COPY backend" backend/Dockerfile
# Attendu : COPY backend /app/backend

# Vérifier que pytest est dans requirements.txt
grep pytest backend/requirements.txt
# Attendu : pytest==8.4.2
```

---

## 🔧 Solution : Rebuild l'image (recommandé)

Le `Dockerfile` copie déjà `COPY backend /app/backend`, donc les tests sont inclus dans l'image après rebuild.

### Commandes complètes

```bash
# 1. Rebuild propre (sans cache)
docker compose build --no-cache backend

# 2. Redémarrer le container
docker compose restart backend

# 3. Vérifier que les tests sont présents dans le container
docker compose exec backend ls -la /app/backend/tests/ | grep -E "test_p0|test_pool|test_smoke"

# 4. Smoke test rapide (vérifie l'environnement)
docker compose exec backend pytest backend/tests/test_smoke.py -v

# 5. Tests P0 (validation env, auth Pro, WeasyPrint)
docker compose exec backend pytest backend/tests/test_p0_fixes.py -v

# 6. Tests pool/variant (erreurs 422)
docker compose exec backend pytest backend/tests/test_pool_empty_variant_errors.py -v

# 7. Tous les tests (mode silencieux)
docker compose exec backend pytest backend/tests/ -q

# 8. Tests avec coverage (si installé)
docker compose exec backend pytest backend/tests/ --cov=backend --cov-report=term-missing
```

---

## 🧪 Smoke test

**Fichier** : `backend/tests/test_smoke.py` (nouveau)

**Tests inclus** :
- `test_imports` : Vérifie que FastAPI/HTTPException sont importables
- `test_pythonpath` : Vérifie que PYTHONPATH est correct
- `test_backend_module_import` : Vérifie que le module backend est importable
- `test_validate_env_function` : Vérifie que `validate_env` existe

**Exécution** :
```bash
docker compose exec backend pytest backend/tests/test_smoke.py -v
```

**Attendu** : 4 tests passent en < 1s

---

## 🔍 Diagnostic

### Problème : "ModuleNotFoundError: No module named 'backend'"
```bash
# Vérifier PYTHONPATH
docker compose exec backend python -c "import sys; print('\n'.join(sys.path))"
# Attendu : /app dans la liste

# Vérifier que le module backend existe
docker compose exec backend ls -la /app/backend/
```

### Problème : "FileNotFoundError: backend/tests/test_p0_fixes.py"
```bash
# Vérifier que les tests sont dans l'image
docker compose exec backend ls -la /app/backend/tests/ | grep test_p0

# Si absent : rebuild nécessaire
docker compose build --no-cache backend
docker compose restart backend
```

### Problème : "pytest: command not found"
```bash
# Vérifier installation pytest
docker compose exec backend pip list | grep pytest

# Si absent : installer
docker compose exec backend pip install pytest pytest-asyncio
```

---

## 📋 Checklist de validation

- [ ] Rebuild effectué : `docker compose build --no-cache backend`
- [ ] Container redémarré : `docker compose restart backend`
- [ ] Tests présents : `docker compose exec backend ls /app/backend/tests/ | grep test_p0`
- [ ] Smoke test passe : `docker compose exec backend pytest backend/tests/test_smoke.py -v`
- [ ] Tests P0 passent : `docker compose exec backend pytest backend/tests/test_p0_fixes.py -v`
- [ ] Tests pool/variant passent : `docker compose exec backend pytest backend/tests/test_pool_empty_variant_errors.py -v`

---

## ⚠️ Note importante

Les volumes sont **commentés** dans `docker-compose.yml` (lignes 25-27) pour éviter deadlock au boot. Cela signifie que :
- ✅ Les nouveaux fichiers sont inclus après rebuild
- ❌ Les modifications locales ne sont pas visibles sans rebuild

**Pour développement actif** : Décommenter les volumes en dev (avec risque de deadlock).

**Pour production/CI** : Utiliser rebuild (recommandé).

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Commandes prêtes, smoke test ajouté

