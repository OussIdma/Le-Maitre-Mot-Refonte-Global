"""
Configuration partagée pour les tests pytest
"""
import os
import pytest
from fastapi.testclient import TestClient

# P3.1a: Définir les variables d'environnement de test avant l'import de app
os.environ.setdefault('LM_TESTING', '1')
os.environ.setdefault('MONGO_URL', 'mongodb://localhost:27017')
os.environ.setdefault('DB_NAME', 'test_db')
os.environ.setdefault('ENABLE_PY_EXPORT', 'false')  # Désactiver l'export Python en mode test

from backend.server import app


@pytest.fixture
def test_client():
    """Fixture pour créer un client de test FastAPI"""
    return TestClient(app)

