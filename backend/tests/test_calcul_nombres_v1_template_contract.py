"""
Test minimal pour valider le contrat template de CALCUL_NOMBRES_V1.

Vérifie que le générateur fournit toujours les variables requises par les templates admin :
- consigne (str)
- enonce (str)
- solution (str)
- reponse_finale (str)
- calculs_intermediaires (list[str] OU str)

Usage:
    pytest -q backend/tests/test_calcul_nombres_v1_template_contract.py
    ou
    python -m pytest backend/tests/test_calcul_nombres_v1_template_contract.py -v
"""
import pytest
import sys
import os

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.generators.calcul_nombres_v1 import CalculNombresV1Generator
from fastapi import HTTPException


def test_template_contract_operations_simples_facile():
    """Test que operations_simples facile fournit toutes les variables requises."""
    generator = CalculNombresV1Generator()
    params = {
        "exercise_type": "operations_simples",
        "difficulty": "facile",
        "grade": "6e",
        "seed": 42
    }
    
    result = generator.generate(params)
    variables = result["variables"]
    
    # Vérifier présence des variables requises
    assert "consigne" in variables, "consigne manquante"
    assert "enonce" in variables, "enonce manquante"
    assert "solution" in variables, "solution manquante"
    assert "reponse_finale" in variables, "reponse_finale manquante"
    assert "calculs_intermediaires" in variables, "calculs_intermediaires manquante"
    
    # Vérifier types
    assert isinstance(variables["consigne"], str), "consigne doit être str"
    assert isinstance(variables["enonce"], str), "enonce doit être str"
    assert isinstance(variables["solution"], str), "solution doit être str"
    assert isinstance(variables["reponse_finale"], str), "reponse_finale doit être str"
    assert isinstance(variables["calculs_intermediaires"], (str, list)), "calculs_intermediaires doit être str ou list"
    
    print(f"✅ Test 1 PASS: operations_simples facile")
    print(f"   consigne: {variables['consigne'][:50]}...")
    print(f"   enonce: {variables['enonce'][:50]}...")
    print(f"   reponse_finale: {variables['reponse_finale']}")


def test_template_contract_priorites_operatoires_standard():
    """Test que priorites_operatoires standard fournit toutes les variables requises."""
    generator = CalculNombresV1Generator()
    params = {
        "exercise_type": "priorites_operatoires",
        "difficulty": "standard",
        "grade": "6e",
        "seed": 123
    }
    
    result = generator.generate(params)
    variables = result["variables"]
    
    # Vérifier présence des variables requises
    assert "consigne" in variables, "consigne manquante"
    assert "enonce" in variables, "enonce manquante"
    assert "solution" in variables, "solution manquante"
    assert "reponse_finale" in variables, "reponse_finale manquante"
    assert "calculs_intermediaires" in variables, "calculs_intermediaires manquante"
    
    # Vérifier types
    assert isinstance(variables["consigne"], str), "consigne doit être str"
    assert isinstance(variables["enonce"], str), "enonce doit être str"
    assert isinstance(variables["solution"], str), "solution doit être str"
    assert isinstance(variables["reponse_finale"], str), "reponse_finale doit être str"
    assert isinstance(variables["calculs_intermediaires"], (str, list)), "calculs_intermediaires doit être str ou list"
    
    print(f"✅ Test 2 PASS: priorites_operatoires standard")
    print(f"   reponse_finale: {variables['reponse_finale']}")


def test_template_contract_decimaux_standard():
    """Test que decimaux standard fournit toutes les variables requises."""
    generator = CalculNombresV1Generator()
    params = {
        "exercise_type": "decimaux",
        "difficulty": "standard",
        "grade": "5e",  # decimaux nécessite 5e
        "seed": 456
    }
    
    result = generator.generate(params)
    variables = result["variables"]
    
    # Vérifier présence des variables requises
    assert "consigne" in variables, "consigne manquante"
    assert "enonce" in variables, "enonce manquante"
    assert "solution" in variables, "solution manquante"
    assert "reponse_finale" in variables, "reponse_finale manquante"
    assert "calculs_intermediaires" in variables, "calculs_intermediaires manquante"
    
    # Vérifier types
    assert isinstance(variables["consigne"], str), "consigne doit être str"
    assert isinstance(variables["enonce"], str), "enonce doit être str"
    assert isinstance(variables["solution"], str), "solution doit être str"
    assert isinstance(variables["reponse_finale"], str), "reponse_finale doit être str"
    assert isinstance(variables["calculs_intermediaires"], (str, list)), "calculs_intermediaires doit être str ou list"
    
    print(f"✅ Test 3 PASS: decimaux standard")
    print(f"   reponse_finale: {variables['reponse_finale']}")


def test_alias_echelle_maps_to_operations_simples():
    """Test que exercise_type='echelle' est accepté et mappé vers operations_simples."""
    generator = CalculNombresV1Generator()
    params = {
        "exercise_type": "echelle",  # Alias
        "difficulty": "facile",
        "grade": "6e",
        "seed": 789
    }
    
    # Ne doit PAS lever INVALID_EXERCISE_TYPE
    try:
        result = generator.generate(params)
        variables = result["variables"]
        
        # Vérifier que ça a fonctionné (pas d'exception)
        assert "enonce" in variables, "Génération échouée"
        assert "reponse_finale" in variables, "Génération échouée"
        
        # Vérifier que le type effectif est operations_simples
        assert variables.get("type_exercice") == "operations_simples", "Type exercice doit être operations_simples"
        
        print(f"✅ Test 4 PASS: alias 'echelle' accepté et mappé vers operations_simples")
        print(f"   enonce: {variables['enonce'][:50]}...")
        print(f"   reponse_finale: {variables['reponse_finale']}")
        
    except HTTPException as e:
        if e.status_code == 422 and "INVALID_EXERCISE_TYPE" in str(e.detail):
            pytest.fail(f"INVALID_EXERCISE_TYPE levé pour 'echelle': {e.detail}")
        else:
            raise  # Autre erreur, propager


def test_all_difficulties():
    """Test que toutes les difficultés fonctionnent."""
    generator = CalculNombresV1Generator()
    
    for difficulty in ["facile", "standard"]:
        params = {
            "exercise_type": "operations_simples",
            "difficulty": difficulty,
            "grade": "6e",
            "seed": 1000 + hash(difficulty) % 1000
        }
        
        result = generator.generate(params)
        variables = result["variables"]
        
        # Vérifier variables requises
        required = ["consigne", "enonce", "solution", "reponse_finale", "calculs_intermediaires"]
        for var in required:
            assert var in variables, f"{var} manquante pour difficulty={difficulty}"
        
        print(f"✅ Test difficulty={difficulty} PASS")


if __name__ == "__main__":
    print("=" * 60)
    print("Test contrat template CALCUL_NOMBRES_V1")
    print("=" * 60)
    
    try:
        test_template_contract_operations_simples_facile()
        test_template_contract_priorites_operatoires_standard()
        test_template_contract_decimaux_standard()
        test_alias_echelle_maps_to_operations_simples()
        test_all_difficulties()
        
        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS PASS")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

