"""
GABARIT LOADER - Le Maître Mot

Service de chargement et gestion des gabarits pré-générés.

ARCHITECTURE :
    - Charge les gabarits depuis les fichiers JSON
    - Fournit des gabarits aléatoires par style
    - Interface avec le cache_manager
    - Prépare les valeurs d'interpolation depuis les specs mathématiques
"""

import json
import random
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys
sys.path.insert(0, '/app/backend')
from models.math_models import MathExerciseSpec
from style_manager import StyleFormulation
from pedagogie_rules import ExerciseType

logger = logging.getLogger(__name__)


class GabaritLoader:
    """
    Gestionnaire de gabarits pré-générés.
    
    Responsabilités :
        - Charger les gabarits depuis les fichiers JSON
        - Sélectionner un gabarit aléatoire selon style et type
        - Préparer les valeurs d'interpolation depuis les specs
        - Interface avec le cache pour éviter la régénération
    """
    
    def __init__(self, gabarits_dir: str = "/app/backend/gabarits"):
        """
        Initialise le loader de gabarits.
        
        Args:
            gabarits_dir: Répertoire contenant les fichiers JSON de gabarits
        """
        self.gabarits_dir = Path(gabarits_dir)
        self._gabarits_cache: Dict[str, Dict] = {}
        
        # Charger tous les gabarits au démarrage
        self._load_all_gabarits()
    
    def _load_all_gabarits(self):
        """Charge tous les fichiers de gabarits JSON."""
        if not self.gabarits_dir.exists():
            logger.warning(f"Gabarits directory not found: {self.gabarits_dir}")
            return
        
        for json_file in self.gabarits_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Clé : "chapitre__type_exercice"
                    chapitre = data.get("chapitre", "").lower().replace(" ", "_").replace("é", "e").replace("è", "e")
                    type_ex = data.get("type_exercice", "")
                    key = f"{chapitre}__{type_ex}"
                    
                    self._gabarits_cache[key] = data
                    logger.info(f"✅ Loaded gabarits: {json_file.name} → {key}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to load gabarit file {json_file}: {e}")
        
        logger.info(f"📚 Total gabarit sets loaded: {len(self._gabarits_cache)}")
    
    def has_gabarit(self, chapitre: str, type_exercice: str) -> bool:
        """
        Vérifie si des gabarits existent pour un chapitre/type donné.
        
        Args:
            chapitre: Nom du chapitre (ex: "Symétrie axiale")
            type_exercice: Type d'exercice (ex: "trouver_valeur")
        
        Returns:
            True si des gabarits existent
        """
        key = self._build_key(chapitre, type_exercice)
        return key in self._gabarits_cache
    
    def get_random_gabarit(
        self, 
        chapitre: str, 
        type_exercice: str, 
        style: StyleFormulation
    ) -> Optional[str]:
        """
        Retourne un gabarit aléatoire pour un chapitre, type et style donnés.
        
        Args:
            chapitre: Nom du chapitre
            type_exercice: Type d'exercice
            style: Style de formulation souhaité
        
        Returns:
            Un template de gabarit avec placeholders, ou None si non trouvé
        """
        key = self._build_key(chapitre, type_exercice)
        
        if key not in self._gabarits_cache:
            logger.warning(f"No gabarits found for: {key}")
            return None
        
        gabarit_data = self._gabarits_cache[key]
        gabarits_list = gabarit_data.get("gabarits", [])
        
        # Trouver les gabarits pour ce style
        style_gabarits = None
        for g in gabarits_list:
            if g.get("style") == style.value:
                style_gabarits = g.get("templates", [])
                break
        
        if not style_gabarits:
            logger.warning(f"No templates found for style {style.value} in {key}")
            return None
        
        # Retourner un template aléatoire
        return random.choice(style_gabarits)
    
    def prepare_interpolation_values(self, spec: MathExerciseSpec) -> Dict[str, Any]:
        """
        Prépare les valeurs d'interpolation depuis une spec mathématique.
        
        Cette fonction extrait les valeurs concrètes de la spec et les mappe
        aux placeholders attendus par les gabarits.
        
        Args:
            spec: Spécification mathématique de l'exercice
        
        Returns:
            Dict des valeurs pour interpolation
        
        Examples:
            >>> spec = MathExerciseSpec(
            ...     chapitre="Symétrie axiale",
            ...     parametres={
            ...         "point_initial": "M",
            ...         "point_symetrique": "M'",
            ...         "coord_initial": (3, 5),
            ...         "axe_type": "vertical",
            ...         "axe_value": 7
            ...     }
            ... )
            >>> prepare_interpolation_values(spec)
            {
                "pointA": "M",
                "pointB": "M'",
                "coordA_x": 3,
                "coordA_y": 5,
                "axeDesc": "l'axe vertical x = 7"
            }
        """
        params = spec.parametres
        values = {}
        
        # Détecter le type de chapitre
        chapitre_lower = spec.chapitre.lower()
        
        if "symétrie axiale" in chapitre_lower or "symetrie axiale" in chapitre_lower:
            values = self._prepare_symetrie_axiale_values(params, spec.type_exercice.value)
        
        elif "symétrie centrale" in chapitre_lower or "symetrie centrale" in chapitre_lower:
            values = self._prepare_symetrie_centrale_values(params, spec.type_exercice.value)
        
        elif "pythagore" in chapitre_lower or "théorème de pythagore" in chapitre_lower:
            values = self._prepare_pythagore_values(params)
        
        elif "proportionnalité" in chapitre_lower or "proportionnalite" in chapitre_lower:
            values = self._prepare_proportionnalite_values(params)
        
        elif "périmètre" in chapitre_lower or "aire" in chapitre_lower or "perimetre" in chapitre_lower:
            values = self._prepare_perimetre_aire_values(params)
        
        else:
            logger.warning(f"Unknown chapter for interpolation: {spec.chapitre}")
        
        return values
    
    def _prepare_symetrie_axiale_values(self, params: Dict[str, Any], type_ex: str) -> Dict[str, Any]:
        """Prépare les valeurs pour symétrie axiale."""
        values = {}
        
        # Points - mapper depuis les noms générés (point_original, point_image, etc.)
        values["pointA"] = params.get("point_original", params.get("point_a", params.get("point_initial", "M")))
        values["pointB"] = params.get("point_image", params.get("point_b", params.get("point_symetrique", "M'")))
        
        # Coordonnées du point initial - plusieurs formats possibles
        # Format 1: point_original_coords = {"x": val, "y": val}
        # Format 2: coords_a = {"x": val, "y": val}
        # Format 3: coord_initial = (x, y)
        coord_data = params.get("point_original_coords", params.get("coords_a", params.get("point_a_coords", params.get("coord_initial"))))
        
        if isinstance(coord_data, dict):
            values["coordA_x"] = coord_data.get("x", 0)
            values["coordA_y"] = coord_data.get("y", 0)
        elif isinstance(coord_data, (list, tuple)) and len(coord_data) >= 2:
            values["coordA_x"] = coord_data[0]
            values["coordA_y"] = coord_data[1]
        else:
            values["coordA_x"] = 0
            values["coordA_y"] = 0
        
        # Pour verifier_propriete, ajouter les coordonnées du second point
        if type_ex == "verifier_propriete" or params.get("type") == "verifier_symetrie":
            coord_second = params.get("point_image_coords", params.get("coords_b", params.get("point_b_coords", params.get("coord_second"))))
            
            if isinstance(coord_second, dict):
                values["coordB_x"] = coord_second.get("x", 0)
                values["coordB_y"] = coord_second.get("y", 0)
            elif isinstance(coord_second, (list, tuple)) and len(coord_second) >= 2:
                values["coordB_x"] = coord_second[0]
                values["coordB_y"] = coord_second[1]
            else:
                values["coordB_x"] = 0
                values["coordB_y"] = 0
        
        # Description de l'axe - utiliser axe_description si disponible, sinon construire
        axe_desc = params.get("axe_description")
        if axe_desc:
            values["axeDesc"] = axe_desc
        else:
            axe_type = params.get("axe_type", "vertical")
            axe_value = params.get("axe_value", params.get("axe_position", 0))
            
            if axe_type == "vertical":
                values["axeDesc"] = f"l'axe vertical x = {axe_value}"
            elif axe_type == "horizontal":
                values["axeDesc"] = f"l'axe horizontal y = {axe_value}"
            elif axe_type == "ox":
                values["axeDesc"] = "l'axe des abscisses"
            elif axe_type == "oy":
                values["axeDesc"] = "l'axe des ordonnées"
            elif axe_type == "oblique":
                values["axeDesc"] = "la première bissectrice (y = x)"
            else:
                values["axeDesc"] = f"l'axe {axe_type}"
        
        return values
    
    def _prepare_symetrie_centrale_values(self, params: Dict[str, Any], type_ex: str) -> Dict[str, Any]:
        """Prépare les valeurs pour symétrie centrale."""
        values = {}
        
        # Points
        values["pointA"] = params.get("point_initial", "M")
        values["pointB"] = params.get("point_symetrique", "M'")
        values["pointO"] = params.get("centre_symetrie", "O")
        
        # Coordonnées du point initial
        coord_initial = params.get("coord_initial", (0, 0))
        if isinstance(coord_initial, (list, tuple)) and len(coord_initial) >= 2:
            values["coordA_x"] = coord_initial[0]
            values["coordA_y"] = coord_initial[1]
        else:
            values["coordA_x"] = 0
            values["coordA_y"] = 0
        
        # Pour verifier_propriete, ajouter les coordonnées du second point
        if type_ex == "verifier_propriete":
            coord_second = params.get("coord_second", (0, 0))
            if isinstance(coord_second, (list, tuple)) and len(coord_second) >= 2:
                values["coordB_x"] = coord_second[0]
                values["coordB_y"] = coord_second[1]
            else:
                values["coordB_x"] = 0
                values["coordB_y"] = 0
        
        # Coordonnées du centre
        coord_centre = params.get("coord_centre", (0, 0))
        if isinstance(coord_centre, (list, tuple)) and len(coord_centre) >= 2:
            values["centreX"] = coord_centre[0]
            values["centreY"] = coord_centre[1]
        else:
            values["centreX"] = 0
            values["centreY"] = 0
        
        return values
    
    def _prepare_pythagore_values(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prépare les valeurs pour théorème de Pythagore."""
        values = {}
        
        # Triangle et angle droit
        values["triangle"] = params.get("triangle", "ABC")
        values["angleD"] = params.get("angle_droit", "B")
        
        # Longueurs données
        longueurs_donnees = params.get("longueurs_donnees", {})
        
        # Extraire les deux côtés connus
        cotes = list(longueurs_donnees.keys())
        if len(cotes) >= 2:
            values["cote1"] = cotes[0]
            values["long1"] = longueurs_donnees[cotes[0]]
            values["cote2"] = cotes[1]
            values["long2"] = longueurs_donnees[cotes[1]]
        else:
            # Fallback
            values["cote1"] = "AB"
            values["long1"] = 3
            values["cote2"] = "BC"
            values["long2"] = 4
        
        # Côté à calculer
        values["coteACalculer"] = params.get("longueur_a_calculer", "AC")
        
        return values
    
    def _prepare_proportionnalite_values(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prépare les valeurs pour proportionnalité."""
        values = {}
        
        # Valeurs données et résultats
        valeurs_donnees = params.get("valeurs_donnees", [3, 6])
        resultats_donnes = params.get("resultats_donnes", [9, 18])
        
        values["val1"] = valeurs_donnees[0] if len(valeurs_donnees) > 0 else 3
        values["val2"] = valeurs_donnees[1] if len(valeurs_donnees) > 1 else 6
        values["res1"] = resultats_donnes[0] if len(resultats_donnes) > 0 else 9
        values["res2"] = resultats_donnes[1] if len(resultats_donnes) > 1 else 18
        
        # Valeur à trouver
        values["val3"] = params.get("valeur_a_trouver", 9)
        
        return values
    
    def _prepare_perimetre_aire_values(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prépare les valeurs pour périmètres et aires."""
        values = {}
        
        # Type de figure
        figure_type = params.get("figure", "rectangle")
        
        # Mapping des noms de figures
        figure_names = {
            "rectangle": "rectangle",
            "carre": "carré",
            "cercle": "cercle",
            "triangle": "triangle"
        }
        values["figureType"] = figure_names.get(figure_type, figure_type)
        
        # Dimensions selon le type de figure
        if figure_type == "rectangle":
            values["dim1Nom"] = "longueur"
            values["dim1Val"] = params.get("longueur", 10)
            values["dim2Nom"] = "largeur"
            values["dim2Val"] = params.get("largeur", 5)
            values["unite"] = "cm"
            values["quoiCalculer"] = "périmètre"  # ou "aire" selon le contexte
            
        elif figure_type == "carre":
            values["dim1Nom"] = "côté"
            values["dim1Val"] = params.get("cote", 5)
            values["dim2Nom"] = "côté"
            values["dim2Val"] = params.get("cote", 5)
            values["unite"] = "cm"
            values["quoiCalculer"] = "périmètre"
            
        elif figure_type == "cercle":
            values["dim1Nom"] = "rayon"
            values["dim1Val"] = params.get("rayon", 5)
            values["dim2Nom"] = "diamètre"
            values["dim2Val"] = params.get("rayon", 5) * 2
            values["unite"] = "cm"
            values["quoiCalculer"] = "périmètre"
            
        else:
            # Fallback générique
            values["dim1Nom"] = "dimension1"
            values["dim1Val"] = 10
            values["dim2Nom"] = "dimension2"
            values["dim2Val"] = 5
            values["unite"] = "cm"
            values["quoiCalculer"] = "mesure"
        
        return values
    
    def _build_key(self, chapitre: str, type_exercice: str) -> str:
        """Construit la clé de recherche pour les gabarits."""
        chapitre_clean = chapitre.lower().replace(" ", "_").replace("é", "e").replace("è", "e")
        return f"{chapitre_clean}__{type_exercice}"


# Instance globale
gabarit_loader = GabaritLoader()


# Export des symboles publics
__all__ = [
    "GabaritLoader",
    "gabarit_loader"
]
