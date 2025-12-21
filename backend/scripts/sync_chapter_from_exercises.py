#!/usr/bin/env python3
"""
Script de synchronisation : créer un chapitre dans le référentiel curriculum
à partir des exercices existants dans la collection exercises.

Usage:
    python scripts/sync_chapter_from_exercises.py 6e_G07_DYN
"""

import asyncio
import sys
import os
from typing import List, Set, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.curriculum_persistence_service import (
    CurriculumPersistenceService,
    ChapterCreateRequest
)


async def extract_exercise_types_from_chapter(
    db,
    chapter_code: str
) -> Set[str]:
    """
    Extrait les exercise_types uniques depuis les exercices d'un chapitre.
    
    Args:
        db: Base de données MongoDB
        chapter_code: Code du chapitre (ex: "6E_G07_DYN")
    
    Returns:
        Set d'exercise_types uniques
    """
    exercises_collection = db.exercises
    
    # Récupérer tous les exercices dynamiques du chapitre
    exercises = await exercises_collection.find(
        {
            "chapter_code": chapter_code.upper(),
            "is_dynamic": True,
            "generator_key": {"$exists": True, "$ne": None}
        },
        {"generator_key": 1}
    ).to_list(100)
    
    exercise_types = set()
    for ex in exercises:
        generator_key = ex.get("generator_key")
        if generator_key:
            # Mapper generator_key → exercise_type
            try:
                from backend.generators.factory import GeneratorFactory
                exercise_type = GeneratorFactory.get_exercise_type(generator_key) or generator_key
                exercise_types.add(exercise_type)
            except Exception:
                exercise_types.add(generator_key)
    
    return exercise_types


async def sync_chapter_from_exercises(
    chapter_code: str,
    libelle: Optional[str] = None,
    domaine: str = "Géométrie",
    statut: str = "prod"
) -> bool:
    """
    Crée un chapitre dans le référentiel curriculum à partir des exercices existants.
    
    Args:
        chapter_code: Code du chapitre (ex: "6e_G07_DYN")
        libelle: Libellé du chapitre (si None, généré automatiquement)
        domaine: Domaine mathématique (défaut: "Géométrie")
        statut: Statut du chapitre (défaut: "prod")
    
    Returns:
        True si le chapitre a été créé, False s'il existait déjà
    """
    mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    db_name = os.getenv('MONGODB_DB', 'le_maitre_mot')
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    try:
        # Normaliser le code
        chapter_code_normalized = chapter_code.upper()
        
        # Extraire les exercise_types depuis les exercices
        exercise_types = await extract_exercise_types_from_chapter(
            db,
            chapter_code_normalized
        )
        
        if not exercise_types:
            print(f"⚠️  Aucun exercice dynamique trouvé pour {chapter_code_normalized}")
            print("   Le chapitre sera créé sans exercise_types (sera marqué 'indisponible')")
            exercise_types_list = []
        else:
            exercise_types_list = sorted(list(exercise_types))
            print(f"✅ Exercise types détectés: {', '.join(exercise_types_list)}")
        
        # Générer le libellé si non fourni
        if not libelle:
            # Extraire le nom depuis le code (ex: "6e_G07_DYN" → "G07 DYN")
            parts = chapter_code_normalized.split('_')
            if len(parts) >= 2:
                libelle = f"{parts[1]} {parts[2] if len(parts) > 2 else ''}".strip()
            else:
                libelle = chapter_code_normalized
        
        # Créer le service de persistance
        service = CurriculumPersistenceService(db)
        
        # Vérifier si le chapitre existe déjà
        existing = await service.get_chapter_by_code(chapter_code_normalized)
        if existing:
            print(f"ℹ️  Le chapitre {chapter_code_normalized} existe déjà dans le référentiel curriculum")
            print(f"   Exercise types actuels: {existing.get('exercise_types', [])}")
            
            # Mettre à jour si exercise_types manquants
            if not existing.get('exercise_types') and exercise_types_list:
                from backend.services.curriculum_persistence_service import ChapterUpdateRequest
                update_request = ChapterUpdateRequest(
                    exercise_types=exercise_types_list
                )
                updated = await service.update_chapter(chapter_code_normalized, update_request)
                print(f"✅ Chapitre mis à jour avec exercise_types: {updated.get('exercise_types')}")
                return True
            else:
                return False
        
        # Créer le chapitre
        create_request = ChapterCreateRequest(
            code_officiel=chapter_code_normalized,
            libelle=libelle,
            domaine=domaine,
            exercise_types=exercise_types_list,
            statut=statut,
            difficulte_min=1,
            difficulte_max=3,
            schema_requis=any(
                et in ["SYMETRIE_AXIALE", "THALES", "TRIANGLE_QUELCONQUE", "RECTANGLE", "CERCLE"]
                for et in exercise_types_list
            )
        )
        
        chapter = await service.create_chapter(create_request)
        
        print(f"✅ Chapitre créé: {chapter_code_normalized}")
        print(f"   Libellé: {libelle}")
        print(f"   Domaine: {domaine}")
        print(f"   Exercise types: {exercise_types_list}")
        print(f"   Statut: {statut}")
        
        return True
    
    except ValueError as e:
        print(f"❌ Erreur: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()


async def main():
    """Point d'entrée du script"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/sync_chapter_from_exercises.py <chapter_code> [libelle] [domaine] [statut]")
        print("Exemple: python scripts/sync_chapter_from_exercises.py 6e_G07_DYN 'Symétrie axiale (dynamique)' 'Géométrie' 'prod'")
        sys.exit(1)
    
    chapter_code = sys.argv[1]
    libelle = sys.argv[2] if len(sys.argv) > 2 else None
    domaine = sys.argv[3] if len(sys.argv) > 3 else "Géométrie"
    statut = sys.argv[4] if len(sys.argv) > 4 else "prod"
    
    print(f"🔄 Synchronisation du chapitre {chapter_code}...")
    success = await sync_chapter_from_exercises(
        chapter_code,
        libelle=libelle,
        domaine=domaine,
        statut=statut
    )
    
    if success:
        print("\n✅ Synchronisation terminée avec succès!")
        print("   Le chapitre devrait maintenant apparaître dans le catalogue.")
        print("   Rechargez le générateur pour voir le changement.")
    else:
        print("\n⚠️  Synchronisation terminée (chapitre existant ou erreur)")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())




