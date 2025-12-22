"""
Tests complets pour le générateur de Symétrie centrale (5e)
Valide le générateur, le SVG et l'intégration API
"""

import pytest
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService, MathExerciseType
from services.geometry_render_service import geometry_render_service


class TestSymetrieCentraleGenerator:
    """Tests unitaires du générateur de symétrie centrale"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.math_service = MathGenerationService()
    
    def test_symetrie_centrale_generator_exists(self):
        """Test : Le générateur de symétrie centrale existe"""
        print("\n" + "="*80)
        print("TEST : GÉNÉRATEUR SYMÉTRIE CENTRALE EXISTE")
        print("="*80)
        
        assert MathExerciseType.SYMETRIE_CENTRALE in MathExerciseType
        print(f"✅ Type SYMETRIE_CENTRALE défini : {MathExerciseType.SYMETRIE_CENTRALE.value}")
        
        assert hasattr(self.math_service, '_gen_symetrie_centrale')
        print("✅ Méthode _gen_symetrie_centrale existe")
    
    def test_symetrie_centrale_mapping(self):
        """Test : 'Symétrie centrale' est correctement mappé"""
        print("\n" + "="*80)
        print("TEST : MAPPING SYMÉTRIE CENTRALE")
        print("="*80)
        
        chapitre = "Symétrie centrale"
        niveau = "5e"
        
        types = self.math_service._map_chapter_to_types(chapitre, niveau)
        
        print(f"Chapitre : {chapitre}")
        print(f"Types mappés : {[t.value for t in types]}")
        
        assert len(types) > 0, f"Le chapitre '{chapitre}' doit avoir un mapping"
        assert MathExerciseType.SYMETRIE_CENTRALE in types
        
        print("✅ Mapping correct : Symétrie centrale → symetrie_centrale")
    
    def test_generate_symetrie_centrale_facile(self):
        """Test : Génération exercice facile"""
        print("\n" + "="*80)
        print("TEST : GÉNÉRATION SYMÉTRIE CENTRALE FACILE")
        print("="*80)
        
        spec = self.math_service._gen_symetrie_centrale(
            niveau="5e",
            chapitre="Symétrie centrale",
            difficulte="facile"
        )
        
        print(f"Type : {spec.type_exercice}")
        print(f"Type spécifique : {spec.parametres.get('type')}")
        print(f"Résultat : {spec.resultat_final}")
        print(f"Étapes : {len(spec.etapes_calculees)}")
        
        # Validations
        assert spec.type_exercice == MathExerciseType.SYMETRIE_CENTRALE
        assert spec.niveau == "5e"
        assert spec.chapitre == "Symétrie centrale"
        assert len(spec.etapes_calculees) > 0
        assert spec.figure_geometrique is not None
        assert spec.figure_geometrique.type == "symetrie_centrale"
        
        # Vérifier les coordonnées
        coords = spec.parametres
        assert "point_original" in coords
        assert "centre" in coords
        assert "point_image" in coords
        
        print("✅ Exercice facile généré correctement")
    
    def test_symetrie_centrale_formule_correcte(self):
        """Test : La formule M' = 2O - M est correcte"""
        print("\n" + "="*80)
        print("TEST : FORMULE SYMÉTRIE CENTRALE")
        print("="*80)
        
        spec = self.math_service._gen_symetrie_centrale(
            niveau="5e",
            chapitre="Symétrie centrale",
            difficulte="facile"
        )
        
        # Extraire les coordonnées
        M_x = spec.parametres["point_original_coords"]["x"]
        M_y = spec.parametres["point_original_coords"]["y"]
        O_x = spec.parametres["centre_coords"]["x"]
        O_y = spec.parametres["centre_coords"]["y"]
        M_prime_x = spec.solution_calculee["image_coords"]["x"]
        M_prime_y = spec.solution_calculee["image_coords"]["y"]
        
        print(f"Point M({M_x}, {M_y})")
        print(f"Centre O({O_x}, {O_y})")
        print(f"Image M'({M_prime_x}, {M_prime_y})")
        
        # Vérifier la formule M' = 2O - M
        assert M_prime_x == 2 * O_x - M_x, "Formule x incorrecte"
        assert M_prime_y == 2 * O_y - M_y, "Formule y incorrecte"
        
        # Vérifier que O est le milieu de [MM']
        milieu_x = (M_x + M_prime_x) / 2
        milieu_y = (M_y + M_prime_y) / 2
        
        print(f"Milieu calculé : ({milieu_x}, {milieu_y})")
        
        assert milieu_x == O_x, "O doit être le milieu en x"
        assert milieu_y == O_y, "O doit être le milieu en y"
        
        print("✅ Formule mathématique correcte")
    
    def test_symetrie_centrale_svg(self):
        """Test : Le SVG est généré"""
        print("\n" + "="*80)
        print("TEST : GÉNÉRATION SVG")
        print("="*80)
        
        spec = self.math_service._gen_symetrie_centrale(
            niveau="5e",
            chapitre="Symétrie centrale",
            difficulte="facile"
        )
        
        svg = geometry_render_service.render_figure_to_svg(spec.figure_geometrique)
        
        assert svg is not None
        assert len(svg) > 0
        assert "<svg" in svg
        
        # Vérifier que le centre est en rouge
        assert "#FF0000" in svg or "#ff0000" in svg, "Le centre doit être rouge"
        
        # Vérifier la présence de points
        assert "circle" in svg, "Des points doivent être présents"
        
        print(f"✅ SVG généré : {len(svg)} caractères")


class TestSymetrieCentraleAPI:
    """Tests d'intégration API pour symétrie centrale"""
    
    BASE_URL = "http://localhost:8001"
    
    def test_api_symetrie_centrale_returns_200(self):
        """Test CRITIQUE : Symétrie centrale retourne HTTP 200"""
        print("\n" + "="*80)
        print("TEST API : SYMÉTRIE CENTRALE → HTTP 200")
        print("="*80)
        
        response = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": "5e",
                "chapitre": "Symétrie centrale",
                "type_doc": "exercices",
                "difficulte": "facile",
                "nb_exercices": 1,
                "guest_id": "test_symetrie_centrale_api"
            },
            timeout=60
        )
        
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}"
        
        data = response.json()
        ex = data["document"]["exercises"][0]
        
        type_ex = ex["spec_mathematique"]["type_exercice"]
        print(f"Type : {type_ex}")
        
        assert type_ex == "symetrie_centrale"
        
        print("✅ HTTP 200 avec exercice de symétrie centrale")
    
    def test_api_svg_present(self):
        """Test : L'API retourne un figure_svg"""
        print("\n" + "="*80)
        print("TEST API : figure_svg PRÉSENT")
        print("="*80)
        
        response = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": "5e",
                "chapitre": "Symétrie centrale",
                "type_doc": "exercices",
                "difficulte": "facile",
                "nb_exercices": 1,
                "guest_id": "test_svg"
            },
            timeout=60
        )
        
        data = response.json()
        ex = data["document"]["exercises"][0]
        
        assert "figure_svg" in ex
        assert ex["figure_svg"] is not None
        assert len(ex["figure_svg"]) > 0
        
        svg = ex["figure_svg"]
        print(f"SVG : {len(svg)} caractères")
        
        # Vérifications du contenu SVG
        assert "<svg" in svg
        assert "circle" in svg
        assert "#FF0000" in svg or "#ff0000" in svg, "Centre en rouge"
        
        print("✅ figure_svg présent et valide")
    
    def test_api_multiple_exercises(self):
        """Test : Génération de plusieurs exercices"""
        print("\n" + "="*80)
        print("TEST API : PLUSIEURS EXERCICES")
        print("="*80)
        
        nb = 3
        
        response = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": "5e",
                "chapitre": "Symétrie centrale",
                "type_doc": "exercices",
                "difficulte": "moyen",
                "nb_exercices": nb,
                "guest_id": "test_multiple"
            },
            timeout=60
        )
        
        data = response.json()
        exercises = data["document"]["exercises"]
        
        assert len(exercises) == nb
        
        for i, ex in enumerate(exercises):
            assert ex["spec_mathematique"]["type_exercice"] == "symetrie_centrale"
            assert "figure_svg" in ex
            assert ex["figure_svg"] is not None
            print(f"  ✓ Exercice {i+1} : OK")
        
        print(f"✅ {nb} exercices générés avec SVG")
    
    def test_non_regression_symetrie_axiale(self):
        """Test NON-RÉGRESSION : Symétrie axiale fonctionne toujours"""
        print("\n" + "="*80)
        print("TEST NON-RÉGRESSION : SYMÉTRIE AXIALE")
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
                "guest_id": "test_non_reg"
            },
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        ex = data["document"]["exercises"][0]
        assert ex["spec_mathematique"]["type_exercice"] == "symetrie_axiale"
        
        print("✅ Symétrie axiale fonctionne toujours")


if __name__ == "__main__":
    print("\n" + "🧪"*40)
    print("TESTS SYMÉTRIE CENTRALE")
    print("🧪"*40 + "\n")
    
    # Tests unitaires
    test_gen = TestSymetrieCentraleGenerator()
    test_gen.setup_method()
    
    try:
        test_gen.test_symetrie_centrale_generator_exists()
        test_gen.test_symetrie_centrale_mapping()
        test_gen.test_generate_symetrie_centrale_facile()
        test_gen.test_symetrie_centrale_formule_correcte()
        test_gen.test_symetrie_centrale_svg()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS UNITAIRES PASSENT")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC TEST UNITAIRE: {e}\n")
        exit(1)
    
    # Tests API
    print("\n" + "🌐"*40)
    print("TESTS API SYMÉTRIE CENTRALE")
    print("🌐"*40 + "\n")
    
    test_api = TestSymetrieCentraleAPI()
    
    try:
        test_api.test_api_symetrie_centrale_returns_200()
        test_api.test_api_svg_present()
        test_api.test_api_multiple_exercises()
        test_api.test_non_regression_symetrie_axiale()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS API PASSENT")
        print("="*80 + "\n")
        
        print("\n" + "🎉"*40)
        print("✅ ✅ ✅  TOUS LES TESTS RÉUSSIS  ✅ ✅ ✅")
        print("🎉"*40 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC TEST API: {e}\n")
        exit(1)
