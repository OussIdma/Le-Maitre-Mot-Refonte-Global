"""
Handler pour les exercices dynamiques (TESTS_DYN)
=================================================

Ce handler gère la génération d'exercices dynamiques utilisant des templates
et des générateurs de variables (comme THALES_V1).

Workflow:
1. Sélectionner un exercice template depuis tests_dyn_exercises.py
2. Appeler le générateur (generator_key) pour obtenir les variables
3. Rendre les templates avec les variables
4. Générer les SVG depuis les variables
5. Retourner l'exercice complet
"""

import time
import random
from typing import Dict, Any, Optional, List

from data.tests_dyn_exercises import (
    get_tests_dyn_exercises,
    get_tests_dyn_batch,
    get_tests_dyn_stats,
    get_random_tests_dyn_exercise
)
from backend.generators.thales_generator import generate_dynamic_exercise, GENERATORS_REGISTRY
from services.template_renderer import render_template


def is_tests_dyn_request(code_officiel: Optional[str]) -> bool:
    """Vérifie si la requête concerne le chapitre TESTS_DYN."""
    if not code_officiel:
        return False
    return code_officiel.upper() in ["6E_TESTS_DYN", "TESTS_DYN"]


def format_dynamic_exercise(
    exercise_template: Dict[str, Any],
    timestamp: int,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Formate un exercice dynamique complet.
    
    Args:
        exercise_template: Template d'exercice depuis la DB
        timestamp: Timestamp pour l'ID unique
        seed: Seed pour le générateur (reproductibilité)
    
    Returns:
        Exercice formaté avec HTML rendu et SVG générés
    """
    exercise_id = f"ex_6e_tests_dyn_{exercise_template['id']}_{timestamp}"
    is_premium = exercise_template["offer"] == "pro"
    
    # Récupérer le générateur
    generator_key = exercise_template.get("generator_key", "THALES_V1")
    difficulty = exercise_template.get("difficulty", "moyen")
    
    # Générer les variables et SVG
    gen_result = generate_dynamic_exercise(
        generator_key=generator_key,
        seed=seed,
        difficulty=difficulty
    )
    
    variables = gen_result["variables"]
    results = gen_result["results"]
    
    # Rendre les templates
    enonce_template = exercise_template.get("enonce_template_html", "")
    solution_template = exercise_template.get("solution_template_html", "")
    
    # Fusionner variables et results pour le rendu
    all_vars = {**variables, **results}
    
    enonce_html = render_template(enonce_template, all_vars)
    solution_html = render_template(solution_template, all_vars)
    
    return {
        "id_exercice": exercise_id,
        "niveau": "6e",
        "chapitre": "Tests Dynamiques - Agrandissements/Réductions",
        "enonce_html": enonce_html,
        "solution_html": solution_html,
        "figure_svg": gen_result.get("figure_svg_enonce"),
        "figure_svg_enonce": gen_result.get("figure_svg_enonce"),
        "figure_svg_solution": gen_result.get("figure_svg_solution"),
        "svg": gen_result.get("figure_svg_enonce"),
        "pdf_token": exercise_id,
        "metadata": {
            "code_officiel": "6e_TESTS_DYN",
            "difficulte": difficulty,
            "difficulty": difficulty,
            "is_premium": is_premium,
            "offer": "pro" if is_premium else "free",
            "generator_code": f"6e_TESTS_DYN_{generator_key}",
            "family": exercise_template["family"],
            "exercise_type": exercise_template.get("exercise_type"),
            "exercise_id": exercise_template["id"],
            "is_dynamic": True,
            "generator_key": generator_key,
            "seed_used": seed,
            "variables": variables,
            "variables_used": {"source": "generator", **variables},
            "source": "dynamic_generator",
            "needs_svg": exercise_template.get("needs_svg", True)
        }
    }


def generate_tests_dyn_exercise(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    seed: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Génère UN exercice dynamique.
    
    Args:
        offer: "free" ou "pro"
        difficulty: "facile", "moyen", "difficile"
        seed: Graine pour reproductibilité
    
    Returns:
        Exercice formaté pour l'API ou None
    """
    offer = (offer or "free").lower()
    if difficulty:
        difficulty = difficulty.lower()
    
    # Sélectionner un template
    exercise_template = get_random_tests_dyn_exercise(
        offer=offer,
        difficulty=difficulty,
        seed=seed
    )
    
    if not exercise_template:
        return None
    
    timestamp = int(time.time() * 1000)
    
    # Utiliser un seed dérivé pour le générateur
    gen_seed = (seed or timestamp) + exercise_template["id"]
    
    return format_dynamic_exercise(exercise_template, timestamp, seed=gen_seed)


def generate_tests_dyn_batch(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    count: int = 1,
    seed: Optional[int] = None
) -> tuple:
    """
    Génère un batch d'exercices dynamiques.
    
    Chaque exercice utilise un seed différent pour des variantes uniques.
    
    Args:
        offer: "free" ou "pro"
        difficulty: "facile", "moyen", "difficile"
        count: Nombre d'exercices souhaités
        seed: Graine de base pour reproductibilité
    
    Returns:
        Tuple (exercises, batch_info)
    """
    offer = (offer or "free").lower()
    if difficulty:
        difficulty = difficulty.lower()
    
    # Récupérer les templates disponibles
    templates, info = get_tests_dyn_batch(
        offer=offer,
        difficulty=difficulty,
        count=count,
        seed=seed
    )
    
    if not templates:
        return [], {
            "requested": count,
            "available": 0,
            "returned": 0,
            "filters": {"offer": offer, "difficulty": difficulty},
            "is_dynamic": True
        }
    
    timestamp = int(time.time() * 1000)
    exercises = []
    
    for i, template in enumerate(templates):
        # Seed unique pour chaque exercice
        ex_seed = (seed or timestamp) + i * 1000 + template["id"]
        
        formatted = format_dynamic_exercise(template, timestamp + i, seed=ex_seed)
        exercises.append(formatted)
    
    batch_info = {
        "requested": count,
        "available": info["available"],
        "returned": len(exercises),
        "filters": {"offer": offer, "difficulty": difficulty},
        "is_dynamic": True,
        "generator_used": "THALES_V1"
    }
    
    return exercises, batch_info


def get_available_generators() -> List[str]:
    """Retourne la liste des générateurs disponibles."""
    return list(GENERATORS_REGISTRY.keys())


if __name__ == "__main__":
    # Test rapide
    print("=== TEST HANDLER TESTS_DYN ===")
    
    # Test single
    ex = generate_tests_dyn_exercise(offer="free", difficulty="moyen", seed=42)
    if ex:
        print(f"✅ Single: {ex['id_exercice']}")
        print(f"   Énoncé: {ex['enonce_html'][:100]}...")
        print(f"   Variables: {ex['metadata']['variables']}")
    
    # Test batch
    exercises, info = generate_tests_dyn_batch(offer="free", count=3, seed=123)
    print(f"\n✅ Batch: {info['returned']}/{info['requested']} exercices")
    for ex in exercises:
        print(f"   - {ex['id_exercice']}: {ex['metadata']['variables'].get('coefficient', 'N/A')}")
