"""
Test PR2: GM07/GM08 DB ONLY

Vérifie que:
- GM07/GM08 ne dépendent plus de data/*.py
- Les fonctions sont async et utilisent StaticExerciseRepository
- Le batch retourne <=count sans doublons (si pool >= count)
- Le batch retourne pool complet si pool < count + warning log
- offer/difficulty sont passés au repo
- Déterminisme: avec seed fixe, single renvoie toujours le même exo
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from backend.services.static_exercise_repository import StaticExerciseRepository
from backend.services.gm07_handler import generate_gm07_exercise, generate_gm07_batch
from backend.services.gm08_handler import generate_gm08_exercise, generate_gm08_batch


class TestGM07GM08DBOnly:
    """Tests pour vérifier que GM07/GM08 utilisent uniquement la DB"""
    
    @pytest.fixture
    def fake_db(self):
        """Crée un fake DB pour les tests"""
        fake_db = MagicMock()
        fake_db.__getitem__.return_value = MagicMock()
        return fake_db
    
    @pytest.fixture
    def fake_pool(self):
        """Pool d'exercices factices pour les tests"""
        return [
            {"id": 1, "chapter_code": "6E_GM07", "difficulty": "facile", "offer": "free", "enonce_html": "Exo 1", "solution_html": "Sol 1", "family": "TEST"},
            {"id": 2, "chapter_code": "6E_GM07", "difficulty": "facile", "offer": "free", "enonce_html": "Exo 2", "solution_html": "Sol 2", "family": "TEST"},
            {"id": 3, "chapter_code": "6E_GM07", "difficulty": "moyen", "offer": "free", "enonce_html": "Exo 3", "solution_html": "Sol 3", "family": "TEST"},
        ]
    
    @pytest.mark.asyncio
    async def test_gm07_batch_returns_count_if_pool_sufficient(self, fake_db, fake_pool):
        """Vérifie que batch retourne exactement count si pool >= count"""
        with patch.object(StaticExerciseRepository, 'list_by_chapter', new_callable=AsyncMock, return_value=fake_pool):
            repo = StaticExerciseRepository(fake_db)
            exercises, batch_meta = await generate_gm07_batch(
                db=fake_db,
                offer="free",
                difficulty="facile",
                count=2,
                seed=42
            )
            
            assert len(exercises) == 2
            assert batch_meta["requested"] == 2
            assert batch_meta["returned"] == 2
            assert batch_meta["available"] == 3
            # Vérifier qu'il n'y a pas de doublons (IDs différents)
            exercise_ids = [ex["metadata"]["exercise_id"] for ex in exercises]
            assert len(exercise_ids) == len(set(exercise_ids))
    
    @pytest.mark.asyncio
    async def test_gm07_batch_returns_pool_complete_if_pool_insufficient(self, fake_db, fake_pool):
        """Vérifie que batch retourne pool complet si pool < count + warning"""
        with patch.object(StaticExerciseRepository, 'list_by_chapter', new_callable=AsyncMock, return_value=fake_pool):
            with patch('backend.services.gm07_handler.logger') as mock_logger:
                exercises, batch_meta = await generate_gm07_batch(
                    db=fake_db,
                    offer="free",
                    difficulty="facile",
                    count=5,  # Plus que le pool disponible
                    seed=42
                )
                
                assert len(exercises) == 3  # Pool complet
                assert batch_meta["requested"] == 5
                assert batch_meta["returned"] == 3
                assert batch_meta["available"] == 3
                assert "warning" in batch_meta
                # Vérifier que le warning a été loggé
                mock_logger.warning.assert_called()
    
    @pytest.mark.asyncio
    async def test_gm07_batch_filters_offer_difficulty(self, fake_db, fake_pool):
        """Vérifie que offer et difficulty sont passés au repository"""
        with patch.object(StaticExerciseRepository, 'list_by_chapter', new_callable=AsyncMock, return_value=fake_pool) as mock_list:
            await generate_gm07_batch(
                db=fake_db,
                offer="free",
                difficulty="facile",
                count=1,
                seed=42
            )
            
            # Vérifier que list_by_chapter a été appelé avec les bons paramètres
            mock_list.assert_called_once_with("6E_GM07", offer="free", difficulty="facile")
    
    @pytest.mark.asyncio
    async def test_gm07_single_deterministic_with_seed(self, fake_db, fake_pool):
        """Vérifie que avec seed fixe, single renvoie toujours le même exercice"""
        with patch.object(StaticExerciseRepository, 'list_by_chapter', new_callable=AsyncMock, return_value=fake_pool):
            # Premier appel
            ex1 = await generate_gm07_exercise(
                db=fake_db,
                offer="free",
                difficulty="facile",
                seed=42
            )
            
            # Deuxième appel avec le même seed
            ex2 = await generate_gm07_exercise(
                db=fake_db,
                offer="free",
                difficulty="facile",
                seed=42
            )
            
            # Devrait retourner le même exercice (même exercise_id)
            assert ex1 is not None
            assert ex2 is not None
            assert ex1["metadata"]["exercise_id"] == ex2["metadata"]["exercise_id"]
    
    @pytest.mark.asyncio
    async def test_gm08_batch_returns_count_if_pool_sufficient(self, fake_db, fake_pool):
        """Vérifie que GM08 batch retourne exactement count si pool >= count"""
        # Adapter le pool pour GM08
        gm08_pool = [ex.copy() for ex in fake_pool]
        for ex in gm08_pool:
            ex["chapter_code"] = "6E_GM08"
        
        with patch.object(StaticExerciseRepository, 'list_by_chapter', new_callable=AsyncMock, return_value=gm08_pool):
            exercises, batch_meta = await generate_gm08_batch(
                db=fake_db,
                offer="free",
                difficulty="facile",
                count=2,
                seed=42
            )
            
            assert len(exercises) == 2
            assert batch_meta["requested"] == 2
            assert batch_meta["returned"] == 2
            assert batch_meta["available"] == 3
            # Vérifier qu'il n'y a pas de doublons
            exercise_ids = [ex["metadata"]["exercise_id"] for ex in exercises]
            assert len(exercise_ids) == len(set(exercise_ids))
    
    @pytest.mark.asyncio
    async def test_gm08_single_deterministic_with_seed(self, fake_db, fake_pool):
        """Vérifie que GM08 avec seed fixe renvoie toujours le même exercice"""
        # Adapter le pool pour GM08
        gm08_pool = [ex.copy() for ex in fake_pool]
        for ex in gm08_pool:
            ex["chapter_code"] = "6E_GM08"
        
        with patch.object(StaticExerciseRepository, 'list_by_chapter', new_callable=AsyncMock, return_value=gm08_pool):
            # Premier appel
            ex1 = await generate_gm08_exercise(
                db=fake_db,
                offer="free",
                difficulty="facile",
                seed=42
            )
            
            # Deuxième appel avec le même seed
            ex2 = await generate_gm08_exercise(
                db=fake_db,
                offer="free",
                difficulty="facile",
                seed=42
            )
            
            # Devrait retourner le même exercice
            assert ex1 is not None
            assert ex2 is not None
            assert ex1["metadata"]["exercise_id"] == ex2["metadata"]["exercise_id"]
    
    @pytest.mark.asyncio
    async def test_gm07_empty_pool_returns_none(self, fake_db):
        """Vérifie que si le pool est vide, single retourne None"""
        with patch.object(StaticExerciseRepository, 'list_by_chapter', new_callable=AsyncMock, return_value=[]):
            result = await generate_gm07_exercise(
                db=fake_db,
                offer="free",
                difficulty="facile",
                seed=42
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_gm07_empty_pool_batch_returns_empty_with_warning(self, fake_db):
        """Vérifie que si le pool est vide, batch retourne [] avec warning"""
        with patch.object(StaticExerciseRepository, 'list_by_chapter', new_callable=AsyncMock, return_value=[]):
            exercises, batch_meta = await generate_gm07_batch(
                db=fake_db,
                offer="free",
                difficulty="facile",
                count=5,
                seed=42
            )
            
            assert exercises == []
            assert batch_meta["available"] == 0
            assert batch_meta["returned"] == 0
            assert "warning" in batch_meta

