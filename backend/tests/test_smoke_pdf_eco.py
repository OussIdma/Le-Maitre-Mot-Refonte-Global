"""
Smoke test pour l'export PDF éco
=================================

Test minimal pour valider que l'endpoint export-standard génère un PDF valide
avec le layout éco (2 colonnes).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient
import os
import base64


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
    from server import app
    
    # Injecter la DB de test dans l'app
    app.state.db = test_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_sheet(test_db):
    """Crée une fiche de test avec un exercice minimal"""
    from backend.constants.collections import EXERCISE_SHEETS_COLLECTION, SHEET_ITEMS_COLLECTION, EXERCISE_TYPES_COLLECTION
    
    # Créer un exercise_type minimal avec les champs requis
    exercise_type = {
        "id": "test_ex_type_1",
        "code_ref": "TEST_ECO_1",
        "generator_key": "TEST_ECO_1",
        "titre": "Test Éco",
        "niveau": "6e",
        "domaine": "Nombres",
        "chapter_code": "6E_TEST",
        "enonce_template": "<p>Calcule : {{expression}}</p>",
        "solution_template": "<p>Résultat : {{resultat}}</p>",
        "enonce_template_html": "<p>Calcule : {{expression}}</p>",
        "solution_template_html": "<p>Résultat : {{resultat}}</p>"
    }
    await test_db[EXERCISE_TYPES_COLLECTION].update_one(
        {"id": "test_ex_type_1"},
        {"$set": exercise_type},
        upsert=True
    )
    
    # Créer une fiche (utiliser le même format que l'endpoint attend)
    sheet = {
        "id": "test_sheet_eco_1",
        "titre": "Test PDF Éco",
        "niveau": "6e",
        "description": "Fiche de test pour PDF éco"
    }
    await test_db[EXERCISE_SHEETS_COLLECTION].update_one(
        {"id": "test_sheet_eco_1"},
        {"$set": sheet},
        upsert=True
    )
    
    # Créer un item
    item = {
        "id": "test_item_1",
        "sheet_id": "test_sheet_eco_1",
        "exercise_type_id": "test_ex_type_1",
        "order": 1,
        "config": {
            "nb_questions": 1,
            "seed": 1,
            "difficulty": "moyen",
            "options": {}
        }
    }
    await test_db[SHEET_ITEMS_COLLECTION].update_one(
        {"id": "test_item_1"},
        {"$set": item},
        upsert=True
    )
    
    yield "test_sheet_eco_1"
    
    # Cleanup
    await test_db[EXERCISE_SHEETS_COLLECTION].delete_many({"id": "test_sheet_eco_1"})
    await test_db[SHEET_ITEMS_COLLECTION].delete_many({"sheet_id": "test_sheet_eco_1"})
    await test_db[EXERCISE_TYPES_COLLECTION].delete_many({"id": "test_ex_type_1"})


@pytest.mark.asyncio
async def test_export_pdf_eco_smoke(client, test_sheet):
    """Test que l'endpoint export-standard génère un PDF éco valide"""
    # Générer un guest_id pour le test
    import uuid
    guest_id = str(uuid.uuid4())
    
    response = await client.post(
        f"/api/mathalea/sheets/{test_sheet}/export-standard?layout=eco",
        headers={"X-Guest-ID": guest_id}
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json() if response.status_code != 200 else 'OK'}"
    data = response.json()
    
    # Vérifier que les 2 PDFs sont présents
    assert "student_pdf" in data, "student_pdf manquant dans la réponse"
    assert "correction_pdf" in data, "correction_pdf manquant dans la réponse"
    
    # Vérifier que les PDFs sont en base64 valides
    student_pdf_b64 = data["student_pdf"]
    correction_pdf_b64 = data["correction_pdf"]
    
    assert student_pdf_b64, "student_pdf est vide"
    assert correction_pdf_b64, "correction_pdf est vide"
    
    # Décoder et vérifier que ce sont bien des PDFs (commencent par %PDF)
    try:
        student_pdf_bytes = base64.b64decode(student_pdf_b64)
        correction_pdf_bytes = base64.b64decode(correction_pdf_b64)
        
        # Vérifier la signature PDF
        assert student_pdf_bytes.startswith(b"%PDF"), "student_pdf n'est pas un PDF valide"
        assert correction_pdf_bytes.startswith(b"%PDF"), "correction_pdf n'est pas un PDF valide"
        
        # Vérifier une taille minimale (au moins 1KB)
        assert len(student_pdf_bytes) > 1024, f"student_pdf trop petit: {len(student_pdf_bytes)} bytes"
        assert len(correction_pdf_bytes) > 1024, f"correction_pdf trop petit: {len(correction_pdf_bytes)} bytes"
        
    except Exception as e:
        pytest.fail(f"Erreur lors du décodage des PDFs: {e}")


@pytest.mark.asyncio
async def test_export_pdf_eco_default_layout(client, test_sheet):
    """Test que le layout par défaut est 'eco'"""
    import uuid
    guest_id = str(uuid.uuid4())
    
    # Appel sans paramètre layout (doit être eco par défaut)
    response = await client.post(
        f"/api/mathalea/sheets/{test_sheet}/export-standard",
        headers={"X-Guest-ID": guest_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "student_pdf" in data
    assert "correction_pdf" in data
    
    # Vérifier que les PDFs sont valides
    student_pdf_bytes = base64.b64decode(data["student_pdf"])
    assert student_pdf_bytes.startswith(b"%PDF")

