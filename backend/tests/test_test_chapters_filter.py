"""
Tests pour le filtrage des chapitres de test.
"""

import pytest
import os
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Client de test FastAPI"""
    from backend.server import app
    return TestClient(app)


def test_is_test_chapter():
    """Test que is_test_chapter détecte correctement les chapitres de test."""
    from curriculum.loader import is_test_chapter
    
    # Chapitres de test
    assert is_test_chapter("6e_AA_TEST") == True
    assert is_test_chapter("6e_TESTS_DYN") == True
    assert is_test_chapter("6e_MIXED_QA") == True
    assert is_test_chapter("6e_AA_TEST_STAT") == True
    
    # Chapitres normaux
    assert is_test_chapter("6e_N08") == False
    assert is_test_chapter("6e_GM07") == False
    assert is_test_chapter("6e_G01") == False
    
    # Cas limites
    assert is_test_chapter("") == False
    assert is_test_chapter(None) == False


def test_should_show_test_chapters():
    """Test que should_show_test_chapters respecte la variable d'environnement."""
    from curriculum.loader import should_show_test_chapters
    
    # Par défaut, ne pas afficher
    with patch.dict(os.environ, {}, clear=True):
        assert should_show_test_chapters() == False
    
    # Avec SHOW_TEST_CHAPTERS=false
    with patch.dict(os.environ, {"SHOW_TEST_CHAPTERS": "false"}, clear=True):
        assert should_show_test_chapters() == False
    
    # Avec SHOW_TEST_CHAPTERS=true
    with patch.dict(os.environ, {"SHOW_TEST_CHAPTERS": "true"}, clear=True):
        assert should_show_test_chapters() == True
    
    # Avec SHOW_TEST_CHAPTERS=TRUE (insensible à la casse)
    with patch.dict(os.environ, {"SHOW_TEST_CHAPTERS": "TRUE"}, clear=True):
        assert should_show_test_chapters() == True


@pytest.mark.asyncio
async def test_catalog_excludes_test_chapters_by_default():
    """Test que le catalogue exclut les chapitres de test par défaut."""
    from curriculum.loader import get_catalog
    
    with patch.dict(os.environ, {}, clear=True):
        catalog = await get_catalog("6e", db=None)
        
        # Vérifier qu'aucun chapitre de test n'est présent
        for domain in catalog.get("domains", []):
            for chapter in domain.get("chapters", []):
                code = chapter.get("code_officiel", "")
                assert "TEST" not in code.upper() and "QA" not in code.upper(), \
                    f"Chapitre de test trouvé dans le catalogue: {code}"
        
        # Vérifier qu'aucun macro group ne contient de codes de test
        for mg in catalog.get("macro_groups", []):
            codes = mg.get("codes_officiels", [])
            for code in codes:
                assert "TEST" not in code.upper() and "QA" not in code.upper(), \
                    f"Code de test trouvé dans macro group: {code}"


@pytest.mark.asyncio
async def test_catalog_includes_test_chapters_in_dev_mode():
    """Test que le catalogue inclut les chapitres de test en mode dev."""
    from curriculum.loader import get_catalog
    
    with patch.dict(os.environ, {"SHOW_TEST_CHAPTERS": "true"}, clear=True):
        catalog = await get_catalog("6e", db=None)
        
        # Vérifier qu'au moins un chapitre de test est présent
        test_chapters_found = []
        for domain in catalog.get("domains", []):
            for chapter in domain.get("chapters", []):
                code = chapter.get("code_officiel", "")
                if "TEST" in code.upper() or "QA" in code.upper():
                    test_chapters_found.append(code)
        
        assert len(test_chapters_found) > 0, \
            "Aucun chapitre de test trouvé en mode dev (SHOW_TEST_CHAPTERS=true)"


@pytest.mark.asyncio
async def test_generate_exercise_rejects_test_chapter_in_public_mode(client):
    """Test que la génération rejette un chapitre de test en mode public."""
    with patch.dict(os.environ, {}, clear=True):
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_AA_TEST",
                "difficulte": "facile",
                "offer": "free",
                "seed": 42
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        detail = data.get("detail", {})
        assert detail.get("error_code") == "TEST_CHAPTER_FORBIDDEN"
        assert "test_chapter_forbidden" in detail.get("error", "")
        assert "chapitre de test" in detail.get("message", "").lower()


@pytest.mark.asyncio
async def test_generate_exercise_allows_test_chapter_in_dev_mode(client):
    """Test que la génération accepte un chapitre de test en mode dev."""
    with patch.dict(os.environ, {"SHOW_TEST_CHAPTERS": "true"}, clear=True):
        # Note: Ce test peut échouer si aucun exercice n'existe pour 6e_AA_TEST
        # Dans ce cas, on s'attend à un 422 POOL_EMPTY, pas TEST_CHAPTER_FORBIDDEN
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_AA_TEST",
                "difficulte": "facile",
                "offer": "free",
                "seed": 42
            }
        )
        
        # Ne doit pas être TEST_CHAPTER_FORBIDDEN
        if response.status_code == 422:
            data = response.json()
            detail = data.get("detail", {})
            error_code = detail.get("error_code") if isinstance(detail, dict) else None
            assert error_code != "TEST_CHAPTER_FORBIDDEN", \
                "Chapitre de test rejeté même en mode dev"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

