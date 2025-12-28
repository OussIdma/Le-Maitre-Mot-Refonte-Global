"""
Tests d'invariants - CRITERES_DIVISIBILITE_V1
=============================================

Ces tests verifient des proprietes mathematiques stables
qui ne doivent JAMAIS etre violees.

Invariants testes:
1. Divisibilite par 2: le dernier chiffre est pair
2. Divisibilite par 5: le dernier chiffre est 0 ou 5
3. Divisibilite par 10: le dernier chiffre est 0
4. Divisibilite par 3: la somme des chiffres est divisible par 3
5. Divisibilite par 9: la somme des chiffres est divisible par 9
6. Pas de placeholders {{ }} dans les variables
7. Reproductibilite: meme seed = memes variables
8. Pas de HTML dangereux (XSS)
"""

import re
import pytest
from typing import Any


# Patterns de detection
PLACEHOLDER_PATTERN = re.compile(r'\{\{[^}]+\}\}')
DANGEROUS_HTML_PATTERN = re.compile(
    r'<\s*script|javascript\s*:|onerror\s*=|onload\s*=',
    re.IGNORECASE
)


def check_no_placeholders_recursive(obj: Any, path: str = "") -> list:
    """Verifie recursivement qu'aucun placeholder {{ }} n'est present."""
    found = []
    if isinstance(obj, str):
        if PLACEHOLDER_PATTERN.search(obj):
            found.append(f"{path}: '{obj[:50]}...'")
    elif isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}" if path else key
            found.extend(check_no_placeholders_recursive(value, child_path))
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            child_path = f"{path}[{i}]"
            found.extend(check_no_placeholders_recursive(item, child_path))
    return found


def check_no_dangerous_html_recursive(obj: Any, path: str = "") -> list:
    """Verifie recursivement qu'aucun HTML dangereux n'est present."""
    found = []
    if isinstance(obj, str):
        if DANGEROUS_HTML_PATTERN.search(obj):
            found.append(f"{path}: pattern dangereux detecte")
    elif isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}" if path else key
            found.extend(check_no_dangerous_html_recursive(value, child_path))
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            child_path = f"{path}[{i}]"
            found.extend(check_no_dangerous_html_recursive(item, child_path))
    return found


def is_divisible_by(n: int, d: int) -> bool:
    """Verifie si n est divisible par d."""
    return n % d == 0


class TestCriteresDivisibiliteV1Invariants:
    """Tests d'invariants pour CRITERES_DIVISIBILITE_V1."""

    GENERATOR_KEY = "CRITERES_DIVISIBILITE_V1"
    NUM_SEEDS_TO_TEST = 30

    @pytest.fixture(autouse=True)
    def setup(self):
        """Import tardif pour eviter les problemes de chargement."""
        from backend.generators.factory import GeneratorFactory
        self.factory = GeneratorFactory

    # =========================================================================
    # INVARIANT 1: Divisibilite par 2 (dernier chiffre pair)
    # =========================================================================

    def test_divisibility_by_2(self):
        """
        La reponse de divisibilite par 2 doit etre correcte.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "verifier", "diviseur": "2"},
                seed=seed
            )
            variables = result.get("variables", {})

            nombre = variables.get("nombre")
            est_divisible = variables.get("est_divisible")

            if nombre is not None and est_divisible is not None:
                expected = is_divisible_by(nombre, 2)
                assert est_divisible == expected, (
                    f"seed={seed}: divisibilite par 2 incorrecte\n"
                    f"  {nombre} % 2 = {nombre % 2}\n"
                    f"  attendu: {expected}, obtenu: {est_divisible}"
                )

    # =========================================================================
    # INVARIANT 2: Divisibilite par 5 (dernier chiffre 0 ou 5)
    # =========================================================================

    def test_divisibility_by_5(self):
        """
        La reponse de divisibilite par 5 doit etre correcte.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "verifier", "diviseur": "5"},
                seed=seed
            )
            variables = result.get("variables", {})

            nombre = variables.get("nombre")
            est_divisible = variables.get("est_divisible")

            if nombre is not None and est_divisible is not None:
                expected = is_divisible_by(nombre, 5)
                assert est_divisible == expected, (
                    f"seed={seed}: divisibilite par 5 incorrecte\n"
                    f"  {nombre} % 5 = {nombre % 5}\n"
                    f"  attendu: {expected}, obtenu: {est_divisible}"
                )

    # =========================================================================
    # INVARIANT 3: Divisibilite par 3 (somme des chiffres)
    # =========================================================================

    def test_divisibility_by_3(self):
        """
        La reponse de divisibilite par 3 doit etre correcte.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "verifier", "diviseur": "3"},
                seed=seed
            )
            variables = result.get("variables", {})

            nombre = variables.get("nombre")
            est_divisible = variables.get("est_divisible")

            if nombre is not None and est_divisible is not None:
                expected = is_divisible_by(nombre, 3)
                assert est_divisible == expected, (
                    f"seed={seed}: divisibilite par 3 incorrecte\n"
                    f"  {nombre} % 3 = {nombre % 3}\n"
                    f"  attendu: {expected}, obtenu: {est_divisible}"
                )

    # =========================================================================
    # INVARIANT 4: Divisibilite par 9 (somme des chiffres)
    # =========================================================================

    def test_divisibility_by_9(self):
        """
        La reponse de divisibilite par 9 doit etre correcte.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "verifier", "diviseur": "9"},
                seed=seed
            )
            variables = result.get("variables", {})

            nombre = variables.get("nombre")
            est_divisible = variables.get("est_divisible")

            if nombre is not None and est_divisible is not None:
                expected = is_divisible_by(nombre, 9)
                assert est_divisible == expected, (
                    f"seed={seed}: divisibilite par 9 incorrecte\n"
                    f"  {nombre} % 9 = {nombre % 9}\n"
                    f"  attendu: {expected}, obtenu: {est_divisible}"
                )

    # =========================================================================
    # INVARIANT 5: Identifier tous les diviseurs correctement
    # =========================================================================

    def test_identify_all_divisors(self):
        """
        L'exercice identifier doit lister correctement tous les diviseurs.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "identifier"},
                seed=seed
            )
            variables = result.get("variables", {})

            nombre = variables.get("nombre")
            diviseurs_ok = variables.get("diviseurs_ok", [])

            if nombre is not None:
                for d in [2, 3, 5, 9, 10]:
                    is_div = is_divisible_by(nombre, d)
                    if is_div:
                        assert d in diviseurs_ok, (
                            f"seed={seed}: {nombre} est divisible par {d} "
                            f"mais {d} n'est pas dans diviseurs_ok={diviseurs_ok}"
                        )
                    else:
                        assert d not in diviseurs_ok, (
                            f"seed={seed}: {nombre} n'est pas divisible par {d} "
                            f"mais {d} est dans diviseurs_ok={diviseurs_ok}"
                        )

    # =========================================================================
    # INVARIANT 6: Pas de placeholders {{ }} non resolus
    # =========================================================================

    def test_no_unresolved_placeholders(self):
        """
        Aucun placeholder {{ }} ne doit rester dans les variables.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            variables = result.get("variables", {})

            placeholders = check_no_placeholders_recursive(variables, "variables")
            assert len(placeholders) == 0, (
                f"seed={seed}: placeholders non resolus trouves:\n"
                + "\n".join(placeholders[:5])
            )

    # =========================================================================
    # INVARIANT 7: Reproductibilite (meme seed = memes variables)
    # =========================================================================

    def test_reproducibility_same_seed_same_result(self):
        """
        Avec la meme seed et les memes parametres, le resultat doit etre identique.
        """
        test_seeds = [0, 42, 123, 999]

        for seed in test_seeds:
            result1 = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            result2 = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )

            vars1 = result1.get("variables", {})
            vars2 = result2.get("variables", {})

            assert vars1 == vars2, (
                f"seed={seed}: resultats differents:\n"
                f"  1: {vars1}\n"
                f"  2: {vars2}"
            )

    # =========================================================================
    # INVARIANT 8: Pas de HTML dangereux (XSS)
    # =========================================================================

    def test_no_dangerous_html_in_variables(self):
        """
        Les variables string ne doivent pas contenir de HTML dangereux.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            variables = result.get("variables", {})

            dangerous = check_no_dangerous_html_recursive(variables, "variables")
            assert len(dangerous) == 0, (
                f"seed={seed}: HTML dangereux detecte:\n"
                + "\n".join(dangerous[:5])
            )

    # =========================================================================
    # INVARIANT 9: Structure de sortie valide
    # =========================================================================

    def test_output_structure(self):
        """
        Le output doit contenir les cles obligatoires.
        """
        result = self.factory.generate(
            key=self.GENERATOR_KEY,
            overrides={},
            seed=42
        )

        assert "variables" in result, "Le output doit contenir 'variables'"
        variables = result["variables"]

        assert "enonce" in variables, "Variable obligatoire manquante: enonce"
        assert "reponse_finale" in variables, "Variable obligatoire manquante: reponse_finale"

    # =========================================================================
    # INVARIANT 10: Tous les types d'exercices fonctionnent
    # =========================================================================

    @pytest.mark.parametrize("exercise_type", ["verifier", "trouver", "identifier"])
    def test_all_exercise_types_work(self, exercise_type):
        """
        Tous les types d'exercices doivent produire des resultats valides.
        """
        for seed in range(10):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": exercise_type},
                seed=seed
            )
            variables = result.get("variables", {})

            assert "enonce" in variables, (
                f"exercise_type={exercise_type}, seed={seed}: "
                "enonce manquant"
            )
            assert "reponse_finale" in variables, (
                f"exercise_type={exercise_type}, seed={seed}: "
                "reponse_finale manquante"
            )
