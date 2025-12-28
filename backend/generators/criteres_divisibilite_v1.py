"""
Generateur CRITERES_DIVISIBILITE_V1 - Criteres de divisibilite
==============================================================

Version: 1.0.0

Exercices sur les criteres de divisibilite:
- Verifier si un nombre est divisible par 2, 3, 5, 9, 10
- Identifier les diviseurs d'un nombre
- Trouver des nombres divisibles par un critere donne

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


def is_divisible_by(n: int, d: int) -> bool:
    """Verifie si n est divisible par d."""
    return n % d == 0


def get_divisibility_explanation(n: int, d: int) -> str:
    """Retourne une explication du critere de divisibilite."""
    not_div = "n'est pas"
    if d == 2:
        last_digit = n % 10
        is_div = last_digit in [0, 2, 4, 6, 8]
        pair_text = "Il est pair" if is_div else "Il est impair"
        div_text = "est" if is_div else not_div
        return f"Le chiffre des unites est {last_digit}. {pair_text}, donc {n} {div_text} divisible par 2."
    elif d == 5:
        last_digit = n % 10
        is_div = last_digit in [0, 5]
        five_text = "Il est 0 ou 5" if is_div else "Il n'est ni 0 ni 5"
        div_text = "est" if is_div else not_div
        return f"Le chiffre des unites est {last_digit}. {five_text}, donc {n} {div_text} divisible par 5."
    elif d == 10:
        last_digit = n % 10
        is_div = last_digit == 0
        ten_text = "Il est 0" if is_div else "Il n'est pas 0"
        div_text = "est" if is_div else not_div
        return f"Le chiffre des unites est {last_digit}. {ten_text}, donc {n} {div_text} divisible par 10."
    elif d == 3:
        digit_sum = sum(int(c) for c in str(n))
        is_div = digit_sum % 3 == 0
        sum_text = "Elle est divisible par 3" if is_div else "Elle n'est pas divisible par 3"
        div_text = "est" if is_div else not_div
        return f"La somme des chiffres est {digit_sum}. {sum_text}, donc {n} {div_text} divisible par 3."
    elif d == 9:
        digit_sum = sum(int(c) for c in str(n))
        is_div = digit_sum % 9 == 0
        sum_text = "Elle est divisible par 9" if is_div else "Elle n'est pas divisible par 9"
        div_text = "est" if is_div else not_div
        return f"La somme des chiffres est {digit_sum}. {sum_text}, donc {n} {div_text} divisible par 9."
    return ""


@GeneratorFactory.register
class CriteresDivisibiliteV1Generator(BaseGenerator):
    """Generateur Gold pour les criteres de divisibilite."""

    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="CRITERES_DIVISIBILITE_V1",
            label="Criteres de divisibilite",
            description="Exercices sur les criteres de divisibilite par 2, 3, 5, 9, 10",
            version="1.0.0",
            niveaux=["6e"],
            exercise_type="CRITERES_DIVISIBILITE",
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
                default="verifier",
                options=["verifier", "trouver", "identifier"]
            ),
            ParamSchema(
                name="diviseur",
                type=ParamType.ENUM,
                description="Diviseur a tester",
                default="2",
                options=["2", "3", "5", "9", "10", "aleatoire"]
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
                key="6e_div2",
                label="6e - Divisibilite par 2",
                description="Verifier la divisibilite par 2",
                niveau="6e",
                params={"exercise_type": "verifier", "diviseur": "2", "difficulty": "facile", "seed": 42}
            ),
            Preset(
                key="6e_div3",
                label="6e - Divisibilite par 3",
                description="Verifier la divisibilite par 3",
                niveau="6e",
                params={"exercise_type": "verifier", "diviseur": "3", "difficulty": "standard", "seed": 42}
            ),
            Preset(
                key="6e_div5",
                label="6e - Divisibilite par 5",
                description="Verifier la divisibilite par 5",
                niveau="6e",
                params={"exercise_type": "verifier", "diviseur": "5", "difficulty": "facile", "seed": 42}
            ),
            Preset(
                key="6e_identifier",
                label="6e - Identifier les diviseurs",
                description="Identifier par quels nombres un nombre est divisible",
                niveau="6e",
                params={"exercise_type": "identifier", "diviseur": "aleatoire", "difficulty": "standard", "seed": 42}
            ),
        ]

    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        exercise_type = params.get("exercise_type", "verifier")
        diviseur_param = params.get("diviseur", "2")
        difficulty = params.get("difficulty", "standard")

        # Determiner le diviseur
        if diviseur_param == "aleatoire":
            diviseur = self.rng_choice([2, 3, 5, 9, 10])
        else:
            diviseur = int(diviseur_param)

        if exercise_type == "verifier":
            variables = self._generate_verifier(diviseur, difficulty)
        elif exercise_type == "trouver":
            variables = self._generate_trouver(diviseur, difficulty)
        else:  # identifier
            variables = self._generate_identifier(difficulty)

        variables["exercise_type"] = exercise_type
        variables["difficulty"] = difficulty

        return {
            "variables": variables,
            "geo_data": None,
            "figure_svg_enonce": None,
            "figure_svg_solution": None,
            "meta": {"generator_key": "CRITERES_DIVISIBILITE_V1"},
        }

    def _generate_verifier(self, diviseur: int, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: verifier si un nombre est divisible."""
        if difficulty == "facile":
            nombre = self.rng_randint(10, 100)
        else:
            nombre = self.rng_randint(100, 1000)

        is_div = is_divisible_by(nombre, diviseur)
        explication = get_divisibility_explanation(nombre, diviseur)

        return {
            "enonce": f"Le nombre {nombre} est-il divisible par {diviseur} ?",
            "nombre": nombre,
            "diviseur": diviseur,
            "est_divisible": is_div,
            "reponse_finale": "Oui" if is_div else "Non",
            "explication": explication,
            "consigne": f"Utilise le critere de divisibilite par {diviseur}.",
        }

    def _generate_trouver(self, diviseur: int, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: trouver un nombre divisible."""
        if difficulty == "facile":
            min_val, max_val = 10, 50
        else:
            min_val, max_val = 50, 200

        # Generer quelques nombres, certains divisibles, d'autres non
        nombres = []
        for _ in range(6):
            n = self.rng_randint(min_val, max_val)
            if n not in nombres:
                nombres.append(n)

        divisibles = [n for n in nombres if is_divisible_by(n, diviseur)]

        return {
            "enonce": f"Parmi les nombres suivants, lesquels sont divisibles par {diviseur} ? {', '.join(map(str, nombres))}",
            "nombres": nombres,
            "diviseur": diviseur,
            "divisibles": divisibles,
            "reponse_finale": ", ".join(map(str, divisibles)) if divisibles else "Aucun",
            "consigne": f"Trouve les nombres divisibles par {diviseur}.",
        }

    def _generate_identifier(self, difficulty: str) -> Dict[str, Any]:
        """Genere un exercice: identifier par quoi un nombre est divisible."""
        if difficulty == "facile":
            # Generer un nombre divisible par au moins un critere simple
            base = self.rng_randint(1, 20)
            mult = self.rng_choice([2, 5, 10])
            nombre = base * mult
        else:
            # Generer un nombre avec des proprietes interessantes
            nombre = self.rng_randint(100, 500)

        diviseurs_test = [2, 3, 5, 9, 10]
        diviseurs_ok = [d for d in diviseurs_test if is_divisible_by(nombre, d)]

        return {
            "enonce": f"Par quels nombres parmi 2, 3, 5, 9 et 10 le nombre {nombre} est-il divisible ?",
            "nombre": nombre,
            "diviseurs_testes": diviseurs_test,
            "diviseurs_ok": diviseurs_ok,
            "reponse_finale": ", ".join(map(str, diviseurs_ok)) if diviseurs_ok else "Aucun",
            "consigne": "Identifie tous les diviseurs parmi 2, 3, 5, 9, 10.",
        }
