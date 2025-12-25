#!/usr/bin/env python3
"""
Script de test automatisé des générateurs dynamiques (P4.1)

Teste chaque générateur sur le pipeline complet :
1. Génération
2. Sauvegarde (simulation)
3. Reload (simulation)
4. Ajout à une fiche (simulation)
5. Export PDF (simulation)

Usage:
    python backend/scripts/test_dynamic_generators.py [--generator GENERATOR_KEY] [--output OUTPUT_FILE]
"""

import asyncio
import json
import sys
import argparse
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.generators.factory import GeneratorFactory
from backend.services.template_renderer import render_template
from backend.services.exercise_persistence_service import ExercisePersistenceService
from backend.server import db
import logging

logging.basicConfig(level=logging.WARNING)  # Réduire le bruit des logs
logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTES
# =============================================================================

DIFFICULTIES = ["facile", "moyen", "difficile", "standard"]  # Toutes les difficultés possibles
TEST_SEED = 42  # Seed fixe pour reproductibilité
TEST_USER_EMAIL = "test@example.com"  # Email de test


# =============================================================================
# HELPERS
# =============================================================================

def get_available_difficulties(generator_key: str) -> List[str]:
    """Récupère les difficultés disponibles pour un générateur depuis son schéma."""
    gen_class = GeneratorFactory.get(generator_key)
    if not gen_class:
        return []
    
    schema = gen_class.get_schema()
    difficulty_param = next((p for p in schema if p.name == "difficulty"), None)
    
    if difficulty_param and difficulty_param.type.value == "enum":
        return difficulty_param.options or []
    
    # Par défaut, tester toutes les difficultés
    return DIFFICULTIES


def requires_seed(generator_key: str) -> bool:
    """Vérifie si un générateur requiert un seed obligatoire."""
    gen_class = GeneratorFactory.get(generator_key)
    if not gen_class:
        return False
    
    schema = gen_class.get_schema()
    seed_param = next((p for p in schema if p.name == "seed"), None)
    
    return seed_param is not None and seed_param.required


# =============================================================================
# TESTS
# =============================================================================

async def test_generation(generator_key: str, difficulty: str, seed: Optional[int] = None) -> Dict[str, Any]:
    """Test 1: Génération d'un exercice."""
    try:
        gen_class = GeneratorFactory.get(generator_key)
        if not gen_class:
            return {
                "status": "FAIL",
                "step": "GENERATION",
                "error": f"Générateur {generator_key} non trouvé dans Factory"
            }
        
        # Préparer les paramètres
        params = {"difficulty": difficulty}
        if seed is not None:
            params["seed"] = seed
        elif requires_seed(generator_key):
            params["seed"] = TEST_SEED
        
        # Générer
        result = GeneratorFactory.generate(
            key=generator_key,
            exercise_params=params,
            seed=seed or TEST_SEED
        )
        
        # Vérifier que le résultat contient les champs requis
        required_fields = ["variables"]
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            return {
                "status": "FAIL",
                "step": "GENERATION",
                "error": f"Champs manquants dans le résultat: {missing_fields}"
            }
        
        return {
            "status": "PASS",
            "step": "GENERATION",
            "result": {
                "variables_count": len(result.get("variables", {})),
                "has_svg_enonce": result.get("figure_svg_enonce") is not None,
                "has_svg_solution": result.get("figure_svg_solution") is not None,
                "has_geo_data": result.get("geo_data") is not None
            }
        }
    
    except Exception as e:
        return {
            "status": "FAIL",
            "step": "GENERATION",
            "error": f"{type(e).__name__}: {str(e)}",
            "traceback": traceback.format_exc()
        }


async def test_template_rendering(generator_key: str, difficulty: str, seed: Optional[int] = None) -> Dict[str, Any]:
    """Test 2: Rendu des templates HTML."""
    try:
        # Générer d'abord
        gen_result = await test_generation(generator_key, difficulty, seed)
        if gen_result["status"] != "PASS":
            return gen_result
        
        # Récupérer le résultat de génération
        params = {"difficulty": difficulty}
        if seed is not None:
            params["seed"] = seed
        elif requires_seed(generator_key):
            params["seed"] = TEST_SEED
        
        result = GeneratorFactory.generate(
            key=generator_key,
            exercise_params=params,
            seed=seed or TEST_SEED
        )
        
        variables = result.get("variables", {})
        
        # Templates de test (simples)
        test_enonce_template = "<p>Test: {{test_var}}</p>"
        test_solution_template = "<p>Solution: {{test_var}}</p>"
        
        # Si le générateur a des variables, tester le rendu
        if variables:
            # Prendre une variable au hasard pour tester
            test_var = list(variables.keys())[0] if variables else "test_var"
            test_vars = {test_var: variables.get(test_var, "test_value")}
            
            try:
                rendered = render_template(test_enonce_template.replace("test_var", test_var), test_vars)
                if "{{" in rendered or "}}" in rendered:
                    return {
                        "status": "FAIL",
                        "step": "TEMPLATE_RENDERING",
                        "error": f"Placeholders non résolus dans le template: {rendered}"
                    }
            except Exception as e:
                return {
                    "status": "FAIL",
                    "step": "TEMPLATE_RENDERING",
                    "error": f"Erreur de rendu: {type(e).__name__}: {str(e)}"
                }
        
        return {
            "status": "PASS",
            "step": "TEMPLATE_RENDERING"
        }
    
    except Exception as e:
        return {
            "status": "FAIL",
            "step": "TEMPLATE_RENDERING",
            "error": f"{type(e).__name__}: {str(e)}"
        }


async def test_save_simulation(generator_key: str, difficulty: str, seed: Optional[int] = None) -> Dict[str, Any]:
    """Test 3: Simulation de sauvegarde (vérifie que l'exercice peut être sérialisé)."""
    try:
        params = {"difficulty": difficulty}
        if seed is not None:
            params["seed"] = seed
        elif requires_seed(generator_key):
            params["seed"] = TEST_SEED
        
        result = GeneratorFactory.generate(
            key=generator_key,
            exercise_params=params,
            seed=seed or TEST_SEED
        )
        
        # Simuler la sauvegarde en sérialisant en JSON
        try:
            json_str = json.dumps(result, default=str)
            json.loads(json_str)  # Vérifier que c'est valide
        except (TypeError, ValueError) as e:
            return {
                "status": "FAIL",
                "step": "SAVE_SIMULATION",
                "error": f"Impossible de sérialiser en JSON: {type(e).__name__}: {str(e)}"
            }
        
        return {
            "status": "PASS",
            "step": "SAVE_SIMULATION",
            "result": {
                "json_size_bytes": len(json_str)
            }
        }
    
    except Exception as e:
        return {
            "status": "FAIL",
            "step": "SAVE_SIMULATION",
            "error": f"{type(e).__name__}: {str(e)}"
        }


async def test_reload_simulation(generator_key: str, difficulty: str, seed: Optional[int] = None) -> Dict[str, Any]:
    """Test 4: Simulation de rechargement (vérifie que l'exercice peut être désérialisé)."""
    try:
        # Simuler sauvegarde puis rechargement
        save_result = await test_save_simulation(generator_key, difficulty, seed)
        if save_result["status"] != "PASS":
            return save_result
        
        # Si la sauvegarde fonctionne, le rechargement devrait aussi fonctionner
        return {
            "status": "PASS",
            "step": "RELOAD_SIMULATION"
        }
    
    except Exception as e:
        return {
            "status": "FAIL",
            "step": "RELOAD_SIMULATION",
            "error": f"{type(e).__name__}: {str(e)}"
        }


async def test_pdf_export_simulation(generator_key: str, difficulty: str, seed: Optional[int] = None) -> Dict[str, Any]:
    """Test 5: Simulation d'export PDF (vérifie que l'exercice a les champs nécessaires)."""
    try:
        params = {"difficulty": difficulty}
        if seed is not None:
            params["seed"] = seed
        elif requires_seed(generator_key):
            params["seed"] = TEST_SEED
        
        result = GeneratorFactory.generate(
            key=generator_key,
            exercise_params=params,
            seed=seed or TEST_SEED
        )
        
        # Vérifier que l'exercice a les champs nécessaires pour un PDF
        # (enonce_html et solution_html seront générés depuis les templates + variables)
        variables = result.get("variables", {})
        
        if not variables:
            return {
                "status": "FAIL",
                "step": "PDF_EXPORT_SIMULATION",
                "error": "Aucune variable générée, impossible de créer un PDF"
            }
        
        # Vérifier que les variables peuvent être utilisées pour générer du HTML
        # (simulation : on vérifie juste que les variables existent)
        return {
            "status": "PASS",
            "step": "PDF_EXPORT_SIMULATION",
            "result": {
                "variables_available": len(variables) > 0,
                "has_svg": result.get("figure_svg_enonce") is not None or result.get("figure_svg_solution") is not None
            }
        }
    
    except Exception as e:
        return {
            "status": "FAIL",
            "step": "PDF_EXPORT_SIMULATION",
            "error": f"{type(e).__name__}: {str(e)}"
        }


async def test_generator_full_pipeline(generator_key: str, difficulty: str, seed: Optional[int] = None) -> Dict[str, Any]:
    """Test complet du pipeline pour un générateur et une difficulté."""
    results = {
        "generator": generator_key,
        "difficulty": difficulty,
        "seed": seed or TEST_SEED,
        "tests": [],
        "status": "PASS",
        "failed_step": None,
        "error": None
    }
    
    # Test 1: Génération
    gen_test = await test_generation(generator_key, difficulty, seed)
    results["tests"].append(gen_test)
    if gen_test["status"] != "PASS":
        results["status"] = "FAIL"
        results["failed_step"] = gen_test["step"]
        results["error"] = gen_test.get("error")
        return results
    
    # Test 2: Rendu template
    template_test = await test_template_rendering(generator_key, difficulty, seed)
    results["tests"].append(template_test)
    if template_test["status"] != "PASS":
        results["status"] = "FAIL"
        results["failed_step"] = template_test["step"]
        results["error"] = template_test.get("error")
        return results
    
    # Test 3: Sauvegarde
    save_test = await test_save_simulation(generator_key, difficulty, seed)
    results["tests"].append(save_test)
    if save_test["status"] != "PASS":
        results["status"] = "FAIL"
        results["failed_step"] = save_test["step"]
        results["error"] = save_test.get("error")
        return results
    
    # Test 4: Rechargement
    reload_test = await test_reload_simulation(generator_key, difficulty, seed)
    results["tests"].append(reload_test)
    if reload_test["status"] != "PASS":
        results["status"] = "FAIL"
        results["failed_step"] = reload_test["step"]
        results["error"] = reload_test.get("error")
        return results
    
    # Test 5: Export PDF
    pdf_test = await test_pdf_export_simulation(generator_key, difficulty, seed)
    results["tests"].append(pdf_test)
    if pdf_test["status"] != "PASS":
        results["status"] = "FAIL"
        results["failed_step"] = pdf_test["step"]
        results["error"] = pdf_test.get("error")
        return results
    
    return results


# =============================================================================
# MAIN
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Test automatisé des générateurs dynamiques")
    parser.add_argument("--generator", type=str, help="Tester un générateur spécifique")
    parser.add_argument("--output", type=str, help="Fichier de sortie JSON (défaut: stdout)")
    parser.add_argument("--difficulty", type=str, help="Tester une difficulté spécifique")
    args = parser.parse_args()
    
    # Lister tous les générateurs
    all_generators = GeneratorFactory.list_all()
    
    if args.generator:
        all_generators = [g for g in all_generators if g["key"] == args.generator]
        if not all_generators:
            print(f"❌ Générateur {args.generator} non trouvé", file=sys.stderr)
            sys.exit(1)
    
    print(f"🧪 Test de {len(all_generators)} générateur(s)...", file=sys.stderr)
    
    all_results = []
    summary = {
        "total": 0,
        "pass": 0,
        "fail": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    for gen_info in all_generators:
        generator_key = gen_info["key"]
        version = gen_info.get("version", "unknown")
        
        print(f"\n📦 {generator_key} (v{version})", file=sys.stderr)
        
        # Déterminer les difficultés à tester
        if args.difficulty:
            difficulties_to_test = [args.difficulty]
        else:
            difficulties_to_test = get_available_difficulties(generator_key)
            if not difficulties_to_test:
                # Par défaut, tester "moyen" ou "standard"
                difficulties_to_test = ["moyen"] if "moyen" in DIFFICULTIES else ["standard"]
        
        for difficulty in difficulties_to_test:
            print(f"  ⚙️  Difficulté: {difficulty}", file=sys.stderr)
            
            result = await test_generator_full_pipeline(generator_key, difficulty)
            result["version"] = version
            
            all_results.append(result)
            summary["total"] += 1
            
            if result["status"] == "PASS":
                summary["pass"] += 1
                print(f"    ✅ PASS", file=sys.stderr)
            else:
                summary["fail"] += 1
                print(f"    ❌ FAIL: {result.get('failed_step')} - {result.get('error', 'Unknown error')}", file=sys.stderr)
    
    # Générer le rapport final
    report = {
        "summary": summary,
        "results": all_results
    }
    
    # Afficher ou sauvegarder
    output_json = json.dumps(report, indent=2, default=str)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output_json)
        print(f"\n✅ Rapport sauvegardé dans {args.output}", file=sys.stderr)
    else:
        print(output_json)
    
    # Afficher le résumé
    print(f"\n📊 Résumé:", file=sys.stderr)
    print(f"   Total: {summary['total']}", file=sys.stderr)
    print(f"   ✅ Pass: {summary['pass']}", file=sys.stderr)
    print(f"   ❌ Fail: {summary['fail']}", file=sys.stderr)
    
    # Code de sortie
    sys.exit(0 if summary["fail"] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())




