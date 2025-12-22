# FIGURES_FUSION - Notes techniques (Étape 1 : Cartographie)

## 🎯 Objectif
Réintégrer les schémas/figures legacy (SVG/HTML) dans le nouveau système Builder + PDF

---

## 📋 Architecture actuelle des figures

### 1. Génération des figures dans le système legacy

**Modèle de données** : `/app/backend/models/math_models.py`

```python
class GeometricFigure(BaseModel):
    type: str  # Ex: "symetrie_axiale", "triangle", "cercle", etc.
    points: List[str]  # Ex: ["A", "B", "C"]
    longueurs_connues: Dict[str, float]  # Ex: {"AB": 5.0, "AC": 6.0}
    proprietes: List[str]  # Ex: ["rectangle_en_A", "axe_vertical"]
```

**Intégration dans MathExerciseSpec** :
```python
class MathExerciseSpec(BaseModel):
    niveau: str
    chapitre: str
    type_exercice: MathExerciseType
    parametres: Dict[str, Any]
    solution_calculee: Dict[str, Any]
    figure_geometrique: Optional[GeometricFigure] = None  # ← FIGURE ICI
```

### 2. Génération des figures par type d'exercice

#### Exercices avec figures identifiés :

**A. Symétrie axiale** (`_gen_symetrie_axiale`)
- Fichier : `/app/backend/services/math_generation_service.py` (ligne 1493)
- Type figure : `symetrie_axiale`
- Contenu :
  ```python
  figure = GeometricFigure(
      type="symetrie_axiale",
      points=[point_original, point_image],  # Ex: ["A", "A'"]
      longueurs_connues={
          f"{point_original}_x": point_x,
          f"{point_original}_y": point_y,
          f"{point_image}_x": image_x,
          f"{point_image}_y": image_y
      },
      proprietes=[f"axe_{axe_type}", f"axe_position_{axe_position}"]
  )
  ```

**B. Triangles et géométrie plane**
- Aires de triangles (ligne 320)
- Périmètres (ligne 609)
- Théorème de Pythagore (lignes 699, 739, 774)
- Théorème de Thalès (lignes 828, 1222, 1259, 1296)
- Triangles rectangles (lignes 1379, 1490)
- Triangles quelconques (lignes 1617, 1781, 1863)

**C. Géométrie spatiale**
- Volumes (lignes 1973, 2075, 2176)
- Figures 3D : cylindre, pyramide, cube, etc.

### 3. Rendu des figures en SVG

**Renderers disponibles** :

#### A. SchemaRenderer (`/app/backend/render_schema.py`)
- Convertit JSON schema → SVG via matplotlib
- Méthode principale : `render_to_svg(schema_data: dict) -> str`
- Types supportés :
  - `cylindre`
  - `triangle`
  - `triangle_rectangle`
  - `rectangle`
  - `carre`
  - `cercle`
  - `pyramide`
  - Fallback générique pour autres types

#### B. GeometryRenderer (`/app/backend/geometry_renderer.py`)
- Génère des figures géométriques 2D
- Spécialisé pour symétrie axiale
- Méthode : `render_symmetry_figure(...) -> str`
- Retourne un `<svg>...</svg>` complet

#### C. GeometryRenderService (`/app/backend/services/geometry_render_service.py`)
- Service de plus haut niveau
- Gère différents types de figures :
  - Type 1 : dessiner_figure_initiale (triangle + axe)
  - Type 2 : dessiner_symetrique (+ image symétrique)
  - Type 3 : completer_figure (cacher certains éléments)

---

## 🔍 Flux actuel de génération

### Dans le système legacy complet (ancien)

```
MathGenerationService
   ↓
_gen_symetrie_axiale() / _gen_triangle() / etc.
   ↓
Crée MathExerciseSpec avec figure_geometrique
   ↓
Conversion vers Question
   ↓
figure_geometrique → data["figure"]
   ↓
GeometryRenderer.render_symmetry_figure()
   ↓
SVG généré et inséré dans HTML
   ↓
PDF legacy (anciens templates)
```

### Dans le nouveau système (Builder actuel)

```
ExerciseTemplateService
   ↓
generate_exercise()
   ↓
_generate_legacy_questions()
   ↓
_generate_legacy_fallback_question()  ← PROBLÈME ICI
   ↓
Questions sans figure_geometrique
   ↓
Preview JSON sans SVG
   ↓
PDFs sans figures ❌
```

**PROBLÈME IDENTIFIÉ** :
- Ligne 517 dans `/app/backend/services/exercise_template_service.py`
- Commentaire : "Pour l'instant, les générateurs legacy ne sont pas complètement implémentés"
- Utilise `_generate_legacy_fallback_question` qui ne gère PAS les figures

---

## 📊 Structure de données des questions

### Format actuel dans le preview JSON

```json
{
  "questions": [
    {
      "id": "q1",
      "enonce_brut": "Le point A(3, 5) a pour symétrique...",
      "data": {},  ← Vide actuellement
      "solution_brut": "Par symétrie axiale...",
      "metadata": {
        "generator": "legacy",
        "fallback": true
      }
    }
  ]
}
```

### Format souhaité (avec figures)

```json
{
  "questions": [
    {
      "id": "q1",
      "enonce_brut": "Le point A(3, 5) a pour symétrique...",
      "data": {
        "figure": {  ← Figure géométrique
          "type": "symetrie_axiale",
          "points": ["A", "A'"],
          "longueurs_connues": {
            "A_x": 3,
            "A_y": 5,
            "A'_x": 7,
            "A'_y": 5
          }
        }
      },
      "figure_html": "<svg>...</svg>",  ← SVG rendu (NOUVEAU)
      "solution_brut": "Par symétrie axiale...",
      "metadata": {
        "generator": "legacy",
        "has_figure": true
      }
    }
  ]
}
```

---

## 🎨 Intégration dans les templates HTML/PDF

### Templates Standard (`mathalea_sheet_pdf_builder.py`)

**Fonction `_render_exercise`** (ligne ~250-300) :
- Génère le HTML pour chaque exercice
- Structure actuelle :
  ```html
  <div class="exercise">
    <div class="exercise-header">
      <h2>Exercice 1</h2>
    </div>
    <div class="exercise-questions">
      <div class="question">
        <p class="question-text">{enonce_brut}</p>
        <!-- Pas de figure ici actuellement ❌ -->
      </div>
    </div>
  </div>
  ```

**Modification nécessaire** :
```html
<div class="exercise-questions">
  <div class="question">
    <p class="question-text">{enonce_brut}</p>
    
    {% if question.figure_html %}  ← AJOUT
    <div class="exercise-figure">
      {{ question.figure_html | safe }}
    </div>
    {% endif %}
    
  </div>
</div>
```

### Templates Pro (Jinja2 historiques)

**Fichiers** :
- `/app/backend/templates/sujet_classique.html`
- `/app/backend/templates/corrige_classique.html`
- `/app/backend/templates/sujet_academique.html`
- `/app/backend/templates/corrige_academique.html`

**Modification nécessaire** : Similaire aux templates standard
- Détecter si `question.figure_html` existe
- L'insérer dans un bloc stylisé

---

## 🔧 Plan d'action technique (Étapes 2-5)

### Étape 2 : Enrichir le service de génération

**Fichier** : `/app/backend/services/exercise_template_service.py`

**Fonction à modifier** : `_generate_legacy_questions` (ligne 453)

**Changements nécessaires** :

1. **Remplacer le fallback par un vrai appel au générateur legacy** :
```python
# AVANT (ligne 517)
question = self._generate_legacy_fallback_question(...)

# APRÈS
# Appeler le vrai générateur legacy
legacy_service = MathGenerationService()
spec = legacy_service.generate_exercise(
    niveau=exercise_type.niveau,
    chapitre=exercise_type.domaine,
    type_exercice=legacy_type,
    difficulte=difficulty
)

# Convertir MathExerciseSpec → Question avec figure
question = self._convert_math_spec_to_question(spec, question_number)
```

2. **Créer une nouvelle fonction `_convert_math_spec_to_question`** :
```python
def _convert_math_spec_to_question(
    self,
    spec: MathExerciseSpec,
    question_number: int
) -> Dict[str, Any]:
    """
    Convertit un MathExerciseSpec (avec figure_geometrique)
    en question au format standardisé (avec figure_html)
    """
    question = {
        "id": f"q{question_number}",
        "enonce_brut": spec.question_text,  # À extraire de spec
        "data": {},
        "solution_brut": spec.solution_text,  # À extraire de spec
        "metadata": {
            "generator": "legacy",
            "has_figure": spec.figure_geometrique is not None
        }
    }
    
    # GÉNÉRER LE SVG si figure présente
    if spec.figure_geometrique:
        figure_svg = self._render_figure_to_svg(spec.figure_geometrique)
        question["figure_html"] = figure_svg
        question["data"]["figure"] = spec.figure_geometrique.dict()
    
    return question
```

3. **Créer une fonction `_render_figure_to_svg`** :
```python
def _render_figure_to_svg(self, figure: GeometricFigure) -> str:
    """
    Convertit une GeometricFigure en SVG HTML
    """
    from services.geometry_render_service import GeometryRenderService
    from render_schema import schema_renderer
    
    if figure.type == "symetrie_axiale":
        # Utiliser GeometryRenderService
        service = GeometryRenderService()
        svg = service.render_figure(figure)
        return svg
    
    elif figure.type in ["triangle", "rectangle", "cercle", etc.]:
        # Utiliser SchemaRenderer
        schema_data = {
            "type": figure.type,
            "points": figure.points,
            ...
        }
        svg = schema_renderer.render_to_svg(schema_data)
        return svg
    
    else:
        return ""  # Pas de figure pour ce type
```

### Étape 3 : Afficher dans le preview HTML

**Fichier** : `/app/frontend/src/components/SheetPreviewModal.js`

**Modification dans le rendu des questions** :
```jsx
{question.enonce_brut && (
  <p className="question-text">{question.enonce_brut}</p>
)}

{/* AJOUT : Affichage de la figure */}
{question.figure_html && (
  <div 
    className="exercise-figure"
    dangerouslySetInnerHTML={{ __html: question.figure_html }}
  />
)}
```

**Style CSS à ajouter** :
```css
.exercise-figure {
  margin: 20px auto;
  text-align: center;
  max-width: 100%;
}

.exercise-figure svg {
  max-width: 100%;
  height: auto;
}
```

### Étape 4 : Intégrer dans les PDFs standard

**Fichier** : `/app/backend/engine/pdf_engine/mathalea_sheet_pdf_builder.py`

**Fonction `_render_exercise`** :
- Ajouter le rendu de `figure_html` dans le HTML de chaque question

### Étape 5 : Intégrer dans les PDFs Pro

**Fichiers** : Templates Jinja2 historiques

**Modification** : Ajouter bloc conditionnel pour les figures

---

## ✅ Exercices legacy avec figures identifiés

| Type d'exercice | Legacy Generator ID | Fichier | Ligne | Figure |
|----------------|---------------------|---------|-------|--------|
| Symétrie axiale | SYMETRIE_AXIALE | math_generation_service.py | 1493 | ✅ |
| Aires triangles | AIRES_FIGURES | math_generation_service.py | 320 | ✅ |
| Périmètres | PERIMETRES | math_generation_service.py | 609 | ✅ |
| Pythagore | PYTHAGORE | math_generation_service.py | 699, 739, 774 | ✅ |
| Thalès | THALES | math_generation_service.py | 828, 1222, 1259 | ✅ |
| Triangles rect. | TRIANGLES_RECTANGLES | math_generation_service.py | 1379, 1490 | ✅ |
| Triangles qq. | TRIANGLES | math_generation_service.py | 1617, 1781 | ✅ |
| Volumes | VOLUMES | math_generation_service.py | 1973, 2075 | ✅ |

---

## 🚨 Points d'attention

1. **Sécurité HTML** :
   - Les SVG doivent être générés côté backend (contrôlé)
   - Utiliser `dangerouslySetInnerHTML` uniquement avec contenu backend
   - Pas d'injection de contenu utilisateur dans les SVG

2. **Performance** :
   - Génération SVG peut être coûteuse (matplotlib)
   - Considérer une mise en cache si nécessaire
   - Limiter la taille des SVG (max-width CSS)

3. **Compatibilité WeasyPrint** :
   - WeasyPrint supporte les SVG inline
   - Éviter les `<foreignObject>` (non supportés)
   - Tester la génération PDF après chaque modification

4. **Fallback gracieux** :
   - Si génération SVG échoue → log erreur mais ne pas crash
   - Afficher l'exercice sans figure plutôt que tout casser

---

## 📝 Prochaines étapes

**Étape 2** : Implémenter `_convert_math_spec_to_question` et `_render_figure_to_svg`
**Étape 3** : Modifier `SheetPreviewModal.js` pour afficher les figures
**Étape 4** : Intégrer dans `mathalea_sheet_pdf_builder.py`
**Étape 5** : Intégrer dans les templates Pro Jinja2
**Étape 6** : Tests et validation

---

**Date** : Décembre 2024
**Status** : ✅ Cartographie complète
**Prochaine étape** : Implémentation Étape 2
