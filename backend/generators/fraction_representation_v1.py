"""
Generateur FRACTION_REPRESENTATION_V1 - Representation de fractions
====================================================================

Version: 1.0.0

Exercices sur la representation des fractions:
- Representer une fraction (ex: colorier 3/4 d'une figure)
- Lire une fraction a partir d'une figure
- Placer une fraction sur une droite graduee

Chapitre cible: 6e_N08
"""

import math
from typing import Dict, Any, List
from backend.generators.base_generator import (
    BaseGenerator,
    GeneratorMeta,
    ParamSchema,
    Preset,
    ParamType,
)
from backend.generators.factory import GeneratorFactory


@GeneratorFactory.register
class FractionRepresentationV1Generator(BaseGenerator):
    """Generateur Gold pour la representation des fractions."""

    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="FRACTION_REPRESENTATION_V1",
            label="Representation de fractions",
            description="Exercices sur la representation graphique des fractions",
            version="1.0.0",
            niveaux=["6e"],
            exercise_type="FRACTION_REPRESENTATION",
            svg_mode="AUTO",
            supports_double_svg=False,
            is_dynamic=True,
            supported_grades=["6e"],
            supported_chapters=["6e_N08"],
        )

    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        return [
            ParamSchema(
                name="exercise_type",
                type=ParamType.ENUM,
                description="Type d'exercice",
                default="lire",
                options=["lire", "representer", "placer"]
            ),
            ParamSchema(
                name="max_denominator",
                type=ParamType.INT,
                description="Denominateur maximum",
                default=10,
                min=2,
                max=20
            ),
            ParamSchema(
                name="difficulty",
                type=ParamType.ENUM,
                description="Difficulte",
                default="standard",
                options=["facile", "standard"]
            ),
        ]

    @classmethod
    def get_presets(cls) -> List[Preset]:
        return [
            Preset(
                key="6e_lire_facile",
                label="6e Facile - Lire une fraction",
                description="Lire une fraction a partir d'une figure",
                niveau="6e",
                params={"exercise_type": "lire", "max_denominator": 6, "difficulty": "facile", "seed": 42}
            ),
            Preset(
                key="6e_representer",
                label="6e - Representer une fraction",
                description="Colorier une partie d'une figure",
                niveau="6e",
                params={"exercise_type": "representer", "max_denominator": 8, "difficulty": "standard", "seed": 42}
            ),
            Preset(
                key="6e_placer",
                label="6e - Placer sur droite graduee",
                description="Placer une fraction sur une droite graduee",
                niveau="6e",
                params={"exercise_type": "placer", "max_denominator": 10, "difficulty": "standard", "seed": 42}
            ),
        ]

    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        exercise_type = params.get("exercise_type", "lire")
        max_denominator = params.get("max_denominator", 10)
        difficulty = params.get("difficulty", "standard")

        if exercise_type == "lire":
            variables = self._generate_lire(max_denominator, difficulty)
        elif exercise_type == "representer":
            variables = self._generate_representer(max_denominator, difficulty)
        else:  # placer
            variables = self._generate_placer(max_denominator, difficulty)

        variables["exercise_type"] = exercise_type
        variables["difficulty"] = difficulty

        # Générer les SVG pour la représentation de fraction
        figure_svg_enonce = self._generate_svg_enonce(exercise_type, variables)
        figure_svg_solution = self._generate_svg_solution(exercise_type, variables)

        return {
            "variables": variables,
            "geo_data": None,
            "figure_svg_enonce": figure_svg_enonce,
            "figure_svg_solution": figure_svg_solution,
            "meta": {"generator_key": "FRACTION_REPRESENTATION_V1"},
        }

    def _generate_lire(self, max_denominator: int, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: lire une fraction a partir d'une figure."""
        if difficulty == "facile":
            denominateur = self.rng_choice([2, 3, 4])
        else:
            denominateur = self.rng_randint(2, max_denominator)

        numerateur = self.rng_randint(1, denominateur - 1)

        figure = self.rng_choice(["rectangle", "cercle", "carre"])
        description = f"Une figure ({figure}) divisee en {denominateur} parties egales, dont {numerateur} sont coloriees."

        return {
            "enonce": f"Observe la figure ci-dessous. {description} Quelle fraction de la figure est coloriee ?",
            "figure": figure,
            "numerateur": numerateur,
            "denominateur": denominateur,
            "parties_coloriees": numerateur,
            "parties_totales": denominateur,
            "reponse_finale": f"{numerateur}/{denominateur}",
            "consigne": "Ecris la fraction correspondant a la partie coloriee.",
        }

    def _generate_representer(self, max_denominator: int, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: representer une fraction."""
        if difficulty == "facile":
            denominateur = self.rng_choice([2, 4, 6])
        else:
            denominateur = self.rng_randint(2, max_denominator)

        numerateur = self.rng_randint(1, denominateur - 1)

        figure = self.rng_choice(["rectangle", "cercle", "carre"])

        return {
            "enonce": f"Represente la fraction {numerateur}/{denominateur} en coloriant la partie correspondante d'un {figure} divise en {denominateur} parties egales.",
            "figure": figure,
            "numerateur": numerateur,
            "denominateur": denominateur,
            "reponse_finale": f"Colorier {numerateur} parties sur {denominateur}",
            "consigne": f"Colorie {numerateur} parties sur les {denominateur} parties du {figure}.",
        }

    def _generate_placer(self, max_denominator: int, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: placer une fraction sur une droite graduee."""
        if difficulty == "facile":
            denominateur = self.rng_choice([2, 3, 4])
        else:
            denominateur = self.rng_randint(2, max_denominator)

        # Generer une fraction entre 0 et 2
        max_num = 2 * denominateur
        numerateur = self.rng_randint(1, max_num - 1)

        # Position sur la droite
        position_decimale = round(numerateur / denominateur, 2)

        return {
            "enonce": f"Place la fraction {numerateur}/{denominateur} sur la droite graduee ci-dessous.",
            "numerateur": numerateur,
            "denominateur": denominateur,
            "position_decimale": position_decimale,
            "droite_min": 0,
            "droite_max": 2,
            "reponse_finale": f"{numerateur}/{denominateur} = {position_decimale}",
            "consigne": f"Place {numerateur}/{denominateur} sur la droite graduee de 0 a 2.",
        }

    def _generate_svg_enonce(self, exercise_type: str, variables: Dict[str, Any]) -> str:
        """Genere le SVG de la representation de fraction pour l'enonce."""
        if exercise_type == "placer":
            # Pour placer, on génère une droite graduée
            numerateur = variables.get("numerateur", 1)
            denominateur = variables.get("denominateur", 2)
            position_decimale = variables.get("position_decimale", 0.5)
            droite_min = variables.get("droite_min", 0)
            droite_max = variables.get("droite_max", 2)
            
            width = 600
            height = 150
            padding = 50
            scale = (width - 2 * padding) / (droite_max - droite_min) if droite_max > droite_min else 1
            
            svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">']
            svg_parts.append(f'  <!-- Droite -->')
            svg_parts.append(f'  <line x1="{padding}" y1="{height // 2}" x2="{width - padding}" y2="{height // 2}" stroke="#333" stroke-width="3"/>')
            
            # Graduations principales (0, 1, 2)
            for i in range(int(droite_min), int(droite_max) + 1):
                x = padding + (i - droite_min) * scale
                svg_parts.append(f'  <line x1="{x}" y1="{height // 2 - 10}" x2="{x}" y2="{height // 2 + 10}" stroke="#333" stroke-width="2"/>')
                svg_parts.append(f'  <text x="{x}" y="{height // 2 + 35}" text-anchor="middle" font-size="14" fill="#333">{i}</text>')
            
            # Point pour la fraction (si pas encore placé dans l'énoncé)
            if exercise_type == "placer":
                x_point = padding + (position_decimale - droite_min) * scale
                svg_parts.append(f'  <circle cx="{x_point}" cy="{height // 2}" r="6" fill="#4caf50" opacity="0.5"/>')
            
            svg_parts.append('</svg>')
            return '\n'.join(svg_parts)
        
        # Pour lire et representer, on génère une figure
        figure = variables.get("figure", "rectangle")
        numerateur = variables.get("numerateur", 1)
        denominateur = variables.get("denominateur", 2)
        parties_coloriees = variables.get("parties_coloriees", numerateur)
        
        width = 300
        height = 300
        padding = 20
        
        if figure == "rectangle":
            return self._svg_rectangle_fraction(width, height, padding, denominateur, parties_coloriees, exercise_type)
        elif figure == "cercle":
            return self._svg_cercle_fraction(width, height, padding, denominateur, parties_coloriees, exercise_type)
        else:  # carre
            return self._svg_carre_fraction(width, height, padding, denominateur, parties_coloriees, exercise_type)

    def _svg_rectangle_fraction(self, width: int, height: int, padding: int, denominateur: int, parties_coloriees: int, exercise_type: str) -> str:
        """Genere un SVG de rectangle divise en parties."""
        rect_width = width - 2 * padding
        rect_height = height - 2 * padding - 30
        part_height = rect_height / denominateur
        
        svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">']
        
        # Rectangle de base
        svg_parts.append(f'  <rect x="{padding}" y="{padding}" width="{rect_width}" height="{rect_height}" fill="#fff" stroke="#333" stroke-width="2"/>')
        
        # Lignes de division
        for i in range(1, denominateur):
            y = padding + i * part_height
            svg_parts.append(f'  <line x1="{padding}" y1="{y}" x2="{padding + rect_width}" y2="{y}" stroke="#333" stroke-width="1"/>')
        
        # Parties coloriées
        for i in range(parties_coloriees):
            y = padding + i * part_height
            color = "#4caf50" if exercise_type == "lire" else "#e0e0e0"
            svg_parts.append(f'  <rect x="{padding}" y="{y}" width="{rect_width}" height="{part_height}" fill="{color}" opacity="0.7"/>')
        
        # Label
        svg_parts.append(f'  <text x="{width // 2}" y="{height - 10}" text-anchor="middle" font-size="14" fill="#333">{parties_coloriees}/{denominateur}</text>')
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def _svg_cercle_fraction(self, width: int, height: int, padding: int, denominateur: int, parties_coloriees: int, exercise_type: str) -> str:
        """Genere un SVG de cercle divise en secteurs."""
        center_x = width // 2
        center_y = height // 2 - 15
        radius = min(width, height) // 2 - padding - 20
        angle_step = 360 / denominateur
        
        svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">']
        
        # Cercle de base
        svg_parts.append(f'  <circle cx="{center_x}" cy="{center_y}" r="{radius}" fill="#fff" stroke="#333" stroke-width="2"/>')
        
        # Secteurs
        for i in range(denominateur):
            angle_start = i * angle_step
            angle_end = (i + 1) * angle_step
            angle_start_rad = math.radians(angle_start - 90)
            angle_end_rad = math.radians(angle_end - 90)
            
            x1 = center_x + radius * math.cos(angle_start_rad)
            y1 = center_y + radius * math.sin(angle_start_rad)
            x2 = center_x + radius * math.cos(angle_end_rad)
            y2 = center_y + radius * math.sin(angle_end_rad)
            
            large_arc = 1 if angle_step > 180 else 0
            
            color = "#4caf50" if i < parties_coloriees and exercise_type == "lire" else "#e0e0e0" if i < parties_coloriees else "none"
            svg_parts.append(f'  <path d="M {center_x} {center_y} L {x1} {y1} A {radius} {radius} 0 {large_arc} 1 {x2} {y2} Z" fill="{color}" stroke="#333" stroke-width="1" opacity="0.7"/>')
        
        # Label
        svg_parts.append(f'  <text x="{width // 2}" y="{height - 10}" text-anchor="middle" font-size="14" fill="#333">{parties_coloriees}/{denominateur}</text>')
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def _svg_carre_fraction(self, width: int, height: int, padding: int, denominateur: int, parties_coloriees: int, exercise_type: str) -> str:
        """Genere un SVG de carre divise en parties."""
        # Pour un carré, on divise en lignes ou colonnes selon le dénominateur
        # Si dénominateur est un carré parfait, on fait une grille, sinon on divise en lignes
        sqrt_denom = int(math.sqrt(denominateur))
        if sqrt_denom * sqrt_denom == denominateur:
            # Grille carrée
            cols = rows = sqrt_denom
        else:
            # Diviser en lignes
            cols = denominateur
            rows = 1
        
        rect_size = min(width, height) - 2 * padding - 30
        part_width = rect_size / cols
        part_height = rect_size / rows
        
        start_x = (width - rect_size) // 2
        start_y = padding
        
        svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">']
        
        # Carré de base
        svg_parts.append(f'  <rect x="{start_x}" y="{start_y}" width="{rect_size}" height="{rect_size}" fill="#fff" stroke="#333" stroke-width="2"/>')
        
        # Lignes de division
        for i in range(1, cols):
            x = start_x + i * part_width
            svg_parts.append(f'  <line x1="{x}" y1="{start_y}" x2="{x}" y2="{start_y + rect_size}" stroke="#333" stroke-width="1"/>')
        for i in range(1, rows):
            y = start_y + i * part_height
            svg_parts.append(f'  <line x1="{start_x}" y1="{y}" x2="{start_x + rect_size}" y2="{y}" stroke="#333" stroke-width="1"/>')
        
        # Parties coloriées
        colored = 0
        for row in range(rows):
            for col in range(cols):
                if colored < parties_coloriees:
                    x = start_x + col * part_width
                    y = start_y + row * part_height
                    color = "#4caf50" if exercise_type == "lire" else "#e0e0e0"
                    svg_parts.append(f'  <rect x="{x}" y="{y}" width="{part_width}" height="{part_height}" fill="{color}" opacity="0.7"/>')
                    colored += 1
        
        # Label
        svg_parts.append(f'  <text x="{width // 2}" y="{height - 10}" text-anchor="middle" font-size="14" fill="#333">{parties_coloriees}/{denominateur}</text>')
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def _generate_svg_solution(self, exercise_type: str, variables: Dict[str, Any]) -> str:
        """Genere le SVG de la representation de fraction pour la solution."""
        # Pour la solution, on affiche la même chose mais avec la réponse visible
        if exercise_type == "representer":
            # Pour representer, la solution montre les parties coloriées
            variables_sol = variables.copy()
            variables_sol["parties_coloriees"] = variables.get("numerateur", 1)
            return self._generate_svg_enonce("lire", variables_sol)
        return self._generate_svg_enonce(exercise_type, variables)
