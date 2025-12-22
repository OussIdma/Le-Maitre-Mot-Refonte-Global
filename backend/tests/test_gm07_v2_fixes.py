#!/usr/bin/env python3
"""
Tests GM07 - Chapitre Pilote - Correctifs v2
=============================================

Tests spécifiques pour valider:
1. HTML pur (pas de Markdown/LaTeX)
2. Pas de doublons dans les lots
"""

import requests
import pytest
import re
from typing import Dict, Any, Set

BASE_URL = "https://math-exercise-sync.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api/v1/exercises"


def generate_gm07(offer: str = None, difficulty: str = None, seed: int = None) -> tuple:
    """Génère un exercice GM07"""
    payload = {"code_officiel": "6e_GM07"}
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


class TestGM07HtmlPur:
    """Tests: HTML pur sans Markdown ni LaTeX"""
    
    def test_solution_no_markdown_bold(self):
        """La solution ne contient pas de Markdown gras (**texte**)"""
        data, status = generate_gm07(difficulty="facile")
        assert status == 200
        
        solution = data.get("solution_html", "")
        # Chercher le pattern Markdown **texte**
        markdown_bold = re.search(r'\*\*[^*]+\*\*', solution)
        assert markdown_bold is None, f"Markdown trouvé dans solution: {markdown_bold.group() if markdown_bold else ''}"
    
    def test_solution_no_latex_math(self):
        """La solution ne contient pas de LaTeX ($...$)"""
        data, status = generate_gm07(difficulty="moyen")
        assert status == 200
        
        solution = data.get("solution_html", "")
        # Chercher le pattern LaTeX $...$
        latex_math = re.search(r'\$[^$]+\$', solution)
        assert latex_math is None, f"LaTeX trouvé dans solution: {latex_math.group() if latex_math else ''}"
    
    def test_solution_no_latex_times(self):
        """La solution ne contient pas \\times (utilise × à la place)"""
        data, status = generate_gm07(difficulty="facile")
        assert status == 200
        
        solution = data.get("solution_html", "")
        assert "\\times" not in solution, "\\times trouvé dans solution (doit être ×)"
    
    def test_enonce_no_markdown_bold(self):
        """L'énoncé ne contient pas de Markdown gras"""
        data, status = generate_gm07(difficulty="difficile")
        assert status == 200
        
        enonce = data.get("enonce_html", "")
        # Le Markdown ** ne doit pas apparaître (sauf dans <strong>)
        # On vérifie qu'il n'y a pas de ** hors des balises HTML
        markdown_bold = re.search(r'(?<!<strong>)\*\*[^*<]+\*\*(?!</strong>)', enonce)
        assert markdown_bold is None
    
    def test_solution_uses_html_strong(self):
        """La solution utilise <strong> au lieu de **"""
        data, status = generate_gm07(difficulty="facile")
        assert status == 200
        
        solution = data.get("solution_html", "")
        # Doit contenir des balises <strong>
        assert "<strong>" in solution, "La solution doit utiliser <strong> pour le gras"
    
    def test_all_exercises_html_pure(self):
        """Vérifie que TOUS les exercices sont en HTML pur"""
        # Tester plusieurs exercices avec différentes difficultés
        for diff in ["facile", "moyen", "difficile"]:
            for _ in range(3):
                data, status = generate_gm07(difficulty=diff)
                assert status == 200
                
                solution = data.get("solution_html", "")
                enonce = data.get("enonce_html", "")
                
                # Pas de Markdown
                assert "**" not in solution.replace("<strong>", "").replace("</strong>", ""), \
                    f"Markdown ** trouvé dans solution (diff={diff})"
                
                # Pas de LaTeX
                assert "$" not in solution, f"LaTeX $ trouvé dans solution (diff={diff})"
                assert "\\times" not in solution, f"\\times trouvé dans solution (diff={diff})"
                assert "\\frac" not in solution, f"\\frac trouvé dans solution (diff={diff})"
                assert "\\text" not in solution, f"\\text trouvé dans solution (diff={diff})"


class TestGM07SansDoublons:
    """Tests: Pas de doublons dans les lots"""
    
    def test_5_exercises_no_duplicates_free_facile(self):
        """5 exercices FREE facile ne doivent pas avoir de doublons"""
        exercise_ids: Set[int] = set()
        
        # Simuler 5 appels avec des seeds différents (comme le frontend)
        base_seed = 1000
        for i in range(5):
            seed = base_seed + i
            data, status = generate_gm07(difficulty="facile", seed=seed)
            assert status == 200
            
            ex_id = data["metadata"]["exercise_id"]
            exercise_ids.add(ex_id)
        
        # On doit avoir 5 exercices différents (ou moins si le stock est insuffisant)
        # Stock FREE facile: ids 1, 5, 6, 10 = 4 exercices max
        # Donc 4 uniques minimum
        assert len(exercise_ids) >= 4, f"Trop de doublons: {len(exercise_ids)} uniques sur 5"
    
    def test_5_exercises_no_duplicates_free_moyen(self):
        """5 exercices FREE moyen ne doivent pas avoir de doublons"""
        exercise_ids: Set[int] = set()
        
        base_seed = 2000
        for i in range(5):
            seed = base_seed + i
            data, status = generate_gm07(difficulty="moyen", seed=seed)
            assert status == 200
            
            ex_id = data["metadata"]["exercise_id"]
            exercise_ids.add(ex_id)
        
        # Stock FREE moyen: ids 2, 4, 7, 8 = 4 exercices max
        assert len(exercise_ids) >= 4, f"Trop de doublons: {len(exercise_ids)} uniques sur 5"
    
    def test_5_exercises_no_duplicates_pro_difficile(self):
        """5 exercices PRO difficile ne doivent pas avoir de doublons"""
        exercise_ids: Set[int] = set()
        
        base_seed = 3000
        for i in range(5):
            seed = base_seed + i
            data, status = generate_gm07(offer="pro", difficulty="difficile", seed=seed)
            assert status == 200
            
            ex_id = data["metadata"]["exercise_id"]
            exercise_ids.add(ex_id)
        
        # Stock PRO difficile: ids 3, 9 (free) + 13, 16, 19, 20 (pro) = 6 exercices
        # Donc 5 uniques attendus
        assert len(exercise_ids) == 5, f"Doublons détectés: {len(exercise_ids)} uniques sur 5"
    
    def test_different_seeds_different_exercises(self):
        """Des seeds différents doivent retourner des exercices différents"""
        ex1, _ = generate_gm07(difficulty="moyen", seed=100)
        ex2, _ = generate_gm07(difficulty="moyen", seed=101)
        ex3, _ = generate_gm07(difficulty="moyen", seed=102)
        ex4, _ = generate_gm07(difficulty="moyen", seed=103)
        
        ids = {
            ex1["metadata"]["exercise_id"],
            ex2["metadata"]["exercise_id"],
            ex3["metadata"]["exercise_id"],
            ex4["metadata"]["exercise_id"]
        }
        
        # 4 seeds différents → 4 exercices différents (si stock >= 4)
        assert len(ids) == 4, f"Seeds différents mais mêmes exercices: {len(ids)} uniques"
    
    def test_same_seed_same_exercise(self):
        """Le même seed doit toujours retourner le même exercice"""
        ex1, _ = generate_gm07(difficulty="facile", seed=12345)
        ex2, _ = generate_gm07(difficulty="facile", seed=12345)
        
        assert ex1["metadata"]["exercise_id"] == ex2["metadata"]["exercise_id"], \
            "Même seed mais exercices différents"


class TestGM07NonRegression:
    """Tests de non-régression"""
    
    def test_other_chapters_not_affected(self):
        """Les autres chapitres ne sont pas affectés"""
        # Test Fractions
        response = requests.post(
            f"{API_URL}/generate",
            json={"code_officiel": "6e_N08", "difficulte": "facile"},
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "FRACTION" in data["metadata"]["generator_code"]
    
    def test_free_pro_logic_preserved(self):
        """La logique Free/Pro est préservée"""
        # Free ne doit avoir que des exercices free
        for _ in range(5):
            data, status = generate_gm07(difficulty="moyen")
            assert status == 200
            assert data["metadata"]["is_premium"] == False
            assert data["metadata"]["offer"] == "free"
        
        # Pro peut avoir des exercices premium
        pro_found = False
        for _ in range(10):
            data, status = generate_gm07(offer="pro", difficulty="difficile")
            assert status == 200
            if data["metadata"]["is_premium"]:
                pro_found = True
                break
        
        assert pro_found, "Aucun exercice premium trouvé en mode pro"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
