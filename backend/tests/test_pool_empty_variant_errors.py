"""
Tests pour les erreurs 422 : pool vide et variant_id invalide
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException


@pytest.fixture
def client():
    """Client de test FastAPI"""
    from backend.server import app
    return TestClient(app)


@pytest.mark.asyncio
async def test_pool_empty_mixed_pipeline():
    """Test que le pool vide retourne 422 avec error_code POOL_EMPTY"""
    from backend.routes.exercises_routes import generate_exercise
    from backend.models.exercise_models import ExerciseGenerateRequest
    
    request = ExerciseGenerateRequest(
        code_officiel="6E_AA_TEST",
        difficulte="facile",
        offer="free",
        seed=42
    )
    
    # Mock : aucun exercice dynamique disponible
    with patch('backend.routes.exercises_routes.exercise_service') as mock_service:
        mock_service.get_exercises = AsyncMock(return_value=[])  # Pool vide
        
        with pytest.raises(HTTPException) as exc_info:
            await generate_exercise(request)
        
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error_code"] == "POOL_EMPTY"
        assert "hint" in detail
        assert "context" in detail
        assert detail["context"]["chapter"] == "6E_AA_TEST"
        assert detail["context"]["difficulty"] == "facile"
        assert detail["context"]["offer"] == "free"
        assert detail["context"]["pipeline"] == "MIXED"


@pytest.mark.asyncio
async def test_variant_id_not_found():
    """Test que variant_id invalide retourne 422 avec error_code VARIANT_ID_NOT_FOUND"""
    from backend.services.tests_dyn_handler import format_dynamic_exercise
    
    # Mock exercice avec template_variants
    exercise_template = {
        "id": "test_exercise_1",
        "generator_key": "SIMPLIFICATION_FRACTIONS_V2",
        "is_dynamic": True,
        "template_variants": [
            {"id": "A", "variant_id": "A", "label": "Direct"},
            {"id": "B", "variant_id": "B", "label": "Guidé"}
        ]
    }
    
    # Mock variables avec variant_id invalide
    variables = {"variant_id": "Z"}  # Variant Z n'existe pas
    
    # Mock GeneratorFactory.generate pour retourner des variables
    with patch('backend.services.tests_dyn_handler.GeneratorFactory.generate') as mock_gen:
        mock_gen.return_value = {
            "variables": variables,
            "results": {}
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await format_dynamic_exercise(
                exercise_template=exercise_template,
                timestamp=1000,
                seed=42,
                exercise_params=variables
            )
        
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error_code"] == "VARIANT_ID_NOT_FOUND"
        assert "hint" in detail
        assert "context" in detail
        assert detail["context"]["variant_id_requested"] == "Z"
        assert "variants_present" in detail["context"]
        assert "A" in detail["context"]["variants_present"]
        assert "B" in detail["context"]["variants_present"]


@pytest.mark.asyncio
async def test_pool_empty_integration(client):
    """Test d'intégration : requête réelle avec pool vide"""
    # Nécessite un chapitre sans exercices dynamiques
    response = client.post(
        "/api/v1/exercises/generate",
        json={
            "code_officiel": "6E_AA_TEST",
            "difficulte": "facile",
            "offer": "free",
            "seed": 42
        }
    )
    
    # Si pool vide, doit retourner 422
    if response.status_code == 422:
        data = response.json()
        assert "detail" in data
        detail = data["detail"]
        assert detail.get("error_code") == "POOL_EMPTY"
        assert "hint" in detail
        assert "context" in detail


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

