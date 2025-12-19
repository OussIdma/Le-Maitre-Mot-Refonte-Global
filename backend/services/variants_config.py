"""
Configuration explicite des chapitres autorisés pour template_variants.
Feature flag : allowlist stricte (pas de détection automatique).

Phase A : Allowlist explicite
- Liste blanche de chapitres autorisés pour les template_variants
- Contrôle total sur l'activation (pas de détection implicite)
- Rollback facile (retirer un chapitre de l'allowlist)
"""

from typing import Set


# Allowlist explicite (feature flag)
# Format : codes chapitres en UPPERCASE (ex: "6E_TESTS_DYN")
VARIANTS_ALLOWED_CHAPTERS: Set[str] = {
    "6E_TESTS_DYN",  # Pilote (déjà fonctionnel)
    # Ajouter ici les futurs chapitres validés manuellement
    # Exemple : "6E_G07" (si validé après tests)
}


def is_variants_allowed(chapter_code: str) -> bool:
    """
    Vérifie si un chapitre est autorisé pour les template_variants.
    
    Args:
        chapter_code: Code du chapitre (ex: "6e_TESTS_DYN", "6E_TESTS_DYN")
    
    Returns:
        True si le chapitre est dans l'allowlist, False sinon
    
    Examples:
        >>> is_variants_allowed("6e_TESTS_DYN")
        True
        >>> is_variants_allowed("6E_TESTS_DYN")
        True
        >>> is_variants_allowed("6e_G07")
        False
    """
    if not chapter_code:
        return False
    
    # Normalisation : uppercase + trim
    normalized = chapter_code.strip().upper()
    return normalized in VARIANTS_ALLOWED_CHAPTERS

