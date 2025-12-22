"""
Détection automatique des chapitres template-based pour template_variants.
Phase Finale : Industrialisation (suppression allowlist manuelle).

Un chapitre est template-based (compatible template_variants) si :
1. Handler dédié : intercepté par tests_dyn_handler (ex: 6E_TESTS_DYN)
2. Exercice dynamique : au moins un exercice avec is_dynamic=True + generator_key + enonce_template_html

Exclusions explicites :
- 6E_GM07, 6E_GM08 (statiques, pas de templates)
"""

from typing import Dict, Any, Optional

# Import lazy pour éviter import circulaire et coût à chaque appel
_is_tests_dyn_request_func = None


def _get_is_tests_dyn_request():
    """Lazy import de is_tests_dyn_request pour éviter import circulaire et coût per-call."""
    global _is_tests_dyn_request_func
    if _is_tests_dyn_request_func is None:
        from backend.services.tests_dyn_handler import is_tests_dyn_request
        _is_tests_dyn_request_func = is_tests_dyn_request
    return _is_tests_dyn_request_func


# Chapitres exclus explicitement (statiques, pas de templates)
EXCLUDED_CHAPTERS = {"6E_GM07", "6E_GM08"}


def is_chapter_template_based(
    chapter_code: str,
    exercise_template: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Détecte automatiquement si un chapitre est template-based (compatible template_variants).
    
    Critères (AU MOINS UN doit être vrai) :
    1. Handler dédié : chapitre intercepté par tests_dyn_handler
    2. Exercice dynamique : exercise_template avec is_dynamic=True + generator_key + enonce_template_html
    
    Args:
        chapter_code: Code du chapitre (ex: "6e_TESTS_DYN", "6E_TESTS_DYN")
        exercise_template: Template d'exercice (optionnel, pour détection basée sur données)
    
    Returns:
        True si template-based (compatible template_variants)
        False si spec-based ou statique (incompatible)
    
    Examples:
        >>> is_chapter_template_based("6e_TESTS_DYN")
        True
        >>> is_chapter_template_based("6E_GM07")
        False
        >>> is_chapter_template_based("6e_G07", {"is_dynamic": True, "generator_key": "THALES_V1", "enonce_template_html": "<p>{{var}}</p>"})
        True
    """
    if not chapter_code:
        return False
    
    # Normalisation
    chapter_upper = chapter_code.strip().upper().replace("-", "_")
    
    # Exclusion explicite (GM07/GM08) - AVANT tout import
    if chapter_upper in EXCLUDED_CHAPTERS:
        return False
    
    # Critère 1 : Handler dédié (tests_dyn_handler) - lazy import
    is_tests_dyn_request = _get_is_tests_dyn_request()
    if is_tests_dyn_request(chapter_code):
        return True
    
    # Critère 2 : Exercice dynamique avec templates (si exercise_template fourni)
    if exercise_template:
        if (
            exercise_template.get("is_dynamic") is True
            and exercise_template.get("generator_key")
            and exercise_template.get("enonce_template_html")
        ):
            return True
    
    # Par défaut : spec-based (incompatible)
    return False

