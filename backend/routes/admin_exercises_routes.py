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


class ChapterExerciseStatsResponse(BaseModel):
    """Statistiques des exercices d'un chapitre"""
    chapter_code: str
    total: int
    by_offer: dict
    by_difficulty: dict
    by_family: dict


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
    
    except Exception as e:
        logger.error(f"Erreur liste exercices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    service=Depends(get_exercise_service)
):
    """Crée un nouvel exercice"""
    logger.info(f"Admin: Création exercice dans {chapter_code}")
    
    try:
        exercise = await service.create_exercise(chapter_code, request)
        
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
    service=Depends(get_exercise_service)
):
    """Met à jour un exercice"""
    logger.info(f"Admin: Mise à jour exercice {chapter_code} #{exercise_id}")
    
    try:
        exercise = await service.update_exercise(chapter_code, exercise_id, request)
        
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
    response_model=ChapterExerciseStatsResponse,
    summary="Statistiques des exercices d'un chapitre"
)
async def get_exercise_stats(
    chapter_code: str,
    service=Depends(get_exercise_service)
):
    """Retourne les statistiques des exercices d'un chapitre"""
    stats = await service.get_stats(chapter_code)
    
    return ChapterExerciseStatsResponse(**stats)


@router.get(
    "/exercises/pilot-chapters",
    summary="Liste des chapitres pilotes avec exercices figés"
)
async def list_pilot_chapters():
    """Retourne la liste des chapitres pilotes supportés"""
    from models.exercise_types import get_all_exercise_types
    
    return {
        "pilot_chapters": [
            {
                "code": "6e_GM07",
                "name": "Durées et lecture de l'heure",
                "status": "production",
                "exercise_count": 20
            },
            {
                "code": "6e_GM08",
                "name": "Longueurs et périmètres",
                "status": "production",
                "exercise_count": 20
            }
        ],
        "families": ["CONVERSION", "COMPARAISON", "PERIMETRE", "PROBLEME", "DUREES", "LECTURE_HORLOGE"],
        "difficulties": ["facile", "moyen", "difficile"],
        "offers": ["free", "pro"],
        "exercise_types": get_all_exercise_types()
    }

