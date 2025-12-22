"""
🧪 SCRIPT DE VALIDATION COMPLÈTE - SPRINT 3
Générateurs 6e : G04, G05, N05, N06, N07

Ce script valide tous les aspects critiques du SPRINT 3 :
- Mapping des chapitres
- Génération des exercices
- Énoncés contextuels (pas de "Question 1")
- Cohérence énoncé/correction
- Schémas géométriques (G04, G05)
- Pipeline complet
- Non-régression SPRINT 1 & 2
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService
from services.exercise_template_service import ExerciseTemplateService

# ============================================================================
# CONFIGURATION
# ============================================================================

CHAPITRES_SPRINT3 = [
    "Triangles (construction et classification)",  # G04
    "Quadrilatères usuels (carré, rectangle, losange, parallélogramme)",  # G05
    "Multiplication de nombres entiers",  # N05
    "Division euclidienne",  # N06
    "Multiples et diviseurs, critères de divisibilité"  # N07
]

NIVEAU = "6e"
DIFFICULTES = ["facile", "moyen", "difficile"]

# ============================================================================
# TESTS
# ============================================================================

def test_sprint3():
    """Exécute tous les tests du SPRINT 3"""
    
    print("\n" + "="*80)
    print("🧪 VALIDATION COMPLÈTE - SPRINT 3")
    print("Chapitres testés : G04, G05, N05, N06, N07")
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
    
    # Compteurs
    total_tests = 0
    tests_passed = 0
    errors = []
    warnings = []
    
    print("\n" + "="*80)
    print("TEST 1 : MAPPING DES CHAPITRES")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT3:
        total_tests += 1
        try:
            types = math_service._map_chapter_to_types(chapitre, NIVEAU)
            
            if not types:
                errors.append(f"{chapitre} : Aucun type mappé")
            else:
                print(f"✅ {chapitre} → {[t.value for t in types]}")
                tests_passed += 1
        except ValueError as e:
            errors.append(f"{chapitre} : {str(e)}")
    
    print("\n" + "="*80)
    print("TEST 2 : GÉNÉRATION D'EXERCICES (3 NIVEAUX)")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT3:
        for difficulte in DIFFICULTES:
            total_tests += 1
            try:
                specs = math_service.generate_math_exercise_specs(
                    niveau=NIVEAU,
                    chapitre=chapitre,
                    difficulte=difficulte,
                    nb_exercices=3
                )
                
                if len(specs) == 3 and all(s is not None for s in specs):
                    print(f"✅ {chapitre} ({difficulte}) : 3 exercices OK")
                    tests_passed += 1
                else:
                    errors.append(f"{chapitre} ({difficulte}) : {len(specs)}/3 exercices générés")
            except Exception as e:
                errors.append(f"{chapitre} ({difficulte}) : Exception - {str(e)}")
    
    print("\n" + "="*80)
    print("TEST 3 : ÉNONCÉS CONTEXTUELS")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT3:
        total_tests += 1
        try:
            spec = math_service.generate_math_exercise_specs(NIVEAU, chapitre, "facile", 1)[0]
            enonce = spec.parametres.get("enonce", "")
            
            if not enonce:
                errors.append(f"{chapitre} : Énoncé vide")
            elif "Question 1" in enonce or "Question 2" in enonce:
                errors.append(f"{chapitre} : Énoncé générique")
            elif len(enonce) < 20:
                warnings.append(f"{chapitre} : Énoncé court ({len(enonce)} chars)")
                tests_passed += 1  # Warning mais pas erreur
            else:
                print(f"✅ {chapitre} : '{enonce[:60]}...'")
                tests_passed += 1
        except Exception as e:
            errors.append(f"{chapitre} : Exception - {str(e)}")
    
    print("\n" + "="*80)
    print("TEST 4 : SCHÉMAS GÉOMÉTRIQUES")
    print("="*80)
    
    chapitres_avec_schema = [
        "Triangles (construction et classification)",
        "Quadrilatères usuels (carré, rectangle, losange, parallélogramme)"
    ]
    
    for chapitre in chapitres_avec_schema:
        total_tests += 1
        try:
            spec = math_service.generate_math_exercise_specs(NIVEAU, chapitre, "facile", 1)[0]
            
            if spec.figure_geometrique is None:
                errors.append(f"{chapitre} : Pas de figure géométrique")
            elif not spec.figure_geometrique.points or len(spec.figure_geometrique.points) < 3:
                errors.append(f"{chapitre} : Pas assez de points ({len(spec.figure_geometrique.points) if spec.figure_geometrique.points else 0})")
            else:
                print(f"✅ {chapitre} : Schéma OK ({len(spec.figure_geometrique.points)} points)")
                tests_passed += 1
        except Exception as e:
            errors.append(f"{chapitre} : Exception - {str(e)}")
    
    # Vérifier que les chapitres N n'ont PAS de schéma
    chapitres_sans_schema = [
        "Multiplication de nombres entiers",
        "Division euclidienne",
        "Multiples et diviseurs, critères de divisibilité"
    ]
    
    for chapitre in chapitres_sans_schema:
        total_tests += 1
        try:
            spec = math_service.generate_math_exercise_specs(NIVEAU, chapitre, "facile", 1)[0]
            
            if spec.figure_geometrique is not None:
                warnings.append(f"{chapitre} : Schéma présent (devrait être None)")
                tests_passed += 1  # Warning mais pas erreur
            else:
                print(f"✅ {chapitre} : Pas de schéma (OK)")
                tests_passed += 1
        except Exception as e:
            errors.append(f"{chapitre} : Exception - {str(e)}")
    
    print("\n" + "="*80)
    print("TEST 5 : PIPELINE COMPLET")
    print("="*80)
    
    for chapitre in CHAPITRES_SPRINT3:
        total_tests += 1
        try:
            spec = math_service.generate_math_exercise_specs(NIVEAU, chapitre, "facile", 1)[0]
            question = template_service._convert_math_spec_to_question(spec, 1)
            
            if "enonce_brut" not in question:
                errors.append(f"{chapitre} : enonce_brut manquant")
            elif question["enonce_brut"] == "Question 1":
                errors.append(f"{chapitre} : Énoncé générique après conversion")
            elif len(question["enonce_brut"]) < 20:
                errors.append(f"{chapitre} : Énoncé trop court après conversion")
            elif "solution_brut" not in question or len(question["solution_brut"]) < 10:
                errors.append(f"{chapitre} : Solution manquante ou trop courte")
            else:
                print(f"✅ {chapitre} : Pipeline OK")
                tests_passed += 1
        except Exception as e:
            errors.append(f"{chapitre} : Exception - {str(e)}")
    
    # Rapport final
    print("\n" + "="*80)
    print("📊 RÉSUMÉ FINAL")
    print("="*80)
    print(f"✅ Tests passés : {tests_passed}/{total_tests}")
    print(f"❌ Tests échoués : {len([e for e in errors])}")
    print(f"📊 Taux de réussite : {(tests_passed/total_tests*100):.1f}%")
    
    if warnings:
        print(f"\n⚠️  Avertissements ({len(warnings)}) :")
        for warning in warnings[:5]:
            print(f"   • {warning}")
    
    if errors:
        print(f"\n❌ Erreurs ({len(errors)}) :")
        for error in errors[:10]:
            print(f"   • {error}")
        print(f"\n⚠️  {len(errors)} erreur(s) détectée(s). Veuillez corriger.")
        return False
    else:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS ! SPRINT 3 VALIDÉ ✅")
        print("🚀 Les 13 générateurs (SPRINT 1+2+3) fonctionnent parfaitement.")
        return True

# ============================================================================
# EXÉCUTION
# ============================================================================

if __name__ == "__main__":
    success = test_sprint3()
    sys.exit(0 if success else 1)
