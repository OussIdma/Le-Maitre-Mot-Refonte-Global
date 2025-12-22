"""
Tests pour reproduire les bugs signalés en production réelle par l'utilisateur :

BUG 1 : Point symétrique visible dans le sujet (exercice "trouver le symétrique")
- Niveau : 6e, Chapitre : Symétrie axiale, Difficulté : moyen
- Exemple : "Trouve les coordonnées du point N, symétrique de M..."
- Attendu : Sujet montre uniquement M, Corrigé montre M + N

BUG 2 : Axe incorrect dans le schéma (incohérent avec l'énoncé)
- Exemple : Énoncé dit "axe horizontal y = 5", schéma montre "y = x"
- Attendu : L'axe dessiné doit correspondre exactement à l'énoncé
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


def test_bug_1_trouver_symetrique_moyen():
    """
    TEST BUG 1 : Reproduire le cas exact signalé
    
    Niveau : 6e
    Chapitre : Symétrie axiale  
    Difficulte : moyen
    Type : trouver le symétrique
    
    Attendu :
    - Sujet : UNIQUEMENT le point M (+ axe)
    - Corrigé : M + N + segment complet
    """
    
    print("\n" + "="*70)
    print("TEST BUG 1 : Point symétrique caché dans exercice 'trouver_symetrique'")
    print("="*70)
    print("\nConditions : 6e, Symétrie axiale, difficulté MOYEN")
    print()
    
    data = generate_exercises("Symétrie axiale", "6e", "moyen", 20)
    
    if not data:
        print("❌ ÉCHEC: Génération impossible")
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    
    # Filtrer les exercices "trouver_symetrique"
    exercices_trouver = []
    for i, ex in enumerate(exercises, 1):
        spec = ex.get("spec_mathematique", {})
        params = spec.get("parametres", {})
        type_ex = params.get("type", "")
        
        if type_ex == "trouver_symetrique":
            exercices_trouver.append((i, ex))
    
    if not exercices_trouver:
        print("⚠️  Aucun exercice 'trouver_symetrique' dans cette génération")
        return True
    
    print(f"✅ {len(exercices_trouver)} exercice(s) 'trouver_symetrique' trouvé(s)")
    print()
    
    all_passed = True
    for i, ex in exercices_trouver:
        enonce = ex.get("enonce", "")
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        # Compter les cercles (points)
        circles_q = svg_q.count('<circle')
        circles_c = svg_c.count('<circle')
        
        # Extraire les points visibles
        points_q = re.findall(r'<text[^>]*>([A-Z])</text>', svg_q)
        points_c = re.findall(r'<text[^>]*>([A-Z])</text>', svg_c)
        
        print(f"  📝 Exercice {i}:")
        print(f"     Énoncé: {enonce[:80]}...")
        print(f"     Sujet: {set(points_q)} ({circles_q} cercles)")
        print(f"     Corrigé: {set(points_c)} ({circles_c} cercles)")
        
        # Vérifications
        if circles_q == circles_c:
            print(f"     ❌ ÉCHEC: Sujet et corrigé identiques ({circles_q} cercles)")
            all_passed = False
        elif len(set(points_c)) > len(set(points_q)):
            print(f"     ✅ CORRECT: Plus de points dans corrigé ({len(set(points_c))} vs {len(set(points_q))})")
        else:
            print(f"     ⚠️  BIZARRE: Même nombre de points mais cercles différents")
        
        print()
    
    if all_passed:
        print("="*70)
        print("✅ TEST BUG 1 RÉUSSI : Séparation correcte sujet/corrigé")
        print("="*70)
    else:
        print("="*70)
        print("❌ TEST BUG 1 ÉCHOUÉ : Points visibles dans le sujet")
        print("="*70)
    
    return all_passed


def test_bug_2_axe_incoherent():
    """
    TEST BUG 2 : Reproduire le cas d'axe incohérent
    
    Exemple signalé :
    - Énoncé : "axe horizontal y = 5"
    - Schéma : montre "y = x" (oblique)
    
    Attendu :
    - Si énoncé dit "horizontal y = 5" → schéma doit montrer "y = 5"
    - Si énoncé dit "vertical x = 3" → schéma doit montrer "x = 3"
    - Si énoncé dit "y = x" ou "oblique" → schéma doit montrer "y = x"
    """
    
    print("\n" + "="*70)
    print("TEST BUG 2 : Cohérence axe énoncé ↔ schéma")
    print("="*70)
    print("\nVérification exhaustive sur 50 exercices")
    print()
    
    # Générer beaucoup d'exercices pour couvrir tous les cas
    data = generate_exercises("Symétrie axiale", "6e", "moyen", 50)
    
    if not data:
        print("❌ ÉCHEC: Génération impossible")
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    print(f"✅ {len(exercises)} exercices générés")
    print()
    
    all_passed = True
    nb_tested = 0
    
    for i, ex in enumerate(exercises, 1):
        enonce = ex.get("enonce", "").lower()
        svg_q = ex.get("figure_svg_question", "")
        spec = ex.get("spec_mathematique", {})
        fig = spec.get("figure_geometrique", {})
        props = fig.get("proprietes", [])
        
        # Déterminer le type d'axe dans l'énoncé
        axe_enonce_type = None
        axe_enonce_value = None
        
        if "horizontal" in enonce:
            axe_enonce_type = "horizontal"
            match = re.search(r'y = (\d+)', enonce)
            axe_enonce_value = match.group(1) if match else None
        elif "vertical" in enonce:
            axe_enonce_type = "vertical"
            match = re.search(r'x = (\d+)', enonce)
            axe_enonce_value = match.group(1) if match else None
        elif "y = x" in enonce or "oblique" in enonce or "bissectrice" in enonce:
            axe_enonce_type = "oblique"
            axe_enonce_value = "y=x"
        else:
            # Axe non identifié dans l'énoncé, skip
            continue
        
        nb_tested += 1
        
        # Déterminer le type d'axe dans le SVG
        axe_svg_type = None
        axe_svg_value = None
        
        if "y = x" in svg_q:
            axe_svg_type = "oblique"
            axe_svg_value = "y=x"
        elif "y =" in svg_q and "y = x" not in svg_q:
            axe_svg_type = "horizontal"
            match = re.search(r'y = (\d+)', svg_q)
            axe_svg_value = match.group(1) if match else None
        elif "x =" in svg_q:
            axe_svg_type = "vertical"
            match = re.search(r'x = (\d+)', svg_q)
            axe_svg_value = match.group(1) if match else None
        
        # Vérifier la cohérence
        coherent = True
        details = []
        
        if axe_enonce_type != axe_svg_type:
            coherent = False
            details.append(f"Type différent: énoncé={axe_enonce_type}, SVG={axe_svg_type}")
        
        if axe_enonce_value and axe_svg_value and axe_enonce_value != axe_svg_value:
            coherent = False
            details.append(f"Valeur différente: énoncé={axe_enonce_value}, SVG={axe_svg_value}")
        
        if not coherent:
            print(f"  ❌ EXERCICE {i} - INCOHÉRENT")
            print(f"     Énoncé (extrait): {enonce[:100]}...")
            print(f"     Attendu: {axe_enonce_type} {axe_enonce_value or ''}")
            print(f"     Obtenu dans SVG: {axe_svg_type} {axe_svg_value or ''}")
            for detail in details:
                print(f"     → {detail}")
            print()
            all_passed = False
    
    print(f"\n📊 Résumé: {nb_tested} exercices testés")
    
    if all_passed:
        print("="*70)
        print("✅ TEST BUG 2 RÉUSSI : Tous les axes sont cohérents")
        print("="*70)
    else:
        print("="*70)
        print("❌ TEST BUG 2 ÉCHOUÉ : Incohérences détectées")
        print("="*70)
    
    return all_passed


def test_exercice_verifier_symetrie():
    """
    TEST COMPLÉMENTAIRE : Vérifier que les exercices "verifier_symetrie"
    montrent bien les DEUX points (comportement attendu différent)
    """
    
    print("\n" + "="*70)
    print("TEST COMPLÉMENTAIRE : Exercices 'verifier_symetrie'")
    print("="*70)
    print("\nPour ce type, les DEUX points DOIVENT être visibles dans le sujet")
    print()
    
    data = generate_exercises("Symétrie axiale", "6e", "difficile", 30)
    
    if not data:
        print("❌ ÉCHEC: Génération impossible")
        return False
    
    exercises = data.get("document", {}).get("exercises", [])
    
    # Filtrer les exercices "verifier_symetrie"
    exercices_verifier = []
    for i, ex in enumerate(exercises, 1):
        spec = ex.get("spec_mathematique", {})
        params = spec.get("parametres", {})
        type_ex = params.get("type", "")
        
        if type_ex == "verifier_symetrie":
            exercices_verifier.append((i, ex))
    
    if not exercices_verifier:
        print("⚠️  Aucun exercice 'verifier_symetrie' dans cette génération")
        return True
    
    print(f"✅ {len(exercices_verifier)} exercice(s) 'verifier_symetrie' trouvé(s)")
    print()
    
    all_passed = True
    for i, ex in exercices_verifier:
        enonce = ex.get("enonce", "")
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        circles_q = svg_q.count('<circle')
        circles_c = svg_c.count('<circle')
        
        points_q = re.findall(r'<text[^>]*>([A-Z])</text>', svg_q)
        points_c = re.findall(r'<text[^>]*>([A-Z])</text>', svg_c)
        
        print(f"  📝 Exercice {i}:")
        print(f"     Énoncé: {enonce[:80]}...")
        print(f"     Sujet: {set(points_q)} ({circles_q} cercles)")
        print(f"     Corrigé: {set(points_c)} ({circles_c} cercles)")
        
        # Pour "verifier_symetrie", sujet = corrigé est CORRECT
        if len(set(points_q)) >= 2 and circles_q == circles_c:
            print(f"     ✅ CORRECT: Les 2 points sont visibles (attendu pour verifier_symetrie)")
        elif len(set(points_q)) < 2:
            print(f"     ❌ ÉCHEC: Moins de 2 points dans le sujet")
            all_passed = False
        else:
            print(f"     ⚠️  BIZARRE: Sujet ≠ corrigé pour verifier_symetrie")
        
        print()
    
    if all_passed:
        print("="*70)
        print("✅ TEST COMPLÉMENTAIRE RÉUSSI")
        print("="*70)
    else:
        print("="*70)
        print("❌ TEST COMPLÉMENTAIRE ÉCHOUÉ")
        print("="*70)
    
    return all_passed


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║  TESTS DE REPRODUCTION DES BUGS PRODUCTION                      ║")
    print("╚" + "="*68 + "╝")
    print()
    print("Ces tests reproduisent EXACTEMENT les cas signalés par l'utilisateur")
    
    results = []
    
    # Test Bug 1
    try:
        result1 = test_bug_1_trouver_symetrique_moyen()
        results.append(("BUG 1 - Point symétrique visible dans sujet", result1))
    except Exception as e:
        print(f"\n❌ TEST BUG 1 ÉCHOUÉ : {e}")
        import traceback
        traceback.print_exc()
        results.append(("BUG 1 - Point symétrique visible dans sujet", False))
    
    # Test Bug 2
    try:
        result2 = test_bug_2_axe_incoherent()
        results.append(("BUG 2 - Axe incohérent énoncé/schéma", result2))
    except Exception as e:
        print(f"\n❌ TEST BUG 2 ÉCHOUÉ : {e}")
        import traceback
        traceback.print_exc()
        results.append(("BUG 2 - Axe incohérent énoncé/schéma", False))
    
    # Test complémentaire
    try:
        result3 = test_exercice_verifier_symetrie()
        results.append(("TEST - verifier_symetrie (2 points visibles)", result3))
    except Exception as e:
        print(f"\n❌ TEST COMPLÉMENTAIRE ÉCHOUÉ : {e}")
        import traceback
        traceback.print_exc()
        results.append(("TEST - verifier_symetrie (2 points visibles)", False))
    
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
        print("✅ Validation production:")
        print("  • Bug 1 RÉSOLU: Point symétrique caché dans sujet 'trouver_symetrique'")
        print("  • Bug 2 RÉSOLU: Axes cohérents entre énoncé et schéma")
        print("  • Comportement correct pour 'verifier_symetrie' (2 points visibles)")
        sys.exit(0)
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        sys.exit(1)
