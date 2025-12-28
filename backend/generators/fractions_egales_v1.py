"""
Generateur FRACTIONS_EGALES_V1 - Fractions egales
==================================================

Version: 1.0.0

Exercices sur les fractions egales:
- Trouver une fraction egale (extension)
- Simplifier une fraction
- Verifier si deux fractions sont egales

Chapitre cible: 6e_N09
"""

from typing import Dict, Any, List
from math import gcd
from backend.generators.base_generator import (
    BaseGenerator,
    GeneratorMeta,
    ParamSchema,
    Preset,
    ParamType,
)
from backend.generators.factory import GeneratorFactory


def simplify_fraction(num: int, den: int) -> tuple:
    """Simplifie une fraction et retourne (num_simplifie, den_simplifie, pgcd)."""
    if den == 0:
        raise ValueError("Le denominateur ne peut pas etre 0")
    d = gcd(abs(num), abs(den))
    return num // d, den // d, d


@GeneratorFactory.register
class FractionsEgalesV1Generator(BaseGenerator):
    """Generateur Gold pour les fractions egales."""

    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="FRACTIONS_EGALES_V1",
            label="Fractions egales",
            description="Exercices sur les fractions equivalentes et la simplification",
            version="1.0.0",
            niveaux=["6e"],
            exercise_type="FRACTIONS_EGALES",
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
                default="extension",
                options=["extension", "simplification", "verifier"]
            ),
            ParamSchema(
                name="max_denominator",
                type=ParamType.INT,
                description="Denominateur maximum",
                default=24,
                min=6,
                max=100
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
                key="6e_extension_facile",
                label="6e Facile - Extension de fraction",
                description="Trouver une fraction egale par multiplication",
                niveau="6e",
                params={"exercise_type": "extension", "max_denominator": 20, "difficulty": "facile", "seed": 42}
            ),
            Preset(
                key="6e_simplification",
                label="6e - Simplifier une fraction",
                description="Simplifier une fraction en divisant par le PGCD",
                niveau="6e",
                params={"exercise_type": "simplification", "max_denominator": 24, "difficulty": "standard", "seed": 42}
            ),
            Preset(
                key="6e_verifier",
                label="6e - Verifier fractions egales",
                description="Verifier si deux fractions sont egales",
                niveau="6e",
                params={"exercise_type": "verifier", "max_denominator": 30, "difficulty": "standard", "seed": 42}
            ),
        ]

    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        exercise_type = params.get("exercise_type", "extension")
        max_denominator = params.get("max_denominator", 24)
        difficulty = params.get("difficulty", "standard")

        if exercise_type == "extension":
            variables = self._generate_extension(max_denominator, difficulty)
        elif exercise_type == "simplification":
            variables = self._generate_simplification(max_denominator, difficulty)
        else:  # verifier
            variables = self._generate_verifier(max_denominator, difficulty)

        variables["exercise_type"] = exercise_type
        variables["difficulty"] = difficulty

        return {
            "variables": variables,
            "geo_data": None,
            "figure_svg_enonce": None,
            "figure_svg_solution": None,
            "meta": {"generator_key": "FRACTIONS_EGALES_V1"},
        }

    def _generate_extension(self, max_denominator: int, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: trouver une fraction egale par extension."""
        if difficulty == "facile":
            denominateur = self.rng_choice([2, 3, 4, 5])
            multiplicateur = self.rng_randint(2, 4)
        else:
            denominateur = self.rng_randint(2, 10)
            multiplicateur = self.rng_randint(2, 6)

        numerateur = self.rng_randint(1, denominateur - 1)

        # Fraction etendue
        num_etendu = numerateur * multiplicateur
        den_etendu = denominateur * multiplicateur

        # Type de question: trouver numerateur ou denominateur
        cherche_num = self._rng.random() < 0.5

        if cherche_num:
            enonce = f"Complete: {numerateur}/{denominateur} = ?/{den_etendu}"
            reponse = num_etendu
        else:
            enonce = f"Complete: {numerateur}/{denominateur} = {num_etendu}/?"
            reponse = den_etendu

        return {
            "enonce": enonce,
            "numerateur": numerateur,
            "denominateur": denominateur,
            "multiplicateur": multiplicateur,
            "num_etendu": num_etendu,
            "den_etendu": den_etendu,
            "cherche_num": cherche_num,
            "reponse": reponse,
            "reponse_finale": str(reponse),
            "explication": f"{numerateur}/{denominateur} = ({numerateur} x {multiplicateur})/({denominateur} x {multiplicateur}) = {num_etendu}/{den_etendu}",
            "consigne": "Trouve le nombre manquant pour obtenir une fraction egale.",
        }

    def _generate_simplification(self, max_denominator: int, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: simplifier une fraction."""
        if difficulty == "facile":
            # Fractions avec PGCD simple (2, 3, 5)
            diviseur = self.rng_choice([2, 2, 3, 3, 5])
            num_simple = self.rng_randint(1, 5)
            den_simple = self.rng_randint(num_simple + 1, 8)
        else:
            diviseur = self.rng_randint(2, 6)
            num_simple = self.rng_randint(1, 8)
            den_simple = self.rng_randint(num_simple + 1, 12)

        # S'assurer que num_simple et den_simple sont premiers entre eux
        d = gcd(num_simple, den_simple)
        num_simple = num_simple // d
        den_simple = den_simple // d

        # Creer la fraction a simplifier
        numerateur = num_simple * diviseur
        denominateur = den_simple * diviseur

        # Verifier les limites
        if denominateur > max_denominator:
            denominateur = den_simple * 2
            numerateur = num_simple * 2
            diviseur = 2

        return {
            "enonce": f"Simplifie la fraction {numerateur}/{denominateur}.",
            "numerateur": numerateur,
            "denominateur": denominateur,
            "pgcd": diviseur,
            "num_simplifie": num_simple,
            "den_simplifie": den_simple,
            "reponse_finale": f"{num_simple}/{den_simple}",
            "explication": f"{numerateur}/{denominateur} = ({numerateur} / {diviseur})/({denominateur} / {diviseur}) = {num_simple}/{den_simple}",
            "consigne": "Divise le numerateur et le denominateur par leur PGCD.",
        }

    def _generate_verifier(self, max_denominator: int, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: verifier si deux fractions sont egales."""
        # Generer une premiere fraction
        den1 = self.rng_randint(2, 10)
        num1 = self.rng_randint(1, den1 - 1)

        # 60% de chances que les fractions soient egales
        sont_egales = self._rng.random() < 0.6

        if sont_egales:
            # Creer une fraction egale
            multiplicateur = self.rng_randint(2, 4)
            num2 = num1 * multiplicateur
            den2 = den1 * multiplicateur
        else:
            # Creer une fraction differente
            den2 = self.rng_randint(2, max_denominator // 2)
            num2 = self.rng_randint(1, den2 - 1)
            # Verifier qu'elles ne sont pas egales par hasard
            if num1 * den2 == num2 * den1:
                num2 = num2 + 1 if num2 < den2 - 1 else num2 - 1

        # Verifier l'egalite (produit en croix)
        produit1 = num1 * den2
        produit2 = num2 * den1
        sont_egales_verif = produit1 == produit2

        return {
            "enonce": f"Les fractions {num1}/{den1} et {num2}/{den2} sont-elles egales ?",
            "num1": num1,
            "den1": den1,
            "num2": num2,
            "den2": den2,
            "produit_croix_1": produit1,
            "produit_croix_2": produit2,
            "sont_egales": sont_egales_verif,
            "reponse_finale": "Oui" if sont_egales_verif else "Non",
            "explication": f"{num1} x {den2} = {produit1} et {num2} x {den1} = {produit2}. "
                          + (f"Les produits en croix sont egaux." if sont_egales_verif else f"Les produits en croix sont differents."),
            "consigne": "Utilise le produit en croix pour verifier.",
        }
