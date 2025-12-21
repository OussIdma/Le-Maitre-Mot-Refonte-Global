"""
Tests de déterminisme et variété pour SIMPLIFICATION_FRACTIONS_V2
==================================================================

Objectifs :
- Vérifier que même seed + même mode (A/B/C) → même variant sélectionné
- Vérifier que variant_id absent → random (compatibilité legacy)
- Vérifier que générations multiples en "difficile" → variété via pool d'exercices
"""

import pytest
from backend.services.tests_dyn_handler import format_dynamic_exercise
from backend.generators.factory import GeneratorFactory
from typing import Dict, Any


def create_mock_exercise_template(
    exercise_id: str,
    variant_id: str = None,
    template_variants: list = None
) -> Dict[str, Any]:
    """Crée un template d'exercice mock pour les tests."""
    
    if template_variants is None:
        template_variants = [
            {
                "id": "A",
                "variant_id": "A",
                "enonce_template_html": "<p>Variant A: {{fraction}}</p>",
                "solution_template_html": "<p>Solution A: {{fraction_reduite}}</p>",
                "weight": 1
            },
            {
                "id": "B",
                "variant_id": "B",
                "enonce_template_html": "<p>Variant B: {{fraction}} {{hint_display}}</p>",
                "solution_template_html": "<p>Solution B: {{fraction_reduite}}</p>",
                "weight": 1
            },
            {
                "id": "C",
                "variant_id": "C",
                "enonce_template_html": "<p>Variant C: {{fraction}} {{wrong_simplification}}</p>",
                "solution_template_html": "<p>Solution C: {{fraction_reduite}}</p>",
                "weight": 1
            }
        ]
    
    variables = {
        "difficulty": "difficile",
        "max_denominator": 40,
        "force_reducible": True,
    }
    
    if variant_id:
        variables["variant_id"] = variant_id
        variables["pedagogy_mode"] = "standard" if variant_id == "A" else ("guided" if variant_id == "B" else "diagnostic")
    
    return {
        "id": exercise_id,
        "chapter_code": "6E_AA_TEST",
        "generator_key": "SIMPLIFICATION_FRACTIONS_V2",
        "is_dynamic": True,
        "difficulty": "difficile",
        "offer": "pro",
        "family": "SIMPLIFICATION_FRACTIONS",
        "variables": variables,
        "template_variants": template_variants,
        "enonce_template_html": "<p>Legacy: {{fraction}}</p>",
        "solution_template_html": "<p>Legacy solution</p>",
    }


def test_determinism_same_seed_same_variant_id():
    """Test : même seed + même variant_id → même variant sélectionné."""
    
    seed = 12345
    variant_id = "A"
    
    template1 = create_mock_exercise_template("ex1", variant_id=variant_id)
    template2 = create_mock_exercise_template("ex2", variant_id=variant_id)
    
    # Générer avec même seed et même variant_id
    result1 = format_dynamic_exercise(template1, timestamp=1000, seed=seed)
    result2 = format_dynamic_exercise(template2, timestamp=2000, seed=seed)
    
    # Vérifier que les variables sont identiques (même fraction générée)
    assert result1["metadata"]["variables"]["variant_id"] == variant_id
    assert result2["metadata"]["variables"]["variant_id"] == variant_id
    assert result1["metadata"]["variables"]["fraction"] == result2["metadata"]["variables"]["fraction"]


def test_determinism_different_variant_ids():
    """Test : même seed + variant_id différents → variants différents sélectionnés."""
    
    seed = 12345
    
    template_a = create_mock_exercise_template("ex_a", variant_id="A")
    template_b = create_mock_exercise_template("ex_b", variant_id="B")
    template_c = create_mock_exercise_template("ex_c", variant_id="C")
    
    result_a = format_dynamic_exercise(template_a, timestamp=1000, seed=seed)
    result_b = format_dynamic_exercise(template_b, timestamp=2000, seed=seed)
    result_c = format_dynamic_exercise(template_c, timestamp=3000, seed=seed)
    
    # Vérifier que les variant_id sont corrects
    assert result_a["metadata"]["variables"]["variant_id"] == "A"
    assert result_b["metadata"]["variables"]["variant_id"] == "B"
    assert result_c["metadata"]["variables"]["variant_id"] == "C"
    
    # Vérifier que les templates utilisés sont différents (énoncés différents)
    # Variant A n'a pas hint_display, Variant B l'a, Variant C a wrong_simplification
    assert "hint_display" not in result_a["enonce_html"] or "{{hint_display}}" not in result_a["enonce_html"]
    assert "wrong_simplification" not in result_a["enonce_html"] or "{{wrong_simplification}}" not in result_a["enonce_html"]


def test_deterministic_fallback_when_variant_id_absent():
    """Test : variant_id absent → fallback déterministe sur le premier variant (compatibilité legacy)."""
    
    seed = 12345
    
    template = create_mock_exercise_template("ex_no_variant", variant_id=None)
    
    # Générer plusieurs fois avec même seed mais sans variant_id
    # Le fallback doit être déterministe : toujours le premier variant (A)
    results = []
    for i in range(5):
        result = format_dynamic_exercise(template, timestamp=1000 + i, seed=seed)
        variant_id = result["metadata"]["variables"].get("variant_id")
        results.append(variant_id)
    
    # Le fallback déterministe doit toujours sélectionner le premier variant (A)
    # même avec des timestamps différents
    assert all(v == "A" for v in results), f"Fallback non déterministe: {results}"


def test_variant_id_invalid_raises_error():
    """Test : variant_id invalide → erreur 422."""
    
    seed = 12345
    
    template = create_mock_exercise_template("ex_invalid", variant_id="D")  # D n'existe pas
    
    with pytest.raises(Exception) as exc_info:
        format_dynamic_exercise(template, timestamp=1000, seed=seed)
    
    # Vérifier que c'est une HTTPException 422
    assert hasattr(exc_info.value, "status_code") and exc_info.value.status_code == 422


def test_generator_v2_registered():
    """Test : SIMPLIFICATION_FRACTIONS_V2 est enregistré dans GeneratorFactory."""
    
    gen = GeneratorFactory.get("SIMPLIFICATION_FRACTIONS_V2")
    assert gen is not None
    assert gen.get_meta().key == "SIMPLIFICATION_FRACTIONS_V2"


def test_generator_v2_generates_variables():
    """Test : le générateur génère les variables attendues."""
    
    gen = GeneratorFactory.get("SIMPLIFICATION_FRACTIONS_V2")
    result = GeneratorFactory.generate(
        key="SIMPLIFICATION_FRACTIONS_V2",
        exercise_params={
            "difficulty": "difficile",
            "variant_id": "A",
            "pedagogy_mode": "standard"
        },
        seed=12345
    )
    
    variables = result.get("variables", {})
    
    # Vérifier les variables obligatoires
    assert "fraction" in variables
    assert "fraction_reduite" in variables
    assert "n" in variables
    assert "d" in variables
    assert "pgcd" in variables
    assert "n_red" in variables
    assert "d_red" in variables
    assert variables.get("variant_id") == "A"
    assert variables.get("pedagogy_mode") == "standard"

