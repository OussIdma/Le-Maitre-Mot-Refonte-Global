"""
Migration 002 : Ajouter chapter_code aux ExerciseType existants

Cette migration :
1. Parcourt tous les ExerciseType
2. Pour chaque exercice avec chapitre_id mais sans chapter_code :
   - Cherche le chapitre correspondant dans la collection chapters
   - Ajoute le chapter_code si trouvé
3. Est idempotente : peut être relancée sans danger
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

# Ajouter le dossier parent au path pour importer les modules
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_exercise_types():
    """Migration principale"""
    # Connexion à MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client.mathalea_db
    
    logger.info("🔧 Début de la migration 002 : Ajout de chapter_code aux ExerciseType")
    
    # Collections
    exercise_types_collection = db.exercise_types
    chapters_collection = db.chapters
    
    # Compteurs
    total_exercises = 0
    updated_exercises = 0
    already_migrated = 0
    no_match_found = 0
    errors = 0
    
    # Récupérer tous les ExerciseType
    cursor = exercise_types_collection.find({}, {"_id": 0})
    exercises = await cursor.to_list(None)
    total_exercises = len(exercises)
    
    logger.info(f"📊 Nombre total d'ExerciseType à traiter: {total_exercises}")
    
    for exercise in exercises:
        try:
            exercise_id = exercise.get("id")
            chapitre_id = exercise.get("chapitre_id")
            chapter_code = exercise.get("chapter_code")
            
            # Si chapter_code est déjà présent, passer
            if chapter_code:
                already_migrated += 1
                continue
            
            # Si pas de chapitre_id, on ne peut rien faire
            if not chapitre_id:
                logger.debug(f"  ⚠️  ExerciseType {exercise_id} : pas de chapitre_id")
                no_match_found += 1
                continue
            
            # Chercher le chapitre correspondant
            # Stratégie 1: Par legacy_code (pour les anciens codes style "6G20")
            chapter = await chapters_collection.find_one(
                {"legacy_code": chapitre_id},
                {"_id": 0, "code": 1}
            )
            
            # Stratégie 2: Par code directement (si chapitre_id est déjà un code MathALÉA)
            if not chapter:
                chapter = await chapters_collection.find_one(
                    {"code": chapitre_id},
                    {"_id": 0, "code": 1}
                )
            
            # Stratégie 3: Par titre + niveau (pour les anciens titres style "Nombres relatifs")
            # C'est le cas le plus courant dans notre base
            if not chapter:
                niveau = exercise.get("niveau")
                domaine = exercise.get("domaine")
                
                # Chercher par titre (insensible à la casse) et niveau
                chapter = await chapters_collection.find_one(
                    {
                        "niveau": niveau,
                        "titre": {"$regex": f".*{chapitre_id}.*", "$options": "i"}
                    },
                    {"_id": 0, "code": 1}
                )
                
                # Si toujours pas trouvé, essayer juste avec le titre sans filtrer par niveau
                if not chapter:
                    chapter = await chapters_collection.find_one(
                        {
                            "titre": {"$regex": f".*{chapitre_id}.*", "$options": "i"}
                        },
                        {"_id": 0, "code": 1}
                    )
            
            if chapter:
                # Mettre à jour l'ExerciseType
                new_chapter_code = chapter["code"]
                
                result = await exercise_types_collection.update_one(
                    {"id": exercise_id},
                    {"$set": {"chapter_code": new_chapter_code}}
                )
                
                if result.modified_count > 0:
                    updated_exercises += 1
                    logger.info(f"  ✅ {exercise_id}: chapitre_id='{chapitre_id}' → chapter_code='{new_chapter_code}'")
            else:
                # Aucun chapitre trouvé
                no_match_found += 1
                logger.warning(f"  ⚠️  ExerciseType {exercise_id}: Aucun chapitre trouvé pour chapitre_id='{chapitre_id}'")
        
        except Exception as e:
            errors += 1
            logger.error(f"  ❌ Erreur lors du traitement de l'exercice {exercise.get('id')}: {e}")
    
    # Résumé
    logger.info("\n" + "="*60)
    logger.info("📊 RÉSUMÉ DE LA MIGRATION")
    logger.info("="*60)
    logger.info(f"Total d'ExerciseType traités: {total_exercises}")
    logger.info(f"✅ Mis à jour avec succès: {updated_exercises}")
    logger.info(f"⏭️  Déjà migrés (chapter_code présent): {already_migrated}")
    logger.info(f"⚠️  Aucun chapitre correspondant trouvé: {no_match_found}")
    logger.info(f"❌ Erreurs: {errors}")
    logger.info("="*60)
    
    if updated_exercises > 0:
        logger.info(f"✅ Migration terminée avec succès! {updated_exercises} ExerciseType mis à jour.")
    else:
        logger.info("ℹ️  Aucune mise à jour nécessaire (tous les exercices sont déjà migrés).")
    
    # Fermer la connexion
    client.close()


async def verify_migration():
    """Vérifier l'état de la migration"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client.mathalea_db
    
    logger.info("\n🔍 Vérification post-migration:")
    
    # Compter les exercices avec chapter_code
    total = await db.exercise_types.count_documents({})
    with_chapter_code = await db.exercise_types.count_documents({"chapter_code": {"$ne": None}})
    with_chapitre_id = await db.exercise_types.count_documents({"chapitre_id": {"$ne": None}})
    
    logger.info(f"  Total ExerciseType: {total}")
    logger.info(f"  Avec chapitre_id: {with_chapitre_id}")
    logger.info(f"  Avec chapter_code: {with_chapter_code}")
    logger.info(f"  Taux de migration: {(with_chapter_code/total*100):.1f}%")
    
    # Afficher quelques exemples
    logger.info("\n📋 Exemples d'ExerciseType migrés:")
    exercises = await db.exercise_types.find(
        {"chapter_code": {"$ne": None}},
        {"_id": 0, "code_ref": 1, "titre": 1, "chapitre_id": 1, "chapter_code": 1}
    ).limit(3).to_list(3)
    
    for ex in exercises:
        logger.info(f"  • {ex.get('code_ref')}: '{ex.get('chapitre_id')}' → '{ex.get('chapter_code')}'")
    
    client.close()


async def main():
    """Point d'entrée principal"""
    await migrate_exercise_types()
    await verify_migration()


if __name__ == "__main__":
    asyncio.run(main())
