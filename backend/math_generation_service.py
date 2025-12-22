"""
Service de génération d'exercices mathématiques structurés
Génère specs mathématiques complètes avec solutions calculées (SANS IA)
"""

import random
import math
from fractions import Fraction
from typing import List, Dict, Any, Tuple
import logging
from math_models import (
    MathExerciseSpec, MathExerciseType, DifficultyLevel, 
    GeometricFigure
)

logger = logging.getLogger(__name__)

class MathGenerationService:
    """Service de génération d'exercices mathématiques structurés"""
    
    def __init__(self):
        # Points utilisables pour la géométrie (éviter ABC en premier)
        self.geometry_points_sets = [
            ["D", "E", "F"],
            ["M", "N", "P"], 
            ["R", "S", "T"],
            ["X", "Y", "Z"],
            ["G", "H", "I"],
            ["J", "K", "L"],
            ["A", "B", "C"]  # Dernier recours
        ]
        self.used_points_sets = set()
    
    def generate_math_exercise_specs(
        self, 
        niveau: str, 
        chapitre: str, 
        difficulte: str, 
        nb_exercices: int
    ) -> List[MathExerciseSpec]:
        """Point d'entrée principal - génère les specs d'exercices"""
        
        # Reset pour chaque génération
        self.used_points_sets.clear()
        
        # Mapper chapitre vers types d'exercices
        exercise_types = self._map_chapter_to_types(chapitre, niveau)
        
        specs = []
        for i in range(nb_exercices):
            # Choisir un type d'exercice
            exercise_type = random.choice(exercise_types)
            
            # Générer la spec selon le type
            spec = self._generate_spec_by_type(
                niveau, chapitre, exercise_type, difficulte
            )
            
            if spec:
                specs.append(spec)
            
        return specs
    
    def _map_chapter_to_types(self, chapitre: str, niveau: str) -> List[MathExerciseType]:
        """Mappe les chapitres aux types d'exercices appropriés"""
        
        # Note: Les chapitres sont uniques dans le mapping
        # Pour des chapitres présents dans plusieurs niveaux, 
        # le mapping s'applique à tous les niveaux
        mapping = {
            # 6e
            "Nombres entiers et décimaux": [MathExerciseType.CALCUL_DECIMAUX],
            "Périmètres et aires": [MathExerciseType.PERIMETRE_AIRE, MathExerciseType.RECTANGLE],
            "Aires": [MathExerciseType.PERIMETRE_AIRE, MathExerciseType.CERCLE],
            "Géométrie - Triangles et quadrilatères": [MathExerciseType.RECTANGLE, MathExerciseType.PERIMETRE_AIRE],
            
            # Chapitres multi-niveaux (6e, 4e, 5e, 3e)
            "Fractions": [MathExerciseType.CALCUL_FRACTIONS],
            "Proportionnalité": [MathExerciseType.PROPORTIONNALITE],
            "Nombres relatifs": [MathExerciseType.CALCUL_RELATIFS],
            "Statistiques": [MathExerciseType.STATISTIQUES],
            "Géométrie dans l'espace": [MathExerciseType.VOLUME],
            "Volumes": [MathExerciseType.VOLUME],
            "Puissances": [MathExerciseType.PUISSANCES],
            "Calcul littéral": [MathExerciseType.EQUATION_1ER_DEGRE, MathExerciseType.CALCUL_DECIMAUX],
            
            # 5e  
            "Triangles": [MathExerciseType.TRIANGLE_QUELCONQUE, MathExerciseType.TRIANGLE_RECTANGLE],
            "Aires et périmètres": [MathExerciseType.PERIMETRE_AIRE, MathExerciseType.CERCLE, MathExerciseType.RECTANGLE],
            
            # 4e
            "Théorème de Pythagore": [MathExerciseType.TRIANGLE_RECTANGLE],
            "Équations": [MathExerciseType.EQUATION_1ER_DEGRE],
            "Cosinus": [MathExerciseType.TRIGONOMETRIE],
            
            # 3e et géométrie avancée
            "Probabilités": [MathExerciseType.PROBABILITES],
            "Statistiques et probabilités": [MathExerciseType.STATISTIQUES, MathExerciseType.PROBABILITES],
            "Aires et volumes": [MathExerciseType.VOLUME, MathExerciseType.PERIMETRE_AIRE],
            "Théorème de Thalès": [MathExerciseType.THALES],
            "Trigonométrie": [MathExerciseType.TRIGONOMETRIE],
            "Le cercle": [MathExerciseType.CERCLE],
            "Cercle": [MathExerciseType.CERCLE]
        }
        
        return mapping.get(chapitre, [MathExerciseType.CALCUL_DECIMAUX])
    
    def _generate_spec_by_type(
        self, 
        niveau: str, 
        chapitre: str, 
        exercise_type: MathExerciseType, 
        difficulte: str
    ) -> MathExerciseSpec:
        """Génère une spec selon le type d'exercice"""
        
        generators = {
            MathExerciseType.CALCUL_RELATIFS: self._gen_calcul_relatifs,
            MathExerciseType.CALCUL_FRACTIONS: self._gen_calcul_fractions,
            MathExerciseType.CALCUL_DECIMAUX: self._gen_calcul_decimaux,
            MathExerciseType.EQUATION_1ER_DEGRE: self._gen_equation_1er_degre,
            MathExerciseType.TRIANGLE_RECTANGLE: self._gen_triangle_rectangle,
            MathExerciseType.TRIANGLE_QUELCONQUE: self._gen_triangle_quelconque,
            MathExerciseType.PROPORTIONNALITE: self._gen_proportionnalite,
            MathExerciseType.PERIMETRE_AIRE: self._gen_perimetre_aire,
            MathExerciseType.RECTANGLE: self._gen_rectangle,
            MathExerciseType.VOLUME: self._gen_volume,
            MathExerciseType.STATISTIQUES: self._gen_statistiques,
            MathExerciseType.PROBABILITES: self._gen_probabilites,
            MathExerciseType.PUISSANCES: self._gen_puissances,
            MathExerciseType.CERCLE: self._gen_cercle,
            MathExerciseType.THALES: self._gen_thales,
            MathExerciseType.TRIGONOMETRIE: self._gen_trigonometrie
        }
        
        generator = generators.get(exercise_type)
        if generator:
            return generator(niveau, chapitre, difficulte)
        else:
            # Fallback
            return self._gen_calcul_decimaux(niveau, chapitre, difficulte)
    
    def _get_next_geometry_points(self) -> List[str]:
        """Retourne le prochain set de points géométriques non utilisé"""
        for point_set in self.geometry_points_sets:
            point_tuple = tuple(point_set)
            if point_tuple not in self.used_points_sets:
                self.used_points_sets.add(point_tuple)
                return point_set.copy()
        
        # Si tous utilisés, recommencer avec le premier
        self.used_points_sets.clear()
        self.used_points_sets.add(tuple(self.geometry_points_sets[0]))
        return self.geometry_points_sets[0].copy()
    
    # === GÉNÉRATEURS SPÉCIALISÉS ===
    
    def _gen_triangle_rectangle(
        self, niveau: str, chapitre: str, difficulte: str
    ) -> MathExerciseSpec:
        """Génère un exercice de triangle rectangle (Pythagore)
        
        RÈGLE CRITIQUE : Toutes les longueurs dans l'énoncé (longueurs_connues) 
        doivent être des entiers ou décimaux simples, JAMAIS des valeurs irrationnelles.
        """
        
        points = self._get_next_geometry_points()
        angle_droit = points[1]  # Point de l'angle droit (milieu par défaut)
        
        # Triplets pythagoriciens exacts pour garantir des valeurs entières
        triplets_faciles = [
            (3, 4, 5), (5, 12, 13), (6, 8, 10), (7, 24, 25), 
            (8, 15, 17), (9, 12, 15), (9, 40, 41), (12, 16, 20)
        ]
        
        triplets_difficiles = [
            (11, 60, 61), (13, 84, 85), (20, 21, 29), (28, 45, 53),
            (33, 56, 65), (36, 77, 85), (5, 12, 13), (8, 15, 17)
        ]
        
        # Choisir un triplet selon la difficulté
        if difficulte == "facile":
            a, b, c = random.choice(triplets_faciles)
        else:
            a, b, c = random.choice(triplets_difficiles)
        
        # Décider quel côté calculer
        calcul_type = random.choice(["hypotenuse", "cote"])
        
        if calcul_type == "hypotenuse":
            # CAS 1 : Calculer l'hypoténuse
            # Donner les deux côtés de l'angle droit (a et b)
            # L'élève doit calculer l'hypoténuse (c)
            longueurs_connues = {
                f"{points[0]}{points[1]}": a,  # Premier côté
                f"{points[1]}{points[2]}": b   # Deuxième côté
            }
            longueur_a_calculer = f"{points[0]}{points[2]}"  # Hypoténuse
            resultat = c
            
            etapes = [
                f"Le triangle {points[0]}{points[1]}{points[2]} est rectangle en {angle_droit}",
                "D'après le théorème de Pythagore :",
                f"{longueur_a_calculer}² = {points[0]}{points[1]}² + {points[1]}{points[2]}²",
                f"{longueur_a_calculer}² = {a}² + {b}² = {a*a} + {b*b} = {a*a + b*b}",
                f"{longueur_a_calculer} = √{a*a + b*b} = {c} cm"
            ]
            
        else:
            # CAS 2 : Calculer un côté de l'angle droit
            # Donner l'hypoténuse (c) et un côté (a)
            # L'élève doit calculer l'autre côté (b)
            longueurs_connues = {
                f"{points[0]}{points[1]}": a,      # Côté connu
                f"{points[0]}{points[2]}": c       # Hypoténuse
            }
            longueur_a_calculer = f"{points[1]}{points[2]}"  # Côté à calculer
            resultat = b
            
            etapes = [
                f"Le triangle {points[0]}{points[1]}{points[2]} est rectangle en {angle_droit}",
                "D'après le théorème de Pythagore :",
                f"{points[0]}{points[2]}² = {points[0]}{points[1]}² + {longueur_a_calculer}²",
                f"{c}² = {a}² + {longueur_a_calculer}²",
                f"{longueur_a_calculer}² = {c}² - {a}² = {c*c} - {a*a} = {c*c - a*a}",
                f"{longueur_a_calculer} = √{c*c - a*a} = {b} cm"
            ]
        
        # Créer la figure géométrique avec UNIQUEMENT des valeurs entières
        figure = GeometricFigure(
            type="triangle_rectangle",
            points=points,
            rectangle_en=angle_droit,
            longueurs_connues=longueurs_connues,  # ✅ Uniquement des entiers
            longueurs_a_calculer=[longueur_a_calculer]
        )
        
        return MathExerciseSpec(
            niveau=niveau,
            chapitre=chapitre,
            type_exercice=MathExerciseType.TRIANGLE_RECTANGLE,
            difficulte=DifficultyLevel(difficulte),
            parametres={
                "triangle": f"{points[0]}{points[1]}{points[2]}",
                "angle_droit": angle_droit,
                "longueurs_donnees": longueurs_connues,
                "longueur_a_calculer": longueur_a_calculer,
                "triplet_utilise": f"({a}, {b}, {c})"
            },
            solution_calculee={
                "longueur_calculee": resultat,
                "unite": "cm",
                "methode": "pythagore",
                "triplet": f"({a}, {b}, {c})"
            },
            etapes_calculees=etapes,
            resultat_final=f"{resultat} cm",  # ✅ Entier, pas de décimale
            figure_geometrique=figure,
            points_bareme=[
                {"etape": "Identification théorème de Pythagore", "points": 1.0},
                {"etape": "Application formule", "points": 2.0},
                {"etape": "Calcul et résultat", "points": 1.0}
            ]
        )
    
    def _gen_calcul_relatifs(
        self, niveau: str, chapitre: str, difficulte: str
    ) -> MathExerciseSpec:
        """Génère un exercice de calculs avec nombres relatifs"""
        
        if difficulte == "facile":
            operandes = [random.randint(-10, 10) for _ in range(3)]
            operations_list = ["+", "-"]
        else:
            operandes = [random.randint(-20, 20) for _ in range(4)]
            operations_list = ["+", "-", "*"] if difficulte == "difficile" else ["+", "-"]
        
        # Construire l'expression et stocker les opérations
        expression = str(operandes[0])
        operations_used = []
        
        for i in range(1, len(operandes)):
            op = random.choice(operations_list)
            operations_used.append(op)
            operand = operandes[i]
            
            if op == "+" and operand >= 0:
                expression += f" + {operand}"
            elif op == "+" and operand < 0:
                expression += f" + ({operand})"
            elif op == "-" and operand >= 0:
                expression += f" - {operand}"
            elif op == "-" and operand < 0:
                expression += f" - ({operand})"
            elif op == "*":
                expression += f" × {operand}"
        
        # Calculer le résultat correctement
        resultat = operandes[0]
        for i, op in enumerate(operations_used):
            operand = operandes[i + 1]
            if op == "+":
                resultat += operand
            elif op == "-":
                resultat -= operand
            elif op == "*":
                resultat *= operand
        
        # Construire les étapes
        etapes = [
            f"Expression à calculer : {expression}",
            "Calcul étape par étape :",
        ]
        
        # Détailler les étapes intermédiaires
        intermediate = operandes[0]
        for i, op in enumerate(operations_used):
            operand = operandes[i + 1]
            if op == "+":
                intermediate += operand
            elif op == "-":
                intermediate -= operand
            elif op == "*":
                intermediate *= operand
            etapes.append(f"= {intermediate}")
        
        return MathExerciseSpec(
            niveau=niveau,
            chapitre=chapitre,
            type_exercice=MathExerciseType.CALCUL_RELATIFS,
            difficulte=DifficultyLevel(difficulte),
            parametres={
                "expression": expression,
                "operandes": operandes,
                "operations": operations_used
            },
            solution_calculee={
                "resultat": resultat,
                "methode": "calcul_step_by_step"
            },
            etapes_calculees=etapes,
            resultat_final=resultat,
            points_bareme=[
                {"etape": "Organisation du calcul", "points": 1.0},
                {"etape": "Calculs intermédiaires", "points": 2.0},
                {"etape": "Résultat final", "points": 1.0}
            ]
        )
    
    def _gen_equation_1er_degre(
        self, niveau: str, chapitre: str, difficulte: str
    ) -> MathExerciseSpec:
        """Génère une équation du premier degré"""
        
        # Choisir la solution d'abord (pour éviter fractions complexes)
        x_solution = random.randint(1, 10) if difficulte == "facile" else random.randint(-5, 15)
        
        # Générer coefficients
        a = random.randint(2, 8)
        b = random.randint(-10, 10)
        
        # Calculer c pour que x_solution soit la solution
        c = a * x_solution + b
        
        equation = f"{a}x + {b} = {c}"
        
        etapes = [
            f"Équation : {equation}",
            f"{a}x = {c} - {b}",
            f"{a}x = {c - b}",
            f"x = {c - b} ÷ {a}",
            f"x = {x_solution}"
        ]
        
        return MathExerciseSpec(
            niveau=niveau,
            chapitre=chapitre,
            type_exercice=MathExerciseType.EQUATION_1ER_DEGRE,
            difficulte=DifficultyLevel(difficulte),
            parametres={
                "forme": "ax + b = c",
                "a": a,
                "b": b, 
                "c": c,
                "equation": equation
            },
            solution_calculee={
                "x": x_solution,
                "verification": f"{a} × {x_solution} + {b} = {a * x_solution + b}"
            },
            etapes_calculees=etapes,
            resultat_final=f"x = {x_solution}",
            points_bareme=[
                {"etape": "Isoler le terme en x", "points": 2.0},
                {"etape": "Division finale", "points": 1.0},
                {"etape": "Vérification", "points": 1.0}
            ]
        )
    
    # Générateurs supplémentaires (simplifiés pour l'exemple)
    
    def _gen_calcul_fractions(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
        """Génère un exercice de calculs avec fractions"""
        
        if difficulte == "facile":
            # Fractions simples avec dénominateurs petits
            num1, den1 = random.randint(1, 5), random.choice([2, 3, 4, 5])
            num2, den2 = random.randint(1, 5), random.choice([2, 3, 4, 5])
        else:
            num1, den1 = random.randint(1, 10), random.randint(2, 12)
            num2, den2 = random.randint(1, 10), random.randint(2, 12)
        
        frac1 = Fraction(num1, den1)
        frac2 = Fraction(num2, den2)
        
        operation = random.choice(["+", "-"])
        
        if operation == "+":
            resultat = frac1 + frac2
            expression = f"\\frac{{{num1}}}{{{den1}}} + \\frac{{{num2}}}{{{den2}}}"
        else:
            resultat = frac1 - frac2
            expression = f"\\frac{{{num1}}}{{{den1}}} - \\frac{{{num2}}}{{{den2}}}"
        
        etapes = [
            f"Expression : {expression}",
            f"Trouver un dénominateur commun : {frac1.denominator * frac2.denominator // math.gcd(frac1.denominator, frac2.denominator)}",
            f"Résultat : \\frac{{{resultat.numerator}}}{{{resultat.denominator}}}"
        ]
        
        return MathExerciseSpec(
            niveau=niveau,
            chapitre=chapitre,
            type_exercice=MathExerciseType.CALCUL_FRACTIONS,
            difficulte=DifficultyLevel(difficulte),
            parametres={
                "fraction1": f"{num1}/{den1}",
                "fraction2": f"{num2}/{den2}",
                "operation": operation,
                "expression": expression
            },
            solution_calculee={
                "resultat_fraction": f"{resultat.numerator}/{resultat.denominator}",
                "resultat_decimal": float(resultat)
            },
            etapes_calculees=etapes,
            resultat_final=f"\\frac{{{resultat.numerator}}}{{{resultat.denominator}}}"
        )
    
    def _gen_calcul_decimaux(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
        """Génère un exercice de calculs avec nombres décimaux"""
        
        if difficulte == "facile":
            a = round(random.uniform(1, 20), 1)
            b = round(random.uniform(1, 20), 1)
        else:
            a = round(random.uniform(5, 50), 2)
            b = round(random.uniform(5, 50), 2)
        
        operation = random.choice(["+", "-", "*"])
        
        if operation == "+":
            resultat = round(a + b, 2)
            expression = f"{a} + {b}"
            op_text = "addition"
        elif operation == "-":
            resultat = round(a - b, 2)
            expression = f"{a} - {b}"
            op_text = "soustraction"
        else:
            resultat = round(a * b, 2)
            expression = f"{a} × {b}"
            op_text = "multiplication"
        
        etapes = [
            f"Calcul : {expression}",
            f"Résultat : {resultat}"
        ]
        
        return MathExerciseSpec(
            niveau=niveau,
            chapitre=chapitre,
            type_exercice=MathExerciseType.CALCUL_DECIMAUX,
            difficulte=DifficultyLevel(difficulte),
            parametres={
                "a": a,
                "b": b,
                "operation": operation,
                "expression": expression
            },
            solution_calculee={
                "resultat": resultat,
                "operation": op_text
            },
            etapes_calculees=etapes,
            resultat_final=resultat
        )
    
    def _gen_triangle_quelconque(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
        """Génère un exercice sur triangle quelconque (angles)"""
        
        points = self._get_next_geometry_points()
        
        # Générer deux angles, le troisième se déduit
        angle1 = random.randint(30, 80)
        angle2 = random.randint(30, 80)
        angle3 = 180 - angle1 - angle2
        
        # Vérifier que le troisième angle est valide
        if angle3 <= 0 or angle3 >= 150:
            angle1 = 60
            angle2 = 70
            angle3 = 50
        
        figure = GeometricFigure(
            type="triangle",
            points=points,
            angles_connus={
                f"{points[0]}{points[1]}{points[2]}": angle1,
                f"{points[1]}{points[2]}{points[0]}": angle2
            },
            angles_a_calculer=[f"{points[2]}{points[0]}{points[1]}"]
        )
        
        etapes = [
            f"Triangle {points[0]}{points[1]}{points[2]}",
            "La somme des angles d'un triangle est 180°",
            f"Angle en {points[0]} = {angle1}°, Angle en {points[1]} = {angle2}°",
            f"Angle en {points[2]} = 180° - {angle1}° - {angle2}° = {angle3}°"
        ]
        
        return MathExerciseSpec(
            niveau=niveau,
            chapitre=chapitre,
            type_exercice=MathExerciseType.TRIANGLE_QUELCONQUE,
            difficulte=DifficultyLevel(difficulte),
            parametres={
                "triangle": f"{points[0]}{points[1]}{points[2]}",
                "angle1": angle1,
                "angle2": angle2
            },
            solution_calculee={
                "angle3": angle3
            },
            etapes_calculees=etapes,
            resultat_final=f"{angle3}°",
            figure_geometrique=figure
        )
    
    def _gen_proportionnalite(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
        """Génère un exercice de proportionnalité"""
        
        # Coefficient de proportionnalité
        k = random.randint(2, 8)
        
        # Valeurs du tableau
        val1 = random.randint(3, 10)
        val2 = random.randint(12, 25)
        val3 = random.randint(5, 15)  # Valeur à trouver
        
        resultat1 = val1 * k
        resultat2 = val2 * k
        resultat_a_trouver = val3 * k
        
        etapes = [
            "Tableau de proportionnalité",
            f"{val1} → {resultat1}",
            f"{val2} → {resultat2}",
            f"Coefficient : {k}",
            f"{val3} → {val3} × {k} = {resultat_a_trouver}"
        ]
        
        return MathExerciseSpec(
            niveau=niveau,
            chapitre=chapitre,
            type_exercice=MathExerciseType.PROPORTIONNALITE,
            difficulte=DifficultyLevel(difficulte),
            parametres={
                "valeurs_donnees": [val1, val2],
                "resultats_donnes": [resultat1, resultat2],
                "valeur_a_trouver": val3,
                "coefficient": k
            },
            solution_calculee={
                "resultat": resultat_a_trouver,
                "methode": "produit_en_croix"
            },
            etapes_calculees=etapes,
            resultat_final=resultat_a_trouver
        )
    
    def _gen_perimetre_aire(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
        """Génère un exercice de périmètres et aires"""
        
        figure_type = random.choice(["rectangle", "carre", "cercle"])
        
        if figure_type == "rectangle":
            longueur = random.randint(8, 20)
            largeur = random.randint(4, 12)
            perimetre = 2 * (longueur + largeur)
            aire = longueur * largeur
            
            return MathExerciseSpec(
                niveau=niveau,
                chapitre=chapitre,
                type_exercice=MathExerciseType.PERIMETRE_AIRE,
                difficulte=DifficultyLevel(difficulte),
                parametres={
                    "figure": "rectangle",
                    "longueur": longueur,
                    "largeur": largeur
                },
                solution_calculee={
                    "perimetre": perimetre,
                    "aire": aire
                },
                etapes_calculees=[
                    f"Rectangle de longueur {longueur} cm et largeur {largeur} cm",
                    f"Périmètre = 2 × ({longueur} + {largeur}) = {perimetre} cm",
                    f"Aire = {longueur} × {largeur} = {aire} cm²"
                ],
                resultat_final=f"Périmètre = {perimetre} cm, Aire = {aire} cm²"
            )
        
        elif figure_type == "carre":
            cote = random.randint(5, 15)
            perimetre = 4 * cote
            aire = cote * cote
            
            return MathExerciseSpec(
                niveau=niveau,
                chapitre=chapitre,
                type_exercice=MathExerciseType.PERIMETRE_AIRE,
                difficulte=DifficultyLevel(difficulte),
                parametres={
                    "figure": "carre",
                    "cote": cote
                },
                solution_calculee={
                    "perimetre": perimetre,
                    "aire": aire
                },
                etapes_calculees=[
                    f"Carré de côté {cote} cm",
                    f"Périmètre = 4 × {cote} = {perimetre} cm",
                    f"Aire = {cote}² = {aire} cm²"
                ],
                resultat_final=f"Périmètre = {perimetre} cm, Aire = {aire} cm²"
            )
        
        else:  # cercle
            rayon = random.randint(3, 10)
            perimetre = round(2 * math.pi * rayon, 2)
            aire = round(math.pi * rayon * rayon, 2)
            
            return MathExerciseSpec(
                niveau=niveau,
                chapitre=chapitre,
                type_exercice=MathExerciseType.PERIMETRE_AIRE,
                difficulte=DifficultyLevel(difficulte),
                parametres={
                    "figure": "cercle",
                    "rayon": rayon
                },
                solution_calculee={
                    "perimetre": perimetre,
                    "aire": aire
                },
                etapes_calculees=[
                    f"Cercle de rayon {rayon} cm",
                    f"Périmètre = 2 × π × {rayon} ≈ {perimetre} cm",
                    f"Aire = π × {rayon}² ≈ {aire} cm²"
                ],
                resultat_final=f"Périmètre ≈ {perimetre} cm, Aire ≈ {aire} cm²"
            )
    
    def _gen_rectangle(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
        """Générateur pour rectangles"""
        points = self._get_next_geometry_points()[:4]  # P, Q, R, S par défaut
        
        longueur = random.randint(8, 20)
        largeur = random.randint(4, 12)
        
        figure = GeometricFigure(
            type="rectangle",
            points=points,
            longueurs_connues={
                f"{points[0]}{points[1]}": largeur,
                f"{points[1]}{points[2]}": longueur
            },
            proprietes=["rectangle"]
        )
        
        perimetre = 2 * (longueur + largeur)
        aire = longueur * largeur
        
        return MathExerciseSpec(
            niveau=niveau,
            chapitre=chapitre,
            type_exercice=MathExerciseType.RECTANGLE,
            difficulte=DifficultyLevel(difficulte),
            parametres={
                "longueur": longueur,
                "largeur": largeur,
                "rectangle": f"{points[0]}{points[1]}{points[2]}{points[3]}"
            },
            solution_calculee={
                "perimetre": perimetre,
                "aire": aire
            },
            etapes_calculees=[
                f"Rectangle {points[0]}{points[1]}{points[2]}{points[3]}",
                f"Longueur = {longueur} cm, largeur = {largeur} cm",
                f"Périmètre = 2 × ({longueur} + {largeur}) = {perimetre} cm",
                f"Aire = {longueur} × {largeur} = {aire} cm²"
            ],
            resultat_final=f"Périmètre = {perimetre} cm, Aire = {aire} cm²",
            figure_geometrique=figure
        )

    def _gen_volume(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
        """Génère un exercice de calcul de volumes"""
        
        solides = ["cube", "pave", "cylindre", "prisme"]
        
        if difficulte == "facile":
            solides = ["cube", "pave"]
        
        solide = random.choice(solides)
        
        if solide == "cube":
            arete = random.randint(3, 12)
            volume = arete ** 3
            
            etapes = [
                f"Cube d'arête {arete} cm",
                "Volume = arête³",
                f"Volume = {arete}³ = {arete} × {arete} × {arete}",
                f"Volume = {volume} cm³"
            ]
            
            return MathExerciseSpec(
                niveau=niveau,
                chapitre=chapitre,
                type_exercice=MathExerciseType.VOLUME,
                difficulte=DifficultyLevel(difficulte),
                parametres={
                    "solide": "cube",
                    "arete": arete
                },
                solution_calculee={
                    "volume": volume,
                    "unite": "cm³"
                },
                etapes_calculees=etapes,
                resultat_final=f"{volume} cm³"
            )
        
        elif solide == "pave":
            longueur = random.randint(5, 15)
            largeur = random.randint(4, 12)
            hauteur = random.randint(3, 10)
            volume = longueur * largeur * hauteur
            
            etapes = [
                f"Pavé droit de dimensions {longueur} cm × {largeur} cm × {hauteur} cm",
                "Volume = longueur × largeur × hauteur",
                f"Volume = {longueur} × {largeur} × {hauteur}",
                f"Volume = {volume} cm³"
            ]
            
            return MathExerciseSpec(
                niveau=niveau,
                chapitre=chapitre,
                type_exercice=MathExerciseType.VOLUME,
                difficulte=DifficultyLevel(difficulte),
                parametres={
                    "solide": "pave",
                    "longueur": longueur,
                    "largeur": largeur,
                    "hauteur": hauteur
                },
                solution_calculee={
                    "volume": volume,
                    "unite": "cm³"
                },
                etapes_calculees=etapes,
                resultat_final=f"{volume} cm³"
            )
        
        elif solide == "cylindre":
            rayon = random.randint(3, 10)
            hauteur = random.randint(5, 15)
            volume = round(math.pi * rayon * rayon * hauteur, 2)
            
            etapes = [
                f"Cylindre de rayon {rayon} cm et hauteur {hauteur} cm",
                "Volume = π × rayon² × hauteur",
                f"Volume = π × {rayon}² × {hauteur}",
                f"Volume = π × {rayon * rayon} × {hauteur}",
                f"Volume ≈ {volume} cm³"
            ]
            
            return MathExerciseSpec(
                niveau=niveau,
                chapitre=chapitre,
                type_exercice=MathExerciseType.VOLUME,
                difficulte=DifficultyLevel(difficulte),
                parametres={
                    "solide": "cylindre",
                    "rayon": rayon,
                    "hauteur": hauteur
                },
                solution_calculee={
                    "volume": volume,
                    "unite": "cm³"
                },
                etapes_calculees=etapes,
                resultat_final=f"{volume} cm³"
            )
        
        else:  # prisme
            base_longueur = random.randint(5, 12)
            base_largeur = random.randint(4, 10)
            hauteur = random.randint(6, 15)
            aire_base = base_longueur * base_largeur
            volume = aire_base * hauteur
            
            etapes = [
                f"Prisme droit à base rectangulaire ({base_longueur} cm × {base_largeur} cm), hauteur {hauteur} cm",
                "Volume = aire de la base × hauteur",
                f"Aire de la base = {base_longueur} × {base_largeur} = {aire_base} cm²",
                f"Volume = {aire_base} × {hauteur} = {volume} cm³"
            ]
            
            return MathExerciseSpec(
                niveau=niveau,
                chapitre=chapitre,
                type_exercice=MathExerciseType.VOLUME,
                difficulte=DifficultyLevel(difficulte),
                parametres={
                    "solide": "prisme",
                    "base_longueur": base_longueur,
                    "base_largeur": base_largeur,
                    "hauteur": hauteur
                },
                solution_calculee={
                    "volume": volume,
                    "aire_base": aire_base,
                    "unite": "cm³"
                },
                etapes_calculees=etapes,
                resultat_final=f"{volume} cm³"
            )
    
    def _gen_statistiques(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
        """Génère un exercice de statistiques (moyenne, médiane, étendue)"""
        
        # Générer une série de données
        if difficulte == "facile":
            nb_valeurs = random.randint(5, 8)
            valeurs = [random.randint(5, 20) for _ in range(nb_valeurs)]
        else:
            nb_valeurs = random.randint(8, 12)
            valeurs = [random.randint(0, 30) for _ in range(nb_valeurs)]
        
        # Calculs statistiques
        moyenne = round(sum(valeurs) / len(valeurs), 2)
        valeurs_triees = sorted(valeurs)
        
        # Médiane
        n = len(valeurs_triees)
        if n % 2 == 0:
            mediane = (valeurs_triees[n//2 - 1] + valeurs_triees[n//2]) / 2
        else:
            mediane = valeurs_triees[n//2]
        
        # Étendue
        etendue = max(valeurs) - min(valeurs)
        
        etapes = [
            f"Série de données : {valeurs}",
            f"Nombre de valeurs : {len(valeurs)}",
            f"Moyenne = somme / effectif = {sum(valeurs)} / {len(valeurs)} = {moyenne}",
            f"Série triée : {valeurs_triees}",
            f"Médiane = {mediane}",
            f"Étendue = max - min = {max(valeurs)} - {min(valeurs)} = {etendue}"
        ]
        
        return MathExerciseSpec(
            niveau=niveau,
            chapitre=chapitre,
            type_exercice=MathExerciseType.STATISTIQUES,
            difficulte=DifficultyLevel(difficulte),
            parametres={
                "valeurs": valeurs,
                "nb_valeurs": len(valeurs)
            },
            solution_calculee={
                "moyenne": moyenne,
                "mediane": mediane,
                "etendue": etendue,
                "min": min(valeurs),
                "max": max(valeurs)
            },
            etapes_calculees=etapes,
            resultat_final=f"Moyenne = {moyenne}, Médiane = {mediane}, Étendue = {etendue}"
        )
    
    def _gen_probabilites(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
        """Génère un exercice de probabilités"""
        
        situations = [
            {
                "contexte": "dé",
                "nb_issues": 6,
                "question": "obtenir un nombre pair",
                "issues_favorables": 3
            },
            {
                "contexte": "dé",
                "nb_issues": 6,
                "question": "obtenir un nombre supérieur à 4",
                "issues_favorables": 2
            },
            {
                "contexte": "pièce",
                "nb_issues": 2,
                "question": "obtenir pile",
                "issues_favorables": 1
            },
            {
                "contexte": "sac avec 5 boules rouges et 3 boules bleues",
                "nb_issues": 8,
                "question": "tirer une boule rouge",
                "issues_favorables": 5
            }
        ]
        
        situation = random.choice(situations)
        
        probabilite = situation["issues_favorables"] / situation["nb_issues"]
        probabilite_fraction = Fraction(situation["issues_favorables"], situation["nb_issues"])
        
        etapes = [
            f"Expérience : {situation['contexte']}",
            f"Nombre d'issues possibles : {situation['nb_issues']}",
            f"Nombre d'issues favorables ({situation['question']}) : {situation['issues_favorables']}",
            "Probabilité = issues favorables / issues possibles",
            f"Probabilité = {situation['issues_favorables']} / {situation['nb_issues']}",
            f"Probabilité = {probabilite_fraction} = {probabilite:.2f}"
        ]
        
        return MathExerciseSpec(
            niveau=niveau,
            chapitre=chapitre,
            type_exercice=MathExerciseType.PROBABILITES,
            difficulte=DifficultyLevel(difficulte),
            parametres={
                "contexte": situation["contexte"],
                "question": situation["question"],
                "nb_issues": situation["nb_issues"],
                "issues_favorables": situation["issues_favorables"]
            },
            solution_calculee={
                "probabilite": probabilite,
                "fraction": f"{probabilite_fraction.numerator}/{probabilite_fraction.denominator}"
            },
            etapes_calculees=etapes,
            resultat_final=f"\\frac{{{probabilite_fraction.numerator}}}{{{probabilite_fraction.denominator}}}"
        )
    
    def _gen_puissances(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
        """Génère un exercice sur les puissances"""
        
        type_calcul = random.choice(["calcul_simple", "produit", "quotient"])
        
        if type_calcul == "calcul_simple":
            base = random.randint(2, 10)
            exposant = random.randint(2, 5) if difficulte == "facile" else random.randint(3, 6)
            resultat = base ** exposant
            
            etapes = [
                f"Calculer {base}^{{{exposant}}}",
                f"{base}^{{{exposant}}} = " + " × ".join([str(base)] * exposant),
                f"{base}^{{{exposant}}} = {resultat}"
            ]
            
            return MathExerciseSpec(
                niveau=niveau,
                chapitre=chapitre,
                type_exercice=MathExerciseType.PUISSANCES,
                difficulte=DifficultyLevel(difficulte),
                parametres={
                    "type": "calcul_simple",
                    "base": base,
                    "exposant": exposant
                },
                solution_calculee={
                    "resultat": resultat
                },
                etapes_calculees=etapes,
                resultat_final=resultat
            )
        
        elif type_calcul == "produit":
            base = random.randint(2, 8)
            exp1 = random.randint(2, 4)
            exp2 = random.randint(2, 4)
            exp_somme = exp1 + exp2
            resultat = base ** exp_somme
            
            etapes = [
                f"Calculer {base}^{{{exp1}}} × {base}^{{{exp2}}}",
                "Propriété : a^m × a^n = a^(m+n)",
                f"{base}^{{{exp1}}} × {base}^{{{exp2}}} = {base}^{{{exp1}+{exp2}}}",
                f"{base}^{{{exp1}}} × {base}^{{{exp2}}} = {base}^{{{exp_somme}}}",
                f"{base}^{{{exp_somme}}} = {resultat}"
            ]
            
            return MathExerciseSpec(
                niveau=niveau,
                chapitre=chapitre,
                type_exercice=MathExerciseType.PUISSANCES,
                difficulte=DifficultyLevel(difficulte),
                parametres={
                    "type": "produit",
                    "base": base,
                    "exposant1": exp1,
                    "exposant2": exp2
                },
                solution_calculee={
                    "exposant_somme": exp_somme,
                    "resultat": resultat
                },
                etapes_calculees=etapes,
                resultat_final=resultat
            )
        
        else:  # quotient
            base = random.randint(2, 8)
            exp1 = random.randint(4, 7)
            exp2 = random.randint(2, exp1-1)  # exp2 < exp1 pour éviter exposants négatifs
            exp_diff = exp1 - exp2
            resultat = base ** exp_diff
            
            etapes = [
                f"Calculer {base}^{{{exp1}}} ÷ {base}^{{{exp2}}}",
                "Propriété : a^m ÷ a^n = a^(m-n)",
                f"{base}^{{{exp1}}} ÷ {base}^{{{exp2}}} = {base}^{{{exp1}-{exp2}}}",
                f"{base}^{{{exp1}}} ÷ {base}^{{{exp2}}} = {base}^{{{exp_diff}}}",
                f"{base}^{{{exp_diff}}} = {resultat}"
            ]
            
            return MathExerciseSpec(
                niveau=niveau,
                chapitre=chapitre,
                type_exercice=MathExerciseType.PUISSANCES,
                difficulte=DifficultyLevel(difficulte),
                parametres={
                    "type": "quotient",
                    "base": base,
                    "exposant1": exp1,
                    "exposant2": exp2
                },
                solution_calculee={
                    "exposant_diff": exp_diff,
                    "resultat": resultat
                },
                etapes_calculees=etapes,
                resultat_final=resultat
            )

    def _gen_cercle(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
        """Génère un exercice sur les cercles (périmètre, aire)"""
        
        type_calcul = random.choice(["perimetre", "aire", "rayon_depuis_perimetre"])
        
        if type_calcul == "perimetre":
            rayon = random.randint(3, 15)
            perimetre = round(2 * math.pi * rayon, 2)
            
            etapes = [
                f"Cercle de rayon {rayon} cm",
                "Périmètre = 2 × π × rayon",
                f"Périmètre = 2 × π × {rayon}",
                f"Périmètre ≈ {perimetre} cm"
            ]
            
            return MathExerciseSpec(
                niveau=niveau,
                chapitre=chapitre,
                type_exercice=MathExerciseType.CERCLE,
                difficulte=DifficultyLevel(difficulte),
                parametres={
                    "type": "perimetre",
                    "rayon": rayon
                },
                solution_calculee={
                    "perimetre": perimetre,
                    "unite": "cm"
                },
                etapes_calculees=etapes,
                resultat_final=f"{perimetre} cm"
            )
        
        elif type_calcul == "aire":
            rayon = random.randint(3, 12)
            aire = round(math.pi * rayon * rayon, 2)
            
            etapes = [
                f"Cercle de rayon {rayon} cm",
                "Aire = π × rayon²",
                f"Aire = π × {rayon}²",
                f"Aire = π × {rayon * rayon}",
                f"Aire ≈ {aire} cm²"
            ]
            
            return MathExerciseSpec(
                niveau=niveau,
                chapitre=chapitre,
                type_exercice=MathExerciseType.CERCLE,
                difficulte=DifficultyLevel(difficulte),
                parametres={
                    "type": "aire",
                    "rayon": rayon
                },
                solution_calculee={
                    "aire": aire,
                    "unite": "cm²"
                },
                etapes_calculees=etapes,
                resultat_final=f"{aire} cm²"
            )
        
        else:  # rayon depuis périmètre
            rayon = random.randint(5, 12)
            perimetre = round(2 * math.pi * rayon, 2)
            
            etapes = [
                f"Périmètre du cercle = {perimetre} cm",
                "Périmètre = 2 × π × rayon",
                f"{perimetre} = 2 × π × rayon",
                f"rayon = {perimetre} / (2 × π)",
                f"rayon ≈ {rayon} cm"
            ]
            
            return MathExerciseSpec(
                niveau=niveau,
                chapitre=chapitre,
                type_exercice=MathExerciseType.CERCLE,
                difficulte=DifficultyLevel(difficulte),
                parametres={
                    "type": "rayon_depuis_perimetre",
                    "perimetre": perimetre
                },
                solution_calculee={
                    "rayon": rayon,
                    "unite": "cm"
                },
                etapes_calculees=etapes,
                resultat_final=f"{rayon} cm"
            )
    
    def _gen_thales(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
        """Génère un exercice sur le théorème de Thalès"""
        
        # Obtenir 2 sets de points (3+3 = 6 points, on en utilisera 5)
        points_set1 = self._get_next_geometry_points()  # A, B, C
        points_set2 = self._get_next_geometry_points()  # D, E, F (on prendra D, E)
        points = points_set1 + points_set2[:2]  # A, B, C, D, E
        
        # Configuration : triangle ABC avec droite (DE) parallèle à (BC)
        # D sur [AB], E sur [AC]
        
        # Choisir des rapports simples
        if difficulte == "facile":
            rapports = [2, 3, 4]
            k = random.choice(rapports)
        else:
            k = random.randint(2, 5)
        
        # Longueurs
        AD = random.randint(3, 8)
        AE = random.randint(3, 8)
        
        # DB = k × AD (pour que AB = AD + DB)
        DB = k * AD
        AB = AD + DB
        
        # EC = k × AE
        EC = k * AE
        AC = AE + EC
        
        # DE = BC / k (proportionnalité)
        BC = random.randint(10, 20)
        DE = round(BC / (k + 1), 2)
        
        etapes = [
            f"Triangle {points[0]}{points[1]}{points[2]} avec (DE) // (BC)",
            f"{points[3]} sur [{points[0]}{points[1]}], {points[4]} sur [{points[0]}{points[2]}]",
            "D'après le théorème de Thalès :",
            f"{points[0]}{points[3]}/{points[0]}{points[1]} = {points[0]}{points[4]}/{points[0]}{points[2]} = {points[3]}{points[4]}/{points[1]}{points[2]}",
            f"{AD}/{AB} = {AE}/{AC}",
            f"Rapport = {AD}/{AB} = {AD}/{AD + DB} ≈ {round(AD/AB, 2)}"
        ]
        
        figure = GeometricFigure(
            type="thales",
            points=points[:5],
            longueurs_connues={
                f"{points[0]}{points[3]}": AD,
                f"{points[3]}{points[1]}": DB,
                f"{points[0]}{points[4]}": AE,
                f"{points[4]}{points[2]}": EC
            },
            proprietes=["thales", f"({points[3]}{points[4]}) // ({points[1]}{points[2]})"]
        )
        
        return MathExerciseSpec(
            niveau=niveau,
            chapitre=chapitre,
            type_exercice=MathExerciseType.THALES,
            difficulte=DifficultyLevel(difficulte),
            parametres={
                "points": points[:5],
                "AD": AD,
                "DB": DB,
                "AE": AE,
                "EC": EC,
                "rapport": round(AD/AB, 2)
            },
            solution_calculee={
                "AB": AB,
                "AC": AC,
                "rapport": round(AD/AB, 2)
            },
            etapes_calculees=etapes,
            resultat_final=f"Rapport = {round(AD/AB, 2)}",
            figure_geometrique=figure
        )
    
    def _gen_trigonometrie(self, niveau: str, chapitre: str, difficulte: str) -> MathExerciseSpec:
        """Génère un exercice de trigonométrie"""
        
        points = self._get_next_geometry_points()
        
        # Angles remarquables
        angles_remarquables = {
            30: {"sin": 0.5, "cos": round(math.sqrt(3)/2, 4), "tan": round(1/math.sqrt(3), 4)},
            45: {"sin": round(math.sqrt(2)/2, 4), "cos": round(math.sqrt(2)/2, 4), "tan": 1.0},
            60: {"sin": round(math.sqrt(3)/2, 4), "cos": 0.5, "tan": round(math.sqrt(3), 4)}
        }
        
        if difficulte == "facile":
            angle = random.choice([30, 45, 60])
        else:
            angle = random.randint(25, 70)
        
        type_calcul = random.choice(["cote_oppose", "cote_adjacent", "hypotenuse"])
        
        if type_calcul == "cote_oppose":
            # Calculer le côté opposé avec sin
            hypotenuse = random.randint(10, 20)
            
            if angle in angles_remarquables:
                sin_angle = angles_remarquables[angle]["sin"]
            else:
                sin_angle = round(math.sin(math.radians(angle)), 4)
            
            cote_oppose = round(hypotenuse * sin_angle, 2)
            
            etapes = [
                f"Triangle rectangle {points[0]}{points[1]}{points[2]}",
                f"Angle en {points[0]} = {angle}°",
                f"Hypoténuse {points[0]}{points[2]} = {hypotenuse} cm",
                f"sin({angle}°) = côté opposé / hypoténuse",
                f"sin({angle}°) = {points[1]}{points[2]} / {hypotenuse}",
                f"{points[1]}{points[2]} = {hypotenuse} × sin({angle}°)",
                f"{points[1]}{points[2]} ≈ {cote_oppose} cm"
            ]
            
            resultat = cote_oppose
            
        elif type_calcul == "cote_adjacent":
            # Calculer le côté adjacent avec cos
            hypotenuse = random.randint(10, 20)
            
            if angle in angles_remarquables:
                cos_angle = angles_remarquables[angle]["cos"]
            else:
                cos_angle = round(math.cos(math.radians(angle)), 4)
            
            cote_adjacent = round(hypotenuse * cos_angle, 2)
            
            etapes = [
                f"Triangle rectangle {points[0]}{points[1]}{points[2]}",
                f"Angle en {points[0]} = {angle}°",
                f"Hypoténuse = {hypotenuse} cm",
                f"cos({angle}°) = côté adjacent / hypoténuse",
                f"côté adjacent = {hypotenuse} × cos({angle}°)",
                f"côté adjacent ≈ {cote_adjacent} cm"
            ]
            
            resultat = cote_adjacent
            
        else:  # hypotenuse
            cote_oppose = random.randint(5, 12)
            
            if angle in angles_remarquables:
                sin_angle = angles_remarquables[angle]["sin"]
            else:
                sin_angle = round(math.sin(math.radians(angle)), 4)
            
            hypotenuse = round(cote_oppose / sin_angle, 2)
            
            etapes = [
                f"Triangle rectangle, angle = {angle}°",
                f"Côté opposé = {cote_oppose} cm",
                f"sin({angle}°) = {cote_oppose} / hypoténuse",
                f"hypoténuse = {cote_oppose} / sin({angle}°)",
                f"hypoténuse ≈ {hypotenuse} cm"
            ]
            
            resultat = hypotenuse
        
        figure = GeometricFigure(
            type="triangle_rectangle",
            points=points[:3],
            rectangle_en=points[1],
            angles_connus={points[0]: angle}
        )
        
        return MathExerciseSpec(
            niveau=niveau,
            chapitre=chapitre,
            type_exercice=MathExerciseType.TRIGONOMETRIE,
            difficulte=DifficultyLevel(difficulte),
            parametres={
                "triangle": f"{points[0]}{points[1]}{points[2]}",
                "angle": angle,
                "type_calcul": type_calcul
            },
            solution_calculee={
                "resultat": resultat,
                "unite": "cm",
                "angle": angle
            },
            etapes_calculees=etapes,
            resultat_final=f"{resultat} cm",
            figure_geometrique=figure
        )