"""
Tests de cohérence texte
Vérifie normalisation symboles, absence prénoms, cohérence points
"""
import sys
import os
import asyncio
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService
from services.math_text_service import MathTextService


async def test_text_normalization():
    """Test normalisation des symboles mathématiques"""
    print("="*80)
    print("📝 TEST 1: NORMALISATION SYMBOLES MATHÉMATIQUES")
    print("="*80)
    
    math_service = MathGenerationService()
    text_service = MathTextService()
    
    # Générer quelques specs
    test_cases = [
        ("Cercles", math_service._gen_cercle("6e", "Aires", "facile")),
        ("Puissances", math_service._gen_puissances("4e", "Puissances", "facile")),
        ("Trigonométrie", math_service._gen_trigonometrie("3e", "Trigonométrie", "facile")),
    ]
    
    issues = []
    
    for name, spec in test_cases:
        # Générer le texte
        gen_exercises = await text_service.generate_text_for_specs([spec])
        
        if not gen_exercises:
            continue
        
        gen_ex = gen_exercises[0]
        enonce = gen_ex.texte.enonce
        solution = gen_ex.texte.solution_redigee
        
        print(f"\n🔍 Test {name}:")
        print(f"  Énoncé: {enonce[:80]}...")
        
        # Vérifier symboles normalisés
        symbols_to_check = {
            '×': 'multiplication',
            '²': 'carré',
            '³': 'cube',
            '°': 'degré',
            'π': 'pi',
            '≈': 'approximation'
        }
        
        found_symbols = []
        for symbol, desc in symbols_to_check.items():
            if symbol in enonce or symbol in solution:
                found_symbols.append(desc)
        
        if found_symbols:
            print(f"  ✅ Symboles normalisés trouvés: {', '.join(found_symbols)}")
        
        # Vérifier absence de * ou x en multiplication
        if re.search(r'(\d+)\s*[\*x]\s*(\d+)', enonce):
            issues.append(f"{name}: * ou x non normalisé trouvé")
            print(f"  ❌ * ou x trouvé (pas normalisé)")
        else:
            print(f"  ✅ Pas de * ou x (bien normalisé)")
    
    print(f"\n{'='*80}")
    if issues:
        print(f"⚠️ {len(issues)} problème(s) détecté(s)")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ TOUS LES SYMBOLES SONT NORMALISÉS")


async def test_no_personal_names():
    """Test absence de prénoms personnels"""
    print(f"\n{'='*80}")
    print("📝 TEST 2: ABSENCE PRÉNOMS PERSONNELS")
    print("="*80)
    
    math_service = MathGenerationService()
    text_service = MathTextService()
    
    # Générer 10 exercices de types variés
    specs = []
    specs.append(math_service._gen_triangle_rectangle("4e", "Théorème de Pythagore", "facile"))
    specs.append(math_service._gen_cercle("6e", "Aires", "facile"))
    specs.append(math_service._gen_thales("3e", "Théorème de Thalès", "facile"))
    specs.append(math_service._gen_equation_1er_degre("4e", "Équations", "facile"))
    specs.append(math_service._gen_volume("6e", "Volumes", "facile"))
    
    gen_exercises = await text_service.generate_text_for_specs(specs)
    
    # Prénoms à surveiller
    prenoms = [
        'Chaima', 'Pierre', 'Marie', 'Jean', 'Sophie', 'Lucas',
        'Emma', 'Louis', 'Léa', 'Hugo', 'Chloé', 'Gabriel'
    ]
    
    issues_found = []
    
    for i, gen_ex in enumerate(gen_exercises, 1):
        enonce = gen_ex.texte.enonce
        solution = gen_ex.texte.solution_redigee
        
        for prenom in prenoms:
            if re.search(rf'\b{prenom}\b', enonce, re.IGNORECASE) or \
               re.search(rf'\b{prenom}\b', solution, re.IGNORECASE):
                issues_found.append(f"Exercice {i}: Prénom '{prenom}' trouvé")
    
    print(f"\n📊 Exercices testés: {len(gen_exercises)}")
    print(f"Prénoms surveillés: {len(prenoms)}")
    
    if issues_found:
        print(f"\n❌ {len(issues_found)} PRÉNOM(S) TROUVÉ(S):")
        for issue in issues_found:
            print(f"  - {issue}")
    else:
        print(f"\n✅ AUCUN PRÉNOM PERSONNEL TROUVÉ")


async def test_geometry_points_consistency():
    """Test cohérence des points géométriques"""
    print(f"\n{'='*80}")
    print("📝 TEST 3: COHÉRENCE POINTS GÉOMÉTRIQUES")
    print("="*80)
    
    math_service = MathGenerationService()
    text_service = MathTextService()
    
    # Exercices avec géométrie
    test_cases = [
        ("Pythagore", math_service._gen_triangle_rectangle("4e", "Théorème de Pythagore", "facile")),
        ("Thalès", math_service._gen_thales("3e", "Théorème de Thalès", "facile")),
        ("Triangle", math_service._gen_triangle_quelconque("5e", "Triangles", "facile")),
        ("Rectangle", math_service._gen_rectangle("6e", "Géométrie - Triangles et quadrilatères", "facile")),
    ]
    
    issues = []
    
    for name, spec in test_cases:
        if not spec.figure_geometrique:
            continue
        
        spec_points = set(spec.figure_geometrique.points)
        
        # Générer texte
        gen_exercises = await text_service.generate_text_for_specs([spec])
        if not gen_exercises:
            continue
        
        gen_ex = gen_exercises[0]
        enonce = gen_ex.texte.enonce
        
        # Extraire points de l'énoncé
        found_points = set(re.findall(r'\b([A-Z])\b', enonce))
        
        # Filtrer points non géométriques courants
        geometric_letters = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        found_points = found_points & geometric_letters
        
        print(f"\n🔍 {name}:")
        print(f"  Points spec: {sorted(spec_points)}")
        print(f"  Points énoncé: {sorted(found_points)}")
        
        # Vérifier que les points principaux sont dans l'énoncé
        main_points = list(spec_points)[:3]  # 3 premiers points
        main_in_enonce = [p for p in main_points if p in found_points]
        
        if len(main_in_enonce) >= 2:
            print(f"  ✅ Points principaux présents ({len(main_in_enonce)}/3)")
        else:
            issues.append(f"{name}: Seulement {len(main_in_enonce)}/3 points principaux dans énoncé")
            print(f"  ⚠️ Peu de points dans énoncé ({len(main_in_enonce)}/3)")
        
        # Vérifier points inattendus majeurs
        unexpected = found_points - spec_points
        if len(unexpected) > 3:  # Tolérer quelques faux positifs
            issues.append(f"{name}: {len(unexpected)} points inattendus")
            print(f"  ⚠️ Points inattendus: {sorted(unexpected)}")
    
    print(f"\n{'='*80}")
    if issues:
        print(f"⚠️ {len(issues)} incohérence(s) détectée(s)")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ COHÉRENCE POINTS VALIDÉE")


async def run_all_text_tests():
    """Exécute tous les tests de cohérence texte"""
    await test_text_normalization()
    await test_no_personal_names()
    await test_geometry_points_consistency()
    
    print(f"\n\n{'='*80}")
    print("🎯 TESTS COHÉRENCE TEXTE TERMINÉS")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(run_all_text_tests())
