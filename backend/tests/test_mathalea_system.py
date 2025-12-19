"""
Tests pour le système MathALÉA
Valide les modèles et endpoints CRUD
"""

import pytest
import asyncio
from httpx import AsyncClient
import sys
from pathlib import Path

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import app


@pytest.fixture
async def client():
    """Client HTTP async pour les tests"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ============================================================================
# TESTS: Competence
# ============================================================================

@pytest.mark.asyncio
async def test_create_competence(client):
    """Test création d'une compétence"""
    competence_data = {
        "code": "6G1_TEST",
        "intitule": "Test - Reconnaître une symétrie axiale",
        "niveau": "6e",
        "domaine": "Espace et géométrie"
    }
    
    response = await client.post("/api/mathalea/competences", json=competence_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["code"] == competence_data["code"]
    assert data["intitule"] == competence_data["intitule"]
    assert "id" in data
    
    return data["id"]


@pytest.mark.asyncio
async def test_list_competences(client):
    """Test listage des compétences"""
    response = await client.get("/api/mathalea/competences")
    assert response.status_code == 200
    
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_filter_competences_by_niveau(client):
    """Test filtrage des compétences par niveau"""
    response = await client.get("/api/mathalea/competences?niveau=6e")
    assert response.status_code == 200
    
    data = response.json()
    for item in data["items"]:
        assert item["niveau"] == "6e"


@pytest.mark.asyncio
async def test_get_competence(client):
    """Test récupération d'une compétence par ID"""
    # Créer d'abord une compétence
    create_response = await client.post("/api/mathalea/competences", json={
        "code": "6G2_TEST",
        "intitule": "Test compétence",
        "niveau": "6e",
        "domaine": "Géométrie"
    })
    competence_id = create_response.json()["id"]
    
    # Récupérer la compétence
    response = await client.get(f"/api/mathalea/competences/{competence_id}")
    assert response.status_code == 200
    assert response.json()["id"] == competence_id


@pytest.mark.asyncio
async def test_update_competence(client):
    """Test mise à jour d'une compétence"""
    # Créer une compétence
    create_response = await client.post("/api/mathalea/competences", json={
        "code": "6G3_TEST",
        "intitule": "Ancien intitulé",
        "niveau": "6e",
        "domaine": "Géométrie"
    })
    competence_id = create_response.json()["id"]
    
    # Mettre à jour
    update_data = {"intitule": "Nouvel intitulé"}
    response = await client.patch(
        f"/api/mathalea/competences/{competence_id}",
        json=update_data
    )
    assert response.status_code == 200
    assert response.json()["intitule"] == "Nouvel intitulé"


@pytest.mark.asyncio
async def test_delete_competence(client):
    """Test suppression d'une compétence"""
    # Créer une compétence
    create_response = await client.post("/api/mathalea/competences", json={
        "code": "6G4_TEST",
        "intitule": "À supprimer",
        "niveau": "6e",
        "domaine": "Géométrie"
    })
    competence_id = create_response.json()["id"]
    
    # Supprimer
    response = await client.delete(f"/api/mathalea/competences/{competence_id}")
    assert response.status_code == 204
    
    # Vérifier qu'elle n'existe plus
    get_response = await client.get(f"/api/mathalea/competences/{competence_id}")
    assert get_response.status_code == 404


# ============================================================================
# TESTS: ExerciseType
# ============================================================================

@pytest.mark.asyncio
async def test_create_exercise_type(client):
    """Test création d'un type d'exercice"""
    exercise_type_data = {
        "code_ref": "SYM_AX_TEST_01",
        "titre": "Test - Symétrie axiale simple",
        "niveau": "6e",
        "domaine": "Géométrie",
        "min_questions": 1,
        "max_questions": 10,
        "default_questions": 5,
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "generator_kind": "template",
        "supports_seed": True,
        "supports_ai_enonce": False,
        "supports_ai_correction": False
    }
    
    response = await client.post("/api/mathalea/exercise-types", json=exercise_type_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["code_ref"] == exercise_type_data["code_ref"]
    assert data["titre"] == exercise_type_data["titre"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_list_exercise_types(client):
    """Test listage des types d'exercices"""
    response = await client.get("/api/mathalea/exercise-types")
    assert response.status_code == 200
    
    data = response.json()
    assert "total" in data
    assert "items" in data


@pytest.mark.asyncio
async def test_filter_exercise_types(client):
    """Test filtrage des types d'exercices"""
    response = await client.get("/api/mathalea/exercise-types?niveau=6e&domaine=Géométrie")
    assert response.status_code == 200
    
    data = response.json()
    for item in data["items"]:
        assert item["niveau"] == "6e"
        assert item["domaine"] == "Géométrie"


# ============================================================================
# TESTS: ExerciseSheet
# ============================================================================

@pytest.mark.asyncio
async def test_create_exercise_sheet(client):
    """Test création d'une feuille d'exercices"""
    sheet_data = {
        "titre": "Révisions géométrie 6e - Test",
        "niveau": "6e",
        "owner_id": "test_user_123"
    }
    
    response = await client.post("/api/mathalea/sheets", json=sheet_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["titre"] == sheet_data["titre"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_exercise_sheets(client):
    """Test listage des feuilles"""
    response = await client.get("/api/mathalea/sheets")
    assert response.status_code == 200
    
    data = response.json()
    assert "total" in data
    assert "items" in data


# ============================================================================
# TESTS: SheetItem
# ============================================================================

@pytest.mark.asyncio
async def test_create_sheet_item(client):
    """Test ajout d'un item à une feuille"""
    # Créer d'abord une feuille et un type d'exercice
    sheet_response = await client.post("/api/mathalea/sheets", json={
        "titre": "Test feuille",
        "niveau": "6e",
        "owner_id": "test_user"
    })
    sheet_id = sheet_response.json()["id"]
    
    exercise_type_response = await client.post("/api/mathalea/exercise-types", json={
        "code_ref": "TEST_ITEM_01",
        "titre": "Test exercice",
        "niveau": "6e",
        "domaine": "Test"
    })
    exercise_type_id = exercise_type_response.json()["id"]
    
    # Créer l'item
    item_data = {
        "sheet_id": sheet_id,
        "exercise_type_id": exercise_type_id,
        "nb_questions": 5,
        "difficulty": "moyen",
        "ai_enonce": False,
        "ai_correction": False
    }
    
    response = await client.post("/api/mathalea/sheet-items", json=item_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["sheet_id"] == sheet_id
    assert data["exercise_type_id"] == exercise_type_id
    assert data["order"] == 1  # Premier item


@pytest.mark.asyncio
async def test_list_sheet_items(client):
    """Test listage des items d'une feuille"""
    # Créer une feuille
    sheet_response = await client.post("/api/mathalea/sheets", json={
        "titre": "Test",
        "niveau": "6e",
        "owner_id": "test"
    })
    sheet_id = sheet_response.json()["id"]
    
    # Lister les items (devrait être vide)
    response = await client.get(f"/api/mathalea/sheet-items?sheet_id={sheet_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] == 0


# ============================================================================
# TEST D'INTÉGRATION
# ============================================================================

@pytest.mark.asyncio
async def test_full_workflow(client):
    """Test du workflow complet"""
    # 1. Créer une compétence
    comp_response = await client.post("/api/mathalea/competences", json={
        "code": "WORKFLOW_TEST",
        "intitule": "Test workflow",
        "niveau": "6e",
        "domaine": "Test"
    })
    comp_id = comp_response.json()["id"]
    
    # 2. Créer un type d'exercice lié à cette compétence
    ex_type_response = await client.post("/api/mathalea/exercise-types", json={
        "code_ref": "WORKFLOW_EX",
        "titre": "Exercice workflow",
        "niveau": "6e",
        "domaine": "Test",
        "competences_ids": [comp_id]
    })
    ex_type_id = ex_type_response.json()["id"]
    
    # 3. Créer une feuille
    sheet_response = await client.post("/api/mathalea/sheets", json={
        "titre": "Feuille workflow",
        "niveau": "6e",
        "owner_id": "workflow_user"
    })
    sheet_id = sheet_response.json()["id"]
    
    # 4. Ajouter un item à la feuille
    item_response = await client.post("/api/mathalea/sheet-items", json={
        "sheet_id": sheet_id,
        "exercise_type_id": ex_type_id,
        "nb_questions": 3,
        "difficulty": "facile"
    })
    
    assert item_response.status_code == 201
    
    # 5. Vérifier que tout est lié correctement
    item = item_response.json()
    assert item["sheet_id"] == sheet_id
    assert item["exercise_type_id"] == ex_type_id
    
    print("\n✅ Workflow complet validé!")


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v", "-s"])
