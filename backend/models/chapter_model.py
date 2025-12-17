"""
Modèle pour les chapitres MathALÉA
Collection MongoDB: chapters
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


class ChapterBase(BaseModel):
    """Modèle de base pour un chapitre"""
    code: str = Field(..., description="Code MathALÉA unique, ex: '6e_G04'")
    legacy_code: Optional[str] = Field(None, description="Code legacy pour migration, ex: '6G20'")
    niveau: str = Field(..., description="Niveau scolaire, ex: '6e', '2nde', 'Tale'")
    domaine: str = Field(..., description="Domaine mathématique, ex: 'Géométrie'")
    domaine_legacy: Optional[str] = Field(None, description="Domaine au format legacy, ex: 'Espace et géométrie'")
    titre: str = Field(..., description="Libellé complet du chapitre")
    ordre: int = Field(..., description="Ordre d'affichage dans le niveau/domaine")


class ChapterCreate(ChapterBase):
    """Modèle pour la création d'un chapitre"""
    pass


class Chapter(ChapterBase):
    """Modèle complet d'un chapitre avec métadonnées"""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "6e_G04",
                "legacy_code": "6G20",
                "niveau": "6e",
                "domaine": "Géométrie",
                "domaine_legacy": "Espace et géométrie",
                "titre": "Angles et droites perpendiculaires",
                "ordre": 4
            }
        }


# Mapping des domaines MathALÉA → Legacy
DOMAINE_MAPPING = {
    "Géométrie": "Espace et géométrie",
    "Nombres et calculs": "Nombres et calculs",
    "Grandeurs et mesures": "Grandeurs et mesures",
    "Organisation et gestion de données": "Organisation et gestion de données",
    "Proportionnalité et pourcentages": "Organisation et gestion de données",
    "Proportionnalité et fonctions": "Organisation et gestion de données",
    "Calcul littéral et équations": "Algèbre",
    "Calcul littéral": "Algèbre",
    "Statistiques et probabilités": "Organisation et gestion de données",
    "Probabilités": "Organisation et gestion de données",
    "Fonctions": "Algèbre",
    "Suites": "Algèbre",
    "Algorithmique et programmation": "Algorithmique",
    "Géométrie repérée": "Espace et géométrie",
    "Géométrie de l'espace": "Espace et géométrie",
    "Géométrie et vecteurs": "Espace et géométrie",
    "Géométrie et espace": "Espace et géométrie",
    "Produit scalaire": "Espace et géométrie",
    "Limites et continuité": "Analyse",
    "Fonctions et calcul différentiel": "Analyse",
    "Fonctions et dérivation": "Analyse",
    "Fonctions exponentielles et logarithmes": "Analyse"
}


def get_domaine_legacy(domaine_mathalea: str) -> str:
    """
    Retourne le domaine au format legacy
    
    Args:
        domaine_mathalea: Domaine au format MathALÉA
        
    Returns:
        Domaine au format legacy
    """
    return DOMAINE_MAPPING.get(domaine_mathalea, domaine_mathalea)


__all__ = [
    "Chapter",
    "ChapterCreate",
    "ChapterBase",
    "DOMAINE_MAPPING",
    "get_domaine_legacy"
]
