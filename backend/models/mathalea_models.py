"""
Modèles MathALÉA-like pour Le Maître Mot
Architecture extensible pour gestion avancée des exercices

Respecte:
- Pydantic v2
- MongoDB avec Motor
- Architecture non-destructive
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime, timezone
from uuid import UUID, uuid4


class GeneratorKind(str, Enum):
    """Type de générateur d'exercice"""
    TEMPLATE = "template"  # Gabarits pré-définis
    IA = "ia"  # Génération par IA
    HYBRID = "hybrid"  # Combinaison des deux
    LEGACY = "legacy"  # Générateurs du système legacy (Sprint F.1)


# ============================================================================
# MODÈLE: Competence
# ============================================================================

class CompetenceBase(BaseModel):
    """Base pour les compétences (sans ID)"""
    code: str = Field(..., description="Code unique de la compétence (ex: 6G1)")
    intitule: str = Field(..., description="Intitulé complet de la compétence")
    niveau: str = Field(..., description="Niveau scolaire (ex: 6e, 5e, 4e)")
    domaine: str = Field(..., description="Domaine (Nombres, Géométrie, etc.)")


class CompetenceCreate(CompetenceBase):
    """Modèle pour création d'une compétence"""
    pass


class CompetenceUpdate(BaseModel):
    """Modèle pour mise à jour d'une compétence"""
    code: Optional[str] = None
    intitule: Optional[str] = None
    niveau: Optional[str] = None
    domaine: Optional[str] = None


class Competence(CompetenceBase):
    """Modèle complet d'une compétence (avec ID)"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="UUID de la compétence")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "6G1",
                "intitule": "Reconnaître et construire une symétrie axiale",
                "niveau": "6e",
                "domaine": "Espace et géométrie"
            }
        }


# ============================================================================
# MODÈLE: ExerciseType
# ============================================================================

class ExerciseTypeBase(BaseModel):
    """Base pour les types d'exercices (sans ID)"""
    code_ref: str = Field(..., description="Code de référence unique (ex: SYM_AX_01)")
    titre: str = Field(..., description="Titre de l'exercice")
    chapitre_id: Optional[str] = Field(None, description="ID du chapitre associé (legacy)")
    chapter_code: Optional[str] = Field(None, description="Code du chapitre MathALÉA (ex: 6e_G04)")
    niveau: str = Field(..., description="Niveau scolaire")
    domaine: str = Field(..., description="Domaine mathématique")
    
    # Relations
    competences_ids: List[str] = Field(
        default_factory=list,
        description="IDs des compétences liées"
    )
    
    # Configuration des questions
    min_questions: int = Field(1, ge=1, description="Nombre minimum de questions")
    max_questions: int = Field(10, ge=1, description="Nombre maximum de questions")
    default_questions: int = Field(5, ge=1, description="Nombre par défaut de questions")
    
    # Niveaux de difficulté disponibles
    difficulty_levels: List[str] = Field(
        default_factory=lambda: ["facile", "moyen", "difficile"],
        description="Niveaux de difficulté disponibles"
    )
    
    # Types de questions possibles
    question_kinds: Dict[str, Any] = Field(
        default_factory=dict,
        description="Types de questions (ex: trouver_valeur, verifier_propriete)"
    )
    
    # Configuration aléatoire
    random_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration pour la génération aléatoire"
    )
    
    # Type de générateur
    generator_kind: GeneratorKind = Field(
        default=GeneratorKind.TEMPLATE,
        description="Type de générateur (template/ia/hybrid/legacy)"
    )
    
    # ID du générateur legacy (Sprint F.1)
    legacy_generator_id: Optional[str] = Field(
        None,
        description="ID du générateur legacy (MathExerciseType) si generator_kind=LEGACY"
    )
    
    # Capacités IA
    supports_seed: bool = Field(
        default=True,
        description="Support de la graine aléatoire pour reproductibilité"
    )
    supports_ai_enonce: bool = Field(
        default=False,
        description="Support de la génération d'énoncé par IA"
    )
    supports_ai_correction: bool = Field(
        default=False,
        description="Support de la génération de correction par IA"
    )


class ExerciseTypeCreate(ExerciseTypeBase):
    """Modèle pour création d'un type d'exercice"""
    pass


class ExerciseTypeUpdate(BaseModel):
    """Modèle pour mise à jour d'un type d'exercice"""
    code_ref: Optional[str] = None
    titre: Optional[str] = None
    chapitre_id: Optional[str] = None
    chapter_code: Optional[str] = None
    niveau: Optional[str] = None
    domaine: Optional[str] = None
    competences_ids: Optional[List[str]] = None
    min_questions: Optional[int] = None
    max_questions: Optional[int] = None
    default_questions: Optional[int] = None
    difficulty_levels: Optional[List[str]] = None
    question_kinds: Optional[Dict[str, Any]] = None
    random_config: Optional[Dict[str, Any]] = None
    generator_kind: Optional[GeneratorKind] = None
    legacy_generator_id: Optional[str] = None
    supports_seed: Optional[bool] = None
    supports_ai_enonce: Optional[bool] = None
    supports_ai_correction: Optional[bool] = None


class ExerciseType(ExerciseTypeBase):
    """Modèle complet d'un type d'exercice (avec ID)"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="UUID du type d'exercice")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "code_ref": "SYM_AX_01",
                "titre": "Symétrie axiale - Trouver le symétrique",
                "chapitre_id": "chapitre_123",
                "niveau": "6e",
                "domaine": "Espace et géométrie",
                "competences_ids": ["550e8400-e29b-41d4-a716-446655440000"],
                "min_questions": 1,
                "max_questions": 10,
                "default_questions": 5,
                "difficulty_levels": ["facile", "moyen", "difficile"],
                "generator_kind": "template",
                "supports_seed": True,
                "supports_ai_enonce": False,
                "supports_ai_correction": False
            }
        }


# ============================================================================
# MODÈLE: ExerciseSheet (Feuille d'exercices)
# ============================================================================

class ExerciseSheetBase(BaseModel):
    """Base pour les feuilles d'exercices"""
    titre: str = Field(..., description="Titre de la feuille")
    niveau: str = Field(..., description="Niveau scolaire")
    description: Optional[str] = Field(None, description="Description optionnelle")


class ExerciseSheetCreate(ExerciseSheetBase):
    """Modèle pour création d'une feuille"""
    owner_id: str = Field(..., description="ID du propriétaire (user ou guest)")


class ExerciseSheetUpdate(BaseModel):
    """Modèle pour mise à jour d'une feuille"""
    titre: Optional[str] = None
    niveau: Optional[str] = None
    description: Optional[str] = None


class ExerciseSheet(ExerciseSheetBase):
    """Modèle complet d'une feuille d'exercices"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="UUID de la feuille")
    owner_id: str = Field(..., description="ID du propriétaire")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440000",
                "titre": "Révisions Géométrie 6e",
                "niveau": "6e",
                "owner_id": "user_123",
                "created_at": "2025-01-01T10:00:00Z",
                "updated_at": "2025-01-01T10:00:00Z"
            }
        }


# ============================================================================
# MODÈLE: ExerciseItemConfig (Configuration standardisée pour SheetItem)
# ============================================================================

class ExerciseItemConfig(BaseModel):
    """
    Configuration standardisée pour un SheetItem
    
    Cette structure définit exactement comment générer un exercice
    à partir d'un ExerciseType dans une feuille.
    """
    nb_questions: int = Field(..., ge=1, description="Nombre de questions")
    difficulty: Optional[str] = Field(None, description="Niveau de difficulté")
    seed: int = Field(..., description="Graine pour reproductibilité")
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Options spécifiques à l'exercice"
    )
    ai_enonce: bool = Field(False, description="Utiliser l'IA pour l'énoncé")
    ai_correction: bool = Field(False, description="Utiliser l'IA pour la correction")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nb_questions": 5,
                "difficulty": "moyen",
                "seed": 42,
                "options": {},
                "ai_enonce": False,
                "ai_correction": False
            }
        }


# ============================================================================
# MODÈLE: SheetItem (Item dans une feuille)
# ============================================================================

class SheetItemBase(BaseModel):
    """Base pour les items d'une feuille"""
    sheet_id: str = Field(..., description="ID de la feuille parente")
    exercise_type_id: str = Field(..., description="ID du type d'exercice")
    config: ExerciseItemConfig = Field(..., description="Configuration de l'exercice")


class SheetItemCreate(SheetItemBase):
    """Modèle pour création d'un item de feuille"""
    pass


class SheetItemUpdate(BaseModel):
    """Modèle pour mise à jour d'un item de feuille"""
    config: Optional[ExerciseItemConfig] = None


class SheetItem(SheetItemBase):
    """Modèle complet d'un item de feuille"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="UUID de l'item")
    order: int = Field(0, description="Ordre dans la feuille")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "880e8400-e29b-41d4-a716-446655440000",
                "sheet_id": "770e8400-e29b-41d4-a716-446655440000",
                "exercise_type_id": "660e8400-e29b-41d4-a716-446655440000",
                "config": {
                    "nb_questions": 5,
                    "difficulty": "moyen",
                    "seed": 12345,
                    "options": {},
                    "ai_enonce": False,
                    "ai_correction": False
                },
                "order": 1
            }
        }


# ============================================================================
# MODÈLES DE RÉPONSE
# ============================================================================

class CompetenceListResponse(BaseModel):
    """Réponse pour liste de compétences"""
    total: int
    items: List[Competence]


class ExerciseTypeListResponse(BaseModel):
    """Réponse pour liste de types d'exercices"""
    total: int
    items: List[ExerciseType]


class ExerciseSheetListResponse(BaseModel):
    """Réponse pour liste de feuilles"""
    total: int
    items: List[ExerciseSheet]


class SheetItemListResponse(BaseModel):
    """Réponse pour liste d'items de feuille"""
    total: int
    items: List[SheetItem]


# ============================================================================
# MODÈLE: Pro PDF Request
# ============================================================================

class ProPdfRequest(BaseModel):
    """Requête pour génération de PDF Pro avec template"""
    template: str = Field(
        default="classique",
        description="Template à utiliser: 'classique' ou 'academique'"
    )
    type_doc: str = Field(
        default="exercices",
        description="Type de document: 'exercices', 'controle', 'evaluation', 'dm'"
    )


# ============================================================================
# MODÈLE: Pro User Configuration
# ============================================================================

class ProUserConfig(BaseModel):
    """Configuration Pro pour un utilisateur"""
    user_email: str = Field(..., description="Email de l'utilisateur Pro")
    professor_name: str = Field(default="", description="Nom du professeur")
    school_name: str = Field(default="", description="Nom de l'établissement")
    school_year: str = Field(default="", description="Année scolaire (ex: 2024-2025)")
    footer_text: str = Field(default="", description="Texte du pied de page")
    logo_url: Optional[str] = Field(default=None, description="URL du logo de l'établissement")
    template_choice: str = Field(default="classique", description="Template préféré: classique ou academique")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProUserConfigCreate(BaseModel):
    """Modèle pour création/mise à jour de configuration Pro"""
    professor_name: Optional[str] = None
    school_name: Optional[str] = None
    school_year: Optional[str] = None
    footer_text: Optional[str] = None
    logo_url: Optional[str] = None
    template_choice: Optional[str] = "classique"
