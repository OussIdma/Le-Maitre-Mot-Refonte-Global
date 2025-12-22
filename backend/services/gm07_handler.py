"""
GM07 Handler - Gestionnaire dédié pour le chapitre pilote
=========================================================

Ce handler intercepte les requêtes pour code_officiel="6e_GM07"
et retourne des exercices depuis la source figée (gm07_exercises.py).

Logique métier:
- FREE: ne voit que les exercices offer="free" (ids 1-10)
- PRO: voit tous les exercices (ids 1-20)
- La difficulté filtre réellement les exercices disponibles
- Génération de lots SANS DOUBLONS (tant que possible)
"""

import random
import time
from typing import Dict, Any, Optional, List
from data.gm07_exercises import (
    get_random_gm07_exercise, 
    get_gm07_exercises, 
    get_gm07_stats,
    get_gm07_batch,
    get_exercise_by_seed_index
)
from services.svg_render_service import generate_exercise_svgs


def is_gm07_request(code_officiel: Optional[str]) -> bool:
    """
    Vérifie si la requête concerne le chapitre GM07.
    
    Args:
        code_officiel: Le code officiel du chapitre
    
    Returns:
        True si c'est une requête GM07
    """
    return code_officiel and code_officiel.upper() == "6E_GM07"


def _format_exercise_response(exercise: Dict[str, Any], timestamp: int) -> Dict[str, Any]:
    """
    Formate un exercice brut en réponse API.
    
    Args:
        exercise: Exercice brut depuis gm07_exercises.py
        timestamp: Timestamp pour l'ID unique
    
    Returns:
        Exercice formaté pour l'API
    """
    is_premium = exercise["offer"] == "pro"
    exercise_id = f"ex_6e_gm07_{exercise['id']}_{timestamp}"
    
    # Générer les SVG selon le type d'exercice
    svg_result = generate_exercise_svgs(exercise)
    
    return {
        "id_exercice": exercise_id,
        "niveau": "6e",
        "chapitre": "Durées et lecture de l'heure",
        "enonce_html": exercise["enonce_html"],
        "solution_html": exercise["solution_html"],
        "figure_svg": svg_result["figure_svg"],  # Compatibilité
        "figure_svg_enonce": svg_result["figure_svg_enonce"],
        "figure_svg_solution": svg_result["figure_svg_solution"],
        "svg": svg_result["figure_svg"],  # Compatibilité ancienne
        "pdf_token": exercise_id,
        "metadata": {
            "code_officiel": "6e_GM07",
            "difficulte": exercise["difficulty"],
            "difficulty": exercise["difficulty"],
            "is_premium": is_premium,
            "offer": "pro" if is_premium else "free",
            "generator_code": f"6e_GM07_{exercise['family']}",
            "family": exercise["family"],
            "exercise_type": exercise.get("exercise_type"),
            "exercise_id": exercise["id"],
            "is_fallback": False,
            "source": "gm07_fixed_exercises",
            "needs_svg": exercise.get("needs_svg", False),
            "variables": exercise.get("variables"),
            "variables_used": svg_result.get("variables_used")
        }
    }


def generate_gm07_exercise(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    seed: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Génère UN exercice GM07 depuis la source figée.
    
    Utilise le seed pour sélectionner un index déterministe,
    garantissant que des seeds différents retournent des exercices différents.
    
    Args:
        offer: "free" ou "pro" (défaut: "free")
        difficulty: "facile", "moyen", "difficile" (défaut: tous)
        seed: Graine pour la sélection (utilisée comme index déterministe)
    
    Returns:
        Exercice formaté pour l'API ou None si aucun exercice disponible
    """
    # Normaliser les paramètres
    offer = (offer or "free").lower()
    if difficulty:
        difficulty = difficulty.lower()
    
    # Sélectionner un exercice basé sur le seed (sélection déterministe)
    exercise = get_exercise_by_seed_index(
        offer=offer,
        difficulty=difficulty,
        seed=seed
    )
    
    if not exercise:
        return None
    
    timestamp = int(time.time() * 1000)
    return _format_exercise_response(exercise, timestamp)


def generate_gm07_batch(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    count: int = 1,
    seed: Optional[int] = None
) -> tuple:
    """
    Génère un LOT d'exercices GM07 SANS DOUBLONS - VERSION PRODUCTION.
    
    Comportement produit:
    - Si pool_size >= count: retourne exactement count exercices UNIQUES
    - Si pool_size < count: retourne pool_size exercices avec metadata.warning
    - JAMAIS de doublons
    
    Args:
        offer: "free" ou "pro" (défaut: "free")
        difficulty: "facile", "moyen", "difficile" (défaut: tous)
        count: Nombre d'exercices demandés
        seed: Graine pour le mélange aléatoire
    
    Returns:
        Tuple (exercices: List[Dict], batch_metadata: Dict)
        - exercices: Liste d'exercices formatés pour l'API
        - batch_metadata: Infos sur le batch (requested, returned, available, warning?)
    """
    # Normaliser les paramètres
    offer = (offer or "free").lower()
    if difficulty:
        difficulty = difficulty.lower()
    
    # Obtenir le lot sans doublons
    exercises, batch_meta = get_gm07_batch(
        offer=offer,
        difficulty=difficulty,
        count=count,
        seed=seed
    )
    
    if not exercises:
        return [], batch_meta
    
    # Formater chaque exercice avec un timestamp unique
    base_timestamp = int(time.time() * 1000)
    result = []
    
    for idx, exercise in enumerate(exercises):
        formatted = _format_exercise_response(exercise, base_timestamp + idx)
        
        # Ajouter les métadonnées de batch à chaque exercice
        formatted["metadata"]["batch_info"] = {
            "position": idx + 1,
            "total_in_batch": len(exercises),
            "requested": batch_meta["requested"],
            "available": batch_meta["available"]
        }
        
        # Ajouter le warning si présent (uniquement sur le premier exercice)
        if idx == 0 and "warning" in batch_meta:
            formatted["metadata"]["warning"] = batch_meta["warning"]
        
        result.append(formatted)
    
    return result, batch_meta


def get_gm07_available_exercises(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retourne les informations sur les exercices GM07 disponibles.
    Utile pour le debug et les tests.
    """
    exercises = get_gm07_exercises(offer=offer, difficulty=difficulty)
    
    return {
        "count": len(exercises),
        "exercises": [
            {
                "id": ex["id"],
                "family": ex["family"],
                "difficulty": ex["difficulty"],
                "offer": ex["offer"]
            }
            for ex in exercises
        ],
        "filters_applied": {
            "offer": offer or "free",
            "difficulty": difficulty or "all"
        }
    }


# =============================================================================
# STATISTIQUES GM07 (pour debug)
# =============================================================================

def get_gm07_chapter_info() -> Dict[str, Any]:
    """Retourne les informations complètes sur le chapitre GM07"""
    stats = get_gm07_stats()
    
    return {
        "code_officiel": "6e_GM07",
        "titre": "Durées et lecture de l'heure",
        "niveau": "6e",
        "domaine": "Grandeurs et mesures",
        "type": "chapitre_pilote",
        "source": "exercices_figes",
        "statistics": stats,
        "rules": {
            "free_range": "ids 1-10",
            "pro_range": "ids 11-20",
            "difficulty_levels": ["facile", "moyen", "difficile"],
            "families": ["LECTURE_HORLOGE", "CONVERSION", "CALCUL_DUREE", "PROBLEME_DUREES"]
        }
    }
