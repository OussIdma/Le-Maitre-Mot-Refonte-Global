"""
Tests pour l'erreur PLACEHOLDER_UNRESOLVED (422)
"""

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.tests_dyn_handler import format_dynamic_exercise


@pytest.mark.asyncio
async def test_placeholder_unresolved_422():
    """Test que les placeholders non résolus retournent 422 avec error_code PLACEHOLDER_UNRESOLVED"""
    
    # Mock exercice avec template contenant des placeholders non résolus
    exercise_template = {
        "id": "test_exercise_1",
        "chapter_code": "6E_TESTS_DYN",
        "generator_key": "THALES_V1",
        "is_dynamic": True,
        "enonce_template_html": "<p>Le côté mesure {{cote_initial}} cm et {{variable_inexistante}} est manquant.</p>",
        "solution_template_html": "<p>Solution avec {{autre_variable_manquante}}.</p>",
        "variables": {}
    }
    
    # Mock GeneratorFactory.generate pour retourner des variables incomplètes
    with patch('backend.services.tests_dyn_handler.GeneratorFactory.generate') as mock_gen:
        mock_gen.return_value = {
            "variables": {
                "cote_initial": 5,  # Cette variable est fournie
                # variable_inexistante et autre_variable_manquante sont absentes
            },
            "results": {}
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await format_dynamic_exercise(
                exercise_template=exercise_template,
                timestamp=1000,
                seed=42
            )
        
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error_code"] == "PLACEHOLDER_UNRESOLVED"
        assert "hint" in detail
        assert "context" in detail
        assert detail["context"]["chapter_code"] == "6E_TESTS_DYN"
        assert "missing" in detail["context"]
        assert len(detail["context"]["missing"]) > 0
        assert "variable_inexistante" in detail["context"]["missing"] or "autre_variable_manquante" in detail["context"]["missing"]
        assert detail["context"]["template_id"] == "test_exercise_1"
        assert detail["context"]["generator_key"] == "THALES_V1"


@pytest.mark.asyncio
async def test_placeholder_unresolved_multiple_missing():
    """Test avec plusieurs placeholders manquants"""
    
    exercise_template = {
        "id": "test_exercise_2",
        "chapter_code": "6E_TESTS_DYN",
        "generator_key": "SYMETRIE_AXIALE_V2",
        "is_dynamic": True,
        "enonce_template_html": "<p>{{var1}} et {{var2}} et {{var3}} sont manquants.</p>",
        "solution_template_html": "<p>Solution.</p>",
        "variables": {}
    }
    
    with patch('backend.services.tests_dyn_handler.GeneratorFactory.generate') as mock_gen:
        mock_gen.return_value = {
            "variables": {},  # Aucune variable fournie
            "results": {}
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await format_dynamic_exercise(
                exercise_template=exercise_template,
                timestamp=1000,
                seed=42
            )
        
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error_code"] == "PLACEHOLDER_UNRESOLVED"
        assert len(detail["context"]["missing"]) >= 3
        assert "var1" in detail["context"]["missing"]
        assert "var2" in detail["context"]["missing"]
        assert "var3" in detail["context"]["missing"]


@pytest.mark.asyncio
async def test_placeholder_all_resolved_success():
    """Test que si tous les placeholders sont résolus, pas d'erreur"""
    
    exercise_template = {
        "id": "test_exercise_3",
        "chapter_code": "6E_TESTS_DYN",
        "generator_key": "THALES_V1",
        "is_dynamic": True,
        "enonce_template_html": "<p>Le côté mesure {{cote_initial}} cm.</p>",
        "solution_template_html": "<p>Solution : {{cote_final}} cm.</p>",
        "variables": {}
    }
    
    with patch('backend.services.tests_dyn_handler.GeneratorFactory.generate') as mock_gen, \
         patch('backend.services.tests_dyn_handler.generate_svg_for_exercise') as mock_svg:
        
        mock_gen.return_value = {
            "variables": {
                "cote_initial": 5,
                "cote_final": 10
            },
            "results": {}
        }
        mock_svg.return_value = {
            "figure_svg_enonce": "<svg></svg>",
            "figure_svg_solution": "<svg></svg>"
        }
        
        # Ne doit pas lever d'exception
        result = await format_dynamic_exercise(
            exercise_template=exercise_template,
            timestamp=1000,
            seed=42
        )
        
        assert result is not None
        assert "enonce_html" in result
        assert "{{cote_initial}}" not in result["enonce_html"]  # Placeholder résolu
        assert "5" in result["enonce_html"]  # Valeur substituée


@pytest.mark.asyncio
async def test_simplification_fractions_v2_all_variants():
    """Test que SIMPLIFICATION_FRACTIONS_V2 fournit toujours check_equivalence_str, diagnostic_explanation, wrong_simplification"""
    from backend.services.tests_dyn_handler import format_dynamic_exercise
    
    # Test pour chaque variant (A, B, C)
    for variant_id in ["A", "B", "C"]:
        exercise_template = {
            "id": f"test_simplification_{variant_id}",
            "chapter_code": "6E_AA_TEST",
            "generator_key": "SIMPLIFICATION_FRACTIONS_V2",
            "is_dynamic": True,
            "enonce_template_html": "<p>{{fraction}}</p>",
            "solution_template_html": "<p>{{fraction_reduite}}</p>",
            "template_variants": [
                {
                    "id": variant_id,
                    "variant_id": variant_id,
                    "label": "Test",
                    "enonce_template_html": "<p>{{fraction}}</p>",
                    "solution_template_html": "<p>{{fraction_reduite}}</p>"
                }
            ],
            "variables": {
                "variant_id": variant_id,
                "difficulty": "moyen"
            }
        }
        
        # Mock GeneratorFactory.generate pour retourner les variables
        with patch('backend.services.tests_dyn_handler.GeneratorFactory.generate') as mock_gen, \
             patch('backend.services.tests_dyn_handler.generate_svg_for_exercise') as mock_svg:
            
            # Simuler une génération réussie avec toutes les variables
            mock_gen.return_value = {
                "variables": {
                    "fraction": "6/8",
                    "fraction_reduite": "3/4",
                    "check_equivalence_str": "6 × 4 = 24 et 8 × 3 = 24. Les produits sont égaux.",
                    "diagnostic_explanation": "La simplification est correcte.",
                    "wrong_simplification": "3/4"
                },
                "results": {}
            }
            mock_svg.return_value = {
                "figure_svg_enonce": "<svg></svg>",
                "figure_svg_solution": "<svg></svg>"
            }
            
            # Ne doit pas lever d'exception PLACEHOLDER_UNRESOLVED
            result = await format_dynamic_exercise(
                exercise_template=exercise_template,
                timestamp=1000,
                seed=42,
                exercise_params={"variant_id": variant_id, "difficulty": "moyen"}
            )
            
            assert result is not None
            assert "enonce_html" in result
            # Vérifier que les placeholders sont résolus
            assert "{{fraction}}" not in result["enonce_html"]


@pytest.mark.asyncio
async def test_simplification_fractions_v2_missing_diagnostic_vars():
    """Test que si check_equivalence_str est manquant, on obtient PLACEHOLDER_UNRESOLVED"""
    from backend.services.tests_dyn_handler import format_dynamic_exercise
    from fastapi import HTTPException
    
    exercise_template = {
        "id": "test_simplification_missing",
        "chapter_code": "6E_AA_TEST",
        "generator_key": "SIMPLIFICATION_FRACTIONS_V2",
        "is_dynamic": True,
        "enonce_template_html": "<p>{{fraction}}</p>",
        "solution_template_html": "<p>{{check_equivalence_str}}</p>",  # Placeholder qui doit être fourni
        "variables": {
            "variant_id": "A",
            "difficulty": "moyen"
        }
    }
    
    # Mock GeneratorFactory.generate pour retourner des variables INCOMPLÈTES
    with patch('backend.services.tests_dyn_handler.GeneratorFactory.generate') as mock_gen:
        mock_gen.return_value = {
            "variables": {
                "fraction": "6/8",
                "fraction_reduite": "3/4",
                # check_equivalence_str manquant intentionnellement
            },
            "results": {}
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await format_dynamic_exercise(
                exercise_template=exercise_template,
                timestamp=1000,
                seed=42
            )
        
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error_code"] == "PLACEHOLDER_UNRESOLVED"
        assert "check_equivalence_str" in detail["context"]["missing"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

