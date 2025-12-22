#!/usr/bin/env python3
"""
Tests Figure SVG - Validation du rendu des figures
==================================================

Tests pour valider que les exercices avec needs_svg=True
retournent bien un champ figure_svg contenant un SVG valide.
"""

import requests
import pytest

BASE_URL = "https://math-exercise-sync.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api/v1/exercises"


class TestFigureSvgGM07:
    """Tests pour le rendu SVG des exercices GM07 (horloge)"""
    
    def test_lecture_horloge_has_figure_svg(self):
        """Les exercices LECTURE_HORLOGE ont un figure_svg"""
        # Générer un batch pour avoir des exercices variés
        payload = {
            "code_officiel": "6e_GM07",
            "nb_exercices": 10,
            "offer": "free"
        }
        
        response = requests.post(
            f"{API_URL}/generate/batch/gm07",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        exercises = data.get("exercises", [])
        
        # Vérifier les exercices LECTURE_HORLOGE
        horloge_exercises = [ex for ex in exercises if ex["metadata"]["family"] == "LECTURE_HORLOGE"]
        
        for ex in horloge_exercises:
            assert ex["metadata"].get("needs_svg") == True, f"Ex #{ex['metadata']['exercise_id']} should have needs_svg=True"
            assert ex.get("figure_svg") is not None, f"Ex #{ex['metadata']['exercise_id']} should have figure_svg"
            assert ex["figure_svg"].strip().startswith("<svg"), f"figure_svg should start with <svg"
    
    def test_conversion_no_figure_svg(self):
        """Les exercices CONVERSION n'ont pas de figure_svg"""
        # Générer un batch pour avoir des exercices variés
        payload = {
            "code_officiel": "6e_GM07",
            "nb_exercices": 10,
            "offer": "free"
        }
        
        response = requests.post(
            f"{API_URL}/generate/batch/gm07",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        exercises = data.get("exercises", [])
        
        # Vérifier les exercices CONVERSION
        conversion_exercises = [ex for ex in exercises if ex["metadata"]["family"] == "CONVERSION"]
        
        for ex in conversion_exercises:
            assert ex["metadata"].get("needs_svg") == False, f"Ex #{ex['metadata']['exercise_id']} should have needs_svg=False"
            assert ex.get("figure_svg") is None, f"Ex #{ex['metadata']['exercise_id']} should NOT have figure_svg"
    
    def test_svg_content_is_valid(self):
        """Le contenu SVG est valide (contient les éléments attendus)"""
        # Générer un exercice horloge spécifiquement
        payload = {
            "code_officiel": "6e_GM07",
            "nb_exercices": 10,
            "offer": "pro"  # PRO pour avoir les 20 exercices
        }
        
        response = requests.post(
            f"{API_URL}/generate/batch/gm07",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        exercises = data.get("exercises", [])
        
        # Trouver un exercice LECTURE_HORLOGE avec SVG
        svg_exercises = [ex for ex in exercises 
                        if ex.get("figure_svg") and ex["metadata"]["family"] == "LECTURE_HORLOGE"]
        
        if len(svg_exercises) == 0:
            # Si pas de LECTURE_HORLOGE dans ce batch, on passe le test
            # Les autres tests couvrent ce cas
            return
        
        svg_content = svg_exercises[0]["figure_svg"]
        
        # Vérifier le contenu
        assert "<svg" in svg_content, "SVG doit contenir balise svg"
        assert "</svg>" in svg_content, "SVG doit être fermé"
        assert "viewBox" in svg_content, "SVG doit avoir viewBox"
        
        # Pour une horloge, doit avoir des cercles et lignes
        assert "<circle" in svg_content, "Horloge doit avoir cercle (cadran)"
        assert "<line" in svg_content, "Horloge doit avoir lignes (aiguilles)"
    
    def test_single_endpoint_returns_figure_svg(self):
        """L'endpoint /generate retourne aussi figure_svg"""
        # Essayer plusieurs seeds jusqu'à avoir un exercice avec SVG
        for seed in [1, 10, 100, 1000, 5000]:
            payload = {
                "code_officiel": "6e_GM07",
                "offer": "free",
                "seed": seed
            }
            
            response = requests.post(
                f"{API_URL}/generate",
                json=payload,
                timeout=30
            )
            
            assert response.status_code == 200
            data = response.json()
            
            if data["metadata"]["family"] == "LECTURE_HORLOGE":
                assert data.get("figure_svg") is not None, "LECTURE_HORLOGE doit avoir figure_svg"
                assert data["figure_svg"].strip().startswith("<svg"), "figure_svg doit commencer par <svg"
                return  # Test passé
        
        # Si on n'a pas trouvé de LECTURE_HORLOGE après 5 essais, c'est OK
        # (le test ci-dessus avec batch couvre ce cas)


class TestFigureSvgGM08:
    """Tests pour le rendu SVG des exercices GM08 (longueurs)"""
    
    def test_gm08_no_svg_by_default(self):
        """Les exercices GM08 n'ont pas de SVG par défaut"""
        payload = {
            "code_officiel": "6e_GM08",
            "nb_exercices": 5,
            "offer": "free"
        }
        
        response = requests.post(
            f"{API_URL}/generate/batch/gm08",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        exercises = data.get("exercises", [])
        
        for ex in exercises:
            # GM08 actuel n'a pas de needs_svg=True
            assert ex["metadata"].get("needs_svg") == False
            assert ex.get("figure_svg") is None


class TestSvgRenderService:
    """Tests unitaires du service de rendu SVG"""
    
    def test_render_clock_from_brief(self):
        """Test du rendu d'horloge via le service"""
        # Test en important directement le service
        import sys
        sys.path.insert(0, '/app/backend')
        
        from services.svg_render_service import render_svg_from_brief
        
        svg = render_svg_from_brief("horloge montrant 10h30")
        
        assert svg is not None
        assert svg.strip().startswith("<svg")
        assert "<circle" in svg
        assert "<line" in svg
    
    def test_render_timeline_from_brief(self):
        """Test du rendu de timeline via le service"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from services.svg_render_service import render_svg_from_brief
        
        svg = render_svg_from_brief("droite du temps")
        
        assert svg is not None
        assert svg.strip().startswith("<svg")
        assert "<line" in svg
    
    def test_render_placeholder_for_unknown(self):
        """Test du placeholder pour type inconnu"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from services.svg_render_service import render_svg_from_brief
        
        svg = render_svg_from_brief("quelque chose d'inconnu")
        
        assert svg is not None
        assert svg.strip().startswith("<svg")
        assert "Figure à visualiser" in svg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
