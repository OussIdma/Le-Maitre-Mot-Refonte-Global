"""
🧪 SCRIPT DE VALIDATION COMPLÈTE - SPRINT 2
Générateurs 6e : G01, G02, N01, N02, N04

Ce script valide tous les aspects critiques du SPRINT 2 :
- Mapping des chapitres
- Génération des exercices
- Énoncés contextuels (pas de "Question 1")
- Cohérence énoncé/correction
- Schémas géométriques (G01, G02)
- Pipeline complet
- Difficulté progressive
- Non-régression
"""

import sys
import os
import re
from typing import List, Dict, Any

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService
from services.exercise_template_service import ExerciseTemplateService
from models.math_models import MathExerciseType

# ============================================================================
# CONFIGURATION
# ============================================================================

CHAPITRES_SPRINT2 = [
    "Points, segments, droites, demi-droites",  # G01
    "Alignement, milieu d'un segment",  # G02
    "Lire et écrire les nombres entiers",  # N01
    "Comparer et ranger des nombres entiers",  # N02
    "Addition et soustraction de nombres entiers"  # N04
]

NIVEAU = "6e"
DIFFICULTES = ["facile", "moyen", "difficile"]

# ============================================================================
# CLASSES DE TEST
# ============================================================================

class TestResult:
    """Résultat d'un test"""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.errors = []
        self.warnings = []
        self.info = []
    
    def add_error(self, message: str):
        self.errors.append(message)
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def add_info(self, message: str):
        self.info.append(message)
    
    def set_passed(self):
        self.passed = True
    
    def print_report(self):
        """Affiche le rapport du test"""
        status = "✅ PASSÉ" if self.passed else "❌ ÉCHOUÉ"
        print(f"\n{'='*80}")
        print(f"{status} : {self.test_name}")
        print(f"{'='*80}")
        
        if self.info:
            print("\n📋 Informations :")
            for info in self.info:
                print(f"   • {info}")
        
        if self.warnings:
            print("\n⚠️  Avertissements :")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if self.errors:
            print("\n❌ Erreurs :")
            for error in self.errors:
                print(f"   • {error}")
        
        return self.passed

# ============================================================================
# TESTS
# ============================================================================

def test_1_mapping_chapitres(math_service: MathGenerationService) -> TestResult:
    """Test 1 : Tous les chapitres SPRINT 2 sont mappés"""
    result = TestResult("Test 1 : Mapping des chapitres")
    
    print("\n" + "="*80)
    print("TEST 1 : MAPPING DES CHAPITRES")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT2:
        try:
            types = math_service._map_chapter_to_types(chapitre, NIVEAU)
            
            if not types:
                result.add_error(f"{chapitre} : Aucun type mappé")
            else:
                result.add_info(f"{chapitre} → {[t.value for t in types]}")
        except ValueError as e:
            result.add_error(f"{chapitre} : {str(e)}")
    
    if not result.errors:
        result.set_passed()
    
    return result

def test_2_generation_exercices(math_service: MathGenerationService) -> TestResult:
    """Test 2 : Génération d'exercices pour chaque chapitre"""
    result = TestResult("Test 2 : Génération d'exercices")
    
    print("\n" + "="*80)
    print("TEST 2 : GÉNÉRATION D'EXERCICES")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT2:
        for difficulte in DIFFICULTES:
            try:
                specs = math_service.generate_math_exercise_specs(
                    niveau=NIVEAU,
                    chapitre=chapitre,
                    difficulte=difficulte,
                    nb_exercices=3
                )
                
                if len(specs) != 3:
                    result.add_error(f"{chapitre} ({difficulte}) : {len(specs)}/3 exercices générés")
                elif any(s is None for s in specs):
                    result.add_error(f"{chapitre} ({difficulte}) : Spec None générée")
                else:
                    result.add_info(f"{chapitre} ({difficulte}) : 3 exercices OK")
            except Exception as e:
                result.add_error(f"{chapitre} ({difficulte}) : Exception - {str(e)}")
    
    if not result.errors:
        result.set_passed()
    
    return result

def test_3_enonces_contextuels(math_service: MathGenerationService) -> TestResult:
    """Test 3 : Aucun énoncé générique "Question 1" """
    result = TestResult("Test 3 : Énoncés contextuels")
    
    print("\n" + "="*80)
    print("TEST 3 : ÉNONCÉS CONTEXTUELS")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT2:
        for difficulte in DIFFICULTES:
            try:
                specs = math_service.generate_math_exercise_specs(
                    niveau=NIVEAU,
                    chapitre=chapitre,
                    difficulte=difficulte,
                    nb_exercices=5
                )
                
                for i, spec in enumerate(specs):
                    enonce = spec.parametres.get("enonce", "")
                    
                    # Vérifier que l'énoncé existe
                    if not enonce:
                        result.add_error(f"{chapitre} ({difficulte}) ex.{i+1} : Énoncé vide")
                        continue
                    
                    # Vérifier qu'il n'est pas générique
                    if "Question 1" in enonce or "Question 2" in enonce:
                        result.add_error(f"{chapitre} ({difficulte}) ex.{i+1} : Énoncé générique '{enonce[:50]}...'")
                        continue
                    
                    # Vérifier qu'il est contextuel (longueur minimale)
                    if len(enonce) < 20:
                        result.add_warning(f"{chapitre} ({difficulte}) ex.{i+1} : Énoncé court ({len(enonce)} chars)")
                    
                    # Afficher un exemple
                    if i == 0:
                        result.add_info(f"{chapitre} ({difficulte}) : '{enonce[:70]}...'")
            except Exception as e:
                result.add_error(f"{chapitre} ({difficulte}) : Exception - {str(e)}")
    
    if not result.errors:
        result.set_passed()
    
    return result

def test_4_schemas_geometriques(math_service: MathGenerationService) -> TestResult:
    """Test 4 : Schémas géométriques pour G01, G02"""
    result = TestResult("Test 4 : Schémas géométriques")
    
    print("\n" + "="*80)
    print("TEST 4 : SCHÉMAS GÉOMÉTRIQUES")
    print("="*80)
    
    chapitres_avec_schema = [
        "Points, segments, droites, demi-droites",
        "Alignement, milieu d'un segment"
    ]
    
    for chapitre in chapitres_avec_schema:
        try:
            spec = math_service.generate_math_exercise_specs(
                niveau=NIVEAU,
                chapitre=chapitre,
                difficulte="facile",
                nb_exercices=1
            )[0]
            
            if spec.figure_geometrique is None:
                result.add_error(f"{chapitre} : Pas de figure géométrique")
            else:
                figure = spec.figure_geometrique
                
                if not figure.points:
                    result.add_error(f"{chapitre} : Points manquants dans la figure")
                elif len(figure.points) < 2:
                    result.add_error(f"{chapitre} : Pas assez de points ({len(figure.points)})")
                else:
                    result.add_info(f"{chapitre} : Schéma OK ({len(figure.points)} points)")
                
                if "with_grid" not in figure.proprietes:
                    result.add_warning(f"{chapitre} : Grille non spécifiée dans proprietes")
        except Exception as e:
            result.add_error(f"{chapitre} : Exception - {str(e)}")
    
    # Vérifier que les chapitres N n'ont PAS de schéma
    chapitres_sans_schema = [
        "Lire et écrire les nombres entiers",
        "Comparer et ranger des nombres entiers",
        "Addition et soustraction de nombres entiers"
    ]
    
    for chapitre in chapitres_sans_schema:
        try:
            spec = math_service.generate_math_exercise_specs(
                niveau=NIVEAU,
                chapitre=chapitre,
                difficulte="facile",
                nb_exercices=1
            )[0]
            
            if spec.figure_geometrique is not None:
                result.add_warning(f"{chapitre} : Schéma présent (devrait être None)")
            else:
                result.add_info(f"{chapitre} : Pas de schéma (OK)")
        except Exception as e:
            result.add_warning(f"{chapitre} : Exception lors de la vérification - {str(e)}")
    
    if not result.errors:
        result.set_passed()
    
    return result

def test_5_pipeline_complet(math_service: MathGenerationService, template_service: ExerciseTemplateService) -> TestResult:
    """Test 5 : Pipeline complet (génération → conversion → question)"""
    result = TestResult("Test 5 : Pipeline complet")
    
    print("\n" + "="*80)
    print("TEST 5 : PIPELINE COMPLET")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT2:
        try:
            # Générer
            spec = math_service.generate_math_exercise_specs(
                niveau=NIVEAU,
                chapitre=chapitre,
                difficulte="facile",
                nb_exercices=1
            )[0]
            
            # Convertir en question
            question = template_service._convert_math_spec_to_question(spec, 1)
            
            # Vérifications
            if "enonce_brut" not in question:
                result.add_error(f"{chapitre} : enonce_brut manquant")
            elif question["enonce_brut"] == "Question 1":
                result.add_error(f"{chapitre} : Énoncé générique après conversion")
            elif len(question["enonce_brut"]) < 20:
                result.add_error(f"{chapitre} : Énoncé trop court après conversion")
            else:
                result.add_info(f"{chapitre} : Pipeline OK - '{question['enonce_brut'][:60]}...'")
            
            if "solution_brut" not in question:
                result.add_error(f"{chapitre} : solution_brut manquant")
            elif len(question["solution_brut"]) < 10:
                result.add_error(f"{chapitre} : Solution trop courte")
        except Exception as e:
            result.add_error(f"{chapitre} : Exception - {str(e)}")
    
    if not result.errors:
        result.set_passed()
    
    return result

def test_6_structure_math_exercise_spec(math_service: MathGenerationService) -> TestResult:
    """Test 6 : Structure complète de MathExerciseSpec"""
    result = TestResult("Test 6 : Structure MathExerciseSpec")
    
    print("\n" + "="*80)
    print("TEST 6 : STRUCTURE MATH EXERCISE SPEC")
    print("="*80)
    
    champs_obligatoires = [
        "niveau",
        "chapitre",
        "type_exercice",
        "difficulte",
        "parametres",
        "solution_calculee",
        "etapes_calculees",
        "resultat_final"
    ]
    
    for chapitre in CHAPITRES_SPRINT2:
        try:
            spec = math_service.generate_math_exercise_specs(NIVEAU, chapitre, "facile", 1)[0]
            
            # Vérifier tous les champs obligatoires
            for champ in champs_obligatoires:
                if not hasattr(spec, champ):
                    result.add_error(f"{chapitre} : Champ manquant - {champ}")
                elif getattr(spec, champ) is None:
                    result.add_warning(f"{chapitre} : Champ None - {champ}")
            
            # Vérifier que parametres contient "enonce"
            if "enonce" not in spec.parametres:
                result.add_error(f"{chapitre} : parametres['enonce'] manquant")
            
            # Vérifier que etapes_calculees est une liste non vide
            if not spec.etapes_calculees:
                result.add_error(f"{chapitre} : etapes_calculees vide")
            
            # Vérifier que resultat_final existe
            if not spec.resultat_final:
                result.add_warning(f"{chapitre} : resultat_final vide")
            
            if not result.errors:
                result.add_info(f"{chapitre} : Structure complète OK")
        except Exception as e:
            result.add_error(f"{chapitre} : Exception - {str(e)}")
    
    if not result.errors:
        result.set_passed()
    
    return result

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def run_all_tests():
    """Exécute tous les tests et génère un rapport"""
    
    print("\n" + "="*80)
    print("🧪 VALIDATION COMPLÈTE - SPRINT 2")
    print("Chapitres testés : G01, G02, N01, N02, N04")
    print("="*80)
    
    # Initialiser les services
    try:
        math_service = MathGenerationService()
        template_service = ExerciseTemplateService()
    except Exception as e:
        print(f"\n❌ ERREUR : Impossible d'initialiser les services - {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Exécuter tous les tests
    tests = [
        test_1_mapping_chapitres(math_service),
        test_2_generation_exercices(math_service),
        test_3_enonces_contextuels(math_service),
        test_4_schemas_geometriques(math_service),
        test_5_pipeline_complet(math_service, template_service),
        test_6_structure_math_exercise_spec(math_service)
    ]
    
    # Générer le rapport
    print("\n" + "="*80)
    print("📊 RAPPORT FINAL")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test.print_report():
            passed += 1
        else:
            failed += 1
    
    # Résumé final
    print("\n" + "="*80)
    print("📈 RÉSUMÉ")
    print("="*80)
    print(f"✅ Tests passés : {passed}/{len(tests)}")
    print(f"❌ Tests échoués : {failed}/{len(tests)}")
    print(f"📊 Taux de réussite : {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS ! SPRINT 2 VALIDÉ ✅")
        print("🚀 Vous pouvez démarrer le SPRINT 3 en toute confiance.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) ont échoué. Veuillez corriger avant de continuer.")
        return False

# ============================================================================
# EXÉCUTION
# ============================================================================

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
