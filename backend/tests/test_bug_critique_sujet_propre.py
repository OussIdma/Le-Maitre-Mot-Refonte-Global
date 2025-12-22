"""
Test du bug critique : Le SUJET d'un exercice "trouver_symetrique" 
NE DOIT contenir AUCUN élément de la réponse.

Bug signalé : Dans certains exercices, le sujet affiche :
- ❌ Le point symétrique E
- ❌ Le segment DE
- ❌ Le point milieu rouge

Ce test vérifie rigoureusement l'absence de ces éléments.
"""

import requests
import json
import sys
import re

BASE_URL = "http://localhost:8001"


def test_sujet_propre_trouver_symetrique():
    """
    Test critique : Le SUJET ne doit contenir AUCUN élément de réponse
    
    Pour un exercice "trouver_symetrique" :
        SUJET autorisé : point original, axe, grille
        SUJET interdit : point symétrique, segment, point milieu
    """
    
    print("\n" + "="*70)
    print("TEST CRITIQUE : SUJET PROPRE (aucun élément de réponse)")
    print("="*70)
    
    # Tester avec différentes difficultés
    all_passed = True
    total_tested = 0
    
    for difficulte in ["facile", "moyen", "difficile"]:
        print(f"\n📝 Difficulté : {difficulte}")
        
        payload = {
            "matiere": "Mathématiques",
            "niveau": "6e",
            "chapitre": "Symétrie axiale",
            "type_doc": "Fiche",
            "difficulte": difficulte,
            "nb_exercices": 15
        }
        
        response = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=120)
        
        if response.status_code != 200:
            print(f"  ❌ Erreur HTTP {response.status_code}")
            all_passed = False
            continue
        
        data = response.json()
        exercises = data.get("document", {}).get("exercises", [])
        
        # Filtrer les exercices "trouver_symetrique"
        exercices_trouver = []
        for i, ex in enumerate(exercises, 1):
            spec = ex.get("spec_mathematique", {})
            params = spec.get("parametres", {})
            if params.get("type") == "trouver_symetrique":
                exercices_trouver.append((i, ex))
        
        if not exercices_trouver:
            print(f"  ⚠️  Aucun exercice 'trouver_symetrique' généré")
            continue
        
        print(f"  ✅ {len(exercices_trouver)} exercice(s) 'trouver_symetrique' à tester")
        
        for idx, ex in exercices_trouver:
            total_tested += 1
            svg_q = ex.get("figure_svg_question", "")
            svg_c = ex.get("figure_svg_correction", "")
            
            # Extraire les noms des points de l'énoncé
            enonce = ex.get("enonce", "").lower()
            
            # Compter les éléments
            circles_q = svg_q.count('<circle')
            circles_c = svg_c.count('<circle')
            
            # Vérifier l'absence d'éléments interdits
            problemes = []
            
            # 1. Vérifier que le sujet a MOINS de cercles que le corrigé
            if circles_q >= circles_c:
                problemes.append(f"Même nombre de cercles ({circles_q}) que le corrigé")
            
            # 2. Chercher les cercles rouges avec fill (points milieu)
            circles_rouge_fill = re.findall(r'<circle[^>]*fill=["\']#FF0000["\']', svg_q)
            if circles_rouge_fill:
                problemes.append(f"{len(circles_rouge_fill)} cercle(s) rouge(s) (point milieu)")
            
            # 3. Chercher les segments bleus (segments de construction)
            segments_bleus = re.findall(r'<line[^>]*stroke=["\']#0066CC["\']', svg_q)
            if segments_bleus:
                problemes.append(f"{len(segments_bleus)} segment(s) bleu(s) (construction)")
            
            # 4. Chercher les points nommés avec prime (M', E', etc.)
            points_prime = re.findall(r'<text[^>]*>([A-Z])\'</text>', svg_q)
            if points_prime:
                problemes.append(f"Point(s) avec prime: {points_prime}")
            
            # 5. Vérifier le nombre de points visibles
            points_q = set(re.findall(r'<text[^>]*>([A-Z])</text>', svg_q))
            points_c = set(re.findall(r'<text[^>]*>([A-Z])</text>', svg_c))
            
            if len(points_c) > len(points_q):
                # Correct - le corrigé a plus de points
                pass
            elif len(points_c) == len(points_q):
                # Peut être correct pour "verifier_symetrie" mais pas pour "trouver_symetrique"
                problemes.append(f"Même nombre de points ({len(points_q)}) que le corrigé")
            
            # Afficher le résultat
            if problemes:
                print(f"    ❌ Exercice {idx} : {'; '.join(problemes)}")
                all_passed = False
            else:
                print(f"    ✅ Exercice {idx} : Sujet propre")
    
    print("\n" + "="*70)
    if all_passed:
        print(f"✅ TEST RÉUSSI : {total_tested} exercices testés, tous corrects")
    else:
        print(f"❌ TEST ÉCHOUÉ : Problèmes détectés")
    print("="*70)
    
    return all_passed


def test_corrige_complet():
    """
    Test complémentaire : Le CORRIGÉ doit contenir tous les éléments
    """
    
    print("\n" + "="*70)
    print("TEST COMPLÉMENTAIRE : CORRIGÉ COMPLET (tous les éléments)")
    print("="*70)
    
    payload = {
        "matiere": "Mathématiques",
        "niveau": "6e",
        "chapitre": "Symétrie axiale",
        "type_doc": "Fiche",
        "difficulte": "facile",
        "nb_exercices": 10
    }
    
    response = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=120)
    
    if response.status_code != 200:
        print(f"❌ Erreur HTTP {response.status_code}")
        return False
    
    data = response.json()
    exercises = data.get("document", {}).get("exercises", [])
    
    all_passed = True
    
    for i, ex in enumerate(exercises, 1):
        spec = ex.get("spec_mathematique", {})
        params = spec.get("parametres", {})
        
        if params.get("type") == "trouver_symetrique":
            svg_c = ex.get("figure_svg_correction", "")
            
            # Le corrigé DOIT contenir :
            circles_c = svg_c.count('<circle')
            segments_bleus = len(re.findall(r'<line[^>]*stroke=["\']#0066CC["\']', svg_c))
            
            print(f"  Exercice {i}:", end="")
            
            # Vérifier qu'il y a au moins 2 points (original + symétrique)
            if circles_c >= 2:
                print(f" {circles_c} points", end="")
            else:
                print(f" ❌ Seulement {circles_c} point(s)", end="")
                all_passed = False
            
            # Vérifier qu'il y a au moins 1 segment
            if segments_bleus >= 1:
                print(f", {segments_bleus} segment(s)", end="")
            else:
                print(f", ❌ Aucun segment", end="")
                all_passed = False
            
            print(" ✅" if circles_c >= 2 and segments_bleus >= 1 else "")
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ TEST RÉUSSI : Tous les corrigés sont complets")
    else:
        print("❌ TEST ÉCHOUÉ : Corrigés incomplets")
    print("="*70)
    
    return all_passed


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║  TEST BUG CRITIQUE : SUJET PROPRE                                ║")
    print("╚" + "="*68 + "╝")
    
    results = []
    
    # Test principal
    try:
        result1 = test_sujet_propre_trouver_symetrique()
        results.append(("Sujet propre (aucun élément de réponse)", result1))
    except Exception as e:
        print(f"\n❌ TEST ÉCHOUÉ : {e}")
        import traceback
        traceback.print_exc()
        results.append(("Sujet propre (aucun élément de réponse)", False))
    
    # Test complémentaire
    try:
        result2 = test_corrige_complet()
        results.append(("Corrigé complet (tous les éléments)", result2))
    except Exception as e:
        print(f"\n❌ TEST ÉCHOUÉ : {e}")
        import traceback
        traceback.print_exc()
        results.append(("Corrigé complet (tous les éléments)", False))
    
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
        print("✅ Validation:")
        print("  • SUJET : Aucun élément de réponse visible")
        print("  • CORRIGÉ : Tous les éléments présents")
        print("  • Règle pédagogique respectée")
        sys.exit(0)
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print()
        print("⚠️  Le bug critique persiste :")
        print("  • Des éléments de réponse apparaissent dans le sujet")
        print("  • Correction nécessaire dans geometry_svg_renderer.py")
        sys.exit(1)
