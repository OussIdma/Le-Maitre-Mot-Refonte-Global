# Cahier des Charges — Générateurs Dynamiques

**Version :** 1.1.0  
**Date :** 2025-01-XX  
**Objectif :** Définir les spécifications complètes pour créer et intégrer des générateurs d'exercices dynamiques dans Le Maître Mot.

**📚 PROCÉDURES COMPLÉMENTAIRES :**
- **Création d'un générateur** : `docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md` (procédure pas-à-pas industrialisée)
- **Ajout d'un template** : `docs/PROCEDURE_AJOUT_TEMPLATE_DYNAMIQUE.md` (une fois le générateur créé)

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture technique](#architecture-technique)
3. [Structure d'un générateur](#structure-dun-générateur)
4. [Définition des paramètres](#définition-des-paramètres)
5. [Templates HTML](#templates-html)
6. [Génération SVG](#génération-svg)
7. [Mapping multi-chapitres](#mapping-multi-chapitres)
8. [Presets pédagogiques](#presets-pédagogiques)
9. [Validation et tests](#validation-et-tests)
10. [Exemple complet](#exemple-complet)
11. [Checklist d'intégration](#checklist-dintégration)
12. [Génération d'un exercice : flux complet](#génération-dun-exercice--flux-complet)

---

## 🎯 Vue d'ensemble

### Objectifs

Un **générateur dynamique** est un composant Python qui :
- Génère des exercices mathématiques de manière **déterministe** (même seed = même résultat)
- Accepte des **paramètres configurables** (difficulté, type de figure, etc.)
- Produit des **variables** pour remplir des templates HTML
- Génère des **SVG** pour les figures géométriques (si applicable)
- Peut être **mappé à plusieurs chapitres** du curriculum

### Exemple de cas d'usage

**Générateur "Pythagore"** :
- Chapitre 1 : "Triangle rectangle - Calcul d'hypoténuse" (6e)
- Chapitre 2 : "Triangle rectangle - Calcul d'un côté" (5e)
- Chapitre 3 : "Triangle rectangle - Vérification" (4e)

**Un seul générateur** → **3 chapitres différents** avec des templates et paramètres différents.

---

## 🏗 Architecture technique

### Hiérarchie des classes

```
BaseGenerator (abstract)
    ├── SymetrieAxialeV2Generator
    ├── ThalesV2Generator
    └── [VotreGénérateur]
```

### Flux d'exécution

```
1. Admin crée un exercice dynamique
   └─> Stocke: generator_key, variables (params), template_variants

2. Élève demande un exercice
   └─> Backend appelle GeneratorFactory.generate()
       ├─> Valide les paramètres
       ├─> Génère variables + geo_data + SVG
       └─> Remplit les templates HTML avec les variables

3. Frontend affiche
   └─> Énoncé HTML + SVG énoncé
   └─> Solution HTML + SVG solution
```

### Fichiers à créer

```
backend/generators/
    ├── votre_generateur.py          # Votre générateur
    └── [optionnel] votre_generateur_v2.py  # Si adaptation d'un legacy
```

---

## 📦 Structure d'un générateur

### Template minimal

```python
"""
Générateur VOTRE_GENERATEUR_V1 - Description courte
===================================================

Version: 1.0.0

Description détaillée du générateur.
"""

from typing import Dict, Any, List, Optional
from backend.generators.base_generator import (
    BaseGenerator,
    GeneratorMeta,
    ParamSchema,
    Preset,
    ParamType,
    create_svg_wrapper,  # Si SVG nécessaire
)
from backend.generators.factory import GeneratorFactory


@GeneratorFactory.register
class VotreGenerateurV1Generator(BaseGenerator):
    """Description du générateur."""
    
    # Constantes de configuration
    CONSTANTE_1 = 10
    CONSTANTE_2 = 20
    
    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        """Métadonnées du générateur."""
        return GeneratorMeta(
            key="VOTRE_GENERATEUR_V1",
            label="Nom lisible",
            description="Description complète",
            version="1.0.0",
            niveaux=["6e", "5e"],  # Niveaux supportés
            exercise_type="VOTRE_TYPE",  # Doit correspondre à un MathExerciseType
            svg_mode="AUTO",  # "AUTO" ou "MANUAL"
            supports_double_svg=True,  # SVG séparés énoncé/solution
            pedagogical_tips="⚠️ Conseils pédagogiques (optionnel)"
        )
    
    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        """Définit les paramètres acceptés."""
        return [
            ParamSchema(
                name="param1",
                type=ParamType.ENUM,
                description="Description du paramètre",
                default="valeur_par_defaut",
                options=["option1", "option2", "option3"]
            ),
            # ... autres paramètres
        ]
    
    @classmethod
    def get_presets(cls) -> List[Preset]:
        """Presets pédagogiques prédéfinis."""
        return [
            Preset(
                key="6e_facile",
                label="6e Facile - Description",
                description="Description détaillée du preset",
                niveau="6e",
                params={
                    "param1": "valeur1",
                    "param2": "valeur2",
                }
            ),
            # ... autres presets
        ]
    
    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un exercice complet.
        
        Args:
            params: Paramètres validés (depuis schema)
            
        Returns:
            Dict avec:
            - variables: dict pour templates HTML
            - geo_data: données géométriques JSON-safe (si applicable)
            - figure_svg_enonce: SVG énoncé (si applicable)
            - figure_svg_solution: SVG solution (si applicable)
            - meta: métadonnées de l'exercice généré
            - results: résultats calculés (optionnel)
        """
        # 1. Générer les données de l'exercice
        # 2. Construire les variables pour les templates
        # 3. Générer les SVG (si nécessaire)
        # 4. Retourner le dict complet
        
        variables = self._build_variables(params)
        geo_data = self._build_geo_data(params)  # Si géométrie
        svg_enonce = self._generate_svg_enonce(geo_data, params)  # Si SVG
        svg_solution = self._generate_svg_solution(geo_data, params)  # Si SVG
        
        return {
            "variables": variables,
            "geo_data": geo_data,  # Optionnel
            "figure_svg_enonce": svg_enonce,  # Optionnel
            "figure_svg_solution": svg_solution,  # Optionnel
            "meta": {
                "exercise_type": "VOTRE_TYPE",
                "svg_mode": "AUTO",
                # ... autres métadonnées
            },
            "results": {}  # Optionnel
        }
    
    # Méthodes privées pour la logique interne
    def _build_variables(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Construit les variables pour les templates HTML."""
        pass
    
    def _build_geo_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Construit les données géométriques JSON-safe."""
        pass
    
    def _generate_svg_enonce(self, geo_data: Dict, params: Dict) -> str:
        """Génère le SVG de l'énoncé."""
        pass
    
    def _generate_svg_solution(self, geo_data: Dict, params: Dict) -> str:
        """Génère le SVG de la solution."""
        pass
```

---

## ⚙️ Définition des paramètres

### Types de paramètres supportés

| Type | Description | Exemple |
|------|-------------|---------|
| `ParamType.INT` | Entier | `ParamSchema(name="nombre", type=ParamType.INT, default=5, min=1, max=10)` |
| `ParamType.FLOAT` | Décimal | `ParamSchema(name="coefficient", type=ParamType.FLOAT, default=2.5, min=0.5, max=10.0)` |
| `ParamType.BOOL` | Booléen | `ParamSchema(name="show_grid", type=ParamType.BOOL, default=True)` |
| `ParamType.ENUM` | Liste de valeurs | `ParamSchema(name="figure_type", type=ParamType.ENUM, default="carre", options=["carre", "rectangle", "triangle"])` |
| `ParamType.STRING` | Texte | `ParamSchema(name="label", type=ParamType.STRING, default="A")` |

### Règles de validation

- **`required=True`** : Le paramètre est obligatoire
- **`min` / `max`** : Pour INT et FLOAT uniquement
- **`options`** : Pour ENUM uniquement (liste des valeurs autorisées)
- **`default`** : Valeur par défaut si non fournie

### Exemple complet

```python
@classmethod
def get_schema(cls) -> List[ParamSchema]:
    return [
        ParamSchema(
            name="figure_type",
            type=ParamType.ENUM,
            description="Type de figure géométrique",
            default="carre",
            options=["carre", "rectangle", "triangle"]
        ),
        ParamSchema(
            name="difficulty",
            type=ParamType.ENUM,
            description="Niveau de difficulté",
            default="moyen",
            options=["facile", "moyen", "difficile"]
        ),
        ParamSchema(
            name="coefficient",
            type=ParamType.FLOAT,
            description="Coefficient de transformation",
            default=2.0,
            min=0.5,
            max=10.0
        ),
        ParamSchema(
            name="show_grid",
            type=ParamType.BOOL,
            description="Afficher la grille",
            default=True
        ),
        ParamSchema(
            name="nombre_points",
            type=ParamType.INT,
            description="Nombre de points à générer",
            default=3,
            min=2,
            max=10,
            required=True
        )
    ]
```

---

## 📝 Templates HTML

### Format des placeholders

Les templates utilisent la syntaxe **`{{variable}}`** pour les placeholders.

```html
<p>Le côté initial mesure <strong>{{cote_initial}} cm</strong>.</p>
<p>Après transformation, le côté final mesure <strong>{{cote_final}} cm</strong>.</p>
```

### Variables disponibles

Les variables sont définies dans la méthode `_build_variables()` du générateur.

**Règles importantes :**
- ✅ Tous les placeholders utilisés dans les templates **DOIVENT** être présents dans `variables`
- ✅ Les valeurs doivent être **JSON-safe** (pas d'objets Python complexes)
- ✅ Les nombres peuvent être `int`, `float`, ou `str` (formatage)
- ✅ Les listes doivent être des listes Python simples (pas de tuples)

### Exemple de template énoncé

```html
<p><strong>Agrandissement d'{{figure_type_article}} :</strong></p>
<p>On considère {{figure_type_article}} de côté <strong>{{cote_initial}} cm</strong>.</p>
<p>On effectue un <strong>{{transformation}}</strong> de coefficient <strong>{{coefficient_str}}</strong>.</p>
<p><em>Question :</em> Quelle est la mesure du côté de la figure obtenue ?</p>
```

### Exemple de template solution

```html
<h4>Correction détaillée</h4>
<ol>
  <li><strong>Compréhension :</strong> On a {{figure_type_article}} de côté {{cote_initial}} cm.</li>
  <li><strong>Méthode :</strong> On multiplie chaque dimension par {{coefficient_str}}.</li>
  <li><strong>Calculs :</strong> {{cote_initial}} × {{coefficient_str}} = <strong>{{cote_final}} cm</strong></li>
  <li><strong>Conclusion :</strong> Le côté final mesure <strong>{{cote_final}} cm</strong>.</li>
</ol>
```

### Template variants (multi-variants)

Un exercice peut avoir **plusieurs variants** de templates pour varier la formulation :

```json
{
  "template_variants": [
    {
      "id": "v1",
      "label": "Formulation directe",
      "enonce_template_html": "<p>Calcule {{valeur1}} + {{valeur2}}.</p>",
      "solution_template_html": "<p>Résultat : {{resultat}}</p>",
      "weight": 1
    },
    {
      "id": "v2",
      "label": "Formulation contextuelle",
      "enonce_template_html": "<p>Marie a {{valeur1}} pommes. Elle en achète {{valeur2}} de plus. Combien en a-t-elle maintenant ?</p>",
      "solution_template_html": "<p>Total : {{valeur1}} + {{valeur2}} = {{resultat}} pommes.</p>",
      "weight": 1
    }
  ]
}
```

Le système sélectionne automatiquement un variant selon le `seed` (déterministe).

---

## 🎨 Génération SVG

### Quand générer des SVG ?

- ✅ **Géométrie** : Figures, graphiques, schémas
- ✅ **Représentations visuelles** : Diagrammes, tableaux visuels
- ❌ **Calculs purs** : Pas besoin de SVG

### Structure SVG

Les SVG doivent être **autonomes** (avec viewBox, width, height) :

```python
def _generate_svg_enonce(self, geo_data: Dict, params: Dict) -> str:
    """Génère le SVG de l'énoncé."""
    width = 400
    height = 300
    viewbox = "0 0 400 300"
    
    content = f"""
    <circle cx="100" cy="100" r="50" fill="#1976d2"/>
    <text x="100" y="100" text-anchor="middle" fill="white">A</text>
    """
    
    return create_svg_wrapper(content, width, height, viewbox)
```

### Utilisation de `create_svg_wrapper()`

```python
from backend.generators.base_generator import create_svg_wrapper

svg = create_svg_wrapper(
    content="<circle cx='50' cy='50' r='20'/>",
    width=200,
    height=200,
    viewbox="0 0 200 200"  # Optionnel
)
```

### SVG énoncé vs solution

- **`figure_svg_enonce`** : Figure sans la solution (élève doit construire)
- **`figure_svg_solution`** : Figure avec la solution complète

**Exemple (Symétrie axiale) :**
- Énoncé : Figure originale + axe (sans symétrique)
- Solution : Figure originale + axe + symétrique

### Données géométriques JSON-safe

Si vous générez des SVG, stockez aussi les données brutes dans `geo_data` :

```python
geo_data = {
    "points": [
        {"x": 1, "y": 2, "label": "A"},
        {"x": 3, "y": 4, "label": "B"}
    ],
    "figure_type": "triangle",
    "bounds": {"min_x": 0, "max_x": 10, "min_y": 0, "max_y": 10}
}
```

**Règles :**
- ✅ Utiliser des `dict` et `list` Python (pas de tuples, sets, etc.)
- ✅ Tous les nombres doivent être `int`, `float`, ou `str`
- ✅ Pas d'objets Python complexes (datetime, etc.)

---

## 🔗 Mapping multi-chapitres

### Principe

**Un générateur peut être utilisé par plusieurs chapitres** avec des configurations différentes.

### Exemple : Générateur "Pythagore"

**Chapitre 1 : "Triangle rectangle - Hypothénuse" (6e)**
```json
{
  "generator_key": "PYTHAGORE_V1",
  "variables": {
    "question_type": "hypotenuse",
    "difficulty": "facile"
  },
  "enonce_template_html": "<p>Calcule l'hypoténuse d'un triangle rectangle de côtés {{cote1}} cm et {{cote2}} cm.</p>"
}
```

**Chapitre 2 : "Triangle rectangle - Côté" (5e)**
```json
{
  "generator_key": "PYTHAGORE_V1",
  "variables": {
    "question_type": "cote",
    "difficulty": "moyen"
  },
  "enonce_template_html": "<p>Calcule le côté manquant d'un triangle rectangle d'hypoténuse {{hypotenuse}} cm et de côté {{cote_connu}} cm.</p>"
}
```

**Chapitre 3 : "Triangle rectangle - Vérification" (4e)**
```json
{
  "generator_key": "PYTHAGORE_V1",
  "variables": {
    "question_type": "verification",
    "difficulty": "difficile"
  },
  "enonce_template_html": "<p>Vérifie si un triangle de côtés {{cote1}}, {{cote2}}, {{cote3}} est rectangle.</p>"
}
```

### Implémentation dans le générateur

Le générateur doit gérer les différents `question_type` :

```python
def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
    question_type = params.get("question_type", "hypotenuse")
    
    if question_type == "hypotenuse":
        return self._generate_hypotenuse(params)
    elif question_type == "cote":
        return self._generate_cote(params)
    elif question_type == "verification":
        return self._generate_verification(params)
    else:
        raise ValueError(f"Type de question inconnu: {question_type}")
```

### Paramètres par chapitre

Chaque chapitre peut définir ses propres paramètres dans l'exercice dynamique :

```json
{
  "chapter_code": "6e_PYTHAGORE_HYPOTENUSE",
  "generator_key": "PYTHAGORE_V1",
  "variables": {
    "question_type": "hypotenuse",
    "difficulty": "facile",
    "show_steps": true
  }
}
```

---

## 🎓 Presets pédagogiques

### Définition

Les **presets** sont des configurations prédéfinies pour faciliter la création d'exercices par les admins.

### Structure

```python
Preset(
    key="6e_facile",                    # Identifiant unique
    label="6e Facile - Description",    # Label lisible
    description="Description détaillée", # Explication
    niveau="6e",                        # Niveau cible
    params={                            # Paramètres du preset
        "figure_type": "carre",
        "difficulty": "facile",
        "show_grid": True
    }
)
```

### Exemple complet

```python
@classmethod
def get_presets(cls) -> List[Preset]:
    return [
        Preset(
            key="6e_facile",
            label="6e Facile - Carré simple",
            description="Agrandissement d'un carré avec coefficient entier",
            niveau="6e",
            params={
                "figure_type": "carre",
                "difficulty": "facile",
                "force_agrandissement": True
            }
        ),
        Preset(
            key="6e_moyen",
            label="6e Moyen - Figures variées",
            description="Transformations avec coefficients simples",
            niveau="6e",
            params={
                "figure_type": "rectangle",
                "difficulty": "moyen"
            }
        ),
        Preset(
            key="5e_difficile",
            label="5e Difficile - Calcul d'aires",
            description="Focus sur le rapport des aires",
            niveau="5e",
            params={
                "figure_type": "triangle",
                "difficulty": "difficile"
            }
        )
    ]
```

### Utilisation par les admins

Les presets apparaissent dans l'interface admin lors de la création d'un exercice dynamique. L'admin peut :
1. Sélectionner un preset
2. Modifier les paramètres si nécessaire
3. Créer l'exercice

---

## ✅ Validation et tests

### Tests unitaires

Créer un fichier `backend/tests/test_votre_generateur.py` :

```python
import pytest
from backend.generators.votre_generateur import VotreGenerateurV1Generator


def test_generator_meta():
    """Test que les métadonnées sont correctes."""
    meta = VotreGenerateurV1Generator.get_meta()
    assert meta.key == "VOTRE_GENERATEUR_V1"
    assert "6e" in meta.niveaux


def test_generator_schema():
    """Test que le schéma est valide."""
    schema = VotreGenerateurV1Generator.get_schema()
    assert len(schema) > 0
    assert all(p.name for p in schema)


def test_generator_validation():
    """Test la validation des paramètres."""
    valid, result = VotreGenerateurV1Generator.validate_params({
        "param1": "valeur1",
        "param2": 5
    })
    assert valid is True
    assert "param1" in result


def test_generator_generation():
    """Test la génération d'un exercice."""
    gen = VotreGenerateurV1Generator(seed=42)
    result = gen.safe_generate({
        "param1": "valeur1"
    })
    
    assert "variables" in result
    assert "meta" in result
    assert result["meta"]["exercise_type"] == "VOTRE_TYPE"


def test_generator_determinism():
    """Test que le générateur est déterministe."""
    gen1 = VotreGenerateurV1Generator(seed=42)
    gen2 = VotreGenerateurV1Generator(seed=42)
    
    result1 = gen1.safe_generate({"param1": "valeur1"})
    result2 = gen2.safe_generate({"param1": "valeur1"})
    
    assert result1["variables"] == result2["variables"]


def test_generator_presets():
    """Test que les presets sont valides."""
    presets = VotreGenerateurV1Generator.get_presets()
    assert len(presets) > 0
    
    for preset in presets:
        # Valider que les paramètres du preset sont valides
        valid, _ = VotreGenerateurV1Generator.validate_params(preset.params)
        assert valid, f"Preset {preset.key} a des paramètres invalides"
```

### Tests d'intégration

Tester l'intégration avec le système complet :

```python
def test_generator_factory_integration():
    """Test que le générateur est bien enregistré dans la Factory."""
    from backend.generators.factory import GeneratorFactory
    
    gen_class = GeneratorFactory.get("VOTRE_GENERATEUR_V1")
    assert gen_class is not None
    assert gen_class == VotreGenerateurV1Generator


def test_generator_api_endpoint():
    """Test l'endpoint API de prévisualisation."""
    # Tester /api/v1/generators/preview-dynamic
    # avec generator_key="VOTRE_GENERATEUR_V1"
    pass
```

### Validation des templates

Vérifier que tous les placeholders sont résolus :

```python
def test_template_placeholders():
    """Test que tous les placeholders des templates sont fournis."""
    gen = VotreGenerateurV1Generator(seed=42)
    result = gen.safe_generate({})
    
    variables = result["variables"]
    
    # Extraire les placeholders d'un template exemple
    template = "<p>{{variable1}} et {{variable2}}</p>"
    import re
    placeholders = re.findall(r'\{\{(\w+)\}\}', template)
    
    # Vérifier que toutes les variables sont présentes
    for placeholder in placeholders:
        assert placeholder in variables, f"Placeholder {placeholder} manquant"
```

---

## 📚 Exemple complet

### Générateur "Périmètre Rectangle"

```python
"""
Générateur PERIMETRE_RECTANGLE_V1 - Calcul de périmètre
========================================================

Version: 1.0.0

Génère des exercices sur le calcul du périmètre d'un rectangle.
"""

from typing import Dict, Any, List, Optional
import random
from backend.generators.base_generator import (
    BaseGenerator,
    GeneratorMeta,
    ParamSchema,
    Preset,
    ParamType,
    create_svg_wrapper,
)
from backend.generators.factory import GeneratorFactory


@GeneratorFactory.register
class PerimetreRectangleV1Generator(BaseGenerator):
    """Générateur d'exercices sur le périmètre de rectangles."""
    
    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="PERIMETRE_RECTANGLE_V1",
            label="Périmètre Rectangle",
            description="Exercices sur le calcul du périmètre d'un rectangle",
            version="1.0.0",
            niveaux=["6e", "5e"],
            exercise_type="PERIMETRE",
            svg_mode="AUTO",
            supports_double_svg=True,
            pedagogical_tips="⚠️ Erreur fréquente: confusion périmètre/aire. Rappeler la formule P = 2 × (L + l)."
        )
    
    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        return [
            ParamSchema(
                name="question_type",
                type=ParamType.ENUM,
                description="Type de question",
                default="calcul_perimetre",
                options=["calcul_perimetre", "calcul_cote", "verification"]
            ),
            ParamSchema(
                name="difficulty",
                type=ParamType.ENUM,
                description="Niveau de difficulté",
                default="moyen",
                options=["facile", "moyen", "difficile"]
            ),
            ParamSchema(
                name="longueur_min",
                type=ParamType.INT,
                description="Longueur minimale (cm)",
                default=2,
                min=1,
                max=20
            ),
            ParamSchema(
                name="longueur_max",
                type=ParamType.INT,
                description="Longueur maximale (cm)",
                default=10,
                min=1,
                max=50
            ),
            ParamSchema(
                name="show_svg",
                type=ParamType.BOOL,
                description="Afficher le SVG du rectangle",
                default=True
            )
        ]
    
    @classmethod
    def get_presets(cls) -> List[Preset]:
        return [
            Preset(
                key="6e_facile",
                label="6e Facile - Calcul direct",
                description="Calcul du périmètre avec dimensions simples",
                niveau="6e",
                params={
                    "question_type": "calcul_perimetre",
                    "difficulty": "facile",
                    "longueur_min": 2,
                    "longueur_max": 5,
                    "show_svg": True
                }
            ),
            Preset(
                key="6e_moyen",
                label="6e Moyen - Calcul avec formule",
                description="Calcul du périmètre avec dimensions moyennes",
                niveau="6e",
                params={
                    "question_type": "calcul_perimetre",
                    "difficulty": "moyen",
                    "longueur_min": 5,
                    "longueur_max": 15,
                    "show_svg": True
                }
            ),
            Preset(
                key="5e_difficile",
                label="5e Difficile - Calcul d'un côté",
                description="Trouver une dimension à partir du périmètre",
                niveau="5e",
                params={
                    "question_type": "calcul_cote",
                    "difficulty": "difficile",
                    "longueur_min": 10,
                    "longueur_max": 30,
                    "show_svg": False
                }
            )
        ]
    
    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un exercice sur le périmètre."""
        
        question_type = params["question_type"]
        difficulty = params["difficulty"]
        longueur_min = params["longueur_min"]
        longueur_max = params["longueur_max"]
        show_svg = params["show_svg"]
        
        # Générer les dimensions
        longueur = self._rng.randint(longueur_min, longueur_max)
        largeur = self._rng.randint(longueur_min, longueur_max - 1)  # Différent de longueur
        
        # Calculer le périmètre
        perimetre = 2 * (longueur + largeur)
        
        # Construire les variables selon le type de question
        if question_type == "calcul_perimetre":
            variables = {
                "longueur": longueur,
                "largeur": largeur,
                "perimetre": perimetre,
                "question": "Quel est le périmètre de ce rectangle ?",
                "reponse": f"{perimetre} cm"
            }
        elif question_type == "calcul_cote":
            # On donne le périmètre et une dimension, on cherche l'autre
            cote_connu = longueur
            cote_inconnu = largeur
            variables = {
                "perimetre": perimetre,
                "cote_connu": cote_connu,
                "cote_inconnu": cote_inconnu,
                "question": f"Un rectangle a un périmètre de {perimetre} cm et une longueur de {cote_connu} cm. Quelle est sa largeur ?",
                "reponse": f"{cote_inconnu} cm"
            }
        else:  # verification
            # On donne 3 dimensions, on vérifie si c'est un rectangle
            variables = {
                "longueur": longueur,
                "largeur": largeur,
                "perimetre": perimetre,
                "question": f"Un rectangle a une longueur de {longueur} cm et une largeur de {largeur} cm. Son périmètre est-il {perimetre} cm ?",
                "reponse": "Oui" if perimetre == 2 * (longueur + largeur) else "Non"
            }
        
        # Données géométriques
        geo_data = {
            "longueur": longueur,
            "largeur": largeur,
            "perimetre": perimetre,
            "question_type": question_type
        }
        
        # SVG
        svg_enonce = None
        svg_solution = None
        if show_svg:
            svg_enonce = self._generate_svg_enonce(geo_data, params)
            svg_solution = self._generate_svg_solution(geo_data, params)
        
        return {
            "variables": variables,
            "geo_data": geo_data,
            "figure_svg_enonce": svg_enonce,
            "figure_svg_solution": svg_solution,
            "meta": {
                "exercise_type": "PERIMETRE",
                "svg_mode": "AUTO",
                "question_type": question_type,
                "difficulty": difficulty
            }
        }
    
    def _generate_svg_enonce(self, geo_data: Dict, params: Dict) -> str:
        """Génère le SVG du rectangle (énoncé)."""
        longueur = geo_data["longueur"]
        largeur = geo_data["largeur"]
        
        # Échelle : 1 cm = 20 pixels
        scale = 20
        width = longueur * scale + 40
        height = largeur * scale + 40
        
        rect_x = 20
        rect_y = 20
        rect_width = longueur * scale
        rect_height = largeur * scale
        
        content = f"""
        <rect x="{rect_x}" y="{rect_y}" width="{rect_width}" height="{rect_height}" 
              fill="none" stroke="#1976d2" stroke-width="3"/>
        <text x="{rect_x + rect_width/2}" y="{rect_y - 10}" text-anchor="middle" 
              font-size="14" fill="#1976d2">{longueur} cm</text>
        <text x="{rect_x - 30}" y="{rect_y + rect_height/2}" text-anchor="middle" 
              font-size="14" fill="#1976d2" transform="rotate(-90 {rect_x - 30} {rect_y + rect_height/2})">{largeur} cm</text>
        """
        
        return create_svg_wrapper(content, int(width), int(height))
    
    def _generate_svg_solution(self, geo_data: Dict, params: Dict) -> str:
        """Génère le SVG du rectangle (solution avec périmètre)."""
        # Même SVG que l'énoncé, mais avec le périmètre affiché
        svg_enonce = self._generate_svg_enonce(geo_data, params)
        
        # Ajouter le périmètre
        perimetre = geo_data["perimetre"]
        longueur = geo_data["longueur"]
        largeur = geo_data["largeur"]
        
        scale = 20
        rect_width = longueur * scale
        rect_height = largeur * scale
        
        # Extraire le contenu du SVG et ajouter le périmètre
        content_with_perimetre = svg_enonce.replace(
            "</svg>",
            f'<text x="{20 + rect_width/2}" y="{20 + rect_height + 30}" text-anchor="middle" '
            f'font-size="16" fill="#c62828" font-weight="bold">Périmètre = {perimetre} cm</text></svg>'
        )
        
        return content_with_perimetre
```

### Templates HTML associés

**Énoncé (calcul_perimetre) :**
```html
<p><strong>Calcul du périmètre</strong></p>
<p>Un rectangle a une longueur de <strong>{{longueur}} cm</strong> et une largeur de <strong>{{largeur}} cm</strong>.</p>
<p><em>{{question}}</em></p>
```

**Solution (calcul_perimetre) :**
```html
<h4>Correction</h4>
<ol>
  <li><strong>Formule :</strong> P = 2 × (L + l)</li>
  <li><strong>Calcul :</strong> P = 2 × ({{longueur}} + {{largeur}}) = 2 × {{longueur + largeur}} = <strong>{{perimetre}} cm</strong></li>
  <li><strong>Réponse :</strong> Le périmètre est de <strong>{{reponse}}</strong>.</li>
</ol>
```

---

## ✅ Checklist d'intégration

**📚 PROCÉDURE COMPLÈTE** : Voir `docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md` pour une procédure pas-à-pas industrialisée.

### Avant de soumettre votre générateur

#### Structure et imports

- [ ] **Fichier créé** : `backend/generators/votre_generateur.py`
- [ ] **Imports obligatoires** : `time`, `safe_random_choice`, `safe_randrange` présents
- [ ] **Décorateur** : `@GeneratorFactory.register` présent
- [ ] **Import dans factory.py** : Ajouté dans `_register_all_generators()` avec `try/except ImportError`

#### Métadonnées et schéma

- [ ] **Métadonnées** : `get_meta()` retourne un `GeneratorMeta` complet
- [ ] **Schéma** : `get_schema()` définit tous les paramètres avec validation
- [ ] **Paramètre difficulty** : Présent et obligatoire dans le schéma
- [ ] **Presets** : `get_presets()` contient au moins 1 preset par niveau supporté

#### Génération

- [ ] **Génération** : `generate()` retourne un dict avec `variables`, `meta`, et optionnellement `geo_data`, `figure_svg_enonce`, `figure_svg_solution`
- [ ] **Logs structurés** : `event=generate_in` et `event=generate_complete` présents
- [ ] **Duration** : `duration_ms` calculé avec `time.time()`
- [ ] **Safe random** : `safe_random_choice` / `safe_randrange` utilisés (pas `random.choice/randrange`)
- [ ] **Filtrage préventif** : Pools filtrées AVANT de choisir (éviter crash randrange)

#### Qualité

- [ ] **Déterminisme** : Même seed + mêmes params = même résultat
- [ ] **Variables** : Toutes les variables utilisées dans les templates sont présentes
- [ ] **Templates** : `ENONCE_TEMPLATE` et `SOLUTION_TEMPLATE` définis comme constantes
- [ ] **JSON-safe** : Toutes les données sont JSON-serializables
- [ ] **Documentation** : Docstrings complètes sur toutes les méthodes

### Tests à effectuer

- [ ] **Fichier de test créé** : `backend/tests/test_votre_generateur.py`
- [ ] **Test meta** : `test_meta_data()` vérifie les métadonnées
- [ ] **Test schema** : `test_schema_definition()` vérifie le schéma
- [ ] **Test validation** : `test_validate_params()` vérifie la validation
- [ ] **Test déterminisme** : `test_determinism()` vérifie la reproductibilité
- [ ] **Test factory** : `test_factory_registration()` vérifie l'enregistrement
- [ ] **Test placeholders** : `test_all_placeholders_resolved()` ⚠️ CRITIQUE
- [ ] **Test cas limites** : Tests pour `max_denominator` petit, `force_reducible=False`, etc.
- [ ] **Génération avec différents seeds** → résultats différents mais cohérents
- [ ] **Génération avec même seed** → résultats identiques
- [ ] **Validation des paramètres** → erreurs claires si invalides
- [ ] **Presets** → tous valides et testables
- [ ] **Templates** → tous les placeholders résolus
- [ ] **SVG** → affichage correct (si applicable)
- [ ] **API endpoint** → `/api/v1/generators/preview-dynamic` fonctionne

### Déploiement

- [ ] **Compilation** : `python3 -m py_compile backend/generators/votre_generateur.py` → OK
- [ ] **Tests** : `pytest backend/tests/test_votre_generateur.py` → tous passent
- [ ] **Rebuild Docker** : `docker compose build backend` → OK
- [ ] **Restart backend** : `docker compose restart backend` → OK
- [ ] **Logs backend** : Aucune erreur au démarrage
- [ ] **API liste** : `/api/v1/exercises/generators` → générateur présent
- [ ] **API schéma** : `/api/v1/exercises/generators/VOTRE_KEY/full-schema` → OK

### Intégration dans l'admin

- [ ] Le générateur apparaît dans la liste des générateurs disponibles
- [ ] Les presets sont sélectionnables lors de la création d'exercice
- [ ] Les paramètres peuvent être modifiés manuellement
- [ ] La prévisualisation fonctionne
- [ ] L'exercice peut être sauvegardé et généré côté élève
- [ ] **Templates** : Utilisation des templates de référence du générateur (voir `PROCEDURE_AJOUT_TEMPLATE_DYNAMIQUE.md`)

---

## 🐛 Pièges courants et solutions

**📚 PROCÉDURE COMPLÈTE** : Voir `docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md` section "Pièges courants et solutions" pour une liste exhaustive.

### Pièges les plus fréquents

1. **Import manquant dans factory.py** → Générateur non visible dans l'API
2. **Imports manquants** (`time`, `safe_random_choice`, `safe_randrange`) → `NameError`
3. **Crash randrange** → Filtrage préventif des pools obligatoire
4. **Placeholders non résolus** → Tous les placeholders DOIVENT être dans `variables`
5. **Docker non rebuild** → Code modifié mais non pris en compte
6. **Décorateur manquant** → `@GeneratorFactory.register` obligatoire

---

## 📞 Support

Pour toute question ou problème lors de l'intégration :
1. **Consulter les procédures** :
   - `docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md` (création complète)
   - `docs/PROCEDURE_AJOUT_TEMPLATE_DYNAMIQUE.md` (ajout de template)
2. **Consulter les générateurs existants** : `simplification_fractions_v1.py`, `simplification_fractions_v2.py`, `thales_v2.py`
3. **Vérifier les tests existants** dans `backend/tests/`
4. **Vérifier les incidents** dans `docs/incidents/` pour les problèmes connus

---

**Document créé le :** 2025-01-XX  
**Dernière mise à jour :** 2025-01-XX  
**Version :** 1.1.0

**📚 PROCÉDURES COMPLÉMENTAIRES :**
- **Création d'un générateur** : `docs/PROCEDURE_CREATION_GENERATEUR_DYNAMIQUE.md` (procédure pas-à-pas industrialisée)
- **Ajout d'un template** : `docs/PROCEDURE_AJOUT_TEMPLATE_DYNAMIQUE.md` (une fois le générateur créé)

