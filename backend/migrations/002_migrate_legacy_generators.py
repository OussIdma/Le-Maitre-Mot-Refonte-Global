"""
Migration Sprint F.1 : Créer des ExerciseType pour chaque générateur legacy

Ce script scanne les générateurs legacy (MathExerciseType) et crée
des ExerciseType correspondants avec generator_kind="LEGACY"
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
from models.math_models import MathExerciseType
from models.mathalea_models import GeneratorKind

# Configuration MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client.mathalea_db

# Mapping des générateurs legacy vers les métadonnées ExerciseType
LEGACY_GENERATORS_METADATA = {
    # Calculs
    MathExerciseType.CALCUL_RELATIFS: {
        "code_ref": "LEGACY_CALC_REL",
        "titre": "Calculs avec nombres relatifs",
        "domaine": "Nombres et calculs",
        "chapitres": ["Nombres relatifs"],
        "niveaux": ["5e", "4e", "3e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 10,
        "default_questions": 5
    },
    MathExerciseType.CALCUL_FRACTIONS: {
        "code_ref": "LEGACY_CALC_FRAC",
        "titre": "Calculs avec fractions",
        "domaine": "Nombres et calculs",
        "chapitres": ["Fractions", "Nombres rationnels"],
        "niveaux": ["6e", "5e", "4e", "3e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 10,
        "default_questions": 5
    },
    MathExerciseType.CALCUL_DECIMAUX: {
        "code_ref": "LEGACY_CALC_DEC",
        "titre": "Calculs avec nombres décimaux",
        "domaine": "Nombres et calculs",
        "chapitres": ["Nombres décimaux", "Nombres entiers et décimaux"],
        "niveaux": ["6e", "5e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 10,
        "default_questions": 5
    },
    MathExerciseType.PUISSANCES: {
        "code_ref": "LEGACY_PUISS",
        "titre": "Calculs avec puissances",
        "domaine": "Nombres et calculs",
        "chapitres": ["Puissances"],
        "niveaux": ["4e", "3e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 10,
        "default_questions": 5
    },
    
    # Équations
    MathExerciseType.EQUATION_1ER_DEGRE: {
        "code_ref": "LEGACY_EQ_1DEG",
        "titre": "Équations du 1er degré",
        "domaine": "Nombres et calculs",
        "chapitres": ["Calcul littéral", "Équations"],
        "niveaux": ["4e", "3e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 8,
        "default_questions": 4
    },
    
    # Proportionnalité
    MathExerciseType.PROPORTIONNALITE: {
        "code_ref": "LEGACY_PROP",
        "titre": "Proportionnalité",
        "domaine": "Nombres et calculs",
        "chapitres": ["Proportionnalité"],
        "niveaux": ["6e", "5e", "4e", "3e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 8,
        "default_questions": 4
    },
    MathExerciseType.POURCENTAGES: {
        "code_ref": "LEGACY_POURC",
        "titre": "Pourcentages",
        "domaine": "Nombres et calculs",
        "chapitres": ["Proportionnalité", "Pourcentages"],
        "niveaux": ["6e", "5e", "4e", "3e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 8,
        "default_questions": 4
    },
    
    # Géométrie
    MathExerciseType.TRIANGLE_RECTANGLE: {
        "code_ref": "LEGACY_TRI_RECT",
        "titre": "Triangle rectangle - Pythagore",
        "domaine": "Espace et géométrie",
        "chapitres": ["Triangles", "Théorème de Pythagore"],
        "niveaux": ["4e", "3e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 6,
        "default_questions": 3
    },
    MathExerciseType.TRIANGLE_QUELCONQUE: {
        "code_ref": "LEGACY_TRI_QLCQ",
        "titre": "Triangle quelconque",
        "domaine": "Espace et géométrie",
        "chapitres": ["Triangles", "Angles et triangles"],
        "niveaux": ["6e", "5e", "4e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 6,
        "default_questions": 3
    },
    MathExerciseType.RECTANGLE: {
        "code_ref": "LEGACY_RECT",
        "titre": "Rectangle et quadrilatères",
        "domaine": "Espace et géométrie",
        "chapitres": ["Géométrie - Triangles et quadrilatères", "Parallélogrammes"],
        "niveaux": ["6e", "5e"],
        "difficulty_levels": ["facile", "moyen"],
        "min_questions": 1,
        "max_questions": 6,
        "default_questions": 3
    },
    MathExerciseType.CERCLE: {
        "code_ref": "LEGACY_CERCLE",
        "titre": "Cercle - Périmètre et aire",
        "domaine": "Espace et géométrie",
        "chapitres": ["Aires", "Aires et périmètres"],
        "niveaux": ["6e", "5e"],
        "difficulty_levels": ["facile", "moyen"],
        "min_questions": 1,
        "max_questions": 6,
        "default_questions": 3
    },
    MathExerciseType.PERIMETRE_AIRE: {
        "code_ref": "LEGACY_PERIM_AIRE",
        "titre": "Périmètres et aires",
        "domaine": "Espace et géométrie",
        "chapitres": ["Périmètres et aires", "Aires et périmètres", "Aires"],
        "niveaux": ["6e", "5e", "4e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 8,
        "default_questions": 4
    },
    MathExerciseType.VOLUME: {
        "code_ref": "LEGACY_VOL",
        "titre": "Volumes",
        "domaine": "Espace et géométrie",
        "chapitres": ["Volumes", "Géométrie dans l'espace"],
        "niveaux": ["6e", "5e", "4e", "3e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 6,
        "default_questions": 3
    },
    MathExerciseType.SYMETRIE_AXIALE: {
        "code_ref": "LEGACY_SYM_AX",
        "titre": "Symétrie axiale",
        "domaine": "Espace et géométrie",
        "chapitres": ["Symétrie axiale"],
        "niveaux": ["6e"],
        "difficulty_levels": ["facile", "moyen"],
        "min_questions": 1,
        "max_questions": 6,
        "default_questions": 3
    },
    MathExerciseType.SYMETRIE_CENTRALE: {
        "code_ref": "LEGACY_SYM_CENT",
        "titre": "Symétrie centrale",
        "domaine": "Espace et géométrie",
        "chapitres": ["Symétrie centrale"],
        "niveaux": ["5e"],
        "difficulty_levels": ["facile", "moyen"],
        "min_questions": 1,
        "max_questions": 6,
        "default_questions": 3
    },
    MathExerciseType.THALES: {
        "code_ref": "LEGACY_THALES",
        "titre": "Théorème de Thalès",
        "domaine": "Espace et géométrie",
        "chapitres": ["Théorème de Thalès"],
        "niveaux": ["3e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 5,
        "default_questions": 3
    },
    MathExerciseType.TRIGONOMETRIE: {
        "code_ref": "LEGACY_TRIGO",
        "titre": "Trigonométrie",
        "domaine": "Espace et géométrie",
        "chapitres": ["Trigonométrie"],
        "niveaux": ["3e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 6,
        "default_questions": 3
    },
    
    # Statistiques
    MathExerciseType.STATISTIQUES: {
        "code_ref": "LEGACY_STAT",
        "titre": "Statistiques",
        "domaine": "Organisation et gestion de données",
        "chapitres": ["Statistiques"],
        "niveaux": ["6e", "5e", "4e", "3e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 6,
        "default_questions": 3
    },
    MathExerciseType.PROBABILITES: {
        "code_ref": "LEGACY_PROBA",
        "titre": "Probabilités",
        "domaine": "Organisation et gestion de données",
        "chapitres": ["Probabilités"],
        "niveaux": ["4e", "3e"],
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "min_questions": 1,
        "max_questions": 6,
        "default_questions": 3
    },
}


async def migrate_legacy_generators():
    """Crée des ExerciseType pour chaque générateur legacy"""
    
    print("=" * 60)
    print("MIGRATION Sprint F.1: Générateurs Legacy → ExerciseType")
    print("=" * 60)
    
    exercise_types_collection = db.exercise_types
    
    # Vérifier si la migration a déjà été effectuée
    existing_count = await exercise_types_collection.count_documents({"generator_kind": "legacy"})
    if existing_count > 0:
        print(f"\n⚠️  {existing_count} ExerciseType legacy déjà existants")
        response = input("Voulez-vous réinitialiser et recréer ? (y/N): ")
        if response.lower() != 'y':
            print("Migration annulée")
            return
        
        # Supprimer les anciens
        result = await exercise_types_collection.delete_many({"generator_kind": "legacy"})
        print(f"✓ {result.deleted_count} ExerciseType legacy supprimés")
    
    print(f"\n📊 Générateurs legacy à migrer: {len(LEGACY_GENERATORS_METADATA)}")
    
    created_count = 0
    
    for legacy_type, metadata in LEGACY_GENERATORS_METADATA.items():
        try:
            # Pour chaque niveau, créer un ExerciseType
            for niveau in metadata["niveaux"]:
                exercise_type = {
                    "id": str(uuid4()),
                    "code_ref": f"{metadata['code_ref']}_{niveau}",
                    "titre": f"{metadata['titre']} ({niveau})",
                    "chapitre_id": metadata["chapitres"][0] if metadata["chapitres"] else None,
                    "niveau": niveau,
                    "domaine": metadata["domaine"],
                    "competences_ids": [],
                    "min_questions": metadata["min_questions"],
                    "max_questions": metadata["max_questions"],
                    "default_questions": metadata["default_questions"],
                    "difficulty_levels": metadata["difficulty_levels"],
                    "question_kinds": {},
                    "random_config": {},
                    "generator_kind": "legacy",
                    "legacy_generator_id": legacy_type.value,  # MathExerciseType enum value
                    "supports_seed": True,
                    "supports_ai_enonce": True,  # Legacy supporte l'enrichissement IA
                    "supports_ai_correction": True,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
                
                await exercise_types_collection.insert_one(exercise_type)
                created_count += 1
                print(f"  ✓ {exercise_type['code_ref']}: {exercise_type['titre']}")
        
        except Exception as e:
            print(f"  ❌ Erreur pour {legacy_type.value}: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Migration terminée: {created_count} ExerciseType créés")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(migrate_legacy_generators())
