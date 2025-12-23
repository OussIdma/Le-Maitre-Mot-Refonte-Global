"""
Tests pour le contrôle d'accès aux générateurs premium (P2.1)

Vérifie que :
- offer="free" + générateur premium => 403 PREMIUM_REQUIRED
- offer="pro" + générateur premium => 200 + is_premium true
- Le comportement est déterministe
"""
import pytest
from fastapi.testclient import TestClient
from backend.generators.factory import GeneratorFactory


def test_free_user_blocked_on_premium_generator(test_client):
    """
    Test P2.1.1: Un utilisateur free sur chapitre mixte => fallback sur free
    """
    response = test_client.post(
        "/api/v1/exercises/generate",
        json={
            "code_officiel": "6e_SP03",  # Chapitre mixte (premium + free)
            "offer": "free",
            "difficulte": "facile",
            "seed": 42
        }
    )
    
    # Chapitre mixte => fallback sur générateur free => HTTP 200
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier les metadata de fallback
    assert data["metadata"]["is_premium"] is False
    assert data["metadata"]["premium_available"] is True
    assert "RAISONNEMENT_MULTIPLICATIF_V1" in data["metadata"]["filtered_premium_generators"]
    assert "hint" in data["metadata"]
    assert "premium" in data["metadata"]["hint"].lower()


def test_pro_user_can_access_premium_generator(test_client):
    """
    Test P2.1.2: Un utilisateur pro peut accéder à un générateur premium
    """
    response = test_client.post(
        "/api/v1/exercises/generate",
        json={
            "code_officiel": "6e_SP03",  # Chapitre avec RAISONNEMENT_MULTIPLICATIF_V1
            "offer": "pro",
            "difficulte": "facile",
            "seed": 42
        }
    )
    
    # Doit retourner 200
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["is_premium"] is True
    assert data["metadata"]["generator_key"] in ["RAISONNEMENT_MULTIPLICATIF_V1", "CALCUL_NOMBRES_V1"]


def test_deterministic_premium_block(test_client):
    """
    Test P2.1.3: Le filtrage premium est déterministe
    """
    # Premier appel
    response1 = test_client.post(
        "/api/v1/exercises/generate",
        json={
            "code_officiel": "6e_SP03",
            "offer": "free",
            "difficulte": "facile",
            "seed": 42
        }
    )
    
    # Deuxième appel (même seed)
    response2 = test_client.post(
        "/api/v1/exercises/generate",
        json={
            "code_officiel": "6e_SP03",
            "offer": "free",
            "difficulte": "facile",
            "seed": 42
        }
    )
    
    # Les deux doivent retourner 200 (fallback sur free)
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Les metadata de filtrage doivent être identiques
    assert response1.json()["metadata"]["premium_available"] == response2.json()["metadata"]["premium_available"]
    assert response1.json()["metadata"]["filtered_premium_generators"] == response2.json()["metadata"]["filtered_premium_generators"]


def test_free_user_can_access_free_generators(test_client):
    """
    Test P2.1.4: Un utilisateur free peut toujours accéder aux générateurs free
    """
    # Trouver un chapitre avec des générateurs free
    response = test_client.post(
        "/api/v1/exercises/generate",
        json={
            "code_officiel": "6e_N08",  # Chapitre avec SIMPLIFICATION_FRACTIONS (free)
            "offer": "free",
            "difficulte": "facile",
            "seed": 42
        }
    )
    
    # Doit retourner 200 ou 422 structuré (pas 403)
    assert response.status_code in [200, 422]
    if response.status_code == 422:
        # Si 422, vérifier que ce n'est pas PREMIUM_REQUIRED
        data = response.json()
        assert data.get("detail", {}).get("error_code") != "PREMIUM_REQUIRED"


def test_all_premium_generators_have_min_offer_pro():
    """
    Test P2.1.5: Vérifier que tous les générateurs premium ont bien min_offer="pro"
    """
    premium_generators = [
        "RAISONNEMENT_MULTIPLICATIF_V1",
        "CALCUL_NOMBRES_V1",
    ]
    
    for gen_key in premium_generators:
        gen_class = GeneratorFactory.get(gen_key)
        if gen_class:
            meta = gen_class.get_meta()
            assert getattr(meta, 'min_offer', 'free') == "pro", \
                f"Le générateur {gen_key} doit avoir min_offer='pro'"
    
    # Vérifier que SIMPLIFICATION_FRACTIONS_V2 est bien free (stratégie commerciale)
    gen_class = GeneratorFactory.get("SIMPLIFICATION_FRACTIONS_V2")
    if gen_class:
        meta = gen_class.get_meta()
        assert getattr(meta, 'min_offer', 'free') == "free", \
            "SIMPLIFICATION_FRACTIONS_V2 doit être free (amélioration UX, pas premium)"


def test_filter_exercise_types_for_free_users(test_client):
    """
    Test P2.1.6: Les exercise_types sont filtrés pour les utilisateurs free
    """
    # Tester directement sur un chapitre connu pour contenir des générateurs premium
    # 6e_SP03 contient RAISONNEMENT_MULTIPLICATIF_V1 (premium) + PROPORTIONNALITE (free)
    response = test_client.post(
        "/api/v1/exercises/generate",
        json={
            "code_officiel": "6e_SP03",
            "offer": "free",
            "difficulte": "facile",
            "seed": 99
        }
    )
    
    # Chapitre mixte => 200 avec fallback sur générateur free
    assert response.status_code == 200
    
    # Vérifier les metadata de fallback
    data = response.json()
    assert data["metadata"]["is_premium"] is False
    assert data["metadata"]["premium_available"] is True
    assert "filtered_premium_generators" in data["metadata"]
    assert "RAISONNEMENT_MULTIPLICATIF_V1" in data["metadata"]["filtered_premium_generators"]
    assert "hint" in data["metadata"]

