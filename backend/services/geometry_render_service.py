"""
Service de rendu SVG pour les figures géométriques
Convertit les objets GeometricFigure en images SVG affichables

RÈGLE PÉDAGOGIQUE UNIVERSELLE (appliquée à toutes les transformations géométriques) :
    - SUJET = données connues uniquement
    - CORRIGÉ = données connues + données à trouver

Ce service utilise le module central `pedagogie_rules` pour appliquer
les règles de manière uniforme à tous les types d'exercices.
"""

import logging
from typing import Dict, Any, Optional, List
from backend.models.math_models import GeometricFigure
from backend.geometry_svg_renderer import GeometrySVGRenderer
from backend.pedagogie_rules import determine_elements_to_hide_in_question as determine_hiding_rules

logger = logging.getLogger(__name__)


def determine_elements_to_hide_in_question(exercise_type: str, figure: GeometricFigure) -> Dict[str, Any]:
    """
    Wrapper pour utiliser le module central pedagogie_rules.
    
    Cette fonction adapte l'interface existante au nouveau système universel.
    """
    
    # Construire les métadonnées pour le module central
    metadata = {
        "points": figure.points if figure.points else [],
        "properties": figure.proprietes if figure.proprietes else [],
        "shapes": [],
        "is_geometry": True,
        "is_completion": "triangle" in (figure.proprietes if figure.proprietes else [])
    }
    
    # Appeler le module central
    hiding_rules = determine_hiding_rules(exercise_type, metadata)
    
    # Adapter le résultat au format attendu par ce service
    # (pour compatibilité avec le code existant)
    return {
        "points_to_hide": hiding_rules["elements_to_hide"],
        "hide_image_shapes": hiding_rules["hide_constructions"],
        "hide_construction_lines": hiding_rules["hide_constructions"],
        "exercise_type": hiding_rules["exercise_type_detected"]
    }


def determine_elements_to_hide_in_question_legacy(exercise_type: str, figure: GeometricFigure) -> Dict[str, Any]:
    """
    📌 FONCTION LEGACY : Ancienne logique (conservée pour référence)
    
    Détermine quels éléments doivent être cachés dans le SUJET selon le type d'exercice.
    
    Règle officielle (manuels scolaires, brevet, prescriptions IPR) :
        - SUJET : données connues uniquement
        - CORRIGÉ : données connues + données à trouver
    
    Types d'exercices :
        1. trouver_symetrique : L'élève doit trouver le point/figure image
           → Cacher : point M' ou triangle A'B'C'
           
        2. verifier_symetrie : L'élève vérifie si deux points DONNÉS sont symétriques
           → Ne rien cacher (tous les points sont des données connues)
           
        3. completer_figure : L'élève doit compléter une figure (triangle)
           → Cacher : le triangle image A'B'C'
    
    Args:
        exercise_type: Type d'exercice (extrait des propriétés de la figure)
        figure: Objet GeometricFigure
    
    Returns:
        Dict avec :
            - points_to_hide: List[str] - Noms des points à cacher
            - hide_image_shapes: bool - Cacher les formes images (triangles, etc.)
            - hide_construction_lines: bool - Cacher les segments de construction
    """
    
    # Extraire le type d'exercice des propriétés
    # Les propriétés contiennent "symetriques_True/False" pour verifier_symetrie
    is_verification = any("symetriques_" in prop for prop in figure.proprietes)
    is_triangle = "triangle" in figure.proprietes
    
    # Déterminer le type d'exercice
    if is_verification:
        # Type 2 : verifier_symetrie
        # → NE RIEN CACHER (tous les éléments sont des données connues)
        return {
            "points_to_hide": [],
            "hide_image_shapes": False,
            "hide_construction_lines": False,
            "exercise_type": "verifier_symetrie"
        }
    
    elif is_triangle:
        # Type 3 : completer_figure
        # → Cacher le triangle image A'B'C'
        return {
            "points_to_hide": [],  # Géré par hide_image_shapes
            "hide_image_shapes": True,
            "hide_construction_lines": True,
            "exercise_type": "completer_figure"
        }
    
    else:
        # Type 1 : trouver_symetrique
        # → Cacher le point image M'
        points_list = figure.points if figure.points else []
        
        # Pour symétrie axiale : [point_original, point_image]
        # Pour symétrie centrale : [point_original, centre, point_image]
        if figure.type.lower() == "symetrie_axiale" and len(points_list) >= 2:
            points_to_hide = [points_list[1]]  # Le 2ème point est l'image
        elif figure.type.lower() == "symetrie_centrale" and len(points_list) >= 3:
            points_to_hide = [points_list[2]]  # Le 3ème point est l'image
        else:
            points_to_hide = []
        
        return {
            "points_to_hide": points_to_hide,
            "hide_image_shapes": False,
            "hide_construction_lines": True,
            "exercise_type": "trouver_symetrique"
        }

class GeometryRenderService:
    """Service de rendu SVG pour figures géométriques"""
    
    def __init__(self):
        self.renderer = GeometrySVGRenderer(width=400, height=300)
    
    def render_figure_to_svg(self, figure: GeometricFigure):
        """
        Convertit une GeometricFigure en SVG
        
        Args:
            figure: Objet GeometricFigure à rendre
            
        Returns:
            - Pour symétrie axiale/centrale : dict avec {figure_svg, figure_svg_question, figure_svg_correction}
            - Pour autres types : Chaîne SVG ou None en cas d'erreur
        """
        try:
            figure_type = figure.type.lower()
            
            # Dispatcher selon le type de figure
            if figure_type == "triangle_rectangle":
                return self._render_triangle_rectangle(figure)
            elif figure_type == "rectangle":
                return self._render_rectangle(figure)
            elif figure_type == "cercle":
                return self._render_cercle(figure)
            elif figure_type == "triangle":
                return self._render_triangle(figure)
            elif figure_type == "thales":
                return self._render_thales(figure)
            elif figure_type == "symetrie_axiale":
                # Retourne un dict avec question et correction
                return self._render_symetrie_axiale(figure)
            elif figure_type == "symetrie_centrale":
                # Retourne un dict avec question et correction
                return self._render_symetrie_centrale(figure)
            # ✅ NOUVEAUX TYPES SPRINT
            elif figure_type == "points_segments_droites":
                return self._render_points_segments_droites(figure)
            elif figure_type == "alignement_milieu":
                return self._render_alignement_milieu(figure)
            elif figure_type == "perpendiculaires_paralleles":
                return self._render_perpendiculaires_paralleles(figure)
            elif figure_type == "quadrilatere":
                return self._render_quadrilatere(figure)
            elif figure_type == "segment" or figure_type == "segments_comparaison":
                return self._render_segment(figure)
            elif figure_type == "carre":
                # Carré = rectangle avec propriété carrée
                return self._render_rectangle(figure)
            elif figure_type == "droite_numerique":
                # Droite graduée (nombre line)
                return self._render_droite_numerique(figure)
            else:
                logger.warning(f"Type de figure non supporté: {figure_type}")
                # Fallback : grille simple avec points
                return self._render_fallback_grid_with_points(figure)
                
        except Exception as e:
            logger.error(f"Erreur lors du rendu SVG: {e}", exc_info=True)
            return None
    
    def _render_triangle_rectangle(self, figure: GeometricFigure) -> str:
        """Rendu d'un triangle rectangle"""
        
        # Extraire les longueurs connues
        longueurs = {}
        for seg, val in figure.longueurs_connues.items():
            longueurs[seg] = val
        
        # Préparer les données pour le renderer
        data = {
            "points": figure.points[:3],  # 3 points pour un triangle
            "angle_droit": figure.rectangle_en or figure.points[1],  # Par défaut point B
            "longueurs_connues": longueurs
        }
        
        # Extraire base et hauteur si disponibles
        # Pour Pythagore: on a souvent 2 côtés de l'angle droit
        if len(longueurs) >= 2:
            values = list(longueurs.values())
            data["base"] = values[0] if isinstance(values[0], (int, float)) else 100
            data["hauteur"] = values[1] if isinstance(values[1], (int, float)) else 80
        
        # Préparer les segments avec métadonnées
        segments = []
        for seg_name, longueur in longueurs.items():
            if len(seg_name) == 2:
                p1, p2 = seg_name[0], seg_name[1]
                segments.append([p1, p2, {"longueur": longueur}])
        
        data["segments"] = segments
        
        return self.renderer.render_triangle_rectangle(data)
    
    def _render_rectangle(self, figure: GeometricFigure) -> str:
        """Rendu d'un rectangle"""
        
        # Extraire longueur et largeur
        longueurs = list(figure.longueurs_connues.values())
        
        data = {
            "points": figure.points[:4],  # 4 points pour un rectangle
            "longueur": longueurs[1] if len(longueurs) > 1 else 120,
            "largeur": longueurs[0] if len(longueurs) > 0 else 80
        }
        
        return self.renderer.render_rectangle(data)
    
    def _render_cercle(self, figure: GeometricFigure) -> str:
        """Rendu d'un cercle"""
        
        # Le rayon peut être dans les paramètres ou calculé
        rayon = 60  # Valeur par défaut
        
        # Essayer de trouver le rayon dans les longueurs connues
        for seg_name, val in figure.longueurs_connues.items():
            if isinstance(val, (int, float)):
                rayon = val
                break
        
        data = {
            "rayon": rayon,
            "centre": figure.points[0] if figure.points else "O"
        }
        
        return self.renderer.render_cercle(data)
    
    def _render_triangle(self, figure: GeometricFigure) -> str:
        """Rendu d'un triangle quelconque"""
        
        data = {
            "points": figure.points[:3],
            "type": "quelconque"
        }
        
        # Ajouter les segments avec longueurs si disponibles
        segments = []
        for seg_name, longueur in figure.longueurs_connues.items():
            if len(seg_name) == 2:
                p1, p2 = seg_name[0], seg_name[1]
                segments.append([p1, p2, {"longueur": longueur}])
        
        data["segments"] = segments
        
        return self.renderer.render_triangle(data)
    
    def _render_thales(self, figure: GeometricFigure) -> str:
        """Rendu d'une configuration de Thalès"""
        
        # Configuration Thalès: triangle DEF avec MN // EF
        # Points: D, E, F (triangle principal), M (sur DE), N (sur DF)
        
        if len(figure.points) < 5:
            logger.warning("Configuration Thalès nécessite 5 points minimum")
            return self._render_triangle(figure)  # Fallback
        
        # Préparer les données pour le renderer Thalès
        data = {
            "points": figure.points[:5],  # Les 5 points : D, E, F, M, N
            "longueurs_connues": figure.longueurs_connues,
            "proprietes": figure.proprietes
        }
        
        # Préparer les segments avec longueurs pour les cotes
        segments = []
        for seg_name, longueur in figure.longueurs_connues.items():
            if len(seg_name) == 2:
                p1, p2 = seg_name[0], seg_name[1]
                segments.append([p1, p2, {"longueur": longueur}])
        
        data["segments"] = segments
        
        return self.renderer.render_thales(data)
    
    def _render_symetrie_axiale(self, figure: GeometricFigure) -> dict:
        """
        Rendu d'une symétrie axiale
        
        Figure contient:
        - points: [point_original, point_image]
        - longueurs_connues: {
            "point_x": coordonnée x,
            "point_y": coordonnée y,
            "point_prime_x": coordonnée x symétrique,
            "point_prime_y": coordonnée y symétrique
          }
        - proprietes: ["axe_vertical"/"axe_horizontal"/"axe_oblique", "axe_position_X"]
        """
        
        # Extraire les coordonnées des points
        coords = {}
        for key, val in figure.longueurs_connues.items():
            coords[key] = val
        
        # Extraire le type d'axe depuis les propriétés
        axe_type = "vertical"
        axe_position = 5
        
        for prop in figure.proprietes:
            if prop.startswith("axe_"):
                parts = prop.split("_")
                if len(parts) >= 2:
                    if parts[1] in ["vertical", "horizontal", "oblique"]:
                        axe_type = parts[1]
                    elif parts[1] == "position":
                        try:
                            if "y=x" in prop:
                                axe_type = "oblique"
                                axe_position = "y=x"
                            else:
                                axe_position = int(parts[2]) if len(parts) > 2 else 5
                        except:
                            axe_position = 5
        
        # Récupérer les points
        points_list = figure.points if figure.points else []
        
        # 📌 APPLIQUER LA RÈGLE PÉDAGOGIQUE UNIVERSELLE
        # Le type d'exercice sera détecté automatiquement depuis les propriétés
        hiding_rules = determine_elements_to_hide_in_question("", figure)
        
        # GRILLE SYSTÉMATIQUE pour tous les exercices de symétrie axiale (collège)
        with_grid = True  # Toujours activée pour cohérence pédagogique
        
        # Vérifier si c'est un triangle
        is_triangle = "triangle" in figure.proprietes
        
        # Construire les données pour le renderer
        data = {
            "axe_type": axe_type,
            "axe_position": axe_position,
            "points_coords": coords,
            "points_labels": points_list,
            "is_triangle": is_triangle,
            "with_grid": with_grid,
            "points_to_hide_in_question": hiding_rules["points_to_hide"],
            "hide_image_shapes": hiding_rules["hide_image_shapes"],
            "hide_construction_lines": hiding_rules["hide_construction_lines"],
            "exercise_type_detected": hiding_rules["exercise_type"]
        }
        
        # Générer les deux versions (question et correction)
        svg_question, svg_correction = self.renderer.render_symetrie_axiale_question_et_correction(data)
        
        return {
            "figure_svg": svg_correction,  # Rétrocompatibilité
            "figure_svg_question": svg_question,
            "figure_svg_correction": svg_correction
        }
    
    def _render_symetrie_centrale(self, figure: GeometricFigure) -> dict:
        """
        Rendu d'une symétrie centrale
        
        Figure contient:
        - points: [point_original, centre, point_image]
        - longueurs_connues: coordonnées des points
        - proprietes: ["centre_symetrie"]
        """
        
        # Extraire les coordonnées
        coords = {}
        for key, val in figure.longueurs_connues.items():
            coords[key] = val
        
        # 📌 APPLIQUER LA RÈGLE PÉDAGOGIQUE UNIVERSELLE
        # Le type d'exercice sera détecté automatiquement depuis les propriétés
        hiding_rules = determine_elements_to_hide_in_question("", figure)
        
        # GRILLE SYSTÉMATIQUE pour tous les exercices de symétrie centrale (collège)
        with_grid = True  # Toujours activée pour cohérence pédagogique
        
        # Récupérer les points
        points_list = figure.points if figure.points else []
        
        # Vérifier si c'est un triangle
        is_triangle = "triangle" in figure.proprietes
        
        # Construire les données pour le renderer
        data = {
            "points_coords": coords,
            "points_labels": points_list,
            "is_triangle": is_triangle,
            "with_grid": with_grid,
            "points_to_hide_in_question": hiding_rules["points_to_hide"],
            "hide_image_shapes": hiding_rules["hide_image_shapes"],
            "hide_construction_lines": hiding_rules["hide_construction_lines"],
            "exercise_type_detected": hiding_rules["exercise_type"]
        }
        
        # Générer les deux versions (question et correction)
        svg_question, svg_correction = self.renderer.render_symetrie_centrale_question_et_correction(data)
        
        return {
            "figure_svg": svg_correction,  # Rétrocompatibilité
            "figure_svg_question": svg_question,
            "figure_svg_correction": svg_correction
        }


    
    # ============================================================================
    # RENDU DES FIGURES SPRINT
    # ============================================================================
    
    def _render_points_segments_droites(self, figure: GeometricFigure) -> str:
        """Rendu pour points, segments, droites, demi-droites (6e_G01)"""
        
        # Créer une grille avec les points
        points_data = []
        for point in figure.points:
            x_key = f"{point}_x"
            y_key = f"{point}_y"
            if x_key in figure.longueurs_connues and y_key in figure.longueurs_connues:
                x = figure.longueurs_connues[x_key]
                y = figure.longueurs_connues[y_key]
                points_data.append({"name": point, "x": x, "y": y})
        
        # Déterminer le type de figure à dessiner
        figure_props = figure.proprietes if figure.proprietes else []
        
        data = {
            "points": points_data,
            "grid": True,
            "figure_type": "segment" if "segment" in figure_props else "droite" if "droite" in figure_props else "demi_droite"
        }
        
        # Utiliser le renderer de base pour grille + points + segments
        return self.renderer.render_points_and_lines(data)
    
    def _render_alignement_milieu(self, figure: GeometricFigure) -> str:
        """Rendu pour alignement et milieu d'un segment (6e_G02)"""
        
        # Créer les points
        points_data = []
        for point in figure.points:
            x_key = f"{point}_x"
            y_key = f"{point}_y"
            if x_key in figure.longueurs_connues and y_key in figure.longueurs_connues:
                x = figure.longueurs_connues[x_key]
                y = figure.longueurs_connues[y_key]
                points_data.append({"name": point, "x": x, "y": y})
        
        # Vérifier si c'est un exercice de milieu
        is_milieu = "milieu" in (figure.proprietes if figure.proprietes else [])
        
        data = {
            "points": points_data,
            "grid": True,
            "show_milieu": is_milieu,
            "alignement": "alignement" in (figure.proprietes if figure.proprietes else [])
        }
        
        return self.renderer.render_points_and_lines(data)
    
    def _render_perpendiculaires_paralleles(self, figure: GeometricFigure) -> str:
        """Rendu pour perpendiculaires et parallèles (6e_G03)"""
        
        # Créer les points
        points_data = []
        for point in figure.points:
            x_key = f"{point}_x"
            y_key = f"{point}_y"
            if x_key in figure.longueurs_connues and y_key in figure.longueurs_connues:
                x = figure.longueurs_connues[x_key]
                y = figure.longueurs_connues[y_key]
                points_data.append({"name": point, "x": x, "y": y})
        
        data = {
            "points": points_data,
            "grid": True,
            "show_perpendiculaires": "perpendiculaires" in (figure.proprietes if figure.proprietes else []),
            "show_paralleles": "paralleles" in (figure.proprietes if figure.proprietes else [])
        }
        
        return self.renderer.render_points_and_lines(data)
    
    def _render_quadrilatere(self, figure: GeometricFigure) -> str:
        """Rendu pour quadrilatères (6e_G05)"""
        
        # Extraire les coordonnées des 4 points
        points_coords = []
        for point in figure.points[:4]:
            x_key = f"{point}_x"
            y_key = f"{point}_y"
            if x_key in figure.longueurs_connues and y_key in figure.longueurs_connues:
                x = figure.longueurs_connues[x_key]
                y = figure.longueurs_connues[y_key]
                points_coords.append({"name": point, "x": x, "y": y})
        
        # Déterminer le type de quadrilatère
        quad_type = "quelconque"
        if figure.proprietes:
            if "carre" in figure.proprietes:
                quad_type = "carre"
            elif "rectangle" in figure.proprietes:
                quad_type = "rectangle"
            elif "losange" in figure.proprietes:
                quad_type = "losange"
            elif "parallelogramme" in figure.proprietes:
                quad_type = "parallelogramme"
        
        data = {
            "points": points_coords,
            "quad_type": quad_type,
            "grid": True
        }
        
        return self.renderer.render_quadrilatere(data)
    
    def _render_segment(self, figure: GeometricFigure) -> str:
        """Rendu pour segments avec mesures (6e_GM01)"""
        
        # Créer les segments
        segments_data = []
        
        if figure.type == "segments_comparaison":
            # Plusieurs segments à comparer
            i = 0
            while i < len(figure.points):
                if i + 1 < len(figure.points):
                    p1 = figure.points[i]
                    p2 = figure.points[i + 1]
                    
                    x1_key = f"{p1}_x"
                    y1_key = f"{p1}_y"
                    x2_key = f"{p2}_x"
                    y2_key = f"{p2}_y"
                    
                    if all(k in figure.longueurs_connues for k in [x1_key, y1_key, x2_key, y2_key]):
                        x1 = figure.longueurs_connues[x1_key]
                        y1 = figure.longueurs_connues[y1_key]
                        x2 = figure.longueurs_connues[x2_key]
                        y2 = figure.longueurs_connues[y2_key]
                        
                        segments_data.append({
                            "p1": p1,
                            "p2": p2,
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2
                        })
                    i += 2
                else:
                    break
        else:
            # Un seul segment
            if len(figure.points) >= 2:
                p1, p2 = figure.points[0], figure.points[1]
                x1_key = f"{p1}_x"
                y1_key = f"{p1}_y"
                x2_key = f"{p2}_x"
                y2_key = f"{p2}_y"
                
                if all(k in figure.longueurs_connues for k in [x1_key, y1_key, x2_key, y2_key]):
                    segments_data.append({
                        "p1": p1,
                        "p2": p2,
                        "x1": figure.longueurs_connues[x1_key],
                        "y1": figure.longueurs_connues[y1_key],
                        "x2": figure.longueurs_connues[x2_key],
                        "y2": figure.longueurs_connues[y2_key]
                    })
        
        data = {
            "segments": segments_data,
            "grid": True,
            "show_measures": "mesure" in (figure.proprietes if figure.proprietes else [])
        }
        
        return self.renderer.render_segments(data)
    
    def _render_droite_numerique(self, figure: GeometricFigure) -> dict:
        """
        Rendu d'une droite graduée (nombre line)
        Retourne un dict avec question et correction comme les symétries
        """
        
        # Extraire les paramètres
        min_val = figure.longueurs_connues.get("min", 0)
        max_val = figure.longueurs_connues.get("max", 10)
        graduation = figure.longueurs_connues.get("graduation", 1)
        
        # Extraire les points avec abscisses
        points_data = []
        for point in figure.points:
            abscisse_key = f"point_{point}_abscisse"
            if abscisse_key in figure.longueurs_connues:
                abscisse = figure.longueurs_connues[abscisse_key]
                points_data.append({"name": point, "abscisse": abscisse})
        
        # Déterminer le type d'exercice
        is_lire_abscisse = "lire_abscisse" in (figure.proprietes if figure.proprietes else [])
        is_placer_nombre = "placer_nombre" in (figure.proprietes if figure.proprietes else [])
        
        # VERSION QUESTION
        # - Pour "lire_abscisse" : afficher le point (l'élève doit lire l'abscisse)
        # - Pour "placer_nombre" : NE PAS afficher le point (l'élève doit le placer)
        data_question = {
            "min": min_val,
            "max": max_val,
            "graduation": graduation,
            "points": points_data if is_lire_abscisse else [],  # ✅ Cacher point si "placer"
            "show_points": is_lire_abscisse,
            "with_graduations": True,
            "with_labels": True
        }
        
        # VERSION CORRECTION
        # - Toujours afficher le point (solution)
        data_correction = {
            "min": min_val,
            "max": max_val,
            "graduation": graduation,
            "points": points_data,
            "show_points": True,  # ✅ Toujours afficher dans la correction
            "with_graduations": True,
            "with_labels": True
        }
        
        # Générer les deux versions
        svg_question = self.renderer.render_number_line(data_question)
        svg_correction = self.renderer.render_number_line(data_correction)
        
        return {
            "figure_svg": svg_correction,  # Rétrocompatibilité
            "figure_svg_question": svg_question,
            "figure_svg_correction": svg_correction
        }
    
    def _render_fallback_grid_with_points(self, figure: GeometricFigure) -> str:
        """Fallback : grille simple avec points pour les types non supportés"""
        
        # Extraire tous les points disponibles
        points_data = []
        for point in figure.points if figure.points else []:
            x_key = f"{point}_x"
            y_key = f"{point}_y"
            if x_key in figure.longueurs_connues and y_key in figure.longueurs_connues:
                x = figure.longueurs_connues[x_key]
                y = figure.longueurs_connues[y_key]
                points_data.append({"name": point, "x": x, "y": y})
        
        # Si pas de points, créer une grille vide simple
        if not points_data:
            data = {
                "grid_only": True,
                "width": 400,
                "height": 300
            }
        else:
            data = {
                "points": points_data,
                "grid": True
            }
        
        return self.renderer.render_grid_with_points(data)


# Instance globale
geometry_render_service = GeometryRenderService()
