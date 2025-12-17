"""
Générateur THALES_V2 - Adaptateur du générateur existant
========================================================

Version: 2.0.0 (Dynamic Factory v1)

Ce générateur adapte THALES_V1 existant pour le nouveau système Factory.
Il conserve la compatibilité arrière tout en ajoutant:
- Schema des paramètres
- Presets pédagogiques
- Validation des paramètres
"""

from typing import Dict, Any, List, Optional
from generators.base_generator import (
    BaseGenerator, 
    GeneratorMeta, 
    ParamSchema, 
    Preset,
    ParamType
)
from generators.factory import GeneratorFactory
from generators.thales_generator import ThalesV1Generator, ThalesV1Config


@GeneratorFactory.register
class ThalesV2Generator(BaseGenerator):
    """Générateur THALES adapté au nouveau système Factory."""
    
    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="THALES_V2",
            label="Agrandissements/Réductions",
            description="Exercices sur les transformations de figures (proportionnalité)",
            version="2.0.0",
            niveaux=["6e", "5e"],
            exercise_type="THALES",
            svg_mode="AUTO",
            supports_double_svg=True,
            pedagogical_tips="⚠️ Niveau conseillé: 6e. Erreur fréquente: confusion ×/÷ selon agrandissement ou réduction."
        )
    
    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        return [
            ParamSchema(
                name="figure_type",
                type=ParamType.ENUM,
                description="Type de figure géométrique",
                default="carre",
                options=ThalesV1Config.FIGURE_TYPES
            ),
            ParamSchema(
                name="difficulty",
                type=ParamType.ENUM,
                description="Niveau de difficulté",
                default="moyen",
                options=["facile", "moyen", "difficile"]
            ),
            ParamSchema(
                name="force_coefficient",
                type=ParamType.FLOAT,
                description="Forcer un coefficient spécifique (optionnel)",
                default=None,
                min=0.5,
                max=10
            ),
            ParamSchema(
                name="force_agrandissement",
                type=ParamType.BOOL,
                description="Forcer un agrandissement (True) ou réduction (False)",
                default=None
            )
        ]
    
    @classmethod
    def get_presets(cls) -> List[Preset]:
        return [
            Preset(
                key="6e_facile",
                label="6e Facile - Carré simple",
                description="Agrandissement d'un carré avec coefficient entier",
                niveau="6e",
                params={
                    "figure_type": "carre",
                    "difficulty": "facile",
                    "force_agrandissement": True
                }
            ),
            Preset(
                key="6e_moyen",
                label="6e Moyen - Figures variées",
                description="Transformations avec coefficients simples",
                niveau="6e",
                params={
                    "figure_type": "rectangle",
                    "difficulty": "moyen"
                }
            ),
            Preset(
                key="6e_difficile",
                label="6e Difficile - Triangles et décimaux",
                description="Triangles avec coefficients décimaux",
                niveau="6e",
                params={
                    "figure_type": "triangle",
                    "difficulty": "difficile"
                }
            ),
            Preset(
                key="5e_moyen",
                label="5e Moyen - Calcul d'aires",
                description="Focus sur le rapport des aires",
                niveau="5e",
                params={
                    "figure_type": "rectangle",
                    "difficulty": "moyen"
                }
            )
        ]
    
    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un exercice en utilisant le générateur THALES_V1 existant."""
        
        # Créer une instance du générateur legacy
        legacy_gen = ThalesV1Generator(
            seed=self._seed,
            difficulty=params.get("difficulty", "moyen")
        )
        
        # Forcer le type de figure si spécifié
        if params.get("figure_type"):
            # On override le random pour forcer le type
            original_choice = legacy_gen._rng.choice
            legacy_gen._rng.choice = lambda x: params["figure_type"] if x == ThalesV1Config.FIGURE_TYPES else original_choice(x)
        
        # Générer avec le système legacy
        result = legacy_gen.generate()
        
        # Adapter au nouveau format
        return {
            "variables": result["variables"],
            "geo_data": {
                "figure_type": result["variables"]["figure_type"],
                "base_dimensions": result["svg_params"]["base_dimensions"],
                "final_dimensions": result["svg_params"]["final_dimensions"],
                "coefficient": result["svg_params"]["coefficient"],
                "is_agrandissement": result["svg_params"]["is_agrandissement"]
            },
            "figure_svg_enonce": result["figure_svg_enonce"],
            "figure_svg_solution": result["figure_svg_solution"],
            "meta": {
                "exercise_type": "THALES",
                "svg_mode": "AUTO",
                "figure_type": result["variables"]["figure_type"],
                "coefficient": result["variables"]["coefficient"],
                "difficulty": params.get("difficulty", "moyen")
            },
            "results": result["results"]
        }


# Conserver la compatibilité avec l'ancien nom
THALES_V2_TEMPLATES = {
    "enonce": """<p><strong>{{transformation}} d'{{figure_type_article}} :</strong></p>
<p>On considère {{figure_type_article}} de côté <strong>{{cote_initial}} cm</strong>.</p>
<p>On effectue un <strong>{{transformation}}</strong> de coefficient <strong>{{coefficient_str}}</strong>.</p>
<p><em>Question :</em> Quelle est la mesure du côté de la figure obtenue ?</p>""",
    "solution": """<h4>Correction détaillée</h4>
<ol>
  <li><strong>Compréhension :</strong> On a {{figure_type_article}} qu'on {{transformation_verbe}}.</li>
  <li><strong>Méthode :</strong> Multiplier chaque dimension par le coefficient.</li>
  <li><strong>Calculs :</strong> {{cote_initial}} × {{coefficient_str}} = <strong>{{cote_final}} cm</strong></li>
  <li><strong>Conclusion :</strong> La figure mesure <strong>{{cote_final}} cm</strong>.</li>
</ol>"""
}
