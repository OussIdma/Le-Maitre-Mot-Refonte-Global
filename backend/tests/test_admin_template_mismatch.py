"""
Tests pour la validation ADMIN_TEMPLATE_MISMATCH (422)
"""

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch, MagicMock
from backend.services.exercise_persistence_service import ExercisePersistenceService, ExerciseCreateRequest, ExerciseUpdateRequest
from backend.services.template_renderer import get_template_variables


@pytest.fixture
def mock_db():
    """Mock MongoDB database"""
    db = MagicMock()
    db.admin_exercises = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    """Service de persistance avec DB mockée"""
    return ExercisePersistenceService(mock_db)


@pytest.mark.asyncio
async def test_admin_template_mismatch_create(service):
    """Test que la création d'un exercice avec mismatch retourne 422 ADMIN_TEMPLATE_MISMATCH"""
    
    # Mock collection
    service.collection = MagicMock()
    service.collection.find_one = AsyncMock(return_value=None)  # Pas d'exercice existant
    service.collection.insert_one = AsyncMock()
    service.collection.find = AsyncMock(return_value=MagicMock(sort=MagicMock(return_value=MagicMock(to_list=AsyncMock(return_value=[])))))
    
    # Mock GeneratorFactory pour retourner un générateur qui ne fournit pas toutes les variables
    with patch('backend.services.exercise_persistence_service.GeneratorFactory.get') as mock_get_gen:
        mock_gen_class = MagicMock()
        mock_generator = MagicMock()
        mock_generator.generate.return_value = {
            "variables": {
                "fraction": "6/8",
                "fraction_reduite": "3/4"
                # check_equivalence_str manquant intentionnellement
            }
        }
        mock_gen_class.return_value = mock_generator
        mock_get_gen.return_value = mock_gen_class
        
        request = ExerciseCreateRequest(
            is_dynamic=True,
            generator_key="SIMPLIFICATION_FRACTIONS_V2",
            enonce_template_html="<p>{{fraction}}</p>",
            solution_template_html="<p>{{check_equivalence_str}}</p>",  # Placeholder qui n'est pas fourni
            difficulty="moyen",
            offer="free"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await service.create_exercise("6E_AA_TEST", request)
        
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error_code"] == "ADMIN_TEMPLATE_MISMATCH"
        assert "hint" in detail
        assert "context" in detail
        assert detail["context"]["generator_key"] == "SIMPLIFICATION_FRACTIONS_V2"
        assert "mismatches" in detail["context"]
        assert "check_equivalence_str" in detail["context"]["missing_summary"]


@pytest.mark.asyncio
async def test_admin_template_mismatch_update(service):
    """Test que la mise à jour d'un exercice avec mismatch retourne 422 ADMIN_TEMPLATE_MISMATCH"""
    
    # Mock exercice existant
    existing_exercise = {
        "chapter_code": "6E_AA_TEST",
        "id": 1,
        "is_dynamic": True,
        "generator_key": "SIMPLIFICATION_FRACTIONS_V2",
        "enonce_template_html": "<p>{{fraction}}</p>",
        "solution_template_html": "<p>{{fraction_reduite}}</p>",
        "variables": {}
    }
    
    service.collection = MagicMock()
    service.collection.find_one = AsyncMock(return_value=existing_exercise)
    service.collection.update_one = AsyncMock()
    
    # Mock GeneratorFactory pour retourner un générateur qui ne fournit pas toutes les variables
    with patch('backend.services.exercise_persistence_service.GeneratorFactory.get') as mock_get_gen:
        mock_gen_class = MagicMock()
        mock_generator = MagicMock()
        mock_generator.generate.return_value = {
            "variables": {
                "fraction": "6/8",
                "fraction_reduite": "3/4"
                # check_equivalence_str manquant intentionnellement
            }
        }
        mock_gen_class.return_value = mock_generator
        mock_get_gen.return_value = mock_gen_class
        
        request = ExerciseUpdateRequest(
            solution_template_html="<p>{{check_equivalence_str}}</p>"  # Placeholder qui n'est pas fourni
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await service.update_exercise("6E_AA_TEST", 1, request)
        
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error_code"] == "ADMIN_TEMPLATE_MISMATCH"
        assert "check_equivalence_str" in detail["context"]["missing_summary"]


@pytest.mark.asyncio
async def test_admin_template_match_success(service):
    """Test que si tous les placeholders sont fournis, pas d'erreur"""
    
    # Mock collection
    service.collection = MagicMock()
    service.collection.find_one = AsyncMock(return_value=None)
    service.collection.insert_one = AsyncMock()
    service.collection.find = AsyncMock(return_value=MagicMock(sort=MagicMock(return_value=MagicMock(to_list=AsyncMock(return_value=[])))))
    
    # Mock GeneratorFactory pour retourner un générateur qui fournit toutes les variables
    with patch('backend.services.exercise_persistence_service.GeneratorFactory.get') as mock_get_gen:
        mock_gen_class = MagicMock()
        mock_generator = MagicMock()
        mock_generator.generate.return_value = {
            "variables": {
                "fraction": "6/8",
                "fraction_reduite": "3/4",
                "check_equivalence_str": "6 × 4 = 24 et 8 × 3 = 24. Les produits sont égaux."
            }
        }
        mock_gen_class.return_value = mock_generator
        mock_get_gen.return_value = mock_gen_class
        
        request = ExerciseCreateRequest(
            is_dynamic=True,
            generator_key="SIMPLIFICATION_FRACTIONS_V2",
            enonce_template_html="<p>{{fraction}}</p>",
            solution_template_html="<p>{{check_equivalence_str}}</p>",
            difficulty="moyen",
            offer="free"
        )
        
        # Ne doit pas lever d'exception
        result = await service.create_exercise("6E_AA_TEST", request)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

