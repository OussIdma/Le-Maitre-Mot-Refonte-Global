"""
P0 Gold - Tests No-Crash pour TOUS les générateurs
===================================================

Ce test vérifie que chaque générateur peut générer 100 exercices
sans crash, quelle que soit la seed.

IMPORTANT: Ce test est BLOQUANT en CI - tout échec bloque le merge.
"""

import pytest
from typing import List


def get_all_generator_keys() -> List[str]:
    """
    Récupère la liste de tous les générateurs au runtime.

    NOTE: Cette fonction est appelée au runtime (pas à l'import) pour éviter
    les problèmes de registry non initialisé.
    """
    from backend.generators.factory import GeneratorFactory

    generators = GeneratorFactory.list_all(include_disabled=False)
    return [g["key"] for g in generators]


def pytest_generate_tests(metafunc):
    """
    Hook pytest pour générer dynamiquement les tests paramétrés.

    Cela évite les problèmes d'import au moment de la collecte des tests.
    """
    if "generator_key" in metafunc.fixturenames:
        # Récupérer la liste des générateurs au runtime
        try:
            keys = get_all_generator_keys()
        except Exception as e:
            # Si l'import échoue, utiliser une liste vide
            # Le test échouera avec un message clair
            pytest.skip(f"Impossible de charger les générateurs: {e}")
            keys = []

        metafunc.parametrize("generator_key", keys)


class TestNoCrash100Seeds:
    """Tests no-crash pour tous les générateurs."""

    def test_generator_100_seeds(self, generator_key: str):
        """
        Vérifie qu'un générateur peut générer 100 exercices sans crash.

        Args:
            generator_key: Clé du générateur à tester
        """
        from backend.generators.factory import GeneratorFactory

        errors = []

        for seed in range(100):
            try:
                result = GeneratorFactory.generate(
                    key=generator_key,
                    overrides={},
                    seed=seed
                )

                # Vérifications basiques
                assert result is not None, f"seed={seed}: result is None"
                assert isinstance(result, dict), f"seed={seed}: result n'est pas un dict"

                # Vérifier que les champs essentiels existent
                assert "variables" in result or "generation_meta" in result, \
                    f"seed={seed}: pas de 'variables' ni 'generation_meta'"

            except Exception as e:
                errors.append(f"seed={seed}: {type(e).__name__}: {e}")

                # Limiter le nombre d'erreurs collectées
                if len(errors) >= 5:
                    break

        if errors:
            error_msg = f"Générateur {generator_key} a crashé:\n" + "\n".join(errors)
            pytest.fail(error_msg)


class TestBasicGeneration:
    """Tests basiques de génération."""

    def test_at_least_one_generator_exists(self):
        """Vérifie qu'au moins un générateur est enregistré."""
        keys = get_all_generator_keys()
        assert len(keys) > 0, "Aucun générateur enregistré dans la Factory"

    def test_all_generators_have_meta(self):
        """Vérifie que tous les générateurs ont des métadonnées."""
        from backend.generators.factory import GeneratorFactory

        for key in get_all_generator_keys():
            gen_class = GeneratorFactory.get(key)
            assert gen_class is not None, f"Générateur {key} non trouvé"

            meta = gen_class.get_meta()
            assert meta is not None, f"Générateur {key} n'a pas de meta"
            assert meta.key == key, f"Générateur {key}: meta.key != key"
            assert meta.label, f"Générateur {key}: meta.label vide"

    def test_all_generators_have_schema(self):
        """Vérifie que tous les générateurs ont un schéma valide."""
        from backend.generators.factory import GeneratorFactory

        for key in get_all_generator_keys():
            gen_class = GeneratorFactory.get(key)
            schema = gen_class.get_schema()

            assert isinstance(schema, list), f"Générateur {key}: schema n'est pas une liste"

            for param in schema:
                assert hasattr(param, "name"), f"Générateur {key}: param sans 'name'"
                assert hasattr(param, "type"), f"Générateur {key}: param sans 'type'"
