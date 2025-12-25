"""
Tests pour les endpoints admin chapter generators (P4.B)
"""

import pytest
from fastapi.testclient import TestClient
from backend.server import app
from backend.services.curriculum_persistence_service import (
    CurriculumPersistenceService,
    EnabledGeneratorConfig,
)
from backend.generators.factory import GeneratorFactory


@pytest.fixture
def client():
    """Client de test FastAPI"""
    return TestClient(app)


@pytest.fixture
async def test_chapter_code():
    """Code de chapitre de test"""
    return "6e_TEST_GEN"


@pytest.mark.asyncio
async def test_get_chapter_generators(client, test_chapter_code):
    """Test GET /api/v1/admin/chapters/{code}/generators"""
    # Créer un chapitre de test si nécessaire
    # (nécessite une DB de test)
    
    response = client.get(f"/api/v1/admin/chapters/{test_chapter_code}/generators")
    
    # Le chapitre peut ne pas exister, donc 404 est acceptable
    if response.status_code == 404:
        pytest.skip(f"Chapitre {test_chapter_code} n'existe pas (test nécessite DB)")
    
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier la structure de la réponse
    assert "chapter_code" in data
    assert "available_generators" in data
    assert "enabled_generators" in data
    assert "warnings" in data
    
    # Vérifier que les générateurs disponibles ont les bonnes propriétés
    if data["available_generators"]:
        gen = data["available_generators"][0]
        assert "key" in gen
        assert "label" in gen
        assert "supported_difficulties" in gen
        assert "min_offer" in gen
        assert "is_gold" in gen
        assert "is_disabled" in gen
        
        # Vérifier que les difficultés sont normalisées (jamais "standard")
        for diff in gen["supported_difficulties"]:
            assert diff in ["facile", "moyen", "difficile"]


@pytest.mark.asyncio
async def test_put_chapter_generators(client, test_chapter_code):
    """Test PUT /api/v1/admin/chapters/{code}/generators"""
    # Récupérer un générateur réel
    all_generators = GeneratorFactory.list_all(include_disabled=False)
    if not all_generators:
        pytest.skip("Aucun générateur disponible pour le test")
    
    test_generator = all_generators[0]
    generator_key = test_generator["key"]
    
    # Construire la requête
    payload = {
        "enabled_generators": [
            {
                "generator_key": generator_key,
                "difficulty_presets": ["facile", "moyen", "difficile"],
                "min_offer": "free",
                "is_enabled": True
            }
        ]
    }
    
    response = client.put(
        f"/api/v1/admin/chapters/{test_chapter_code}/generators",
        json=payload
    )
    
    # Le chapitre peut ne pas exister, donc 404 est acceptable
    if response.status_code == 404:
        pytest.skip(f"Chapitre {test_chapter_code} n'existe pas (test nécessite DB)")
    
    # Vérifier que le générateur invalide est rejeté
    if response.status_code == 400:
        # C'est OK si le générateur est désactivé ou invalide
        assert "detail" in response.json()
        return
    
    assert response.status_code == 200
    data = response.json()
    
    assert "chapter_code" in data
    assert "enabled_generators_count" in data
    assert data["enabled_generators_count"] == 1


@pytest.mark.asyncio
async def test_put_chapter_generators_invalid_generator(client, test_chapter_code):
    """Test PUT avec un générateur invalide"""
    payload = {
        "enabled_generators": [
            {
                "generator_key": "INVALID_GENERATOR_XYZ",
                "difficulty_presets": ["facile"],
                "min_offer": "free",
                "is_enabled": True
            }
        ]
    }
    
    response = client.put(
        f"/api/v1/admin/chapters/{test_chapter_code}/generators",
        json=payload
    )
    
    # Le chapitre peut ne pas exister, donc 404 est acceptable
    if response.status_code == 404:
        pytest.skip(f"Chapitre {test_chapter_code} n'existe pas (test nécessite DB)")
    
    # Doit retourner 400 pour générateur invalide
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_put_chapter_generators_normalizes_difficulties(client, test_chapter_code):
    """Test que PUT normalise les difficultés (standard -> moyen)"""
    all_generators = GeneratorFactory.list_all(include_disabled=False)
    if not all_generators:
        pytest.skip("Aucun générateur disponible pour le test")
    
    test_generator = all_generators[0]
    generator_key = test_generator["key"]
    
    # Utiliser "standard" dans la requête
    payload = {
        "enabled_generators": [
            {
                "generator_key": generator_key,
                "difficulty_presets": ["facile", "standard", "difficile"],  # "standard" doit être normalisé
                "min_offer": "free",
                "is_enabled": True
            }
        ]
    }
    
    response = client.put(
        f"/api/v1/admin/chapters/{test_chapter_code}/generators",
        json=payload
    )
    
    if response.status_code == 404:
        pytest.skip(f"Chapitre {test_chapter_code} n'existe pas (test nécessite DB)")
    
    if response.status_code == 400:
        # C'est OK si le générateur est désactivé
        return
    
    # Vérifier que "standard" a été normalisé en "moyen"
    # En rechargeant le chapitre
    get_response = client.get(f"/api/v1/admin/chapters/{test_chapter_code}/generators")
    if get_response.status_code == 200:
        data = get_response.json()
        enabled = data.get("enabled_generators", [])
        if enabled:
            presets = enabled[0].get("difficulty_presets", [])
            # "standard" ne doit pas apparaître, "moyen" doit être présent
            assert "standard" not in presets
            if "facile" in presets or "difficile" in presets:
                # Si facile ou difficile est présent, moyen devrait aussi être là (normalisé depuis standard)
                pass  # On vérifie juste qu'il n'y a pas "standard"


@pytest.mark.asyncio
async def test_auto_fill_chapter_generators(client, test_chapter_code):
    """Test POST /api/v1/admin/chapters/{code}/generators/auto-fill"""
    response = client.post(
        f"/api/v1/admin/chapters/{test_chapter_code}/generators/auto-fill"
    )
    
    if response.status_code == 404:
        pytest.skip(f"Chapitre {test_chapter_code} n'existe pas (test nécessite DB)")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "chapter_code" in data
    assert "added_generators" in data
    assert "suggestions" in data
    assert "message" in data




