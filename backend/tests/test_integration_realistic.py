"""
Tests d'intégration réalistes
Simule des scénarios typiques d'utilisation
"""
import requests
import json


BASE_URL = "http://localhost:8001"


def test_scenario_6e_aires():
    """Scénario 1: Génération exercices 6e Aires"""
    print("="*80)
    print("🧪 SCÉNARIO 1: 6e - Aires (Cercles)")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json={
            "matiere": "Mathématiques",
            "niveau": "6e",
            "chapitre": "Aires",
            "type_doc": "evaluation",
            "difficulte": "facile",
            "nb_exercices": 3,
            "versions": ["A"]
        },
        timeout=90
    )
    
    if response.status_code == 200:
        data = response.json()
        exercises = data['document']['exercises']
        
        print(f"✅ Génération réussie")
        print(f"📊 Exercices générés: {len(exercises)}")
        
        cercle_count = sum(1 for ex in exercises if 'cercle' in ex['enonce'].lower())
        print(f"🔵 Exercices cercles: {cercle_count}/{len(exercises)}")
        
        spec_count = sum(1 for ex in exercises if ex.get('spec_mathematique'))
        print(f"📋 spec_mathematique présente: {spec_count}/{len(exercises)}")
        
        return True
    else:
        print(f"❌ Erreur: {response.status_code}")
        return False


def test_scenario_6e_fractions():
    """Scénario 2: Génération exercices 6e Fractions"""
    print(f"\n{'='*80}")
    print("🧪 SCÉNARIO 2: 6e - Fractions")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json={
            "matiere": "Mathématiques",
            "niveau": "6e",
            "chapitre": "Fractions",
            "type_doc": "evaluation",
            "difficulte": "facile",
            "nb_exercices": 2,
            "versions": ["A"]
        },
        timeout=90
    )
    
    if response.status_code == 200:
        data = response.json()
        exercises = data['document']['exercises']
        
        print(f"✅ Génération réussie")
        print(f"📊 Exercices générés: {len(exercises)}")
        
        # Vérifier symboles fraction
        frac_count = sum(1 for ex in exercises if '\\frac' in ex['enonce'] or '/' in ex['enonce'])
        print(f"➗ Exercices avec fractions: {frac_count}/{len(exercises)}")
        
        return True
    else:
        print(f"❌ Erreur: {response.status_code}")
        return False


def test_scenario_3e_trigonometrie():
    """Scénario 3: Génération exercices 3e Trigonométrie"""
    print(f"\n{'='*80}")
    print("🧪 SCÉNARIO 3: 3e - Trigonométrie")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json={
            "matiere": "Mathématiques",
            "niveau": "3e",
            "chapitre": "Trigonométrie",
            "type_doc": "evaluation",
            "difficulte": "facile",
            "nb_exercices": 3,
            "versions": ["A"]
        },
        timeout=90
    )
    
    if response.status_code == 200:
        data = response.json()
        exercises = data['document']['exercises']
        
        print(f"✅ Génération réussie")
        print(f"📊 Exercices générés: {len(exercises)}")
        
        # Vérifier angles
        angle_count = sum(1 for ex in exercises if '°' in ex['enonce'])
        print(f"📐 Exercices avec angles: {angle_count}/{len(exercises)}")
        
        # Vérifier trigonométrie
        trigo_keywords = ['sin', 'cos', 'tan', 'cosinus', 'sinus']
        trigo_count = sum(1 for ex in exercises if any(kw in ex['enonce'].lower() for kw in trigo_keywords))
        print(f"📐 Exercices trigonométrie: {trigo_count}/{len(exercises)}")
        
        return True
    else:
        print(f"❌ Erreur: {response.status_code}")
        return False


def test_scenario_3e_thales():
    """Scénario 4: Génération exercices 3e Thalès"""
    print(f"\n{'='*80}")
    print("🧪 SCÉNARIO 4: 3e - Théorème de Thalès")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json={
            "matiere": "Mathématiques",
            "niveau": "3e",
            "chapitre": "Théorème de Thalès",
            "type_doc": "evaluation",
            "difficulte": "facile",
            "nb_exercices": 2,
            "versions": ["A"]
        },
        timeout=90
    )
    
    if response.status_code == 200:
        data = response.json()
        exercises = data['document']['exercises']
        
        print(f"✅ Génération réussie")
        print(f"📊 Exercices générés: {len(exercises)}")
        
        # Vérifier mentions Thalès
        thales_count = sum(1 for ex in exercises if 'thalès' in ex['enonce'].lower() or 'thales' in ex['enonce'].lower())
        print(f"🔺 Exercices Thalès: {thales_count}/{len(exercises)}")
        
        # Vérifier 5 points
        for i, ex in enumerate(exercises, 1):
            spec = ex.get('spec_mathematique', {})
            if spec:
                points = spec.get('parametres', {}).get('points', [])
                print(f"  Exercice {i}: {len(points)} points")
        
        return True
    else:
        print(f"❌ Erreur: {response.status_code}")
        return False


def test_scenario_multiple_versions():
    """Scénario 5: Génération versions A et B"""
    print(f"\n{'='*80}")
    print("🧪 SCÉNARIO 5: Génération versions A et B")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json={
            "matiere": "Mathématiques",
            "niveau": "4e",
            "chapitre": "Théorème de Pythagore",
            "type_doc": "evaluation",
            "difficulte": "facile",
            "nb_exercices": 2,
            "versions": ["A", "B"]
        },
        timeout=90
    )
    
    if response.status_code == 200:
        data = response.json()
        exercises = data['document']['exercises']
        
        print(f"✅ Génération réussie")
        print(f"📊 Exercices générés: {len(exercises)}")
        
        # Compter versions
        versions = {}
        for ex in exercises:
            v = ex.get('version', 'Unknown')
            versions[v] = versions.get(v, 0) + 1
        
        print(f"📑 Versions:")
        for v, count in versions.items():
            print(f"  - Version {v}: {count} exercices")
        
        return True
    else:
        print(f"❌ Erreur: {response.status_code}")
        return False


def run_all_integration_tests():
    """Exécute tous les tests d'intégration"""
    print("="*80)
    print("🔗 TESTS D'INTÉGRATION RÉALISTES")
    print("="*80)
    
    results = {
        "6e Aires": test_scenario_6e_aires(),
        "6e Fractions": test_scenario_6e_fractions(),
        "3e Trigonométrie": test_scenario_3e_trigonometrie(),
        "3e Thalès": test_scenario_3e_thales(),
        "Versions multiples": test_scenario_multiple_versions()
    }
    
    print(f"\n\n{'='*80}")
    print("📊 RÉSULTATS TESTS INTÉGRATION")
    print("="*80)
    
    success_count = sum(1 for v in results.values() if v)
    total = len(results)
    
    for scenario, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {scenario}")
    
    print(f"\n🎯 Taux de réussite: {success_count}/{total} ({success_count/total*100:.0f}%)")
    
    if success_count == total:
        print("\n✅ TOUS LES SCÉNARIOS RÉALISTES FONCTIONNENT")
    else:
        print(f"\n⚠️ {total - success_count} SCÉNARIO(S) EN ÉCHEC")


if __name__ == "__main__":
    run_all_integration_tests()
