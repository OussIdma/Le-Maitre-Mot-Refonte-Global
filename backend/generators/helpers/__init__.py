"""
P0 Gold - Helpers communs pour les générateurs d'exercices
==========================================================

Ce module fournit des fonctions utilitaires réutilisables pour les générateurs:
- numbers: génération et manipulation de nombres (PGCD, fractions, etc.)
- units: conversion d'unités et formatage localisé
- formatting: formatage sécurisé HTML et LaTeX
- answer_validator: validation et normalisation des réponses élèves
"""

from .number_utils import (
    generate_clean_number,
    pgcd,
    simplify_fraction,
    is_prime,
    prime_factors,
    lcm,
)

from .units import (
    convert_unit,
    format_number,
    format_number_fr,
)

from .formatting import (
    safe_html,
    round_smart,
    format_latex_fraction,
    format_latex_sqrt,
)

from .answer_validator import (
    normalize_answer,
    validate_answer,
    AnswerValidationResult,
)

__all__ = [
    # numbers
    "generate_clean_number",
    "pgcd",
    "simplify_fraction",
    "is_prime",
    "prime_factors",
    "lcm",
    # units
    "convert_unit",
    "format_number",
    "format_number_fr",
    # formatting
    "safe_html",
    "round_smart",
    "format_latex_fraction",
    "format_latex_sqrt",
    # answer_validator
    "normalize_answer",
    "validate_answer",
    "AnswerValidationResult",
]
