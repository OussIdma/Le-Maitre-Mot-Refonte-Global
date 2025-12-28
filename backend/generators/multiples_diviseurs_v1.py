"""
Generateur MULTIPLES_DIVISEURS_V1 - Multiples et diviseurs
==========================================================

Version: 1.0.0

Exercices sur les multiples et diviseurs:
- Lister les multiples d'un nombre
- Lister les diviseurs d'un nombre
- Verifier si un nombre est multiple/diviseur d'un autre

Chapitre cible: 6e_N07
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


def get_divisors(n: int) -> List[int]:
    """Retourne la liste des diviseurs de n."""
    divisors = []
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            divisors.append(i)
            if i != n // i:
                divisors.append(n // i)
    return sorted(divisors)


def get_multiples(n: int, count: int, start: int = 1) -> List[int]:
    """Retourne les premiers multiples de n."""
    return [n * i for i in range(start, start + count)]


@GeneratorFactory.register
class MultiplesDiviseursV1Generator(BaseGenerator):
    """Generateur Gold pour les multiples et diviseurs."""

    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="MULTIPLES_DIVISEURS_V1",
            label="Multiples et diviseurs",
            description="Exercices sur les multiples et diviseurs d'un nombre",
            version="1.0.0",
            niveaux=["6e"],
            exercise_type="MULTIPLES_DIVISEURS",
            svg_mode="NONE",
            supports_double_svg=False,
            is_dynamic=True,
            supported_grades=["6e"],
            supported_chapters=["6e_N07"],
        )

    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        return [
            ParamSchema(
                name="exercise_type",
                type=ParamType.ENUM,
                description="Type d'exercice",
                default="multiples",
                options=["multiples", "diviseurs", "verifier"]
            ),
            ParamSchema(
                name="difficulty",
                type=ParamType.ENUM,
                description="Difficulte",
                default="standard",
                options=["facile", "standard"]
            ),
            ParamSchema(
                name="max_number",
                type=ParamType.INT,
                description="Nombre maximum",
                default=50,
                min=10,
                max=200
            ),
        ]

    @classmethod
    def get_presets(cls) -> List[Preset]:
        return [
            Preset(
                key="6e_multiples_facile",
                label="6e Facile - Multiples",
                description="Trouver les multiples d'un petit nombre",
                niveau="6e",
                params={"exercise_type": "multiples", "difficulty": "facile", "max_number": 20, "seed": 42}
            ),
            Preset(
                key="6e_multiples_standard",
                label="6e Standard - Multiples",
                description="Trouver les multiples d'un nombre",
                niveau="6e",
                params={"exercise_type": "multiples", "difficulty": "standard", "max_number": 50, "seed": 42}
            ),
            Preset(
                key="6e_diviseurs",
                label="6e - Diviseurs",
                description="Trouver tous les diviseurs d'un nombre",
                niveau="6e",
                params={"exercise_type": "diviseurs", "difficulty": "standard", "max_number": 50, "seed": 42}
            ),
            Preset(
                key="6e_verifier",
                label="6e - Verifier multiple/diviseur",
                description="Verifier si un nombre est multiple ou diviseur d'un autre",
                niveau="6e",
                params={"exercise_type": "verifier", "difficulty": "standard", "max_number": 100, "seed": 42}
            ),
        ]

    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        exercise_type = params.get("exercise_type", "multiples")
        difficulty = params.get("difficulty", "standard")
        max_number = params.get("max_number", 50)

        if exercise_type == "multiples":
            variables = self._generate_multiples(difficulty)
        elif exercise_type == "diviseurs":
            variables = self._generate_diviseurs(difficulty, max_number)
        else:  # verifier
            variables = self._generate_verifier(difficulty, max_number)

        variables["exercise_type"] = exercise_type
        variables["difficulty"] = difficulty

        return {
            "variables": variables,
            "geo_data": None,
            "figure_svg_enonce": None,
            "figure_svg_solution": None,
            "meta": {"generator_key": "MULTIPLES_DIVISEURS_V1"},
        }

    def _generate_multiples(self, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: trouver les multiples."""
        if difficulty == "facile":
            nombre = self.rng_randint(2, 5)
            count = 5
        else:
            nombre = self.rng_randint(3, 12)
            count = 6

        multiples = get_multiples(nombre, count)

        return {
            "enonce": f"Donne les {count} premiers multiples de {nombre} (en commencant par {nombre}).",
            "nombre": nombre,
            "count": count,
            "multiples": multiples,
            "reponse_finale": ", ".join(map(str, multiples)),
            "consigne": f"Trouve les {count} premiers multiples de {nombre}.",
        }

    def _generate_diviseurs(self, difficulty: str, max_number: int) -> Dict[str, Any]:
        """Genere un exercice: trouver les diviseurs."""
        if difficulty == "facile":
            # Choisir un nombre avec peu de diviseurs
            candidats = [12, 15, 16, 18, 20, 24]
            nombre = self.rng_choice(candidats)
        else:
            nombre = self.rng_randint(20, min(max_number, 60))

        diviseurs = get_divisors(nombre)

        return {
            "enonce": f"Trouve tous les diviseurs de {nombre}.",
            "nombre": nombre,
            "diviseurs": diviseurs,
            "nb_diviseurs": len(diviseurs),
            "reponse_finale": ", ".join(map(str, diviseurs)),
            "consigne": "Liste tous les diviseurs de ce nombre.",
        }

    def _generate_verifier(self, difficulty: str, max_number: int) -> Dict[str, Any]:
        """Genere un exercice: verifier si a est multiple/diviseur de b."""
        operation = self.rng_choice(["multiple", "diviseur"])

        if operation == "multiple":
            # a est-il un multiple de b ?
            b = self.rng_randint(2, 12)
            if self._rng.random() < 0.6:
                # Cas vrai
                k = self.rng_randint(2, 10)
                a = b * k
                est_vrai = True
            else:
                # Cas faux
                a = self.rng_randint(10, max_number)
                while a % b == 0:
                    a = self.rng_randint(10, max_number)
                est_vrai = False

            enonce = f"Le nombre {a} est-il un multiple de {b} ?"
            explication = f"{a} = {b} x {a // b}" if est_vrai else f"{a} = {b} x {a // b} + {a % b} (reste non nul)"
        else:
            # a est-il un diviseur de b ?
            if self._rng.random() < 0.6:
                # Cas vrai
                a = self.rng_randint(2, 12)
                k = self.rng_randint(2, 8)
                b = a * k
                est_vrai = True
            else:
                # Cas faux
                b = self.rng_randint(20, max_number)
                a = self.rng_randint(2, 12)
                while b % a == 0:
                    a = self.rng_randint(2, 12)
                est_vrai = False

            enonce = f"Le nombre {a} est-il un diviseur de {b} ?"
            explication = f"{b} = {a} x {b // a}" if est_vrai else f"{b} = {a} x {b // a} + {b % a} (reste non nul)"

        return {
            "enonce": enonce,
            "nombre_a": a,
            "nombre_b": b,
            "operation": operation,
            "est_vrai": est_vrai,
            "reponse_finale": "Oui" if est_vrai else "Non",
            "explication": explication,
            "consigne": "Justifie ta reponse.",
        }
