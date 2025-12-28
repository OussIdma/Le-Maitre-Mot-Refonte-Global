"""
Tests d'invariants - FRACTIONS_EGALES_V1
=========================================

Invariants testes:
1. Extension: num/den = num*k/den*k
2. Simplification: PGCD divise num et den
3. Fraction simplifiee irreductible
4. Verifier: produit en croix correct
5. Denominateur > 0
6. Pas de placeholders {{ }}
7. Reproductibilite
8. Pas de HTML dangereux
"""

import re
import pytest
from typing import Any
from math import gcd


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


class TestFractionsEgalesV1Invariants:
    """Tests d'invariants pour FRACTIONS_EGALES_V1."""

    GENERATOR_KEY = "FRACTIONS_EGALES_V1"
    NUM_SEEDS_TO_TEST = 30

    @pytest.fixture(autouse=True)
    def setup(self):
        from backend.generators.factory import GeneratorFactory
        self.factory = GeneratorFactory

    def test_extension_equivalence(self):
        """Extension: num/den = num_etendu/den_etendu."""
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "extension"},
                seed=seed
            )
            variables = result.get("variables", {})

            num = variables.get("numerateur")
            den = variables.get("denominateur")
            num_ext = variables.get("num_etendu")
            den_ext = variables.get("den_etendu")

            if all(v is not None for v in [num, den, num_ext, den_ext]):
                # Produits en croix doivent etre egaux
                assert num * den_ext == num_ext * den, (
                    f"seed={seed}: fractions non equivalentes\n"
                    f"  {num}/{den} != {num_ext}/{den_ext}"
                )

    def test_simplification_pgcd_correct(self):
        """Le PGCD divise correctement num et den."""
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "simplification"},
                seed=seed
            )
            variables = result.get("variables", {})

            num = variables.get("numerateur")
            den = variables.get("denominateur")
            pgcd = variables.get("pgcd")

            if all(v is not None for v in [num, den, pgcd]):
                assert num % pgcd == 0, f"seed={seed}: PGCD {pgcd} ne divise pas num={num}"
                assert den % pgcd == 0, f"seed={seed}: PGCD {pgcd} ne divise pas den={den}"

    def test_simplified_fraction_irreducible(self):
        """La fraction simplifiee doit etre irreductible."""
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "simplification"},
                seed=seed
            )
            variables = result.get("variables", {})

            num_simp = variables.get("num_simplifie")
            den_simp = variables.get("den_simplifie")

            if num_simp is not None and den_simp is not None:
                computed_gcd = gcd(abs(num_simp), abs(den_simp))
                assert computed_gcd == 1, (
                    f"seed={seed}: fraction {num_simp}/{den_simp} "
                    f"n'est pas irreductible (PGCD={computed_gcd})"
                )

    def test_verifier_cross_product_correct(self):
        """Produit en croix verifie correctement l'egalite."""
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "verifier"},
                seed=seed
            )
            variables = result.get("variables", {})

            num1 = variables.get("num1")
            den1 = variables.get("den1")
            num2 = variables.get("num2")
            den2 = variables.get("den2")
            sont_egales = variables.get("sont_egales")

            if all(v is not None for v in [num1, den1, num2, den2, sont_egales]):
                expected = (num1 * den2 == num2 * den1)
                assert sont_egales == expected, (
                    f"seed={seed}: verification incorrecte\n"
                    f"  {num1}/{den1} vs {num2}/{den2}\n"
                    f"  attendu: {expected}, obtenu: {sont_egales}"
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

            for key in ["denominateur", "den_etendu", "den_simplifie", "den1", "den2"]:
                den = variables.get(key)
                if den is not None:
                    assert den > 0, f"seed={seed}: {key}={den} doit etre > 0"

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

    @pytest.mark.parametrize("exercise_type", ["extension", "simplification", "verifier"])
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
