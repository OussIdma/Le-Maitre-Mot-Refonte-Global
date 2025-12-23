"""
Modèles pour les templates éditables de générateurs

Les templates permettent aux admins de définir la rédaction pédagogique
(énoncés et solutions) sans toucher au code backend.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GeneratorTemplateCreate(BaseModel):
    """Données pour créer un template"""
    generator_key: str = Field(..., description="Clé du générateur (ex: RAISONNEMENT_MULTIPLICATIF_V1)")
    variant_id: str = Field(default="default", description="Variant pédagogique (A, B, C, default)")
    grade: Optional[str] = Field(default=None, description="Niveau (6e, 5e, null=tous)")
    difficulty: Optional[str] = Field(default=None, description="Difficulté (facile, moyen, difficile, null=tous)")
    
    enonce_template_html: str = Field(..., description="Template HTML de l'énoncé")
    solution_template_html: str = Field(..., description="Template HTML de la solution")
    
    allowed_html_vars: List[str] = Field(
        default_factory=list,
        description="Variables autorisées en triple moustaches {{{var}}} (ex: tableau_html)"
    )


class GeneratorTemplateUpdate(BaseModel):
    """Données pour mettre à jour un template"""
    variant_id: Optional[str] = None
    grade: Optional[str] = None
    difficulty: Optional[str] = None
    enonce_template_html: Optional[str] = None
    solution_template_html: Optional[str] = None
    allowed_html_vars: Optional[List[str]] = None


class GeneratorTemplate(BaseModel):
    """Template éditable pour un générateur (stocké en DB)"""
    id: Optional[str] = Field(default=None, alias="_id")
    generator_key: str
    variant_id: str = "default"
    grade: Optional[str] = None
    difficulty: Optional[str] = None
    
    enonce_template_html: str
    solution_template_html: str
    allowed_html_vars: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(default=None, description="User ID du créateur")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GeneratorTemplateValidateRequest(BaseModel):
    """Requête de validation/preview d'un template"""
    generator_key: str
    variant_id: str = "default"
    grade: Optional[str] = None
    difficulty: Optional[str] = None
    seed: int = Field(default=42, description="Seed pour générer les variables")
    
    enonce_template_html: str
    solution_template_html: str
    allowed_html_vars: List[str] = Field(default_factory=list)


class GeneratorTemplateValidateResponse(BaseModel):
    """Réponse de validation/preview"""
    valid: bool
    used_placeholders: List[str] = Field(default_factory=list)
    missing_placeholders: List[str] = Field(default_factory=list)
    html_security_errors: List[dict] = Field(default_factory=list)
    preview: Optional[dict] = None  # {enonce_html, solution_html, variables}
    error_message: Optional[str] = None

