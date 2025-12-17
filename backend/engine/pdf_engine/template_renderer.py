"""
Template Renderer Service
Utilise Jinja2 pour rendre les templates HTML historiques pour les PDFs Pro
"""

import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Chemin vers les templates
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

# Créer l'environnement Jinja2
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True
)


def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """
    Rend un template Jinja2 avec le contexte fourni
    
    Args:
        template_name: Nom du fichier template (ex: "sujet_classique.html")
        context: Dictionnaire de variables pour le template
    
    Returns:
        HTML rendu en string
    
    Raises:
        Exception si le template n'existe pas ou si le rendu échoue
    """
    try:
        template = jinja_env.get_template(template_name)
        html = template.render(**context)
        logger.info(f"✅ Template '{template_name}' rendu avec succès ({len(html)} caractères)")
        
        # DEBUG: Sauvegarder le HTML généré pour inspection
        import tempfile
        temp_path = tempfile.gettempdir()
        debug_file = f"{temp_path}/debug_{template_name}"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html)
        logger.info(f"📝 HTML sauvegardé dans: {debug_file}")
        
        return html
    except Exception as e:
        logger.error(f"❌ Erreur lors du rendu du template '{template_name}': {e}")
        raise


def render_pro_sujet(
    template_style: str,
    document_data: Dict[str, Any],
    template_config: Dict[str, Any] = None
) -> str:
    """
    Rend le template de sujet Pro (Classique ou Académique)
    
    Args:
        template_style: "classique" ou "academique"
        document_data: Données du document (exercises, titre, niveau, etc.)
        template_config: Configuration Pro (logo, école, professeur, etc.)
    
    Returns:
        HTML rendu
    """
    template_name = f"sujet_{template_style}.html"
    
    context = {
        "document": document_data,
        "template_config": template_config or {},
        "date_creation": document_data.get("date_creation", "")
    }
    
    return render_template(template_name, context)


def render_pro_corrige(
    template_style: str,
    document_data: Dict[str, Any],
    template_config: Dict[str, Any] = None
) -> str:
    """
    Rend le template de corrigé Pro (Classique ou Académique)
    
    Args:
        template_style: "classique" ou "academique"
        document_data: Données du document (exercises, solutions, etc.)
        template_config: Configuration Pro (logo, école, professeur, etc.)
    
    Returns:
        HTML rendu
    """
    template_name = f"corrige_{template_style}.html"
    
    context = {
        "document": document_data,
        "template_config": template_config or {}
    }
    
    return render_template(template_name, context)


__all__ = [
    "render_template",
    "render_pro_sujet",
    "render_pro_corrige"
]
