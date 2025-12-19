"""
Tests pour l'API Exercises v1
Endpoint: POST /api/v1/exercises/generate
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Ajouter le dossier backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server import app

client = TestClient(app)


class TestExercisesAPIGenerate:
    """Tests pour l'endpoint POST /api/v1/exercises/generate"""
    
    def test_generate_exercise_success_geometry(self):
        """
        Test nominal : génération d'un exercice de géométrie (5e - Symétrie axiale)
        Vérifie que tous les champs requis sont présents et que le SVG est généré
        """
        # Arrange
        request_data = {
            "niveau": "5e",
            "chapitre": "Symétrie centrale",
            "type_exercice": "standard",
            "difficulte": "moyen"
        }
        
        # Act
        response = client.post("/api/v1/exercises/generate", json=request_data)
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Vérifier les champs obligatoires
        assert "id_exercice" in data
        assert "niveau" in data
        assert "chapitre" in data
        assert "enonce_html" in data
        assert "solution_html" in data
        assert "pdf_token" in data
        assert "metadata" in data
        
        # Vérifier les valeurs
        assert data["niveau"] == "5e"
        assert data["chapitre"] == "Symétrie centrale"
        assert data["pdf_token"] == data["id_exercice"]  # v1: pdf_token = id_exercice
        
        # Vérifier l'énoncé HTML
        assert "<" in data["enonce_html"]  # Contient du HTML
        assert len(data["enonce_html"]) > 10
        
        # Vérifier la solution HTML
        assert "<" in data["solution_html"]
        assert "Solution" in data["solution_html"] or "solution" in data["solution_html"]
        
        # Vérifier les métadonnées
        assert data["metadata"]["type_exercice"] == "standard"
        assert data["metadata"]["difficulte"] == "moyen"
        assert "duree_estimee" in data["metadata"]
        assert "points" in data["metadata"]
        
        # Pour un exercice de géométrie, vérifier le SVG
        # Note: Le SVG peut être None si pas de figure, mais pour symétrie centrale il devrait y en avoir
        if data.get("svg"):
            assert "<svg" in data["svg"]
            assert len(data["svg"]) > 100
        
        print(f"✅ Exercice généré: id={data['id_exercice']}, has_svg={data.get('svg') is not None}")
    
    def test_generate_exercise_success_calculation(self):
        """
        Test nominal : génération d'un exercice de calcul (6e - Fractions)
        Vérifie que l'énoncé HTML est bien construit
        """
        # Arrange
        request_data = {
            "niveau": "6e",
            "chapitre": "Fractions",
            "difficulte": "facile"
        }
        
        # Act
        response = client.post("/api/v1/exercises/generate", json=request_data)
        
        # Assert
        assert response.status_code == 200
        
        data = response.json()
        
        # Vérifier les champs
        assert data["niveau"] == "6e"
        assert data["chapitre"] == "Fractions"
        
        # L'énoncé doit contenir du HTML
        assert "<" in data["enonce_html"]
        assert ">" in data["enonce_html"]
        
        # La solution doit être présente
        assert len(data["solution_html"]) > 20
        
        print(f"✅ Exercice de calcul généré: {data['id_exercice']}")
    
    def test_generate_exercise_invalid_niveau(self):
        """
        Test erreur : niveau invalide
        Vérifie que l'API retourne 422 avec un message pédagogique et la liste des niveaux
        """
        # Arrange
        request_data = {
            "niveau": "5eme",  # Invalide (devrait être "5e")
            "chapitre": "Symétrie centrale"
        }
        
        # Act
        response = client.post("/api/v1/exercises/generate", json=request_data)
        
        # Assert
        assert response.status_code == 422
        
        error = response.json()
        assert "detail" in error
        
        detail = error["detail"]
        assert "error" in detail
        assert detail["error"] == "niveau_invalide"
        
        # Vérifier le message pédagogique
        assert "message" in detail
        assert "5eme" in detail["message"]
        assert "Niveaux disponibles" in detail["message"] or "disponibles" in detail["message"]
        
        # Vérifier la liste des niveaux disponibles
        assert "niveaux_disponibles" in detail
        assert isinstance(detail["niveaux_disponibles"], list)
        assert len(detail["niveaux_disponibles"]) > 0
        assert "5e" in detail["niveaux_disponibles"]
        assert "CP" in detail["niveaux_disponibles"]
        
        print(f"✅ Erreur niveau invalide correctement gérée: {detail['message'][:80]}...")
    
    def test_generate_exercise_invalid_chapitre(self):
        """
        Test erreur : chapitre invalide pour un niveau donné
        Vérifie que l'API retourne 422 avec la liste des chapitres disponibles
        """
        # Arrange
        request_data = {
            "niveau": "5e",
            "chapitre": "Géométrie spatiale avancée"  # Chapitre qui n'existe probablement pas
        }
        
        # Act
        response = client.post("/api/v1/exercises/generate", json=request_data)
        
        # Assert
        assert response.status_code == 422
        
        error = response.json()
        detail = error["detail"]
        
        assert detail["error"] == "chapitre_invalide"
        
        # Vérifier le message
        assert "message" in detail
        assert "5e" in detail["message"]
        assert "Géométrie spatiale avancée" in detail["message"]
        
        # Vérifier les champs supplémentaires
        assert "niveau" in detail
        assert detail["niveau"] == "5e"
        
        assert "chapitres_disponibles" in detail
        assert isinstance(detail["chapitres_disponibles"], list)
        assert len(detail["chapitres_disponibles"]) > 0
        
        print(f"✅ Erreur chapitre invalide: {len(detail['chapitres_disponibles'])} chapitres disponibles pour 5e")
    
    def test_generate_exercise_with_difficulty_levels(self):
        """
        Test : génération avec différents niveaux de difficulté
        Vérifie que le paramètre difficulté est bien pris en compte
        """
        difficultes = ["facile", "moyen", "difficile"]
        
        for difficulte in difficultes:
            # Arrange
            request_data = {
                "niveau": "6e",
                "chapitre": "Fractions",
                "difficulte": difficulte
            }
            
            # Act
            response = client.post("/api/v1/exercises/generate", json=request_data)
            
            # Assert
            assert response.status_code == 200, f"Failed for difficulte={difficulte}"
            
            data = response.json()
            assert data["metadata"]["difficulte"] == difficulte
            
            print(f"✅ Exercice généré avec difficulté: {difficulte}")
    
    def test_pdf_token_format(self):
        """
        Test : vérification du format du pdf_token
        Pour la v1, pdf_token doit être égal à id_exercice
        """
        # Arrange
        request_data = {
            "niveau": "5e",
            "chapitre": "Symétrie centrale"
        }
        
        # Act
        response = client.post("/api/v1/exercises/generate", json=request_data)
        
        # Assert
        assert response.status_code == 200
        
        data = response.json()
        
        # Vérifier que pdf_token = id_exercice (comportement v1)
        assert data["pdf_token"] == data["id_exercice"]
        
        # Vérifier le format de l'id
        assert data["id_exercice"].startswith("ex_")
        assert "5e" in data["id_exercice"]
        
        print(f"✅ Format pdf_token vérifié: {data['pdf_token']}")
    
    def test_health_endpoint(self):
        """
        Test : endpoint de santé /api/v1/exercises/health
        Vérifie que le service est opérationnel
        """
        # Act
        response = client.get("/api/v1/exercises/health")
        
        # Assert
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "exercises_v1"
        assert "curriculum" in data
        
        curriculum_info = data["curriculum"]
        assert "total_niveaux" in curriculum_info
        assert "niveaux" in curriculum_info
        assert "total_chapitres" in curriculum_info
        
        print(f"✅ Health check OK: {curriculum_info['total_niveaux']} niveaux, {curriculum_info['total_chapitres']} chapitres")


class TestExercisesAPIRobustness:
    """Tests de robustesse et de régression"""
    
    def test_svg_regression_geometry_chapters(self):
        """
        Test de régression : chapitres géométriques doivent générer un SVG
        V1-BE-002-FIX: S'assurer que les chapitres géométriques génèrent bien un SVG non vide
        """
        # Liste de chapitres géométriques connus pour avoir des figures
        geometry_chapters = [
            {"niveau": "5e", "chapitre": "Symétrie centrale"},
            {"niveau": "6e", "chapitre": "Symétrie axiale"},
            {"niveau": "5e", "chapitre": "Triangles"},
        ]
        
        for test_case in geometry_chapters:
            # Arrange
            request_data = {
                "niveau": test_case["niveau"],
                "chapitre": test_case["chapitre"],
                "difficulte": "moyen"
            }
            
            # Act
            response = client.post("/api/v1/exercises/generate", json=request_data)
            
            # Assert
            assert response.status_code == 200, \
                f"Failed for {test_case['niveau']} - {test_case['chapitre']}: {response.text}"
            
            data = response.json()
            
            # Vérifier que le SVG est présent et non vide
            assert data.get("svg") is not None, \
                f"SVG is None for geometry chapter: {test_case['chapitre']}"
            
            assert len(data["svg"]) > 0, \
                f"SVG is empty for geometry chapter: {test_case['chapitre']}"
            
            assert "<svg" in data["svg"], \
                f"SVG doesn't contain <svg tag for: {test_case['chapitre']}"
            
            print(f"✅ SVG regression OK: {test_case['niveau']} - {test_case['chapitre']} ({len(data['svg'])} chars)")


class TestExercisesAPIValidation:
    """Tests supplémentaires pour la validation Pydantic"""
    
    def test_invalid_difficulte_value(self):
        """
        Test : valeur invalide pour le paramètre difficulte
        Devrait être rejeté par Pydantic avant même d'atteindre la route
        """
        # Arrange
        request_data = {
            "niveau": "5e",
            "chapitre": "Symétrie axiale",
            "difficulte": "tres_facile"  # Invalide
        }
        
        # Act
        response = client.post("/api/v1/exercises/generate", json=request_data)
        
        # Assert
        assert response.status_code == 422  # Erreur de validation Pydantic
        
        error = response.json()
        assert "detail" in error
        
        print(f"✅ Validation Pydantic: difficulté invalide rejetée")
    
    def test_missing_required_fields(self):
        """
        Test : champs obligatoires manquants (niveau, chapitre)
        """
        # Arrange - niveau manquant
        request_data = {
            "chapitre": "Symétrie axiale"
        }
        
        # Act
        response = client.post("/api/v1/exercises/generate", json=request_data)
        
        # Assert
        assert response.status_code == 422
        
        print(f"✅ Validation: champ obligatoire 'niveau' manquant détecté")


# Fonction pour exécuter les tests manuellement
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
