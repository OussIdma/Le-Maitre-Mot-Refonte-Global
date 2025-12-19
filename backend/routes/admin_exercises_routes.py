"""
Routes API admin pour la gestion des exercices figés.

Endpoints CRUD pour visualiser et modifier les exercices des chapitres pilotes.
Compatible avec les handlers GM07, GM08, etc.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.services.exercise_persistence_service import (
    ExerciseCreateRequest,
    ExerciseUpdateRequest,
    ExerciseResponse,
    get_exercise_persistence_service
)
from backend.services.curriculum_sync_service import get_curriculum_sync_service
from logger import get_logger

logger = get_logger()

# Router admin exercices
router = APIRouter(prefix="/api/admin", tags=["Admin Exercises"])


# =============================================================================
# MODÈLES DE RÉPONSE
# =============================================================================

class ExerciseListResponse(BaseModel):
    """Réponse pour la liste des exercices"""
    chapter_code: str
    total: int
    exercises: List[dict]
    stats: dict = {}


class ExerciseCRUDResponse(BaseModel):
    """Réponse pour les opérations CRUD"""
    success: bool
    message: str
    exercise: Optional[dict] = None


# =============================================================================
# DÉPENDANCES
# =============================================================================

async def get_db():
    """Dépendance pour obtenir la base de données"""
    from server import db
    return db


async def get_exercise_service(db=Depends(get_db)):
    """Dépendance pour obtenir le service de persistance"""
    return get_exercise_persistence_service(db)


async def get_curriculum_sync_service_dep(db=Depends(get_db)):
    """Dépendance pour obtenir le service de synchronisation curriculum"""
    return get_curriculum_sync_service(db)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "/chapters/{chapter_code}/exercises",
    response_model=ExerciseListResponse,
    summary="Lister les exercices d'un chapitre",
    description="""
    Retourne tous les exercices d'un chapitre pilote.
    Supporte les filtres par offre et difficulté.
    
    **Chapitres supportés:** 6e_GM07, 6e_GM08, 6e_TESTS_DYN
    """
)
async def list_exercises(
    chapter_code: str,
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    service=Depends(get_exercise_service)
):
    """Liste les exercices d'un chapitre"""
    logger.info(f"Admin: Liste des exercices pour {chapter_code}")
    
    try:
        exercises = await service.get_exercises(
            chapter_code=chapter_code,
            offer=offer,
            difficulty=difficulty
        )
        
        stats = await service.get_stats(chapter_code)
        
        return ExerciseListResponse(
            chapter_code=chapter_code.upper(),
            total=len(exercises),
            exercises=exercises,
            stats=stats
        )
    
    except ValueError as e:
        # Erreur de validation (ex: import Python échoué)
        logger.error(f"Erreur validation liste exercices {chapter_code}: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "EXERCISE_LOAD_ERROR",
                "error": "exercise_load_error",
                "message": str(e),
                "chapter_code": chapter_code,
                "hint": "Vérifiez que le fichier Python source existe et est valide."
            }
        )
    except Exception as e:
        # Erreur inattendue
        logger.error(f"Erreur liste exercices {chapter_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "error": "internal_server_error",
                "message": "Une erreur interne s'est produite lors de la récupération des exercices",
                "chapter_code": chapter_code,
                "hint": "Consultez les logs backend pour plus de détails."
            }
        )


@router.get(
    "/chapters/{chapter_code}/exercises/{exercise_id}",
    summary="Récupérer un exercice spécifique"
)
async def get_exercise(
    chapter_code: str,
    exercise_id: int,
    service=Depends(get_exercise_service)
):
    """Récupère un exercice par son ID"""
    exercise = await service.get_exercise_by_id(chapter_code, exercise_id)
    
    if not exercise:
        raise HTTPException(
            status_code=404,
            detail=f"Exercice #{exercise_id} non trouvé dans {chapter_code}"
        )
    
    return exercise


@router.post(
    "/chapters/{chapter_code}/exercises",
    response_model=ExerciseCRUDResponse,
    summary="Créer un nouvel exercice",
    description="""
    Crée un nouvel exercice dans un chapitre pilote.
    
    **Contraintes:**
    - Contenu en HTML pur (pas de LaTeX, pas de Markdown)
    - Solution en 4 étapes (structure <ol><li>...)
    - Difficulté: facile, moyen, difficile
    - Offer: free, pro
    """
)
async def create_exercise(
    chapter_code: str,
    request: ExerciseCreateRequest,
    service=Depends(get_exercise_service),
    sync_service=Depends(get_curriculum_sync_service_dep)
):
    """Crée un nouvel exercice et synchronise automatiquement le chapitre dans le curriculum"""
    logger.info(f"Admin: Création exercice dans {chapter_code}")
    
    try:
        # Créer l'exercice
        exercise = await service.create_exercise(chapter_code, request)
        
        # Synchroniser automatiquement le chapitre dans le curriculum
        try:
            sync_result = await sync_service.sync_chapter_to_curriculum(chapter_code)
            if sync_result['created']:
                logger.info(f"[AUTO-SYNC] Chapitre {chapter_code} créé automatiquement dans le curriculum")
            elif sync_result['updated']:
                logger.info(f"[AUTO-SYNC] Chapitre {chapter_code} mis à jour dans le curriculum")
        except Exception as sync_error:
            # Ne pas faire échouer la création d'exercice si la sync échoue
            logger.warning(
                f"[AUTO-SYNC] Échec synchronisation curriculum pour {chapter_code}: {sync_error}. "
                "L'exercice a été créé mais le chapitre n'est pas synchronisé."
            )
        
        return ExerciseCRUDResponse(
            success=True,
            message=f"Exercice #{exercise['id']} créé avec succès",
            exercise=exercise
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur création exercice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/chapters/{chapter_code}/exercises/{exercise_id}",
    response_model=ExerciseCRUDResponse,
    summary="Modifier un exercice",
    description="Met à jour un exercice existant. Seuls les champs fournis sont modifiés."
)
async def update_exercise(
    chapter_code: str,
    exercise_id: int,
    request: ExerciseUpdateRequest,
    service=Depends(get_exercise_service),
    sync_service=Depends(get_curriculum_sync_service_dep)
):
    """Met à jour un exercice et synchronise automatiquement le chapitre dans le curriculum"""
    logger.info(f"Admin: Mise à jour exercice {chapter_code} #{exercise_id}")
    
    try:
        # Mettre à jour l'exercice
        exercise = await service.update_exercise(chapter_code, exercise_id, request)
        
        # Synchroniser automatiquement le chapitre dans le curriculum
        try:
            sync_result = await sync_service.sync_chapter_to_curriculum(chapter_code)
            if sync_result['created']:
                logger.info(f"[AUTO-SYNC] Chapitre {chapter_code} créé automatiquement dans le curriculum")
            elif sync_result['updated']:
                logger.info(f"[AUTO-SYNC] Chapitre {chapter_code} mis à jour dans le curriculum")
        except Exception as sync_error:
            # Ne pas faire échouer la mise à jour d'exercice si la sync échoue
            logger.warning(
                f"[AUTO-SYNC] Échec synchronisation curriculum pour {chapter_code}: {sync_error}. "
                "L'exercice a été mis à jour mais le chapitre n'est pas synchronisé."
            )
        
        return ExerciseCRUDResponse(
            success=True,
            message=f"Exercice #{exercise_id} mis à jour avec succès",
            exercise=exercise
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur mise à jour exercice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/chapters/{chapter_code}/exercises/{exercise_id}",
    response_model=ExerciseCRUDResponse,
    summary="Supprimer un exercice",
    description="Supprime définitivement un exercice. Cette action est irréversible."
)
async def delete_exercise(
    chapter_code: str,
    exercise_id: int,
    service=Depends(get_exercise_service)
):
    """Supprime un exercice"""
    logger.info(f"Admin: Suppression exercice {chapter_code} #{exercise_id}")
    
    try:
        deleted = await service.delete_exercise(chapter_code, exercise_id)
        
        if deleted:
            return ExerciseCRUDResponse(
                success=True,
                message=f"Exercice #{exercise_id} supprimé avec succès",
                exercise=None
            )
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la suppression")
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur suppression exercice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/chapters/{chapter_code}/exercises/stats",
    summary="Statistiques des exercices d'un chapitre"
)
async def get_exercise_stats(
    chapter_code: str,
    service=Depends(get_exercise_service)
):
    """Retourne les statistiques des exercices d'un chapitre"""
    stats = await service.get_stats(chapter_code)
    return stats


@router.post(
    "/chapters/{chapter_code}/sync-curriculum",
    summary="Forcer la synchronisation du chapitre dans le curriculum",
    description="""
    Force la synchronisation d'un chapitre depuis la collection exercises 
    vers le référentiel curriculum. Utile pour corriger un chapitre "indisponible".
    
    Extrait automatiquement les exercise_types depuis les exercices (dynamiques via generator_key,
    statiques via exercise_type) et crée/met à jour le chapitre dans le curriculum.
    """
)
async def sync_chapter_to_curriculum_endpoint(
    chapter_code: str,
    sync_service=Depends(get_curriculum_sync_service_dep)
):
    """Force la synchronisation d'un chapitre dans le curriculum"""
    logger.info(f"Admin: Synchronisation manuelle du chapitre {chapter_code}")
    
    try:
        result = await sync_service.sync_chapter_to_curriculum(chapter_code)
        
        return {
            "success": True,
            "message": f"Chapitre {chapter_code} synchronisé avec succès",
            "created": result['created'],
            "updated": result['updated'],
            "exercise_types": result['exercise_types']
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur synchronisation chapitre: {e}")
        raise HTTPException(status_code=500, detail=str(e))
