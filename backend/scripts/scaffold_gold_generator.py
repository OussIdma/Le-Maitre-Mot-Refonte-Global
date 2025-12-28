#!/usr/bin/env python3
"""
Scaffold Gold Generator - Génère un template de générateur Gold
================================================================

Usage:
    python backend/scripts/scaffold_gold_generator.py MON_GENERATEUR_V1 "Mon générateur"

Génère:
    backend/generators/mon_generateur_v1.py
"""

import sys
import os

TEMPLATE = '''"""
Générateur {key} - {label}
{'=' * (len(f"Générateur {key} - {label}"))}

Version: 1.0.0

TODO: Décrire le générateur ici.
"""

from typing import Dict, Any, List
from backend.generators.base_generator import (
    BaseGenerator,
    GeneratorMeta,
    ParamSchema,
    Preset,
    ParamType,
)
from backend.generators.factory import GeneratorFactory


@GeneratorFactory.register
class {class_name}(BaseGenerator):
    """Générateur Gold: {label}."""

    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="{key}",
            label="{label}",
            description="TODO: description",
            version="1.0.0",
            niveaux=["6e"],
            exercise_type="TODO",
            svg_mode="NONE",
            supports_double_svg=False,
            is_dynamic=True,
        )

    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        return [
            ParamSchema(
                name="difficulty",
                type=ParamType.ENUM,
                description="Niveau de difficulté",
                default="moyen",
                options=["facile", "moyen", "difficile"]
            ),
        ]

    @classmethod
    def get_presets(cls) -> List[Preset]:
        return [
            Preset(
                key="6e_standard",
                label="6e Standard",
                description="Exercices niveau 6e",
                niveau="6e",
                params={{"difficulty": "moyen", "seed": 42}}
            ),
        ]

    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        difficulty = params.get("difficulty", "moyen")

        # TODO: Implémenter la génération
        variables = {{
            "enonce": "TODO: énoncé",
            "reponse_finale": "TODO",
        }}

        return {{
            "variables": variables,
            "geo_data": None,
            "figure_svg_enonce": None,
            "figure_svg_solution": None,
            "meta": {{"generator_key": "{key}"}},
        }}
'''

def main():
    if len(sys.argv) < 3:
        print("Usage: python scaffold_gold_generator.py KEY \"Label\"")
        print("Ex:    python scaffold_gold_generator.py CALCUL_PERIMETRE_V1 \"Calcul de périmètre\"")
        sys.exit(1)

    key = sys.argv[1].upper()
    label = sys.argv[2]
    filename = key.lower() + ".py"
    class_name = "".join(w.title() for w in key.split("_")) + "Generator"

    content = TEMPLATE.format(key=key, label=label, class_name=class_name)
    filepath = os.path.join("backend", "generators", filename)

    if os.path.exists(filepath):
        print(f"ERREUR: {filepath} existe déjà!")
        sys.exit(1)

    with open(filepath, "w") as f:
        f.write(content)

    print(f"Créé: {filepath}")
    print("\nProchaines étapes:")
    print(f"  1. Implémenter generate() dans {filepath}")
    print(f"  2. Ajouter tests: backend/tests/invariants/test_{key.lower()}_invariants.py")
    print(f"  3. Ajouter à GOLD_GENERATORS dans test_generators_gold.py")
    print(f"  4. Importer dans factory.py: _register_all_generators()")

if __name__ == "__main__":
    main()
