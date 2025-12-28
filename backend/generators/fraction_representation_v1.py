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
            svg_mode="NONE",
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

        return {
            "variables": variables,
            "geo_data": None,
            "figure_svg_enonce": None,
            "figure_svg_solution": None,
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
