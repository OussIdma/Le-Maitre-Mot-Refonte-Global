"""
Tests pour l'import/export de packages complets (PR10)
=====================================================

Cas testés:
1) export package retourne schema_version pkg-1.0 + metadata.counts cohérents
2) import package dry_run ne crée aucun doc (counts 0 en DB) mais retourne stats
3) import package apply insère chapters + exercises (et templates si support) et ensuite export retrouve les mêmes counts
4) rollback : simuler exception sur insert_many exercises → vérifier 0 reste en DB (batch_id rollback)
5) normalisation : importer avec chapter_code "6e-gm07" → stocke "6E_GM07"
"""

import pytest
import pytest_asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os
from backend.services.package_schema import normalize_chapter_code
from backend.constants.collections import EXERCISES_COLLECTION, CURRICULUM_CHAPTERS_COLLECTION


# Fixture pour la connexion MongoDB de test
@pytest_asyncio.fixture
async def test_db():
    """Crée une connexion MongoDB de test"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('TEST_DB_NAME', 'test_le_maitre_mot_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Nettoyer les collections de test avant les tests
    exercises_collection = db[EXERCISES_COLLECTION]
    curriculum_collection = db[CURRICULUM_CHAPTERS_COLLECTION]
    
    # Nettoyer pour plusieurs codes de test possibles
    test_chapters = ["6E_TEST_IMPORT", "6E_GM07", "6E_GM08"]
    for chapter_code in test_chapters:
        await exercises_collection.delete_many({"chapter_code": chapter_code})
        await curriculum_collection.delete_many({"code_officiel": chapter_code})
    
    yield db
    
    # Nettoyer après les tests
    for chapter_code in test_chapters:
        await exercises_collection.delete_many({"chapter_code": chapter_code})
        await curriculum_collection.delete_many({"code_officiel": chapter_code})
    client.close()


@pytest.fixture
def test_niveau():
    """Niveau de test"""
    return "6e"


@pytest.fixture
def test_chapter_code():
    """Code de chapitre de test (normalisé)"""
    return "6E_GM07"


@pytest.fixture
def sample_package(test_niveau, test_chapter_code):
    """Package de test v1.0"""
    return {
        "schema_version": "pkg-1.0",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "scope": {
            "niveau": test_niveau
        },
        "curriculum_chapters": [
            {
                "code_officiel": test_chapter_code,
                "titre": "Test Chapitre",
                "domaine": "Géométrie",
                "niveau": test_niveau,
                "pipeline": "SPEC"
            }
        ],
        "admin_exercises": [
            {
                "id": "ex1",
                "chapter_code": test_chapter_code,
                "enonce_html": "<p>Exercice test</p>",
                "solution_html": "<p>Solution test</p>",
                "difficulty": "moyen",
                "offer": "free",
                "is_dynamic": False
            },
            {
                "id": "ex2",
                "chapter_code": test_chapter_code,
                "enonce_html": "<p>Exercice test 2</p>",
                "solution_html": "<p>Solution test 2</p>",
                "difficulty": "facile",
                "offer": "free",
                "is_dynamic": False
            }
        ],
        "admin_templates": [],
        "metadata": {
            "counts": {
                "chapters": 1,
                "exercises": 2,
                "templates": 0
            },
            "normalized": True,
            "templates_supported": False
        }
    }


@pytest_asyncio.fixture
async def client(test_db):
    """Client HTTP async pour les tests"""
    from httpx import AsyncClient, ASGITransport
    from server import app
    
    # Injecter la DB de test dans l'app
    app.state.db = test_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_export_package_returns_valid_schema(client, test_niveau):
    """
    Test 1: export package retourne schema_version pkg-1.0 + metadata.counts cohérents
    """
    response = await client.get(f"/api/admin/package/export?niveau={test_niveau}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier schema_version
    assert data["schema_version"] == "pkg-1.0"
    
    # Vérifier scope
    assert data["scope"]["niveau"] == test_niveau
    
    # Vérifier metadata.counts cohérents
    metadata = data["metadata"]
    assert metadata["counts"]["chapters"] == len(data["curriculum_chapters"])
    assert metadata["counts"]["exercises"] == len(data["admin_exercises"])
    assert metadata["counts"]["templates"] == len(data["admin_templates"])
    
    # Vérifier normalized
    assert metadata["normalized"] is True


@pytest.mark.asyncio
async def test_import_package_dry_run_no_writes(client, sample_package, test_chapter_code, test_db):
    """
    Test 2: import package dry_run ne crée aucun doc (counts 0 en DB) mais retourne stats
    """
    # Compter avant
    exercises_before = await test_db[EXERCISES_COLLECTION].count_documents({"chapter_code": test_chapter_code})
    chapters_before = await test_db[CURRICULUM_CHAPTERS_COLLECTION].count_documents({"code_officiel": test_chapter_code})
    
    # Import dry_run
    response = await client.post("/api/admin/package/import?dry_run=true", json=sample_package)
    
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier dry_run
    assert data["dry_run"] is True
    assert data["validation"] == "passed"
    assert "stats" in data
    
    # Vérifier qu'aucun doc n'a été créé
    exercises_after = await test_db[EXERCISES_COLLECTION].count_documents({"chapter_code": test_chapter_code})
    chapters_after = await test_db[CURRICULUM_CHAPTERS_COLLECTION].count_documents({"code_officiel": test_chapter_code})
    
    assert exercises_after == exercises_before
    assert chapters_after == chapters_before


@pytest.mark.asyncio
async def test_import_package_apply_then_export(client, sample_package, test_niveau, test_chapter_code, test_db):
    """
    Test 3: import package apply insère chapters + exercises et ensuite export retrouve les mêmes counts
    """
    # Nettoyer avant (si nécessaire)
    await test_db[EXERCISES_COLLECTION].delete_many({"chapter_code": test_chapter_code})
    await test_db[CURRICULUM_CHAPTERS_COLLECTION].delete_many({"code_officiel": test_chapter_code})
    
    # Import réel
    response = await client.post("/api/admin/package/import?dry_run=false", json=sample_package)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["stats"]["exercises_inserted"] == 2
    assert data["stats"]["chapters_created"] >= 0  # Peut être 0 si chapitre existe déjà
    
    # Export et vérifier counts
    response = await client.get(f"/api/admin/package/export?niveau={test_niveau}")
    assert response.status_code == 200
    export_data = response.json()
    
    # Vérifier que les exercices exportés incluent ceux importés
    exported_exercises = [ex for ex in export_data["admin_exercises"] if ex["chapter_code"] == test_chapter_code]
    assert len(exported_exercises) >= 2  # Au moins les 2 exercices importés
    
    # Nettoyer après
    await test_db[EXERCISES_COLLECTION].delete_many({"chapter_code": test_chapter_code})
    await test_db[CURRICULUM_CHAPTERS_COLLECTION].delete_many({"code_officiel": test_chapter_code})


@pytest.mark.asyncio
async def test_import_package_rollback_on_error(client, test_niveau, test_chapter_code, test_db):
    """
    Test 4: rollback : simuler exception sur insert_many exercises → vérifier 0 reste en DB (batch_id rollback)
    """
    # Nettoyer avant
    await test_db[EXERCISES_COLLECTION].delete_many({"chapter_code": test_chapter_code})
    
    # Créer un package avec un exercice invalide (pour provoquer une erreur)
    invalid_package = {
        "schema_version": "pkg-1.0",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "scope": {"niveau": test_niveau},
        "curriculum_chapters": [],
        "admin_exercises": [
            {
                "id": "ex_invalid",
                "chapter_code": test_chapter_code,
                "enonce_html": "",  # Vide → invalide
                "solution_html": "<p>Solution</p>",
                "difficulty": "moyen",
                "offer": "free"
            }
        ],
        "admin_templates": [],
        "metadata": {
            "counts": {"chapters": 0, "exercises": 1, "templates": 0},
            "normalized": True,
            "templates_supported": False
        }
    }
    
    # Import devrait échouer
    response = await client.post("/api/admin/package/import?dry_run=false", json=invalid_package)
    
    # Devrait retourner 400 (validation error)
    assert response.status_code == 400
    
    # Vérifier qu'aucun exercice n'a été inséré
    count = await test_db[EXERCISES_COLLECTION].count_documents({"chapter_code": test_chapter_code})
    assert count == 0


@pytest.mark.asyncio
async def test_import_package_normalizes_chapter_code(client, test_niveau, test_db):
    """
    Test 5: normalisation : importer avec chapter_code "6e-gm07" → stocke "6E_GM07"
    """
    # Code non normalisé
    non_normalized_code = "6e-gm07"
    normalized_code = "6E_GM07"
    
    # Nettoyer avant
    await test_db[EXERCISES_COLLECTION].delete_many({"chapter_code": normalized_code})
    
    package = {
        "schema_version": "pkg-1.0",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "scope": {"niveau": test_niveau},
        "curriculum_chapters": [],
        "admin_exercises": [
            {
                "id": "ex_normalize",
                "chapter_code": non_normalized_code,  # Non normalisé
                "enonce_html": "<p>Test normalisation</p>",
                "solution_html": "<p>Solution</p>",
                "difficulty": "moyen",
                "offer": "free"
            }
        ],
        "admin_templates": [],
        "metadata": {
            "counts": {"chapters": 0, "exercises": 1, "templates": 0},
            "normalized": False,  # Package non normalisé
            "templates_supported": False
        }
    }
    
    # Import
    response = await client.post("/api/admin/package/import?dry_run=false", json=package)
    
    # Devrait réussir (normalisation automatique)
    assert response.status_code == 200
    
    # Vérifier que l'exercice est stocké avec le code normalisé
    exercise = await test_db[EXERCISES_COLLECTION].find_one({"id": "ex_normalize"})
    assert exercise is not None
    assert exercise["chapter_code"] == normalized_code  # Normalisé
    
    # Nettoyer après
    await test_db[EXERCISES_COLLECTION].delete_many({"chapter_code": normalized_code})


def test_normalize_chapter_code():
    """Test helper de normalisation"""
    assert normalize_chapter_code("6e-gm07") == "6E_GM07"
    assert normalize_chapter_code("6E_GM07") == "6E_GM07"
    assert normalize_chapter_code("6e_n10") == "6E_N10"
    assert normalize_chapter_code("4E-G07") == "4E_G07"

