"""
Tests pour l'import/export versionné v1.0 avec rollback atomique
================================================================

Tests:
1. Import missing schema_version => 400
2. Import bad schema_version => 400
3. Import good payload => 200 + insert N
4. Rollback: simuler exception pendant insert_many => vérifier delete_many appelé
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock
from motor.motor_asyncio import AsyncIOMotorClient
import os
from backend.constants.collections import EXERCISES_COLLECTION


# Fixture pour la connexion MongoDB de test
@pytest_asyncio.fixture
async def test_db():
    """Crée une connexion MongoDB de test"""
    from backend.constants.collections import CURRICULUM_CHAPTERS_COLLECTION
    
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('TEST_DB_NAME', 'test_le_maitre_mot_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Nettoyer les collections de test avant les tests
    exercises_collection = db[EXERCISES_COLLECTION]
    curriculum_collection = db[CURRICULUM_CHAPTERS_COLLECTION]
    
    # Nettoyer pour plusieurs codes de test possibles
    test_chapters = ["6E_TEST_IMPORT", "6E_GM07"]
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
def mock_chapter_6e_gm07():
    """
    Fixture pour créer un chapitre mock qui sera utilisé par les tests.
    """
    from curriculum.loader import CurriculumChapter
    
    # Créer un chapitre mock qui sera retourné par get_chapter_by_official_code
    mock_chapter = CurriculumChapter(
        niveau="6e",
        code_officiel="6e_GM07",  # Format attendu par le loader (minuscule)
        domaine="Grandeurs et mesures",
        libelle="GM07 TEST - Durées",
        chapitre_backend="GM07",
        exercise_types=[],
        pipeline="MIXED",
        statut="beta",
        schema_requis=False,
        difficulte_min=1,
        difficulte_max=3,
        tags=[],
        contexts=[]
    )
    
    return mock_chapter


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
@patch('backend.routes.admin_exercises_routes.get_chapter_by_official_code')
async def test_import_missing_schema_version(mock_get_chapter, client, test_db):
    """Test que l'import sans schema_version est traité en mode legacy et échoue si le chapitre n'existe pas"""
    chapter_code = "6E_TEST_IMPORT"
    
    # S'assurer que le chapitre n'existe PAS (pas de mock, donc get_chapter_by_official_code retournera None)
    mock_get_chapter.return_value = None
    
    # Nettoyer avant le test
    from backend.constants.collections import CURRICULUM_CHAPTERS_COLLECTION
    curriculum_collection = test_db[CURRICULUM_CHAPTERS_COLLECTION]
    await curriculum_collection.delete_many({"code_officiel": {"$in": [chapter_code, chapter_code.lower()]}})
    
    payload = {
        "chapter_code": chapter_code,
        "exercises": []
    }
    
    response = await client.post(
        f"/api/admin/chapters/{chapter_code}/exercises/import",
        json=payload
    )
    
    # Le payload legacy sans schema_version nécessite que le chapitre existe
    # Si le chapitre n'existe pas, on obtient 422 INVALID_CHAPTER
    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.json()}"
    detail = response.json()["detail"]
    assert detail["error_code"] == "INVALID_CHAPTER"


@pytest.mark.asyncio
@patch('backend.routes.admin_exercises_routes.get_chapter_by_official_code')
async def test_import_bad_schema_version(mock_get_chapter, client, test_db, mock_chapter_6e_gm07):
    """Test que l'import avec un schema_version invalide est rejeté"""
    mock_get_chapter.return_value = mock_chapter_6e_gm07
    
    payload = {
        "schema_version": "2.0",  # Version non supportée
        "chapter_code": "6E_GM07",
        "exercises": [],
        "metadata": {"total_exercises": 0}
    }
    
    response = await client.post(
        "/api/admin/chapters/6E_GM07/exercises/import",
        json=payload
    )
    
    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.json()}"
    detail = response.json()["detail"]
    assert detail["error_code"] == "INVALID_SCHEMA_VERSION"


@pytest.mark.asyncio
@patch('backend.routes.admin_exercises_routes.get_chapter_by_official_code')
async def test_import_good_payload_success(mock_get_chapter, client, test_db, mock_chapter_6e_gm07):
    """Test que l'import avec un payload valide insère les exercices"""
    mock_get_chapter.return_value = mock_chapter_6e_gm07
    
    chapter_code = "6E_GM07"
    collection = test_db[EXERCISES_COLLECTION]
    
    # Nettoyer avant le test
    await collection.delete_many({"chapter_code": chapter_code})
    
    payload = {
        "schema_version": "1.0",
        "chapter_code": chapter_code,
        "exercises": [
            {
                "id": 1000001,  # ID unique
                "chapter_code": chapter_code,
                "enonce_html": "<p>Énoncé test 1</p>",
                "solution_html": "<p>Solution test 1. Donc explication.</p>",
                "offer": "free",
                "difficulty": "facile",
            },
            {
                "id": 1000002,  # ID unique
                "chapter_code": chapter_code,
                "enonce_html": "<p>Énoncé test 2</p>",
                "solution_html": "<p>Solution test 2. Donc explication.</p>",
                "offer": "free",
                "difficulty": "facile",
            },
        ],
        "metadata": {
            "total_exercises": 2
        }
    }
    
    response = await client.post(
        f"/api/admin/chapters/{chapter_code}/exercises/import",
        json=payload
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["success"] is True
    assert data["imported"] == 2
    
    # Vérifier l'insertion en DB
    count = await collection.count_documents({"chapter_code": chapter_code})
    assert count == 2, f"Expected 2 exercises, got {count}"
    
    # Nettoyer après le test
    await collection.delete_many({"chapter_code": chapter_code})


@pytest.mark.asyncio
@patch('backend.routes.admin_exercises_routes.get_chapter_by_official_code')
async def test_import_rollback_on_exception(mock_get_chapter, client, test_db, mock_chapter_6e_gm07):
    """Test que le rollback fonctionne en cas d'exception pendant insert_many (partial insert)"""
    # Configurer le mock pour retourner notre chapitre
    mock_get_chapter.return_value = mock_chapter_6e_gm07
    
    chapter_code = "6E_GM07"
    
    # S'assurer que le chapitre existe dans curriculum_chapters (comme dans test_import_good_payload_success)
    from backend.constants.collections import CURRICULUM_CHAPTERS_COLLECTION
    curriculum_collection = test_db[CURRICULUM_CHAPTERS_COLLECTION]
    await curriculum_collection.update_one(
        {"code_officiel": "6e_GM07"},
        {"$set": {
            "code_officiel": "6e_GM07",
            "level": "6e",
            "title": "GM07 TEST",
            "is_active": True,
            "order": 1
        }},
        upsert=True
    )
    
    # Nettoyer la DB avant le test
    collection = test_db[EXERCISES_COLLECTION]
    await collection.delete_many({"chapter_code": chapter_code})
    
    payload = {
        "schema_version": "1.0",
        "chapter_code": chapter_code,
        "exercises": [
            {
                "chapter_code": chapter_code,
                "enonce_html": "<p>Énoncé test</p>",
                "solution_html": "<p>Solution test. Donc explication.</p>",
                "offer": "free",
                "difficulty": "facile",
            },
            {
                "chapter_code": chapter_code,
                "enonce_html": "<p>Énoncé test 2</p>",
                "solution_html": "<p>Solution test 2. Donc explication.</p>",
                "offer": "free",
                "difficulty": "facile",
            },
        ],
        "metadata": {
            "total_exercises": 2
        }
    }
    
    # IMPORTANT: La route fait collection = db[EXERCISES_COLLECTION] où db vient de get_db()
    # get_db() retourne app.state.db qui est test_db
    # Le problème est que test_db.__getitem__ est une méthode liée, donc on doit utiliser patch.object
    # sur la classe AsyncIOMotorDatabase pour intercepter __getitem__
    
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from unittest.mock import patch as mock_patch
    
    original_insert_one = collection.insert_one
    original_insert_many = collection.insert_many
    
    # Créer une collection mockée qui sera retournée par test_db[EXERCISES_COLLECTION]
    # On copie toutes les méthodes de la vraie collection sauf insert_many
    from unittest.mock import MagicMock
    mock_collection = MagicMock()
    # Copier les méthodes réelles nécessaires
    mock_collection.insert_one = original_insert_one
    mock_collection.count_documents = collection.count_documents
    mock_collection.delete_many = collection.delete_many
    
    async def insert_many_side_effect(docs, *args, **kwargs):
        """Simule un insert partiel : insère le premier doc puis lève une exception"""
        # La route ajoute batch_id avant d'appeler insert_many, donc docs[0] a déjà batch_id
        # Insérer seulement le premier document pour simuler un insert partiel
        if len(docs) > 0:
            await original_insert_one(docs[0])
        # Lever une exception pour simuler l'échec
        raise Exception("Simulated insertion error after partial insert")
    
    # Patcher insert_many sur la collection mockée
    mock_collection.insert_many = insert_many_side_effect
    
    # Patcher __getitem__ sur la classe AsyncIOMotorDatabase pour intercepter les appels
    # On doit vérifier que c'est test_db qui appelle __getitem__
    original_getitem = AsyncIOMotorDatabase.__getitem__
    
    def mock_getitem(self, key):
        # Si c'est test_db qui appelle et qu'on demande EXERCISES_COLLECTION, retourner mock_collection
        if self is test_db and key == EXERCISES_COLLECTION:
            return mock_collection
        return original_getitem(self, key)
    
    # Utiliser patch.object pour patcher __getitem__ sur la classe
    with mock_patch.object(AsyncIOMotorDatabase, '__getitem__', mock_getitem):
        response = await client.post(
            f"/api/admin/chapters/{chapter_code}/exercises/import",
            json=payload
        )
        
        # L'import doit échouer avec 500
        assert response.status_code == 500, f"Expected 500, got {response.status_code}: {response.json()}"
        detail = response.json()["detail"]
        assert detail["error_code"] == "IMPORT_FAILED"
        assert detail.get("rollback_performed") is True
    
    # Vérifier rollback effectif: 0 doc restant pour ce chapitre
    # Le rollback doit avoir supprimé tous les documents avec le batch_id
    remaining = await collection.count_documents({"chapter_code": chapter_code})
    assert remaining == 0, f"Aucun exercice ne devrait rester après rollback, mais {remaining} trouvé(s)"
    
    # Nettoyer après le test
    await collection.delete_many({"chapter_code": chapter_code})
    await curriculum_collection.delete_many({"code_officiel": "6e_GM07"})


@pytest.mark.asyncio
@patch('backend.routes.admin_exercises_routes.get_chapter_by_official_code')
async def test_export_versioned_format(mock_get_chapter, client, test_db, mock_chapter_6e_gm07):
    """Test que l'export retourne le format versionné v1.0"""
    mock_get_chapter.return_value = mock_chapter_6e_gm07
    
    chapter_code = "6E_GM07"
    
    # S'assurer que le chapitre existe dans curriculum_chapters (comme dans les autres tests)
    from backend.constants.collections import CURRICULUM_CHAPTERS_COLLECTION
    curriculum_collection = test_db[CURRICULUM_CHAPTERS_COLLECTION]
    await curriculum_collection.update_one(
        {"code_officiel": "6e_GM07"},
        {"$set": {
            "code_officiel": "6e_GM07",
            "level": "6e",
            "title": "GM07 TEST",
            "is_active": True,
            "order": 1
        }},
        upsert=True
    )
    
    collection = test_db[EXERCISES_COLLECTION]
    
    # Nettoyer avant le test
    await collection.delete_many({"chapter_code": chapter_code})
    
    # Insérer 2 exercices de test avec chapter_code en UPPERCASE (comme normalisé par l'export)
    # L'export normalise chapter_code avec .upper().replace("-", "_")
    normalized_chapter_code = chapter_code.upper().replace("-", "_")
    await collection.insert_many([
        {
            "id": 2000001,
            "chapter_code": normalized_chapter_code,  # UPPERCASE comme normalisé par l'export
            "enonce_html": "<p>Énoncé export test 1</p>",
            "solution_html": "<p>Solution export test 1</p>",
            "offer": "free",
            "difficulty": "facile",
        },
        {
            "id": 2000002,
            "chapter_code": normalized_chapter_code,  # UPPERCASE comme normalisé par l'export
            "enonce_html": "<p>Énoncé export test 2</p>",
            "solution_html": "<p>Solution export test 2</p>",
            "offer": "free",
            "difficulty": "facile",
        },
    ])
    
    response = await client.get(
        f"/api/admin/chapters/{chapter_code}/exercises-export"
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    payload = response.json()
    
    assert payload["schema_version"] == "1.0"
    assert payload["chapter_code"] == normalized_chapter_code  # L'export normalise en uppercase
    assert "exported_at" in payload
    assert payload["metadata"]["total_exercises"] == 2
    assert len(payload["exercises"]) == 2
    
    # Nettoyer après le test
    await collection.delete_many({"chapter_code": normalized_chapter_code})
    await curriculum_collection.delete_many({"code_officiel": "6e_GM07"})
