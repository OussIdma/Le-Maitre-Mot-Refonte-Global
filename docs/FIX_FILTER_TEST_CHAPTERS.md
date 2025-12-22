# Fix Filtrage Chapitres de Test - Documentation

**Date :** 2025-01-XX  
**Statut :** ✅ Implémenté

---

## Objectif

Empêcher les chapitres de test (`*_TEST*`, `6E_AA_TEST`, `6E_TESTS_DYN`, etc.) d'apparaître pour un utilisateur normal, tout en gardant un accès pour dev/admin.

---

## Solution implémentée

### Mode dev : Variable d'environnement

**Méthode choisie** : Variable d'environnement `SHOW_TEST_CHAPTERS=true`

**Avantages** :
- Simple et non fragile
- Pas de modification frontend nécessaire
- Compatible avec Docker/CI
- Pas de query param ou header à gérer

**Activation** :
```bash
export SHOW_TEST_CHAPTERS=true
# ou dans docker-compose.yml
environment:
  - SHOW_TEST_CHAPTERS=true
```

---

## Modifications Backend

### 1. Fonctions helper (`backend/curriculum/loader.py`)

**Nouvelle fonction** : `is_test_chapter(code_officiel: str) -> bool`
- Détecte si un code contient "TEST" ou "QA" (insensible à la casse)
- Exemples : `6e_AA_TEST`, `6e_TESTS_DYN`, `6e_MIXED_QA`

**Nouvelle fonction** : `should_show_test_chapters() -> bool`
- Vérifie la variable d'environnement `SHOW_TEST_CHAPTERS`
- Retourne `True` si `SHOW_TEST_CHAPTERS=true`, `False` sinon

### 2. Filtrage dans `get_catalog()` (`backend/curriculum/loader.py`)

**Changements** :
- Filtrage des chapitres de test dans `domains[].chapters[]`
- Filtrage des codes de test dans `macro_groups[].codes_officiels[]`
- Exclusion des macro groups vides après filtrage

**Code ajouté** :
```python
# Déterminer si on doit afficher les chapitres de test
show_test_chapters = should_show_test_chapters()

# Dans la boucle des chapitres
if not show_test_chapters and is_test_chapter(chapter.code_officiel):
    continue

# Dans la boucle des macro groups
if not show_test_chapters:
    codes = [code for code in codes if not is_test_chapter(code)]
    if not codes:
        continue
```

### 3. Validation dans `generate_exercise()` (`backend/routes/exercises_routes.py`)

**Changement** : Validation stricte après récupération du chapitre

**Code ajouté** :
```python
# Vérifier si c'est un chapitre de test (interdit en mode public)
from curriculum.loader import is_test_chapter, should_show_test_chapters
if is_test_chapter(request.code_officiel) and not should_show_test_chapters():
    raise HTTPException(
        status_code=422,
        detail={
            "error_code": "TEST_CHAPTER_FORBIDDEN",
            "error": "test_chapter_forbidden",
            "message": f"Le code officiel '{request.code_officiel}' est un chapitre de test et n'est pas accessible en mode public.",
            "hint": "Les chapitres de test sont réservés au développement. Activez SHOW_TEST_CHAPTERS=true pour y accéder.",
            "context": {
                "code_officiel": request.code_officiel,
                "is_test_chapter": True
            }
        }
    )
```

---

## Tests

### Fichier créé : `backend/tests/test_test_chapters_filter.py`

**Tests inclus** :
1. `test_is_test_chapter` : Vérifie la détection des chapitres de test
2. `test_should_show_test_chapters` : Vérifie le respect de la variable d'environnement
3. `test_catalog_excludes_test_chapters_by_default` : Vérifie que le catalogue exclut les chapitres de test par défaut
4. `test_catalog_includes_test_chapters_in_dev_mode` : Vérifie que le catalogue inclut les chapitres de test en mode dev
5. `test_generate_exercise_rejects_test_chapter_in_public_mode` : Vérifie que la génération rejette un chapitre de test en mode public
6. `test_generate_exercise_allows_test_chapter_in_dev_mode` : Vérifie que la génération accepte un chapitre de test en mode dev

**Exécution** :
```bash
pytest backend/tests/test_test_chapters_filter.py -v
```

---

## Format d'erreur pour chapitre de test interdit

```json
{
  "error_code": "TEST_CHAPTER_FORBIDDEN",
  "error": "test_chapter_forbidden",
  "message": "Le code officiel '6e_AA_TEST' est un chapitre de test et n'est pas accessible en mode public.",
  "hint": "Les chapitres de test sont réservés au développement. Activez SHOW_TEST_CHAPTERS=true pour y accéder.",
  "context": {
    "code_officiel": "6e_AA_TEST",
    "is_test_chapter": true
  }
}
```

---

## Commandes Docker

```bash
# 1. Rebuild propre (sans cache)
docker compose build --no-cache backend

# 2. Redémarrer le container avec mode dev activé
docker compose up -d backend
# ou dans docker-compose.yml:
# environment:
#   - SHOW_TEST_CHAPTERS=true

# 3. Tests unitaires
docker compose exec backend pytest backend/tests/test_test_chapters_filter.py -v

# 4. Test manuel - Catalogue sans chapitres de test (par défaut)
curl http://localhost:8000/api/v1/curriculum/6e/catalog | jq '.domains[].chapters[] | select(.code_officiel | contains("TEST"))'

# 5. Test manuel - Génération avec chapitre de test (doit échouer)
curl -X POST http://localhost:8000/api/v1/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"code_officiel": "6e_AA_TEST", "difficulte": "facile", "offer": "free", "seed": 42}'
```

---

## Checklist manuelle (5 points)

### 1. Test catalogue par défaut (sans chapitres de test)
- Ouvrir `/generer` en mode normal
- **Attendu** : Aucun chapitre contenant "TEST" ou "QA" dans la liste
- Vérifier les domaines et macro groups
- **Attendu** : Aucun code de test visible

### 2. Test génération avec chapitre de test (mode public)
- Essayer de générer avec `code_officiel="6e_AA_TEST"`
- **Attendu** : 422 `TEST_CHAPTER_FORBIDDEN` avec message clair

### 3. Test mode dev (SHOW_TEST_CHAPTERS=true)
- Activer `SHOW_TEST_CHAPTERS=true` dans docker-compose.yml
- Redémarrer le backend
- Ouvrir `/generer`
- **Attendu** : Chapitres de test visibles (6e_AA_TEST, 6e_TESTS_DYN, etc.)

### 4. Test génération avec chapitre de test (mode dev)
- En mode dev, générer avec `code_officiel="6e_AA_TEST"`
- **Attendu** : Pas d'erreur `TEST_CHAPTER_FORBIDDEN` (peut être POOL_EMPTY si aucun exercice)

### 5. Test frontend (sélection invalide)
- Sélectionner un chapitre de test (si visible par erreur)
- Passer en mode public (redémarrer sans SHOW_TEST_CHAPTERS)
- **Attendu** : Le chapitre sélectionné est reset ou une erreur claire est affichée

---

## Fichiers modifiés

1. **backend/curriculum/loader.py**
   - Ajout `is_test_chapter()` et `should_show_test_chapters()`
   - Filtrage dans `get_catalog()` pour domains et macro_groups

2. **backend/routes/exercises_routes.py**
   - Validation stricte pour rejeter les chapitres de test en mode public

3. **backend/tests/test_test_chapters_filter.py** (nouveau)
   - Tests unitaires pour le filtrage

---

## Validation

- ✅ Compilation : Pas d'erreurs de syntaxe
- ✅ Filtrage catalogue : Chapitres de test exclus par défaut
- ✅ Mode dev : Chapitres de test inclus si `SHOW_TEST_CHAPTERS=true`
- ✅ Validation génération : Rejet des chapitres de test en mode public
- ✅ Tests unitaires : 6 tests créés

---

## Notes

- **Pas de breaking change** : Les chapitres normaux fonctionnent comme avant
- **Comportement inchangé en dev** : Si `SHOW_TEST_CHAPTERS=true`, tout fonctionne comme avant
- **Erreurs explicites** : 422 `TEST_CHAPTER_FORBIDDEN` avec hint clair
- **Frontend** : Aucune modification nécessaire (le filtrage est transparent)

---

**Document créé le :** 2025-01-XX  
**Statut :** ✅ Implémenté, prêt pour validation

