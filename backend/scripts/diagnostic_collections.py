#!/usr/bin/env python3
"""
Script de diagnostic rapide pour identifier le problème d'exercices manquants.
Usage: python diagnostic_collections.py
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def diagnostic():
    """Diagnostic complet des collections MongoDB"""
    
    # Connexion MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'le_maitre_mot')
    
    print(f"\n{'='*80}")
    print(f"DIAGNOSTIC MONGODB - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Test chapitre
    chapter_code = "6E_N10"
    
    print(f"🔍 Recherche d'exercices pour chapitre: {chapter_code}\n")
    
    # 1. Vérifier collection admin_exercises (BONNE collection)
    print("─" * 80)
    print("✅ Collection: admin_exercises (CORRECT avec underscore)")
    print("─" * 80)
    
    admin_exercises = db["admin_exercises"]
    count_admin = await admin_exercises.count_documents({"chapter_code": chapter_code})
    print(f"📊 Nombre total: {count_admin} exercices")
    
    if count_admin > 0:
        print("\n📝 Exercices trouvés:")
        async for ex in admin_exercises.find({"chapter_code": chapter_code}).limit(5):
            print(f"  - ID: {ex.get('id')}")
            print(f"    Generator: {ex.get('generator_key')}")
            print(f"    Dynamic: {ex.get('is_dynamic')}")
            print(f"    Type: {ex.get('exercise_type')}")
            print()
    else:
        print("⚠️  AUCUN EXERCICE TROUVÉ dans admin_exercises!")
    
    # 2. Vérifier collection adminexercises (MAUVAISE collection - typo)
    print("\n" + "─" * 80)
    print("❌ Collection: adminexercises (INCORRECT sans underscore)")
    print("─" * 80)
    
    adminexercises_typo = db["adminexercises"]
    count_typo = await adminexercises_typo.count_documents({"chapter_code": chapter_code})
    print(f"📊 Nombre total: {count_typo} exercices")
    
    if count_typo > 0:
        print("⚠️  ATTENTION: Des exercices existent dans la MAUVAISE collection!")
        print("   Il faut migrer ces exercices vers 'admin_exercises'")
    else:
        print("✅ Aucun exercice (c'est normal, cette collection ne devrait pas exister)")
    
    # 3. Vérifier collection exercise_types
    print("\n" + "─" * 80)
    print("🔄 Collection: exercise_types (utilisée par endpoint mathalea)")
    print("─" * 80)
    
    exercise_types = db["exercise_types"]
    count_types = await exercise_types.count_documents({"chapter_code": chapter_code})
    print(f"📊 Nombre total: {count_types} exercise types")
    
    if count_types > 0:
        print("\n📝 Exercise types trouvés:")
        async for et in exercise_types.find({"chapter_code": chapter_code}).limit(5):
            print(f"  - ID: {et.get('id')}")
            print(f"    Code Ref: {et.get('code_ref')}")
            print(f"    Niveau: {et.get('niveau')}")
            print()
    else:
        print("⚠️  AUCUN EXERCISE TYPE TROUVÉ!")
        print("   C'est probablement la cause de l'erreur NO_EXERCISE_AVAILABLE")
    
    # 4. Vérifier chapters
    print("\n" + "─" * 80)
    print("📚 Collection: chapters (curriculum)")
    print("─" * 80)
    
    chapters = db["curriculum_chapters"]
    chapter_doc = await chapters.find_one({"code_officiel": chapter_code})
    
    if chapter_doc:
        print(f"✅ Chapitre trouvé:")
        print(f"  - Code: {chapter_doc.get('code_officiel')}")
        print(f"  - Libellé: {chapter_doc.get('libelle')}")
        print(f"  - Exercise Types: {chapter_doc.get('exercise_types', [])}")
    else:
        print("⚠️  Chapitre NON TROUVÉ dans la collection curriculum_chapters!")
    
    # DIAGNOSTIC FINAL
    print("\n" + "=" * 80)
    print("🎯 DIAGNOSTIC FINAL")
    print("=" * 80 + "\n")
    
    if count_admin > 0 and count_types == 0:
        print("🔴 PROBLÈME IDENTIFIÉ:")
        print("   - Exercices existent dans 'admin_exercises' ✅")
        print("   - MAIS aucun dans 'exercise_types' ❌")
        print("\n💡 SOLUTION:")
        print("   - Synchroniser admin_exercises → exercise_types")
        print("   - Utiliser le script: sync_admin_to_exercise_types.py")
    elif count_admin == 0:
        print("🔴 PROBLÈME:")
        print("   - Aucun exercice dans 'admin_exercises'")
        print("\n💡 VÉRIFICATION:")
        print("   1. L'exercice a-t-il été créé via l'Admin UI?")
        print("   2. Le chapitre code est-il correct (6E_N10 vs 6e_N10)?")
    elif count_types > 0:
        print("✅ Collections OK:")
        print("   - admin_exercises contient des exercices")
        print("   - exercise_types est synchronisé")
        print("\n🤔 Si l'erreur persiste, vérifier:")
        print("   - Les filtres (offer, difficulty)")
        print("   - Le pipeline du chapitre")
    
    # Lister toutes les collections existantes
    print("\n" + "=" * 80)
    print("📋 TOUTES LES COLLECTIONS DANS LA DB")
    print("=" * 80 + "\n")
    
    collections = await db.list_collection_names()
    for coll in sorted(collections):
        count = await db[coll].count_documents({})
        print(f"  - {coll}: {count} documents")
    
    client.close()
    
    print("\n" + "=" * 80)
    print("FIN DU DIAGNOSTIC")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(diagnostic())



