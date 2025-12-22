# Guide API MathALÉA System

## 📚 Vue d'ensemble

Le système MathALÉA permet de créer, gérer et organiser des exercices mathématiques de manière structurée et flexible.

**Architecture** : MongoDB + Pydantic v2 + FastAPI

---

## 🔗 Endpoints de Base

Base URL : `http://localhost:8001/api/mathalea/`

---

## 1. Compétences (`/competences`)

### Créer une compétence
```bash
POST /api/mathalea/competences
Content-Type: application/json

{
  "code": "6G1",
  "intitule": "Reconnaître et construire une symétrie axiale",
  "niveau": "6e",
  "domaine": "Espace et géométrie"
}

# Response: 201
{
  "id": "uuid-generated",
  "code": "6G1",
  "intitule": "Reconnaître et construire une symétrie axiale",
  "niveau": "6e",
  "domaine": "Espace et géométrie"
}
```

### Lister les compétences
```bash
GET /api/mathalea/competences?niveau=6e&domaine=Géométrie&skip=0&limit=50

# Response: 200
{
  "total": 10,
  "items": [...]
}
```

### Récupérer une compétence
```bash
GET /api/mathalea/competences/{competence_id}

# Response: 200
{...}
```

### Mettre à jour
```bash
PATCH /api/mathalea/competences/{competence_id}
Content-Type: application/json

{
  "intitule": "Nouveau titre"
}
```

### Supprimer
```bash
DELETE /api/mathalea/competences/{competence_id}

# Response: 204
```

---

## 2. Types d'Exercices (`/exercise-types`)

### Créer un type d'exercice
```bash
POST /api/mathalea/exercise-types
Content-Type: application/json

{
  "code_ref": "SYM_AX_01",
  "titre": "Symétrie axiale - Trouver le symétrique",
  "chapitre_id": "optional-chapter-id",
  "niveau": "6e",
  "domaine": "Espace et géométrie",
  "competences_ids": ["uuid-competence-1", "uuid-competence-2"],
  "min_questions": 1,
  "max_questions": 10,
  "default_questions": 5,
  "difficulty_levels": ["facile", "moyen", "difficile"],
  "question_kinds": {
    "trouver_valeur": true,
    "verifier_propriete": false
  },
  "random_config": {
    "min_value": 1,
    "max_value": 10
  },
  "generator_kind": "template",
  "supports_seed": true,
  "supports_ai_enonce": false,
  "supports_ai_correction": false
}

# Response: 201
{
  "id": "uuid-generated",
  "created_at": "2025-12-08T10:00:00Z",
  "updated_at": "2025-12-08T10:00:00Z",
  ...
}
```

### Lister avec filtres
```bash
GET /api/mathalea/exercise-types?niveau=6e&domaine=Géométrie&chapitre_id=xxx&generator_kind=template

# Filtres disponibles:
# - niveau (ex: 6e, 5e, 4e)
# - domaine (ex: Géométrie, Nombres)
# - chapitre_id
# - generator_kind (template, ia, hybrid)
# - skip, limit (pagination)
```

### CRUD standard
```bash
GET /api/mathalea/exercise-types/{id}          # Récupérer
PATCH /api/mathalea/exercise-types/{id}        # Mettre à jour
DELETE /api/mathalea/exercise-types/{id}       # Supprimer
```

---

## 3. Feuilles d'Exercices (`/sheets`)

### Créer une feuille
```bash
POST /api/mathalea/sheets
Content-Type: application/json

{
  "titre": "Révisions Géométrie 6e",
  "niveau": "6e",
  "description": "Feuille de révision pour le contrôle",
  "owner_id": "user-123"
}

# Response: 201
{
  "id": "uuid-generated",
  "titre": "Révisions Géométrie 6e",
  "niveau": "6e",
  "description": "Feuille de révision pour le contrôle",
  "owner_id": "user-123",
  "created_at": "2025-12-08T10:00:00Z",
  "updated_at": "2025-12-08T10:00:00Z"
}
```

### Lister les feuilles d'un utilisateur
```bash
GET /api/mathalea/sheets?owner_id=user-123&niveau=6e
```

### CRUD standard
```bash
GET /api/mathalea/sheets/{id}          # Récupérer
PATCH /api/mathalea/sheets/{id}        # Mettre à jour
DELETE /api/mathalea/sheets/{id}       # Supprimer (+ cascade items)
```

---

## 4. Items de Feuille (`/sheet-items`)

### Ajouter un exercice à une feuille
```bash
POST /api/mathalea/sheet-items
Content-Type: application/json

{
  "sheet_id": "uuid-sheet",
  "exercise_type_id": "uuid-exercise-type",
  "nb_questions": 5,
  "difficulty": "moyen",
  "seed": 12345,
  "options": {
    "custom_param_1": "value"
  },
  "ai_enonce": false,
  "ai_correction": false
}

# Response: 201
{
  "id": "uuid-generated",
  "sheet_id": "uuid-sheet",
  "exercise_type_id": "uuid-exercise-type",
  "nb_questions": 5,
  "difficulty": "moyen",
  "seed": 12345,
  "options": {...},
  "ai_enonce": false,
  "ai_correction": false,
  "order": 1  # Auto-incrémenté
}
```

### Lister les items d'une feuille
```bash
GET /api/mathalea/sheet-items?sheet_id=uuid-sheet

# Response: 200
{
  "total": 3,
  "items": [
    {
      "id": "...",
      "order": 1,
      ...
    },
    {
      "id": "...",
      "order": 2,
      ...
    }
  ]
}
```

### CRUD standard
```bash
GET /api/mathalea/sheet-items/{id}          # Récupérer
PATCH /api/mathalea/sheet-items/{id}        # Mettre à jour
DELETE /api/mathalea/sheet-items/{id}       # Supprimer
```

---

## 📊 Workflow Typique

### Cas d'usage : Créer une feuille d'exercices personnalisée

```bash
# 1. Créer des compétences (si pas déjà existantes)
POST /api/mathalea/competences
{
  "code": "6G1",
  "intitule": "Symétrie axiale",
  "niveau": "6e",
  "domaine": "Géométrie"
}
# → Retourne: competence_id

# 2. Créer des types d'exercices
POST /api/mathalea/exercise-types
{
  "code_ref": "SYM_AX_SIMPLE",
  "titre": "Symétrie simple",
  "niveau": "6e",
  "domaine": "Géométrie",
  "competences_ids": [competence_id],
  "generator_kind": "template"
}
# → Retourne: exercise_type_id_1

POST /api/mathalea/exercise-types
{
  "code_ref": "SYM_AX_COMPLEXE",
  "titre": "Symétrie complexe",
  "niveau": "6e",
  "domaine": "Géométrie",
  "competences_ids": [competence_id],
  "generator_kind": "hybrid"
}
# → Retourne: exercise_type_id_2

# 3. Créer une feuille
POST /api/mathalea/sheets
{
  "titre": "Contrôle Symétrie",
  "niveau": "6e",
  "owner_id": "prof_martin"
}
# → Retourne: sheet_id

# 4. Ajouter des exercices à la feuille
POST /api/mathalea/sheet-items
{
  "sheet_id": sheet_id,
  "exercise_type_id": exercise_type_id_1,
  "nb_questions": 3,
  "difficulty": "facile",
  "seed": 42
}

POST /api/mathalea/sheet-items
{
  "sheet_id": sheet_id,
  "exercise_type_id": exercise_type_id_2,
  "nb_questions": 2,
  "difficulty": "difficile",
  "ai_enonce": true
}

# 5. Récupérer la feuille complète
GET /api/mathalea/sheets/{sheet_id}
GET /api/mathalea/sheet-items?sheet_id={sheet_id}
```

---

## 🔧 Modèles de Données

### GeneratorKind (Enum)
- `template` : Génération par gabarits pré-définis
- `ia` : Génération 100% par IA
- `hybrid` : Combinaison gabarit + IA

### Competence
```python
{
  "id": str (UUID),
  "code": str (unique),
  "intitule": str,
  "niveau": str,
  "domaine": str
}
```

### ExerciseType
```python
{
  "id": str (UUID),
  "code_ref": str (unique),
  "titre": str,
  "chapitre_id": Optional[str],
  "niveau": str,
  "domaine": str,
  "competences_ids": List[str],
  "min_questions": int,
  "max_questions": int,
  "default_questions": int,
  "difficulty_levels": List[str],
  "question_kinds": Dict,
  "random_config": Dict,
  "generator_kind": GeneratorKind,
  "supports_seed": bool,
  "supports_ai_enonce": bool,
  "supports_ai_correction": bool,
  "created_at": datetime,
  "updated_at": datetime
}
```

### ExerciseSheet
```python
{
  "id": str (UUID),
  "titre": str,
  "niveau": str,
  "description": Optional[str],
  "owner_id": str,
  "created_at": datetime,
  "updated_at": datetime
}
```

### SheetItem
```python
{
  "id": str (UUID),
  "sheet_id": str (FK),
  "exercise_type_id": str (FK),
  "nb_questions": int,
  "difficulty": str,
  "seed": Optional[int],
  "options": Dict,
  "ai_enonce": bool,
  "ai_correction": bool,
  "order": int
}
```

---

## ⚠️ Points d'attention

1. **UUIDs** : Tous les IDs sont des UUIDs v4 stockés en string
2. **Timestamps** : Format ISO 8601 avec timezone UTC
3. **Cascade Delete** : Supprimer une sheet supprime aussi ses items
4. **Order** : Auto-incrémenté à la création, permet réorganisation
5. **Validation** : Pydantic valide automatiquement les données

---

## 🧪 Tests

Tests disponibles : `/app/backend/tests/test_mathalea_system.py`

```bash
# Exécuter tous les tests
pytest tests/test_mathalea_system.py -v

# Exécuter un test spécifique
pytest tests/test_mathalea_system.py::test_create_competence -v
```

---

## 📖 Documentation Complète

- **Modèles** : `/app/backend/models/mathalea_models.py`
- **Routes** : `/app/backend/routes/mathalea_routes.py`
- **Migration** : `/app/backend/migrations/001_init_mathalea_collections.py`
- **Rapport Sprint A** : `/app/SPRINT_A_RAPPORT.md`
