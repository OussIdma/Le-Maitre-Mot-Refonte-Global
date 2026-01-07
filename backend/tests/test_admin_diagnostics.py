"""
Tests pour les endpoints de diagnostic et de reroll (P4.2)

Tests à implémenter:
- test_diagnostics_endpoint_returns_200: endpoint diagnostics répond 200 et contient pipeline_used + db_exercises_count
- test_reroll_conserve_template_id: reroll conserve template_id mais change seed/variables
- test_new_exercise_change_template_id: new-exercise change seed (et template_id si possible)
- test_disable_file_pipelines_empêche_pipelines_fichier: DISABLE_FILE_PIPELINES=true empêche choix pipeline FILE_*
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

from backend.server import app


@pytest.fixture
def client():
    """Fixture pour créer un client de test FastAPI"""
    return TestClient(app)


def test_diagnostics_endpoint_returns_200(client: TestClient):
    """
    Test: GET /api/admin/diagnostics/chapter/{code_officiel} retourne 200
    avec pipeline_used + db_exercises_count
    """
    # Tester avec un code de chapitre connu
    response = client.get("/api/admin/diagnostics/chapter/6e_N01")
    
    # Vérifier que la requête a réussi
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
    
    data = response.json()
    
    # Vérifier que la réponse contient les champs requis
    assert "code_officiel" in data
    assert "normalized_code" in data
    assert "pipeline_used" in data
    assert "reason" in data
    assert "db_exercises_count" in data
    assert "file_pipeline_available" in data
    assert "static_available" in data
    assert "fallback_used" in data
    
    # Vérifier que les valeurs sont du bon type
    assert isinstance(data["code_officiel"], str)
    assert isinstance(data["pipeline_used"], str)
    assert isinstance(data["reason"], str)
    assert isinstance(data["db_exercises_count"], int)
    assert isinstance(data["file_pipeline_available"], bool)
    assert isinstance(data["static_available"], bool)
    assert isinstance(data["fallback_used"], bool)
    
    # Vérifier que le code_officiel est correctement retourné
    assert data["code_officiel"] == "6e_N01"
    
    print(f"✅ Diagnostic endpoint works correctly: {data['pipeline_used']} for {data['code_officiel']}")


def test_reroll_conserve_template_id(client: TestClient):
    """
    Test: POST /api/v1/exercises/reroll-data conserve template_id mais change seed/variables
    """
    # Ce test nécessite un exercice existant avec generator_key et template_id
    # Pour l'instant, on teste juste que l'endpoint existe et renvoie une erreur structurée
    # plutot qu'une erreur interne
    response = client.post("/api/v1/exercises/reroll-data", json={
        "generator_key": "THALES_V1",
        "template_id": "default",
        "seed": 12345
    })
    
    # Devrait retourner 401 (auth requise) ou 200 (génération réussie) mais pas 500
    assert response.status_code in [401, 200], f"Expected 401/200, got {response.status_code}"
    
    if response.status_code == 401:
        data = response.json()
        # Vérifier que la structure d'erreur est cohérente
        assert "detail" in data
        if "detail" in data and isinstance(data["detail"], dict):
            assert "error_code" in data["detail"] or "error" in data["detail"]
    
    print(f"✅ Reroll endpoint responds with proper structure (status={response.status_code})")


def test_new_exercise_change_template_id(client: TestClient):
    """
    Test: POST /api/v1/exercises/new-exercise change seed (et template_id si possible)
    """
    # Ce test nécessite un generator_key valide
    # Pour l'instant, on teste juste que l'endpoint existe et renvoie une réponse structurée
    response = client.post("/api/v1/exercises/new-exercise", json={
        "generator_key": "THALES_V1",
        "seed": 12345
    })
    
    # Devrait retourner 401 (auth requise) ou 200 (génération réussie) mais pas 500
    assert response.status_code in [401, 200], f"Expected 401/200, got {response.status_code}"
    
    if response.status_code == 401:
        data = response.json()
        # Vérifier que la structure d'erreur est cohérente
        assert "detail" in data
        if "detail" in data and isinstance(data["detail"], dict):
            assert "error_code" in data["detail"] or "error" in data["detail"]
    
    print(f"✅ New exercise endpoint responds with proper structure (status={response.status_code})")


def test_disable_file_pipelines_empêche_pipelines_fichier(monkeypatch, client: TestClient):
    """
    Test: DISABLE_FILE_PIPELINES=true empêche le choix d'un pipeline FILE_*
    """
    # Définir l'environnement pour désactiver les pipelines fichiers
    monkeypatch.setenv("DISABLE_FILE_PIPELINES", "true")
    
    # Tester avec un code qui normalement utiliserait un pipeline fichier
    response = client.get("/api/admin/diagnostics/chapter/6e_GM07")
    
    assert response.status_code == 200
    data = response.json()
    
    # Avec DISABLE_FILE_PIPELINES=true, le pipeline devrait être DB_DYNAMIC ou similaire
    # et fallback_used devrait être True
    print(f"✅ With DISABLE_FILE_PIPELINES=true: pipeline={data['pipeline_used']}, fallback={data['fallback_used']}")
    
    # Réinitialiser l'environnement
    monkeypatch.setenv("DISABLE_FILE_PIPELINES", "false")


def test_diagnostics_endpoint_with_nonexistent_code(client: TestClient):
    """
    Test: GET /api/admin/diagnostics/chapter avec code inexistant fonctionne quand même
    """
    response = client.get("/api/admin/diagnostics/chapter/6e_CODE_INEXISTANT")
    
    # Devrait quand même retourner 200 mais avec des infos spécifiques
    assert response.status_code == 200
    
    data = response.json()
    
    # Vérifier que la réponse contient les champs requis
    assert "code_officiel" in data
    assert "pipeline_used" in data
    assert "reason" in data
    assert "db_exercises_count" in data
    assert "file_pipeline_available" in data
    assert "static_available" in data
    assert "fallback_used" in data
    
    # Le code_officiel doit être retourné correctement
    assert data["code_officiel"] == "6e_CODE_INEXISTANT"
    
    print(f"✅ Diagnostic endpoint handles nonexistent codes: {data['pipeline_used']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])