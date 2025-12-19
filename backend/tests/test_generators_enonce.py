"""
Tests pour vérifier que TOUS les générateurs renvoient TOUJOURS un énoncé non vide
Audit critique du pipeline de génération d'exercices
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService
from services.math_text_service import MathTextService
import asyncio


class TestGenerateursEnonce:
    """Tests pour vérifier que tous les générateurs produisent un énoncé valide"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.math_service = MathGenerationService()
        self.text_service = MathTextService()
    
    # Configuration de tous les générateurs
    GENERATEURS = [
        ("4e", "Théorème de Pythagore", "triangle_rectangle"),
        ("5e", "Nombres relatifs", "calcul_relatifs"),
        ("3e", "Équations du premier degré", "equation_1er_degre"),
        ("4e", "Fractions", "calcul_fractions"),
        ("6e", "Nombres décimaux", "calcul_decimaux"),
        ("5e", "Triangles", "triangle_quelconque"),
        ("4e", "Proportionnalité", "proportionnalite"),
        ("6e", "Aires", "perimetre_aire"),
        ("5e", "Aires et périmètres", "rectangle"),
        ("4e", "Volumes", "volume"),
        ("3e", "Statistiques", "statistiques"),
        ("3e", "Probabilités", "probabilites"),
        ("4e", "Puissances", "puissances"),
        ("6e", "Aires", "cercle"),
        ("3e", "Théorème de Thalès", "thales"),
        ("3e", "Trigonométrie", "trigonometrie"),
    ]
    
    def test_tous_generateurs_renvoient_enonce_non_vide(self):
        """Test critique : TOUS les générateurs doivent renvoyer un énoncé non vide"""
        
        print("\n" + "="*80)
        print("TEST CRITIQUE : VÉRIFICATION DES ÉNONCÉS")
        print("="*80 + "\n")
        
        echecs = []
        succes = []
        
        for niveau, chapitre, gen_name in self.GENERATEURS:
            print(f"Test: {gen_name:30} ({niveau} - {chapitre})")
            print("-"*80)
            
            try:
                # Générer la spec mathématique (pure Python, pas d'IA)
                specs = self.math_service.generate_math_exercise_specs(
                    niveau=niveau,
                    chapitre=chapitre,
                    difficulte="facile",
                    nb_exercices=1
                )
                
                assert len(specs) > 0, "Aucune spec générée"
                spec = specs[0]
                
                # Tester le fallback (sans IA)
                fallback_text = self.text_service._generate_fallback_text(spec)
                
                # VÉRIFICATIONS CRITIQUES
                assert fallback_text is not None, "fallback_text est None"
                assert hasattr(fallback_text, 'enonce'), "Pas d'attribut 'enonce'"
                assert fallback_text.enonce is not None, "enonce est None"
                assert fallback_text.enonce != "", "enonce est vide"
                assert len(fallback_text.enonce) > 10, f"enonce trop court: '{fallback_text.enonce}'"
                
                print(f"   ✅ SUCCÈS")
                print(f"   Énoncé: {fallback_text.enonce[:80]}...")
                succes.append(gen_name)
                
            except AssertionError as e:
                print(f"   ❌ ÉCHEC: {e}")
                echecs.append((gen_name, str(e)))
            except Exception as e:
                print(f"   ❌ ERREUR: {e}")
                echecs.append((gen_name, f"Exception: {e}"))
            
            print()
        
        # Rapport final
        print("="*80)
        print("RÉSUMÉ DU TEST")
        print("="*80)
        print(f"✅ Succès: {len(succes)}/{len(self.GENERATEURS)}")
        print(f"❌ Échecs: {len(echecs)}/{len(self.GENERATEURS)}")
        
        if echecs:
            print("\n⚠️  GÉNÉRATEURS EN ÉCHEC :")
            for gen_name, error in echecs:
                print(f"   • {gen_name}: {error}")
        
        print("="*80 + "\n")
        
        # Le test échoue s'il y a des échecs
        assert len(echecs) == 0, f"{len(echecs)} générateur(s) ne produisent pas d'énoncé valide"
    
    def test_fallback_generic_fonctionne(self):
        """Test que le fallback générique produit toujours un énoncé"""
        
        # Créer une spec minimale
        from models.math_models import MathExerciseSpec, MathExerciseType, DifficultyLevel
        
        spec = MathExerciseSpec(
            niveau="6e",
            chapitre="Test",
            type_exercice=MathExerciseType.CALCUL_DECIMAUX,
            difficulte=DifficultyLevel.FACILE,
            parametres={"test": True},
            solution_calculee={"resultat": 42},
            etapes_calculees=["Étape 1"],
            resultat_final=42
        )
        
        fallback = self.text_service._fallback_generic(spec)
        
        assert fallback.enonce is not None
        assert fallback.enonce != ""
        assert len(fallback.enonce) > 10
        
        print(f"✅ Fallback générique OK: '{fallback.enonce}'")
    
    def test_integration_complete_avec_fallback(self):
        """Test d'intégration : génération complète avec fallback si l'IA échoue"""
        
        print("\n" + "="*80)
        print("TEST D'INTÉGRATION : GÉNÉRATION COMPLÈTE")
        print("="*80 + "\n")
        
        # Test avec Pythagore
        specs = self.math_service.generate_math_exercise_specs(
            niveau="4e",
            chapitre="Théorème de Pythagore",
            difficulte="facile",
            nb_exercices=1
        )
        
        assert len(specs) > 0, "Aucune spec générée"
        
        # Simuler le pipeline complet avec fallback
        spec = specs[0]
        
        # Utiliser le fallback (pour éviter l'appel IA dans les tests)
        text = self.text_service._generate_fallback_text(spec)
        
        # Créer l'exercice complet
        from models.math_models import GeneratedMathExercise
        exercise = GeneratedMathExercise(spec=spec, texte=text)
        
        # Convertir en dict pour l'API
        exercise_dict = exercise.to_exercise_dict()
        
        # VÉRIFICATIONS CRITIQUES
        assert "enonce" in exercise_dict, "Clé 'enonce' manquante"
        assert exercise_dict["enonce"] is not None, "enonce est None"
        assert exercise_dict["enonce"] != "", "enonce est vide"
        assert len(exercise_dict["enonce"]) > 10, "enonce trop court"
        
        print(f"✅ Exercice complet généré avec succès")
        print(f"   Énoncé: {exercise_dict['enonce'][:100]}...")
        print(f"   Clés présentes: {list(exercise_dict.keys())}")
        
        # Vérifier les autres champs obligatoires
        assert "solution" in exercise_dict
        assert "bareme" in exercise_dict
        
        print("="*80 + "\n")
    
    def test_spec_sans_parametres_optionnels(self):
        """Test avec une spec minimale (sans figure géométrique)"""
        
        from models.math_models import MathExerciseSpec, MathExerciseType, DifficultyLevel
        
        spec = MathExerciseSpec(
            niveau="5e",
            chapitre="Calculs",
            type_exercice=MathExerciseType.CALCUL_RELATIFS,
            difficulte=DifficultyLevel.MOYEN,
            parametres={"a": 5, "b": -3},
            solution_calculee={"resultat": 2},
            etapes_calculees=["5 + (-3) = 2"],
            resultat_final=2
        )
        
        fallback = self.text_service._generate_fallback_text(spec)
        
        assert fallback.enonce is not None
        assert fallback.enonce != ""
        
        print(f"✅ Spec minimale OK: '{fallback.enonce}'")


if __name__ == "__main__":
    # Exécution directe pour tests rapides
    test = TestGenerateursEnonce()
    test.setup_method()
    
    print("\n🧪 LANCEMENT DES TESTS D'ÉNONCÉS\n")
    
    try:
        test.test_tous_generateurs_renvoient_enonce_non_vide()
        test.test_fallback_generic_fonctionne()
        test.test_integration_complete_avec_fallback()
        test.test_spec_sans_parametres_optionnels()
        
        print("\n" + "="*80)
        print("✅ TOUS LES TESTS PASSENT")
        print("="*80 + "\n")
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DES TESTS: {e}\n")
        sys.exit(1)
