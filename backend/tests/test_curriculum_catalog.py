"""
Test pour l'endpoint GET /api/v1/curriculum/6e/catalog
"""
import pytest
from fastapi.testclient import TestClient
from backend.server import app

client = TestClient(app)

def test_curriculum_catalog_6e():
    """
    Test: GET /api/v1/curriculum/6e/catalog retourne 200
    """
    response = client.get("/api/v1/curriculum/6e/catalog")
    
    # Vérifier que la réponse est 200
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
    
    # Vérifier que la réponse est JSON
    assert response.headers["content-type"].startswith("application/json")
    
    # Vérifier que la réponse contient les champs attendus
    data = response.json()
    assert "domains" in data
    assert "macro_groups" in data
    assert "total_chapters" in data
    assert "total_macro_groups" in data
    
    print("✅ Test curriculum catalog 6e passed!")


def test_curriculum_catalog_5e():
    """
    Test: GET /api/v1/curriculum/5e/catalog retourne 200 ou erreur appropriée
    """
    response = client.get("/api/v1/curriculum/5e/catalog")
    
    # Devrait retourner 200 ou une erreur spécifique (pas 500 Internal Server Error)
    assert response.status_code in [200, 404, 400], f"Expected 200/404/400, got {response.status_code}"
    
    print(f"✅ Test curriculum catalog 5e passed! Status: {response.status_code}")


def test_curriculum_catalog_legacy():
    """
    Test: GET /api/v1/catalog (legacy) retourne 200
    """
    response = client.get("/api/v1/catalog")
    
    # Vérifier que la réponse est 200
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
    
    # Vérifier que la réponse est JSON
    assert response.headers["content-type"].startswith("application/json")
    
    # Vérifier que la réponse contient les champs attendus
    data = response.json()
    assert "domains" in data
    assert "macro_groups" in data
    
    print("✅ Test curriculum catalog legacy passed!")