"""
Migration 008 : Unifier les bases MongoDB vers le_maitre_mot_db
================================================================

Objectif :
- Copier les collections de mathalea_db vers le_maitre_mot_db
- Préserver toutes les données existantes
- Collections à copier :
  - admin_exercises
  - curriculum_chapters
  - user_templates (si existe)
  - competences (si existe)
  - exercise_types (si existe)
  - exercise_sheets (si existe)
  - sheet_items (si existe)

Note : Cette migration est idempotente (peut être exécutée plusieurs fois).
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# Collections à migrer
COLLECTIONS_TO_MIGRATE = [
    "admin_exercises",
    "curriculum_chapters",
    "user_templates",
    "competences",
    "exercise_types",
    "exercise_sheets",
    "sheet_items",
]

SOURCE_DB = "mathalea_db"
TARGET_DB = "le_maitre_mot_db"


async def unify_databases():
    """Copie les collections de mathalea_db vers le_maitre_mot_db."""
    
    # Connexion MongoDB
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://mongo:27017")
    client = AsyncIOMotorClient(mongo_uri)
    
    source_db = client[SOURCE_DB]
    target_db = client[TARGET_DB]
    
    print(f"\n{'='*80}")
    print(f"Migration 008 : Unification des bases MongoDB")
    print(f"{'='*80}\n")
    print(f"Source : {SOURCE_DB}")
    print(f"Cible  : {TARGET_DB}\n")
    
    # Vérifier que la source existe
    source_collections = await source_db.list_collection_names()
    if not source_collections:
        print(f"⚠️  Aucune collection trouvée dans {SOURCE_DB}")
        print("   Migration non exécutée.")
        client.close()
        return
    
    print(f"📊 Collections trouvées dans {SOURCE_DB}: {len(source_collections)}")
    for coll in source_collections:
        count = await source_db[coll].count_documents({})
        print(f"   - {coll}: {count} document(s)")
    
    print(f"\n{'='*80}")
    print("🔄 Copie des collections...")
    print("-" * 80)
    
    total_copied = 0
    total_skipped = 0
    
    for collection_name in COLLECTIONS_TO_MIGRATE:
        if collection_name not in source_collections:
            print(f"⏭️  {collection_name}: n'existe pas dans {SOURCE_DB} → ignoré")
            total_skipped += 1
            continue
        
        source_coll = source_db[collection_name]
        target_coll = target_db[collection_name]
        
        # Compter les documents
        source_count = await source_coll.count_documents({})
        target_count = await target_coll.count_documents({})
        
        if source_count == 0:
            print(f"⏭️  {collection_name}: vide dans {SOURCE_DB} → ignoré")
            total_skipped += 1
            continue
        
        # Vérifier si la collection cible existe déjà
        if target_count > 0:
            print(f"⚠️  {collection_name}: {target_count} document(s) déjà présents dans {TARGET_DB}")
            print(f"   → Vérification des doublons...")
            
            # Compter les documents qui seraient dupliqués
            # (basé sur _id pour éviter les doublons)
            source_ids = set()
            async for doc in source_coll.find({}, {"_id": 1}):
                source_ids.add(str(doc.get("_id")))
            
            target_ids = set()
            async for doc in target_coll.find({}, {"_id": 1}):
                target_ids.add(str(doc.get("_id")))
            
            new_ids = source_ids - target_ids
            duplicate_count = len(source_ids) - len(new_ids)
            
            if duplicate_count > 0:
                print(f"   → {duplicate_count} document(s) déjà présents (doublons évités)")
            
            if len(new_ids) == 0:
                print(f"✅ {collection_name}: tous les documents déjà présents → ignoré")
                total_skipped += 1
                continue
            
            # Copier uniquement les nouveaux documents (ceux qui n'existent pas déjà)
            docs_to_copy = []
            async for doc in source_coll.find({}):
                # Vérifier si le document existe déjà dans la cible
                existing = await target_coll.find_one({"_id": doc.get("_id")})
                if not existing:
                    docs_to_copy.append(doc)
            
            if docs_to_copy:
                try:
                    await target_coll.insert_many(docs_to_copy, ordered=False)
                    copied = len(docs_to_copy)
                    print(f"✅ {collection_name}: {copied} nouveau(x) document(s) copié(s) (sur {source_count} total)")
                except Exception as e:
                    # Gérer les erreurs de doublons (peuvent survenir en cas de race condition)
                    print(f"⚠️  {collection_name}: Erreur lors de la copie (peut être partielle): {e}")
                    copied = 0
            else:
                print(f"✅ {collection_name}: tous les documents déjà présents → ignoré")
                copied = 0
                total_skipped += 1
        else:
            # Collection vide dans la cible → copie complète
            docs_to_copy = []
            async for doc in source_coll.find({}):
                docs_to_copy.append(doc)
            
            if docs_to_copy:
                await target_coll.insert_many(docs_to_copy, ordered=False)
                copied = len(docs_to_copy)
                print(f"✅ {collection_name}: {copied} document(s) copié(s)")
            else:
                print(f"⏭️  {collection_name}: vide → ignoré")
                total_skipped += 1
        
        if 'copied' in locals():
            total_copied += copied
    
    print(f"\n{'='*80}")
    print(f"📊 Résumé de la migration :")
    print(f"   - Collections copiées : {len(COLLECTIONS_TO_MIGRATE) - total_skipped}")
    print(f"   - Collections ignorées : {total_skipped}")
    print(f"   - Documents copiés : {total_copied}")
    print(f"\n✅ Migration terminée avec succès !")
    print(f"\n💡 Prochaines étapes :")
    print(f"   1. Mettre à jour DB_NAME dans docker-compose.yml : le_maitre_mot_db")
    print(f"   2. Mettre à jour les fichiers qui utilisent mathalea_db en dur")
    print(f"   3. Redémarrer le backend : docker compose restart backend")
    print(f"   4. Vérifier : docker compose exec backend mongosh --eval 'db.getName()'")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(unify_databases())

