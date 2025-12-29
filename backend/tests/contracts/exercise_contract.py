"""
Contrat contractuel pour les exercices générés
==============================================

Ce module fournit des validations contractuelles pour garantir la qualité
des exercices générés. Utilisé par les tests CI pour bloquer les régressions.

Validations:
- Énoncé/solution non vides
- Pas de placeholders non résolus
- Sujet ≠ Corrigé (solution suffisamment riche)
- SVG valides si présents
"""

import re
from typing import Dict, Any, List


def strip_html(text: str) -> str:
    """
    Supprime les tags HTML et normalise les espaces.
    
    Args:
        text: Texte HTML
    
    Returns:
        Texte sans HTML, espaces normalisés
    """
    if not text:
        return ""
    
    # Supprimer les tags HTML
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Normaliser les espaces (multiples espaces → un seul)
    text = re.sub(r'\s+', ' ', text)
    
    # Supprimer les espaces en début/fin
    text = text.strip()
    
    return text


def assert_no_unresolved_placeholders(text: str, context: str = ""):
    """
    Vérifie qu'il n'y a pas de placeholders non résolus.
    
    Échoue si contient:
    - {{variable}} ou {variable}
    - [[variable]]
    - PLACEHOLDER, TODO, TBD
    - <VAR> ou autres patterns suspects
    
    Args:
        text: Texte à vérifier
        context: Contexte pour les messages d'erreur (ex: "enonce_html")
    
    Raises:
        AssertionError: Si des placeholders non résolus sont trouvés
    """
    if not text:
        return
    
    # Patterns de placeholders non résolus
    placeholder_patterns = [
        (r'\{\{[^}]+\}\}', '{{variable}}'),
        (r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', '{variable}'),
        (r'\[\[[^\]]+\]\]', '[[variable]]'),
        (r'PLACEHOLDER', 'PLACEHOLDER'),
        (r'TODO', 'TODO'),
        (r'TBD', 'TBD'),
        (r'<VAR>', '<VAR>'),
        (r'\{[^}]*$', '{incomplete'),  # Accolade ouvrante sans fermeture
    ]
    
    errors = []
    for pattern, description in placeholder_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            errors.append(f"{description}: {matches[:3]}")  # Limiter à 3 exemples
    
    if errors:
        context_msg = f" dans {context}" if context else ""
        raise AssertionError(
            f"Placeholders non résolus{context_msg}:\n" + "\n".join(errors)
        )


def assert_exercise_contract(exercise: Dict[str, Any], generator_key: str = ""):
    """
    Valide le contrat complet d'un exercice.
    
    Vérifie:
    1. Énoncé et solution présents et non vides
    2. Pas de placeholders non résolus
    3. Sujet ≠ Corrigé (solution suffisamment riche)
    4. SVG valides si présents
    
    Args:
        exercise: Dict de l'exercice avec enonce_html, solution_html, etc.
        generator_key: Clé du générateur (pour messages d'erreur)
    
    Raises:
        AssertionError: Si le contrat n'est pas respecté
    """
    gen_info = f" (générateur: {generator_key})" if generator_key else ""
    
    # 1. Vérifier présence et non-vacuité de enonce_html
    assert "enonce_html" in exercise, \
        f"enonce_html manquant{gen_info}"
    
    enonce_html = exercise.get("enonce_html", "")
    enonce_txt = strip_html(enonce_html)
    assert enonce_txt, \
        f"enonce_html vide après suppression HTML{gen_info}"
    
    # 2. Vérifier présence et non-vacuité de solution_html
    assert "solution_html" in exercise, \
        f"solution_html manquant{gen_info}"
    
    solution_html = exercise.get("solution_html", "")
    solution_txt = strip_html(solution_html)
    assert solution_txt, \
        f"solution_html vide après suppression HTML{gen_info}"
    
    # 3. Vérifier pas de placeholders non résolus
    assert_no_unresolved_placeholders(enonce_html, "enonce_html")
    assert_no_unresolved_placeholders(solution_html, "solution_html")
    
    # Vérifier aussi les templates si présents
    if "enonce_template" in exercise:
        assert_no_unresolved_placeholders(
            exercise.get("enonce_template", ""),
            "enonce_template"
        )
    if "solution_template" in exercise:
        assert_no_unresolved_placeholders(
            exercise.get("solution_template", ""),
            "solution_template"
        )
    
    # 4. Sujet ≠ Corrigé (heuristique robuste)
    # La solution doit être suffisamment riche pour être différente de l'énoncé
    
    # Cas spéciaux : certains exercices ont des solutions courtes mais valides
    # (ex: "Écris en lettres" → réponse = "cent-trente-huit")
    # (ex: exercices géométriques avec SVG → solution visuelle, texte court)
    # On accepte si la solution est différente de l'énoncé ET non vide
    if solution_txt.strip() and solution_txt.strip() != enonce_txt.strip():
        # Vérifier si l'exercice a des SVG (solution visuelle)
        has_svg = (
            exercise.get("figure_svg_enonce") or
            exercise.get("figure_svg_solution") or
            exercise.get("figure_svg") or
            exercise.get("svg")
        )
        
        # Si la solution est très différente de l'énoncé (pas juste une répétition),
        # on accepte même si elle est courte
        words_enonce = set(enonce_txt.lower().split())
        words_solution = set(solution_txt.lower().split())
        # Si moins de 50% des mots sont communs, c'est probablement une vraie solution
        if len(words_enonce) > 0:
            overlap_ratio = len(words_enonce & words_solution) / len(words_enonce)
            if overlap_ratio < 0.5:
                # Solution suffisamment différente, on accepte
                pass
            else:
                # Solution trop similaire à l'énoncé, vérifier qu'elle est riche
                explanation_markers = [
                    "Donc", "Ainsi", "On calcule", "On applique", "Car", "Puis",
                    "Étape", "Conclusion", "Vérif", "Remarque", "Méthode",
                    "Calcul", "Résultat", "Réponse", "Solution", "Explication"
                ]
                
                has_explanation = any(
                    marker.lower() in solution_txt.lower()
                    for marker in explanation_markers
                )
                
                # Longueur minimale relative (plus tolérante pour les exercices courts)
                # Si SVG présent, réduire encore la longueur minimale (solution visuelle)
                if has_svg:
                    min_length = max(40, int(len(enonce_txt) * 0.4))  # Très tolérant pour SVG
                else:
                    min_length = max(80, int(len(enonce_txt) * 0.6))
                is_long_enough = len(solution_txt) >= min_length
                
                # La solution doit avoir au moins une explication OU être suffisamment longue
                # OU avoir un SVG (solution visuelle)
                if not (has_explanation or is_long_enough or has_svg):
                    raise AssertionError(
                        f"Solution trop pauvre{gen_info}:\n"
                        f"  - Énoncé: {len(enonce_txt)} caractères\n"
                        f"  - Solution: {len(solution_txt)} caractères\n"
                        f"  - Minimum attendu: {min_length} caractères OU présence d'un marqueur d'explication OU SVG\n"
                        f"  - Marqueurs trouvés: {[m for m in explanation_markers if m.lower() in solution_txt.lower()]}\n"
                        f"  - SVG présent: {bool(has_svg)}\n"
                        f"  - Solution text: {solution_txt[:200]}..."
                    )
    else:
        # Solution vide ou identique à l'énoncé → erreur
        raise AssertionError(
            f"Solution vide ou identique à l'énoncé{gen_info}:\n"
            f"  - Énoncé: {enonce_txt[:100]}...\n"
            f"  - Solution: {solution_txt[:100]}..."
        )
    
    # 5. Vérifier SVG si présents
    svg_fields = [
        "figure_svg",
        "figure_svg_enonce",
        "figure_svg_solution",
        "svg"
    ]
    
    for svg_field in svg_fields:
        if svg_field in exercise and exercise[svg_field] is not None:
            svg_content = str(exercise[svg_field])
            if svg_content:  # Si non vide
                assert "<svg" in svg_content.lower(), \
                    f"{svg_field} ne contient pas '<svg'{gen_info}"
                assert "</svg>" in svg_content.lower(), \
                    f"{svg_field} ne contient pas '</svg>'{gen_info}"

