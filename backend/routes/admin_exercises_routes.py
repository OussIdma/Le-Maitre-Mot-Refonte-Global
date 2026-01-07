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
from backend.services.collection_guard_rails import check_collection_typos
from backend.curriculum.loader import get_chapter_by_official_code
from backend.logger import get_logger
from typing import Literal

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


class ExerciseImportPayload(BaseModel):
    """Payload pour importer une liste d'exercices dans un chapitre."""
    pipeline: Optional[Literal["SPEC", "TEMPLATE", "MIXED"]] = Field(
        default=None,
        description="Pipeline attendu pour validation (optionnel)."
    )
    exercises: List[dict] = Field(default_factory=list, description="Exercices à importer")


# =============================================================================
# DÉPENDANCES
# =============================================================================

async def get_db():
    """Dépendance pour obtenir la base de données"""
    from backend.server import app, db
    # Si app.state.db est défini (pour les tests), l'utiliser
    if hasattr(app.state, 'db') and app.state.db is not None:
        return app.state.db
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
    "/exercises/pilot-chapters",
    summary="Liste des chapitres pilotes",
    description="Retourne la liste des chapitres pilotes (GM07, GM08, TESTS_DYN) avec leurs types d'exercices"
)
async def get_pilot_chapters(service=Depends(get_exercise_service)):
    """Retourne la liste des chapitres pilotes"""
    from backend.services.exercise_persistence_service import ExercisePersistenceService
    
    pilot_chapters = []
    exercise_types = set()
    
    for chapter_code in ExercisePersistenceService.PILOT_CHAPTERS:
        try:
            exercises = await service.get_exercises(chapter_code=chapter_code)
            chapter_exercise_types = set()
            
            for ex in exercises:
                if ex.get("is_dynamic") and ex.get("generator_key"):
                    chapter_exercise_types.add(ex.get("generator_key"))
                    exercise_types.add(ex.get("generator_key"))
            
            pilot_chapters.append({
                "code": chapter_code,
                "exercise_types": list(chapter_exercise_types)
            })
        except Exception as e:
            logger.warning(f"Erreur chargement chapitre pilote {chapter_code}: {e}")
            pilot_chapters.append({
                "code": chapter_code,
                "exercise_types": []
            })
    
    return {
        "pilot_chapters": pilot_chapters,
        "exercise_types": list(exercise_types)
    }


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
    sync_service=Depends(get_curriculum_sync_service_dep),
    db=Depends(get_db)
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
                logger.info(f"[AUTO-SYNC] Chapitre {chapter_code} créé dans curriculum")
            elif sync_result['updated']:
                logger.info(f"[AUTO-SYNC] Chapitre {chapter_code} mis à jour dans curriculum")
        except Exception as sync_error:
            logger.warning(
                f"[AUTO-SYNC] Échec sync curriculum pour {chapter_code}: {sync_error}"
            )
        
        # 3. ✨ NOUVEAU: Synchroniser automatiquement vers exercise_types
        # (Uniquement pour les exercices dynamiques)
        if request.is_dynamic and request.generator_key:
            try:
                et_sync_result = await sync_service.sync_chapter_to_exercise_types(chapter_code)
                logger.info(
                    f"[AUTO-SYNC] exercise_types synchronisé pour {chapter_code}: "
                    f"créés={et_sync_result['created']}, mis à jour={et_sync_result['updated']}, "
                    f"generators={et_sync_result['generator_keys']}"
                )
            except Exception as et_sync_error:
                # Ne pas faire échouer la création si la sync exercise_types échoue
                logger.warning(
                    f"[AUTO-SYNC] Échec sync exercise_types pour {chapter_code}: {et_sync_error}. "
                    "L'exercice a été créé mais exercise_types n'est pas synchronisé. "
                    "Utilisez l'endpoint /sync-curriculum pour corriger."
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


@router.get(
    "/chapters/{chapter_code}/exercises-export",
    summary="Exporter les exercices d'un chapitre (format versionné v1.0)",
    description="Export JSON versionné des exercices d'un chapitre. Format canonique v1.0 avec schema_version, exported_at, metadata."
)
async def export_exercises(
    chapter_code: str,
    pipeline: Optional[Literal["SPEC", "TEMPLATE"]] = None,
    service=Depends(get_exercise_service),
    db=Depends(get_db)
):
    """
    Exporte les exercices d'un chapitre au format versionné v1.0.
    
    Format de sortie:
    {
        "schema_version": "1.0",
        "exported_at": "ISO8601",
        "chapter_code": "6E_GM07",
        "exercises": [...],
        "metadata": {
            "total_exercises": 43
        }
    }
    """
    try:
        from datetime import datetime
        from backend.constants.collections import EXERCISES_COLLECTION
        
        normalized_code = chapter_code.upper().replace("-", "_")
        chapter = get_chapter_by_official_code(normalized_code) or get_chapter_by_official_code(chapter_code)

        # Récupérer les exercices depuis la DB directement
        collection = db[EXERCISES_COLLECTION]
        query = {"chapter_code": normalized_code}
        
        exercises = await collection.find(query, {"_id": 0}).sort("id", 1).to_list(length=None)
        
        # Filtrer par pipeline si demandé
        if pipeline == "TEMPLATE":
            exercises = [ex for ex in exercises if ex.get("is_dynamic") is True]
        elif pipeline == "SPEC":
            exercises = [ex for ex in exercises if ex.get("is_dynamic") is not True]

        # Format versionné v1.0
        return {
            "schema_version": "1.0",
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "chapter_code": normalized_code,
            "exercises": exercises,
            "metadata": {
                "total_exercises": len(exercises),
                "pipeline": chapter.pipeline if chapter else None,
                "domaine": chapter.domaine if chapter else None,
                "libelle": chapter.libelle if chapter else normalized_code,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur export exercices {chapter_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/chapters/{chapter_code}/exercises/import",
    summary="Importer des exercices dans un chapitre (format versionné v1.0)",
    description="Importe une liste d'exercices (JSON versionné v1.0) pour un chapitre existant. Import atomique avec rollback automatique en cas d'erreur."
)
async def import_exercises(
    chapter_code: str,
    payload: dict,  # Accepte dict pour format versionné flexible (v1.0 ou legacy)
    service=Depends(get_exercise_service),
    sync_service=Depends(get_curriculum_sync_service_dep),
    db=Depends(get_db)
):
    """
    Importe des exercices au format versionné v1.0 avec rollback atomique.
    
    Format attendu:
    {
        "schema_version": "1.0",
        "chapter_code": "6E_GM07",
        "exercises": [...],
        "metadata": {"total_exercises": N}
    }
    
    Pipeline:
    1. Validation stricte du payload
    2. Génération batch_id unique
    3. Insertion atomique (bulk)
    4. Rollback automatique en cas d'erreur
    """
    from uuid import uuid4
    from datetime import datetime
    from backend.services.import_export_validator import validate_import_payload_v1
    from backend.constants.collections import EXERCISES_COLLECTION
    
    logger.info(f"Admin: Import exercices versionné dans {chapter_code}")
    
    # Détecter le format du payload (v1.0 versionné ou legacy)
    schema_version = payload.get("schema_version")
    is_versioned = schema_version == "1.0"
    
    # Si schema_version est présent mais invalide, rejeter immédiatement
    if schema_version is not None and schema_version != "1.0":
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_SCHEMA_VERSION",
                "error": "invalid_schema_version",
                "message": f"Version de schéma invalide: '{schema_version}'. Version attendue: '1.0'",
                "provided_version": schema_version,
                "expected_version": "1.0"
            }
        )
    
    if is_versioned:
        # Format versionné v1.0: validation stricte + import atomique
        # 1. Validation stricte du payload v1.0
        try:
            validate_import_payload_v1(payload)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur validation payload import: {e}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "error": "validation_error",
                    "message": f"Erreur lors de la validation du payload: {str(e)}"
                }
            )
        
        # 2. Vérifier que le chapitre existe
        normalized_code = payload["chapter_code"].upper().replace("-", "_")
        chapter = get_chapter_by_official_code(normalized_code) or get_chapter_by_official_code(chapter_code)
        if not chapter:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "INVALID_CHAPTER",
                    "error": "invalid_chapter",
                    "message": f"Le chapitre '{chapter_code}' n'existe pas dans le curriculum.",
                },
            )
        
        # 3. Générer batch_id unique pour rollback
        batch_id = str(uuid4())
        imported_at = datetime.utcnow()
        
        # 4. Préparer les exercices pour insertion
        exercises_to_insert = []
        for exercise in payload["exercises"]:
            # Normaliser chapter_code
            exercise["chapter_code"] = normalized_code
            
            # Ajouter métadonnées d'import
            exercise["batch_id"] = batch_id
            exercise["imported_at"] = imported_at
            
            # Supprimer _id si présent (pour éviter conflit)
            exercise.pop("_id", None)
            
            exercises_to_insert.append(exercise)
        
        # 5. Insertion atomique avec rollback
        collection = db[EXERCISES_COLLECTION]
        inserted_count = 0
        
        try:
            # Insertion en bulk
            if exercises_to_insert:
                result = await collection.insert_many(exercises_to_insert)
                inserted_count = len(result.inserted_ids)
                logger.info(f"Import atomique réussi: {inserted_count} exercices insérés (batch_id={batch_id})")
        except Exception as e:
            # Rollback: supprimer tous les exercices avec ce batch_id
            logger.error(f"Erreur lors de l'insertion bulk (batch_id={batch_id}): {e}", exc_info=True)
            try:
                delete_result = await collection.delete_many({"batch_id": batch_id})
                logger.info(f"Rollback effectué: {delete_result.deleted_count} exercices supprimés (batch_id={batch_id})")
            except Exception as rollback_error:
                logger.critical(
                    f"ERREUR CRITIQUE: Échec du rollback (batch_id={batch_id}): {rollback_error}. "
                    f"Des exercices orphelins peuvent exister dans la DB."
                )
            
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "IMPORT_FAILED",
                    "error": "import_failed",
                    "message": f"Erreur lors de l'insertion des exercices: {str(e)}",
                    "batch_id": batch_id,
                    "rollback_performed": True
                }
            )
        
        # 6. Vérifier qu'au moins un exercice a été inséré
        if inserted_count == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "IMPORT_FAILED",
                    "error": "import_failed",
                    "message": f"Aucun exercice inséré pour {chapter_code}",
                    "batch_id": batch_id
                }
            )
        
        created_count = inserted_count
        
    else:
        # Format legacy: comportement existant (pour compatibilité)
        logger.info(f"Admin: Import exercices legacy dans {chapter_code} (count={len(payload.get('exercises', []))})")
        normalized_code = chapter_code.upper()
        chapter = get_chapter_by_official_code(normalized_code) or get_chapter_by_official_code(chapter_code)
        if not chapter:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "INVALID_CHAPTER",
                    "error": "invalid_chapter",
                    "message": f"Le chapitre '{chapter_code}' n'existe pas dans le curriculum.",
                },
            )

        # Validation pipeline (pré)
        expected_pipeline = payload.get("pipeline") or chapter.pipeline
        exercises_list = payload.get("exercises", [])
        dynamic_count = sum(1 for ex in exercises_list if ex.get("is_dynamic"))
        static_count = sum(1 for ex in exercises_list if not ex.get("is_dynamic"))
        if expected_pipeline == "TEMPLATE" and dynamic_count == 0:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "TEMPLATE_PIPELINE_NO_DYNAMIC_EXERCISES",
                    "error": "template_pipeline_no_exercises",
                    "message": (
                        f"Le pipeline TEMPLATE requiert au moins un exercice dynamique. Aucun exercice dynamique dans le payload pour '{chapter_code}'."
                    ),
                },
            )
        if expected_pipeline == "SPEC" and static_count == 0 and not chapter.exercise_types:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "SPEC_PIPELINE_INVALID_EXERCISE_TYPES",
                    "error": "spec_pipeline_invalid",
                    "message": (
                        f"Le pipeline SPEC requiert des exercise_types valides ou des exercices statiques. "
                        f"Aucun statique dans le payload et pas d'exercise_types pour '{chapter_code}'."
                    ),
                },
            )

        created = []
        errors = []
        for ex in exercises_list:
            try:
                req = ExerciseCreateRequest(**ex)
                created_ex = await service.create_exercise(normalized_code, req)
                created.append(created_ex)
            except Exception as e:
                logger.warning(f"Import exercice KO ({chapter_code}): {e}")
                errors.append(str(e))
        
        created_count = len(created)
        
        if errors and not created:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "IMPORT_FAILED",
                    "error": "import_failed",
                    "message": f"Aucun exercice importé pour {chapter_code}",
                    "errors": errors,
                },
            )

    # 7. Sync curriculum et exercise_types (non-bloquant)
    try:
        await sync_service.sync_chapter_to_curriculum(normalized_code)
    except Exception as sync_error:
        logger.warning(f"[AUTO-SYNC] Échec sync curriculum après import {chapter_code}: {sync_error}")
    
    try:
        et_sync_result = await sync_service.sync_chapter_to_exercise_types(normalized_code)
        logger.info(
            f"[AUTO-SYNC] exercise_types synchronisé après import batch pour {normalized_code}: "
            f"créés={et_sync_result['created']}, mis à jour={et_sync_result['updated']}"
        )
    except Exception as et_sync_error:
        logger.warning(
            f"[AUTO-SYNC] Échec sync exercise_types après import pour {normalized_code}: {et_sync_error}"
        )

    # 8. Réponse
    response = {
        "success": True,
        "chapter_code": normalized_code,
        "imported": created_count,
    }
    
    if is_versioned:
        response["batch_id"] = batch_id  # Pour traçabilité
        response["imported_at"] = imported_at.isoformat() + "Z"
    else:
        # Format legacy: inclure errors si présents
        if "errors" in locals() and errors:
            response["errors"] = errors
    
    return response


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
    sync_service=Depends(get_curriculum_sync_service_dep),
    db=Depends(get_db)
):
    """Met à jour un exercice et synchronise automatiquement curriculum + exercise_types"""
    logger.info(f"Admin: Mise à jour exercice {chapter_code} #{exercise_id}")
    
    try:
        # 1. Mettre à jour l'exercice dans admin_exercises
        exercise = await service.update_exercise(chapter_code, exercise_id, request)
        logger.info(f"✅ Exercice #{exercise_id} mis à jour dans admin_exercises")
        
        # 2. Synchroniser automatiquement vers curriculum
        try:
            sync_result = await sync_service.sync_chapter_to_curriculum(chapter_code)
            if sync_result['created']:
                logger.info(f"[AUTO-SYNC] Chapitre {chapter_code} créé dans curriculum")
            elif sync_result['updated']:
                logger.info(f"[AUTO-SYNC] Chapitre {chapter_code} mis à jour dans curriculum")
        except Exception as sync_error:
            logger.warning(
                f"[AUTO-SYNC] Échec sync curriculum pour {chapter_code}: {sync_error}"
            )
        
        # 3. ✨ NOUVEAU: Synchroniser automatiquement vers exercise_types
        # (Pour tous les exercices du chapitre, pas seulement celui mis à jour)
        try:
            et_sync_result = await sync_service.sync_chapter_to_exercise_types(chapter_code)
            logger.info(
                f"[AUTO-SYNC] exercise_types synchronisé pour {chapter_code}: "
                f"créés={et_sync_result['created']}, mis à jour={et_sync_result['updated']}"
            )
        except Exception as et_sync_error:
            logger.warning(
                f"[AUTO-SYNC] Échec sync exercise_types pour {chapter_code}: {et_sync_error}"
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
    service=Depends(get_exercise_service),
    sync_service=Depends(get_curriculum_sync_service_dep)
):
    """Supprime un exercice et synchronise automatiquement exercise_types (cleanup)"""
    logger.info(f"Admin: Suppression exercice {chapter_code} #{exercise_id}")
    
    try:
        # 1. Supprimer l'exercice de admin_exercises
        deleted = await service.delete_exercise(chapter_code, exercise_id)
        
        if not deleted:
            raise HTTPException(status_code=500, detail="Erreur lors de la suppression")
        
        logger.info(f"✅ Exercice #{exercise_id} supprimé de admin_exercises")
        
        # 2. ✨ NOUVEAU: Synchroniser exercise_types pour cleanup des orphelins
        # Si c'était le dernier exercice avec ce generator_key, l'exercise_type sera supprimé
        try:
            et_sync_result = await sync_service.sync_chapter_to_exercise_types(chapter_code)
            logger.info(
                f"[AUTO-SYNC] exercise_types synchronisé après suppression pour {chapter_code}: "
                f"supprimés={et_sync_result['deleted']}"
            )
        except Exception as et_sync_error:
            logger.warning(
                f"[AUTO-SYNC] Échec cleanup exercise_types pour {chapter_code}: {et_sync_error}"
            )
        
        return ExerciseCRUDResponse(
            success=True,
            message=f"Exercice #{exercise_id} supprimé avec succès",
            exercise=None
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur suppression exercice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/collections/guard-rails",
    summary="Vérifier les guard rails des collections",
    description="Détecte les typos et incohérences dans les noms de collections MongoDB"
)
async def check_collections_guard_rails(db=Depends(get_db)):
    """Vérifie les guard rails des collections"""
    try:
        results = await check_collection_typos(db)
        return {
            "warnings": results["warnings"],
            "errors": results["errors"],
            "status": "error" if results["errors"] else ("warning" if results["warnings"] else "ok")
        }
    except Exception as e:
        logger.error(f"Erreur guard rails: {e}")
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
