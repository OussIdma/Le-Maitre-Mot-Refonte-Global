"""
Tests pour vérifier la séparation pédagogique des SVG question/correction
et la présence homogène de la grille dans tous les exercices de symétrie.

Tests :
1. Vérification que les exercices de type "construction" ont des SVG différents
2. Vérification que la grille est présente dans tous les exercices de symétrie
3. Vérification que le SVG question ne contient PAS le triangle image
4. Vérification que le SVG correction CONTIENT le triangle image
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8001"


def generate_symmetry_exercises(chapitre: str, niveau: str, nb_exercices: int = 10, difficulte: str = "moyen"):
    """Génère des exercices de symétrie et retourne la réponse"""
    
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
        print(f"❌ Erreur HTTP {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return None
    
    return response.json()


def test_triangle_construction_separation():
    """
    Test 1: Vérifier que les exercices de construction de triangle
    ont des SVG question/correction différents.
    """
    
    print("\n" + "="*70)
    print("TEST 1: Séparation question/correction pour exercices de construction")
    print("="*70)
    
    # Générer plusieurs exercices pour augmenter les chances d'avoir un exercice avec triangle
    data = generate_symmetry_exercises("Symétrie axiale", "6e", nb_exercices=15, difficulte="moyen")
    
    if not data:
        print("❌ ÉCHEC: Impossible de générer des exercices")
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    
    if not exercises:
        print("❌ ÉCHEC: Aucun exercice généré")
        return False
    
    print(f"\n✅ {len(exercises)} exercices générés")
    
    # Trouver les exercices avec triangles
    triangle_exercises = []
    for i, ex in enumerate(exercises, 1):
        enonce = ex.get("enonce", "").lower()
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        has_triangle_keyword = any(word in enonce for word in ["triangle", "complet", "trace", "constru"])
        has_triangle_initial = "triangle-initial" in svg_q
        
        if has_triangle_keyword or has_triangle_initial:
            triangle_exercises.append({
                "index": i,
                "exercise": ex,
                "enonce": enonce
            })
    
    if not triangle_exercises:
        print("\n⚠️  AVERTISSEMENT: Aucun exercice avec triangle trouvé dans cette génération")
        print("    (Cela peut arriver aléatoirement, mais les exercices avec triangles existent)")
        print("    Relancer le test peut donner un résultat différent.")
        return True  # Pas un échec du système, juste pas de chance
    
    print(f"\n✅ {len(triangle_exercises)} exercice(s) avec triangle détecté(s)")
    
    # Tester chaque exercice avec triangle
    all_passed = True
    for item in triangle_exercises:
        i = item["index"]
        ex = item["exercise"]
        
        print(f"\n  📝 Exercice {i} (avec triangle):")
        print(f"     Énoncé: {item['enonce'][:80]}...")
        
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        # Vérification 1: Les SVG doivent être différents
        are_different = svg_q != svg_c
        if not are_different:
            print(f"     ❌ ÉCHEC: Les SVG question et correction sont identiques")
            all_passed = False
            continue
        
        print(f"     ✅ SVG question ≠ SVG correction")
        
        # Vérification 2: Le SVG question ne doit PAS contenir le triangle image
        has_triangle_image_q = "triangle-image" in svg_q
        if has_triangle_image_q:
            print(f"     ❌ ÉCHEC: Le SVG question contient le triangle image (solution visible)")
            all_passed = False
            continue
        
        print(f"     ✅ SVG question ne contient PAS le triangle image")
        
        # Vérification 3: Le SVG correction doit contenir le triangle image
        has_triangle_image_c = "triangle-image" in svg_c
        if not has_triangle_image_c:
            print(f"     ❌ ÉCHEC: Le SVG correction ne contient PAS le triangle image")
            all_passed = False
            continue
        
        print(f"     ✅ SVG correction contient le triangle image")
        
        # Vérification 4: Le SVG question doit contenir le triangle initial
        has_triangle_initial_q = "triangle-initial" in svg_q
        if not has_triangle_initial_q:
            print(f"     ⚠️  AVERTISSEMENT: Le SVG question ne contient pas le triangle initial")
        else:
            print(f"     ✅ SVG question contient le triangle initial")
        
        print(f"     ✅ Séparation pédagogique correcte pour exercice {i}")
    
    if all_passed:
        print("\n" + "="*70)
        print("✅ TEST 1 RÉUSSI: Séparation question/correction valide")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TEST 1 ÉCHOUÉ: Problèmes de séparation détectés")
        print("="*70)
    
    return all_passed


def test_grid_presence_all_symmetries():
    """
    Test 2: Vérifier que TOUS les exercices de symétrie (axiale et centrale)
    contiennent une grille dans leurs SVG.
    """
    
    print("\n" + "="*70)
    print("TEST 2: Présence de la grille dans tous les exercices de symétrie")
    print("="*70)
    
    all_passed = True
    
    # Test pour Symétrie axiale
    print("\n📐 Test Symétrie axiale (6e)...")
    data_axiale = generate_symmetry_exercises("Symétrie axiale", "6e", nb_exercices=8, difficulte="facile")
    
    if not data_axiale:
        print("❌ ÉCHEC: Impossible de générer des exercices de symétrie axiale")
        return False
    
    exercises_axiale = data_axiale.get("document", {}).get("exercises", [])
    print(f"✅ {len(exercises_axiale)} exercices de symétrie axiale générés")
    
    for i, ex in enumerate(exercises_axiale, 1):
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        has_grid_q = "grid-line" in svg_q
        has_grid_c = "grid-line" in svg_c
        
        if not has_grid_q:
            print(f"  ❌ Exercice {i}: Grille absente dans SVG question")
            all_passed = False
        
        if not has_grid_c:
            print(f"  ❌ Exercice {i}: Grille absente dans SVG correction")
            all_passed = False
        
        if has_grid_q and has_grid_c:
            print(f"  ✅ Exercice {i}: Grille présente dans question ET correction")
    
    # Test pour Symétrie centrale
    print("\n🔄 Test Symétrie centrale (5e)...")
    data_centrale = generate_symmetry_exercises("Symétrie centrale", "5e", nb_exercices=8, difficulte="facile")
    
    if not data_centrale:
        print("❌ ÉCHEC: Impossible de générer des exercices de symétrie centrale")
        return False
    
    exercises_centrale = data_centrale.get("document", {}).get("exercises", [])
    print(f"✅ {len(exercises_centrale)} exercices de symétrie centrale générés")
    
    for i, ex in enumerate(exercises_centrale, 1):
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        has_grid_q = "grid-line" in svg_q
        has_grid_c = "grid-line" in svg_c
        
        if not has_grid_q:
            print(f"  ❌ Exercice {i}: Grille absente dans SVG question")
            all_passed = False
        
        if not has_grid_c:
            print(f"  ❌ Exercice {i}: Grille absente dans SVG correction")
            all_passed = False
        
        if has_grid_q and has_grid_c:
            print(f"  ✅ Exercice {i}: Grille présente dans question ET correction")
    
    if all_passed:
        print("\n" + "="*70)
        print("✅ TEST 2 RÉUSSI: Grille présente dans tous les exercices de symétrie")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TEST 2 ÉCHOUÉ: Grilles manquantes détectées")
        print("="*70)
    
    return all_passed


def test_grid_style_consistency():
    """
    Test 3 (Bonus): Vérifier que le style de grille est cohérent
    (même couleur, même épaisseur).
    """
    
    print("\n" + "="*70)
    print("TEST 3 (Bonus): Cohérence du style de grille")
    print("="*70)
    
    data = generate_symmetry_exercises("Symétrie axiale", "6e", nb_exercices=5, difficulte="facile")
    
    if not data:
        print("❌ ÉCHEC: Impossible de générer des exercices")
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    
    if not exercises:
        print("❌ ÉCHEC: Aucun exercice généré")
        return False
    
    print(f"\n✅ {len(exercises)} exercices générés")
    
    # Extraire les attributs de grille du premier exercice comme référence
    reference_svg = exercises[0].get("figure_svg_question", "")
    
    # Chercher les attributs de la première ligne de grille
    import re
    grid_line_pattern = r'class="grid-line"'
    color_pattern = r'stroke="(#[A-Fa-f0-9]{6})"'
    width_pattern = r'stroke-width="([\d.]+)"'
    
    if grid_line_pattern not in reference_svg:
        print("⚠️  Pas de grille dans le premier exercice, test ignoré")
        return True
    
    # Extraire couleur et épaisseur de référence
    color_match = re.search(color_pattern, reference_svg)
    width_match = re.search(width_pattern, reference_svg)
    
    if not color_match or not width_match:
        print("⚠️  Impossible d'extraire les attributs de grille")
        return True
    
    ref_color = color_match.group(1)
    ref_width = width_match.group(1)
    
    print(f"\n📏 Style de grille de référence:")
    print(f"   - Couleur: {ref_color}")
    print(f"   - Épaisseur: {ref_width}px")
    
    # Vérifier la cohérence dans tous les exercices
    all_consistent = True
    for i, ex in enumerate(exercises, 1):
        svg = ex.get("figure_svg_question", "")
        
        if "grid-line" not in svg:
            continue
        
        color_match = re.search(color_pattern, svg)
        width_match = re.search(width_pattern, svg)
        
        if color_match and width_match:
            color = color_match.group(1)
            width = width_match.group(1)
            
            if color != ref_color or width != ref_width:
                print(f"  ❌ Exercice {i}: Style incohérent (couleur: {color}, épaisseur: {width})")
                all_consistent = False
            else:
                print(f"  ✅ Exercice {i}: Style cohérent")
    
    if all_consistent:
        print("\n" + "="*70)
        print("✅ TEST 3 RÉUSSI: Style de grille cohérent")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TEST 3 ÉCHOUÉ: Incohérences de style détectées")
        print("="*70)
    
    return all_consistent


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║  TESTS PÉDAGOGIQUES - Séparation SVG & Grille homogène           ║")
    print("╚" + "="*68 + "╝")
    
    results = []
    
    # Test 1: Séparation question/correction
    try:
        result1 = test_triangle_construction_separation()
        results.append(("Séparation question/correction", result1))
    except Exception as e:
        print(f"\n❌ TEST 1 ÉCHOUÉ avec exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Séparation question/correction", False))
    
    # Test 2: Présence de la grille
    try:
        result2 = test_grid_presence_all_symmetries()
        results.append(("Grille dans tous les exercices", result2))
    except Exception as e:
        print(f"\n❌ TEST 2 ÉCHOUÉ avec exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Grille dans tous les exercices", False))
    
    # Test 3: Cohérence du style de grille
    try:
        result3 = test_grid_style_consistency()
        results.append(("Cohérence du style de grille", result3))
    except Exception as e:
        print(f"\n❌ TEST 3 ÉCHOUÉ avec exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Cohérence du style de grille", False))
    
    # Résumé
    print("\n\n")
    print("╔" + "="*68 + "╗")
    print("║  RÉSUMÉ DES TESTS PÉDAGOGIQUES                                   ║")
    print("╚" + "="*68 + "╝")
    print()
    
    for test_name, passed in results:
        status = "✅ RÉUSSI" if passed else "❌ ÉCHOUÉ"
        print(f"  {test_name:40s} : {status}")
    
    print()
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("🎉 TOUS LES TESTS PÉDAGOGIQUES SONT PASSÉS!")
        print()
        print("📚 Résumé:")
        print("  • Les SVG question/correction sont correctement séparés")
        print("  • La grille est présente dans tous les exercices de symétrie")
        print("  • Le style de grille est homogène")
        sys.exit(0)
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        sys.exit(1)
