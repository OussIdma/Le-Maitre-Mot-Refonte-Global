"""
Test contractuel ciblé pour SIMPLIFICATION_FRACTIONS_V1 et V2
==============================================================

Ce test vérifie spécifiquement que les générateurs SIMPLIFICATION_FRACTIONS
respectent le contrat complet (enonce_html/solution_html non vides, sujet≠corrigé).

CI-safe : pas de dépendance MongoDB.
"""

import pytest
from backend.tests.contracts.exercise_contract import assert_exercise_contract
from backend.tests.test_generators_contract import TestGeneratorsContract


# Éviter que pytest collecte les tests de TestGeneratorsContract depuis ce fichier
TestGeneratorsContract.__test__ = False


class TestSimplificationFractionsContract:
    """Tests contractuels spécifiques pour SIMPLIFICATION_FRACTIONS."""
    
    GENERATORS = ["SIMPLIFICATION_FRACTIONS_V1", "SIMPLIFICATION_FRACTIONS_V2"]
    TEST_SEEDS = [1, 2, 3]
    
    @pytest.mark.parametrize("generator_key", GENERATORS)
    def test_simplification_fractions_contract(self, generator_key: str):
        """
        Vérifie que chaque exercice SIMPLIFICATION_FRACTIONS respecte le contrat complet.
        
        Args:
            generator_key: Clé du générateur (V1 ou V2)
        """
        from backend.generators.factory import GeneratorFactory
        
        gen_class = GeneratorFactory.get(generator_key)
        if gen_class is None:
            pytest.skip(f"Générateur {generator_key} non trouvé")
        
        # Utiliser la méthode du test contractuel pour construire l'exercice
        test_instance = TestGeneratorsContract()
        
        errors = []
        
        for seed in self.TEST_SEEDS:
            try:
                # Essayer avec "standard" comme difficulté (V1/V2 supportent "standard")
                try:
                    exercise = test_instance._generate_exercise_dict(generator_key, seed, "standard")
                except ValueError:
                    # Si "standard" n'est pas supporté, essayer sans difficulté
                    exercise = test_instance._generate_exercise_dict(generator_key, seed, None)
                
                # Valider le contrat
                try:
                    assert_exercise_contract(exercise, generator_key)
                except AssertionError as e:
                    errors.append(f"seed={seed}: {e}")
            
            except Exception as e:
                errors.append(f"seed={seed}: génération échouée: {e}")
        
        if errors:
            pytest.fail(
                f"{generator_key}: violations du contrat:\n" +
                "\n".join(errors)
            )

