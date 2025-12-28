"""
Tests d'invariants - FRACTION_COMPARAISON_V1
=============================================

Invariants testes:
1. Comparaison correcte (produit en croix)
2. Rangement correct (ordre croissant verifie)
3. Denominateur > 0
4. Pas de placeholders {{ }}
5. Reproductibilite
6. Pas de HTML dangereux
"""

import re
import pytest
from typing import Any


PLACEHOLDER_PATTERN = re.compile(r'\{\{[^}]+\}\}')
DANGEROUS_HTML_PATTERN = re.compile(
    r'<\s*script|javascript\s*:|onerror\s*=|onload\s*=',
    re.IGNORECASE
)


def check_no_placeholders_recursive(obj: Any, path: str = "") -> list:
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
            found.extend(check_no_placeholders_recursive(item, f"{path}[{i}]"))
    return found


def check_no_dangerous_html_recursive(obj: Any, path: str = "") -> list:
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
            found.extend(check_no_dangerous_html_recursive(item, f"{path}[{i}]"))
    return found


def compare_fractions(num1, den1, num2, den2):
    """Compare deux fractions, retourne le signe."""
    val1 = num1 * den2
    val2 = num2 * den1
    if val1 < val2:
        return "<"
    elif val1 > val2:
        return ">"
    return "="


class TestFractionComparaisonV1Invariants:
    """Tests d'invariants pour FRACTION_COMPARAISON_V1."""

    GENERATOR_KEY = "FRACTION_COMPARAISON_V1"
    NUM_SEEDS_TO_TEST = 30

    @pytest.fixture(autouse=True)
    def setup(self):
        from backend.generators.factory import GeneratorFactory
        self.factory = GeneratorFactory

    def test_comparison_correctness(self):
        """Le signe de comparaison doit etre mathematiquement correct."""
        for exercise_type in ["meme_denominateur", "meme_numerateur", "produit_croix"]:
            for seed in range(self.NUM_SEEDS_TO_TEST):
                result = self.factory.generate(
                    key=self.GENERATOR_KEY,
                    overrides={"exercise_type": exercise_type},
                    seed=seed
                )
                variables = result.get("variables", {})

                num1 = variables.get("num1")
                den1 = variables.get("den1")
                num2 = variables.get("num2")
                den2 = variables.get("den2")
                signe = variables.get("signe")

                if all(v is not None for v in [num1, den1, num2, den2, signe]):
                    expected = compare_fractions(num1, den1, num2, den2)
                    assert signe == expected, (
                        f"seed={seed}, type={exercise_type}: comparaison incorrecte\n"
                        f"  {num1}/{den1} vs {num2}/{den2}\n"
                        f"  attendu: {expected}, obtenu: {signe}"
                    )

    def test_ordering_correctness(self):
        """Le rangement doit etre dans l'ordre croissant."""
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "ranger"},
                seed=seed
            )
            variables = result.get("variables", {})

            fractions_triees = variables.get("fractions_triees", [])

            if len(fractions_triees) >= 2:
                # Verifier que chaque fraction est <= la suivante
                for i in range(len(fractions_triees) - 1):
                    f1 = fractions_triees[i]
                    f2 = fractions_triees[i + 1]
                    val1 = f1[0] / f1[1]
                    val2 = f2[0] / f2[1]
                    assert val1 <= val2, (
                        f"seed={seed}: ordre incorrect\n"
                        f"  {f1[0]}/{f1[1]} = {val1} devrait etre <= {f2[0]}/{f2[1]} = {val2}"
                    )

    def test_denominators_positive(self):
        """Tous les denominateurs doivent etre > 0."""
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            variables = result.get("variables", {})

            for key in ["den1", "den2"]:
                den = variables.get(key)
                if den is not None:
                    assert den > 0, f"seed={seed}: {key}={den} doit etre > 0"

            # Pour ranger, verifier les fractions
            fractions = variables.get("fractions", [])
            for f in fractions:
                assert f[1] > 0, f"seed={seed}: denominateur {f[1]} doit etre > 0"

    def test_numerators_positive(self):
        """Tous les numerateurs doivent etre > 0."""
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            variables = result.get("variables", {})

            for key in ["num1", "num2"]:
                num = variables.get(key)
                if num is not None:
                    assert num > 0, f"seed={seed}: {key}={num} doit etre > 0"

    def test_no_unresolved_placeholders(self):
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(key=self.GENERATOR_KEY, overrides={}, seed=seed)
            variables = result.get("variables", {})
            placeholders = check_no_placeholders_recursive(variables, "variables")
            assert len(placeholders) == 0

    def test_reproducibility_same_seed_same_result(self):
        for seed in [0, 42, 123, 999]:
            result1 = self.factory.generate(key=self.GENERATOR_KEY, overrides={}, seed=seed)
            result2 = self.factory.generate(key=self.GENERATOR_KEY, overrides={}, seed=seed)
            assert result1.get("variables") == result2.get("variables")

    def test_no_dangerous_html_in_variables(self):
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(key=self.GENERATOR_KEY, overrides={}, seed=seed)
            variables = result.get("variables", {})
            dangerous = check_no_dangerous_html_recursive(variables, "variables")
            assert len(dangerous) == 0

    def test_output_structure(self):
        result = self.factory.generate(key=self.GENERATOR_KEY, overrides={}, seed=42)
        assert "variables" in result
        variables = result["variables"]
        assert "enonce" in variables
        assert "reponse_finale" in variables

    @pytest.mark.parametrize("exercise_type", ["meme_denominateur", "meme_numerateur", "produit_croix", "ranger"])
    def test_all_exercise_types_work(self, exercise_type):
        for seed in range(10):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": exercise_type},
                seed=seed
            )
            variables = result.get("variables", {})
            assert "enonce" in variables
            assert "reponse_finale" in variables
