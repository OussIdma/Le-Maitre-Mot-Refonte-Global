"""
Tests pour vérifier que l'API /api/generate fonctionne correctement
pour les chapitres Symétrie axiale et Symétrie centrale.

Ce test vérifie :
1. La structure de réponse contient bien {"document": {"exercises": [...]}}
2. Chaque exercice contient les champs figure_svg_question et figure_svg_correction
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8001"


def test_symetrie_axiale_api():
    """Test que l'API génère correctement des exercices de Symétrie axiale"""
    
    print("\n" + "="*60)
    print("TEST 1: Symétrie axiale - Structure de réponse API")
    print("="*60)
    
    payload = {
        "matiere": "Mathématiques",
        "niveau": "6e",
        "chapitre": "Symétrie axiale",
        "type_doc": "Fiche",
        "difficulte": "facile",
        "nb_exercices": 2
    }
    
    print(f"\n📤 Requête: POST {BASE_URL}/api/generate")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json=payload,
        timeout=120
    )
    
    print(f"\n📥 Status Code: {response.status_code}")
    
    # Vérification 1: Status code
    if response.status_code != 200:
        print(f"❌ ÉCHEC: Status code {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return False
    
    # Vérification 2: Structure JSON
    try:
        data = response.json()
    except Exception as e:
        print(f"❌ ÉCHEC: Réponse n'est pas du JSON valide - {e}")
        return False
    
    # Vérification 3: Clé "document"
    if "document" not in data:
        print(f"❌ ÉCHEC: Clé 'document' absente dans la réponse")
        print(f"Clés présentes: {list(data.keys())}")
        return False
    
    print("✅ Clé 'document' présente")
    
    document = data["document"]
    
    # Vérification 4: Clé "exercises" dans document
    if "exercises" not in document:
        print(f"❌ ÉCHEC: Clé 'exercises' absente dans document")
        print(f"Clés document: {list(document.keys())}")
        return False
    
    print("✅ Clé 'exercises' présente dans document")
    
    exercises = document["exercises"]
    
    # Vérification 5: Liste d'exercices non vide
    if not exercises or len(exercises) == 0:
        print(f"❌ ÉCHEC: Liste exercises vide")
        return False
    
    print(f"✅ {len(exercises)} exercices générés")
    
    # Vérification 6: Chaque exercice a les champs SVG
    for i, exercise in enumerate(exercises, 1):
        print(f"\n  📝 Exercice {i}:")
        
        if "figure_svg_question" not in exercise:
            print(f"    ❌ ÉCHEC: Champ 'figure_svg_question' absent")
            return False
        
        if "figure_svg_correction" not in exercise:
            print(f"    ❌ ÉCHEC: Champ 'figure_svg_correction' absent")
            return False
        
        svg_q = exercise["figure_svg_question"]
        svg_c = exercise["figure_svg_correction"]
        
        if not svg_q or len(svg_q) == 0:
            print(f"    ❌ ÉCHEC: 'figure_svg_question' est vide")
            return False
        
        if not svg_c or len(svg_c) == 0:
            print(f"    ❌ ÉCHEC: 'figure_svg_correction' est vide")
            return False
        
        print(f"    ✅ figure_svg_question: {len(svg_q)} caractères")
        print(f"    ✅ figure_svg_correction: {len(svg_c)} caractères")
        
        # Vérifier que les SVGs sont des strings
        if not isinstance(svg_q, str):
            print(f"    ❌ ÉCHEC: figure_svg_question n'est pas une string (type: {type(svg_q)})")
            return False
        
        if not isinstance(svg_c, str):
            print(f"    ❌ ÉCHEC: figure_svg_correction n'est pas une string (type: {type(svg_c)})")
            return False
        
        print(f"    ✅ Les deux champs SVG sont des strings valides")
    
    print("\n" + "="*60)
    print("✅ TEST 1 RÉUSSI: Symétrie axiale - Structure correcte")
    print("="*60)
    return True


def test_symetrie_centrale_api():
    """Test que l'API génère correctement des exercices de Symétrie centrale"""
    
    print("\n" + "="*60)
    print("TEST 2: Symétrie centrale - Structure de réponse API")
    print("="*60)
    
    payload = {
        "matiere": "Mathématiques",
        "niveau": "5e",
        "chapitre": "Symétrie centrale",
        "type_doc": "Fiche",
        "difficulte": "facile",
        "nb_exercices": 2
    }
    
    print(f"\n📤 Requête: POST {BASE_URL}/api/generate")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json=payload,
        timeout=120
    )
    
    print(f"\n📥 Status Code: {response.status_code}")
    
    # Vérification 1: Status code
    if response.status_code != 200:
        print(f"❌ ÉCHEC: Status code {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return False
    
    # Vérification 2: Structure JSON
    try:
        data = response.json()
    except Exception as e:
        print(f"❌ ÉCHEC: Réponse n'est pas du JSON valide - {e}")
        return False
    
    # Vérification 3: Clé "document"
    if "document" not in data:
        print(f"❌ ÉCHEC: Clé 'document' absente dans la réponse")
        print(f"Clés présentes: {list(data.keys())}")
        return False
    
    print("✅ Clé 'document' présente")
    
    document = data["document"]
    
    # Vérification 4: Clé "exercises" dans document
    if "exercises" not in document:
        print(f"❌ ÉCHEC: Clé 'exercises' absente dans document")
        print(f"Clés document: {list(document.keys())}")
        return False
    
    print("✅ Clé 'exercises' présente dans document")
    
    exercises = document["exercises"]
    
    # Vérification 5: Liste d'exercices non vide
    if not exercises or len(exercises) == 0:
        print(f"❌ ÉCHEC: Liste exercises vide")
        return False
    
    print(f"✅ {len(exercises)} exercices générés")
    
    # Vérification 6: Chaque exercice a les champs SVG
    for i, exercise in enumerate(exercises, 1):
        print(f"\n  📝 Exercice {i}:")
        
        if "figure_svg_question" not in exercise:
            print(f"    ❌ ÉCHEC: Champ 'figure_svg_question' absent")
            return False
        
        if "figure_svg_correction" not in exercise:
            print(f"    ❌ ÉCHEC: Champ 'figure_svg_correction' absent")
            return False
        
        svg_q = exercise["figure_svg_question"]
        svg_c = exercise["figure_svg_correction"]
        
        if not svg_q or len(svg_q) == 0:
            print(f"    ❌ ÉCHEC: 'figure_svg_question' est vide")
            return False
        
        if not svg_c or len(svg_c) == 0:
            print(f"    ❌ ÉCHEC: 'figure_svg_correction' est vide")
            return False
        
        print(f"    ✅ figure_svg_question: {len(svg_q)} caractères")
        print(f"    ✅ figure_svg_correction: {len(svg_c)} caractères")
        
        # Vérifier que les SVGs sont des strings
        if not isinstance(svg_q, str):
            print(f"    ❌ ÉCHEC: figure_svg_question n'est pas une string (type: {type(svg_q)})")
            return False
        
        if not isinstance(svg_c, str):
            print(f"    ❌ ÉCHEC: figure_svg_correction n'est pas une string (type: {type(svg_c)})")
            return False
        
        print(f"    ✅ Les deux champs SVG sont des strings valides")
    
    print("\n" + "="*60)
    print("✅ TEST 2 RÉUSSI: Symétrie centrale - Structure correcte")
    print("="*60)
    return True


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║  TESTS API /api/generate - Symétries                    ║")
    print("╚" + "="*58 + "╝")
    
    results = []
    
    # Test 1
    try:
        result1 = test_symetrie_axiale_api()
        results.append(("Symétrie axiale", result1))
    except Exception as e:
        print(f"\n❌ TEST 1 ÉCHOUÉ avec exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Symétrie axiale", False))
    
    # Test 2
    try:
        result2 = test_symetrie_centrale_api()
        results.append(("Symétrie centrale", result2))
    except Exception as e:
        print(f"\n❌ TEST 2 ÉCHOUÉ avec exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Symétrie centrale", False))
    
    # Résumé
    print("\n\n")
    print("╔" + "="*58 + "╗")
    print("║  RÉSUMÉ DES TESTS                                        ║")
    print("╚" + "="*58 + "╝")
    print()
    
    for test_name, passed in results:
        status = "✅ RÉUSSI" if passed else "❌ ÉCHOUÉ"
        print(f"  {test_name:30s} : {status}")
    
    print()
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("🎉 TOUS LES TESTS SONT PASSÉS!")
        sys.exit(0)
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        sys.exit(1)
