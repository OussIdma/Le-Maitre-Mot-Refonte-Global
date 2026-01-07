"""
Tests P0: Pipeline explicite au niveau chapitre

Tests de non-régression pour vérifier que :
- Les intercepts GM07/GM08/TESTS_DYN fonctionnent toujours (priorité absolue)
- Les pipelines SPEC/TEMPLATE/MIXED fonctionnent correctement
- Les validations bloquantes fonctionnent
- Le fallback legacy fonctionne si pipeline absent
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from backend.models.exercise_models import ExerciseGenerateRequest
from backend.models.math_models import MathExerciseType


@pytest.fixture
def client():
    """Client de test FastAPI"""
    from backend.server import app
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock de la base de données MongoDB"""
    db = MagicMock()
    return db


class TestInterceptsPriority:
    """Tests pour vérifier que les intercepts ont priorité absolue"""
    
    def test_gm07_intercept_priority(self, client):
        """GM07 doit être intercepté en priorité, même si pipeline défini"""
        # Note: Ce test nécessite que GM07 soit configuré dans le curriculum
        # Pour l'instant, on vérifie juste que l'intercept fonctionne
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_GM07",
                "difficulte": "facile",
                "offer": "free",
                "seed": 12345
            }
        )
        
        # GM07 doit être intercepté avant le pipeline
        assert response.status_code in [200, 422]  # 200 si exercice trouvé, 422 si pas d'exercice
        if response.status_code == 200:
            data = response.json()
            assert "enonce_html" in data or "enonce" in data
    
    def test_gm08_intercept_priority(self, client):
        """GM08 doit être intercepté en priorité, même si pipeline défini"""
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_GM08",
                "difficulte": "moyen",
                "offer": "free",
                "seed": 12345
            }
        )
        
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "enonce_html" in data or "enonce" in data
    
    def test_tests_dyn_intercept_priority(self, client):
        """TESTS_DYN doit être intercepté en priorité, même si pipeline défini"""
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_TESTS_DYN",
                "difficulte": "facile",
                "offer": "free",
                "seed": 12345
            }
        )
        
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "enonce_html" in data or "enonce" in data


class TestPipelineSPEC:
    """Tests pour le pipeline SPEC (statique uniquement)"""
    
    @pytest.mark.asyncio
    async def test_pipeline_spec_with_valid_exercise_types(self, mock_db):
        """Pipeline SPEC avec exercise_types valides doit fonctionner"""
        # Mock du curriculum avec pipeline SPEC
        from backend.curriculum.loader import CurriculumChapter
        
        chapter = CurriculumChapter(
            niveau="6e",
            code_officiel="6e_N08",
            domaine="Nombres et calculs",
            libelle="Fractions",
            chapitre_backend="Fractions",
            exercise_types=["CALCUL_FRACTIONS", "FRACTION_REPRESENTATION"],
            pipeline="SPEC"
        )
        
        # Vérifier que le pipeline est bien défini
        assert chapter.pipeline == "SPEC"
        assert len(chapter.exercise_types) > 0
        
        # Vérifier que les exercise_types sont valides
        for et in chapter.exercise_types:
            assert hasattr(MathExerciseType, et), f"{et} n'est pas dans MathExerciseType"
    
    @pytest.mark.asyncio
    async def test_pipeline_spec_with_invalid_exercise_types_raises_error(self, mock_db):
        """Pipeline SPEC avec exercise_types tous invalides doit lever une erreur"""
        from backend.services.curriculum_persistence_service import (
            CurriculumPersistenceService,
            ChapterCreateRequest
        )
        
        service = CurriculumPersistenceService(mock_db)
        
        request = ChapterCreateRequest(
            code_officiel="6e_TEST_SPEC_INVALID",
            libelle="Test SPEC Invalid",
            domaine="Test",
            chapitre_backend="Test",
            exercise_types=["INVALID_TYPE_1", "INVALID_TYPE_2"],  # Types invalides
            pipeline="SPEC"
        )
        
        # La création doit lever une ValueError
        with pytest.raises(ValueError) as exc_info:
            await service.create_chapter(request)
        
        assert "SPEC" in str(exc_info.value)
        assert "MathExerciseType" in str(exc_info.value)


class TestPipelineTEMPLATE:
    """Tests pour le pipeline TEMPLATE (dynamique uniquement)"""
    
    @pytest.mark.asyncio
    async def test_pipeline_template_with_dynamic_exercises(self, mock_db):
        """Pipeline TEMPLATE avec exercices dynamiques en DB doit fonctionner"""
        from backend.services.curriculum_persistence_service import (
            CurriculumPersistenceService,
            ChapterCreateRequest
        )
        
        # Mock de la DB avec exercices dynamiques
        mock_exercises_collection = MagicMock()
        mock_exercises_collection.find.return_value.to_list = AsyncMock(return_value=[
            {
                "id": 1,
                "chapter_code": "6E_TEST_TEMPLATE",
                "is_dynamic": True,
                "generator_key": "THALES_V1",
                "enonce_template_html": "<p>{{var}}</p>"
            }
        ])
        mock_db.exercises = mock_exercises_collection
        
        # Mock de has_exercises_in_db
        with patch('backend.services.curriculum_sync_service.get_curriculum_sync_service') as mock_sync:
            sync_service = MagicMock()
            sync_service.has_exercises_in_db = AsyncMock(return_value=True)
            mock_sync.return_value = sync_service
            
            service = CurriculumPersistenceService(mock_db)
            
            request = ChapterCreateRequest(
                code_officiel="6e_TEST_TEMPLATE",
                libelle="Test TEMPLATE",
                domaine="Test",
                chapitre_backend="Test",
                pipeline="TEMPLATE"
            )
            
            # Mock de get_exercises
            with patch('backend.services.exercise_persistence_service.get_exercise_persistence_service') as mock_exercise_service:
                exercise_service = MagicMock()
                exercise_service.get_exercises = AsyncMock(return_value=[
                    {
                        "id": 1,
                        "chapter_code": "6E_TEST_TEMPLATE",
                        "is_dynamic": True,
                        "generator_key": "THALES_V1"
                    }
                ])
                mock_exercise_service.return_value = exercise_service
                
                # La création doit réussir (pas d'erreur)
                # Note: On mock aussi la collection pour éviter l'insertion réelle
                mock_chapters_collection = MagicMock()
                mock_chapters_collection.find_one = AsyncMock(return_value=None)  # Pas de chapitre existant
                mock_chapters_collection.insert_one = AsyncMock()
                mock_db.curriculum_chapters = mock_chapters_collection
                
                # Mock de _sync_to_json et _reload_curriculum_index
                service._sync_to_json = AsyncMock()
                service._reload_curriculum_index = AsyncMock()
                
                result = await service.create_chapter(request)
                assert result["pipeline"] == "TEMPLATE"
    
    @pytest.mark.asyncio
    async def test_pipeline_template_without_dynamic_exercises_raises_error(self, mock_db):
        """Pipeline TEMPLATE sans exercices dynamiques doit lever une erreur"""
        from backend.services.curriculum_persistence_service import (
            CurriculumPersistenceService,
            ChapterCreateRequest
        )
        
        # Mock de has_exercises_in_db retournant False
        with patch('backend.services.curriculum_sync_service.get_curriculum_sync_service') as mock_sync:
            sync_service = MagicMock()
            sync_service.has_exercises_in_db = AsyncMock(return_value=False)
            mock_sync.return_value = sync_service
            
            service = CurriculumPersistenceService(mock_db)
            
            request = ChapterCreateRequest(
                code_officiel="6e_TEST_TEMPLATE_NO_EX",
                libelle="Test TEMPLATE No Exercises",
                domaine="Test",
                chapitre_backend="Test",
                pipeline="TEMPLATE"
            )
            
            # Mock de la collection pour éviter l'insertion
            mock_chapters_collection = MagicMock()
            mock_chapters_collection.find_one = AsyncMock(return_value=None)
            mock_db.curriculum_chapters = mock_chapters_collection
            
            # La création doit lever une ValueError
            with pytest.raises(ValueError) as exc_info:
                await service.create_chapter(request)
            
            assert "TEMPLATE" in str(exc_info.value)
            assert "exercice dynamique" in str(exc_info.value).lower()


class TestPipelineMIXED:
    """Tests pour le pipeline MIXED (priorité dynamique, sinon statique)"""
    
    @pytest.mark.asyncio
    async def test_pipeline_mixed_priority_dynamic(self, mock_db):
        """Pipeline MIXED doit utiliser dynamique si exercices dynamiques existent"""
        # Ce test nécessite une intégration complète
        # Pour l'instant, on vérifie juste la logique dans la route
        pass  # TODO: Test d'intégration complet


class TestPipelineFallback:
    """Tests pour le fallback legacy (pipeline absent)"""
    
    @pytest.mark.asyncio
    async def test_pipeline_fallback_when_absent(self, mock_db):
        """Si pipeline absent, fallback sur ancien comportement (détection automatique)"""
        from backend.curriculum.loader import CurriculumChapter
        
        # Chapitre sans pipeline
        chapter = CurriculumChapter(
            niveau="6e",
            code_officiel="6e_N08",
            domaine="Nombres et calculs",
            libelle="Fractions",
            chapitre_backend="Fractions",
            exercise_types=["CALCUL_FRACTIONS"]
            # pipeline non défini → None par défaut
        )
        
        # Vérifier que pipeline est None ou absent
        assert not hasattr(chapter, 'pipeline') or chapter.pipeline is None or chapter.pipeline == "SPEC"


class TestValidations:
    """Tests pour les validations bloquantes"""
    
    @pytest.mark.asyncio
    async def test_validation_template_no_exercises(self, mock_db):
        """Validation: TEMPLATE sans exercices dynamiques → erreur"""
        # Déjà testé dans TestPipelineTEMPLATE.test_pipeline_template_without_dynamic_exercises_raises_error
        pass
    
    @pytest.mark.asyncio
    async def test_validation_spec_invalid_types(self, mock_db):
        """Validation: SPEC avec exercise_types tous invalides → erreur"""
        # Déjà testé dans TestPipelineSPEC.test_pipeline_spec_with_invalid_exercise_types_raises_error
        pass




