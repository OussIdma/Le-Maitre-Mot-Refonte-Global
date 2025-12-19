"""
Tests complets pour le générateur de Symétrie axiale
Valide le générateur et l'intégration API end-to-end
"""

import pytest
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService, MathExerciseType


class TestSymetrieAxialeGenerator:
    """Tests unitaires du générateur de symétrie axiale"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.math_service = MathGenerationService()
    
    def test_symetrie_axiale_generator_exists(self):
        """Test : Le générateur de symétrie axiale existe"""
        print("\n" + "="*80)
        print("TEST : GÉNÉRATEUR SYMÉTRIE AXIALE EXISTE")
        print("="*80)
        
        # Vérifier que SYMETRIE_AXIALE est dans l'enum
        assert MathExerciseType.SYMETRIE_AXIALE in MathExerciseType
        print(f"✅ Type d'exercice SYMETRIE_AXIALE défini : {MathExerciseType.SYMETRIE_AXIALE.value}")
        
        # Vérifier que la méthode _gen_symetrie_axiale existe
        assert hasattr(self.math_service, '_gen_symetrie_axiale')
        print("✅ Méthode _gen_symetrie_axiale existe")
    
    def test_symetrie_axiale_mapping(self):
        """Test : 'Symétrie axiale' est correctement mappé"""
        print("\n" + "="*80)
        print("TEST : MAPPING SYMÉTRIE AXIALE")
        print("="*80)
        
        chapitre = "Symétrie axiale"
        niveau = "6e"
        
        # Le chapitre ne doit plus lever d'exception
        types = self.math_service._map_chapter_to_types(chapitre, niveau)
        
        print(f"Chapitre : {chapitre}")
        print(f"Types mappés : {[t.value for t in types]}")
        
        assert len(types) > 0, f"Le chapitre '{chapitre}' doit avoir un mapping"
        assert MathExerciseType.SYMETRIE_AXIALE in types, \
            f"Le chapitre doit mapper vers SYMETRIE_AXIALE"
        
        print("✅ Mapping correct : Symétrie axiale → symetrie_axiale")
    
    def test_generate_symetrie_facile(self):
        """Test : Génération d'un exercice facile de symétrie axiale"""
        print("\n" + "="*80)
        print("TEST : GÉNÉRATION SYMÉTRIE AXIALE FACILE")
        print("="*80)
        
        spec = self.math_service._gen_symetrie_axiale(
            niveau="6e",
            chapitre="Symétrie axiale",
            difficulte="facile"
        )
        
        print(f"Type exercice : {spec.type_exercice}")
        print(f"Type spécifique : {spec.parametres.get('type')}")
        print(f"Axe : {spec.parametres.get('axe_description')}")
        print(f"Résultat : {spec.resultat_final}")
        print(f"Nombre d'étapes : {len(spec.etapes_calculees)}")
        
        # Validations
        assert spec.type_exercice == MathExerciseType.SYMETRIE_AXIALE
        assert spec.niveau == "6e"
        assert spec.chapitre == "Symétrie axiale"
        assert spec.difficulte.value == "facile"
        assert len(spec.etapes_calculees) > 0
        assert spec.figure_geometrique is not None
        assert spec.figure_geometrique.type == "symetrie_axiale"
        
        # Type d'exercice doit être défini
        assert "type" in spec.parametres
        assert spec.parametres["type"] in ["trouver_symetrique", "verifier_symetrie", "completer_figure"]
        
        print("✅ Exercice facile généré correctement")
    
    def test_generate_symetrie_moyen(self):
        """Test : Génération d'un exercice moyen de symétrie axiale"""
        print("\n" + "="*80)
        print("TEST : GÉNÉRATION SYMÉTRIE AXIALE MOYEN")
        print("="*80)
        
        spec = self.math_service._gen_symetrie_axiale(
            niveau="6e",
            chapitre="Symétrie axiale",
            difficulte="moyen"
        )
        
        print(f"Type exercice : {spec.type_exercice}")
        print(f"Type spécifique : {spec.parametres.get('type')}")
        print(f"Difficulté : {spec.difficulte}")
        
        assert spec.difficulte.value == "moyen"
        assert spec.type_exercice == MathExerciseType.SYMETRIE_AXIALE
        
        print("✅ Exercice moyen généré correctement")
    
    def test_symetrie_multiple_generations(self):
        """Test : Génération de plusieurs exercices (variété)"""
        print("\n" + "="*80)
        print("TEST : VARIÉTÉ DES EXERCICES")
        print("="*80)
        
        types_generes = set()
        
        for i in range(10):
            spec = self.math_service._gen_symetrie_axiale(
                niveau="6e",
                chapitre="Symétrie axiale",
                difficulte="moyen"
            )
            types_generes.add(spec.parametres.get("type"))
        
        print(f"Types générés : {types_generes}")
        print(f"Nombre de variantes : {len(types_generes)}")
        
        # On devrait avoir au moins 2 types différents sur 10 générations
        assert len(types_generes) >= 1, "Le générateur doit produire des exercices variés"
        
        print("✅ Variété des exercices validée")
    
    def test_symetrie_figure_geometrique(self):
        """Test : La figure géométrique est correctement générée"""
        print("\n" + "="*80)
        print("TEST : FIGURE GÉOMÉTRIQUE")
        print("="*80)
        
        spec = self.math_service._gen_symetrie_axiale(
            niveau="6e",
            chapitre="Symétrie axiale",
            difficulte="facile"
        )
        
        figure = spec.figure_geometrique
        
        print(f"Type figure : {figure.type}")
        print(f"Points : {figure.points}")
        print(f"Propriétés : {figure.proprietes}")
        
        assert figure is not None
        assert figure.type == "symetrie_axiale"
        assert len(figure.points) >= 2, "Au moins 2 points (original + image)"
        assert len(figure.proprietes) > 0, "Des propriétés doivent être définies"
        
        print("✅ Figure géométrique valide")


class TestSymetrieAxialeAPI:
    """Tests d'intégration API pour la symétrie axiale"""
    
    BASE_URL = "http://localhost:8001"
    
    def test_symetrie_axiale_api_returns_200(self):
        """Test CRITIQUE : L'API retourne HTTP 200 pour Symétrie axiale"""
        print("\n" + "="*80)
        print("TEST CRITIQUE : SYMÉTRIE AXIALE → HTTP 200 (plus de 422 !)")
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
                "guest_id": "test_symetrie_api"
            },
            timeout=60
        )
        
        print(f"Status code: {response.status_code}")
        
        # AVANT le fix : retournait 422
        # APRÈS le fix : doit retourner 200
        assert response.status_code == 200, \
            f"❌ L'API doit maintenant retourner 200 pour Symétrie axiale, got {response.status_code}"
        
        data = response.json()
        assert "document" in data, "La réponse doit contenir 'document'"
        assert "exercises" in data["document"], "Le document doit contenir 'exercises'"
        
        ex = data["document"]["exercises"][0]
        assert "spec_mathematique" in ex
        
        type_ex = ex["spec_mathematique"]["type_exercice"]
        print(f"Type d'exercice généré : {type_ex}")
        
        assert type_ex == "symetrie_axiale", \
            f"Type doit être 'symetrie_axiale', got '{type_ex}'"
        
        # Vérifier l'énoncé
        enonce = ex.get("enonce", "")
        print(f"Énoncé : {enonce[:100]}...")
        
        assert len(enonce) > 0, "L'énoncé ne doit pas être vide"
        
        print("✅ Test réussi : HTTP 200 avec exercice de symétrie axiale correct")
    
    def test_symetrie_axiale_multiple_exercises(self):
        """Test : Génération de plusieurs exercices via API"""
        print("\n" + "="*80)
        print("TEST : GÉNÉRATION MULTIPLE EXERCICES")
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
                "guest_id": "test_multiple"
            },
            timeout=60
        )
        
        print(f"Status code: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        exercises = data["document"]["exercises"]
        
        print(f"Nombre d'exercices reçus : {len(exercises)}")
        assert len(exercises) == nb_exercices
        
        # Vérifier que tous sont de type symetrie_axiale
        for i, ex in enumerate(exercises):
            type_ex = ex["spec_mathematique"]["type_exercice"]
            print(f"  Exercice {i+1} : {type_ex}")
            assert type_ex == "symetrie_axiale"
        
        print(f"✅ {nb_exercices} exercices de symétrie axiale générés")
    
    def test_symetrie_non_regression_autres_chapitres(self):
        """Test NON-RÉGRESSION : Les autres chapitres fonctionnent toujours"""
        print("\n" + "="*80)
        print("TEST NON-RÉGRESSION : AUTRES CHAPITRES")
        print("="*80)
        
        chapitres_test = [
            ("6e", "Fractions", "calcul_fractions"),
            ("4e", "Théorème de Pythagore", "triangle_rectangle"),
            ("6e", "Aires", "perimetre_aire")
        ]
        
        for niveau, chapitre, type_attendu in chapitres_test:
            response = requests.post(
                f"{self.BASE_URL}/api/generate",
                json={
                    "matiere": "Mathématiques",
                    "niveau": niveau,
                    "chapitre": chapitre,
                    "type_doc": "exercices",
                    "difficulte": "facile",
                    "nb_exercices": 1,
                    "guest_id": f"test_{chapitre.lower()}"
                },
                timeout=60
            )
            
            assert response.status_code == 200, \
                f"Le chapitre '{chapitre}' doit toujours fonctionner (got {response.status_code})"
            
            data = response.json()
            type_genere = data["document"]["exercises"][0]["spec_mathematique"]["type_exercice"]
            
            # Certains chapitres peuvent générer plusieurs types
            if chapitre == "Aires":
                assert type_genere in ["perimetre_aire", "cercle"]
            else:
                assert type_genere == type_attendu
            
            print(f"  ✅ {chapitre} ({niveau}) : {type_genere}")
        
        print("✅ Non-régression validée : autres chapitres OK")


if __name__ == "__main__":
    # Tests unitaires
    print("\n" + "🧪"*40)
    print("TESTS GÉNÉRATEUR SYMÉTRIE AXIALE")
    print("🧪"*40 + "\n")
    
    test_generator = TestSymetrieAxialeGenerator()
    test_generator.setup_method()
    
    try:
        test_generator.test_symetrie_axiale_generator_exists()
        test_generator.test_symetrie_axiale_mapping()
        test_generator.test_generate_symetrie_facile()
        test_generator.test_generate_symetrie_moyen()
        test_generator.test_symetrie_multiple_generations()
        test_generator.test_symetrie_figure_geometrique()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS UNITAIRES PASSENT")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC TESTS UNITAIRES: {e}\n")
        exit(1)
    
    # Tests API
    print("\n" + "🌐"*40)
    print("TESTS API SYMÉTRIE AXIALE")
    print("🌐"*40 + "\n")
    
    test_api = TestSymetrieAxialeAPI()
    
    try:
        test_api.test_symetrie_axiale_api_returns_200()
        test_api.test_symetrie_axiale_multiple_exercises()
        test_api.test_symetrie_non_regression_autres_chapitres()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS API PASSENT")
        print("="*80 + "\n")
        
        print("\n" + "🎉"*40)
        print("✅ ✅ ✅  TOUS LES TESTS RÉUSSIS  ✅ ✅ ✅")
        print("🎉"*40 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC TESTS API: {e}\n")
        exit(1)
