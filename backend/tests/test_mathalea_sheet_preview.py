"""
Tests pour le système de Preview de Fiches d'Exercices (Sprint C)

Couvre:
- Création de fiches avec items
- Génération de preview JSON
- Reproductibilité (seed)
- Validation des contraintes (min/max questions)
- Gestion des erreurs (ExerciseType inexistant)
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timezone
from uuid import uuid4
import sys
from pathlib import Path

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import app


@pytest_asyncio.fixture
async def client():
    """Client HTTP async pour les tests"""
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_competence(client):
    """Créer une compétence de test"""
    response = await client.post(
        "/api/mathalea/competences",
        json={
            "code": "TEST_C1",
            "intitule": "Compétence de test",
            "niveau": "6e",
            "domaine": "Test"
        }
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_exercise_type(client, test_competence):
    """Créer un ExerciseType de test"""
    response = await client.post(
        "/api/mathalea/exercise-types",
        json={
            "code_ref": "TEST_EX_01",
            "titre": "Exercice de test",
            "chapitre_id": "test_chapter",
            "niveau": "6e",
            "domaine": "Test",
            "competences_ids": [test_competence["id"]],
            "min_questions": 1,
            "max_questions": 10,
            "default_questions": 5,
            "difficulty_levels": ["facile", "moyen", "difficile"],
            "question_kinds": {"trouver_valeur": True},
            "random_config": {
                "min_value": 1,
                "max_value": 10,
                "operations": ["+", "-"]
            },
            "generator_kind": "template",
            "supports_seed": True
        }
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_sheet(client):
    """Créer une feuille de test"""
    response = await client.post(
        "/api/mathalea/sheets",
        json={
            "titre": "Feuille de test",
            "niveau": "6e",
            "owner_id": "test_user"
        }
    )
    assert response.status_code == 201
    return response.json()


# ============================================================================
# TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_preview_empty_sheet(client, test_sheet):
    """
    TEST 1: Création d'une fiche avec 0 item
    → preview renvoie une structure avec items = []
    """
    sheet_id = test_sheet["id"]
    
    # Appeler le preview
    response = await client.post(f"/api/mathalea/sheets/{sheet_id}/preview")
    
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier la structure
    assert data["sheet_id"] == sheet_id
    assert data["titre"] == "Feuille de test"
    assert data["niveau"] == "6e"
    assert data["items"] == []


@pytest.mark.asyncio
async def test_preview_with_two_items(client, test_sheet, test_exercise_type):
    """
    TEST 2: Ajout de 2 SheetItem avec des seeds différentes
    → preview renvoie bien 2 blocs generated, chacun avec des questions
    """
    sheet_id = test_sheet["id"]
    exercise_type_id = test_exercise_type["id"]
    
    # Ajouter 2 items avec des seeds différentes
    item1_response = await client.post(
        f"/api/mathalea/sheets/{sheet_id}/items",
        json={
            "exercise_type_id": exercise_type_id,
            "config": {
                "nb_questions": 3,
                "difficulty": "facile",
                "seed": 100,
                "options": {},
                "ai_enonce": False,
                "ai_correction": False
            }
        }
    )
    assert item1_response.status_code == 201
    item1 = item1_response.json()
    
    item2_response = await client.post(
        f"/api/mathalea/sheets/{sheet_id}/items",
        json={
            "exercise_type_id": exercise_type_id,
            "config": {
                "nb_questions": 5,
                "difficulty": "moyen",
                "seed": 200,
                "options": {},
                "ai_enonce": False,
                "ai_correction": False
            }
        }
    )
    assert item2_response.status_code == 201
    item2 = item2_response.json()
    
    # Appeler le preview
    preview_response = await client.post(
        f"/api/mathalea/sheets/{sheet_id}/preview"
    )
    
    assert preview_response.status_code == 200
    preview_data = preview_response.json()
    
    # Vérifier la structure
    assert preview_data["sheet_id"] == sheet_id
    assert len(preview_data["items"]) == 2
    
    # Vérifier item 1
    preview_item1 = preview_data["items"][0]
    assert preview_item1["item_id"] == item1["id"]
    assert preview_item1["exercise_type_id"] == exercise_type_id
    assert preview_item1["exercise_type_summary"]["code_ref"] == "TEST_EX_01"
    assert preview_item1["config"]["nb_questions"] == 3
    assert preview_item1["config"]["seed"] == 100
    assert "generated" in preview_item1
    assert len(preview_item1["generated"]["questions"]) == 3
    assert preview_item1["generated"]["seed"] == 100
    
    # Vérifier item 2
    preview_item2 = preview_data["items"][1]
    assert preview_item2["item_id"] == item2["id"]
    assert preview_item2["config"]["nb_questions"] == 5
    assert preview_item2["config"]["seed"] == 200
    assert len(preview_item2["generated"]["questions"]) == 5
    assert preview_item2["generated"]["seed"] == 200


@pytest.mark.asyncio
async def test_preview_reproducibility(client, test_sheet, test_exercise_type):
    """
    TEST 3: Même fiche + mêmes seeds
    → deux appels consécutifs à /preview renvoient des données identiques
    (reproductibilité)
    """
    sheet_id = test_sheet["id"]
    exercise_type_id = test_exercise_type["id"]
    
    # Ajouter un item avec un seed fixe
    await client.post(
        f"/api/mathalea/sheets/{sheet_id}/items",
        json={
            "exercise_type_id": exercise_type_id,
            "config": {
                "nb_questions": 4,
                "difficulty": "moyen",
                "seed": 42,
                "options": {},
                "ai_enonce": False,
                "ai_correction": False
            }
        }
    )
    
    # Appeler le preview deux fois
    preview1_response = await client.post(
        f"/api/mathalea/sheets/{sheet_id}/preview"
    )
    preview2_response = await client.post(
        f"/api/mathalea/sheets/{sheet_id}/preview"
    )
    
    assert preview1_response.status_code == 200
    assert preview2_response.status_code == 200
    
    preview1 = preview1_response.json()
    preview2 = preview2_response.json()
    
    # Vérifier que les questions générées sont identiques
    assert len(preview1["items"]) == len(preview2["items"])
    
    for i in range(len(preview1["items"])):
        item1 = preview1["items"][i]
        item2 = preview2["items"][i]
        
        # Les questions doivent être identiques
        questions1 = item1["generated"]["questions"]
        questions2 = item2["generated"]["questions"]
        
        assert len(questions1) == len(questions2)
        
        for j in range(len(questions1)):
            q1 = questions1[j]
            q2 = questions2[j]
            
            # Vérifier que l'énoncé, la solution et les données sont identiques
            assert q1["enonce_brut"] == q2["enonce_brut"]
            assert q1["solution_brut"] == q2["solution_brut"]
            assert q1["data"] == q2["data"]


@pytest.mark.asyncio
async def test_preview_nb_questions_below_min(client, test_sheet, test_exercise_type):
    """
    TEST 4a: Contrôle min/max
    Si config.nb_questions est en dessous du min → erreur 422
    """
    sheet_id = test_sheet["id"]
    exercise_type_id = test_exercise_type["id"]
    
    # test_exercise_type a min_questions = 1
    # Essayer d'ajouter un item avec nb_questions = 0
    response = await client.post(
        f"/api/mathalea/sheets/{sheet_id}/items",
        json={
            "exercise_type_id": exercise_type_id,
            "config": {
                "nb_questions": 0,
                "difficulty": "facile",
                "seed": 123,
                "options": {},
                "ai_enonce": False,
                "ai_correction": False
            }
        }
    )
    
    assert response.status_code == 422
    assert "min_questions" in response.json()["detail"]


@pytest.mark.asyncio
async def test_preview_nb_questions_above_max(client, test_sheet, test_exercise_type):
    """
    TEST 4b: Contrôle min/max
    Si config.nb_questions est au-dessus du max → erreur 422
    """
    sheet_id = test_sheet["id"]
    exercise_type_id = test_exercise_type["id"]
    
    # test_exercise_type a max_questions = 10
    # Essayer d'ajouter un item avec nb_questions = 20
    response = await client.post(
        f"/api/mathalea/sheets/{sheet_id}/items",
        json={
            "exercise_type_id": exercise_type_id,
            "config": {
                "nb_questions": 20,
                "difficulty": "facile",
                "seed": 123,
                "options": {},
                "ai_enonce": False,
                "ai_correction": False
            }
        }
    )
    
    assert response.status_code == 422
    assert "max_questions" in response.json()["detail"]


@pytest.mark.asyncio
async def test_preview_exercise_type_not_found(client, test_sheet):
    """
    TEST 5: Erreur
    Si ExerciseType n'existe plus pour un item → erreur propre 404
    """
    sheet_id = test_sheet["id"]
    fake_exercise_type_id = str(uuid4())
    
    # Essayer d'ajouter un item avec un ExerciseType inexistant
    response = await client.post(
        f"/api/mathalea/sheets/{sheet_id}/items",
        json={
            "exercise_type_id": fake_exercise_type_id,
            "config": {
                "nb_questions": 5,
                "difficulty": "moyen",
                "seed": 456,
                "options": {},
                "ai_enonce": False,
                "ai_correction": False
            }
        }
    )
    
    assert response.status_code == 404
    assert "ExerciseType not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_preview_invalid_difficulty(client, test_sheet, test_exercise_type):
    """
    TEST 6: Difficulté invalide
    Si difficulty n'est pas dans difficulty_levels → erreur 422
    """
    sheet_id = test_sheet["id"]
    exercise_type_id = test_exercise_type["id"]
    
    # test_exercise_type a difficulty_levels = ["facile", "moyen", "difficile"]
    # Essayer d'ajouter un item avec une difficulté invalide
    response = await client.post(
        f"/api/mathalea/sheets/{sheet_id}/items",
        json={
            "exercise_type_id": exercise_type_id,
            "config": {
                "nb_questions": 5,
                "difficulty": "impossible",
                "seed": 789,
                "options": {},
                "ai_enonce": False,
                "ai_correction": False
            }
        }
    )
    
    assert response.status_code == 422
    assert "difficulty" in response.json()["detail"]
    assert "available levels" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_sheet_items(client, test_sheet, test_exercise_type):
    """
    TEST 7: GET /api/mathalea/sheets/{sheet_id}/items
    Vérifier que l'endpoint retourne les items triés par order
    """
    sheet_id = test_sheet["id"]
    exercise_type_id = test_exercise_type["id"]
    
    # Ajouter 3 items
    for i in range(3):
        await client.post(
            f"/api/mathalea/sheets/{sheet_id}/items",
            json={
                "exercise_type_id": exercise_type_id,
                "config": {
                    "nb_questions": 2 + i,
                    "difficulty": "facile",
                    "seed": 100 + i,
                    "options": {},
                    "ai_enonce": False,
                    "ai_correction": False
                }
            }
        )
    
    # Récupérer les items
    response = await client.get(f"/api/mathalea/sheets/{sheet_id}/items")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    
    # Vérifier que les items sont triés par order
    for i, item in enumerate(data["items"]):
        assert item["config"]["nb_questions"] == 2 + i
        assert item["config"]["seed"] == 100 + i
        assert item["order"] == i + 1
