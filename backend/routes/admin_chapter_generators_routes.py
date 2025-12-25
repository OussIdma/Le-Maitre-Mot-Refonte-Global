"""
Routes admin pour la gestion des générateurs activés dans un chapitre (P4.B)

Endpoints:
- GET /api/v1/admin/chapters/{code}/generators
- PUT /api/v1/admin/chapters/{code}/generators
- POST /api/v1/admin/chapters/{code}/generators/auto-fill
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from backend.server import db
from backend.services.curriculum_persistence_service import (
    CurriculumPersistenceService,
    EnabledGeneratorConfig,
)
from backend.generators.factory import GeneratorFactory
from backend.utils.difficulty_utils import (
    normalize_difficulty,
    get_all_canonical_difficulties,
    auto_complete_presets,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/chapters", tags=["Admin - Chapter Generators"])


# =============================================================================
# MODÈLES
# =============================================================================

class GeneratorInfo(BaseModel):
    """Information sur un générateur disponible"""
    key: str
    label: str
    version: str
    exercise_type: Optional[str] = None
    supported_difficulties: List[str] = Field(default_factory=list)
    min_offer: str = Field(default="free", description="Offre minimum: 'free' ou 'pro'")
    is_gold: bool = Field(default=False, description="Si le générateur est classé GOLD")
    is_disabled: bool = Field(default=False, description="Si le générateur est désactivé")


class EnabledGeneratorInfo(BaseModel):
    """Information sur un générateur activé dans un chapitre"""
    generator_key: str
    difficulty_presets: List[str]
    min_offer: str
    is_enabled: bool
    generator_info: Optional[GeneratorInfo] = None  # Info complète du générateur


class ChapterGeneratorsResponse(BaseModel):
    """Réponse pour GET /chapters/{code}/generators"""
    chapter_code: str
    available_generators: List[GeneratorInfo] = Field(default_factory=list)
    enabled_generators: List[EnabledGeneratorInfo] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class UpdateChapterGeneratorsRequest(BaseModel):
    """Requête pour PUT /chapters/{code}/generators"""
    enabled_generators: List[EnabledGeneratorConfig]


class AutoFillResponse(BaseModel):
    """Réponse pour POST /chapters/{code}/generators/auto-fill"""
    chapter_code: str
    added_generators: List[str] = Field(default_factory=list)
    suggestions: List[Dict[str, Any]] = Field(default_factory=list)
    message: str


# =============================================================================
# HELPERS
# =============================================================================

def get_generator_info(generator_key: str) -> Optional[GeneratorInfo]:
    """Récupère les informations complètes d'un générateur"""
    try:
        gen_class = GeneratorFactory.get(generator_key)
        if not gen_class:
            return None
        
        all_gens = GeneratorFactory.list_all(include_disabled=True)
        gen_meta = next((g for g in all_gens if g["key"] == generator_key.upper()), None)
        
        if not gen_meta:
            return None
        
        # Récupérer les difficultés supportées depuis le schéma
        schema = gen_class.get_schema()
        supported_difficulties = []
        if schema:
            difficulty_param = next((p for p in schema if p.name == "difficulty"), None)
            if difficulty_param and hasattr(difficulty_param, 'options'):
                supported_difficulties = difficulty_param.options or []
        
        # Normaliser les difficultés
        normalized_difficulties = []
        for diff in supported_difficulties:
            try:
                normalized = normalize_difficulty(diff)
                if normalized not in normalized_difficulties:
                    normalized_difficulties.append(normalized)
            except ValueError:
                pass
        
        # Si aucune difficulté, utiliser les canoniques
        if not normalized_difficulties:
            normalized_difficulties = get_all_canonical_difficulties()
        
        return GeneratorInfo(
            key=generator_key.upper(),
            label=gen_meta.get("label", generator_key),
            version=gen_meta.get("version", ""),
            exercise_type=gen_meta.get("exercise_type"),
            supported_difficulties=normalized_difficulties,
            min_offer=gen_meta.get("min_offer", "free"),
            is_gold=True,  # Tous les générateurs non désactivés sont considérés GOLD pour l'instant
            is_disabled=gen_meta.get("disabled", False),
        )
    except Exception as e:
        logger.warning(f"Erreur lors de la récupération des infos du générateur {generator_key}: {e}")
        return None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/{chapter_code}/generators", response_model=ChapterGeneratorsResponse)
async def get_chapter_generators(chapter_code: str):
    """
    Récupère la liste des générateurs disponibles et activés pour un chapitre.
    
    Retourne:
    - Tous les générateurs disponibles (GOLD + autres)
    - Les générateurs actuellement activés dans ce chapitre
    - Les difficultés réellement supportées par chaque générateur
    """
    try:
        service = CurriculumPersistenceService(db)
        chapter = await service.get_chapter_by_code(chapter_code)
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapitre '{chapter_code}' introuvable"
            )
        
        # Récupérer tous les générateurs disponibles
        all_generators = GeneratorFactory.list_all(include_disabled=False)
        available_generators = []
        
        for gen_meta in all_generators:
            gen_info = get_generator_info(gen_meta["key"])
            if gen_info:
                available_generators.append(gen_info)
        
        # Récupérer les générateurs activés dans ce chapitre
        enabled_generators_data = chapter.get("enabled_generators", [])
        enabled_generators = []
        
        for enabled_gen in enabled_generators_data:
            gen_key = enabled_gen.get("generator_key", "").upper()
            gen_info = get_generator_info(gen_key)
            
            enabled_generators.append(EnabledGeneratorInfo(
                generator_key=gen_key,
                difficulty_presets=enabled_gen.get("difficulty_presets", []),
                min_offer=enabled_gen.get("min_offer", "free"),
                is_enabled=enabled_gen.get("is_enabled", True),
                generator_info=gen_info,
            ))
        
        # Warnings
        warnings = []
        pipeline = chapter.get("pipeline", "SPEC")
        if pipeline in ["TEMPLATE", "MIXED"] and not enabled_generators_data:
            warnings.append(
                f"⚠️ Ce chapitre est en mode '{pipeline}' mais aucun générateur n'est activé. "
                f"La génération dynamique ne fonctionnera pas."
            )
        
        return ChapterGeneratorsResponse(
            chapter_code=chapter_code,
            available_generators=available_generators,
            enabled_generators=enabled_generators,
            warnings=warnings,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des générateurs pour {chapter_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des générateurs: {str(e)}"
        )


@router.put("/{chapter_code}/generators", response_model=Dict[str, Any])
async def update_chapter_generators(chapter_code: str, request: UpdateChapterGeneratorsRequest):
    """
    Met à jour la liste des générateurs activés dans un chapitre.
    
    Payload:
    {
      "enabled_generators": [
        {
          "generator_key": "THALES_V2",
          "difficulty_presets": ["facile", "moyen", "difficile"],
          "min_offer": "free",
          "is_enabled": true
        }
      ]
    }
    """
    try:
        service = CurriculumPersistenceService(db)
        chapter = await service.get_chapter_by_code(chapter_code)
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapitre '{chapter_code}' introuvable"
            )
        
        # Valider les générateurs
        for enabled_gen in request.enabled_generators:
            gen_key = enabled_gen.generator_key.upper()
            
            # Vérifier que le générateur existe
            gen_class = GeneratorFactory.get(gen_key)
            if not gen_class:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Générateur '{gen_key}' introuvable ou désactivé"
                )
            
            # P4.C - Normaliser et auto-compléter les presets
            # Récupérer les difficultés supportées par le générateur
            schema = gen_class.get_schema()
            supported_difficulties = []
            if schema:
                difficulty_param = next((p for p in schema if p.name == "difficulty"), None)
                if difficulty_param and hasattr(difficulty_param, 'options'):
                    supported_difficulties = difficulty_param.options or []
            
            # Normaliser les difficultés supportées
            supported_normalized = [normalize_difficulty(d) for d in supported_difficulties] if supported_difficulties else get_all_canonical_difficulties()
            
            # Normaliser les presets demandés
            normalized_presets = []
            for diff in enabled_gen.difficulty_presets:
                try:
                    normalized = normalize_difficulty(diff)
                    if normalized not in normalized_presets:
                        normalized_presets.append(normalized)
                except ValueError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Difficulté invalide '{diff}' pour le générateur '{gen_key}': {e}"
                    )
            
            # P4.C - Auto-compléter les presets manquants
            completed_presets = auto_complete_presets(
                requested_presets=normalized_presets,
                supported_difficulties=supported_normalized
            )
            
            # Remplacer les difficultés normalisées et complétées
            enabled_gen.difficulty_presets = completed_presets
        
        # Mettre à jour le chapitre
        from backend.services.curriculum_persistence_service import ChapterUpdateRequest
        update_request = ChapterUpdateRequest(
            enabled_generators=request.enabled_generators
        )
        
        updated = await service.update_chapter(chapter_code, update_request)
        
        logger.info(
            f"[P4.B] Générateurs mis à jour pour {chapter_code}: "
            f"{len(request.enabled_generators)} générateur(s) activé(s)"
        )
        
        return {
            "chapter_code": chapter_code,
            "enabled_generators_count": len(request.enabled_generators),
            "message": "Générateurs mis à jour avec succès"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des générateurs pour {chapter_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour des générateurs: {str(e)}"
        )


@router.post("/{chapter_code}/generators/normalize", response_model=Dict[str, Any])
async def normalize_chapter_generators(chapter_code: str):
    """
    Normalise et complète les presets de difficultés pour tous les générateurs activés.
    
    P4.C - Auto-complète les presets manquants et normalise les difficultés.
    """
    try:
        service = CurriculumPersistenceService(db)
        chapter = await service.get_chapter_by_code(chapter_code)
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapitre '{chapter_code}' introuvable"
            )
        
        enabled_generators_data = chapter.get("enabled_generators", [])
        updated_count = 0
        
        for enabled_gen_data in enabled_generators_data:
            gen_key = enabled_gen_data.get("generator_key", "").upper()
            gen_class = GeneratorFactory.get(gen_key)
            
            if not gen_class:
                continue
            
            # Récupérer les difficultés supportées
            schema = gen_class.get_schema()
            supported_difficulties = []
            if schema:
                difficulty_param = next((p for p in schema if p.name == "difficulty"), None)
                if difficulty_param and hasattr(difficulty_param, 'options'):
                    supported_difficulties = difficulty_param.options or []
            
            # Normaliser les difficultés supportées
            supported_normalized = [normalize_difficulty(d) for d in supported_difficulties] if supported_difficulties else get_all_canonical_difficulties()
            
            # Normaliser les presets actuels
            current_presets = enabled_gen_data.get("difficulty_presets", [])
            normalized_presets = [normalize_difficulty(d) for d in current_presets]
            
            # Auto-compléter
            completed_presets = auto_complete_presets(
                requested_presets=normalized_presets,
                supported_difficulties=supported_normalized
            )
            
            # Mettre à jour si nécessaire
            if set(completed_presets) != set(current_presets):
                enabled_gen_data["difficulty_presets"] = completed_presets
                updated_count += 1
        
        # Sauvegarder si des modifications ont été faites
        if updated_count > 0:
            from backend.services.curriculum_persistence_service import ChapterUpdateRequest, EnabledGeneratorConfig
            update_request = ChapterUpdateRequest(
                enabled_generators=[EnabledGeneratorConfig(**eg) for eg in enabled_generators_data]
            )
            await service.update_chapter(chapter_code, update_request)
        
        return {
            "chapter_code": chapter_code,
            "updated_generators": updated_count,
            "message": f"{updated_count} générateur(s) normalisé(s)"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la normalisation pour {chapter_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la normalisation: {str(e)}"
        )


@router.post("/{chapter_code}/generators/auto-fill", response_model=AutoFillResponse)
async def auto_fill_chapter_generators(chapter_code: str):
    """
    Active automatiquement les générateurs GOLD non référencés pour un chapitre.
    
    Cette fonction suggère et active les générateurs GOLD qui ne sont pas encore
    référencés dans le curriculum, en se basant sur les exercise_types du chapitre.
    """
    try:
        service = CurriculumPersistenceService(db)
        chapter = await service.get_chapter_by_code(chapter_code)
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapitre '{chapter_code}' introuvable"
            )
        
        # Récupérer tous les générateurs GOLD
        all_generators = GeneratorFactory.list_all(include_disabled=False)
        gold_generators = []
        
        for gen_meta in all_generators:
            gen_key = gen_meta["key"]
            gen_info = get_generator_info(gen_key)
            if gen_info and not gen_info.is_disabled:
                gold_generators.append(gen_info)
        
        # Récupérer les générateurs déjà activés
        enabled_generators_data = chapter.get("enabled_generators", [])
        enabled_keys = {eg.get("generator_key", "").upper() for eg in enabled_generators_data}
        
        # Récupérer les exercise_types du chapitre pour suggérer des correspondances
        exercise_types = chapter.get("exercise_types", [])
        
        # Suggestions basées sur les exercise_types
        suggestions = []
        added_generators = []
        
        for gen_info in gold_generators:
            # Si déjà activé, skip
            if gen_info.key in enabled_keys:
                continue
            
            # Vérifier si le générateur correspond à un exercise_type
            should_add = False
            reason = ""
            
            if gen_info.exercise_type:
                # Vérifier si l'exercise_type correspond
                if gen_info.exercise_type.upper() in [et.upper() for et in exercise_types]:
                    should_add = True
                    reason = f"Correspond à l'exercise_type '{gen_info.exercise_type}' du chapitre"
            
            # Vérifier aussi par nom de générateur (ex: SYMETRIE_AXIALE_V2 pour chapitre symétrie)
            if not should_add:
                gen_name_lower = gen_info.label.lower()
                chapter_libelle_lower = chapter.get("libelle", "").lower()
                
                # Correspondances simples
                if "symétrie" in gen_name_lower and "symétrie" in chapter_libelle_lower:
                    should_add = True
                    reason = "Correspond au thème du chapitre (symétrie)"
                elif "thales" in gen_name_lower or "agrandissement" in gen_name_lower:
                    # Thalès peut être dans plusieurs chapitres, on suggère seulement
                    suggestions.append({
                        "generator_key": gen_info.key,
                        "label": gen_info.label,
                        "reason": "Générateur GOLD disponible (à activer manuellement si pertinent)"
                    })
            
            if should_add:
                # Ajouter le générateur avec toutes les difficultés supportées
                difficulty_presets = gen_info.supported_difficulties or get_all_canonical_difficulties()
                
                enabled_generators_data.append({
                    "generator_key": gen_info.key,
                    "difficulty_presets": difficulty_presets,
                    "min_offer": gen_info.min_offer,
                    "is_enabled": True,
                })
                added_generators.append(gen_info.key)
                logger.info(
                    f"[P4.B AUTO-FILL] Ajout automatique de {gen_info.key} à {chapter_code}: {reason}"
                )
        
        # Mettre à jour le chapitre si des générateurs ont été ajoutés
        if added_generators:
            from backend.services.curriculum_persistence_service import ChapterUpdateRequest
            update_request = ChapterUpdateRequest(
                enabled_generators=[EnabledGeneratorConfig(**eg) for eg in enabled_generators_data]
            )
            await service.update_chapter(chapter_code, update_request)
        
        message = (
            f"{len(added_generators)} générateur(s) activé(s) automatiquement. "
            f"{len(suggestions)} suggestion(s) disponible(s)."
        )
        
        return AutoFillResponse(
            chapter_code=chapter_code,
            added_generators=added_generators,
            suggestions=suggestions,
            message=message,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'auto-fill pour {chapter_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'auto-fill: {str(e)}"
        )

