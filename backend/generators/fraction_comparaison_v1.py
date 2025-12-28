"""
Generateur FRACTION_COMPARAISON_V1 - Comparaison de fractions
==============================================================

Version: 1.0.0

Exercices sur la comparaison de fractions:
- Comparer deux fractions (meme denominateur)
- Comparer deux fractions (meme numerateur)
- Comparer deux fractions (produit en croix)
- Ranger des fractions

Chapitre cible: 6e_N09
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
class FractionComparaisonV1Generator(BaseGenerator):
    """Generateur Gold pour la comparaison de fractions."""

    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="FRACTION_COMPARAISON_V1",
            label="Comparaison de fractions",
            description="Exercices sur la comparaison et le rangement de fractions",
            version="1.0.0",
            niveaux=["6e"],
            exercise_type="FRACTION_COMPARAISON",
            svg_mode="NONE",
            supports_double_svg=False,
            is_dynamic=True,
            supported_grades=["6e"],
            supported_chapters=["6e_N09"],
        )

    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        return [
            ParamSchema(
                name="exercise_type",
                type=ParamType.ENUM,
                description="Type d'exercice",
                default="meme_denominateur",
                options=["meme_denominateur", "meme_numerateur", "produit_croix", "ranger"]
            ),
            ParamSchema(
                name="max_denominator",
                type=ParamType.INT,
                description="Denominateur maximum",
                default=12,
                min=3,
                max=30
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
                key="6e_meme_den_facile",
                label="6e Facile - Meme denominateur",
                description="Comparer deux fractions de meme denominateur",
                niveau="6e",
                params={"exercise_type": "meme_denominateur", "max_denominator": 10, "difficulty": "facile", "seed": 42}
            ),
            Preset(
                key="6e_meme_num",
                label="6e - Meme numerateur",
                description="Comparer deux fractions de meme numerateur",
                niveau="6e",
                params={"exercise_type": "meme_numerateur", "max_denominator": 12, "difficulty": "standard", "seed": 42}
            ),
            Preset(
                key="6e_produit_croix",
                label="6e - Produit en croix",
                description="Comparer deux fractions par le produit en croix",
                niveau="6e",
                params={"exercise_type": "produit_croix", "max_denominator": 12, "difficulty": "standard", "seed": 42}
            ),
            Preset(
                key="6e_ranger",
                label="6e - Ranger des fractions",
                description="Ranger des fractions dans l'ordre croissant",
                niveau="6e",
                params={"exercise_type": "ranger", "max_denominator": 10, "difficulty": "standard", "seed": 42}
            ),
        ]

    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        exercise_type = params.get("exercise_type", "meme_denominateur")
        max_denominator = params.get("max_denominator", 12)
        difficulty = params.get("difficulty", "standard")

        if exercise_type == "meme_denominateur":
            variables = self._generate_meme_denominateur(max_denominator, difficulty)
        elif exercise_type == "meme_numerateur":
            variables = self._generate_meme_numerateur(max_denominator, difficulty)
        elif exercise_type == "produit_croix":
            variables = self._generate_produit_croix(max_denominator, difficulty)
        else:  # ranger
            variables = self._generate_ranger(max_denominator, difficulty)

        variables["exercise_type"] = exercise_type
        variables["difficulty"] = difficulty

        return {
            "variables": variables,
            "geo_data": None,
            "figure_svg_enonce": None,
            "figure_svg_solution": None,
            "meta": {"generator_key": "FRACTION_COMPARAISON_V1"},
        }

    def _compare_fractions(self, num1: int, den1: int, num2: int, den2: int) -> str:
        """Compare deux fractions et retourne le signe."""
        val1 = num1 * den2
        val2 = num2 * den1
        if val1 < val2:
            return "<"
        elif val1 > val2:
            return ">"
        else:
            return "="

    def _generate_meme_denominateur(self, max_denominator: int, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: comparer avec meme denominateur."""
        if difficulty == "facile":
            denominateur = self.rng_choice([3, 4, 5, 6])
        else:
            denominateur = self.rng_randint(3, max_denominator)

        num1 = self.rng_randint(1, denominateur - 1)
        num2 = self.rng_randint(1, denominateur - 1)

        # Eviter l'egalite
        while num1 == num2:
            num2 = self.rng_randint(1, denominateur - 1)

        signe = "<" if num1 < num2 else ">"

        return {
            "enonce": f"Compare les fractions {num1}/{denominateur} et {num2}/{denominateur}.",
            "num1": num1,
            "den1": denominateur,
            "num2": num2,
            "den2": denominateur,
            "signe": signe,
            "reponse_finale": f"{num1}/{denominateur} {signe} {num2}/{denominateur}",
            "explication": f"Meme denominateur: on compare les numerateurs. {num1} {signe} {num2}.",
            "consigne": "Quand le denominateur est le meme, compare les numerateurs.",
        }

    def _generate_meme_numerateur(self, max_denominator: int, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: comparer avec meme numerateur."""
        if difficulty == "facile":
            numerateur = self.rng_choice([1, 2, 3])
            denominateurs = [self.rng_randint(numerateur + 1, 8) for _ in range(2)]
        else:
            numerateur = self.rng_randint(1, 5)
            denominateurs = [self.rng_randint(numerateur + 1, max_denominator) for _ in range(2)]

        den1, den2 = denominateurs

        # Eviter l'egalite
        while den1 == den2:
            den2 = self.rng_randint(numerateur + 1, max_denominator)

        # Avec meme numerateur: plus le denominateur est grand, plus la fraction est petite
        signe = ">" if den1 < den2 else "<"

        return {
            "enonce": f"Compare les fractions {numerateur}/{den1} et {numerateur}/{den2}.",
            "num1": numerateur,
            "den1": den1,
            "num2": numerateur,
            "den2": den2,
            "signe": signe,
            "reponse_finale": f"{numerateur}/{den1} {signe} {numerateur}/{den2}",
            "explication": f"Meme numerateur: plus le denominateur est grand, plus la fraction est petite.",
            "consigne": "Quand le numerateur est le meme, la plus grande fraction a le plus petit denominateur.",
        }

    def _generate_produit_croix(self, max_denominator: int, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: comparer avec produit en croix."""
        if difficulty == "facile":
            den1 = self.rng_randint(3, 8)
            den2 = self.rng_randint(3, 8)
        else:
            den1 = self.rng_randint(3, max_denominator)
            den2 = self.rng_randint(3, max_denominator)

        # Eviter les memes denominateurs
        while den1 == den2:
            den2 = self.rng_randint(3, max_denominator)

        num1 = self.rng_randint(1, den1 - 1)
        num2 = self.rng_randint(1, den2 - 1)

        # Eviter l'egalite
        while num1 * den2 == num2 * den1:
            num2 = self.rng_randint(1, den2 - 1)

        produit1 = num1 * den2
        produit2 = num2 * den1
        signe = "<" if produit1 < produit2 else ">"

        return {
            "enonce": f"Compare les fractions {num1}/{den1} et {num2}/{den2}.",
            "num1": num1,
            "den1": den1,
            "num2": num2,
            "den2": den2,
            "produit_croix_1": produit1,
            "produit_croix_2": produit2,
            "signe": signe,
            "reponse_finale": f"{num1}/{den1} {signe} {num2}/{den2}",
            "explication": f"Produits en croix: {num1} x {den2} = {produit1} et {num2} x {den1} = {produit2}. Donc {produit1} {signe} {produit2}.",
            "consigne": "Utilise le produit en croix pour comparer.",
        }

    def _generate_ranger(self, max_denominator: int, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: ranger des fractions."""
        if difficulty == "facile":
            # Meme denominateur pour faciliter
            denominateur = self.rng_choice([4, 5, 6, 8])
            nb_fractions = 3
            numerateurs = []
            while len(numerateurs) < nb_fractions:
                n = self.rng_randint(1, denominateur - 1)
                if n not in numerateurs:
                    numerateurs.append(n)
            fractions = [(n, denominateur) for n in numerateurs]
        else:
            nb_fractions = 4
            fractions = []
            while len(fractions) < nb_fractions:
                den = self.rng_randint(3, max_denominator)
                num = self.rng_randint(1, den - 1)
                if (num, den) not in fractions:
                    fractions.append((num, den))

        # Trier les fractions
        def fraction_value(f):
            return f[0] / f[1]

        fractions_triees = sorted(fractions, key=fraction_value)

        fractions_str = ", ".join([f"{f[0]}/{f[1]}" for f in fractions])
        fractions_triees_str = " < ".join([f"{f[0]}/{f[1]}" for f in fractions_triees])

        return {
            "enonce": f"Range les fractions suivantes dans l'ordre croissant: {fractions_str}",
            "fractions": fractions,
            "fractions_triees": fractions_triees,
            "nb_fractions": nb_fractions,
            "reponse_finale": fractions_triees_str,
            "consigne": "Range de la plus petite a la plus grande.",
        }
