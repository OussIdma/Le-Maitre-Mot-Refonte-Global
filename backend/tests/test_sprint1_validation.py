"""
🧪 SCRIPT DE VALIDATION COMPLÈTE - SPRINT 1
Générateurs 6e : G03, N03, SP01

Ce script valide tous les aspects critiques du SPRINT 1 :
- Mapping des chapitres
- Génération des exercices
- Énoncés contextuels (pas de "Question 1")
- Cohérence énoncé/correction
- Schémas géométriques
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

CHAPITRES_SPRINT1 = [
    "Perpendiculaires et parallèles à la règle et à l'équerre",  # G03
    "Droite numérique et repérage",  # N03
    "Lire et compléter des tableaux de données"  # SP01
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
    """Test 1 : Tous les chapitres SPRINT 1 sont mappés"""
    result = TestResult("Test 1 : Mapping des chapitres")
    
    print("\n" + "="*80)
    print("TEST 1 : MAPPING DES CHAPITRES")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT1:
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
    
    for chapitre in CHAPITRES_SPRINT1:
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
    
    for chapitre in CHAPITRES_SPRINT1:
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

def test_4_coherence_enonce_correction(math_service: MathGenerationService) -> TestResult:
    """Test 4 : Cohérence entre énoncé et correction"""
    result = TestResult("Test 4 : Cohérence énoncé/correction")
    
    print("\n" + "="*80)
    print("TEST 4 : COHÉRENCE ÉNONCÉ/CORRECTION")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT1:
        try:
            spec = math_service.generate_math_exercise_specs(
                niveau=NIVEAU,
                chapitre=chapitre,
                difficulte="facile",
                nb_exercices=1
            )[0]
            
            enonce = spec.parametres.get("enonce", "")
            etapes = " ".join(spec.etapes_calculees)
            
            # Extraire les nombres
            nombres_enonce = set(re.findall(r'\d+', enonce))
            nombres_etapes = set(re.findall(r'\d+', etapes))
            
            if nombres_enonce:
                intersection = nombres_enonce & nombres_etapes
                ratio = len(intersection) / len(nombres_enonce) if nombres_enonce else 0
                
                if ratio < 0.3:
                    result.add_error(
                        f"{chapitre} : Cohérence faible ({ratio:.0%}) - "
                        f"Seulement {len(intersection)}/{len(nombres_enonce)} nombres communs"
                    )
                else:
                    result.add_info(
                        f"{chapitre} : Cohérence {ratio:.0%} - "
                        f"{len(intersection)}/{len(nombres_enonce)} nombres communs"
                    )
            else:
                result.add_warning(f"{chapitre} : Aucun nombre dans l'énoncé")
        except Exception as e:
            result.add_error(f"{chapitre} : Exception - {str(e)}")
    
    if not result.errors:
        result.set_passed()
    
    return result

def test_5_schemas_geometriques(math_service: MathGenerationService) -> TestResult:
    """Test 5 : Schémas géométriques pour G03"""
    result = TestResult("Test 5 : Schémas géométriques")
    
    print("\n" + "="*80)
    print("TEST 5 : SCHÉMAS GÉOMÉTRIQUES")
    print("="*80)
    
    chapitre_geometrie = "Perpendiculaires et parallèles à la règle et à l'équerre"
    
    try:
        spec = math_service.generate_math_exercise_specs(
            niveau=NIVEAU,
            chapitre=chapitre_geometrie,
            difficulte="facile",
            nb_exercices=1
        )[0]
        
        if spec.figure_geometrique is None:
            result.add_error(f"{chapitre_geometrie} : Pas de figure géométrique")
        else:
            figure = spec.figure_geometrique
            
            if not figure.points:
                result.add_error(f"{chapitre_geometrie} : Points manquants dans la figure")
            elif len(figure.points) < 2:
                result.add_error(f"{chapitre_geometrie} : Pas assez de points ({len(figure.points)})")
            else:
                result.add_info(f"{chapitre_geometrie} : Schéma OK ({len(figure.points)} points)")
            
            if "with_grid" not in figure.proprietes:
                result.add_warning(f"{chapitre_geometrie} : Grille non spécifiée dans proprietes")
    except Exception as e:
        result.add_error(f"{chapitre_geometrie} : Exception - {str(e)}")
    
    # Vérifier que les autres chapitres n'ont PAS de schéma (sauf si nécessaire)
    chapitres_sans_schema = [
        "Droite numérique et repérage",  # N03 - peut avoir schéma (droite graduée)
        "Lire et compléter des tableaux de données"  # SP01 - peut avoir schéma (tableau)
    ]
    
    for chapitre in chapitres_sans_schema:
        try:
            spec = math_service.generate_math_exercise_specs(
                niveau=NIVEAU,
                chapitre=chapitre,
                difficulte="facile",
                nb_exercices=1
            )[0]
            
            # Note : N03 et SP01 peuvent avoir des schémas (droite graduée, tableau)
            # Donc on ne génère pas d'erreur, juste une info
            if spec.figure_geometrique:
                result.add_info(f"{chapitre} : Schéma présent (OK si nécessaire)")
        except Exception as e:
            result.add_warning(f"{chapitre} : Exception lors de la vérification - {str(e)}")
    
    if not result.errors:
        result.set_passed()
    
    return result

def test_6_pipeline_complet(math_service: MathGenerationService, template_service: ExerciseTemplateService) -> TestResult:
    """Test 6 : Pipeline complet (génération → conversion → question)"""
    result = TestResult("Test 6 : Pipeline complet")
    
    print("\n" + "="*80)
    print("TEST 6 : PIPELINE COMPLET")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT1:
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
            
            # Vérifier figure_html si schéma présent
            if spec.figure_geometrique:
                if "figure_html" not in question:
                    result.add_warning(f"{chapitre} : figure_html manquant malgré figure_geometrique")
                else:
                    result.add_info(f"{chapitre} : figure_html généré")
        except Exception as e:
            result.add_error(f"{chapitre} : Exception - {str(e)}")
    
    if not result.errors:
        result.set_passed()
    
    return result

def test_7_difficulte_progressive(math_service: MathGenerationService) -> TestResult:
    """Test 7 : Les valeurs varient selon la difficulté"""
    result = TestResult("Test 7 : Difficulté progressive")
    
    print("\n" + "="*80)
    print("TEST 7 : DIFFICULTÉ PROGRESSIVE")
    print("="*80)
    
    # Tester sur un chapitre numérique (N03)
    chapitre_test = "Droite numérique et repérage"
    
    valeurs_facile = []
    valeurs_moyen = []
    valeurs_difficile = []
    
    try:
        for _ in range(10):
            spec_f = math_service.generate_math_exercise_specs(NIVEAU, chapitre_test, "facile", 1)[0]
            spec_m = math_service.generate_math_exercise_specs(NIVEAU, chapitre_test, "moyen", 1)[0]
            spec_d = math_service.generate_math_exercise_specs(NIVEAU, chapitre_test, "difficile", 1)[0]
            
            # Extraire valeurs selon le chapitre
            params_f = spec_f.parametres
            params_m = spec_m.parametres
            params_d = spec_d.parametres
            
            # Pour droite numérique, chercher abscisse, max_val, etc.
            if "nombre" in params_f:
                valeurs_facile.append(abs(params_f.get("nombre", 0)))
                valeurs_moyen.append(abs(params_m.get("nombre", 0)))
                valeurs_difficile.append(abs(params_d.get("nombre", 0)))
            elif "max_val" in params_f:
                valeurs_facile.append(params_f.get("max_val", 0))
                valeurs_moyen.append(params_m.get("max_val", 0))
                valeurs_difficile.append(params_d.get("max_val", 0))
        
        if valeurs_facile and valeurs_moyen and valeurs_difficile:
            max_facile = max(valeurs_facile)
            max_moyen = max(valeurs_moyen)
            max_difficile = max(valeurs_difficile)
            
            if max_difficile < max_facile:
                result.add_error(f"{chapitre_test} : Difficulté non progressive (difficile max={max_difficile} < facile max={max_facile})")
            else:
                result.add_info(
                    f"{chapitre_test} : Difficulté progressive - "
                    f"facile max={max_facile}, moyen max={max_moyen}, difficile max={max_difficile}"
                )
        else:
            result.add_warning(f"{chapitre_test} : Impossible d'extraire des valeurs pour tester la progression")
    except Exception as e:
        result.add_error(f"{chapitre_test} : Exception - {str(e)}")
    
    if not result.errors:
        result.set_passed()
    
    return result

def test_8_non_regression(math_service: MathGenerationService) -> TestResult:
    """Test 8 : Les chapitres existants fonctionnent toujours"""
    result = TestResult("Test 8 : Non-régression")
    
    print("\n" + "="*80)
    print("TEST 8 : NON-RÉGRESSION")
    print("="*80)
    
    chapitres_existants = [
        "Symétrie axiale (points, segments, figures)",
        "Nombres décimaux",
        "Fractions",
        "Proportionnalité"
    ]
    
    for chapitre in chapitres_existants:
        try:
            spec = math_service.generate_math_exercise_specs("6e", chapitre, "facile", 1)[0]
            
            if spec is None:
                result.add_error(f"{chapitre} : RÉGRESSION - Spec None")
            elif not spec.parametres:
                result.add_error(f"{chapitre} : RÉGRESSION - Paramètres manquants")
            elif not spec.parametres.get("enonce"):
                result.add_warning(f"{chapitre} : Énoncé vide (peut être normal pour certains générateurs)")
            else:
                result.add_info(f"{chapitre} : OK - Pas de régression")
        except Exception as e:
            result.add_error(f"{chapitre} : RÉGRESSION - Exception - {str(e)}")
    
    if not result.errors:
        result.set_passed()
    
    return result

def test_9_structure_math_exercise_spec(math_service: MathGenerationService) -> TestResult:
    """Test 9 : Structure complète de MathExerciseSpec"""
    result = TestResult("Test 9 : Structure MathExerciseSpec")
    
    print("\n" + "="*80)
    print("TEST 9 : STRUCTURE MATH EXERCISE SPEC")
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
    
    for chapitre in CHAPITRES_SPRINT1:
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
    print("🧪 VALIDATION COMPLÈTE - SPRINT 1")
    print("Chapitres testés : G03, N03, SP01")
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
        test_4_coherence_enonce_correction(math_service),
        test_5_schemas_geometriques(math_service),
        test_6_pipeline_complet(math_service, template_service),
        test_7_difficulte_progressive(math_service),
        test_8_non_regression(math_service),
        test_9_structure_math_exercise_spec(math_service)
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
        print("\n🎉 TOUS LES TESTS SONT PASSÉS ! SPRINT 1 VALIDÉ ✅")
        print("🚀 Vous pouvez démarrer le SPRINT 2 en toute confiance.")
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
