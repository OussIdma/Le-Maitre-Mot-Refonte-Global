"""
Générateur SIMPLIFICATION_FRACTIONS_V1 - Simplification de fractions
=====================================================================

Version: 1.0.0

Génère des exercices sur la simplification de fractions à l'aide du PGCD.
Compétence : Simplifier une fraction à l'aide du PGCD (CM2 → 5e)
"""

import math
import time
from typing import Dict, Any, List, Optional
from backend.generators.base_generator import (
    BaseGenerator,
    GeneratorMeta,
    ParamSchema,
    Preset,
    ParamType,
    create_svg_wrapper,
)
from backend.generators.factory import GeneratorFactory
from backend.observability import (
    get_request_context,
    safe_random_choice,
    safe_randrange,
)


# Templates HTML de référence
ENONCE_TEMPLATE = "<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>"

SOLUTION_TEMPLATE = """<ol>
  <li>{{step1}}</li>
  <li>{{step2}}</li>
  <li>{{step3}}</li>
  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>
</ol>"""


@GeneratorFactory.register
class SimplificationFractionsV1Generator(BaseGenerator):
    """Générateur d'exercices sur la simplification de fractions."""
    
    # Constantes SVG
    SVG_WIDTH = 520
    SVG_HEIGHT = 140
    SVG_VIEWBOX = "0 0 520 140"
    SVG_PADDING_LEFT = 40
    SVG_PADDING_RIGHT = 40
    SVG_PADDING_TOP = 40
    SVG_PADDING_BOTTOM = 40
    NUMBER_LINE_LENGTH = 440  # SVG_WIDTH - SVG_PADDING_LEFT - SVG_PADDING_RIGHT
    
    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="SIMPLIFICATION_FRACTIONS_V1",
            label="Simplification de fractions",
            description="Simplifier des fractions à l'aide du PGCD",
            version="1.0.0",
            niveaux=["CM2", "6e", "5e"],
            exercise_type="FRACTIONS",
            svg_mode="AUTO",
            supports_double_svg=True,
            pedagogical_tips="⚠️ Rappeler : PGCD divise numérateur ET dénominateur. Erreur fréquente : division d'un seul côté."
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
            ParamSchema(
                name="allow_negative",
                type=ParamType.BOOL,
                description="Autoriser les fractions négatives",
                default=False
            ),
            ParamSchema(
                name="max_denominator",
                type=ParamType.INT,
                description="Dénominateur maximum",
                default=60,
                min=6,
                max=500
            ),
            ParamSchema(
                name="force_reducible",
                type=ParamType.BOOL,
                description="Forcer une fraction réductible (PGCD > 1)",
                default=True
            ),
            ParamSchema(
                name="show_svg",
                type=ParamType.BOOL,
                description="Afficher le SVG de la droite graduée",
                default=True
            ),
            ParamSchema(
                name="representation",
                type=ParamType.ENUM,
                description="Type de représentation visuelle",
                default="number_line",
                options=["none", "number_line"]
            )
        ]
    
    @classmethod
    def get_presets(cls) -> List[Preset]:
        return [
            Preset(
                key="CM2_facile",
                label="CM2 Facile - Fractions simples",
                description="Fractions avec petits dénominateurs et PGCD simples",
                niveau="CM2",
                params={
                    "difficulty": "facile",
                    "allow_negative": False,
                    "max_denominator": 12,
                    "force_reducible": True,
                    "show_svg": True,
                    "representation": "number_line"
                }
            ),
            Preset(
                key="6e_facile",
                label="6e Facile - Fractions réductibles",
                description="Fractions avec dénominateurs moyens et PGCD évidents",
                niveau="6e",
                params={
                    "difficulty": "facile",
                    "allow_negative": False,
                    "max_denominator": 12,
                    "force_reducible": True,
                    "show_svg": True,
                    "representation": "number_line"
                }
            ),
            Preset(
                key="6e_moyen",
                label="6e Moyen - Fractions variées",
                description="Fractions avec dénominateurs moyens et PGCD variés",
                niveau="6e",
                params={
                    "difficulty": "moyen",
                    "allow_negative": False,
                    "max_denominator": 20,
                    "force_reducible": True,
                    "show_svg": True,
                    "representation": "number_line"
                }
            ),
            Preset(
                key="5e_moyen",
                label="5e Moyen - Fractions complexes",
                description="Fractions avec dénominateurs plus grands et PGCD variés",
                niveau="5e",
                params={
                    "difficulty": "moyen",
                    "allow_negative": False,
                    "max_denominator": 40,
                    "force_reducible": True,
                    "show_svg": True,
                    "representation": "number_line"
                }
            ),
            Preset(
                key="5e_difficile",
                label="5e Difficile - Fractions avancées",
                description="Fractions avec dénominateurs grands et PGCD complexes",
                niveau="5e",
                params={
                    "difficulty": "difficile",
                    "allow_negative": False,
                    "max_denominator": 40,
                    "force_reducible": True,
                    "show_svg": True,
                    "representation": "number_line"
                }
            )
        ]
    
    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un exercice de simplification de fraction.
        
        Args:
            params: Paramètres validés
            
        Returns:
            Dict avec variables, geo_data, SVG, meta, results
        """
        gen_start = time.time()
        ctx = get_request_context()
        ctx.update({
            'generator_key': 'SIMPLIFICATION_FRACTIONS_V1',
            'difficulty': params.get('difficulty'),
        })
        
        # Log début génération
        self._obs_logger.info(
            "event=generate_in",
            event="generate_in",
            outcome="in_progress",
            **ctx
        )
        
        # Log paramètres (DEBUG uniquement si LOG_VERBOSE=1)
        self._obs_logger.debug(
            "event=params",
            event="params",
            outcome="in_progress",
            params_keys=list(params.keys()),
            **ctx
        )
        
        difficulty = params["difficulty"]
        allow_negative = params["allow_negative"]
        max_denominator = params["max_denominator"]
        force_reducible = params["force_reducible"]
        show_svg = params["show_svg"]
        representation = params["representation"]
        
        # Générer la fraction selon la difficulté
        n, d, pgcd = self._pick_fraction(difficulty, max_denominator, force_reducible)
        
        # Gérer le signe négatif si autorisé
        if allow_negative and self._rng.random() < 0.3:  # 30% de chance
            n = -n
        
        # Calculer la fraction réduite
        n_red = n // pgcd
        d_red = d // pgcd
        
        # Construire les variables
        variables = self._build_variables(n, d, n_red, d_red, pgcd, difficulty)
        
        # Données géométriques
        geo_data = {
            "n": n,
            "d": d,
            "n_red": n_red,
            "d_red": d_red,
            "pgcd": pgcd,
            "difficulty": difficulty,
            "representation": representation
        }
        
        # Générer les SVG si nécessaire
        svg_enonce = None
        svg_solution = None
        if show_svg and representation == "number_line":
            svg_enonce = self._generate_svg_enonce(n, d, allow_negative)
            svg_solution = self._generate_svg_solution(n, d, n_red, d_red, allow_negative)
            
            # Log SVG générés (DEBUG)
            self._obs_logger.debug(
                "event=svg_generated",
                event="svg_generated",
                outcome="success",
                svg_enonce_present=svg_enonce is not None,
                svg_solution_present=svg_solution is not None,
                **ctx
            )
        
        # Log succès génération
        gen_duration_ms = int((time.time() - gen_start) * 1000)
        self._obs_logger.info(
            "event=generate_complete",
            event="generate_complete",
            outcome="success",
            duration_ms=gen_duration_ms,
            fraction=f"{n}/{d}",
            fraction_reduite=f"{n_red}/{d_red}",
            pgcd=pgcd,
            **ctx
        )
        
        return {
            "variables": variables,
            "geo_data": geo_data,
            "figure_svg_enonce": svg_enonce,
            "figure_svg_solution": svg_solution,
            "meta": {
                "exercise_type": "FRACTIONS",
                "difficulty": difficulty,
                "question_type": "simplifier"
            },
            "results": {
                "n_red": n_red,
                "d_red": d_red,
                "pgcd": pgcd
            }
        }
    
    def _pick_fraction(
        self, 
        difficulty: str, 
        max_denominator: int, 
        force_reducible: bool
    ) -> tuple:
        """
        Génère une fraction (n, d) avec son PGCD selon la difficulté.
        
        Returns:
            (n, d, pgcd)
        """
        max_attempts = 100
        
        if difficulty == "facile":
            max_denom_base = 12
            pgcd_options = [2, 3, 4, 5]
            max_numerator_ratio = 0.9  # Fraction propre (< 1)
        elif difficulty == "moyen":
            max_denom_base = 20
            pgcd_options = [2, 3, 4, 5, 6, 8, 9, 10]
            max_numerator_ratio = 1.0
        else:  # difficile
            max_denom_base = min(40, max_denominator)
            pgcd_options = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15]
            max_numerator_ratio = 1.0
        
        # FIX P0: Filtrer pgcd_options selon max_denom_base pour éviter crash randrange
        # Un PGCD ne peut fonctionner que si max_denom_base // pgcd >= 2
        # (sinon denom_max < 2 et safe_randrange(2, denom_max+1) échoue)
        pgcd_options_original = pgcd_options.copy()
        pgcd_options = [pgcd for pgcd in pgcd_options if max_denom_base // pgcd >= 2]
        
        ctx = get_request_context()
        ctx.update({
            'generator_key': 'SIMPLIFICATION_FRACTIONS_V1',
            'difficulty': difficulty,
        })
        
        # Log du filtrage si des PGCD ont été exclus
        if len(pgcd_options) < len(pgcd_options_original):
            self._obs_logger.debug(
                "event=pgcd_filtered",
                event="pgcd_filtered",
                outcome="success",
                pgcd_options_before=pgcd_options_original,
                pgcd_options_after=pgcd_options,
                max_denom_base=max_denom_base,
                max_denominator=max_denominator,
                filtered_count=len(pgcd_options_original) - len(pgcd_options),
                **ctx
            )
        
        for _ in range(max_attempts):
            # Choisir un PGCD avec prévention pool vide
            if not pgcd_options:
                self._obs_logger.warning(
                    "event=pool_empty_prevented",
                    event="pool_empty",
                    outcome="error",
                    reason="list_empty",
                    pool_size=0,
                    pool_type="pgcd_options",
                    **ctx
                )
                raise ValueError(f"pgcd_options est vide pour difficulty={difficulty}")
            
            pgcd = safe_random_choice(pgcd_options, ctx, self._obs_logger)
            
            # Générer le dénominateur de base (avant multiplication par PGCD)
            denom_max = max_denom_base // pgcd
            if denom_max < 2:
                continue
            denom_base = safe_randrange(2, denom_max + 1, context=ctx, logger=self._obs_logger)
            d = denom_base * pgcd
            
            # Limiter au max_denominator
            if d > max_denominator:
                continue
            
            # Générer le numérateur
            max_n = int(d * max_numerator_ratio)
            if max_n < 1:
                max_n = 1
            num_base = safe_randrange(1, max_n + 1, context=ctx, logger=self._obs_logger)
            n = num_base * pgcd
            
            # Vérifier le PGCD réel
            actual_pgcd = math.gcd(abs(n), d)
            
            if force_reducible:
                if actual_pgcd > 1:
                    return (n, d, actual_pgcd)
            else:
                return (n, d, actual_pgcd)
        
        # Fallback : fraction simple
        n = 6
        d = 8
        pgcd = math.gcd(n, d)
        return (n, d, pgcd)
    
    def _build_variables(
        self, 
        n: int, 
        d: int, 
        n_red: int, 
        d_red: int, 
        pgcd: int,
        difficulty: str
    ) -> Dict[str, Any]:
        """
        Construit les variables pour les templates HTML.
        
        Args:
            n: Numérateur original
            d: Dénominateur original
            n_red: Numérateur réduit
            d_red: Dénominateur réduit
            pgcd: PGCD
            difficulty: Niveau de difficulté
            
        Returns:
            Dict avec toutes les variables nécessaires
        """
        # Format de la fraction
        fraction = f"{n}/{d}"
        fraction_reduite = f"{n_red}/{d_red}"
        
        # Étapes de résolution
        step1 = f"PGCD({abs(n)}, {d}) = {pgcd}"
        step2 = "On divise numérateur et dénominateur par " + str(pgcd)
        
        # Calcul final
        if n_red == n // pgcd and d_red == d // pgcd:
            step3 = f"{n} ÷ {pgcd} = {n_red} et {d} ÷ {pgcd} = {d_red}"
        else:
            step3 = f"On obtient {fraction_reduite}"
        
        # Vérifier si irréductible
        is_irreductible = (pgcd == 1)
        
        return {
            "fraction": fraction,
            "n": n,
            "d": d,
            "pgcd": pgcd,
            "n_red": n_red,
            "d_red": d_red,
            "fraction_reduite": fraction_reduite,
            "step1": step1,
            "step2": step2,
            "step3": step3,
            "is_irreductible": is_irreductible,
            "difficulty": difficulty
        }
    
    def _generate_svg_enonce(
        self, 
        n: int, 
        d: int, 
        allow_negative: bool
    ) -> str:
        """
        Génère le SVG de la droite graduée pour l'énoncé.
        
        Args:
            n: Numérateur
            d: Dénominateur
            allow_negative: Si True, autorise les valeurs négatives
            
        Returns:
            SVG string
        """
        # Calculer la position sur la droite (0 à 1)
        t = abs(n) / d if d != 0 else 0.0
        t = min(1.0, max(0.0, t))  # Clamp dans [0, 1]
        
        # Position en pixels
        x_pos = self.SVG_PADDING_LEFT + int(t * self.NUMBER_LINE_LENGTH)
        y_pos = self.SVG_PADDING_TOP + 30
        
        # Construire le contenu SVG
        content_parts = []
        
        # Droite graduée
        x_start = self.SVG_PADDING_LEFT
        x_end = self.SVG_PADDING_LEFT + self.NUMBER_LINE_LENGTH
        y_line = y_pos
        
        # Ligne principale
        content_parts.append(
            f'<line x1="{x_start}" y1="{y_line}" x2="{x_end}" y2="{y_line}" '
            f'stroke="#000" stroke-width="2"/>'
        )
        
        # Graduations 0 et 1
        content_parts.append(
            f'<line x1="{x_start}" y1="{y_line - 5}" x2="{x_start}" y2="{y_line + 5}" '
            f'stroke="#000" stroke-width="2"/>'
        )
        content_parts.append(
            f'<text x="{x_start}" y="{y_line - 10}" text-anchor="middle" '
            f'font-size="14" fill="#000">0</text>'
        )
        
        content_parts.append(
            f'<line x1="{x_end}" y1="{y_line - 5}" x2="{x_end}" y2="{y_line + 5}" '
            f'stroke="#000" stroke-width="2"/>'
        )
        content_parts.append(
            f'<text x="{x_end}" y="{y_line - 10}" text-anchor="middle" '
            f'font-size="14" fill="#000">1</text>'
        )
        
        # Point positionné
        content_parts.append(
            f'<circle cx="{x_pos}" cy="{y_line}" r="6" fill="#1976d2" stroke="#1976d2" stroke-width="2"/>'
        )
        
        # Label de la fraction
        fraction_label = f"{n}/{d}"
        if allow_negative and n < 0:
            fraction_label = f"-{abs(n)}/{d}"
        
        content_parts.append(
            f'<text x="{x_pos}" y="{y_line + 25}" text-anchor="middle" '
            f'font-size="16" fill="#1976d2" font-weight="bold">{fraction_label}</text>'
        )
        
        content = "\n".join(content_parts)
        return create_svg_wrapper(
            content, 
            self.SVG_WIDTH, 
            self.SVG_HEIGHT, 
            self.SVG_VIEWBOX
        )
    
    def _generate_svg_solution(
        self, 
        n: int, 
        d: int, 
        n_red: int, 
        d_red: int,
        allow_negative: bool
    ) -> str:
        """
        Génère le SVG de la droite graduée pour la solution.
        
        Args:
            n: Numérateur original
            d: Dénominateur original
            n_red: Numérateur réduit
            d_red: Dénominateur réduit
            allow_negative: Si True, autorise les valeurs négatives
            
        Returns:
            SVG string
        """
        # Calculer la position sur la droite (0 à 1)
        t = abs(n) / d if d != 0 else 0.0
        t = min(1.0, max(0.0, t))  # Clamp dans [0, 1]
        
        # Position en pixels
        x_pos = self.SVG_PADDING_LEFT + int(t * self.NUMBER_LINE_LENGTH)
        y_pos = self.SVG_PADDING_TOP + 30
        
        # Construire le contenu SVG
        content_parts = []
        
        # Droite graduée
        x_start = self.SVG_PADDING_LEFT
        x_end = self.SVG_PADDING_LEFT + self.NUMBER_LINE_LENGTH
        y_line = y_pos
        
        # Ligne principale
        content_parts.append(
            f'<line x1="{x_start}" y1="{y_line}" x2="{x_end}" y2="{y_line}" '
            f'stroke="#000" stroke-width="2"/>'
        )
        
        # Graduations 0 et 1
        content_parts.append(
            f'<line x1="{x_start}" y1="{y_line - 5}" x2="{x_start}" y2="{y_line + 5}" '
            f'stroke="#000" stroke-width="2"/>'
        )
        content_parts.append(
            f'<text x="{x_start}" y="{y_line - 10}" text-anchor="middle" '
            f'font-size="14" fill="#000">0</text>'
        )
        
        content_parts.append(
            f'<line x1="{x_end}" y1="{y_line - 5}" x2="{x_end}" y2="{y_line + 5}" '
            f'stroke="#000" stroke-width="2"/>'
        )
        content_parts.append(
            f'<text x="{x_end}" y="{y_line - 10}" text-anchor="middle" '
            f'font-size="14" fill="#000">1</text>'
        )
        
        # Point positionné
        content_parts.append(
            f'<circle cx="{x_pos}" cy="{y_line}" r="6" fill="#c62828" stroke="#c62828" stroke-width="2"/>'
        )
        
        # Label de la fraction réduite
        fraction_label = f"{n_red}/{d_red}"
        if allow_negative and n < 0:
            fraction_label = f"-{abs(n_red)}/{d_red}"
        
        content_parts.append(
            f'<text x="{x_pos}" y="{y_line + 25}" text-anchor="middle" '
            f'font-size="16" fill="#c62828" font-weight="bold">{fraction_label}</text>'
        )
        
        content = "\n".join(content_parts)
        return create_svg_wrapper(
            content, 
            self.SVG_WIDTH, 
            self.SVG_HEIGHT, 
            self.SVG_VIEWBOX
        )

