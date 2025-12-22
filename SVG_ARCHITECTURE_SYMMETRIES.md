# 🎨 Architecture SVG pour les Symétries

## 📋 Vue d'ensemble

Ce document explique l'architecture du système de rendu SVG pour les transformations géométriques (Symétrie axiale, Symétrie centrale, etc.) et comment l'étendre pour de nouvelles transformations.

---

## 🏗️ Architecture actuelle

### 1. Services impliqués

```
┌─────────────────────────────────────────────────────────┐
│  Générateur d'exercices                                  │
│  (services/math_generation_service.py)                   │
│                                                          │
│  _gen_symetrie_axiale()                                 │
│  → Crée MathExerciseSpec avec figure_geometrique       │
└────────────────┬─────────────────────────────────────────┘
                 │
                 │ GeometricFigure
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Service de rendu géométrique                            │
│  (services/geometry_render_service.py)                   │
│                                                          │
│  render_figure_to_svg(figure)                           │
│  ├─ _render_symetrie_axiale(figure)                    │
│  ├─ _render_cercle(figure)                             │
│  ├─ _render_triangle_rectangle(figure)                 │
│  └─ ...                                                 │
└────────────────┬─────────────────────────────────────────┘
                 │
                 │ data: Dict
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Renderer SVG bas niveau                                 │
│  (geometry_svg_renderer.py)                              │
│                                                          │
│  GeometrySVGRenderer                                     │
│  ├─ render_symetrie_axiale(data)                       │
│  ├─ render_cercle(data)                                │
│  ├─ add_line(), add_point()                            │
│  └─ create_svg_root()                                  │
└────────────────┬─────────────────────────────────────────┘
                 │
                 │ SVG string
                 ▼
┌─────────────────────────────────────────────────────────┐
│  API / Frontend / PDF                                    │
│  → figure_svg injecté dans l'exercice                   │
│  → Affiché en HTML / Export PDF                         │
└──────────────────────────────────────────────────────────┘
```

---

## 🔧 Implémentation actuelle : Symétrie axiale

### 1. Générateur d'exercices

**Fichier** : `/app/backend/services/math_generation_service.py`

**Méthode** : `_gen_symetrie_axiale()`

```python
def _gen_symetrie_axiale(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
    # ... logique de génération ...
    
    # Créer la figure géométrique avec les données
    figure = GeometricFigure(
        type="symetrie_axiale",
        points=[point_original, point_image],
        longueurs_connues={
            f"{point_original}_x": point_x,
            f"{point_original}_y": point_y,
            f"{point_image}_x": image_x,
            f"{point_image}_y": image_y
        },
        proprietes=[f"axe_{axe_type}", f"axe_position_{axe_position}"]
    )
    
    return MathExerciseSpec(
        # ...
        figure_geometrique=figure
    )
```

**Données requises dans `GeometricFigure`** :
- **type** : `"symetrie_axiale"`
- **points** : Liste des labels (ex: `["D", "E"]`)
- **longueurs_connues** : Coordonnées des points en format plat :
  - `"D_x"`: coordonnée x du point D
  - `"D_y"`: coordonnée y du point D
  - `"E_x"`: coordonnée x du point E
  - `"E_y"`: coordonnée y du point E
- **proprietes** : Métadonnées de l'axe :
  - `"axe_vertical"` | `"axe_horizontal"` | `"axe_oblique"`
  - `"axe_position_5"` (pour un axe x=5 ou y=5)

---

### 2. Service de rendu

**Fichier** : `/app/backend/services/geometry_render_service.py`

**Méthode** : `_render_symetrie_axiale()`

```python
def _render_symetrie_axiale(self, figure: GeometricFigure) -> str:
    # Extraire les coordonnées
    coords = {}
    for key, val in figure.longueurs_connues.items():
        coords[key] = val
    
    # Extraire le type d'axe
    axe_type = "vertical"
    axe_position = 5
    
    for prop in figure.proprietes:
        if prop.startswith("axe_"):
            # Parser les propriétés
            ...
    
    # Construire les données pour le renderer
    data = {
        "axe_type": axe_type,
        "axe_position": axe_position,
        "points_coords": coords,
        "points_labels": figure.points
    }
    
    return self.renderer.render_symetrie_axiale(data)
```

**Rôle** : Transformer `GeometricFigure` en structure de données simple pour le renderer SVG.

---

### 3. Renderer SVG

**Fichier** : `/app/backend/geometry_svg_renderer.py`

**Méthode** : `render_symetrie_axiale()`

```python
def render_symetrie_axiale(self, data: Dict[str, Any]) -> str:
    svg = self.create_svg_root()
    
    # 1. Dessiner le repère (axes X et Y)
    # 2. Dessiner l'axe de symétrie (rouge, pointillés)
    # 3. Dessiner les points (original et symétrique)
    # 4. Dessiner le segment entre les points
    
    return ET.tostring(svg, encoding='unicode')
```

**Éléments SVG générés** :
- Axes de coordonnées (gris clair)
- Axe de symétrie (rouge, pointillés, avec label "x = 5" ou "y = 6")
- Points (cercles noirs avec labels)
- Segment entre les points (bleu)
- Point milieu (rouge, sur l'axe)

---

## 🔄 Comment réutiliser pour Symétrie centrale

### 1. Créer le générateur

**Fichier** : `/app/backend/services/math_generation_service.py`

```python
def _gen_symetrie_centrale(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
    # Logique similaire à symetrie_axiale
    
    # Point central de symétrie
    centre_x = random.randint(4, 10)
    centre_y = random.randint(4, 10)
    
    # Point original
    point_x = random.randint(1, 8)
    point_y = random.randint(1, 8)
    
    # Calcul du symétrique par rapport au centre
    # Formule : M' = 2*O - M
    image_x = 2 * centre_x - point_x
    image_y = 2 * centre_y - point_y
    
    figure = GeometricFigure(
        type="symetrie_centrale",  # ✅ Nouveau type
        points=[point_original, centre_label, point_image],
        longueurs_connues={
            f"{point_original}_x": point_x,
            f"{point_original}_y": point_y,
            f"{centre_label}_x": centre_x,
            f"{centre_label}_y": centre_y,
            f"{point_image}_x": image_x,
            f"{point_image}_y": image_y
        },
        proprietes=[f"centre_symetrie"]
    )
    
    return MathExerciseSpec(...)
```

---

### 2. Ajouter le handler dans geometry_render_service.py

```python
# Dans render_figure_to_svg():
elif figure_type == "symetrie_centrale":
    return self._render_symetrie_centrale(figure)

# Nouvelle méthode:
def _render_symetrie_centrale(self, figure: GeometricFigure) -> str:
    coords = {}
    for key, val in figure.longueurs_connues.items():
        coords[key] = val
    
    data = {
        "points_coords": coords,
        "points_labels": figure.points
    }
    
    return self.renderer.render_symetrie_centrale(data)
```

---

### 3. Créer le renderer SVG

**Fichier** : `/app/backend/geometry_svg_renderer.py`

```python
def render_symetrie_centrale(self, data: Dict[str, Any]) -> str:
    svg = self.create_svg_root()
    
    # 1. Dessiner le repère
    # 2. Dessiner le centre de symétrie (croix ou point plus gros)
    # 3. Dessiner les deux points (original et symétrique)
    # 4. Dessiner les segments :
    #    - Point original → Centre
    #    - Centre → Point symétrique
    # 5. Montrer que le centre est le milieu
    
    return ET.tostring(svg, encoding='unicode')
```

**Différences visuelles avec Symétrie axiale** :
- Pas d'axe, mais un **point central** marqué
- Les **2 segments** (M→O et O→M') sont de même longueur
- Le centre O est le **milieu du segment MM'**

---

## 🎯 Template générique pour toute transformation

Pour ajouter une nouvelle transformation géométrique (homothétie, rotation, translation, etc.) :

### Étape 1 : Générateur

```python
def _gen_transformation_X(self, niveau, chapitre, difficulte):
    # 1. Générer les paramètres mathématiques
    # 2. Calculer les images/résultats
    # 3. Créer GeometricFigure avec :
    figure = GeometricFigure(
        type="nom_transformation",  # identifiant unique
        points=["A", "B", ...],
        longueurs_connues={"A_x": ..., "A_y": ...},
        proprietes=["param1", "param2"]
    )
```

### Étape 2 : Handler dans geometry_render_service.py

```python
elif figure_type == "nom_transformation":
    return self._render_nom_transformation(figure)

def _render_nom_transformation(self, figure):
    data = {...}  # Extraire et formater les données
    return self.renderer.render_nom_transformation(data)
```

### Étape 3 : Renderer SVG

```python
def render_nom_transformation(self, data):
    svg = self.create_svg_root()
    
    # Utiliser les méthodes helper:
    # - add_line(svg, line)
    # - add_point(svg, point)
    # - ET.SubElement() pour éléments personnalisés
    
    return ET.tostring(svg, encoding='unicode')
```

---

## 📦 Méthodes helper disponibles

### Dans GeometrySVGRenderer

```python
# Création
create_svg_root() -> ET.Element

# Ajout d'éléments
add_line(svg, line: Line)
add_point(svg, point: Point, show_label=True)
add_right_angle_mark(svg, vertex, p1, p2)
add_dimension_label(svg, line, text)

# Classes utilitaires
Point(x, y, label)
Line(start_point, end_point, style="solid", color="#000000")
```

---

## 🧪 Tests à créer

Pour chaque nouvelle transformation :

1. **Test unitaire** : Génération de la figure
2. **Test SVG** : Présence des éléments essentiels
3. **Test API** : figure_svg retourné par l'API
4. **Test PDF** (optionnel) : SVG présent dans le PDF

Exemple :
```python
def test_transformation_X_svg():
    spec = math_service._gen_transformation_X(...)
    svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
    
    assert svg is not None
    assert "<svg" in svg
    assert "element_specifique" in svg
```

---

## 📝 Checklist pour nouvelle transformation

- [ ] Ajouter le type dans `MathExerciseType` (models/math_models.py)
- [ ] Créer `_gen_transformation_X()` dans math_generation_service.py
- [ ] Ajouter mapping chapitre → type
- [ ] Créer `_render_transformation_X()` dans geometry_render_service.py
- [ ] Créer `render_transformation_X()` dans geometry_svg_renderer.py
- [ ] Créer tests unitaires + API
- [ ] Documenter les coordonnées attendues
- [ ] Vérifier l'affichage en preview HTML
- [ ] Vérifier l'export PDF

---

## 🎨 Bonnes pratiques visuelles

### Couleurs recommandées

```python
COLORS = {
    'axes': '#CCCCCC',           # Gris clair pour les axes de coordonnées
    'construction': '#FF6600',    # Orange MathALÉA pour lignes de construction
    'symetrie_axe': '#FF0000',   # Rouge pour axe de symétrie
    'symetrie_centre': '#FF0000', # Rouge pour centre de symétrie
    'points': '#000000',          # Noir pour les points
    'segments': '#0066CC',        # Bleu pour segments principaux
    'text': '#000000'             # Noir pour texte
}
```

### Tailles recommandées

```python
SIZES = {
    'point_radius': 3,            # Rayon des points
    'line_width': 1.5,            # Épaisseur des lignes normales
    'construction_width': 2.0,    # Épaisseur lignes construction
    'text_size': 14,              # Taille du texte
    'margin': 40,                 # Marge autour du SVG
    'width': 400,                 # Largeur SVG
    'height': 300                 # Hauteur SVG
}
```

### Styles de ligne

- **Solide** : Figures principales, segments
- **Pointillés** (`dashed`) : Axes de symétrie, lignes de construction
- **Épaisseur 2px** : Éléments importants (axe de symétrie, centre)

---

## 📖 Exemples de code complets

### Exemple : Symétrie axiale verticale

```python
# Données d'entrée
data = {
    "axe_type": "vertical",
    "axe_position": 5,
    "points_coords": {
        "D_x": 3,
        "D_y": 7,
        "E_x": 7,
        "E_y": 7
    },
    "points_labels": ["D", "E"]
}

# Rendu SVG
svg = renderer.render_symetrie_axiale(data)

# Résultat : SVG avec :
# - Repère cartésien
# - Axe vertical rouge en x=5
# - Point D(3,7) et E(7,7)
# - Segment D-E
# - Label "x = 5"
```

---

## 🔮 Évolutions futures possibles

1. **Animations SVG** : Montrer la transformation étape par étape
2. **Interactivité** : Points déplaçables pour explorer
3. **Grille de fond** : Option pour afficher un quadrillage
4. **Export haute résolution** : SVG optimisé pour impression
5. **Thèmes** : Mode clair/sombre, couleurs personnalisables
6. **Mesures dynamiques** : Calcul automatique des distances/angles

---

## ✅ Résumé

L'architecture SVG est **modulaire**, **extensible** et **testée**. 

Pour ajouter une nouvelle transformation :
1. Définir les données mathématiques (coords, paramètres)
2. Créer le générateur qui remplit `GeometricFigure`
3. Créer le renderer SVG qui dessine les éléments
4. Tester unitairement et via l'API
5. Documenter

**Symétrie axiale** sert de **référence complète** pour toutes les futures transformations.
