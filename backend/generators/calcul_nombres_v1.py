"""
Générateur CALCUL_NOMBRES_V1 - Calculs numériques (6e et 5e)
============================================================

Version: 1.0.0

Générateur robuste et déterministe pour les calculs numériques :
- Opérations simples (addition, soustraction, multiplication, division)
- Priorités opératoires (expressions à 2-3 opérations, parenthèses)
- Décimaux (comparaison, calculs, arrondis)

Caractéristiques :
- Variables toujours présentes (aucun placeholder non résolu)
- Erreurs 422 structurées avec error_code
- Presets pédagogiques pour 6e et 5e
- Déterministe (seed fixe → même résultat)
- Batch-compatible
"""

import math
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from backend.generators.base_generator import (
    BaseGenerator,
    GeneratorMeta,
    ParamSchema,
    Preset,
    ParamType,
)
from backend.generators.factory import GeneratorFactory
from backend.observability import (
    get_request_context,
    safe_random_choice,
    safe_randrange,
)


@GeneratorFactory.register
class CalculNombresV1Generator(BaseGenerator):
    """Générateur d'exercices de calcul numérique pour 6e et 5e."""
    
    # Pool de formulations alternatives (P0.1 - Variabilité)
    _ENONCE_VARIANTS = {
        "operations_simples": [
            "Calculer :",
            "Effectue le calcul suivant :",
            "Calcule :",
            "Détermine le résultat de :",
        ],
        "priorites_operatoires": [
            "Calcule en respectant les priorités opératoires :",
            "Effectue le calcul suivant (attention aux priorités) :",
            "Détermine le résultat en appliquant les priorités :",
            "Calcule (pense aux priorités des opérations) :",
        ],
        "decimaux": [
            "Effectue l'opération avec les nombres décimaux :",
            "Calcule avec des nombres décimaux :",
            "Résous ce calcul décimal :",
        ]
    }
    
    _CONSIGNE_VARIANTS = {
        "operations_simples": [
            "Effectue le calcul et donne le résultat.",
            "Calcule et indique le résultat.",
            "Détermine le résultat de l'opération.",
        ],
        "priorites_operatoires": [
            "Effectue le calcul en respectant les priorités opératoires.",
            "Calcule en appliquant les règles de priorité.",
            "Résous en respectant l'ordre des opérations.",
        ],
        "decimaux": [
            "Effectue le calcul avec des nombres décimaux.",
            "Calcule avec des nombres à virgule.",
            "Résous cette opération décimale.",
        ]
    }
    
    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="CALCUL_NOMBRES_V1",
            label="Calculs numériques",
            description="Exercices de calcul numérique : opérations simples, priorités opératoires, décimaux",
            version="1.0.0",
            niveaux=["6e", "5e"],
            exercise_type="CALCUL_NOMBRES",
            svg_mode="NONE",
            supports_double_svg=False,
            pedagogical_tips="⚠️ Rappeler l'ordre des opérations : parenthèses → ×/÷ → +/-. Erreur fréquente : calculer de gauche à droite sans respecter les priorités.",
            is_dynamic=True,  # P1.2 - Générateur dynamique
            supported_grades=["6e", "5e"],  # P1.2 - Niveaux compatibles
            supported_chapters=["6e_N04", "6e_N05", "6e_N06", "6e_SP01", "6e_SP03", "5e_N01", "5e_N02", "5e_N03", "5e_N04"],  # P1.2 - Chapitres recommandés
            min_offer="pro"  # P2.1 - Générateur premium
        )
    
    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        return [
            ParamSchema(
                name="exercise_type",
                type=ParamType.ENUM,
                description="Type d'exercice",
                default="operations_simples",
                options=["operations_simples", "priorites_operatoires", "decimaux"],
                required=False
            ),
            ParamSchema(
                name="difficulty",
                type=ParamType.ENUM,
                description="Niveau de difficulté",
                default="standard",
                options=["facile", "standard"],
                required=False
            ),
            ParamSchema(
                name="grade",
                type=ParamType.ENUM,
                description="Niveau scolaire",
                default="6e",
                options=["6e", "5e"],
                required=False
            ),
            ParamSchema(
                name="preset",
                type=ParamType.ENUM,
                description="Preset pédagogique",
                default="standard",
                options=["simple", "standard"],
                required=False
            ),
            ParamSchema(
                name="variant_id",
                type=ParamType.ENUM,
                description="Variant pédagogique (P1.1)",
                default="A",
                options=["A", "B", "C"],
                required=False
            ),
            ParamSchema(
                name="seed",
                type=ParamType.INT,
                description="Seed pour reproductibilité (obligatoire)",
                default=None,
                required=True
            ),
        ]
    
    @classmethod
    def get_presets(cls) -> List[Preset]:
        return [
            # 6e - Opérations simples
            Preset(
                key="6e_operations_facile",
                label="6e Facile - Opérations simples",
                description="Additions et soustractions avec entiers naturels",
                niveau="6e",
                params={
                    "exercise_type": "operations_simples",
                    "difficulty": "facile",
                    "grade": "6e",
                    "preset": "simple",
                    "seed": 42
                }
            ),
            Preset(
                key="6e_operations_standard",
                label="6e Standard - Opérations simples",
                description="Toutes opérations avec entiers naturels",
                niveau="6e",
                params={
                    "exercise_type": "operations_simples",
                    "difficulty": "standard",
                    "grade": "6e",
                    "preset": "standard",
                    "seed": 42
                }
            ),
            # 6e - Priorités opératoires
            Preset(
                key="6e_priorites_facile",
                label="6e Facile - Priorités opératoires",
                description="Expressions à 2 opérations sans parenthèses",
                niveau="6e",
                params={
                    "exercise_type": "priorites_operatoires",
                    "difficulty": "facile",
                    "grade": "6e",
                    "preset": "simple",
                    "seed": 42
                }
            ),
            Preset(
                key="6e_priorites_standard",
                label="6e Standard - Priorités opératoires",
                description="Expressions à 2-3 opérations avec parenthèses possibles",
                niveau="6e",
                params={
                    "exercise_type": "priorites_operatoires",
                    "difficulty": "standard",
                    "grade": "6e",
                    "preset": "standard",
                    "seed": 42
                }
            ),
            # 5e - Opérations simples avec décimaux
            Preset(
                key="5e_operations_standard",
                label="5e Standard - Opérations avec décimaux",
                description="Opérations avec entiers et décimaux simples",
                niveau="5e",
                params={
                    "exercise_type": "operations_simples",
                    "difficulty": "standard",
                    "grade": "5e",
                    "preset": "standard",
                    "seed": 42
                }
            ),
            # 5e - Priorités opératoires
            Preset(
                key="5e_priorites_standard",
                label="5e Standard - Priorités opératoires",
                description="Expressions complexes avec décimaux",
                niveau="5e",
                params={
                    "exercise_type": "priorites_operatoires",
                    "difficulty": "standard",
                    "grade": "5e",
                    "preset": "standard",
                    "seed": 42
                }
            ),
            # 5e - Décimaux
            Preset(
                key="5e_decimaux_standard",
                label="5e Standard - Décimaux",
                description="Comparaison, calculs et arrondis avec décimaux",
                niveau="5e",
                params={
                    "exercise_type": "decimaux",
                    "difficulty": "standard",
                    "grade": "5e",
                    "preset": "standard",
                    "seed": 42
                }
            ),
        ]
    
    def _validate_exercise_type(self, exercise_type: str) -> None:
        """Valide le type d'exercice."""
        valid_types = ["operations_simples", "priorites_operatoires", "decimaux"]
        if exercise_type not in valid_types:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "INVALID_EXERCISE_TYPE",
                    "error": "invalid_exercise_type",
                    "message": f"Type d'exercice invalide: {exercise_type}",
                    "hint": f"Types valides: {', '.join(valid_types)}",
                    "context": {
                        "exercise_type": exercise_type,
                        "valid_types": valid_types
                    }
                }
            )
    
    def _validate_grade(self, grade: str) -> None:
        """Valide le niveau scolaire."""
        valid_grades = ["6e", "5e"]
        if grade not in valid_grades:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "INVALID_GRADE",
                    "error": "invalid_grade",
                    "message": f"Niveau scolaire invalide: {grade}",
                    "hint": f"Niveaux valides: {', '.join(valid_grades)}",
                    "context": {
                        "grade": grade,
                        "valid_grades": valid_grades
                    }
                }
            )
    
    def _validate_difficulty(self, difficulty: str) -> None:
        """Valide la difficulté."""
        valid_difficulties = ["facile", "standard"]
        if difficulty not in valid_difficulties:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "INVALID_DIFFICULTY",
                    "error": "invalid_difficulty",
                    "message": f"Difficulté invalide: {difficulty}",
                    "hint": f"Difficultés valides: {', '.join(valid_difficulties)}",
                    "context": {
                        "difficulty": difficulty,
                        "valid_difficulties": valid_difficulties
                    }
                }
            )
    
    def _generate_operations_simples(self, difficulty: str, grade: str) -> Dict[str, Any]:
        """Génère un exercice d'opérations simples."""
        if grade == "6e":
            # 6e : entiers naturels uniquement
            if difficulty == "facile":
                a = self.rng_randrange(1, 50)
                b = self.rng_randrange(1, 50)
                operation = self.rng_choice(["+", "-"])
            else:  # standard
                a = self.rng_randrange(1, 100)
                b = self.rng_randrange(1, 100)
                operation = self.rng_choice(["+", "-", "×", "÷"])
        else:  # 5e
            # 5e : entiers et décimaux simples
            if difficulty == "facile":
                use_decimal = self._rng.random() < 0.3
                if use_decimal:
                    a = round(self._rng.uniform(1, 20), 1)
                    b = round(self._rng.uniform(1, 20), 1)
                else:
                    a = self.rng_randrange(1, 50)
                    b = self.rng_randrange(1, 50)
                operation = self.rng_choice(["+", "-"])
            else:  # standard
                use_decimal = self._rng.random() < 0.5
                if use_decimal:
                    a = round(self._rng.uniform(1, 50), 1)
                    b = round(self._rng.uniform(1, 50), 1)
                else:
                    a = self.rng_randrange(1, 100)
                    b = self.rng_randrange(1, 100)
                operation = self.rng_choice(["+", "-", "×", "÷"])
        
        # Calculer le résultat
        if operation == "+":
            resultat = a + b
            calcul_intermediaire = f"{a} + {b} = {resultat}"
        elif operation == "-":
            # S'assurer que le résultat est positif
            if a < b:
                a, b = b, a
            resultat = a - b
            calcul_intermediaire = f"{a} - {b} = {resultat}"
        elif operation == "×":
            resultat = a * b
            calcul_intermediaire = f"{a} × {b} = {resultat}"
        else:  # ÷
            # S'assurer que la division est exacte
            if isinstance(a, float) or isinstance(b, float):
                # Pour les décimaux, utiliser une division simple
                resultat = round(a / b, 2) if b != 0 else 0
            else:
                # Pour les entiers, s'assurer que a est un multiple de b
                if a % b != 0:
                    a = b * self.rng_randrange(2, 10)
                resultat = a // b
            calcul_intermediaire = f"{a} ÷ {b} = {resultat}"
        
        # Formater l'énoncé (P0.1 - Variant)
        intro = self.rng_choice(self._ENONCE_VARIANTS["operations_simples"])
        enonce = f"{intro} {a} {operation} {b}"
        consigne = self.rng_choice(self._CONSIGNE_VARIANTS["operations_simples"])
        
        return {
            "enonce": enonce,
            "solution": f"Pour calculer {a} {operation} {b}, on effectue l'opération.",
            "calculs_intermediaires": calcul_intermediaire,
            "reponse_finale": str(resultat),
            "niveau": grade,
            "type_exercice": "operations_simples",
            "consigne": consigne
        }
    
    def _generate_priorites_operatoires(self, difficulty: str, grade: str) -> Dict[str, Any]:
        """Génère un exercice sur les priorités opératoires."""
        if grade == "6e":
            # 6e : entiers uniquement
            if difficulty == "facile":
                # Expression à 2 opérations sans parenthèses
                a = self.rng_randrange(1, 20)
                b = self.rng_randrange(1, 20)
                c = self.rng_randrange(1, 20)
                op1 = self.rng_choice(["+", "-"])
                op2 = self.rng_choice(["+", "-"])
                expression = f"{a} {op1} {b} {op2} {c}"
            else:  # standard
                # Expression à 2-3 opérations avec parenthèses possibles
                use_parentheses = self._rng.random() < 0.5
                a = self.rng_randrange(1, 30)
                b = self.rng_randrange(1, 30)
                c = self.rng_randrange(1, 30)
                op1 = self.rng_choice(["+", "-", "×"])
                op2 = self.rng_choice(["+", "-", "×"])
                
                if use_parentheses:
                    expression = f"({a} {op1} {b}) {op2} {c}"
                else:
                    expression = f"{a} {op1} {b} {op2} {c}"
        else:  # 5e
            # 5e : entiers et décimaux
            if difficulty == "facile":
                use_decimal = self._rng.random() < 0.3
                if use_decimal:
                    a = round(self._rng.uniform(1, 20), 1)
                    b = round(self._rng.uniform(1, 20), 1)
                    c = round(self._rng.uniform(1, 20), 1)
                else:
                    a = self.rng_randrange(1, 20)
                    b = self.rng_randrange(1, 20)
                    c = self.rng_randrange(1, 20)
                op1 = self.rng_choice(["+", "-"])
                op2 = self.rng_choice(["+", "-"])
                expression = f"{a} {op1} {b} {op2} {c}"
            else:  # standard
                use_decimal = self._rng.random() < 0.5
                use_parentheses = self._rng.random() < 0.5
                if use_decimal:
                    a = round(self._rng.uniform(1, 30), 1)
                    b = round(self._rng.uniform(1, 30), 1)
                    c = round(self._rng.uniform(1, 30), 1)
                else:
                    a = self.rng_randrange(1, 30)
                    b = self.rng_randrange(1, 30)
                    c = self.rng_randrange(1, 30)
                op1 = self.rng_choice(["+", "-", "×"])
                op2 = self.rng_choice(["+", "-", "×"])
                
                if use_parentheses:
                    expression = f"({a} {op1} {b}) {op2} {c}"
                else:
                    expression = f"{a} {op1} {b} {op2} {c}"
        
        # Calculer le résultat en respectant les priorités
        try:
            # Remplacer les symboles pour l'évaluation Python
            eval_expr = expression.replace("×", "*").replace("÷", "/")
            resultat = eval(eval_expr)
            if isinstance(resultat, float):
                resultat = round(resultat, 2)
        except Exception:
            # En cas d'erreur, recalculer avec un nouveau seed
            self._rng.seed(self._seed + 1000)
            return self._generate_priorites_operatoires(difficulty, grade)
        
        # Construire les calculs intermédiaires de manière robuste
        parts = expression.split()
        calculs = ""
        
        if "(" in expression:
            # Avec parenthèses
            if expression.startswith("("):
                # (a op1 b) op2 c
                paren_start = expression.find("(")
                paren_end = expression.find(")")
                part_expr = expression[paren_start+1:paren_end]
                part_parts = part_expr.split()
                a_val = float(part_parts[0])
                op1 = part_parts[1]
                b_val = float(part_parts[2])
                
                # Calculer la partie entre parenthèses
                if op1 == "+":
                    part1 = a_val + b_val
                elif op1 == "-":
                    part1 = a_val - b_val
                elif op1 == "×":
                    part1 = a_val * b_val
                else:  # ÷
                    part1 = a_val / b_val if b_val != 0 else 0
                    if isinstance(part1, float):
                        part1 = round(part1, 2)
                
                # Deuxième opération
                op2 = parts[3]
                c_val = float(parts[4])
                if op2 == "+":
                    resultat = part1 + c_val
                elif op2 == "-":
                    resultat = part1 - c_val
                elif op2 == "×":
                    resultat = part1 * c_val
                else:  # ÷
                    resultat = part1 / c_val if c_val != 0 else 0
                    if isinstance(resultat, float):
                        resultat = round(resultat, 2)
                
                calculs = f"Étape 1 : On calcule d'abord {part_expr} = {part1}\n"
                calculs += f"Étape 2 : Puis {part1} {op2} {c_val} = {resultat}"
            else:
                # a op1 (b op2 c)
                a_val = float(parts[0])
                op1 = parts[1]
                part_expr = expression[expression.find("(")+1:expression.find(")")]
                part_parts = part_expr.split()
                b_val = float(part_parts[0])
                op2 = part_parts[1]
                c_val = float(part_parts[2])
                
                # Calculer la partie entre parenthèses
                if op2 == "+":
                    part2 = b_val + c_val
                elif op2 == "-":
                    part2 = b_val - c_val
                elif op2 == "×":
                    part2 = b_val * c_val
                else:  # ÷
                    part2 = b_val / c_val if c_val != 0 else 0
                    if isinstance(part2, float):
                        part2 = round(part2, 2)
                
                # Première opération
                if op1 == "+":
                    resultat = a_val + part2
                elif op1 == "-":
                    resultat = a_val - part2
                elif op1 == "×":
                    resultat = a_val * part2
                else:  # ÷
                    resultat = a_val / part2 if part2 != 0 else 0
                    if isinstance(resultat, float):
                        resultat = round(resultat, 2)
                
                calculs = f"Étape 1 : On calcule d'abord {part_expr} = {part2}\n"
                calculs += f"Étape 2 : Puis {a_val} {op1} {part2} = {resultat}"
        else:
            # Sans parenthèses : respecter les priorités ×/÷ avant +/-
            if len(parts) == 5:  # a op1 b op2 c
                a_val = float(parts[0])
                op1 = parts[1]
                b_val = float(parts[2])
                op2 = parts[3]
                c_val = float(parts[4])
                
                # Vérifier les priorités
                if op1 in ["×", "÷"]:
                    # op1 a priorité
                    if op1 == "×":
                        inter = a_val * b_val
                    else:  # ÷
                        inter = a_val / b_val if b_val != 0 else 0
                        if isinstance(inter, float):
                            inter = round(inter, 2)
                    calculs = f"Étape 1 : On calcule d'abord {a_val} {op1} {b_val} = {inter}\n"
                    if op2 == "+":
                        resultat = inter + c_val
                    elif op2 == "-":
                        resultat = inter - c_val
                    elif op2 == "×":
                        resultat = inter * c_val
                    else:  # ÷
                        resultat = inter / c_val if c_val != 0 else 0
                        if isinstance(resultat, float):
                            resultat = round(resultat, 2)
                    calculs += f"Étape 2 : Puis {inter} {op2} {c_val} = {resultat}"
                elif op2 in ["×", "÷"]:
                    # op2 a priorité
                    if op2 == "×":
                        inter = b_val * c_val
                    else:  # ÷
                        inter = b_val / c_val if c_val != 0 else 0
                        if isinstance(inter, float):
                            inter = round(inter, 2)
                    calculs = f"Étape 1 : On calcule d'abord {b_val} {op2} {c_val} = {inter}\n"
                    if op1 == "+":
                        resultat = a_val + inter
                    else:  # -
                        resultat = a_val - inter
                    calculs += f"Étape 2 : Puis {a_val} {op1} {inter} = {resultat}"
                else:
                    # Même priorité : de gauche à droite
                    if op1 == "+":
                        inter = a_val + b_val
                    else:  # -
                        inter = a_val - b_val
                    calculs = f"Étape 1 : On calcule d'abord {a_val} {op1} {b_val} = {inter}\n"
                    if op2 == "+":
                        resultat = inter + c_val
                    else:  # -
                        resultat = inter - c_val
                    calculs += f"Étape 2 : Puis {inter} {op2} {c_val} = {resultat}"
            else:
                calculs = f"On respecte les priorités : × et ÷ avant + et -\n"
                calculs += f"Résultat : {resultat}"
        
        intro = self.rng_choice(self._ENONCE_VARIANTS["priorites_operatoires"])
        enonce = f"{intro} {expression}"
        consigne = self.rng_choice(self._CONSIGNE_VARIANTS["priorites_operatoires"])
        
        return {
            "enonce": enonce,
            "solution": f"Pour calculer {expression}, on respecte l'ordre des opérations.",
            "calculs_intermediaires": calculs,
            "reponse_finale": str(resultat),
            "niveau": grade,
            "type_exercice": "priorites_operatoires",
            "consigne": consigne
        }
    
    def _generate_decimaux(self, difficulty: str, grade: str) -> Dict[str, Any]:
        """Génère un exercice sur les décimaux (5e uniquement)."""
        if grade == "6e":
            # 6e ne couvre pas les décimaux de cette manière
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "INVALID_GRADE",
                    "error": "invalid_grade",
                    "message": "Les exercices sur les décimaux ne sont pas disponibles pour le niveau 6e",
                    "hint": "Utilisez grade='5e' pour les exercices sur les décimaux",
                    "context": {
                        "grade": grade,
                        "exercise_type": "decimaux"
                    }
                }
            )
        
        # 5e uniquement
        exercise_subtype = self.rng_choice(["comparaison", "calcul", "arrondi"])
        
        if exercise_subtype == "comparaison":
            a = round(self._rng.uniform(1, 100), 1)
            b = round(self._rng.uniform(1, 100), 1)
            if a < b:
                signe = "<"
                reponse = f"{a} < {b}"
            elif a > b:
                signe = ">"
                reponse = f"{a} > {b}"
            else:
                signe = "="
                reponse = f"{a} = {b}"
            
            intro = self.rng_choice(self._ENONCE_VARIANTS["decimaux"])
            enonce = f"{intro}\n\nComparer : {a} et {b}"
            calculs = f"On compare les parties entières puis les décimales.\n{a} {signe} {b}"
            consigne = self.rng_choice(self._CONSIGNE_VARIANTS["decimaux"])
            
        elif exercise_subtype == "calcul":
            a = round(self._rng.uniform(1, 50), 1)
            b = round(self._rng.uniform(1, 50), 1)
            operation = self.rng_choice(["+", "-", "×"])
            
            if operation == "+":
                resultat = round(a + b, 1)
            elif operation == "-":
                if a < b:
                    a, b = b, a
                resultat = round(a - b, 1)
            else:  # ×
                resultat = round(a * b, 2)
            
            intro = self.rng_choice(self._ENONCE_VARIANTS["decimaux"])
            enonce = f"{intro}\n\nCalculer : {a} {operation} {b}"
            calculs = f"{a} {operation} {b} = {resultat}"
            consigne = self.rng_choice(self._CONSIGNE_VARIANTS["decimaux"])
            reponse = str(resultat)
            
        else:  # arrondi
            nombre = round(self._rng.uniform(1, 100), 2)
            precision = self.rng_choice([0, 1])
            if precision == 0:
                resultat = round(nombre)
                consigne = f"Arrondir {nombre} à l'unité."
                calculs = f"L'arrondi de {nombre} à l'unité est {resultat}."
            else:
                resultat = round(nombre, 1)
                consigne = f"Arrondir {nombre} au dixième."
                calculs = f"L'arrondi de {nombre} au dixième est {resultat}."
            
            intro = self.rng_choice(self._ENONCE_VARIANTS["decimaux"])
            enonce = f"{intro}\n\nArrondir : {nombre}"
            reponse = str(resultat)
        
        return {
            "enonce": enonce,
            "solution": f"Solution pour l'exercice sur les décimaux.",
            "calculs_intermediaires": calculs,
            "reponse_finale": reponse,
            "niveau": grade,
            "type_exercice": "decimaux",
            "consigne": consigne
        }
    
    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un exercice de calcul numérique.
        
        Args:
            params: Paramètres validés
            
        Returns:
            Dict avec variables, geo_data, meta
        """
        # Extraire et valider les paramètres
        exercise_type = params.get("exercise_type", "operations_simples")
        difficulty = params.get("difficulty", "standard")
        grade = params.get("grade", "6e")
        seed = params.get("seed")
        
        # Validation explicite
        if seed is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "GENERATION_FAILED",
                    "error": "seed_required",
                    "message": "Le paramètre 'seed' est obligatoire",
                    "hint": "Fournissez un seed (nombre entier) pour garantir la reproductibilité",
                    "context": {
                        "missing_param": "seed"
                    }
                }
            )
        
        self._validate_exercise_type(exercise_type)
        self._validate_grade(grade)
        self._validate_difficulty(difficulty)
        
        # Générer selon le type
        try:
            if exercise_type == "operations_simples":
                variables = self._generate_operations_simples(difficulty, grade)
            elif exercise_type == "priorites_operatoires":
                variables = self._generate_priorites_operatoires(difficulty, grade)
            else:  # decimaux
                variables = self._generate_decimaux(difficulty, grade)
        except HTTPException:
            # Propager les HTTPException telles quelles
            raise
        except Exception as e:
            # Autres erreurs → 422 GENERATION_FAILED
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "GENERATION_FAILED",
                    "error": "generation_failed",
                    "message": f"Erreur lors de la génération de l'exercice: {str(e)}",
                    "hint": "Vérifiez les paramètres fournis et réessayez",
                    "context": {
                        "exercise_type": exercise_type,
                        "difficulty": difficulty,
                        "grade": grade,
                        "exception_type": type(e).__name__
                    }
                }
            )
        
        # S'assurer que TOUTES les variables sont présentes
        required_vars = [
            "enonce", "solution", "calculs_intermediaires", 
            "reponse_finale", "niveau", "type_exercice", "consigne"
        ]
        for var in required_vars:
            if var not in variables:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": "GENERATION_FAILED",
                        "error": "missing_variable",
                        "message": f"Variable manquante: {var}",
                        "hint": "Erreur interne du générateur. Contactez l'administrateur.",
                        "context": {
                            "missing_variable": var,
                            "available_variables": list(variables.keys())
                        }
                    }
                )
        
        # Retourner le résultat standard
        return {
            "variables": variables,
            "geo_data": None,  # Pas de géométrie pour ce générateur
            "figure_svg_enonce": None,
            "figure_svg_solution": None,
            "meta": {
                "generator_key": "CALCUL_NOMBRES_V1",
                "exercise_type": exercise_type,
                "difficulty": difficulty,
                "grade": grade
            }
        }

