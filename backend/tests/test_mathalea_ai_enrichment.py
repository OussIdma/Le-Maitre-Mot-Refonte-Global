"""
Tests pour le système d'enrichissement IA des Fiches (Sprint E)

Couvre:
- Enrichissement désactivé (ai_enonce=false, ai_correction=false)
- Enrichissement énoncé uniquement
- Enrichissement correction uniquement
- Enrichissement complet
- Robustesse (erreur IA)
- Intégration avec generate-pdf
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timezone
from uuid import uuid4
import sys
from pathlib import Path
import base64
from unittest.mock import patch, AsyncMock

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
            "code": f"TEST_AI_C_{uuid4().hex[:8]}",
            "intitule": "Compétence de test IA",
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
            "code_ref": f"TEST_AI_EX_{uuid4().hex[:8]}",
            "titre": "Exercice de test IA",
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
            "titre": f"Feuille test IA {uuid4().hex[:8]}",
            "niveau": "6e",
            "owner_id": "test_user_ai"
        }
    )
    assert response.status_code == 201
    return response.json()


# ============================================================================
# TESTS FONCTIONNELS
# ============================================================================

@pytest.mark.asyncio
async def test_enrichment_disabled():
    """
    TEST 1: Enrichissement désactivé
    ai_enonce=false, ai_correction=false
    → preview identique (aucun texte modifié)
    """
    from engine.pdf_engine.sheet_ai_enrichment_helper import apply_ai_enrichment_to_sheet_preview
    
    # Preview factice
    preview = {
        "sheet_id": "test123",
        "titre": "Test",
        "niveau": "6e",
        "items": [
            {
                "item_id": "item1",
                "config": {
                    "ai_enonce": False,
                    "ai_correction": False
                },
                "generated": {
                    "questions": [
                        {
                            "id": "q1",
                            "enonce_brut": "Calculer 2 + 3",
                            "data": {"a": 2, "b": 3},
                            "solution_brut": "Résultat: 5"
                        }
                    ]
                }
            }
        ]
    }
    
    # Appliquer l'enrichissement
    enriched = await apply_ai_enrichment_to_sheet_preview(preview)
    
    # Vérifier que rien n'a changé
    assert enriched["items"][0]["generated"]["questions"][0]["enonce_brut"] == "Calculer 2 + 3"
    assert enriched["items"][0]["generated"]["questions"][0]["solution_brut"] == "Résultat: 5"
    assert enriched["items"][0]["generated"]["questions"][0]["data"] == {"a": 2, "b": 3}
    
    print("✓ Test 1: Enrichissement désactivé → preview identique")


@pytest.mark.asyncio
async def test_enrichment_statement_only():
    """
    TEST 2: Enrichissement énoncé uniquement
    ai_enonce=true, ai_correction=false
    → enonce_brut modifié, solution_brut et data intacts
    """
    from engine.pdf_engine.sheet_ai_enrichment_helper import apply_ai_enrichment_to_sheet_preview
    from ia_engine.exercise_ai_enrichment import enrich_statement
    
    # Mock de enrich_statement pour contrôler la sortie
    async def mock_enrich_statement(enonce_brut, data, niveau, style=None):
        return f"[ENRICHI] {enonce_brut}"
    
    with patch('ia_engine.exercise_ai_enrichment.enrich_statement', side_effect=mock_enrich_statement):
        preview = {
            "sheet_id": "test123",
            "titre": "Test",
            "niveau": "6e",
            "items": [
                {
                    "item_id": "item1",
                    "config": {
                        "ai_enonce": True,
                        "ai_correction": False
                    },
                    "generated": {
                        "questions": [
                            {
                                "id": "q1",
                                "enonce_brut": "Calculer 2 + 3",
                                "data": {"a": 2, "b": 3},
                                "solution_brut": "Résultat: 5"
                            }
                        ]
                    }
                }
            ]
        }
        
        enriched = await apply_ai_enrichment_to_sheet_preview(preview)
        
        # Vérifier que l'énoncé est modifié
        assert enriched["items"][0]["generated"]["questions"][0]["enonce_brut"] == "[ENRICHI] Calculer 2 + 3"
        
        # Vérifier que solution et data sont intacts
        assert enriched["items"][0]["generated"]["questions"][0]["solution_brut"] == "Résultat: 5"
        assert enriched["items"][0]["generated"]["questions"][0]["data"] == {"a": 2, "b": 3}
        
        print("✓ Test 2: Énoncé enrichi, solution et data intacts")


@pytest.mark.asyncio
async def test_enrichment_correction_only():
    """
    TEST 3: Enrichissement correction uniquement
    ai_enonce=false, ai_correction=true
    → solution_brut modifié, enonce_brut et data intacts
    """
    from engine.pdf_engine.sheet_ai_enrichment_helper import apply_ai_enrichment_to_sheet_preview
    
    async def mock_enrich_correction(solution_brut, data, niveau):
        return f"[ENRICHI] {solution_brut}"
    
    with patch('ia_engine.exercise_ai_enrichment.enrich_correction', side_effect=mock_enrich_correction):
        preview = {
            "sheet_id": "test123",
            "titre": "Test",
            "niveau": "6e",
            "items": [
                {
                    "item_id": "item1",
                    "config": {
                        "ai_enonce": False,
                        "ai_correction": True
                    },
                    "generated": {
                        "questions": [
                            {
                                "id": "q1",
                                "enonce_brut": "Calculer 2 + 3",
                                "data": {"a": 2, "b": 3},
                                "solution_brut": "Résultat: 5"
                            }
                        ]
                    }
                }
            ]
        }
        
        enriched = await apply_ai_enrichment_to_sheet_preview(preview)
        
        # Vérifier que la solution est modifiée
        assert enriched["items"][0]["generated"]["questions"][0]["solution_brut"] == "[ENRICHI] Résultat: 5"
        
        # Vérifier que énoncé et data sont intacts
        assert enriched["items"][0]["generated"]["questions"][0]["enonce_brut"] == "Calculer 2 + 3"
        assert enriched["items"][0]["generated"]["questions"][0]["data"] == {"a": 2, "b": 3}
        
        print("✓ Test 3: Correction enrichie, énoncé et data intacts")


@pytest.mark.asyncio
async def test_enrichment_both():
    """
    TEST 4: Enrichissement complet
    ai_enonce=true, ai_correction=true
    → les deux modifiés, data intact
    """
    from engine.pdf_engine.sheet_ai_enrichment_helper import apply_ai_enrichment_to_sheet_preview
    
    async def mock_enrich_statement(enonce_brut, data, niveau, style=None):
        return f"[ENONCE ENRICHI] {enonce_brut}"
    
    async def mock_enrich_correction(solution_brut, data, niveau):
        return f"[SOLUTION ENRICHIE] {solution_brut}"
    
    with patch('ia_engine.exercise_ai_enrichment.enrich_statement', side_effect=mock_enrich_statement), \
         patch('ia_engine.exercise_ai_enrichment.enrich_correction', side_effect=mock_enrich_correction):
        
        preview = {
            "sheet_id": "test123",
            "titre": "Test",
            "niveau": "6e",
            "items": [
                {
                    "item_id": "item1",
                    "config": {
                        "ai_enonce": True,
                        "ai_correction": True
                    },
                    "generated": {
                        "questions": [
                            {
                                "id": "q1",
                                "enonce_brut": "Calculer 2 + 3",
                                "data": {"a": 2, "b": 3},
                                "solution_brut": "Résultat: 5"
                            }
                        ]
                    }
                }
            ]
        }
        
        enriched = await apply_ai_enrichment_to_sheet_preview(preview)
        
        # Vérifier que les deux sont modifiés
        assert enriched["items"][0]["generated"]["questions"][0]["enonce_brut"] == "[ENONCE ENRICHI] Calculer 2 + 3"
        assert enriched["items"][0]["generated"]["questions"][0]["solution_brut"] == "[SOLUTION ENRICHIE] Résultat: 5"
        
        # Vérifier que data est intact
        assert enriched["items"][0]["generated"]["questions"][0]["data"] == {"a": 2, "b": 3}
        
        print("✓ Test 4: Énoncé et correction enrichis, data intact")


@pytest.mark.asyncio
async def test_robustness_error_handling():
    """
    TEST 5: Robustesse
    Simuler une erreur IA → vérifier que le système:
    - ne crash pas
    - conserve les textes bruts
    - journalise l'erreur
    """
    from engine.pdf_engine.sheet_ai_enrichment_helper import apply_ai_enrichment_to_sheet_preview
    
    async def mock_enrich_statement_error(*args, **kwargs):
        raise Exception("IA indisponible")
    
    with patch('ia_engine.exercise_ai_enrichment.enrich_statement', side_effect=mock_enrich_statement_error):
        preview = {
            "sheet_id": "test123",
            "titre": "Test",
            "niveau": "6e",
            "items": [
                {
                    "item_id": "item1",
                    "config": {
                        "ai_enonce": True,
                        "ai_correction": False
                    },
                    "generated": {
                        "questions": [
                            {
                                "id": "q1",
                                "enonce_brut": "Calculer 2 + 3",
                                "data": {"a": 2, "b": 3},
                                "solution_brut": "Résultat: 5"
                            }
                        ]
                    }
                }
            ]
        }
        
        # Ne doit pas crasher
        try:
            enriched = await apply_ai_enrichment_to_sheet_preview(preview)
            
            # Vérifier que les textes bruts sont conservés
            assert enriched["items"][0]["generated"]["questions"][0]["enonce_brut"] == "Calculer 2 + 3"
            assert enriched["items"][0]["generated"]["questions"][0]["solution_brut"] == "Résultat: 5"
            
            print("✓ Test 5: Robustesse - erreur IA gérée, textes bruts conservés")
        except Exception as e:
            pytest.fail(f"Le système ne doit pas crasher en cas d'erreur IA: {str(e)}")


@pytest.mark.asyncio
async def test_check_if_ai_needed():
    """
    TEST 6: Vérification de la nécessité de l'IA
    """
    from engine.pdf_engine.sheet_ai_enrichment_helper import check_if_ai_needed
    
    # Preview sans IA
    preview_no_ai = {
        "items": [
            {
                "config": {
                    "ai_enonce": False,
                    "ai_correction": False
                }
            }
        ]
    }
    
    # Preview avec IA
    preview_with_ai = {
        "items": [
            {
                "config": {
                    "ai_enonce": True,
                    "ai_correction": False
                }
            }
        ]
    }
    
    assert check_if_ai_needed(preview_no_ai) == False
    assert check_if_ai_needed(preview_with_ai) == True
    
    print("✓ Test 6: Vérification nécessité IA OK")


# ============================================================================
# TESTS D'INTÉGRATION
# ============================================================================

@pytest.mark.asyncio
async def test_integration_pdf_without_ai(client, test_sheet, test_exercise_type):
    """
    TEST 7: Intégration PDF sans IA
    Appeler /generate-pdf avec une fiche sans IA
    → PDF généré sans erreur, comportement identique à Sprint D
    """
    sheet_id = test_sheet["id"]
    exercise_type_id = test_exercise_type["id"]
    
    # Ajouter un item SANS IA
    await client.post(
        f"/api/mathalea/sheets/{sheet_id}/items",
        json={
            "exercise_type_id": exercise_type_id,
            "config": {
                "nb_questions": 2,
                "difficulty": "moyen",
                "seed": 100,
                "options": {},
                "ai_enonce": False,  # IA désactivée
                "ai_correction": False
            }
        }
    )
    
    # Générer les PDFs
    pdf_response = await client.post(f"/api/mathalea/sheets/{sheet_id}/generate-pdf")
    
    assert pdf_response.status_code == 200
    data = pdf_response.json()
    
    # Vérifier que les PDFs sont générés
    assert "subject_pdf" in data
    assert "student_pdf" in data
    assert "correction_pdf" in data
    
    # Vérifier que l'IA n'a pas été appliquée
    assert data["metadata"]["ai_enrichment_applied"] == False
    
    # Vérifier que ce sont des PDFs valides
    subject_bytes = base64.b64decode(data["subject_pdf"])
    assert subject_bytes.startswith(b'%PDF')
    
    print("✓ Test 7: Intégration PDF sans IA OK")


@pytest.mark.asyncio
async def test_integration_pdf_with_ai_mock(client, test_sheet, test_exercise_type):
    """
    TEST 8: Intégration PDF avec IA (mocké)
    Appeler /generate-pdf avec une fiche avec IA activée
    → PDF généré sans erreur
    """
    sheet_id = test_sheet["id"]
    exercise_type_id = test_exercise_type["id"]
    
    # Mock des fonctions IA pour éviter les vrais appels
    async def mock_enrich(*args, **kwargs):
        return args[0]  # Retourner tel quel
    
    with patch('ia_engine.exercise_ai_enrichment.enrich_statement', side_effect=mock_enrich), \
         patch('ia_engine.exercise_ai_enrichment.enrich_correction', side_effect=mock_enrich):
        
        # Ajouter un item AVEC IA
        await client.post(
            f"/api/mathalea/sheets/{sheet_id}/items",
            json={
                "exercise_type_id": exercise_type_id,
                "config": {
                    "nb_questions": 2,
                    "difficulty": "moyen",
                    "seed": 200,
                    "options": {},
                    "ai_enonce": True,  # IA activée
                    "ai_correction": True
                }
            }
        )
        
        # Générer les PDFs
        pdf_response = await client.post(f"/api/mathalea/sheets/{sheet_id}/generate-pdf")
        
        assert pdf_response.status_code == 200
        data = pdf_response.json()
        
        # Vérifier que les PDFs sont générés
        assert "subject_pdf" in data
        assert "student_pdf" in data
        assert "correction_pdf" in data
        
        # Vérifier que l'IA a été détectée
        assert data["metadata"]["ai_enrichment_applied"] == True
        
        # Vérifier que ce sont des PDFs valides
        subject_bytes = base64.b64decode(data["subject_pdf"])
        assert subject_bytes.startswith(b'%PDF')
        
        print("✓ Test 8: Intégration PDF avec IA (mocké) OK")
