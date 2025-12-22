"""
Tests d'intégration pour l'endpoint /api/generate
Vérifie que la route API utilisée par le frontend renvoie TOUJOURS un énoncé
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app

client = TestClient(app)


class TestAPIGenerateIntegration:
    """Tests d'intégration pour /api/generate - Route réelle utilisée par le frontend"""
    
    # Configuration des tests - matières et chapitres réels
    TEST_CONFIGS = [
        {"matiere": "Mathématiques", "niveau": "6e", "chapitre": "Aires"},
        {"matiere": "Mathématiques", "niveau": "5e", "chapitre": "Aires et périmètres"},
        {"matiere": "Mathématiques", "niveau": "4e", "chapitre": "Théorème de Pythagore"},
        {"matiere": "Mathématiques", "niveau": "3e", "chapitre": "Théorème de Thalès"},
        {"matiere": "Mathématiques", "niveau": "3e", "chapitre": "Trigonométrie"},
    ]
    
    def test_api_generate_returns_enonce_for_all_configs(self):
        """Test critique : /api/generate doit TOUJOURS renvoyer un énoncé pour chaque exercice"""
        
        print("\n" + "="*80)
        print("TEST INTÉGRATION API /api/generate")
        print("="*80 + "\n")
        
        echecs = []
        succes = 0
        
        for config in self.TEST_CONFIGS:
            print(f"Test: {config['matiere']} > {config['niveau']} > {config['chapitre']}")
            print("-"*80)
            
            # Appel API exactement comme le frontend
            response = client.post("/api/generate", json={
                "matiere": config["matiere"],
                "niveau": config["niveau"],
                "chapitre": config["chapitre"],
                "type_doc": "exercices",
                "difficulte": "facile",
                "nb_exercices": 2,  # Tester avec plusieurs exercices
                "guest_id": "test_integration"
            })
            
            # Vérifications
            assert response.status_code == 200, f"Status code {response.status_code} pour {config}"
            
            data = response.json()
            assert "document" in data, "Clé 'document' manquante dans la réponse"
            
            document = data["document"]
            assert "exercises" in document, "Clé 'exercises' manquante dans le document"
            
            exercises = document["exercises"]
            assert len(exercises) > 0, "Aucun exercice généré"
            
            # VÉRIFICATION CRITIQUE : Chaque exercice doit avoir un énoncé
            for i, exercise in enumerate(exercises):
                exercise_id = exercise.get("id", f"exercice_{i}")
                
                # Vérifier la présence de la clé "enonce"
                if "enonce" not in exercise:
                    error_msg = f"Exercice {exercise_id}: Clé 'enonce' MANQUANTE"
                    print(f"   ❌ {error_msg}")
                    print(f"      Clés présentes: {list(exercise.keys())}")
                    echecs.append((config, error_msg))
                    continue
                
                # Vérifier que l'énoncé n'est pas vide
                enonce = exercise["enonce"]
                if not enonce:
                    error_msg = f"Exercice {exercise_id}: énoncé VIDE (None, '', ou whitespace)"
                    print(f"   ❌ {error_msg}")
                    print(f"      Valeur: {repr(enonce)}")
                    echecs.append((config, error_msg))
                    continue
                
                if not enonce.strip():
                    error_msg = f"Exercice {exercise_id}: énoncé VIDE (whitespace uniquement)"
                    print(f"   ❌ {error_msg}")
                    echecs.append((config, error_msg))
                    continue
                
                if len(enonce.strip()) < 10:
                    error_msg = f"Exercice {exercise_id}: énoncé TROP COURT ({len(enonce.strip())} caractères)"
                    print(f"   ⚠️  {error_msg}")
                    print(f"      Énoncé: '{enonce}'")
                    echecs.append((config, error_msg))
                    continue
                
                # Succès
                print(f"   ✅ Exercice {i+1}: énoncé OK ({len(enonce)} caractères)")
                print(f"      Preview: {enonce[:80]}...")
                succes += 1
            
            print()
        
        # Rapport final
        print("="*80)
        print("RÉSUMÉ DES TESTS D'INTÉGRATION")
        print("="*80)
        print(f"✅ Exercices avec énoncé valide: {succes}")
        print(f"❌ Exercices en échec: {len(echecs)}")
        
        if echecs:
            print("\n⚠️  ÉCHECS DÉTAILLÉS :")
            for config, error in echecs:
                print(f"   • {config['matiere']} {config['niveau']} - {config['chapitre']}")
                print(f"     {error}")
        
        print("="*80 + "\n")
        
        # Le test échoue s'il y a des échecs
        assert len(echecs) == 0, f"{len(echecs)} exercice(s) sans énoncé valide détecté(s)"
    
    def test_api_generate_structure_complete(self):
        """Test que la réponse API a la structure attendue par le frontend"""
        
        print("\n" + "="*80)
        print("TEST STRUCTURE RÉPONSE API")
        print("="*80 + "\n")
        
        response = client.post("/api/generate", json={
            "matiere": "Mathématiques",
            "niveau": "4e",
            "chapitre": "Théorème de Pythagore",
            "type_doc": "exercices",
            "difficulte": "moyen",
            "nb_exercices": 1,
            "guest_id": "test_structure"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Structure attendue
        assert "document" in data
        document = data["document"]
        
        # Champs obligatoires du document
        required_document_fields = ["id", "matiere", "niveau", "chapitre", "exercises"]
        for field in required_document_fields:
            assert field in document, f"Champ '{field}' manquant dans le document"
        
        # Champs obligatoires de chaque exercice
        exercises = document["exercises"]
        assert len(exercises) > 0
        
        exercise = exercises[0]
        required_exercise_fields = ["id", "enonce", "solution", "bareme", "difficulte"]
        
        for field in required_exercise_fields:
            assert field in exercise, f"Champ '{field}' manquant dans l'exercice"
        
        # Vérifier les types
        assert isinstance(exercise["enonce"], str), "enonce doit être une string"
        assert isinstance(exercise["solution"], dict), "solution doit être un dict"
        assert isinstance(exercise["bareme"], list), "bareme doit être une liste"
        
        print("✅ Structure de la réponse API conforme")
        print(f"   Document ID: {document['id']}")
        print(f"   Nombre d'exercices: {len(exercises)}")
        print(f"   Énoncé présent: {len(exercise['enonce'])} caractères")
        print("="*80 + "\n")
    
    def test_api_generate_avec_figure_svg(self):
        """Test que les exercices géométriques incluent le SVG"""
        
        print("\n" + "="*80)
        print("TEST FIGURE SVG DANS LA RÉPONSE API")
        print("="*80 + "\n")
        
        # Tester avec un chapitre géométrique
        response = client.post("/api/generate", json={
            "matiere": "Mathématiques",
            "niveau": "3e",
            "chapitre": "Théorème de Thalès",
            "type_doc": "exercices",
            "difficulte": "facile",
            "nb_exercices": 1,
            "guest_id": "test_svg"
        })
        
        assert response.status_code == 200
        data = response.json()
        exercise = data["document"]["exercises"][0]
        
        # Vérifier énoncé
        assert "enonce" in exercise
        assert exercise["enonce"]
        print(f"✅ Énoncé présent: {len(exercise['enonce'])} caractères")
        
        # Vérifier figure SVG (optionnel pour géométrie)
        if "figure_svg" in exercise and exercise["figure_svg"]:
            print(f"✅ Figure SVG présente: {len(exercise['figure_svg'])} caractères")
            assert "<svg" in exercise["figure_svg"], "SVG invalide"
        else:
            print(f"⚠️  Pas de figure SVG (peut être normal)")
        
        # Vérifier spec_mathematique (nouvelle architecture)
        if "spec_mathematique" in exercise:
            print(f"✅ Spec mathématique présente")
        
        print("="*80 + "\n")
    
    def test_api_generate_gestion_erreurs(self):
        """Test que l'API gère correctement les erreurs sans crasher"""
        
        print("\n" + "="*80)
        print("TEST GESTION DES ERREURS API")
        print("="*80 + "\n")
        
        # Test avec matière invalide
        response = client.post("/api/generate", json={
            "matiere": "MatiereInexistante",
            "niveau": "6e",
            "chapitre": "Test",
            "type_doc": "exercices",
            "difficulte": "facile",
            "nb_exercices": 1,
            "guest_id": "test_error"
        })
        
        # Doit retourner une erreur propre, pas un crash
        assert response.status_code in [400, 404, 423], f"Status code attendu 400/404/423, reçu {response.status_code}"
        print(f"✅ Erreur gérée correctement: status {response.status_code}")
        
        # Test avec niveau invalide
        response = client.post("/api/generate", json={
            "matiere": "Mathématiques",
            "niveau": "NiveauInvalide",
            "chapitre": "Test",
            "type_doc": "exercices",
            "difficulte": "facile",
            "nb_exercices": 1,
            "guest_id": "test_error"
        })
        
        assert response.status_code in [400, 404], f"Status code attendu 400/404, reçu {response.status_code}"
        print(f"✅ Niveau invalide géré: status {response.status_code}")
        
        print("="*80 + "\n")


if __name__ == "__main__":
    # Exécution directe pour tests rapides
    test = TestAPIGenerateIntegration()
    
    print("\n🧪 LANCEMENT DES TESTS D'INTÉGRATION API\n")
    
    try:
        test.test_api_generate_returns_enonce_for_all_configs()
        test.test_api_generate_structure_complete()
        test.test_api_generate_avec_figure_svg()
        test.test_api_generate_gestion_erreurs()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS D'INTÉGRATION PASSENT")
        print("="*80 + "\n")
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DES TESTS: {e}\n")
        sys.exit(1)
