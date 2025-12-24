"""
Migration 009: Initialisation collection user_exercises (P3.0)

Crée la collection et les index nécessaires pour la bibliothèque d'exercices utilisateur.
Compatible MongoDB - Non destructif
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Charger les variables d'environnement
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')


async def migrate():
    """Exécuter la migration"""
    print("🚀 Migration 009: Initialisation user_exercises (P3.0)")
    
    # Connexion MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    if not mongo_url:
        raise ValueError("MONGO_URL environment variable is required")
    
    client = AsyncIOMotorClient(mongo_url)
    db_name = os.environ.get('DB_NAME', 'le_maitre_mot_db')
    db = client[db_name]
    
    try:
        # ====================================================================
        # Collection: user_exercises
        # ====================================================================
        print("\n📚 Création collection: user_exercises")
        user_exercises = db.user_exercises
        
        # Créer les index
        # Index composé pour tri par user_email et created_at DESC
        await user_exercises.create_index(
            [("user_email", 1), ("created_at", -1)],
            name="user_email_created_at_compound"
        )
        print("   ✅ Index créé: user_email + created_at DESC")
        
        # Index unique pour éviter doublons (user_email + exercise_uid)
        await user_exercises.create_index(
            [("user_email", 1), ("exercise_uid", 1)],
            unique=True,
            name="user_email_exercise_uid_unique"
        )
        print("   ✅ Index unique créé: user_email + exercise_uid")
        
        # Index pour filtres (code_officiel, difficulty)
        await user_exercises.create_index("code_officiel")
        await user_exercises.create_index("difficulty")
        print("   ✅ Index créés: code_officiel, difficulty")
        
        # ====================================================================
        # Vérification
        # ====================================================================
        print("\n🔍 Vérification de la collection...")
        collections = await db.list_collection_names()
        
        if "user_exercises" in collections:
            count = await db.user_exercises.count_documents({})
            print(f"   ✅ user_exercises: {count} documents")
        else:
            print(f"   ⚠️  user_exercises: Collection non trouvée")
        
        print("\n✨ Migration 009 terminée avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(migrate())




