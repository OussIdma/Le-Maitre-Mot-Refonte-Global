#!/usr/bin/env python3
"""
Script de backfill pour nettoyer les exercices sauvegardés avec accolades résiduelles.

Problème P3.0.1 : Les exercices sauvegardés avant la correction de render_template()
peuvent contenir des accolades { } autour des tableaux/schémas dans enonce_html.

Ce script :
1. Détecte les exercices avec accolades résiduelles
2. Nettoie les accolades autour des tableaux/SVG
3. Marque les exercices backfillés dans metadata
"""
import asyncio
import sys
import os
import re
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "le_maitre_mot_db")


def clean_html_accolades(html: str) -> str:
    """
    Nettoie les accolades résiduelles autour des tableaux/SVG.
    
    Patterns à nettoyer :
    - {<table>...</table>} → <table>...</table>
    - {<svg>...</svg>} → <svg>...</svg>
    - {<div class="table">...</div>} → <div class="table">...</div>
    """
    if not html:
        return html
    
    # Pattern 1: Accolades autour de <table>...</table>
    # {<table ...>...</table>} → <table ...>...</table>
    html = re.sub(
        r'\{(\s*<table[^>]*>.*?</table>\s*)\}',
        r'\1',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # Pattern 2: Accolades autour de <svg>...</svg>
    # {<svg ...>...</svg>} → <svg ...>...</svg>
    html = re.sub(
        r'\{(\s*<svg[^>]*>.*?</svg>\s*)\}',
        r'\1',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # Pattern 3: Accolades autour de div avec classe "table" ou "tableau"
    # {<div class="table">...</div>} → <div class="table">...</div>
    html = re.sub(
        r'\{(\s*<div[^>]*class=["\'].*table[^"\']*["\'][^>]*>.*?</div>\s*)\}',
        r'\1',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    return html


def has_accolades_issue(html: str) -> bool:
    """Détecte si le HTML contient des accolades problématiques autour de tableaux/SVG."""
    if not html:
        return False
    
    # Chercher des patterns problématiques
    patterns = [
        r'\{<table',  # {<table
        r'</table>\}',  # </table>}
        r'\{<svg',  # {<svg
        r'</svg>\}',  # </svg>}
    ]
    
    for pattern in patterns:
        if re.search(pattern, html, re.IGNORECASE):
            return True
    
    return False


async def backfill_exercises(dry_run: bool = True):
    """Nettoie les exercices avec accolades résiduelles."""
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db['user_exercises']
    
    try:
        # Trouver tous les exercices
        exercises = await collection.find({}).to_list(1000)
        
        print(f'📊 Exercices trouvés: {len(exercises)}')
        
        issues_found = 0
        cleaned = 0
        errors = 0
        
        for ex in exercises:
            ex_id = ex.get('_id')
            exercise_uid = ex.get('exercise_uid', 'N/A')[:20]
            enonce_html = ex.get('enonce_html', '')
            solution_html = ex.get('solution_html', '')
            
            # Vérifier si problème
            has_enonce_issue = has_accolades_issue(enonce_html)
            has_solution_issue = has_accolades_issue(solution_html)
            
            if not has_enonce_issue and not has_solution_issue:
                continue
            
            issues_found += 1
            print(f'\n🔍 Exercice {exercise_uid}... (ID: {ex_id})')
            
            # Nettoyer
            cleaned_enonce = clean_html_accolades(enonce_html)
            cleaned_solution = clean_html_accolades(solution_html)
            
            if cleaned_enonce != enonce_html or cleaned_solution != solution_html:
                print(f'  ✅ Accolades détectées et nettoyées')
                
                if not dry_run:
                    # Mettre à jour
                    update_data = {}
                    if cleaned_enonce != enonce_html:
                        update_data['enonce_html'] = cleaned_enonce
                    if cleaned_solution != solution_html:
                        update_data['solution_html'] = cleaned_solution
                    
                    # Marquer comme backfillé
                    metadata = ex.get('metadata', {})
                    metadata['backfilled'] = True
                    metadata['backfilled_at'] = asyncio.get_event_loop().time()
                    update_data['metadata'] = metadata
                    
                    result = await collection.update_one(
                        {'_id': ex_id},
                        {'$set': update_data}
                    )
                    
                    if result.modified_count > 0:
                        cleaned += 1
                        print(f'  ✅ Exercice nettoyé et mis à jour')
                    else:
                        errors += 1
                        print(f'  ⚠️  Échec mise à jour')
                else:
                    cleaned += 1
                    print(f'  [DRY-RUN] Serait nettoyé')
            else:
                print(f'  ⚠️  Accolades détectées mais nettoyage non effectif')
        
        print(f'\n📊 Résumé:')
        print(f'   🔍 Exercices avec problèmes: {issues_found}')
        print(f'   ✅ Exercices nettoyés: {cleaned}')
        if errors > 0:
            print(f'   ❌ Erreurs: {errors}')
        
        if dry_run:
            print(f'\n⚠️  Mode DRY-RUN - Aucune modification effectuée')
            print(f'   Pour appliquer: python {sys.argv[0]} --apply')
        else:
            print(f'\n✅ Backfill terminé')
        
    finally:
        client.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Backfill exercices avec accolades résiduelles')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Mode dry-run (par défaut)')
    parser.add_argument('--apply', action='store_true', help='Appliquer les modifications')
    
    args = parser.parse_args()
    
    # Si --apply est spécifié, désactiver dry-run
    dry_run = not args.apply
    
    asyncio.run(backfill_exercises(dry_run=dry_run))

