"""
Tests pour la synchronisation admin_exercises → exercise_types

Vérifie que:
1. POST admin crée un exercice dynamique → exercise_types est synchronisé
2. GET /api/mathalea/chapters/{chapter_code}/exercise-types retourne l'item
3. La synchronisation est idempotente (pas de doublon)
"""

import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone

from backend.services.exercise_types_sync_service import (
    sync_admin_exercise_to_exercise_types,
    _normalize_chapter_code
)
from backend.constants.collections import EXERCISES_COLLECTION, EXERCISE_TYPES_COLLECTION


@pytest.mark.asyncio
async def test_sync_admin_exercise_to_exercise_types(db: AsyncIOMotorDatabase):
    """Test que la sync crée un document dans exercise_types"""
    chapter_code = "6E_N10"
    generator_key = "NOMBRES_ENTIERS_V1"
    
    # Nettoyer avant le test
    exercise_types_collection = db[EXERCISE_TYPES_COLLECTION]
    await exercise_types_collection.delete_many({
        "chapter_code": _normalize_chapter_code(chapter_code),
        "code_ref": generator_key
    })
    
    # Synchroniser
    await sync_admin_exercise_to_exercise_types(
        db=db,
        chapter_code=chapter_code,
        generator_key=generator_key,
        needs_svg=False
    )
    
    # Vérifier que le document existe
    doc = await exercise_types_collection.find_one({
        "chapter_code": _normalize_chapter_code(chapter_code),
        "code_ref": generator_key
    })
    
    assert doc is not None, "Le document exercise_type devrait être créé"
    assert doc["chapter_code"] == "6E_N10"
    assert doc["code_ref"] == generator_key
    assert doc["generator_kind"] == "DYNAMIC"
    assert doc["niveau"] == "6e"
    assert "Nombres" in doc["domaine"] or "nombres" in doc["domaine"].lower()
    assert doc["source"] == "admin_exercises_auto_sync"
    assert "difficulty_levels" in doc
    assert "facile" in doc["difficulty_levels"]


@pytest.mark.asyncio
async def test_sync_idempotent(db: AsyncIOMotorDatabase):
    """Test que la sync est idempotente (pas de doublon)"""
    chapter_code = "6E_N10"
    generator_key = "NOMBRES_ENTIERS_V1"
    
    exercise_types_collection = db[EXERCISE_TYPES_COLLECTION]
    
    # Première sync
    await sync_admin_exercise_to_exercise_types(
        db=db,
        chapter_code=chapter_code,
        generator_key=generator_key,
        needs_svg=False
    )
    
    # Compter les documents
    count_before = await exercise_types_collection.count_documents({
        "chapter_code": _normalize_chapter_code(chapter_code),
        "code_ref": generator_key
    })
    
    # Deuxième sync (devrait mettre à jour, pas créer)
    await sync_admin_exercise_to_exercise_types(
        db=db,
        chapter_code=chapter_code,
        generator_key=generator_key,
        needs_svg=True  # Changer needs_svg pour vérifier la mise à jour
    )
    
    # Vérifier qu'il n'y a toujours qu'un seul document
    count_after = await exercise_types_collection.count_documents({
        "chapter_code": _normalize_chapter_code(chapter_code),
        "code_ref": generator_key
    })
    
    assert count_after == count_before == 1, "La sync devrait être idempotente"
    
    # Vérifier que needs_svg a été mis à jour
    doc = await exercise_types_collection.find_one({
        "chapter_code": _normalize_chapter_code(chapter_code),
        "code_ref": generator_key
    })
    assert doc["requires_svg"] is True


@pytest.mark.asyncio
async def test_create_admin_exercise_syncs_to_exercise_types(client: TestClient, db: AsyncIOMotorDatabase):
    """
    Test end-to-end: POST admin crée un exercice dynamique → exercise_types est synchronisé
    """
    chapter_code = "6E_N10"
    generator_key = "NOMBRES_ENTIERS_V1"
    
    exercise_types_collection = db[EXERCISE_TYPES_COLLECTION]
    admin_collection = db[EXERCISES_COLLECTION]
    
    # Nettoyer avant le test
    await exercise_types_collection.delete_many({
        "chapter_code": _normalize_chapter_code(chapter_code),
        "code_ref": generator_key
    })
    
    # Créer un exercice dynamique via l'API admin
    payload = {
        "is_dynamic": True,
        "generator_key": generator_key,
        "difficulty": "facile",
        "offer": "free",
        "enonce_template_html": "<p>{{enonce}}</p>",
        "solution_template_html": "<p>Réponse: {{reponse_finale}}</p>",
        "needs_svg": False
    }
    
    response = client.post(
        f"/api/admin/chapters/{chapter_code}/exercises",
        json=payload
    )
    
    assert response.status_code == 200, f"Erreur création exercice: {response.text}"
    data = response.json()
    assert data["success"] is True
    
    # Vérifier que l'exercice existe dans admin_exercises
    exercise_id = data["exercise"]["id"]
    admin_exercise = await admin_collection.find_one({
        "chapter_code": _normalize_chapter_code(chapter_code),
        "id": exercise_id
    })
    assert admin_exercise is not None
    assert admin_exercise["is_dynamic"] is True
    assert admin_exercise["generator_key"] == generator_key
    
    # Vérifier que exercise_types a été synchronisé
    exercise_type = await exercise_types_collection.find_one({
        "chapter_code": _normalize_chapter_code(chapter_code),
        "code_ref": generator_key
    })
    
    assert exercise_type is not None, "exercise_types devrait être synchronisé"
    assert exercise_type["code_ref"] == generator_key
    assert exercise_type["generator_kind"] == "DYNAMIC"


@pytest.mark.asyncio
async def test_get_chapter_exercise_types_returns_synced_item(client: TestClient, db: AsyncIOMotorDatabase):
    """
    Test que GET /api/mathalea/chapters/{chapter_code}/exercise-types retourne l'item synchronisé
    """
    chapter_code = "6E_N10"
    generator_key = "NOMBRES_ENTIERS_V1"
    
    # Synchroniser manuellement d'abord
    await sync_admin_exercise_to_exercise_types(
        db=db,
        chapter_code=chapter_code,
        generator_key=generator_key,
        needs_svg=False
    )
    
    # Appeler l'endpoint MathALÉA
    response = client.get(
        f"/api/mathalea/chapters/{chapter_code}/exercise-types"
    )
    
    assert response.status_code == 200, f"Erreur GET exercise-types: {response.text}"
    data = response.json()
    
    assert "total" in data
    assert data["total"] >= 1, "Au moins un exercise_type devrait être retourné"
    
    # Vérifier que notre item est dans la liste
    items = data.get("items", [])
    found = False
    for item in items:
        if item.get("code_ref") == generator_key and item.get("chapter_code") == _normalize_chapter_code(chapter_code):
            found = True
            assert item["generator_kind"] == "DYNAMIC"
            break
    
    assert found, f"L'exercise_type {generator_key} devrait être dans la liste"


@pytest.mark.asyncio
async def test_normalize_chapter_code():
    """Test la normalisation du chapter_code"""
    assert _normalize_chapter_code("6e-n10") == "6E_N10"
    assert _normalize_chapter_code("6E_N10") == "6E_N10"
    assert _normalize_chapter_code("6e_n10") == "6E_N10"
    assert _normalize_chapter_code("4E-G07") == "4E_G07"

