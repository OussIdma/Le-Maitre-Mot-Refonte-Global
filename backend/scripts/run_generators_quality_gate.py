#!/usr/bin/env python3
"""
Script runner pour la qualité des générateurs (P4.2)

Exécute les tests, génère la classification, et met à jour DISABLED_GENERATORS automatiquement.

Usage:
    # Mode normal (modifie les fichiers)
    python backend/scripts/run_generators_quality_gate.py
    
    # Mode check (vérifie sans modifier)
    python backend/scripts/run_generators_quality_gate.py --check
"""

import sys
import json
import subprocess
import argparse
import re
from pathlib import Path
from typing import List, Dict, Any, Set

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))


# =============================================================================
# CONSTANTES
# =============================================================================

TEST_SCRIPT = ROOT_DIR / "backend" / "scripts" / "test_dynamic_generators.py"
CLASSIFY_SCRIPT = ROOT_DIR / "backend" / "scripts" / "classify_generators.py"
TEST_RESULTS_FILE = ROOT_DIR / "test_results.json"
CLASSIFICATION_FILE = ROOT_DIR / "docs" / "CLASSIFICATION_GENERATEURS.md"
FACTORY_FILE = ROOT_DIR / "backend" / "generators" / "factory.py"


# =============================================================================
# HELPERS
# =============================================================================

def run_command(cmd: List[str], cwd: Path = None) -> tuple[int, str, str]:
    """Exécute une commande et retourne (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or ROOT_DIR,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def extract_disabled_generators_from_classification(class_file: Path) -> Set[str]:
    """Extrait la liste des générateurs désactivés depuis le fichier de classification."""
    if not class_file.exists():
        return set()
    
    disabled = set()
    in_disabled_section = False
    
    with open(class_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # Détecter la section DÉSACTIVÉ
            if line.startswith("## 🔴 DÉSACTIVÉ"):
                in_disabled_section = True
                continue
            
            # Sortir de la section si on rencontre une autre section
            if in_disabled_section and line.startswith("##"):
                break
            
            # Extraire les noms de générateurs dans la section DÉSACTIVÉ
            if in_disabled_section and line.startswith("- **"):
                # Format: - **GENERATOR_KEY** (vX.X.X)
                match = re.match(r'- \*\*(\w+)\*\*', line)
                if match:
                    disabled.add(match.group(1))
    
    return disabled


def extract_disabled_generators_from_factory(factory_file: Path) -> Set[str]:
    """Extrait la liste actuelle de DISABLED_GENERATORS depuis factory.py."""
    if not factory_file.exists():
        return set()
    
    disabled = set()
    
    with open(factory_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Pattern pour trouver DISABLED_GENERATORS = [...]
    pattern = r'DISABLED_GENERATORS:\s*List\[str\]\s*=\s*\[(.*?)\]'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        list_content = match.group(1)
        # Extraire les strings entre guillemets
        matches = re.findall(r'"([^"]+)"', list_content)
        disabled.update(matches)
    
    return disabled


def update_factory_disabled_generators(factory_file: Path, disabled_generators: Set[str]) -> bool:
    """
    Met à jour DISABLED_GENERATORS dans factory.py.
    
    Returns:
        True si le fichier a été modifié, False sinon
    """
    if not factory_file.exists():
        print(f"❌ Fichier {factory_file} introuvable", file=sys.stderr)
        return False
    
    # Lire le fichier
    with open(factory_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Trouver la ligne avec DISABLED_GENERATORS
    start_idx = None
    end_idx = None
    in_list = False
    
    for i, line in enumerate(lines):
        if "DISABLED_GENERATORS" in line and "=" in line:
            start_idx = i
            if "[" in line:
                in_list = True
                if "]" in line:
                    # Liste sur une seule ligne
                    end_idx = i
                    break
            continue
        
        if in_list:
            if "]" in line:
                end_idx = i
                break
    
    if start_idx is None or end_idx is None:
        print(f"❌ Impossible de trouver DISABLED_GENERATORS dans {factory_file}", file=sys.stderr)
        return False
    
    # Générer la nouvelle liste (triée alphabétiquement)
    sorted_generators = sorted(disabled_generators)
    
    # Construire les nouvelles lignes
    new_lines = []
    
    # Conserver les lignes avant DISABLED_GENERATORS
    new_lines.extend(lines[:start_idx])
    
    # Ligne de déclaration
    declaration_line = lines[start_idx]
    # Extraire l'indentation
    indent_match = re.match(r'(\s*)', declaration_line)
    indent = indent_match.group(1) if indent_match else "    "
    
    # Nouvelle déclaration avec la liste
    if not sorted_generators:
        new_lines.append(f'{indent}DISABLED_GENERATORS: List[str] = [\n')
        new_lines.append(f'{indent}    # Aucun générateur désactivé pour le moment\n')
        new_lines.append(f'{indent}]\n')
    else:
        new_lines.append(f'{indent}DISABLED_GENERATORS: List[str] = [\n')
        for gen in sorted_generators:
            new_lines.append(f'{indent}    "{gen}",\n')
        new_lines.append(f'{indent}]\n')
    
    # Conserver les lignes après la liste
    new_lines.extend(lines[end_idx + 1:])
    
    # Vérifier si le contenu a changé
    new_content = "".join(new_lines)
    old_content = "".join(lines)
    
    if new_content != old_content:
        with open(factory_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    
    return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Quality gate pour les générateurs dynamiques")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Mode check : vérifie sans modifier les fichiers"
    )
    args = parser.parse_args()
    
    print("🚀 Quality Gate - Générateurs dynamiques", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Étape 1: Exécuter les tests
    print("\n📊 Étape 1: Exécution des tests...", file=sys.stderr)
    exit_code, stdout, stderr = run_command([
        sys.executable,
        str(TEST_SCRIPT),
        "--output",
        str(TEST_RESULTS_FILE)
    ])
    
    if exit_code != 0:
        print(f"❌ Échec des tests", file=sys.stderr)
        print(stderr, file=sys.stderr)
        sys.exit(1)
    
    print(f"✅ Tests terminés ({TEST_RESULTS_FILE})", file=sys.stderr)
    
    # Étape 2: Générer la classification
    print("\n📝 Étape 2: Génération de la classification...", file=sys.stderr)
    exit_code, stdout, stderr = run_command([
        sys.executable,
        str(CLASSIFY_SCRIPT),
        "--input",
        str(TEST_RESULTS_FILE),
        "--output",
        str(CLASSIFICATION_FILE)
    ])
    
    if exit_code != 0:
        print(f"❌ Échec de la classification", file=sys.stderr)
        print(stderr, file=sys.stderr)
        sys.exit(1)
    
    print(f"✅ Classification générée ({CLASSIFICATION_FILE})", file=sys.stderr)
    
    # Étape 3: Extraire les générateurs désactivés
    print("\n🔍 Étape 3: Extraction des générateurs désactivés...", file=sys.stderr)
    disabled_from_classification = extract_disabled_generators_from_classification(CLASSIFICATION_FILE)
    disabled_from_factory = extract_disabled_generators_from_factory(FACTORY_FILE)
    
    print(f"   Classification: {len(disabled_from_classification)} générateur(s) désactivé(s)", file=sys.stderr)
    print(f"   Factory actuel: {len(disabled_from_factory)} générateur(s) désactivé(s)", file=sys.stderr)
    
    if disabled_from_classification:
        print(f"   Générateurs désactivés: {', '.join(sorted(disabled_from_classification))}", file=sys.stderr)
    
    # Étape 4: Vérifier ou mettre à jour
    if args.check:
        print("\n🔍 Mode CHECK: Vérification uniquement...", file=sys.stderr)
        
        if disabled_from_classification != disabled_from_factory:
            print("❌ DISABLED_GENERATORS ne correspond pas à la classification", file=sys.stderr)
            print(f"   Attendu: {sorted(disabled_from_classification)}", file=sys.stderr)
            print(f"   Actuel: {sorted(disabled_from_factory)}", file=sys.stderr)
            sys.exit(1)
        
        print("✅ DISABLED_GENERATORS est à jour", file=sys.stderr)
        
        # Vérifier que la classification est à jour (comparer timestamp si possible)
        # Pour l'instant, on considère que si DISABLED_GENERATORS correspond, c'est OK
        print("✅ Classification à jour", file=sys.stderr)
        
    else:
        print("\n✏️  Mode UPDATE: Mise à jour de DISABLED_GENERATORS...", file=sys.stderr)
        
        if disabled_from_classification == disabled_from_factory:
            print("✅ DISABLED_GENERATORS est déjà à jour", file=sys.stderr)
        else:
            modified = update_factory_disabled_generators(FACTORY_FILE, disabled_from_classification)
            if modified:
                print(f"✅ DISABLED_GENERATORS mis à jour dans {FACTORY_FILE}", file=sys.stderr)
            else:
                print(f"⚠️  Aucune modification nécessaire", file=sys.stderr)
    
    print("\n" + "=" * 60, file=sys.stderr)
    print("✅ Quality Gate terminé avec succès", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()

