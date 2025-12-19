# V1-BE-002 : Endpoint POST /api/v1/exercises/generate - Contexte Technique

## 📋 Informations du ticket

- **ID** : V1-BE-002
- **Type** : Feature
- **Priorité** : High
- **Statut** : En cours
- **Assigné** : Backend Team

---

## 🎯 Objectif

Créer un endpoint REST API permettant de générer des exercices mathématiques personnalisés avec leurs corrections, figures géométriques et tokens PDF.

---

## 🏗️ Architecture technique

### Stack technique

- **Framework** : FastAPI (Python 3.11)
- **Database** : MongoDB
- **Server** : /app/backend/server.py
- **Routes** : /app/backend/routes/

### Structure du projet

```
/app/backend/
├── server.py                          # Application FastAPI principale
├── routes/
│   ├── math_routes.py                 # Routes math legacy
│   ├── mathalea_routes.py             # Routes MathALÉA
│   └── exercises_routes.py            # ✨ NOUVEAU : Routes v1 exercises
├── services/
│   ├── math_generation_service.py     # Service de génération math
│   ├── geometry_render_service.py     # Service de rendu SVG
│   ├── exercise_template_service.py   # Service de templates
│   └── curriculum_service.py          # ✨ NOUVEAU : Service curriculum
├── models/
│   └── exercise_models.py             # ✨ NOUVEAU : Modèles Pydantic
├── tests/
│   └── test_api_exercises.py          # ✨ NOUVEAU : Tests de l'API
└── curriculum_complete.py             # Source de vérité curriculum
```

---

## 🔧 Services existants à utiliser

### 1. MathGenerationService

**Fichier** : `/app/backend/services/math_generation_service.py`

**Méthodes clés** :
- `generate_exercise(niveau, chapitre, difficulte)` → MathExerciseSpec
- `_gen_symetrie_axiale()`, `_gen_fractions()`, etc.

**Sortie** : MathExerciseSpec contenant :
- `enonce` : Énoncé textuel
- `figure_geometrique` : GeometricFigure si applicable
- `etapes_calculees` : Étapes de résolution
- `resultat_final` : Solution finale

### 2. GeometryRenderService

**Fichier** : `/app/backend/services/geometry_render_service.py`

**Méthodes clés** :
- `render_figure_to_svg(figure: GeometricFigure)` → dict ou string SVG

**Sortie** :
- `figure_svg_question` : SVG pour l'énoncé (sans solution)
- `figure_svg_correction` : SVG pour la correction (avec solution)

### 3. CurriculumComplete

**Fichier** : `/app/backend/curriculum_complete.py`

**Structure** :
```python
CURRICULUM_DATA_COMPLETE = {
    "Mathématiques": {
        "data": {
            "5e": {
                "Symétrie axiale": [...],
                "Symétrie centrale": [...],
                "Triangles": [...]
            }
        }
    }
}
```

**Niveaux disponibles** :
- Primaire : CP, CE1, CE2, CM1, CM2
- Collège : 6e, 5e, 4e, 3e
- Lycée : 2nde, 1ère, Terminale

---

## 📦 Nouveaux composants à créer

### 1. CurriculumService

**Responsabilité** : Validation du niveau et du chapitre

```python
class CurriculumService:
    def validate_niveau(niveau: str) -> bool
    def validate_chapitre(niveau: str, chapitre: str) -> bool
    def get_niveaux_disponibles() -> List[str]
    def get_chapitres_disponibles(niveau: str) -> List[str]
```

### 2. ExerciseModels (Pydantic)

**Request Model** :
```python
class ExerciseGenerateRequest(BaseModel):
    niveau: str
    chapitre: str
    type_exercice: str = "standard"
    difficulte: str = "facile"
```

**Response Model** :
```python
class ExerciseGenerateResponse(BaseModel):
    id_exercice: str
    niveau: str
    chapitre: str
    enonce_html: str
    svg: Optional[str]
    solution_html: str
    pdf_token: str
    metadata: dict
```

### 3. ExercisesRouter

**Fichier** : `/app/backend/routes/exercises_routes.py`

**Endpoint** :
```python
@router.post("/api/v1/exercises/generate", response_model=ExerciseGenerateResponse)
async def generate_exercise(request: ExerciseGenerateRequest):
    # 1. Valider niveau + chapitre
    # 2. Générer exercice avec MathGenerationService
    # 3. Générer SVG avec GeometryRenderService
    # 4. Construire HTML énoncé + solution
    # 5. Générer pdf_token
    # 6. Retourner réponse
```

---

## 🔄 Flux de traitement

```
1. Client envoie POST /api/v1/exercises/generate
   ↓
2. Validation Pydantic (niveau, chapitre)
   ↓
3. CurriculumService.validate_niveau()
   → Si invalide : HTTP 422 avec message pédagogique
   ↓
4. CurriculumService.validate_chapitre()
   → Si invalide : HTTP 422 avec liste des chapitres disponibles
   ↓
5. MathGenerationService.generate_exercise()
   → Génère MathExerciseSpec
   ↓
6. GeometryRenderService.render_figure_to_svg()
   → Génère SVG (si figure présente)
   ↓
7. Construction de l'énoncé HTML
   → Utilise enonce + svg_question
   ↓
8. Construction de la solution HTML
   → Utilise etapes_calculees + svg_correction
   ↓
9. Génération du pdf_token
   → Format : id_exercice (pour v1, pas de PDF réel)
   ↓
10. Retour HTTP 200 avec ExerciseGenerateResponse
```

---

## 🧪 Tests à implémenter

### test_api_exercises.py

**Cas de test** :

1. **test_generate_exercise_success_geometry**
   - Niveau : 5e
   - Chapitre : Symétrie axiale
   - Vérifier : 200, tous les champs présents, SVG non vide

2. **test_generate_exercise_success_calculation**
   - Niveau : 6e
   - Chapitre : Fractions
   - Vérifier : 200, enonce_html contient du HTML

3. **test_generate_exercise_invalid_niveau**
   - Niveau : "5eme" (invalide)
   - Vérifier : 422, message pédagogique, liste des niveaux

4. **test_generate_exercise_invalid_chapitre**
   - Niveau : 5e
   - Chapitre : "Géométrie spatiale" (invalide)
   - Vérifier : 422, message pédagogique, liste des chapitres

5. **test_generate_exercise_with_difficulty**
   - Difficulté : difficile
   - Vérifier : 200, metadata contient difficulte

6. **test_pdf_token_format**
   - Vérifier : pdf_token == id_exercice (v1)

---

## 🔐 Contraintes et règles métier

### Validation du niveau

- Format attendu : exactement comme dans `CURRICULUM_DATA_COMPLETE`
- Exemples valides : "5e", "CP", "2nde"
- Exemples invalides : "5eme", "5ème", "cinquième"

### Validation du chapitre

- Sensible à la casse
- Doit exister dans le niveau spécifié
- Exemples : "Symétrie axiale", "Fractions", "Triangles"

### Génération du pdf_token

- Format v1 (simple) : `id_exercice`
- Format v2 (futur) : token temporaire avec expiration

### HTML Sanitization

- Utiliser `bleach` ou équivalent
- Autoriser : `<p>`, `<strong>`, `<em>`, `<br>`, `<ul>`, `<li>`, `<table>`
- Interdire : `<script>`, `<iframe>`, `<object>`

---

## 📊 Format de l'id_exercice

```
Format : ex_{niveau}_{chapitre_slug}_{timestamp}
Exemples :
  - ex_5e_symetrie-axiale_1702401234
  - ex_6e_fractions_1702401235
  - ex_cm2_geometrie_1702401236
```

**Génération** :
```python
import time
import re

def generate_exercise_id(niveau: str, chapitre: str) -> str:
    chapitre_slug = re.sub(r'[^a-z0-9]+', '-', chapitre.lower()).strip('-')
    timestamp = int(time.time())
    return f"ex_{niveau}_{chapitre_slug}_{timestamp}"
```

---

## 🚨 Gestion des erreurs

### Erreurs métier (422)

```python
from fastapi import HTTPException

# Niveau invalide
raise HTTPException(
    status_code=422,
    detail={
        "error": "niveau_invalide",
        "message": f"Le niveau '{niveau}' n'est pas reconnu...",
        "niveaux_disponibles": curriculum_service.get_niveaux_disponibles()
    }
)

# Chapitre invalide
raise HTTPException(
    status_code=422,
    detail={
        "error": "chapitre_invalide",
        "message": f"Le chapitre '{chapitre}' n'existe pas pour le niveau '{niveau}'...",
        "niveau": niveau,
        "chapitres_disponibles": curriculum_service.get_chapitres_disponibles(niveau)
    }
)
```

### Erreurs techniques (500)

```python
try:
    spec = math_service.generate_exercise(...)
except Exception as e:
    logger.error(f"Erreur génération exercice: {e}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail=f"Erreur lors de la génération de l'exercice : {str(e)}"
    )
```

---

## 📝 Exemple d'implémentation (pseudo-code)

```python
@router.post("/api/v1/exercises/generate")
async def generate_exercise(request: ExerciseGenerateRequest):
    # 1. Validation
    curriculum_service = CurriculumService()
    if not curriculum_service.validate_niveau(request.niveau):
        raise HTTPException(422, detail={"error": "niveau_invalide", ...})
    
    if not curriculum_service.validate_chapitre(request.niveau, request.chapitre):
        raise HTTPException(422, detail={"error": "chapitre_invalide", ...})
    
    # 2. Génération
    math_service = MathGenerationService()
    spec = math_service.generate_exercise(
        niveau=request.niveau,
        chapitre=request.chapitre,
        difficulte=request.difficulte
    )
    
    # 3. Rendu SVG
    svg = None
    if spec.figure_geometrique:
        geom_service = GeometryRenderService()
        result = geom_service.render_figure_to_svg(spec.figure_geometrique)
        svg = result.get("figure_svg_question") if isinstance(result, dict) else result
    
    # 4. Construction HTML
    enonce_html = f"<p>{spec.enonce}</p>"
    if svg:
        enonce_html += svg
    
    solution_html = "<p><strong>Solution :</strong></p><ul>"
    for etape in spec.etapes_calculees:
        solution_html += f"<li>{etape}</li>"
    solution_html += f"</ul><p>Résultat final : {spec.resultat_final}</p>"
    
    # 5. ID et token
    id_exercice = generate_exercise_id(request.niveau, request.chapitre)
    pdf_token = id_exercice  # v1: simple
    
    # 6. Réponse
    return ExerciseGenerateResponse(
        id_exercice=id_exercice,
        niveau=request.niveau,
        chapitre=request.chapitre,
        enonce_html=enonce_html,
        svg=svg,
        solution_html=solution_html,
        pdf_token=pdf_token,
        metadata={
            "type_exercice": request.type_exercice,
            "difficulte": request.difficulte,
            "duree_estimee": 5,
            "points": 2.0
        }
    )
```

---

## 🔗 Intégration dans server.py

```python
# Dans server.py
from routes.exercises_routes import router as exercises_router

app.include_router(exercises_router, tags=["Exercises v1"])
```

---

## ✅ Checklist d'implémentation

- [ ] Créer `/app/backend/models/exercise_models.py`
- [ ] Créer `/app/backend/services/curriculum_service.py`
- [ ] Créer `/app/backend/routes/exercises_routes.py`
- [ ] Ajouter le router dans `server.py`
- [ ] Créer `/app/backend/tests/test_api_exercises.py`
- [ ] Implémenter les 6 tests
- [ ] Vérifier que tous les tests passent (`pytest`)
- [ ] Tester manuellement avec `curl`
- [ ] Documenter dans `V1_BE_002_RESULTAT.md`

---

## 📚 Références

- Spécification fonctionnelle : `/app/docs/API_EXERCISES.md`
- Service Math : `/app/backend/services/math_generation_service.py`
- Service Geometry : `/app/backend/services/geometry_render_service.py`
- Curriculum : `/app/backend/curriculum_complete.py`
- FastAPI docs : https://fastapi.tiangolo.com/
