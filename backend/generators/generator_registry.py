"""
Registre des générateurs dynamiques avec leurs schémas de variables
====================================================================

Ce module centralise:
- La définition des variables disponibles pour chaque générateur
- Les templates exemples pré-remplis
- Les métadonnées pour l'affichage admin (label, svg_modes, etc.)

Version: 1.0.0 (P0.2 - Variables explicites pour les profs)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class VariableSchema:
    """Schéma d'une variable disponible dans un générateur."""
    name: str
    type: str  # "string", "number", "boolean"
    description: str
    example: Any
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GeneratorSchema:
    """Schéma complet d'un générateur dynamique."""
    generator_key: str
    label: str
    description: str
    niveau: str
    variables: List[VariableSchema]
    svg_modes: List[str] = field(default_factory=lambda: ["AUTO", "CUSTOM"])
    supports_double_svg: bool = True
    difficulties: List[str] = field(default_factory=lambda: ["facile", "moyen", "difficile"])
    pedagogical_tips: Optional[str] = None
    template_example_enonce: str = ""
    template_example_solution: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "generator_key": self.generator_key,
            "label": self.label,
            "description": self.description,
            "niveau": self.niveau,
            "variables": [v.to_dict() for v in self.variables],
            "svg_modes": self.svg_modes,
            "supports_double_svg": self.supports_double_svg,
            "difficulties": self.difficulties,
            "pedagogical_tips": self.pedagogical_tips,
            "template_example_enonce": self.template_example_enonce,
            "template_example_solution": self.template_example_solution
        }


# =============================================================================
# SCHÉMAS DES GÉNÉRATEURS DISPONIBLES
# =============================================================================

THALES_V1_SCHEMA = GeneratorSchema(
    generator_key="THALES_V1",
    label="Agrandissements/Réductions",
    description="Génère des exercices sur les transformations de figures géométriques (proportionnalité)",
    niveau="6e",
    pedagogical_tips="⚠️ Niveau conseillé: 6e. Piège fréquent: confusion ×/÷ selon agrandissement ou réduction.",
    variables=[
        # Variables de base
        VariableSchema("figure_type", "string", "Type de figure (carre, rectangle, triangle)", "triangle"),
        VariableSchema("figure_type_article", "string", "Article + type (un carré, un rectangle...)", "un triangle"),
        VariableSchema("coefficient", "number", "Coefficient de transformation", 2),
        VariableSchema("coefficient_str", "string", "Coefficient formaté en string", "2"),
        VariableSchema("transformation", "string", "Type: agrandissement ou réduction", "agrandissement"),
        VariableSchema("transformation_verbe", "string", "Verbe: agrandi ou réduit", "agrandi"),
        VariableSchema("facteur", "string", "Facteur formaté (× 2 ou ÷ 2)", "× 2"),
        
        # Dimensions carré
        VariableSchema("cote_initial", "number", "Côté initial (carré)", 5),
        VariableSchema("cote_final", "number", "Côté final après transformation", 10),
        
        # Dimensions rectangle
        VariableSchema("longueur_initiale", "number", "Longueur initiale (rectangle)", 6),
        VariableSchema("largeur_initiale", "number", "Largeur initiale (rectangle)", 4),
        VariableSchema("longueur_finale", "number", "Longueur finale (rectangle)", 12),
        VariableSchema("largeur_finale", "number", "Largeur finale (rectangle)", 8),
        
        # Dimensions triangle
        VariableSchema("base_initiale", "number", "Base initiale (triangle)", 5),
        VariableSchema("hauteur_initiale", "number", "Hauteur initiale (triangle)", 4),
        VariableSchema("base_finale", "number", "Base finale (triangle)", 10),
        VariableSchema("hauteur_finale", "number", "Hauteur finale (triangle)", 8),
        
        # Résultats calculés
        VariableSchema("aire_initiale", "number", "Aire de la figure initiale", 20),
        VariableSchema("aire_finale", "number", "Aire de la figure finale", 80),
        VariableSchema("perimetre_initial", "number", "Périmètre initial", 20),
        VariableSchema("perimetre_final", "number", "Périmètre final", 40),
        VariableSchema("rapport_aires", "number", "Rapport des aires (coefficient²)", 4),
    ],
    svg_modes=["AUTO", "CUSTOM"],
    supports_double_svg=True,
    difficulties=["facile", "moyen", "difficile"],
    template_example_enonce="""<p><strong>Agrandissement d'{{figure_type_article}} :</strong></p>
<p>On considère {{figure_type_article}} de côté <strong>{{cote_initial}} cm</strong>.</p>
<p>On effectue un <strong>{{transformation}}</strong> de coefficient <strong>{{coefficient_str}}</strong>.</p>
<p><em>Question :</em> Quelle est la mesure du côté de la figure obtenue ?</p>""",
    template_example_solution="""<h4>Correction détaillée</h4>
<ol>
  <li><strong>Compréhension :</strong> On a {{figure_type_article}} qu'on {{transformation_verbe}}.</li>
  <li><strong>Méthode :</strong> Multiplier chaque dimension par le coefficient.</li>
  <li><strong>Calculs :</strong> {{cote_initial}} × {{coefficient_str}} = <strong>{{cote_final}} cm</strong></li>
  <li><strong>Conclusion :</strong> La figure mesure <strong>{{cote_final}} cm</strong>.</li>
</ol>"""
)


# =============================================================================
# REGISTRE PRINCIPAL
# =============================================================================

GENERATOR_SCHEMAS: Dict[str, GeneratorSchema] = {
    "THALES_V1": THALES_V1_SCHEMA,
}


def get_generator_schema(generator_key: str) -> Optional[GeneratorSchema]:
    """Récupère le schéma d'un générateur par sa clé."""
    return GENERATOR_SCHEMAS.get(generator_key)


def get_all_generator_keys() -> List[str]:
    """Liste toutes les clés de générateurs disponibles."""
    return list(GENERATOR_SCHEMAS.keys())


def get_all_schemas_summary() -> List[Dict[str, Any]]:
    """Retourne un résumé de tous les générateurs pour l'admin."""
    return [
        {
            "generator_key": schema.generator_key,
            "label": schema.label,
            "description": schema.description,
            "niveau": schema.niveau,
            "variable_count": len(schema.variables),
            "supports_double_svg": schema.supports_double_svg
        }
        for schema in GENERATOR_SCHEMAS.values()
    ]


if __name__ == "__main__":
    # Test rapide
    print("=== TEST GENERATOR REGISTRY ===")
    schema = get_generator_schema("THALES_V1")
    if schema:
        print(f"✅ {schema.label}")
        print(f"   Variables: {len(schema.variables)}")
        print(f"   SVG modes: {schema.svg_modes}")
        for v in schema.variables[:5]:
            print(f"   - {v.name} ({v.type}): {v.example}")
