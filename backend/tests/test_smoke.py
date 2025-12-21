"""
Smoke test simple pour vérifier que l'environnement de test fonctionne
Ne dépend d'aucune fixture externe (DB, services, etc.)
"""

import pytest
import sys
from pathlib import Path


def test_imports():
    """Test que les imports de base fonctionnent"""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_pythonpath():
    """Test que PYTHONPATH est correctement configuré"""
    import sys
    assert "/app" in sys.path or str(Path("/app").resolve()) in [str(Path(p).resolve()) for p in sys.path]


def test_backend_module_import():
    """Test que le module backend est importable"""
    try:
        import backend
        assert backend is not None
    except ImportError as e:
        pytest.fail(f"Backend module import failed: {e}")


def test_validate_env_function():
    """Test que validate_env existe et est callable"""
    try:
        from backend.server import validate_env
        assert callable(validate_env)
    except ImportError as e:
        pytest.fail(f"validate_env import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

