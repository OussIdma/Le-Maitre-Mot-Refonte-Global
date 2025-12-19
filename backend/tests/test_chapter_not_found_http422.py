"""
Tests d'intégration pour vérifier que les chapitres non mappés retournent HTTP 422
Au lieu de générer un exercice incorrect silencieusement
"""

import pytest
import requests
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestChapterNotFoundHTTP422:
    """Tests pour vérifier le comportement HTTP 422 pour chapitres non mappés"""
    
    BASE_URL = "http://localhost:8001"
    
    def test_symetrie_axiale_returns_200(self):
        """Test : Symétrie axiale doit maintenant retourner HTTP 200 (générateur implémenté)"""
        print("\n" + "="*80)
        print("TEST : SYMÉTRIE AXIALE → HTTP 200 (GÉNÉRATEUR IMPLÉMENTÉ)")
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
                "guest_id": "test_symetrie_200"
            },
            timeout=60
        )
        
        print(f"Status code: {response.status_code}")
        
        # APRÈS implémentation du générateur : doit retourner 200
        assert response.status_code == 200, \
            f"❌ Symétrie axiale doit maintenant retourner 200 (générateur implémenté), got {response.status_code}"
        
        # Vérifier que l'exercice est du bon type
        data = response.json()
        assert "document" in data, "La réponse doit contenir 'document'"
        assert "exercises" in data["document"], "Le document doit contenir 'exercises'"
        
        ex = data["document"]["exercises"][0]
        type_ex = ex["spec_mathematique"]["type_exercice"]
        
        print(f"Type d'exercice généré : {type_ex}")
        
        assert type_ex == "symetrie_axiale", \
            f"Type doit être 'symetrie_axiale', got '{type_ex}'"
        
        print("✅ Test réussi : HTTP 200 avec exercice de symétrie axiale correct")
    
    def test_symetrie_centrale_returns_422(self):
        """Test : Symétrie centrale (5e) doit aussi retourner HTTP 422"""
        print("\n" + "="*80)
        print("TEST : SYMÉTRIE CENTRALE (5e) → HTTP 422")
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
                "guest_id": "test_symetrie_centrale_422"
            },
            timeout=60
        )
        
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 422, \
            f"❌ Expected 422, got {response.status_code}"
        
        print("✅ Test réussi : HTTP 422 retourné pour Symétrie centrale")
    
    def test_existing_chapter_aires_returns_200(self):
        """Test NON-RÉGRESSION : Aires (chapitre existant) doit retourner HTTP 200"""
        print("\n" + "="*80)
        print("TEST NON-RÉGRESSION : AIRES → HTTP 200 (chapitre existant)")
        print("="*80)
        
        response = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": "6e",
                "chapitre": "Aires",
                "type_doc": "exercices",
                "difficulte": "facile",
                "nb_exercices": 1,
                "guest_id": "test_aires_200"
            },
            timeout=60
        )
        
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 200, \
            f"❌ Chapitre existant 'Aires' doit retourner 200, got {response.status_code}"
        
        data = response.json()
        assert "document" in data, "La réponse doit contenir 'document'"
        assert "exercises" in data["document"], "Le document doit contenir 'exercises'"
        assert len(data["document"]["exercises"]) > 0, "Il doit y avoir au moins 1 exercice"
        
        # Vérifier que l'exercice est bien du bon type
        ex = data["document"]["exercises"][0]
        assert "spec_mathematique" in ex, "L'exercice doit contenir 'spec_mathematique'"
        type_ex = ex["spec_mathematique"]["type_exercice"]
        # Aires peut générer différents types (perimetre_aire, cercle)
        assert type_ex in ["perimetre_aire", "cercle"], \
            f"Type d'exercice pour Aires doit être perimetre_aire ou cercle, got '{type_ex}'"
        
        print(f"✅ Exercice généré avec succès : type={type_ex}")
        print("✅ Test réussi : Chapitre existant fonctionne correctement")
    
    def test_existing_chapter_pythagore_returns_200(self):
        """Test NON-RÉGRESSION : Théorème de Pythagore doit retourner HTTP 200"""
        print("\n" + "="*80)
        print("TEST NON-RÉGRESSION : THÉORÈME DE PYTHAGORE → HTTP 200")
        print("="*80)
        
        response = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": "4e",
                "chapitre": "Théorème de Pythagore",
                "type_doc": "exercices",
                "difficulte": "facile",
                "nb_exercices": 1,
                "guest_id": "test_pythagore_200"
            },
            timeout=60
        )
        
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 200, \
            f"❌ Chapitre existant 'Théorème de Pythagore' doit retourner 200, got {response.status_code}"
        
        data = response.json()
        ex = data["document"]["exercises"][0]
        type_ex = ex["spec_mathematique"]["type_exercice"]
        
        assert type_ex == "triangle_rectangle", \
            f"Type d'exercice pour Pythagore doit être 'triangle_rectangle', got '{type_ex}'"
        
        print(f"✅ Exercice Pythagore généré : type={type_ex}")
        print("✅ Test réussi : Pythagore fonctionne correctement")
    
    def test_existing_chapter_fractions_returns_200(self):
        """Test NON-RÉGRESSION : Fractions doit retourner HTTP 200"""
        print("\n" + "="*80)
        print("TEST NON-RÉGRESSION : FRACTIONS → HTTP 200")
        print("="*80)
        
        response = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": "6e",
                "chapitre": "Fractions",
                "type_doc": "exercices",
                "difficulte": "facile",
                "nb_exercices": 1,
                "guest_id": "test_fractions_200"
            },
            timeout=60
        )
        
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 200, \
            f"❌ Chapitre existant 'Fractions' doit retourner 200, got {response.status_code}"
        
        data = response.json()
        ex = data["document"]["exercises"][0]
        type_ex = ex["spec_mathematique"]["type_exercice"]
        
        assert type_ex == "calcul_fractions", \
            f"Type d'exercice pour Fractions doit être 'calcul_fractions', got '{type_ex}'"
        
        print(f"✅ Exercice Fractions généré : type={type_ex}")
        print("✅ Test réussi : Fractions fonctionne correctement")
    
    def test_invalid_chapter_random_returns_422(self):
        """Test : Un chapitre complètement inventé doit retourner HTTP 422"""
        print("\n" + "="*80)
        print("TEST : CHAPITRE INVENTÉ → HTTP 422")
        print("="*80)
        
        response = requests.post(
            f"{self.BASE_URL}/api/generate",
            json={
                "matiere": "Mathématiques",
                "niveau": "6e",
                "chapitre": "Chapitre Totalement Inventé XYZ123",
                "type_doc": "exercices",
                "difficulte": "facile",
                "nb_exercices": 1,
                "guest_id": "test_inventé_422"
            },
            timeout=60
        )
        
        print(f"Status code: {response.status_code}")
        
        # Ce chapitre n'existe même pas dans le curriculum, donc devrait être rejeté
        # soit par la validation curriculum (400), soit par le mapping (422)
        assert response.status_code in [400, 422], \
            f"❌ Chapitre inventé doit retourner 400 ou 422, got {response.status_code}"
        
        print(f"✅ Test réussi : Chapitre inventé rejeté avec {response.status_code}")


if __name__ == "__main__":
    # Exécution directe
    test = TestChapterNotFoundHTTP422()
    
    print("\n" + "🧪"*40)
    print("TESTS HTTP 422 - CHAPITRES NON MAPPÉS")
    print("🧪"*40 + "\n")
    
    try:
        # Test : Symétrie axiale fonctionne maintenant (200)
        test.test_symetrie_axiale_returns_200()
        
        # Test critique : Symétrie centrale doit retourner 422 (pas encore implémenté)
        test.test_symetrie_centrale_returns_422()
        
        # Tests de non-régression (chapitres existants)
        test.test_existing_chapter_aires_returns_200()
        test.test_existing_chapter_pythagore_returns_200()
        test.test_existing_chapter_fractions_returns_200()
        
        # Tests de sécurité
        test.test_invalid_chapter_random_returns_422()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS HTTP 422 PASSENT")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DES TESTS: {e}\n")
        exit(1)
