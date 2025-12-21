#!/usr/bin/env python3
"""
Script de validation des placeholders de templates dynamiques
==============================================================

Ce script valide que tous les placeholders utilisés dans les templates
d'un exercice dynamique sont bien générés par le générateur correspondant.

Usage:
    python backend/scripts/validate_template_placeholders.py \
        --generator SIMPLIFICATION_FRACTIONS_V1 \
        --enonce-template "<p>{{fraction}}</p>" \
        --solution-template "<ol><li>{{step1}}</li></ol>"

Ou pour valider un exercice en DB:
    python backend/scripts/validate_template_placeholders.py \
        --chapter-code 6E_AA_TEST \
        --exercise-id 1
"""

import sys
import os
import re
import argparse
import asyncio
from typing import Dict, Set, List, Any, Optional

# Ajouter le chemin du backend au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from backend.generators.factory import GeneratorFactory
from backend.logger import get_logger

logger = get_logger()

# Configuration MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("DB_NAME", "lemaitremot")


def extract_placeholders(template: str) -> Set[str]:
    """
    Extrait tous les placeholders {{variable}} d'un template.
    
    Args:
        template: Template HTML avec placeholders
        
    Returns:
        Ensemble des noms de placeholders (sans les {{}})
    """
    if not template:
        return set()
    
    pattern = r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}"
    matches = re.findall(pattern, template)
    return set(matches)


def validate_placeholders(
    generator_key: str,
    enonce_template: str,
    solution_template: str,
    difficulty: str = "moyen",
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Valide que tous les placeholders sont générés par le générateur.
    
    Args:
        generator_key: Clé du générateur (ex: SIMPLIFICATION_FRACTIONS_V1)
        enonce_template: Template énoncé avec placeholders
        solution_template: Template solution avec placeholders
        difficulty: Difficulté pour la génération de test
        seed: Seed pour la génération (optionnel)
        
    Returns:
        Dict avec:
        - valid: bool
        - errors: List[str] (si valid=False)
        - placeholders_used: Set[str]
        - variables_generated: Set[str]
        - missing: Set[str] (placeholders manquants)
    """
    # Extraire les placeholders des templates
    enonce_placeholders = extract_placeholders(enonce_template)
    solution_placeholders = extract_placeholders(solution_template)
    all_placeholders = enonce_placeholders.union(solution_placeholders)
    
    # Récupérer le générateur
    generator_class = GeneratorFactory.get(generator_key.upper())
    if not generator_class:
        return {
            "valid": False,
            "errors": [f"Générateur '{generator_key}' non trouvé dans GeneratorFactory"],
            "placeholders_used": all_placeholders,
            "variables_generated": set(),
            "missing": all_placeholders
        }
    
    # Générer un exercice de test
    try:
        if seed is None:
            import time
            seed = int(time.time() * 1000)
        
        generator = generator_class(seed=seed)
        result = generator.generate({"difficulty": difficulty})
        
        # Fusionner variables et results
        variables = result.get("variables", {})
        results = result.get("results", {})
        all_variables = set(variables.keys()).union(set(results.keys()))
        
        # Identifier les placeholders manquants
        missing = all_placeholders - all_variables
        
        if missing:
            return {
                "valid": False,
                "errors": [
                    f"Placeholders manquants: {sorted(missing)}",
                    f"Variables générées: {sorted(all_variables)}"
                ],
                "placeholders_used": all_placeholders,
                "variables_generated": all_variables,
                "missing": missing
            }
        else:
            return {
                "valid": True,
                "errors": [],
                "placeholders_used": all_placeholders,
                "variables_generated": all_variables,
                "missing": set()
            }
    
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Erreur lors de la génération de test: {str(e)}"],
            "placeholders_used": all_placeholders,
            "variables_generated": set(),
            "missing": all_placeholders
        }


async def validate_exercise_from_db(
    chapter_code: str,
    exercise_id: int
) -> Dict[str, Any]:
    """
    Valide un exercice dynamique depuis la DB.
    
    Args:
        chapter_code: Code du chapitre (ex: 6E_AA_TEST)
        exercise_id: ID de l'exercice
        
    Returns:
        Dict avec les résultats de validation
    """
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    exercises_collection = db.admin_exercises
    
    chapter_upper = chapter_code.upper().replace("-", "_")
    
    # Récupérer l'exercice
    exercise = await exercises_collection.find_one(
        {"chapter_code": chapter_upper, "id": exercise_id},
        {"_id": 0}
    )
    
    if not exercise:
        client.close()
        return {
            "valid": False,
            "errors": [f"Exercice {chapter_code}/{exercise_id} non trouvé en DB"]
        }
    
    if not exercise.get("is_dynamic"):
        client.close()
        return {
            "valid": False,
            "errors": [f"L'exercice {chapter_code}/{exercise_id} n'est pas dynamique"]
        }
    
    generator_key = exercise.get("generator_key", "")
    if not generator_key:
        client.close()
        return {
            "valid": False,
            "errors": [f"L'exercice {chapter_code}/{exercise_id} n'a pas de generator_key"]
        }
    
    # Récupérer les templates
    enonce_template = exercise.get("enonce_template_html", "")
    solution_template = exercise.get("solution_template_html", "")
    difficulty = exercise.get("difficulty", "moyen")
    
    # Valider les templates principaux
    result = validate_placeholders(
        generator_key=generator_key,
        enonce_template=enonce_template,
        solution_template=solution_template,
        difficulty=difficulty
    )
    
    # Valider aussi les variants si présents
    template_variants = exercise.get("template_variants", [])
    variant_errors = []
    
    for variant in template_variants:
        if isinstance(variant, dict):
            variant_id = variant.get("id", "unknown")
            variant_enonce = variant.get("enonce_template_html", "")
            variant_solution = variant.get("solution_template_html", "")
            
            variant_result = validate_placeholders(
                generator_key=generator_key,
                enonce_template=variant_enonce,
                solution_template=variant_solution,
                difficulty=difficulty
            )
            
            if not variant_result["valid"]:
                variant_errors.append({
                    "variant_id": variant_id,
                    "errors": variant_result["errors"],
                    "missing": variant_result["missing"]
                })
    
    client.close()
    
    # Fusionner les résultats
    if variant_errors:
        result["errors"].extend([
            f"Variant {v['variant_id']}: {', '.join(v['errors'])}"
            for v in variant_errors
        ])
        result["valid"] = False
    
    result["exercise_info"] = {
        "chapter_code": chapter_code,
        "exercise_id": exercise_id,
        "generator_key": generator_key,
        "has_variants": len(template_variants) > 0,
        "variant_count": len(template_variants)
    }
    
    return result


def print_validation_result(result: Dict[str, Any]) -> None:
    """
    Affiche les résultats de validation de manière lisible.
    """
    if result.get("valid"):
        print("✅ Validation réussie")
        print(f"   Placeholders utilisés: {len(result['placeholders_used'])}")
        print(f"   Variables générées: {len(result['variables_generated'])}")
    else:
        print("❌ Validation échouée")
        for error in result.get("errors", []):
            print(f"   - {error}")
        
        if result.get("missing"):
            print(f"\n   Placeholders manquants: {sorted(result['missing'])}")
            print(f"   Variables disponibles: {sorted(result['variables_generated'])}")
    
    if result.get("exercise_info"):
        info = result["exercise_info"]
        print(f"\n📋 Exercice: {info['chapter_code']}/{info['exercise_id']}")
        print(f"   Générateur: {info['generator_key']}")
        if info["has_variants"]:
            print(f"   Variants: {info['variant_count']}")


async def main():
    parser = argparse.ArgumentParser(
        description="Valide les placeholders de templates dynamiques"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--generator",
        type=str,
        help="Clé du générateur (ex: SIMPLIFICATION_FRACTIONS_V1)"
    )
    group.add_argument(
        "--chapter-code",
        type=str,
        help="Code du chapitre (ex: 6E_AA_TEST)"
    )
    
    parser.add_argument(
        "--enonce-template",
        type=str,
        help="Template énoncé (requis si --generator)"
    )
    parser.add_argument(
        "--solution-template",
        type=str,
        help="Template solution (requis si --generator)"
    )
    parser.add_argument(
        "--exercise-id",
        type=int,
        help="ID de l'exercice (requis si --chapter-code)"
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        default="moyen",
        choices=["facile", "moyen", "difficile"],
        help="Difficulté pour la génération de test"
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Seed pour la génération (optionnel)"
    )
    
    args = parser.parse_args()
    
    if args.generator:
        # Validation depuis templates fournis
        if not args.enonce_template or not args.solution_template:
            parser.error("--enonce-template et --solution-template sont requis avec --generator")
        
        result = validate_placeholders(
            generator_key=args.generator,
            enonce_template=args.enonce_template,
            solution_template=args.solution_template,
            difficulty=args.difficulty,
            seed=args.seed
        )
        
        print_validation_result(result)
        
        sys.exit(0 if result["valid"] else 1)
    
    elif args.chapter_code:
        # Validation depuis DB
        if not args.exercise_id:
            parser.error("--exercise-id est requis avec --chapter-code")
        
        result = await validate_exercise_from_db(
            chapter_code=args.chapter_code,
            exercise_id=args.exercise_id
        )
        
        print_validation_result(result)
        
        sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    asyncio.run(main())

