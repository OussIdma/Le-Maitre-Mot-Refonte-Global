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
    
    # Statistiques
    STATISTIQUES = "statistiques"
    PROBABILITES = "probabilites"

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
            exercise["geometric_schema"] = {
                "type": self.spec.figure_geometrique.type,
                "points": self.spec.figure_geometrique.points,
                "segments": [
                    [seg[:len(seg)//2], seg[len(seg)//2:], {"longueur": f"{val} cm"}]
                    for seg, val in self.spec.figure_geometrique.longueurs_connues.items()
                ],
                "angles": [
                    [self.spec.figure_geometrique.rectangle_en, {"angle_droit": True}]
                ] if self.spec.figure_geometrique.rectangle_en else []
            }
        
        return exercise