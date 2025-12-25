#!/usr/bin/env python3
"""
Script de diagnostic pour comprendre pourquoi 6e_G07 génère des exercices statiques.

Usage:
    python scripts/diagnostic_6e_g07.py
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'le_maitre_mot_db')


async def diagnostic_6e_g07():
    """Diagnostic complet pour 6e_G07"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("=" * 80)
    print("DIAGNOSTIC 6E_G07 - Pourquoi exercices statiques au lieu de dynamiques?")
    print("=" * 80)
    print()
    
    # 1. Vérifier le chapitre dans curriculum_chapters
    print("1. VÉRIFICATION DU CHAPITRE DANS curriculum_chapters")
    print("-" * 80)
    
    chapter_variants = ["6E_G07", "6e_G07", "6e_g07"]
    chapter_found = None
    
    for variant in chapter_variants:
        chapter = await db.curriculum_chapters.find_one(
            {"code_officiel": variant},
            {"_id": 0, "code_officiel": 1, "pipeline": 1, "enabled_generators": 1, "libelle": 1}
        )
        if chapter:
            chapter_found = chapter
            print(f"✅ Chapitre trouvé avec code_officiel='{variant}':")
            print(f"   - code_officiel: {chapter.get('code_officiel')}")
            print(f"   - libelle: {chapter.get('libelle')}")
            print(f"   - pipeline: {chapter.get('pipeline')} (type: {type(chapter.get('pipeline'))})")
            print(f"   - enabled_generators: {chapter.get('enabled_generators')}")
            break
    
    if not chapter_found:
        print("❌ Chapitre NON TROUVÉ dans curriculum_chapters avec aucun des variants:")
        for variant in chapter_variants:
            print(f"   - {variant}")
        print()
        print("Recherche dans TOUS les chapitres contenant 'G07':")
        all_g07 = await db.curriculum_chapters.find(
            {"code_officiel": {"$regex": "G07", "$options": "i"}},
            {"_id": 0, "code_officiel": 1, "pipeline": 1}
        ).to_list(10)
        for ch in all_g07:
            print(f"   - {ch.get('code_officiel')} (pipeline: {ch.get('pipeline')})")
    
    print()
    
    # 2. Vérifier les exercices dans admin_exercises
    print("2. VÉRIFICATION DES EXERCICES DANS admin_exercises")
    print("-" * 80)
    
    chapter_code_variants = ["6E_G07", "6e_G07", "6e_g07"]
    
    for variant in chapter_code_variants:
        print(f"\nRecherche avec chapter_code='{variant}':")
        
        # Total
        total = await db.admin_exercises.count_documents({"chapter_code": variant})
        print(f"   Total exercices: {total}")
        
        # Dynamiques
        dynamic = await db.admin_exercises.count_documents({
            "chapter_code": variant,
            "is_dynamic": True
        })
        print(f"   Exercices dynamiques (is_dynamic: true): {dynamic}")
        
        # Statiques
        static = await db.admin_exercises.count_documents({
            "chapter_code": variant,
            "$or": [
                {"is_dynamic": False},
                {"is_dynamic": {"$exists": False}}
            ]
        })
        print(f"   Exercices statiques (is_dynamic: false ou absent): {static}")
        
        # Détails des exercices dynamiques
        if dynamic > 0:
            print(f"\n   Détails des {dynamic} exercices dynamiques:")
            dyn_exercises = await db.admin_exercises.find(
                {"chapter_code": variant, "is_dynamic": True},
                {"_id": 0, "id": 1, "generator_key": 1, "is_dynamic": 1, "offer": 1, "difficulty": 1}
            ).to_list(10)
            for ex in dyn_exercises:
                print(f"      - id={ex.get('id')}, generator_key={ex.get('generator_key')}, "
                      f"offer={ex.get('offer')}, difficulty={ex.get('difficulty')}")
        
        # Détails des exercices statiques (premiers 3)
        if static > 0:
            print(f"\n   Détails des premiers {min(3, static)} exercices statiques:")
            static_exercises = await db.admin_exercises.find(
                {
                    "chapter_code": variant,
                    "$or": [
                        {"is_dynamic": False},
                        {"is_dynamic": {"$exists": False}}
                    ]
                },
                {"_id": 0, "id": 1, "is_dynamic": 1, "generator_key": 1, "offer": 1, "difficulty": 1, "enonce_html": 1}
            ).limit(3).to_list(3)
            for ex in static_exercises:
                enonce_preview = str(ex.get('enonce_html', ''))[:80]
                print(f"      - id={ex.get('id')}, is_dynamic={ex.get('is_dynamic')}, "
                      f"generator_key={ex.get('generator_key')}, "
                      f"offer={ex.get('offer')}, difficulty={ex.get('difficulty')}")
                print(f"        enonce_preview: {enonce_preview}...")
    
    print()
    
    # 3. Vérifier les générateurs SYMETRIE_AXIALE
    print("3. VÉRIFICATION DES GÉNÉRATEURS SYMETRIE_AXIALE")
    print("-" * 80)
    
    for variant in chapter_code_variants:
        symetrie_exercises = await db.admin_exercises.find(
            {
                "chapter_code": variant,
                "generator_key": {"$regex": "SYMETRIE", "$options": "i"}
            },
            {"_id": 0, "id": 1, "generator_key": 1, "is_dynamic": 1, "chapter_code": 1}
        ).to_list(10)
        
        if symetrie_exercises:
            print(f"\nExercices avec generator_key SYMETRIE* pour chapter_code='{variant}':")
            for ex in symetrie_exercises:
                print(f"   - id={ex.get('id')}, generator_key={ex.get('generator_key')}, "
                      f"is_dynamic={ex.get('is_dynamic')}, chapter_code={ex.get('chapter_code')}")
        else:
            print(f"\nAucun exercice avec generator_key SYMETRIE* pour chapter_code='{variant}'")
    
    print()
    
    # 4. Résumé et recommandations
    print("4. RÉSUMÉ ET RECOMMANDATIONS")
    print("-" * 80)
    
    if chapter_found:
        pipeline = chapter_found.get("pipeline")
        enabled_gens = chapter_found.get("enabled_generators", [])
        enabled_gen_keys = [eg.get("generator_key") for eg in enabled_gens if eg.get("is_enabled")]
        
        print(f"✅ Chapitre trouvé: {chapter_found.get('code_officiel')}")
        print(f"   Pipeline: {pipeline}")
        print(f"   Générateurs activés: {enabled_gen_keys}")
        
        if pipeline != "MIXED" and pipeline != "TEMPLATE":
            print(f"\n❌ PROBLÈME: Pipeline est '{pipeline}' au lieu de 'MIXED' ou 'TEMPLATE'")
            print(f"   → Solution: Mettre à jour le pipeline à 'MIXED'")
        else:
            print(f"\n✅ Pipeline correct: {pipeline}")
        
        # Vérifier si des exercices dynamiques existent
        total_dynamic = 0
        for variant in chapter_code_variants:
            count = await db.admin_exercises.count_documents({
                "chapter_code": variant,
                "is_dynamic": True
            })
            total_dynamic += count
        
        if total_dynamic == 0:
            print(f"\n❌ PROBLÈME: Aucun exercice dynamique trouvé pour 6E_G07")
            print(f"   → Solution: Créer des exercices dynamiques avec is_dynamic: true")
        else:
            print(f"\n✅ {total_dynamic} exercice(s) dynamique(s) trouvé(s)")
    
    print()
    print("=" * 80)
    print("FIN DU DIAGNOSTIC")
    print("=" * 80)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(diagnostic_6e_g07())



