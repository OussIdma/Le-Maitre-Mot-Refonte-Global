"""
Routes API pour les générateurs dynamiques (Dynamic Factory v1)
===============================================================

Endpoints:
- GET /api/v1/exercises/generators : Liste tous les générateurs
- GET /api/v1/exercises/generators/{key}/schema : Schéma complet d'un générateur
- POST /api/admin/exercises/preview-dynamic : Preview d'un exercice dynamique
- POST /api/admin/exercises/generate-from-factory : Génération via Factory

Version: 2.0.0 (Dynamic Factory v1)
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi import status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# Import du nouveau système Factory
from backend.generators.factory import (
    get_generators_list,
    get_generator_schema as factory_get_schema,
    generate_exercise as factory_generate,
    validate_exercise_params
)

# Imports legacy pour compatibilité
from backend.generators.generator_registry import (
    get_generator_schema as legacy_get_schema,
    get_all_generator_keys,
    get_all_schemas_summary
)
from backend.generators.thales_generator import generate_dynamic_exercise
from backend.services.template_renderer import render_template
from backend.logger import get_logger

logger = get_logger()

router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_generator_schema(generator_key: str):
    """
    Récupère le schéma d'un générateur (essaie Factory puis Legacy).
    Retourne None si non trouvé.
    """
    # Essayer d'abord le nouveau système Factory
    schema = factory_get_schema(generator_key.upper())
    if schema:
        return schema
    
    # Fallback sur le système legacy
    return legacy_get_schema(generator_key.upper())


def _normalize_figure_type(raw: Optional[str]) -> Optional[str]:
    """
    Normalise le type de figure pour les générateurs de géométrie (THALES_V1, ...).
    - lower + trim
    - mapping de quelques synonymes évidents (carré/square -> carre)
    """
    if not raw:
        return None

    v = str(raw).strip().lower()
    mapping = {
        "carré": "carre",
        "square": "carre",
    }
    return mapping.get(v, v)


def _apply_thales_alias_mappings(all_vars: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applique les mêmes mappings d'alias que pour le pipeline TESTS_DYN
    afin d'éviter les placeholders {{...}} en preview admin pour THALES_V1.

    - triangle: base/hauteur -> longueur/largeur
    - rectangle: longueur/largeur -> base/hauteur
    - carre: cote -> longueur/largeur/base/hauteur
    """
    raw_figure_type = all_vars.get("figure_type")
    figure_type = _normalize_figure_type(raw_figure_type)
    if figure_type:
        all_vars["figure_type"] = figure_type

    # 1) triangle → rectangle (base/hauteur -> longueur/largeur)
    if figure_type == "triangle":
        if "base_initiale" in all_vars:
            all_vars.setdefault("longueur_initiale", all_vars["base_initiale"])
        if "hauteur_initiale" in all_vars:
            all_vars.setdefault("largeur_initiale", all_vars["hauteur_initiale"])
        if "base_finale" in all_vars:
            all_vars.setdefault("longueur_finale", all_vars["base_finale"])
        if "hauteur_finale" in all_vars:
            all_vars.setdefault("largeur_finale", all_vars["hauteur_finale"])

    # 2) rectangle → triangle (longueur/largeur -> base/hauteur)
    if figure_type == "rectangle":
        if "longueur_initiale" in all_vars:
            all_vars.setdefault("base_initiale", all_vars["longueur_initiale"])
        if "largeur_initiale" in all_vars:
            all_vars.setdefault("hauteur_initiale", all_vars["largeur_initiale"])
        if "longueur_finale" in all_vars:
            all_vars.setdefault("base_finale", all_vars["longueur_finale"])
        if "largeur_finale" in all_vars:
            all_vars.setdefault("hauteur_finale", all_vars["largeur_finale"])

    # 3) carré → rectangle + triangle (cote -> longueur/largeur/base/hauteur)
    if figure_type == "carre":
        cote_initial = (
            all_vars.get("cote_initial")
            or all_vars.get("cote_initiale")
            or all_vars.get("side_initial")
            or all_vars.get("side")
        )
        cote_final = (
            all_vars.get("cote_final")
            or all_vars.get("cote_finale")
            or all_vars.get("side_final")
        )

        if cote_initial is not None:
            all_vars.setdefault("cote_initial", cote_initial)
        if cote_final is not None:
            all_vars.setdefault("cote_final", cote_final)

        if cote_initial is not None:
            all_vars.setdefault("longueur_initiale", cote_initial)
            all_vars.setdefault("largeur_initiale", cote_initial)
            all_vars.setdefault("base_initiale", cote_initial)
            all_vars.setdefault("hauteur_initiale", cote_initial)

        if cote_final is not None:
            all_vars.setdefault("longueur_finale", cote_final)
            all_vars.setdefault("largeur_finale", cote_final)
            all_vars.setdefault("base_finale", cote_final)
            all_vars.setdefault("hauteur_finale", cote_final)

    return all_vars


# =============================================================================
# MODÈLES PYDANTIC
# =============================================================================

class GeneratorSchemaResponse(BaseModel):
    generator_key: str
    label: str
    description: str
    niveau: str
    variables: List[Dict[str, Any]]
    svg_modes: List[str]
    supports_double_svg: bool
    difficulties: List[str]
    pedagogical_tips: Optional[str]
    template_example_enonce: str
    template_example_solution: str


class DynamicPreviewRequest(BaseModel):
    generator_key: str = Field(description="Clé du générateur (ex: THALES_V1)")
    enonce_template_html: str = Field(description="Template HTML de l'énoncé")
    solution_template_html: str = Field(description="Template HTML de la solution")
    difficulty: str = Field(default="moyen")
    seed: Optional[int] = Field(default=None)
    svg_mode: str = Field(default="AUTO")


class DynamicPreviewResponse(BaseModel):
    success: bool
    enonce_html: str
    solution_html: str
    variables_used: Dict[str, Any]
    svg_enonce: Optional[str]
    svg_solution: Optional[str]
    errors: List[str] = Field(default_factory=list)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/generators/{generator_key}/schema", response_model=GeneratorSchemaResponse, tags=["Generators"])
async def get_generator_schema_endpoint(generator_key: str):
    """Récupère le schéma complet d'un générateur dynamique."""
    try:
        schema = get_generator_schema(generator_key.upper())
        
        if not schema:
            available = get_all_generator_keys()
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "generator_not_found",
                    "error": "generator_not_found",
                    "message": f"Générateur '{generator_key}' non trouvé",
                    "available_generators": available
                }
            )
        
        return GeneratorSchemaResponse(**schema.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting generator schema: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "error": "internal_error",
                "message": f"Erreur lors de la récupération du schéma: {str(e)}"
            }
        )


@router.get("/generators/list", tags=["Generators"])
async def list_generators_endpoint():
    """Liste tous les générateurs disponibles."""
    summaries = get_all_schemas_summary()
    return {"generators": summaries, "count": len(summaries)}


@router.post("/preview-dynamic", response_model=DynamicPreviewResponse, tags=["Generators"])
async def preview_dynamic_exercise(request: DynamicPreviewRequest):
    """Prévisualise un exercice dynamique AVANT de le sauvegarder."""
    import re
    from fastapi.responses import JSONResponse
    from fastapi import status
    import traceback
    
    logger.info(f"🔍 Preview dynamic: generator={request.generator_key}, seed={request.seed}")
    
    # Wrapper COMPLET dans try/except pour garantir JSON même en cas d'erreur
    try:
        errors = []
        
        # Récupération du schéma (dans le try pour catch les exceptions d'import/attribut)
        generator_key = request.generator_key.upper()
        schema = get_generator_schema(generator_key)
        if not schema:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error_code": "invalid_generator",
                    "error": "invalid_generator",
                    "message": f"Générateur '{request.generator_key}' non reconnu",
                    "success": False,
                    "enonce_html": "",
                    "solution_html": "",
                    "variables_used": {},
                    "svg_enonce": None,
                    "svg_solution": None,
                    "errors": [f"Générateur '{request.generator_key}' non reconnu"]
                }
            )
        
        # =========================================================================
        # Génération de l'exercice
        # - Si le générateur existe dans la Factory v1 -> utiliser factory_generate
        # - Sinon, fallback sur le pipeline legacy THALES_V1
        # =========================================================================

        factory_schema = factory_get_schema(generator_key)
        if factory_schema:
            # Nouveau pipeline Factory (ex: SYMETRIE_AXIALE_V2, THALES_V2, ...)
            logger.info(f"🏭 Preview via Factory pour generator={generator_key}")
            result = factory_generate(
                generator_key=generator_key,
                exercise_params=None,
                overrides=None,
                seed=request.seed,
            )

            variables = result.get("variables", {})
            # La Factory peut aussi retourner des résultats/geo_data utiles pour le template
            all_vars = {
                **variables,
                **result.get("results", {}),
                **result.get("geo_data", {}),
            }

            svg_enonce = result.get("figure_svg_enonce") if request.svg_mode == "AUTO" else None
            svg_solution = result.get("figure_svg_solution") if request.svg_mode == "AUTO" else None
        else:
            # Pipeline legacy (THALES_V1 historique)
            logger.info(f"📐 Preview via générateur legacy pour generator={generator_key}")
            gen_result = generate_dynamic_exercise(
                generator_key=generator_key,
                seed=request.seed,
                difficulty=request.difficulty,
            )

            variables = gen_result.get("variables", {})
            results = gen_result.get("results", {})
            all_vars = {**variables, **results}

            # Harmoniser le comportement avec le pipeline élève (TESTS_DYN) pour THALES_V1 :
            # appliquer les mêmes alias de variables afin d'éviter les placeholders {{...}}
            # lorsque les templates utilisent base/hauteur/longueur/largeur avec des carrés.
            if generator_key.startswith("THALES"):
                all_vars = _apply_thales_alias_mappings(all_vars)

            svg_enonce = gen_result.get("figure_svg_enonce") if request.svg_mode == "AUTO" else None
            svg_solution = gen_result.get("figure_svg_solution") if request.svg_mode == "AUTO" else None
        
        # Rendu des templates
        enonce_html = render_template(request.enonce_template_html, all_vars)
        solution_html = render_template(request.solution_template_html, all_vars)
        
        # Détection des placeholders non résolus
        unreplaced_enonce = re.findall(r'\{\{(\w+)\}\}', enonce_html)
        unreplaced_solution = re.findall(r'\{\{(\w+)\}\}', solution_html)
        
        for var in set(unreplaced_enonce + unreplaced_solution):
            errors.append(f"Variable inconnue: {{{{{var}}}}}")
        
        return DynamicPreviewResponse(
            success=len(errors) == 0,
            enonce_html=enonce_html,
            solution_html=solution_html,
            variables_used=all_vars,
            svg_enonce=svg_enonce,
            svg_solution=svg_solution,
            errors=errors
        )
        
    except HTTPException as http_exc:
        # Re-raise HTTPException mais en format JSON structuré
        return JSONResponse(
            status_code=http_exc.status_code,
            content={
                "error_code": http_exc.detail.get("error", "http_error") if isinstance(http_exc.detail, dict) else "http_error",
                "error": http_exc.detail.get("error", "http_error") if isinstance(http_exc.detail, dict) else "http_error",
                "message": http_exc.detail.get("message", str(http_exc.detail)) if isinstance(http_exc.detail, dict) else str(http_exc.detail),
                "success": False,
                "enonce_html": "",
                "solution_html": "",
                "variables_used": {},
                "svg_enonce": None,
                "svg_solution": None,
                "errors": [str(http_exc.detail)]
            }
        )
    except Exception as e:
        logger.error(f"❌ Preview internal error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "error": "preview_failed",
                "message": "Erreur interne lors de la prévisualisation",
                "details": str(e),
                "success": False,
                "enonce_html": "",
                "solution_html": "",
                "variables_used": {},
                "svg_enonce": None,
                "svg_solution": None,
                "errors": [f"Erreur interne: {str(e)}"]
            }
        )


@router.post("/validate-template", tags=["Generators"])
async def validate_template(template: str, generator_key: str):
    """Valide les variables d'un template."""
    import re
    
    schema = legacy_get_schema(generator_key.upper())
    if not schema:
        raise HTTPException(status_code=400, detail={"error": "invalid_generator"})
    
    used_vars = set(re.findall(r'\{\{(\w+)\}\}', template))
    known_var_names = {v.name for v in schema.variables}
    
    known = list(used_vars & known_var_names)
    unknown = list(used_vars - known_var_names)
    
    return {"valid": len(unknown) == 0, "unknown_variables": unknown, "known_variables": known}


# =============================================================================
# NOUVEAUX ENDPOINTS - DYNAMIC FACTORY V1
# =============================================================================

@router.get("/generators", tags=["Factory"])
async def list_all_generators():
    """
    Liste tous les générateurs disponibles (Dynamic Factory v1).
    
    Retourne les métadonnées de chaque générateur:
    - key, label, description
    - version, niveaux supportés
    - exercise_type, svg_mode
    - nombre de paramètres et presets
    """
    generators = get_generators_list()
    return {
        "generators": generators,
        "count": len(generators),
        "api_version": "2.0.0"
    }


class FactorySchemaResponse(BaseModel):
    """Réponse du schéma Factory."""
    generator_key: str
    meta: Dict[str, Any]
    defaults: Dict[str, Any]
    schema: List[Dict[str, Any]]
    presets: List[Dict[str, Any]]


@router.get("/generators/{generator_key}/full-schema", response_model=FactorySchemaResponse, tags=["Factory"])
async def get_factory_schema(generator_key: str):
    """
    Récupère le schéma complet d'un générateur (Dynamic Factory v1).
    
    Retourne:
    - meta: métadonnées du générateur
    - defaults: valeurs par défaut
    - schema: définition des paramètres avec types
    - presets: configurations pédagogiques prédéfinies
    """
    schema = factory_get_schema(generator_key.upper())
    
    if not schema:
        # Fallback sur le système legacy
        legacy = legacy_get_schema(generator_key.upper())
        if legacy:
            return FactorySchemaResponse(
                generator_key=generator_key.upper(),
                meta={
                    "key": generator_key.upper(),
                    "label": legacy.label,
                    "description": legacy.description,
                    "version": "1.0.0",
                    "niveaux": [legacy.niveau],
                    "exercise_type": "DYNAMIC",
                    "svg_mode": "AUTO"
                },
                defaults={},
                schema=[v.to_dict() for v in legacy.variables],
                presets=[]
            )
        
        available = get_generators_list()
        raise HTTPException(
            status_code=404,
            detail={
                "error": "generator_not_found",
                "message": f"Générateur '{generator_key}' non trouvé",
                "available": [g["key"] for g in available]
            }
        )
    
    return FactorySchemaResponse(**schema)


class FactoryGenerateRequest(BaseModel):
    """Request pour génération via Factory."""
    generator_key: str = Field(description="Clé du générateur")
    exercise_params: Optional[Dict[str, Any]] = Field(default=None, description="Paramètres stockés dans l'exercice")
    overrides: Optional[Dict[str, Any]] = Field(default=None, description="Overrides du prof")
    seed: Optional[int] = Field(default=None, description="Seed pour reproductibilité")
    enonce_template: Optional[str] = Field(default=None, description="Template HTML énoncé")
    solution_template: Optional[str] = Field(default=None, description="Template HTML solution")


class FactoryGenerateResponse(BaseModel):
    """Réponse de génération Factory."""
    success: bool
    variables: Dict[str, Any]
    geo_data: Dict[str, Any]
    figure_svg_enonce: Optional[str]
    figure_svg_solution: Optional[str]
    enonce_html: Optional[str]
    solution_html: Optional[str]
    generation_meta: Dict[str, Any]
    errors: List[str] = Field(default_factory=list)


@router.post("/generate-from-factory", response_model=FactoryGenerateResponse, tags=["Factory"])
async def generate_from_factory(request: FactoryGenerateRequest):
    """
    Génère un exercice via Dynamic Factory avec fusion des paramètres.
    
    Ordre de fusion: defaults < exercise_params < overrides
    
    Workflow:
    1. Récupère le générateur
    2. Fusionne defaults + exercise_params + overrides
    3. Valide les paramètres
    4. Génère l'exercice
    5. Rend les templates (si fournis)
    """
    logger.info(f"🏭 Factory generate: {request.generator_key}, seed={request.seed}")
    
    errors = []
    
    try:
        # Générer via Factory
        result = factory_generate(
            generator_key=request.generator_key,
            exercise_params=request.exercise_params,
            overrides=request.overrides,
            seed=request.seed
        )
        
        variables = result.get("variables", {})
        
        # Rendre les templates si fournis
        enonce_html = None
        solution_html = None
        
        if request.enonce_template:
            import re
            all_vars = {**variables, **result.get("results", {}), **result.get("geo_data", {})}
            enonce_html = render_template(request.enonce_template, all_vars)
            
            unreplaced = re.findall(r'\{\{(\w+)\}\}', enonce_html)
            for var in unreplaced:
                errors.append(f"Variable inconnue dans énoncé: {{{{{var}}}}}")
        
        if request.solution_template:
            import re
            all_vars = {**variables, **result.get("results", {}), **result.get("geo_data", {})}
            solution_html = render_template(request.solution_template, all_vars)
            
            unreplaced = re.findall(r'\{\{(\w+)\}\}', solution_html)
            for var in unreplaced:
                errors.append(f"Variable inconnue dans solution: {{{{{var}}}}}")
        
        return FactoryGenerateResponse(
            success=len(errors) == 0,
            variables=variables,
            geo_data=result.get("geo_data", {}),
            figure_svg_enonce=result.get("figure_svg_enonce"),
            figure_svg_solution=result.get("figure_svg_solution"),
            enonce_html=enonce_html,
            solution_html=solution_html,
            generation_meta=result.get("generation_meta", {}),
            errors=errors
        )
        
    except ValueError as e:
        logger.error(f"❌ Factory validation error: {str(e)}")
        raise HTTPException(status_code=400, detail={"error": "validation_failed", "message": str(e)})
    except Exception as e:
        logger.error(f"❌ Factory generate error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "generation_failed", "message": str(e)})


@router.post("/validate-params", tags=["Factory"])
async def validate_generator_params(generator_key: str, params: Dict[str, Any]):
    """
    Valide des paramètres pour un générateur sans générer.
    
    Utile pour la validation en temps réel dans l'admin.
    """
    valid, result = validate_exercise_params(generator_key, params)
    
    return {
        "valid": valid,
        "validated_params": result if valid else None,
        "errors": result if not valid else []
    }
