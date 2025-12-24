"""
Tests pour le service de gestion des templates de générateurs
"""
import pytest
from datetime import datetime
from backend.models.generator_template import (
    GeneratorTemplateCreate,
    GeneratorTemplateUpdate,
    GeneratorTemplateValidateRequest
)


@pytest.mark.asyncio
async def test_create_template(template_service):
    """Test création d'un template"""
    template_data = GeneratorTemplateCreate(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1",
        variant_id="A",
        grade="6e",
        difficulty="facile",
        enonce_template_html="<p>{{consigne}}</p>",
        solution_template_html="<p>{{solution}}</p>",
        allowed_html_vars=[]
    )
    
    template = await template_service.create_template(template_data)
    
    assert template.id is not None
    assert template.generator_key == "RAISONNEMENT_MULTIPLICATIF_V1"
    assert template.variant_id == "A"
    assert template.grade == "6e"
    assert template.difficulty == "facile"
    assert template.created_at is not None


@pytest.mark.asyncio
async def test_list_templates_filtered(template_service):
    """Test listage des templates avec filtres"""
    # Créer plusieurs templates
    await template_service.create_template(GeneratorTemplateCreate(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1",
        variant_id="A",
        grade="6e",
        enonce_template_html="<p>{{consigne}}</p>",
        solution_template_html="<p>{{solution}}</p>"
    ))
    
    await template_service.create_template(GeneratorTemplateCreate(
        generator_key="CALCUL_NOMBRES_V1",
        variant_id="B",
        grade="5e",
        enonce_template_html="<p>{{enonce}}</p>",
        solution_template_html="<p>{{solution}}</p>"
    ))
    
    # Filtrer par generator_key
    templates = await template_service.list_templates(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1"
    )
    
    assert len(templates) == 1
    assert templates[0].generator_key == "RAISONNEMENT_MULTIPLICATIF_V1"


@pytest.mark.asyncio
async def test_update_template(template_service):
    """Test mise à jour d'un template"""
    # Créer un template
    template = await template_service.create_template(GeneratorTemplateCreate(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1",
        enonce_template_html="<p>{{consigne}}</p>",
        solution_template_html="<p>{{solution}}</p>"
    ))
    
    # Mettre à jour
    updated = await template_service.update_template(
        template.id,
        GeneratorTemplateUpdate(
            enonce_template_html="<p><strong>{{consigne}}</strong></p>",
            allowed_html_vars=["tableau_html"]
        )
    )
    
    assert updated.id == template.id
    assert updated.enonce_template_html == "<p><strong>{{consigne}}</strong></p>"
    assert "tableau_html" in updated.allowed_html_vars
    assert updated.updated_at > template.updated_at


@pytest.mark.asyncio
async def test_delete_template(template_service):
    """Test suppression d'un template"""
    # Créer un template
    template = await template_service.create_template(GeneratorTemplateCreate(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1",
        enonce_template_html="<p>{{consigne}}</p>",
        solution_template_html="<p>{{solution}}</p>"
    ))
    
    # Supprimer
    success = await template_service.delete_template(template.id)
    assert success is True
    
    # Vérifier que le template n'existe plus
    deleted = await template_service.get_template(template.id)
    assert deleted is None


@pytest.mark.asyncio
async def test_get_best_template_priority(template_service):
    """Test sélection du meilleur template selon la priorité"""
    # Créer plusieurs templates avec différentes spécificités
    # 1. Default
    await template_service.create_template(GeneratorTemplateCreate(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1",
        variant_id="default",
        enonce_template_html="<p>DEFAULT</p>",
        solution_template_html="<p>DEFAULT</p>"
    ))
    
    # 2. Variant A (plus spécifique)
    await template_service.create_template(GeneratorTemplateCreate(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1",
        variant_id="A",
        enonce_template_html="<p>VARIANT A</p>",
        solution_template_html="<p>VARIANT A</p>"
    ))
    
    # 3. Variant A + Grade 6e (encore plus spécifique)
    await template_service.create_template(GeneratorTemplateCreate(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1",
        variant_id="A",
        grade="6e",
        enonce_template_html="<p>VARIANT A + 6e</p>",
        solution_template_html="<p>VARIANT A + 6e</p>"
    ))
    
    # Test priorité 1: Exact match (A + 6e)
    best = await template_service.get_best_template(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1",
        variant_id="A",
        grade="6e"
    )
    assert "6e" in best.enonce_template_html
    
    # Test priorité 2: Variant A (sans grade)
    best = await template_service.get_best_template(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1",
        variant_id="A",
        grade="5e"  # 5e n'existe pas, fallback sur A sans grade
    )
    assert "VARIANT A</p>" in best.enonce_template_html
    assert "6e" not in best.enonce_template_html
    
    # Test priorité 3: Default
    best = await template_service.get_best_template(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1",
        variant_id="B"  # B n'existe pas, fallback sur default
    )
    assert "DEFAULT" in best.enonce_template_html


@pytest.mark.asyncio
async def test_validate_template_success(template_service):
    """Test validation réussie d'un template"""
    request = GeneratorTemplateValidateRequest(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1",
        variant_id="default",
        grade="6e",
        difficulty="facile",
        seed=42,
        enonce_template_html="<p><strong>{{consigne}}</strong></p><p>{{enonce}}</p>{{{tableau_html}}}",
        solution_template_html="<h4>{{methode}}</h4><p>{{reponse_finale}}</p>",
        allowed_html_vars=["tableau_html"]
    )
    
    result = await template_service.validate_template(request)
    
    assert result.valid is True
    assert len(result.missing_placeholders) == 0
    assert len(result.html_security_errors) == 0
    assert result.preview is not None
    assert "enonce_html" in result.preview
    assert "solution_html" in result.preview


@pytest.mark.asyncio
async def test_validate_template_missing_placeholder(template_service):
    """Test validation avec placeholder manquant"""
    request = GeneratorTemplateValidateRequest(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1",
        variant_id="default",
        seed=42,
        enonce_template_html="<p>{{consigne}}</p><p>{{vitesse_lumiere}}</p>",  # vitesse_lumiere n'existe pas
        solution_template_html="<p>{{solution}}</p>",
        allowed_html_vars=[]
    )
    
    result = await template_service.validate_template(request)
    
    assert result.valid is False
    assert "vitesse_lumiere" in result.missing_placeholders
    assert result.error_message is not None
    assert "manquants" in result.error_message.lower()


@pytest.mark.asyncio
async def test_validate_template_html_var_not_allowed(template_service):
    """Test validation avec triple moustaches non autorisées"""
    request = GeneratorTemplateValidateRequest(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1",
        variant_id="default",
        seed=42,
        enonce_template_html="<p>{{{enonce}}}</p>",  # Triple moustaches sans autorisation
        solution_template_html="<p>{{solution}}</p>",
        allowed_html_vars=[]  # enonce pas dans allowed_html_vars
    )
    
    result = await template_service.validate_template(request)
    
    assert result.valid is False
    assert len(result.html_security_errors) > 0
    assert result.html_security_errors[0]["type"] == "html_var_not_allowed"
    assert result.html_security_errors[0]["placeholder"] == "enonce"


@pytest.mark.asyncio
async def test_validate_template_html_var_allowed(template_service):
    """Test validation avec triple moustaches autorisées"""
    request = GeneratorTemplateValidateRequest(
        generator_key="RAISONNEMENT_MULTIPLICATIF_V1",
        variant_id="default",
        seed=42,
        enonce_template_html="<p>{{enonce}}</p>{{{tableau_html}}}",
        solution_template_html="<p>{{solution}}</p>",
        allowed_html_vars=["tableau_html"]  # tableau_html est autorisé
    )
    
    result = await template_service.validate_template(request)
    
    assert result.valid is True
    assert len(result.html_security_errors) == 0


# Fixtures

@pytest.fixture
async def template_service(test_db):
    """Fixture pour créer un service de templates avec DB de test"""
    from backend.services.generator_template_service import GeneratorTemplateService
    
    service = GeneratorTemplateService(test_db)
    
    # Nettoyer la collection avant chaque test
    await test_db.generator_templates.delete_many({})
    
    yield service
    
    # Nettoyer après le test
    await test_db.generator_templates.delete_many({})


@pytest.fixture
async def test_db():
    """Fixture pour créer une DB de test"""
    from motor.motor_asyncio import AsyncIOMotorClient
    
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_lemaitremot"]
    
    yield db
    
    # Nettoyer après tous les tests
    await db.generator_templates.delete_many({})
    client.close()





