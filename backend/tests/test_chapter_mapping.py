"""
Tests critiques de mapping chapitre → générateur
Garantit que tous les chapitres du curriculum génèrent les bons exercices
"""

import pytest
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService, MathExerciseType


class TestChapterMapping:
    """Tests du mapping chapitre → générateur"""
    
    BASE_URL = "http://localhost:8001"
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.math_service = MathGenerationService()
    
    def test_symetrie_axiale_mapping(self):
        """Test CRITIQUE : Symétrie axiale doit générer des exercices géométriques"""
        print("\n" + "="*80)
        print("TEST CRITIQUE : SYMÉTRIE AXIALE")
        print("="*80)
        
        chapitre = "Symétrie axiale"
        niveau = "6e"
        
        # Test unitaire : vérifier le mapping
        types = self.math_service._map_chapter_to_types(chapitre, niveau)
        
        print(f"Chapitre : {chapitre}")
        print(f"Types mappés : {[t.value for t in types]}")
        
        assert len(types) > 0, f"Aucun type mappé pour '{chapitre}'"
        assert MathExerciseType.CALCUL_DECIMAUX not in types, \
            f"❌ ERREUR : '{chapitre}' ne doit PAS générer CALCUL_DECIMAUX"
        
        # Vérifier que c'est un type géométrique
        geometric_types = [
            MathExerciseType.RECTANGLE,
            MathExerciseType.TRIANGLE_QUELCONQUE,
            MathExerciseType.TRIANGLE_RECTANGLE
        ]
        assert any(t in types for t in geometric_types), \
            f"'{chapitre}' doit mapper vers un type géométrique"
        
        print("✅ Mapping correct")
        
        # Test end-to-end : générer via API
        response = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": niveau,
                "chapitre": chapitre,
                "type_doc": "exercices",
                "difficulte": "facile",
                "nb_exercices": 1,
                "guest_id": "test_symetrie"
            },
            timeout=60
        )
        
        assert response.status_code == 200, f"Erreur API : {response.status_code}"
        data = response.json()
        
        ex = data["document"]["exercises"][0]
        type_genere = ex["spec_mathematique"]["type_exercice"]
        
        print(f"Type généré via API : {type_genere}")
        print(f"Énoncé : {ex['enonce'][:80]}...")
        
        assert type_genere != "calcul_decimaux", \
            f"❌ API génère CALCUL_DECIMAUX pour '{chapitre}'"
        
        print("✅ Test end-to-end réussi")
    
    def test_all_6e_chapters_have_mapping(self):
        """Test : Tous les chapitres de 6e doivent avoir un mapping"""
        print("\n" + "="*80)
        print("TEST : TOUS LES CHAPITRES 6e MAPPÉS")
        print("="*80)
        
        # Liste des chapitres 6e (selon curriculum_data.py)
        chapitres_6e = [
            "Nombres entiers et décimaux",
            "Fractions",
            "Proportionnalité",
            "Périmètres et aires",
            "Aires",
            "Volumes",
            "Géométrie dans l'espace",
            "Géométrie dans le plan",
            "Symétrie axiale"
        ]
        
        manquants = []
        
        for chapitre in chapitres_6e:
            try:
                types = self.math_service._map_chapter_to_types(chapitre, "6e")
                if len(types) == 0:
                    manquants.append(chapitre)
                    print(f"❌ {chapitre} : Aucun type mappé")
                else:
                    print(f"✅ {chapitre} : {[t.value for t in types]}")
            except ValueError as e:
                manquants.append(chapitre)
                print(f"❌ {chapitre} : {str(e)}")
        
        assert len(manquants) == 0, \
            f"Chapitres sans mapping : {manquants}"
        
        print(f"\n✅ Tous les chapitres 6e sont mappés ({len(chapitres_6e)}/{len(chapitres_6e)})")
    
    def test_unknown_chapter_raises_error(self):
        """Test : Un chapitre inconnu doit lever une erreur explicite"""
        print("\n" + "="*80)
        print("TEST : SÉCURITÉ - CHAPITRE INCONNU")
        print("="*80)
        
        chapitre_invalide = "Chapitre Inexistant XYZ"
        
        with pytest.raises(ValueError) as exc_info:
            self.math_service._map_chapter_to_types(chapitre_invalide, "6e")
        
        error_message = str(exc_info.value)
        
        print(f"Erreur levée : {error_message[:100]}...")
        
        assert "CHAPITRE NON MAPPÉ" in error_message, \
            "Le message d'erreur doit être explicite"
        assert chapitre_invalide in error_message, \
            "Le message doit contenir le nom du chapitre problématique"
        
        print("✅ Erreur explicite levée correctement")
    
    def test_no_silent_fallback_to_calcul_decimaux(self):
        """Test : Aucun fallback silencieux vers CALCUL_DECIMAUX"""
        print("\n" + "="*80)
        print("TEST : PAS DE FALLBACK SILENCIEUX")
        print("="*80)
        
        # Chapitres qui ne devraient PAS générer CALCUL_DECIMAUX
        chapitres_geometriques = [
            "Symétrie axiale",
            "Théorème de Pythagore",
            "Théorème de Thalès",
            "Trigonométrie"
        ]
        
        for chapitre in chapitres_geometriques:
            types = self.math_service._map_chapter_to_types(chapitre, "4e")  # Niveau générique
            
            assert MathExerciseType.CALCUL_DECIMAUX not in types, \
                f"❌ '{chapitre}' ne doit PAS fallback vers CALCUL_DECIMAUX"
            
            print(f"✅ {chapitre} : Pas de fallback")
        
        print("\n✅ Aucun fallback silencieux détecté")
    
    def test_symetrie_centrale_5e(self):
        """Test : Symétrie centrale (5e) doit être mappée"""
        print("\n" + "="*80)
        print("TEST : SYMÉTRIE CENTRALE (5e)")
        print("="*80)
        
        chapitre = "Symétrie centrale"
        types = self.math_service._map_chapter_to_types(chapitre, "5e")
        
        assert len(types) > 0, f"'{chapitre}' doit être mappé"
        assert MathExerciseType.CALCUL_DECIMAUX not in types, \
            f"'{chapitre}' ne doit pas fallback vers CALCUL_DECIMAUX"
        
        print(f"✅ {chapitre} mappé : {[t.value for t in types]}")
    
    def test_parallelogrammes_5e(self):
        """Test : Parallélogrammes (5e) doit être mappé"""
        print("\n" + "="*80)
        print("TEST : PARALLÉLOGRAMMES (5e)")
        print("="*80)
        
        chapitre = "Parallélogrammes"
        types = self.math_service._map_chapter_to_types(chapitre, "5e")
        
        assert len(types) > 0, f"'{chapitre}' doit être mappé"
        assert MathExerciseType.CALCUL_DECIMAUX not in types
        
        print(f"✅ {chapitre} mappé : {[t.value for t in types]}")
    
    def test_batch_chapters_no_regression(self):
        """Test batch : Vérifier plusieurs chapitres importants"""
        print("\n" + "="*80)
        print("TEST BATCH : NON-RÉGRESSION")
        print("="*80)
        
        # Chapitres critiques à tester
        chapitres_critiques = {
            "6e": ["Symétrie axiale", "Fractions", "Aires"],
            "5e": ["Symétrie centrale", "Parallélogrammes", "Triangles"],
            "4e": ["Théorème de Pythagore", "Équations"],
            "3e": ["Théorème de Thalès", "Trigonométrie", "Probabilités"]
        }
        
        total = 0
        succes = 0
        
        for niveau, chapitres in chapitres_critiques.items():
            print(f"\n📘 {niveau} :")
            for chapitre in chapitres:
                total += 1
                try:
                    types = self.math_service._map_chapter_to_types(chapitre, niveau)
                    
                    if len(types) > 0 and MathExerciseType.CALCUL_DECIMAUX not in types:
                        succes += 1
                        print(f"  ✅ {chapitre}")
                    else:
                        print(f"  ❌ {chapitre} : Fallback détecté")
                        
                except ValueError:
                    print(f"  ❌ {chapitre} : Non mappé")
        
        taux = succes / total * 100
        print(f"\n📊 Taux de succès : {taux:.1f}% ({succes}/{total})")
        
        assert taux >= 90, f"Taux de succès insuffisant : {taux:.1f}% (min 90%)"


if __name__ == "__main__":
    # Exécution directe
    test = TestChapterMapping()
    test.setup_method()
    
    print("\n" + "🧪"*40)
    print("TESTS MAPPING CHAPITRE → GÉNÉRATEUR")
    print("🧪"*40 + "\n")
    
    try:
        test.test_symetrie_axiale_mapping()
        test.test_all_6e_chapters_have_mapping()
        test.test_unknown_chapter_raises_error()
        test.test_no_silent_fallback_to_calcul_decimaux()
        test.test_symetrie_centrale_5e()
        test.test_parallelogrammes_5e()
        test.test_batch_chapters_no_regression()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS DE MAPPING PASSENT")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DES TESTS: {e}\n")
        exit(1)
