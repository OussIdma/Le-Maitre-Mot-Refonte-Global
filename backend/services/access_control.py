"""
Service de contrôle d'accès centralisé pour les exports PDF

PR7.1: Gating export PDF = compte requis
- Tous les exports PDF nécessitent un compte (Free ou Pro)
- Layout "eco" nécessite Premium (PR8)
"""

from fastapi import HTTPException
from typing import Optional, Dict, Any


def assert_can_export_pdf(user_email: Optional[str]) -> None:
    """
    Vérifie qu'un utilisateur peut exporter en PDF.
    
    PR7.1: Export PDF nécessite un compte (Free ou Pro).
    
    Args:
        user_email: Email de l'utilisateur (None si non connecté)
    
    Raises:
        HTTPException(401): Si user_email est None avec code "AUTH_REQUIRED_EXPORT"
    """
    if user_email is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "AUTH_REQUIRED_EXPORT",
                "code": "AUTH_REQUIRED_EXPORT",
                "message": "Connexion requise pour exporter un PDF. Créez un compte gratuit pour continuer.",
                "action": "show_login_modal"
            }
        )


def assert_can_use_layout(user_email: Optional[str], is_pro: bool, layout: str) -> None:
    """
    Vérifie qu'un utilisateur peut utiliser un layout spécifique.
    
    PR8: Layout "eco" = Premium uniquement.
    
    Args:
        user_email: Email de l'utilisateur (None si non connecté)
        is_pro: True si l'utilisateur est Premium
        layout: Layout demandé ("eco" ou "classic")
    
    Raises:
        HTTPException(401): Si user_email est None
        HTTPException(403): Si layout="eco" et user pas Premium
    """
    # PR7.1: D'abord vérifier qu'un compte est requis
    assert_can_export_pdf(user_email)
    
    # PR8: Layout "eco" nécessite Premium
    if layout == "eco" and not is_pro:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "PREMIUM_REQUIRED_ECO",
                "error": "premium_required",
                "message": "Mode éco réservé Premium",
                "action": "upgrade"
            }
        )

