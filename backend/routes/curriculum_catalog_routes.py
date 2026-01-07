"""
Routes API pour le catalogue du curriculum.

Endpoint public pour alimenter /generate avec le référentiel officiel.
"""

from fastapi import APIRouter, Depends
from typing import Optional

from backend.curriculum.loader import get_catalog, get_codes_for_macro_group
from backend.logger import get_logger

logger = get_logger()

router = APIRouter(prefix="/api/v1/curriculum", tags=["Curriculum Catalog"])
legacy_router = APIRouter(prefix="/api/v1", tags=["Curriculum Catalog"])


async def get_db():
    """Dépendance pour obtenir la base de données"""
    from backend.server import db
    return db


@router.get(
    "/{level}/catalog",
    summary="Catalogue du curriculum pour le frontend",
    description="""
    Retourne le catalogue complet d'un niveau pour alimenter /generate.
    
    **Source de vérité enrichie** :
    - Curriculum (exercise_types) : source principale
    - Collection exercises (DB) : enrichissement si exercices existent en DB
    
    Si un chapitre a des exercices en DB mais pas d'exercise_types dans le curriculum,
    les exercise_types sont extraits depuis la DB pour rendre le chapitre disponible.
    
    Contient:
    - **domains**: Liste des domaines avec leurs chapitres officiels
    - **macro_groups**: Groupes simplifiés pour le mode "simple"
    
    Le frontend peut utiliser:
    - Mode officiel: affiche domains[].chapters[]
    - Mode simple: affiche macro_groups[]
    
    Pour générer, utiliser toujours code_officiel dans la requête.
    """
)
async def get_curriculum_catalog(level: str, db=Depends(get_db)):
    """
    Retourne le catalogue du curriculum pour un niveau, enrichi depuis la DB.
    """
    logger.info(f"Catalog: Récupération du catalogue pour le niveau {level}")
    
    catalog = await get_catalog(level, db=db)
    
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


# ---------------------------------------------------------------------------
# Legacy alias: /api/v1/catalog (par défaut niveau 6e)
# ---------------------------------------------------------------------------
@legacy_router.get(
    "/catalog",
    summary="Alias legacy du catalogue 6e",
    description="Retourne le catalogue pour le niveau 6e (compatibilité /api/v1/catalog)."
)
async def get_default_catalog(db=Depends(get_db)):
    logger.info("Catalog: alias /api/v1/catalog → niveau 6e (legacy)")
    catalog = await get_catalog("6e", db=db)
    return catalog
