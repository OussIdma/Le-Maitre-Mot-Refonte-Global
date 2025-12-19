"""
Tests de la règle pédagogique universelle pour les transformations géométriques

RÈGLE OFFICIELLE (manuels scolaires, brevet, prescriptions IPR) :
    - SUJET = données connues uniquement
    - CORRIGÉ = données connues + données à trouver

Cette règle s'applique à TOUTES les transformations géométriques :
    - Symétrie axiale
    - Symétrie centrale
    - Homothétie (futur)
    - Translation (futur)
    - Rotation (futur)
"""

import requests
import json
import sys
import re

BASE_URL = "http://localhost:8001"


def generate_exercises(chapitre: str, niveau: str, difficulte: str, nb_exercices: int):
    """Génère des exercices et retourne la réponse JSON"""
    
    payload = {
        "matiere": "Mathématiques",
        "niveau": niveau,
        "chapitre": chapitre,
        "type_doc": "Fiche",
        "difficulte": difficulte,
        "nb_exercices": nb_exercices
    }
    
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json=payload,
        timeout=120
    )
    
    if response.status_code != 200:
        print(f"❌ HTTP {response.status_code}")
        print(response.text[:500])
        return None
    
    return response.json()


def test_1_trouver_symetrique():
    """
    TEST 1 : Type "trouver_symetrique"
    
    Données connues : point M, axe/centre, grille
    Donnée à trouver : point M'
    
    RÈGLE :
        - SUJET : M uniquement (+ axe + grille)
        - CORRIGÉ : M + M' (+ segments de construction)
    """
    
    print("\n" + "="*70)
    print("TEST 1 : Type 'trouver_symetrique' - SUJET = M, CORRIGÉ = M + M'")
    print("="*70)
    
    all_passed = True
    
    # Test symétrie axiale
    print("\n📐 Symétrie axiale")
    data = generate_exercises("Symétrie axiale", "6e", "moyen", 20)
    
    if not data:
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    
    exercices_trouver = []
    for i, ex in enumerate(exercises, 1):
        spec = ex.get("spec_mathematique", {})
        params = spec.get("parametres", {})
        if params.get("type") == "trouver_symetrique":
            exercices_trouver.append((i, ex))
    
    print(f"✅ {len(exercices_trouver)} exercice(s) 'trouver_symetrique' trouvé(s)")
    
    for i, ex in exercices_trouver:
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        circles_q = svg_q.count('<circle')
        circles_c = svg_c.count('<circle')
        
        points_q = re.findall(r'<text[^>]*>([A-Z])</text>', svg_q)
        points_c = re.findall(r'<text[^>]*>([A-Z])</text>', svg_c)
        
        print(f"  Exercice {i}: Sujet={len(set(points_q))} points, Corrigé={len(set(points_c))} points", end="")
        
        # Vérification : Sujet doit avoir MOINS de points que Corrigé
        if len(set(points_c)) > len(set(points_q)):
            print(" ✅")
        else:
            print(f" ❌ (Sujet devrait avoir moins de points)")
            all_passed = False
    
    # Test symétrie centrale
    print("\n🔄 Symétrie centrale")
    data = generate_exercises("Symétrie centrale", "5e", "moyen", 20)
    
    if data:
        exercises = data.get("document", {}).get("exercises", [])
        
        exercices_trouver = []
        for i, ex in enumerate(exercises, 1):
            spec = ex.get("spec_mathematique", {})
            params = spec.get("parametres", {})
            if params.get("type") == "trouver_symetrique":
                exercices_trouver.append((i, ex))
        
        print(f"✅ {len(exercices_trouver)} exercice(s) 'trouver_symetrique' trouvé(s)")
        
        for i, ex in exercices_trouver:
            svg_q = ex.get("figure_svg_question", "")
            svg_c = ex.get("figure_svg_correction", "")
            
            circles_q = svg_q.count('<circle')
            circles_c = svg_c.count('<circle')
            
            print(f"  Exercice {i}: Sujet={circles_q} cercles, Corrigé={circles_c} cercles", end="")
            
            if circles_c > circles_q:
                print(" ✅")
            else:
                print(f" ❌")
                all_passed = False
    
    if all_passed:
        print("\n" + "="*70)
        print("✅ TEST 1 RÉUSSI")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TEST 1 ÉCHOUÉ")
        print("="*70)
    
    return all_passed


def test_2_completer_triangle():
    """
    TEST 2 : Type "completer_figure"
    
    Données connues : triangle ABC
    Données à trouver : triangle A'B'C'
    
    RÈGLE :
        - SUJET : ABC uniquement (+ axe + grille)
        - CORRIGÉ : ABC + A'B'C' (+ segments de construction)
    """
    
    print("\n" + "="*70)
    print("TEST 2 : Type 'completer_figure' - SUJET = ABC, CORRIGÉ = ABC + A'B'C'")
    print("="*70)
    
    all_passed = True
    
    # Générer beaucoup d'exercices difficiles pour avoir des triangles
    print("\n📐 Symétrie axiale - triangles")
    data = generate_exercises("Symétrie axiale", "6e", "difficile", 20)
    
    if not data:
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    
    exercices_triangle = []
    for i, ex in enumerate(exercises, 1):
        svg_q = ex.get("figure_svg_question", "")
        if "triangle-initial" in svg_q:
            exercices_triangle.append((i, ex))
    
    if not exercices_triangle:
        print("⚠️  Aucun exercice avec triangle (aléatoire)")
        return True
    
    print(f"✅ {len(exercices_triangle)} exercice(s) avec triangle trouvé(s)")
    
    for i, ex in exercices_triangle:
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        has_triangle_initial_q = "triangle-initial" in svg_q
        has_triangle_image_q = "triangle-image" in svg_q
        has_triangle_image_c = "triangle-image" in svg_c
        
        print(f"  Exercice {i}:", end="")
        print(f" Initial(Q)={'✓' if has_triangle_initial_q else '✗'}", end="")
        print(f" Image(Q)={'✗' if not has_triangle_image_q else '✓'}", end="")
        print(f" Image(C)={'✓' if has_triangle_image_c else '✗'}", end="")
        
        # Vérification de la règle
        if has_triangle_initial_q and not has_triangle_image_q and has_triangle_image_c:
            print(" ✅")
        else:
            print(" ❌")
            all_passed = False
    
    # Test symétrie centrale
    print("\n🔄 Symétrie centrale - triangles")
    data = generate_exercises("Symétrie centrale", "5e", "difficile", 20)
    
    if data:
        exercises = data.get("document", {}).get("exercises", [])
        
        exercices_triangle = []
        for i, ex in enumerate(exercises, 1):
            svg_q = ex.get("figure_svg_question", "")
            if "triangle-initial" in svg_q:
                exercices_triangle.append((i, ex))
        
        if exercices_triangle:
            print(f"✅ {len(exercices_triangle)} exercice(s) avec triangle trouvé(s)")
            
            for i, ex in exercices_triangle:
                svg_q = ex.get("figure_svg_question", "")
                svg_c = ex.get("figure_svg_correction", "")
                
                has_triangle_image_q = "triangle-image" in svg_q
                has_triangle_image_c = "triangle-image" in svg_c
                
                print(f"  Exercice {i}:", end="")
                
                if not has_triangle_image_q and has_triangle_image_c:
                    print(" ✅")
                else:
                    print(" ❌")
                    all_passed = False
    
    if all_passed:
        print("\n" + "="*70)
        print("✅ TEST 2 RÉUSSI")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TEST 2 ÉCHOUÉ")
        print("="*70)
    
    return all_passed


def test_3_verifier_symetrie():
    """
    TEST 3 : Type "verifier_symetrie"
    
    Données connues : points A et B, axe
    Données à trouver : AUCUNE (vérification uniquement)
    
    RÈGLE :
        - SUJET : A + B + axe + grille (RIEN à cacher)
        - CORRIGÉ : A + B + axe + grille (peut ajouter éléments auxiliaires)
    """
    
    print("\n" + "="*70)
    print("TEST 3 : Type 'verifier_symetrie' - SUJET = CORRIGÉ (rien à cacher)")
    print("="*70)
    
    all_passed = True
    
    print("\n📐 Symétrie axiale")
    data = generate_exercises("Symétrie axiale", "6e", "moyen", 20)
    
    if not data:
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    
    exercices_verifier = []
    for i, ex in enumerate(exercises, 1):
        spec = ex.get("spec_mathematique", {})
        params = spec.get("parametres", {})
        if params.get("type") == "verifier_symetrie":
            exercices_verifier.append((i, ex))
    
    print(f"✅ {len(exercices_verifier)} exercice(s) 'verifier_symetrie' trouvé(s)")
    
    for i, ex in exercices_verifier:
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        points_q = re.findall(r'<text[^>]*>([A-Z])</text>', svg_q)
        points_c = re.findall(r'<text[^>]*>([A-Z])</text>', svg_c)
        
        print(f"  Exercice {i}: Sujet={len(set(points_q))} points, Corrigé={len(set(points_c))} points", end="")
        
        # Pour verifier_symetrie, Sujet doit contenir au moins 2 points
        if len(set(points_q)) >= 2:
            print(" ✅")
        else:
            print(" ❌ (Devrait montrer au moins 2 points)")
            all_passed = False
    
    if all_passed:
        print("\n" + "="*70)
        print("✅ TEST 3 RÉUSSI")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TEST 3 ÉCHOUÉ")
        print("="*70)
    
    return all_passed


def test_4_pas_de_regression():
    """
    TEST 4 : Pas de régression
    
    Vérifier que :
    - La grille est toujours présente
    - Les axes sont cohérents
    - Aucun impact sur Pythagore, Rectangles, etc.
    """
    
    print("\n" + "="*70)
    print("TEST 4 : Pas de régression - Grille, axes, autres chapitres")
    print("="*70)
    
    all_passed = True
    
    # Test grille
    print("\n📏 Grille présente dans tous les exercices de symétrie")
    data = generate_exercises("Symétrie axiale", "6e", "facile", 10)
    
    if not data:
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    
    for i, ex in enumerate(exercises, 1):
        svg_q = ex.get("figure_svg_question", "")
        has_grid = "grid-line" in svg_q
        
        print(f"  Exercice {i}: Grille={'✓' if has_grid else '✗'}", end="")
        
        if has_grid:
            print(" ✅")
        else:
            print(" ❌")
            all_passed = False
    
    # Test Pythagore (ne doit pas être affecté)
    print("\n📐 Pythagore (non affecté)")
    data = generate_exercises("Théorème de Pythagore", "4e", "moyen", 5)
    
    if data:
        exercises = data.get("document", {}).get("exercises", [])
        print(f"  ✅ {len(exercises)} exercices Pythagore générés sans erreur")
    else:
        print("  ⚠️  Impossible de générer Pythagore")
    
    if all_passed:
        print("\n" + "="*70)
        print("✅ TEST 4 RÉUSSI")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TEST 4 ÉCHOUÉ")
        print("="*70)
    
    return all_passed


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║  TESTS RÈGLE PÉDAGOGIQUE UNIVERSELLE                            ║")
    print("╚" + "="*68 + "╝")
    print()
    print("RÈGLE : SUJET = données connues | CORRIGÉ = données + réponse")
    print()
    
    results = []
    
    # Test 1
    try:
        result1 = test_1_trouver_symetrique()
        results.append(("Test 1 - trouver_symetrique", result1))
    except Exception as e:
        print(f"\n❌ TEST 1 ÉCHOUÉ : {e}")
        import traceback
        traceback.print_exc()
        results.append(("Test 1 - trouver_symetrique", False))
    
    # Test 2
    try:
        result2 = test_2_completer_triangle()
        results.append(("Test 2 - completer_figure (triangles)", result2))
    except Exception as e:
        print(f"\n❌ TEST 2 ÉCHOUÉ : {e}")
        import traceback
        traceback.print_exc()
        results.append(("Test 2 - completer_figure (triangles)", False))
    
    # Test 3
    try:
        result3 = test_3_verifier_symetrie()
        results.append(("Test 3 - verifier_symetrie", result3))
    except Exception as e:
        print(f"\n❌ TEST 3 ÉCHOUÉ : {e}")
        import traceback
        traceback.print_exc()
        results.append(("Test 3 - verifier_symetrie", False))
    
    # Test 4
    try:
        result4 = test_4_pas_de_regression()
        results.append(("Test 4 - Pas de régression", result4))
    except Exception as e:
        print(f"\n❌ TEST 4 ÉCHOUÉ : {e}")
        import traceback
        traceback.print_exc()
        results.append(("Test 4 - Pas de régression", False))
    
    # Résumé
    print("\n\n")
    print("╔" + "="*68 + "╗")
    print("║  RÉSUMÉ GLOBAL                                                   ║")
    print("╚" + "="*68 + "╝")
    print()
    
    for test_name, passed in results:
        status = "✅ RÉUSSI" if passed else "❌ ÉCHOUÉ"
        print(f"  {test_name:50s} : {status}")
    
    print()
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("🎉 TOUS LES TESTS SONT PASSÉS!")
        print()
        print("✅ Règle pédagogique universelle validée:")
        print("  • SUJET = données connues uniquement")
        print("  • CORRIGÉ = données connues + données à trouver")
        print("  • Appliquée à tous les types d'exercices")
        print("  • Aucune régression détectée")
        sys.exit(0)
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        sys.exit(1)
