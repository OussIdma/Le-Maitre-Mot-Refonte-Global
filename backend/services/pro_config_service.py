"""
Service de gestion des configurations Pro
Centralise la logique de lecture/création des paramètres Pro pour l'export PDF
"""

from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import logging

logger = logging.getLogger(__name__)

# Connexion MongoDB
mongo_url = os.environ.get('MONGO_URL')
if not mongo_url:
    raise ValueError("MONGO_URL environment variable is required")

client = AsyncIOMotorClient(mongo_url)
db = client.mathalea_db

# Utiliser la collection user_templates de l'ancien système (migration sans rupture)
user_templates_collection = db.user_templates


async def get_pro_config_for_user(user_email: str) -> Dict[str, Any]:
    """
    Récupère la configuration Pro d'un utilisateur depuis la collection user_templates
    Compatible avec l'ancien système
    
    Args:
        user_email: Email de l'utilisateur Pro
    
    Returns:
        Dict avec la configuration Pro:
        {
            "professor_name": str,
            "school_name": str,
            "school_year": str,
            "footer_text": str,
            "logo_url": str | None,
            "template_choice": str,
            "template_style": str
        }
    """
    logger.info(f"🔍 Récupération config Pro (user_templates) pour : {user_email}")
    
    try:
        # Chercher dans la collection user_templates (ancien système)
        template_doc = await user_templates_collection.find_one(
            {"user_email": user_email},
            {"_id": 0}
        )
        
        if template_doc:
            logger.info(f"✅ Template trouvé pour {user_email}")
            
            # Mapper les champs de UserTemplate vers notre format
            # Migrations de noms de champs si nécessaire
            logo_url = template_doc.get("logo_url")
            
            # Migration des anciens chemins logo
            if logo_url and logo_url.startswith('/uploads/logos/'):
                logo_url = logo_url  # Garder tel quel pour l'instant
            
            return {
                "professor_name": template_doc.get("professor_name", ""),
                "school_name": template_doc.get("school_name", ""),
                "school_year": template_doc.get("school_year", "2024-2025"),
                "footer_text": template_doc.get("footer_text", ""),
                "logo_url": logo_url,
                "template_choice": template_doc.get("template_style", "classique"),
                "template_style": template_doc.get("template_style", "minimaliste")
            }
        
        # Aucune config trouvée → créer une config par défaut dans user_templates
        logger.info(f"⚠️ Aucun template trouvé pour {user_email}, création d'un template par défaut")
        
        from models.server_models import UserTemplate
        
        default_template = {
            "user_email": user_email,
            "logo_filename": None,
            "logo_url": None,
            "professor_name": "",
            "school_name": "Le Maître Mot",
            "school_year": "2024-2025",
            "footer_text": "Document généré par Le Maître Mot",
            "template_style": "classique",
            "colors": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Insérer le template par défaut
        await user_templates_collection.insert_one(default_template)
        logger.info(f"✅ Template par défaut créé pour {user_email}")
        
        return {
            "professor_name": "",
            "school_name": "Le Maître Mot",
            "school_year": "2024-2025",
            "footer_text": "Document généré par Le Maître Mot",
            "logo_url": None,
            "template_choice": "classique",
            "template_style": "classique"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération template pour {user_email}: {e}")
        # En cas d'erreur, retourner une config par défaut sans insertion
        return {
            "professor_name": "",
            "school_name": "Le Maître Mot",
            "school_year": "2024-2025",
            "footer_text": "Document généré par Le Maître Mot",
            "logo_url": None,
            "template_choice": "classique",
            "template_style": "classique"
        }


async def update_pro_config(user_email: str, updates: Dict[str, Any]) -> bool:
    """
    Met à jour la configuration Pro d'un utilisateur dans user_templates
    
    Args:
        user_email: Email de l'utilisateur
        updates: Dict avec les champs à mettre à jour
    
    Returns:
        True si succès, False sinon
    """
    try:
        updates["updated_at"] = datetime.now(timezone.utc)
        
        # Mapper les noms de champs si nécessaire
        # template_choice → template_style pour compatibilité
        if "template_choice" in updates:
            updates["template_style"] = updates["template_choice"]
        
        result = await user_templates_collection.update_one(
            {"user_email": user_email},
            {"$set": updates},
            upsert=True
        )
        
        logger.info(f"✅ Template mis à jour pour {user_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour template: {e}")
        return False


__all__ = [
    "get_pro_config_for_user",
    "update_pro_config"
]
