"""
Generateur DROITE_GRADUEE_V1 - Reperage sur droite graduee
==========================================================

Version: 1.0.0

Exercices sur le reperage:
- Placer un nombre sur une droite graduee
- Lire un nombre sur une droite graduee
- Encadrer un nombre

Chapitre cible: 6e_N03
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
class DroiteGradueeV1Generator(BaseGenerator):
    """Generateur Gold pour le reperage sur droite graduee."""

    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="DROITE_GRADUEE_V1",
            label="Droite graduee (reperage)",
            description="Exercices de reperage sur une droite graduee",
            version="1.0.0",
            niveaux=["6e"],
            exercise_type="DROITE_GRADUEE",
            svg_mode="AUTO",
            supports_double_svg=False,
            is_dynamic=True,
            supported_grades=["6e"],
            supported_chapters=["6e_N03"],
        )

    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        return [
            ParamSchema(
                name="exercise_type",
                type=ParamType.ENUM,
                description="Type d'exercice",
                default="lire",
                options=["lire", "placer", "encadrer"]
            ),
            ParamSchema(
                name="number_type",
                type=ParamType.ENUM,
                description="Type de nombres",
                default="entiers",
                options=["entiers", "decimaux"]
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
                key="6e_lire_entiers",
                label="6e - Lire sur droite (entiers)",
                description="Lire un nombre entier sur une droite graduee",
                niveau="6e",
                params={"exercise_type": "lire", "number_type": "entiers", "difficulty": "standard", "seed": 42}
            ),
            Preset(
                key="6e_placer_entiers",
                label="6e - Placer sur droite (entiers)",
                description="Placer un nombre entier sur une droite graduee",
                niveau="6e",
                params={"exercise_type": "placer", "number_type": "entiers", "difficulty": "standard", "seed": 42}
            ),
            Preset(
                key="6e_encadrer",
                label="6e - Encadrer un nombre",
                description="Encadrer un nombre entre deux entiers consecutifs",
                niveau="6e",
                params={"exercise_type": "encadrer", "number_type": "decimaux", "difficulty": "standard", "seed": 42}
            ),
        ]

    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        exercise_type = params.get("exercise_type", "lire")
        number_type = params.get("number_type", "entiers")
        difficulty = params.get("difficulty", "standard")

        if exercise_type == "lire":
            variables = self._generate_lire(number_type, difficulty)
        elif exercise_type == "placer":
            variables = self._generate_placer(number_type, difficulty)
        else:  # encadrer
            variables = self._generate_encadrer(difficulty)

        variables["exercise_type"] = exercise_type
        variables["number_type"] = number_type
        variables["difficulty"] = difficulty

        # Générer les SVG pour la droite graduée
        figure_svg_enonce = self._generate_svg_enonce(exercise_type, variables)
        figure_svg_solution = self._generate_svg_solution(exercise_type, variables)

        return {
            "variables": variables,
            "geo_data": None,
            "figure_svg_enonce": figure_svg_enonce,
            "figure_svg_solution": figure_svg_solution,
            "meta": {"generator_key": "DROITE_GRADUEE_V1"},
        }

    def _generate_lire(self, number_type: str, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: lire un nombre sur une droite graduee."""
        if difficulty == "facile":
            origin = 0
            step = 1
            max_grad = 10
        else:
            origin = self.rng_randint(0, 5) * 10
            step = self.rng_choice([1, 2, 5, 10])
            max_grad = 10

        # Position a lire (en nombre de graduations depuis l'origine)
        position = self.rng_randint(1, max_grad - 1)
        nombre = origin + position * step

        if number_type == "decimaux" and difficulty == "standard":
            # Ajouter une partie decimale
            decimal_part = self.rng_choice([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
            nombre = origin + position * step + decimal_part * step

        # Creer la description de la droite
        graduations = [origin + i * step for i in range(max_grad + 1)]

        return {
            "enonce": f"Sur la droite graduee ci-dessous, quel nombre est represente par le point A ?",
            "origin": origin,
            "step": step,
            "graduations": graduations,
            "position": position,
            "reponse_finale": str(nombre),
            "nombre": nombre,
            "consigne": "Lis l'abscisse du point A.",
        }

    def _generate_placer(self, number_type: str, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: placer un nombre sur une droite graduee."""
        if difficulty == "facile":
            origin = 0
            step = 1
            max_grad = 10
        else:
            origin = self.rng_randint(0, 5) * 10
            step = self.rng_choice([1, 2, 5, 10])
            max_grad = 10

        # Nombre a placer
        position = self.rng_randint(1, max_grad - 1)
        nombre = origin + position * step

        graduations = [origin + i * step for i in range(max_grad + 1)]

        return {
            "enonce": f"Place le nombre {nombre} sur la droite graduee.",
            "origin": origin,
            "step": step,
            "graduations": graduations,
            "nombre": nombre,
            "reponse_finale": f"Position {position} (entre {graduations[position-1]} et {graduations[position+1] if position+1 < len(graduations) else graduations[position]})",
            "position": position,
            "consigne": "Place ce nombre sur la droite graduee.",
        }

    def _generate_encadrer(self, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: encadrer un nombre."""
        if difficulty == "facile":
            partie_entiere = self.rng_randint(1, 20)
        else:
            partie_entiere = self.rng_randint(10, 100)

        # Partie decimale
        decimal = self.rng_choice([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
        nombre = partie_entiere + decimal

        borne_inf = partie_entiere
        borne_sup = partie_entiere + 1

        return {
            "enonce": f"Encadre le nombre {nombre} par deux entiers consecutifs.",
            "nombre": nombre,
            "borne_inf": borne_inf,
            "borne_sup": borne_sup,
            "reponse_finale": f"{borne_inf} < {nombre} < {borne_sup}",
            "consigne": "Trouve les deux entiers consecutifs qui encadrent ce nombre.",
        }

    def _generate_svg_enonce(self, exercise_type: str, variables: Dict[str, Any]) -> str:
        """Genere le SVG de la droite graduee pour l'enonce."""
        if exercise_type == "encadrer":
            # Pour encadrer, on affiche une droite simple avec les bornes
            nombre = variables.get("nombre", 0)
            borne_inf = variables.get("borne_inf", 0)
            borne_sup = variables.get("borne_sup", 1)
            
            width = 600
            height = 150
            padding = 50
            scale = (width - 2 * padding) / (borne_sup - borne_inf + 1)
            
            # Position du nombre
            x_nombre = padding + (nombre - borne_inf) * scale
            
            svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <!-- Droite -->
  <line x1="{padding}" y1="{height // 2}" x2="{width - padding}" y2="{height // 2}" 
        stroke="#333" stroke-width="3"/>
  
  <!-- Graduations et labels -->
  <line x1="{padding}" y1="{height // 2 - 10}" x2="{padding}" y2="{height // 2 + 10}" 
        stroke="#333" stroke-width="2"/>
  <text x="{padding}" y="{height // 2 + 35}" text-anchor="middle" font-size="14" fill="#333">{borne_inf}</text>
  
  <line x1="{width - padding}" y1="{height // 2 - 10}" x2="{width - padding}" y2="{height // 2 + 10}" 
        stroke="#333" stroke-width="2"/>
  <text x="{width - padding}" y="{height // 2 + 35}" text-anchor="middle" font-size="14" fill="#333">{borne_sup}</text>
  
  <!-- Point pour le nombre -->
  <circle cx="{x_nombre}" cy="{height // 2}" r="6" fill="#f57c00"/>
  <text x="{x_nombre}" y="{height // 2 - 20}" text-anchor="middle" font-size="12" fill="#f57c00" font-weight="bold">{nombre}</text>
</svg>'''
            return svg
        
        # Pour lire et placer
        graduations = variables.get("graduations", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        origin = variables.get("origin", 0)
        step = variables.get("step", 1)
        position = variables.get("position", 0)
        nombre = variables.get("nombre", 0)
        
        if not graduations:
            return ""
        
        width = 600
        height = 150
        padding = 50
        min_val = min(graduations)
        max_val = max(graduations)
        scale = (width - 2 * padding) / (max_val - min_val) if max_val > min_val else 1
        
        svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">']
        svg_parts.append(f'  <!-- Droite -->')
        svg_parts.append(f'  <line x1="{padding}" y1="{height // 2}" x2="{width - padding}" y2="{height // 2}" stroke="#333" stroke-width="3"/>')
        
        # Graduations
        for grad in graduations:
            x = padding + (grad - min_val) * scale
            svg_parts.append(f'  <line x1="{x}" y1="{height // 2 - 10}" x2="{x}" y2="{height // 2 + 10}" stroke="#333" stroke-width="2"/>')
            svg_parts.append(f'  <text x="{x}" y="{height // 2 + 35}" text-anchor="middle" font-size="14" fill="#333">{grad}</text>')
        
        # Point A pour lire ou position pour placer
        if exercise_type == "lire":
            x_point = padding + (nombre - min_val) * scale
            svg_parts.append(f'  <circle cx="{x_point}" cy="{height // 2}" r="6" fill="#f57c00"/>')
            svg_parts.append(f'  <text x="{x_point}" y="{height // 2 - 20}" text-anchor="middle" font-size="12" fill="#f57c00" font-weight="bold">A</text>')
        elif exercise_type == "placer":
            x_point = padding + (nombre - min_val) * scale
            svg_parts.append(f'  <circle cx="{x_point}" cy="{height // 2}" r="6" fill="#4caf50"/>')
            svg_parts.append(f'  <text x="{x_point}" y="{height // 2 - 20}" text-anchor="middle" font-size="12" fill="#4caf50" font-weight="bold">{nombre}</text>')
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def _generate_svg_solution(self, exercise_type: str, variables: Dict[str, Any]) -> str:
        """Genere le SVG de la droite graduee pour la solution."""
        # Pour la solution, on affiche la même chose mais avec la réponse visible
        return self._generate_svg_enonce(exercise_type, variables)
