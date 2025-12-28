"""
Service de synchronisation entre admin_exercises et exercise_types.

Quand un exercice dynamique est créé/modifié dans admin_exercises,
ce service synchronise automatiquement un document correspondant dans exercise_types
pour qu'il soit visible par l'endpoint MathALÉA.
"""

import logging
from typing import Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid

from backend.constants.collections import EXERCISE_TYPES_COLLECTION
from backend.generators.factory import GeneratorFactory

logger = logging.getLogger(__name__)


def _normalize_chapter_code(chapter_code: str) -> str:
    """Normalise le code de chapitre: upper() + remplacer '-' par '_'."""
    return chapter_code.upper().replace("-", "_")


def _infer_domaine(chapter_code: str) -> str:
    """
    Infère le domaine depuis le code de chapitre.
    
    Exemples:
    - 6E_N10 -> Nombres
    - 6E_G07 -> Géométrie
    - 6E_SP01 -> Statistiques et probabilités
    """
    normalized = _normalize_chapter_code(chapter_code)
    
    # Extraire le préfixe du code (N, G, SP, etc.)
    parts = normalized.split("_")
    if len(parts) < 2:
        return "Géométrie"  # Fallback
    
    prefix = parts[1][0] if parts[1] else "G"
    
    # Mapping préfixe -> domaine
    domaine_map = {
        "N": "Nombres et calculs",
        "G": "Espace et géométrie",
        "GM": "Grandeurs et mesures",
        "SP": "Statistiques et probabilités",
        "A": "Algèbre",
        "F": "Fonctions",
    }
    
    # Chercher le préfixe le plus long qui correspond
    for key in sorted(domaine_map.keys(), key=len, reverse=True):
        if parts[1].startswith(key):
            return domaine_map[key]
    
    # Fallback par défaut
    return "Géométrie"


def _get_generator_label(generator_key: str) -> str:
    """Récupère le label lisible d'un générateur."""
    try:
        gen_info = GeneratorFactory.get_generator_info(generator_key)
        if gen_info and hasattr(gen_info, 'label'):
            return gen_info.label
        if gen_info and hasattr(gen_info, 'name'):
            return gen_info.name
    except Exception as e:
        logger.debug(f"Impossible de récupérer le label pour {generator_key}: {e}")
    
    # Fallback: formatter depuis le generator_key
    return generator_key.replace("_", " ").title()


async def sync_admin_exercise_to_exercise_types(
    db: AsyncIOMotorDatabase,
    chapter_code: str,
    generator_key: str,
    needs_svg: Optional[bool] = None,
) -> None:
    """
    Synchronise un exercice admin dynamique vers exercise_types.
    
    Crée ou met à jour un document dans exercise_types pour qu'il soit visible
    par l'endpoint GET /api/mathalea/chapters/{chapter_code}/exercise-types.
    
    Args:
        db: Connexion MongoDB
        chapter_code: Code du chapitre (ex: "6E_N10")
        generator_key: Clé du générateur (ex: "NOMBRES_ENTIERS_V1")
        needs_svg: Si l'exercice nécessite un SVG (optionnel)
    
    Raises:
        ValueError: Si chapter_code ou generator_key est vide
    """
    if not chapter_code or not chapter_code.strip():
        raise ValueError("chapter_code ne peut pas être vide")
    if not generator_key or not generator_key.strip():
        raise ValueError("generator_key ne peut pas être vide")
    
    # Normaliser chapter_code
    normalized_chapter_code = _normalize_chapter_code(chapter_code)
    
    # Extraire le niveau depuis chapter_code (ex: "6E_N10" -> "6e")
    niveau = normalized_chapter_code.split("_")[0].lower()
    
    # Inférer le domaine
    domaine = _infer_domaine(normalized_chapter_code)
    
    # Récupérer le label du générateur
    titre = _get_generator_label(generator_key)
    
    # Collection exercise_types
    collection = db[EXERCISE_TYPES_COLLECTION]
    
    # Vérifier si un document existe déjà (idempotent)
    existing = await collection.find_one({
        "chapter_code": normalized_chapter_code,
        "code_ref": generator_key
    })
    
    if existing:
        # Mettre à jour le document existant
        update_doc = {
            "$set": {
                "titre": titre,
                "domaine": domaine,
                "niveau": niveau,
                "chapitre_id": normalized_chapter_code,  # Fallback legacy
                "updated_at": datetime.now(timezone.utc),
                "requires_svg": needs_svg if needs_svg is not None else existing.get("requires_svg", False),
                "source": "admin_exercises_auto_sync"
            }
        }
        
        await collection.update_one(
            {"_id": existing["_id"]},
            update_doc
        )
        
        logger.info(
            f"[SYNC] ExerciseType mis à jour: chapter_code={normalized_chapter_code}, "
            f"code_ref={generator_key}"
        )
    else:
        # Créer un nouveau document
        exercise_type_id = f"{normalized_chapter_code}_{generator_key}_{uuid.uuid4().hex[:8]}"
        
        exercise_type_doc = {
            "id": exercise_type_id,
            "code_ref": generator_key,
            "titre": titre,
            "chapter_code": normalized_chapter_code,
            "chapitre_id": normalized_chapter_code,  # Fallback legacy
            "niveau": niveau,
            "domaine": domaine,
            "generator_kind": "DYNAMIC",
            "difficulty_levels": ["facile", "moyen", "difficile"],
            "min_questions": 1,
            "max_questions": 10,
            "default_questions": 5,
            "requires_svg": needs_svg if needs_svg is not None else False,
            "supports_seed": True,
            "supports_ai_enonce": False,
            "supports_ai_correction": False,
            "competences_ids": [],
            "question_kinds": {},
            "random_config": {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "source": "admin_exercises_auto_sync"
        }
        
        await collection.insert_one(exercise_type_doc)
        
        logger.info(
            f"[SYNC] ExerciseType créé: chapter_code={normalized_chapter_code}, "
            f"code_ref={generator_key}, id={exercise_type_id}"
        )


async def delete_exercise_type_sync(
    db: AsyncIOMotorDatabase,
    chapter_code: str,
    generator_key: str,
) -> None:
    """
    Supprime ou archive un exercise_type correspondant à un exercice admin supprimé.
    
    Pour l'instant, on ne supprime pas vraiment pour éviter de casser la lecture.
    On pourrait ajouter un champ "archived" si nécessaire.
    
    Args:
        db: Connexion MongoDB
        chapter_code: Code du chapitre
        generator_key: Clé du générateur
    """
    normalized_chapter_code = _normalize_chapter_code(chapter_code)
    collection = db[EXERCISE_TYPES_COLLECTION]
    
    # Pour l'instant, on ne supprime pas, juste un log
    # TODO: Implémenter un système d'archivage si nécessaire
    logger.info(
        f"[SYNC] Exercise admin supprimé: chapter_code={normalized_chapter_code}, "
        f"code_ref={generator_key}. ExerciseType conservé pour compatibilité."
    )

