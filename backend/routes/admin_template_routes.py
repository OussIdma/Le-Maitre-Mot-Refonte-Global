"""
Routes API admin pour la gestion des templates de générateurs

Permet aux admins de créer, modifier, et valider les templates
de rédaction (énoncés/solutions) sans toucher au code.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.models.generator_template import (
    GeneratorTemplate,
    GeneratorTemplateCreate,
    GeneratorTemplateUpdate,
    GeneratorTemplateValidateRequest,
    GeneratorTemplateValidateResponse
)
from backend.services.generator_template_service import get_template_service
from logger import get_logger

logger = get_logger()

router = APIRouter(prefix="/api/v1/admin/generator-templates", tags=["Admin - Templates"])


def get_db_dependency():
    """Dépendance pour récupérer la DB"""
    from server import db
    return db


@router.get("", response_model=List[GeneratorTemplate])
async def list_generator_templates(
    generator_key: Optional[str] = Query(None, description="Filtrer par clé de générateur"),
    variant_id: Optional[str] = Query(None, description="Filtrer par variant"),
    grade: Optional[str] = Query(None, description="Filtrer par niveau"),
    difficulty: Optional[str] = Query(None, description="Filtrer par difficulté"),
    db: AsyncIOMotorDatabase = Depends(get_db_dependency)
):
    """
    Liste tous les templates avec filtres optionnels
    
    **Exemples:**
    - GET /api/v1/admin/generator-templates
    - GET /api/v1/admin/generator-templates?generator_key=RAISONNEMENT_MULTIPLICATIF_V1
    - GET /api/v1/admin/generator-templates?generator_key=CALCUL_NOMBRES_V1&grade=6e
    """
    service = get_template_service(db)
    templates = await service.list_templates(
        generator_key=generator_key,
        variant_id=variant_id,
        grade=grade,
        difficulty=difficulty
    )
    
    logger.info(f"Liste templates: {len(templates)} trouvés")
    return templates


@router.get("/{template_id}", response_model=GeneratorTemplate)
async def get_generator_template(
    template_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db_dependency)
):
    """
    Récupérer un template par ID
    
    **Exemple:**
    - GET /api/v1/admin/generator-templates/507f1f77bcf86cd799439011
    """
    service = get_template_service(db)
    template = await service.get_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "TEMPLATE_NOT_FOUND",
                "message": f"Template '{template_id}' introuvable"
            }
        )
    
    return template


@router.post("", response_model=GeneratorTemplate, status_code=201)
async def create_generator_template(
    template_data: GeneratorTemplateCreate,
    db: AsyncIOMotorDatabase = Depends(get_db_dependency)
):
    """
    Créer un nouveau template
    
    **Exemple:**
    ```json
    {
      "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
      "variant_id": "A",
      "grade": "6e",
      "difficulty": "facile",
      "enonce_template_html": "<p><strong>{{consigne}}</strong></p><p>{{enonce}}</p>{{{tableau_html}}}",
      "solution_template_html": "<h4>{{methode}}</h4><pre>{{calculs_intermediaires}}</pre>",
      "allowed_html_vars": ["tableau_html"]
    }
    ```
    """
    service = get_template_service(db)
    
    try:
        template = await service.create_template(template_data)
        logger.info(f"Template créé: id={template.id}, generator={template.generator_key}")
        return template
    except Exception as e:
        logger.error(f"Erreur création template: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "TEMPLATE_CREATION_FAILED",
                "message": f"Erreur lors de la création du template: {str(e)}"
            }
        )


@router.put("/{template_id}", response_model=GeneratorTemplate)
async def update_generator_template(
    template_id: str,
    template_update: GeneratorTemplateUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db_dependency)
):
    """
    Mettre à jour un template existant
    
    **Exemple:**
    ```json
    {
      "enonce_template_html": "<p><strong>{{consigne}}</strong></p><p>{{enonce}}</p>",
      "allowed_html_vars": []
    }
    ```
    """
    service = get_template_service(db)
    
    template = await service.update_template(template_id, template_update)
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "TEMPLATE_NOT_FOUND",
                "message": f"Template '{template_id}' introuvable"
            }
        )
    
    logger.info(f"Template mis à jour: id={template_id}")
    return template


@router.delete("/{template_id}")
async def delete_generator_template(
    template_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db_dependency)
):
    """
    Supprimer un template
    
    **Exemple:**
    - DELETE /api/v1/admin/generator-templates/507f1f77bcf86cd799439011
    """
    service = get_template_service(db)
    
    success = await service.delete_template(template_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "TEMPLATE_NOT_FOUND",
                "message": f"Template '{template_id}' introuvable"
            }
        )
    
    logger.info(f"Template supprimé: id={template_id}")
    return {"success": True, "message": f"Template '{template_id}' supprimé"}


@router.post("/validate", response_model=GeneratorTemplateValidateResponse)
async def validate_generator_template(
    request: GeneratorTemplateValidateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db_dependency)
):
    """
    Valider un template et générer un preview
    
    **Actions effectuées:**
    1. Génère des variables via GeneratorFactory.generate()
    2. Parse les placeholders utilisés dans les templates
    3. Vérifie que tous les placeholders existent
    4. Vérifie la sécurité HTML (triple moustaches {{{var}}})
    5. Génère un preview du rendu HTML
    
    **Exemple de requête:**
    ```json
    {
      "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
      "variant_id": "default",
      "grade": "6e",
      "difficulty": "facile",
      "seed": 42,
      "enonce_template_html": "<p><strong>{{consigne}}</strong></p><p>{{enonce}}</p>{{{tableau_html}}}",
      "solution_template_html": "<h4>{{methode}}</h4><pre>{{calculs_intermediaires}}</pre><p>{{reponse_finale}}</p>",
      "allowed_html_vars": ["tableau_html"]
    }
    ```
    
    **Réponse succès (valid=true):**
    ```json
    {
      "valid": true,
      "used_placeholders": ["consigne", "enonce", "tableau_html", "methode", "calculs_intermediaires", "reponse_finale"],
      "missing_placeholders": [],
      "html_security_errors": [],
      "preview": {
        "enonce_html": "<p><strong>Compléter le tableau</strong></p>...",
        "solution_html": "<h4>Proportionnalité</h4>...",
        "variables": {...}
      }
    }
    ```
    
    **Réponse erreur (valid=false):**
    ```json
    {
      "valid": false,
      "used_placeholders": ["consigne", "vitesse", "enonce"],
      "missing_placeholders": ["vitesse"],
      "html_security_errors": [
        {
          "type": "html_var_not_allowed",
          "placeholder": "enonce",
          "message": "Triple moustaches interdites pour 'enonce'. Ajoutez 'enonce' à allowed_html_vars ou utilisez {{var}}"
        }
      ],
      "error_message": "Placeholders manquants: vitesse. Ces variables n'existent pas dans le générateur."
    }
    ```
    """
    service = get_template_service(db)
    
    logger.info(
        f"Validation template: generator={request.generator_key}, "
        f"variant={request.variant_id}, seed={request.seed}"
    )
    
    result = await service.validate_template(request)
    
    # Si invalid, retourner 422 avec détails
    if not result.valid:
        logger.warning(
            f"Template invalide: generator={request.generator_key}, "
            f"missing={result.missing_placeholders}, "
            f"html_errors={len(result.html_security_errors)}"
        )
        
        # P4.D - Distinguer les erreurs de difficulté invalide des erreurs de template mismatch
        error_code = "ADMIN_TEMPLATE_MISMATCH"
        if result.html_security_errors and not result.missing_placeholders:
            error_code = "HTML_VAR_NOT_ALLOWED"
        elif "ne peut pas générer avec la difficulté" in (result.error_message or ""):
            error_code = "GENERATOR_INVALID_DIFFICULTY"
        
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": error_code,
                "message": result.error_message,
                "used_placeholders": result.used_placeholders,
                "missing_placeholders": result.missing_placeholders,
                "html_security_errors": result.html_security_errors,
                "difficulty_requested": result.difficulty_requested,
                "difficulty_used": result.difficulty_used
            }
        )
    
    logger.info(
        f"Template valide: generator={request.generator_key}, "
        f"placeholders={len(result.used_placeholders)}"
    )
    
    return result

