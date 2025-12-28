#!/usr/bin/env python3
"""
Script de synchronisation admin_exercises → exercise_types

Ce script synchronise tous les exercices dynamiques de admin_exercises
vers la collection exercise_types pour qu'ils soient visibles par
l'endpoint /api/mathalea/chapters/{chapter_code}/exercise-types

Usage:
    python sync_admin_to_exercise_types.py [--chapter CHAPTER_CODE] [--dry-run]
    
Arguments:
    --chapter CHAPTER_CODE : Synchroniser uniquement un chapitre spécifique
    --dry-run : Mode simulation (ne modifie pas la DB)
"""

import os
import sys
import asyncio
import argparse
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

# Importer la factory pour obtenir exercise_type depuis generator_key
sys.path.insert(0, '/app/backend')
from generators.factory import GeneratorFactory

async def sync_admin_to_exercise_types(
    db, 
    chapter_code=None, 
    dry_run=False
):
    """
    Synchronise les exercices admin_exercises vers exercise_types
    
    Args:
        db: Instance MongoDB
        chapter_code: Code du chapitre (optionnel, None = tous)
        dry_run: Si True, n'écrit pas en DB (simulation)
    """
    
    admin_exercises = db["admin_exercises"]
    exercise_types = db["exercise_types"]
    
    # Construire le filtre
    query = {"is_dynamic": True}
    if chapter_code:
        query["chapter_code"] = chapter_code.upper().replace("-", "_")
    
    print(f"\n{'='*80}")
    print(f"SYNCHRONISATION admin_exercises → exercise_types")
    print(f"{'='*80}\n")
    print(f"Mode: {'🔍 DRY-RUN (simulation)' if dry_run else '✍️  ÉCRITURE EN DB'}")
    print(f"Filtre: {query}\n")
    
    # Compter les exercices à synchroniser
    total_exercises = await admin_exercises.count_documents(query)
    print(f"📊 {total_exercises} exercices dynamiques à traiter\n")
    
    if total_exercises == 0:
        print("⚠️  Aucun exercice dynamique trouvé!")
        return
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    # Traiter chaque exercice
    async for ex in admin_exercises.find(query):
        chapter = ex.get("chapter_code")
        generator_key = ex.get("generator_key")
        
        if not generator_key:
            print(f"⚠️  Exercice {ex.get('id')} sans generator_key, ignoré")
            skipped_count += 1
            continue
        
        print(f"🔄 Traitement: {chapter}/{generator_key}")
        
        # Vérifier si exercise_type existe déjà
        existing = await exercise_types.find_one({
            "code_ref": generator_key,
            "chapter_code": chapter
        })
        
        if existing:
            print(f"  ⏭️  Déjà existant (id: {existing.get('id')})")
            skipped_count += 1
            continue
        
        # Obtenir exercise_type depuis GeneratorFactory
        try:
            exercise_type_name = GeneratorFactory.get_exercise_type(generator_key)
            
            if not exercise_type_name:
                # Fallback: utiliser generator_key comme exercise_type
                exercise_type_name = generator_key
                print(f"  ⚠️  Pas de mapping, utilise generator_key: {generator_key}")
            else:
                print(f"  ✅ Exercise type: {exercise_type_name}")
            
            # Extraire niveau depuis chapter_code (ex: "6E_N10" → "6E")
            niveau = chapter.split('_')[0] if chapter else "6E"
            
            # Créer le document exercise_type
            exercise_type_doc = {
                "id": f"{chapter}_{generator_key}_{uuid.uuid4().hex[:8]}",
                "code_ref": generator_key,
                "chapter_code": chapter,
                "chapitre_id": chapter,  # Fallback legacy
                "niveau": niveau,
                "domaine": _infer_domain(chapter),
                "libelle": f"Exercice {generator_key}",
                "description": f"Exercice dynamique généré par {generator_key}",
                "generator_kind": "DYNAMIC",
                "difficulty_levels": ["facile", "moyen", "difficile"],
                "min_questions": 1,
                "max_questions": 10,
                "requires_svg": ex.get("needs_svg", False),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "source": "admin_exercises_sync"
            }
            
            if not dry_run:
                # Insérer en DB
                await exercise_types.insert_one(exercise_type_doc)
                print(f"  ✅ Créé: {exercise_type_doc['id']}")
            else:
                print(f"  🔍 [DRY-RUN] Créerait: {exercise_type_doc['id']}")
            
            created_count += 1
            
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            error_count += 1
    
    # Résumé
    print(f"\n{'='*80}")
    print(f"📊 RÉSUMÉ")
    print(f"{'='*80}\n")
    print(f"  ✅ Créés: {created_count}")
    print(f"  ⏭️  Ignorés (déjà existants): {skipped_count}")
    print(f"  ❌ Erreurs: {error_count}")
    print(f"  📝 Total traité: {created_count + skipped_count + error_count}/{total_exercises}")
    
    if dry_run:
        print(f"\n🔍 Mode DRY-RUN: Aucune modification en DB")
        print(f"   Pour appliquer les changements, relancer sans --dry-run")
    else:
        print(f"\n✅ Synchronisation terminée!")
    
    print(f"\n{'='*80}\n")

def _infer_domain(chapter_code):
    """Inférer le domaine mathématique depuis le code chapitre"""
    if not chapter_code:
        return "Géométrie"
    
    # Ex: "6E_GM07" → "GM" → "Géométrie et Mesures"
    parts = chapter_code.split('_')
    if len(parts) >= 2:
        domain_code = parts[1][:1]  # Premier caractère (G, N, C, etc.)
        
        domain_map = {
            'G': 'Géométrie',
            'N': 'Nombres',
            'C': 'Calcul',
            'A': 'Algèbre',
            'F': 'Fonctions',
            'S': 'Statistiques',
            'P': 'Probabilités',
            'M': 'Mesures'
        }
        
        return domain_map.get(domain_code, 'Géométrie')
    
    return 'Géométrie'

async def main():
    parser = argparse.ArgumentParser(
        description='Synchroniser admin_exercises → exercise_types'
    )
    parser.add_argument(
        '--chapter',
        type=str,
        help='Code du chapitre à synchroniser (ex: 6E_N10)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Mode simulation (ne modifie pas la DB)'
    )
    
    args = parser.parse_args()
    
    # Connexion MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'lemaitremotdb')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        await sync_admin_to_exercise_types(
            db,
            chapter_code=args.chapter,
            dry_run=args.dry_run
        )
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
