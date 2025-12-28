"""
P0 Gold - Helpers pour le formatage HTML et LaTeX
==================================================

Fonctions utilitaires pour formater du contenu de manière sécurisée.
"""

from typing import Union
from html import escape
from decimal import Decimal, ROUND_HALF_UP
import re


def safe_html(text: str) -> str:
    """
    Échappe les caractères HTML dangereux pour éviter les injections XSS.

    Args:
        text: Texte à sécuriser

    Returns:
        Texte avec caractères HTML échappés

    Examples:
        >>> safe_html("<script>alert('xss')</script>")
        "&lt;script&gt;alert('xss')&lt;/script&gt;"
        >>> safe_html("5 > 3")
        "5 &gt; 3"
    """
    return escape(str(text), quote=True)


def round_smart(
    value: Union[int, float, Decimal],
    decimals: int = 2,
    strip_trailing_zeros: bool = True,
) -> str:
    """
    Arrondit un nombre de manière intelligente.

    Args:
        value: Nombre à arrondir
        decimals: Nombre maximum de décimales
        strip_trailing_zeros: Supprimer les zéros inutiles à droite

    Returns:
        Nombre arrondi en chaîne

    Examples:
        >>> round_smart(3.14159, 2)
        '3.14'
        >>> round_smart(5.00, 2)
        '5'
        >>> round_smart(5.10, 2)
        '5.1'
        >>> round_smart(5.10, 2, strip_trailing_zeros=False)
        '5.10'
    """
    dec = Decimal(str(value))
    rounded = dec.quantize(
        Decimal(10) ** -decimals,
        rounding=ROUND_HALF_UP
    )

    result = f"{rounded:.{decimals}f}"

    if strip_trailing_zeros:
        # Supprimer les zéros après la virgule, et la virgule si inutile
        result = result.rstrip("0").rstrip(".")

    return result


def format_latex_fraction(
    numerator: Union[int, float, str],
    denominator: Union[int, float, str],
    display_style: bool = False,
) -> str:
    """
    Formate une fraction en LaTeX.

    Args:
        numerator: Numérateur
        denominator: Dénominateur
        display_style: Utiliser \\dfrac au lieu de \\frac

    Returns:
        Code LaTeX de la fraction

    Examples:
        >>> format_latex_fraction(3, 4)
        '\\\\frac{3}{4}'
        >>> format_latex_fraction(3, 4, display_style=True)
        '\\\\dfrac{3}{4}'
    """
    cmd = "\\dfrac" if display_style else "\\frac"
    return f"{cmd}{{{numerator}}}{{{denominator}}}"


def format_latex_sqrt(
    value: Union[int, float, str],
    index: int = 2,
) -> str:
    """
    Formate une racine en LaTeX.

    Args:
        value: Valeur sous la racine
        index: Indice de la racine (2 = racine carrée, 3 = racine cubique)

    Returns:
        Code LaTeX de la racine

    Examples:
        >>> format_latex_sqrt(2)
        '\\\\sqrt{2}'
        >>> format_latex_sqrt(8, 3)
        '\\\\sqrt[3]{8}'
    """
    if index == 2:
        return f"\\sqrt{{{value}}}"
    return f"\\sqrt[{index}]{{{value}}}"


def format_latex_power(base: Union[int, float, str], exponent: Union[int, float, str]) -> str:
    """
    Formate une puissance en LaTeX.

    Args:
        base: Base
        exponent: Exposant

    Returns:
        Code LaTeX de la puissance

    Examples:
        >>> format_latex_power(2, 3)
        '2^{3}'
        >>> format_latex_power("x", "n")
        'x^{n}'
    """
    return f"{base}^{{{exponent}}}"


def format_latex_subscript(base: str, subscript: Union[int, str]) -> str:
    """
    Formate un indice en LaTeX.

    Args:
        base: Variable de base
        subscript: Indice

    Returns:
        Code LaTeX avec indice

    Examples:
        >>> format_latex_subscript("a", 1)
        'a_{1}'
        >>> format_latex_subscript("x", "n")
        'x_{n}'
    """
    return f"{base}_{{{subscript}}}"


def strip_html_tags(text: str) -> str:
    """
    Supprime les balises HTML d'un texte.

    Args:
        text: Texte contenant potentiellement du HTML

    Returns:
        Texte sans balises HTML

    Examples:
        >>> strip_html_tags("<p>Hello <b>world</b></p>")
        'Hello world'
    """
    return re.sub(r"<[^>]+>", "", text)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Tronque un texte à une longueur maximale.

    Args:
        text: Texte à tronquer
        max_length: Longueur maximale (incluant le suffix)
        suffix: Suffix à ajouter si tronqué

    Returns:
        Texte tronqué ou original si déjà court

    Examples:
        >>> truncate_text("Hello world", 8)
        'Hello...'
        >>> truncate_text("Hi", 10)
        'Hi'
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


# =============================================================================
# TESTS AUTO-EXÉCUTABLES
# =============================================================================

if __name__ == "__main__":
    # Tests safe_html
    assert "&lt;script&gt;" in safe_html("<script>")
    assert "&gt;" in safe_html("5 > 3")

    # Tests round_smart
    assert round_smart(3.14159, 2) == "3.14"
    assert round_smart(5.00, 2) == "5"
    assert round_smart(5.10, 2) == "5.1"
    assert round_smart(5.10, 2, strip_trailing_zeros=False) == "5.10"

    # Tests format_latex_fraction
    assert format_latex_fraction(3, 4) == "\\frac{3}{4}"
    assert format_latex_fraction(3, 4, display_style=True) == "\\dfrac{3}{4}"

    # Tests format_latex_sqrt
    assert format_latex_sqrt(2) == "\\sqrt{2}"
    assert format_latex_sqrt(8, 3) == "\\sqrt[3]{8}"

    # Tests format_latex_power
    assert format_latex_power(2, 3) == "2^{3}"

    # Tests strip_html_tags
    assert strip_html_tags("<p>Hello <b>world</b></p>") == "Hello world"

    # Tests truncate_text
    assert truncate_text("Hello world", 8) == "Hello..."
    assert truncate_text("Hi", 10) == "Hi"

    print("OK - Tous les tests passent")
