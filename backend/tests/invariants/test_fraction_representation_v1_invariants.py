"""
Tests d'invariants - FRACTION_REPRESENTATION_V1
================================================

Invariants testes:
1. Numerateur < Denominateur pour les fractions propres
2. Denominateur > 0
3. Pas de placeholders {{ }}
4. Reproductibilite
5. Pas de HTML dangereux
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


class TestFractionRepresentationV1Invariants:
    """Tests d'invariants pour FRACTION_REPRESENTATION_V1."""

    GENERATOR_KEY = "FRACTION_REPRESENTATION_V1"
    NUM_SEEDS_TO_TEST = 30

    @pytest.fixture(autouse=True)
    def setup(self):
        from backend.generators.factory import GeneratorFactory
        self.factory = GeneratorFactory

    def test_denominator_positive(self):
        """Le denominateur doit etre strictement positif."""
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            variables = result.get("variables", {})

            denominateur = variables.get("denominateur")
            if denominateur is not None:
                assert denominateur > 0, (
                    f"seed={seed}: denominateur={denominateur} doit etre > 0"
                )

    def test_numerator_valid_for_lire_representer(self):
        """Pour lire/representer, numerateur < denominateur."""
        for exercise_type in ["lire", "representer"]:
            for seed in range(self.NUM_SEEDS_TO_TEST):
                result = self.factory.generate(
                    key=self.GENERATOR_KEY,
                    overrides={"exercise_type": exercise_type},
                    seed=seed
                )
                variables = result.get("variables", {})

                numerateur = variables.get("numerateur")
                denominateur = variables.get("denominateur")

                if numerateur is not None and denominateur is not None:
                    assert 0 < numerateur < denominateur, (
                        f"seed={seed}, type={exercise_type}: "
                        f"numerateur={numerateur} doit etre entre 0 et {denominateur}"
                    )

    def test_no_unresolved_placeholders(self):
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            variables = result.get("variables", {})
            placeholders = check_no_placeholders_recursive(variables, "variables")
            assert len(placeholders) == 0, (
                f"seed={seed}: placeholders trouves:\n" + "\n".join(placeholders[:5])
            )

    def test_reproducibility_same_seed_same_result(self):
        for seed in [0, 42, 123, 999]:
            result1 = self.factory.generate(key=self.GENERATOR_KEY, overrides={}, seed=seed)
            result2 = self.factory.generate(key=self.GENERATOR_KEY, overrides={}, seed=seed)

            vars1 = result1.get("variables", {})
            vars2 = result2.get("variables", {})

            assert vars1 == vars2, f"seed={seed}: resultats differents"

    def test_no_dangerous_html_in_variables(self):
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            variables = result.get("variables", {})
            dangerous = check_no_dangerous_html_recursive(variables, "variables")
            assert len(dangerous) == 0, (
                f"seed={seed}: HTML dangereux:\n" + "\n".join(dangerous[:5])
            )

    def test_output_structure(self):
        result = self.factory.generate(key=self.GENERATOR_KEY, overrides={}, seed=42)

        assert "variables" in result
        variables = result["variables"]
        assert "enonce" in variables
        assert "reponse_finale" in variables

    @pytest.mark.parametrize("exercise_type", ["lire", "representer", "placer"])
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
