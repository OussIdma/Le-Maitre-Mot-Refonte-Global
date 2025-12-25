"""
Tests pour vérifier le comportement des générateurs désactivés (P4.2)
"""

import pytest
from backend.generators.factory import GeneratorFactory


def test_list_all_excludes_disabled():
    """Vérifie que list_all() n'inclut pas les générateurs désactivés par défaut."""
    all_generators = GeneratorFactory.list_all()
    disabled_generators = GeneratorFactory.DISABLED_GENERATORS
    
    # Vérifier qu'aucun générateur désactivé n'est dans la liste
    generator_keys = [g["key"] for g in all_generators]
    for disabled_key in disabled_generators:
        assert disabled_key not in generator_keys, (
            f"Le générateur désactivé '{disabled_key}' ne devrait pas apparaître dans list_all()"
        )


def test_list_all_includes_disabled_when_requested():
    """Vérifie que list_all(include_disabled=True) inclut les générateurs désactivés."""
    all_generators = GeneratorFactory.list_all(include_disabled=True)
    disabled_generators = GeneratorFactory.DISABLED_GENERATORS
    
    if disabled_generators:
        generator_keys = [g["key"] for g in all_generators]
        for disabled_key in disabled_generators:
            assert disabled_key in generator_keys, (
                f"Le générateur désactivé '{disabled_key}' devrait apparaître dans list_all(include_disabled=True)"
            )
            
            # Vérifier que le flag disabled est True
            gen_info = next((g for g in all_generators if g["key"] == disabled_key), None)
            assert gen_info is not None, f"Générateur {disabled_key} non trouvé"
            assert gen_info.get("disabled") is True, f"Le flag 'disabled' devrait être True pour {disabled_key}"


def test_get_returns_none_for_disabled():
    """Vérifie que get() retourne None pour un générateur désactivé."""
    disabled_generators = GeneratorFactory.DISABLED_GENERATORS
    
    if not disabled_generators:
        pytest.skip("Aucun générateur désactivé pour tester")
    
    # Tester avec le premier générateur désactivé
    disabled_key = disabled_generators[0]
    result = GeneratorFactory.get(disabled_key)
    
    assert result is None, (
        f"GeneratorFactory.get('{disabled_key}') devrait retourner None pour un générateur désactivé"
    )


def test_generate_raises_error_for_disabled():
    """Vérifie que generate() lève une ValueError pour un générateur désactivé."""
    disabled_generators = GeneratorFactory.DISABLED_GENERATORS
    
    if not disabled_generators:
        pytest.skip("Aucun générateur désactivé pour tester")
    
    # Tester avec le premier générateur désactivé
    disabled_key = disabled_generators[0]
    
    with pytest.raises(ValueError) as exc_info:
        GeneratorFactory.generate(
            key=disabled_key,
            exercise_params={"difficulty": "moyen"},
            seed=42
        )
    
    assert "désactivé" in str(exc_info.value).lower() or "disabled" in str(exc_info.value).lower(), (
        f"L'erreur devrait mentionner que le générateur est désactivé"
    )
    assert disabled_key in str(exc_info.value), (
        f"L'erreur devrait mentionner le nom du générateur désactivé: {disabled_key}"
    )


def test_get_schema_returns_none_for_disabled():
    """Vérifie que get_schema() retourne None pour un générateur désactivé."""
    disabled_generators = GeneratorFactory.DISABLED_GENERATORS
    
    if not disabled_generators:
        pytest.skip("Aucun générateur désactivé pour tester")
    
    # Tester avec le premier générateur désactivé
    disabled_key = disabled_generators[0]
    result = GeneratorFactory.get_schema(disabled_key)
    
    assert result is None, (
        f"GeneratorFactory.get_schema('{disabled_key}') devrait retourner None pour un générateur désactivé"
    )


def test_disabled_generators_list_is_sorted():
    """Vérifie que DISABLED_GENERATORS est trié alphabétiquement."""
    disabled_generators = GeneratorFactory.DISABLED_GENERATORS
    sorted_generators = sorted(disabled_generators)
    
    assert disabled_generators == sorted_generators, (
        f"DISABLED_GENERATORS devrait être trié alphabétiquement. "
        f"Attendu: {sorted_generators}, Actuel: {disabled_generators}"
    )




