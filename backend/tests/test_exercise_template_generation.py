"""
Tests pour le système de génération d'exercices par TEMPLATE
Validation de la reproductibilité et du déterminisme
"""

import pytest
import asyncio
from httpx import AsyncClient
import sys
from pathlib import Path

# Ajouter le répertoire backend au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import app
from services.exercise_template_service import exercise_template_service


@pytest.fixture
async def client():
    """Client HTTP async pour les tests"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def sample_exercise_type(client):
    """Créer un ExerciseType de test"""
    # Créer une compétence
    comp_response = await client.post("/api/mathalea/competences", json={
        "code": "TEST_GEN",
        "intitule": "Test génération",
        "niveau": "6e",
        "domaine": "Test"
    })
    comp_id = comp_response.json()["id"]
    
    # Créer un ExerciseType
    exercise_type_response = await client.post("/api/mathalea/exercise-types", json={
        "code_ref": "TEST_GEN_01",
        "titre": "Test génération simple",
        "niveau": "6e",
        "domaine": "Test",
        "competences_ids": [comp_id],
        "min_questions": 1,
        "max_questions": 20,
        "default_questions": 5,
        "difficulty_levels": ["facile", "moyen", "difficile"],
        "question_kinds": {
            "trouver_valeur": True
        },
        "random_config": {
            "min_value": 1,
            "max_value": 10,
            "operations": ["+", "-", "*"]
        },
        "generator_kind": "template",
        "supports_seed": True
    })
    
    return exercise_type_response.json()


# ============================================================================
# TEST 1: Reproductibilité avec seed
# ============================================================================

@pytest.mark.asyncio
async def test_reproducibility_same_seed(client, sample_exercise_type):
    """Test : Même seed → Même exercice"""
    exercise_type_id = sample_exercise_type["id"]
    seed = 42
    
    # Première génération
    response1 = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": exercise_type_id,
        "nb_questions": 5,
        "seed": seed,
        "difficulty": "moyen"
    })
    
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Deuxième génération avec même seed
    response2 = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": exercise_type_id,
        "nb_questions": 5,
        "seed": seed,
        "difficulty": "moyen"
    })
    
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Vérifier que les questions sont identiques
    assert len(data1["questions"]) == len(data2["questions"])
    
    for q1, q2 in zip(data1["questions"], data2["questions"]):
        assert q1["enonce_brut"] == q2["enonce_brut"]
        assert q1["solution_brut"] == q2["solution_brut"]
        assert q1["data"] == q2["data"]
    
    print("\n✅ Reproductibilité validée : même seed = même exercice")


@pytest.mark.asyncio
async def test_different_seeds_different_exercises(client, sample_exercise_type):
    """Test : Seeds différentes → Exercices différents"""
    exercise_type_id = sample_exercise_type["id"]
    
    # Génération avec seed 42
    response1 = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": exercise_type_id,
        "nb_questions": 3,
        "seed": 42,
        "difficulty": "moyen"
    })
    data1 = response1.json()
    
    # Génération avec seed 123
    response2 = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": exercise_type_id,
        "nb_questions": 3,
        "seed": 123,
        "difficulty": "moyen"
    })
    data2 = response2.json()
    
    # Vérifier que les questions sont différentes
    questions_equal = all(
        q1["data"] == q2["data"]
        for q1, q2 in zip(data1["questions"], data2["questions"])
    )
    
    assert not questions_equal, "Les exercices devraient être différents avec des seeds différentes"
    
    print("\n✅ Seeds différentes → exercices différents")


# ============================================================================
# TEST 2: Nombre de questions
# ============================================================================

@pytest.mark.asyncio
async def test_generate_1_question(client, sample_exercise_type):
    """Test : Génération d'1 question"""
    exercise_type_id = sample_exercise_type["id"]
    
    response = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": exercise_type_id,
        "nb_questions": 1,
        "seed": 100,
        "difficulty": "facile"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["questions"]) == 1
    assert data["questions"][0]["id"] == "q1"
    assert "enonce_brut" in data["questions"][0]
    assert "solution_brut" in data["questions"][0]
    
    print("\n✅ Génération d'1 question : OK")


@pytest.mark.asyncio
async def test_generate_3_questions(client, sample_exercise_type):
    """Test : Génération de 3 questions"""
    exercise_type_id = sample_exercise_type["id"]
    
    response = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": exercise_type_id,
        "nb_questions": 3,
        "seed": 200,
        "difficulty": "moyen"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["questions"]) == 3
    assert data["questions"][0]["id"] == "q1"
    assert data["questions"][1]["id"] == "q2"
    assert data["questions"][2]["id"] == "q3"
    
    print("\n✅ Génération de 3 questions : OK")


@pytest.mark.asyncio
async def test_generate_10_questions(client, sample_exercise_type):
    """Test : Génération de 10 questions"""
    exercise_type_id = sample_exercise_type["id"]
    
    response = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": exercise_type_id,
        "nb_questions": 10,
        "seed": 300,
        "difficulty": "difficile"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["questions"]) == 10
    
    # Vérifier que toutes les questions sont uniques
    ids = [q["id"] for q in data["questions"]]
    assert len(ids) == len(set(ids)), "Les IDs des questions doivent être uniques"
    
    print("\n✅ Génération de 10 questions : OK")


# ============================================================================
# TEST 3: Validation des contraintes
# ============================================================================

@pytest.mark.asyncio
async def test_validate_min_questions(client, sample_exercise_type):
    """Test : Validation du nombre minimum de questions"""
    exercise_type_id = sample_exercise_type["id"]
    
    # Tenter de générer 0 questions (min = 1)
    response = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": exercise_type_id,
        "nb_questions": 0,
        "seed": 400
    })
    
    assert response.status_code == 400
    assert "min_questions" in response.json()["detail"]
    
    print("\n✅ Validation min_questions : OK")


@pytest.mark.asyncio
async def test_validate_max_questions(client, sample_exercise_type):
    """Test : Validation du nombre maximum de questions"""
    exercise_type_id = sample_exercise_type["id"]
    
    # Tenter de générer 25 questions (max = 20)
    response = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": exercise_type_id,
        "nb_questions": 25,
        "seed": 500
    })
    
    assert response.status_code == 400
    assert "max_questions" in response.json()["detail"]
    
    print("\n✅ Validation max_questions : OK")


@pytest.mark.asyncio
async def test_validate_difficulty(client, sample_exercise_type):
    """Test : Validation de la difficulté"""
    exercise_type_id = sample_exercise_type["id"]
    
    # Tenter avec une difficulté invalide
    response = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": exercise_type_id,
        "nb_questions": 2,
        "seed": 600,
        "difficulty": "impossible"  # Pas dans difficulty_levels
    })
    
    assert response.status_code == 400
    assert "difficulty" in response.json()["detail"]
    
    print("\n✅ Validation difficulty : OK")


# ============================================================================
# TEST 4: Influence de random_config
# ============================================================================

@pytest.mark.asyncio
async def test_random_config_influences_generation(client):
    """Test : random_config influence bien la génération"""
    # Créer deux ExerciseTypes avec des random_config différents
    
    # Type 1 : valeurs 1-10
    type1_response = await client.post("/api/mathalea/exercise-types", json={
        "code_ref": "CONFIG_TEST_1",
        "titre": "Config Test 1",
        "niveau": "6e",
        "domaine": "Test",
        "min_questions": 1,
        "max_questions": 5,
        "default_questions": 1,
        "question_kinds": {"trouver_valeur": True},
        "random_config": {
            "min_value": 1,
            "max_value": 10
        },
        "generator_kind": "template"
    })
    type1_id = type1_response.json()["id"]
    
    # Type 2 : valeurs 50-100
    type2_response = await client.post("/api/mathalea/exercise-types", json={
        "code_ref": "CONFIG_TEST_2",
        "titre": "Config Test 2",
        "niveau": "6e",
        "domaine": "Test",
        "min_questions": 1,
        "max_questions": 5,
        "default_questions": 1,
        "question_kinds": {"trouver_valeur": True},
        "random_config": {
            "min_value": 50,
            "max_value": 100
        },
        "generator_kind": "template"
    })
    type2_id = type2_response.json()["id"]
    
    # Générer avec même seed mais configs différentes
    response1 = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": type1_id,
        "nb_questions": 1,
        "seed": 42
    })
    
    response2 = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": type2_id,
        "nb_questions": 1,
        "seed": 42
    })
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Les valeurs générées doivent être dans les bonnes plages
    value_a_1 = data1["questions"][0]["data"]["value_a"]
    value_a_2 = data2["questions"][0]["data"]["value_a"]
    
    assert 1 <= value_a_1 <= 10, "Value 1 devrait être dans [1, 10]"
    assert 50 <= value_a_2 <= 100, "Value 2 devrait être dans [50, 100]"
    
    print(f"\n✅ random_config influence la génération : {value_a_1} vs {value_a_2}")


# ============================================================================
# TEST 5: Structure de sortie
# ============================================================================

@pytest.mark.asyncio
async def test_output_structure(client, sample_exercise_type):
    """Test : Vérifier la structure de sortie standardisée"""
    exercise_type_id = sample_exercise_type["id"]
    
    response = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": exercise_type_id,
        "nb_questions": 2,
        "seed": 700
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier la structure principale
    assert "exercise_type_id" in data
    assert "exercise_type" in data
    assert "seed" in data
    assert "difficulty" in data
    assert "nb_questions" in data
    assert "questions" in data
    assert "metadata" in data
    
    # Vérifier exercise_type
    assert "code_ref" in data["exercise_type"]
    assert "titre" in data["exercise_type"]
    assert "niveau" in data["exercise_type"]
    assert "domaine" in data["exercise_type"]
    
    # Vérifier metadata
    assert "generator_kind" in data["metadata"]
    assert "supports_seed" in data["metadata"]
    assert "competences_ids" in data["metadata"]
    
    # Vérifier structure des questions
    for question in data["questions"]:
        assert "id" in question
        assert "enonce_brut" in question
        assert "data" in question
        assert "solution_brut" in question
        assert "metadata" in question
        
        # Vérifier metadata de la question
        assert "difficulty" in question["metadata"]
        assert "competences" in question["metadata"]
        assert "question_number" in question["metadata"]
    
    print("\n✅ Structure de sortie standardisée : OK")


# ============================================================================
# TEST 6: Types de questions
# ============================================================================

@pytest.mark.asyncio
async def test_trouver_valeur_type(client):
    """Test : Génération type 'trouver_valeur'"""
    # Créer un ExerciseType de type trouver_valeur
    ex_type_response = await client.post("/api/mathalea/exercise-types", json={
        "code_ref": "TROUVER_VAL_TEST",
        "titre": "Test trouver valeur",
        "niveau": "6e",
        "domaine": "Test",
        "question_kinds": {
            "trouver_valeur": True
        },
        "random_config": {
            "min_value": 1,
            "max_value": 20
        },
        "generator_kind": "template"
    })
    ex_type_id = ex_type_response.json()["id"]
    
    response = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": ex_type_id,
        "nb_questions": 1,
        "seed": 800
    })
    
    assert response.status_code == 200
    data = response.json()
    
    question = data["questions"][0]
    assert question["data"]["type"] == "trouver_valeur"
    assert "value_a" in question["data"]
    assert "value_b" in question["data"]
    
    print("\n✅ Type 'trouver_valeur' : OK")


@pytest.mark.asyncio
async def test_verifier_propriete_type(client):
    """Test : Génération type 'verifier_propriete'"""
    # Créer un ExerciseType de type verifier_propriete
    ex_type_response = await client.post("/api/mathalea/exercise-types", json={
        "code_ref": "VERIF_PROP_TEST",
        "titre": "Test vérifier propriété",
        "niveau": "6e",
        "domaine": "Test",
        "question_kinds": {
            "verifier_propriete": True
        },
        "random_config": {
            "min_value": 1,
            "max_value": 20,
            "property_type": "egalite"
        },
        "generator_kind": "template"
    })
    ex_type_id = ex_type_response.json()["id"]
    
    response = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": ex_type_id,
        "nb_questions": 1,
        "seed": 900
    })
    
    assert response.status_code == 200
    data = response.json()
    
    question = data["questions"][0]
    assert question["data"]["type"] == "verifier_propriete"
    assert "expected_answer" in question["data"]
    assert isinstance(question["data"]["expected_answer"], bool)
    
    print("\n✅ Type 'verifier_propriete' : OK")


# ============================================================================
# TEST 7: Difficulté influence la génération
# ============================================================================

@pytest.mark.asyncio
async def test_difficulty_affects_values(client, sample_exercise_type):
    """Test : La difficulté influence les valeurs générées"""
    exercise_type_id = sample_exercise_type["id"]
    seed = 1000
    
    # Génération facile
    response_facile = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": exercise_type_id,
        "nb_questions": 5,
        "seed": seed,
        "difficulty": "facile"
    })
    
    # Génération difficile
    response_difficile = await client.post("/api/mathalea/generate-exercise", json={
        "exercise_type_id": exercise_type_id,
        "nb_questions": 5,
        "seed": seed,
        "difficulty": "difficile"
    })
    
    data_facile = response_facile.json()
    data_difficile = response_difficile.json()
    
    # Extraire les valeurs moyennes
    values_facile = []
    values_difficile = []
    
    for q in data_facile["questions"]:
        values_facile.append(q["data"].get("value_a", 0))
        values_facile.append(q["data"].get("value_b", 0))
    
    for q in data_difficile["questions"]:
        values_difficile.append(q["data"].get("value_a", 0))
        values_difficile.append(q["data"].get("value_b", 0))
    
    avg_facile = sum(values_facile) / len(values_facile)
    avg_difficile = sum(values_difficile) / len(values_difficile)
    
    # Les valeurs difficiles devraient être en moyenne plus grandes
    # (à cause du difficulty_multiplier)
    assert avg_difficile >= avg_facile, "Les valeurs difficiles devraient être >= faciles"
    
    print(f"\n✅ Difficulté influence les valeurs : facile={avg_facile:.1f}, difficile={avg_difficile:.1f}")


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v", "-s"])
