"""
Modèles de données pour la génération mathématique structurée
Sépare complètement la logique mathématique de la rédaction IA
"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel
from enum import Enum
import json

class DifficultyLevel(str, Enum):
    FACILE = "facile"
    MOYEN = "moyen"
    DIFFICILE = "difficile"

class MathExerciseType(str, Enum):
    # Calculs
    CALCUL_RELATIFS = "calcul_relatifs"
    CALCUL_FRACTIONS = "calcul_fractions"
    CALCUL_DECIMAUX = "calcul_decimaux"
    PUISSANCES = "puissances"
    
    # Équations et inéquations
    EQUATION_1ER_DEGRE = "equation_1er_degre"
    INEQUATION = "inequation"
    SYSTEME_EQUATIONS = "systeme_equations"
    
    # Proportionnalité
    PROPORTIONNALITE = "proportionnalite"
    POURCENTAGES = "pourcentages"
    ECHELLE = "echelle"
    
    # ========== VAGUE 1 - Générateurs 6e ==========
    # Fractions avancées
    FRACTION_REPRESENTATION = "fraction_representation"  # 6N2-FRAC-REPR
    
    # Proportionnalité avancée
    PROP_TABLEAU = "prop_tableau"  # 6N3-PROP-TAB
    PROP_ACHAT = "prop_achat"  # 6N3-PROP-ACHAT
    
    # Problèmes
    PROBLEME_2_ETAPES = "probleme_2_etapes"  # 6P-PROB-2ET
    
    # Nombres entiers
    NOMBRES_LECTURE = "nombres_lecture"  # 6N1-LECTURE
    NOMBRES_COMPARAISON = "nombres_comparaison"  # 6N1-COMP
    
    # Géométrie
    TRIANGLE_RECTANGLE = "triangle_rectangle"
    TRIANGLE_QUELCONQUE = "triangle_quelconque"
    RECTANGLE = "rectangle"
    CERCLE = "cercle"
    PERIMETRE_AIRE = "perimetre_aire"
    VOLUME = "volume"
    ANGLES = "angles"
    THALES = "thales"
    TRIGONOMETRIE = "trigonometrie"
    SYMETRIE_AXIALE = "symetrie_axiale"
    SYMETRIE_CENTRALE = "symetrie_centrale"
    
    # Statistiques
    STATISTIQUES = "statistiques"
    PROBABILITES = "probabilites"
    
    # ========== VAGUE 2 - Générateurs 6e ==========
    # Droites graduées
    DROITE_GRADUEE_ENTIERS = "droite_graduee_entiers"
    DROITE_GRADUEE_DECIMAUX = "droite_graduee_decimaux"
    FRACTION_DROITE = "fraction_droite"
    
    # Fractions avancées
    FRACTION_COMPARAISON = "fraction_comparaison"
    FRACTIONS_EGALES = "fractions_egales"
    
    # Proportionnalité avancée
    PROP_COEFFICIENT = "prop_coefficient"
    VITESSE_DUREE_DISTANCE = "vitesse_duree_distance"
    PROP_GRAPHIQUE = "prop_graphique"
    
    # Aires avancées
    AIRE_TRIANGLE = "aire_triangle"
    AIRE_FIGURES_COMPOSEES = "aire_figures_composees"
    
    # Volumes
    VOLUME_PAVE = "volume_pave"
    
    # Données et statistiques
    TABLEAU_LECTURE = "tableau_lecture"
    DIAGRAMME_BARRES = "diagramme_barres"
    DIAGRAMME_CIRCULAIRE = "diagramme_circulaire"
    TABLEAU_COMPLETER = "tableau_completer"
    
    # Problèmes
    PROBLEME_1_ETAPE = "probleme_1_etape"
    
    # Géométrie figures
    TRIANGLE_CONSTRUCTION = "triangle_construction"
    QUADRILATERES = "quadrilateres"
    ANGLE_MESURE = "angle_mesure"
    ANGLE_VOCABULAIRE = "angle_vocabulaire"
    ANGLE_PROPRIETES = "angle_proprietes"
    
    # Calcul littéral
    FORMULES = "formules"
    SUBSTITUTION = "substitution"
    
    # ========== VAGUE 3 - Générateurs 6e ==========
    # Nombres
    DECOMPOSITION = "decomposition"
    ENCADREMENT = "encadrement"
    ARRONDI = "arrondi"
    
    # Calculs
    PRIORITES_OPERATIONS = "priorites_operations"
    PARENTHESES = "parentheses"
    ERREURS_COURANTES = "erreurs_courantes"
    
    # Divisibilité
    CRITERES_DIVISIBILITE = "criteres_divisibilite"
    MULTIPLES = "multiples"
    
    # Conversions
    CONVERSIONS_UNITES = "conversions_unites"
    
    # Symétrie
    SYMETRIE_PROPRIETES = "symetrie_proprietes"
    
    # ========== GÉNÉRATEURS DÉDIÉS 6e (P1) ==========
    CALCUL_MENTAL_DEDIE = "calcul_mental_dedie"
    CALCUL_POSE_DEDIE = "calcul_pose_dedie"
    CALCUL_INSTRUMENTE_DEDIE = "calcul_instrumente_dedie"
    GRANDEURS_MESURES_DEDIE = "grandeurs_mesures_dedie"
    
    # ========== CHAPITRE MODÈLE: DURÉES ET LECTURE DE L'HEURE (6e) ==========
    # Type 1: Lecture d'horloge analogique (SVG obligatoire)
    LECTURE_HORLOGE = "lecture_horloge"
    # Type 2: Conversions de durées (h↔min, min↔s)
    CONVERSION_DUREES = "conversion_durees"
    # Type 3: Calcul de durée entre deux instants (SVG recommandé)
    CALCUL_DUREE = "calcul_duree"
    # Type 4: Problèmes contextualisés sur les durées
    PROBLEME_DUREES = "probleme_durees"
    
    # ========== GÉNÉRATEUR PREMIUM: DURÉES (6e_GM07) ==========
    # Générateur de qualité manuel scolaire professionnel
    # Activé uniquement pour l'offre PRO
    DUREES_PREMIUM = "durees_premium"

class GeometricFigure(BaseModel):
    """Définition structurée d'une figure géométrique"""
    type: str  # triangle_rectangle, rectangle, cercle, etc.
    points: List[str]  # ["A", "B", "C"]
    rectangle_en: Optional[str] = None  # Point de l'angle droit
    longueurs_connues: Dict[str, Union[int, float]] = {}  # {"AB": 5, "BC": 12}
    longueurs_a_calculer: List[str] = []  # ["AC"]
    angles_connus: Dict[str, Union[int, float]] = {}  # {"BAC": 90}
    angles_a_calculer: List[str] = []  # ["ACB"]
    proprietes: List[str] = []  # ["isocele", "equilateral", etc.]
    
    def get_segment_key(self, point1: str, point2: str) -> str:
        """Normalise les clés de segments (AB = BA)"""
        return "".join(sorted([point1, point2]))

class MathExerciseSpec(BaseModel):
    """Spécification complète d'un exercice de mathématiques"""
    
    # Métadonnées
    matiere: str = "Mathématiques"
    niveau: str
    chapitre: str
    type_exercice: MathExerciseType
    difficulte: DifficultyLevel
    
    # Paramètres mathématiques (variables selon le type)
    parametres: Dict[str, Any]
    
    # Solution calculée par le backend
    solution_calculee: Dict[str, Any]
    etapes_calculees: List[str]
    resultat_final: Union[int, float, str]
    
    # Géométrie spécialisée
    figure_geometrique: Optional[GeometricFigure] = None
    
    # Métadonnées additionnelles
    points_bareme: List[Dict[str, Any]] = []
    conseils_prof: List[str] = []
    
    def to_ai_prompt_data(self) -> Dict[str, Any]:
        """Convertit la spec en données pour le prompt IA"""
        data = {
            "niveau": self.niveau,
            "chapitre": self.chapitre,
            "type_exercice": self.type_exercice,
            "difficulte": self.difficulte,
            "parametres": self.parametres,
            "resultat_attendu": self.resultat_final
        }
        
        if self.figure_geometrique:
            data["figure"] = self.figure_geometrique.dict()
            
        return data

class MathTextGeneration(BaseModel):
    """Réponse attendue de l'IA pour la rédaction"""
    enonce: str
    explication_prof: Optional[str] = None
    solution_redigee: Optional[str] = None
    
class GeneratedMathExercise(BaseModel):
    """Exercice mathématique complet (spec + texte IA)"""
    spec: MathExerciseSpec
    texte: MathTextGeneration
    
    def to_exercise_dict(self) -> Dict[str, Any]:
        """Convertit vers le format Exercise existant pour compatibilité"""
        exercise = {
            "id": f"math_{hash(str(self.spec.parametres))}",
            "titre": f"Exercice - {self.spec.chapitre}",
            "enonce": self.texte.enonce,
            "type": "ouvert",
            "difficulte": self.spec.difficulte,
            "solution": {
                "etapes": self.spec.etapes_calculees,
                "resultat": str(self.spec.resultat_final),
                "explication": self.texte.solution_redigee or ""
            },
            "bareme": self.spec.points_bareme or [
                {"etape": "Méthode", "points": 2.0},
                {"etape": "Résultat", "points": 2.0}
            ],
            # Nouvelles données structurées
            "spec_mathematique": self.spec.dict(),
            "solution_calculee": self.spec.solution_calculee
        }
        
        # Ajouter geometric_schema si géométrie
        if self.spec.figure_geometrique:
            # Traiter les segments correctement selon le type de figure
            segments = []
            for seg, val in self.spec.figure_geometrique.longueurs_connues.items():
                # Pour les cercles, seg = "rayon" (pas un segment entre 2 points)
                if self.spec.figure_geometrique.type == "cercle" and seg == "rayon":
                    segments.append([seg, {"longueur": f"{val} cm"}])
                # Pour les autres figures, diviser le segment en 2 points (ex: "AB" -> ["A", "B"])
                elif len(seg) >= 2:
                    segments.append([seg[:len(seg)//2], seg[len(seg)//2:], {"longueur": f"{val} cm"}])
                else:
                    # Cas spécial (ne devrait pas arriver normalement)
                    segments.append([seg, {"longueur": f"{val} cm"}])
            
            exercise["geometric_schema"] = {
                "type": self.spec.figure_geometrique.type,
                "points": self.spec.figure_geometrique.points,
                "segments": segments,
                "angles": [
                    [self.spec.figure_geometrique.rectangle_en, {"angle_droit": True}]
                ] if self.spec.figure_geometrique.rectangle_en else []
            }
        
        return exercise    
