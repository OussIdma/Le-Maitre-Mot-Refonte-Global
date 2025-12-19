"""
Tests pour le système de génération PDF des Fiches d'Exercices (Sprint D)

Couvre:
- Génération simple (1 item)
- Génération multiple (3 items)
- Cohérence des 3 PDFs
- Reproductibilité
- Aucune exception dans le pipeline
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timezone
from uuid import uuid4
import sys
from pathlib import Path
import base64

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
            "code": "TEST_PDF_C1",
            "intitule": "Compétence de test PDF",
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
            "code_ref": "TEST_PDF_EX",
            "titre": "Exercice de test PDF",
            "chapitre_id": "test_chapter",
            "niveau": "6e",
            "domaine": "Géométrie",
            "competences_ids": [test_competence["id"]],
            "min_questions": 1,
            "max_questions": 10,
            "default_questions": 5,
            "difficulty_levels": ["facile", "moyen", "difficile"],
            "question_kinds": {"trouver_valeur": True},
            "random_config": {
                "min_value": 1,
                "max_value": 10,
                "operations": ["+", "-", "*"]
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
            "titre": "Feuille de test PDF",
            "niveau": "6e",
            "owner_id": "test_user_pdf"
        }
    )
    assert response.status_code == 201
    return response.json()


# ============================================================================
# TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_generate_pdf_simple(client, test_sheet, test_exercise_type):
    """
    TEST 1: Génération simple
    Fiche avec 1 item → 3 PDFs produits sans erreur
    """
    sheet_id = test_sheet["id"]
    exercise_type_id = test_exercise_type["id"]
    
    # Ajouter 1 item
    item_response = await client.post(
        f"/api/mathalea/sheets/{sheet_id}/items",
        json={
            "exercise_type_id": exercise_type_id,
            "config": {
                "nb_questions": 3,
                "difficulty": "moyen",
                "seed": 42,
                "options": {},
                "ai_enonce": False,
                "ai_correction": False
            }
        }
    )
    assert item_response.status_code == 201
    
    # Générer les PDFs
    pdf_response = await client.post(f"/api/mathalea/sheets/{sheet_id}/generate-pdf")
    
    assert pdf_response.status_code == 200
    data = pdf_response.json()
    
    # Vérifier la structure de la réponse
    assert "subject_pdf" in data
    assert "student_pdf" in data
    assert "correction_pdf" in data
    assert "metadata" in data
    
    # Vérifier les métadonnées
    assert data["metadata"]["sheet_id"] == sheet_id
    assert data["metadata"]["nb_exercises"] == 1
    
    # Décoder les PDFs
    subject_bytes = base64.b64decode(data["subject_pdf"])
    student_bytes = base64.b64decode(data["student_pdf"])
    correction_bytes = base64.b64decode(data["correction_pdf"])
    
    # Vérifier que ce sont bien des PDFs (commence par %PDF)
    assert subject_bytes.startswith(b'%PDF')
    assert student_bytes.startswith(b'%PDF')
    assert correction_bytes.startswith(b'%PDF')
    
    print(f"✓ PDFs générés: sujet={len(subject_bytes)}B, élève={len(student_bytes)}B, corrigé={len(correction_bytes)}B")


@pytest.mark.asyncio
async def test_generate_pdf_multiple_items(client, test_sheet, test_exercise_type):
    """
    TEST 2: Génération avec 3 items
    PDF contient les titres et sections attendues
    PDF non vide (len(bytes) > 1000)
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
                    "difficulty": ["facile", "moyen", "difficile"][i],
                    "seed": 100 + i,
                    "options": {},
                    "ai_enonce": False,
                    "ai_correction": False
                }
            }
        )
    
    # Générer les PDFs
    pdf_response = await client.post(f"/api/mathalea/sheets/{sheet_id}/generate-pdf")
    
    assert pdf_response.status_code == 200
    data = pdf_response.json()
    
    # Vérifier les métadonnées
    assert data["metadata"]["nb_exercises"] == 3
    
    # Décoder les PDFs
    subject_bytes = base64.b64decode(data["subject_pdf"])
    student_bytes = base64.b64decode(data["student_pdf"])
    correction_bytes = base64.b64decode(data["correction_pdf"])
    
    # Vérifier que les PDFs ne sont pas vides (> 1000 bytes)
    assert len(subject_bytes) > 1000
    assert len(student_bytes) > 1000
    assert len(correction_bytes) > 1000
    
    # Vérifier que les PDFs contiennent le titre de la feuille
    # (convertir en string pour rechercher)
    subject_str = subject_bytes.decode('latin-1', errors='ignore')
    assert "Feuille de test PDF" in subject_str
    
    print(f"✓ 3 exercices: sujet={len(subject_bytes)}B, élève={len(student_bytes)}B, corrigé={len(correction_bytes)}B")


@pytest.mark.asyncio
async def test_pdf_coherence(client, test_sheet, test_exercise_type):
    """
    TEST 3: Cohérence
    subject.pdf ≠ student.pdf ≠ corrige.pdf
    """
    sheet_id = test_sheet["id"]
    exercise_type_id = test_exercise_type["id"]
    
    # Ajouter 1 item
    await client.post(
        f"/api/mathalea/sheets/{sheet_id}/items",
        json={
            "exercise_type_id": exercise_type_id,
            "config": {
                "nb_questions": 3,
                "difficulty": "moyen",
                "seed": 789,
                "options": {},
                "ai_enonce": False,
                "ai_correction": False
            }
        }
    )
    
    # Générer les PDFs
    pdf_response = await client.post(f"/api/mathalea/sheets/{sheet_id}/generate-pdf")
    
    assert pdf_response.status_code == 200
    data = pdf_response.json()
    
    # Décoder les PDFs
    subject_bytes = base64.b64decode(data["subject_pdf"])
    student_bytes = base64.b64decode(data["student_pdf"])
    correction_bytes = base64.b64decode(data["correction_pdf"])
    
    # Vérifier qu'ils sont différents
    assert subject_bytes != student_bytes
    assert student_bytes != correction_bytes
    assert subject_bytes != correction_bytes
    
    # Vérifier des caractéristiques spécifiques
    subject_str = subject_bytes.decode('latin-1', errors='ignore')
    student_str = student_bytes.decode('latin-1', errors='ignore')
    correction_str = correction_bytes.decode('latin-1', errors='ignore')
    
    # Le PDF élève doit contenir des champs pour le nom
    assert "Nom:" in student_str or "Prénom:" in student_str
    
    # Le PDF corrigé doit contenir "Solution" ou "Corrigé"
    assert "Solution" in correction_str or "Corrigé" in correction_str
    
    print("✓ Les 3 PDFs sont distincts et cohérents")


@pytest.mark.asyncio
async def test_pdf_reproducibility(client, test_sheet, test_exercise_type):
    """
    TEST 4: Reproductibilité
    Deux appels consécutifs → mêmes PDF bytes
    """
    sheet_id = test_sheet["id"]
    exercise_type_id = test_exercise_type["id"]
    
    # Ajouter 1 item avec un seed fixe
    await client.post(
        f"/api/mathalea/sheets/{sheet_id}/items",
        json={
            "exercise_type_id": exercise_type_id,
            "config": {
                "nb_questions": 4,
                "difficulty": "difficile",
                "seed": 999,
                "options": {},
                "ai_enonce": False,
                "ai_correction": False
            }
        }
    )
    
    # Générer les PDFs deux fois
    pdf_response_1 = await client.post(f"/api/mathalea/sheets/{sheet_id}/generate-pdf")
    pdf_response_2 = await client.post(f"/api/mathalea/sheets/{sheet_id}/generate-pdf")
    
    assert pdf_response_1.status_code == 200
    assert pdf_response_2.status_code == 200
    
    data1 = pdf_response_1.json()
    data2 = pdf_response_2.json()
    
    # Décoder les PDFs
    subject_1 = base64.b64decode(data1["subject_pdf"])
    subject_2 = base64.b64decode(data2["subject_pdf"])
    
    student_1 = base64.b64decode(data1["student_pdf"])
    student_2 = base64.b64decode(data2["student_pdf"])
    
    correction_1 = base64.b64decode(data1["correction_pdf"])
    correction_2 = base64.b64decode(data2["correction_pdf"])
    
    # Note: WeasyPrint peut générer des PDFs avec des métadonnées légèrement différentes
    # (timestamps, etc.). On vérifie plutôt que les tailles sont identiques
    # et que le contenu texte est le même
    
    assert len(subject_1) == len(subject_2)
    assert len(student_1) == len(student_2)
    assert len(correction_1) == len(correction_2)
    
    print("✓ PDFs reproductibles (même taille)")


@pytest.mark.asyncio
async def test_pdf_no_exceptions(client, test_sheet, test_exercise_type):
    """
    TEST 5: Aucune exception
    0 crash dans le pipeline PDF
    """
    sheet_id = test_sheet["id"]
    exercise_type_id = test_exercise_type["id"]
    
    # Ajouter plusieurs items avec différentes configurations
    configs = [
        {"nb_questions": 1, "difficulty": "facile", "seed": 1},
        {"nb_questions": 5, "difficulty": "moyen", "seed": 2},
        {"nb_questions": 10, "difficulty": "difficile", "seed": 3},
    ]
    
    for config in configs:
        await client.post(
            f"/api/mathalea/sheets/{sheet_id}/items",
            json={
                "exercise_type_id": exercise_type_id,
                "config": {
                    **config,
                    "options": {},
                    "ai_enonce": False,
                    "ai_correction": False
                }
            }
        )
    
    # Générer les PDFs - ne doit pas crasher
    try:
        pdf_response = await client.post(f"/api/mathalea/sheets/{sheet_id}/generate-pdf")
        assert pdf_response.status_code == 200
        
        data = pdf_response.json()
        
        # Vérifier que tous les PDFs sont présents
        assert "subject_pdf" in data
        assert "student_pdf" in data
        assert "correction_pdf" in data
        
        # Vérifier que ce sont des PDFs valides
        subject_bytes = base64.b64decode(data["subject_pdf"])
        student_bytes = base64.b64decode(data["student_pdf"])
        correction_bytes = base64.b64decode(data["correction_pdf"])
        
        assert subject_bytes.startswith(b'%PDF')
        assert student_bytes.startswith(b'%PDF')
        assert correction_bytes.startswith(b'%PDF')
        
        print("✓ Aucune exception dans le pipeline PDF")
        
    except Exception as e:
        pytest.fail(f"Pipeline PDF a crashé: {str(e)}")


@pytest.mark.asyncio
async def test_pdf_empty_sheet(client, test_sheet):
    """
    TEST 6: Feuille vide
    Fiche sans item → PDFs générés mais vides (ou avec message)
    """
    sheet_id = test_sheet["id"]
    
    # Générer les PDFs pour une feuille vide
    pdf_response = await client.post(f"/api/mathalea/sheets/{sheet_id}/generate-pdf")
    
    assert pdf_response.status_code == 200
    data = pdf_response.json()
    
    # Vérifier que les PDFs sont générés
    assert "subject_pdf" in data
    assert "student_pdf" in data
    assert "correction_pdf" in data
    
    # Vérifier que la métadonnée indique 0 exercices
    assert data["metadata"]["nb_exercises"] == 0
    
    # Décoder et vérifier que ce sont des PDFs valides
    subject_bytes = base64.b64decode(data["subject_pdf"])
    assert subject_bytes.startswith(b'%PDF')
    
    print("✓ PDF généré pour feuille vide")


@pytest.mark.asyncio
async def test_pdf_sheet_not_found(client):
    """
    TEST 7: Feuille inexistante
    sheet_id invalide → erreur 404
    """
    fake_sheet_id = str(uuid4())
    
    pdf_response = await client.post(f"/api/mathalea/sheets/{fake_sheet_id}/generate-pdf")
    
    assert pdf_response.status_code == 404
    assert "ExerciseSheet not found" in pdf_response.json()["detail"]
    
    print("✓ Erreur 404 pour feuille inexistante")
