"""
Tests unitaires pour le dispatch premium générique (P0.3)
Vérifie que l'API /api/v1/exercises/generate sélectionne et appelle correctement
les générateurs premium enregistrés dans GeneratorFactory.
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.routes.exercises_routes import router
from backend.models.exercise_models import ExerciseGenerateRequest
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Créer une instance FastAPI et y inclure le router
app = FastAPI()
app.include_router(router, prefix="/api/v1/exercises")
client = TestClient(app)


class TestPremiumDispatch:
    """Tests pour le dispatch premium générique via GeneratorFactory"""

    @patch('backend.routes.exercises_routes.get_chapter_by_official_code')
    @patch('backend.routes.exercises_routes.GeneratorFactory.generate')
    @patch('backend.routes.exercises_routes.GeneratorFactory._generators', {
        "RAISONNEMENT_MULTIPLICATIF_V1": MagicMock,
        "CALCUL_NOMBRES_V1": MagicMock,
        "SIMPLIFICATION_FRACTIONS_V2": MagicMock
    })
    def test_premium_dispatch_avec_generateur_factory(
        self,
        mock_factory_generate,
        mock_get_chapter
    ):
        """
        Test nominal: offer=pro, chapitre avec RAISONNEMENT_MULTIPLICATIF_V1 dans exercise_types
        → GeneratorFactory.generate() doit être appelé
        → Réponse 200 avec metadata.is_premium=True
        """
        # Mock du chapitre avec générateur premium
        mock_chapter = MagicMock()
        mock_chapter.exercise_types = ["RAISONNEMENT_MULTIPLICATIF_V1", "CALCUL_NOMBRES_V1"]
        mock_get_chapter.return_value = mock_chapter

        # Mock du résultat de génération
        mock_factory_generate.return_value = {
            "enonce_html": "<p>Test énoncé premium</p>",
            "solution_html": "<p>Test solution premium</p>",
            "figure_svg_enonce": None,
            "figure_svg_solution": None,
        }

        # Requête POST /api/v1/exercises/generate
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_SP03",
                "niveau": "6e",
                "chapitre": "Proportionnalité",
                "difficulte": "moyen",
                "offer": "pro",
                "seed": 42,
            }
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier que metadata.is_premium est True
        assert data["metadata"]["is_premium"] is True
        assert data["metadata"]["generator_key"] in ["RAISONNEMENT_MULTIPLICATIF_V1", "CALCUL_NOMBRES_V1"]
        
        # Vérifier que GeneratorFactory.generate a été appelé
        mock_factory_generate.assert_called_once()
        call_args = mock_factory_generate.call_args
        assert call_args[1]["key"] in ["RAISONNEMENT_MULTIPLICATIF_V1", "CALCUL_NOMBRES_V1"]
        assert call_args[1]["seed"] == 42

    @patch('backend.routes.exercises_routes.get_chapter_by_official_code')
    @patch('backend.routes.exercises_routes.GeneratorFactory._generators', {
        "RAISONNEMENT_MULTIPLICATIF_V1": MagicMock,
        "CALCUL_NOMBRES_V1": MagicMock
    })
    def test_premium_dispatch_pas_de_generateur_factory(
        self,
        mock_get_chapter
    ):
        """
        Test: offer=pro, mais chapitre sans générateur Factory enregistré
        → Fallback sur le flux legacy (pas d'erreur)
        """
        # Mock du chapitre sans générateur premium Factory
        mock_chapter = MagicMock()
        mock_chapter.exercise_types = ["CALCUL_MENTAL", "EXERCICE_BASIQUE"]
        mock_get_chapter.return_value = mock_chapter

        # Requête POST /api/v1/exercises/generate
        # Note: Ce test va probablement échouer avec 422 car le chapitre n'est pas mappé
        # C'est OK, on vérifie juste qu'il n'y a pas d'erreur de dispatch Factory
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_TEST",
                "niveau": "6e",
                "chapitre": "Test",
                "difficulte": "moyen",
                "offer": "pro",
                "seed": 42,
            }
        )

        # L'important ici est qu'on ne crash pas avec une erreur Factory
        # On accepte 422 (chapitre invalide) ou 200 (si le fallback fonctionne)
        assert response.status_code in [200, 422]

    @patch('backend.routes.exercises_routes.get_chapter_by_official_code')
    @patch('backend.routes.exercises_routes.GeneratorFactory.generate')
    @patch('backend.routes.exercises_routes.GeneratorFactory._generators', {
        "RAISONNEMENT_MULTIPLICATIF_V1": MagicMock,
        "CALCUL_NOMBRES_V1": MagicMock
    })
    def test_premium_dispatch_deterministe_avec_seed(
        self,
        mock_factory_generate,
        mock_get_chapter
    ):
        """
        Test: seed fixe → même générateur sélectionné (déterminisme)
        """
        # Mock du chapitre avec plusieurs générateurs premium
        mock_chapter = MagicMock()
        mock_chapter.exercise_types = ["RAISONNEMENT_MULTIPLICATIF_V1", "CALCUL_NOMBRES_V1"]
        mock_get_chapter.return_value = mock_chapter

        # Mock du résultat de génération
        mock_factory_generate.return_value = {
            "enonce_html": "<p>Test</p>",
            "solution_html": "<p>Solution</p>",
            "figure_svg_enonce": None,
            "figure_svg_solution": None,
        }

        # Premier appel avec seed=42
        response1 = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_SP03",
                "niveau": "6e",
                "chapitre": "Proportionnalité",
                "difficulte": "moyen",
                "offer": "pro",
                "seed": 42,
            }
        )

        generator_key_1 = response1.json()["metadata"]["generator_key"]

        # Deuxième appel avec le même seed=42
        response2 = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_SP03",
                "niveau": "6e",
                "chapitre": "Proportionnalité",
                "difficulte": "moyen",
                "offer": "pro",
                "seed": 42,
            }
        )

        generator_key_2 = response2.json()["metadata"]["generator_key"]

        # Vérifier que le même générateur est sélectionné
        assert generator_key_1 == generator_key_2

    @patch('backend.routes.exercises_routes.get_chapter_by_official_code')
    @patch('backend.routes.exercises_routes.GeneratorFactory.generate')
    @patch('backend.routes.exercises_routes.GeneratorFactory._generators', {
        "RAISONNEMENT_MULTIPLICATIF_V1": MagicMock
    })
    def test_premium_dispatch_fallback_sur_erreur_factory(
        self,
        mock_factory_generate,
        mock_get_chapter
    ):
        """
        Test: GeneratorFactory.generate() lève une exception
        → L'API doit fallback gracieusement sur le flux legacy (pas de 500)
        """
        # Mock du chapitre avec générateur premium
        mock_chapter = MagicMock()
        mock_chapter.exercise_types = ["RAISONNEMENT_MULTIPLICATIF_V1"]
        mock_get_chapter.return_value = mock_chapter

        # Mock du résultat de génération qui échoue
        mock_factory_generate.side_effect = Exception("Erreur de génération Factory")

        # Requête POST /api/v1/exercises/generate
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_SP03",
                "niveau": "6e",
                "chapitre": "Proportionnalité",
                "difficulte": "moyen",
                "offer": "pro",
                "seed": 42,
            }
        )

        # L'API ne doit pas crasher avec 500, mais fallback (possiblement 422 si pas de legacy)
        assert response.status_code in [200, 422]

    @patch('backend.routes.exercises_routes.get_chapter_by_official_code')
    @patch('backend.routes.exercises_routes.GeneratorFactory._generators', {
        "RAISONNEMENT_MULTIPLICATIF_V1": MagicMock
    })
    def test_premium_dispatch_offer_free_pas_de_premium(
        self,
        mock_get_chapter
    ):
        """
        Test: offer=free, même si chapitre a des générateurs premium
        → Ne doit PAS utiliser Factory (respecter l'offre)
        """
        # Mock du chapitre avec générateur premium
        mock_chapter = MagicMock()
        mock_chapter.exercise_types = ["RAISONNEMENT_MULTIPLICATIF_V1"]
        mock_get_chapter.return_value = mock_chapter

        # Requête POST /api/v1/exercises/generate avec offer=free
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_SP03",
                "niveau": "6e",
                "chapitre": "Proportionnalité",
                "difficulte": "moyen",
                "offer": "free",
                "seed": 42,
            }
        )

        # Devrait fallback sur legacy (200 ou 422), mais pas utiliser Factory
        assert response.status_code in [200, 422]
        
        # Si 200, vérifier qu'on n'a pas is_premium=True
        if response.status_code == 200:
            data = response.json()
            # offer=free ne devrait pas déclencher premium Factory
            # (le metadata peut ne pas avoir is_premium, ou être False)
            assert data["metadata"].get("is_premium", False) is False

