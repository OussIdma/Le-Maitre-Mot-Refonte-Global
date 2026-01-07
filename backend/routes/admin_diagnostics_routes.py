"""
Routes API pour les diagnostics administratifs (P4.2)

Endpoints:
- GET /api/admin/diagnostics/chapter/{code_officiel}: Diagnostique le pipeline utilisé pour un chapitre
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any, List
import os
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.logger import get_logger
from backend.services.exercise_persistence_service import get_exercise_persistence_service
from backend.services.gm07_handler import is_gm07_request
from backend.services.gm08_handler import is_gm08_request
from backend.services.tests_dyn_handler import is_tests_dyn_request
from backend.server import db

logger = get_logger()
router = APIRouter(prefix="/api/admin", tags=["Admin Diagnostics"])


async def resolve_pipeline(code_officiel: str, offer: str = "free", difficulty: str = "moyen") -> tuple[str, str]:
    """
    Détermine quel pipeline est utilisé pour un chapitre donné.

    Args:
        code_officiel: Code officiel du chapitre (ex: 6e_GM07, 6e_N01)
        offer: Offre de l'utilisateur (free/pro)
        difficulty: Difficulté demandée (facile/moyen/difficile)

    Returns:
        tuple: (pipeline_used, reason)
    """
    if not code_officiel:
        return "UNKNOWN", "Code officiel manquant"

    # Normaliser le code_officiel
    normalized_code = code_officiel.upper().replace("-", "_")

    # Vérifier si les pipelines basés sur fichiers sont désactivés
    disable_file_pipelines = os.getenv("DISABLE_FILE_PIPELINES", "false").lower() == "true"

    # Vérifier les pipelines spécifiques
    is_gm07 = is_gm07_request(normalized_code)
    is_gm08 = is_gm08_request(normalized_code)
    is_tests_dyn = is_tests_dyn_request(normalized_code)

    if is_gm07 and not disable_file_pipelines:
        return "FILE_GM07", "Chapitre GM07 détecté, pipelines fichiers activés"
    elif is_gm07 and disable_file_pipelines:
        return "DB_DYNAMIC", "Chapitre GM07 mais pipelines fichiers désactivés (DB fallback)"
    elif is_gm08 and not disable_file_pipelines:
        return "FILE_GM08", "Chapitre GM08 détecté, pipelines fichiers activés"
    elif is_gm08 and disable_file_pipelines:
        return "DB_DYNAMIC", "Chapitre GM08 mais pipelines fichiers désactivés (DB fallback)"
    elif is_tests_dyn and not disable_file_pipelines:
        return "FILE_TESTS_DYN", "Chapitre TESTS_DYN détecté, pipelines fichiers activés"
    elif is_tests_dyn and disable_file_pipelines:
        return "DB_DYNAMIC", "Chapitre TESTS_DYN mais pipelines fichiers désactivés (DB fallback)"
    else:
        # Vérifier si le chapitre existe en DB
        from backend.services.curriculum_persistence_service import get_curriculum_persistence_service
        curriculum_service_db = get_curriculum_persistence_service(db)

        try:
            chapter_from_db = await curriculum_service_db.get_chapter_by_code(normalized_code)
        except:
            chapter_from_db = None

        if chapter_from_db:
            pipeline = chapter_from_db.get("pipeline", "DB_DYNAMIC")
            return pipeline, f"Chapitre trouvé en DB avec pipeline={pipeline}"
        else:
            # Vérifier dans le fichier JSON legacy
            from backend.curriculum.loader import get_chapter_by_official_code
            chapter_legacy = get_chapter_by_official_code(code_officiel)
            if chapter_legacy:
                return "STATIC_JSON", "Chapitre trouvé dans JSON legacy (migration nécessaire)"
            else:
                return "NOT_FOUND", "Chapitre non trouvé dans DB ni dans JSON"


@router.get("/diagnostics/chapter/{code_officiel}", 
            summary="Diagnostic du pipeline pour un chapitre",
            description="Retourne des informations sur quel pipeline sert un chapitre spécifique")
async def get_chapter_diagnostics(code_officiel: str):
    """
    Diagnostic du pipeline utilisé pour un chapitre spécifique.
    
    Returns:
        - code_officiel: Le code du chapitre demandé
        - normalized_code: Le code normalisé (uppercase, underscores)
        - pipeline_used: Pipeline actuellement utilisé (FILE_GM07, FILE_GM08, FILE_TESTS_DYN, DB_DYNAMIC, STATIC_JSON, NOT_FOUND)
        - reason: Raison du choix du pipeline
        - db_exercises_count: Nombre d'exercices disponibles en DB pour ce chapitre
        - file_pipeline_available: Indique si un pipeline basé sur fichier est disponible
        - static_available: Indique si des exercices statiques sont disponibles
        - fallback_used: Indique si un fallback est utilisé
    """
    try:
        # Normaliser le code_officiel
        normalized_code = code_officiel.upper().replace("-", "_")
        
        # Vérifier si les pipelines basés sur fichiers sont désactivés
        disable_file_pipelines = os.getenv("DISABLE_FILE_PIPELINES", "false").lower() == "true"
        
        # Déterminer le pipeline utilisé
        pipeline_used, reason = await resolve_pipeline(code_officiel)

        # Compter les exercices en DB pour ce chapitre
        exercise_service = get_exercise_persistence_service(db)
        db_exercises_count = 0
        try:
            exercises = await exercise_service.get_exercises(normalized_code)
            db_exercises_count = len(exercises)
        except Exception as e:
            logger.warning(f"Erreur lors du comptage des exercices DB pour {normalized_code}: {e}")
            db_exercises_count = 0

        # Déterminer si un pipeline fichier est disponible
        # Vérifier à nouveau les types de chapitres pour ce diagnostic
        from backend.services.gm07_handler import is_gm07_request
        from backend.services.gm08_handler import is_gm08_request
        from backend.services.tests_dyn_handler import is_tests_dyn_request

        is_gm07_local = is_gm07_request(normalized_code)
        is_gm08_local = is_gm08_request(normalized_code)
        is_tests_dyn_local = is_tests_dyn_request(normalized_code)

        file_pipeline_available = is_gm07_local or is_gm08_local or is_tests_dyn_local

        # Vérifier si des exercices statiques sont disponibles
        static_available = False
        try:
            from backend.curriculum.loader import get_chapter_by_official_code
            chapter_legacy = get_chapter_by_official_code(code_officiel)
            static_available = chapter_legacy is not None
        except Exception:
            static_available = False

        # Déterminer si fallback est utilisé
        fallback_used = (
            (is_gm07_local or is_gm08_local or is_tests_dyn_local) and
            disable_file_pipelines
        )

        logger.info(
            f"[DIAGNOSTICS] Chapter: {code_officiel} → pipeline={pipeline_used}, "
            f"db_count={db_exercises_count}, file_available={file_pipeline_available}, "
            f"fallback_used={fallback_used}"
        )

        return {
            "code_officiel": code_officiel,
            "normalized_code": normalized_code,
            "pipeline_used": pipeline_used,
            "reason": reason,
            "db_exercises_count": db_exercises_count,
            "file_pipeline_available": file_pipeline_available,
            "static_available": static_available,
            "fallback_used": fallback_used
        }

    except Exception as e:
        logger.error(f"Erreur lors du diagnostic du chapitre {code_officiel}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "DIAGNOSTIC_FAILED",
                "error": "diagnostic_failed",
                "message": f"Erreur lors du diagnostic du chapitre {code_officiel}",
                "error_details": str(e)
            }
        )


# Routes de compatibilité ascendante (backward compatibility)
# Ces routes existent déjà mais doivent supporter le paramètre subject optionnel
@router.get("/catalogue/levels/{level}/chapters",
            summary="Catalogue des chapitres par niveau (backward compatible)",
            description="Version backward compatible: assume subject='math' si non spécifié")
async def get_catalog_by_level_backward_compatible(level: str):
    """
    Catalogue des chapitres par niveau (backward compatible).

    Args:
        level: Niveau scolaire (ex: 6e, 5e, 4e, 3e)

    Returns:
        - subject: "math" (par défaut pour backward compatibility)
        - level: Le niveau demandé
        - chapters: Liste des chapitres disponibles
        - count: Nombre de chapitres
    """
    try:
        # Pour backward compatibility, assume subject="math"
        subject = "math"

        # Récupérer les chapitres pour le niveau spécifié
        from backend.services.curriculum_persistence_service import get_curriculum_persistence_service
        curriculum_service_db = get_curriculum_persistence_service(db)

        chapters = await curriculum_service_db.get_all_chapters(level)

        logger.info(
            f"[CATALOGUE_DIAG] (BC) Subject: {subject}, Level: {level} → {len(chapters)} chapters"
        )

        return {
            "subject": subject,
            "level": level,
            "chapters": chapters,
            "count": len(chapters)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du chargement du catalogue BC pour {level}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "CATALOG_LOAD_FAILED_BC",
                "error": "catalog_load_failed",
                "message": f"Erreur lors du chargement du catalogue pour {level} (backward compatible)",
                "error_details": str(e)
            }
        )


# Endpoint admin curriculum avec support de subject
@router.get("/admin/curriculum/{subject}/{level}",
            summary="Admin curriculum par matière et niveau",
            description="Retourne le curriculum pour une matière et un niveau donnés")
async def get_admin_curriculum_by_subject_and_level(subject: str, level: str):
    """
    Curriculum admin par matière et niveau.

    Args:
        subject: Matière (ex: math, physics, chemistry)
        level: Niveau scolaire (ex: 6e, 5e, 4e, 3e)

    Returns:
        - subject: La matière demandée
        - level: Le niveau demandé
        - curriculum: Données du curriculum
        - count: Nombre de chapitres
    """
    try:
        # Pour l'instant, on ne gère que la matière "math" (V1)
        # En V2, on pourra étendre à d'autres matières
        if subject.lower() != "math":
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "SUBJECT_NOT_SUPPORTED",
                    "error": "subject_not_supported",
                    "message": f"La matière '{subject}' n'est pas supportée dans cette version.",
                    "supported_subjects": ["math"],
                    "hint": "Utilisez 'math' comme matière pour accéder au curriculum."
                }
            )

        # Récupérer le curriculum pour le niveau spécifié
        from backend.services.curriculum_persistence_service import get_curriculum_persistence_service
        curriculum_service_db = get_curriculum_persistence_service(db)

        chapters = await curriculum_service_db.get_all_chapters(level)

        curriculum_data = {
            "subject": subject,
            "level": level,
            "chapters": chapters,
            "count": len(chapters)
        }

        logger.info(
            f"[ADMIN_CURRICULUM_DIAG] Subject: {subject}, Level: {level} → {len(chapters)} chapters"
        )

        return curriculum_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du chargement du curriculum admin pour {subject}/{level}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "ADMIN_CURRICULUM_LOAD_FAILED",
                "error": "admin_curriculum_load_failed",
                "message": f"Erreur lors du chargement du curriculum admin pour {subject}/{level}",
                "error_details": str(e)
            }
        )


# Routes de compatibilité ascendante pour admin curriculum
@router.get("/admin/curriculum/{level}",
            summary="Admin curriculum par niveau (backward compatible)",
            description="Version backward compatible: assume subject='math' si non spécifié")
async def get_admin_curriculum_by_level_backward_compatible(level: str):
    """
    Curriculum admin par niveau (backward compatible).

    Args:
        level: Niveau scolaire (ex: 6e, 5e, 4e, 3e)

    Returns:
        - subject: "math" (par défaut pour backward compatibility)
        - level: Le niveau demandé
        - curriculum: Données du curriculum
        - count: Nombre de chapitres
    """
    try:
        # Pour backward compatibility, assume subject="math"
        subject = "math"

        # Récupérer le curriculum pour le niveau spécifié
        from backend.services.curriculum_persistence_service import get_curriculum_persistence_service
        curriculum_service_db = get_curriculum_persistence_service(db)

        chapters = await curriculum_service_db.get_all_chapters(level)

        curriculum_data = {
            "subject": subject,
            "level": level,
            "chapters": chapters,
            "count": len(chapters)
        }

        logger.info(
            f"[ADMIN_CURRICULUM_DIAG] (BC) Subject: {subject}, Level: {level} → {len(chapters)} chapters"
        )

        return curriculum_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du chargement du curriculum admin BC pour {level}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "ADMIN_CURRICULUM_LOAD_FAILED_BC",
                "error": "admin_curriculum_load_failed",
                "message": f"Erreur lors du chargement du curriculum admin pour {level} (backward compatible)",
                "error_details": str(e)
            }
        )


# Nouvelles routes catalogue avec support de subject
@router.get("/catalogue/{subject}/levels/{level}/chapters",
            summary="Catalogue des chapitres par matière et niveau",
            description="Retourne la liste des chapitres pour une matière et un niveau donnés")
async def get_catalog_by_subject_and_level(subject: str, level: str):
    """
    Catalogue des chapitres par matière et niveau.

    Args:
        subject: Matière (ex: math, physics, chemistry)
        level: Niveau scolaire (ex: 6e, 5e, 4e, 3e)

    Returns:
        - subject: La matière demandée
        - level: Le niveau demandé
        - chapters: Liste des chapitres disponibles
        - count: Nombre de chapitres
    """
    try:
        # Pour l'instant, on ne gère que la matière "math" (V1)
        # En V2, on pourra étendre à d'autres matières
        if subject.lower() != "math":
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "SUBJECT_NOT_SUPPORTED",
                    "error": "subject_not_supported",
                    "message": f"La matière '{subject}' n'est pas supportée dans cette version.",
                    "supported_subjects": ["math"],
                    "hint": "Utilisez 'math' comme matière pour accéder au catalogue."
                }
            )

        # Récupérer les chapitres pour le niveau spécifié
        from backend.services.curriculum_persistence_service import get_curriculum_persistence_service
        curriculum_service_db = get_curriculum_persistence_service(db)

        chapters = await curriculum_service_db.get_all_chapters(level)

        logger.info(
            f"[CATALOGUE_DIAG] Subject: {subject}, Level: {level} → {len(chapters)} chapters"
        )

        return {
            "subject": subject,
            "level": level,
            "chapters": chapters,
            "count": len(chapters)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du chargement du catalogue pour {subject}/{level}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "CATALOG_LOAD_FAILED",
                "error": "catalog_load_failed",
                "message": f"Erreur lors du chargement du catalogue pour {subject}/{level}",
                "error_details": str(e)
            }
        )