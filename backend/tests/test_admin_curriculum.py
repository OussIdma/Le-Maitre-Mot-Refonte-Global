"""
Tests pour l'endpoint admin de gestion du curriculum (P1.2)

Test de l'ajout/retrait de générateurs à un chapitre via l'API admin.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
import json
import shutil
from pathlib import Path

client = TestClient(app)

# Chemin curriculum test
CURRICULUM_DIR = Path(__file__).parent.parent / "curriculum"
TEST_CURRICULUM_FILE = CURRICULUM_DIR / "curriculum_6e.json"


@pytest.fixture
def backup_curriculum():
    """Créer un backup du curriculum avant chaque test."""
    backup_path = TEST_CURRICULUM_FILE.with_suffix('.json.test_backup')
    
    # Backup
    if TEST_CURRICULUM_FILE.exists():
        shutil.copy(TEST_CURRICULUM_FILE, backup_path)
    
    yield
    
    # Restore
    if backup_path.exists():
        shutil.copy(backup_path, TEST_CURRICULUM_FILE)
        backup_path.unlink()


class TestAdminCurriculumEndpoints:
    """Tests pour les endpoints admin curriculum."""
    
    def test_get_generators_with_metadata(self):
        """Vérifier que /generators retourne is_dynamic, supported_grades."""
        response = client.get("/api/v1/exercises/generators")
        assert response.status_code == 200
        
        data = response.json()
        assert "generators" in data
        assert len(data["generators"]) > 0
        
        # Vérifier qu'au moins un générateur a les nouvelles métadonnées
        gen = data["generators"][0]
        assert "key" in gen
        assert "is_dynamic" in gen
        assert "supported_grades" in gen
        assert isinstance(gen["is_dynamic"], bool)
        assert isinstance(gen["supported_grades"], list)
    
    def test_get_chapter_exercise_types(self):
        """Vérifier GET /admin/curriculum/chapters/{code}/exercise-types."""
        response = client.get("/api/v1/admin/curriculum/chapters/6e_SP03/exercise-types")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "code_officiel" in data
        assert data["code_officiel"] == "6e_SP03"
        assert "exercise_types" in data
        assert isinstance(data["exercise_types"], list)
        
        # Vérifier la structure enrichie
        if len(data["exercise_types"]) > 0:
            ex_type = data["exercise_types"][0]
            assert "key" in ex_type
            assert "label" in ex_type
            assert "is_dynamic" in ex_type
            assert "supported_grades" in ex_type
            assert "exists" in ex_type
    
    def test_add_generator_to_chapter_idempotent(self, backup_curriculum):
        """
        Vérifier que POST /admin/curriculum/chapters/{code}/exercise-types
        est idempotent (ajouter 2x le même générateur ne doit pas le dupliquer).
        """
        code_officiel = "6e_SP03"
        generator_key = "CALCUL_NOMBRES_V1"
        
        # Premier ajout
        response1 = client.post(
            f"/api/v1/admin/curriculum/chapters/{code_officiel}/exercise-types",
            json={"add": [generator_key]}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["modified"] is True
        assert generator_key in data1["added"]
        
        # Deuxième ajout (idempotent)
        response2 = client.post(
            f"/api/v1/admin/curriculum/chapters/{code_officiel}/exercise-types",
            json={"add": [generator_key]}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["modified"] is False  # Pas modifié car déjà présent
        assert len(data2["added"]) == 0  # Rien ajouté
        
        # Vérifier que le générateur n'est présent qu'une seule fois
        current_types = data2["current_exercise_types"]
        count = current_types.count(generator_key)
        assert count == 1, f"{generator_key} présent {count} fois (attendu: 1)"
    
    def test_remove_generator_from_chapter_idempotent(self, backup_curriculum):
        """
        Vérifier que remove est idempotent.
        """
        code_officiel = "6e_SP03"
        generator_key = "CALCUL_NOMBRES_V1"
        
        # Ajouter d'abord
        client.post(
            f"/api/v1/admin/curriculum/chapters/{code_officiel}/exercise-types",
            json={"add": [generator_key]}
        )
        
        # Premier retrait
        response1 = client.post(
            f"/api/v1/admin/curriculum/chapters/{code_officiel}/exercise-types",
            json={"remove": [generator_key]}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["modified"] is True
        assert generator_key in data1["removed"]
        
        # Deuxième retrait (idempotent)
        response2 = client.post(
            f"/api/v1/admin/curriculum/chapters/{code_officiel}/exercise-types",
            json={"remove": [generator_key]}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["modified"] is False  # Pas modifié car déjà retiré
        assert len(data2["removed"]) == 0  # Rien retiré
    
    def test_add_unknown_generator_key(self, backup_curriculum):
        """
        Vérifier que l'ajout d'un générateur inconnu retourne 422.
        """
        code_officiel = "6e_SP03"
        unknown_key = "GENERATEUR_INEXISTANT_XYZ"
        
        response = client.post(
            f"/api/v1/admin/curriculum/chapters/{code_officiel}/exercise-types",
            json={"add": [unknown_key]}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "error_code" in data["detail"]
        assert data["detail"]["error_code"] == "UNKNOWN_GENERATOR_KEYS"
        assert unknown_key in data["detail"]["unknown_keys"]
    
    def test_add_and_remove_together(self, backup_curriculum):
        """
        Vérifier qu'on peut ajouter et retirer des générateurs en même temps.
        """
        code_officiel = "6e_SP03"
        
        response = client.post(
            f"/api/v1/admin/curriculum/chapters/{code_officiel}/exercise-types",
            json={
                "add": ["CALCUL_NOMBRES_V1"],
                "remove": ["RAISONNEMENT_MULTIPLICATIF_V1"]  # Si présent
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier la structure
        assert "modified" in data
        assert "added" in data
        assert "removed" in data
        assert "current_exercise_types" in data
    
    def test_chapter_not_found(self):
        """Vérifier que 404 si chapitre introuvable."""
        code_officiel = "6e_INEXISTANT_XYZ"
        
        response = client.post(
            f"/api/v1/admin/curriculum/chapters/{code_officiel}/exercise-types",
            json={"add": ["CALCUL_NOMBRES_V1"]}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error_code" in data["detail"]
        assert data["detail"]["error_code"] == "CHAPTER_NOT_FOUND"
    
    def test_backup_created_on_modification(self, backup_curriculum):
        """Vérifier qu'un backup est créé lors de la modification."""
        code_officiel = "6e_SP03"
        
        # Supprimer le backup s'il existe
        backup_path = TEST_CURRICULUM_FILE.with_suffix('.json.bak')
        if backup_path.exists():
            backup_path.unlink()
        
        # Ajouter un générateur
        response = client.post(
            f"/api/v1/admin/curriculum/chapters/{code_officiel}/exercise-types",
            json={"add": ["CALCUL_NOMBRES_V1"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier que le backup_path est retourné
        assert "backup_path" in data
        
        # Vérifier que le fichier backup existe
        backup_path_returned = Path(data["backup_path"])
        assert backup_path_returned.exists(), f"Backup {backup_path_returned} n'existe pas"
        
        # Cleanup
        if backup_path_returned.exists():
            backup_path_returned.unlink()
