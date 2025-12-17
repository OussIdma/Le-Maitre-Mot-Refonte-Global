"""
Types d'exercices et comportements SVG associés.

Ce module définit les types d'exercices pédagogiques et leur comportement
en termes de génération de figures SVG pour l'énoncé et la solution.

Architecture:
- ExerciseType: Enum des types d'exercices
- SVG_BEHAVIOR: Mapping type → comportement SVG
- get_svg_behavior(): Fonction utilitaire pour obtenir le comportement
"""

from enum import Enum
from typing import Dict, Any, Optional, NamedTuple


class SvgBehavior(NamedTuple):
    """Comportement SVG pour un type d'exercice"""
    svg_in_enonce: bool  # Afficher SVG dans l'énoncé
    svg_in_solution: bool  # Afficher SVG dans la solution
    enonce_svg_type: str  # Type de SVG pour l'énoncé (ex: "clock_with_hands", "clock_empty")
    solution_svg_type: str  # Type de SVG pour la solution


class ExerciseType(str, Enum):
    """
    Types d'exercices pédagogiques.
    
    Chaque type définit un comportement spécifique pour:
    - La génération de SVG dans l'énoncé
    - La génération de SVG dans la solution
    """
    
    # === LECTURE DE L'HEURE ===
    LECTURE_HEURE = "LECTURE_HEURE"
    """Lire l'heure sur une horloge - SVG avec aiguilles dans l'énoncé uniquement"""
    
    PLACER_AIGUILLES = "PLACER_AIGUILLES"
    """Placer les aiguilles - SVG vide dans l'énoncé, SVG complet dans la solution"""
    
    # === DURÉES ===
    CALCUL_DUREE = "CALCUL_DUREE"
    """Calculer une durée - Droite du temps optionnelle"""
    
    CONVERSION_DUREE = "CONVERSION_DUREE"
    """Conversion d'unités de temps - Pas de SVG"""
    
    # === LONGUEURS / GRANDEURS ===
    CONVERSION = "CONVERSION"
    """Conversion d'unités (longueurs, masses...) - Pas de SVG"""
    
    COMPARAISON = "COMPARAISON"
    """Comparer des grandeurs - Pas de SVG"""
    
    PERIMETRE = "PERIMETRE"
    """Calculer un périmètre - SVG de forme dans l'énoncé"""
    
    AIRE = "AIRE"
    """Calculer une aire - SVG de forme dans l'énoncé"""
    
    # === GÉOMÉTRIE ===
    SYMETRIE_AXIALE = "SYMETRIE_AXIALE"
    """Symétrie axiale - Axe seul dans énoncé, figure complète dans solution"""
    
    SYMETRIE_CENTRALE = "SYMETRIE_CENTRALE"
    """Symétrie centrale - Centre seul dans énoncé, figure complète dans solution"""
    
    CONSTRUCTION = "CONSTRUCTION"
    """Construction géométrique - Figure initiale dans énoncé, figure finale dans solution"""
    
    # === PROBLÈMES ===
    PROBLEME = "PROBLEME"
    """Problème contextuel - SVG optionnel selon contexte"""


# =============================================================================
# MAPPING TYPE → COMPORTEMENT SVG
# =============================================================================

SVG_BEHAVIOR: Dict[str, SvgBehavior] = {
    # Lecture de l'heure: horloge avec aiguilles dans l'énoncé, rien en solution
    ExerciseType.LECTURE_HEURE.value: SvgBehavior(
        svg_in_enonce=True,
        svg_in_solution=False,
        enonce_svg_type="clock_with_hands",
        solution_svg_type=""
    ),
    
    # Placer les aiguilles: horloge vide dans l'énoncé, horloge complète dans la solution
    ExerciseType.PLACER_AIGUILLES.value: SvgBehavior(
        svg_in_enonce=True,
        svg_in_solution=True,
        enonce_svg_type="clock_empty",
        solution_svg_type="clock_with_hands"
    ),
    
    # Calcul de durée: droite du temps optionnelle
    ExerciseType.CALCUL_DUREE.value: SvgBehavior(
        svg_in_enonce=True,
        svg_in_solution=False,
        enonce_svg_type="timeline",
        solution_svg_type=""
    ),
    
    # Conversions: pas de SVG
    ExerciseType.CONVERSION.value: SvgBehavior(
        svg_in_enonce=False,
        svg_in_solution=False,
        enonce_svg_type="",
        solution_svg_type=""
    ),
    
    ExerciseType.CONVERSION_DUREE.value: SvgBehavior(
        svg_in_enonce=False,
        svg_in_solution=False,
        enonce_svg_type="",
        solution_svg_type=""
    ),
    
    # Comparaison: pas de SVG
    ExerciseType.COMPARAISON.value: SvgBehavior(
        svg_in_enonce=False,
        svg_in_solution=False,
        enonce_svg_type="",
        solution_svg_type=""
    ),
    
    # Périmètre: forme dans l'énoncé
    ExerciseType.PERIMETRE.value: SvgBehavior(
        svg_in_enonce=True,
        svg_in_solution=False,
        enonce_svg_type="shape",
        solution_svg_type=""
    ),
    
    # Aire: forme dans l'énoncé
    ExerciseType.AIRE.value: SvgBehavior(
        svg_in_enonce=True,
        svg_in_solution=False,
        enonce_svg_type="shape",
        solution_svg_type=""
    ),
    
    # Symétrie axiale: axe seul → figure complète
    ExerciseType.SYMETRIE_AXIALE.value: SvgBehavior(
        svg_in_enonce=True,
        svg_in_solution=True,
        enonce_svg_type="axis_only",
        solution_svg_type="axis_with_symmetric"
    ),
    
    # Symétrie centrale: centre seul → figure complète
    ExerciseType.SYMETRIE_CENTRALE.value: SvgBehavior(
        svg_in_enonce=True,
        svg_in_solution=True,
        enonce_svg_type="center_only",
        solution_svg_type="center_with_symmetric"
    ),
    
    # Construction: figure initiale → figure finale
    ExerciseType.CONSTRUCTION.value: SvgBehavior(
        svg_in_enonce=True,
        svg_in_solution=True,
        enonce_svg_type="initial",
        solution_svg_type="final"
    ),
    
    # Problème: comportement par défaut
    ExerciseType.PROBLEME.value: SvgBehavior(
        svg_in_enonce=False,
        svg_in_solution=False,
        enonce_svg_type="",
        solution_svg_type=""
    ),
}


def get_svg_behavior(exercise_type: Optional[str], family: Optional[str] = None) -> SvgBehavior:
    """
    Retourne le comportement SVG pour un type d'exercice.
    
    Si exercise_type n'est pas fourni, utilise family pour déterminer
    le comportement par défaut (rétro-compatibilité).
    
    Args:
        exercise_type: Type d'exercice explicite (prioritaire)
        family: Famille d'exercice (fallback pour rétro-compatibilité)
    
    Returns:
        SvgBehavior définissant où afficher les SVG
    """
    # Si exercise_type est explicite, l'utiliser
    if exercise_type and exercise_type in SVG_BEHAVIOR:
        return SVG_BEHAVIOR[exercise_type]
    
    # Sinon, déduire depuis family (rétro-compatibilité GM07/GM08)
    if family:
        family_upper = family.upper()
        
        # Mapping famille → type par défaut
        family_to_type = {
            "LECTURE_HORLOGE": ExerciseType.LECTURE_HEURE.value,
            "CALCUL_DUREE": ExerciseType.CALCUL_DUREE.value,
            "DUREES": ExerciseType.CALCUL_DUREE.value,
            "CONVERSION": ExerciseType.CONVERSION.value,
            "COMPARAISON": ExerciseType.COMPARAISON.value,
            "PERIMETRE": ExerciseType.PERIMETRE.value,
            "PROBLEME": ExerciseType.PROBLEME.value,
        }
        
        if family_upper in family_to_type:
            return SVG_BEHAVIOR.get(
                family_to_type[family_upper],
                _default_behavior()
            )
    
    return _default_behavior()


def _default_behavior() -> SvgBehavior:
    """Comportement par défaut (rétro-compatible avec l'existant)"""
    return SvgBehavior(
        svg_in_enonce=True,
        svg_in_solution=False,
        enonce_svg_type="auto",
        solution_svg_type=""
    )


def get_all_exercise_types() -> list:
    """Retourne la liste de tous les types d'exercices pour l'admin"""
    return [
        {"value": t.value, "label": _get_type_label(t.value), "description": _get_type_description(t.value)}
        for t in ExerciseType
    ]


def _get_type_label(exercise_type: str) -> str:
    """Label humain pour un type d'exercice"""
    labels = {
        "LECTURE_HEURE": "Lire l'heure",
        "PLACER_AIGUILLES": "Placer les aiguilles",
        "CALCUL_DUREE": "Calculer une durée",
        "CONVERSION_DUREE": "Conversion de durées",
        "CONVERSION": "Conversion d'unités",
        "COMPARAISON": "Comparaison",
        "PERIMETRE": "Périmètre",
        "AIRE": "Aire",
        "SYMETRIE_AXIALE": "Symétrie axiale",
        "SYMETRIE_CENTRALE": "Symétrie centrale",
        "CONSTRUCTION": "Construction",
        "PROBLEME": "Problème",
    }
    return labels.get(exercise_type, exercise_type)


def _get_type_description(exercise_type: str) -> str:
    """Description du comportement SVG pour un type"""
    behavior = SVG_BEHAVIOR.get(exercise_type, _default_behavior())
    
    if behavior.svg_in_enonce and behavior.svg_in_solution:
        return "Figure dans énoncé ET solution"
    elif behavior.svg_in_enonce:
        return "Figure dans énoncé uniquement"
    elif behavior.svg_in_solution:
        return "Figure dans solution uniquement"
    else:
        return "Pas de figure"
