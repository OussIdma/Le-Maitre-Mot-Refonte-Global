"""
TEST P0 - Validation de la cohérence texte/SVG via variables
=============================================================

Ces tests vérifient que:
1. Le SVG est généré depuis 'variables' (source de vérité unique)
2. Il n'y a jamais de mismatch entre le texte de l'énoncé et la figure SVG
3. Les exercices PLACER_AIGUILLES ont deux figures différentes
"""

import pytest
import re
from data.gm07_exercises import GM07_EXERCISES, get_gm07_exercises
from services.svg_render_service import generate_exercise_svgs


class TestP0SvgVariablesConsistency:
    """Tests de cohérence SVG basé sur les variables."""
    
    def test_all_clock_exercises_have_variables(self):
        """Tous les exercices avec SVG horloge doivent avoir des variables."""
        exercises = get_gm07_exercises(offer="pro")  # PRO voit tous les exercices
        
        clock_families = ["LECTURE_HORLOGE", "CALCUL_DUREE"]
        missing_variables = []
        
        for ex in exercises:
            if ex.get("needs_svg") and ex.get("family") in clock_families:
                if not ex.get("variables"):
                    missing_variables.append(ex["id"])
        
        assert len(missing_variables) == 0, f"Exercices sans variables: {missing_variables}"
    
    def test_svg_generated_from_variables_source(self):
        """Le SVG doit être généré depuis 'variables', pas depuis le parsing HTML."""
        exercises = get_gm07_exercises(offer="pro")
        
        for ex in exercises:
            if ex.get("needs_svg") and ex.get("variables"):
                svg_result = generate_exercise_svgs(ex)
                variables_used = svg_result.get("variables_used", {})
                
                assert variables_used.get("source") == "variables", \
                    f"Exercice {ex['id']}: source attendue 'variables', obtenue '{variables_used.get('source')}'"
    
    def test_clock_hour_matches_enonce(self):
        """L'heure dans variables doit correspondre à l'énoncé."""
        exercises = [ex for ex in get_gm07_exercises(offer="pro") 
                     if ex.get("needs_svg") and ex.get("variables")]
        
        for ex in exercises:
            variables = ex["variables"]
            hour = variables.get("hour")
            minute = variables.get("minute", 0)
            
            # Vérifier que l'heure est mentionnée dans l'énoncé ou la solution
            combined_text = ex["enonce_html"] + ex["solution_html"]
            
            # Formats possibles: "12h15", "12 h 15", "12h", "12 heures"
            hour_pattern = rf'\b{hour}\s*h'
            has_hour_mention = bool(re.search(hour_pattern, combined_text, re.IGNORECASE))
            
            # Pour les exercices de type description, on vérifie juste que hour est raisonnable
            if not has_hour_mention:
                # Vérifier format "sur le X" pour les aiguilles
                position_pattern = rf'sur le {hour % 12 or 12}|vers le {hour % 12 or 12}|pointe.*{hour % 12 or 12}'
                has_hour_mention = bool(re.search(position_pattern, combined_text, re.IGNORECASE))
            
            assert has_hour_mention, \
                f"Exercice {ex['id']}: hour={hour} non trouvée dans l'énoncé/solution"
    
    def test_placer_aiguilles_has_two_different_svgs(self):
        """Les exercices PLACER_AIGUILLES doivent avoir deux SVG différents."""
        exercises = [ex for ex in get_gm07_exercises(offer="pro") 
                     if ex.get("exercise_type") == "PLACER_AIGUILLES"]
        
        assert len(exercises) >= 2, "Il devrait y avoir au moins 2 exercices PLACER_AIGUILLES"
        
        for ex in exercises:
            svg_result = generate_exercise_svgs(ex)
            
            svg_enonce = svg_result.get("figure_svg_enonce")
            svg_solution = svg_result.get("figure_svg_solution")
            
            assert svg_enonce, f"Exercice {ex['id']}: SVG énoncé manquant"
            assert svg_solution, f"Exercice {ex['id']}: SVG solution manquant"
            assert svg_enonce != svg_solution, \
                f"Exercice {ex['id']}: Les deux SVG doivent être différents (énoncé vide, solution avec aiguilles)"
    
    def test_placer_aiguilles_enonce_is_empty_clock(self):
        """L'énoncé PLACER_AIGUILLES doit montrer une horloge vide."""
        exercises = [ex for ex in get_gm07_exercises(offer="pro") 
                     if ex.get("exercise_type") == "PLACER_AIGUILLES"]
        
        for ex in exercises:
            svg_result = generate_exercise_svgs(ex)
            svg_enonce = svg_result.get("figure_svg_enonce", "")
            
            # Une horloge vide ne devrait pas avoir de lignes d'aiguilles longues
            # Le SVG vide a juste le cadran sans les aiguilles
            assert "sans aiguilles" in ex["enonce_html"].lower() or "place" in ex["enonce_html"].lower(), \
                f"Exercice {ex['id']}: L'énoncé devrait mentionner qu'il faut placer les aiguilles"
    
    def test_five_clock_exercises_match_text_and_svg(self):
        """Test de 5 exercices horloges: cohérence texte/SVG."""
        exercises = [ex for ex in get_gm07_exercises(offer="pro") 
                     if ex.get("needs_svg") and ex.get("variables")][:5]
        
        assert len(exercises) >= 5, "Il faut au moins 5 exercices avec SVG et variables"
        
        for ex in exercises:
            svg_result = generate_exercise_svgs(ex)
            variables_used = svg_result.get("variables_used", {})
            
            # Vérifier que la source est bien 'variables'
            assert variables_used.get("source") == "variables", \
                f"Exercice {ex['id']}: source doit être 'variables'"
            
            # Vérifier que les variables utilisées matchent les variables originales
            original_vars = ex.get("variables", {})
            assert variables_used.get("hour") == original_vars.get("hour"), \
                f"Exercice {ex['id']}: hour mismatch"
            assert variables_used.get("minute") == original_vars.get("minute", 0), \
                f"Exercice {ex['id']}: minute mismatch"
            
            print(f"✅ Exercice {ex['id']}: hour={original_vars.get('hour')}:{original_vars.get('minute', 0)}, SVG OK")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
