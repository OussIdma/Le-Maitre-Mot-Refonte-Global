"""
RÈGLES PÉDAGOGIQUES UNIVERSELLES - Le Maître Mot

Ce module centralise la logique pédagogique universelle qui s'applique
à TOUTES les matières et TOUS les chapitres.

RÈGLE FONDAMENTALE :
    SUJET = Données connues uniquement
    CORRIGÉ = Données connues + Réponse + Raisonnement/Construction

Cette règle est NON NÉGOCIABLE et s'applique partout :
    - Mathématiques (géométrie, algèbre, etc.)
    - Français (grammaire, orthographe, etc.)
    - Histoire-Géographie
    - Anglais
    - etc.
"""

from typing import Dict, Any, List
from enum import Enum


class ExerciseType(str, Enum):
    """
    Classification universelle des types d'exercices.
    
    Cette classification pilote automatiquement ce qui doit être caché/affiché
    dans le SUJET vs le CORRIGÉ.
    """
    
    TROUVER_VALEUR = "trouver_valeur"
    """
    L'élève doit trouver quelque chose (point, angle, longueur, mot, résultat, etc.)
    
    Exemples :
        - "Trouve le point M' symétrique de M"
        - "Calcule la longueur BC"
        - "Trouve le mot qui convient"
        - "Calcule le résultat"
    
    SUJET : Ne contient JAMAIS l'objet à trouver
    CORRIGÉ : Montre l'objet trouvé + construction + justification
    """
    
    VERIFIER_PROPRIETE = "verifier_propriete"
    """
    L'élève doit vérifier si une propriété est vraie.
    
    Exemples :
        - "Les points A et B sont-ils symétriques ?"
        - "Les droites (AB) et (CD) sont-elles parallèles ?"
        - "Le mot 'mangé' est-il correctement orthographié ?"
    
    SUJET : Montre TOUS les objets nécessaires (ils doivent être visibles)
    CORRIGÉ : Explication + éventuellement constructions intermédiaires
    """
    
    COMPLETER_STRUCTURE = "completer_structure"
    """
    L'élève doit compléter une figure, un texte, un tableau, une équation.
    
    Exemples :
        - "Complète le triangle par symétrie"
        - "Complète la phrase avec le bon mot"
        - "Complète le tableau"
    
    SUJET : Montre uniquement la partie donnée
    CORRIGÉ : Montre la partie donnée + la complétion + raisonnement
    """
    
    PROBLEME_REDIGE = "probleme_redige"
    """
    Texte contextualisé + plusieurs questions.
    
    Exemples :
        - Problème de géométrie avec plusieurs étapes
        - Problème de physique avec contexte
        - Texte avec questions de compréhension
    
    SUJET : Texte + questions
    CORRIGÉ : Solutions détaillées étape par étape
    """


def determine_elements_to_hide_in_question(
    exercise_type: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    🎯 FONCTION CENTRALE : Règle pédagogique universelle
    
    Détermine quels éléments doivent être cachés dans le SUJET selon le type d'exercice.
    
    Cette fonction est INDÉPENDANTE du chapitre/matière :
        - Pas de logique spécifique "symétrie axiale"
        - Pas de logique spécifique "Pythagore"
        - Tout découle de exercise_type + metadata
    
    Args:
        exercise_type: Type d'exercice (voir ExerciseType)
        metadata: Métadonnées de l'exercice contenant :
            - points: Liste des points [point_initial, point_a_trouver, ...]
            - shapes: Liste des formes (triangles, segments, etc.)
            - properties: Propriétés de l'exercice
            
    Returns:
        Dict contenant :
            - elements_to_hide: List[str] - Noms des éléments à cacher
            - hide_constructions: bool - Cacher les constructions intermédiaires
            - hide_annotations: bool - Cacher les annotations/labels de réponse
            - exercise_type_detected: str - Type détecté
    
    Examples:
        >>> # Exercice "trouver le symétrique"
        >>> determine_elements_to_hide_in_question(
        ...     "trouver_valeur",
        ...     {"points": ["M", "M'"], "is_geometry": True}
        ... )
        {
            "elements_to_hide": ["M'"],
            "hide_constructions": True,
            "hide_annotations": True,
            "exercise_type_detected": "trouver_valeur"
        }
        
        >>> # Exercice "vérifier si symétriques"
        >>> determine_elements_to_hide_in_question(
        ...     "verifier_propriete",
        ...     {"points": ["A", "B"], "is_geometry": True}
        ... )
        {
            "elements_to_hide": [],
            "hide_constructions": False,
            "hide_annotations": False,
            "exercise_type_detected": "verifier_propriete"
        }
    """
    
    # Normaliser le type d'exercice
    try:
        ex_type = ExerciseType(exercise_type)
    except ValueError:
        # Type non reconnu, essayer de le détecter depuis les métadonnées
        ex_type = _detect_exercise_type_from_metadata(metadata)
    
    # Appliquer les règles selon le type
    if ex_type == ExerciseType.TROUVER_VALEUR:
        return _rules_trouver_valeur(metadata)
    
    elif ex_type == ExerciseType.VERIFIER_PROPRIETE:
        return _rules_verifier_propriete(metadata)
    
    elif ex_type == ExerciseType.COMPLETER_STRUCTURE:
        return _rules_completer_structure(metadata)
    
    elif ex_type == ExerciseType.PROBLEME_REDIGE:
        return _rules_probleme_redige(metadata)
    
    else:
        # Par défaut : comportement conservateur (ne rien cacher)
        return {
            "elements_to_hide": [],
            "hide_constructions": False,
            "hide_annotations": False,
            "exercise_type_detected": "unknown"
        }


def _detect_exercise_type_from_metadata(metadata: Dict[str, Any]) -> ExerciseType:
    """
    Détecte automatiquement le type d'exercice depuis les métadonnées.
    
    Utilisé quand exercise_type n'est pas explicitement fourni.
    """
    
    # Détecter "verifier_propriete" : présence de "symetriques_", "alignes_", etc.
    properties = metadata.get("properties", [])
    if any("symetriques_" in str(prop) for prop in properties):
        return ExerciseType.VERIFIER_PROPRIETE
    if any("alignes_" in str(prop) for prop in properties):
        return ExerciseType.VERIFIER_PROPRIETE
    if any("orthogonaux_" in str(prop) for prop in properties):
        return ExerciseType.VERIFIER_PROPRIETE
    
    # Détecter "completer_structure" : présence de "triangle" + "is_completion"
    if "triangle" in properties and metadata.get("is_completion", False):
        return ExerciseType.COMPLETER_STRUCTURE
    
    # Par défaut : trouver_valeur (cas le plus courant)
    return ExerciseType.TROUVER_VALEUR


def _rules_trouver_valeur(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Règles pour les exercices de type TROUVER_VALEUR.
    
    SUJET : Objet initial seulement
    CORRIGÉ : Objet initial + objet à trouver + constructions
    """
    
    points = metadata.get("points", [])
    shapes = metadata.get("shapes", [])
    
    # Identifier les éléments à cacher
    elements_to_hide = []
    
    # Pour la géométrie : cacher le dernier point (généralement le point à trouver)
    if metadata.get("is_geometry", False):
        if len(points) >= 2:
            # Le dernier point est généralement celui à trouver
            elements_to_hide.append(points[-1])
        
        # Cacher les formes "image" ou "transformée"
        for shape in shapes:
            if "image" in str(shape).lower() or "prime" in str(shape).lower():
                elements_to_hide.append(shape)
    
    # Pour les autres matières : cacher les réponses textuelles
    if metadata.get("answer_text"):
        elements_to_hide.append("answer_text")
    
    return {
        "elements_to_hide": elements_to_hide,
        "hide_constructions": True,  # Cacher segments, points milieu, etc.
        "hide_annotations": True,    # Cacher les labels de réponse
        "exercise_type_detected": "trouver_valeur"
    }


def _rules_verifier_propriete(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Règles pour les exercices de type VERIFIER_PROPRIETE.
    
    SUJET : Tous les éléments nécessaires (visibles)
    CORRIGÉ : + constructions / annotations
    """
    
    return {
        "elements_to_hide": [],  # Ne rien cacher dans le sujet
        "hide_constructions": False,  # Les constructions peuvent être visibles
        "hide_annotations": False,    # Les annotations basiques peuvent être visibles
        "exercise_type_detected": "verifier_propriete"
    }


def _rules_completer_structure(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Règles pour les exercices de type COMPLETER_STRUCTURE.
    
    SUJET : Structure initiale
    CORRIGÉ : Structure initiale + complétion
    """
    
    shapes = metadata.get("shapes", [])
    
    # Cacher les formes complétées (généralement marquées "image", "complete", etc.)
    elements_to_hide = []
    for shape in shapes:
        if any(marker in str(shape).lower() for marker in ["image", "complete", "prime"]):
            elements_to_hide.append(shape)
    
    return {
        "elements_to_hide": elements_to_hide,
        "hide_constructions": True,
        "hide_annotations": True,
        "exercise_type_detected": "completer_structure"
    }


def _rules_probleme_redige(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Règles pour les exercices de type PROBLEME_REDIGE.
    
    SUJET : Texte + questions
    CORRIGÉ : Solutions détaillées
    """
    
    return {
        "elements_to_hide": [],  # Le texte est visible
        "hide_constructions": False,
        "hide_annotations": False,
        "exercise_type_detected": "probleme_redige"
    }


# Export des symboles publics
__all__ = [
    "ExerciseType",
    "determine_elements_to_hide_in_question"
]
