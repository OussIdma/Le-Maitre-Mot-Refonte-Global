"""
Routes admin pour la gestion des exercices statiques (P1.5 - Partie 2/3)

Permet de lister, créer, modifier et supprimer des exercices statiques (figés).
Les exercices statiques sont ceux avec is_dynamic=False.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.observability.logger import get_logger

router = APIRouter(prefix="/api/v1/admin", tags=["admin-static-exercises"])
obs_logger = get_logger()

# =============================================================================
# MODÈLES PYDANTIC
# =============================================================================

class StaticExerciseResponse(BaseModel):
    """Réponse pour un exercice statique"""
    id: int = Field(..., description="ID de l'exercice")
    chapter_code: str = Field(..., description="Code du chapitre (ex: 6e_GM07)")
    title: Optional[str] = Field(None, description="Titre de l'exercice")
    difficulty: str = Field(..., description="Difficulté: facile, moyen, difficile")
    enonce_html: str = Field(..., description="Énoncé HTML")
    solution_html: str = Field(..., description="Solution HTML")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags optionnels")
    order: Optional[int] = Field(None, description="Ordre d'affichage dans le chapitre")
    exercise_type: Optional[str] = Field(None, description="Type d'exercice")
    offer: str = Field(default="free", description="Offre: free ou pro")
    updated_at: Optional[datetime] = Field(None, description="Date de dernière mise à jour")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "chapter_code": "6e_GM07",
                "title": "Lecture de l'heure - 8h30",
                "difficulty": "facile",
                "enonce_html": "<p>Quelle heure indique l'horloge ?</p>",
                "solution_html": "<p><strong>Réponse :</strong> 8h30</p>",
                "tags": ["horloge", "lecture"],
                "order": 1,
                "offer": "free",
                "updated_at": "2025-12-23T10:30:00Z"
            }
        }


class StaticExerciseUpdate(BaseModel):
    """Modèle pour la mise à jour d'un exercice statique"""
    title: Optional[str] = Field(None, max_length=200, description="Titre de l'exercice")
    difficulty: Optional[str] = Field(None, description="Difficulté: facile, moyen, difficile")
    enonce_html: Optional[str] = Field(None, max_length=10000, description="Énoncé HTML")
    solution_html: Optional[str] = Field(None, max_length=10000, description="Solution HTML")
    tags: Optional[List[str]] = Field(None, description="Tags")
    order: Optional[int] = Field(None, ge=0, description="Ordre d'affichage")
    exercise_type: Optional[str] = Field(None, max_length=100, description="Type d'exercice")
    offer: Optional[str] = Field(None, description="Offre: free ou pro")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Lecture de l'heure - 8h30 (modifié)",
                "enonce_html": "<p>Quelle heure indique l'horloge ci-dessous ?</p>",
                "solution_html": "<p><strong>Réponse :</strong> Il est 8 heures 30 minutes.</p>",
                "tags": ["horloge", "lecture", "matin"],
                "order": 1
            }
        }


class StaticExerciseCreate(BaseModel):
    """Modèle pour la création d'un exercice statique"""
    title: Optional[str] = Field(None, max_length=200, description="Titre de l'exercice")
    difficulty: str = Field("facile", description="Difficulté: facile, moyen, difficile")
    enonce_html: str = Field("<p>Énoncé à compléter...</p>", max_length=10000, description="Énoncé HTML")
    solution_html: str = Field("<p>Solution à compléter...</p>", max_length=10000, description="Solution HTML")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags")
    order: Optional[int] = Field(None, ge=0, description="Ordre d'affichage")
    exercise_type: Optional[str] = Field(None, max_length=100, description="Type d'exercice")
    offer: str = Field("free", description="Offre: free ou pro")


# =============================================================================
# HELPER: Obtenir le service de persistance
# =============================================================================

def get_exercise_service():
    """
    Dépendance pour obtenir le service de persistance des exercices.
    
    Note: Le service est chargé paresseusement pour éviter les imports circulaires.
    """
    from backend.server import db
    from backend.services.exercise_persistence_service import ExercisePersistenceService
    
    return ExercisePersistenceService(db)


# =============================================================================
# ROUTES
# =============================================================================

@router.get("/chapters/{code_officiel}/static-exercises", response_model=List[StaticExerciseResponse])
async def list_static_exercises_by_chapter(
    code_officiel: str,
    service = Depends(get_exercise_service)
):
    """
    Liste tous les exercices STATIQUES d'un chapitre.
    
    Filtre:
    - is_dynamic = False (ou generator_key absent/null)
    - chapter_code = code_officiel
    
    Tri:
    - Par `order` si défini, sinon par `id`
    
    Args:
        code_officiel: Code du chapitre (ex: 6e_GM07)
    
    Returns:
        Liste des exercices statiques
    
    Raises:
        HTTPException 404: Si le chapitre n'existe pas ou n'a pas d'exercices statiques
    """
    try:
        obs_logger.info(
            f"[ADMIN] Liste exercices statiques pour {code_officiel}",
            chapter_code=code_officiel
        )
        
        # Récupérer les exercices du chapitre
        all_exercises = await service.get_all_by_chapter(code_officiel)
        
        # Filtrer les exercices statiques (is_dynamic=False ou absent)
        static_exercises = [
            ex for ex in all_exercises
            if not ex.get("is_dynamic", False) and not ex.get("generator_key")
        ]
        
        # Trier par order puis id
        static_exercises.sort(key=lambda ex: (ex.get("order") or 999999, ex.get("id", 0)))
        
        # Convertir au format de réponse
        results = []
        for ex in static_exercises:
            results.append(StaticExerciseResponse(
                id=ex.get("id"),
                chapter_code=ex.get("chapter_code"),
                title=ex.get("title"),
                difficulty=ex.get("difficulty", "facile"),
                enonce_html=ex.get("enonce_html", ""),
                solution_html=ex.get("solution_html", ""),
                tags=ex.get("tags", []),
                order=ex.get("order"),
                exercise_type=ex.get("exercise_type"),
                offer=ex.get("offer", "free"),
                updated_at=ex.get("updated_at")
            ))
        
        obs_logger.info(
            f"[ADMIN] {len(results)} exercices statiques trouvés",
            chapter_code=code_officiel,
            count=len(results)
        )
        
        return results
        
    except Exception as e:
        obs_logger.error(
            f"[ADMIN] Erreur liste exercices statiques: {str(e)}",
            chapter_code=code_officiel,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": f"Erreur lors de la récupération des exercices: {str(e)}",
                "chapter_code": code_officiel
            }
        )


@router.put("/static-exercises/{exercise_id}", response_model=StaticExerciseResponse)
async def update_static_exercise(
    exercise_id: int,
    update_data: StaticExerciseUpdate,
    service = Depends(get_exercise_service)
):
    """
    Met à jour un exercice STATIQUE.
    
    Sécurité:
    - Refuse de modifier un exercice dynamique (is_dynamic=True)
    - Valide que l'exercice existe
    
    Args:
        exercise_id: ID de l'exercice à modifier
        update_data: Données à mettre à jour
    
    Returns:
        Exercice mis à jour
    
    Raises:
        HTTPException 404: Si l'exercice n'existe pas
        HTTPException 400: Si tentative de modification d'un exercice dynamique
        HTTPException 422: Si données invalides
    """
    try:
        obs_logger.info(
            f"[ADMIN] Mise à jour exercice statique {exercise_id}",
            exercise_id=exercise_id
        )
        
        # Récupérer l'exercice existant
        existing = await service.get_by_id(exercise_id)
        
        if not existing:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "EXERCISE_NOT_FOUND",
                    "message": f"Exercice {exercise_id} introuvable",
                    "exercise_id": exercise_id
                }
            )
        
        # Vérifier que c'est un exercice statique
        if existing.get("is_dynamic") or existing.get("generator_key"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "CANNOT_UPDATE_DYNAMIC_VIA_STATIC_ENDPOINT",
                    "message": f"L'exercice {exercise_id} est dynamique. Utilisez l'endpoint dédié.",
                    "exercise_id": exercise_id,
                    "is_dynamic": existing.get("is_dynamic"),
                    "generator_key": existing.get("generator_key"),
                    "hint": "Utilisez /api/v1/admin/exercises/{id} pour modifier les exercices dynamiques"
                }
            )
        
        # Valider les champs si fournis
        if update_data.difficulty and update_data.difficulty not in ["facile", "moyen", "difficile"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "INVALID_DIFFICULTY",
                    "message": f"Difficulté invalide: {update_data.difficulty}",
                    "valid_values": ["facile", "moyen", "difficile"]
                }
            )
        
        if update_data.offer and update_data.offer not in ["free", "pro"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "INVALID_OFFER",
                    "message": f"Offre invalide: {update_data.offer}",
                    "valid_values": ["free", "pro"]
                }
            )
        
        # Préparer les données de mise à jour (ne mettre que les champs fournis)
        update_dict = {}
        if update_data.title is not None:
            update_dict["title"] = update_data.title
        if update_data.difficulty is not None:
            update_dict["difficulty"] = update_data.difficulty
        if update_data.enonce_html is not None:
            update_dict["enonce_html"] = update_data.enonce_html
        if update_data.solution_html is not None:
            update_dict["solution_html"] = update_data.solution_html
        if update_data.tags is not None:
            update_dict["tags"] = update_data.tags
        if update_data.order is not None:
            update_dict["order"] = update_data.order
        if update_data.exercise_type is not None:
            update_dict["exercise_type"] = update_data.exercise_type
        if update_data.offer is not None:
            update_dict["offer"] = update_data.offer
        
        # Ajouter updated_at
        update_dict["updated_at"] = datetime.utcnow()
        
        # Mettre à jour en base
        updated_exercise = await service.update(exercise_id, update_dict)
        
        if not updated_exercise:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "UPDATE_FAILED",
                    "message": f"La mise à jour de l'exercice {exercise_id} a échoué",
                    "exercise_id": exercise_id
                }
            )
        
        obs_logger.info(
            f"[ADMIN] Exercice statique {exercise_id} mis à jour",
            exercise_id=exercise_id,
            fields_updated=list(update_dict.keys())
        )
        
        # Retourner la réponse formatée
        return StaticExerciseResponse(
            id=updated_exercise.get("id"),
            chapter_code=updated_exercise.get("chapter_code"),
            title=updated_exercise.get("title"),
            difficulty=updated_exercise.get("difficulty", "facile"),
            enonce_html=updated_exercise.get("enonce_html", ""),
            solution_html=updated_exercise.get("solution_html", ""),
            tags=updated_exercise.get("tags", []),
            order=updated_exercise.get("order"),
            exercise_type=updated_exercise.get("exercise_type"),
            offer=updated_exercise.get("offer", "free"),
            updated_at=updated_exercise.get("updated_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        obs_logger.error(
            f"[ADMIN] Erreur mise à jour exercice statique: {str(e)}",
            exercise_id=exercise_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": f"Erreur lors de la mise à jour: {str(e)}",
                "exercise_id": exercise_id
            }
        )


@router.post("/chapters/{code_officiel}/static-exercises", response_model=StaticExerciseResponse, status_code=201)
async def create_static_exercise(
    code_officiel: str,
    create_data: StaticExerciseCreate,
    service = Depends(get_exercise_service)
):
    """
    Crée un nouvel exercice STATIQUE dans un chapitre.
    
    L'exercice créé contient du contenu minimal/template que l'admin devra compléter.
    
    Args:
        code_officiel: Code du chapitre (ex: 6e_GM07)
        create_data: Données de l'exercice à créer
    
    Returns:
        Exercice créé
    
    Raises:
        HTTPException 422: Si données invalides
    """
    try:
        obs_logger.info(
            f"[ADMIN] Création exercice statique dans {code_officiel}",
            chapter_code=code_officiel
        )
        
        # Valider difficulty
        if create_data.difficulty not in ["facile", "moyen", "difficile"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "INVALID_DIFFICULTY",
                    "message": f"Difficulté invalide: {create_data.difficulty}",
                    "valid_values": ["facile", "moyen", "difficile"]
                }
            )
        
        # Valider offer
        if create_data.offer not in ["free", "pro"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "INVALID_OFFER",
                    "message": f"Offre invalide: {create_data.offer}",
                    "valid_values": ["free", "pro"]
                }
            )
        
        # Préparer les données pour la création
        exercise_dict = {
            "chapter_code": code_officiel,
            "title": create_data.title,
            "difficulty": create_data.difficulty,
            "enonce_html": create_data.enonce_html,
            "solution_html": create_data.solution_html,
            "tags": create_data.tags,
            "order": create_data.order,
            "exercise_type": create_data.exercise_type,
            "offer": create_data.offer,
            "is_dynamic": False,  # IMPORTANT: Marquer comme statique
            "needs_svg": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Créer en base
        created_exercise = await service.create(exercise_dict)
        
        if not created_exercise:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "CREATE_FAILED",
                    "message": f"La création de l'exercice a échoué",
                    "chapter_code": code_officiel
                }
            )
        
        obs_logger.info(
            f"[ADMIN] Exercice statique créé: {created_exercise.get('id')}",
            chapter_code=code_officiel,
            exercise_id=created_exercise.get("id")
        )
        
        # Retourner la réponse formatée
        return StaticExerciseResponse(
            id=created_exercise.get("id"),
            chapter_code=created_exercise.get("chapter_code"),
            title=created_exercise.get("title"),
            difficulty=created_exercise.get("difficulty", "facile"),
            enonce_html=created_exercise.get("enonce_html", ""),
            solution_html=created_exercise.get("solution_html", ""),
            tags=created_exercise.get("tags", []),
            order=created_exercise.get("order"),
            exercise_type=created_exercise.get("exercise_type"),
            offer=created_exercise.get("offer", "free"),
            updated_at=created_exercise.get("updated_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        obs_logger.error(
            f"[ADMIN] Erreur création exercice statique: {str(e)}",
            chapter_code=code_officiel,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": f"Erreur lors de la création: {str(e)}",
                "chapter_code": code_officiel
            }
        )


@router.delete("/static-exercises/{exercise_id}", status_code=204)
async def delete_static_exercise(
    exercise_id: int,
    service = Depends(get_exercise_service)
):
    """
    Supprime un exercice STATIQUE.
    
    Sécurité:
    - Refuse de supprimer un exercice dynamique (is_dynamic=True)
    - Valide que l'exercice existe
    
    Args:
        exercise_id: ID de l'exercice à supprimer
    
    Raises:
        HTTPException 404: Si l'exercice n'existe pas
        HTTPException 400: Si tentative de suppression d'un exercice dynamique
    """
    try:
        obs_logger.info(
            f"[ADMIN] Suppression exercice statique {exercise_id}",
            exercise_id=exercise_id
        )
        
        # Récupérer l'exercice existant
        existing = await service.get_by_id(exercise_id)
        
        if not existing:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "EXERCISE_NOT_FOUND",
                    "message": f"Exercice {exercise_id} introuvable",
                    "exercise_id": exercise_id
                }
            )
        
        # Vérifier que c'est un exercice statique
        if existing.get("is_dynamic") or existing.get("generator_key"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "CANNOT_DELETE_DYNAMIC_VIA_STATIC_ENDPOINT",
                    "message": f"L'exercice {exercise_id} est dynamique. Utilisez l'endpoint dédié.",
                    "exercise_id": exercise_id,
                    "is_dynamic": existing.get("is_dynamic"),
                    "generator_key": existing.get("generator_key"),
                    "hint": "Utilisez /api/v1/admin/exercises/{id} pour supprimer les exercices dynamiques"
                }
            )
        
        # Supprimer
        deleted = await service.delete(exercise_id)
        
        if not deleted:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "DELETE_FAILED",
                    "message": f"La suppression de l'exercice {exercise_id} a échoué",
                    "exercise_id": exercise_id
                }
            )
        
        obs_logger.info(
            f"[ADMIN] Exercice statique {exercise_id} supprimé",
            exercise_id=exercise_id
        )
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        obs_logger.error(
            f"[ADMIN] Erreur suppression exercice statique: {str(e)}",
            exercise_id=exercise_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": f"Erreur lors de la suppression: {str(e)}",
                "exercise_id": exercise_id
            }
        )

