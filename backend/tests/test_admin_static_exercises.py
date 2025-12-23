"""
Tests pour les endpoints admin exercices statiques (P1.5 - Partie 2/3)

Tests de:
- GET /api/v1/admin/chapters/{code}/static-exercises
- PUT /api/v1/admin/static-exercises/{id}
- POST /api/v1/admin/chapters/{code}/static-exercises
- DELETE /api/v1/admin/static-exercises/{id}
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from backend.server import app

@pytest.fixture
def client(mock_service):
    """Client de test FastAPI avec service mocké"""
    from backend.routes.admin_static_exercises_routes import get_exercise_service
    
    # Remplacer la dépendance par le mock
    app.dependency_overrides[get_exercise_service] = lambda: mock_service
    
    yield TestClient(app)
    
    # Nettoyer après le test
    app.dependency_overrides.clear()


@pytest.fixture
def mock_service(mocker):
    """
    Mock du ExercisePersistenceService.
    
    Simule une base de données avec quelques exercices de test.
    """
    # Exercices de test
    mock_exercises = {
        1: {
            "id": 1,
            "chapter_code": "6e_GM07",
            "title": "Lecture de l'heure - 8h30",
            "difficulty": "facile",
            "enonce_html": "<p>Quelle heure indique l'horloge ?</p>",
            "solution_html": "<p><strong>Réponse :</strong> 8h30</p>",
            "tags": ["horloge", "lecture"],
            "order": 1,
            "exercise_type": "LECTURE_HEURE",
            "offer": "free",
            "is_dynamic": False,
            "generator_key": None,
            "updated_at": datetime.utcnow()
        },
        2: {
            "id": 2,
            "chapter_code": "6e_GM07",
            "title": "Exercice dynamique (ne doit pas apparaître)",
            "difficulty": "moyen",
            "enonce_html": "",
            "solution_html": "",
            "is_dynamic": True,
            "generator_key": "LECTURE_HORLOGE",
            "order": 2,
            "updated_at": datetime.utcnow()
        },
        3: {
            "id": 3,
            "chapter_code": "6e_GM07",
            "title": "Lecture de l'heure - 14h45",
            "difficulty": "moyen",
            "enonce_html": "<p>Quelle heure est-il ?</p>",
            "solution_html": "<p><strong>Réponse :</strong> 14h45</p>",
            "tags": ["horloge"],
            "order": None,
            "exercise_type": "LECTURE_HEURE",
            "offer": "free",
            "is_dynamic": False,
            "generator_key": None,
            "updated_at": datetime.utcnow()
        }
    }
    
    next_id = [4]  # Compteur pour les nouveaux IDs
    
    # Mock des méthodes du service
    async def get_all_by_chapter(chapter_code):
        return [ex for ex in mock_exercises.values() if ex["chapter_code"] == chapter_code]
    
    async def get_by_id(exercise_id):
        return mock_exercises.get(exercise_id)
    
    async def update(exercise_id, update_data):
        if exercise_id not in mock_exercises:
            return None
        mock_exercises[exercise_id].update(update_data)
        return mock_exercises[exercise_id]
    
    async def create(exercise_dict):
        new_id = next_id[0]
        next_id[0] += 1
        exercise_dict["id"] = new_id
        mock_exercises[new_id] = exercise_dict
        return exercise_dict
    
    async def delete(exercise_id):
        if exercise_id not in mock_exercises:
            return False
        del mock_exercises[exercise_id]
        return True
    
    # Créer le mock
    mock_svc = mocker.Mock()
    mock_svc.get_all_by_chapter = get_all_by_chapter
    mock_svc.get_by_id = get_by_id
    mock_svc.update = update
    mock_svc.create = create
    mock_svc.delete = delete
    
    return mock_svc


# =============================================================================
# TESTS GET /api/v1/admin/chapters/{code}/static-exercises
# =============================================================================

def test_list_static_by_chapter(client, mock_service):
    """
    Test nominal: liste les exercices statiques d'un chapitre.
    
    Doit:
    - Retourner HTTP 200
    - Contenir uniquement les exercices statiques (is_dynamic=False)
    - Exclure les exercices dynamiques (is_dynamic=True)
    - Trier par order puis id
    """
    response = client.get("/api/v1/admin/chapters/6e_GM07/static-exercises")
    
    # Debug: afficher l'erreur si HTTP 500
    if response.status_code == 500:
        print(f"\n❌ Erreur 500: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Doit avoir 2 exercices statiques (ID 1 et 3)
    assert len(data) == 2
    
    # Premier exercice (order=1)
    assert data[0]["id"] == 1
    assert data[0]["title"] == "Lecture de l'heure - 8h30"
    # Note: is_dynamic et generator_key ne font pas partie de StaticExerciseResponse
    
    # Deuxième exercice (order=None → trié par id)
    assert data[1]["id"] == 3
    assert data[1]["title"] == "Lecture de l'heure - 14h45"


def test_list_static_empty_chapter(client, mock_service):
    """
    Test: chapitre vide ou sans exercices statiques.
    
    Doit retourner une liste vide (pas d'erreur 404).
    """
    response = client.get("/api/v1/admin/chapters/6e_N01/static-exercises")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


# =============================================================================
# TESTS PUT /api/v1/admin/static-exercises/{id}
# =============================================================================

def test_update_static_success(client, mock_service):
    """
    Test nominal: mise à jour d'un exercice statique.
    
    Doit:
    - Retourner HTTP 200
    - Mettre à jour les champs fournis
    - Préserver les champs non fournis
    """
    response = client.put(
        "/api/v1/admin/static-exercises/1",
        json={
            "enonce_html": "<p>Quelle heure indique l'horloge ci-dessous ?</p>",
            "solution_html": "<p><strong>Réponse :</strong> Il est 8 heures 30 minutes.</p>",
            "tags": ["horloge", "lecture", "matin"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == 1
    assert data["enonce_html"] == "<p>Quelle heure indique l'horloge ci-dessous ?</p>"
    assert data["solution_html"] == "<p><strong>Réponse :</strong> Il est 8 heures 30 minutes.</p>"
    assert data["tags"] == ["horloge", "lecture", "matin"]
    # Champs non modifiés doivent être préservés
    assert data["title"] == "Lecture de l'heure - 8h30"
    assert data["difficulty"] == "facile"


def test_update_static_not_found(client, mock_service):
    """
    Test: tentative de mise à jour d'un exercice inexistant.
    
    Doit retourner HTTP 404.
    """
    response = client.put(
        "/api/v1/admin/static-exercises/999",
        json={"enonce_html": "<p>Test</p>"}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["error_code"] == "EXERCISE_NOT_FOUND"


def test_cannot_update_dynamic_via_static_endpoint(client, mock_service):
    """
    Test CRITIQUE: tentative de modification d'un exercice dynamique.
    
    Doit:
    - Retourner HTTP 400
    - Refuser la modification
    - Fournir un message d'erreur clair
    """
    response = client.put(
        "/api/v1/admin/static-exercises/2",  # ID 2 = dynamique
        json={"enonce_html": "<p>Tentative de modification</p>"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error_code"] == "CANNOT_UPDATE_DYNAMIC_VIA_STATIC_ENDPOINT"
    assert "dynamique" in data["detail"]["message"].lower()
    assert data["detail"]["is_dynamic"] == True


def test_update_static_invalid_difficulty(client, mock_service):
    """
    Test: validation de la difficulté.
    
    Doit retourner HTTP 422 si difficulté invalide.
    """
    response = client.put(
        "/api/v1/admin/static-exercises/1",
        json={"difficulty": "tres_difficile"}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["error_code"] == "INVALID_DIFFICULTY"


def test_update_static_invalid_offer(client, mock_service):
    """
    Test: validation de l'offre.
    
    Doit retourner HTTP 422 si offre invalide.
    """
    response = client.put(
        "/api/v1/admin/static-exercises/1",
        json={"offer": "premium"}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["error_code"] == "INVALID_OFFER"


# =============================================================================
# TESTS POST /api/v1/admin/chapters/{code}/static-exercises
# =============================================================================

def test_create_static_success(client, mock_service):
    """
    Test nominal: création d'un exercice statique.
    
    Doit:
    - Retourner HTTP 201
    - Créer l'exercice avec is_dynamic=False
    - Retourner l'exercice créé avec son ID
    """
    response = client.post(
        "/api/v1/admin/chapters/6e_GM08/static-exercises",
        json={
            "title": "Nouveau problème de durées",
            "difficulty": "moyen",
            "enonce_html": "<p>Énoncé du problème...</p>",
            "solution_html": "<p>Solution du problème...</p>",
            "tags": ["durees", "probleme"],
            "order": 10
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["id"] is not None  # ID assigné
    assert data["chapter_code"] == "6e_GM08"
    assert data["title"] == "Nouveau problème de durées"
    assert data["difficulty"] == "moyen"
    assert data["enonce_html"] == "<p>Énoncé du problème...</p>"
    assert data["tags"] == ["durees", "probleme"]
    assert data["order"] == 10


def test_create_static_minimal(client, mock_service):
    """
    Test: création avec données minimales (utilise valeurs par défaut).
    """
    response = client.post(
        "/api/v1/admin/chapters/6e_N01/static-exercises",
        json={}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["chapter_code"] == "6e_N01"
    assert data["difficulty"] == "facile"  # Valeur par défaut
    assert "<p>" in data["enonce_html"]  # Template par défaut
    assert data["offer"] == "free"  # Valeur par défaut


def test_create_static_invalid_difficulty(client, mock_service):
    """
    Test: validation lors de la création.
    """
    response = client.post(
        "/api/v1/admin/chapters/6e_N01/static-exercises",
        json={"difficulty": "impossible"}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["error_code"] == "INVALID_DIFFICULTY"


# =============================================================================
# TESTS DELETE /api/v1/admin/static-exercises/{id}
# =============================================================================

def test_delete_static_success(client, mock_service):
    """
    Test nominal: suppression d'un exercice statique.
    
    Doit retourner HTTP 204 (No Content).
    """
    response = client.delete("/api/v1/admin/static-exercises/1")
    
    assert response.status_code == 204
    assert response.content == b""  # No content


def test_delete_static_not_found(client, mock_service):
    """
    Test: tentative de suppression d'un exercice inexistant.
    """
    response = client.delete("/api/v1/admin/static-exercises/999")
    
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["error_code"] == "EXERCISE_NOT_FOUND"


def test_cannot_delete_dynamic_via_static_endpoint(client, mock_service):
    """
    Test CRITIQUE: tentative de suppression d'un exercice dynamique.
    
    Doit retourner HTTP 400 et refuser.
    """
    response = client.delete("/api/v1/admin/static-exercises/2")  # ID 2 = dynamique
    
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error_code"] == "CANNOT_DELETE_DYNAMIC_VIA_STATIC_ENDPOINT"


# =============================================================================
# TESTS DE NON-RÉGRESSION
# =============================================================================

def test_static_exercises_preserved_after_operations(client, mock_service):
    """
    Test de non-régression: vérifier que les opérations sur statiques
    ne modifient pas les exercices dynamiques.
    """
    # 1. Lister les exercices statiques
    response1 = client.get("/api/v1/admin/chapters/6e_GM07/static-exercises")
    assert response1.status_code == 200
    static_before = response1.json()
    
    # 2. Modifier un exercice statique
    response2 = client.put(
        "/api/v1/admin/static-exercises/1",
        json={"title": "Titre modifié"}
    )
    assert response2.status_code == 200
    
    # 3. Re-lister les exercices statiques
    response3 = client.get("/api/v1/admin/chapters/6e_GM07/static-exercises")
    assert response3.status_code == 200
    static_after = response3.json()
    
    # Le nombre d'exercices statiques doit être identique
    assert len(static_after) == len(static_before)
    
    # L'exercice dynamique (ID 2) ne doit jamais apparaître
    static_ids = [ex["id"] for ex in static_after]
    assert 2 not in static_ids

