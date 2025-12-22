"""
Modèles pour le catalogue unifié (Sprint F.2)

Structure organisationnelle des exercices :
- Niveaux (6e, 5e, 4e, 3e)
- Domaines (Nombres et calculs, Espace et géométrie, etc.)
- Chapitres (Symétrie axiale, Pythagore, etc.)
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ChapterBase(BaseModel):
    """Base pour un chapitre"""
    titre: str = Field(..., description="Titre du chapitre")
    niveau: str = Field(..., description="Niveau scolaire (6e, 5e, 4e, 3e)")
    domaine: str = Field(..., description="Domaine mathématique")
    code: Optional[str] = Field(None, description="Code Eduscol (ex: 5G10)")
    description: Optional[str] = Field(None, description="Description du chapitre")
    ordre: int = Field(0, description="Ordre d'affichage dans le niveau")


class Chapter(ChapterBase):
    """Chapitre complet avec ID"""
    id: str = Field(..., description="ID unique du chapitre")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "chapter_sym_ax_6e",
                "titre": "Symétrie axiale",
                "niveau": "6e",
                "domaine": "Espace et géométrie",
                "code": "6G20",
                "ordre": 10
            }
        }


class ChapterWithStats(Chapter):
    """Chapitre avec statistiques (nombre d'exercices)"""
    nb_exercises: int = Field(0, description="Nombre d'exercices disponibles")


class CatalogueExerciseType(BaseModel):
    """ExerciseType enrichi pour le catalogue"""
    id: str
    code_ref: str
    titre: str
    niveau: str
    domaine: str
    chapitre: Optional[dict] = Field(None, description="Info du chapitre")
    generator_kind: str
    difficulty_levels: List[str]
    min_questions: int
    max_questions: int
    default_questions: int
    supports_ai_enonce: bool
    supports_ai_correction: bool
    is_legacy: bool = Field(False, description="Est un exercice legacy")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "ex123",
                "code_ref": "LEGACY_SYM_AX_6e",
                "titre": "Symétrie axiale (6e)",
                "niveau": "6e",
                "domaine": "Espace et géométrie",
                "chapitre": {
                    "id": "chapter_sym_ax_6e",
                    "titre": "Symétrie axiale",
                    "code": "6G20"
                },
                "generator_kind": "legacy",
                "difficulty_levels": ["facile", "moyen"],
                "min_questions": 1,
                "max_questions": 6,
                "default_questions": 3,
                "supports_ai_enonce": True,
                "supports_ai_correction": True,
                "is_legacy": True
            }
        }


# Export
__all__ = [
    "Chapter",
    "ChapterBase",
    "ChapterWithStats",
    "CatalogueExerciseType"
]
