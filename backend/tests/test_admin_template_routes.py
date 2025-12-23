"""
Tests pour les routes admin de gestion des templates
"""
import pytest


def test_list_templates_empty(test_client):
    """Test listage des templates (vide au départ)"""
    response = test_client.get("/api/v1/admin/generator-templates")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_create_template(test_client):
    """Test création d'un template"""
    template_data = {
        "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
        "variant_id": "A",
        "grade": "6e",
        "difficulty": "facile",
        "enonce_template_html": "<p><strong>{{consigne}}</strong></p><p>{{enonce}}</p>{{{tableau_html}}}",
        "solution_template_html": "<h4>{{methode}}</h4><p>{{reponse_finale}}</p>",
        "allowed_html_vars": ["tableau_html"]
    }
    
    response = test_client.post("/api/v1/admin/generator-templates", json=template_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["generator_key"] == "RAISONNEMENT_MULTIPLICATIF_V1"
    assert data["variant_id"] == "A"
    assert data["grade"] == "6e"
    assert data["id"] is not None


def test_get_template(test_client):
    """Test récupération d'un template par ID"""
    # Créer un template
    create_response = test_client.post("/api/v1/admin/generator-templates", json={
        "generator_key": "CALCUL_NOMBRES_V1",
        "enonce_template_html": "<p>{{enonce}}</p>",
        "solution_template_html": "<p>{{solution}}</p>"
    })
    template_id = create_response.json()["id"]
    
    # Récupérer le template
    response = test_client.get(f"/api/v1/admin/generator-templates/{template_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == template_id
    assert data["generator_key"] == "CALCUL_NOMBRES_V1"


def test_get_template_not_found(test_client):
    """Test récupération d'un template inexistant"""
    response = test_client.get("/api/v1/admin/generator-templates/507f1f77bcf86cd799439011")
    
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["error_code"] == "TEMPLATE_NOT_FOUND"


def test_update_template(test_client):
    """Test mise à jour d'un template"""
    # Créer un template
    create_response = test_client.post("/api/v1/admin/generator-templates", json={
        "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
        "enonce_template_html": "<p>{{consigne}}</p>",
        "solution_template_html": "<p>{{solution}}</p>"
    })
    template_id = create_response.json()["id"]
    
    # Mettre à jour
    update_response = test_client.put(
        f"/api/v1/admin/generator-templates/{template_id}",
        json={
            "enonce_template_html": "<p><strong>{{consigne}}</strong></p>",
            "allowed_html_vars": ["tableau_html"]
        }
    )
    
    assert update_response.status_code == 200
    data = update_response.json()
    assert "<strong>" in data["enonce_template_html"]
    assert "tableau_html" in data["allowed_html_vars"]


def test_delete_template(test_client):
    """Test suppression d'un template"""
    # Créer un template
    create_response = test_client.post("/api/v1/admin/generator-templates", json={
        "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
        "enonce_template_html": "<p>{{consigne}}</p>",
        "solution_template_html": "<p>{{solution}}</p>"
    })
    template_id = create_response.json()["id"]
    
    # Supprimer
    delete_response = test_client.delete(f"/api/v1/admin/generator-templates/{template_id}")
    
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True
    
    # Vérifier que le template n'existe plus
    get_response = test_client.get(f"/api/v1/admin/generator-templates/{template_id}")
    assert get_response.status_code == 404


def test_list_templates_filtered(test_client):
    """Test listage avec filtres"""
    # Créer plusieurs templates
    test_client.post("/api/v1/admin/generator-templates", json={
        "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
        "variant_id": "A",
        "enonce_template_html": "<p>{{enonce}}</p>",
        "solution_template_html": "<p>{{solution}}</p>"
    })
    
    test_client.post("/api/v1/admin/generator-templates", json={
        "generator_key": "CALCUL_NOMBRES_V1",
        "variant_id": "B",
        "enonce_template_html": "<p>{{enonce}}</p>",
        "solution_template_html": "<p>{{solution}}</p>"
    })
    
    # Filtrer par generator_key
    response = test_client.get(
        "/api/v1/admin/generator-templates?generator_key=RAISONNEMENT_MULTIPLICATIF_V1"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["generator_key"] == "RAISONNEMENT_MULTIPLICATIF_V1"


def test_validate_template_success(test_client):
    """Test validation réussie d'un template"""
    validate_request = {
        "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
        "variant_id": "default",
        "grade": "6e",
        "difficulty": "facile",
        "seed": 42,
        "enonce_template_html": "<p><strong>{{consigne}}</strong></p><p>{{enonce}}</p>{{{tableau_html}}}",
        "solution_template_html": "<h4>{{methode}}</h4><p>{{reponse_finale}}</p>",
        "allowed_html_vars": ["tableau_html"]
    }
    
    response = test_client.post("/api/v1/admin/generator-templates/validate", json=validate_request)
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert len(data["missing_placeholders"]) == 0
    assert len(data["html_security_errors"]) == 0
    assert data["preview"] is not None
    assert "enonce_html" in data["preview"]
    assert "solution_html" in data["preview"]


def test_validate_template_missing_placeholder(test_client):
    """Test validation avec placeholder manquant => 422 ADMIN_TEMPLATE_MISMATCH"""
    validate_request = {
        "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
        "seed": 42,
        "enonce_template_html": "<p>{{consigne}}</p><p>{{vitesse_lumiere}}</p>",  # Variable inexistante
        "solution_template_html": "<p>{{solution}}</p>",
        "allowed_html_vars": []
    }
    
    response = test_client.post("/api/v1/admin/generator-templates/validate", json=validate_request)
    
    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["error_code"] == "ADMIN_TEMPLATE_MISMATCH"
    assert "vitesse_lumiere" in data["detail"]["missing_placeholders"]
    assert "manquants" in data["detail"]["message"].lower()


def test_validate_template_html_var_not_allowed(test_client):
    """Test validation avec triple moustaches non autorisées => 422 HTML_VAR_NOT_ALLOWED"""
    validate_request = {
        "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
        "seed": 42,
        "enonce_template_html": "<p>{{{enonce}}}</p>",  # Triple moustaches sans autorisation
        "solution_template_html": "<p>{{solution}}</p>",
        "allowed_html_vars": []  # enonce pas autorisé
    }
    
    response = test_client.post("/api/v1/admin/generator-templates/validate", json=validate_request)
    
    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["error_code"] == "HTML_VAR_NOT_ALLOWED"
    assert len(data["detail"]["html_security_errors"]) > 0
    assert data["detail"]["html_security_errors"][0]["type"] == "html_var_not_allowed"
    assert data["detail"]["html_security_errors"][0]["placeholder"] == "enonce"


def test_validate_template_combined_errors(test_client):
    """Test validation avec plusieurs types d'erreurs"""
    validate_request = {
        "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
        "seed": 42,
        "enonce_template_html": "<p>{{{enonce}}}</p><p>{{variable_inexistante}}</p>",
        "solution_template_html": "<p>{{solution}}</p>",
        "allowed_html_vars": []
    }
    
    response = test_client.post("/api/v1/admin/generator-templates/validate", json=validate_request)
    
    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["error_code"] == "ADMIN_TEMPLATE_MISMATCH"  # Missing placeholders en priorité
    assert len(data["detail"]["missing_placeholders"]) > 0
    assert len(data["detail"]["html_security_errors"]) > 0

