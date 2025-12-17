"""
Routes API admin pour la gestion du curriculum.

Endpoints CRUD pour visualiser et modifier le référentiel pédagogique.
Protection par flag d'environnement ADMIN_ENABLED.

V2: Ajout des fonctionnalités d'édition (POST, PUT, DELETE)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel, Field
import os

from curriculum.loader import (
    get_curriculum_index,
    CurriculumChapter,
    validate_curriculum
)
from backend.services.curriculum_persistence_service import (
    ChapterCreateRequest,
    ChapterUpdateRequest,
    get_curriculum_persistence_service
)
from logger import get_logger

logger = get_logger()

# Router admin
router = APIRouter(prefix="/api/admin", tags=["Admin Curriculum"])


# ============================================================================
# MODÈLES DE RÉPONSE
# ============================================================================

class AdminChapterResponse(BaseModel):
    """Représentation d'un chapitre pour l'admin"""
    code_officiel: str
    domaine: str
    libelle: str
    generateurs: List[str]
    has_diagramme: bool
    statut: str
    chapitre_backend: str
    tags: List[str] = []
    difficulte_min: int = 1
    difficulte_max: int = 3
    schema_requis: bool = False


class AdminCurriculumResponse(BaseModel):
    """Réponse complète du curriculum pour l'admin"""
    niveau: str
    total_chapitres: int
    chapitres: List[AdminChapterResponse]
    stats: dict = {}


class AdminValidationResponse(BaseModel):
    """Réponse de validation du curriculum"""
    valid: bool
    total_chapters: int
    chapters_with_generators: int
    chapters_without_generators: int
    chapters_by_status: dict
    chapters_by_domaine: dict
    warnings: List[str] = []


class ChapterCRUDResponse(BaseModel):
    """Réponse pour les opérations CRUD"""
    success: bool
    message: str
    chapter: Optional[AdminChapterResponse] = None


class AvailableOptionsResponse(BaseModel):
    """Options disponibles pour le formulaire d'édition"""
    generators: List[str]
    domaines: List[str]
    statuts: List[str] = ["prod", "beta", "hidden"]


# ============================================================================
# HELPERS
# ============================================================================

# Générateurs qui produisent des schémas/diagrammes SVG
GENERATORS_WITH_DIAGRAMS = {
    "FRACTION_REPRESENTATION",
    "FRACTION_DROITE",
    "DROITE_GRADUEE_ENTIERS",
    "DROITE_GRADUEE_DECIMAUX",
    "TRIANGLE_QUELCONQUE",
    "TRIANGLE_CONSTRUCTION",
    "TRIANGLE_RECTANGLE",
    "RECTANGLE",
    "CERCLE",
    "QUADRILATERES",
    "PERIMETRE_AIRE",
    "AIRE_TRIANGLE",
    "AIRE_FIGURES_COMPOSEES",
    "VOLUME",
    "VOLUME_PAVE",
    "SYMETRIE_AXIALE",
    "SYMETRIE_CENTRALE",
    "SYMETRIE_PROPRIETES",
    "DIAGRAMME_BARRES",
    "DIAGRAMME_CIRCULAIRE",
    "PROP_TABLEAU",
    "TABLEAU_LECTURE",
    "TABLEAU_COMPLETER",
}


def has_diagram_generator(exercise_types: List[str]) -> bool:
    """Détermine si un chapitre a des générateurs produisant des schémas"""
    for et in exercise_types:
        if et in GENERATORS_WITH_DIAGRAMS:
            return True
    return False


def check_admin_enabled():
    """
    Vérifie que l'admin est activé via la variable d'environnement.
    Retourne True si ADMIN_ENABLED=true, sinon lève une exception 403.
    """
    admin_enabled = os.environ.get("ADMIN_ENABLED", "true").lower()
    
    # Pour la V1, on autorise par défaut (lecture seule)
    if admin_enabled not in ("true", "1", "yes"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "admin_disabled",
                "message": "L'accès admin est désactivé. Définir ADMIN_ENABLED=true pour activer."
            }
        )
    return True


def chapter_to_response(chapter: dict) -> AdminChapterResponse:
    """Convertit un chapitre dict en AdminChapterResponse"""
    exercise_types = chapter.get("exercise_types", [])
    
    return AdminChapterResponse(
        code_officiel=chapter.get("code_officiel", ""),
        domaine=chapter.get("domaine", ""),
        libelle=chapter.get("libelle", ""),
        generateurs=exercise_types,
        has_diagramme=has_diagram_generator(exercise_types),
        statut=chapter.get("statut", "beta"),
        chapitre_backend=chapter.get("chapitre_backend", ""),
        tags=chapter.get("tags", []),
        difficulte_min=chapter.get("difficulte_min", 1),
        difficulte_max=chapter.get("difficulte_max", 3),
        schema_requis=chapter.get("schema_requis", False)
    )


# ============================================================================
# DEPENDENCY - Database injection
# ============================================================================

async def get_db():
    """Dépendance pour obtenir la base de données"""
    from server import db
    return db


async def get_persistence_service(db=Depends(get_db)):
    """Dépendance pour obtenir le service de persistance"""
    return get_curriculum_persistence_service(db)


# ============================================================================
# ENDPOINTS READ (V1)
# ============================================================================

@router.get(
    "/curriculum/6e",
    response_model=AdminCurriculumResponse,
    summary="Récupérer le référentiel curriculum 6e",
    description="""
    Endpoint READ-ONLY qui retourne tous les chapitres du référentiel 6e
    avec leurs générateurs associés.
    
    **Accès** : Nécessite ADMIN_ENABLED=true (activé par défaut pour V1)
    """
)
async def get_curriculum_6e(admin_check: bool = Depends(check_admin_enabled)):
    """
    Retourne le référentiel curriculum 6e complet.
    """
    logger.info("Admin: Récupération du curriculum 6e")
    
    try:
        index = get_curriculum_index()
        
        chapitres = []
        for code, chapter in sorted(index.by_official_code.items()):
            if chapter.niveau != "6e":
                continue
                
            chapitres.append(AdminChapterResponse(
                code_officiel=chapter.code_officiel,
                domaine=chapter.domaine,
                libelle=chapter.libelle,
                generateurs=chapter.exercise_types,
                has_diagramme=has_diagram_generator(chapter.exercise_types),
                statut=chapter.statut,
                chapitre_backend=chapter.chapitre_backend,
                tags=chapter.tags,
                difficulte_min=chapter.difficulte_min,
                difficulte_max=chapter.difficulte_max,
                schema_requis=chapter.schema_requis
            ))
        
        # Statistiques
        stats = {
            "total": len(chapitres),
            "with_diagrams": sum(1 for c in chapitres if c.has_diagramme),
            "by_domaine": {},
            "by_status": {}
        }
        
        for ch in chapitres:
            stats["by_domaine"][ch.domaine] = stats["by_domaine"].get(ch.domaine, 0) + 1
            stats["by_status"][ch.statut] = stats["by_status"].get(ch.statut, 0) + 1
        
        logger.info(f"Admin: {len(chapitres)} chapitres 6e retournés")
        
        return AdminCurriculumResponse(
            niveau="6e",
            total_chapitres=len(chapitres),
            chapitres=chapitres,
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Admin: Erreur récupération curriculum 6e: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération du curriculum: {str(e)}"
        )


@router.get(
    "/curriculum/6e/validate",
    response_model=AdminValidationResponse,
    summary="Valider le référentiel curriculum 6e",
    description="Endpoint de diagnostic qui valide le curriculum et retourne un rapport."
)
async def validate_curriculum_6e(admin_check: bool = Depends(check_admin_enabled)):
    """
    Valide le curriculum 6e et retourne un rapport de diagnostic.
    """
    logger.info("Admin: Validation du curriculum 6e")
    
    try:
        report = validate_curriculum()
        
        return AdminValidationResponse(
            valid=len(report.get("warnings", [])) == 0,
            total_chapters=report["total_chapters"],
            chapters_with_generators=report["chapters_with_generators"],
            chapters_without_generators=report["chapters_without_generators"],
            chapters_by_status=report["chapters_by_status"],
            chapters_by_domaine=report["chapters_by_domaine"],
            warnings=report.get("warnings", [])
        )
        
    except Exception as e:
        logger.error(f"Admin: Erreur validation curriculum: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la validation: {str(e)}"
        )


@router.get(
    "/curriculum/6e/{code_officiel}",
    response_model=AdminChapterResponse,
    summary="Récupérer un chapitre spécifique",
    description="Retourne les détails d'un chapitre par son code officiel."
)
async def get_chapter_by_code(
    code_officiel: str,
    admin_check: bool = Depends(check_admin_enabled)
):
    """
    Retourne les détails d'un chapitre spécifique.
    """
    from curriculum.loader import get_chapter_by_official_code
    
    chapter = get_chapter_by_official_code(code_officiel)
    
    if not chapter:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "chapter_not_found",
                "message": f"Le code officiel '{code_officiel}' n'existe pas."
            }
        )
    
    return AdminChapterResponse(
        code_officiel=chapter.code_officiel,
        domaine=chapter.domaine,
        libelle=chapter.libelle,
        generateurs=chapter.exercise_types,
        has_diagramme=has_diagram_generator(chapter.exercise_types),
        statut=chapter.statut,
        chapitre_backend=chapter.chapitre_backend,
        tags=chapter.tags,
        difficulte_min=chapter.difficulte_min,
        difficulte_max=chapter.difficulte_max,
        schema_requis=chapter.schema_requis
    )


@router.get(
    "/curriculum/stats",
    summary="Statistiques globales du curriculum",
    description="Retourne des statistiques globales sur tous les niveaux disponibles."
)
async def get_curriculum_stats_endpoint(admin_check: bool = Depends(check_admin_enabled)):
    """
    Retourne des statistiques globales.
    """
    report = validate_curriculum()
    
    return {
        "niveaux_disponibles": ["6e"],  # Pour l'instant uniquement 6e
        "total_chapitres_6e": report["total_chapters"],
        "chapitres_avec_generateurs": report["chapters_with_generators"],
        "repartition_domaines": report["chapters_by_domaine"],
        "repartition_statuts": report["chapters_by_status"]
    }


# ============================================================================
# ENDPOINTS CRUD (V2)
# ============================================================================

@router.get(
    "/curriculum/options",
    response_model=AvailableOptionsResponse,
    summary="Options disponibles pour l'édition",
    description="Retourne les listes de générateurs, domaines et statuts disponibles."
)
async def get_available_options(
    admin_check: bool = Depends(check_admin_enabled),
    service=Depends(get_persistence_service)
):
    """
    Récupère les options disponibles pour le formulaire d'édition.
    """
    generators = await service.get_available_generators()
    domaines = await service.get_available_domaines()
    
    return AvailableOptionsResponse(
        generators=generators,
        domaines=domaines if domaines else [
            "Nombres et calculs",
            "Géométrie",
            "Grandeurs et mesures",
            "Organisation et gestion de données"
        ],
        statuts=["prod", "beta", "hidden"]
    )


@router.post(
    "/curriculum/6e/chapters",
    response_model=ChapterCRUDResponse,
    summary="Créer un nouveau chapitre",
    description="""
    Crée un nouveau chapitre dans le référentiel 6e.
    Le code_officiel doit être unique.
    """
)
async def create_chapter(
    request: ChapterCreateRequest,
    admin_check: bool = Depends(check_admin_enabled),
    service=Depends(get_persistence_service)
):
    """
    Crée un nouveau chapitre dans le curriculum.
    """
    logger.info(f"Admin: Création du chapitre {request.code_officiel}")
    
    try:
        chapter = await service.create_chapter(request)
        
        return ChapterCRUDResponse(
            success=True,
            message=f"Chapitre '{request.code_officiel}' créé avec succès",
            chapter=chapter_to_response(chapter)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation_error",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Admin: Erreur création chapitre: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la création: {str(e)}"
        )


@router.put(
    "/curriculum/6e/chapters/{code_officiel}",
    response_model=ChapterCRUDResponse,
    summary="Mettre à jour un chapitre",
    description="""
    Met à jour un chapitre existant.
    Seuls les champs fournis sont mis à jour.
    """
)
async def update_chapter(
    code_officiel: str,
    request: ChapterUpdateRequest,
    admin_check: bool = Depends(check_admin_enabled),
    service=Depends(get_persistence_service)
):
    """
    Met à jour un chapitre existant.
    """
    logger.info(f"Admin: Mise à jour du chapitre {code_officiel}")
    
    try:
        chapter = await service.update_chapter(code_officiel, request)
        
        return ChapterCRUDResponse(
            success=True,
            message=f"Chapitre '{code_officiel}' mis à jour avec succès",
            chapter=chapter_to_response(chapter)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "not_found",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Admin: Erreur mise à jour chapitre: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


@router.delete(
    "/curriculum/6e/chapters/{code_officiel}",
    response_model=ChapterCRUDResponse,
    summary="Supprimer un chapitre",
    description="""
    Supprime définitivement un chapitre du référentiel.
    Cette action est irréversible.
    """
)
async def delete_chapter(
    code_officiel: str,
    admin_check: bool = Depends(check_admin_enabled),
    service=Depends(get_persistence_service)
):
    """
    Supprime un chapitre du curriculum.
    """
    logger.info(f"Admin: Suppression du chapitre {code_officiel}")
    
    try:
        deleted = await service.delete_chapter(code_officiel)
        
        if deleted:
            return ChapterCRUDResponse(
                success=True,
                message=f"Chapitre '{code_officiel}' supprimé avec succès",
                chapter=None
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Erreur lors de la suppression"
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "not_found",
                "message": str(e)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin: Erreur suppression chapitre: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )
