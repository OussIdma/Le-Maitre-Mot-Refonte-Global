"""
Tests d'invariants - SIMPLIFICATION_FRACTIONS_V2
================================================

Ces tests vérifient des propriétés mathématiques stables
qui ne doivent JAMAIS être violées.

Invariants testés:
1. Équivalence: n/d = n_red/d_red
2. Le PGCD divise le numérateur et le dénominateur
3. La fraction réduite est irréductible (PGCD = 1)
4. Pas de placeholders {{ }} dans les variables
5. Reproductibilité: même seed = mêmes variables
6. Pas de HTML dangereux (XSS)
"""

import re
import math
import pytest
from typing import Dict, Any


# Patterns de détection
PLACEHOLDER_PATTERN = re.compile(r'\{\{[^}]+\}\}')
DANGEROUS_HTML_PATTERN = re.compile(
    r'<\s*script|javascript\s*:|onerror\s*=|onload\s*=',
    re.IGNORECASE
)


def gcd(a: int, b: int) -> int:
    """Calcule le PGCD de deux nombres."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def check_no_placeholders_recursive(obj: Any, path: str = "") -> list:
    """Vérifie récursivement qu'aucun placeholder {{ }} n'est présent."""
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
    """Vérifie récursivement qu'aucun HTML dangereux n'est présent."""
    found = []
    if isinstance(obj, str):
        if DANGEROUS_HTML_PATTERN.search(obj):
            found.append(f"{path}: pattern dangereux détecté")
    elif isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}" if path else key
            found.extend(check_no_dangerous_html_recursive(value, child_path))
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            child_path = f"{path}[{i}]"
            found.extend(check_no_dangerous_html_recursive(item, child_path))
    return found


class TestSimplificationFractionsV2Invariants:
    """Tests d'invariants pour SIMPLIFICATION_FRACTIONS_V2."""

    GENERATOR_KEY = "SIMPLIFICATION_FRACTIONS_V2"
    NUM_SEEDS_TO_TEST = 30

    @pytest.fixture(autouse=True)
    def setup(self):
        """Import tardif pour éviter les problèmes de chargement."""
        from backend.generators.factory import GeneratorFactory
        self.factory = GeneratorFactory

    # =========================================================================
    # INVARIANT 1: Équivalence n/d = n_red/d_red
    # =========================================================================

    def test_fraction_equivalence(self):
        """
        La fraction réduite doit être équivalente à la fraction originale.

        n/d = n_red/d_red => n * d_red = n_red * d
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            geo_data = result.get("geo_data", {})

            n = geo_data.get("n")
            d = geo_data.get("d")
            n_red = geo_data.get("n_red")
            d_red = geo_data.get("d_red")

            # Vérifier que les valeurs existent
            assert all(v is not None for v in [n, d, n_red, d_red]), (
                f"seed={seed}: valeurs manquantes dans geo_data"
            )

            # Vérifier l'équivalence: n * d_red = n_red * d
            assert n * d_red == n_red * d, (
                f"seed={seed}: fractions non équivalentes!\n"
                f"  {n}/{d} != {n_red}/{d_red}\n"
                f"  {n} * {d_red} = {n * d_red}\n"
                f"  {n_red} * {d} = {n_red * d}"
            )

    # =========================================================================
    # INVARIANT 2: Le PGCD divise le numérateur et le dénominateur
    # =========================================================================

    def test_pgcd_divides_numerator_and_denominator(self):
        """
        Le PGCD annoncé doit effectivement diviser n et d.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            geo_data = result.get("geo_data", {})

            n = geo_data.get("n")
            d = geo_data.get("d")
            pgcd = geo_data.get("pgcd")

            # Le PGCD doit diviser n
            assert n % pgcd == 0, (
                f"seed={seed}: PGCD {pgcd} ne divise pas n={n}"
            )

            # Le PGCD doit diviser d
            assert d % pgcd == 0, (
                f"seed={seed}: PGCD {pgcd} ne divise pas d={d}"
            )

    # =========================================================================
    # INVARIANT 3: La fraction réduite est irréductible
    # =========================================================================

    def test_reduced_fraction_is_irreducible(self):
        """
        La fraction réduite doit avoir un PGCD de 1.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            geo_data = result.get("geo_data", {})

            n_red = abs(geo_data.get("n_red", 0))
            d_red = abs(geo_data.get("d_red", 1))

            computed_gcd = gcd(n_red, d_red)
            assert computed_gcd == 1, (
                f"seed={seed}: fraction réduite {n_red}/{d_red} "
                f"n'est pas irréductible (PGCD={computed_gcd})"
            )

    # =========================================================================
    # INVARIANT 4: Pas de placeholders {{ }} non résolus
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
                f"seed={seed}: placeholders non résolus trouvés:\n"
                + "\n".join(placeholders[:5])
            )

    # =========================================================================
    # INVARIANT 5: Reproductibilité (même seed = mêmes variables)
    # =========================================================================

    def test_reproducibility_same_seed_same_result(self):
        """
        Avec la même seed et les mêmes paramètres, le résultat doit être identique.
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

            geo1 = result1.get("geo_data", {})
            geo2 = result2.get("geo_data", {})

            # Comparer les valeurs numériques
            for key in ["n", "d", "n_red", "d_red", "pgcd"]:
                assert geo1.get(key) == geo2.get(key), (
                    f"seed={seed}: résultats différents pour '{key}':\n"
                    f"  1: {geo1.get(key)}\n"
                    f"  2: {geo2.get(key)}"
                )

    # =========================================================================
    # INVARIANT 6: Pas de HTML dangereux (XSS)
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
                f"seed={seed}: HTML dangereux détecté:\n"
                + "\n".join(dangerous[:5])
            )

    # =========================================================================
    # INVARIANT 7: Structure de sortie valide
    # =========================================================================

    def test_output_structure(self):
        """
        Le output doit contenir les clés obligatoires.
        """
        result = self.factory.generate(
            key=self.GENERATOR_KEY,
            overrides={},
            seed=42
        )

        # Clés obligatoires
        assert "variables" in result, "Le output doit contenir 'variables'"
        assert "geo_data" in result, "Le output doit contenir 'geo_data'"

        geo_data = result["geo_data"]

        # Variables numériques obligatoires dans geo_data
        required_geo = ["n", "d", "n_red", "d_red", "pgcd"]
        for var in required_geo:
            assert var in geo_data, f"Variable geo_data obligatoire manquante: {var}"

    # =========================================================================
    # INVARIANT 8: Dénominateur non nul
    # =========================================================================

    def test_denominators_are_positive(self):
        """
        Les dénominateurs doivent être positifs (non nuls).
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            geo_data = result.get("geo_data", {})

            d = geo_data.get("d")
            d_red = geo_data.get("d_red")

            assert d > 0, f"seed={seed}: dénominateur d={d} doit être > 0"
            assert d_red > 0, f"seed={seed}: dénominateur réduit d_red={d_red} doit être > 0"

    # =========================================================================
    # INVARIANT 9: Cohérence avec les différentes difficultés
    # =========================================================================

    @pytest.mark.parametrize("difficulty", ["facile", "moyen", "difficile"])
    def test_all_difficulties_produce_valid_fractions(self, difficulty):
        """
        Toutes les difficultés doivent produire des fractions valides.
        """
        for seed in range(10):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"difficulty": difficulty},
                seed=seed
            )
            geo_data = result.get("geo_data", {})

            # Vérifier l'équivalence
            n = geo_data.get("n")
            d = geo_data.get("d")
            n_red = geo_data.get("n_red")
            d_red = geo_data.get("d_red")

            assert n * d_red == n_red * d, (
                f"difficulty={difficulty}, seed={seed}: "
                f"fractions non équivalentes {n}/{d} != {n_red}/{d_red}"
            )
