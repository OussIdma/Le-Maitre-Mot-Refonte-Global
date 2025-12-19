# Tests d'intégration pour chapter_code

**Date de création:** 2024-12-09  
**Sprint:** Exploitation de chapter_code dans l'API

---

## 📋 Vue d'ensemble

Ces tests vérifient l'intégration correcte du système `chapter_code` dans l'application, incluant :
- La cohérence de la migration des données
- Le fonctionnement de l'API avec les nouveaux filtres
- La compatibilité avec l'existant (chapitre_id)
- Le service de mapping

---

## 🧪 Tests disponibles

### Test 1 : Cohérence de la migration 002

**Fichier:** `backend/tests/test_chapter_code_integration.py::test_migration_002_coherence`

**Objectif:** Vérifier que tous les `chapter_code` présents dans les ExerciseType correspondent à des chapitres réels dans la collection `chapters`.

**Vérifie:**
- ✅ Chaque ExerciseType avec `chapter_code` a un chapitre correspondant
- ✅ Les `chapter_code` sont valides (existent dans la base)
- ✅ Pas de références cassées

**Résultat attendu:**
```
✅ Test migration 002: 40 exercices vérifiés avec chapter_code valide
```

---

### Test 2 : Filtrage API par chapter_code

**Fichier:** `backend/tests/test_chapter_code_integration.py::test_api_filter_by_chapter_code`

**Objectif:** Vérifier que le paramètre `chapter_code` filtre correctement les résultats de l'API.

**Note:** Ce test est actuellement **conceptuel** car il nécessite un TestClient FastAPI actif. Il documente la structure attendue des tests API.

**Tests à implémenter avec TestClient:**
1. Appel sans `chapter_code` → retourne tous les exercices
2. Appel avec `chapter_code` valide → retourne uniquement les exercices correspondants
3. Appel avec `chapter_code` inexistant → retourne liste vide

**Exemple de test complet:**
```python
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_api_without_filter():
    response = client.get("/api/mathalea/exercise-types")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 47

def test_api_with_chapter_code():
    response = client.get("/api/mathalea/exercise-types?chapter_code=6e_G07")
    assert response.status_code == 200
    items = response.json()["items"]
    assert all(ex["chapter_code"] == "6e_G07" for ex in items)
```

---

### Test 3 : Présence des champs dans les réponses

**Fichier:** `backend/tests/test_chapter_code_integration.py::test_response_contains_both_fields`

**Objectif:** Vérifier que les réponses API contiennent **à la fois** `chapitre_id` (legacy) et `chapter_code` (nouveau).

**Vérifie:**
- ✅ Champ `chapitre_id` présent (compatibilité)
- ✅ Champ `chapter_code` présent
- ✅ `chapter_code` n'est pas None

**Résultat attendu:**
```
✅ Test champs présents: chapitre_id='Nombres relatifs', chapter_code='5e_N08'
```

---

### Test 4 : Service de mapping

**Fichier:** `backend/tests/test_chapter_code_integration.py::test_chapter_mapping_service`

**Objectif:** Vérifier que le `ChapterMappingService` fonctionne correctement.

**Vérifie:**
- ✅ `get_chapter_code_for_exercise_type()` retourne le bon code
- ✅ Le service gère correctement les ExerciseType avec chapter_code
- ✅ Pas d'erreurs lors de l'appel au service

**Résultat attendu:**
```
✅ Test mapping service: chapter_code '5e_N08' correctement retourné
```

---

### Test 5 : Exercices non migrés restent fonctionnels

**Fichier:** `backend/tests/test_chapter_code_integration.py::test_unmapped_exercises_remain_functional`

**Objectif:** Vérifier que les 7 ExerciseType sans `chapter_code` restent fonctionnels via leur `chapitre_id`.

**Vérifie:**
- ✅ Exactement 7 exercices sans `chapter_code`
- ✅ Tous ont un `chapitre_id` valide
- ✅ Pas de régression sur ces exercices

**Résultat attendu:**
```
✅ Test exercices non migrés: 7 exercices avec chapitre_id valide
```

---

## 🚀 Comment lancer les tests

### Méthode 1 : Exécution directe

```bash
cd /app/backend && python3 tests/test_chapter_code_integration.py
```

**Sortie attendue:**
```
================================================================================
🧪 TESTS D'INTÉGRATION - CHAPTER_CODE
================================================================================

Test 1: Cohérence migration 002
✅ Test migration 002: 40 exercices vérifiés avec chapter_code valide

Test 2: Filtrage API (conceptuel)
✅ Test API filter (conceptuel): Structure validée

Test 3: Présence des champs dans les réponses
✅ Test champs présents: chapitre_id='Nombres relatifs', chapter_code='5e_N08'

Test 4: Service de mapping
✅ Test mapping service: chapter_code '5e_N08' correctement retourné

Test 5: Exercices non migrés fonctionnels
✅ Test exercices non migrés: 7 exercices avec chapitre_id valide

================================================================================
✅ TOUS LES TESTS RÉUSSIS
================================================================================
```

### Méthode 2 : Avec pytest (recommandé)

**Installation :**
```bash
pip install pytest pytest-asyncio
```

**Exécution :**
```bash
cd /app/backend && pytest tests/test_chapter_code_integration.py -v
```

**Options utiles :**
```bash
# Afficher les print()
pytest tests/test_chapter_code_integration.py -v -s

# Arrêter au premier échec
pytest tests/test_chapter_code_integration.py -v -x

# Afficher le coverage
pytest tests/test_chapter_code_integration.py --cov=services --cov=models
```

---

## 📊 Couverture des tests

| Composant | Couverture | Tests |
|-----------|------------|-------|
| Migration 002 | ✅ | Test 1 |
| API /exercise-types | ⚠️ Partiel | Test 2 (conceptuel) |
| Modèle ExerciseType | ✅ | Test 3 |
| ChapterMappingService | ✅ | Test 4 |
| Non-régression | ✅ | Test 5 |

**Légende:**
- ✅ : Test complet et fonctionnel
- ⚠️ : Test partiel ou conceptuel (à compléter)

---

## 🔧 Tests à ajouter (backlog)

### Tests API avec TestClient

```python
from fastapi.testclient import TestClient

def test_api_backward_compatibility():
    """Vérifier que les anciens appels fonctionnent toujours"""
    # Test avec chapitre_id (legacy)
    response = client.get("/api/mathalea/exercise-types?chapitre_id=Nombres relatifs")
    assert response.status_code == 200
    assert len(response.json()["items"]) > 0

def test_api_combined_filters():
    """Tester la combinaison de filtres"""
    response = client.get("/api/mathalea/exercise-types?niveau=6e&chapter_code=6e_G07")
    assert response.status_code == 200
    items = response.json()["items"]
    assert all(ex["niveau"] == "6e" and ex["chapter_code"] == "6e_G07" for ex in items)
```

### Tests de performance

```python
def test_query_performance_with_chapter_code():
    """Vérifier que les requêtes par chapter_code sont rapides"""
    import time
    
    start = time.time()
    response = client.get("/api/mathalea/exercise-types?chapter_code=6e_G07")
    duration = time.time() - start
    
    assert duration < 0.5  # Moins de 500ms
```

### Tests de régression

```python
def test_no_regression_on_old_endpoints():
    """Vérifier qu'aucun endpoint existant n'est cassé"""
    endpoints = [
        "/api/mathalea/exercise-types",
        "/api/mathalea/exercise-types?niveau=6e",
        "/api/catalogue/levels/6e/chapters"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200
```

---

## ✅ Critères de succès

Pour que les tests soient considérés comme **réussis**, il faut :

1. ✅ Tous les tests existants passent (5/5)
2. ✅ Aucune régression détectée sur l'API existante
3. ✅ Les 7 exercices non migrés restent fonctionnels
4. ✅ Le service de mapping fonctionne correctement
5. ⚠️ Tests API avec TestClient à ajouter (backlog)

---

## 📝 Notes

- Ces tests sont **non destructifs** : ils ne modifient pas la base de données
- Ils peuvent être exécutés en environnement de développement ou CI/CD
- Pour des tests d'intégration complets, utiliser une base de données de test isolée
- Les tests conceptuels (Test 2) nécessitent un refactoring pour utiliser TestClient

---

## 🔗 Ressources

- **Fichier de tests:** `backend/tests/test_chapter_code_integration.py`
- **Service testé:** `backend/services/chapter_mapping_service.py`
- **Documentation migration:** `docs/exercise_types_non_mappes.md`
- **Modèle:** `backend/models/mathalea_models.py`
