"""
Tests pour le script de migration des exercices pseudo-statiques.

Tests:
- Dry-run ne crée rien
- Apply crée N exercices
- Idempotence: relancer → 0 insert, N skip
- UID stable (mêmes inputs → même uid)
"""

import pytest
import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
from pathlib import Path
from typing import Tuple

# Ajouter le chemin du backend
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from backend.scripts.migrate_pseudo_static_to_db import (
    compute_exercise_uid,
    validate_exercise,
    prepare_exercise_document,
    migrate_exercises
)


# Fixture pour la connexion MongoDB de test
@pytest.fixture
async def test_db():
    """Crée une connexion MongoDB de test"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('TEST_DB_NAME', 'test_le_maitre_mot_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Nettoyer la collection de test avant les tests
    collection = db["admin_exercises"]
    await collection.delete_many({"source": "legacy_migration"})
    
    yield db
    
    # Nettoyer après les tests
    await collection.delete_many({"source": "legacy_migration"})
    client.close()


@pytest.mark.asyncio
async def test_compute_exercise_uid_stable(test_db):
    """Test que l'UID est stable pour les mêmes inputs"""
    uid1 = compute_exercise_uid(
        chapter_code="6E_GM07",
        enonce_html="<p>Test</p>",
        solution_html="<p>Solution</p>",
        difficulty="facile"
    )
    
    uid2 = compute_exercise_uid(
        chapter_code="6E_GM07",
        enonce_html="<p>Test</p>",
        solution_html="<p>Solution</p>",
        difficulty="facile"
    )
    
    assert uid1 == uid2, "L'UID doit être stable pour les mêmes inputs"
    
    # Test avec des espaces (normalisation)
    uid3 = compute_exercise_uid(
        chapter_code="6E_GM07",
        enonce_html="  <p>Test</p>  ",
        solution_html="  <p>Solution</p>  ",
        difficulty="facile"
    )
    
    assert uid1 == uid3, "L'UID doit être identique après normalisation (strip)"


@pytest.mark.asyncio
async def test_compute_exercise_uid_different(test_db):
    """Test que l'UID est différent pour des inputs différents"""
    uid1 = compute_exercise_uid(
        chapter_code="6E_GM07",
        enonce_html="<p>Test 1</p>",
        solution_html="<p>Solution</p>",
        difficulty="facile"
    )
    
    uid2 = compute_exercise_uid(
        chapter_code="6E_GM07",
        enonce_html="<p>Test 2</p>",
        solution_html="<p>Solution</p>",
        difficulty="facile"
    )
    
    assert uid1 != uid2, "L'UID doit être différent pour des énoncés différents"


@pytest.mark.asyncio
async def test_validate_exercise_valid(test_db):
    """Test validation d'un exercice valide"""
    ex = {
        "chapter_code": "6E_GM07",
        "enonce_html": "<p>Test</p>",
        "solution_html": "<p>Solution</p>",
        "difficulty": "facile"
    }
    
    is_valid, error = validate_exercise(ex)
    assert is_valid is True
    assert error is None


@pytest.mark.asyncio
async def test_validate_exercise_missing_enonce(test_db):
    """Test validation échoue si enonce_html vide"""
    ex = {
        "chapter_code": "6E_GM07",
        "enonce_html": "",
        "solution_html": "<p>Solution</p>",
        "difficulty": "facile"
    }
    
    is_valid, error = validate_exercise(ex)
    assert is_valid is False
    assert "enonce_html" in error.lower()


@pytest.mark.asyncio
async def test_validate_exercise_missing_solution(test_db):
    """Test validation échoue si solution_html vide"""
    ex = {
        "chapter_code": "6E_GM07",
        "enonce_html": "<p>Test</p>",
        "solution_html": "",
        "difficulty": "facile"
    }
    
    is_valid, error = validate_exercise(ex)
    assert is_valid is False
    assert "solution_html" in error.lower()


@pytest.mark.asyncio
async def test_prepare_exercise_document(test_db):
    """Test préparation d'un document MongoDB"""
    ex = {
        "chapter_code": "6E_GM07",
        "id": 1,
        "enonce_html": "<p>Test</p>",
        "solution_html": "<p>Solution</p>",
        "difficulty": "facile",
        "offer": "free"
    }
    
    uid = compute_exercise_uid(
        ex["chapter_code"],
        ex["enonce_html"],
        ex["solution_html"],
        ex["difficulty"]
    )
    
    doc = prepare_exercise_document(ex, uid, locked=True)
    
    assert doc["chapter_code"] == "6E_GM07"
    assert doc["exercise_uid"] == uid
    assert doc["is_dynamic"] is False
    assert doc["locked"] is True
    assert doc["source"] == "legacy_migration"
    assert "created_at" in doc
    assert "updated_at" in doc


@pytest.mark.asyncio
async def test_prepare_exercise_document_unlock(test_db):
    """Test préparation avec unlock"""
    ex = {
        "chapter_code": "6E_GM07",
        "id": 1,
        "enonce_html": "<p>Test</p>",
        "solution_html": "<p>Solution</p>",
        "difficulty": "facile"
    }
    
    uid = compute_exercise_uid(
        ex["chapter_code"],
        ex["enonce_html"],
        ex["solution_html"],
        ex["difficulty"]
    )
    
    doc = prepare_exercise_document(ex, uid, locked=False)
    assert doc["locked"] is False


@pytest.mark.asyncio
async def test_migrate_dry_run(test_db):
    """Test que dry-run ne crée rien"""
    # Créer un exercice de test
    test_exercises = {
        "6E_TEST": [
            {
                "chapter_code": "6E_TEST",
                "id": 1,
                "enonce_html": "<p>Test exercice</p>",
                "solution_html": "<p>Solution test</p>",
                "difficulty": "facile",
                "offer": "free"
            }
        ]
    }
    
    # Mock load_all_legacy_exercises
    import backend.scripts.migrate_pseudo_static_to_db as migrate_module
    original_load = migrate_module.load_all_legacy_exercises
    
    def mock_load(chapter_code=None):
        return test_exercises
    
    migrate_module.load_all_legacy_exercises = mock_load
    
    try:
        stats = await migrate_exercises(
            db=test_db,
            chapter_code=None,
            dry_run=True,
            unlock=False
        )
        
        # Vérifier qu'aucun document n'a été créé
        collection = test_db["admin_exercises"]
        count = await collection.count_documents({"source": "legacy_migration"})
        assert count == 0, "Dry-run ne doit pas créer de documents"
        
        # Mais les stats doivent indiquer qu'on aurait inséré
        assert stats["inserted"] > 0, "Les stats doivent indiquer des insertions simulées"
        
    finally:
        migrate_module.load_all_legacy_exercises = original_load


@pytest.mark.asyncio
async def test_migrate_idempotence(test_db):
    """Test idempotence: relancer la migration → 0 insert, N skip"""
    # Créer un exercice de test
    test_exercises = {
        "6E_TEST": [
            {
                "chapter_code": "6E_TEST",
                "id": 1,
                "enonce_html": "<p>Test exercice idempotence</p>",
                "solution_html": "<p>Solution test</p>",
                "difficulty": "facile",
                "offer": "free"
            }
        ]
    }
    
    # Mock load_all_legacy_exercises
    import backend.scripts.migrate_pseudo_static_to_db as migrate_module
    original_load = migrate_module.load_all_legacy_exercises
    
    def mock_load(chapter_code=None):
        return test_exercises
    
    migrate_module.load_all_legacy_exercises = mock_load
    
    try:
        # Première migration (apply)
        stats1 = await migrate_exercises(
            db=test_db,
            chapter_code=None,
            dry_run=False,
            unlock=False
        )
        
        assert stats1["inserted"] > 0, "Première migration doit insérer"
        assert stats1["skipped"] == 0, "Première migration ne doit rien skip"
        
        # Deuxième migration (idempotence)
        stats2 = await migrate_exercises(
            db=test_db,
            chapter_code=None,
            dry_run=False,
            unlock=False
        )
        
        assert stats2["inserted"] == 0, "Deuxième migration ne doit rien insérer"
        assert stats2["skipped"] > 0, "Deuxième migration doit skip les existants"
        
    finally:
        migrate_module.load_all_legacy_exercises = original_load
        
        # Nettoyer
        collection = test_db["admin_exercises"]
        await collection.delete_many({"source": "legacy_migration"})


@pytest.mark.asyncio
async def test_migrate_needs_solution_flag(test_db):
    """Test que needs_solution=True si solution vide ou placeholder"""
    ex1 = {
        "chapter_code": "6E_TEST",
        "id": 1,
        "enonce_html": "<p>Test</p>",
        "solution_html": "",  # Vide
        "difficulty": "facile"
    }
    
    uid1 = compute_exercise_uid(
        ex1["chapter_code"],
        ex1["enonce_html"],
        ex1["solution_html"],
        ex1["difficulty"]
    )
    
    doc1 = prepare_exercise_document(ex1, uid1, locked=True)
    assert doc1["needs_solution"] is True
    assert "Solution à compléter" in doc1["solution_html"]
    
    ex2 = {
        "chapter_code": "6E_TEST",
        "id": 2,
        "enonce_html": "<p>Test</p>",
        "solution_html": "<p>Solution à compléter</p>",  # Placeholder
        "difficulty": "facile"
    }
    
    uid2 = compute_exercise_uid(
        ex2["chapter_code"],
        ex2["enonce_html"],
        ex2["solution_html"],
        ex2["difficulty"]
    )
    
    doc2 = prepare_exercise_document(ex2, uid2, locked=True)
    assert doc2["needs_solution"] is True
    
    ex3 = {
        "chapter_code": "6E_TEST",
        "id": 3,
        "enonce_html": "<p>Test</p>",
        "solution_html": "<p>Solution complète</p>",  # Solution réelle
        "difficulty": "facile"
    }
    
    uid3 = compute_exercise_uid(
        ex3["chapter_code"],
        ex3["enonce_html"],
        ex3["solution_html"],
        ex3["difficulty"]
    )
    
    doc3 = prepare_exercise_document(ex3, uid3, locked=True)
    assert doc3["needs_solution"] is False

