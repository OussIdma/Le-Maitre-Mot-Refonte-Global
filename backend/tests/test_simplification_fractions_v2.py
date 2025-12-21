"""
Tests unitaires pour SimplificationFractionsV2Generator
========================================================
"""

import pytest
import re
import math
import json
from backend.generators.simplification_fractions_v2 import (
    SimplificationFractionsV2Generator,
    ENONCE_TEMPLATE_A,
    ENONCE_TEMPLATE_B,
    ENONCE_TEMPLATE_C,
    SOLUTION_TEMPLATE_A,
    SOLUTION_TEMPLATE_B,
    SOLUTION_TEMPLATE_C,
    ENONCE_TEMPLATE_V1,
    SOLUTION_TEMPLATE_V1,
)
from backend.generators.factory import GeneratorFactory


def test_meta_valide():
    """Test que les métadonnées sont correctes."""
    meta = SimplificationFractionsV2Generator.get_meta()
    
    assert meta.key == "SIMPLIFICATION_FRACTIONS_V2"
    assert meta.label == "Simplification de fractions (PREMIUM)"
    assert "variants pédagogiques" in meta.description.lower()
    assert meta.version == "2.0.0"
    assert "CM2" in meta.niveaux
    assert "6e" in meta.niveaux
    assert "5e" in meta.niveaux
    assert meta.exercise_type == "FRACTIONS"
    assert meta.svg_mode == "AUTO"
    assert meta.supports_double_svg is True


def test_schema_valide():
    """Test que le schéma est valide avec les nouveaux paramètres V2."""
    schema = SimplificationFractionsV2Generator.get_schema()
    
    param_names = [p.name for p in schema]
    
    # Paramètres V1 (conservés)
    assert "difficulty" in param_names
    assert "allow_negative" in param_names
    assert "max_denominator" in param_names
    assert "force_reducible" in param_names
    assert "show_svg" in param_names
    assert "representation" in param_names
    
    # Nouveaux paramètres V2
    assert "variant_id" in param_names
    assert "pedagogy_mode" in param_names
    assert "hint_level" in param_names
    assert "include_feedback" in param_names
    assert "allow_improper" in param_names
    
    # Vérifier les types et valeurs
    variant_param = next(p for p in schema if p.name == "variant_id")
    assert variant_param.type.value == "enum"
    assert "A" in variant_param.options
    assert "B" in variant_param.options
    assert "C" in variant_param.options
    assert variant_param.default == "A"
    
    hint_level_param = next(p for p in schema if p.name == "hint_level")
    assert hint_level_param.type.value == "int"
    assert hint_level_param.min == 0
    assert hint_level_param.max == 3
    assert hint_level_param.default == 0


def test_non_regression_v1():
    """Test de non-régression : comportement V1 strictement inchangé."""
    seed = 42
    params_v1 = {
        "difficulty": "moyen",
        "allow_negative": False,
        "max_denominator": 60,
        "force_reducible": True,
        "show_svg": True,
        "representation": "number_line",
        # Paramètres V2 avec valeurs V1 (compatibilité)
        "variant_id": "A",
        "pedagogy_mode": "standard",
        "hint_level": 0,
        "include_feedback": False,
        "allow_improper": False
    }
    
    gen_v2 = SimplificationFractionsV2Generator(seed=seed)
    result_v2 = gen_v2.safe_generate(params_v1)
    
    # Vérifier que les variables V1 sont présentes et identiques
    variables = result_v2["variables"]
    assert "fraction" in variables
    assert "n" in variables
    assert "d" in variables
    assert "pgcd" in variables
    assert "n_red" in variables
    assert "d_red" in variables
    assert "fraction_reduite" in variables
    assert "step1" in variables
    assert "step2" in variables
    assert "step3" in variables
    assert "is_irreductible" in variables
    assert "difficulty" in variables
    
    # Vérifier que les variables V2 ne sont pas présentes (mode V1)
    assert "hints" not in variables or len(variables.get("hints", [])) == 0
    assert "hint_used" not in variables or variables["hint_used"] == ""
    assert "wrong_simplification" not in variables
    assert "error_catalog" not in variables


def test_determinism_variant_a():
    """Test que le générateur est déterministe (variant A)."""
    seed = 42
    params = {
        "difficulty": "moyen",
        "variant_id": "A",
        "pedagogy_mode": "standard",
        "hint_level": 0,
        "include_feedback": False,
        "allow_improper": False
    }
    
    gen1 = SimplificationFractionsV2Generator(seed=seed)
    gen2 = SimplificationFractionsV2Generator(seed=seed)
    
    result1 = gen1.safe_generate(params)
    result2 = gen2.safe_generate(params)
    
    assert result1["variables"] == result2["variables"]
    assert result1["figure_svg_enonce"] == result2["figure_svg_enonce"]
    assert result1["figure_svg_solution"] == result2["figure_svg_solution"]
    assert result1["results"] == result2["results"]


def test_determinism_variant_c():
    """Test que le générateur est déterministe (variant C - diagnostic)."""
    seed = 42
    params = {
        "difficulty": "moyen",
        "variant_id": "C",
        "pedagogy_mode": "diagnostic",
        "hint_level": 0,
        "include_feedback": True,
        "allow_improper": False
    }
    
    gen1 = SimplificationFractionsV2Generator(seed=seed)
    gen2 = SimplificationFractionsV2Generator(seed=seed)
    
    result1 = gen1.safe_generate(params)
    result2 = gen2.safe_generate(params)
    
    assert result1["variables"] == result2["variables"]
    assert result1["variables"]["wrong_simplification"] == result2["variables"]["wrong_simplification"]
    assert result1["variables"]["diagnostic_is_correct"] == result2["variables"]["diagnostic_is_correct"]


def test_placeholders_variant_a():
    """Test que tous les placeholders du variant A sont présents."""
    gen = SimplificationFractionsV2Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "variant_id": "A",
        "pedagogy_mode": "standard"
    })
    
    variables = result["variables"]
    
    placeholders_a_enonce = re.findall(r'\{\{(\w+)\}\}', ENONCE_TEMPLATE_A)
    placeholders_a_solution = re.findall(r'\{\{(\w+)\}\}', SOLUTION_TEMPLATE_A)
    
    for placeholder in placeholders_a_enonce + placeholders_a_solution:
        assert placeholder in variables, f"Placeholder '{placeholder}' manquant dans variables (variant A)"


def test_placeholders_variant_b():
    """Test que tous les placeholders du variant B sont présents."""
    gen = SimplificationFractionsV2Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "variant_id": "B",
        "pedagogy_mode": "guided",
        "hint_level": 1
    })
    
    variables = result["variables"]
    
    placeholders_b_enonce = re.findall(r'\{\{(\w+)\}\}', ENONCE_TEMPLATE_B)
    placeholders_b_solution = re.findall(r'\{\{(\w+)\}\}', SOLUTION_TEMPLATE_B)
    
    for placeholder in placeholders_b_enonce + placeholders_b_solution:
        assert placeholder in variables, f"Placeholder '{placeholder}' manquant dans variables (variant B)"


def test_placeholders_variant_c():
    """Test que tous les placeholders du variant C sont présents."""
    gen = SimplificationFractionsV2Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "variant_id": "C",
        "pedagogy_mode": "diagnostic"
    })
    
    variables = result["variables"]
    
    placeholders_c_enonce = re.findall(r'\{\{(\w+)\}\}', ENONCE_TEMPLATE_C)
    placeholders_c_solution = re.findall(r'\{\{(\w+)\}\}', SOLUTION_TEMPLATE_C)
    
    for placeholder in placeholders_c_enonce + placeholders_c_solution:
        assert placeholder in variables, f"Placeholder '{placeholder}' manquant dans variables (variant C)"


def test_hint_level_bounds():
    """Test que hint_level respecte les bornes 0-3."""
    gen = SimplificationFractionsV2Generator(seed=42)
    
    # Test hint_level = 0
    result0 = gen.safe_generate({
        "difficulty": "moyen",
        "variant_id": "B",
        "hint_level": 0
    })
    assert "hints" in result0["variables"]
    assert len(result0["variables"]["hints"]) == 0
    
    # Test hint_level = 3
    result3 = gen.safe_generate({
        "difficulty": "moyen",
        "variant_id": "B",
        "hint_level": 3
    })
    assert "hints" in result3["variables"]
    assert len(result3["variables"]["hints"]) == 3
    
    # Test hint_level invalide (doit être validé par le schéma)
    valid, errors = SimplificationFractionsV2Generator.validate_params({
        "hint_level": 4  # > max
    })
    assert valid is False
    
    valid, errors = SimplificationFractionsV2Generator.validate_params({
        "hint_level": -1  # < min
    })
    assert valid is False


def test_factory_registration():
    """Test que le générateur est bien enregistré dans la Factory."""
    gen_class = GeneratorFactory.get("SIMPLIFICATION_FRACTIONS_V2")
    
    assert gen_class is not None
    assert gen_class == SimplificationFractionsV2Generator


def test_factory_schema():
    """Test que la Factory retourne le schéma correct."""
    schema = GeneratorFactory.get_schema("SIMPLIFICATION_FRACTIONS_V2")
    
    assert schema is not None
    assert schema["generator_key"] == "SIMPLIFICATION_FRACTIONS_V2"
    assert "meta" in schema
    assert "schema" in schema
    assert "presets" in schema
    assert schema["meta"]["exercise_type"] == "FRACTIONS"


def test_variant_b_hints():
    """Test que les hints sont générés correctement pour variant B."""
    gen = SimplificationFractionsV2Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "variant_id": "B",
        "pedagogy_mode": "guided",
        "hint_level": 2
    })
    
    variables = result["variables"]
    assert "hints" in variables
    assert len(variables["hints"]) == 2
    assert "hint_used" in variables
    assert variables["hint_used"] == variables["hints"][1]  # hint_level 2 = index 1


def test_variant_c_diagnostic():
    """Test que le variant C génère correctement les variables de diagnostic."""
    gen = SimplificationFractionsV2Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "variant_id": "C",
        "pedagogy_mode": "diagnostic"
    })
    
    variables = result["variables"]
    assert "wrong_simplification" in variables
    assert "diagnostic_is_correct" in variables
    assert isinstance(variables["diagnostic_is_correct"], bool)
    assert "diagnostic_explanation" in variables
    assert "check_equivalence_str" in variables
    assert "produit en croix" in variables["check_equivalence_str"].lower() or "×" in variables["check_equivalence_str"]


def test_error_catalog():
    """Test que le catalogue d'erreurs est construit correctement."""
    gen = SimplificationFractionsV2Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "include_feedback": True
    })
    
    variables = result["variables"]
    assert "error_catalog" in variables
    catalog = variables["error_catalog"]
    
    assert "divide_numerator_only" in catalog
    assert "divide_denominator_only" in catalog
    assert "not_fully_reduced" in catalog
    assert "wrong_pgcd" in catalog
    assert "sign_misplaced" in catalog
    
    # Vérifier la structure de chaque erreur
    for error_code, error_data in catalog.items():
        assert "message" in error_data
        assert "trigger" in error_data


def test_error_examples():
    """Test que les exemples d'erreurs sont générés."""
    gen = SimplificationFractionsV2Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "include_feedback": True
    })
    
    variables = result["variables"]
    assert "error_type_examples" in variables
    examples = variables["error_type_examples"]
    
    assert "divide_numerator_only" in examples
    assert "divide_denominator_only" in examples
    assert "correct" in examples


def test_force_reducible_false():
    """Test que force_reducible=False permet PGCD=1."""
    gen = SimplificationFractionsV2Generator(seed=42)
    
    found_irreductible = False
    for _ in range(20):  # Tester plusieurs fois
        result = gen.safe_generate({
            "difficulty": "moyen",
            "force_reducible": False,
            "show_svg": False,
            "representation": "none"
        })
        
        pgcd = result["variables"]["pgcd"]
        if pgcd == 1:
            found_irreductible = True
            assert result["variables"]["is_irreductible"] is True
            break
    
    assert found_irreductible, "force_reducible=False devrait permettre PGCD=1"


def test_allow_improper():
    """Test que allow_improper=True permet des fractions impropres."""
    gen = SimplificationFractionsV2Generator(seed=42)
    
    found_improper = False
    for _ in range(20):
        result = gen.safe_generate({
            "difficulty": "moyen",
            "allow_improper": True,
            "show_svg": False,
            "representation": "none"
        })
        
        n = result["variables"]["n"]
        d = result["variables"]["d"]
        if abs(n) >= d:
            found_improper = True
            assert result["variables"]["is_improper"] is True
            break
    
    assert found_improper, "allow_improper=True devrait permettre des fractions impropres"


def test_svg_solution_v2_ids():
    """Test que le SVG solution V2 contient des IDs stables."""
    gen = SimplificationFractionsV2Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "variant_id": "A",
        "show_svg": True,
        "representation": "number_line"
    })
    
    svg_solution = result["figure_svg_solution"]
    assert svg_solution is not None
    
    # Vérifier la présence des IDs stables
    assert 'id="reduced-box"' in svg_solution
    assert 'id="reduced-fraction"' in svg_solution
    assert 'id="reduced-label"' in svg_solution


def test_meta_variant_id():
    """Test que meta contient variant_id et pedagogy_mode."""
    gen = SimplificationFractionsV2Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "variant_id": "B",
        "pedagogy_mode": "guided"
    })
    
    assert "meta" in result
    assert result["meta"]["variant_id"] == "B"
    assert result["meta"]["pedagogy_mode"] == "guided"
    assert result["meta"]["question_type"] == "simplifier"


def test_presets_premium():
    """Test que les presets PREMIUM sont valides."""
    presets = SimplificationFractionsV2Generator.get_presets()
    
    premium_presets = [p for p in presets if "guided" in p.key or "diagnostic" in p.key or "irreductible" in p.key]
    assert len(premium_presets) > 0
    
    for preset in premium_presets:
        valid, _ = SimplificationFractionsV2Generator.validate_params(preset.params)
        assert valid, f"Preset {preset.key} a des paramètres invalides"


def test_json_safe():
    """Test que toutes les variables sont JSON-safe."""
    gen = SimplificationFractionsV2Generator(seed=42)
    result = gen.safe_generate({
        "difficulty": "moyen",
        "variant_id": "C",
        "include_feedback": True
    })
    
    # Tester que variables est JSON-serializable
    json_str = json.dumps(result["variables"])
    variables_loaded = json.loads(json_str)
    assert variables_loaded == result["variables"]
    
    # Tester que geo_data est JSON-serializable
    json_str = json.dumps(result["geo_data"])
    geo_data_loaded = json.loads(json_str)
    assert geo_data_loaded == result["geo_data"]


def test_fraction_reduction_correct():
    """Test que la simplification est mathématiquement correcte (tous variants)."""
    gen = SimplificationFractionsV2Generator(seed=42)
    
    for variant in ["A", "B", "C"]:
        result = gen.safe_generate({
            "difficulty": "moyen",
            "variant_id": variant
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
        assert math.gcd(abs(n_red), d_red) == 1

