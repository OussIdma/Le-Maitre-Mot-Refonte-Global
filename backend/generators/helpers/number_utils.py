"""
P0 Gold - Helpers pour la manipulation de nombres
==================================================

Fonctions utilitaires pour générer et manipuler des nombres dans les exercices.
"""

from typing import List, Tuple, Optional
from math import gcd as math_gcd
import random


def pgcd(a: int, b: int) -> int:
    """
    Calcule le PGCD (Plus Grand Commun Diviseur) de deux entiers.

    Args:
        a: Premier entier
        b: Deuxième entier

    Returns:
        PGCD de a et b

    Examples:
        >>> pgcd(12, 18)
        6
        >>> pgcd(7, 3)
        1
    """
    return math_gcd(abs(a), abs(b))


def lcm(a: int, b: int) -> int:
    """
    Calcule le PPCM (Plus Petit Commun Multiple) de deux entiers.

    Args:
        a: Premier entier
        b: Deuxième entier

    Returns:
        PPCM de a et b

    Examples:
        >>> lcm(4, 6)
        12
        >>> lcm(3, 5)
        15
    """
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // pgcd(a, b)


def simplify_fraction(numerator: int, denominator: int) -> Tuple[int, int]:
    """
    Simplifie une fraction en divisant par le PGCD.

    Args:
        numerator: Numérateur
        denominator: Dénominateur

    Returns:
        Tuple (numérateur simplifié, dénominateur simplifié)

    Raises:
        ValueError: Si le dénominateur est 0

    Examples:
        >>> simplify_fraction(4, 8)
        (1, 2)
        >>> simplify_fraction(12, 18)
        (2, 3)
        >>> simplify_fraction(-6, 9)
        (-2, 3)
    """
    if denominator == 0:
        raise ValueError("Le dénominateur ne peut pas être 0")

    d = pgcd(numerator, denominator)
    num = numerator // d
    den = denominator // d

    # Convention: le signe est toujours au numérateur
    if den < 0:
        num = -num
        den = -den

    return (num, den)


def is_prime(n: int) -> bool:
    """
    Vérifie si un nombre est premier.

    Args:
        n: Nombre à tester

    Returns:
        True si n est premier, False sinon

    Examples:
        >>> is_prime(2)
        True
        >>> is_prime(4)
        False
        >>> is_prime(17)
        True
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def prime_factors(n: int) -> List[int]:
    """
    Retourne la liste des facteurs premiers d'un nombre (avec répétition).

    Args:
        n: Nombre à factoriser (doit être >= 2)

    Returns:
        Liste des facteurs premiers ordonnés

    Examples:
        >>> prime_factors(12)
        [2, 2, 3]
        >>> prime_factors(17)
        [17]
        >>> prime_factors(100)
        [2, 2, 5, 5]
    """
    if n < 2:
        return []

    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def generate_clean_number(
    min_val: int = 1,
    max_val: int = 100,
    avoid_multiples: Optional[List[int]] = None,
    must_be_prime: bool = False,
    must_be_even: bool = False,
    must_be_odd: bool = False,
    rng: Optional[random.Random] = None,
    max_attempts: int = 1000,
) -> int:
    """
    Génère un nombre "propre" selon les contraintes spécifiées.

    Args:
        min_val: Valeur minimale (incluse)
        max_val: Valeur maximale (incluse)
        avoid_multiples: Liste de nombres dont les multiples sont à éviter
        must_be_prime: Le nombre doit être premier
        must_be_even: Le nombre doit être pair
        must_be_odd: Le nombre doit être impair
        rng: Générateur aléatoire (pour reproductibilité)
        max_attempts: Nombre maximum de tentatives

    Returns:
        Un nombre satisfaisant toutes les contraintes

    Raises:
        ValueError: Si aucun nombre valide n'est trouvé après max_attempts tentatives

    Examples:
        >>> generate_clean_number(1, 10, must_be_prime=True, rng=random.Random(42))
        5  # ou un autre nombre premier entre 1 et 10
    """
    if rng is None:
        rng = random.Random()

    avoid_multiples = avoid_multiples or []

    for _ in range(max_attempts):
        n = rng.randint(min_val, max_val)

        # Vérifier les contraintes
        if must_be_prime and not is_prime(n):
            continue
        if must_be_even and n % 2 != 0:
            continue
        if must_be_odd and n % 2 == 0:
            continue

        # Éviter les multiples
        skip = False
        for m in avoid_multiples:
            if m != 0 and n % m == 0:
                skip = True
                break
        if skip:
            continue

        return n

    raise ValueError(
        f"Impossible de générer un nombre satisfaisant les contraintes après {max_attempts} tentatives. "
        f"Contraintes: min={min_val}, max={max_val}, prime={must_be_prime}, even={must_be_even}, odd={must_be_odd}"
    )


# =============================================================================
# TESTS AUTO-EXÉCUTABLES
# =============================================================================

if __name__ == "__main__":
    # Tests rapides
    assert pgcd(12, 18) == 6, "PGCD(12, 18) devrait être 6"
    assert pgcd(7, 3) == 1, "PGCD(7, 3) devrait être 1"
    assert lcm(4, 6) == 12, "PPCM(4, 6) devrait être 12"
    assert simplify_fraction(4, 8) == (1, 2), "4/8 simplifié devrait être 1/2"
    assert simplify_fraction(-6, 9) == (-2, 3), "-6/9 simplifié devrait être -2/3"
    assert is_prime(17) is True, "17 est premier"
    assert is_prime(4) is False, "4 n'est pas premier"
    assert prime_factors(12) == [2, 2, 3], "Facteurs de 12: [2, 2, 3]"

    # Test generate_clean_number avec seed fixe
    rng = random.Random(42)
    n = generate_clean_number(10, 50, must_be_prime=True, rng=rng)
    assert is_prime(n), f"{n} devrait être premier"

    print("OK - Tous les tests passent")
