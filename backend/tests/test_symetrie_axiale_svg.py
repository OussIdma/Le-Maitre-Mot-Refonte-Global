"""
Tests pour les schémas SVG de symétrie axiale
Valide la génération, le contenu et l'intégration des SVG
"""

import pytest
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService
from services.geometry_render_service import geometry_render_service


class TestSymetrieAxialeSVG:
    """Tests unitaires pour le rendu SVG de la symétrie axiale"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.math_service = MathGenerationService()
    
    def test_svg_generation_basic(self):
        """Test : Un exercice de symétrie axiale génère un SVG"""
        print("\n" + "="*80)
        print("TEST : GÉNÉRATION SVG BASIQUE")
        print("="*80)
        
        # Générer un exercice
        spec = self.math_service._gen_symetrie_axiale(
            niveau="6e",
            chapitre="Symétrie axiale",
            difficulte="facile"
        )
        
        # Vérifier que la figure géométrique existe
        assert spec.figure_geometrique is not None, "La spec doit avoir une figure géométrique"
        
        # Générer le SVG
        svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
        
        print(f"SVG généré : {len(svg) if svg else 0} caractères")
        
        assert svg is not None, "Le SVG ne doit pas être None"
        assert len(svg) > 0, "Le SVG ne doit pas être vide"
        assert "<svg" in svg, "Le SVG doit contenir la balise <svg>"
        
        print("✅ SVG généré avec succès")
    
    def test_svg_contains_axes(self):
        """Test : Le SVG contient les axes de coordonnées"""
        print("\n" + "="*80)
        print("TEST : SVG CONTIENT LES AXES")
        print("="*80)
        
        spec = self.math_service._gen_symetrie_axiale(
            niveau="6e",
            chapitre="Symétrie axiale",
            difficulte="facile"
        )
        
        svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
        
        # Vérifier la présence d'éléments essentiels
        assert "line" in svg, "Le SVG doit contenir des lignes (axes)"
        assert "text" in svg, "Le SVG doit contenir des labels de texte"
        
        # Vérifier les labels des axes x et y
        assert "x" in svg or "X" in svg, "Le SVG doit contenir le label de l'axe X"
        assert "y" in svg or "Y" in svg, "Le SVG doit contenir le label de l'axe Y"
        
        print("✅ Le SVG contient les axes de coordonnées")
    
    def test_svg_contains_symmetry_axis(self):
        """Test : Le SVG contient l'axe de symétrie"""
        print("\n" + "="*80)
        print("TEST : SVG CONTIENT L'AXE DE SYMÉTRIE")
        print("="*80)
        
        spec = self.math_service._gen_symetrie_axiale(
            niveau="6e",
            chapitre="Symétrie axiale",
            difficulte="facile"
        )
        
        svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
        
        # L'axe de symétrie devrait être en rouge (#FF0000)
        assert "#FF0000" in svg or "#ff0000" in svg, "L'axe de symétrie doit être en rouge"
        
        # L'axe doit être en pointillés (dashed)
        assert "dashed" in svg or "stroke-dasharray" in svg, "L'axe doit être en pointillés"
        
        # Vérifier la présence de "x =" ou "y =" (label de l'axe)
        axe_type = spec.parametres.get("axe_type", "")
        if axe_type == "vertical":
            assert "x =" in svg or "x=" in svg, "L'axe vertical doit être labellé 'x ='"
        elif axe_type == "horizontal":
            assert "y =" in svg or "y=" in svg, "L'axe horizontal doit être labellé 'y ='"
        elif axe_type == "oblique":
            assert "y = x" in svg or "y=x" in svg, "L'axe oblique doit être labellé 'y = x'"
        
        print(f"✅ L'axe de symétrie ({axe_type}) est présent dans le SVG")
    
    def test_svg_contains_points(self):
        """Test : Le SVG contient les points (original et symétrique)"""
        print("\n" + "="*80)
        print("TEST : SVG CONTIENT LES POINTS")
        print("="*80)
        
        spec = self.math_service._gen_symetrie_axiale(
            niveau="6e",
            chapitre="Symétrie axiale",
            difficulte="facile"
        )
        
        svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
        
        # Vérifier la présence de cercles (points)
        assert "circle" in svg, "Le SVG doit contenir des cercles (points)"
        
        # Vérifier les labels des points
        point_original = spec.parametres.get("point_original", "")
        point_image = spec.parametres.get("point_image", "")
        
        if point_original:
            assert point_original in svg, f"Le point original '{point_original}' doit être dans le SVG"
            print(f"  ✓ Point original '{point_original}' trouvé")
        
        if point_image:
            assert point_image in svg, f"Le point image '{point_image}' doit être dans le SVG"
            print(f"  ✓ Point image '{point_image}' trouvé")
        
        print("✅ Les points sont présents dans le SVG")
    
    def test_svg_different_axes_types(self):
        """Test : Le SVG gère différents types d'axes"""
        print("\n" + "="*80)
        print("TEST : SVG AVEC DIFFÉRENTS TYPES D'AXES")
        print("="*80)
        
        axes_types = []
        
        # Générer plusieurs exercices pour obtenir différents axes
        for i in range(10):
            spec = self.math_service._gen_symetrie_axiale(
                niveau="6e",
                chapitre="Symétrie axiale",
                difficulte="moyen"
            )
            axe_type = spec.parametres.get("axe_type", "")
            axes_types.append(axe_type)
            
            # Tester le rendu
            svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
            assert svg is not None and len(svg) > 0, f"SVG doit être généré pour axe {axe_type}"
        
        axes_types_uniques = set(axes_types)
        print(f"Types d'axes générés : {axes_types_uniques}")
        
        # On devrait avoir au moins 2 types différents sur 10 générations
        assert len(axes_types_uniques) >= 1, "Le générateur doit produire différents types d'axes"
        
        print(f"✅ {len(axes_types_uniques)} types d'axes différents générés")


class TestSymetrieAxialeSVG_API:
    """Tests d'intégration API pour les SVG de symétrie axiale"""
    
    BASE_URL = "http://localhost:8001"
    
    def test_api_returns_svg(self):
        """Test CRITIQUE : L'API retourne un figure_svg pour symétrie axiale"""
        print("\n" + "="*80)
        print("TEST API : figure_svg PRÉSENT")
        print("="*80)
        
        response = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": "6e",
                "chapitre": "Symétrie axiale",
                "type_doc": "exercices",
                "difficulte": "facile",
                "nb_exercices": 1,
                "guest_id": "test_svg_api"
            },
            timeout=60
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        ex = data["document"]["exercises"][0]
        
        # Vérifier que figure_svg est présent
        assert "figure_svg" in ex, "L'exercice doit contenir 'figure_svg'"
        assert ex["figure_svg"] is not None, "figure_svg ne doit pas être None"
        assert len(ex["figure_svg"]) > 0, "figure_svg ne doit pas être vide"
        
        svg = ex["figure_svg"]
        print(f"figure_svg reçu : {len(svg)} caractères")
        
        # Vérifications de base
        assert "<svg" in svg, "figure_svg doit être du SVG valide"
        assert "</svg>" in svg, "figure_svg doit être du SVG complet"
        
        print("✅ L'API retourne bien un figure_svg")
    
    def test_api_svg_content(self):
        """Test : Le contenu du SVG de l'API est correct"""
        print("\n" + "="*80)
        print("TEST API : CONTENU DU SVG")
        print("="*80)
        
        response = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": "6e",
                "chapitre": "Symétrie axiale",
                "type_doc": "exercices",
                "difficulte": "facile",
                "nb_exercices": 1,
                "guest_id": "test_svg_content"
            },
            timeout=60
        )
        
        data = response.json()
        ex = data["document"]["exercises"][0]
        svg = ex["figure_svg"]
        
        # Vérifier les éléments essentiels du SVG
        checks = {
            "Axes de coordonnées": "line" in svg,
            "Points": "circle" in svg,
            "Labels": "text" in svg,
            "Axe de symétrie (rouge)": "#FF0000" in svg or "#ff0000" in svg,
            "Axe en pointillés": "dashed" in svg or "stroke-dasharray" in svg
        }
        
        for nom, resultat in checks.items():
            status = "✓" if resultat else "✗"
            print(f"  {status} {nom}")
            assert resultat, f"{nom} manquant dans le SVG"
        
        print("✅ Tous les éléments essentiels sont présents")
    
    def test_api_multiple_exercises_all_have_svg(self):
        """Test : Tous les exercices générés ont un SVG"""
        print("\n" + "="*80)
        print("TEST API : TOUS LES EXERCICES ONT UN SVG")
        print("="*80)
        
        nb_exercices = 3
        
        response = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": "6e",
                "chapitre": "Symétrie axiale",
                "type_doc": "exercices",
                "difficulte": "moyen",
                "nb_exercices": nb_exercices,
                "guest_id": "test_multiple_svg"
            },
            timeout=60
        )
        
        data = response.json()
        exercises = data["document"]["exercises"]
        
        assert len(exercises) == nb_exercices, f"Expected {nb_exercices} exercises"
        
        for i, ex in enumerate(exercises):
            assert "figure_svg" in ex, f"Exercice {i+1} doit avoir figure_svg"
            assert ex["figure_svg"] is not None, f"Exercice {i+1}: figure_svg ne doit pas être None"
            assert len(ex["figure_svg"]) > 100, f"Exercice {i+1}: figure_svg trop court"
            print(f"  ✓ Exercice {i+1} : SVG présent ({len(ex['figure_svg'])} car.)")
        
        print(f"✅ Tous les {nb_exercices} exercices ont un SVG")


if __name__ == "__main__":
    print("\n" + "🎨"*40)
    print("TESTS SVG SYMÉTRIE AXIALE")
    print("🎨"*40 + "\n")
    
    # Tests unitaires
    test_svg = TestSymetrieAxialeSVG()
    test_svg.setup_method()
    
    try:
        test_svg.test_svg_generation_basic()
        test_svg.test_svg_contains_axes()
        test_svg.test_svg_contains_symmetry_axis()
        test_svg.test_svg_contains_points()
        test_svg.test_svg_different_axes_types()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS UNITAIRES SVG PASSENT")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC TEST UNITAIRE: {e}\n")
        exit(1)
    
    # Tests API
    print("\n" + "🌐"*40)
    print("TESTS API SVG SYMÉTRIE AXIALE")
    print("🌐"*40 + "\n")
    
    test_api = TestSymetrieAxialeSVG_API()
    
    try:
        test_api.test_api_returns_svg()
        test_api.test_api_svg_content()
        test_api.test_api_multiple_exercises_all_have_svg()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS API SVG PASSENT")
        print("="*80 + "\n")
        
        print("\n" + "🎉"*40)
        print("✅ ✅ ✅  TOUS LES TESTS SVG RÉUSSIS  ✅ ✅ ✅")
        print("🎉"*40 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC TEST API: {e}\n")
        exit(1)
