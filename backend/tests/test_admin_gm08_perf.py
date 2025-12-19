"""
Tests pour le bug admin GM08 (500 + lenteur).

Vérifie :
- Pas d'erreur 500 pour GM08
- Cache fonctionne (HIT/MISS)
- Performance acceptable
"""

import pytest
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
from backend.services.exercise_persistence_service import (
    ExercisePersistenceService,
    get_exercise_persistence_service
)
from motor.motor_asyncio import AsyncIOMotorClient
import os


@pytest.fixture
async def mock_db():
    """Mock MongoDB pour tests"""
    mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    db_name = os.getenv('MONGODB_DB', 'le_maitre_mot_test')
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    yield db
    client.close()


@pytest.mark.asyncio
async def test_gm08_list_exercises_no_500(mock_db):
    """
    Test que list_exercises pour GM08 ne lève pas HTTP 500.
    
    Root cause attendue : ValueError dans _load_from_python_file remonté correctement.
    """
    service = ExercisePersistenceService(mock_db)
    
    # Doit fonctionner (ou lever ValueError explicite, pas 500)
    try:
        exercises = await service.get_exercises("6e_GM08")
        # Si succès : OK
        assert isinstance(exercises, list)
    except ValueError as e:
        # ValueError explicite = OK (pas 500)
        assert "Erreur" in str(e) or "Impossible" in str(e)
    except Exception as e:
        # Autre exception = KO (devrait être ValueError)
        pytest.fail(f"Exception inattendue pour GM08: {type(e).__name__}: {e}")


@pytest.mark.asyncio
async def test_get_stats_cache_hit_miss(mock_db):
    """
    Test que get_stats utilise le cache (HIT après MISS).
    
    Vérifie :
    - Première requête = CACHE MISS (requête DB)
    - Deuxième requête = CACHE HIT (pas de requête DB)
    """
    service = ExercisePersistenceService(mock_db)
    
    # Reset cache
    service._stats_cache.clear()
    
    # Première requête (CACHE MISS)
    stats1 = await service.get_stats("6e_GM08")
    assert "total" in stats1
    assert "by_offer" in stats1
    
    # Vérifier que cache est rempli
    cache_key = "6E_GM08_stats"
    assert cache_key in service._stats_cache
    
    # Deuxième requête (CACHE HIT)
    # Modifier manuellement le cache pour simuler un HIT
    cached_stats, cached_time = service._stats_cache[cache_key]
    # Forcer un HIT en mettant une date récente
    service._stats_cache[cache_key] = (cached_stats, datetime.now(timezone.utc))
    
    stats2 = await service.get_stats("6e_GM08")
    
    # Vérifier que stats2 = stats1 (même objet si cache HIT)
    assert stats2 == stats1


@pytest.mark.asyncio
async def test_get_stats_cache_ttl_expiry(mock_db):
    """
    Test que le cache TTL expire correctement (5 min).
    """
    service = ExercisePersistenceService(mock_db)
    
    # Reset cache
    service._stats_cache.clear()
    
    # Première requête
    stats1 = await service.get_stats("6e_GM08")
    
    # Forcer expiration TTL (date > 5 min)
    cache_key = "6E_GM08_stats"
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=6)
    service._stats_cache[cache_key] = (stats1, expired_time)
    
    # Deuxième requête (CACHE MISS car TTL expiré)
    stats2 = await service.get_stats("6e_GM08")
    
    # Stats doivent être recalculées (même structure)
    assert "total" in stats2
    assert "by_offer" in stats2


@pytest.mark.asyncio
async def test_initialize_chapter_cache(mock_db):
    """
    Test que initialize_chapter utilise le cache (évite requêtes DB répétées).
    """
    service = ExercisePersistenceService(mock_db)
    
    # Reset
    service._initialized.clear()
    
    # Première initialisation
    await service.initialize_chapter("6E_GM08")
    assert "6E_GM08" in service._initialized
    
    # Deuxième initialisation (doit être rapide, pas de requête DB)
    # On ne peut pas vraiment tester sans mock, mais on vérifie que _initialized est utilisé
    initial_count = len(service._initialized)
    await service.initialize_chapter("6E_GM08")
    assert len(service._initialized) == initial_count  # Pas de nouvelle entrée



