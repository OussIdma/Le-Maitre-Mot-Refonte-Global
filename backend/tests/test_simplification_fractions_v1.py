"""
Tests unitaires pour SimplificationFractionsV1Generator
========================================================
"""

import pytest
import re
from backend.generators.simplification_fractions_v1 import (
    SimplificationFractionsV1Generator,
    ENONCE_TEMPLATE,
    SOLUTION_TEMPLATE,
)
from backend.generators.factory import GeneratorFactory


def test_meta_valide():
    """Test que les métadonnées sont correctes."""
    meta = SimplificationFractionsV1Generator.get_meta()
    
    assert meta.key == "SIMPLIFICATION_FRACTIONS_V1"
    assert meta.label == "Simplification de fractions"
    assert meta.description == "Simplifier des fractions à l'aide du PGCD"
    assert meta.version == "1.0.0"
    assert "CM2" in meta.niveaux
    assert "6e" in meta.niveaux
    assert "5e" in meta.niveaux
    assert meta.exercise_type == "FRACTIONS"
    assert meta.svg_mode == "AUTO"
    assert meta.supports_double_svg is True
    assert "PGCD" in meta.pedagogical_tips


def test_schema_valide():
    """Test que le schéma est valide."""
    schema = SimplificationFractionsV1Generator.get_schema()
    
    assert len(schema) > 0
    
    # Vérifier que tous les paramètres ont un nom et un type
    param_names = [p.name for p in schema]
    assert "difficulty" in param_names
    assert "allow_negative" in param_names
    assert "max_denominator" in param_names
    assert "force_reducible" in param_names
    assert "show_svg" in param_names
    assert "representation" in param_names
    
    # Vérifier les types
    difficulty_param = next(p for p in schema if p.name == "difficulty")
    assert difficulty_param.type.value == "enum"
    assert "facile" in difficulty_param.options
    assert "moyen" in difficulty_param.options
    assert "difficile" in difficulty_param.options


def test_validate_params_ok():
    """Test la validation des paramètres."""
    params = {
        "difficulty": "moyen",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": True,
        "representation": "number_line"
    }
    
    valid, result = SimplificationFractionsV1Generator.validate_params(params)
    
    assert valid is True
    assert "difficulty" in result
    assert result["difficulty"] == "moyen"
    assert result["max_denominator"] == 60


def test_validate_params_invalid():
    """Test la validation avec paramètres invalides."""
    params = {
        "difficulty": "tres_facile",  # Invalide
        "max_denominator": 1000,  # Trop grand
    }
    
    valid, errors = SimplificationFractionsV1Generator.validate_params(params)
    
    assert valid is False
    assert isinstance(errors, list)
    assert len(errors) > 0


def test_determinism():
    """Test que le générateur est déterministe."""
    seed = 42
    params = {
        "difficulty": "moyen",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": True,
        "representation": "number_line"
    }
    
    gen1 = SimplificationFractionsV1Generator(seed=seed)
    gen2 = SimplificationFractionsV1Generator(seed=seed)
    
    result1 = gen1.safe_generate(params)
    result2 = gen2.safe_generate(params)
    
    # Vérifier que les variables sont identiques
    assert result1["variables"] == result2["variables"]
    
    # Vérifier que les SVG sont identiques
    assert result1["figure_svg_enonce"] == result2["figure_svg_enonce"]
    assert result1["figure_svg_solution"] == result2["figure_svg_solution"]
    
    # Vérifier que les résultats sont identiques
    assert result1["results"] == result2["results"]


def test_factory_registration():
    """Test que le générateur est bien enregistré dans la Factory."""
    gen_class = GeneratorFactory.get("SIMPLIFICATION_FRACTIONS_V1")
    
    assert gen_class is not None
    assert gen_class == SimplificationFractionsV1Generator


def test_factory_schema():
    """Test que la Factory retourne le schéma correct."""
    schema = GeneratorFactory.get_schema("SIMPLIFICATION_FRACTIONS_V1")
    
    assert schema is not None
    assert schema["generator_key"] == "SIMPLIFICATION_FRACTIONS_V1"
    assert "meta" in schema
    assert "schema" in schema
    assert "presets" in schema
    assert schema["meta"]["exercise_type"] == "FRACTIONS"


def test_placeholders_enonce():
    """Test que tous les placeholders de l'énoncé sont présents dans les variables."""
    gen = SimplificationFractionsV1Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": True,
        "representation": "number_line"
    })
    
    variables = result["variables"]
    
    # Extraire les placeholders du template énoncé
    placeholders = re.findall(r'\{\{(\w+)\}\}', ENONCE_TEMPLATE)
    
    # Vérifier que tous les placeholders sont présents
    for placeholder in placeholders:
        assert placeholder in variables, f"Placeholder '{placeholder}' manquant dans variables"


def test_placeholders_solution():
    """Test que tous les placeholders de la solution sont présents dans les variables."""
    gen = SimplificationFractionsV1Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": True,
        "representation": "number_line"
    })
    
    variables = result["variables"]
    
    # Extraire les placeholders du template solution
    placeholders = re.findall(r'\{\{(\w+)\}\}', SOLUTION_TEMPLATE)
    
    # Vérifier que tous les placeholders sont présents
    for placeholder in placeholders:
        assert placeholder in variables, f"Placeholder '{placeholder}' manquant dans variables"


def test_variables_completes():
    """Test que toutes les variables obligatoires sont présentes."""
    gen = SimplificationFractionsV1Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": True,
        "representation": "number_line"
    })
    
    variables = result["variables"]
    
    # Variables obligatoires
    required_vars = [
        "fraction",
        "n",
        "d",
        "pgcd",
        "n_red",
        "d_red",
        "fraction_reduite",
        "step1",
        "step2",
        "step3",
        "is_irreductible",
        "difficulty"
    ]
    
    for var_name in required_vars:
        assert var_name in variables, f"Variable '{var_name}' manquante"


def test_meta_question_type():
    """Test que meta contient question_type='simplifier'."""
    gen = SimplificationFractionsV1Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": True,
        "representation": "number_line"
    })
    
    assert "meta" in result
    assert result["meta"]["question_type"] == "simplifier"
    assert result["meta"]["exercise_type"] == "FRACTIONS"


def test_results_structure():
    """Test que results contient les champs attendus."""
    gen = SimplificationFractionsV1Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": True,
        "representation": "number_line"
    })
    
    assert "results" in result
    results = result["results"]
    assert "n_red" in results
    assert "d_red" in results
    assert "pgcd" in results
    
    # Vérifier que les résultats sont cohérents
    variables = result["variables"]
    assert results["n_red"] == variables["n_red"]
    assert results["d_red"] == variables["d_red"]
    assert results["pgcd"] == variables["pgcd"]


def test_geo_data_structure():
    """Test que geo_data est JSON-safe et contient les champs attendus."""
    gen = SimplificationFractionsV1Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": True,
        "representation": "number_line"
    })
    
    assert "geo_data" in result
    geo_data = result["geo_data"]
    
    # Vérifier les champs
    assert "n" in geo_data
    assert "d" in geo_data
    assert "n_red" in geo_data
    assert "d_red" in geo_data
    assert "pgcd" in geo_data
    assert "difficulty" in geo_data
    assert "representation" in geo_data
    
    # Vérifier que c'est JSON-safe (types simples)
    import json
    json_str = json.dumps(geo_data)
    geo_data_loaded = json.loads(json_str)
    assert geo_data_loaded == geo_data


def test_svg_generation():
    """Test que les SVG sont générés correctement."""
    gen = SimplificationFractionsV1Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": True,
        "representation": "number_line"
    })
    
    assert "figure_svg_enonce" in result
    assert "figure_svg_solution" in result
    assert result["figure_svg_enonce"] is not None
    assert result["figure_svg_solution"] is not None
    
    # Vérifier que ce sont des SVG valides
    assert result["figure_svg_enonce"].startswith("<svg")
    assert result["figure_svg_solution"].startswith("<svg")
    assert "viewBox" in result["figure_svg_enonce"]
    assert "viewBox" in result["figure_svg_solution"]


def test_svg_disabled():
    """Test que les SVG ne sont pas générés si show_svg=False."""
    gen = SimplificationFractionsV1Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": False,
        "representation": "number_line"
    })
    
    assert result["figure_svg_enonce"] is None
    assert result["figure_svg_solution"] is None


def test_presets_valides():
    """Test que tous les presets sont valides."""
    presets = SimplificationFractionsV1Generator.get_presets()
    
    assert len(presets) > 0
    
    for preset in presets:
        # Valider que les paramètres du preset sont valides
        valid, _ = SimplificationFractionsV1Generator.validate_params(preset.params)
        assert valid, f"Preset {preset.key} a des paramètres invalides"


def test_fraction_reduction_correct():
    """Test que la simplification est mathématiquement correcte."""
    gen = SimplificationFractionsV1Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": True,
        "representation": "number_line"
    })
    
    variables = result["variables"]
    n = variables["n"]
    d = variables["d"]
    n_red = variables["n_red"]
    d_red = variables["d_red"]
    pgcd = variables["pgcd"]
    
    # Vérifier que la simplification est correcte
    assert n_red * pgcd == n or n_red * pgcd == -n
    assert d_red * pgcd == d
    
    # Vérifier que la fraction réduite est irréductible
    import math
    assert math.gcd(abs(n_red), d_red) == 1


def test_force_reducible():
    """Test que force_reducible=True génère toujours des fractions réductibles."""
    gen = SimplificationFractionsV1Generator(seed=42)
    
    for _ in range(10):  # Tester plusieurs fois
        result = gen.safe_generate({
            "difficulty": "moyen",
            "allow_negative": False,
            "max_denominator": 60,
            "force_reducible": True,
            "show_svg": False,
            "representation": "none"
        })
        
        pgcd = result["variables"]["pgcd"]
        assert pgcd > 1, "force_reducible=True mais PGCD = 1"


def test_difficulty_ranges():
    """Test que les plages de génération respectent la difficulté."""
    gen_facile = SimplificationFractionsV1Generator(seed=42)
    gen_moyen = SimplificationFractionsV1Generator(seed=42)
    gen_difficile = SimplificationFractionsV1Generator(seed=42)
    
    result_facile = gen_facile.safe_generate({
        "difficulty": "facile",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": False,
        "representation": "none"
    })
    
    result_moyen = gen_moyen.safe_generate({
        "difficulty": "moyen",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": False,
        "representation": "none"
    })
    
    result_difficile = gen_difficile.safe_generate({
        "difficulty": "difficile",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": False,
        "representation": "none"
    })
    
    d_facile = result_facile["variables"]["d"]
    d_moyen = result_moyen["variables"]["d"]
    d_difficile = result_difficile["variables"]["d"]
    
    # Facile : dénominateur ≤ 12
    assert d_facile <= 12
    
    # Moyen : dénominateur ≤ 20
    assert d_moyen <= 20
    
    # Difficile : dénominateur ≤ 40
    assert d_difficile <= 40


def test_max_denominator_small_difficile():
    """
    Test P0: Cas limite difficile + max_denominator très petit.
    
    Vérifie que le filtrage de pgcd_options fonctionne correctement
    et évite le crash randrange.
    """
    gen = SimplificationFractionsV1Generator(seed=42)
    
    # Cas critique : difficile avec max_denominator=6
    # pgcd_options original = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15]
    # max_denom_base = min(40, 6) = 6
    # Seuls [2, 3] peuvent fonctionner (6 // 2 = 3 >= 2, 6 // 3 = 2 >= 2)
    # Les autres (4, 5, 6, 7, 8, 9, 10, 12, 15) doivent être filtrés
    
    result = gen.safe_generate({
        "difficulty": "difficile",
        "allow_negative": False,
        "max_denominator": 6,  # Très petit
        "force_reducible": True,
        "show_svg": False,
        "representation": "none"
    })
    
    # Vérifier que la génération a réussi (pas de crash)
    assert "variables" in result
    d = result["variables"]["d"]
    pgcd = result["variables"]["pgcd"]
    
    # Vérifier les contraintes
    assert d <= 6, f"d={d} doit être <= 6"
    # Vérifier que le PGCD est valide selon le filtrage (max_denom_base // pgcd >= 2)
    max_denom_base = min(40, 6)  # = 6
    assert max_denom_base // pgcd >= 2, f"pgcd={pgcd} invalide pour max_denom_base={max_denom_base}"
    # Pour max_denominator=6, seuls [2, 3] sont valides
    assert pgcd in [2, 3], f"pgcd={pgcd} devrait être dans [2, 3] pour max_denominator=6"


def test_max_denominator_small_moyen():
    """
    Test P0: Cas limite moyen + max_denominator très petit.
    """
    gen = SimplificationFractionsV1Generator(seed=42)
    
    # Cas : moyen avec max_denominator=8
    # pgcd_options = [2, 3, 4, 5, 6, 8, 9, 10]
    # max_denom_base = 20, mais limité par max_denominator=8
    # Seuls [2, 3, 4] peuvent fonctionner (8 // 2 = 4 >= 2, 8 // 3 = 2 >= 2, 8 // 4 = 2 >= 2)
    
    result = gen.safe_generate({
        "difficulty": "moyen",
        "allow_negative": False,
        "max_denominator": 8,  # Très petit
        "force_reducible": True,
        "show_svg": False,
        "representation": "none"
    })
    
    # Vérifier que la génération a réussi
    assert "variables" in result
    assert result["variables"]["d"] <= 8
    assert result["variables"]["pgcd"] in [2, 3, 4]  # PGCD possibles après filtrage


def test_pgcd_filtering_edge_cases():
    """
    Test P0: Cas limites de filtrage PGCD.
    
    Vérifie que le filtrage fonctionne pour différentes combinaisons
    difficulty + max_denominator.
    """
    gen = SimplificationFractionsV1Generator(seed=42)
    
    test_cases = [
        {"difficulty": "difficile", "max_denominator": 10, "expected_pgcd_max": 5},  # 10 // 5 = 2
        {"difficulty": "difficile", "max_denominator": 12, "expected_pgcd_max": 6},  # 12 // 6 = 2
        {"difficulty": "difficile", "max_denominator": 15, "expected_pgcd_max": 7},  # 15 // 7 = 2
        {"difficulty": "moyen", "max_denominator": 6, "expected_pgcd_max": 3},      # 6 // 3 = 2
        {"difficulty": "facile", "max_denominator": 4, "expected_pgcd_max": 2},     # 4 // 2 = 2
    ]
    
    for case in test_cases:
        result = gen.safe_generate({
            "difficulty": case["difficulty"],
            "allow_negative": False,
            "max_denominator": case["max_denominator"],
            "force_reducible": True,
            "show_svg": False,
            "representation": "none"
        })
        
        # Vérifier que le PGCD est valide
        assert result["variables"]["pgcd"] <= case["expected_pgcd_max"]
        assert result["variables"]["d"] <= case["max_denominator"]


def test_force_reducible_false_small_denominator():
    """
    Test P0: force_reducible=False avec max_denominator très petit.
    
    Vérifie que même avec force_reducible=False, le générateur
    fonctionne correctement avec des dénominateurs petits.
    """
    gen = SimplificationFractionsV1Generator(seed=42)
    
    result = gen.safe_generate({
        "difficulty": "facile",
        "allow_negative": False,
        "max_denominator": 5,  # Très petit
        "force_reducible": False,  # Peut générer des fractions irréductibles
        "show_svg": False,
        "representation": "none"
    })
    
    # Vérifier que la génération a réussi
    assert "variables" in result
    assert result["variables"]["d"] <= 5
    # Le PGCD peut être 1 (irréductible) ou > 1 (réductible)
    assert result["variables"]["pgcd"] >= 1

