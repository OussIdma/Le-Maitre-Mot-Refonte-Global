"""
Generateur NOMBRES_ENTIERS_V1 - Lecture et ecriture des nombres entiers
========================================================================

Version: 1.0.0

Exercices sur les nombres entiers:
- Ecrire un nombre en lettres
- Ecrire un nombre en chiffres
- Comparer deux nombres
- Ranger des nombres dans l'ordre

Chapitres cibles: 6e_N01, 6e_N02
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


# Dictionnaire pour convertir les nombres en lettres
UNITS = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
TEENS = ["dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
TENS = ["", "dix", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante", "quatre-vingt", "quatre-vingt"]


def number_to_words(n: int) -> str:
    """Convertit un nombre entier en lettres (francais)."""
    if n == 0:
        return "zero"
    if n < 0:
        return "moins " + number_to_words(-n)

    if n < 10:
        return UNITS[n]

    if n < 20:
        return TEENS[n - 10]

    if n < 100:
        tens_digit = n // 10
        unit_digit = n % 10

        if tens_digit == 7:
            if unit_digit == 1:
                return "soixante-et-onze"
            elif unit_digit < 10:
                return "soixante-" + TEENS[unit_digit]
        elif tens_digit == 8:
            if unit_digit == 0:
                return "quatre-vingts"
            else:
                return "quatre-vingt-" + UNITS[unit_digit]
        elif tens_digit == 9:
            return "quatre-vingt-" + TEENS[unit_digit]
        else:
            if unit_digit == 0:
                return TENS[tens_digit]
            elif unit_digit == 1 and tens_digit in [2, 3, 4, 5, 6]:
                return TENS[tens_digit] + "-et-un"
            else:
                return TENS[tens_digit] + "-" + UNITS[unit_digit]

    if n < 1000:
        hundreds = n // 100
        remainder = n % 100
        if hundreds == 1:
            prefix = "cent"
        else:
            prefix = UNITS[hundreds] + "-cents" if remainder == 0 else UNITS[hundreds] + "-cent"
        if remainder == 0:
            return prefix
        return prefix + "-" + number_to_words(remainder)

    if n < 10000:
        thousands = n // 1000
        remainder = n % 1000
        if thousands == 1:
            prefix = "mille"
        else:
            prefix = number_to_words(thousands) + "-mille"
        if remainder == 0:
            return prefix
        return prefix + "-" + number_to_words(remainder)

    if n < 1000000:
        thousands = n // 1000
        remainder = n % 1000
        prefix = number_to_words(thousands) + "-mille"
        if remainder == 0:
            return prefix
        return prefix + "-" + number_to_words(remainder)

    return str(n)


@GeneratorFactory.register
class NombresEntiersV1Generator(BaseGenerator):
    """Generateur Gold pour la lecture et l'ecriture des nombres entiers."""

    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="NOMBRES_ENTIERS_V1",
            label="Nombres entiers (lecture/ecriture)",
            description="Exercices sur la lecture et l'ecriture des nombres entiers",
            version="1.0.0",
            niveaux=["6e"],
            exercise_type="NOMBRES_ENTIERS",
            svg_mode="NONE",
            supports_double_svg=False,
            is_dynamic=True,
            supported_grades=["6e"],
            supported_chapters=["6e_N01", "6e_N02"],
        )

    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        return [
            ParamSchema(
                name="exercise_type",
                type=ParamType.ENUM,
                description="Type d'exercice",
                default="ecrire_lettres",
                options=["ecrire_lettres", "ecrire_chiffres", "comparer", "ranger"]
            ),
            ParamSchema(
                name="difficulty",
                type=ParamType.ENUM,
                description="Difficulte",
                default="standard",
                options=["facile", "standard", "difficile"]
            ),
            ParamSchema(
                name="max_value",
                type=ParamType.INT,
                description="Valeur maximale",
                default=1000,
                min=10,
                max=1000000
            ),
        ]

    @classmethod
    def get_presets(cls) -> List[Preset]:
        return [
            Preset(
                key="6e_facile_lettres",
                label="6e Facile - Ecrire en lettres",
                description="Nombres < 100 a ecrire en lettres",
                niveau="6e",
                params={"exercise_type": "ecrire_lettres", "difficulty": "facile", "max_value": 100, "seed": 42}
            ),
            Preset(
                key="6e_standard_lettres",
                label="6e Standard - Ecrire en lettres",
                description="Nombres < 1000 a ecrire en lettres",
                niveau="6e",
                params={"exercise_type": "ecrire_lettres", "difficulty": "standard", "max_value": 1000, "seed": 42}
            ),
            Preset(
                key="6e_comparer",
                label="6e - Comparer des nombres",
                description="Comparer deux nombres entiers",
                niveau="6e",
                params={"exercise_type": "comparer", "difficulty": "standard", "max_value": 10000, "seed": 42}
            ),
            Preset(
                key="6e_ranger",
                label="6e - Ranger des nombres",
                description="Ranger des nombres dans l'ordre",
                niveau="6e",
                params={"exercise_type": "ranger", "difficulty": "standard", "max_value": 1000, "seed": 42}
            ),
        ]

    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        exercise_type = params.get("exercise_type", "ecrire_lettres")
        difficulty = params.get("difficulty", "standard")
        max_value = params.get("max_value", 1000)

        # Ajuster max_value selon difficulte
        if difficulty == "facile":
            max_value = min(max_value, 100)
        elif difficulty == "standard":
            max_value = min(max_value, 1000)

        if exercise_type == "ecrire_lettres":
            variables = self._generate_ecrire_lettres(max_value)
        elif exercise_type == "ecrire_chiffres":
            variables = self._generate_ecrire_chiffres(max_value)
        elif exercise_type == "comparer":
            variables = self._generate_comparer(max_value)
        else:  # ranger
            variables = self._generate_ranger(max_value, difficulty)

        variables["exercise_type"] = exercise_type
        variables["difficulty"] = difficulty

        return {
            "variables": variables,
            "geo_data": None,
            "figure_svg_enonce": None,
            "figure_svg_solution": None,
            "meta": {"generator_key": "NOMBRES_ENTIERS_V1"},
        }

    def _generate_ecrire_lettres(self, max_value: int) -> Dict[str, Any]:
        """Genere un exercice: ecrire un nombre en lettres."""
        nombre = self.rng_randint(1, max_value)
        nombre_lettres = number_to_words(nombre)

        return {
            "enonce": f"Ecris le nombre {nombre} en lettres.",
            "nombre": nombre,
            "reponse_finale": nombre_lettres,
            "consigne": "Ecris ce nombre en toutes lettres.",
        }

    def _generate_ecrire_chiffres(self, max_value: int) -> Dict[str, Any]:
        """Genere un exercice: ecrire un nombre en chiffres."""
        nombre = self.rng_randint(1, max_value)
        nombre_lettres = number_to_words(nombre)

        return {
            "enonce": f"Ecris en chiffres : {nombre_lettres}",
            "nombre_lettres": nombre_lettres,
            "reponse_finale": str(nombre),
            "consigne": "Ecris ce nombre en chiffres.",
        }

    def _generate_comparer(self, max_value: int) -> Dict[str, Any]:
        """Genere un exercice: comparer deux nombres."""
        a = self.rng_randint(1, max_value)
        b = self.rng_randint(1, max_value)

        # Eviter l'egalite
        while b == a:
            b = self.rng_randint(1, max_value)

        if a < b:
            symbole = "<"
            reponse = f"{a} < {b}"
        else:
            symbole = ">"
            reponse = f"{a} > {b}"

        return {
            "enonce": f"Compare les nombres {a} et {b} en utilisant < ou >.",
            "nombre_a": a,
            "nombre_b": b,
            "symbole": symbole,
            "reponse_finale": reponse,
            "consigne": "Compare ces deux nombres.",
        }

    def _generate_ranger(self, max_value: int, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: ranger des nombres."""
        nb_nombres = 4 if difficulty == "facile" else 5

        nombres = []
        for _ in range(nb_nombres):
            n = self.rng_randint(1, max_value)
            while n in nombres:
                n = self.rng_randint(1, max_value)
            nombres.append(n)

        ordre = self.rng_choice(["croissant", "decroissant"])

        if ordre == "croissant":
            nombres_tries = sorted(nombres)
            consigne_ordre = "du plus petit au plus grand"
        else:
            nombres_tries = sorted(nombres, reverse=True)
            consigne_ordre = "du plus grand au plus petit"

        return {
            "enonce": f"Range les nombres suivants {consigne_ordre} : {', '.join(map(str, nombres))}",
            "nombres": nombres,
            "ordre": ordre,
            "reponse_finale": " < ".join(map(str, nombres_tries)) if ordre == "croissant" else " > ".join(map(str, nombres_tries)),
            "nombres_tries": nombres_tries,
            "consigne": f"Range ces nombres {consigne_ordre}.",
        }
