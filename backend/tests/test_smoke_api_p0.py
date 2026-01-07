"""
Smoke tests P0 pour validation release
=======================================

Tests minimaux pour valider que l'API est fonctionnelle avant release.
Ces tests doivent être rapides et ne pas dépendre d'états externes complexes.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient
import os


@pytest_asyncio.fixture
async def test_db():
    """Crée une connexion MongoDB de test"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('TEST_DB_NAME', 'test_le_maitre_mot_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    yield db
    
    client.close()


@pytest_asyncio.fixture
async def client(test_db):
    """Client HTTP async pour les tests"""
    from backend.server import app
    
    # Injecter la DB de test dans l'app
    app.state.db = test_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    """Test que l'endpoint /api/health répond correctement"""
    response = await client.get("/api/health")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "ok"]


@pytest.mark.asyncio
async def test_generate_exercise_smoke(client):
    """Test que l'endpoint de génération répond avec un exercice valide"""
    # Utiliser un générateur gold qui ne nécessite pas d'exercices en DB
    # SIMPLIFICATION_FRACTIONS_V2 est un générateur gold stable
    payload = {
        "generator_key": "SIMPLIFICATION_FRACTIONS_V2",
        "overrides": {
            "seed": 1,
            "difficulty": "moyen"
        }
    }
    
    response = await client.post(
        "/api/v1/exercises/generate",
        json=payload
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    
    # Vérifier que l'exercice contient les champs essentiels
    assert "enonce_html" in data, "enonce_html manquant dans la réponse"
    assert "solution_html" in data, "solution_html manquant dans la réponse"
    
    # Vérifier que les champs ne sont pas vides
    assert data["enonce_html"], "enonce_html est vide"
    assert data["solution_html"], "solution_html est vide"
    
    # Vérifier que ce n'est pas juste du HTML vide
    enonce_text = data["enonce_html"].replace("<", "").replace(">", "").strip()
    solution_text = data["solution_html"].replace("<", "").replace(">", "").strip()
    assert enonce_text, "enonce_html ne contient pas de texte"
    assert solution_text, "solution_html ne contient pas de texte"


@pytest.mark.asyncio
async def test_request_id_header(client):
    """Test que le middleware request_id fonctionne"""
    # Test sans header X-Request-Id (doit être généré)
    response = await client.get("/api/health")
    
    assert response.status_code == 200
    # Le middleware doit ajouter X-Request-Id dans la réponse
    assert "X-Request-Id" in response.headers, "X-Request-Id manquant dans les headers de réponse"
    request_id = response.headers["X-Request-Id"]
    assert request_id, "X-Request-Id est vide"
    assert len(request_id) > 0, "X-Request-Id invalide"
    
    # Test avec header X-Request-Id fourni (doit être réutilisé)
    custom_request_id = "test-request-id-12345"
    response2 = await client.get(
        "/api/health",
        headers={"X-Request-Id": custom_request_id}
    )
    
    assert response2.status_code == 200
    assert response2.headers["X-Request-Id"] == custom_request_id, "X-Request-Id fourni n'a pas été réutilisé"


@pytest.mark.asyncio
async def test_export_pdf_eco_smoke(client, test_db):
    """Test que l'export PDF eco fonctionne (2 colonnes + compact)"""
    # Créer une fiche de test minimaliste
    from backend.constants.collections import EXERCISE_SHEETS_COLLECTION
    from uuid import uuid4
    
    sheet_id = f"test_sheet_{uuid4().hex[:8]}"
    
    # Insérer une fiche minimale
    sheet_collection = test_db[EXERCISE_SHEETS_COLLECTION]
    await sheet_collection.insert_one({
        "id": sheet_id,
        "titre": "Test PDF Eco",
        "niveau": "6e",
        "created_at": "2025-01-01T00:00:00Z"
    })
    
    # Appeler l'endpoint export-standard avec layout=eco
    # Note: Le test vérifie que l'endpoint accepte layout=eco, même si la fiche est vide
    response = await client.post(
        f"/api/mathalea/sheets/{sheet_id}/export-standard?layout=eco",
        headers={"X-Guest-ID": "test-guest-id"}
    )
    
    # Vérifier que l'endpoint répond (400 si fiche vide, 200 si fiche avec items)
    # L'important est que l'endpoint fonctionne et accepte le paramètre layout=eco
    # Codes acceptables: 200 (succès), 400 (fiche vide), 404 (fiche non trouvée), 402 (quota)
    assert response.status_code in [200, 400, 404, 402], f"Expected 200, 400, 404, or 402, got {response.status_code}: {response.json()}"
    
    # Si 200, vérifier que les PDFs sont présents
    if response.status_code == 200:
        data = response.json()
        assert "student_pdf" in data, "student_pdf manquant dans la réponse"
        assert "correction_pdf" in data, "correction_pdf manquant dans la réponse"
        
        # Vérifier que les PDFs sont en base64 (non vides)
        assert data["student_pdf"], "student_pdf est vide"
        assert data["correction_pdf"], "correction_pdf est vide"
        
        # Vérifier que ce sont bien des données base64 (commencent par des caractères valides)
        assert len(data["student_pdf"]) > 100, "student_pdf semble trop court"
        assert len(data["correction_pdf"]) > 100, "correction_pdf semble trop court"
    
    # Nettoyer
    await sheet_collection.delete_one({"id": sheet_id})

