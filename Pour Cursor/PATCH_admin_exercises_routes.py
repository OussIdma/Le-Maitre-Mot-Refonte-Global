"""
PATCH PRODUCTION - admin_exercises_routes.py
=============================================

Ajouter la synchronisation automatique vers exercise_types lors des opérations CRUD

Modifications à apporter dans les endpoints:
- create_exercise()
- update_exercise()
- delete_exercise()
- import_exercises()
"""

import logging

logger = logging.getLogger(__name__)


# ============================================================================
# MODIFICATION #1: create_exercise() - Ligne ~22212
# ============================================================================

# AVANT (ligne 22212-22249):
"""
@router.post(
    "/chapters/{chapter_code}/exercises",
    response_model=ExerciseCRUDResponse
)
async def create_exercise(
    chapter_code: str,
    request: ExerciseCreateRequest,
    service=Depends(get_exercise_service),
    sync_service=Depends(get_curriculum_sync_service_dep)
):
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
"""

# APRÈS (avec sync exercise_types):
@router.post(
    "/chapters/{chapter_code}/exercises",
    response_model=ExerciseCRUDResponse,
    summary="Créer un nouvel exercice"
)
async def create_exercise(
    chapter_code: str,
    request: ExerciseCreateRequest,
    service=Depends(get_exercise_service),
    sync_service=Depends(get_curriculum_sync_service_dep)
):
    """Crée un nouvel exercice et synchronise automatiquement curriculum + exercise_types"""
    logger.info(f"Admin: Création exercice dans {chapter_code}")
    
    try:
        # 1. Créer l'exercice dans admin_exercises
        exercise = await service.create_exercise(chapter_code, request)
        logger.info(f"✅ Exercice #{exercise['id']} créé dans admin_exercises")
        
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


# ============================================================================
# MODIFICATION #2: update_exercise() - Ligne ~22380
# ============================================================================

# AVANT (ligne 22380-22418):
"""
@router.put(
    "/chapters/{chapter_code}/exercises/{exercise_id}",
    response_model=ExerciseCRUDResponse
)
async def update_exercise(
    chapter_code: str,
    exercise_id: int,
    request: ExerciseUpdateRequest,
    service=Depends(get_exercise_service),
    sync_service=Depends(get_curriculum_sync_service_dep)
):
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
"""

# APRÈS (avec sync exercise_types):
@router.put(
    "/chapters/{chapter_code}/exercises/{exercise_id}",
    response_model=ExerciseCRUDResponse,
    summary="Modifier un exercice"
)
async def update_exercise(
    chapter_code: str,
    exercise_id: int,
    request: ExerciseUpdateRequest,
    service=Depends(get_exercise_service),
    sync_service=Depends(get_curriculum_sync_service_dep)
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


# ============================================================================
# MODIFICATION #3: delete_exercise() - Ligne ~22427
# ============================================================================

# AVANT (ligne 22427-22453):
"""
@router.delete(
    "/chapters/{chapter_code}/exercises/{exercise_id}",
    response_model=ExerciseCRUDResponse
)
async def delete_exercise(
    chapter_code: str,
    exercise_id: int,
    service=Depends(get_exercise_service)
):
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
"""

# APRÈS (avec sync exercise_types):
@router.delete(
    "/chapters/{chapter_code}/exercises/{exercise_id}",
    response_model=ExerciseCRUDResponse,
    summary="Supprimer un exercice"
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


# ============================================================================
# MODIFICATION #4: import_exercises() - Ligne ~22291
# ============================================================================

# AVANT (ligne 22349-22371):
"""
    # Sync curriculum (enrichissement exercise_types)
    try:
        await sync_service.sync_chapter_to_curriculum(normalized_code)
    except Exception as sync_error:
        logger.warning(f"[AUTO-SYNC] Échec sync curriculum après import {chapter_code}: {sync_error}")

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

    return {
        "success": True,
        "chapter_code": chapter_code.upper(),
        "imported": len(created),
        "errors": errors,
    }
"""

# APRÈS (avec sync exercise_types):
    # Sync curriculum (enrichissement exercise_types)
    try:
        await sync_service.sync_chapter_to_curriculum(normalized_code)
    except Exception as sync_error:
        logger.warning(f"[AUTO-SYNC] Échec sync curriculum après import {chapter_code}: {sync_error}")
    
    # ✨ NOUVEAU: Sync exercise_types après import batch
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

    return {
        "success": True,
        "chapter_code": chapter_code.upper(),
        "imported": len(created),
        "errors": errors,
    }


# ============================================================================
# RÉSUMÉ DES MODIFICATIONS
# ============================================================================

"""
Changements apportés dans admin_exercises_routes.py:

1. ✅ create_exercise() - Ajout sync_chapter_to_exercise_types() après création
2. ✅ update_exercise() - Ajout sync_chapter_to_exercise_types() après mise à jour
3. ✅ delete_exercise() - Ajout sync_chapter_to_exercise_types() après suppression (cleanup)
4. ✅ import_exercises() - Ajout sync_chapter_to_exercise_types() après import batch

Caractéristiques:
- Sync automatique (pas d'action manuelle requise)
- Non-bloquante (si sync échoue, l'opération principale réussit quand même)
- Loggée (pour debug et monitoring)
- Transactionnelle (ne casse pas admin_exercises)
- Idempotente (peut être appelée plusieurs fois)

Comportement en cas d'erreur:
- admin_exercises: opération réussie ✅
- exercise_types: warning loggé ⚠️ mais pas d'échec HTTP
- Utilisateur: peut forcer la sync via /sync-curriculum si nécessaire
"""
