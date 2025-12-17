"""
Générateur SYMETRIE_AXIALE_V1 - Symétrie Axiale (Réflexion)
===========================================================
Version intégrable Admin -> Génération.
- HTML pur (pas de LaTeX)
- RNG local (self.rng)
- variables + geo_data JSON-safe (listes)
- meta.exercise_type + svg_mode=AUTO
"""

import random
import math
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SymetrieAxialeV1Config:
    COORD_RANGE = list(range(-5, 6))  # -5 à 5
    FIGURE_TYPES = ["point", "segment", "triangle"]
    AXE_TYPES = ["horizontal", "vertical", "oblique_simple"]


class SymetrieAxialeV1Generator:
    # ⚠️ À aligner avec ton svg_render_service.py (clé attendue)
    EXERCISE_TYPE = "SYMETRIE_AXIALE"
    SVG_MODE = "AUTO"

    def __init__(self, seed: Optional[int] = None, difficulty: str = "moyen"):
        self.seed = seed
        self.difficulty = difficulty.lower()
        self.rng = random.Random(seed)

    def _calculate_symmetric_point(
        self, point: Tuple[float, float], axe_type: str, axe_param: float
    ) -> Tuple[float, float]:
        x, y = point
        if axe_type == "horizontal":
            x_sym, y_sym = x, 2 * axe_param - y
        elif axe_type == "vertical":
            x_sym, y_sym = 2 * axe_param - x, y
        elif axe_type == "oblique_simple":
            if axe_param == 1:       # y = x
                x_sym, y_sym = y, x
            elif axe_param == -1:    # y = -x
                x_sym, y_sym = -y, -x
            else:
                x_sym, y_sym = x, y
        else:
            raise ValueError(f"Type d'axe inconnu: {axe_type}")
        return (round(x_sym, 2), round(y_sym, 2))

    def _calculate_symmetric_figure(
        self, figure_coords: Dict[str, Tuple[float, float]], axe_type: str, axe_param: float
    ) -> Dict[str, Tuple[float, float]]:
        return {f"{name}'": self._calculate_symmetric_point(pt, axe_type, axe_param)
                for name, pt in figure_coords.items()}

    def generate(self) -> Dict[str, Any]:
        figure_type = self.rng.choice(SymetrieAxialeV1Config.FIGURE_TYPES)
        axe_type_raw = self.rng.choice(SymetrieAxialeV1Config.AXE_TYPES)

        axe_type, axe_param, axe_label = self._generate_axis(axe_type_raw)

        base_coords = self._generate_figure_coordinates(
            figure_type=figure_type, axe_type=axe_type, axe_param=axe_param
        )
        final_coords = self._calculate_symmetric_figure(base_coords, axe_type, axe_param)

        variables = self._build_variables(
            figure_type=figure_type,
            base_coords=base_coords,
            final_coords=final_coords,
            axe_label=axe_label,
        )

        # geo_data JSON-safe: listes [x, y]
        points_base = {k: [v[0], v[1]] for k, v in base_coords.items()}
        points_sym = {k: [v[0], v[1]] for k, v in final_coords.items()}

        variables["geo_data"] = {
            "points_base": points_base,
            "points_sym": points_sym,
            "axe": {"type": axe_type, "param": axe_param},
            "bounds": {
                "min": min(SymetrieAxialeV1Config.COORD_RANGE),
                "max": max(SymetrieAxialeV1Config.COORD_RANGE),
            },
        }

        results = self._calculate_results(final_coords)

        return {
            "variables": variables,
            "results": results,
            "meta": {
                "exercise_type": self.EXERCISE_TYPE,
                "svg_mode": self.SVG_MODE,
            },
        }

    def _generate_axis(self, axe_type: str):
        if axe_type == "horizontal":
            param = self.rng.choice(SymetrieAxialeV1Config.COORD_RANGE)
            label = f"la droite (d) d'équation y = {param}"
            return "horizontal", param, label

        if axe_type == "vertical":
            param = self.rng.choice(SymetrieAxialeV1Config.COORD_RANGE)
            label = f"la droite (d) d'équation x = {param}"
            return "vertical", param, label

        # oblique_simple
        param = self.rng.choice([1, -1])
        label = "la droite (d) d'équation y = x" if param == 1 else "la droite (d) d'équation y = -x"
        return "oblique_simple", param, label

    def _generate_figure_coordinates(self, figure_type: str, axe_type: str, axe_param: float):
        def pick_not_on_axis():
            # évite les points sur l'axe quand horizontal/vertical
            for _ in range(50):
                x = self.rng.choice(SymetrieAxialeV1Config.COORD_RANGE)
                y = self.rng.choice(SymetrieAxialeV1Config.COORD_RANGE)

                if axe_type == "vertical" and x == axe_param:
                    continue
                if axe_type == "horizontal" and y == axe_param:
                    continue
                # Pour y=x : éviter trop souvent x=y (trivial), sans l'interdire totalement
                if axe_type == "oblique_simple" and axe_param == 1 and x == y and self.rng.random() < 0.8:
                    continue
                if axe_type == "oblique_simple" and axe_param == -1 and x == -y and self.rng.random() < 0.8:
                    continue
                return (x, y)
            return (0, 1)  # fallback

        if figure_type == "point":
            return {"A": pick_not_on_axis()}

        if figure_type == "segment":
            A = pick_not_on_axis()
            B = pick_not_on_axis()
            while B == A:
                B = pick_not_on_axis()
            return {"A": A, "B": B}

        # triangle
        pts = set()
        while len(pts) < 3:
            pts.add(pick_not_on_axis())
        pts = list(pts)
        return {"A": pts[0], "B": pts[1], "C": pts[2]}

    def _build_variables(self, figure_type: str, base_coords: Dict, final_coords: Dict, axe_label: str):
        variables = {
            "figure_type": figure_type,
            "axe_label": axe_label,
            "description_enonce": self._describe_figure(base_coords, figure_type),
            "description_solution": self._describe_figure(final_coords, figure_type, prime=True),
        }

        # Toujours fournir les coords lisibles pour templates (point/segment/triangle)
        for name, (x, y) in base_coords.items():
            variables[f"coords_{name.lower()}"] = f"{name}({x}; {y})"
        for name, (x, y) in final_coords.items():
            # name = "A'"
            clean = name.replace("'", "_prime").lower()
            variables[f"coords_{clean}"] = f"{name}({x}; {y})"

        # Optionnel: une longueur pour segment (utile en correction)
        if figure_type == "segment":
            A, B = base_coords["A"], base_coords["B"]
            variables["longueur_ab"] = round(math.dist(A, B), 2)

        return variables

    def _calculate_results(self, final_coords: Dict) -> Dict[str, Any]:
        results = {}
        # clés explicites (coord_a_prime, coord_b_prime, …)
        for name, (x, y) in final_coords.items():
            clean = name.replace("'", "_prime").lower()
            results[f"coord_{clean}"] = f"({x}; {y})"
        return results

    def _describe_figure(self, coords: Dict, figure_type: str, prime: bool = False):
        pts = ", ".join([f"{n}({c[0]}; {c[1]})" for n, c in coords.items()])
        if figure_type == "point":
            return f"le point {pts}"
        if figure_type == "segment":
            return f"le segment avec les points {pts}"
        return f"le triangle avec les sommets {pts}"