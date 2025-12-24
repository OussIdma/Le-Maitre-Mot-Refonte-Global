"""
Service pour charger les exercices legacy depuis les fichiers Python.

Supporte:
- Pattern A: Fichiers Python (gm07_exercises.py, gm08_exercises.py, tests_dyn_exercises.py)
- Pattern B: Curriculum JSON (curriculum_6e.json, curriculum_5e.json) - à implémenter si nécessaire
"""

import os
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

# Ajouter le chemin du backend au PYTHONPATH
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import de la normalisation
try:
    from backend.services.curriculum_persistence_service import normalize_code_officiel
except ImportError:
    # Fallback si import échoue
    def normalize_code_officiel(code: str) -> str:
        """Normalise le code officiel au format canonique."""
        import re
        code = code.strip()
        if not code:
            return code
        match = re.match(r'^(\d+[eE])_(.+)$', code)
        if match:
            niveau = match.group(1).lower()
            reste = match.group(2).upper()
            return f"{niveau}_{reste}"
        return code

logger = None
try:
    from backend.observability.logger import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def discover_legacy_sources() -> Dict[str, List[str]]:
    """
    Découvre toutes les sources d'exercices legacy dans le repo.
    
    Returns:
        Dict avec les clés:
        - "python_files": Liste des fichiers Python contenant des exercices
        - "json_files": Liste des fichiers JSON curriculum
        - "chapters": Liste des codes de chapitres trouvés
    """
    backend_dir = Path(__file__).parent.parent
    data_dir = backend_dir / "data"
    curriculum_dir = backend_dir / "curriculum"
    
    sources = {
        "python_files": [],
        "json_files": [],
        "chapters": []
    }
    
    # Pattern A: Fichiers Python
    python_mapping = {
        "gm07_exercises.py": "6E_GM07",
        "gm08_exercises.py": "6E_GM08",
        "tests_dyn_exercises.py": "6E_TESTS_DYN"
    }
    
    if data_dir.exists():
        for filename, chapter_code in python_mapping.items():
            filepath = data_dir / filename
            if filepath.exists():
                sources["python_files"].append(str(filepath))
                sources["chapters"].append(chapter_code)
                if logger:
                    logger.info(f"✅ Trouvé fichier Python: {filename} → {chapter_code}")
    
    # Pattern B: Fichiers JSON curriculum
    if curriculum_dir.exists():
        for json_file in curriculum_dir.glob("curriculum_*.json"):
            sources["json_files"].append(str(json_file))
            if logger:
                logger.info(f"✅ Trouvé fichier JSON: {json_file.name}")
    
    return sources


def load_exercises_from_python_file(filepath: str, chapter_code: str) -> List[Dict[str, Any]]:
    """
    Charge les exercices depuis un fichier Python legacy.
    
    Args:
        filepath: Chemin vers le fichier Python
        chapter_code: Code du chapitre (ex: "6E_GM07")
    
    Returns:
        Liste des exercices avec leurs métadonnées
    """
    if not os.path.exists(filepath):
        if logger:
            logger.warning(f"⚠️ Fichier non trouvé: {filepath}")
        return []
    
    try:
        # Importer dynamiquement selon le chapitre
        if chapter_code == "6E_GM07":
            from data.gm07_exercises import GM07_EXERCISES as exercises
        elif chapter_code == "6E_GM08":
            from data.gm08_exercises import GM08_EXERCISES as exercises
        elif chapter_code == "6E_TESTS_DYN":
            from data.tests_dyn_exercises import TESTS_DYN_EXERCISES as exercises
        else:
            if logger:
                logger.warning(f"⚠️ Chapitre non supporté: {chapter_code}")
            return []
        
        # Normaliser les exercices pour la migration
        normalized = []
        for ex in exercises:
            # Filtrer uniquement les exercices statiques (is_dynamic=False ou absent)
            is_dynamic = ex.get("is_dynamic", False)
            if is_dynamic:
                continue  # Skip les exercices dynamiques
            
            # Normaliser le code du chapitre
            normalized_chapter_code = normalize_code_officiel(chapter_code)
            
            # Extraire les champs nécessaires
            normalized_ex = {
                "id": ex.get("id"),
                "chapter_code": normalized_chapter_code,
                "title": None,  # Sera généré si absent
                "difficulty": ex.get("difficulty", "moyen"),
                "offer": ex.get("offer", "free"),
                "enonce_html": ex.get("enonce_html", ""),
                "solution_html": ex.get("solution_html", ""),
                "needs_svg": ex.get("needs_svg", False),
                "exercise_type": ex.get("exercise_type"),
                "family": ex.get("family"),
                "variables": ex.get("variables"),
                "svg_enonce_brief": ex.get("svg_enonce_brief"),
                "svg_solution_brief": ex.get("svg_solution_brief"),
                # Métadonnées de migration
                "source": "legacy_migration",
                "legacy_ref": f"{os.path.basename(filepath)}:id={ex.get('id')}",
                "is_dynamic": False  # Forcer à False pour les statiques
            }
            
            normalized.append(normalized_ex)
        
        if logger:
            logger.info(f"✅ Chargé {len(normalized)} exercices statiques depuis {filepath}")
        
        return normalized
        
    except ImportError as e:
        if logger:
            logger.error(f"❌ Erreur d'import pour {chapter_code}: {e}")
        return []
    except Exception as e:
        if logger:
            logger.error(f"❌ Erreur lors du chargement de {filepath}: {e}")
        return []


def load_all_legacy_exercises(chapter_code: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Charge tous les exercices legacy, ou ceux d'un chapitre spécifique.
    
    Args:
        chapter_code: Code du chapitre (ex: "6E_GM07") ou None pour tous
    
    Returns:
        Dict avec clé=chapter_code, valeur=liste d'exercices
    """
    sources = discover_legacy_sources()
    all_exercises = {}
    
    # Pattern A: Fichiers Python
    # Mapping: fichier -> code legacy (en majuscules) -> code normalisé
    python_mapping = {
        "gm07_exercises.py": ("6E_GM07", "6e_GM07"),
        "gm08_exercises.py": ("6E_GM08", "6e_GM08"),
        "tests_dyn_exercises.py": ("6E_TESTS_DYN", "6e_TESTS_DYN")
    }
    
    backend_dir = Path(__file__).parent.parent
    data_dir = backend_dir / "data"
    
    for filename, (legacy_code, normalized_code) in python_mapping.items():
        # Vérifier si on doit charger ce chapitre
        if chapter_code:
            # Normaliser le code demandé pour comparaison
            normalized_chapter_code = normalize_code_officiel(chapter_code)
            # Comparer avec le code normalisé ET le code legacy (pour flexibilité)
            if normalized_code != normalized_chapter_code and legacy_code != chapter_code:
                continue
        
        filepath = data_dir / filename
        if filepath.exists():
            exercises = load_exercises_from_python_file(str(filepath), legacy_code)
            if exercises:
                # Utiliser le code normalisé comme clé pour cohérence
                all_exercises[normalized_code] = exercises
    
    return all_exercises

