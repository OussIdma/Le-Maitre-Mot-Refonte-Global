"""
Migration 001: Initialisation des collections MathALÉA

Crée les collections et index nécessaires pour le système MathALÉA
Compatible avec MongoDB - Non destructif
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
    print("🚀 Migration 001: Initialisation MathALÉA System")
    
    # Connexion MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    if not mongo_url:
        raise ValueError("MONGO_URL environment variable is required")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'lemaitremot')]
    
    try:
        # ====================================================================
        # Collection: mathalea_competences
        # ====================================================================
        print("\n📚 Création collection: mathalea_competences")
        competences = db.mathalea_competences
        
        # Créer les index
        await competences.create_index("id", unique=True)
        await competences.create_index("code", unique=True)
        await competences.create_index([("niveau", 1), ("domaine", 1)])
        
        print("   ✅ Index créés: id (unique), code (unique), niveau+domaine")
        
        # ====================================================================
        # Collection: mathalea_exercise_types
        # ====================================================================
        print("\n📝 Création collection: mathalea_exercise_types")
        exercise_types = db.mathalea_exercise_types
        
        # Créer les index
        await exercise_types.create_index("id", unique=True)
        await exercise_types.create_index("code_ref", unique=True)
        await exercise_types.create_index([("niveau", 1), ("domaine", 1)])
        await exercise_types.create_index("chapitre_id")
        await exercise_types.create_index("generator_kind")
        await exercise_types.create_index("created_at")
        
        print("   ✅ Index créés: id, code_ref (unique), niveau+domaine, chapitre_id, generator_kind, created_at")
        
        # ====================================================================
        # Collection: mathalea_exercise_sheets
        # ====================================================================
        print("\n📋 Création collection: mathalea_exercise_sheets")
        sheets = db.mathalea_exercise_sheets
        
        # Créer les index
        await sheets.create_index("id", unique=True)
        await sheets.create_index("owner_id")
        await sheets.create_index([("owner_id", 1), ("niveau", 1)])
        await sheets.create_index("created_at")
        
        print("   ✅ Index créés: id (unique), owner_id, owner_id+niveau, created_at")
        
        # ====================================================================
        # Collection: mathalea_sheet_items
        # ====================================================================
        print("\n📌 Création collection: mathalea_sheet_items")
        items = db.mathalea_sheet_items
        
        # Créer les index
        await items.create_index("id", unique=True)
        await items.create_index([("sheet_id", 1), ("order", 1)])
        await items.create_index("exercise_type_id")
        
        print("   ✅ Index créés: id (unique), sheet_id+order, exercise_type_id")
        
        # ====================================================================
        # Vérification
        # ====================================================================
        print("\n🔍 Vérification des collections...")
        collections = await db.list_collection_names()
        
        required_collections = [
            "mathalea_competences",
            "mathalea_exercise_types",
            "mathalea_exercise_sheets",
            "mathalea_sheet_items"
        ]
        
        for coll in required_collections:
            if coll in collections:
                count = await db[coll].count_documents({})
                print(f"   ✅ {coll}: {count} documents")
            else:
                print(f"   ⚠️  {coll}: Collection non trouvée")
        
        print("\n✨ Migration 001 terminée avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {e}")
        raise
    finally:
        client.close()


async def rollback():
    """Rollback de la migration (optionnel)"""
    print("🔄 Rollback Migration 001")
    
    mongo_url = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'lemaitremot')]
    
    try:
        # Supprimer les collections (DANGER: À utiliser avec précaution)
        collections_to_drop = [
            "mathalea_competences",
            "mathalea_exercise_types",
            "mathalea_exercise_sheets",
            "mathalea_sheet_items"
        ]
        
        for coll in collections_to_drop:
            await db[coll].drop()
            print(f"   🗑️  Collection supprimée: {coll}")
        
        print("\n✅ Rollback terminé")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du rollback: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())
