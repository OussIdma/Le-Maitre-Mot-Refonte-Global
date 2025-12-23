"""
Tests unitaires pour CALCUL_NOMBRES_V1
=====================================

Tests requis :
- génération OK pour chaque exercise_type
- génération OK pour 6e et 5e
- déterminisme (seed fixe → même résultat)
- aucune clé manquante dans variables
- erreur 422 si type invalide
- batch-compatible (appel répété)
"""

import pytest
from fastapi import HTTPException
from backend.generators.calcul_nombres_v1 import CalculNombresV1Generator


class TestCalculNombresV1:
    """Tests pour le générateur CALCUL_NOMBRES_V1."""
    
    def test_generate_operations_simples_6e_facile(self):
        """Test génération opérations simples 6e facile."""
        generator = CalculNombresV1Generator(seed=42)
        params = {
            "exercise_type": "operations_simples",
            "difficulty": "facile",
            "grade": "6e",
            "seed": 42
        }
        
        result = generator.generate(params)
        
        assert "variables" in result
        variables = result["variables"]
        
        # Vérifier toutes les variables requises
        required_vars = [
            "enonce", "solution", "calculs_intermediaires",
            "reponse_finale", "niveau", "type_exercice", "consigne"
        ]
        for var in required_vars:
            assert var in variables, f"Variable manquante: {var}"
            assert variables[var] is not None, f"Variable {var} est None"
            assert variables[var] != "", f"Variable {var} est vide"
        
        assert variables["niveau"] == "6e"
        assert variables["type_exercice"] == "operations_simples"
    
    def test_generate_operations_simples_5e_standard(self):
        """Test génération opérations simples 5e standard."""
        generator = CalculNombresV1Generator(seed=123)
        params = {
            "exercise_type": "operations_simples",
            "difficulty": "standard",
            "grade": "5e",
            "seed": 123
        }
        
        result = generator.generate(params)
        variables = result["variables"]
        
        assert variables["niveau"] == "5e"
        assert variables["type_exercice"] == "operations_simples"
        assert "enonce" in variables
        assert "reponse_finale" in variables
    
    def test_generate_priorites_operatoires_6e_facile(self):
        """Test génération priorités opératoires 6e facile."""
        generator = CalculNombresV1Generator(seed=456)
        params = {
            "exercise_type": "priorites_operatoires",
            "difficulty": "facile",
            "grade": "6e",
            "seed": 456
        }
        
        result = generator.generate(params)
        variables = result["variables"]
        
        assert variables["niveau"] == "6e"
        assert variables["type_exercice"] == "priorites_operatoires"
        assert "enonce" in variables
        assert "calculs_intermediaires" in variables
    
    def test_generate_priorites_operatoires_5e_standard(self):
        """Test génération priorités opératoires 5e standard."""
        generator = CalculNombresV1Generator(seed=789)
        params = {
            "exercise_type": "priorites_operatoires",
            "difficulty": "standard",
            "grade": "5e",
            "seed": 789
        }
        
        result = generator.generate(params)
        variables = result["variables"]
        
        assert variables["niveau"] == "5e"
        assert variables["type_exercice"] == "priorites_operatoires"
    
    def test_generate_decimaux_5e_standard(self):
        """Test génération décimaux 5e standard."""
        generator = CalculNombresV1Generator(seed=101)
        params = {
            "exercise_type": "decimaux",
            "difficulty": "standard",
            "grade": "5e",
            "seed": 101
        }
        
        result = generator.generate(params)
        variables = result["variables"]
        
        assert variables["niveau"] == "5e"
        assert variables["type_exercice"] == "decimaux"
        assert "enonce" in variables
        assert "reponse_finale" in variables
    
    def test_decimaux_6e_should_fail(self):
        """Test que décimaux en 6e lève une erreur 422."""
        generator = CalculNombresV1Generator(seed=202)
        params = {
            "exercise_type": "decimaux",
            "difficulty": "standard",
            "grade": "6e",
            "seed": 202
        }
        
        with pytest.raises(HTTPException) as exc_info:
            generator.generate(params)
        
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error_code"] == "INVALID_GRADE"
    
    def test_determinism_same_seed(self):
        """Test déterminisme : même seed → même résultat."""
        seed = 999
        
        generator1 = CalculNombresV1Generator(seed=seed)
        params = {
            "exercise_type": "operations_simples",
            "difficulty": "standard",
            "grade": "6e",
            "seed": seed
        }
        result1 = generator1.generate(params)
        
        generator2 = CalculNombresV1Generator(seed=seed)
        result2 = generator2.generate(params)
        
        # Les variables doivent être identiques
        assert result1["variables"] == result2["variables"]
    
    def test_determinism_different_seed(self):
        """Test que des seeds différents produisent des résultats différents."""
        generator1 = CalculNombresV1Generator(seed=111)
        generator2 = CalculNombresV1Generator(seed=222)
        
        params = {
            "exercise_type": "operations_simples",
            "difficulty": "standard",
            "grade": "6e",
            "seed": 111
        }
        result1 = generator1.generate(params)
        
        params2 = {
            "exercise_type": "operations_simples",
            "difficulty": "standard",
            "grade": "6e",
            "seed": 222
        }
        result2 = generator2.generate(params2)
        
        # Les énoncés doivent être différents (probablement)
        # Note: ce n'est pas garanti à 100%, mais très probable
        assert result1["variables"]["enonce"] != result2["variables"]["enonce"] or \
               result1["variables"]["reponse_finale"] != result2["variables"]["reponse_finale"]
    
    def test_invalid_exercise_type(self):
        """Test erreur 422 si type d'exercice invalide."""
        generator = CalculNombresV1Generator(seed=303)
        params = {
            "exercise_type": "type_invalide",
            "difficulty": "standard",
            "grade": "6e",
            "seed": 303
        }
        
        with pytest.raises(HTTPException) as exc_info:
            generator.generate(params)
        
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error_code"] == "INVALID_EXERCISE_TYPE"
    
    def test_invalid_grade(self):
        """Test erreur 422 si grade invalide."""
        generator = CalculNombresV1Generator(seed=404)
        params = {
            "exercise_type": "operations_simples",
            "difficulty": "standard",
            "grade": "4e",  # Invalide
            "seed": 404
        }
        
        with pytest.raises(HTTPException) as exc_info:
            generator.generate(params)
        
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error_code"] == "INVALID_GRADE"
    
    def test_invalid_difficulty(self):
        """Test erreur 422 si difficulté invalide."""
        generator = CalculNombresV1Generator(seed=505)
        params = {
            "exercise_type": "operations_simples",
            "difficulty": "difficile",  # Invalide (seulement facile/standard)
            "grade": "6e",
            "seed": 505
        }
        
        with pytest.raises(HTTPException) as exc_info:
            generator.generate(params)
        
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error_code"] == "INVALID_DIFFICULTY"
    
    def test_missing_seed(self):
        """Test erreur 422 si seed manquant."""
        generator = CalculNombresV1Generator(seed=606)
        params = {
            "exercise_type": "operations_simples",
            "difficulty": "standard",
            "grade": "6e",
            # seed manquant
        }
        
        with pytest.raises(HTTPException) as exc_info:
            generator.generate(params)
        
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error_code"] == "GENERATION_FAILED"
        assert "seed" in detail["error"] or "seed" in str(detail["message"]).lower()
    
    def test_batch_compatible(self):
        """Test que le générateur est batch-compatible (appels répétés)."""
        generator = CalculNombresV1Generator(seed=707)
        params = {
            "exercise_type": "operations_simples",
            "difficulty": "standard",
            "grade": "6e",
            "seed": 707
        }
        
        # Générer plusieurs fois
        results = []
        for i in range(5):
            # Utiliser un seed différent pour chaque appel (comme dans un batch)
            params_batch = params.copy()
            params_batch["seed"] = 707 + i
            result = generator.generate(params_batch)
            results.append(result)
        
        # Tous les résultats doivent avoir les variables requises
        for result in results:
            variables = result["variables"]
            required_vars = [
                "enonce", "solution", "calculs_intermediaires",
                "reponse_finale", "niveau", "type_exercice", "consigne"
            ]
            for var in required_vars:
                assert var in variables, f"Variable manquante dans batch: {var}"
    
    def test_all_variables_present(self):
        """Test que toutes les variables requises sont toujours présentes."""
        generator = CalculNombresV1Generator(seed=808)
        
        # Tester tous les types d'exercices
        exercise_types = ["operations_simples", "priorites_operatoires", "decimaux"]
        grades = ["6e", "5e"]
        
        for exercise_type in exercise_types:
            for grade in grades:
                if exercise_type == "decimaux" and grade == "6e":
                    # Décimaux non disponibles en 6e
                    continue
                
                params = {
                    "exercise_type": exercise_type,
                    "difficulty": "standard",
                    "grade": grade,
                    "seed": 808
                }
                
                result = generator.generate(params)
                variables = result["variables"]
                
                required_vars = [
                    "enonce", "solution", "calculs_intermediaires",
                    "reponse_finale", "niveau", "type_exercice", "consigne"
                ]
                
                for var in required_vars:
                    assert var in variables, \
                        f"Variable {var} manquante pour {exercise_type} {grade}"
                    assert variables[var] is not None, \
                        f"Variable {var} est None pour {exercise_type} {grade}"
                    assert variables[var] != "", \
                        f"Variable {var} est vide pour {exercise_type} {grade}"


