"""
Migration P0: Ajout du champ pipeline au modèle CurriculumChapter

Ce script migre tous les chapitres existants pour ajouter le champ pipeline:
- Tous les chapitres → pipeline = "SPEC" (par défaut)
- TESTS_DYN → pipeline = "TEMPLATE"
- Détection automatique: si chapitre a exercices dynamiques en DB → "TEMPLATE"

Script idempotent: peut être relancé sans erreur.
"""

import asyncio
import sys
import os

# Ajouter le chemin du backend au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from backend.logger import get_logger

logger = get_logger()

# Configuration MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("DB_NAME", "lemaitremot")


async def migrate_pipeline_field():
    """
    Migration one-shot: ajoute le champ pipeline à tous les chapitres.
    """
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    chapters_collection = db.curriculum_chapters
    exercises_collection = db.exercises
    
    logger.info("🚀 Début migration: ajout champ pipeline")
    
    # Récupérer tous les chapitres
    chapters = await chapters_collection.find({}).to_list(1000)
    logger.info(f"📚 {len(chapters)} chapitres trouvés")
    
    updated_count = 0
    skipped_count = 0
    
    for chapter in chapters:
        code_officiel = chapter.get("code_officiel")
        
        # Vérifier si le champ pipeline existe déjà
        if "pipeline" in chapter and chapter["pipeline"]:
            logger.debug(f"⏭️  Chapitre {code_officiel} a déjà un pipeline: {chapter['pipeline']}")
            skipped_count += 1
            continue
        
        # Déterminer le pipeline
        pipeline_value = "SPEC"  # Par défaut
        
        # TESTS_DYN → TEMPLATE
        if code_officiel and code_officiel.upper() in ["6E_TESTS_DYN", "TESTS_DYN"]:
            pipeline_value = "TEMPLATE"
            logger.info(f"✅ Chapitre {code_officiel} → pipeline=TEMPLATE (TESTS_DYN)")
        else:
            # Détection automatique: vérifier si exercices dynamiques en DB
            chapter_code_upper = code_officiel.upper().replace("-", "_") if code_officiel else None
            if chapter_code_upper:
                try:
                    # Vérifier si exercices dynamiques existent
                    dynamic_exercises_count = await exercises_collection.count_documents({
                        "chapter_code": chapter_code_upper,
                        "is_dynamic": True
                    })
                    
                    if dynamic_exercises_count > 0:
                        pipeline_value = "TEMPLATE"
                        logger.info(
                            f"✅ Chapitre {code_officiel} → pipeline=TEMPLATE "
                            f"(détection automatique: {dynamic_exercises_count} exercices dynamiques)"
                        )
                    else:
                        logger.debug(f"📝 Chapitre {code_officiel} → pipeline=SPEC (par défaut)")
                except Exception as e:
                    logger.warning(
                        f"⚠️  Erreur détection automatique pour {code_officiel}: {e}. "
                        f"Utilisation de SPEC par défaut."
                    )
        
        # Mettre à jour le chapitre
        result = await chapters_collection.update_one(
            {"code_officiel": code_officiel},
            {"$set": {"pipeline": pipeline_value}}
        )
        
        if result.modified_count > 0:
            updated_count += 1
            logger.info(f"✅ Chapitre {code_officiel} mis à jour: pipeline={pipeline_value}")
        else:
            logger.warning(f"⚠️  Aucune modification pour {code_officiel}")
    
    # Synchroniser avec le fichier JSON (si nécessaire)
    # Note: Le service curriculum_persistence_service fait ça automatiquement,
    # mais on peut forcer une sync ici si besoin
    
    logger.info(f"✅ Migration terminée: {updated_count} chapitres mis à jour, {skipped_count} ignorés")
    
    client.close()
    return updated_count, skipped_count


if __name__ == "__main__":
    asyncio.run(migrate_pipeline_field())


