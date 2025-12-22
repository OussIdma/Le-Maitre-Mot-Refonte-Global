"""
TESTS_DYN - Exercices dynamiques pour tests
============================================

Ce fichier contient des exercices "template" pour le chapitre de test dynamique.
Les exercices avec is_dynamic=True utilisent un générateur pour produire des variantes.

IMPORTANT: Les exercices dynamiques ne stockent pas l'énoncé/solution figé,
mais des templates avec placeholders {{variable}}.
"""

from typing import List, Dict, Any, Optional
import random
from backend.observability import (
    get_logger as get_obs_logger,
    safe_random_choice,
    safe_randrange,
    get_request_context,
)

obs_logger = get_obs_logger('TESTS_DYN')


# =============================================================================
# EXERCICES TESTS_DYN - Templates dynamiques
# =============================================================================

TESTS_DYN_EXERCISES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "family": "AGRANDISSEMENT_REDUCTION",
        "difficulty": "facile",
        "offer": "free",
        "is_dynamic": True,
        "generator_key": "THALES_V1",
        "enonce_template_html": """<p><strong>Agrandissement d'{{figure_type_article}} :</strong></p>
<p>On considère {{figure_type_article}} de côté <strong>{{cote_initial}} cm</strong>.</p>
<p>On effectue un <strong>{{transformation}}</strong> de coefficient <strong>{{coefficient_str}}</strong>.</p>
<p><em>Question :</em> Quelle est la mesure du côté de la figure obtenue ?</p>""",
        "solution_template_html": """<h4>Correction détaillée</h4>
<ol>
  <li><strong>Compréhension :</strong> On a {{figure_type_article}} de côté {{cote_initial}} cm qu'on {{transformation_verbe}} par {{coefficient_str}}.</li>
  <li><strong>Méthode :</strong> Pour un {{transformation}}, on multiplie chaque dimension par le coefficient.</li>
  <li><strong>Calculs :</strong> {{cote_initial}} × {{coefficient_str}} = <strong>{{cote_final}} cm</strong></li>
  <li><strong>Conclusion :</strong> Le côté de la figure {{transformation_verbe}} mesure <strong>{{cote_final}} cm</strong>.</li>
</ol>""",
        "variables_schema": {
            "figure_type": "string",
            "cote_initial": "number",
            "cote_final": "number",
            "coefficient_str": "string",
            "transformation": "string",
            "transformation_verbe": "string"
        },
        "needs_svg": True,
        "exercise_type": "AGRANDISSEMENT_REDUCTION"
    },
    {
        "id": 2,
        "family": "AGRANDISSEMENT_REDUCTION",
        "difficulty": "moyen",
        "offer": "free",
        "is_dynamic": True,
        "generator_key": "THALES_V1",
        "enonce_template_html": """<p><strong>Agrandissement d'{{figure_type_article}} :</strong></p>
<p>On considère {{figure_type_article}} de longueur <strong>{{longueur_initiale}} cm</strong> et de largeur <strong>{{largeur_initiale}} cm</strong>.</p>
<p>On effectue un <strong>{{transformation}}</strong> de coefficient <strong>{{coefficient_str}}</strong>.</p>
<p><em>Question :</em> Quelles sont les dimensions du rectangle obtenu ?</p>""",
        "solution_template_html": """<h4>Correction détaillée</h4>
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
</ol>""",
        "variables_schema": {
            "longueur_initiale": "number",
            "largeur_initiale": "number",
            "longueur_finale": "number",
            "largeur_finale": "number",
            "coefficient_str": "string",
            "transformation": "string"
        },
        "needs_svg": True,
        "exercise_type": "AGRANDISSEMENT_REDUCTION"
    },
    {
        "id": 3,
        "family": "AGRANDISSEMENT_REDUCTION",
        "difficulty": "difficile",
        "offer": "free",
        "is_dynamic": True,
        "generator_key": "THALES_V1",
        "enonce_template_html": """<p><strong>Agrandissement d'{{figure_type_article}} rectangle :</strong></p>
<p>On considère {{figure_type_article}} rectangle de base <strong>{{base_initiale}} cm</strong> et de hauteur <strong>{{hauteur_initiale}} cm</strong>.</p>
<p>On effectue un <strong>{{transformation}}</strong> de coefficient <strong>{{coefficient_str}}</strong>.</p>
<p><em>Question :</em> Quelles sont les dimensions du triangle obtenu ? Calculer aussi l'aire de chaque triangle.</p>""",
        "solution_template_html": """<h4>Correction détaillée</h4>
<ol>
  <li><strong>Compréhension :</strong> On a {{figure_type_article}} de base {{base_initiale}} cm et hauteur {{hauteur_initiale}} cm.</li>
  <li><strong>Méthode :</strong> On multiplie chaque dimension par {{coefficient_str}}.</li>
  <li><strong>Calculs des dimensions :</strong>
    <ul>
      <li>Base : {{base_initiale}} × {{coefficient_str}} = <strong>{{base_finale}} cm</strong></li>
      <li>Hauteur : {{hauteur_initiale}} × {{coefficient_str}} = <strong>{{hauteur_finale}} cm</strong></li>
    </ul>
  </li>
  <li><strong>Conclusion :</strong> Le triangle {{transformation_verbe}} a une base de <strong>{{base_finale}} cm</strong> et une hauteur de <strong>{{hauteur_finale}} cm</strong>.</li>
</ol>""",
        "variables_schema": {
            "base_initiale": "number",
            "hauteur_initiale": "number",
            "base_finale": "number",
            "hauteur_finale": "number",
            "coefficient_str": "string"
        },
        "needs_svg": True,
        "exercise_type": "AGRANDISSEMENT_REDUCTION"
    }
]


# =============================================================================
# FONCTIONS D'ACCÈS AUX EXERCICES
# =============================================================================

def get_tests_dyn_exercises(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filtre les exercices selon les critères.
    
    IMPORTANT: Si offer="pro" mais qu'aucun exercice "pro" n'existe,
    on fait un fallback explicite vers "free" pour éviter un pool vide.
    """
    exercises = TESTS_DYN_EXERCISES
    
    if offer:
        offer = offer.lower()
        if offer == "free":
            exercises = [ex for ex in exercises if ex["offer"] == "free"]
        elif offer == "pro":
            # Filtrer les exercices "pro"
            pro_exercises = [ex for ex in exercises if ex["offer"] == "pro"]
            # Fallback explicite: si aucun exercice "pro", utiliser "free"
            if not pro_exercises:
                exercises = [ex for ex in exercises if ex["offer"] == "free"]
            else:
                exercises = pro_exercises
        # Si offer est autre chose, on garde tous les exercices (comportement par défaut)
    else:
        exercises = [ex for ex in exercises if ex["offer"] == "free"]
    
    if difficulty:
        difficulty = difficulty.lower()
        exercises = [ex for ex in exercises if ex["difficulty"] == difficulty]
    
    return exercises


def get_random_tests_dyn_exercise(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    seed: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Sélectionne UN exercice de manière déterministe.
    
    Utilise random.Random(seed) pour éviter les effets de bord du random.seed() global.
    """
    available = get_tests_dyn_exercises(offer=offer, difficulty=difficulty)
    
    if not available:
        return None
    
    # Utiliser random.Random(seed) pour un déterminisme isolé
    if seed is not None:
        rng = random.Random(seed)
        return rng.choice(available)
    else:
        ctx = get_request_context()
        return safe_random_choice(available, ctx, obs_logger)


def get_tests_dyn_batch(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    count: int = 1,
    seed: Optional[int] = None
) -> tuple:
    """
    Retourne un batch d'exercices sans doublons.
    
    Utilise random.Random(seed) pour un déterminisme isolé.
    """
    available = get_tests_dyn_exercises(offer=offer, difficulty=difficulty)
    
    if not available:
        return [], {"requested": count, "available": 0, "returned": 0}
    
    # Utiliser random.Random(seed) pour un déterminisme isolé
    if seed is not None:
        rng = random.Random(seed)
        shuffled = available.copy()
        rng.shuffle(shuffled)
    else:
        shuffled = available.copy()
        random.shuffle(shuffled)
    
    actual_count = min(count, len(shuffled))
    selected = shuffled[:actual_count]
    
    info = {
        "requested": count,
        "available": len(available),
        "returned": actual_count,
        "filters": {
            "offer": offer or "free",
            "difficulty": difficulty
        }
    }
    
    return selected, info


def get_tests_dyn_stats() -> Dict[str, Any]:
    """Retourne les statistiques du chapitre."""
    stats = {
        "total": len(TESTS_DYN_EXERCISES),
        "by_offer": {},
        "by_difficulty": {},
        "by_family": {},
        "dynamic_count": 0
    }
    
    for ex in TESTS_DYN_EXERCISES:
        stats["by_offer"][ex["offer"]] = stats["by_offer"].get(ex["offer"], 0) + 1
        stats["by_difficulty"][ex["difficulty"]] = stats["by_difficulty"].get(ex["difficulty"], 0) + 1
        stats["by_family"][ex["family"]] = stats["by_family"].get(ex["family"], 0) + 1
        
        if ex.get("is_dynamic"):
            stats["dynamic_count"] += 1
    
    return stats
