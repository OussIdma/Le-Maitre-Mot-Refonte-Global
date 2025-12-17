"""
Migration 003 : Créer des ExerciseType pour les générateurs SPRINT 1-4 (niveau 6e)

Ce script crée des ExerciseType dans MongoDB pour les 19 chapitres 6e
implémentés dans les SPRINTs 1, 2, 3 et 4.

Les générateurs utilisent generator_kind="template" et sont liés aux chapitres
via chapter_code (ex: 6e_G01, 6e_N01, etc.)
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
import os

# Configuration MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client.mathalea_db

exercise_types_collection = db.exercise_types
chapters_collection = db.chapters

# Mapping des 19 chapitres SPRINT 1-4 vers leurs métadonnées
SPRINT_GENERATORS_METADATA = {
    # ========== SPRINT 1 (3 chapitres) ==========
    "Perpendiculaires et parallèles à la règle et à l'équerre": {
        "chapter_code": "6e_G03",
        "code_ref": "SPRINT_G03",
        "domaine": "Géométrie",
        "niveau": "6e"
    },
    "Droite numérique et repérage": {
        "chapter_code": "6e_N03",
        "code_ref": "SPRINT_N03",
        "domaine": "Nombres et calculs",
        "niveau": "6e"
    },
    "Lire et compléter des tableaux de données": {
        "chapter_code": "6e_SP01",
        "code_ref": "SPRINT_SP01",
        "domaine": "Organisation et gestion de données",
        "niveau": "6e"
    },
    
    # ========== SPRINT 2 (5 chapitres) ==========
    "Points, segments, droites, demi-droites": {
        "chapter_code": "6e_G01",
        "code_ref": "SPRINT_G01",
        "domaine": "Géométrie",
        "niveau": "6e"
    },
    "Alignement, milieu d'un segment": {
        "chapter_code": "6e_G02",
        "code_ref": "SPRINT_G02",
        "domaine": "Géométrie",
        "niveau": "6e"
    },
    "Lire et écrire les nombres entiers": {
        "chapter_code": "6e_N01",
        "code_ref": "SPRINT_N01",
        "domaine": "Nombres et calculs",
        "niveau": "6e"
    },
    "Comparer et ranger des nombres entiers": {
        "chapter_code": "6e_N02",
        "code_ref": "SPRINT_N02",
        "domaine": "Nombres et calculs",
        "niveau": "6e"
    },
    "Addition et soustraction de nombres entiers": {
        "chapter_code": "6e_N04",
        "code_ref": "SPRINT_N04",
        "domaine": "Nombres et calculs",
        "niveau": "6e"
    },
    
    # ========== SPRINT 3 (5 chapitres) ==========
    "Triangles (construction et classification)": {
        "chapter_code": "6e_G04",
        "code_ref": "SPRINT_G04",
        "domaine": "Géométrie",
        "niveau": "6e"
    },
    "Quadrilatères usuels (carré, rectangle, losange, parallélogramme)": {
        "chapter_code": "6e_G05",
        "code_ref": "SPRINT_G05",
        "domaine": "Géométrie",
        "niveau": "6e"
    },
    "Multiplication de nombres entiers": {
        "chapter_code": "6e_N05",
        "code_ref": "SPRINT_N05",
        "domaine": "Nombres et calculs",
        "niveau": "6e"
    },
    "Division euclidienne": {
        "chapter_code": "6e_N06",
        "code_ref": "SPRINT_N06",
        "domaine": "Nombres et calculs",
        "niveau": "6e"
    },
    "Multiples et diviseurs, critères de divisibilité": {
        "chapter_code": "6e_N07",
        "code_ref": "SPRINT_N07",
        "domaine": "Nombres et calculs",
        "niveau": "6e"
    },
    
    # ========== SPRINT 4 (6 chapitres) ==========
    "Fractions comme partage et quotient": {
        "chapter_code": "6e_N08",
        "code_ref": "SPRINT_N08",
        "domaine": "Nombres et calculs",
        "niveau": "6e"
    },
    "Fractions simples de l'unité": {
        "chapter_code": "6e_N09",
        "code_ref": "SPRINT_N09",
        "domaine": "Nombres et calculs",
        "niveau": "6e"
    },
    "Mesurer et comparer des longueurs": {
        "chapter_code": "6e_GM01",
        "code_ref": "SPRINT_GM01",
        "domaine": "Grandeurs et mesures",
        "niveau": "6e"
    },
    "Périmètre de figures usuelles": {
        "chapter_code": "6e_GM02",
        "code_ref": "SPRINT_GM02",
        "domaine": "Grandeurs et mesures",
        "niveau": "6e"
    },
    "Aire du rectangle et du carré": {
        "chapter_code": "6e_GM03",
        "code_ref": "SPRINT_GM03",
        "domaine": "Grandeurs et mesures",
        "niveau": "6e"
    },
    "Diagrammes en barres et pictogrammes": {
        "chapter_code": "6e_SP02",
        "code_ref": "SPRINT_SP02",
        "domaine": "Organisation et gestion de données",
        "niveau": "6e"
    }
}


async def migrate_sprint_generators():
    """Crée des ExerciseType pour chaque générateur SPRINT 1-4"""
    
    print("=" * 60)
    print("🚀 Migration 003 : ExerciseType pour générateurs SPRINT 1-4")
    print("=" * 60)
    print(f"\n📚 {len(SPRINT_GENERATORS_METADATA)} chapitres à migrer\n")
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    for chapter_title, metadata in SPRINT_GENERATORS_METADATA.items():
        try:
            # 1. Vérifier que le chapitre existe dans MongoDB
            chapter = await chapters_collection.find_one(
                {"code": metadata["chapter_code"]},
                {"_id": 0, "titre": 1, "code": 1, "niveau": 1, "domaine": 1}
            )
            
            if not chapter:
                print(f"  ⚠️  Chapitre {metadata['chapter_code']} non trouvé dans MongoDB, skip")
                skipped_count += 1
                continue
            
            # 2. Vérifier si l'ExerciseType existe déjà
            existing = await exercise_types_collection.find_one({
                "chapter_code": metadata["chapter_code"]
            })
            
            if existing:
                print(f"  ⏭️  {metadata['chapter_code']} : ExerciseType déjà existant, skip")
                skipped_count += 1
                continue
            
            # 3. Créer l'ExerciseType
            exercise_type = {
                "id": str(uuid4()),
                "code_ref": metadata["code_ref"],
                "titre": chapter_title,
                "chapitre_id": None,  # Legacy, non utilisé
                "chapter_code": metadata["chapter_code"],
                "niveau": metadata["niveau"],
                "domaine": metadata["domaine"],
                "competences_ids": [],
                "min_questions": 1,
                "max_questions": 10,
                "default_questions": 5,
                "difficulty_levels": ["facile", "moyen", "difficile"],
                "question_kinds": {},
                "random_config": {},
                "generator_kind": "template",  # ✅ Générateur template (SPRINT)
                "legacy_generator_id": None,  # Pas de générateur legacy
                "supports_seed": True,
                "supports_ai_enonce": True,  # Supporte enrichissement IA
                "supports_ai_correction": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            await exercise_types_collection.insert_one(exercise_type)
            created_count += 1
            print(f"  ✅ {metadata['chapter_code']} : {chapter_title[:50]}...")
        
        except Exception as e:
            print(f"  ❌ Erreur pour {metadata['chapter_code']}: {e}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Migration terminée:")
    print(f"   - {created_count} ExerciseType créés")
    print(f"   - {skipped_count} ExerciseType déjà existants ou chapitres non trouvés")
    print(f"   - {error_count} erreurs")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(migrate_sprint_generators())
