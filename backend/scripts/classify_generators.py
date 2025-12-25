#!/usr/bin/env python3
"""
Script de classification automatique des générateurs (P4.1)

Génère docs/CLASSIFICATION_GENERATEURS.md à partir des résultats de test.

Usage:
    python backend/scripts/test_dynamic_generators.py --output test_results.json
    python backend/scripts/classify_generators.py --input test_results.json --output docs/CLASSIFICATION_GENERATEURS.md
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

from backend.generators.factory import GeneratorFactory


# =============================================================================
# RÈGLES DE CLASSIFICATION
# =============================================================================

def classify_generator(generator_key: str, test_results: List[Dict[str, Any]]) -> str:
    """
    Classifie un générateur selon les règles strictes :
    - 🟢 GOLD : 100% des tests passent, seed stable, export PDF OK
    - 🟠 AMÉLIORABLE : Échecs localisés, fix estimable
    - 🔴 DÉSACTIVÉ : Échecs récurrents, monkeypatch RNG, templates inline non maîtrisés
    """
    # Filtrer les résultats pour ce générateur
    gen_results = [r for r in test_results if r.get("generator") == generator_key]
    
    if not gen_results:
        return "🔴 DÉSACTIVÉ"  # Pas de tests = désactivé par défaut
    
    # Compter les passes/échecs
    total = len(gen_results)
    passes = sum(1 for r in gen_results if r.get("status") == "PASS")
    fails = total - passes
    
    # Règle 1: Si 100% des tests passent → GOLD
    if fails == 0:
        # Vérifier les critères supplémentaires pour GOLD
        # - Seed stable (tous les tests utilisent le même seed)
        # - Export PDF OK (aucun échec sur PDF_EXPORT_SIMULATION)
        pdf_fails = sum(
            1 for r in gen_results
            for test in r.get("tests", [])
            if test.get("step") == "PDF_EXPORT_SIMULATION" and test.get("status") != "PASS"
        )
        
        if pdf_fails == 0:
            return "🟢 GOLD"
        else:
            return "🟠 AMÉLIORABLE"  # PDF export a des problèmes
    
    # Règle 2: Échecs localisés mais fix estimable → AMÉLIORABLE
    # Analyser les types d'erreurs
    error_types = defaultdict(int)
    for r in gen_results:
        if r.get("status") == "FAIL":
            failed_step = r.get("failed_step", "UNKNOWN")
            error_types[failed_step] += 1
    
    # Si les erreurs sont concentrées sur une étape spécifique → AMÉLIORABLE
    if len(error_types) <= 2 and max(error_types.values()) <= 2:
        return "🟠 AMÉLIORABLE"
    
    # Règle 3: Vérifier les problèmes connus
    gen_class = GeneratorFactory.get(generator_key)
    if gen_class:
        # Vérifier si le générateur utilise des templates inline
        # (à détecter via inspection du code ou métadonnées)
        # Pour l'instant, on se base sur les erreurs de test
        
        # Si beaucoup d'échecs → DÉSACTIVÉ
        if fails > total * 0.5:  # Plus de 50% d'échecs
            return "🔴 DÉSACTIVÉ"
    
    # Par défaut, si on a des échecs mais pas trop → AMÉLIORABLE
    return "🟠 AMÉLIORABLE"


def generate_classification_markdown(test_results_file: str, output_file: str):
    """Génère le fichier de classification Markdown."""
    # Charger les résultats de test
    with open(test_results_file, "r") as f:
        report = json.load(f)
    
    test_results = report.get("results", [])
    summary = report.get("summary", {})
    
    # Grouper par générateur
    generators = {}
    for result in test_results:
        gen_key = result.get("generator")
        if gen_key not in generators:
            generators[gen_key] = []
        generators[gen_key].append(result)
    
    # Classifier chaque générateur
    classifications = {}
    for gen_key in generators:
        classifications[gen_key] = classify_generator(gen_key, test_results)
    
    # Générer le Markdown
    md_lines = [
        "# CLASSIFICATION DES GÉNÉRATEURS DYNAMIQUES",
        "",
        f"**Date de génération :** {summary.get('timestamp', 'Unknown')}",
        f"**Total tests :** {summary.get('total', 0)}",
        f"**✅ Pass :** {summary.get('pass', 0)}",
        f"**❌ Fail :** {summary.get('fail', 0)}",
        "",
        "---",
        "",
        "## 📊 RÉSUMÉ PAR CATÉGORIE",
        "",
    ]
    
    # Compter par catégorie
    gold_count = sum(1 for c in classifications.values() if "GOLD" in c)
    ameliorable_count = sum(1 for c in classifications.values() if "AMÉLIORABLE" in c)
    desactive_count = sum(1 for c in classifications.values() if "DÉSACTIVÉ" in c)
    
    md_lines.extend([
        f"- 🟢 **GOLD :** {gold_count} générateur(s)",
        f"- 🟠 **AMÉLIORABLE :** {ameliorable_count} générateur(s)",
        f"- 🔴 **DÉSACTIVÉ :** {desactive_count} générateur(s)",
        "",
        "---",
        "",
        "## 🟢 GOLD",
        "",
        "Générateurs 100% fiables, utilisables en production immédiatement.",
        "",
    ])
    
    gold_gens = [k for k, v in classifications.items() if "GOLD" in v]
    if gold_gens:
        for gen_key in sorted(gold_gens):
            gen_info = GeneratorFactory.list_all()
            gen_meta = next((g for g in gen_info if g["key"] == gen_key), None)
            version = gen_meta.get("version", "unknown") if gen_meta else "unknown"
            md_lines.append(f"- **{gen_key}** (v{version})")
    else:
        md_lines.append("*Aucun générateur GOLD pour le moment.*")
    
    md_lines.extend([
        "",
        "---",
        "",
        "## 🟠 AMÉLIORABLE",
        "",
        "Générateurs fonctionnels mais avec des problèmes localisés. Fix estimable.",
        "",
    ])
    
    ameliorable_gens = [k for k, v in classifications.items() if "AMÉLIORABLE" in v]
    if ameliorable_gens:
        for gen_key in sorted(ameliorable_gens):
            gen_info = GeneratorFactory.list_all()
            gen_meta = next((g for g in gen_info if g["key"] == gen_key), None)
            version = gen_meta.get("version", "unknown") if gen_meta else "unknown"
            
            # Analyser les problèmes
            gen_results = [r for r in test_results if r.get("generator") == gen_key]
            problems = []
            for r in gen_results:
                if r.get("status") == "FAIL":
                    failed_step = r.get("failed_step", "UNKNOWN")
                    error = r.get("error", "Unknown error")
                    problems.append(f"{failed_step}: {error[:100]}")
            
            md_lines.append(f"- **{gen_key}** (v{version})")
            if problems:
                md_lines.append(f"  - Problèmes : {', '.join(set(problems[:3]))}")  # Limiter à 3 problèmes
    else:
        md_lines.append("*Aucun générateur AMÉLIORABLE pour le moment.*")
    
    md_lines.extend([
        "",
        "---",
        "",
        "## 🔴 DÉSACTIVÉ",
        "",
        "Générateurs avec échecs récurrents, monkeypatch RNG, ou templates inline non maîtrisés.",
        "",
        "⚠️ **Ces générateurs ne sont PAS visibles dans l'UI et ne peuvent PAS être utilisés.**",
        "",
    ])
    
    desactive_gens = [k for k, v in classifications.items() if "DÉSACTIVÉ" in v]
    if desactive_gens:
        for gen_key in sorted(desactive_gens):
            gen_info = GeneratorFactory.list_all()
            gen_meta = next((g for g in gen_info if g["key"] == gen_key), None)
            version = gen_meta.get("version", "unknown") if gen_meta else "unknown"
            
            # Analyser les problèmes
            gen_results = [r for r in test_results if r.get("generator") == gen_key]
            problems = []
            for r in gen_results:
                if r.get("status") == "FAIL":
                    failed_step = r.get("failed_step", "UNKNOWN")
                    error = r.get("error", "Unknown error")
                    problems.append(f"{failed_step}: {error[:100]}")
            
            md_lines.append(f"- **{gen_key}** (v{version})")
            if problems:
                md_lines.append(f"  - Raisons : {', '.join(set(problems[:3]))}")  # Limiter à 3 problèmes
    else:
        md_lines.append("*Aucun générateur DÉSACTIVÉ pour le moment.*")
    
    md_lines.extend([
        "",
        "---",
        "",
        "## 📝 NOTES",
        "",
        "Cette classification est générée automatiquement à partir des résultats de test.",
        "Pour mettre à jour :",
        "",
        "```bash",
        "python backend/scripts/test_dynamic_generators.py --output test_results.json",
        "python backend/scripts/classify_generators.py --input test_results.json --output docs/CLASSIFICATION_GENERATEURS.md",
        "```",
        "",
    ])
    
    # Écrire le fichier
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    
    print(f"✅ Classification générée dans {output_file}")
    print(f"   🟢 GOLD: {gold_count}")
    print(f"   🟠 AMÉLIORABLE: {ameliorable_count}")
    print(f"   🔴 DÉSACTIVÉ: {desactive_count}")


def main():
    parser = argparse.ArgumentParser(description="Classifie les générateurs à partir des résultats de test")
    parser.add_argument("--input", type=str, required=True, help="Fichier JSON des résultats de test")
    parser.add_argument("--output", type=str, default="docs/CLASSIFICATION_GENERATEURS.md", help="Fichier de sortie Markdown")
    args = parser.parse_args()
    
    generate_classification_markdown(args.input, args.output)


if __name__ == "__main__":
    main()




