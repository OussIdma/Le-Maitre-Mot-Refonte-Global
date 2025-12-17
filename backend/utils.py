"""
Utilitaires partagés pour le backend
"""
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

def get_emergent_key() -> str:
    """Récupère la clé Emergent LLM depuis les variables d'environnement"""
    key = os.getenv('EMERGENT_LLM_KEY')
    if not key:
        raise ValueError("EMERGENT_LLM_KEY not found in environment variables")
    return key
