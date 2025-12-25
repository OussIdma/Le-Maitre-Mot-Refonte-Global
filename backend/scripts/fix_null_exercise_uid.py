#!/usr/bin/env python3
"""
Script pour corriger les exercices avec exercise_uid=null
Causes: exercices créés avant l'ajout du calcul de exercise_uid
"""
import asyncio
import hashlib
import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "le_maitre_mot_db")


def compute_exercise_uid(
    chapter_code: str,
    enonce_content: str,
    solution_content: str,
    difficulty: str = "moyen"
) -> str:
    """Calcule un UID stable pour un exercice"""
    normalized_enonce = enonce_content.strip().lower()
    normalized_solution = solution_content.strip().lower()
    unique_string = f"{chapter_code}|{normalized_enonce}|{normalized_solution}|{difficulty}"
    return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()


async def fix_null_uids():
    """Corrige tous les exercices avec exercise_uid=null"""
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db['admin_exercises']
    
    try:
        # Trouver tous les exercices avec exercise_uid null
        exercises = await collection.find({'exercise_uid': None}).to_list(100)
        
        print(f'📊 Exercices avec exercise_uid=null: {len(exercises)}')
        
        if len(exercises) == 0:
            print('✅ Aucun exercice à corriger')
            return
        
        fixed = 0
        conflicts = 0
        
        for ex in exercises:
            chapter_code = ex.get('chapter_code', '')
            is_dynamic = ex.get('is_dynamic', False)
            ex_id = ex.get('id')
            
            # Calculer l'UID
            if is_dynamic:
                enonce_content = ex.get('enonce_template_html', '') or ''
                solution_content = ex.get('solution_template_html', '') or ''
            else:
                enonce_content = ex.get('enonce_html', '') or ''
                solution_content = ex.get('solution_html', '') or ''
            
            difficulty = ex.get('difficulty', 'moyen').lower()
            exercise_uid = compute_exercise_uid(
                chapter_code, enonce_content, solution_content, difficulty
            )
            
            # Vérifier si cet UID existe déjà (pour un autre exercice)
            existing = await collection.find_one({
                'exercise_uid': exercise_uid,
                '_id': {'$ne': ex.get('_id')}
            })
            
            if existing:
                conflicts += 1
                print(
                    f'⚠️  Conflit UID pour exercice ID={ex_id}, chapter={chapter_code}. '
                    f'UID={exercise_uid[:8]}... existe déjà pour un autre exercice.'
                )
                # Générer un UID unique avec timestamp
                import time
                unique_string = f"{chapter_code}|{enonce_content}|{solution_content}|{difficulty}|{time.time()}"
                exercise_uid = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()
                print(f'   → Nouvel UID généré: {exercise_uid[:8]}...')
            
            # Mettre à jour avec $set
            result = await collection.update_one(
                {'_id': ex.get('_id')},
                {'$set': {'exercise_uid': exercise_uid}}
            )
            
            if result.modified_count > 0:
                fixed += 1
                print(f'✅ Corrigé exercice ID={ex_id}, chapter={chapter_code}, UID={exercise_uid[:8]}...')
        
        print(f'\n📊 Résumé:')
        print(f'   ✅ {fixed} exercice(s) corrigé(s)')
        if conflicts > 0:
            print(f'   ⚠️  {conflicts} conflit(s) résolu(s) avec UID unique')
        
    finally:
        client.close()


if __name__ == '__main__':
    asyncio.run(fix_null_uids())




