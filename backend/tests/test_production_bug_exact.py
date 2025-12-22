"""
Test du bug exact signalé en production :

Niveau : 6e
Chapitre : Symétrie axiale
Difficulté : moyen

Bug : Le SUJET affiche le point symétrique, le segment et le point milieu
"""

import requests
import json
import sys
import re

BASE_URL = "http://localhost:8001"


def test_bug_exact_production():
    """
    Reproduire exactement le cas signalé par l'utilisateur
    """
    
    print("\n" + "="*70)
    print("TEST BUG EXACT PRODUCTION")
    print("="*70)
    print("\nConfiguration : 6e, Symétrie axiale, moyen")
    print()
    
    payload = {
        "matiere": "Mathématiques",
        "niveau": "6e",
        "chapitre": "Symétrie axiale",
        "type_doc": "Fiche",
        "difficulte": "moyen",
        "nb_exercices": 10
    }
    
    response = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=120)
    
    if response.status_code != 200:
        print(f"❌ Erreur HTTP {response.status_code}")
        print(response.text[:500])
        return False
    
    data = response.json()
    exercises = data.get("document", {}).get("exercises", [])
    
    print(f"✅ {len(exercises)} exercices générés\n")
    
    all_passed = True
    
    for i, ex in enumerate(exercises, 1):
        spec = ex.get("spec_mathematique", {})
        params = spec.get("parametres", {})
        type_ex = params.get("type", "N/A")
        
        enonce = ex.get("enonce", "")
        svg_q = ex.get("figure_svg_question", "")
        svg_c = ex.get("figure_svg_correction", "")
        
        print(f"=== EXERCICE {i} - Type: {type_ex} ===")
        print(f"Énoncé: {enonce[:80]}...")
        print()
        
        if type_ex == "trouver_symetrique":
            print("📋 Type: TROUVER LE SYMÉTRIQUE")
            print("   → Le sujet NE DOIT PAS contenir :")
            print("      - le point symétrique (E, M', etc.)")
            print("      - le segment")
            print("      - le point milieu")
            print()
            
            # Analyse du SUJET
            circles_q = svg_q.count('<circle')
            points_q = set(re.findall(r'<text[^>]*>([A-Z])</text>', svg_q))
            segments_bleus_q = len(re.findall(r'<line[^>]*stroke=["\']#0066CC["\']', svg_q))
            midpoint_rouge_q = len(re.findall(r'<circle[^>]*fill=["\']#FF0000["\']', svg_q))
            
            # Analyse du CORRIGÉ
            circles_c = svg_c.count('<circle')
            points_c = set(re.findall(r'<text[^>]*>([A-Z])</text>', svg_c))
            segments_bleus_c = len(re.findall(r'<line[^>]*stroke=["\']#0066CC["\']', svg_c))
            
            print("SUJET:")
            print(f"  - Points visibles: {points_q} ({circles_q} cercles)")
            print(f"  - Segments bleus: {segments_bleus_q}")
            print(f"  - Points milieu rouges: {midpoint_rouge_q}")
            
            print()
            print("CORRIGÉ:")
            print(f"  - Points visibles: {points_c} ({circles_c} cercles)")
            print(f"  - Segments bleus: {segments_bleus_c}")
            
            print()
            
            # Vérifications
            problems = []
            
            # 1. Le sujet doit avoir MOINS de cercles que le corrigé
            if circles_q >= circles_c:
                problems.append(f"Même nombre de cercles que le corrigé ({circles_q})")
            
            # 2. Le sujet NE DOIT PAS avoir de segment bleu
            if segments_bleus_q > 0:
                problems.append(f"{segments_bleus_q} segment(s) bleu(s) visible(s)")
            
            # 3. Le sujet NE DOIT PAS avoir de point milieu rouge
            if midpoint_rouge_q > 0:
                problems.append(f"{midpoint_rouge_q} point(s) milieu rouge(s) visible(s)")
            
            # 4. Le sujet doit avoir moins de points que le corrigé
            if len(points_c) <= len(points_q):
                problems.append(f"Même nombre de points que le corrigé ({len(points_q)})")
            
            if problems:
                print("❌ PROBLÈMES DÉTECTÉS:")
                for prob in problems:
                    print(f"   - {prob}")
                all_passed = False
            else:
                print("✅ SUJET PROPRE : Aucun élément de réponse visible")
        
        elif type_ex == "completer_figure":
            print("📋 Type: COMPLÉTER LE TRIANGLE")
            print("   → Le sujet NE DOIT PAS contenir :")
            print("      - le triangle image M'N'P' (en pointillé)")
            print()
            
            has_triangle_image_q = "triangle-image" in svg_q
            has_triangle_image_c = "triangle-image" in svg_c
            
            print(f"SUJET: Triangle image présent? {has_triangle_image_q}")
            print(f"CORRIGÉ: Triangle image présent? {has_triangle_image_c}")
            print()
            
            if has_triangle_image_q:
                print("❌ PROBLÈME: Le triangle image est visible dans le sujet!")
                all_passed = False
            else:
                print("✅ SUJET PROPRE")
        
        else:
            print(f"Type: {type_ex} - Pas de vérification spécifique")
        
        print()
    
    print("="*70)
    if all_passed:
        print("✅ TOUS LES EXERCICES SONT CORRECTS")
    else:
        print("❌ DES PROBLÈMES ONT ÉTÉ DÉTECTÉS")
    print("="*70)
    
    return all_passed


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║  TEST BUG EXACT PRODUCTION                                       ║")
    print("╚" + "="*68 + "╝")
    print()
    print("Reproduction exacte du cas signalé par l'utilisateur")
    
    try:
        result = test_bug_exact_production()
        
        print("\n\n")
        print("╔" + "="*68 + "╗")
        print("║  RÉSULTAT                                                        ║")
        print("╚" + "="*68 + "╝")
        print()
        
        if result:
            print("✅ TEST RÉUSSI")
            print()
            print("Le bug a été corrigé:")
            print("  • SUJET: Affiche uniquement les données connues")
            print("  • CORRIGÉ: Affiche données + réponse")
            sys.exit(0)
        else:
            print("❌ TEST ÉCHOUÉ")
            print()
            print("Le bug persiste:")
            print("  • Des éléments de réponse sont visibles dans le SUJET")
            print("  • Correction nécessaire")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
