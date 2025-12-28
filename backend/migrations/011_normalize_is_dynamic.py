"""
P0-D: Migration to normalize is_dynamic to strict boolean

This migration converts all is_dynamic values in admin_exercises collection
to strict boolean (True/False) for consistent filtering.

Before: is_dynamic can be bool/int/str ("true", "1", True, 1, etc.)
After: is_dynamic is always bool (True or False)

IDEMPOTENT: Safe to run multiple times.

Usage:
    # Backup first!
    mongodump --db lemaitremot --collection admin_exercises --out ./backup_$(date +%Y%m%d)

    # Dry run (check what would change)
    python -m backend.migrations.011_normalize_is_dynamic --dry-run

    # Apply migration
    python -m backend.migrations.011_normalize_is_dynamic

    # Verify
    python -m backend.migrations.011_normalize_is_dynamic --verify
"""

import asyncio
import argparse
from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import Any


# Collection to migrate
COLLECTION_NAME = "admin_exercises"


def _is_truthy_dynamic(value: Any) -> bool:
    """
    Convert various is_dynamic representations to boolean.

    Handles:
    - bool: True/False
    - int: 1/0
    - str: "true"/"false", "1"/"0", "yes"/"no"
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value == 1
    if isinstance(value, str):
        return value.lower().strip() in ("true", "1", "yes")
    return False


async def analyze_is_dynamic_types(collection) -> dict:
    """Analyze current is_dynamic types in collection."""
    pipeline = [
        {
            "$group": {
                "_id": {"$type": "$is_dynamic"},
                "count": {"$sum": 1},
                "sample_values": {"$push": {"$toString": "$is_dynamic"}}
            }
        }
    ]

    results = {}
    async for doc in collection.aggregate(pipeline):
        type_name = doc["_id"]
        count = doc["count"]
        samples = doc.get("sample_values", [])[:5]  # Limit samples
        results[type_name] = {"count": count, "samples": samples}

    return results


async def normalize_is_dynamic(db, dry_run: bool = True) -> dict:
    """
    Normalize all is_dynamic values to strict boolean.

    Args:
        db: MongoDB database
        dry_run: If True, don't modify data, just report

    Returns:
        dict with stats about the migration
    """
    collection = db[COLLECTION_NAME]

    stats = {
        "total_documents": 0,
        "already_bool": 0,
        "converted_to_true": 0,
        "converted_to_false": 0,
        "errors": []
    }

    # Count total
    stats["total_documents"] = await collection.count_documents({})

    print(f"\n{'='*60}")
    print(f"P0-D: Normalize is_dynamic to boolean")
    print(f"{'='*60}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Total documents: {stats['total_documents']}")
    print(f"Mode: {'DRY RUN' if dry_run else 'APPLYING CHANGES'}")
    print(f"{'='*60}\n")

    # Analyze current types
    print("Current is_dynamic type distribution:")
    type_dist = await analyze_is_dynamic_types(collection)
    for type_name, info in type_dist.items():
        print(f"  {type_name}: {info['count']} documents (samples: {info['samples'][:3]})")

    # Process documents that need conversion
    # Find documents where is_dynamic is NOT a boolean
    query = {
        "$or": [
            {"is_dynamic": {"$type": "string"}},
            {"is_dynamic": {"$type": "int"}},
            {"is_dynamic": {"$type": "double"}},
            {"is_dynamic": {"$type": "null"}},
            {"is_dynamic": {"$exists": False}}
        ]
    }

    cursor = collection.find(query)
    to_update = []

    async for doc in cursor:
        doc_id = doc["_id"]
        old_value = doc.get("is_dynamic")
        new_value = _is_truthy_dynamic(old_value)

        to_update.append({
            "_id": doc_id,
            "old_value": old_value,
            "old_type": type(old_value).__name__,
            "new_value": new_value
        })

        if new_value:
            stats["converted_to_true"] += 1
        else:
            stats["converted_to_false"] += 1

    # Count already boolean
    bool_count = await collection.count_documents({
        "$or": [
            {"is_dynamic": True},
            {"is_dynamic": False}
        ]
    })
    stats["already_bool"] = bool_count

    print(f"\nDocuments to convert: {len(to_update)}")
    print(f"  → Will become True: {stats['converted_to_true']}")
    print(f"  → Will become False: {stats['converted_to_false']}")
    print(f"Already boolean: {stats['already_bool']}")

    if dry_run:
        print("\n[DRY RUN] No changes made. Run without --dry-run to apply.")
        if len(to_update) > 0:
            print("\nSample conversions (first 10):")
            for item in to_update[:10]:
                print(f"  {item['_id']}: {item['old_value']} ({item['old_type']}) → {item['new_value']}")
        return stats

    # Apply changes
    print("\nApplying changes...")
    updated_count = 0

    for item in to_update:
        try:
            result = await collection.update_one(
                {"_id": item["_id"]},
                {"$set": {"is_dynamic": item["new_value"]}}
            )
            if result.modified_count > 0:
                updated_count += 1
        except Exception as e:
            stats["errors"].append(f"Error updating {item['_id']}: {e}")

    print(f"Updated {updated_count} documents.")

    if stats["errors"]:
        print(f"\nErrors ({len(stats['errors'])}):")
        for err in stats["errors"][:10]:
            print(f"  {err}")

    return stats


async def verify_migration(db) -> bool:
    """Verify all is_dynamic values are now boolean."""
    collection = db[COLLECTION_NAME]

    # Check for non-boolean is_dynamic
    non_bool = await collection.count_documents({
        "$and": [
            {"is_dynamic": {"$exists": True}},
            {"is_dynamic": {"$not": {"$type": "bool"}}}
        ]
    })

    print(f"\n{'='*60}")
    print(f"P0-D: Verification")
    print(f"{'='*60}")
    print(f"Documents with non-boolean is_dynamic: {non_bool}")

    if non_bool == 0:
        print("✅ All is_dynamic values are now boolean!")
        return True
    else:
        print("❌ Some documents still have non-boolean is_dynamic")
        # Show samples
        cursor = collection.find({
            "$and": [
                {"is_dynamic": {"$exists": True}},
                {"is_dynamic": {"$not": {"$type": "bool"}}}
            ]
        }).limit(5)
        async for doc in cursor:
            print(f"  {doc['_id']}: is_dynamic={doc.get('is_dynamic')} (type: {type(doc.get('is_dynamic')).__name__})")
        return False


async def create_index(db):
    """Create index on is_dynamic for better query performance."""
    collection = db[COLLECTION_NAME]

    print("\nCreating index on is_dynamic...")
    try:
        await collection.create_index("is_dynamic")
        print("✅ Index created successfully")
    except Exception as e:
        print(f"⚠️ Index creation failed (may already exist): {e}")


async def main():
    parser = argparse.ArgumentParser(description="P0-D: Normalize is_dynamic to boolean")
    parser.add_argument("--dry-run", action="store_true", help="Don't modify data, just report")
    parser.add_argument("--verify", action="store_true", help="Verify migration was successful")
    parser.add_argument("--create-index", action="store_true", help="Create index on is_dynamic")
    args = parser.parse_args()

    # Connect to MongoDB
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("MONGO_DB", "lemaitremot")

    print(f"Connecting to MongoDB: {mongo_url} / {db_name}")

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    try:
        if args.verify:
            success = await verify_migration(db)
            return 0 if success else 1

        if args.create_index:
            await create_index(db)
            return 0

        # Default: run migration
        stats = await normalize_is_dynamic(db, dry_run=args.dry_run)

        if not args.dry_run:
            # Verify after migration
            await verify_migration(db)

        return 0

    finally:
        client.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
