"""
Pro Export Adapter

Ce module adapte les fiches MathALÉA (format JSON) vers le format attendu par le
legacy Pro PDF generator, SANS modifier le code legacy existant.

ARCHITECTURE NON-DESTRUCTIVE :
- Ne touche PAS au legacy Pro generator
- Sert uniquement de pont entre Builder et Legacy
- Extensible pour futurs formats Pro
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def convert_sheet_preview_to_legacy_format(
    preview_json: Dict[str, Any],
    user_pro_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convertit une fiche MathALÉA (format JSON du preview) vers le format
    attendu par le legacy Pro PDF generator.
    
    Args:
        preview_json: Sortie de l'endpoint /preview
            {
                "sheet_id": "...",
                "titre": "Fiche 6e...",
                "niveau": "6e",
                "items": [
                    {
                        "item_id": "...",
                        "exercise_type_summary": {...},
                        "config": {...},
                        "generated": {
                            "questions": [...]
                        }
                    }
                ]
            }
        
        user_pro_config: Configuration Pro de l'utilisateur (optionnel)
            {
                "logo_url": "https://...",
                "etablissement": "Collège Jean Moulin",
                "template_name": "classique",
                "primary_color": "#1a56db"
            }
    
    Returns:
        Dict au format legacy Pro generator :
        {
            "titre": "...",
            "niveau": "...",
            "etablissement": "...",
            "logo_url": "...",
            "template": "...",
            "exercices": [
                {
                    "numero": 1,
                    "titre": "...",
                    "enonce": "...",
                    "correction": "...",
                    "metadata": {...}
                }
            ]
        }
    """
    logger.info(f"🔄 Conversion fiche '{preview_json.get('titre')}' vers format legacy Pro")
    
    # Extraire les infos de base
    titre = preview_json.get("titre", "Fiche d'exercices")
    niveau = preview_json.get("niveau", "")
    items = preview_json.get("items", [])
    
    # Config Pro par défaut
    etablissement = ""
    logo_url = None
    template = "classique"
    primary_color = "#1a56db"
    
    if user_pro_config:
        etablissement = user_pro_config.get("etablissement", "")
        logo_url = user_pro_config.get("logo_url")
        template = user_pro_config.get("template_name", "classique")
        primary_color = user_pro_config.get("primary_color", "#1a56db")
    
    # Convertir chaque item en exercice legacy
    exercices_legacy = []
    
    for idx, item in enumerate(items, start=1):
        try:
            exercice_legacy = _convert_item_to_legacy_exercise(item, idx)
            exercices_legacy.append(exercice_legacy)
        except Exception as e:
            logger.error(f"❌ Erreur conversion item {idx}: {e}")
            # Ajouter un exercice fallback pour ne pas casser le PDF
            exercices_legacy.append({
                "numero": idx,
                "titre": f"Exercice {idx}",
                "enonce": "Exercice temporairement indisponible",
                "correction": "Correction temporairement indisponible",
                "metadata": {"error": True}
            })
    
    # Construire le format legacy
    legacy_format = {
        "titre": titre,
        "niveau": niveau,
        "etablissement": etablissement,
        "logo_url": logo_url,
        "template": template,
        "primary_color": primary_color,
        "exercices": exercices_legacy,
        "metadata": {
            "generator": "mathalea_builder",
            "sheet_id": preview_json.get("sheet_id"),
            "nb_exercices": len(exercices_legacy)
        }
    }
    
    logger.info(f"✅ Conversion réussie: {len(exercices_legacy)} exercices")
    
    return legacy_format


def _convert_item_to_legacy_exercise(item: Dict[str, Any], numero: int) -> Dict[str, Any]:
    """
    Convertit un item de fiche (format Builder) en exercice legacy.
    
    Args:
        item: Item de la fiche
        numero: Numéro de l'exercice (1, 2, 3...)
    
    Returns:
        Exercice au format legacy
    """
    exercise_type = item.get("exercise_type_summary", {})
    config = item.get("config", {})
    generated = item.get("generated", {})
    questions = generated.get("questions", [])
    
    # Titre de l'exercice
    titre = exercise_type.get("titre", f"Exercice {numero}")
    
    # Construire l'énoncé global
    enonce_parts = []
    for q_idx, question in enumerate(questions, start=1):
        enonce_brut = question.get("enonce_brut", "")
        if enonce_brut:
            enonce_parts.append(f"{q_idx}. {enonce_brut}")
    
    enonce = "\n\n".join(enonce_parts) if enonce_parts else "Énoncé non disponible"
    
    # Construire la correction globale
    correction_parts = []
    for q_idx, question in enumerate(questions, start=1):
        solution_brut = question.get("solution_brut", "")
        if solution_brut:
            correction_parts.append(f"{q_idx}. {solution_brut}")
    
    correction = "\n\n".join(correction_parts) if correction_parts else "Correction non disponible"
    
    # Metadata pour le legacy generator
    metadata = {
        "exercise_type_id": item.get("exercise_type_id"),
        "code_ref": exercise_type.get("code_ref"),
        "niveau": exercise_type.get("niveau"),
        "domaine": exercise_type.get("domaine"),
        "generator_kind": exercise_type.get("generator_kind"),
        "nb_questions": len(questions),
        "seed": config.get("seed"),
        "difficulty": config.get("difficulty")
    }
    
    return {
        "numero": numero,
        "titre": titre,
        "enonce": enonce,
        "correction": correction,
        "metadata": metadata
    }


# Export public
__all__ = [
    "convert_sheet_preview_to_legacy_format"
]
