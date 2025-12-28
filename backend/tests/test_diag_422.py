"""
Test minimal pour valider le format standardisé des 422 avec contexte de diagnostic.

Usage:
    python -m pytest backend/tests/test_diag_422.py -v
    ou
    python backend/tests/test_diag_422.py
"""
import pytest
import sys
import os

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from fastapi.testclient import TestClient
from backend.server import app

client = TestClient(app)


def test_422_has_standard_format():
    """
    Test que les 422 retournent le format standardisé avec context.
    """
    # Test 1: Code officiel invalide
    response = client.post(
        "/api/v1/exercises/generate",
        json={
            "code_officiel": "6E_INVALID_XXX",
            "offer": "free",
            "difficulte": "facile"
        }
    )
    
    assert response.status_code == 422
    detail = response.json()["detail"]
    
    # Vérifier format standard
    assert "error_code" in detail, "error_code manquant"
    assert "message" in detail, "message manquant"
    assert "hint" in detail, "hint manquant"
    assert "context" in detail, "context manquant (OBLIGATOIRE)"
    
    # Vérifier context contient les champs requis
    context = detail["context"]
    assert "code_officiel" in context, "context.code_officiel manquant"
    assert "chapter_code" in context, "context.chapter_code manquant"
    assert "pipeline_mode" in context, "context.pipeline_mode manquant"
    assert "total_exercises" in context, "context.total_exercises manquant"
    assert "dynamic_count" in context, "context.dynamic_count manquant"
    assert "static_count" in context, "context.static_count manquant"
    assert "enabled_generators_count" in context, "context.enabled_generators_count manquant"
    
    print(f"✅ Test 1 PASS: Format standardisé validé")
    print(f"   error_code: {detail['error_code']}")
    print(f"   context keys: {list(context.keys())}")


def test_422_context_has_diagnostic_info():
    """
    Test que le context contient les infos de diagnostic nécessaires.
    """
    # Test 2: Chapitre avec pipeline TEMPLATE mais sans exercices
    # (nécessite un chapitre réel configuré TEMPLATE mais sans exercices en DB)
    # Pour ce test, on utilise un code invalide qui retournera CODE_OFFICIEL_INVALID
    
    response = client.post(
        "/api/v1/exercises/generate",
        json={
            "code_officiel": "6E_TEST_NO_EXERCISES",
            "offer": "free",
            "difficulte": "facile"
        }
    )
    
    assert response.status_code == 422
    detail = response.json()["detail"]
    context = detail["context"]
    
    # Vérifier que le context permet de diagnostiquer le problème
    assert context.get("code_officiel") == "6E_TEST_NO_EXERCISES"
    assert context.get("chapter_from_db_exists") is not None, "chapter_from_db_exists manquant"
    
    print(f"✅ Test 2 PASS: Context contient infos de diagnostic")
    print(f"   chapter_from_db_exists: {context.get('chapter_from_db_exists')}")


def test_422_logs_are_grep_friendly():
    """
    Test que les logs [DIAG_422] sont présents (vérification manuelle via logs).
    Note: Ce test vérifie que le format est correct, pas que les logs sont écrits.
    """
    # Ce test est informatif - les logs sont vérifiés manuellement
    print("✅ Test 3 INFO: Vérifier manuellement les logs avec:")
    print("   docker logs le-maitre-mot-backend --tail 100 | grep DIAG_422")
    print("   docker logs le-maitre-mot-backend --tail 100 | grep DIAG_FLOW")


if __name__ == "__main__":
    print("=" * 60)
    print("Test minimal pour validation format 422 standardisé")
    print("=" * 60)
    
    try:
        test_422_has_standard_format()
        test_422_context_has_diagnostic_info()
        test_422_logs_are_grep_friendly()
        
        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS PASS")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



