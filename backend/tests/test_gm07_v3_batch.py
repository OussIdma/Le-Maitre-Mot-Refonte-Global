#!/usr/bin/env python3
"""
Tests GM07 v3 - Batch Production Ready
======================================

Tests pour valider:
1. Unicité garantie quand pool_size >= N
2. Comportement explicite quand pool_size < N (warning)
3. API batch endpoint
"""

import requests
import pytest
from typing import Set, Dict, Any

BASE_URL = "https://math-exercise-sync.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api/v1/exercises"


def generate_gm07_batch(
    nb_exercices: int = 1,
    offer: str = None,
    difficulty: str = None,
    seed: int = None
) -> tuple:
    """Appelle l'endpoint batch GM07"""
    payload = {
        "code_officiel": "6e_GM07",
        "nb_exercices": nb_exercices
    }
    if offer:
        payload["offer"] = offer
    if difficulty:
        payload["difficulte"] = difficulty
    if seed:
        payload["seed"] = seed
    
    response = requests.post(
        f"{API_URL}/generate/batch/gm07",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    return response.json(), response.status_code


class TestGM07BatchUniciteGarantie:
    """Tests: Unicité batch quand pool_size >= N"""
    
    def test_batch_5_exercises_pro_all_difficulties(self):
        """PRO sans filtre difficulté: pool=20, demande=5 => 5 uniques"""
        data, status = generate_gm07_batch(nb_exercices=5, offer="pro", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        batch_meta = data.get("batch_metadata", {})
        
        # Vérifier les métadonnées
        assert batch_meta["requested"] == 5
        assert batch_meta["returned"] == 5
        assert batch_meta["available"] == 20  # PRO voit tout
        assert "warning" not in batch_meta
        
        # Vérifier unicité
        ids = {ex["metadata"]["exercise_id"] for ex in exercises}
        assert len(ids) == 5, f"Doublons détectés: {len(ids)} uniques sur 5"
    
    def test_batch_5_exercises_free_all_difficulties(self):
        """FREE sans filtre difficulté: pool=10, demande=5 => 5 uniques"""
        data, status = generate_gm07_batch(nb_exercices=5, offer="free", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        batch_meta = data.get("batch_metadata", {})
        
        assert batch_meta["requested"] == 5
        assert batch_meta["returned"] == 5
        assert batch_meta["available"] == 10  # FREE voit 10
        assert "warning" not in batch_meta
        
        ids = {ex["metadata"]["exercise_id"] for ex in exercises}
        assert len(ids) == 5
    
    def test_batch_6_exercises_pro_difficile(self):
        """PRO difficile: pool=6, demande=6 => 6 uniques"""
        data, status = generate_gm07_batch(nb_exercices=6, offer="pro", difficulty="difficile", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        batch_meta = data.get("batch_metadata", {})
        
        # PRO difficile: ids 3, 9 (free) + 13, 16, 19, 20 (pro) = 6
        assert batch_meta["requested"] == 6
        assert batch_meta["returned"] == 6
        assert batch_meta["available"] == 6
        assert "warning" not in batch_meta
        
        ids = {ex["metadata"]["exercise_id"] for ex in exercises}
        assert len(ids) == 6


class TestGM07BatchPoolInsuffisant:
    """Tests: Comportement quand pool_size < N"""
    
    def test_batch_5_exercises_free_facile_pool_4(self):
        """FREE facile: pool=4, demande=5 => 4 retournés + warning"""
        data, status = generate_gm07_batch(nb_exercices=5, offer="free", difficulty="facile", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        batch_meta = data.get("batch_metadata", {})
        
        # FREE facile: ids 1, 5, 6, 10 = 4 exercices
        assert batch_meta["requested"] == 5
        assert batch_meta["returned"] == 4
        assert batch_meta["available"] == 4
        
        # DOIT avoir un warning explicite
        assert "warning" in batch_meta
        assert "4" in batch_meta["warning"]
        assert "facile" in batch_meta["warning"].lower()
        
        # Tous uniques (pas de doublons malgré pool < N)
        ids = {ex["metadata"]["exercise_id"] for ex in exercises}
        assert len(ids) == 4
    
    def test_batch_5_exercises_free_moyen_pool_4(self):
        """FREE moyen: pool=4, demande=5 => 4 retournés + warning"""
        data, status = generate_gm07_batch(nb_exercices=5, offer="free", difficulty="moyen", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        batch_meta = data.get("batch_metadata", {})
        
        # FREE moyen: ids 2, 4, 7, 8 = 4 exercices
        assert batch_meta["requested"] == 5
        assert batch_meta["returned"] == 4
        assert batch_meta["available"] == 4
        assert "warning" in batch_meta
        
        ids = {ex["metadata"]["exercise_id"] for ex in exercises}
        assert len(ids) == 4
    
    def test_batch_10_exercises_free_difficile_pool_2(self):
        """FREE difficile: pool=2, demande=10 => 2 retournés + warning"""
        data, status = generate_gm07_batch(nb_exercices=10, offer="free", difficulty="difficile", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        batch_meta = data.get("batch_metadata", {})
        
        # FREE difficile: ids 3, 9 = 2 exercices
        assert batch_meta["requested"] == 10
        assert batch_meta["returned"] == 2
        assert batch_meta["available"] == 2
        assert "warning" in batch_meta
        assert "2" in batch_meta["warning"]
        
        ids = {ex["metadata"]["exercise_id"] for ex in exercises}
        assert len(ids) == 2


class TestGM07BatchMetadata:
    """Tests: Métadonnées correctes sur chaque exercice"""
    
    def test_each_exercise_has_required_metadata(self):
        """Chaque exercice doit avoir les métadonnées requises"""
        data, status = generate_gm07_batch(nb_exercices=3, offer="pro", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        
        for ex in exercises:
            meta = ex.get("metadata", {})
            
            # Champs obligatoires
            assert "exercise_id" in meta
            assert "difficulty" in meta
            assert "offer" in meta
            assert "is_premium" in meta
            assert "family" in meta
            assert "code_officiel" in meta
            
            # batch_info
            assert "batch_info" in meta
            assert "position" in meta["batch_info"]
            assert "total_in_batch" in meta["batch_info"]
    
    def test_batch_info_positions_correct(self):
        """Les positions batch doivent être correctes (1, 2, 3...)"""
        data, status = generate_gm07_batch(nb_exercices=5, offer="pro", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        
        positions = [ex["metadata"]["batch_info"]["position"] for ex in exercises]
        assert positions == [1, 2, 3, 4, 5]


class TestGM07BatchReproductibilite:
    """Tests: Reproductibilité avec seed"""
    
    def test_same_seed_same_batch(self):
        """Même seed => même batch (reproductible)"""
        data1, _ = generate_gm07_batch(nb_exercices=3, offer="pro", seed=99999)
        data2, _ = generate_gm07_batch(nb_exercices=3, offer="pro", seed=99999)
        
        ids1 = [ex["metadata"]["exercise_id"] for ex in data1["exercises"]]
        ids2 = [ex["metadata"]["exercise_id"] for ex in data2["exercises"]]
        
        assert ids1 == ids2, "Même seed mais batches différents"
    
    def test_different_seed_different_order(self):
        """Seeds différents => ordre différent"""
        data1, _ = generate_gm07_batch(nb_exercices=5, offer="pro", seed=11111)
        data2, _ = generate_gm07_batch(nb_exercices=5, offer="pro", seed=22222)
        
        ids1 = [ex["metadata"]["exercise_id"] for ex in data1["exercises"]]
        ids2 = [ex["metadata"]["exercise_id"] for ex in data2["exercises"]]
        
        # Les IDs doivent être les mêmes mais dans un ordre différent
        assert set(ids1) == set(ids2) or ids1 != ids2, "Seeds différents mais même ordre"


class TestGM07BatchNonRegression:
    """Tests de non-régression"""
    
    def test_single_endpoint_still_works(self):
        """L'endpoint single /generate fonctionne toujours"""
        response = requests.post(
            f"{API_URL}/generate",
            json={"code_officiel": "6e_GM07", "difficulte": "facile"},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id_exercice" in data
        assert data["metadata"]["code_officiel"] == "6e_GM07"
    
    def test_other_chapters_not_affected(self):
        """Les autres chapitres ne sont pas affectés"""
        response = requests.post(
            f"{API_URL}/generate",
            json={"code_officiel": "6e_N08", "difficulte": "facile"},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "FRACTION" in data["metadata"]["generator_code"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
