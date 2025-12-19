"""
Tests automatiques pour vérifier la génération de SVG
pour tous les générateurs mathématiques avec figures géométriques
"""

import pytest
import sys
import os

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService
from services.geometry_render_service import geometry_render_service


class TestSVGGeneration:
    """Tests de génération SVG pour tous les générateurs géométriques"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.math_service = MathGenerationService()
    
    def test_triangle_rectangle_svg(self):
        """Test SVG pour triangle rectangle (Pythagore)"""
        specs = self.math_service.generate_math_exercise_specs(
            niveau="4e",
            chapitre="Théorème de Pythagore",
            difficulte="facile",
            nb_exercices=1
        )
        
        assert len(specs) > 0, "Aucune spec générée"
        spec = specs[0]
        
        assert spec.figure_geometrique is not None, "Pas de figure géométrique"
        assert spec.figure_geometrique.type == "triangle_rectangle"
        
        # Tester le rendu SVG
        svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
        assert svg is not None, "SVG non généré"
        assert len(svg) > 0, "SVG vide"
        assert "<svg" in svg, "Pas de balise SVG"
        assert "<circle" in svg, "Pas de points"
        assert "<line" in svg, "Pas de segments"
        
        print(f"✅ Triangle rectangle: {len(svg)} caractères")
    
    def test_trigonometrie_svg(self):
        """Test SVG pour trigonométrie"""
        specs = self.math_service.generate_math_exercise_specs(
            niveau="3e",
            chapitre="Trigonométrie",
            difficulte="facile",
            nb_exercices=1
        )
        
        assert len(specs) > 0
        spec = specs[0]
        
        assert spec.figure_geometrique is not None
        assert spec.figure_geometrique.type == "triangle_rectangle"
        
        svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
        assert svg is not None
        assert len(svg) > 0
        
        print(f"✅ Trigonométrie: {len(svg)} caractères")
    
    def test_thales_svg(self):
        """Test SVG pour Thalès"""
        specs = self.math_service.generate_math_exercise_specs(
            niveau="3e",
            chapitre="Théorème de Thalès",
            difficulte="facile",
            nb_exercices=1
        )
        
        assert len(specs) > 0
        spec = specs[0]
        
        assert spec.figure_geometrique is not None
        assert spec.figure_geometrique.type == "thales"
        assert len(spec.figure_geometrique.points) == 5, "Thalès doit avoir 5 points"
        
        svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
        assert svg is not None
        assert len(svg) > 0
        
        # Vérifier que les 5 points sont présents
        for point in spec.figure_geometrique.points:
            assert f">{point}<" in svg, f"Point {point} manquant dans le SVG"
        
        # Vérifier le segment parallèle en orange
        assert "#FF6600" in svg or "#ff6600" in svg.lower(), "Segment parallèle orange manquant"
        
        print(f"✅ Thalès: {len(svg)} caractères, 5 points présents")
    
    def test_cercle_svg(self):
        """Test SVG pour cercles - Vérifie le rendu optimisé mobile"""
        # Test avec le chapitre "Aires" qui génère des cercles
        specs = self.math_service.generate_math_exercise_specs(
            niveau="6e",
            chapitre="Aires",
            difficulte="facile",
            nb_exercices=5  # Générer plusieurs pour avoir un cercle
        )
        
        # Trouver un exercice de cercle
        cercle_spec = None
        for spec in specs:
            if spec.figure_geometrique and spec.figure_geometrique.type == "cercle":
                cercle_spec = spec
                break
        
        assert cercle_spec is not None, "Aucun exercice de cercle généré"
        
        svg = geometry_render_service.render_figure_to_svg(cercle_spec.figure_geometrique)
        assert svg is not None
        assert len(svg) > 0
        
        # Vérifications structure cercle
        assert '<circle' in svg, "Pas de cercle SVG"
        assert svg.count('<circle') >= 2, "Devrait avoir au moins 2 cercles (figure + point central)"
        assert '<text' in svg, "Pas de labels texte"
        assert 'r =' in svg, "Label du rayon manquant"
        
        # Vérifier que le rayon est bien affiché
        rayon_math = cercle_spec.figure_geometrique.longueurs_connues.get('rayon', 0)
        assert f"r = {rayon_math} cm" in svg, f"Label 'r = {rayon_math} cm' manquant"
        
        print(f"✅ Cercle: {len(svg)} caractères, rayon {rayon_math} cm bien affiché")
    
    def test_rectangle_svg(self):
        """Test SVG pour rectangles/carrés - Vérifie le rendu optimisé mobile"""
        specs = self.math_service.generate_math_exercise_specs(
            niveau="5e",
            chapitre="Aires et périmètres",
            difficulte="facile",
            nb_exercices=10  # Générer plusieurs pour avoir un rectangle
        )
        
        assert len(specs) > 0
        
        # Trouver un exercice de rectangle
        rect_spec = None
        for spec in specs:
            if spec.figure_geometrique and spec.figure_geometrique.type == "rectangle":
                rect_spec = spec
                break
        
        if rect_spec:
            svg = geometry_render_service.render_figure_to_svg(rect_spec.figure_geometrique)
            assert svg is not None
            assert len(svg) > 0
            
            # Vérifications structure rectangle
            assert '<line' in svg, "Pas de lignes"
            assert svg.count('<line') == 4, "Devrait avoir 4 côtés"
            assert '<circle' in svg, "Pas de points"
            assert svg.count('<circle') == 4, "Devrait avoir 4 sommets"
            assert '<text' in svg, "Pas de labels"
            assert svg.count('<text') >= 6, "Devrait avoir au moins 6 textes (4 points + 2 longueurs)"
            
            # Vérifier que les dimensions sont affichées
            longueurs = rect_spec.figure_geometrique.longueurs_connues
            if longueurs:
                # Au moins une dimension devrait être dans le SVG
                dimension_found = False
                for val in longueurs.values():
                    if f"{val} cm" in svg:
                        dimension_found = True
                        break
                assert dimension_found, "Aucune dimension trouvée dans le SVG"
            
            print(f"✅ Rectangle/Carré: {len(svg)} caractères, 4 sommets distincts")
    
    def test_triangle_quelconque_svg(self):
        """Test SVG pour triangles quelconques"""
        specs = self.math_service.generate_math_exercise_specs(
            niveau="5e",
            chapitre="Triangles",
            difficulte="facile",
            nb_exercices=1
        )
        
        assert len(specs) > 0
        spec = specs[0]
        
        if spec.figure_geometrique:
            assert spec.figure_geometrique.type in ["triangle", "triangle_rectangle"]
            
            svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
            assert svg is not None
            assert len(svg) > 0
            
            print(f"✅ Triangle quelconque: {len(svg)} caractères")
    
    def test_all_geometric_generators(self):
        """Test global : tous les générateurs géométriques produisent un SVG"""
        
        geometric_chapters = [
            ("4e", "Théorème de Pythagore"),
            ("3e", "Trigonométrie"),
            ("3e", "Théorème de Thalès"),
            ("6e", "Aires"),
            ("5e", "Triangles"),
        ]
        
        results = []
        
        for niveau, chapitre in geometric_chapters:
            specs = self.math_service.generate_math_exercise_specs(
                niveau=niveau,
                chapitre=chapitre,
                difficulte="facile",
                nb_exercices=1
            )
            
            if specs and specs[0].figure_geometrique:
                svg = geometry_render_service.render_figure_to_svg(specs[0].figure_geometrique)
                has_svg = svg is not None and len(svg) > 0
                results.append((chapitre, has_svg))
            else:
                results.append((chapitre, False))
        
        # Vérifier que tous ont un SVG
        failed = [chap for chap, has_svg in results if not has_svg]
        assert len(failed) == 0, f"Chapitres sans SVG: {failed}"
        
        print(f"\n✅ Tous les générateurs géométriques produisent un SVG")
        print(f"   Testé: {len(results)} chapitres")


if __name__ == "__main__":
    # Exécution directe pour tests rapides
    test = TestSVGGeneration()
    test.setup_method()
    
    print("="*70)
    print("TESTS DE GÉNÉRATION SVG")
    print("="*70 + "\n")
    
    try:
        test.test_triangle_rectangle_svg()
        test.test_trigonometrie_svg()
        test.test_thales_svg()
        test.test_cercle_svg()
        test.test_rectangle_svg()
        test.test_triangle_quelconque_svg()
        test.test_all_geometric_generators()
        
        print("\n" + "="*70)
        print("✅ TOUS LES TESTS PASSENT")
        print("="*70)
    except AssertionError as e:
        print(f"\n❌ ÉCHEC: {e}")
        sys.exit(1)
