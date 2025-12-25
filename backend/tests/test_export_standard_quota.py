"""
P0 - Tests pour la protection quota sur export-standard

Tests:
- Pro user: pas de quota
- Guest sans guest_id: 400
- Guest avec quota OK: export réussi + enregistrement dans db.exports
- Guest avec quota dépassé: 402
- Cas limites: session invalide, guest_id manquant, etc.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock
import sys
from pathlib import Path

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import app
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Connexion MongoDB pour les tests
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
test_db_name = os.environ.get('TEST_DB_NAME', 'le_maitre_mot_test_db')
test_client = AsyncIOMotorClient(mongo_url)
test_db = test_client[test_db_name]


@pytest_asyncio.fixture
async def client():
    """Client HTTP async pour les tests"""
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def clean_exports():
    """Nettoyer la collection exports avant et après chaque test"""
    await test_db.exports.delete_many({})
    yield
    await test_db.exports.delete_many({})


@pytest_asyncio.fixture
async def mock_sheet():
    """Créer une fiche de test"""
    sheet_id = "test_sheet_export_quota"
    sheet = {
        "id": sheet_id,
        "titre": "Test Export Quota",
        "niveau": "6e",
        "description": "Fiche de test pour quota"
    }
    
    # Utiliser la DB de test
    from backend.routes.mathalea_routes import exercise_sheets_collection
    # Note: En production, on devrait utiliser test_db, mais pour simplifier on mock
    
    yield sheet_id
    # Cleanup si nécessaire


@pytest.mark.asyncio
async def test_export_pro_user_no_quota(client, clean_exports, mock_sheet):
    """Test: Utilisateur Pro n'a pas de quota"""
    # Mock validate_session_token et check_user_pro_status
    with patch('backend.routes.mathalea_routes.validate_session_token') as mock_validate, \
         patch('backend.routes.mathalea_routes.check_user_pro_status') as mock_pro:
        
        mock_validate.return_value = "pro@test.com"
        mock_pro.return_value = (True, {"email": "pro@test.com"})
        
        # Mock la génération PDF (simplifié)
        with patch('backend.routes.mathalea_routes.build_sheet_student_pdf') as mock_student, \
             patch('backend.routes.mathalea_routes.build_sheet_correction_pdf') as mock_correction:
            
            mock_student.return_value = b"fake_pdf_student"
            mock_correction.return_value = b"fake_pdf_correction"
            
            # Mock les collections MongoDB
            with patch('backend.routes.mathalea_routes.exercise_sheets_collection') as mock_sheets, \
                 patch('backend.routes.mathalea_routes.sheet_items_collection') as mock_items, \
                 patch('backend.routes.mathalea_routes.exercise_types_collection') as mock_types:
                
                mock_sheets.find_one = AsyncMock(return_value={"id": mock_sheet, "titre": "Test", "niveau": "6e"})
                mock_items.find = AsyncMock(return_value=AsyncMock(to_list=AsyncMock(return_value=[])))
                mock_types.find_one = AsyncMock(return_value=None)
                
                response = await client.post(
                    f"/api/mathalea/sheets/{mock_sheet}/export-standard",
                    headers={"X-Session-Token": "valid_pro_token"}
                )
                
                # Vérifier que l'export réussit
                assert response.status_code == 200
                data = response.json()
                assert "student_pdf" in data
                assert "correction_pdf" in data
                assert data["metadata"]["user_type"] == "pro"
                
                # Vérifier qu'aucun export n'a été enregistré dans db.exports
                export_count = await test_db.exports.count_documents({"sheet_id": mock_sheet})
                assert export_count == 0


@pytest.mark.asyncio
async def test_export_guest_no_guest_id_400(client, clean_exports, mock_sheet):
    """Test: Guest sans guest_id retourne 400"""
    response = await client.post(
        f"/api/mathalea/sheets/{mock_sheet}/export-standard"
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"] == "guest_id_required"


@pytest.mark.asyncio
async def test_export_guest_with_quota_ok(client, clean_exports, mock_sheet):
    """Test: Guest avec quota OK peut exporter"""
    guest_id = "test_guest_123"
    
    # S'assurer que le quota est OK (moins de 3 exports dans les 30 derniers jours)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    existing_count = await test_db.exports.count_documents({
        "guest_id": guest_id,
        "created_at": {"$gte": thirty_days_ago}
    })
    
    # Si déjà 3 exports, nettoyer pour ce test
    if existing_count >= 3:
        await test_db.exports.delete_many({"guest_id": guest_id})
    
    # Mock la génération PDF
    with patch('backend.routes.mathalea_routes.build_sheet_student_pdf') as mock_student, \
         patch('backend.routes.mathalea_routes.build_sheet_correction_pdf') as mock_correction, \
         patch('backend.routes.mathalea_routes.exercise_sheets_collection') as mock_sheets, \
         patch('backend.routes.mathalea_routes.sheet_items_collection') as mock_items, \
         patch('backend.routes.mathalea_routes.exercise_types_collection') as mock_types, \
         patch('backend.routes.mathalea_routes.db') as mock_db:
        
        mock_student.return_value = b"fake_pdf_student"
        mock_correction.return_value = b"fake_pdf_correction"
        mock_sheets.find_one = AsyncMock(return_value={"id": mock_sheet, "titre": "Test", "niveau": "6e"})
        mock_items.find = AsyncMock(return_value=AsyncMock(to_list=AsyncMock(return_value=[])))
        mock_types.find_one = AsyncMock(return_value=None)
        mock_db.exports = test_db.exports  # Utiliser la vraie DB pour les exports
        
        response = await client.post(
            f"/api/mathalea/sheets/{mock_sheet}/export-standard",
            headers={"X-Guest-ID": guest_id}
        )
        
        # Vérifier que l'export réussit
        assert response.status_code == 200
        data = response.json()
        assert "student_pdf" in data
        assert "correction_pdf" in data
        assert data["metadata"]["user_type"] == "guest"
        
        # Vérifier que l'export a été enregistré
        export_doc = await test_db.exports.find_one({
            "guest_id": guest_id,
            "sheet_id": mock_sheet,
            "type": "sheet_export"
        })
        assert export_doc is not None


@pytest.mark.asyncio
async def test_export_guest_quota_exceeded_402(client, clean_exports, mock_sheet):
    """Test: Guest avec quota dépassé retourne 402"""
    guest_id = "test_guest_quota_exceeded"
    
    # Créer 3 exports dans les 30 derniers jours
    now = datetime.now(timezone.utc)
    for i in range(3):
        await test_db.exports.insert_one({
            "guest_id": guest_id,
            "sheet_id": f"sheet_{i}",
            "type": "sheet_export",
            "created_at": now - timedelta(days=i)
        })
    
    # Mock la génération PDF (ne sera pas appelée)
    with patch('backend.routes.mathalea_routes.exercise_sheets_collection') as mock_sheets:
        mock_sheets.find_one = AsyncMock(return_value={"id": mock_sheet, "titre": "Test", "niveau": "6e"})
        
        response = await client.post(
            f"/api/mathalea/sheets/{mock_sheet}/export-standard",
            headers={"X-Guest-ID": guest_id}
        )
        
        # Vérifier que l'export est refusé
        assert response.status_code == 402
        data = response.json()
        assert data["detail"]["error"] == "quota_exceeded"
        assert data["detail"]["action"] == "upgrade_required"
        assert data["detail"]["exports_used"] == 3
        assert data["detail"]["exports_remaining"] == 0


@pytest.mark.asyncio
async def test_export_guest_id_query_param(client, clean_exports, mock_sheet):
    """Test: guest_id peut être passé en query param"""
    guest_id = "test_guest_query"
    
    # Mock la génération PDF
    with patch('backend.routes.mathalea_routes.build_sheet_student_pdf') as mock_student, \
         patch('backend.routes.mathalea_routes.build_sheet_correction_pdf') as mock_correction, \
         patch('backend.routes.mathalea_routes.exercise_sheets_collection') as mock_sheets, \
         patch('backend.routes.mathalea_routes.sheet_items_collection') as mock_items, \
         patch('backend.routes.mathalea_routes.exercise_types_collection') as mock_types, \
         patch('backend.routes.mathalea_routes.db') as mock_db:
        
        mock_student.return_value = b"fake_pdf_student"
        mock_correction.return_value = b"fake_pdf_correction"
        mock_sheets.find_one = AsyncMock(return_value={"id": mock_sheet, "titre": "Test", "niveau": "6e"})
        mock_items.find = AsyncMock(return_value=AsyncMock(to_list=AsyncMock(return_value=[])))
        mock_types.find_one = AsyncMock(return_value=None)
        mock_db.exports = test_db.exports
        
        response = await client.post(
            f"/api/mathalea/sheets/{mock_sheet}/export-standard?guest_id={guest_id}"
        )
        
        # Vérifier que l'export réussit
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["user_type"] == "guest"


@pytest.mark.asyncio
async def test_export_invalid_session_token_treated_as_guest(client, clean_exports, mock_sheet):
    """Test: Session token invalide traité comme guest"""
    guest_id = "test_guest_invalid_session"
    
    # Mock validate_session_token pour lever une exception
    with patch('backend.routes.mathalea_routes.validate_session_token') as mock_validate, \
         patch('backend.routes.mathalea_routes.build_sheet_student_pdf') as mock_student, \
         patch('backend.routes.mathalea_routes.build_sheet_correction_pdf') as mock_correction, \
         patch('backend.routes.mathalea_routes.exercise_sheets_collection') as mock_sheets, \
         patch('backend.routes.mathalea_routes.sheet_items_collection') as mock_items, \
         patch('backend.routes.mathalea_routes.exercise_types_collection') as mock_types, \
         patch('backend.routes.mathalea_routes.db') as mock_db:
        
        mock_validate.side_effect = Exception("Invalid token")
        mock_student.return_value = b"fake_pdf_student"
        mock_correction.return_value = b"fake_pdf_correction"
        mock_sheets.find_one = AsyncMock(return_value={"id": mock_sheet, "titre": "Test", "niveau": "6e"})
        mock_items.find = AsyncMock(return_value=AsyncMock(to_list=AsyncMock(return_value=[])))
        mock_types.find_one = AsyncMock(return_value=None)
        mock_db.exports = test_db.exports
        
        response = await client.post(
            f"/api/mathalea/sheets/{mock_sheet}/export-standard",
            headers={
                "X-Session-Token": "invalid_token",
                "X-Guest-ID": guest_id
            }
        )
        
        # Vérifier que l'export réussit comme guest
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["user_type"] == "guest"


@pytest.mark.asyncio
async def test_export_non_pro_user_requires_guest_id(client, clean_exports, mock_sheet):
    """Test: Utilisateur non-Pro nécessite guest_id"""
    guest_id = "test_guest_non_pro"
    
    # Mock validate_session_token et check_user_pro_status (non-Pro)
    with patch('backend.routes.mathalea_routes.validate_session_token') as mock_validate, \
         patch('backend.routes.mathalea_routes.check_user_pro_status') as mock_pro, \
         patch('backend.routes.mathalea_routes.build_sheet_student_pdf') as mock_student, \
         patch('backend.routes.mathalea_routes.build_sheet_correction_pdf') as mock_correction, \
         patch('backend.routes.mathalea_routes.exercise_sheets_collection') as mock_sheets, \
         patch('backend.routes.mathalea_routes.sheet_items_collection') as mock_items, \
         patch('backend.routes.mathalea_routes.exercise_types_collection') as mock_types, \
         patch('backend.routes.mathalea_routes.db') as mock_db:
        
        mock_validate.return_value = "user@test.com"
        mock_pro.return_value = (False, None)  # Non-Pro
        mock_student.return_value = b"fake_pdf_student"
        mock_correction.return_value = b"fake_pdf_correction"
        mock_sheets.find_one = AsyncMock(return_value={"id": mock_sheet, "titre": "Test", "niveau": "6e"})
        mock_items.find = AsyncMock(return_value=AsyncMock(to_list=AsyncMock(return_value=[])))
        mock_types.find_one = AsyncMock(return_value=None)
        mock_db.exports = test_db.exports
        
        # Test sans guest_id: doit échouer
        response = await client.post(
            f"/api/mathalea/sheets/{mock_sheet}/export-standard",
            headers={"X-Session-Token": "valid_token_but_not_pro"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "guest_id_required"
        
        # Test avec guest_id: doit réussir
        response = await client.post(
            f"/api/mathalea/sheets/{mock_sheet}/export-standard",
            headers={
                "X-Session-Token": "valid_token_but_not_pro",
                "X-Guest-ID": guest_id
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["user_type"] == "guest"



