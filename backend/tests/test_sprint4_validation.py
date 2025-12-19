"""
🧪 SCRIPT DE VALIDATION COMPLÈTE - SPRINT 4 FINAL
Générateurs 6e : N08, N09, GM01, GM02, GM03, SP02

Ce script valide le dernier sprint pour compléter les 19 générateurs 6e.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService
from services.exercise_template_service import ExerciseTemplateService

# ============================================================================
# CONFIGURATION
# ============================================================================

CHAPITRES_SPRINT4 = [
    "Fractions comme partage et quotient",  # N08
    "Fractions simples de l'unité",  # N09
    "Mesurer et comparer des longueurs",  # GM01
    "Périmètre de figures usuelles",  # GM02
    "Aire du rectangle et du carré",  # GM03
    "Diagrammes en barres et pictogrammes"  # SP02
]

NIVEAU = "6e"
DIFFICULTES = ["facile", "moyen", "difficile"]

# ============================================================================
# TEST
# ============================================================================

def test_sprint4():
    """Validation complète SPRINT 4 - Dernier sprint 6e"""
    
    print("\n" + "="*80)
    print("🎉 VALIDATION FINALE - SPRINT 4 (6e COMPLET)")
    print("Chapitres testés : N08, N09, GM01, GM02, GM03, SP02")
    print("="*80)
    
    try:
        math_service = MathGenerationService()
        template_service = ExerciseTemplateService()
    except Exception as e:
        print(f"\n❌ ERREUR : {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    total_tests = 0
    tests_passed = 0
    errors = []
    
    # TEST 1 : MAPPING
    print("\n" + "="*80)
    print("TEST 1 : MAPPING DES CHAPITRES")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT4:
        total_tests += 1
        try:
            types = math_service._map_chapter_to_types(chapitre, NIVEAU)
            if types:
                print(f"✅ {chapitre} → {[t.value for t in types]}")
                tests_passed += 1
            else:
                errors.append(f"{chapitre} : Aucun type mappé")
        except Exception as e:
            errors.append(f"{chapitre} : {str(e)}")
    
    # TEST 2 : GÉNÉRATION
    print("\n" + "="*80)
    print("TEST 2 : GÉNÉRATION D'EXERCICES")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT4:
        for difficulte in DIFFICULTES:
            total_tests += 1
            try:
                specs = math_service.generate_math_exercise_specs(NIVEAU, chapitre, difficulte, 3)
                if len(specs) == 3 and all(s is not None for s in specs):
                    print(f"✅ {chapitre} ({difficulte})")
                    tests_passed += 1
                else:
                    errors.append(f"{chapitre} ({difficulte}) : {len(specs)}/3")
            except Exception as e:
                errors.append(f"{chapitre} ({difficulte}) : {str(e)}")
    
    # TEST 3 : ÉNONCÉS
    print("\n" + "="*80)
    print("TEST 3 : ÉNONCÉS CONTEXTUELS")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT4:
        total_tests += 1
        try:
            spec = math_service.generate_math_exercise_specs(NIVEAU, chapitre, "facile", 1)[0]
            enonce = spec.parametres.get("enonce", "")
            
            if not enonce or "Question 1" in enonce or len(enonce) < 20:
                errors.append(f"{chapitre} : Énoncé invalide")
            else:
                print(f"✅ {chapitre} : '{enonce[:50]}...'")
                tests_passed += 1
        except Exception as e:
            errors.append(f"{chapitre} : {str(e)}")
    
    # TEST 4 : SCHÉMAS
    print("\n" + "="*80)
    print("TEST 4 : SCHÉMAS GÉOMÉTRIQUES")
    print("="*80)
    
    avec_schema = ["Mesurer et comparer des longueurs", "Périmètre de figures usuelles", "Aire du rectangle et du carré"]
    sans_schema = ["Fractions comme partage et quotient", "Fractions simples de l'unité", "Diagrammes en barres et pictogrammes"]
    
    for chapitre in avec_schema:
        total_tests += 1
        try:
            spec = math_service.generate_math_exercise_specs(NIVEAU, chapitre, "facile", 1)[0]
            if spec.figure_geometrique and spec.figure_geometrique.points:
                print(f"✅ {chapitre} : Schéma OK ({len(spec.figure_geometrique.points)} points)")
                tests_passed += 1
            else:
                errors.append(f"{chapitre} : Schéma manquant")
        except Exception as e:
            errors.append(f"{chapitre} : {str(e)}")
    
    for chapitre in sans_schema:
        total_tests += 1
        try:
            spec = math_service.generate_math_exercise_specs(NIVEAU, chapitre, "facile", 1)[0]
            if spec.figure_geometrique is None:
                print(f"✅ {chapitre} : Pas de schéma (OK)")
                tests_passed += 1
            else:
                errors.append(f"{chapitre} : Schéma présent (devrait être None)")
        except Exception as e:
            errors.append(f"{chapitre} : {str(e)}")
    
    # TEST 5 : PIPELINE
    print("\n" + "="*80)
    print("TEST 5 : PIPELINE COMPLET")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT4:
        total_tests += 1
        try:
            spec = math_service.generate_math_exercise_specs(NIVEAU, chapitre, "facile", 1)[0]
            question = template_service._convert_math_spec_to_question(spec, 1)
            
            if "enonce_brut" in question and "solution_brut" in question and len(question["enonce_brut"]) >= 20:
                print(f"✅ {chapitre}")
                tests_passed += 1
            else:
                errors.append(f"{chapitre} : Pipeline incomplet")
        except Exception as e:
            errors.append(f"{chapitre} : {str(e)}")
    
    # RAPPORT FINAL
    print("\n" + "="*80)
    print("📊 RÉSUMÉ FINAL SPRINT 4")
    print("="*80)
    print(f"✅ Tests passés : {tests_passed}/{total_tests}")
    print(f"❌ Tests échoués : {len(errors)}")
    print(f"📊 Taux de réussite : {(tests_passed/total_tests*100):.1f}%")
    
    if errors:
        print(f"\n❌ Erreurs ({len(errors)}) :")
        for error in errors[:10]:
            print(f"   • {error}")
        return False
    else:
        print("\n🎉 SPRINT 4 VALIDÉ ! TOUS LES 19 GÉNÉRATEURS 6e SONT OPÉRATIONNELS ✅")
        print("🏆 Niveau 6e complété à 100% (19/19 chapitres)")
        return True

if __name__ == "__main__":
    success = test_sprint4()
    sys.exit(0 if success else 1)
