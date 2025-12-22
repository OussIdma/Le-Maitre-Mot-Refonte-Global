# Configuration Docker pour exécuter les tests

**Date :** 2025-01-XX  
**Statut :** ✅ Configuration prête

---

## Problème identifié

Les fichiers de tests (`backend/tests/test_p0_fixes.py`, `backend/tests/test_pool_empty_variant_errors.py`) sont présents dans le repo mais peuvent ne pas être accessibles dans le container Docker si l'image n'a pas été rebuild depuis leur création.

**Cause** : Le `docker-compose.yml` a les volumes commentés (lignes 25-27) pour éviter deadlock au boot, donc les nouveaux fichiers ne sont pas montés automatiquement.

---

## Solution

### Option A : Rebuild l'image (recommandé pour production)

Le `Dockerfile` copie déjà `COPY backend /app/backend`, donc les tests sont inclus dans l'image après rebuild.

**Avantages** :
- Tests disponibles même sans volumes
- Image complète et autonome
- Pas de dépendance au système de fichiers local

**Commandes** :
```bash
# Rebuild propre (sans cache)
docker compose build --no-cache backend

# Vérifier que les tests sont présents
docker compose exec backend ls -la /app/backend/tests/ | grep test_p0_fixes.py

# Exécuter les tests
docker compose exec backend pytest backend/tests/test_p0_fixes.py -v
docker compose exec backend pytest backend/tests/test_pool_empty_variant_errors.py -v

# Exécuter tous les tests
docker compose exec backend pytest backend/tests/ -v

# Smoke test rapide
docker compose exec backend pytest backend/tests/test_smoke.py -v
```

---

### Option B : Monter les volumes en dev (pour développement actif)

**Modification docker-compose.yml** :
```yaml
volumes:
  # Activer en dev pour avoir les tests en temps réel
  - ./backend:/app/backend
  - ./scripts:/app/scripts
  - backend_uploads:/app/backend/uploads
```

**Avantages** :
- Modifications de tests visibles immédiatement
- Pas besoin de rebuild après chaque modification

**Inconvénients** :
- Peut causer des deadlocks au boot (d'où le commentaire)
- Nécessite de redémarrer le container après modification

**Commandes** :
```bash
# Redémarrer le container après modification docker-compose.yml
docker compose down
docker compose up -d backend

# Exécuter les tests
docker compose exec backend pytest backend/tests/test_p0_fixes.py -v
```

---

## Vérification de l'environnement

### 1. Vérifier que pytest est installé
```bash
docker compose exec backend pip list | grep pytest
# Attendu : pytest, pytest-asyncio
```

### 2. Vérifier que les tests sont présents
```bash
docker compose exec backend ls -la /app/backend/tests/ | grep -E "test_p0|test_pool|test_smoke"
# Attendu : test_p0_fixes.py, test_pool_empty_variant_errors.py, test_smoke.py
```

### 3. Smoke test
```bash
docker compose exec backend pytest backend/tests/test_smoke.py -v
# Attendu : 4 tests passent (imports, pythonpath, backend module, validate_env)
```

---

## Commandes complètes

### Rebuild et test (Option A - recommandé)
```bash
# 1. Rebuild propre
docker compose build --no-cache backend

# 2. Redémarrer le container
docker compose restart backend

# 3. Vérifier que les tests sont présents
docker compose exec backend ls -la /app/backend/tests/ | grep test_p0

# 4. Smoke test
docker compose exec backend pytest backend/tests/test_smoke.py -v

# 5. Tests P0
docker compose exec backend pytest backend/tests/test_p0_fixes.py -v

# 6. Tests pool/variant
docker compose exec backend pytest backend/tests/test_pool_empty_variant_errors.py -v

# 7. Tous les tests
docker compose exec backend pytest backend/tests/ -q
```

### Exécution rapide (si volumes montés)
```bash
# Tests P0
docker compose exec backend pytest backend/tests/test_p0_fixes.py -v

# Tests pool/variant
docker compose exec backend pytest backend/tests/test_pool_empty_variant_errors.py -v

# Smoke test
docker compose exec backend pytest backend/tests/test_smoke.py -v
```

---

## Smoke test ajouté

**Fichier** : `backend/tests/test_smoke.py` (nouveau)

**Tests inclus** :
1. `test_imports` : Vérifie que FastAPI/HTTPException sont importables
2. `test_pythonpath` : Vérifie que PYTHONPATH est correct
3. `test_backend_module_import` : Vérifie que le module backend est importable
4. `test_validate_env_function` : Vérifie que `validate_env` existe

**Avantages** :
- Ne dépend d'aucune fixture externe (DB, services)
- Exécution rapide (< 1s)
- Détecte les problèmes d'environnement de base

---

## Diagnostic des problèmes

### Problème : "ModuleNotFoundError: No module named 'backend'"
**Solution** : Vérifier PYTHONPATH
```bash
docker compose exec backend python -c "import sys; print(sys.path)"
# Attendu : /app dans la liste
```

### Problème : "FileNotFoundError: backend/tests/test_p0_fixes.py"
**Solution** : Rebuild l'image
```bash
docker compose build --no-cache backend
docker compose restart backend
```

### Problème : "pytest: command not found"
**Solution** : Vérifier requirements.txt
```bash
docker compose exec backend pip list | grep pytest
# Si absent : pip install pytest pytest-asyncio
```

---

## Recommandation

**Pour production/CI** : Utiliser Option A (rebuild image)  
**Pour développement actif** : Utiliser Option B (volumes montés)

**Par défaut** : Les volumes sont commentés, donc il faut rebuild après ajout de nouveaux fichiers de tests.

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Configuration prête, smoke test ajouté

