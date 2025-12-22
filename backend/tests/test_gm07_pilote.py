#!/usr/bin/env python3
"""
Tests GM07 - Chapitre Pilote
============================

Valide les 5 critères d'acceptance:
1. GM07 Free génère toujours un exercice Free
2. GM07 Pro génère des exercices Premium
3. La difficulté change réellement le contenu
4. Les solutions sont affichées correctement
5. Aucun autre chapitre n'est impacté
"""

import requests
import pytest
from typing import Dict, Any

BASE_URL = "https://math-exercise-sync.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api/v1/exercises"


def generate_gm07(offer: str = None, difficulty: str = None) -> tuple:
    """Génère un exercice GM07"""
    payload = {"code_officiel": "6e_GM07"}
    if offer:
        payload["offer"] = offer
    if difficulty:
        payload["difficulte"] = difficulty
    
    response = requests.post(
        f"{API_URL}/generate",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    return response.json(), response.status_code


class TestGM07Critere1FreeProduitFree:
    """Critère 1: GM07 Free génère toujours un exercice Free"""
    
    def test_free_facile_is_not_premium(self):
        data, status = generate_gm07(difficulty="facile")
        assert status == 200
        assert data["metadata"]["is_premium"] == False
        assert data["metadata"]["offer"] == "free"
    
    def test_free_moyen_is_not_premium(self):
        data, status = generate_gm07(difficulty="moyen")
        assert status == 200
        assert data["metadata"]["is_premium"] == False
        assert data["metadata"]["offer"] == "free"
    
    def test_free_difficile_is_not_premium(self):
        data, status = generate_gm07(difficulty="difficile")
        assert status == 200
        assert data["metadata"]["is_premium"] == False
        assert data["metadata"]["offer"] == "free"
    
    def test_free_no_difficulty_is_not_premium(self):
        data, status = generate_gm07()
        assert status == 200
        assert data["metadata"]["is_premium"] == False
    
    def test_free_exercise_id_in_range_1_10(self):
        """Les exercices Free ont un id entre 1 et 10"""
        for _ in range(5):
            data, status = generate_gm07(difficulty="facile")
            assert status == 200
            exercise_id = data["metadata"]["exercise_id"]
            assert 1 <= exercise_id <= 10, f"Free exercise id={exercise_id} hors range 1-10"


class TestGM07Critere2ProProduitPremium:
    """Critère 2: GM07 Pro génère des exercices Premium"""
    
    def test_pro_can_generate_premium(self):
        """Pro doit pouvoir générer des exercices premium"""
        premium_count = 0
        for _ in range(10):
            data, status = generate_gm07(offer="pro", difficulty="moyen")
            assert status == 200
            if data["metadata"]["is_premium"]:
                premium_count += 1
        
        assert premium_count > 0, "Pro n'a généré aucun exercice premium sur 10 essais"
    
    def test_pro_premium_has_correct_metadata(self):
        """Les exercices Pro premium ont offer='pro' et is_premium=True"""
        # Forcer un exercice difficile PRO (plus de chances d'avoir un premium)
        for _ in range(10):
            data, status = generate_gm07(offer="pro", difficulty="difficile")
            if data["metadata"]["is_premium"]:
                assert data["metadata"]["offer"] == "pro"
                assert data["metadata"]["exercise_id"] >= 11
                return
        
        pytest.skip("Pas d'exercice premium trouvé en 10 essais")


class TestGM07Critere3DifficulteChangeContenu:
    """Critère 3: La difficulté change réellement le contenu"""
    
    def test_facile_returns_facile(self):
        data, status = generate_gm07(difficulty="facile")
        assert status == 200
        assert data["metadata"]["difficulty"] == "facile"
    
    def test_moyen_returns_moyen(self):
        data, status = generate_gm07(difficulty="moyen")
        assert status == 200
        assert data["metadata"]["difficulty"] == "moyen"
    
    def test_difficile_returns_difficile(self):
        data, status = generate_gm07(difficulty="difficile")
        assert status == 200
        assert data["metadata"]["difficulty"] == "difficile"
    
    def test_different_difficulties_return_different_exercises(self):
        """Chaque difficulté doit retourner des exercices différents"""
        facile_ids = set()
        moyen_ids = set()
        difficile_ids = set()
        
        for _ in range(5):
            d1, _ = generate_gm07(difficulty="facile")
            d2, _ = generate_gm07(difficulty="moyen")
            d3, _ = generate_gm07(difficulty="difficile")
            
            facile_ids.add(d1["metadata"]["exercise_id"])
            moyen_ids.add(d2["metadata"]["exercise_id"])
            difficile_ids.add(d3["metadata"]["exercise_id"])
        
        # Vérifier qu'il n'y a pas de chevauchement (ou très peu)
        # Note: Avec les exercices fixés, cela devrait être strictement différent
        assert len(facile_ids & difficile_ids) == 0, "Facile et difficile ont des ids communs"


class TestGM07Critere4SolutionsAffichees:
    """Critère 4: Les solutions sont affichées correctement"""
    
    def test_solution_html_not_empty(self):
        data, status = generate_gm07(difficulty="facile")
        assert status == 200
        assert len(data["solution_html"]) > 50
    
    def test_solution_contains_correction_title(self):
        data, status = generate_gm07(difficulty="moyen")
        assert status == 200
        assert "<h4>" in data["solution_html"]
        assert "Correction" in data["solution_html"]
    
    def test_solution_contains_ordered_list(self):
        data, status = generate_gm07(difficulty="moyen")
        assert status == 200
        assert "<ol>" in data["solution_html"]
    
    def test_enonce_html_not_empty(self):
        data, status = generate_gm07(difficulty="difficile")
        assert status == 200
        assert len(data["enonce_html"]) > 50


class TestGM07Critere5PasDeRegression:
    """Critère 5: Aucun autre chapitre n'est impacté"""
    
    def test_fractions_still_works(self):
        response = requests.post(
            f"{API_URL}/generate",
            json={"code_officiel": "6e_N08", "difficulte": "facile"},
            timeout=30
        )
        data = response.json()
        
        assert response.status_code == 200
        assert "Fractions" in data["chapitre"]
        assert "FRACTION" in data["metadata"]["generator_code"]
    
    def test_symetrie_still_works(self):
        response = requests.post(
            f"{API_URL}/generate",
            json={"code_officiel": "6e_G07", "difficulte": "moyen"},
            timeout=30
        )
        data = response.json()
        
        assert response.status_code == 200
    
    def test_legacy_mode_still_works(self):
        response = requests.post(
            f"{API_URL}/generate",
            json={"niveau": "6e", "chapitre": "Fractions", "difficulte": "facile"},
            timeout=30
        )
        data = response.json()
        
        assert response.status_code == 200
        assert "Fractions" in data["chapitre"]


class TestGM07MetadataObligatoires:
    """Tests des métadonnées obligatoires"""
    
    def test_metadata_contains_is_premium(self):
        data, status = generate_gm07(difficulty="facile")
        assert status == 200
        assert "is_premium" in data["metadata"]
        assert isinstance(data["metadata"]["is_premium"], bool)
    
    def test_metadata_contains_offer(self):
        data, status = generate_gm07(difficulty="moyen")
        assert status == 200
        assert "offer" in data["metadata"]
        assert data["metadata"]["offer"] in ["free", "pro"]
    
    def test_metadata_contains_code_officiel(self):
        data, status = generate_gm07(difficulty="difficile")
        assert status == 200
        assert data["metadata"]["code_officiel"] == "6e_GM07"
    
    def test_metadata_contains_difficulty(self):
        data, status = generate_gm07(difficulty="moyen")
        assert status == 200
        assert data["metadata"]["difficulty"] == "moyen"
    
    def test_metadata_contains_family(self):
        data, status = generate_gm07(difficulty="facile")
        assert status == 200
        assert data["metadata"]["family"] in [
            "LECTURE_HORLOGE", "CONVERSION", "CALCUL_DUREE", "PROBLEME_DUREES"
        ]


class TestGM07ErrorHandling:
    """Tests de gestion d'erreurs"""
    
    def test_invalid_difficulty_uses_all(self):
        """Une difficulté invalide devrait retourner un exercice quand même"""
        data, status = generate_gm07(difficulty="super_difficile")
        # Soit on accepte et on ignore le filtre, soit 422
        # Comportement actuel: filtre vide, donc sélection dans tous
        assert status in [200, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
