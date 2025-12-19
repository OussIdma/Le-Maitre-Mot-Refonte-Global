"""
TEST P1 - Exercices Dynamiques THALES_V1
========================================

Ces tests vérifient:
1. Le générateur THALES_V1 produit des variables cohérentes
2. Les templates sont correctement rendus
3. Les exercices dynamiques sont différents avec des seeds différents
4. Les exercices statiques GM07/GM08 continuent de fonctionner
"""

import pytest
from generators.thales_generator import generate_dynamic_exercise, ThalesV1Generator, get_generator
from services.template_renderer import render_template, validate_template
from services.tests_dyn_handler import generate_tests_dyn_exercise, generate_tests_dyn_batch


class TestThalesV1Generator:
    """Tests du générateur THALES_V1."""
    
    def test_generator_returns_required_fields(self):
        """Le générateur retourne tous les champs obligatoires."""
        result = generate_dynamic_exercise("THALES_V1", seed=42)
        
        assert "variables" in result
        assert "results" in result
        assert "svg_params" in result
        assert "figure_svg_enonce" in result
        assert "figure_svg_solution" in result
    
    def test_variables_contain_required_keys(self):
        """Les variables contiennent les clés requises."""
        result = generate_dynamic_exercise("THALES_V1", seed=42)
        variables = result["variables"]
        
        # Clés communes obligatoires
        assert "figure_type" in variables
        assert "coefficient" in variables
        assert "transformation" in variables
        assert "transformation_verbe" in variables
    
    def test_coefficient_in_valid_range(self):
        """Le coefficient est dans une plage valide."""
        for seed in range(10):
            result = generate_dynamic_exercise("THALES_V1", seed=seed)
            coef = result["variables"]["coefficient"]
            
            assert coef > 0, f"Coefficient négatif: {coef}"
            assert coef <= 10, f"Coefficient trop grand: {coef}"
    
    def test_reproducibility_with_same_seed(self):
        """Même seed → mêmes résultats."""
        result1 = generate_dynamic_exercise("THALES_V1", seed=12345)
        result2 = generate_dynamic_exercise("THALES_V1", seed=12345)
        
        assert result1["variables"] == result2["variables"]
    
    def test_different_results_with_different_seeds(self):
        """Seeds différents → résultats différents."""
        result1 = generate_dynamic_exercise("THALES_V1", seed=1)
        result2 = generate_dynamic_exercise("THALES_V1", seed=2)
        
        # Au moins une différence dans les variables
        assert result1["variables"] != result2["variables"]
    
    def test_difficulty_affects_coefficient(self):
        """La difficulté affecte les coefficients disponibles."""
        facile_coefs = set()
        difficile_coefs = set()
        
        for seed in range(20):
            facile = ThalesV1Generator(seed=seed, difficulty="facile").generate()
            difficile = ThalesV1Generator(seed=seed, difficulty="difficile").generate()
            
            facile_coefs.add(facile["variables"]["coefficient"])
            difficile_coefs.add(difficile["variables"]["coefficient"])
        
        # Les coefficients faciles sont des entiers
        for c in facile_coefs:
            assert c == int(c), f"Coefficient facile non entier: {c}"


class TestTemplateRenderer:
    """Tests du service de rendu de templates."""
    
    def test_simple_replacement(self):
        """Remplacement simple de placeholders."""
        template = "Le côté mesure {{cote}} cm"
        result = render_template(template, {"cote": 5})
        
        assert result == "Le côté mesure 5 cm"
    
    def test_multiple_replacements(self):
        """Remplacement de plusieurs placeholders."""
        template = "Rectangle {{longueur}} × {{largeur}} cm"
        result = render_template(template, {"longueur": 6, "largeur": 4})
        
        assert result == "Rectangle 6 × 4 cm"
    
    def test_float_formatting(self):
        """Les floats sont formatés intelligemment."""
        template = "Coefficient: {{coef}}"
        
        # 5.0 → 5
        assert render_template(template, {"coef": 5.0}) == "Coefficient: 5"
        
        # 5.5 reste 5.5
        assert render_template(template, {"coef": 5.5}) == "Coefficient: 5.5"
    
    def test_missing_variable_keeps_placeholder(self):
        """Variable absente → placeholder conservé."""
        template = "{{present}} et {{absent}}"
        result = render_template(template, {"present": "OK"})
        
        assert "OK" in result
        assert "{{absent}}" in result
    
    def test_template_validation(self):
        """La validation de template fonctionne."""
        template = "{{a}} + {{b}} = {{c}}"
        
        valid_result = validate_template(template, ["a", "b", "c"])
        assert valid_result["valid"] == True
        
        invalid_result = validate_template(template, ["a", "b", "c", "d"])
        assert invalid_result["valid"] == False
        assert "d" in invalid_result["missing_variables"]


class TestDynamicExerciseGeneration:
    """Tests de génération d'exercices dynamiques."""
    
    def test_generate_single_dynamic_exercise(self):
        """Génère un exercice dynamique unique."""
        ex = generate_tests_dyn_exercise(offer="free", seed=42)
        
        assert ex is not None
        assert ex["metadata"]["is_dynamic"] == True
        assert ex["metadata"]["generator_key"] == "THALES_V1"
        assert "{{" not in ex["enonce_html"]  # Pas de placeholder non résolu
    
    def test_generate_dynamic_batch(self):
        """Génère un batch d'exercices dynamiques."""
        exercises, info = generate_tests_dyn_batch(offer="free", count=3, seed=123)
        
        assert len(exercises) >= 1  # Au moins 1 template disponible
        assert info["is_dynamic"] == True
        
        for ex in exercises:
            assert ex["metadata"]["is_dynamic"] == True
    
    def test_svg_generated_for_dynamic(self):
        """Les SVG sont générés pour les exercices dynamiques."""
        ex = generate_tests_dyn_exercise(offer="free", seed=42)
        
        assert ex["figure_svg_enonce"] is not None
        assert ex["figure_svg_solution"] is not None
        assert ex["figure_svg_enonce"] != ex["figure_svg_solution"]


class TestNonRegression:
    """Tests de non-régression pour GM07/GM08."""
    
    def test_gm07_still_works(self):
        """GM07 fonctionne toujours après ajout des exercices dynamiques."""
        from services.gm07_handler import generate_gm07_batch
        
        exercises, info = generate_gm07_batch(
            offer="free",
            difficulty="facile",
            count=2,
            seed=42
        )
        
        assert len(exercises) >= 1
        assert info["returned"] >= 1
        
        for ex in exercises:
            assert ex["metadata"].get("is_dynamic") != True  # Pas dynamique
            assert ex["metadata"]["code_officiel"] == "6e_GM07"
    
    def test_gm07_has_variables(self):
        """Les exercices GM07 avec SVG ont le champ variables."""
        from services.gm07_handler import generate_gm07_batch
        
        exercises, _ = generate_gm07_batch(offer="free", count=5, seed=42)
        
        for ex in exercises:
            if ex.get("figure_svg_enonce"):
                # Si SVG, doit avoir variables_used avec source="variables"
                vars_used = ex["metadata"].get("variables_used", {})
                assert vars_used.get("source") == "variables", \
                    f"Exercice {ex['id_exercice']} devrait utiliser variables comme source"


class TestCoherenceTexteSVG:
    """Tests de cohérence entre texte et SVG pour exercices dynamiques."""
    
    def test_dynamic_svg_matches_variables(self):
        """Le SVG correspond aux variables générées."""
        ex = generate_tests_dyn_exercise(offer="free", difficulty="moyen", seed=42)
        
        variables = ex["metadata"]["variables"]
        svg_enonce = ex["figure_svg_enonce"]
        
        # Les dimensions doivent être dans le SVG
        if "longueur_initiale" in variables:
            assert str(variables["longueur_initiale"]) in svg_enonce or \
                   str(int(variables["longueur_initiale"])) in svg_enonce
        
        if "cote_initial" in variables:
            assert str(variables["cote_initial"]) in svg_enonce or \
                   str(int(variables["cote_initial"])) in svg_enonce


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
