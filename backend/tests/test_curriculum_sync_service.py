"""
Tests unitaires pour le service de synchronisation automatique Curriculum ⇄ Exercises.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.services.curriculum_sync_service import (
    CurriculumSyncService,
    GENERATOR_TO_EXERCISE_TYPE
)


@pytest.fixture
def mock_db():
    """Mock de la base de données MongoDB"""
    db = MagicMock()
    db.exercises = MagicMock()
    return db


@pytest.fixture
def sync_service(mock_db):
    """Instance du service de synchronisation"""
    return CurriculumSyncService(mock_db)


@pytest.mark.asyncio
async def test_extract_exercise_types_from_chapter_dynamic(sync_service):
    """Test extraction exercise_types depuis exercices dynamiques"""
    # Mock des exercices dynamiques
    mock_exercises = [
        {"is_dynamic": True, "generator_key": "SYMETRIE_AXIALE_V2"},
        {"is_dynamic": True, "generator_key": "THALES_V1"},
    ]
    
    sync_service.exercises_collection.find = AsyncMock(return_value=AsyncMock(
        to_list=AsyncMock(return_value=mock_exercises)
    ))
    
    exercise_types = await sync_service.extract_exercise_types_from_chapter("6e_G07_DYN")
    
    assert "SYMETRIE_AXIALE" in exercise_types
    assert "THALES" in exercise_types
    assert len(exercise_types) == 2


@pytest.mark.asyncio
async def test_extract_exercise_types_from_chapter_static(sync_service):
    """Test extraction exercise_types depuis exercices statiques"""
    # Mock des exercices statiques
    mock_exercises = [
        {"is_dynamic": False, "exercise_type": "PERIMETRE"},
        {"is_dynamic": False, "exercise_type": "AIRE"},
    ]
    
    sync_service.exercises_collection.find = AsyncMock(return_value=AsyncMock(
        to_list=AsyncMock(return_value=mock_exercises)
    ))
    
    exercise_types = await sync_service.extract_exercise_types_from_chapter("6e_GM07")
    
    assert "PERIMETRE" in exercise_types
    assert "AIRE" in exercise_types
    assert len(exercise_types) == 2


@pytest.mark.asyncio
async def test_extract_exercise_types_from_chapter_mixed(sync_service):
    """Test extraction exercise_types depuis exercices mixtes (statique + dynamique)"""
    # Mock des exercices mixtes
    mock_exercises = [
        {"is_dynamic": True, "generator_key": "SYMETRIE_AXIALE_V2"},
        {"is_dynamic": False, "exercise_type": "PERIMETRE"},
    ]
    
    sync_service.exercises_collection.find = AsyncMock(return_value=AsyncMock(
        to_list=AsyncMock(return_value=mock_exercises)
    ))
    
    exercise_types = await sync_service.extract_exercise_types_from_chapter("6e_G07_DYN")
    
    assert "SYMETRIE_AXIALE" in exercise_types
    assert "PERIMETRE" in exercise_types
    assert len(exercise_types) == 2


@pytest.mark.asyncio
async def test_sync_chapter_to_curriculum_create(sync_service):
    """Test création automatique d'un chapitre dans le curriculum"""
    # Mock : aucun exercice existant
    sync_service.exercises_collection.find = AsyncMock(return_value=AsyncMock(
        to_list=AsyncMock(return_value=[])
    ))
    
    # Mock : chapitre n'existe pas dans le curriculum
    sync_service.curriculum_service.get_chapter_by_code = AsyncMock(return_value=None)
    
    # Mock : création du chapitre
    created_chapter = {
        "code_officiel": "6E_G07_DYN",
        "libelle": "G07 DYN",
        "exercise_types": []
    }
    sync_service.curriculum_service.create_chapter = AsyncMock(return_value=created_chapter)
    
    result = await sync_service.sync_chapter_to_curriculum("6e_G07_DYN")
    
    assert result['created'] is True
    assert result['updated'] is False
    assert result['exercise_types'] == []
    sync_service.curriculum_service.create_chapter.assert_called_once()


@pytest.mark.asyncio
async def test_sync_chapter_to_curriculum_update_additive(sync_service):
    """Test mise à jour additive (ne supprime pas les exercise_types existants)"""
    # Mock : exercices avec nouveaux generator_key
    mock_exercises = [
        {"is_dynamic": True, "generator_key": "SYMETRIE_AXIALE_V2"},
    ]
    
    sync_service.exercises_collection.find = AsyncMock(return_value=AsyncMock(
        to_list=AsyncMock(return_value=mock_exercises)
    ))
    
    # Mock : chapitre existe avec exercise_types existants
    existing_chapter = {
        "code_officiel": "6E_G07_DYN",
        "exercise_types": ["THALES"]  # Existant
    }
    sync_service.curriculum_service.get_chapter_by_code = AsyncMock(return_value=existing_chapter)
    
    # Mock : mise à jour du chapitre
    updated_chapter = {
        "code_officiel": "6E_G07_DYN",
        "exercise_types": ["SYMETRIE_AXIALE", "THALES"]  # Fusion
    }
    sync_service.curriculum_service.update_chapter = AsyncMock(return_value=updated_chapter)
    
    result = await sync_service.sync_chapter_to_curriculum("6e_G07_DYN")
    
    assert result['created'] is False
    assert result['updated'] is True
    assert "SYMETRIE_AXIALE" in result['exercise_types']
    assert "THALES" in result['exercise_types']  # Conservé
    sync_service.curriculum_service.update_chapter.assert_called_once()


@pytest.mark.asyncio
async def test_sync_chapter_to_curriculum_no_change(sync_service):
    """Test qu'aucune mise à jour n'est faite si les exercise_types sont identiques"""
    # Mock : exercices
    mock_exercises = [
        {"is_dynamic": True, "generator_key": "SYMETRIE_AXIALE_V2"},
    ]
    
    sync_service.exercises_collection.find = AsyncMock(return_value=AsyncMock(
        to_list=AsyncMock(return_value=mock_exercises)
    ))
    
    # Mock : chapitre existe avec les mêmes exercise_types
    existing_chapter = {
        "code_officiel": "6E_G07_DYN",
        "exercise_types": ["SYMETRIE_AXIALE"]  # Déjà présent
    }
    sync_service.curriculum_service.get_chapter_by_code = AsyncMock(return_value=existing_chapter)
    
    result = await sync_service.sync_chapter_to_curriculum("6e_G07_DYN")
    
    assert result['created'] is False
    assert result['updated'] is False
    assert result['exercise_types'] == ["SYMETRIE_AXIALE"]
    # update_chapter ne doit pas être appelé
    sync_service.curriculum_service.update_chapter.assert_not_called()




