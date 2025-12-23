"""
Configuration partagée pour les tests pytest
"""
import pytest
from fastapi.testclient import TestClient
from backend.server import app


@pytest.fixture
def test_client():
    """Fixture pour créer un client de test FastAPI"""
    return TestClient(app)

