"""
Routes API pour le catalogue du curriculum.

Endpoint public pour alimenter /generate avec le référentiel officiel.
"""

from fastapi import APIRouter
from typing import Optional

from curriculum.loader import get_catalog, get_codes_for_macro_group
from logger import get_logger

logger = get_logger()

router = APIRouter(prefix="/api/v1/curriculum", tags=["Curriculum Catalog"])


@router.get(
    "/{level}/catalog",
    summary="Catalogue du curriculum pour le frontend",
    description="""
    Retourne le catalogue complet d'un niveau pour alimenter /generate.
    
    Contient:
    - **domains**: Liste des domaines avec leurs chapitres officiels
    - **macro_groups**: Groupes simplifiés pour le mode "simple"
    
    Le frontend peut utiliser:
    - Mode officiel: affiche domains[].chapters[]
    - Mode simple: affiche macro_groups[]
    
    Pour générer, utiliser toujours code_officiel dans la requête.
    """
)
async def get_curriculum_catalog(level: str):
    """
    Retourne le catalogue du curriculum pour un niveau.
    """
    logger.info(f"Catalog: Récupération du catalogue pour le niveau {level}")
    
    catalog = get_catalog(level)
    
    logger.info(f"Catalog: {catalog.get('total_chapters', 0)} chapitres, {catalog.get('total_macro_groups', 0)} macro groups")
    
    return catalog


@router.get(
    "/{level}/macro/{label}/codes",
    summary="Codes officiels d'un macro group",
    description="""
    Retourne les codes officiels associés à un macro group.
    
    Utile pour le mode simple: quand l'utilisateur choisit un groupe macro,
    le frontend peut récupérer les codes et en choisir un aléatoirement.
    """
)
async def get_macro_group_codes(level: str, label: str):
    """
    Retourne les codes officiels pour un macro group.
    """
    if level != "6e":
        return {
            "label": label,
            "codes_officiels": [],
            "error": f"Niveau '{level}' non supporté"
        }
    
    codes = get_codes_for_macro_group(label)
    
    return {
        "label": label,
        "codes_officiels": codes,
        "count": len(codes)
    }
