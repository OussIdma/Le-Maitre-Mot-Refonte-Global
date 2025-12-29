"""
GM07 Handler - Gestionnaire dédié pour le chapitre pilote
=========================================================

Ce handler intercepte les requêtes pour code_officiel="6e_GM07"
et retourne des exercices depuis MongoDB (admin_exercises).

PR2: DB ONLY - Plus de dépendance aux fichiers Python (data/gm07_exercises.py).
DB = source de vérité unique.

Logique métier:
- FREE: ne voit que les exercices offer="free"
- PRO: voit tous les exercices (free + pro)
- La difficulté filtre réellement les exercices disponibles
- Génération de lots SANS DOUBLONS (tant que possible)
- Déterminisme: seed fixe => même exercice (random.Random(seed))
"""

import random
import time
import logging
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.services.static_exercise_repository import StaticExerciseRepository
from backend.services.svg_render_service import generate_exercise_svgs

logger = logging.getLogger(__name__)


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
        exercise: Exercice brut depuis MongoDB (admin_exercises)
        timestamp: Timestamp pour l'ID unique
    
    Returns:
        Exercice formaté pour l'API
    """
    is_premium = exercise.get("offer") == "pro"
    exercise_id_db = exercise.get("id")
    exercise_id = f"ex_6e_gm07_{exercise_id_db}_{timestamp}"
    
    # Générer les SVG selon le type d'exercice
    svg_result = generate_exercise_svgs(exercise)
    
    return {
        "id_exercice": exercise_id,
        "niveau": "6e",
        "chapitre": "Durées et lecture de l'heure",
        "enonce_html": exercise.get("enonce_html", ""),
        "solution_html": exercise.get("solution_html", ""),
        "figure_svg": svg_result["figure_svg"],  # Compatibilité
        "figure_svg_enonce": svg_result["figure_svg_enonce"],
        "figure_svg_solution": svg_result["figure_svg_solution"],
        "svg": svg_result["figure_svg"],  # Compatibilité ancienne
        "pdf_token": exercise_id,
        "metadata": {
            "code_officiel": "6e_GM07",
            "difficulte": exercise.get("difficulty", "moyen"),
            "difficulty": exercise.get("difficulty", "moyen"),
            "is_premium": is_premium,
            "offer": exercise.get("offer", "free"),
            "generator_code": f"6e_GM07_{exercise.get('family', 'NONE')}",
            "family": exercise.get("family"),
            "exercise_type": exercise.get("exercise_type"),
            "exercise_id": exercise_id_db,
            "is_fallback": False,
            "source": "gm07_db_exercises",
            "needs_svg": exercise.get("needs_svg", False),
            "variables": exercise.get("variables"),
            "variables_used": svg_result.get("variables_used")
        }
    }


async def generate_gm07_exercise(
    db: AsyncIOMotorDatabase,
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    seed: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Génère UN exercice GM07 depuis MongoDB.
    
    PR2: DB ONLY - Plus de dépendance aux fichiers Python.
    
    Utilise le seed pour sélectionner un exercice de manière déterministe.
    
    Args:
        db: Instance de la base de données MongoDB
        offer: "free" ou "pro" (défaut: "free")
        difficulty: "facile", "moyen", "difficile" (défaut: tous)
        seed: Graine pour la sélection déterministe
    
    Returns:
        Exercice formaté pour l'API ou None si aucun exercice disponible
    """
    # Normaliser les paramètres
    offer = (offer or "free").lower()
    if difficulty:
        difficulty = difficulty.lower()
    
    # Récupérer le pool d'exercices depuis DB
    repo = StaticExerciseRepository(db)
    pool = await repo.list_by_chapter("6E_GM07", offer=offer, difficulty=difficulty)
    
    if not pool:
        logger.warning(f"[GM07] Aucun exercice disponible pour offer={offer}, difficulty={difficulty}")
        return None
    
    # Sélection déterministe avec seed
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()
    
    # Mélanger le pool et prendre le premier
    pool_copy = pool.copy()
    rng.shuffle(pool_copy)
    exercise = pool_copy[0]
    
    timestamp = int(time.time() * 1000)
    return _format_exercise_response(exercise, timestamp)


async def generate_gm07_batch(
    db: AsyncIOMotorDatabase,
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    count: int = 1,
    seed: Optional[int] = None
) -> tuple:
    """
    Génère un LOT d'exercices GM07 SANS DOUBLONS - VERSION PRODUCTION.
    
    PR2: DB ONLY - Plus de dépendance aux fichiers Python.
    
    Comportement produit:
    - Si pool_size >= count: retourne exactement count exercices UNIQUES
    - Si pool_size < count: retourne pool_size exercices avec metadata.warning
    - JAMAIS de doublons
    
    Args:
        db: Instance de la base de données MongoDB
        offer: "free" ou "pro" (défaut: "free")
        difficulty: "facile", "moyen", "difficile" (défaut: tous)
        count: Nombre d'exercices demandés
        seed: Graine pour le mélange aléatoire (déterminisme)
    
    Returns:
        Tuple (exercices: List[Dict], batch_metadata: Dict)
        - exercices: Liste d'exercices formatés pour l'API
        - batch_metadata: Infos sur le batch (requested, returned, available, warning?)
    """
    # Normaliser les paramètres
    offer = (offer or "free").lower()
    if difficulty:
        difficulty = difficulty.lower()
    
    # Récupérer le pool d'exercices depuis DB
    repo = StaticExerciseRepository(db)
    pool = await repo.list_by_chapter("6E_GM07", offer=offer, difficulty=difficulty)
    
    pool_size = len(pool)
    
    # Construire les métadonnées du batch
    batch_meta = {
        "requested": count,
        "available": pool_size,
        "returned": 0,
        "filters": {
            "offer": offer,
            "difficulty": difficulty
        }
    }
    
    if pool_size == 0:
        batch_meta["warning"] = f"Aucun exercice disponible pour les filtres sélectionnés (offer={offer}, difficulty={difficulty})."
        logger.warning(f"[GM07] {batch_meta['warning']}")
        return [], batch_meta
    
    # Mélanger le pool avec seed pour reproductibilité
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()
    
    pool_copy = pool.copy()
    rng.shuffle(pool_copy)
    
    # Prendre au maximum ce qui est disponible (sans doublons)
    actual_count = min(count, pool_size)
    selected = pool_copy[:actual_count]
    
    batch_meta["returned"] = actual_count
    
    if actual_count < count:
        batch_meta["warning"] = f"Seulement {pool_size} exercices disponibles pour les filtres sélectionnés ({count} demandés)."
        logger.warning(f"[GM07] {batch_meta['warning']}")
    
    # Formater chaque exercice avec un timestamp unique
    base_timestamp = int(time.time() * 1000)
    result = []
    
    for idx, exercise in enumerate(selected):
        formatted = _format_exercise_response(exercise, base_timestamp + idx)
        
        # Ajouter les métadonnées de batch à chaque exercice
        formatted["metadata"]["batch_info"] = {
            "position": idx + 1,
            "total_in_batch": len(selected),
            "requested": batch_meta["requested"],
            "available": batch_meta["available"]
        }
        
        # Ajouter le warning si présent (uniquement sur le premier exercice)
        if idx == 0 and "warning" in batch_meta:
            formatted["metadata"]["warning"] = batch_meta["warning"]
        
        result.append(formatted)
    
    return result, batch_meta


async def get_gm07_available_exercises(
    db: AsyncIOMotorDatabase,
    offer: Optional[str] = None,
    difficulty: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retourne les informations sur les exercices GM07 disponibles.
    Utile pour le debug et les tests.
    
    PR2: DB ONLY - Plus de dépendance aux fichiers Python.
    """
    repo = StaticExerciseRepository(db)
    exercises = await repo.list_by_chapter("6E_GM07", offer=offer, difficulty=difficulty)
    
    return {
        "count": len(exercises),
        "exercises": [
            {
                "id": ex.get("id"),
                "family": ex.get("family"),
                "difficulty": ex.get("difficulty"),
                "offer": ex.get("offer")
            }
            for ex in exercises
        ],
        "filters_applied": {
            "offer": offer or "free",
            "difficulty": difficulty or "all"
        }
    }
