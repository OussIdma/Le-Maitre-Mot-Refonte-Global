"""
P0 Gold - Validation et normalisation des réponses élèves
==========================================================

Ce module fournit des fonctions pour normaliser et valider les réponses
des élèves, en tenant compte des variations d'écriture (virgule/point,
fractions, etc.) et des tolérances numériques.
"""

from typing import Union, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
from .number_utils import simplify_fraction


@dataclass
class AnswerValidationResult:
    """Résultat de la validation d'une réponse."""

    is_correct: bool
    """True si la réponse est correcte."""

    normalized_answer: str
    """Réponse normalisée de l'élève."""

    normalized_expected: str
    """Réponse attendue normalisée."""

    message: Optional[str] = None
    """Message explicatif (erreur, feedback, etc.)."""

    close_but_wrong: bool = False
    """True si la réponse est proche mais incorrecte (erreur d'arrondi, etc.)."""


def normalize_answer(answer: str) -> str:
    """
    Normalise une réponse pour comparaison.

    Transformations appliquées:
    - Supprime les espaces superflus
    - Remplace la virgule par un point (décimales)
    - Supprime les espaces dans les nombres (1 000 -> 1000)
    - Normalise les fractions (1/2, 1 / 2 -> 1/2)
    - Convertit en minuscules

    Args:
        answer: Réponse brute de l'élève

    Returns:
        Réponse normalisée

    Examples:
        >>> normalize_answer("  3,14  ")
        '3.14'
        >>> normalize_answer("1 000")
        '1000'
        >>> normalize_answer("1 / 2")
        '1/2'
        >>> normalize_answer("VRAI")
        'vrai'
    """
    if not isinstance(answer, str):
        answer = str(answer)

    # Trim et lowercase
    result = answer.strip().lower()

    # Supprimer les espaces autour des opérateurs de fraction
    result = re.sub(r"\s*/\s*", "/", result)

    # Remplacer virgule par point (décimales françaises)
    result = result.replace(",", ".")

    # Supprimer les espaces dans les nombres (1 000 -> 1000)
    # Mais garder les espaces entre mots
    result = re.sub(r"(\d)\s+(\d)", r"\1\2", result)

    return result


def _parse_fraction(text: str) -> Optional[Tuple[int, int]]:
    """
    Parse une fraction textuelle et retourne (numérateur, dénominateur).

    Returns:
        Tuple (num, den) ou None si pas une fraction valide.
    """
    match = re.match(r"^(-?\d+)/(-?\d+)$", text.strip())
    if match:
        num = int(match.group(1))
        den = int(match.group(2))
        if den != 0:
            return (num, den)
    return None


def _parse_decimal(text: str) -> Optional[Decimal]:
    """
    Parse un nombre décimal textuel.

    Returns:
        Decimal ou None si pas un nombre valide.
    """
    try:
        return Decimal(text.strip())
    except InvalidOperation:
        return None


def _fractions_equivalent(
    frac1: Tuple[int, int],
    frac2: Tuple[int, int],
) -> bool:
    """
    Vérifie si deux fractions sont équivalentes.
    """
    s1 = simplify_fraction(frac1[0], frac1[1])
    s2 = simplify_fraction(frac2[0], frac2[1])
    return s1 == s2


def validate_answer(
    student_answer: str,
    expected_answer: Union[str, int, float, Tuple[int, int]],
    tolerance: float = 0.0,
    accept_simplified_only: bool = False,
    accept_decimal_for_fraction: bool = True,
) -> AnswerValidationResult:
    """
    Valide une réponse d'élève contre une réponse attendue.

    Supporte:
    - Nombres décimaux (avec tolérance)
    - Fractions (équivalence ou simplification requise)
    - Texte exact (après normalisation)

    Args:
        student_answer: Réponse de l'élève
        expected_answer: Réponse attendue (str, nombre, ou tuple (num, den) pour fraction)
        tolerance: Tolérance relative pour les comparaisons numériques (0.01 = 1%)
        accept_simplified_only: Si True, une fraction doit être irréductible
        accept_decimal_for_fraction: Si True, accepte 0.5 pour 1/2

    Returns:
        AnswerValidationResult avec le résultat de la validation

    Examples:
        >>> validate_answer("3,14", 3.14).is_correct
        True
        >>> validate_answer("2/4", (1, 2)).is_correct
        True
        >>> validate_answer("2/4", (1, 2), accept_simplified_only=True).is_correct
        False
        >>> validate_answer("0.5", (1, 2), accept_decimal_for_fraction=True).is_correct
        True
    """
    normalized_student = normalize_answer(student_answer)

    # Cas 1: expected est une fraction (tuple)
    if isinstance(expected_answer, tuple) and len(expected_answer) == 2:
        expected_num, expected_den = expected_answer
        simplified_expected = simplify_fraction(expected_num, expected_den)
        normalized_expected = f"{simplified_expected[0]}/{simplified_expected[1]}"

        # Essayer de parser la réponse comme fraction
        student_frac = _parse_fraction(normalized_student)
        if student_frac:
            if accept_simplified_only:
                # La fraction doit être irréductible
                simplified_student = simplify_fraction(student_frac[0], student_frac[1])
                if student_frac != simplified_student:
                    return AnswerValidationResult(
                        is_correct=False,
                        normalized_answer=normalized_student,
                        normalized_expected=normalized_expected,
                        message="La fraction doit être simplifiée",
                        close_but_wrong=True,
                    )

            if _fractions_equivalent(student_frac, (expected_num, expected_den)):
                return AnswerValidationResult(
                    is_correct=True,
                    normalized_answer=normalized_student,
                    normalized_expected=normalized_expected,
                )

        # Essayer comme décimal si autorisé
        if accept_decimal_for_fraction:
            student_dec = _parse_decimal(normalized_student)
            if student_dec is not None:
                expected_dec = Decimal(expected_num) / Decimal(expected_den)
                if tolerance > 0:
                    diff = abs(student_dec - expected_dec)
                    if diff <= Decimal(str(tolerance)) * abs(expected_dec):
                        return AnswerValidationResult(
                            is_correct=True,
                            normalized_answer=normalized_student,
                            normalized_expected=normalized_expected,
                        )
                elif student_dec == expected_dec:
                    return AnswerValidationResult(
                        is_correct=True,
                        normalized_answer=normalized_student,
                        normalized_expected=normalized_expected,
                    )

        return AnswerValidationResult(
            is_correct=False,
            normalized_answer=normalized_student,
            normalized_expected=normalized_expected,
        )

    # Cas 2: expected est un nombre
    if isinstance(expected_answer, (int, float, Decimal)):
        expected_dec = Decimal(str(expected_answer))
        normalized_expected = str(expected_answer)

        student_dec = _parse_decimal(normalized_student)
        if student_dec is not None:
            if tolerance > 0:
                diff = abs(student_dec - expected_dec)
                max_diff = Decimal(str(tolerance)) * abs(expected_dec) if expected_dec != 0 else Decimal(str(tolerance))
                if diff <= max_diff:
                    return AnswerValidationResult(
                        is_correct=True,
                        normalized_answer=normalized_student,
                        normalized_expected=normalized_expected,
                    )
                # Vérifier si proche mais hors tolérance
                if diff <= max_diff * 2:
                    return AnswerValidationResult(
                        is_correct=False,
                        normalized_answer=normalized_student,
                        normalized_expected=normalized_expected,
                        message="Réponse proche mais hors tolérance",
                        close_but_wrong=True,
                    )
            elif student_dec == expected_dec:
                return AnswerValidationResult(
                    is_correct=True,
                    normalized_answer=normalized_student,
                    normalized_expected=normalized_expected,
                )

        return AnswerValidationResult(
            is_correct=False,
            normalized_answer=normalized_student,
            normalized_expected=normalized_expected,
        )

    # Cas 3: expected est une chaîne (comparaison textuelle)
    normalized_expected = normalize_answer(str(expected_answer))

    if normalized_student == normalized_expected:
        return AnswerValidationResult(
            is_correct=True,
            normalized_answer=normalized_student,
            normalized_expected=normalized_expected,
        )

    return AnswerValidationResult(
        is_correct=False,
        normalized_answer=normalized_student,
        normalized_expected=normalized_expected,
    )


# =============================================================================
# TESTS AUTO-EXÉCUTABLES
# =============================================================================

if __name__ == "__main__":
    # Tests normalize_answer
    assert normalize_answer("  3,14  ") == "3.14"
    assert normalize_answer("1 000") == "1000"
    assert normalize_answer("1 / 2") == "1/2"
    assert normalize_answer("VRAI") == "vrai"

    # Tests validate_answer - décimaux
    assert validate_answer("3,14", 3.14).is_correct is True
    assert validate_answer("3.14", 3.14).is_correct is True
    assert validate_answer("3.15", 3.14).is_correct is False
    assert validate_answer("3.15", 3.14, tolerance=0.01).is_correct is True

    # Tests validate_answer - fractions
    assert validate_answer("1/2", (1, 2)).is_correct is True
    assert validate_answer("2/4", (1, 2)).is_correct is True  # Équivalent
    assert validate_answer("2/4", (1, 2), accept_simplified_only=True).is_correct is False

    # Tests validate_answer - décimal pour fraction
    assert validate_answer("0.5", (1, 2)).is_correct is True
    assert validate_answer("0,5", (1, 2)).is_correct is True

    # Tests validate_answer - texte
    assert validate_answer("VRAI", "vrai").is_correct is True
    assert validate_answer("  oui  ", "oui").is_correct is True

    print("OK - Tous les tests passent")
