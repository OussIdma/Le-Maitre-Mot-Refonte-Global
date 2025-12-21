"""
Générateur SIMPLIFICATION_FRACTIONS_V2 - Simplification de fractions (PREMIUM)
=============================================================================

Version: 2.0.0

Évolution PREMIUM du générateur V1 avec :
- Variants pédagogiques (A: standard, B: guidé, C: diagnostic)
- Indices gradués déterministes (hint_level 0→3)
- Feedback d'erreurs typiques
- SVG solution amélioré (flèche + encadré + label)
- Support fractions impropres

NON-RÉGRESSION : Si aucun nouveau paramètre n'est fourni, comportement V1 strictement inchangé.

📚 DOCUMENTATION FONCTIONNELLE DES PARAMÈTRES :
   Voir docs/GENERATEUR_SIMPLIFICATION_FRACTIONS_V2.md
   → Mode d'emploi pratique de tous les paramètres (difficulty, variant_id, hint_level, etc.)
"""

import math
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


# Templates HTML de référence (V1 - compatibilité)
ENONCE_TEMPLATE_V1 = "<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>"
SOLUTION_TEMPLATE_V1 = """<ol>
  <li>{{step1}}</li>
  <li>{{step2}}</li>
  <li>{{step3}}</li>
  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>
</ol>"""

# Templates V2 - Variant A (Standard)
ENONCE_TEMPLATE_A = "<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>"
SOLUTION_TEMPLATE_A = """<ol>
  <li>{{step1}}</li>
  <li>{{step2}}</li>
  <li>{{step3}}</li>
  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>
</ol>"""

# Templates V2 - Variant B (Guidé)
ENONCE_TEMPLATE_B = """<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>
{{hint_display}}"""
SOLUTION_TEMPLATE_B = """<ol>
  <li><strong>Méthode :</strong> {{method_explanation}}</li>
  <li>{{step1}}</li>
  <li>{{step2}}</li>
  <li>{{step3}}</li>
  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>
</ol>"""

# Templates V2 - Variant C (Diagnostic)
ENONCE_TEMPLATE_C = """<p><strong>Analyse cette simplification :</strong></p>
<p>Fraction initiale : <strong>{{fraction}}</strong></p>
<p>Simplification proposée : <strong>{{wrong_simplification}}</strong></p>
<p><em>Cette simplification est-elle correcte ?</em></p>"""
SOLUTION_TEMPLATE_C = """<ol>
  <li><strong>Vérification :</strong> {{check_equivalence_str}}</li>
  <li><strong>Conclusion :</strong> {{diagnostic_explanation}}</li>
  <li><strong>Simplification correcte :</strong> {{fraction_reduite}}</li>
</ol>"""


@GeneratorFactory.register
class SimplificationFractionsV2Generator(BaseGenerator):
    """Générateur PREMIUM d'exercices sur la simplification de fractions."""
    
    # Constantes SVG
    SVG_WIDTH = 520
    SVG_HEIGHT = 140
    SVG_VIEWBOX = "0 0 520 140"
    SVG_PADDING_LEFT = 40
    SVG_PADDING_RIGHT = 40
    SVG_PADDING_TOP = 40
    SVG_PADDING_BOTTOM = 40
    NUMBER_LINE_LENGTH = 440
    
    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="SIMPLIFICATION_FRACTIONS_V2",
            label="Simplification de fractions (PREMIUM)",
            description="Simplifier des fractions à l'aide du PGCD avec variants pédagogiques, indices et feedback",
            version="2.0.0",
            niveaux=["CM2", "6e", "5e"],
            exercise_type="FRACTIONS",
            svg_mode="AUTO",
            supports_double_svg=True,
            pedagogical_tips="⚠️ Rappeler : PGCD divise numérateur ET dénominateur. Erreur fréquente : division d'un seul côté."
        )
    
    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        # Paramètres V1 (conservés pour compatibilité)
        schema = [
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
            ),
            # Nouveaux paramètres V2 PREMIUM
            ParamSchema(
                name="variant_id",
                type=ParamType.ENUM,
                description="Variant pédagogique",
                default="A",
                options=["A", "B", "C"]
            ),
            ParamSchema(
                name="pedagogy_mode",
                type=ParamType.ENUM,
                description="Mode pédagogique",
                default="standard",
                options=["standard", "guided", "diagnostic"]
            ),
            ParamSchema(
                name="hint_level",
                type=ParamType.INT,
                description="Niveau d'indice (0-3)",
                default=0,
                min=0,
                max=3
            ),
            ParamSchema(
                name="include_feedback",
                type=ParamType.BOOL,
                description="Inclure le feedback d'erreurs typiques",
                default=True
            ),
            ParamSchema(
                name="allow_improper",
                type=ParamType.BOOL,
                description="Autoriser les fractions impropres (≥ 1)",
                default=False
            ),
        ]
        return schema
    
    @classmethod
    def get_presets(cls) -> List[Preset]:
        # Presets V1 (conservés)
        presets = [
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
                    "representation": "number_line",
                    "variant_id": "A",
                    "pedagogy_mode": "standard",
                    "hint_level": 0,
                    "include_feedback": False,
                    "allow_improper": False
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
                    "representation": "number_line",
                    "variant_id": "A",
                    "pedagogy_mode": "standard",
                    "hint_level": 0,
                    "include_feedback": False,
                    "allow_improper": False
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
                    "representation": "number_line",
                    "variant_id": "A",
                    "pedagogy_mode": "standard",
                    "hint_level": 0,
                    "include_feedback": False,
                    "allow_improper": False
                }
            ),
            # Nouveaux presets PREMIUM
            Preset(
                key="CM2_facile_guided",
                label="CM2 Facile Guidé",
                description="CM2 avec méthode guidée et indices contextuels",
                niveau="CM2",
                params={
                    "difficulty": "facile",
                    "allow_negative": False,
                    "max_denominator": 12,
                    "force_reducible": True,
                    "show_svg": True,
                    "representation": "number_line",
                    "variant_id": "B",
                    "pedagogy_mode": "guided",
                    "hint_level": 1,
                    "include_feedback": True,
                    "allow_improper": False
                }
            ),
            Preset(
                key="6e_moyen_standard",
                label="6e Moyen Standard",
                description="6e avec variant standard",
                niveau="6e",
                params={
                    "difficulty": "moyen",
                    "allow_negative": False,
                    "max_denominator": 20,
                    "force_reducible": True,
                    "show_svg": True,
                    "representation": "number_line",
                    "variant_id": "A",
                    "pedagogy_mode": "standard",
                    "hint_level": 0,
                    "include_feedback": True,
                    "allow_improper": False
                }
            ),
            Preset(
                key="5e_difficile_diagnostic",
                label="5e Difficile Diagnostic",
                description="5e avec variant diagnostic (analyse d'erreurs)",
                niveau="5e",
                params={
                    "difficulty": "difficile",
                    "allow_negative": False,
                    "max_denominator": 40,
                    "force_reducible": True,
                    "show_svg": True,
                    "representation": "number_line",
                    "variant_id": "C",
                    "pedagogy_mode": "diagnostic",
                    "hint_level": 0,
                    "include_feedback": True,
                    "allow_improper": False
                }
            ),
            Preset(
                key="5e_moyen_irreductible",
                label="5e Moyen Irréductible",
                description="5e avec fractions irréductibles possibles",
                niveau="5e",
                params={
                    "difficulty": "moyen",
                    "allow_negative": False,
                    "max_denominator": 40,
                    "force_reducible": False,
                    "show_svg": True,
                    "representation": "number_line",
                    "variant_id": "A",
                    "pedagogy_mode": "standard",
                    "hint_level": 0,
                    "include_feedback": True,
                    "allow_improper": False
                }
            ),
        ]
        return presets
    
    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un exercice de simplification de fraction (V2 PREMIUM).
        
        NON-RÉGRESSION : Si variant_id="A", pedagogy_mode="standard", hint_level=0,
        include_feedback=False, allow_improper=False → comportement V1 strictement inchangé.
        """
        # Paramètres V1
        difficulty = params.get("difficulty", "moyen")
        allow_negative = params.get("allow_negative", False)
        max_denominator = params.get("max_denominator", 60)
        force_reducible = params.get("force_reducible", True)
        show_svg = params.get("show_svg", True)
        representation = params.get("representation", "number_line")
        
        # Paramètres V2 (avec defaults pour compatibilité V1)
        variant_id = params.get("variant_id", "A")
        pedagogy_mode = params.get("pedagogy_mode", "standard")
        hint_level = params.get("hint_level", 0)
        include_feedback = params.get("include_feedback", False)
        allow_improper = params.get("allow_improper", False)
        
        # Détection mode V1 (compatibilité stricte)
        is_v1_mode = (
            variant_id == "A" and
            pedagogy_mode == "standard" and
            hint_level == 0 and
            not include_feedback and
            not allow_improper
        )
        
        # Générer la fraction selon la difficulté
        n, d, pgcd = self._pick_fraction(
            difficulty, max_denominator, force_reducible, allow_improper
        )
        
        # Gérer le signe négatif si autorisé
        if allow_negative and self._rng.random() < 0.3:
            n = -n
        
        # Calculer la fraction réduite
        n_red = n // pgcd
        d_red = d // pgcd
        
        # Construire les variables de base
        variables = self._build_variables_base(n, d, n_red, d_red, pgcd, difficulty)
        
        # Ajouter les variables V2 selon le variant
        if variant_id == "B":
            variables.update(self._build_variables_variant_b(n, d, pgcd, hint_level))
        elif variant_id == "C":
            variables.update(self._build_variables_variant_c(n, d, n_red, d_red, pgcd))
        
        # Ajouter les variables communes V2
        variables.update({
            "variant_id": variant_id,
            "pedagogy_mode": pedagogy_mode,
            "hint_level": hint_level,
            "include_feedback": include_feedback,
            "is_improper": abs(n) >= d
        })
        
        # Ajouter le feedback d'erreurs si demandé
        if include_feedback:
            variables["error_catalog"] = self._build_error_catalog()
            variables["error_type_examples"] = self._build_error_examples(n, d, pgcd)
        
        # Données géométriques
        geo_data = {
            "n": n,
            "d": d,
            "n_red": n_red,
            "d_red": d_red,
            "pgcd": pgcd,
            "difficulty": difficulty,
            "representation": representation,
            "variant_id": variant_id
        }
        
        # Générer les SVG si nécessaire
        svg_enonce = None
        svg_solution = None
        if show_svg and representation == "number_line":
            svg_enonce = self._generate_svg_enonce(n, d, allow_negative)
            svg_solution = self._generate_svg_solution_v2(
                n, d, n_red, d_red, allow_negative, variant_id
            )
        
        return {
            "variables": variables,
            "geo_data": geo_data,
            "figure_svg_enonce": svg_enonce,
            "figure_svg_solution": svg_solution,
            "meta": {
                "exercise_type": "FRACTIONS",
                "difficulty": difficulty,
                "question_type": "simplifier",
                "variant_id": variant_id,
                "pedagogy_mode": pedagogy_mode
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
        force_reducible: bool,
        allow_improper: bool
    ) -> tuple:
        """Génère une fraction (n, d) avec son PGCD selon la difficulté."""
        max_attempts = 100
        
        if difficulty == "facile":
            max_denom_base = 12
            pgcd_options = [2, 3, 4, 5]
            max_numerator_ratio = 0.9 if not allow_improper else 1.5
        elif difficulty == "moyen":
            max_denom_base = 20
            pgcd_options = [2, 3, 4, 5, 6, 8, 9, 10]
            max_numerator_ratio = 1.0 if not allow_improper else 2.0
        else:  # difficile
            max_denom_base = min(40, max_denominator)
            pgcd_options = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15]
            max_numerator_ratio = 1.0 if not allow_improper else 2.5
        
        for _ in range(max_attempts):
            pgcd = self._rng.choice(pgcd_options)
            denom_base = self._rng.randint(2, max_denom_base // pgcd)
            d = denom_base * pgcd
            
            if d > max_denominator:
                continue
            
            max_n = int(d * max_numerator_ratio)
            if max_n < 1:
                max_n = 1
            num_base = self._rng.randint(1, max_n)
            n = num_base * pgcd
            
            actual_pgcd = math.gcd(abs(n), d)
            
            if force_reducible:
                if actual_pgcd > 1:
                    return (n, d, actual_pgcd)
            else:
                return (n, d, actual_pgcd)
        
        # Fallback
        n = 6
        d = 8
        pgcd = math.gcd(n, d)
        return (n, d, pgcd)
    
    def _build_variables_base(
        self, 
        n: int, 
        d: int, 
        n_red: int, 
        d_red: int, 
        pgcd: int,
        difficulty: str
    ) -> Dict[str, Any]:
        """Construit les variables de base (V1 compatibles)."""
        fraction = f"{n}/{d}"
        fraction_reduite = f"{n_red}/{d_red}"
        
        step1 = f"PGCD({abs(n)}, {d}) = {pgcd}"
        step2 = "On divise numérateur et dénominateur par " + str(pgcd)
        
        if n_red == n // pgcd and d_red == d // pgcd:
            step3 = f"{n} ÷ {pgcd} = {n_red} et {d} ÷ {pgcd} = {d_red}"
        else:
            step3 = f"On obtient {fraction_reduite}"
        
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
    
    def _build_variables_variant_b(
        self, 
        n: int, 
        d: int, 
        pgcd: int,
        hint_level: int
    ) -> Dict[str, Any]:
        """Construit les variables pour le variant B (guidé)."""
        method_explanation = (
            "Pour simplifier une fraction, on divise le numérateur et le dénominateur "
            "par leur plus grand diviseur commun (PGCD)."
        )
        
        hints = self._generate_hints(n, d, pgcd, hint_level)
        hint_used = hints[hint_level - 1] if hint_level > 0 and hint_level <= len(hints) else ""
        hint_display = f"<p><em>{hint_used}</em></p>" if hint_used else ""
        
        return {
            "method_explanation": method_explanation,
            "hints": hints,
            "hint_used": hint_used,
            "hint_display": hint_display
        }
    
    def _build_variables_variant_c(
        self, 
        n: int, 
        d: int, 
        n_red: int, 
        d_red: int, 
        pgcd: int
    ) -> Dict[str, Any]:
        """Construit les variables pour le variant C (diagnostic)."""
        # Générer une fausse simplification plausible
        wrong_n = n_red
        wrong_d = d_red
        
        # Erreur type : diviser seulement le numérateur
        if self._rng.random() < 0.5:
            wrong_n = n // pgcd
            wrong_d = d  # Dénominateur non divisé
        else:
            # Erreur type : diviser seulement le dénominateur
            wrong_n = n  # Numérateur non divisé
            wrong_d = d // pgcd
        
        wrong_simplification = f"{wrong_n}/{wrong_d}"
        
        # Vérifier si la simplification est correcte
        diagnostic_is_correct = (wrong_n == n_red and wrong_d == d_red)
        
        # Produit en croix pour vérifier l'équivalence
        check_equivalence_str = (
            f"{n} × {wrong_d} = {n * wrong_d} et "
            f"{d} × {wrong_n} = {d * wrong_n}. "
            f"Les produits sont {'égaux' if n * wrong_d == d * wrong_n else 'différents'}, "
            f"donc la simplification est {'correcte' if diagnostic_is_correct else 'incorrecte'}."
        )
        
        if diagnostic_is_correct:
            diagnostic_explanation = (
                f"La simplification {wrong_simplification} est correcte. "
                f"On a bien divisé le numérateur et le dénominateur par le PGCD."
            )
        else:
            diagnostic_explanation = (
                f"La simplification {wrong_simplification} est incorrecte. "
                f"On doit diviser le numérateur ET le dénominateur par le PGCD, "
                f"pas seulement l'un des deux. La bonne simplification est {n_red}/{d_red}."
            )
        
        return {
            "wrong_simplification": wrong_simplification,
            "diagnostic_is_correct": diagnostic_is_correct,
            "diagnostic_explanation": diagnostic_explanation,
            "check_equivalence_str": check_equivalence_str
        }
    
    def _generate_hints(self, n: int, d: int, pgcd: int, max_level: int) -> List[str]:
        """Génère des indices gradués déterministes (0→3)."""
        hints = []
        
        if max_level >= 1:
            hints.append(f"Indice 1 : Le PGCD de {abs(n)} et {d} est {pgcd}.")
        
        if max_level >= 2:
            hints.append(
                f"Indice 2 : Divise {abs(n)} par {pgcd} et {d} par {pgcd}."
            )
        
        if max_level >= 3:
            hints.append(
                f"Indice 3 : {abs(n)} ÷ {pgcd} = {abs(n) // pgcd} et {d} ÷ {pgcd} = {d // pgcd}."
            )
        
        return hints
    
    def _build_error_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Construit le catalogue d'erreurs typiques."""
        return {
            "divide_numerator_only": {
                "message": "Erreur : vous avez divisé seulement le numérateur. Il faut diviser le numérateur ET le dénominateur par le même nombre.",
                "trigger": "L'élève divise seulement le numérateur par le PGCD."
            },
            "divide_denominator_only": {
                "message": "Erreur : vous avez divisé seulement le dénominateur. Il faut diviser le numérateur ET le dénominateur par le même nombre.",
                "trigger": "L'élève divise seulement le dénominateur par le PGCD."
            },
            "not_fully_reduced": {
                "message": "La fraction peut encore être simplifiée. Vérifiez le PGCD du numérateur et du dénominateur.",
                "trigger": "La fraction simplifiée a encore un PGCD > 1."
            },
            "wrong_pgcd": {
                "message": "Le PGCD utilisé n'est pas correct. Vérifiez les diviseurs communs du numérateur et du dénominateur.",
                "trigger": "L'élève utilise un PGCD incorrect."
            },
            "sign_misplaced": {
                "message": "Attention au signe ! Le signe négatif doit être porté par le numérateur uniquement.",
                "trigger": "Le signe négatif est mal placé dans la fraction simplifiée."
            }
        }
    
    def _build_error_examples(self, n: int, d: int, pgcd: int) -> Dict[str, str]:
        """Construit des exemples d'erreurs typiques pour cette fraction."""
        n_red = n // pgcd
        d_red = d // pgcd
        
        return {
            "divide_numerator_only": f"❌ {n}/{d} = {n_red}/{d} (seulement le numérateur divisé)",
            "divide_denominator_only": f"❌ {n}/{d} = {n}/{d_red} (seulement le dénominateur divisé)",
            "correct": f"✅ {n}/{d} = {n_red}/{d_red} (numérateur ET dénominateur divisés par {pgcd})"
        }
    
    def _generate_svg_enonce(
        self, 
        n: int, 
        d: int, 
        allow_negative: bool
    ) -> str:
        """Génère le SVG de la droite graduée pour l'énoncé (identique V1)."""
        t = abs(n) / d if d != 0 else 0.0
        t = min(1.0, max(0.0, t))
        
        x_pos = self.SVG_PADDING_LEFT + int(t * self.NUMBER_LINE_LENGTH)
        y_pos = self.SVG_PADDING_TOP + 30
        
        content_parts = []
        
        x_start = self.SVG_PADDING_LEFT
        x_end = self.SVG_PADDING_LEFT + self.NUMBER_LINE_LENGTH
        y_line = y_pos
        
        content_parts.append(
            f'<line x1="{x_start}" y1="{y_line}" x2="{x_end}" y2="{y_line}" '
            f'stroke="#000" stroke-width="2"/>'
        )
        
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
        
        content_parts.append(
            f'<circle cx="{x_pos}" cy="{y_line}" r="6" fill="#1976d2" stroke="#1976d2" stroke-width="2"/>'
        )
        
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
    
    def _generate_svg_solution_v2(
        self, 
        n: int, 
        d: int, 
        n_red: int, 
        d_red: int,
        allow_negative: bool,
        variant_id: str
    ) -> str:
        """Génère le SVG solution V2 avec flèche + encadré + label (WOW)."""
        t = abs(n) / d if d != 0 else 0.0
        t = min(1.0, max(0.0, t))
        
        x_pos = self.SVG_PADDING_LEFT + int(t * self.NUMBER_LINE_LENGTH)
        y_pos = self.SVG_PADDING_TOP + 30
        
        content_parts = []
        
        x_start = self.SVG_PADDING_LEFT
        x_end = self.SVG_PADDING_LEFT + self.NUMBER_LINE_LENGTH
        y_line = y_pos
        
        # Droite graduée
        content_parts.append(
            f'<line x1="{x_start}" y1="{y_line}" x2="{x_end}" y2="{y_line}" '
            f'stroke="#000" stroke-width="2"/>'
        )
        
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
        
        # Flèche vers la fraction réduite (si variant A ou B)
        if variant_id in ["A", "B"]:
            arrow_y_start = y_line + 25
            arrow_y_end = y_line + 50
            arrow_x = x_pos
            
            content_parts.append(
                f'<line x1="{arrow_x}" y1="{arrow_y_start}" x2="{arrow_x}" y2="{arrow_y_end}" '
                f'stroke="#c62828" stroke-width="2" marker-end="url(#arrowhead)"/>'
            )
        
        # Encadré avec la fraction réduite (id stable)
        fraction_label = f"{n_red}/{d_red}"
        if allow_negative and n < 0:
            fraction_label = f"-{abs(n_red)}/{d_red}"
        
        box_x = x_pos - 30
        box_y = y_line + 50
        box_width = 60
        box_height = 30
        
        content_parts.append(
            f'<rect x="{box_x}" y="{box_y}" width="{box_width}" height="{box_height}" '
            f'fill="#fff3e0" stroke="#c62828" stroke-width="2" rx="4" id="reduced-box"/>'
        )
        
        content_parts.append(
            f'<text x="{x_pos}" y="{box_y + 20}" text-anchor="middle" '
            f'font-size="16" fill="#c62828" font-weight="bold" id="reduced-fraction">{fraction_label}</text>'
        )
        
        # Label "fraction réduite"
        content_parts.append(
            f'<text x="{x_pos}" y="{box_y + 45}" text-anchor="middle" '
            f'font-size="12" fill="#c62828" font-style="italic" id="reduced-label">fraction réduite</text>'
        )
        
        # Définir le marqueur de flèche
        defs = (
            '<defs>'
            '<marker id="arrowhead" markerWidth="10" markerHeight="10" refX="5" refY="3" orient="auto">'
            '<polygon points="0 0, 10 3, 0 6" fill="#c62828"/>'
            '</marker>'
            '</defs>'
        )
        
        content = defs + "\n".join(content_parts)
        return create_svg_wrapper(
            content, 
            self.SVG_WIDTH, 
            self.SVG_HEIGHT, 
            self.SVG_VIEWBOX
        )

