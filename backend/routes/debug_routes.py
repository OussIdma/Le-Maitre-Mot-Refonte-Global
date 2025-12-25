"""
Routes de debug DEV-only pour diagnostiquer les problèmes de générateurs

P4.D - Endpoint pour voir clairement pourquoi un générateur n'est pas visible
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
import os
import logging

from backend.server import db
from backend.services.curriculum_persistence_service import CurriculumPersistenceService
from backend.generators.factory import GeneratorFactory
from backend.utils.difficulty_utils import normalize_difficulty, get_all_canonical_difficulties
from curriculum.loader import get_chapter_by_official_code  # Legacy fallback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debug", tags=["Debug"])


def is_debug_enabled() -> bool:
    """Vérifie si le mode debug est activé (dev-only)"""
    env = os.getenv("ENVIRONMENT", "development")
    debug_flag = os.getenv("DEBUG", "false").lower() == "true"
    return env != "production" or debug_flag


@router.get("/chapters/{chapter_code}/generators")
async def debug_chapter_generators(chapter_code: str) -> Dict[str, Any]:
    """
    P4.D - Endpoint de debug pour diagnostiquer les générateurs d'un chapitre.
    
    DEV-ONLY : Accessible uniquement si ENVIRONMENT != production ou DEBUG=true
    
    Retourne :
    - enabled_generators_in_db : Liste des générateurs activés dans la DB
    - factory_list_all_count : Nombre total de générateurs dans GeneratorFactory
    - active_generators_resolved : Liste des générateurs activés avec leurs infos
    - warnings : Liste des warnings (chapitre en JSON mais pas en DB, etc.)
    """
    if not is_debug_enabled():
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "DEBUG_DISABLED",
                "error": "debug_disabled",
                "message": "L'endpoint de debug n'est accessible qu'en mode développement.",
                "hint": "Activez DEBUG=true ou ENVIRONMENT=development pour y accéder."
            }
        )
    
    warnings = []
    enabled_generators_in_db = []
    active_generators_resolved = []
    
    # 1. Charger le chapitre depuis MongoDB
    curriculum_service_db = CurriculumPersistenceService(db)
    await curriculum_service_db.initialize()
    
    chapter_from_db = await curriculum_service_db.get_chapter_by_code(chapter_code)
    
    if not chapter_from_db:
        # Fallback legacy
        chapter_legacy = get_chapter_by_official_code(chapter_code)
        if chapter_legacy:
            warnings.append("chapter found in JSON but DB is used (migration nécessaire)")
        else:
            warnings.append(f"chapter '{chapter_code}' not found in DB or JSON")
    else:
        # Récupérer enabled_generators depuis la DB
        enabled_generators_list = chapter_from_db.get("enabled_generators", [])
        enabled_generators_in_db = [
            eg.get("generator_key")
            for eg in enabled_generators_list
            if eg.get("is_enabled") is True
        ]
        
        if not enabled_generators_in_db:
            warnings.append("enabled_generators empty -> prof sees static only")
    
    # 2. Récupérer tous les générateurs de la Factory
    factory_list_all = GeneratorFactory.list_all(include_disabled=False)
    factory_list_all_count = len(factory_list_all)
    
    # 3. Résoudre les générateurs activés avec leurs infos
    for gen_key in enabled_generators_in_db:
        gen_class = GeneratorFactory.get(gen_key)
        if not gen_class:
            warnings.append(f"generator '{gen_key}' in enabled_generators but not found in Factory")
            continue
        
        gen_meta = gen_class.get_meta()
        schema = gen_class.get_schema()
        
        # Récupérer les difficultés supportées
        supported_difficulties = []
        if schema:
            difficulty_param = next((p for p in schema if p.name == "difficulty"), None)
            if difficulty_param and hasattr(difficulty_param, 'options'):
                supported_raw = difficulty_param.options or []
                # Normaliser les difficultés
                for diff in supported_raw:
                    try:
                        normalized = normalize_difficulty(diff)
                        if normalized not in supported_difficulties:
                            supported_difficulties.append(normalized)
                    except ValueError:
                        pass
        
        if not supported_difficulties:
            supported_difficulties = get_all_canonical_difficulties()
        
        active_generators_resolved.append({
            "key": gen_key,
            "label": gen_meta.label if gen_meta else gen_key,
            "version": gen_meta.version if gen_meta else "unknown",
            "supported_difficulties": supported_difficulties,
            "premium": getattr(gen_meta, 'min_offer', 'free') == 'pro' if gen_meta else False,
            "exercise_type": gen_meta.exercise_type if gen_meta else None
        })
    
    return {
        "chapter_code": chapter_code,
        "enabled_generators_in_db": enabled_generators_in_db,
        "factory_list_all_count": factory_list_all_count,
        "active_generators_resolved": active_generators_resolved,
        "warnings": warnings,
        "chapter_found_in_db": chapter_from_db is not None,
        "pipeline": chapter_from_db.get("pipeline") if chapter_from_db else None
    }



