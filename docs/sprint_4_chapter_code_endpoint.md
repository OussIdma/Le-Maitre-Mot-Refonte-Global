# 📘 SPRINT 4 - Endpoint dédié Chapter Code

## Résumé fonctionnel

### Objectif
Créer un endpoint RESTful dédié pour récupérer tous les exercices d'un chapitre MathALÉA spécifique via son code (`chapter_code`).

### Endpoint créé
```
GET /api/mathalea/chapters/{chapter_code}/exercise-types
```

### Avantages
- ✅ **URL sémantique** : `/chapters/{chapter_code}/exercise-types` est plus claire que `/exercise-types?chapter_code=X`
- ✅ **Validation automatique** : Vérifie que le `chapter_code` existe avant de retourner les exercices
- ✅ **HTTP 404** explicite si le chapitre n'existe pas
- ✅ **Pagination** intégrée (`skip` et `limit`)
- ✅ **Compatibilité totale** avec l'ancien système

---

## Exemples d'URL

### Récupérer tous les exercices du chapitre "6e_G07"
```bash
GET /api/mathalea/chapters/6e_G07/exercise-types
```

**Réponse (HTTP 200)** :
```json
{
  "total": 5,
  "items": [
    {
      "id": "uuid-123",
      "code_ref": "6G07_EX01",
      "titre": "Angles et droites perpendiculaires",
      "chapter_code": "6e_G07",
      "niveau": "6e",
      "domaine": "Géométrie",
      "chapitre_id": "Angles",
      "min_questions": 1,
      "max_questions": 10,
      "default_questions": 5,
      "difficulty_levels": ["facile", "moyen", "difficile"],
      "generator_kind": "legacy",
      "supports_seed": true,
      "supports_ai_enonce": false,
      "supports_ai_correction": false,
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

### Avec pagination
```bash
GET /api/mathalea/chapters/6e_G07/exercise-types?limit=10&skip=0
```

### Avec filtre niveau (double vérification)
```bash
GET /api/mathalea/chapters/6e_G07/exercise-types?niveau=6e
```

### Chapter code inexistant
```bash
GET /api/mathalea/chapters/UNKNOWN_CODE/exercise-types
```

**Réponse (HTTP 404)** :
```json
{
  "detail": "Chapter with code 'UNKNOWN_CODE' not found"
}
```

---

## Détails techniques

### Fichiers modifiés
- **`/app/backend/routes/mathalea_routes.py`** : Nouvel endpoint ajouté après l'endpoint existant `GET /api/mathalea/exercise-types`

### Logique de l'endpoint

1. **Validation du chapter_code** :
   - Utilise `ChapterService.get_chapter_by_code()` pour vérifier que le chapitre existe dans la collection `chapters`
   - Si le chapitre n'existe pas → **HTTP 404**

2. **Requête MongoDB** :
   ```python
   query = {"chapter_code": chapter_code}
   if niveau:  # Filtre optionnel
       query["niveau"] = niveau
   ```

3. **Pagination** :
   - Paramètres : `skip` (défaut: 0) et `limit` (défaut: 50, max: 500)
   - Implémentation via `.skip(skip).limit(limit)`

4. **Réponse** :
   - Format identique à `GET /api/mathalea/exercise-types`
   - Type : `ExerciseTypeListResponse` (Pydantic)
   - Champs : `total` (int) et `items` (List[ExerciseType])

### Code de l'endpoint
```python
@router.get("/chapters/{chapter_code}/exercise-types", response_model=ExerciseTypeListResponse)
async def get_chapter_exercise_types(
    chapter_code: str,
    niveau: Optional[str] = Query(None, description="Filtrer par niveau (optionnel)"),
    skip: int = Query(0, ge=0, description="Pagination: nombre d'éléments à sauter"),
    limit: int = Query(50, ge=1, le=500, description="Pagination: nombre maximum d'éléments")
):
    from services.chapter_service import ChapterService
    
    # 1. Vérifier que le chapitre existe
    chapter_service = ChapterService(db)
    chapter = await chapter_service.get_chapter_by_code(chapter_code)
    
    if not chapter:
        raise HTTPException(
            status_code=404,
            detail=f"Chapter with code '{chapter_code}' not found"
        )
    
    # 2. Construire la requête pour les ExerciseType
    query = {"chapter_code": chapter_code}
    if niveau:
        query["niveau"] = niveau
    
    # 3. Récupérer les exercices
    cursor = exercise_types_collection.find(query, {"_id": 0}).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    total = await exercise_types_collection.count_documents(query)
    
    # 4. Retourner la réponse
    return ExerciseTypeListResponse(
        total=total,
        items=[ExerciseType(**item) for item in items]
    )
```

### Compatibilité avec l'ancien système

| Système | Endpoint | Comportement |
|---------|----------|--------------|
| **Ancien** | `GET /api/mathalea/exercise-types?chapter_code=6e_G07` | ✅ Continue de fonctionner |
| **Nouveau** | `GET /api/mathalea/chapters/6e_G07/exercise-types` | ✅ Recommandé |

**Points clés** :
- Les deux endpoints retournent **la même structure de données**
- L'ancien endpoint **ne valide pas** l'existence du `chapter_code` (retourne une liste vide si inexistant)
- Le nouvel endpoint **valide** l'existence et retourne **HTTP 404** si le chapitre n'existe pas

---

## Tests API

### Fichier de tests
```
/app/backend/tests/test_mathalea_api_chapter_code.py
```

### Tests implémentés

| Test | Description | Résultat attendu |
|------|-------------|------------------|
| **Test 1** | Endpoint de base sans filtre | HTTP 200, liste non vide, `chapter_code` présent |
| **Test 2** | Filtre `chapter_code` sur endpoint existant | HTTP 200, tous les items ont le bon `chapter_code` |
| **Test 3** | Nouvel endpoint dédié | HTTP 200, même contenu que Test 2 |
| **Test 4** | `chapter_code` inconnu | HTTP 404 avec message explicite |
| **Test 5** | Compatibilité exercices non migrés | Exercices sans `chapter_code` accessibles via l'ancien endpoint uniquement |
| **Test 6** | Pagination | `limit` et `skip` fonctionnent correctement |

### Lancer les tests

#### Option 1 : Avec pytest
```bash
cd /app/backend
pytest tests/test_mathalea_api_chapter_code.py -v
```

#### Option 2 : Exécution directe (pour debug)
```bash
cd /app/backend
python tests/test_mathalea_api_chapter_code.py
```

#### Option 3 : Tous les tests du dossier
```bash
cd /app/backend
pytest tests/ -v
```

---

## Exemples de réponses JSON

### Succès : 1 exercice trouvé
```json
{
  "total": 1,
  "items": [
    {
      "id": "9e3f4a1b-2c3d-4e5f-6a7b-8c9d0e1f2a3b",
      "code_ref": "6G07_ANGLES_01",
      "titre": "Reconnaître des angles droits",
      "chapter_code": "6e_G07",
      "chapitre_id": "Angles",
      "niveau": "6e",
      "domaine": "Géométrie",
      "competences_ids": [],
      "min_questions": 1,
      "max_questions": 10,
      "default_questions": 5,
      "difficulty_levels": ["facile", "moyen"],
      "question_kinds": {},
      "random_config": {},
      "generator_kind": "legacy",
      "legacy_generator_id": "6G20",
      "supports_seed": true,
      "supports_ai_enonce": false,
      "supports_ai_correction": false,
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

### Succès : Aucun exercice pour ce chapitre
```json
{
  "total": 0,
  "items": []
}
```

### Erreur : Chapter code inexistant
```json
{
  "detail": "Chapter with code 'INVALID_CODE' not found"
}
```

---

## Cas d'usage

### Frontend - Afficher les exercices d'un chapitre
```javascript
async function loadChapterExercises(chapterCode) {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/mathalea/chapters/${chapterCode}/exercise-types`
    );
    
    if (!response.ok) {
      if (response.status === 404) {
        console.error("Chapitre introuvable");
        return [];
      }
      throw new Error("Erreur serveur");
    }
    
    const data = await response.json();
    return data.items;
  } catch (error) {
    console.error("Erreur lors du chargement des exercices:", error);
    return [];
  }
}

// Utilisation
const exercises = await loadChapterExercises("6e_G07");
console.log(`${exercises.length} exercices trouvés`);
```

### Backend - Vérifier la disponibilité d'exercices
```python
async def has_exercises_for_chapter(chapter_code: str) -> bool:
    """Vérifie si un chapitre a des exercices disponibles"""
    from services.chapter_service import ChapterService
    
    chapter_service = ChapterService(db)
    chapter = await chapter_service.get_chapter_by_code(chapter_code)
    
    if not chapter:
        return False
    
    count = await exercise_types_collection.count_documents(
        {"chapter_code": chapter_code}
    )
    
    return count > 0
```

---

## Notes importantes

### ⚠️ Limitations
- Seuls les exercices **avec `chapter_code`** sont retournés
- Les exercices non migrés (sans `chapter_code`) ne sont **pas** accessibles via cet endpoint
- Pour accéder aux exercices non migrés, utiliser l'ancien endpoint : `GET /api/mathalea/exercise-types`

### ✅ Règles de non-régression respectées
- ❌ Aucune modification des migrations existantes
- ❌ Aucune modification de la structure des modèles `Chapter` et `ExerciseType`
- ❌ Aucune modification des endpoints existants
- ✅ Ajout d'un nouvel endpoint sans impact sur le système existant

### 🎯 Prochaines étapes (hors Sprint 4)
- Mapper les 7 exercices non migrés (voir `/app/docs/exercise_types_non_mappes.md`)
- Migrer le frontend pour utiliser le nouvel endpoint
- Ajouter des métriques sur l'utilisation de l'endpoint

---

## Changelog

| Date | Version | Changement |
|------|---------|------------|
| 2025-01-XX | 1.0 | Sprint 4 - Création de l'endpoint dédié et tests API |

---

**Auteur** : Emergent AI  
**Projet** : Le-Maitre-Mot-v16-Refonte  
**Sprint** : 4 - Endpoint dédié + tests API
