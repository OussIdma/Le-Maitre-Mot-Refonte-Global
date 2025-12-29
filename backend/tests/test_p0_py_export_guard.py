"""
Test P0-STABILITY: Guard pour l'export Python (DEV ONLY)

Vérifie que:
- ENABLE_PY_EXPORT absent/false => _sync_to_python_file() ne fait pas open(...,"w")
- ENABLE_PY_EXPORT=true => le code garde le comportement existant (passe le guard)
"""

import os
import pytest
from unittest.mock import MagicMock, patch, call
from backend.services.exercise_persistence_service import (
    ExercisePersistenceService,
    ENABLE_PY_EXPORT
)


class TestPyExportGuard:
    """Tests pour le guard d'export Python"""
    
    def test_enable_py_export_default_false(self):
        """Vérifie que ENABLE_PY_EXPORT est False par défaut"""
        # Le flag doit être False si la variable d'environnement n'est pas définie
        # (on teste la valeur par défaut, pas la valeur actuelle qui peut être modifiée)
        with patch.dict(os.environ, {}, clear=True):
            # Recharger le module pour réinitialiser la constante
            import importlib
            import backend.services.exercise_persistence_service as module
            importlib.reload(module)
            assert module.ENABLE_PY_EXPORT is False
    
    @pytest.mark.asyncio
    async def test_sync_to_python_file_guard_disabled(self):
        """Vérifie que _sync_to_python_file() ne fait rien si ENABLE_PY_EXPORT=false"""
        # Mock de la DB (subscriptable pour db[collection])
        fake_db = MagicMock()
        fake_db.__getitem__.return_value = MagicMock()
        service = ExercisePersistenceService(fake_db)
        
        # Mock get_exercises pour éviter les appels MongoDB
        service.get_exercises = MagicMock(return_value=[])
        
        # Mock open() pour vérifier qu'il n'est pas appelé
        with patch('builtins.open', side_effect=Exception("open() ne devrait pas être appelé")) as mock_open:
            with patch.dict(os.environ, {'ENABLE_PY_EXPORT': 'false'}, clear=False):
                # Recharger le module pour réinitialiser la constante
                import importlib
                import backend.services.exercise_persistence_service as module
                importlib.reload(module)
                service._sync_to_python_file = module.ExercisePersistenceService._sync_to_python_file.__get__(service, ExercisePersistenceService)
                
                # Appeler la fonction
                await service._sync_to_python_file("6E_GM07")
                
                # Vérifier que open() n'a pas été appelé
                mock_open.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_sync_to_python_file_guard_enabled(self):
        """Vérifie que _sync_to_python_file() passe le guard si ENABLE_PY_EXPORT=true"""
        # Mock de la DB (subscriptable pour db[collection])
        fake_db = MagicMock()
        fake_db.__getitem__.return_value = MagicMock()
        service = ExercisePersistenceService(fake_db)
        
        # Mock get_exercises pour retourner des exercices vides (async)
        async def mock_get_exercises(*args, **kwargs):
            return []
        service.get_exercises = mock_get_exercises
        
        # Mock open() pour vérifier qu'il est appelé
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=None)
        mock_file.write = MagicMock()
        
        with patch('builtins.open', return_value=mock_file) as mock_open:
            with patch.dict(os.environ, {'ENABLE_PY_EXPORT': 'true'}, clear=False):
                # Recharger le module pour réinitialiser la constante
                import importlib
                import backend.services.exercise_persistence_service as module
                importlib.reload(module)
                service._sync_to_python_file = module.ExercisePersistenceService._sync_to_python_file.__get__(service, ExercisePersistenceService)
                
                # Appeler la fonction
                await service._sync_to_python_file("6E_GM07")
                
                # Vérifier que open() a été appelé (le guard est passé)
                # Note: on vérifie juste que le guard passe, pas l'écriture complète
                mock_open.assert_called()
    
    def test_reload_handler_guard_disabled(self):
        """Vérifie que _reload_handler() ne fait rien si ENABLE_PY_EXPORT=false"""
        # Mock de la DB (subscriptable pour db[collection])
        fake_db = MagicMock()
        fake_db.__getitem__.return_value = MagicMock()
        service = ExercisePersistenceService(fake_db)
        
        with patch.dict(os.environ, {'ENABLE_PY_EXPORT': 'false'}, clear=False):
            # Recharger le module pour réinitialiser la constante
            import importlib
            import backend.services.exercise_persistence_service as module
            importlib.reload(module)
            service._reload_handler = module.ExercisePersistenceService._reload_handler.__get__(service, ExercisePersistenceService)
            
            # Mock importlib.reload() pour vérifier qu'il n'est pas appelé
            # (on patch importlib.reload directement car il est importé dans la fonction)
            with patch('importlib.reload', side_effect=Exception("reload() ne devrait pas être appelé")) as mock_reload:
                # Appeler la fonction
                service._reload_handler("6E_GM07")
                
                # Vérifier que reload() n'a pas été appelé
                mock_reload.assert_not_called()
    
    def test_reload_handler_is_sync(self):
        """Vérifie que _reload_handler() est synchrone (pas async)"""
        import inspect
        from backend.services.exercise_persistence_service import ExercisePersistenceService
        
        # Vérifier que la méthode n'est pas async
        assert not inspect.iscoroutinefunction(ExercisePersistenceService._reload_handler)
        
        # Vérifier qu'on peut l'appeler sans await
        # Mock de la DB (subscriptable pour db[collection])
        fake_db = MagicMock()
        fake_db.__getitem__.return_value = MagicMock()
        service = ExercisePersistenceService(fake_db)
        
        # Ne devrait pas lever d'erreur (fonction synchrone)
        with patch.dict(os.environ, {'ENABLE_PY_EXPORT': 'false'}, clear=False):
            service._reload_handler("6E_GM07")  # Pas d'await nécessaire

