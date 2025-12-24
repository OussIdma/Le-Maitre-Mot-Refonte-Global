"""
Migration 010: Initialisation collection user_sheets (P3.1)

Collection pour les fiches d'exercices des utilisateurs.
Une fiche = une liste ordonnée d'exercices sauvegardés (user_exercises).
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "le_maitre_mot_db")


async def run_migration():
    """Initialise la collection user_sheets"""
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    try:
        print("🚀 Migration 010: Initialisation user_sheets (P3.1)")
        print("=" * 60)
        
        # Vérifier si la collection existe déjà
        collections = await db.list_collection_names()
        
        if "user_sheets" in collections:
            print("\n⚠️  Collection user_sheets existe déjà")
            count = await db.user_sheets.count_documents({})
            print(f"   📊 Nombre de documents: {count}")
            
            # Vérifier les index
            indexes = await db.user_sheets.list_indexes().to_list(length=10)
            index_names = [idx.get("name") for idx in indexes]
            
            if "user_email_1" in index_names:
                print("   ✅ Index user_email existe")
            else:
                print("   ⚠️  Index user_email manquant - création...")
                await db.user_sheets.create_index("user_email")
                print("   ✅ Index user_email créé")
            
            if "sheet_uid_1" in index_names:
                print("   ✅ Index sheet_uid unique existe")
            else:
                print("   ⚠️  Index sheet_uid unique manquant - création...")
                await db.user_sheets.create_index("sheet_uid", unique=True)
                print("   ✅ Index sheet_uid unique créé")
            
            return
        
        # Collection: user_sheets
        print("\n📚 Création collection: user_sheets")
        user_sheets = db.user_sheets
        
        # Créer les index
        print("\n📑 Création des index...")
        
        # Index sur user_email pour les requêtes de listing
        await user_sheets.create_index("user_email")
        print("   ✅ Index créé: user_email")
        
        # Index unique sur sheet_uid pour éviter les doublons
        await user_sheets.create_index("sheet_uid", unique=True)
        print("   ✅ Index unique créé: sheet_uid")
        
        # Index sur created_at pour le tri
        await user_sheets.create_index("created_at")
        print("   ✅ Index créé: created_at")
        
        print("\n✅ Migration 010 terminée avec succès")
        
        # Afficher le résumé des collections
        print("\n📊 Résumé des collections:")
        collections = await db.list_collection_names()
        for coll_name in sorted(collections):
            if coll_name.startswith("user_"):
                count = await db[coll_name].count_documents({})
                print(f"   ✅ {coll_name}: {count} documents")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(run_migration())

