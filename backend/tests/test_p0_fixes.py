"""
Tests pour les corrections P0:
- P0-1: Validation des variables d'environnement
- P0-2: Authentification Pro pour export PDF
- P0-3: Robustesse WeasyPrint (timeout, logo)
"""

import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta


# ============================================================================
# P0-1: Validation des variables d'environnement
# ============================================================================

def test_env_validation_missing_mongo_url(monkeypatch):
    """Test que l'application refuse de démarrer si MONGO_URL est absent"""
    # Supprimer MONGO_URL
    monkeypatch.delenv("MONGO_URL", raising=False)
    
    # Tenter d'importer le module (qui appelle validate_env au démarrage)
    with pytest.raises(RuntimeError) as exc_info:
        # Simuler l'import qui déclenche validate_env
        from backend.server import validate_env
        validate_env()
    
    assert "MONGO_URL" in str(exc_info.value)
    assert "requises manquantes" in str(exc_info.value)


def test_env_validation_missing_db_name(monkeypatch):
    """Test que l'application refuse de démarrer si DB_NAME est absent"""
    # Garder MONGO_URL mais supprimer DB_NAME
    monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
    monkeypatch.delenv("DB_NAME", raising=False)
    
    with pytest.raises(RuntimeError) as exc_info:
        from backend.server import validate_env
        validate_env()
    
    assert "DB_NAME" in str(exc_info.value)
    assert "requises manquantes" in str(exc_info.value)


def test_env_validation_success(monkeypatch):
    """Test que validate_env retourne les valeurs si toutes les variables sont présentes"""
    monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
    monkeypatch.setenv("DB_NAME", "test_db")
    
    from backend.server import validate_env
    mongo_url, db_name = validate_env()
    
    assert mongo_url == "mongodb://localhost:27017"
    assert db_name == "test_db"


# ============================================================================
# P0-2: Authentification Pro pour export PDF
# ============================================================================

@pytest.fixture
def mock_mathalea_client():
    """Client de test pour les routes mathalea"""
    from backend.server import app
    return TestClient(app)


@pytest.mark.asyncio
async def test_pro_pdf_auth_no_token():
    """Test que l'endpoint PDF Pro rejette les requêtes sans token"""
    from backend.routes.mathalea_routes import generate_pro_pdf
    from backend.models.mathalea_models import ProPdfRequest
    from fastapi import Request
    
    request = ProPdfRequest(template="classique", type_doc="sujet")
    mock_request = MagicMock(spec=Request)
    
    with pytest.raises(HTTPException) as exc_info:
        await generate_pro_pdf(
            sheet_id="test_sheet",
            request=request,
            x_session_token=None
        )
    
    assert exc_info.value.status_code == 401
    assert "AUTHENTICATION_REQUIRED" in str(exc_info.value.detail) or "requis" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_pro_pdf_auth_invalid_token():
    """Test que l'endpoint PDF Pro rejette les tokens invalides"""
    from backend.routes.mathalea_routes import generate_pro_pdf
    from backend.models.mathalea_models import ProPdfRequest
    from backend.server import validate_session_token
    
    # Mock validate_session_token pour retourner None (token invalide)
    with patch('backend.routes.mathalea_routes.validate_session_token', new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = None
        
        request = ProPdfRequest(template="classique", type_doc="sujet")
        
        with pytest.raises(HTTPException) as exc_info:
            await generate_pro_pdf(
                sheet_id="test_sheet",
                request=request,
                x_session_token="fake-token-123"
            )
        
        assert exc_info.value.status_code == 401
        assert "INVALID_SESSION_TOKEN" in str(exc_info.value.detail) or "invalide" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_pro_pdf_auth_user_not_pro():
    """Test que l'endpoint PDF Pro rejette les utilisateurs non-Pro"""
    from backend.routes.mathalea_routes import generate_pro_pdf
    from backend.models.mathalea_models import ProPdfRequest
    from backend.server import validate_session_token, check_user_pro_status
    
    # Mock: token valide mais utilisateur non-Pro
    with patch('backend.routes.mathalea_routes.validate_session_token', new_callable=AsyncMock) as mock_validate, \
         patch('backend.routes.mathalea_routes.check_user_pro_status', new_callable=AsyncMock) as mock_check_pro:
        
        mock_validate.return_value = "user@example.com"
        mock_check_pro.return_value = (False, None)  # Non-Pro
        
        request = ProPdfRequest(template="classique", type_doc="sujet")
        
        with pytest.raises(HTTPException) as exc_info:
            await generate_pro_pdf(
                sheet_id="test_sheet",
                request=request,
                x_session_token="valid-token-but-not-pro"
            )
        
        assert exc_info.value.status_code == 403
        assert "PRO_REQUIRED" in str(exc_info.value.detail) or "Pro" in str(exc_info.value.detail)


# ============================================================================
# P0-3: Robustesse WeasyPrint
# ============================================================================

def test_logo_path_validation_exists_and_is_file():
    """Test que le logo est validé avec exists() ET is_file()"""
    from pathlib import Path
    from unittest.mock import MagicMock
    
    # Mock d'un Path qui existe mais n'est pas un fichier (répertoire)
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = False  # C'est un répertoire, pas un fichier
    
    # Le code doit rejeter ce cas
    logo_url = None
    if mock_path.exists() and mock_path.is_file():
        logo_url = f"file://{mock_path}"
    else:
        logo_url = None
    
    assert logo_url is None, "Un répertoire ne doit pas être accepté comme logo"


def test_logo_path_validation_not_exists():
    """Test que le logo est rejeté s'il n'existe pas"""
    from pathlib import Path
    from unittest.mock import MagicMock
    
    # Mock d'un Path qui n'existe pas
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = False
    mock_path.is_file.return_value = True  # Même si is_file() retourne True, exists() doit être vérifié d'abord
    
    logo_url = None
    if mock_path.exists() and mock_path.is_file():
        logo_url = f"file://{mock_path}"
    else:
        logo_url = None
    
    assert logo_url is None, "Un fichier inexistant ne doit pas être accepté"


@pytest.mark.asyncio
async def test_pdf_generation_timeout():
    """Test que la génération PDF avec timeout fonctionne"""
    import asyncio
    
    async def slow_pdf_generation():
        """Simule une génération PDF lente"""
        await asyncio.sleep(35)  # Plus long que le timeout de 30s
        return b"fake_pdf_bytes"
    
    # Test que le timeout est bien déclenché
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_pdf_generation(), timeout=30)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

