"""
Builder to Legacy Format Converter
Convertit le format Builder (preview JSON) vers le format attendu par les templates Pro historiques
"""

from typing import Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def convert_builder_to_legacy_pro_format(
    preview_json: Dict[str, Any],
    template_config: Dict[str, Any] = None,
    type_doc: str = "exercices"
) -> Dict[str, Any]:
    """
    Convertit le preview JSON du Builder vers le format attendu par les templates Pro historiques
    
    Format Builder (input):
    {
        "sheet_id": "...",
        "titre": "Fiche 6e...",
        "niveau": "6e",
        "items": [
            {
                "item_id": "...",
                "exercise_type_summary": {
                    "titre": "...",
                    "domaine": "...",
                    "niveau": "..."
                },
                "generated": {
                    "questions": [
                        {
                            "enonce_brut": "...",
                            "solution_brut": "..."
                        }
                    ]
                }
            }
        ]
    }
    
    Format Legacy Pro (output):
    {
        "type_doc": "exercices",
        "matiere": "Mathématiques",
        "niveau": "6e",
        "chapitre": "...",
        "date_creation": "01/01/2025",
        "exercises": [
            {
                "enonce": "...",
                "solution": {
                    "etapes": ["..."],
                    "resultat": "..."
                },
                "type": "standard",
                "bareme": [...]
            }
        ]
    }
    
    Args:
        preview_json: Preview JSON du Builder
        template_config: Configuration Pro optionnelle
    
    Returns:
        Document au format Legacy Pro
    """
    logger.info(f"🔄 Conversion Builder → Legacy Pro pour '{preview_json.get('titre')}'")
    
    # Extraire les informations de base
    titre = preview_json.get("titre", "Fiche d'exercices")
    niveau = preview_json.get("niveau", "")
    items = preview_json.get("items", [])
    
    # Convertir les items en exercices Legacy
    exercises = []
    for idx, item in enumerate(items, start=1):
        try:
            exercise = _convert_item_to_legacy_exercise(item, idx)
            exercises.append(exercise)
        except Exception as e:
            logger.error(f"❌ Erreur conversion item {idx}: {e}")
            # Ajouter un exercice fallback
            exercises.append({
                "enonce": f"Exercice {idx} temporairement indisponible",
                "solution": {
                    "etapes": [],
                    "resultat": "Non disponible"
                },
                "type": "standard"
            })
    
    # Construire le document Legacy
    document = {
        "type_doc": type_doc,  # "exercices", "controle", "evaluation", "dm"
        "matiere": "Mathématiques",
        "niveau": niveau,
        "chapitre": titre,  # On utilise le titre de la fiche comme chapitre
        "date_creation": datetime.now().strftime("%d/%m/%Y"),
        "exercises": exercises
    }
    
    logger.info(f"✅ Conversion réussie: {len(exercises)} exercices")
    
    return document


def _convert_item_to_legacy_exercise(item: Dict[str, Any], numero: int) -> Dict[str, Any]:
    """
    Convertit un item Builder en exercice Legacy
    
    Args:
        item: Item de la fiche Builder
        numero: Numéro de l'exercice
    
    Returns:
        Exercice au format Legacy
    """
    exercise_type = item.get("exercise_type_summary", {})
    generated = item.get("generated", {})
    questions = generated.get("questions", [])
    
    # Construire l'énoncé global (toutes les questions) + figures
    enonce_parts = []
    figure_html_parts = []  # Collecter les figures HTML
    
    for q_idx, question in enumerate(questions, start=1):
        enonce_brut = question.get("enonce_brut", "")
        figure_html = question.get("figure_html", "")
        
        if enonce_brut:
            if len(questions) > 1:
                enonce_parts.append(f"{q_idx}. {enonce_brut}")
            else:
                enonce_parts.append(enonce_brut)
        
        # Ajouter la figure si présente
        if figure_html:
            if len(questions) > 1:
                figure_html_parts.append(f'<div class="exercise-figure" data-question="{q_idx}">{figure_html}</div>')
            else:
                figure_html_parts.append(f'<div class="exercise-figure">{figure_html}</div>')
    
    enonce = "\n\n".join(enonce_parts) if enonce_parts else f"Exercice {numero}"
    
    # Collecter les figures dans un champ séparé pour les templates
    figures_combined = "\n".join(figure_html_parts) if figure_html_parts else ""
    
    # Construire la solution avec étapes + figures (si plusieurs questions, répéter les figures)
    etapes = []
    resultat = ""
    correction_figures = []
    
    for q_idx, question in enumerate(questions, start=1):
        solution_brut = question.get("solution_brut", "")
        figure_html = question.get("figure_html", "")
        
        if solution_brut:
            if len(questions) > 1:
                etapes.append(f"Question {q_idx}: {solution_brut}")
            else:
                # Pour une seule question, essayer de séparer en étapes si possible
                # Sinon, mettre toute la solution comme résultat
                if "\n" in solution_brut:
                    lines = solution_brut.split("\n")
                    etapes.extend([line.strip() for line in lines if line.strip()])
                else:
                    resultat = solution_brut
        
        # Ajouter la figure dans la correction aussi (utile pour certains exercices)
        if figure_html and len(questions) > 1:
            correction_figures.append(f'<div class="exercise-figure" data-question="{q_idx}">{figure_html}</div>')
    
    # Si on n'a que des étapes et pas de résultat, prendre la dernière étape comme résultat
    if etapes and not resultat:
        resultat = etapes[-1]
        etapes = etapes[:-1]
    
    # Ajouter les figures dans les étapes si présentes (pour multi-questions)
    if correction_figures:
        etapes.extend(correction_figures)
    
    solution = {
        "etapes": etapes,
        "resultat": resultat if resultat else "Voir les étapes ci-dessus"
    }
    
    # Type d'exercice (standard, qcm, etc.)
    exercise_type_str = "standard"
    
    # Barème (optionnel, peut être ajouté plus tard)
    # Pour l'instant, on ne génère pas de barème automatique
    
    return {
        "enonce": enonce,
        "figure_html": figures_combined,  # Champ séparé pour les templates
        "solution": solution,
        "type": exercise_type_str,
        # "bareme": []  # Optionnel
    }


__all__ = [
    "convert_builder_to_legacy_pro_format"
]
