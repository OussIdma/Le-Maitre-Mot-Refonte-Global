"""
Générateur SYMETRIE_AXIALE_V2 - Symétrie Axiale (Géométrie 6e)
==============================================================

Version: 2.0.0 (Dynamic Factory v1 - Pilote)

Ce générateur produit des exercices sur la symétrie axiale:
- Identifier le symétrique d'un point
- Tracer le symétrique d'une figure
- Reconnaître des axes de symétrie

Conforme au cahier des charges:
- RNG local ✅
- HTML pur ✅  
- geo_data JSON-safe ✅
- meta.exercise_type = SYMETRIE_AXIALE ✅
- meta.svg_mode = AUTO ✅
- validate_params() ✅
- presets pédagogiques ✅
"""

from typing import Dict, Any, List, Optional
from generators.base_generator import (
    BaseGenerator, 
    GeneratorMeta, 
    ParamSchema, 
    Preset,
    ParamType,
    create_svg_wrapper
)
from generators.factory import GeneratorFactory


@GeneratorFactory.register
class SymetrieAxialeV2Generator(BaseGenerator):
    """Générateur d'exercices sur la symétrie axiale."""
    
    # Constantes de configuration
    GRID_SIZE = 10  # Grille 10x10
    SCALE = 30  # Pixels par unité
    PADDING = 40
    
    FIGURE_TYPES = ["point", "segment", "triangle", "rectangle"]
    AXE_TYPES = ["vertical", "horizontal", "oblique"]
    
    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="SYMETRIE_AXIALE_V2",
            label="Symétrie Axiale",
            description="Exercices sur la symétrie axiale: identification, tracé, axes de symétrie",
            version="2.0.0",
            niveaux=["6e", "5e"],
            exercise_type="SYMETRIE_AXIALE",
            svg_mode="AUTO",
            supports_double_svg=True,
            pedagogical_tips="⚠️ Veiller à ce que l'élève utilise l'équerre pour les perpendiculaires. Erreur fréquente: confusion avec la symétrie centrale."
        )
    
    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        return [
            ParamSchema(
                name="figure_type",
                type=ParamType.ENUM,
                description="Type de figure à symétriser",
                default="point",
                options=cls.FIGURE_TYPES
            ),
            ParamSchema(
                name="axe_type",
                type=ParamType.ENUM,
                description="Orientation de l'axe de symétrie",
                default="vertical",
                options=cls.AXE_TYPES
            ),
            ParamSchema(
                name="show_grid",
                type=ParamType.BOOL,
                description="Afficher la grille de repérage",
                default=True
            ),
            ParamSchema(
                name="difficulty",
                type=ParamType.ENUM,
                description="Niveau de difficulté",
                default="moyen",
                options=["facile", "moyen", "difficile"]
            ),
            ParamSchema(
                name="show_solution_steps",
                type=ParamType.BOOL,
                description="Montrer les étapes de construction dans la solution",
                default=True
            ),
            ParamSchema(
                name="label_points",
                type=ParamType.BOOL,
                description="Afficher les lettres sur les points",
                default=True
            )
        ]
    
    @classmethod
    def get_presets(cls) -> List[Preset]:
        return [
            Preset(
                key="6e_facile",
                label="6e Facile - Point seul",
                description="Symétrique d'un point par rapport à un axe vertical, avec grille",
                niveau="6e",
                params={
                    "figure_type": "point",
                    "axe_type": "vertical",
                    "show_grid": True,
                    "difficulty": "facile",
                    "show_solution_steps": True,
                    "label_points": True
                }
            ),
            Preset(
                key="6e_moyen",
                label="6e Moyen - Segment",
                description="Symétrique d'un segment par rapport à un axe",
                niveau="6e",
                params={
                    "figure_type": "segment",
                    "axe_type": "vertical",
                    "show_grid": True,
                    "difficulty": "moyen",
                    "show_solution_steps": True,
                    "label_points": True
                }
            ),
            Preset(
                key="6e_difficile",
                label="6e Difficile - Triangle",
                description="Symétrique d'un triangle par rapport à un axe oblique",
                niveau="6e",
                params={
                    "figure_type": "triangle",
                    "axe_type": "oblique",
                    "show_grid": True,
                    "difficulty": "difficile",
                    "show_solution_steps": True,
                    "label_points": True
                }
            ),
            Preset(
                key="5e_moyen",
                label="5e Moyen - Rectangle",
                description="Symétrique d'un rectangle avec axe horizontal",
                niveau="5e",
                params={
                    "figure_type": "rectangle",
                    "axe_type": "horizontal",
                    "show_grid": False,
                    "difficulty": "moyen",
                    "show_solution_steps": False,
                    "label_points": True
                }
            )
        ]
    
    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un exercice de symétrie axiale."""
        
        figure_type = params["figure_type"]
        axe_type = params["axe_type"]
        show_grid = params["show_grid"]
        difficulty = params["difficulty"]
        show_steps = params["show_solution_steps"]
        label_points = params["label_points"]
        
        # Générer la figure et son symétrique
        figure_data = self._generate_figure(figure_type, difficulty)
        axe_data = self._generate_axe(axe_type, difficulty)
        symmetric_data = self._calculate_symmetric(figure_data, axe_data)
        
        # Construire geo_data (JSON-safe)
        geo_data = {
            "figure": figure_data,
            "axe": axe_data,
            "symmetric": symmetric_data,
            "grid_size": self.GRID_SIZE,
            "scale": self.SCALE
        }
        
        # Variables pour les templates
        variables = self._build_variables(figure_data, axe_data, symmetric_data, params)
        
        # Générer les SVG
        svg_enonce = self._generate_svg_enonce(geo_data, params)
        svg_solution = self._generate_svg_solution(geo_data, params)
        
        return {
            "variables": variables,
            "geo_data": geo_data,
            "figure_svg_enonce": svg_enonce,
            "figure_svg_solution": svg_solution,
            "meta": {
                "exercise_type": "SYMETRIE_AXIALE",
                "svg_mode": "AUTO",
                "figure_type": figure_type,
                "axe_type": axe_type,
                "difficulty": difficulty
            }
        }
    
    def _generate_figure(self, figure_type: str, difficulty: str) -> Dict[str, Any]:
        """Génère les coordonnées de la figure initiale."""
        
        # Zone de génération (côté gauche de la grille pour axe vertical)
        if difficulty == "facile":
            x_range = range(1, 4)
            y_range = range(3, 8)
        elif difficulty == "moyen":
            x_range = range(1, 5)
            y_range = range(2, 9)
        else:
            x_range = range(1, 5)
            y_range = range(1, 10)
        
        if figure_type == "point":
            x = self._rng.choice(list(x_range))
            y = self._rng.choice(list(y_range))
            return {
                "type": "point",
                "points": [{"x": x, "y": y, "label": "A"}]
            }
        
        elif figure_type == "segment":
            x1 = self._rng.choice(list(x_range))
            y1 = self._rng.choice(list(y_range))
            x2 = self._rng.choice([x for x in x_range if x != x1] or [x1 + 1])
            y2 = self._rng.choice([y for y in y_range if y != y1] or [y1 + 1])
            return {
                "type": "segment",
                "points": [
                    {"x": x1, "y": y1, "label": "A"},
                    {"x": x2, "y": y2, "label": "B"}
                ]
            }
        
        elif figure_type == "triangle":
            x1 = self._rng.choice(list(x_range))
            y1 = self._rng.choice(list(y_range))
            x2 = x1 + self._rng.choice([1, 2])
            y2 = y1 + self._rng.choice([-2, -1, 1, 2])
            x3 = x1 + self._rng.choice([0, 1])
            y3 = y1 + self._rng.choice([1, 2, 3])
            return {
                "type": "triangle",
                "points": [
                    {"x": x1, "y": y1, "label": "A"},
                    {"x": x2, "y": y2, "label": "B"},
                    {"x": x3, "y": y3, "label": "C"}
                ]
            }
        
        else:  # rectangle
            x1 = self._rng.choice(list(x_range))
            y1 = self._rng.choice(list(y_range))
            w = self._rng.choice([2, 3])
            h = self._rng.choice([1, 2])
            return {
                "type": "rectangle",
                "points": [
                    {"x": x1, "y": y1, "label": "A"},
                    {"x": x1 + w, "y": y1, "label": "B"},
                    {"x": x1 + w, "y": y1 + h, "label": "C"},
                    {"x": x1, "y": y1 + h, "label": "D"}
                ]
            }
    
    def _generate_axe(self, axe_type: str, difficulty: str) -> Dict[str, Any]:
        """Génère les paramètres de l'axe de symétrie."""
        
        if axe_type == "vertical":
            x = 5  # Milieu de la grille
            return {
                "type": "vertical",
                "x": x,
                "equation": f"x = {x}",
                "label": "(d)"
            }
        
        elif axe_type == "horizontal":
            y = 5
            return {
                "type": "horizontal", 
                "y": y,
                "equation": f"y = {y}",
                "label": "(d)"
            }
        
        else:  # oblique (y = x pour simplifier)
            return {
                "type": "oblique",
                "slope": 1,
                "intercept": 0,
                "equation": "y = x",
                "label": "(d)"
            }
    
    def _calculate_symmetric(self, figure_data: Dict, axe_data: Dict) -> Dict[str, Any]:
        """Calcule les coordonnées du symétrique."""
        
        symmetric_points = []
        
        for point in figure_data["points"]:
            x, y = point["x"], point["y"]
            label = point["label"] + "'"
            
            if axe_data["type"] == "vertical":
                new_x = 2 * axe_data["x"] - x
                new_y = y
            
            elif axe_data["type"] == "horizontal":
                new_x = x
                new_y = 2 * axe_data["y"] - y
            
            else:  # oblique y = x
                new_x = y
                new_y = x
            
            symmetric_points.append({
                "x": new_x,
                "y": new_y,
                "label": label,
                "original": point["label"]
            })
        
        return {
            "type": figure_data["type"],
            "points": symmetric_points
        }
    
    def _build_variables(
        self, 
        figure_data: Dict, 
        axe_data: Dict, 
        symmetric_data: Dict,
        params: Dict
    ) -> Dict[str, Any]:
        """Construit les variables pour les templates HTML."""
        
        points_str = ", ".join([p["label"] for p in figure_data["points"]])
        points_sym_str = ", ".join([p["label"] for p in symmetric_data["points"]])
        
        # Description de la figure
        figure_desc = {
            "point": "le point",
            "segment": "le segment",
            "triangle": "le triangle",
            "rectangle": "le rectangle"
        }[figure_data["type"]]
        
        # Description de l'axe
        axe_desc = {
            "vertical": "verticale",
            "horizontal": "horizontale",
            "oblique": "oblique (première bissectrice)"
        }[axe_data["type"]]
        
        return {
            "figure_type": figure_data["type"],
            "figure_description": figure_desc,
            "points_labels": points_str,
            "points_symmetric_labels": points_sym_str,
            "axe_type": axe_data["type"],
            "axe_description": axe_desc,
            "axe_equation": axe_data["equation"],
            "axe_label": axe_data["label"],
            "point_count": len(figure_data["points"]),
            "coordinates_original": [(p["x"], p["y"]) for p in figure_data["points"]],
            "coordinates_symmetric": [(p["x"], p["y"]) for p in symmetric_data["points"]]
        }
    
    def _generate_svg_enonce(self, geo_data: Dict, params: Dict) -> str:
        """Génère le SVG de l'énoncé (figure + axe, sans solution)."""
        
        width = self.GRID_SIZE * self.SCALE + 2 * self.PADDING
        height = self.GRID_SIZE * self.SCALE + 2 * self.PADDING
        
        content_parts = []
        
        # Grille
        if params["show_grid"]:
            content_parts.append(self._svg_grid())
        
        # Axe de symétrie
        content_parts.append(self._svg_axe(geo_data["axe"]))
        
        # Figure originale
        content_parts.append(self._svg_figure(geo_data["figure"], "#1976d2", params["label_points"]))
        
        content = "\n".join(content_parts)
        return create_svg_wrapper(content, width, height)
    
    def _generate_svg_solution(self, geo_data: Dict, params: Dict) -> str:
        """Génère le SVG de la solution (figure + axe + symétrique)."""
        
        width = self.GRID_SIZE * self.SCALE + 2 * self.PADDING
        height = self.GRID_SIZE * self.SCALE + 2 * self.PADDING
        
        content_parts = []
        
        # Grille
        if params["show_grid"]:
            content_parts.append(self._svg_grid())
        
        # Axe de symétrie
        content_parts.append(self._svg_axe(geo_data["axe"]))
        
        # Figure originale
        content_parts.append(self._svg_figure(geo_data["figure"], "#1976d2", params["label_points"]))
        
        # Lignes de construction (si activé)
        if params["show_solution_steps"]:
            content_parts.append(self._svg_construction_lines(geo_data))
        
        # Figure symétrique
        content_parts.append(self._svg_figure(geo_data["symmetric"], "#c62828", params["label_points"]))
        
        content = "\n".join(content_parts)
        return create_svg_wrapper(content, width, height)
    
    def _svg_grid(self) -> str:
        """Génère la grille SVG."""
        lines = []
        
        for i in range(self.GRID_SIZE + 1):
            x = self.PADDING + i * self.SCALE
            y = self.PADDING + i * self.SCALE
            
            # Verticales
            lines.append(f'<line x1="{x}" y1="{self.PADDING}" x2="{x}" y2="{self.PADDING + self.GRID_SIZE * self.SCALE}" stroke="#e0e0e0" stroke-width="1"/>')
            # Horizontales
            lines.append(f'<line x1="{self.PADDING}" y1="{y}" x2="{self.PADDING + self.GRID_SIZE * self.SCALE}" y2="{y}" stroke="#e0e0e0" stroke-width="1"/>')
        
        return "\n".join(lines)
    
    def _svg_axe(self, axe_data: Dict) -> str:
        """Génère l'axe de symétrie SVG."""
        
        if axe_data["type"] == "vertical":
            x = self.PADDING + axe_data["x"] * self.SCALE
            return f'''<line x1="{x}" y1="{self.PADDING - 10}" x2="{x}" y2="{self.PADDING + self.GRID_SIZE * self.SCALE + 10}" stroke="#4caf50" stroke-width="3" stroke-dasharray="8,4"/>
<text x="{x + 10}" y="{self.PADDING - 15}" font-size="14" fill="#4caf50" font-weight="bold">{axe_data["label"]}</text>'''
        
        elif axe_data["type"] == "horizontal":
            y = self.PADDING + axe_data["y"] * self.SCALE
            return f'''<line x1="{self.PADDING - 10}" y1="{y}" x2="{self.PADDING + self.GRID_SIZE * self.SCALE + 10}" y2="{y}" stroke="#4caf50" stroke-width="3" stroke-dasharray="8,4"/>
<text x="{self.PADDING + self.GRID_SIZE * self.SCALE + 15}" y="{y - 5}" font-size="14" fill="#4caf50" font-weight="bold">{axe_data["label"]}</text>'''
        
        else:  # oblique y = x
            return f'''<line x1="{self.PADDING}" y1="{self.PADDING + self.GRID_SIZE * self.SCALE}" x2="{self.PADDING + self.GRID_SIZE * self.SCALE}" y2="{self.PADDING}" stroke="#4caf50" stroke-width="3" stroke-dasharray="8,4"/>
<text x="{self.PADDING + self.GRID_SIZE * self.SCALE - 20}" y="{self.PADDING + 20}" font-size="14" fill="#4caf50" font-weight="bold">{axe_data["label"]}</text>'''
    
    def _svg_figure(self, figure_data: Dict, color: str, show_labels: bool) -> str:
        """Génère une figure SVG."""
        
        parts = []
        points = figure_data["points"]
        
        # Convertir les coordonnées
        def to_svg(p):
            return (
                self.PADDING + p["x"] * self.SCALE,
                self.PADDING + (self.GRID_SIZE - p["y"]) * self.SCALE
            )
        
        # Dessiner la forme
        if figure_data["type"] == "point":
            sx, sy = to_svg(points[0])
            parts.append(f'<circle cx="{sx}" cy="{sy}" r="6" fill="{color}"/>')
        
        elif figure_data["type"] == "segment":
            (x1, y1), (x2, y2) = to_svg(points[0]), to_svg(points[1])
            parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="3"/>')
            parts.append(f'<circle cx="{x1}" cy="{y1}" r="5" fill="{color}"/>')
            parts.append(f'<circle cx="{x2}" cy="{y2}" r="5" fill="{color}"/>')
        
        elif figure_data["type"] in ["triangle", "rectangle"]:
            coords = [to_svg(p) for p in points]
            points_str = " ".join([f"{x},{y}" for x, y in coords])
            fill = f"{color}20"  # Transparent
            parts.append(f'<polygon points="{points_str}" fill="{fill}" stroke="{color}" stroke-width="2"/>')
            for x, y in coords:
                parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>')
        
        # Labels
        if show_labels:
            for p in points:
                sx, sy = to_svg(p)
                offset_x = 10
                offset_y = -10
                parts.append(f'<text x="{sx + offset_x}" y="{sy + offset_y}" font-size="14" fill="{color}" font-weight="bold">{p["label"]}</text>')
        
        return "\n".join(parts)
    
    def _svg_construction_lines(self, geo_data: Dict) -> str:
        """Génère les lignes de construction (pointillés entre original et symétrique)."""
        
        parts = []
        
        def to_svg(p):
            return (
                self.PADDING + p["x"] * self.SCALE,
                self.PADDING + (self.GRID_SIZE - p["y"]) * self.SCALE
            )
        
        for orig, sym in zip(geo_data["figure"]["points"], geo_data["symmetric"]["points"]):
            x1, y1 = to_svg(orig)
            x2, y2 = to_svg(sym)
            parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#9e9e9e" stroke-width="1" stroke-dasharray="4,4"/>')
        
        return "\n".join(parts)


# =============================================================================
# TEMPLATES HTML EXEMPLES
# =============================================================================

SYMETRIE_TEMPLATE_ENONCE = """<p><strong>Symétrie axiale</strong></p>
<p>Soit {{figure_description}} <strong>{{points_labels}}</strong> et la droite {{axe_label}} d'équation <strong>{{axe_equation}}</strong>.</p>
<p><em>Construire le symétrique de {{points_labels}} par rapport à {{axe_label}}.</em></p>"""

SYMETRIE_TEMPLATE_SOLUTION = """<h4>Correction</h4>
<ol>
  <li><strong>Méthode :</strong> Pour chaque point, tracer la perpendiculaire à {{axe_label}} passant par ce point.</li>
  <li><strong>Report des distances :</strong> Reporter la même distance de l'autre côté de l'axe.</li>
  <li><strong>Résultat :</strong> Les symétriques sont : <strong>{{points_symmetric_labels}}</strong></li>
</ol>"""
