"""
P0 Gold - Tests de validation des schémas de générateurs
=========================================================

Ces tests vérifient que les schémas des générateurs sont cohérents
et correctement définis.
"""

import pytest
from typing import List


def get_all_generator_keys() -> List[str]:
    """Récupère la liste de tous les générateurs."""
    from backend.generators.factory import GeneratorFactory

    generators = GeneratorFactory.list_all(include_disabled=False)
    return [g["key"] for g in generators]


class TestSchemaValidation:
    """Tests de validation des schémas."""

    def test_all_schemas_are_valid(self):
        """Vérifie que tous les schémas sont valides."""
        from backend.generators.factory import GeneratorFactory

        for key in get_all_generator_keys():
            gen_class = GeneratorFactory.get(key)
            assert gen_class is not None, f"Générateur {key} non trouvé"

            schema = gen_class.get_schema()
            assert isinstance(schema, list), f"{key}: schema n'est pas une liste"

            for i, param in enumerate(schema):
                # Vérifier les attributs obligatoires
                assert hasattr(param, "name"), f"{key} param[{i}]: pas de 'name'"
                assert hasattr(param, "type"), f"{key} param[{i}]: pas de 'type'"
                assert hasattr(param, "description"), f"{key} param[{i}]: pas de 'description'"

                # Vérifier que le nom est valide
                assert param.name, f"{key} param[{i}]: name vide"
                assert param.name.isidentifier() or "_" in param.name, \
                    f"{key} param[{i}]: name '{param.name}' invalide"

    def test_defaults_match_schema(self):
        """Vérifie que les defaults correspondent au schéma."""
        from backend.generators.factory import GeneratorFactory

        for key in get_all_generator_keys():
            gen_class = GeneratorFactory.get(key)
            schema = gen_class.get_schema()
            defaults = gen_class.get_defaults()

            schema_names = {p.name for p in schema}
            default_names = set(defaults.keys())

            # Les defaults doivent être un sous-ensemble du schéma
            extra_defaults = default_names - schema_names
            assert len(extra_defaults) == 0, \
                f"{key}: defaults hors schéma: {extra_defaults}"

    def test_presets_use_valid_params(self):
        """Vérifie que les presets n'utilisent que des paramètres valides."""
        from backend.generators.factory import GeneratorFactory

        for key in get_all_generator_keys():
            gen_class = GeneratorFactory.get(key)
            schema = gen_class.get_schema()
            presets = gen_class.get_presets()

            schema_names = {p.name for p in schema}

            for preset in presets:
                preset_params = set(preset.params.keys())
                invalid_params = preset_params - schema_names

                assert len(invalid_params) == 0, \
                    f"{key} preset '{preset.key}': params invalides: {invalid_params}"

    def test_enum_params_have_options(self):
        """Vérifie que les paramètres ENUM ont des options définies."""
        from backend.generators.factory import GeneratorFactory
        from backend.generators.base_generator import ParamType

        for key in get_all_generator_keys():
            gen_class = GeneratorFactory.get(key)
            schema = gen_class.get_schema()

            for param in schema:
                if param.type == ParamType.ENUM:
                    assert param.options is not None and len(param.options) > 0, \
                        f"{key} param '{param.name}': ENUM sans options"

    def test_int_params_have_bounds(self):
        """Vérifie que les paramètres INT ont des bornes définies (recommandé)."""
        from backend.generators.factory import GeneratorFactory
        from backend.generators.base_generator import ParamType

        warnings = []

        for key in get_all_generator_keys():
            gen_class = GeneratorFactory.get(key)
            schema = gen_class.get_schema()

            for param in schema:
                if param.type == ParamType.INT:
                    if param.min is None or param.max is None:
                        warnings.append(f"{key}.{param.name}: INT sans bornes min/max")

        # Afficher les warnings (non bloquant)
        if warnings:
            print("\n[WARNINGS] Paramètres INT sans bornes:")
            for w in warnings[:10]:  # Limiter l'affichage
                print(f"  - {w}")


class TestStrictValidation:
    """Tests de validation stricte (P0 Gold)."""

    def test_unknown_param_raises_error(self):
        """Vérifie que les paramètres inconnus lèvent une erreur."""
        from backend.generators.factory import GeneratorFactory

        keys = get_all_generator_keys()
        if not keys:
            pytest.skip("Aucun générateur disponible")

        # Prendre le premier générateur disponible
        key = keys[0]

        # Essayer de générer avec un paramètre inconnu
        with pytest.raises(ValueError) as excinfo:
            GeneratorFactory.generate(
                key=key,
                overrides={"unknown_param_xyz": 123},
                seed=42
            )

        assert "non déclarés" in str(excinfo.value).lower() or \
               "unknown" in str(excinfo.value).lower() or \
               "invalide" in str(excinfo.value).lower(), \
               f"Message d'erreur inattendu: {excinfo.value}"

    def test_seed_is_global_param(self):
        """Vérifie que 'seed' est accepté comme paramètre global."""
        from backend.generators.factory import GeneratorFactory

        keys = get_all_generator_keys()
        if not keys:
            pytest.skip("Aucun générateur disponible")

        key = keys[0]

        # seed doit être accepté sans erreur
        try:
            result = GeneratorFactory.generate(
                key=key,
                overrides={},
                seed=42
            )
            assert result is not None
        except ValueError as e:
            if "seed" in str(e).lower():
                pytest.fail(f"'seed' devrait être un paramètre global accepté: {e}")
            raise
