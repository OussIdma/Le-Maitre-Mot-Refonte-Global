"""
P0 Gold - Helpers pour les unités et le formatage de nombres
=============================================================

Fonctions utilitaires pour convertir des unités et formater des nombres
selon les conventions françaises ou internationales.
"""

from typing import Union, Optional
from decimal import Decimal, ROUND_HALF_UP


# =============================================================================
# TABLES DE CONVERSION
# =============================================================================

# Facteurs de conversion vers l'unité de base (mètre, gramme, litre, etc.)
LENGTH_FACTORS = {
    "km": 1000,
    "hm": 100,
    "dam": 10,
    "m": 1,
    "dm": 0.1,
    "cm": 0.01,
    "mm": 0.001,
}

MASS_FACTORS = {
    "t": 1_000_000,  # tonne -> grammes
    "q": 100_000,    # quintal -> grammes
    "kg": 1000,
    "hg": 100,
    "dag": 10,
    "g": 1,
    "dg": 0.1,
    "cg": 0.01,
    "mg": 0.001,
}

VOLUME_FACTORS = {
    "kL": 1000,
    "hL": 100,
    "daL": 10,
    "L": 1,
    "dL": 0.1,
    "cL": 0.01,
    "mL": 0.001,
}

AREA_FACTORS = {
    "km2": 1_000_000,
    "ha": 10_000,
    "a": 100,
    "m2": 1,
    "dm2": 0.01,
    "cm2": 0.0001,
    "mm2": 0.000001,
}

TIME_FACTORS = {
    "j": 86400,    # jour -> secondes
    "h": 3600,
    "min": 60,
    "s": 1,
    "ms": 0.001,
}

# Mapping des catégories
UNIT_CATEGORIES = {
    **{u: ("length", LENGTH_FACTORS) for u in LENGTH_FACTORS},
    **{u: ("mass", MASS_FACTORS) for u in MASS_FACTORS},
    **{u: ("volume", VOLUME_FACTORS) for u in VOLUME_FACTORS},
    **{u: ("area", AREA_FACTORS) for u in AREA_FACTORS},
    **{u: ("time", TIME_FACTORS) for u in TIME_FACTORS},
}


def convert_unit(
    value: Union[int, float, Decimal],
    from_unit: str,
    to_unit: str,
    precision: int = 6,
) -> float:
    """
    Convertit une valeur d'une unité à une autre.

    Args:
        value: Valeur à convertir
        from_unit: Unité source (ex: "km", "g", "L")
        to_unit: Unité cible
        precision: Nombre de décimales pour l'arrondi

    Returns:
        Valeur convertie

    Raises:
        ValueError: Si les unités ne sont pas compatibles ou inconnues

    Examples:
        >>> convert_unit(1, "km", "m")
        1000.0
        >>> convert_unit(500, "g", "kg")
        0.5
        >>> convert_unit(2.5, "h", "min")
        150.0
    """
    if from_unit not in UNIT_CATEGORIES:
        raise ValueError(f"Unité source inconnue: {from_unit}")
    if to_unit not in UNIT_CATEGORIES:
        raise ValueError(f"Unité cible inconnue: {to_unit}")

    from_category, from_factors = UNIT_CATEGORIES[from_unit]
    to_category, to_factors = UNIT_CATEGORIES[to_unit]

    if from_category != to_category:
        raise ValueError(
            f"Unités incompatibles: {from_unit} ({from_category}) et {to_unit} ({to_category})"
        )

    # Convertir vers l'unité de base, puis vers l'unité cible
    base_value = float(value) * from_factors[from_unit]
    result = base_value / to_factors[to_unit]

    return round(result, precision)


def format_number(
    value: Union[int, float, Decimal],
    decimals: Optional[int] = None,
    locale: str = "fr",
    thousands_sep: bool = True,
) -> str:
    """
    Formate un nombre selon les conventions locales.

    Args:
        value: Nombre à formater
        decimals: Nombre de décimales (None = automatique)
        locale: "fr" pour français (virgule), "us" pour anglais (point)
        thousands_sep: Ajouter un séparateur de milliers

    Returns:
        Nombre formaté en chaîne

    Examples:
        >>> format_number(1234.567, decimals=2, locale="fr")
        '1 234,57'
        >>> format_number(1234.567, decimals=2, locale="us")
        '1,234.57'
        >>> format_number(1234, locale="fr")
        '1 234'
    """
    if decimals is not None:
        # Arrondir avec Decimal pour précision
        dec = Decimal(str(value))
        rounded = float(dec.quantize(
            Decimal(10) ** -decimals,
            rounding=ROUND_HALF_UP
        ))
    else:
        rounded = float(value)

    # Séparer partie entière et décimale
    if decimals is not None:
        formatted = f"{rounded:.{decimals}f}"
    else:
        # Automatique: retirer les zéros inutiles
        if rounded == int(rounded):
            formatted = str(int(rounded))
        else:
            formatted = str(rounded)

    # Séparateurs selon locale
    if locale == "fr":
        dec_sep = ","
        thou_sep = " "
    else:
        dec_sep = "."
        thou_sep = ","

    # Appliquer les séparateurs
    parts = formatted.split(".")
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else ""

    # Séparateur de milliers
    if thousands_sep and len(integer_part) > 3:
        # Gérer le signe négatif
        sign = ""
        if integer_part.startswith("-"):
            sign = "-"
            integer_part = integer_part[1:]

        # Ajouter les séparateurs
        groups = []
        while integer_part:
            groups.append(integer_part[-3:])
            integer_part = integer_part[:-3]
        integer_part = sign + thou_sep.join(reversed(groups))

    if decimal_part:
        return f"{integer_part}{dec_sep}{decimal_part}"
    return integer_part


def format_number_fr(
    value: Union[int, float, Decimal],
    decimals: Optional[int] = None,
) -> str:
    """
    Raccourci pour formater un nombre en français.

    Args:
        value: Nombre à formater
        decimals: Nombre de décimales

    Returns:
        Nombre formaté avec virgule et espaces

    Examples:
        >>> format_number_fr(1234.5)
        '1 234,5'
    """
    return format_number(value, decimals=decimals, locale="fr")


# =============================================================================
# TESTS AUTO-EXÉCUTABLES
# =============================================================================

if __name__ == "__main__":
    # Tests convert_unit
    assert convert_unit(1, "km", "m") == 1000.0, "1 km = 1000 m"
    assert convert_unit(500, "g", "kg") == 0.5, "500 g = 0.5 kg"
    assert convert_unit(2.5, "h", "min") == 150.0, "2.5 h = 150 min"
    assert convert_unit(1, "ha", "m2") == 10000.0, "1 ha = 10000 m2"

    # Tests format_number
    assert format_number(1234.567, decimals=2, locale="fr") == "1 234,57"
    assert format_number(1234.567, decimals=2, locale="us") == "1,234.57"
    assert format_number(1234, locale="fr") == "1 234"
    assert format_number(1234.5, decimals=1, locale="fr") == "1 234,5"

    # Tests format_number_fr
    assert format_number_fr(1234.5) == "1 234,5"

    print("OK - Tous les tests passent")
