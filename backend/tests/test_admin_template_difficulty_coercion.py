"""
Tests P4.D - Coercition de difficulté dans la validation admin des templates

Vérifie que:
1. La validation admin applique normalize_difficulty() puis coerce_to_supported_difficulty()
2. Les erreurs INVALID_DIFFICULTY sont distinguées de ADMIN_TEMPLATE_MISMATCH
3. La réponse inclut difficulty_requested et difficulty_used
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from backend.services.generator_template_service import GeneratorTemplateService
from backend.models.generator_template import GeneratorTemplateValidateRequest


@pytest.fixture
def mock_db():
    """Mock MongoDB database"""
    db = MagicMock()
    db.generator_templates = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    """Service de templates avec DB mockée"""
    return GeneratorTemplateService(mock_db)


@pytest.mark.asyncio
async def test_validate_template_coerces_difficulty_moyen_to_standard(service):
    """
    Test P4.D: Validation avec difficulté "moyen" pour CALCUL_NOMBRES_V1
    qui n'accepte que "facile" et "standard" -> doit coercte "moyen" vers "standard"
    """
    # Mock GeneratorFactory pour simuler CALCUL_NOMBRES_V1
    with patch('backend.services.generator_template_service.GeneratorFactory') as mock_factory:
        # Mock get() pour retourner une classe de générateur
        mock_gen_class = MagicMock()
        mock_gen_meta = MagicMock()
        mock_gen_meta.supported_difficulties = None  # Pas défini dans meta
        mock_gen_class.get_meta.return_value = mock_gen_meta
        
        # Mock get_schema() pour retourner un schéma avec difficulty options
        mock_schema = [
            MagicMock(name="difficulty", options=["facile", "standard"])
        ]
        mock_gen_class.get_schema.return_value = mock_schema
        mock_factory.get.return_value = mock_gen_class
        
        # Mock generate() pour retourner des variables valides
        mock_factory.generate.return_value = {
            "variables": {
                "enonce": "Calculer : 15 + 23",
                "solution": "15 + 23 = 38",
                "reponse_finale": "38",
                "consigne": "Effectue le calcul."
            }
        }
        
        request = GeneratorTemplateValidateRequest(
            generator_key="CALCUL_NOMBRES_V1",
            difficulty="moyen",  # Difficulté non supportée
            grade="6e",
            seed=42,
            enonce_template_html="<p>{{enonce}}</p>",
            solution_template_html="<p>{{solution}}</p>"
        )
        
        result = await service.validate_template(request)
        
        # Vérifier que la validation a réussi
        assert result.valid is True
        assert result.difficulty_requested == "moyen"
        assert result.difficulty_used == "standard"  # Coercte vers standard
        
        # Vérifier que generate() a été appelé avec la difficulté coercée
        mock_factory.generate.assert_called_once()
        call_kwargs = mock_factory.generate.call_args
        assert call_kwargs[1]["overrides"]["difficulty"] == "standard"


@pytest.mark.asyncio
async def test_validate_template_coerces_difficile_to_standard(service):
    """
    Test P4.D: Validation avec difficulté "difficile" pour CALCUL_NOMBRES_V1
    -> doit coercte "difficile" vers "standard" (fallback chain)
    """
    with patch('backend.services.generator_template_service.GeneratorFactory') as mock_factory:
        mock_gen_class = MagicMock()
        mock_gen_meta = MagicMock()
        mock_gen_meta.supported_difficulties = None
        mock_gen_class.get_meta.return_value = mock_gen_meta
        
        mock_schema = [
            MagicMock(name="difficulty", options=["facile", "standard"])
        ]
        mock_gen_class.get_schema.return_value = mock_schema
        mock_factory.get.return_value = mock_gen_class
        
        mock_factory.generate.return_value = {
            "variables": {
                "enonce": "Calculer : 15 + 23",
                "solution": "15 + 23 = 38"
            }
        }
        
        request = GeneratorTemplateValidateRequest(
            generator_key="CALCUL_NOMBRES_V1",
            difficulty="difficile",  # Difficulté non supportée
            grade="6e",
            seed=42,
            enonce_template_html="<p>{{enonce}}</p>",
            solution_template_html="<p>{{solution}}</p>"
        )
        
        result = await service.validate_template(request)
        
        assert result.valid is True
        assert result.difficulty_requested == "difficile"
        assert result.difficulty_used == "standard"  # Coercte vers standard


@pytest.mark.asyncio
async def test_validate_template_invalid_difficulty_error(service):
    """
    Test P4.D: Si le générateur échoue avec une erreur de difficulté,
    doit retourner GENERATOR_INVALID_DIFFICULTY et non ADMIN_TEMPLATE_MISMATCH
    """
    with patch('backend.services.generator_template_service.GeneratorFactory') as mock_factory:
        mock_gen_class = MagicMock()
        mock_gen_meta = MagicMock()
        mock_gen_meta.supported_difficulties = None
        mock_gen_class.get_meta.return_value = mock_gen_meta
        
        mock_schema = [
            MagicMock(name="difficulty", options=["facile", "standard"])
        ]
        mock_gen_class.get_schema.return_value = mock_schema
        mock_factory.get.return_value = mock_gen_class
        
        # Mock generate() pour lever une ValueError avec message de difficulté
        mock_factory.generate.side_effect = ValueError(
            "Le générateur ne peut pas générer avec la difficulté 'moyen'"
        )
        
        request = GeneratorTemplateValidateRequest(
            generator_key="CALCUL_NOMBRES_V1",
            difficulty="moyen",
            grade="6e",
            seed=42,
            enonce_template_html="<p>{{enonce}}</p>",
            solution_template_html="<p>{{solution}}</p>"
        )
        
        result = await service.validate_template(request)
        
        # Vérifier que la validation a échoué avec le bon message
        assert result.valid is False
        assert "difficulté" in result.error_message.lower()
        assert result.difficulty_requested == "moyen"
        assert result.difficulty_used == "standard"  # Coercte mais génération échoue quand même


@pytest.mark.asyncio
async def test_validate_template_real_mismatch(service):
    """
    Test P4.D: Si le générateur réussit mais que des placeholders sont manquants,
    doit retourner ADMIN_TEMPLATE_MISMATCH (vrai cas)
    """
    with patch('backend.services.generator_template_service.GeneratorFactory') as mock_factory:
        mock_gen_class = MagicMock()
        mock_gen_meta = MagicMock()
        mock_gen_meta.supported_difficulties = None
        mock_gen_class.get_meta.return_value = mock_gen_meta
        
        mock_schema = [
            MagicMock(name="difficulty", options=["facile", "standard"])
        ]
        mock_gen_class.get_schema.return_value = mock_schema
        mock_factory.get.return_value = mock_gen_class
        
        # Génération réussit mais variable manquante
        mock_factory.generate.return_value = {
            "variables": {
                "enonce": "Calculer : 15 + 23",
                "solution": "15 + 23 = 38"
                # "reponse_finale" manquant intentionnellement
            }
        }
        
        request = GeneratorTemplateValidateRequest(
            generator_key="CALCUL_NOMBRES_V1",
            difficulty="facile",
            grade="6e",
            seed=42,
            enonce_template_html="<p>{{enonce}}</p>",
            solution_template_html="<p>{{reponse_finale}}</p>"  # Placeholder manquant
        )
        
        result = await service.validate_template(request)
        
        # Vérifier que c'est un vrai template mismatch
        assert result.valid is False
        assert "reponse_finale" in result.missing_placeholders
        assert result.difficulty_requested == "facile"
        assert result.difficulty_used == "facile"


@pytest.mark.asyncio
async def test_validate_template_normalizes_difficulty(service):
    """
    Test P4.D: Normalisation de "standard" vers "moyen" avant coercition
    """
    with patch('backend.services.generator_template_service.GeneratorFactory') as mock_factory:
        mock_gen_class = MagicMock()
        mock_gen_meta = MagicMock()
        mock_gen_meta.supported_difficulties = None
        mock_gen_class.get_meta.return_value = mock_gen_meta
        
        mock_schema = [
            MagicMock(name="difficulty", options=["facile", "standard"])
        ]
        mock_gen_class.get_schema.return_value = mock_schema
        mock_factory.get.return_value = mock_gen_class
        
        mock_factory.generate.return_value = {
            "variables": {
                "enonce": "Calculer : 15 + 23",
                "solution": "15 + 23 = 38"
            }
        }
        
        request = GeneratorTemplateValidateRequest(
            generator_key="CALCUL_NOMBRES_V1",
            difficulty="standard",  # Doit être normalisé vers "moyen" puis coercte vers "standard"
            grade="6e",
            seed=42,
            enonce_template_html="<p>{{enonce}}</p>",
            solution_template_html="<p>{{solution}}</p>"
        )
        
        result = await service.validate_template(request)
        
        assert result.valid is True
        assert result.difficulty_requested == "moyen"  # Normalisé
        assert result.difficulty_used == "standard"  # Coercte vers standard (supporté)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



