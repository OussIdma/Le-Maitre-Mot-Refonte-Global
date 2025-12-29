"""
Guard rails pour les noms de collections MongoDB.

Détecte les typos et incohérences dans les noms de collections.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.constants.collections import (
    EXERCISES_COLLECTION,
    EXERCISE_TYPES_COLLECTION,
    LEGACY_EXERCISES_COLLECTION
)

logger = logging.getLogger(__name__)


async def check_collection_typos(db: AsyncIOMotorDatabase) -> dict:
    """
    Vérifie les typos dans les noms de collections.
    
    Détecte notamment:
    - Collection "adminexercises" (sans underscore) qui devrait être "admin_exercises"
    
    Returns:
        Dict avec les résultats: {warnings: [], errors: []}
    """
    results = {
        "warnings": [],
        "errors": []
    }
    
    try:
        collections = await db.list_collection_names()
        
        # Vérifier la typo "adminexercises" (sans underscore)
        if LEGACY_EXERCISES_COLLECTION in collections:
            count = await db[LEGACY_EXERCISES_COLLECTION].count_documents({})
            if count > 0:
                warning_msg = (
                    f"⚠️  Collection typo détectée: '{LEGACY_EXERCISES_COLLECTION}' "
                    f"contient {count} documents. "
                    f"Utilisez '{EXERCISES_COLLECTION}' (avec underscore) à la place."
                )
                results["warnings"].append(warning_msg)
                logger.warning(warning_msg)
        
        # Vérifier que les collections attendues existent
        if EXERCISES_COLLECTION not in collections:
            error_msg = f"❌ Collection attendue '{EXERCISES_COLLECTION}' n'existe pas"
            results["errors"].append(error_msg)
            logger.error(error_msg)
        
        if EXERCISE_TYPES_COLLECTION not in collections:
            # Ce n'est qu'un warning car la collection peut être créée à la volée
            warning_msg = f"⚠️  Collection '{EXERCISE_TYPES_COLLECTION}' n'existe pas encore"
            results["warnings"].append(warning_msg)
            logger.warning(warning_msg)
    
    except Exception as e:
        error_msg = f"Erreur lors de la vérification des collections: {e}"
        results["errors"].append(error_msg)
        logger.error(error_msg, exc_info=True)
    
    return results


async def log_collection_guard_rails(db: AsyncIOMotorDatabase) -> None:
    """
    Log les guard rails au démarrage (ou via endpoint admin).
    
    À appeler au démarrage du serveur ou via un endpoint admin.
    """
    results = await check_collection_typos(db)
    
    if results["warnings"]:
        logger.warning("=" * 60)
        logger.warning("GUARD RAILS - AVERTISSEMENTS COLLECTIONS")
        logger.warning("=" * 60)
        for warning in results["warnings"]:
            logger.warning(warning)
        logger.warning("=" * 60)
    
    if results["errors"]:
        logger.error("=" * 60)
        logger.error("GUARD RAILS - ERREURS COLLECTIONS")
        logger.error("=" * 60)
        for error in results["errors"]:
            logger.error(error)
        logger.error("=" * 60)



