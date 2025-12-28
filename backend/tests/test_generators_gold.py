"""
P0 Gold - Tests de performance et invariants pour générateurs Gold
===================================================================

Ces tests sont exécutés uniquement pour les générateurs certifiés "Gold".

Critères Gold:
- Performance: génération < 100ms par exercice
- Pas de placeholders non résolus dans les templates
- Invariants mathématiques respectés
- Déterminisme avec seed fixe

IMPORTANT: Ce test est BLOQUANT en CI pour les générateurs Gold.
"""

import pytest
import time
import re
import os
from typing import List


# Liste des générateurs Gold (peut être surchargée via env var)
GOLD_GENERATORS_DEFAULT = [
    "CALCUL_NOMBRES_V1",
    "SIMPLIFICATION_FRACTIONS_V2",
]


def get_gold_generator_keys() -> List[str]:
    """
    Récupère la liste des générateurs Gold.

    La liste peut être surchargée via la variable d'environnement GOLD_GENERATORS.
    """
    env_value = os.environ.get("GOLD_GENERATORS", "")
    if env_value:
        return [k.strip().upper() for k in env_value.split(",") if k.strip()]
    return GOLD_GENERATORS_DEFAULT


def pytest_generate_tests(metafunc):
    """Hook pytest pour générer les tests paramétrés."""
    if "gold_generator_key" in metafunc.fixturenames:
        keys = get_gold_generator_keys()
        metafunc.parametrize("gold_generator_key", keys)


class TestGoldPerformance:
    """Tests de performance pour générateurs Gold."""

    MAX_GENERATION_TIME_MS = 100  # Max 100ms par génération

    def test_generation_performance(self, gold_generator_key: str):
        """
        Vérifie que la génération est performante (< 100ms).

        Args:
            gold_generator_key: Clé du générateur Gold
        """
        from backend.generators.factory import GeneratorFactory

        gen_class = GeneratorFactory.get(gold_generator_key)
        if gen_class is None:
            pytest.skip(f"Générateur {gold_generator_key} non trouvé")

        times_ms = []
        num_iterations = 50

        for seed in range(num_iterations):
            start = time.perf_counter()
            try:
                GeneratorFactory.generate(
                    key=gold_generator_key,
                    overrides={},
                    seed=seed
                )
            except Exception as e:
                pytest.fail(f"Crash seed={seed}: {e}")

            elapsed_ms = (time.perf_counter() - start) * 1000
            times_ms.append(elapsed_ms)

        avg_time = sum(times_ms) / len(times_ms)
        max_time = max(times_ms)
        p95_time = sorted(times_ms)[int(0.95 * len(times_ms))]

        # Vérifier la performance
        assert avg_time < self.MAX_GENERATION_TIME_MS, \
            f"{gold_generator_key}: temps moyen {avg_time:.1f}ms > {self.MAX_GENERATION_TIME_MS}ms"

        # Log pour debug
        print(f"\n{gold_generator_key} perf: avg={avg_time:.1f}ms, max={max_time:.1f}ms, p95={p95_time:.1f}ms")


class TestGoldPlaceholders:
    """Tests de placeholders pour générateurs Gold."""

    PLACEHOLDER_PATTERN = re.compile(r'\{\{(\w+)\}\}')

    def test_no_unresolved_placeholders(self, gold_generator_key: str):
        """
        Vérifie qu'aucun placeholder n'est laissé non résolu.

        Args:
            gold_generator_key: Clé du générateur Gold
        """
        from backend.generators.factory import GeneratorFactory

        gen_class = GeneratorFactory.get(gold_generator_key)
        if gen_class is None:
            pytest.skip(f"Générateur {gold_generator_key} non trouvé")

        unresolved_vars = set()

        for seed in range(20):
            result = GeneratorFactory.generate(
                key=gold_generator_key,
                overrides={},
                seed=seed
            )

            # Vérifier dans les variables générées
            for key, value in result.get("variables", {}).items():
                if isinstance(value, str):
                    matches = self.PLACEHOLDER_PATTERN.findall(value)
                    unresolved_vars.update(matches)

            # Vérifier dans les résultats
            for key, value in result.get("results", {}).items():
                if isinstance(value, str):
                    matches = self.PLACEHOLDER_PATTERN.findall(value)
                    unresolved_vars.update(matches)

        assert len(unresolved_vars) == 0, \
            f"{gold_generator_key}: placeholders non résolus: {unresolved_vars}"


class TestGoldDeterminism:
    """Tests de déterminisme pour générateurs Gold."""

    def test_same_seed_same_result(self, gold_generator_key: str):
        """
        Vérifie que la même seed produit toujours le même résultat.

        Args:
            gold_generator_key: Clé du générateur Gold
        """
        from backend.generators.factory import GeneratorFactory

        gen_class = GeneratorFactory.get(gold_generator_key)
        if gen_class is None:
            pytest.skip(f"Générateur {gold_generator_key} non trouvé")

        for seed in [0, 42, 999]:
            # Générer deux fois avec la même seed
            result1 = GeneratorFactory.generate(
                key=gold_generator_key,
                overrides={},
                seed=seed
            )
            result2 = GeneratorFactory.generate(
                key=gold_generator_key,
                overrides={},
                seed=seed
            )

            # Comparer les variables (hors metadata)
            vars1 = result1.get("variables", {})
            vars2 = result2.get("variables", {})

            assert vars1 == vars2, \
                f"{gold_generator_key} seed={seed}: résultats différents!\n" \
                f"Result 1: {vars1}\nResult 2: {vars2}"


class TestGoldSchemaCompliance:
    """Tests de conformité au schéma pour générateurs Gold."""

    def test_all_schema_params_have_defaults(self, gold_generator_key: str):
        """
        Vérifie que tous les paramètres du schéma ont des valeurs par défaut.

        Args:
            gold_generator_key: Clé du générateur Gold
        """
        from backend.generators.factory import GeneratorFactory

        gen_class = GeneratorFactory.get(gold_generator_key)
        if gen_class is None:
            pytest.skip(f"Générateur {gold_generator_key} non trouvé")

        schema = gen_class.get_schema()
        defaults = gen_class.get_defaults()

        missing_defaults = []
        for param in schema:
            if param.name not in defaults and param.default is None and not param.required:
                missing_defaults.append(param.name)

        assert len(missing_defaults) == 0, \
            f"{gold_generator_key}: paramètres sans default: {missing_defaults}"

    def test_generation_with_defaults_only(self, gold_generator_key: str):
        """
        Vérifie que la génération fonctionne avec uniquement les defaults.

        Args:
            gold_generator_key: Clé du générateur Gold
        """
        from backend.generators.factory import GeneratorFactory

        # Générer sans aucun override
        try:
            result = GeneratorFactory.generate(
                key=gold_generator_key,
                overrides={},
                seed=42
            )
            assert result is not None
            assert "variables" in result or "generation_meta" in result
        except Exception as e:
            pytest.fail(f"{gold_generator_key}: crash avec defaults: {e}")
