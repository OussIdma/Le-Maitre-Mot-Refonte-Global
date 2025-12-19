"""
Tests pour vérifier les 3 corrections critiques de symétrie :
1. Point symétrique invisible dans le sujet (exercices simples)
2. Synchronisation de l'axe (énoncé = schéma)
3. Grille présente dans tous les exercices
4. Pas de régression sur les triangles
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


def test_1_point_symetrique_invisible_dans_sujet():
    """
    TEST 1 : Point symétrique invisible dans le sujet
    
    Pour les exercices simples (trouver_symetrique) :
    - SUJET : Doit contenir UNIQUEMENT le point original
    - CORRIGÉ : Doit contenir le point original + le point symétrique
    """
    
    print("\n" + "="*70)
    print("TEST 1 : Point symétrique invisible dans le sujet")
    print("="*70)
    
    # Test pour symétrie axiale
    print("\n📐 Symétrie axiale (6e) - difficulté facile (points simples)")
    data = generate_exercises("Symétrie axiale", "6e", "facile", 5)
    
    if not data:
        print("❌ ÉCHEC: Génération d'exercices impossible")
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    
    if not exercises:
        print("❌ ÉCHEC: Aucun exercice généré")
        return False
    
    print(f"✅ {len(exercises)} exercices générés")
    
    all_passed = True
    for i, ex in enumerate(exercises, 1):
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        # Compter les cercles (points) dans chaque version
        circles_q = svg_q.count('<circle')
        circles_c = svg_c.count('<circle')
        
        # Le sujet doit avoir au moins 1 point de moins que la correction
        if circles_c > circles_q:
            print(f"  ✅ Exercice {i}: {circles_q} point(s) dans sujet, {circles_c} dans corrigé")
        else:
            print(f"  ❌ Exercice {i}: Même nombre de points ({circles_q}) dans sujet et corrigé")
            all_passed = False
    
    # Test pour symétrie centrale
    print("\n🔄 Symétrie centrale (5e) - difficulté facile (points simples)")
    data = generate_exercises("Symétrie centrale", "5e", "facile", 5)
    
    if not data:
        print("❌ ÉCHEC: Génération d'exercices impossible")
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    
    for i, ex in enumerate(exercises, 1):
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        circles_q = svg_q.count('<circle')
        circles_c = svg_c.count('<circle')
        
        if circles_c > circles_q:
            print(f"  ✅ Exercice {i}: {circles_q} point(s) dans sujet, {circles_c} dans corrigé")
        else:
            print(f"  ❌ Exercice {i}: Même nombre de points ({circles_q}) dans sujet et corrigé")
            all_passed = False
    
    if all_passed:
        print("\n" + "="*70)
        print("✅ TEST 1 RÉUSSI : Point symétrique correctement caché dans le sujet")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TEST 1 ÉCHOUÉ : Problèmes de séparation détectés")
        print("="*70)
    
    return all_passed


def test_2_synchronisation_axe():
    """
    TEST 2 : Synchronisation de l'axe entre énoncé et schéma
    
    L'axe dessiné dans le SVG doit correspondre exactement à l'axe décrit dans l'énoncé.
    """
    
    print("\n" + "="*70)
    print("TEST 2 : Synchronisation de l'axe (énoncé = schéma)")
    print("="*70)
    
    print("\n📐 Symétrie axiale - vérification des axes")
    data = generate_exercises("Symétrie axiale", "6e", "facile", 10)
    
    if not data:
        print("❌ ÉCHEC: Génération impossible")
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    
    all_passed = True
    for i, ex in enumerate(exercises, 1):
        enonce = ex.get("enonce", "").lower()
        svg_q = ex.get("figure_svg_question", "")
        
        # Extraire le type d'axe de l'énoncé
        if "horizontal" in enonce and "y =" in enonce:
            axe_type_enonce = "horizontal"
            # Extraire la valeur y
            match = re.search(r'y = (\d+)', enonce)
            axe_value_enonce = match.group(1) if match else None
        elif "vertical" in enonce and "x =" in enonce:
            axe_type_enonce = "vertical"
            # Extraire la valeur x
            match = re.search(r'x = (\d+)', enonce)
            axe_value_enonce = match.group(1) if match else None
        elif "y = x" in enonce or "oblique" in enonce:
            axe_type_enonce = "oblique"
            axe_value_enonce = None
        else:
            # Axe non identifié dans l'énoncé
            continue
        
        # Extraire le type d'axe du SVG
        if 'x =' in svg_q and 'y = x' not in svg_q:
            axe_type_svg = "vertical"
            match = re.search(r'x = (\d+)', svg_q)
            axe_value_svg = match.group(1) if match else None
        elif 'y =' in svg_q and 'y = x' not in svg_q:
            axe_type_svg = "horizontal"
            match = re.search(r'y = (\d+)', svg_q)
            axe_value_svg = match.group(1) if match else None
        elif 'y = x' in svg_q:
            axe_type_svg = "oblique"
            axe_value_svg = None
        else:
            axe_type_svg = "inconnu"
            axe_value_svg = None
        
        # Vérifier la concordance
        if axe_type_enonce == axe_type_svg:
            if axe_value_enonce is None or axe_value_enonce == axe_value_svg:
                print(f"  ✅ Exercice {i}: Axe {axe_type_enonce} concordant")
            else:
                print(f"  ❌ Exercice {i}: Axe {axe_type_enonce} mais valeur différente ({axe_value_enonce} vs {axe_value_svg})")
                all_passed = False
        else:
            print(f"  ❌ Exercice {i}: Axe incohérent (énoncé: {axe_type_enonce}, SVG: {axe_type_svg})")
            all_passed = False
    
    if all_passed:
        print("\n" + "="*70)
        print("✅ TEST 2 RÉUSSI : Axes synchronisés entre énoncé et schéma")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TEST 2 ÉCHOUÉ : Incohérences d'axes détectées")
        print("="*70)
    
    return all_passed


def test_3_grille_presente_dans_tous_exercices():
    """
    TEST 3 : Grille présente dans tous les exercices de symétrie
    
    Tous les exercices de symétrie (axiale et centrale) doivent avoir une grille.
    """
    
    print("\n" + "="*70)
    print("TEST 3 : Grille présente dans tous les exercices de symétrie")
    print("="*70)
    
    all_passed = True
    
    # Test symétrie axiale
    print("\n📐 Symétrie axiale (6e)")
    data = generate_exercises("Symétrie axiale", "6e", "facile", 10)
    
    if not data:
        print("❌ ÉCHEC: Génération impossible")
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    print(f"✅ {len(exercises)} exercices générés")
    
    for i, ex in enumerate(exercises, 1):
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        has_grid_q = "grid-line" in svg_q
        has_grid_c = "grid-line" in svg_c
        
        # Compter le nombre de lignes de grille
        grid_lines_q = svg_q.count('class="grid-line"')
        grid_lines_c = svg_c.count('class="grid-line"')
        
        if has_grid_q and has_grid_c:
            print(f"  ✅ Exercice {i}: Grille présente ({grid_lines_q} lignes dans sujet, {grid_lines_c} dans corrigé)")
        else:
            print(f"  ❌ Exercice {i}: Grille manquante (sujet: {has_grid_q}, corrigé: {has_grid_c})")
            all_passed = False
    
    # Test symétrie centrale
    print("\n🔄 Symétrie centrale (5e)")
    data = generate_exercises("Symétrie centrale", "5e", "facile", 10)
    
    if not data:
        print("❌ ÉCHEC: Génération impossible")
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    print(f"✅ {len(exercises)} exercices générés")
    
    for i, ex in enumerate(exercises, 1):
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        has_grid_q = "grid-line" in svg_q
        has_grid_c = "grid-line" in svg_c
        
        grid_lines_q = svg_q.count('class="grid-line"')
        grid_lines_c = svg_c.count('class="grid-line"')
        
        if has_grid_q and has_grid_c:
            print(f"  ✅ Exercice {i}: Grille présente ({grid_lines_q} lignes dans sujet, {grid_lines_c} dans corrigé)")
        else:
            print(f"  ❌ Exercice {i}: Grille manquante (sujet: {has_grid_q}, corrigé: {has_grid_c})")
            all_passed = False
    
    if all_passed:
        print("\n" + "="*70)
        print("✅ TEST 3 RÉUSSI : Grille présente dans tous les exercices")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TEST 3 ÉCHOUÉ : Grilles manquantes")
        print("="*70)
    
    return all_passed


def test_4_aucune_regression_sur_triangles():
    """
    TEST 4 : Aucune régression sur les triangles
    
    Les exercices de type "completer_figure" (triangles) doivent toujours :
    - SUJET : Triangle initial seulement
    - CORRIGÉ : Triangle initial + triangle symétrique
    """
    
    print("\n" + "="*70)
    print("TEST 4 : Pas de régression sur les exercices avec triangles")
    print("="*70)
    
    # Générer plusieurs exercices pour avoir des triangles
    print("\n📐 Symétrie axiale - triangles (difficulté élevée)")
    data = generate_exercises("Symétrie axiale", "6e", "difficile", 15)
    
    if not data:
        print("❌ ÉCHEC: Génération impossible")
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    
    # Trouver les exercices avec triangles
    triangle_exercises = []
    for i, ex in enumerate(exercises, 1):
        svg_q = ex.get("figure_svg_question", "")
        if "triangle-initial" in svg_q:
            triangle_exercises.append((i, ex))
    
    if not triangle_exercises:
        print("⚠️  Aucun exercice avec triangle dans cette génération")
        print("    (Pas un échec - les triangles existent mais sont aléatoires)")
        return True
    
    print(f"✅ {len(triangle_exercises)} exercice(s) avec triangle détecté(s)")
    
    all_passed = True
    for i, ex in triangle_exercises:
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        has_triangle_initial_q = "triangle-initial" in svg_q
        has_triangle_image_q = "triangle-image" in svg_q
        has_triangle_image_c = "triangle-image" in svg_c
        
        print(f"\n  📝 Exercice {i} (triangle):")
        print(f"     Triangle initial dans sujet: {has_triangle_initial_q}")
        print(f"     Triangle image dans sujet: {has_triangle_image_q}")
        print(f"     Triangle image dans corrigé: {has_triangle_image_c}")
        
        if has_triangle_initial_q and not has_triangle_image_q and has_triangle_image_c:
            print(f"     ✅ Séparation correcte")
        else:
            print(f"     ❌ Séparation incorrecte")
            all_passed = False
    
    # Test symétrie centrale
    print("\n🔄 Symétrie centrale - triangles (difficulté élevée)")
    data = generate_exercises("Symétrie centrale", "5e", "difficile", 15)
    
    if data:
        exercises = data.get("document", {}).get("exercises", [])
        
        triangle_exercises = []
        for i, ex in enumerate(exercises, 1):
            svg_q = ex.get("figure_svg_question", "")
            if "triangle-initial" in svg_q:
                triangle_exercises.append((i, ex))
        
        if triangle_exercises:
            print(f"✅ {len(triangle_exercises)} exercice(s) avec triangle détecté(s)")
            
            for i, ex in triangle_exercises:
                svg_q = ex.get("figure_svg_question", "")
                svg_c = ex.get("figure_svg_correction", "")
                
                has_triangle_initial_q = "triangle-initial" in svg_q
                has_triangle_image_q = "triangle-image" in svg_q
                has_triangle_image_c = "triangle-image" in svg_c
                
                print(f"\n  📝 Exercice {i} (triangle):")
                
                if has_triangle_initial_q and not has_triangle_image_q and has_triangle_image_c:
                    print(f"     ✅ Séparation correcte")
                else:
                    print(f"     ❌ Séparation incorrecte")
                    all_passed = False
    
    if all_passed:
        print("\n" + "="*70)
        print("✅ TEST 4 RÉUSSI : Triangles fonctionnent correctement")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TEST 4 ÉCHOUÉ : Régressions sur triangles")
        print("="*70)
    
    return all_passed


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║  TESTS DES CORRECTIONS CRITIQUES DE SYMÉTRIE                    ║")
    print("╚" + "="*68 + "╝")
    
    results = []
    
    # Test 1
    try:
        result1 = test_1_point_symetrique_invisible_dans_sujet()
        results.append(("Test 1 - Point symétrique invisible dans sujet", result1))
    except Exception as e:
        print(f"\n❌ TEST 1 ÉCHOUÉ : {e}")
        import traceback
        traceback.print_exc()
        results.append(("Test 1 - Point symétrique invisible dans sujet", False))
    
    # Test 2
    try:
        result2 = test_2_synchronisation_axe()
        results.append(("Test 2 - Synchronisation axe énoncé/schéma", result2))
    except Exception as e:
        print(f"\n❌ TEST 2 ÉCHOUÉ : {e}")
        import traceback
        traceback.print_exc()
        results.append(("Test 2 - Synchronisation axe énoncé/schéma", False))
    
    # Test 3
    try:
        result3 = test_3_grille_presente_dans_tous_exercices()
        results.append(("Test 3 - Grille dans tous les exercices", result3))
    except Exception as e:
        print(f"\n❌ TEST 3 ÉCHOUÉ : {e}")
        import traceback
        traceback.print_exc()
        results.append(("Test 3 - Grille dans tous les exercices", False))
    
    # Test 4
    try:
        result4 = test_4_aucune_regression_sur_triangles()
        results.append(("Test 4 - Pas de régression sur triangles", result4))
    except Exception as e:
        print(f"\n❌ TEST 4 ÉCHOUÉ : {e}")
        import traceback
        traceback.print_exc()
        results.append(("Test 4 - Pas de régression sur triangles", False))
    
    # Résumé
    print("\n\n")
    print("╔" + "="*68 + "╗")
    print("║  RÉSUMÉ GLOBAL DES TESTS                                        ║")
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
        print("✅ Corrections validées:")
        print("  • Points symétriques correctement cachés dans le sujet")
        print("  • Axes synchronisés entre énoncé et schéma")
        print("  • Grille présente dans tous les exercices")
        print("  • Aucune régression sur les triangles")
        sys.exit(0)
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        sys.exit(1)
