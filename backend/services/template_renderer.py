"""
Service de rendu de templates Mustache simple
==============================================

Ce service effectue le rendu de templates HTML avec des placeholders {{variable}}.
PAS de Jinja exécuté - uniquement des remplacements simples et sûrs.

Usage:
    render_template("<p>Le côté mesure {{cote}} cm</p>", {"cote": 5})
    → "<p>Le côté mesure 5 cm</p>"
"""

import re
from typing import Dict, Any, Optional


def render_template(template: str, variables: Dict[str, Any]) -> str:
    """
    Remplace les placeholders {{var}} par leurs valeurs.
    
    Règles:
    - Format: {{nom_variable}}
    - Espaces autorisés: {{ nom_variable }} 
    - Si variable absente: laisse le placeholder intact
    - Valeurs numériques formatées intelligemment (pas de .0 inutile)
    
    Args:
        template: Template HTML avec placeholders
        variables: Dictionnaire des valeurs
    
    Returns:
        Template rendu avec les valeurs substituées
    """
    if not template:
        return ""
    
    if not variables:
        return template
    
    def replace_placeholder(match):
        var_name = match.group(1).strip()
        
        if var_name in variables:
            value = variables[var_name]
            
            # Formater les nombres
            if isinstance(value, float):
                # Éviter "5.0" → "5"
                if value == int(value):
                    return str(int(value))
                else:
                    return str(value)
            
            return str(value)
        
        # Variable non trouvée - laisser le placeholder
        return match.group(0)
    
    # Pattern: {{ variable }} avec espaces optionnels
    pattern = r'\{\{\s*(\w+)\s*\}\}'
    
    return re.sub(pattern, replace_placeholder, template)


def validate_template(template: str, required_variables: Optional[list] = None) -> Dict[str, Any]:
    """
    Valide un template et extrait les variables utilisées.
    
    Args:
        template: Template à valider
        required_variables: Liste des variables obligatoires
    
    Returns:
        Dict avec:
        - valid: bool
        - variables_found: list des variables trouvées
        - missing_variables: list des variables manquantes
        - errors: list des erreurs
    """
    result = {
        "valid": True,
        "variables_found": [],
        "missing_variables": [],
        "errors": []
    }
    
    if not template:
        result["errors"].append("Template vide")
        result["valid"] = False
        return result
    
    # Extraire toutes les variables
    pattern = r'\{\{\s*(\w+)\s*\}\}'
    matches = re.findall(pattern, template)
    result["variables_found"] = list(set(matches))
    
    # Vérifier les variables requises
    if required_variables:
        for var in required_variables:
            if var not in result["variables_found"]:
                result["missing_variables"].append(var)
                result["valid"] = False
    
    return result


def get_template_variables(template: str) -> list:
    """
    Extrait la liste des variables d'un template.
    
    Args:
        template: Template à analyser
    
    Returns:
        Liste des noms de variables (sans doublons)
    """
    if not template:
        return []
    
    pattern = r'\{\{\s*(\w+)\s*\}\}'
    matches = re.findall(pattern, template)
    return list(set(matches))


# Templates par défaut pour THALES_V1
THALES_V1_TEMPLATES = {
    "carre": {
        "enonce": """<p><strong>Agrandissement d'{{figure_type_article}} :</strong></p>
<p>On considère {{figure_type_article}} de côté <strong>{{cote_initial}} cm</strong>.</p>
<p>On effectue un <strong>{{transformation}}</strong> de coefficient <strong>{{coefficient_str}}</strong>.</p>
<p><em>Question :</em> Quelle est la mesure du côté de la figure obtenue ?</p>""",
        
        "solution": """<h4>Correction détaillée</h4>
<ol>
  <li><strong>Compréhension :</strong> On a {{figure_type_article}} de côté {{cote_initial}} cm qu'on {{transformation_verbe}} par {{coefficient_str}}.</li>
  <li><strong>Méthode :</strong> Pour un {{transformation}}, on multiplie chaque dimension par le coefficient.</li>
  <li><strong>Calculs :</strong> {{cote_initial}} × {{coefficient_str}} = <strong>{{cote_final}} cm</strong></li>
  <li><strong>Conclusion :</strong> Le côté du carré {{transformation_verbe}} mesure <strong>{{cote_final}} cm</strong>.</li>
</ol>"""
    },
    
    "rectangle": {
        "enonce": """<p><strong>Agrandissement d'{{figure_type_article}} :</strong></p>
<p>On considère {{figure_type_article}} de longueur <strong>{{longueur_initiale}} cm</strong> et de largeur <strong>{{largeur_initiale}} cm</strong>.</p>
<p>On effectue un <strong>{{transformation}}</strong> de coefficient <strong>{{coefficient_str}}</strong>.</p>
<p><em>Question :</em> Quelles sont les dimensions du rectangle obtenu ?</p>""",
        
        "solution": """<h4>Correction détaillée</h4>
<ol>
  <li><strong>Compréhension :</strong> On a {{figure_type_article}} de dimensions {{longueur_initiale}} cm × {{largeur_initiale}} cm qu'on {{transformation_verbe}}.</li>
  <li><strong>Méthode :</strong> On multiplie chaque dimension par {{coefficient_str}}.</li>
  <li><strong>Calculs :</strong>
    <ul>
      <li>Longueur : {{longueur_initiale}} × {{coefficient_str}} = <strong>{{longueur_finale}} cm</strong></li>
      <li>Largeur : {{largeur_initiale}} × {{coefficient_str}} = <strong>{{largeur_finale}} cm</strong></li>
    </ul>
  </li>
  <li><strong>Conclusion :</strong> Le rectangle {{transformation_verbe}} mesure <strong>{{longueur_finale}} cm × {{largeur_finale}} cm</strong>.</li>
</ol>"""
    },
    
    "triangle": {
        "enonce": """<p><strong>Agrandissement d'{{figure_type_article}} rectangle :</strong></p>
<p>On considère {{figure_type_article}} rectangle de base <strong>{{base_initiale}} cm</strong> et de hauteur <strong>{{hauteur_initiale}} cm</strong>.</p>
<p>On effectue un <strong>{{transformation}}</strong> de coefficient <strong>{{coefficient_str}}</strong>.</p>
<p><em>Question :</em> Quelles sont les dimensions du triangle obtenu ?</p>""",
        
        "solution": """<h4>Correction détaillée</h4>
<ol>
  <li><strong>Compréhension :</strong> On a {{figure_type_article}} de base {{base_initiale}} cm et hauteur {{hauteur_initiale}} cm.</li>
  <li><strong>Méthode :</strong> On multiplie chaque dimension par {{coefficient_str}}.</li>
  <li><strong>Calculs :</strong>
    <ul>
      <li>Base : {{base_initiale}} × {{coefficient_str}} = <strong>{{base_finale}} cm</strong></li>
      <li>Hauteur : {{hauteur_initiale}} × {{coefficient_str}} = <strong>{{hauteur_finale}} cm</strong></li>
    </ul>
  </li>
  <li><strong>Conclusion :</strong> Le triangle {{transformation_verbe}} a une base de <strong>{{base_finale}} cm</strong> et une hauteur de <strong>{{hauteur_finale}} cm</strong>.</li>
</ol>"""
    }
}


def get_thales_v1_template(figure_type: str, template_type: str = "enonce") -> str:
    """
    Récupère un template par défaut pour THALES_V1.
    
    Args:
        figure_type: "carre", "rectangle" ou "triangle"
        template_type: "enonce" ou "solution"
    
    Returns:
        Template HTML avec placeholders
    """
    if figure_type not in THALES_V1_TEMPLATES:
        figure_type = "rectangle"  # Fallback
    
    return THALES_V1_TEMPLATES[figure_type].get(template_type, "")


if __name__ == "__main__":
    # Test
    template = "<p>Le carré a un côté de {{cote}} cm, soit {{cote}} × {{cote}} = {{aire}} cm².</p>"
    variables = {"cote": 5, "aire": 25}
    
    result = render_template(template, variables)
    print("Template:", template)
    print("Variables:", variables)
    print("Résultat:", result)
    
    # Validation
    validation = validate_template(template, ["cote", "aire", "perimetre"])
    print("\nValidation:", validation)
