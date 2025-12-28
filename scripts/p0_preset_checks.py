#!/usr/bin/env python3
"""
Diagnostic preset-first premium generators.

Checks:
- Seed is present and integer for premium generators.
- Difficulty in exercise matches difficulty in variables for premium.
- Optional: last non-premium dynamic exercise to ensure no preset override.
"""

import os
from typing import Optional
from pprint import pprint
from pymongo import MongoClient, DESCENDING

PREMIUM_KEYS = {"CALCUL_NOMBRES_V1", "RAISONNEMENT_MULTIPLICATIF_V1"}
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("MONGO_DB_NAME", "le_maitre_mot_db")
COLLECTION = os.environ.get("MONGO_COLLECTION", "admin_exercises")


def fetch_latest(collection, query: dict) -> Optional[dict]:
    cursor = collection.find(query, {"_id": 0}).sort("id", DESCENDING).limit(1)
    return next(cursor, None)


def check_premium(doc: dict) -> dict:
    seed = (doc.get("variables") or {}).get("seed")
    diff_var = (doc.get("variables") or {}).get("difficulty")
    diff_doc = doc.get("difficulty")
    seed_is_int = isinstance(seed, int)
    diff_sync = diff_var == diff_doc
    return {
        "generator_key": doc.get("generator_key"),
        "id": doc.get("id"),
        "seed": seed,
        "seed_type": type(seed).__name__,
        "CHECK2_SEED_INT": "PASS" if seed_is_int else "FAIL",
        "difficulty_doc": diff_doc,
        "difficulty_vars": diff_var,
        "CHECK3_DIFF_SYNC": "PASS" if diff_sync else "FAIL",
    }


def check_non_premium(doc: dict) -> dict:
    return {
        "generator_key": doc.get("generator_key"),
        "id": doc.get("id"),
        "note": "non-premium dynamic sample",
        "difficulty_doc": doc.get("difficulty"),
        "difficulty_vars": (doc.get("variables") or {}).get("difficulty"),
    }


def main():
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    coll = db[COLLECTION]

    results = []

    for key in PREMIUM_KEYS:
        doc = fetch_latest(coll, {"generator_key": key})
        if not doc:
            results.append({"generator_key": key, "error": "NO_DOC"})
            continue
        results.append(check_premium(doc))

    non_premium = fetch_latest(
        coll,
        {
          "is_dynamic": True,
          "generator_key": {"$nin": list(PREMIUM_KEYS)},
        },
    )
    if non_premium:
        results.append(check_non_premium(non_premium))

    print("=== P0 PRESET CHECKS REPORT ===")
    for entry in results:
        pprint(entry)
    print("=== END REPORT ===")


if __name__ == "__main__":
    main()
