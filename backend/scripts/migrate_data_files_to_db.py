#!/usr/bin/env python3
"""
Migration script: migrate_data_files_to_db.py

Lit les fichiers gm07_exercises.py, gm08_exercises.py, tests_dyn_exercises.py
Insère/upsert dans MongoDB (admin_exercises) si absent
Affiche un résumé: inserted/updated/skipped
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone
import hashlib

# Add backend to path to import modules
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from motor.motor_asyncio import AsyncIOMotorClient
from backend.constants.collections import EXERCISES_COLLECTION


async def connect_to_db():
    """Connect to MongoDB"""
    # Get MongoDB connection details from environment or use defaults
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "lemaitremot")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    return db


def load_exercises_from_file(file_path, chapter_code):
    """Load exercises from Python file"""
    import importlib.util
    
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return []
    
    spec = importlib.util.spec_from_file_location("exercises_module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Find the exercises list (usually named GM07_EXERCISES, GM08_EXERCISES, etc.)
    for attr_name in dir(module):
        attr_value = getattr(module, attr_name)
        if isinstance(attr_value, list) and len(attr_value) > 0:
            # Check if it looks like exercises (has 'id' or 'enonce_html' fields)
            if len(attr_value) > 0 and isinstance(attr_value[0], dict):
                if 'id' in attr_value[0] or 'enonce_html' in attr_value[0]:
                    print(f"Found exercises list: {attr_name} with {len(attr_value)} exercises")
                    # Add chapter_code to each exercise
                    for exercise in attr_value:
                        exercise['chapter_code'] = chapter_code
                    return attr_value
    
    return []


def calculate_exercise_uid(exercise, chapter_code):
    """Calculate a stable UID for an exercise based on its content"""
    enonce_content = exercise.get('enonce_html', '').strip().lower()
    solution_content = exercise.get('solution_html', '').strip().lower()
    difficulty = exercise.get('difficulty', 'moyen').lower()
    
    unique_string = f"{chapter_code}|{enonce_content}|{solution_content}|{difficulty}"
    return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()


async def migrate_file_to_db(db, file_path, chapter_code):
    """Migrate exercises from a Python file to MongoDB"""
    print(f"\nMigrating {file_path} for chapter {chapter_code}...")
    
    # Load exercises from file
    exercises = load_exercises_from_file(file_path, chapter_code)
    if not exercises:
        print(f"No exercises found in {file_path}")
        return {"inserted": 0, "updated": 0, "skipped": 0}
    
    # Get the exercises collection
    collection = db[EXERCISES_COLLECTION]
    
    stats = {"inserted": 0, "updated": 0, "skipped": 0}
    
    for exercise in exercises:
        # Calculate UID for deduplication
        exercise_uid = calculate_exercise_uid(exercise, chapter_code)
        
        # Prepare the document
        doc = {
            "chapter_code": chapter_code.upper().replace("-", "_"),
            "exercise_uid": exercise_uid,
            "id": exercise.get('id', 1),  # Use existing ID or default to 1
            "title": exercise.get('title'),
            "family": exercise.get('family'),
            "exercise_type": exercise.get('exercise_type'),
            "difficulty": exercise.get('difficulty', 'moyen').lower(),
            "offer": exercise.get('offer', 'free').lower(),
            "enonce_html": exercise.get('enonce_html', ''),
            "solution_html": exercise.get('solution_html', ''),
            "needs_svg": exercise.get('needs_svg', False),
            "variables": exercise.get('variables'),
            "svg_enonce_brief": exercise.get('svg_enonce_brief'),
            "svg_solution_brief": exercise.get('svg_solution_brief'),
            # Fields for dynamic exercises (if any)
            "is_dynamic": exercise.get('is_dynamic', False),
            "generator_key": exercise.get('generator_key'),
            "enonce_template_html": exercise.get('enonce_template_html'),
            "solution_template_html": exercise.get('solution_template_html'),
            "variables_schema": exercise.get('variables_schema'),
            "template_variants": exercise.get('template_variants'),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Check if exercise already exists (by UID or by chapter+id)
        existing = await collection.find_one({
            "$or": [
                {"exercise_uid": doc["exercise_uid"]},
                {"chapter_code": doc["chapter_code"], "id": doc["id"]}
            ]
        })
        
        if existing:
            # Check if content has changed
            content_changed = (
                existing.get('enonce_html') != doc['enonce_html'] or
                existing.get('solution_html') != doc['solution_html'] or
                existing.get('difficulty') != doc['difficulty'] or
                existing.get('offer') != doc['offer']
            )
            
            if content_changed:
                # Update the existing exercise
                await collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {**doc, "updated_at": datetime.now(timezone.utc)}}
                )
                stats["updated"] += 1
                print(f"  Updated exercise {doc['id']} (UID: {doc['exercise_uid'][:8]}...)")
            else:
                stats["skipped"] += 1
                print(f"  Skipped exercise {doc['id']} (already exists with same content, UID: {doc['exercise_uid'][:8]}...)")
        else:
            # Insert new exercise
            await collection.insert_one(doc)
            stats["inserted"] += 1
            print(f"  Inserted exercise {doc['id']} (UID: {doc['exercise_uid'][:8]}...)")
    
    return stats


async def main():
    print("🚀 Starting migration from Python files to MongoDB...")
    
    # Connect to database
    print("🔗 Connecting to MongoDB...")
    db = await connect_to_db()
    
    # Define the files to migrate
    data_dir = Path(__file__).parent.parent / "data"
    migration_files = [
        (data_dir / "gm07_exercises.py", "6E_GM07"),
        (data_dir / "gm08_exercises.py", "6E_GM08"),
        (data_dir / "tests_dyn_exercises.py", "6E_TESTS_DYN"),
    ]

    total_stats = {"inserted": 0, "updated": 0, "skipped": 0}

    # Process each file
    for file_path, chapter_code in migration_files:
        if file_path.exists():
            print(f"\n📁 Processing {file_path.name}...")
            try:
                file_stats = await migrate_file_to_db(db, file_path, chapter_code)
                for key in total_stats:
                    total_stats[key] += file_stats[key]
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️  File not found: {file_path}")
    
    # Print summary
    print(f"\n📈 Migration Summary:")
    print(f"  🆕 Inserted: {total_stats['inserted']}")
    print(f"  🔄 Updated: {total_stats['updated']}")
    print(f"  ⏭️ Skipped: {total_stats['skipped']}")
    print(f"  📊 Total processed: {sum(total_stats.values())}")
    
    print(f"\n✅ Migration completed!")


if __name__ == "__main__":
    asyncio.run(main())