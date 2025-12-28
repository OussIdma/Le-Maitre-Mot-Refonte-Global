"""
Package constants - Constantes centralisées pour le projet.
"""

# Symboles mathématiques normalisés
MATH_SYMBOLS = {
    "multiplication": "×",
    "division": "÷",
    "pi": "π",
    "degree": "°",
    "squared": "²",
    "cubed": "³",
    "sqrt": "√",
    "approximately": "≈",
    "less_than_or_equal": "≤",
    "greater_than_or_equal": "≥"
}

# Points géométriques standards (ordre alphabétique)
GEOMETRY_POINT_SETS = [
    ["A", "B", "C"],
    ["D", "E", "F"],
    ["G", "H", "I"],
    ["J", "K", "L"],
    ["M", "N", "P"],
    ["Q", "R", "S"],
    ["T", "U", "V"],
    ["W", "X", "Y"]
]

# Niveaux scolaires
SCHOOL_LEVELS = ["6e", "5e", "4e", "3e"]

# Difficultés
DIFFICULTY_LEVELS = ["facile", "moyen", "difficile"]

# Types de documents
DOCUMENT_TYPES = ["evaluation", "exercice", "controle", "ds"]

# Collections MongoDB
from backend.constants.collections import (
    EXERCISES_COLLECTION,
    EXERCISE_TYPES_COLLECTION,
    COMPETENCES_COLLECTION,
    EXERCISE_SHEETS_COLLECTION,
    SHEET_ITEMS_COLLECTION,
    CURRICULUM_CHAPTERS_COLLECTION,
    LEGACY_EXERCISES_COLLECTION
)

__all__ = [
    "MATH_SYMBOLS",
    "GEOMETRY_POINT_SETS",
    "SCHOOL_LEVELS",
    "DIFFICULTY_LEVELS",
    "DOCUMENT_TYPES",
    "EXERCISES_COLLECTION",
    "EXERCISE_TYPES_COLLECTION",
    "COMPETENCES_COLLECTION",
    "EXERCISE_SHEETS_COLLECTION",
    "SHEET_ITEMS_COLLECTION",
    "CURRICULUM_CHAPTERS_COLLECTION",
    "LEGACY_EXERCISES_COLLECTION"
]

