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
import re
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from functools import lru_cache
import time

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
    pipeline: Optional[Literal["SPEC", "TEMPLATE", "MIXED"]] = Field(
        default="SPEC",
        description="Pipeline de génération: SPEC (statique), TEMPLATE (dynamique), MIXED (les deux)"
    )
    
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
# Cache catalogue (par niveau) avec TTL simple
_catalog_cache: Dict[str, Dict] = {}
_catalog_cache_timestamp: Dict[str, float] = {}
CATALOG_CACHE_TTL_SECONDS = 300


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


def invalidate_catalog_cache(level: Optional[str] = None) -> None:
    """
    Invalide le cache catalogue pour un niveau (ou tous).
    """
    global _catalog_cache, _catalog_cache_timestamp
    if level:
        _catalog_cache.pop(level, None)
        _catalog_cache_timestamp.pop(level, None)
        logger.debug(f"[CATALOG] Cache invalidé pour {level}")
    else:
        _catalog_cache.clear()
        _catalog_cache_timestamp.clear()
        logger.debug("[CATALOG] Cache invalidé pour tous les niveaux")


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
# FILTRAGE CHAPITRES DE TEST
# ============================================================================

def is_test_chapter(code_officiel: str) -> bool:
    """
    Détermine si un code_officiel est un chapitre de test.
    
    Critères:
    - Contient "TEST" ou "QA" (insensible à la casse)
    - Exemples: 6e_AA_TEST, 6e_TESTS_DYN, 6e_MIXED_QA
    
    Args:
        code_officiel: Code officiel du chapitre (ex: "6e_AA_TEST")
        
    Returns:
        True si c'est un chapitre de test, False sinon
    """
    if not code_officiel:
        return False
    code_upper = code_officiel.upper()
    return bool(re.search(r'(TEST|QA)', code_upper))


def should_show_test_chapters() -> bool:
    """
    Détermine si les chapitres de test doivent être affichés.
    
    Mode dev activé si:
    - Variable d'environnement SHOW_TEST_CHAPTERS=true
    
    Returns:
        True si les chapitres de test doivent être affichés, False sinon
    """
    return os.getenv("SHOW_TEST_CHAPTERS", "false").lower() == "true"


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


async def get_catalog(level: str = "6e", db=None) -> Dict:
    """
    Génère le catalogue complet pour le frontend.
    
    **Source de vérité enrichie** :
    - Curriculum (exercise_types) : source principale
    - Collection exercises (DB) : enrichissement si exercices existent en DB
    
    Si un chapitre a des exercices en DB mais pas d'exercise_types dans le curriculum,
    les exercise_types sont extraits depuis la DB pour rendre le chapitre disponible.
    
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
        db: Base de données MongoDB (optionnel, pour enrichissement depuis exercises)
        
    Returns:
        Dictionnaire du catalogue pour le frontend
    """
    try:
        # Cache simple avec TTL
        now = time.time()
        if level in _catalog_cache and now - _catalog_cache_timestamp.get(level, 0) < CATALOG_CACHE_TTL_SECONDS:
            return _catalog_cache[level]
        
        if level != "6e":
            return {
                "level": level,
                "domains": [],
                "macro_groups": [],
                "error": f"Niveau '{level}' non supporté pour l'instant"
            }
        
        index = get_curriculum_index()
        
        # Service de synchronisation pour enrichir depuis DB (si db fourni)
        sync_service = None
        if db is not None:
            try:
                from backend.services.curriculum_sync_service import get_curriculum_sync_service
                sync_service = get_curriculum_sync_service(db)
            except Exception as e:
                logger.warning(f"[CATALOG] Impossible d'initialiser sync_service pour enrichissement DB: {e}")
                # Continuer sans enrichissement DB plutôt que de planter
        
        # Déterminer si on doit afficher les chapitres de test
        show_test_chapters = should_show_test_chapters()
        
        # Construire les domaines avec chapitres
        domains = []
        for domaine_name in sorted(index.by_domaine.keys()):
            chapters_list = index.by_domaine[domaine_name]
            
            chapters_data = []
            for chapter in sorted(chapters_list, key=lambda c: c.code_officiel):
                # Filtrer les chapitres de test si mode dev non activé
                if not show_test_chapters and is_test_chapter(chapter.code_officiel):
                    continue
                # Source de vérité initiale : curriculum
                generators_from_curriculum = chapter.exercise_types.copy()
                generators_final = generators_from_curriculum.copy()
                source_info = "curriculum"
                
                # Enrichissement depuis DB si exercices existent
                # Pour les chapitres TEMPLATE, on doit vérifier s'il y a des exercices dynamiques
                pipeline_mode = getattr(chapter, 'pipeline', None) or 'SPEC'
                
                if sync_service:
                    try:
                        has_exercises = await sync_service.has_exercises_in_db(chapter.code_officiel)
                        if has_exercises:
                            exercise_types_from_db = await sync_service.get_exercise_types_from_db(chapter.code_officiel)
                            if exercise_types_from_db:
                                # Fusion : curriculum + DB (sans doublons)
                                generators_final = sorted(list(set(generators_from_curriculum) | exercise_types_from_db))
                                if generators_final != generators_from_curriculum:
                                    source_info = "curriculum+db"
                                    logger.info(
                                        f"[CATALOG] Chapitre {chapter.code_officiel} enrichi depuis DB: "
                                        f"curriculum={generators_from_curriculum} → final={generators_final}"
                                    )
                                else:
                                    source_info = "curriculum+db (identique)"
                            else:
                                # Exercices existent mais aucun exercise_type extrait
                                # Pour TEMPLATE, on marque comme disponible même sans exercise_types
                                if pipeline_mode == "TEMPLATE":
                                    # Chapitre TEMPLATE avec exercices dynamiques : disponible
                                    generators_final = ["DYNAMIC"]  # Marqueur pour indiquer dynamique
                                    source_info = "db (dynamic)"
                                    logger.info(
                                        f"[CATALOG] Chapitre {chapter.code_officiel} (TEMPLATE) a des exercices dynamiques en DB"
                                    )
                                else:
                                    logger.warning(
                                        f"[CATALOG] Chapitre {chapter.code_officiel} a des exercices en DB "
                                        f"mais aucun exercise_type extrait (sera marqué 'indisponible')"
                                    )
                        elif pipeline_mode == "TEMPLATE":
                            # Chapitre TEMPLATE sans exercices : indisponible mais visible
                            generators_final = []  # Vide = indisponible
                            source_info = "curriculum (template_no_exercises)"
                            logger.info(
                                f"[CATALOG] Chapitre {chapter.code_officiel} (TEMPLATE) sans exercices dynamiques - marqué indisponible"
                            )
                    except Exception as e:
                        logger.warning(
                            f"[CATALOG] Erreur enrichissement DB pour {chapter.code_officiel}: {e}"
                        )
                        # En cas d'erreur, on garde les generators du curriculum
                
                chapters_data.append({
                    "code_officiel": chapter.code_officiel,
                    "libelle": chapter.libelle,
                    "status": chapter.statut,
                    "schema_requis": chapter.schema_requis,
                    "difficulty_min": chapter.difficulte_min,
                    "difficulty_max": chapter.difficulte_max,
                    "generators": generators_final,
                    "has_svg": any(
                        gen in generators_final
                        for gen in ["LECTURE_HORLOGE", "CALCUL_DUREE", "SYMETRIE_AXIALE", 
                                   "TRIANGLE_QUELCONQUE", "RECTANGLE", "CERCLE", "FRACTION_REPRESENTATION"]
                    ),
                    "_debug_source": source_info  # Debug uniquement (peut être retiré en prod)
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
            
            # Filtrer les codes de test si mode dev non activé
            if not show_test_chapters:
                codes = [code for code in codes if not is_test_chapter(code)]
                # Si tous les codes sont filtrés, exclure le macro group
                if not codes:
                    continue
            
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
        
        result = {
            "level": level,
            "domains": domains,
            "macro_groups": macro_groups,
            "total_chapters": len(index.by_official_code),
            "total_macro_groups": len(macro_groups)
        }
        
        # Mise en cache
        _catalog_cache[level] = result
        _catalog_cache_timestamp[level] = now
        
        return result
    except Exception as e:
        logger.error(f"[CATALOG] Erreur critique lors de la génération du catalogue: {e}", exc_info=True)
        # Retourner un catalogue minimal plutôt que de planter
        return {
            "level": level,
            "domains": [],
            "macro_groups": [],
            "total_chapters": 0,
            "total_macro_groups": 0,
            "error": f"Erreur lors du chargement du catalogue: {str(e)}"
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
