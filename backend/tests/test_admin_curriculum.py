"""
Tests pour les endpoints admin curriculum.

Tests READ-ONLY pour valider les endpoints de visualisation du référentiel.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient


class TestAdminCurriculumEndpoints:
    """Tests pour les endpoints admin curriculum"""
    
    @pytest.fixture
    def client(self):
        """Créer un client de test"""
        # Set ADMIN_ENABLED before importing
        os.environ["ADMIN_ENABLED"] = "true"
        
        from server import app
        return TestClient(app)
    
    def test_get_curriculum_6e(self, client):
        """Test GET /api/admin/curriculum/6e"""
        response = client.get("/api/admin/curriculum/6e")
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier la structure
        assert "niveau" in data
        assert data["niveau"] == "6e"
        assert "chapitres" in data
        assert "total_chapitres" in data
        assert "stats" in data
        
        # Vérifier le nombre de chapitres
        assert data["total_chapitres"] == 27
        assert len(data["chapitres"]) == 27
    
    def test_curriculum_6e_chapter_structure(self, client):
        """Test que chaque chapitre a la bonne structure"""
        response = client.get("/api/admin/curriculum/6e")
        data = response.json()
        
        required_fields = [
            "code_officiel", "domaine", "libelle", "generateurs",
            "has_diagramme", "statut", "chapitre_backend"
        ]
        
        for chapter in data["chapitres"]:
            for field in required_fields:
                assert field in chapter, f"Champ {field} manquant dans {chapter.get('code_officiel', 'inconnu')}"
    
    def test_curriculum_6e_codes_format(self, client):
        """Test que les codes suivent le bon format"""
        import re
        
        response = client.get("/api/admin/curriculum/6e")
        data = response.json()
        
        pattern = r"^6e_(N|G|GM|SP)\d{2}$"
        
        for chapter in data["chapitres"]:
            code = chapter["code_officiel"]
            assert re.match(pattern, code), f"Code {code} ne suit pas le pattern attendu"
    
    def test_curriculum_6e_domaines(self, client):
        """Test que les domaines sont valides"""
        response = client.get("/api/admin/curriculum/6e")
        data = response.json()
        
        valid_domaines = [
            "Nombres et calculs",
            "Géométrie",
            "Grandeurs et mesures",
            "Organisation et gestion de données"
        ]
        
        for chapter in data["chapitres"]:
            assert chapter["domaine"] in valid_domaines, \
                f"Domaine invalide: {chapter['domaine']}"
    
    def test_curriculum_6e_stats(self, client):
        """Test les statistiques retournées"""
        response = client.get("/api/admin/curriculum/6e")
        data = response.json()
        
        stats = data["stats"]
        
        assert "total" in stats
        assert stats["total"] == 27
        assert "by_domaine" in stats
        assert "by_status" in stats
        
        # Vérifier que la somme des domaines = total
        total_by_domaine = sum(stats["by_domaine"].values())
        assert total_by_domaine == 27
    
    def test_get_chapter_by_code(self, client):
        """Test GET /api/admin/curriculum/6e/{code}"""
        response = client.get("/api/admin/curriculum/6e/6e_N08")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code_officiel"] == "6e_N08"
        assert "Fractions" in data["libelle"]
        assert len(data["generateurs"]) > 0
    
    def test_get_chapter_invalid_code(self, client):
        """Test qu'un code invalide retourne 404"""
        response = client.get("/api/admin/curriculum/6e/INVALID_CODE")
        
        assert response.status_code == 404
    
    def test_validate_curriculum_6e(self, client):
        """Test GET /api/admin/curriculum/6e/validate"""
        response = client.get("/api/admin/curriculum/6e/validate")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "valid" in data
        assert "total_chapters" in data
        assert data["total_chapters"] == 27
        assert "chapters_with_generators" in data
        assert data["chapters_with_generators"] > 0
    
    def test_curriculum_stats(self, client):
        """Test GET /api/admin/curriculum/stats"""
        response = client.get("/api/admin/curriculum/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "niveaux_disponibles" in data
        assert "6e" in data["niveaux_disponibles"]
        assert "total_chapitres_6e" in data


class TestAdminCurriculumSecurity:
    """Tests de sécurité pour l'admin"""
    
    def test_admin_disabled(self):
        """Test que l'admin peut être désactivé"""
        # Sauvegarder la valeur actuelle
        old_value = os.environ.get("ADMIN_ENABLED")
        
        try:
            # Désactiver l'admin
            os.environ["ADMIN_ENABLED"] = "false"
            
            # Réimporter pour prendre en compte le changement
            from server import app
            client = TestClient(app)
            
            response = client.get("/api/admin/curriculum/6e")
            
            # Devrait retourner 403 Forbidden
            assert response.status_code == 403
            
        finally:
            # Restaurer la valeur
            if old_value:
                os.environ["ADMIN_ENABLED"] = old_value
            else:
                os.environ["ADMIN_ENABLED"] = "true"


class TestNonRegression:
    """Tests de non-régression pour les endpoints existants"""
    
    @pytest.fixture
    def client(self):
        """Créer un client de test"""
        os.environ["ADMIN_ENABLED"] = "true"
        from server import app
        return TestClient(app)
    
    def test_generate_endpoint_still_works(self, client):
        """Test que /api/v1/exercises/generate fonctionne toujours"""
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "niveau": "6e",
                "chapitre": "Fractions",
                "difficulte": "moyen"
            },
            headers={"X-Session-Token": "test@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "enonce_html" in data
    
    def test_generate_with_code_officiel_still_works(self, client):
        """Test que le mode code_officiel fonctionne toujours"""
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_N08",
                "difficulte": "moyen"
            },
            headers={"X-Session-Token": "test@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "enonce_html" in data
        assert data["chapitre"] == "Fractions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
