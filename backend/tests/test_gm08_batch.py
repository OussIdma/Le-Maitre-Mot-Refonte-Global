#!/usr/bin/env python3
"""
Tests GM08 - Batch Production Ready
===================================

Tests pour valider le chapitre pilote #2 (GM08 - Grandeurs et Mesures):
1. Unicité garantie quand pool_size >= N
2. Comportement explicite quand pool_size < N (warning)
3. API batch endpoint
4. Filtrage par difficulté et offer
"""

import requests
import pytest
from typing import Set, Dict, Any

BASE_URL = "https://math-exercise-sync.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api/v1/exercises"


def generate_gm08_batch(
    nb_exercices: int = 1,
    offer: str = None,
    difficulty: str = None,
    seed: int = None
) -> tuple:
    """Appelle l'endpoint batch GM08"""
    payload = {
        "code_officiel": "6e_GM08",
        "nb_exercices": nb_exercices
    }
    if offer:
        payload["offer"] = offer
    if difficulty:
        payload["difficulte"] = difficulty
    if seed:
        payload["seed"] = seed
    
    response = requests.post(
        f"{API_URL}/generate/batch/gm08",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    return response.json(), response.status_code


def generate_gm08_single(
    offer: str = None,
    difficulty: str = None,
    seed: int = None
) -> tuple:
    """Appelle l'endpoint generate pour GM08"""
    payload = {
        "code_officiel": "6e_GM08"
    }
    if offer:
        payload["offer"] = offer
    if difficulty:
        payload["difficulte"] = difficulty
    if seed:
        payload["seed"] = seed
    
    response = requests.post(
        f"{API_URL}/generate",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    return response.json(), response.status_code


class TestGM08BatchBasic:
    """Tests de base pour le batch GM08"""
    
    def test_batch_endpoint_exists(self):
        """L'endpoint batch GM08 existe et répond"""
        data, status = generate_gm08_batch(nb_exercices=1, offer="free")
        assert status == 200
        assert "exercises" in data
        assert "batch_metadata" in data
    
    def test_batch_returns_exercises_list(self):
        """Le batch retourne une liste d'exercices"""
        data, status = generate_gm08_batch(nb_exercices=3, offer="free", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        assert isinstance(exercises, list)
        assert len(exercises) == 3
    
    def test_batch_metadata_structure(self):
        """Les métadonnées du batch ont la bonne structure"""
        data, status = generate_gm08_batch(nb_exercices=2, offer="free", seed=12345)
        
        assert status == 200
        batch_meta = data.get("batch_metadata", {})
        
        assert "requested" in batch_meta
        assert "returned" in batch_meta
        assert "available" in batch_meta


class TestGM08BatchUniciteGarantie:
    """Tests: Unicité batch quand pool_size >= N"""
    
    def test_batch_5_exercises_pro_all_difficulties(self):
        """PRO sans filtre difficulté: pool=20, demande=5 => 5 uniques"""
        data, status = generate_gm08_batch(nb_exercices=5, offer="pro", seed=12345)
        
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
        data, status = generate_gm08_batch(nb_exercices=5, offer="free", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        batch_meta = data.get("batch_metadata", {})
        
        assert batch_meta["requested"] == 5
        assert batch_meta["returned"] == 5
        assert batch_meta["available"] == 10  # FREE voit 10
        assert "warning" not in batch_meta
        
        ids = {ex["metadata"]["exercise_id"] for ex in exercises}
        assert len(ids) == 5
    
    def test_batch_10_exercises_free_returns_all_10(self):
        """FREE demande=10: retourne les 10 exercices free"""
        data, status = generate_gm08_batch(nb_exercices=10, offer="free", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        batch_meta = data.get("batch_metadata", {})
        
        assert batch_meta["requested"] == 10
        assert batch_meta["returned"] == 10
        assert batch_meta["available"] == 10
        assert "warning" not in batch_meta
        
        ids = {ex["metadata"]["exercise_id"] for ex in exercises}
        assert len(ids) == 10


class TestGM08BatchPoolInsuffisant:
    """Tests: Comportement quand pool_size < N"""
    
    def test_batch_5_exercises_free_facile_pool_4(self):
        """FREE facile: pool=4, demande=5 => 4 retournés + warning"""
        data, status = generate_gm08_batch(nb_exercices=5, offer="free", difficulty="facile", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        batch_meta = data.get("batch_metadata", {})
        
        # FREE facile: ids 1, 2, 3, 4 = 4 exercices
        assert batch_meta["requested"] == 5
        assert batch_meta["returned"] == 4
        assert batch_meta["available"] == 4
        
        # DOIT avoir un warning explicite
        assert "warning" in batch_meta
        assert "4" in batch_meta["warning"]
        
        # Tous uniques (pas de doublons malgré pool < N)
        ids = {ex["metadata"]["exercise_id"] for ex in exercises}
        assert len(ids) == 4
    
    def test_batch_12_exercises_free_pool_10(self):
        """FREE sans filtre: pool=10, demande=12 => 10 retournés + warning"""
        data, status = generate_gm08_batch(nb_exercices=12, offer="free", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        batch_meta = data.get("batch_metadata", {})
        
        assert batch_meta["requested"] == 12
        assert batch_meta["returned"] == 10
        assert batch_meta["available"] == 10
        assert "warning" in batch_meta
        
        ids = {ex["metadata"]["exercise_id"] for ex in exercises}
        assert len(ids) == 10


class TestGM08BatchFiltreDifficulte:
    """Tests: Filtrage par difficulté"""
    
    def test_batch_facile_only_facile_exercises(self):
        """Filtre facile: tous les exercices sont faciles"""
        data, status = generate_gm08_batch(nb_exercices=4, offer="pro", difficulty="facile", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        
        for ex in exercises:
            assert ex["metadata"]["difficulty"] == "facile"
    
    def test_batch_moyen_only_moyen_exercises(self):
        """Filtre moyen: tous les exercices sont moyens"""
        data, status = generate_gm08_batch(nb_exercices=4, offer="pro", difficulty="moyen", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        
        for ex in exercises:
            assert ex["metadata"]["difficulty"] == "moyen"
    
    def test_batch_difficile_only_difficile_exercises(self):
        """Filtre difficile: tous les exercices sont difficiles"""
        data, status = generate_gm08_batch(nb_exercices=4, offer="pro", difficulty="difficile", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        
        for ex in exercises:
            assert ex["metadata"]["difficulty"] == "difficile"


class TestGM08BatchFiltreOffer:
    """Tests: Filtrage par offer (free/pro)"""
    
    def test_free_only_free_exercises(self):
        """FREE: tous les exercices sont offer=free"""
        data, status = generate_gm08_batch(nb_exercices=5, offer="free", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        
        for ex in exercises:
            assert ex["metadata"]["offer"] == "free"
            assert ex["metadata"]["is_premium"] == False
    
    def test_pro_can_see_premium_exercises(self):
        """PRO: peut voir des exercices premium"""
        data, status = generate_gm08_batch(nb_exercices=15, offer="pro", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        
        # Au moins un exercice premium dans le lot
        has_premium = any(ex["metadata"]["is_premium"] for ex in exercises)
        assert has_premium, "PRO devrait avoir accès aux exercices premium"


class TestGM08BatchMetadata:
    """Tests: Métadonnées correctes sur chaque exercice"""
    
    def test_each_exercise_has_required_metadata(self):
        """Chaque exercice doit avoir les métadonnées requises"""
        data, status = generate_gm08_batch(nb_exercices=3, offer="pro", seed=12345)
        
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
            assert "batch_info" in meta
            assert meta["code_officiel"] == "6e_GM08"
            assert meta["source"] == "gm08_fixed_exercises"
    
    def test_batch_info_has_correct_structure(self):
        """batch_info doit avoir la bonne structure"""
        data, status = generate_gm08_batch(nb_exercices=3, offer="pro", seed=12345)
        
        assert status == 200
        exercises = data.get("exercises", [])
        
        for idx, ex in enumerate(exercises):
            batch_info = ex["metadata"]["batch_info"]
            
            assert batch_info["position"] == idx + 1
            assert batch_info["total_in_batch"] == 3
            assert batch_info["requested"] == 3
            assert batch_info["available"] == 20  # PRO voit tout


class TestGM08ExerciseContent:
    """Tests: Contenu des exercices GM08"""
    
    def test_exercise_has_html_content(self):
        """Les exercices ont du contenu HTML"""
        data, status = generate_gm08_batch(nb_exercices=1, offer="free", seed=12345)
        
        assert status == 200
        exercise = data["exercises"][0]
        
        assert "enonce_html" in exercise
        assert "solution_html" in exercise
        assert len(exercise["enonce_html"]) > 0
        assert len(exercise["solution_html"]) > 0
    
    def test_exercise_has_pure_html_no_latex(self):
        """Le contenu est en HTML pur (pas de LaTeX)"""
        data, status = generate_gm08_batch(nb_exercices=5, offer="pro", seed=12345)
        
        assert status == 200
        
        for ex in data["exercises"]:
            enonce = ex["enonce_html"]
            solution = ex["solution_html"]
            
            # Pas de délimiteurs LaTeX
            assert "$" not in enonce, f"LaTeX trouvé dans énoncé: {enonce[:100]}"
            assert "\\frac" not in enonce
            assert "\\(" not in enonce
            
            assert "$" not in solution, f"LaTeX trouvé dans solution: {solution[:100]}"
            assert "\\frac" not in solution
            assert "\\(" not in solution
    
    def test_solution_has_4_steps(self):
        """Les solutions ont 4 étapes (structure attendue)"""
        data, status = generate_gm08_batch(nb_exercices=3, offer="pro", seed=12345)
        
        assert status == 200
        
        for ex in data["exercises"]:
            solution = ex["solution_html"]
            
            # Doit avoir <ol> et des <li>
            assert "<ol>" in solution
            assert "</ol>" in solution
            assert solution.count("<li>") >= 3, f"Pas assez d'étapes dans: {solution[:200]}"


class TestGM08SingleEndpoint:
    """Tests: Endpoint /generate pour GM08"""
    
    def test_generate_single_gm08_works(self):
        """L'endpoint /generate fonctionne pour GM08"""
        data, status = generate_gm08_single(offer="free", seed=12345)
        
        assert status == 200
        assert "id_exercice" in data
        assert "enonce_html" in data
        assert data["metadata"]["code_officiel"] == "6e_GM08"
    
    def test_generate_single_respects_offer(self):
        """L'endpoint /generate respecte le paramètre offer"""
        data, status = generate_gm08_single(offer="free", seed=12345)
        
        assert status == 200
        assert data["metadata"]["offer"] == "free"
        assert data["metadata"]["is_premium"] == False
    
    def test_generate_single_respects_difficulty(self):
        """L'endpoint /generate respecte le paramètre difficulty"""
        data, status = generate_gm08_single(offer="pro", difficulty="difficile", seed=12345)
        
        assert status == 200
        assert data["metadata"]["difficulty"] == "difficile"


class TestGM08BatchReproducibility:
    """Tests: Reproductibilité avec seed"""
    
    def test_same_seed_same_result(self):
        """Même seed => même résultat"""
        seed = 999999
        
        data1, _ = generate_gm08_batch(nb_exercices=3, offer="free", seed=seed)
        data2, _ = generate_gm08_batch(nb_exercices=3, offer="free", seed=seed)
        
        ids1 = [ex["metadata"]["exercise_id"] for ex in data1["exercises"]]
        ids2 = [ex["metadata"]["exercise_id"] for ex in data2["exercises"]]
        
        assert ids1 == ids2, "Même seed devrait produire les mêmes exercices"
    
    def test_different_seed_different_order(self):
        """Seeds différents => ordres potentiellement différents"""
        data1, _ = generate_gm08_batch(nb_exercices=5, offer="pro", seed=11111)
        data2, _ = generate_gm08_batch(nb_exercices=5, offer="pro", seed=22222)
        
        ids1 = [ex["metadata"]["exercise_id"] for ex in data1["exercises"]]
        ids2 = [ex["metadata"]["exercise_id"] for ex in data2["exercises"]]
        
        # Avec des seeds différents, les exercices sélectionnés peuvent être différents
        # C'est le comportement attendu du shuffle avec seed
        # On vérifie simplement qu'on a bien 5 exercices uniques dans chaque cas
        assert len(set(ids1)) == 5
        assert len(set(ids2)) == 5


class TestGM08Families:
    """Tests: Familles d'exercices GM08"""
    
    def test_all_families_represented(self):
        """Toutes les familles d'exercices sont présentes"""
        data, status = generate_gm08_batch(nb_exercices=20, offer="pro", seed=12345)
        
        assert status == 200
        families = {ex["metadata"]["family"] for ex in data["exercises"]}
        
        expected_families = {"CONVERSION", "COMPARAISON", "PERIMETRE", "PROBLEME"}
        assert expected_families.issubset(families), f"Familles manquantes. Trouvées: {families}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
