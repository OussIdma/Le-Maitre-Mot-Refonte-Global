"""
Loader pour le référentiel pédagogique officiel (curriculum).

Ce module charge et indexe les chapitres du curriculum officiel
pour permettre l'accès aux générateurs d'exercices par code officiel.

Usage:
    from curriculum.loader import get_chapter_by_official_code
    
    chapter = get_chapter_by_official_code("6e_N08")
    if chapter:
        print(chapter.libelle)  # "Fractions comme partage et quotient"
        print(chapter.exercise_types)  # ["CALCUL_FRACTIONS", "FRACTION_REPRESENTATION"]
"""

import json
import os
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from functools import lru_cache

logger = logging.getLogger(__name__)

# Chemin vers les fichiers de curriculum
CURRICULUM_DIR = os.path.dirname(os.path.abspath(__file__))
CURRICULUM_6E_PATH = os.path.join(CURRICULUM_DIR, "curriculum_6e.json")


class CurriculumChapter(BaseModel):
    """
    Représente un chapitre du curriculum officiel.
    
    Attributes:
        niveau: Niveau scolaire (ex: "6e")
        code_officiel: Code unique du chapitre (ex: "6e_N08")
        domaine: Domaine mathématique (ex: "Nombres et calculs")
        libelle: Intitulé officiel du chapitre
        chapitre_backend: Nom du chapitre correspondant dans le backend
        exercise_types: Liste des MathExerciseType associés
        schema_requis: Si un schéma/figure est requis pour les exercices
        difficulte_min: Niveau de difficulté minimum (1-3)
        difficulte_max: Niveau de difficulté maximum (1-3)
        statut: Statut du chapitre ("prod", "beta", "hidden")
        tags: Tags pour la recherche et le filtrage
        contexts: Contextes disponibles (ex: ["DBZ", "foot"])
    """
    niveau: str
    code_officiel: str
    domaine: str
    libelle: str
    chapitre_backend: str
    exercise_types: List[str] = Field(default_factory=list)
    schema_requis: bool = False
    difficulte_min: int = 1
    difficulte_max: int = 3
    statut: str = "prod"
    tags: List[str] = Field(default_factory=list)
    contexts: List[str] = Field(default_factory=list)
    
    def is_active(self) -> bool:
        """Retourne True si le chapitre est actif (prod ou beta)."""
        return self.statut in ("prod", "beta")
    
    def has_generators(self) -> bool:
        """Retourne True si le chapitre a des générateurs associés."""
        return len(self.exercise_types) > 0


class CurriculumIndex(BaseModel):
    """
    Index du curriculum pour recherche rapide.
    
    Attributes:
        by_official_code: Dictionnaire indexé par code officiel
        by_backend_chapter: Dictionnaire indexé par nom de chapitre backend
        by_domaine: Dictionnaire indexé par domaine
    """
    by_official_code: Dict[str, CurriculumChapter] = Field(default_factory=dict)
    by_backend_chapter: Dict[str, List[CurriculumChapter]] = Field(default_factory=dict)
    by_domaine: Dict[str, List[CurriculumChapter]] = Field(default_factory=dict)
    
    def get_all_codes(self) -> List[str]:
        """Retourne tous les codes officiels."""
        return list(self.by_official_code.keys())
    
    def get_all_domaines(self) -> List[str]:
        """Retourne tous les domaines uniques."""
        return list(self.by_domaine.keys())
    
    def get_chapters_by_domaine(self, domaine: str) -> List[CurriculumChapter]:
        """Retourne les chapitres d'un domaine."""
        return self.by_domaine.get(domaine, [])
    
    def get_active_chapters(self) -> List[CurriculumChapter]:
        """Retourne tous les chapitres actifs (prod ou beta)."""
        return [ch for ch in self.by_official_code.values() if ch.is_active()]


# Singleton pour l'index du curriculum
_curriculum_index: Optional[CurriculumIndex] = None


def _load_curriculum_from_json(filepath: str) -> List[CurriculumChapter]:
    """
    Charge les chapitres depuis un fichier JSON.
    
    Args:
        filepath: Chemin vers le fichier JSON
        
    Returns:
        Liste des chapitres chargés
        
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        json.JSONDecodeError: Si le JSON est invalide
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Fichier curriculum non trouvé: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    chapters = []
    for chapter_data in data.get("chapitres", []):
        try:
            chapter = CurriculumChapter(**chapter_data)
            chapters.append(chapter)
        except Exception as e:
            logger.warning(f"Erreur lors du chargement du chapitre {chapter_data.get('code_officiel', 'inconnu')}: {e}")
    
    return chapters


def _build_index(chapters: List[CurriculumChapter]) -> CurriculumIndex:
    """
    Construit l'index à partir de la liste des chapitres.
    
    Args:
        chapters: Liste des chapitres à indexer
        
    Returns:
        Index construit
    """
    index = CurriculumIndex()
    
    for chapter in chapters:
        # Index par code officiel
        index.by_official_code[chapter.code_officiel] = chapter
        
        # Index par chapitre backend
        backend_name = chapter.chapitre_backend
        if backend_name not in index.by_backend_chapter:
            index.by_backend_chapter[backend_name] = []
        index.by_backend_chapter[backend_name].append(chapter)
        
        # Index par domaine
        domaine = chapter.domaine
        if domaine not in index.by_domaine:
            index.by_domaine[domaine] = []
        index.by_domaine[domaine].append(chapter)
    
    return index


def load_curriculum_6e() -> CurriculumIndex:
    """
    Charge le curriculum 6e et construit l'index.
    
    Returns:
        Index du curriculum 6e
        
    Raises:
        FileNotFoundError: Si le fichier JSON n'existe pas
    """
    global _curriculum_index
    
    if _curriculum_index is not None:
        return _curriculum_index
    
    logger.info(f"Chargement du curriculum 6e depuis {CURRICULUM_6E_PATH}")
    
    chapters = _load_curriculum_from_json(CURRICULUM_6E_PATH)
    _curriculum_index = _build_index(chapters)
    
    logger.info(f"Curriculum 6e chargé: {len(chapters)} chapitres indexés")
    
    return _curriculum_index


def get_curriculum_index() -> CurriculumIndex:
    """
    Retourne l'index du curriculum (singleton).
    Charge le curriculum si nécessaire.
    
    Returns:
        Index du curriculum
    """
    if _curriculum_index is None:
        load_curriculum_6e()
    return _curriculum_index


def get_chapter_by_official_code(code: str) -> Optional[CurriculumChapter]:
    """
    Récupère un chapitre par son code officiel.
    
    Args:
        code: Code officiel (ex: "6e_N08")
        
    Returns:
        CurriculumChapter si trouvé, None sinon
    """
    index = get_curriculum_index()
    return index.by_official_code.get(code)


def get_chapters_by_backend_name(backend_name: str) -> List[CurriculumChapter]:
    """
    Récupère tous les chapitres associés à un chapitre backend.
    
    Args:
        backend_name: Nom du chapitre backend (ex: "Fractions")
        
    Returns:
        Liste des chapitres officiels associés
    """
    index = get_curriculum_index()
    return index.by_backend_chapter.get(backend_name, [])


def get_all_official_codes() -> List[str]:
    """
    Retourne la liste de tous les codes officiels disponibles.
    
    Returns:
        Liste des codes officiels
    """
    index = get_curriculum_index()
    return index.get_all_codes()


def get_exercise_types_for_official_code(code: str) -> List[str]:
    """
    Récupère les types d'exercices pour un code officiel.
    
    Args:
        code: Code officiel (ex: "6e_N08")
        
    Returns:
        Liste des noms de MathExerciseType (ex: ["CALCUL_FRACTIONS", "FRACTION_REPRESENTATION"])
    """
    chapter = get_chapter_by_official_code(code)
    if chapter:
        return chapter.exercise_types
    return []


def validate_curriculum() -> Dict[str, any]:
    """
    Valide le curriculum et retourne un rapport.
    
    Returns:
        Dictionnaire avec les statistiques et erreurs éventuelles
    """
    index = get_curriculum_index()
    
    report = {
        "total_chapters": len(index.by_official_code),
        "chapters_with_generators": sum(1 for ch in index.by_official_code.values() if ch.has_generators()),
        "chapters_without_generators": sum(1 for ch in index.by_official_code.values() if not ch.has_generators()),
        "chapters_by_status": {},
        "chapters_by_domaine": {},
        "warnings": []
    }
    
    # Comptage par statut
    for chapter in index.by_official_code.values():
        status = chapter.statut
        report["chapters_by_status"][status] = report["chapters_by_status"].get(status, 0) + 1
    
    # Comptage par domaine
    for domaine, chapters in index.by_domaine.items():
        report["chapters_by_domaine"][domaine] = len(chapters)
    
    # Warnings pour les chapitres sans générateurs
    for chapter in index.by_official_code.values():
        if not chapter.has_generators() and chapter.statut == "prod":
            report["warnings"].append(
                f"Chapitre {chapter.code_officiel} ({chapter.libelle}) en prod mais sans générateurs"
            )
    
    return report


# ============================================================================
# CATALOGUE FRONTEND (API pour /generate)
# ============================================================================

class MacroGroup:
    """Groupe macro pour la vue simplifiée."""
    
    def __init__(self, label: str, codes_officiels: List[str], description: str = ""):
        self.label = label
        self.codes_officiels = codes_officiels
        self.description = description


def _load_macro_groups() -> List[Dict]:
    """
    Charge les macro groups depuis le fichier JSON.
    
    Returns:
        Liste des macro groups avec leurs codes officiels
    """
    if not os.path.exists(CURRICULUM_6E_PATH):
        return []
    
    with open(CURRICULUM_6E_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("macro_groups", [])


def get_catalog(level: str = "6e") -> Dict:
    """
    Génère le catalogue complet pour le frontend.
    
    Structure retournée:
    {
        "level": "6e",
        "domains": [
            {
                "name": "Grandeurs et mesures",
                "chapters": [
                    {
                        "code_officiel": "6e_GM07",
                        "libelle": "Lecture de l'heure",
                        "status": "prod",
                        "schema_requis": true,
                        "difficulty_min": 1,
                        "difficulty_max": 3,
                        "generators": ["LECTURE_HORLOGE", ...]
                    }
                ]
            }
        ],
        "macro_groups": [
            {
                "label": "Longueurs, masses, durées",
                "codes_officiels": ["6e_GM01", "6e_GM05", "6e_GM06", "6e_GM07"],
                "status": "prod",
                "description": "Mesures et conversions"
            }
        ]
    }
    
    Args:
        level: Niveau scolaire (par défaut "6e")
        
    Returns:
        Dictionnaire du catalogue pour le frontend
    """
    if level != "6e":
        return {
            "level": level,
            "domains": [],
            "macro_groups": [],
            "error": f"Niveau '{level}' non supporté pour l'instant"
        }
    
    index = get_curriculum_index()
    
    # Construire les domaines avec chapitres
    domains = []
    for domaine_name in sorted(index.by_domaine.keys()):
        chapters_list = index.by_domaine[domaine_name]
        
        chapters_data = []
        for chapter in sorted(chapters_list, key=lambda c: c.code_officiel):
            chapters_data.append({
                "code_officiel": chapter.code_officiel,
                "libelle": chapter.libelle,
                "status": chapter.statut,
                "schema_requis": chapter.schema_requis,
                "difficulty_min": chapter.difficulte_min,
                "difficulty_max": chapter.difficulte_max,
                "generators": chapter.exercise_types,
                "has_svg": any(
                    gen in chapter.exercise_types 
                    for gen in ["LECTURE_HORLOGE", "CALCUL_DUREE", "SYMETRIE_AXIALE", 
                               "TRIANGLE_QUELCONQUE", "RECTANGLE", "CERCLE", "FRACTION_REPRESENTATION"]
                )
            })
        
        domains.append({
            "name": domaine_name,
            "chapters": chapters_data
        })
    
    # Charger les macro groups depuis le JSON
    raw_macro_groups = _load_macro_groups()
    
    # Enrichir les macro groups avec le status calculé
    macro_groups = []
    for mg in raw_macro_groups:
        codes = mg.get("codes_officiels", [])
        
        # Calculer le status du groupe (prod si au moins un chapitre est prod)
        statuses = []
        generators_count = 0
        for code in codes:
            chapter = index.by_official_code.get(code)
            if chapter:
                statuses.append(chapter.statut)
                generators_count += len(chapter.exercise_types)
        
        if "prod" in statuses:
            group_status = "prod"
        elif "beta" in statuses:
            group_status = "beta"
        else:
            group_status = "hidden"
        
        macro_groups.append({
            "label": mg.get("label", ""),
            "codes_officiels": codes,
            "description": mg.get("description", ""),
            "status": group_status,
            "total_generators": generators_count
        })
    
    return {
        "level": level,
        "domains": domains,
        "macro_groups": macro_groups,
        "total_chapters": len(index.by_official_code),
        "total_macro_groups": len(macro_groups)
    }


def get_codes_for_macro_group(label: str) -> List[str]:
    """
    Récupère les codes officiels associés à un macro group.
    
    Args:
        label: Libellé du macro group (ex: "Longueurs, masses, durées")
        
    Returns:
        Liste des codes officiels, ou liste vide si non trouvé
    """
    macro_groups = _load_macro_groups()
    
    for mg in macro_groups:
        if mg.get("label") == label:
            return mg.get("codes_officiels", [])
    
    return []


# Charger automatiquement au premier import (optionnel, peut être fait paresseusement)
# load_curriculum_6e()
