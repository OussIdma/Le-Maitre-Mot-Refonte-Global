"""
Générateur THALES_V1 - Agrandissements et Réductions (Proportionnalité 6e)
==========================================================================

Ce générateur produit des exercices sur les agrandissements et réductions 
de figures géométriques, utilisant la proportionnalité.

Niveau: 6e
Type: Dynamique (templates avec variables)
Seed: Utilisé pour reproductibilité

Sorties:
- variables: dict avec toutes les valeurs pour les templates
- results: dict avec les valeurs calculées
- svg_params: dict pour la génération SVG
- figure_svg_enonce: SVG de la figure initiale
- figure_svg_solution: SVG de la figure agrandie/réduite
"""

import random
import math
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ThalesV1Config:
    """Configuration du générateur THALES_V1."""
    # Coefficients possibles selon la difficulté
    COEFFICIENTS_FACILE = [2, 3, 4, 5]  # Entiers simples
    COEFFICIENTS_MOYEN = [1.5, 2, 2.5, 3, 4]  # Quelques décimaux simples
    COEFFICIENTS_DIFFICILE = [1.25, 1.5, 1.75, 2.25, 2.5, 3.5]  # Décimaux variés
    
    # Longueurs de base (en cm)
    BASE_LENGTHS = list(range(2, 8))  # 2 à 7 cm
    
    # Types de figures
    FIGURE_TYPES = ["rectangle", "triangle", "carre"]


class ThalesV1Generator:
    """Générateur d'exercices sur les agrandissements/réductions."""
    
    def __init__(self, seed: Optional[int] = None, difficulty: str = "moyen"):
        self.seed = seed
        self.difficulty = difficulty.lower()
        
        if seed is not None:
            random.seed(seed)
    
    def generate(self) -> Dict[str, Any]:
        """
        Génère un exercice complet avec variables, résultats et SVG.
        
        Returns:
            Dict avec:
            - variables: dict pour les templates
            - results: dict avec les calculs
            - svg_params: dict pour les SVG
            - figure_svg_enonce: SVG de la figure initiale
            - figure_svg_solution: SVG de la figure finale
        """
        # Sélectionner le type de figure
        figure_type = random.choice(ThalesV1Config.FIGURE_TYPES)
        
        # Sélectionner le coefficient selon la difficulté
        coefficient = self._select_coefficient()
        
        # Déterminer si c'est un agrandissement ou une réduction
        is_agrandissement = coefficient > 1
        
        # Générer les dimensions de base
        if figure_type == "carre":
            base_dim = self._generate_square_dimensions()
        elif figure_type == "rectangle":
            base_dim = self._generate_rectangle_dimensions()
        else:  # triangle
            base_dim = self._generate_triangle_dimensions()
        
        # Calculer les dimensions finales
        final_dim = self._calculate_final_dimensions(base_dim, coefficient)
        
        # Construire les variables pour les templates
        variables = self._build_variables(
            figure_type, base_dim, final_dim, coefficient, is_agrandissement
        )
        
        # Calculer les résultats
        results = self._calculate_results(base_dim, final_dim, coefficient)
        
        # Paramètres pour les SVG
        svg_params = {
            "figure_type": figure_type,
            "base_dimensions": base_dim,
            "final_dimensions": final_dim,
            "coefficient": coefficient,
            "is_agrandissement": is_agrandissement
        }
        
        # Générer les SVG
        svg_enonce = self._generate_svg_enonce(figure_type, base_dim)
        svg_solution = self._generate_svg_solution(figure_type, base_dim, final_dim, is_agrandissement)
        
        return {
            "variables": variables,
            "results": results,
            "svg_params": svg_params,
            "figure_svg_enonce": svg_enonce,
            "figure_svg_solution": svg_solution
        }
    
    def _select_coefficient(self) -> float:
        """Sélectionne un coefficient selon la difficulté."""
        if self.difficulty == "facile":
            return random.choice(ThalesV1Config.COEFFICIENTS_FACILE)
        elif self.difficulty == "difficile":
            return random.choice(ThalesV1Config.COEFFICIENTS_DIFFICILE)
        else:  # moyen
            return random.choice(ThalesV1Config.COEFFICIENTS_MOYEN)
    
    def _generate_square_dimensions(self) -> Dict[str, float]:
        """Génère les dimensions d'un carré."""
        cote = random.choice(ThalesV1Config.BASE_LENGTHS)
        return {"cote": cote, "type": "carre"}
    
    def _generate_rectangle_dimensions(self) -> Dict[str, float]:
        """Génère les dimensions d'un rectangle."""
        longueur = random.choice(ThalesV1Config.BASE_LENGTHS)
        smaller_values = [l for l in ThalesV1Config.BASE_LENGTHS if l < longueur]
        if smaller_values:
            largeur = random.choice(smaller_values)
        else:
            largeur = max(1, longueur - 1)  # Fallback: au moins 1 cm de moins
        return {"longueur": longueur, "largeur": largeur, "type": "rectangle"}
    
    def _generate_triangle_dimensions(self) -> Dict[str, float]:
        """Génère les dimensions d'un triangle rectangle."""
        base = random.choice(ThalesV1Config.BASE_LENGTHS)
        other_values = [h for h in ThalesV1Config.BASE_LENGTHS if h != base]
        if other_values:
            hauteur = random.choice(other_values)
        else:
            hauteur = base + 1  # Fallback
        return {"base": base, "hauteur": hauteur, "type": "triangle"}
    
    def _calculate_final_dimensions(self, base_dim: Dict, coefficient: float) -> Dict[str, float]:
        """Calcule les dimensions après transformation."""
        final = {"type": base_dim["type"]}
        
        for key, value in base_dim.items():
            if key != "type" and isinstance(value, (int, float)):
                final[key] = round(value * coefficient, 2)
        
        return final
    
    def _build_variables(
        self, figure_type: str, base_dim: Dict, final_dim: Dict, 
        coefficient: float, is_agrandissement: bool
    ) -> Dict[str, Any]:
        """Construit le dictionnaire de variables pour les templates."""
        
        # Formater le coefficient
        coef_str = str(coefficient) if coefficient != int(coefficient) else str(int(coefficient))
        
        variables = {
            "figure_type": figure_type,
            "figure_type_article": self._get_article(figure_type),
            "coefficient": coefficient,
            "coefficient_str": coef_str,
            "transformation": "agrandissement" if is_agrandissement else "réduction",
            "transformation_verbe": "agrandi" if is_agrandissement else "réduit",
            "facteur": f"× {coef_str}" if is_agrandissement else f"÷ {coef_str}",
        }
        
        # Ajouter les dimensions selon le type
        if figure_type == "carre":
            variables.update({
                "cote_initial": base_dim["cote"],
                "cote_final": final_dim["cote"],
                "dimension_nom": "côté",
            })
        elif figure_type == "rectangle":
            variables.update({
                "longueur_initiale": base_dim["longueur"],
                "largeur_initiale": base_dim["largeur"],
                "longueur_finale": final_dim["longueur"],
                "largeur_finale": final_dim["largeur"],
                "dimension_nom": "longueur et largeur",
            })
        else:  # triangle
            variables.update({
                "base_initiale": base_dim["base"],
                "hauteur_initiale": base_dim["hauteur"],
                "base_finale": final_dim["base"],
                "hauteur_finale": final_dim["hauteur"],
                "dimension_nom": "base et hauteur",
            })
        
        return variables
    
    def _calculate_results(self, base_dim: Dict, final_dim: Dict, coefficient: float) -> Dict[str, Any]:
        """Calcule les résultats (aires, périmètres, etc.)."""
        results = {}
        
        figure_type = base_dim["type"]
        
        if figure_type == "carre":
            results["aire_initiale"] = base_dim["cote"] ** 2
            results["aire_finale"] = final_dim["cote"] ** 2
            results["perimetre_initial"] = 4 * base_dim["cote"]
            results["perimetre_final"] = 4 * final_dim["cote"]
        
        elif figure_type == "rectangle":
            results["aire_initiale"] = base_dim["longueur"] * base_dim["largeur"]
            results["aire_finale"] = final_dim["longueur"] * final_dim["largeur"]
            results["perimetre_initial"] = 2 * (base_dim["longueur"] + base_dim["largeur"])
            results["perimetre_final"] = 2 * (final_dim["longueur"] + final_dim["largeur"])
        
        else:  # triangle
            results["aire_initiale"] = (base_dim["base"] * base_dim["hauteur"]) / 2
            results["aire_finale"] = (final_dim["base"] * final_dim["hauteur"]) / 2
            # Périmètre approximatif pour triangle rectangle
            hypo_init = math.sqrt(base_dim["base"]**2 + base_dim["hauteur"]**2)
            hypo_final = math.sqrt(final_dim["base"]**2 + final_dim["hauteur"]**2)
            results["perimetre_initial"] = round(base_dim["base"] + base_dim["hauteur"] + hypo_init, 2)
            results["perimetre_final"] = round(final_dim["base"] + final_dim["hauteur"] + hypo_final, 2)
        
        # Rapport des aires
        results["rapport_aires"] = coefficient ** 2
        
        return results
    
    def _get_article(self, figure_type: str) -> str:
        """Retourne l'article approprié pour le type de figure."""
        if figure_type == "carre":
            return "un carré"
        elif figure_type == "rectangle":
            return "un rectangle"
        else:
            return "un triangle"
    
    def _generate_svg_enonce(self, figure_type: str, dimensions: Dict) -> str:
        """Génère le SVG de la figure initiale."""
        
        scale = 30  # Pixels par cm
        padding = 20
        
        if figure_type == "carre":
            cote = dimensions["cote"]
            width = cote * scale + 2 * padding
            height = cote * scale + 2 * padding + 30  # Extra pour le label
            
            return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <rect x="{padding}" y="{padding}" width="{cote * scale}" height="{cote * scale}" 
        fill="#e3f2fd" stroke="#1976d2" stroke-width="2"/>
  <text x="{padding + cote * scale / 2}" y="{padding + cote * scale + 20}" 
        text-anchor="middle" font-size="14" fill="#1976d2">{cote} cm</text>
</svg>'''
        
        elif figure_type == "rectangle":
            longueur = dimensions["longueur"]
            largeur = dimensions["largeur"]
            width = longueur * scale + 2 * padding
            height = largeur * scale + 2 * padding + 30
            
            return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <rect x="{padding}" y="{padding}" width="{longueur * scale}" height="{largeur * scale}" 
        fill="#e8f5e9" stroke="#388e3c" stroke-width="2"/>
  <text x="{padding + longueur * scale / 2}" y="{padding + largeur * scale + 20}" 
        text-anchor="middle" font-size="14" fill="#388e3c">{longueur} cm</text>
  <text x="{padding - 5}" y="{padding + largeur * scale / 2}" 
        text-anchor="end" font-size="14" fill="#388e3c">{largeur} cm</text>
</svg>'''
        
        else:  # triangle
            base = dimensions["base"]
            hauteur = dimensions["hauteur"]
            width = base * scale + 2 * padding
            height = hauteur * scale + 2 * padding + 30
            
            # Triangle rectangle
            points = f"{padding},{padding + hauteur * scale} {padding + base * scale},{padding + hauteur * scale} {padding},{padding}"
            
            return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <polygon points="{points}" fill="#fff3e0" stroke="#f57c00" stroke-width="2"/>
  <text x="{padding + base * scale / 2}" y="{padding + hauteur * scale + 20}" 
        text-anchor="middle" font-size="14" fill="#f57c00">{base} cm</text>
  <text x="{padding - 5}" y="{padding + hauteur * scale / 2}" 
        text-anchor="end" font-size="14" fill="#f57c00">{hauteur} cm</text>
</svg>'''
    
    def _generate_svg_solution(
        self, figure_type: str, base_dim: Dict, final_dim: Dict, is_agrandissement: bool
    ) -> str:
        """Génère le SVG avec les deux figures (initiale et finale) superposées."""
        
        scale = 25  # Plus petit pour montrer les deux
        padding = 30
        gap = 80  # Espace entre les figures
        
        if figure_type == "carre":
            cote1 = base_dim["cote"]
            cote2 = final_dim["cote"]
            max_cote = max(cote1, cote2)
            
            width = cote1 * scale + gap + cote2 * scale + 2 * padding
            height = max_cote * scale + 2 * padding + 40
            
            x2 = padding + cote1 * scale + gap
            
            return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <!-- Figure initiale -->
  <rect x="{padding}" y="{padding}" width="{cote1 * scale}" height="{cote1 * scale}" 
        fill="#e3f2fd" stroke="#1976d2" stroke-width="2"/>
  <text x="{padding + cote1 * scale / 2}" y="{padding + cote1 * scale + 18}" 
        text-anchor="middle" font-size="12" fill="#1976d2">{cote1} cm</text>
  <text x="{padding + cote1 * scale / 2}" y="{padding - 8}" 
        text-anchor="middle" font-size="10" fill="#666">Initial</text>
  
  <!-- Flèche -->
  <line x1="{padding + cote1 * scale + 10}" y1="{padding + max_cote * scale / 2}" 
        x2="{x2 - 10}" y2="{padding + max_cote * scale / 2}" stroke="#666" stroke-width="2" marker-end="url(#arrow)"/>
  <defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
    <path d="M0,0 L0,6 L9,3 z" fill="#666"/></marker></defs>
  
  <!-- Figure finale -->
  <rect x="{x2}" y="{padding}" width="{cote2 * scale}" height="{cote2 * scale}" 
        fill="#ffebee" stroke="#c62828" stroke-width="2"/>
  <text x="{x2 + cote2 * scale / 2}" y="{padding + cote2 * scale + 18}" 
        text-anchor="middle" font-size="12" fill="#c62828">{cote2} cm</text>
  <text x="{x2 + cote2 * scale / 2}" y="{padding - 8}" 
        text-anchor="middle" font-size="10" fill="#666">{"Agrandi" if is_agrandissement else "Réduit"}</text>
</svg>'''
        
        elif figure_type == "rectangle":
            l1, L1 = base_dim["longueur"], base_dim["largeur"]
            l2, L2 = final_dim["longueur"], final_dim["largeur"]
            max_h = max(L1, L2)
            
            width = l1 * scale + gap + l2 * scale + 2 * padding
            height = max_h * scale + 2 * padding + 40
            
            x2 = padding + l1 * scale + gap
            
            return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <!-- Figure initiale -->
  <rect x="{padding}" y="{padding}" width="{l1 * scale}" height="{L1 * scale}" 
        fill="#e8f5e9" stroke="#388e3c" stroke-width="2"/>
  <text x="{padding + l1 * scale / 2}" y="{padding + L1 * scale + 15}" 
        text-anchor="middle" font-size="11" fill="#388e3c">{l1} × {L1} cm</text>
  <text x="{padding + l1 * scale / 2}" y="{padding - 8}" 
        text-anchor="middle" font-size="10" fill="#666">Initial</text>
  
  <!-- Flèche -->
  <line x1="{padding + l1 * scale + 10}" y1="{padding + max_h * scale / 2}" 
        x2="{x2 - 10}" y2="{padding + max_h * scale / 2}" stroke="#666" stroke-width="2" marker-end="url(#arrow)"/>
  <defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
    <path d="M0,0 L0,6 L9,3 z" fill="#666"/></marker></defs>
  
  <!-- Figure finale -->
  <rect x="{x2}" y="{padding}" width="{l2 * scale}" height="{L2 * scale}" 
        fill="#ffebee" stroke="#c62828" stroke-width="2"/>
  <text x="{x2 + l2 * scale / 2}" y="{padding + L2 * scale + 15}" 
        text-anchor="middle" font-size="11" fill="#c62828">{l2} × {L2} cm</text>
  <text x="{x2 + l2 * scale / 2}" y="{padding - 8}" 
        text-anchor="middle" font-size="10" fill="#666">{"Agrandi" if is_agrandissement else "Réduit"}</text>
</svg>'''
        
        else:  # triangle
            b1, h1 = base_dim["base"], base_dim["hauteur"]
            b2, h2 = final_dim["base"], final_dim["hauteur"]
            max_h = max(h1, h2)
            
            width = b1 * scale + gap + b2 * scale + 2 * padding
            height = max_h * scale + 2 * padding + 40
            
            x2 = padding + b1 * scale + gap
            
            points1 = f"{padding},{padding + h1 * scale} {padding + b1 * scale},{padding + h1 * scale} {padding},{padding}"
            points2 = f"{x2},{padding + h2 * scale} {x2 + b2 * scale},{padding + h2 * scale} {x2},{padding}"
            
            return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <!-- Figure initiale -->
  <polygon points="{points1}" fill="#fff3e0" stroke="#f57c00" stroke-width="2"/>
  <text x="{padding + b1 * scale / 2}" y="{padding + h1 * scale + 15}" 
        text-anchor="middle" font-size="11" fill="#f57c00">base {b1} cm</text>
  <text x="{padding + b1 * scale / 2}" y="{padding - 8}" 
        text-anchor="middle" font-size="10" fill="#666">Initial</text>
  
  <!-- Flèche -->
  <line x1="{padding + b1 * scale + 10}" y1="{padding + max_h * scale / 2}" 
        x2="{x2 - 10}" y2="{padding + max_h * scale / 2}" stroke="#666" stroke-width="2" marker-end="url(#arrow)"/>
  <defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
    <path d="M0,0 L0,6 L9,3 z" fill="#666"/></marker></defs>
  
  <!-- Figure finale -->
  <polygon points="{points2}" fill="#ffebee" stroke="#c62828" stroke-width="2"/>
  <text x="{x2 + b2 * scale / 2}" y="{padding + h2 * scale + 15}" 
        text-anchor="middle" font-size="11" fill="#c62828">base {b2} cm</text>
  <text x="{x2 + b2 * scale / 2}" y="{padding - 8}" 
        text-anchor="middle" font-size="10" fill="#666">{"Agrandi" if is_agrandissement else "Réduit"}</text>
</svg>'''


# ============================================================================
# REGISTRY DES GÉNÉRATEURS
# ============================================================================

GENERATORS_REGISTRY = {
    "THALES_V1": ThalesV1Generator
}


def get_generator(generator_key: str, seed: Optional[int] = None, difficulty: str = "moyen"):
    """
    Récupère un générateur par sa clé.
    
    Args:
        generator_key: Clé du générateur (ex: "THALES_V1")
        seed: Graine pour reproductibilité
        difficulty: Niveau de difficulté
    
    Returns:
        Instance du générateur
    """
    if generator_key not in GENERATORS_REGISTRY:
        raise ValueError(f"Générateur inconnu: {generator_key}. Disponibles: {list(GENERATORS_REGISTRY.keys())}")
    
    generator_class = GENERATORS_REGISTRY[generator_key]
    return generator_class(seed=seed, difficulty=difficulty)


def generate_dynamic_exercise(generator_key: str, seed: Optional[int] = None, difficulty: str = "moyen") -> Dict[str, Any]:
    """
    Génère un exercice dynamique complet.
    
    Args:
        generator_key: Clé du générateur (ex: "THALES_V1")
        seed: Graine pour reproductibilité
        difficulty: Niveau de difficulté
    
    Returns:
        Dict avec variables, results, svg_params et les SVG générés
    """
    generator = get_generator(generator_key, seed, difficulty)
    return generator.generate()


if __name__ == "__main__":
    # Test rapide
    result = generate_dynamic_exercise("THALES_V1", seed=42, difficulty="moyen")
    print("=== TEST THALES_V1 ===")
    print(f"Variables: {result['variables']}")
    print(f"Results: {result['results']}")
    print(f"SVG énoncé length: {len(result['figure_svg_enonce'])}")
    print(f"SVG solution length: {len(result['figure_svg_solution'])}")
