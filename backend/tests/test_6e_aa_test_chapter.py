"""
Tests pour la génération d'exercices avec code_officiel="6e_AA_TEST"
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
async def test_6e_aa_test_generation_success():
    """Test que code_officiel="6e_AA_TEST" retourne 200 (ou au minimum ne plus être chapter_not_mapped)"""
    from backend.routes.exercises_routes import generate_exercise
    from backend.models.exercise_models import ExerciseGenerateRequest
    
    request = ExerciseGenerateRequest(
        code_officiel="6e_AA_TEST",
        difficulte="facile",
        offer="free",
        seed=42
    )
    
    # Mock les services nécessaires
    with patch('backend.routes.exercises_routes.get_curriculum_sync_service') as mock_sync, \
         patch('backend.routes.exercises_routes.get_exercise_persistence_service') as mock_exercise, \
         patch('backend.routes.exercises_routes.get_chapter_by_official_code') as mock_get_chapter:
        
        # Mock curriculum_chapter avec pipeline MIXED
        mock_chapter = MagicMock()
        mock_chapter.niveau = "6e"
        mock_chapter.libelle = "AA TEST"
        mock_chapter.code_officiel = "6e_AA_TEST"
        mock_chapter.pipeline = "MIXED"
        mock_get_chapter.return_value = mock_chapter
        
        # Mock services
        mock_sync_service = MagicMock()
        mock_sync_service.has_exercises_in_db = AsyncMock(return_value=True)
        mock_sync.return_value = mock_sync_service
        
        mock_exercise_service = MagicMock()
        mock_exercise_service.get_exercises = AsyncMock(return_value=[
            {
                "id": 1,
                "is_dynamic": True,
                "generator_key": "SIMPLIFICATION_FRACTIONS_V2",
                "difficulty": "facile",
                "offer": "free"
            }
        ])
        mock_exercise.return_value = mock_exercise_service
        
        # Mock format_dynamic_exercise
        with patch('backend.routes.exercises_routes.format_dynamic_exercise') as mock_format:
            mock_format.return_value = {
                "enonce_html": "<p>Simplifier 6/8</p>",
                "solution_html": "<p>3/4</p>",
                "metadata": {"generator_key": "SIMPLIFICATION_FRACTIONS_V2"}
            }
            
            # Ne doit pas lever d'exception CHAPTER_OR_TYPE_INVALID
            result = await generate_exercise(request)
            
            assert result is not None
            assert "enonce_html" in result


@pytest.mark.asyncio
async def test_6e_aa_test_unknown_test_chapter():
    """Test qu'un chapitre de test inconnu retourne 422 TEST_CHAPTER_UNKNOWN"""
    from backend.routes.exercises_routes import generate_exercise
    from backend.models.exercise_models import ExerciseGenerateRequest
    
    request = ExerciseGenerateRequest(
        code_officiel="6e_UNKNOWN_TEST",
        difficulte="facile",
        offer="free",
        seed=42
    )
    
    # Mock get_chapter_by_official_code pour retourner un chapitre avec pattern de test
    with patch('backend.routes.exercises_routes.get_chapter_by_official_code') as mock_get_chapter:
        mock_chapter = MagicMock()
        mock_chapter.niveau = "6e"
        mock_chapter.libelle = "UNKNOWN TEST"
        mock_chapter.code_officiel = "6e_UNKNOWN_TEST"
        mock_chapter.pipeline = None  # Pas de pipeline défini
        mock_get_chapter.return_value = mock_chapter
        
        with pytest.raises(HTTPException) as exc_info:
            await generate_exercise(request)
        
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error_code"] == "TEST_CHAPTER_UNKNOWN"
        assert "hint" in detail
        assert "context" in detail
        assert "6e_UNKNOWN_TEST" in detail["context"]["normalized_code"]


@pytest.mark.asyncio
async def test_6e_aa_test_integration(client):
    """Test d'intégration : requête réelle avec code_officiel=6e_AA_TEST"""
    # Nécessite un exercice dynamique en DB pour 6E_AA_TEST
    response = client.post(
        "/api/v1/exercises/generate",
        json={
            "code_officiel": "6e_AA_TEST",
            "difficulte": "facile",
            "offer": "free",
            "seed": 42
        }
    )
    
    # Ne doit pas retourner 422 CHAPTER_OR_TYPE_INVALID
    if response.status_code == 422:
        data = response.json()
        detail = data.get("detail", {})
        error_code = detail.get("error_code") if isinstance(detail, dict) else None
        assert error_code != "CHAPTER_OR_TYPE_INVALID", f"Erreur inattendue: {detail}"
    
    # Si pool vide, doit retourner 422 POOL_EMPTY (pas CHAPTER_OR_TYPE_INVALID)
    if response.status_code == 422:
        data = response.json()
        detail = data.get("detail", {})
        if isinstance(detail, dict):
            error_code = detail.get("error_code")
            assert error_code in ["POOL_EMPTY", "TEST_CHAPTER_UNKNOWN"], f"Erreur inattendue: {error_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

