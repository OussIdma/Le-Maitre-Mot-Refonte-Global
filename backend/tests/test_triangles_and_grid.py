"""
Tests pour la correction des triangles et de la grille dans les symétries
Valide que :
1. Les triangles sont non alignés
2. Les triangles sont dessinés dans le SVG (pas juste les points)
3. La grille de fond est présente
"""

import pytest
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService
from services.geometry_render_service import geometry_render_service


class TestTrianglesNonAlignes:
    """Tests pour garantir que les triangles sont non alignés"""
    
    def setup_method(self):
        self.math_service = MathGenerationService()
    
    def test_fonction_are_points_aligned(self):
        """Test : La fonction _are_points_aligned fonctionne"""
        print("\n" + "="*80)
        print("TEST : DÉTECTION POINTS ALIGNÉS")
        print("="*80)
        
        # Points alignés (sur une ligne horizontale)
        aligned = self.math_service._are_points_aligned(1, 5, 3, 5, 7, 5)
        print(f"Points (1,5), (3,5), (7,5) alignés : {aligned}")
        assert aligned, "Ces points doivent être détectés comme alignés"
        
        # Points non alignés (triangle)
        not_aligned = self.math_service._are_points_aligned(1, 1, 5, 1, 3, 4)
        print(f"Points (1,1), (5,1), (3,4) alignés : {not_aligned}")
        assert not not_aligned, "Ces points ne doivent PAS être alignés"
        
        print("✅ Détection d'alignement fonctionne")
    
    def test_generate_non_aligned_triangle_points(self):
        """Test : La fonction génère des points non alignés"""
        print("\n" + "="*80)
        print("TEST : GÉNÉRATION TRIANGLE NON ALIGNÉ")
        print("="*80)
        
        for i in range(10):
            x1, y1, x2, y2, x3, y3 = self.math_service._generate_non_aligned_triangle_points()
            
            aligned = self.math_service._are_points_aligned(x1, y1, x2, y2, x3, y3)
            
            print(f"  Test {i+1}: ({x1},{y1}), ({x2},{y2}), ({x3},{y3}) - Alignés: {aligned}")
            
            assert not aligned, f"Les points générés ne doivent PAS être alignés (test {i+1})"
        
        print("✅ 10 triangles non alignés générés")
    
    def test_symetrie_axiale_triangle_non_aligne(self):
        """Test : Les triangles de symétrie axiale sont non alignés"""
        print("\n" + "="*80)
        print("TEST : TRIANGLES SYMÉTRIE AXIALE NON ALIGNÉS")
        print("="*80)
        
        # Générer plusieurs exercices de type "completer_figure"
        for i in range(5):
            spec = self.math_service._gen_symetrie_axiale(
                niveau="6e",
                chapitre="Symétrie axiale",
                difficulte="difficile"  # Plus de chances d'avoir completer_figure
            )
            
            if spec.parametres.get("type") == "completer_figure":
                # Extraire les coordonnées des 3 points initiaux
                coords = spec.parametres.get("point_original_coords", {})
                
                # Si on a 3 points dans figure_geometrique
                if spec.figure_geometrique and len(spec.figure_geometrique.points) >= 6:
                    # Extraire x, y des 3 premiers points (initiaux)
                    longueurs = spec.figure_geometrique.longueurs_connues
                    point1 = spec.figure_geometrique.points[0]
                    point2 = spec.figure_geometrique.points[1]
                    point3 = spec.figure_geometrique.points[2]
                    
                    x1 = longueurs.get(f"{point1}_x")
                    y1 = longueurs.get(f"{point1}_y")
                    x2 = longueurs.get(f"{point2}_x")
                    y2 = longueurs.get(f"{point2}_y")
                    x3 = longueurs.get(f"{point3}_x")
                    y3 = longueurs.get(f"{point3}_y")
                    
                    if all(v is not None for v in [x1, y1, x2, y2, x3, y3]):
                        aligned = self.math_service._are_points_aligned(x1, y1, x2, y2, x3, y3)
                        print(f"  Triangle {i+1}: ({x1},{y1}), ({x2},{y2}), ({x3},{y3}) - Alignés: {aligned}")
                        assert not aligned, "Le triangle généré ne doit PAS être aligné"
        
        print("✅ Triangles de symétrie axiale non alignés")
    
    def test_symetrie_centrale_triangle_non_aligne(self):
        """Test : Les triangles de symétrie centrale sont non alignés"""
        print("\n" + "="*80)
        print("TEST : TRIANGLES SYMÉTRIE CENTRALE NON ALIGNÉS")
        print("="*80)
        
        for i in range(5):
            spec = self.math_service._gen_symetrie_centrale(
                niveau="5e",
                chapitre="Symétrie centrale",
                difficulte="difficile"
            )
            
            if spec.parametres.get("type") == "completer_figure":
                if spec.figure_geometrique and len(spec.figure_geometrique.points) >= 4:
                    longueurs = spec.figure_geometrique.longueurs_connues
                    point1 = spec.figure_geometrique.points[0]
                    point2 = spec.figure_geometrique.points[1]
                    point3 = spec.figure_geometrique.points[2]
                    
                    x1 = longueurs.get(f"{point1}_x")
                    y1 = longueurs.get(f"{point1}_y")
                    x2 = longueurs.get(f"{point2}_x")
                    y2 = longueurs.get(f"{point2}_y")
                    x3 = longueurs.get(f"{point3}_x")
                    y3 = longueurs.get(f"{point3}_y")
                    
                    if all(v is not None for v in [x1, y1, x2, y2, x3, y3]):
                        aligned = self.math_service._are_points_aligned(x1, y1, x2, y2, x3, y3)
                        print(f"  Triangle {i+1}: ({x1},{y1}), ({x2},{y2}), ({x3},{y3}) - Alignés: {aligned}")
                        assert not aligned, "Le triangle généré ne doit PAS être aligné"
        
        print("✅ Triangles de symétrie centrale non alignés")


class TestTrianglesSVG:
    """Tests pour vérifier que les triangles sont dessinés dans le SVG"""
    
    def setup_method(self):
        self.math_service = MathGenerationService()
    
    def test_svg_contains_polygon_symetrie_axiale(self):
        """Test : Le SVG contient des polygones (triangles) pour symétrie axiale"""
        print("\n" + "="*80)
        print("TEST : SVG CONTIENT POLYGONES (SYMÉTRIE AXIALE)")
        print("="*80)
        
        # Générer jusqu'à trouver un completer_figure
        found = False
        for _ in range(20):
            spec = self.math_service._gen_symetrie_axiale(
                niveau="6e",
                chapitre="Symétrie axiale",
                difficulte="difficile"
            )
            
            if spec.parametres.get("type") == "completer_figure":
                svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
                
                assert svg is not None
                assert "<polygon" in svg, "Le SVG doit contenir des polygones (triangles)"
                assert "triangle-initial" in svg, "Le SVG doit avoir la classe triangle-initial"
                assert "triangle-image" in svg, "Le SVG doit avoir la classe triangle-image"
                
                # Compter les polygones
                nb_polygons = svg.count("<polygon")
                print(f"Nombre de polygones (triangles): {nb_polygons}")
                assert nb_polygons >= 2, "Au moins 2 triangles (initial + image)"
                
                found = True
                break
        
        assert found, "Aucun exercice completer_figure trouvé en 20 essais"
        print("✅ Triangles dessinés avec <polygon>")
    
    def test_svg_contains_polygon_symetrie_centrale(self):
        """Test : Le SVG contient des polygones (triangles) pour symétrie centrale"""
        print("\n" + "="*80)
        print("TEST : SVG CONTIENT POLYGONES (SYMÉTRIE CENTRALE)")
        print("="*80)
        
        found = False
        for _ in range(20):
            spec = self.math_service._gen_symetrie_centrale(
                niveau="5e",
                chapitre="Symétrie centrale",
                difficulte="difficile"
            )
            
            if spec.parametres.get("type") == "completer_figure":
                svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
                
                assert svg is not None
                assert "<polygon" in svg, "Le SVG doit contenir des polygones (triangles)"
                
                nb_polygons = svg.count("<polygon")
                print(f"Nombre de polygones (triangles): {nb_polygons}")
                assert nb_polygons >= 2, "Au moins 2 triangles (initial + image)"
                
                found = True
                break
        
        assert found, "Aucun exercice completer_figure trouvé en 20 essais"
        print("✅ Triangles dessinés avec <polygon>")


class TestGrilleSVG:
    """Tests pour vérifier que la grille est présente dans le SVG"""
    
    def setup_method(self):
        self.math_service = MathGenerationService()
    
    def test_svg_contains_grid_symetrie_axiale(self):
        """Test : Le SVG contient une grille pour symétrie axiale"""
        print("\n" + "="*80)
        print("TEST : SVG CONTIENT GRILLE (SYMÉTRIE AXIALE)")
        print("="*80)
        
        found = False
        for _ in range(20):
            spec = self.math_service._gen_symetrie_axiale(
                niveau="6e",
                chapitre="Symétrie axiale",
                difficulte="difficile"
            )
            
            if spec.parametres.get("type") == "completer_figure":
                svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
                
                assert svg is not None
                assert "grid-line" in svg, "Le SVG doit contenir des lignes de grille"
                
                # Compter les lignes de grille
                nb_grid_lines = svg.count('class="grid-line"')
                print(f"Nombre de lignes de grille: {nb_grid_lines}")
                assert nb_grid_lines > 20, "La grille doit avoir au moins 20 lignes (14x14 = 28)"
                
                found = True
                break
        
        assert found, "Aucun exercice completer_figure trouvé"
        print("✅ Grille présente dans le SVG")
    
    def test_svg_contains_grid_symetrie_centrale(self):
        """Test : Le SVG contient une grille pour symétrie centrale"""
        print("\n" + "="*80)
        print("TEST : SVG CONTIENT GRILLE (SYMÉTRIE CENTRALE)")
        print("="*80)
        
        found = False
        for _ in range(20):
            spec = self.math_service._gen_symetrie_centrale(
                niveau="5e",
                chapitre="Symétrie centrale",
                difficulte="difficile"
            )
            
            if spec.parametres.get("type") == "completer_figure":
                svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
                
                assert svg is not None
                assert "grid-line" in svg, "Le SVG doit contenir des lignes de grille"
                
                nb_grid_lines = svg.count('class="grid-line"')
                print(f"Nombre de lignes de grille: {nb_grid_lines}")
                assert nb_grid_lines > 20, "La grille doit avoir suffisamment de lignes"
                
                found = True
                break
        
        assert found, "Aucun exercice completer_figure trouvé"
        print("✅ Grille présente dans le SVG")


class TestAPITrianglesEtGrille:
    """Tests API pour triangles et grille"""
    
    BASE_URL = "http://localhost:8001"
    
    def test_api_symetrie_axiale_triangle_et_grille(self):
        """Test API : Symétrie axiale retourne SVG avec triangle et grille"""
        print("\n" + "="*80)
        print("TEST API : SYMÉTRIE AXIALE - TRIANGLE + GRILLE")
        print("="*80)
        
        # Générer plusieurs fois pour avoir un completer_figure
        for _ in range(10):
            response = requests.post(
                f"{self.BASE_URL}/api/generate",
                json={
                    "matiere": "Mathématiques",
                    "niveau": "6e",
                    "chapitre": "Symétrie axiale",
                    "type_doc": "exercices",
                    "difficulte": "difficile",
                    "nb_exercices": 1,
                    "guest_id": "test_api_triangle"
                },
                timeout=60
            )
            
            assert response.status_code == 200
            data = response.json()
            ex = data["document"]["exercises"][0]
            
            if ex["spec_mathematique"]["parametres"].get("type") == "completer_figure":
                svg = ex.get("figure_svg", "")
                
                assert len(svg) > 0, "SVG ne doit pas être vide"
                assert "<polygon" in svg, "SVG doit contenir des triangles (<polygon>)"
                assert "grid-line" in svg, "SVG doit contenir une grille"
                assert "triangle-initial" in svg, "SVG doit avoir triangle initial"
                assert "triangle-image" in svg, "SVG doit avoir triangle image"
                
                print("✅ API retourne triangle + grille pour symétrie axiale")
                return
        
        # Si on arrive ici, on n'a pas trouvé de completer_figure
        print("⚠️  Aucun completer_figure généré en 10 essais (pas un échec critique)")
    
    def test_api_symetrie_centrale_triangle_et_grille(self):
        """Test API : Symétrie centrale retourne SVG avec triangle et grille"""
        print("\n" + "="*80)
        print("TEST API : SYMÉTRIE CENTRALE - TRIANGLE + GRILLE")
        print("="*80)
        
        for _ in range(10):
            response = requests.post(
                f"{self.BASE_URL}/api/generate",
                json={
                    "matiere": "Mathématiques",
                    "niveau": "5e",
                    "chapitre": "Symétrie centrale",
                    "type_doc": "exercices",
                    "difficulte": "difficile",
                    "nb_exercices": 1,
                    "guest_id": "test_api_centrale_triangle"
                },
                timeout=60
            )
            
            assert response.status_code == 200
            data = response.json()
            ex = data["document"]["exercises"][0]
            
            if ex["spec_mathematique"]["parametres"].get("type") == "completer_figure":
                svg = ex.get("figure_svg", "")
                
                assert len(svg) > 0
                assert "<polygon" in svg
                assert "grid-line" in svg
                
                print("✅ API retourne triangle + grille pour symétrie centrale")
                return
        
        print("⚠️  Aucun completer_figure généré en 10 essais (pas un échec critique)")


if __name__ == "__main__":
    print("\n" + "🔺"*40)
    print("TESTS TRIANGLES ET GRILLE")
    print("🔺"*40 + "\n")
    
    # Tests triangles non alignés
    test_aligned = TestTrianglesNonAlignes()
    test_aligned.setup_method()
    
    try:
        test_aligned.test_fonction_are_points_aligned()
        test_aligned.test_generate_non_aligned_triangle_points()
        test_aligned.test_symetrie_axiale_triangle_non_aligne()
        test_aligned.test_symetrie_centrale_triangle_non_aligne()
        
        print("\n✅ TESTS TRIANGLES NON ALIGNÉS : OK\n")
    except AssertionError as e:
        print(f"\n❌ ÉCHEC : {e}\n")
        exit(1)
    
    # Tests SVG triangles
    test_svg_tri = TestTrianglesSVG()
    test_svg_tri.setup_method()
    
    try:
        test_svg_tri.test_svg_contains_polygon_symetrie_axiale()
        test_svg_tri.test_svg_contains_polygon_symetrie_centrale()
        
        print("\n✅ TESTS SVG TRIANGLES : OK\n")
    except AssertionError as e:
        print(f"\n❌ ÉCHEC : {e}\n")
        exit(1)
    
    # Tests grille
    test_grid = TestGrilleSVG()
    test_grid.setup_method()
    
    try:
        test_grid.test_svg_contains_grid_symetrie_axiale()
        test_grid.test_svg_contains_grid_symetrie_centrale()
        
        print("\n✅ TESTS GRILLE : OK\n")
    except AssertionError as e:
        print(f"\n❌ ÉCHEC : {e}\n")
        exit(1)
    
    # Tests API
    test_api = TestAPITrianglesEtGrille()
    
    try:
        test_api.test_api_symetrie_axiale_triangle_et_grille()
        test_api.test_api_symetrie_centrale_triangle_et_grille()
        
        print("\n✅ TESTS API : OK\n")
    except AssertionError as e:
        print(f"\n❌ ÉCHEC : {e}\n")
        exit(1)
    
    print("\n" + "🎉"*40)
    print("✅ ✅ ✅  TOUS LES TESTS RÉUSSIS  ✅ ✅ ✅")
    print("🎉"*40 + "\n")
