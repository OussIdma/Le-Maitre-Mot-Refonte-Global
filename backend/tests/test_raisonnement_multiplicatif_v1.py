"""
Tests unitaires pour RAISONNEMENT_MULTIPLICATIF_V1
==================================================

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
from backend.generators.raisonnement_multiplicatif_v1 import RaisonnementMultiplicatifV1Generator


class TestRaisonnementMultiplicatifV1:
    """Tests pour le générateur RAISONNEMENT_MULTIPLICATIF_V1."""
    
    def test_generate_proportionnalite_tableau_6e_facile(self):
        """Test génération proportionnalité tableau 6e facile."""
        generator = RaisonnementMultiplicatifV1Generator(seed=42)
        params = {
            "exercise_type": "proportionnalite_tableau",
            "difficulty": "facile",
            "grade": "6e",
            "seed": 42
        }
        
        result = generator.generate(params)
        
        assert "variables" in result
        variables = result["variables"]
        
        # Vérifier toutes les variables requises
        required_vars = [
            "enonce", "consigne", "solution", "calculs_intermediaires",
            "reponse_finale", "donnees", "methode", "niveau", "type_exercice"
        ]
        for var in required_vars:
            assert var in variables, f"Variable manquante: {var}"
            assert variables[var] is not None, f"Variable {var} est None"
            if var != "donnees":
                assert variables[var] != "", f"Variable {var} est vide"
        
        assert variables["niveau"] == "6e"
        assert variables["type_exercice"] == "proportionnalite_tableau"
        assert variables["methode"] == "coefficient_de_proportionnalite"
        assert "donnees" in variables
        assert isinstance(variables["donnees"], dict)
    
    def test_generate_proportionnalite_tableau_5e_moyen(self):
        """Test génération proportionnalité tableau 5e moyen."""
        generator = RaisonnementMultiplicatifV1Generator(seed=123)
        params = {
            "exercise_type": "proportionnalite_tableau",
            "difficulty": "moyen",
            "grade": "5e",
            "seed": 123
        }
        
        result = generator.generate(params)
        variables = result["variables"]
        
        assert variables["niveau"] == "5e"
        assert variables["type_exercice"] == "proportionnalite_tableau"
        assert "enonce" in variables
        assert "reponse_finale" in variables
    
    def test_generate_pourcentage_6e_facile(self):
        """Test génération pourcentage 6e facile."""
        generator = RaisonnementMultiplicatifV1Generator(seed=456)
        params = {
            "exercise_type": "pourcentage",
            "difficulty": "facile",
            "grade": "6e",
            "seed": 456
        }
        
        result = generator.generate(params)
        variables = result["variables"]
        
        assert variables["niveau"] == "6e"
        assert variables["type_exercice"] == "pourcentage"
        assert variables["methode"] == "regle_de_trois_pourcentage"
        assert "enonce" in variables
        assert "calculs_intermediaires" in variables
    
    def test_generate_pourcentage_5e_moyen(self):
        """Test génération pourcentage 5e moyen."""
        generator = RaisonnementMultiplicatifV1Generator(seed=789)
        params = {
            "exercise_type": "pourcentage",
            "difficulty": "moyen",
            "grade": "5e",
            "seed": 789
        }
        
        result = generator.generate(params)
        variables = result["variables"]
        
        assert variables["niveau"] == "5e"
        assert variables["type_exercice"] == "pourcentage"
    
    def test_generate_vitesse_5e_moyen(self):
        """Test génération vitesse 5e moyen."""
        generator = RaisonnementMultiplicatifV1Generator(seed=101)
        params = {
            "exercise_type": "vitesse",
            "difficulty": "moyen",
            "grade": "5e",
            "seed": 101
        }
        
        result = generator.generate(params)
        variables = result["variables"]
        
        assert variables["niveau"] == "5e"
        assert variables["type_exercice"] == "vitesse"
        assert variables["methode"] == "formule_vitesse"
        assert "enonce" in variables
        assert "reponse_finale" in variables
    
    def test_generate_echelle_5e_moyen(self):
        """Test génération échelle 5e moyen."""
        generator = RaisonnementMultiplicatifV1Generator(seed=202)
        params = {
            "exercise_type": "echelle",
            "difficulty": "moyen",
            "grade": "5e",
            "seed": 202
        }
        
        result = generator.generate(params)
        variables = result["variables"]
        
        assert variables["niveau"] == "5e"
        assert variables["type_exercice"] == "echelle"
        assert variables["methode"] == "calcul_echelle"
        assert "enonce" in variables
        assert "reponse_finale" in variables
    
    def test_determinism_same_seed(self):
        """Test déterminisme : même seed → même résultat."""
        seed = 999
        
        generator1 = RaisonnementMultiplicatifV1Generator(seed=seed)
        params = {
            "exercise_type": "proportionnalite_tableau",
            "difficulty": "moyen",
            "grade": "6e",
            "seed": seed
        }
        result1 = generator1.generate(params)
        
        generator2 = RaisonnementMultiplicatifV1Generator(seed=seed)
        result2 = generator2.generate(params)
        
        # Les variables doivent être identiques
        assert result1["variables"] == result2["variables"]
    
    def test_determinism_different_seed(self):
        """Test que des seeds différents produisent des résultats différents."""
        generator1 = RaisonnementMultiplicatifV1Generator(seed=111)
        generator2 = RaisonnementMultiplicatifV1Generator(seed=222)
        
        params1 = {
            "exercise_type": "proportionnalite_tableau",
            "difficulty": "moyen",
            "grade": "6e",
            "seed": 111
        }
        result1 = generator1.generate(params1)
        
        params2 = {
            "exercise_type": "proportionnalite_tableau",
            "difficulty": "moyen",
            "grade": "6e",
            "seed": 222
        }
        result2 = generator2.generate(params2)
        
        # Les énoncés doivent être différents (probablement)
        assert result1["variables"]["enonce"] != result2["variables"]["enonce"] or \
               result1["variables"]["reponse_finale"] != result2["variables"]["reponse_finale"]
    
    def test_invalid_exercise_type(self):
        """Test erreur 422 si type d'exercice invalide."""
        generator = RaisonnementMultiplicatifV1Generator(seed=303)
        params = {
            "exercise_type": "type_invalide",
            "difficulty": "moyen",
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
        generator = RaisonnementMultiplicatifV1Generator(seed=404)
        params = {
            "exercise_type": "proportionnalite_tableau",
            "difficulty": "moyen",
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
        generator = RaisonnementMultiplicatifV1Generator(seed=505)
        params = {
            "exercise_type": "proportionnalite_tableau",
            "difficulty": "tres_difficile",  # Invalide
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
        generator = RaisonnementMultiplicatifV1Generator(seed=606)
        params = {
            "exercise_type": "proportionnalite_tableau",
            "difficulty": "moyen",
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
        generator = RaisonnementMultiplicatifV1Generator(seed=707)
        params = {
            "exercise_type": "proportionnalite_tableau",
            "difficulty": "moyen",
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
                "enonce", "consigne", "solution", "calculs_intermediaires",
                "reponse_finale", "donnees", "methode", "niveau", "type_exercice"
            ]
            for var in required_vars:
                assert var in variables, f"Variable manquante dans batch: {var}"
    
    def test_all_variables_present(self):
        """Test que toutes les variables requises sont toujours présentes."""
        generator = RaisonnementMultiplicatifV1Generator(seed=808)
        
        # Tester tous les types d'exercices
        exercise_types = ["proportionnalite_tableau", "pourcentage", "vitesse", "echelle"]
        grades = ["6e", "5e"]
        
        for exercise_type in exercise_types:
            for grade in grades:
                # Vitesse et échelle principalement pour 5e
                if exercise_type in ["vitesse", "echelle"] and grade == "6e":
                    # Peut fonctionner mais moins courant
                    continue
                
                params = {
                    "exercise_type": exercise_type,
                    "difficulty": "moyen",
                    "grade": grade,
                    "seed": 808
                }
                
                result = generator.generate(params)
                variables = result["variables"]
                
                required_vars = [
                    "enonce", "consigne", "solution", "calculs_intermediaires",
                    "reponse_finale", "donnees", "methode", "niveau", "type_exercice"
                ]
                
                for var in required_vars:
                    assert var in variables, \
                        f"Variable {var} manquante pour {exercise_type} {grade}"
                    assert variables[var] is not None, \
                        f"Variable {var} est None pour {exercise_type} {grade}"
                    if var != "donnees":
                        assert variables[var] != "", \
                            f"Variable {var} est vide pour {exercise_type} {grade}"
                
                # Vérifier que donnees est un dict
                assert isinstance(variables["donnees"], dict), \
                    f"Variable donnees n'est pas un dict pour {exercise_type} {grade}"

