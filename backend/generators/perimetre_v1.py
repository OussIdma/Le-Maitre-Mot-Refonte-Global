"""
Generateur PERIMETRE_V1 - Calcul de perimetres
===============================================

Version: 1.0.0

Exercices sur le calcul de perimetres:
- Perimetre du carre
- Perimetre du rectangle
- Perimetre du triangle
- Perimetre de figures composees simples

Chapitres cibles: 6e_GM02, 6e_GM08
"""

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
class PerimetreV1Generator(BaseGenerator):
    """Generateur Gold pour le calcul de perimetres."""

    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="PERIMETRE_V1",
            label="Calcul de perimetres",
            description="Exercices sur le calcul de perimetres de figures usuelles",
            version="1.0.0",
            niveaux=["6e"],
            exercise_type="PERIMETRE",
            svg_mode="AUTO",
            supports_double_svg=False,
            is_dynamic=True,
            supported_grades=["6e"],
            supported_chapters=["6e_GM02", "6e_GM08"],
        )

    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        return [
            ParamSchema(
                name="figure",
                type=ParamType.ENUM,
                description="Type de figure",
                default="rectangle",
                options=["carre", "rectangle", "triangle", "aleatoire"]
            ),
            ParamSchema(
                name="difficulty",
                type=ParamType.ENUM,
                description="Difficulte",
                default="standard",
                options=["facile", "standard"]
            ),
            ParamSchema(
                name="max_side",
                type=ParamType.INT,
                description="Cote maximum",
                default=20,
                min=5,
                max=100
            ),
            ParamSchema(
                name="with_decimals",
                type=ParamType.BOOL,
                description="Utiliser des decimaux",
                default=False
            ),
        ]

    @classmethod
    def get_presets(cls) -> List[Preset]:
        return [
            Preset(
                key="6e_carre_facile",
                label="6e Facile - Perimetre du carre",
                description="Calculer le perimetre d'un carre",
                niveau="6e",
                params={"figure": "carre", "difficulty": "facile", "max_side": 15, "with_decimals": False, "seed": 42}
            ),
            Preset(
                key="6e_rectangle",
                label="6e - Perimetre du rectangle",
                description="Calculer le perimetre d'un rectangle",
                niveau="6e",
                params={"figure": "rectangle", "difficulty": "standard", "max_side": 20, "with_decimals": False, "seed": 42}
            ),
            Preset(
                key="6e_triangle",
                label="6e - Perimetre du triangle",
                description="Calculer le perimetre d'un triangle",
                niveau="6e",
                params={"figure": "triangle", "difficulty": "standard", "max_side": 15, "with_decimals": False, "seed": 42}
            ),
            Preset(
                key="6e_aleatoire",
                label="6e - Perimetre (aleatoire)",
                description="Calculer le perimetre d'une figure aleatoire",
                niveau="6e",
                params={"figure": "aleatoire", "difficulty": "standard", "max_side": 20, "with_decimals": False, "seed": 42}
            ),
        ]

    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        figure = params.get("figure", "rectangle")
        difficulty = params.get("difficulty", "standard")
        max_side = params.get("max_side", 20)
        with_decimals = params.get("with_decimals", False)

        if figure == "aleatoire":
            figure = self.rng_choice(["carre", "rectangle", "triangle"])

        if figure == "carre":
            variables = self._generate_carre(max_side, with_decimals)
        elif figure == "rectangle":
            variables = self._generate_rectangle(max_side, with_decimals)
        else:  # triangle
            variables = self._generate_triangle(max_side, with_decimals)

        variables["figure"] = figure
        variables["difficulty"] = difficulty

        # Générer les SVG pour la figure
        figure_svg_enonce = self._generate_svg_enonce(figure, variables)
        figure_svg_solution = self._generate_svg_solution(figure, variables)

        return {
            "variables": variables,
            "geo_data": None,
            "figure_svg_enonce": figure_svg_enonce,
            "figure_svg_solution": figure_svg_solution,
            "meta": {"generator_key": "PERIMETRE_V1"},
        }

    def _generate_value(self, max_val: int, with_decimals: bool) -> float:
        """Genere une valeur entiere ou decimale."""
        max_val = max(1, int(max_val))  # Clamp anti 0
        if with_decimals:
            val = self.rng_randint(1, max_val * 10) / 10
            return round(val, 1)
        return self.rng_randint(1, max_val)

    def _generate_carre(self, max_side: int, with_decimals: bool) -> Dict[str, Any]:
        """Genere un exercice: perimetre du carre."""
        cote = self._generate_value(max_side, with_decimals)
        perimetre = 4 * cote
        if isinstance(perimetre, float):
            perimetre = round(perimetre, 1)

        unite = self.rng_choice(["cm", "m", "mm"])

        return {
            "enonce": f"Calcule le perimetre d'un carre de cote {cote} {unite}.",
            "cote": cote,
            "unite": unite,
            "formule": "P = 4 x cote",
            "calcul": f"P = 4 x {cote} = {perimetre}",
            "perimetre": perimetre,
            "reponse_finale": f"{perimetre} {unite}",
            "consigne": "Applique la formule du perimetre du carre.",
        }

    def _generate_rectangle(self, max_side: int, with_decimals: bool) -> Dict[str, Any]:
        """Genere un exercice: perimetre du rectangle."""
        longueur = max(2, self._generate_value(max_side, with_decimals))
        max_largeur = max(1, int(longueur * 0.8))
        largeur = self._generate_value(max_largeur, with_decimals)

        # S'assurer que longueur > largeur
        if largeur >= longueur:
            longueur, largeur = largeur + 1, longueur

        perimetre = 2 * (longueur + largeur)
        if isinstance(perimetre, float):
            perimetre = round(perimetre, 1)

        unite = self.rng_choice(["cm", "m", "mm"])

        return {
            "enonce": f"Calcule le perimetre d'un rectangle de longueur {longueur} {unite} et de largeur {largeur} {unite}.",
            "longueur": longueur,
            "largeur": largeur,
            "unite": unite,
            "formule": "P = 2 x (L + l)",
            "calcul": f"P = 2 x ({longueur} + {largeur}) = 2 x {longueur + largeur} = {perimetre}",
            "perimetre": perimetre,
            "reponse_finale": f"{perimetre} {unite}",
            "consigne": "Applique la formule du perimetre du rectangle.",
        }

    def _generate_triangle(self, max_side: int, with_decimals: bool) -> Dict[str, Any]:
        """Genere un exercice: perimetre du triangle."""
        # Generer trois cotes valides pour un triangle (inegalite triangulaire)
        a = self._generate_value(max_side, with_decimals)
        b = self._generate_value(max_side, with_decimals)

        # c doit verifier |a-b| < c < a+b
        min_c = abs(a - b) + 1
        max_c = a + b - 1
        if min_c > max_c:
            min_c, max_c = 1, max_side

        if with_decimals:
            c = round(self.rng_randint(int(min_c * 10), int(max_c * 10)) / 10, 1)
        else:
            c = self.rng_randint(int(min_c), int(max_c))

        perimetre = a + b + c
        if isinstance(perimetre, float):
            perimetre = round(perimetre, 1)

        unite = self.rng_choice(["cm", "m", "mm"])

        return {
            "enonce": f"Calcule le perimetre d'un triangle dont les cotes mesurent {a} {unite}, {b} {unite} et {c} {unite}.",
            "cote_a": a,
            "cote_b": b,
            "cote_c": c,
            "unite": unite,
            "formule": "P = a + b + c",
            "calcul": f"P = {a} + {b} + {c} = {perimetre}",
            "perimetre": perimetre,
            "reponse_finale": f"{perimetre} {unite}",
            "consigne": "Additionne les trois cotes du triangle.",
        }

    def _generate_svg_enonce(self, figure: str, variables: Dict[str, Any]) -> str:
        """Genere le SVG de la figure pour l'enonce."""
        scale = 30  # Pixels par unite
        padding = 20
        unite = variables.get("unite", "cm")

        if figure == "carre":
            cote = variables.get("cote", 5)
            width = cote * scale + 2 * padding
            height = cote * scale + 2 * padding + 30

            return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <rect x="{padding}" y="{padding}" width="{cote * scale}" height="{cote * scale}" 
        fill="#e3f2fd" stroke="#1976d2" stroke-width="2"/>
  <text x="{padding + cote * scale / 2}" y="{padding + cote * scale + 20}" 
        text-anchor="middle" font-size="14" fill="#1976d2">{cote} {unite}</text>
</svg>'''

        elif figure == "rectangle":
            longueur = variables.get("longueur", 10)
            largeur = variables.get("largeur", 5)
            width = longueur * scale + 2 * padding
            height = largeur * scale + 2 * padding + 30

            return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <rect x="{padding}" y="{padding}" width="{longueur * scale}" height="{largeur * scale}" 
        fill="#e8f5e9" stroke="#388e3c" stroke-width="2"/>
  <text x="{padding + longueur * scale / 2}" y="{padding + largeur * scale + 20}" 
        text-anchor="middle" font-size="14" fill="#388e3c">{longueur} {unite}</text>
  <text x="{padding - 5}" y="{padding + largeur * scale / 2}" 
        text-anchor="end" font-size="14" fill="#388e3c">{largeur} {unite}</text>
</svg>'''

        else:  # triangle
            a = variables.get("cote_a", 5)
            b = variables.get("cote_b", 5)
            c = variables.get("cote_c", 5)
            # Utiliser le plus grand côté comme base pour l'affichage
            base = max(a, b, c)
            # Hauteur approximative pour un triangle équilatéral
            hauteur = base * 0.866  # sqrt(3)/2
            width = base * scale + 2 * padding
            height = hauteur * scale + 2 * padding + 50

            # Triangle rectangle pour simplifier l'affichage
            points = f"{padding},{padding + hauteur * scale} {padding + base * scale},{padding + hauteur * scale} {padding},{padding}"

            return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <polygon points="{points}" fill="#fff3e0" stroke="#f57c00" stroke-width="2"/>
  <text x="{padding + base * scale / 2}" y="{padding + hauteur * scale + 20}" 
        text-anchor="middle" font-size="12" fill="#f57c00">{a} {unite}</text>
  <text x="{padding - 5}" y="{padding + hauteur * scale / 2}" 
        text-anchor="end" font-size="12" fill="#f57c00">{b} {unite}</text>
  <text x="{padding + base * scale / 2}" y="{padding - 5}" 
        text-anchor="middle" font-size="12" fill="#f57c00">{c} {unite}</text>
</svg>'''

    def _generate_svg_solution(self, figure: str, variables: Dict[str, Any]) -> str:
        """Genere le SVG de la figure pour la solution (identique a l'enonce pour le perimetre)."""
        # Pour le perimetre, la solution montre la meme figure avec le resultat
        return self._generate_svg_enonce(figure, variables)
