"""
Routes REST pour le système MathALÉA-like
CRUD pour Competence et ExerciseType

Architecture non-destructive - N'affecte pas les routes existantes
"""

from fastapi import APIRouter, HTTPException, Query, Header, File, UploadFile, Request
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import shutil
from pathlib import Path
import base64
import hashlib
import json

logger = logging.getLogger(__name__)

from backend.models.mathalea_models import (
    Competence,
    CompetenceCreate,
    CompetenceUpdate,
    CompetenceListResponse,
    ExerciseType,
    ExerciseTypeCreate,
    ExerciseTypeUpdate,
    ExerciseTypeListResponse,
    ExerciseSheet,
    ExerciseSheetCreate,
    ExerciseSheetUpdate,
    ExerciseSheetListResponse,
    SheetItem,
    SheetItemCreate,
    SheetItemUpdate,
    SheetItemListResponse,
    ExerciseItemConfig,
    ProPdfRequest
)
from backend.constants.collections import (
    EXERCISE_TYPES_COLLECTION,
    COMPETENCES_COLLECTION,
    EXERCISE_SHEETS_COLLECTION,
    SHEET_ITEMS_COLLECTION
)

# Router avec préfixe pour isoler du système existant
router = APIRouter(prefix="/api/mathalea", tags=["MathALÉA System"])

# Connexion MongoDB (réutilise la config existante)
mongo_url = os.environ.get('MONGO_URL')
if not mongo_url:
    raise ValueError("MONGO_URL environment variable is required")

client = AsyncIOMotorClient(mongo_url)
db_name = os.environ.get('DB_NAME', 'le_maitre_mot_db')
db = client[db_name]  # Use unified DB

# Collections dédiées (ne perturbent pas les collections existantes)
competences_collection = db[COMPETENCES_COLLECTION]
exercise_types_collection = db[EXERCISE_TYPES_COLLECTION]  # Same collection as catalogue
exercise_sheets_collection = db[EXERCISE_SHEETS_COLLECTION]
sheet_items_collection = db[SHEET_ITEMS_COLLECTION]


# ============================================================================
# P0: PDF CACHE HELPERS
# ============================================================================

# Cache TTL: 24 hours (MongoDB TTL index will auto-delete expired documents)
PDF_CACHE_TTL_HOURS = 24


def compute_pdf_cache_key(sheet_id: str, layout: str, items_config: List[Dict]) -> str:
    """
    Compute a deterministic cache key for PDF exports.

    The key is based on:
    - sheet_id: unique identifier for the sheet
    - layout: "eco" or "classic"
    - items_config: sorted list of item configs (exercise_type_id, nb_questions, seed, difficulty)

    Returns a SHA256 hash string.
    """
    # Build a deterministic representation of the configuration
    cache_data = {
        "sheet_id": sheet_id,
        "layout": layout,
        "items": sorted([
            {
                "exercise_type_id": item.get("exercise_type_id"),
                "nb_questions": item.get("config", {}).get("nb_questions"),
                "seed": item.get("config", {}).get("seed"),
                "difficulty": item.get("config", {}).get("difficulty")
            }
            for item in items_config
        ], key=lambda x: x.get("exercise_type_id", ""))
    }

    # Create a stable JSON representation
    cache_json = json.dumps(cache_data, sort_keys=True)

    # Return SHA256 hash
    return hashlib.sha256(cache_json.encode()).hexdigest()


async def get_cached_pdf(db_instance, cache_key: str) -> Optional[Dict]:
    """
    Retrieve cached PDF from MongoDB.

    Returns the cached document or None if not found/expired.
    """
    try:
        cached = await db_instance.pdf_cache.find_one({"cache_key": cache_key})
        if cached:
            # Check if still valid (TTL handles auto-deletion, but double-check)
            expires_at = cached.get("expires_at")
            if expires_at and expires_at > datetime.now(timezone.utc):
                logger.info(f"[PDF_CACHE] HIT cache_key={cache_key[:16]}...")
                return cached
            else:
                logger.info(f"[PDF_CACHE] EXPIRED cache_key={cache_key[:16]}...")
                return None
        return None
    except Exception as e:
        logger.warning(f"[PDF_CACHE] Error reading cache: {e}")
        return None


async def store_pdf_in_cache(
    db_instance,
    cache_key: str,
    student_pdf_b64: str,
    correction_pdf_b64: str,
    metadata: Dict
) -> bool:
    """
    Store generated PDF in MongoDB cache with TTL.

    Returns True on success, False on failure.
    """
    try:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=PDF_CACHE_TTL_HOURS)

        cache_doc = {
            "cache_key": cache_key,
            "student_pdf": student_pdf_b64,
            "correction_pdf": correction_pdf_b64,
            "metadata": metadata,
            "created_at": now,
            "expires_at": expires_at  # TTL index will use this field
        }

        # Upsert to avoid duplicates
        await db_instance.pdf_cache.update_one(
            {"cache_key": cache_key},
            {"$set": cache_doc},
            upsert=True
        )

        logger.info(f"[PDF_CACHE] STORED cache_key={cache_key[:16]}... expires_at={expires_at.isoformat()}")
        return True
    except Exception as e:
        logger.error(f"[PDF_CACHE] Error storing cache: {e}")
        return False


# ============================================================================
# ENDPOINTS: Competence
# ============================================================================

@router.post("/competences", response_model=Competence, status_code=201)
async def create_competence(competence: CompetenceCreate):
    """Créer une nouvelle compétence"""
    competence_dict = Competence(**competence.dict()).dict()
    
    # Vérifier si le code existe déjà
    existing = await competences_collection.find_one({"code": competence.code})
    if existing:
        raise HTTPException(status_code=400, detail=f"Competence with code {competence.code} already exists")
    
    await competences_collection.insert_one(competence_dict)
    return Competence(**competence_dict)


@router.get("/competences", response_model=CompetenceListResponse)
async def list_competences(
    niveau: Optional[str] = Query(None, description="Filtrer par niveau"),
    domaine: Optional[str] = Query(None, description="Filtrer par domaine"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Lister les compétences avec filtres"""
    query = {}
    if niveau:
        query["niveau"] = niveau
    if domaine:
        query["domaine"] = domaine
    
    cursor = competences_collection.find(query, {"_id": 0}).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    total = await competences_collection.count_documents(query)
    
    return CompetenceListResponse(
        total=total,
        items=[Competence(**item) for item in items]
    )


@router.get("/competences/{competence_id}", response_model=Competence)
async def get_competence(competence_id: str):
    """Récupérer une compétence par ID"""
    competence = await competences_collection.find_one({"id": competence_id}, {"_id": 0})
    if not competence:
        raise HTTPException(status_code=404, detail="Competence not found")
    return Competence(**competence)


@router.patch("/competences/{competence_id}", response_model=Competence)
async def update_competence(competence_id: str, update: CompetenceUpdate):
    """Mettre à jour une compétence"""
    update_data = {k: v for k, v in update.dict(exclude_unset=True).items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await competences_collection.update_one(
        {"id": competence_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Competence not found")
    
    updated = await competences_collection.find_one({"id": competence_id}, {"_id": 0})
    return Competence(**updated)


@router.delete("/competences/{competence_id}", status_code=204)
async def delete_competence(competence_id: str):
    """Supprimer une compétence"""
    result = await competences_collection.delete_one({"id": competence_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Competence not found")


# ============================================================================
# ENDPOINTS: ExerciseType
# ============================================================================

@router.post("/exercise-types", response_model=ExerciseType, status_code=201)
async def create_exercise_type(exercise_type: ExerciseTypeCreate):
    """Créer un nouveau type d'exercice"""
    exercise_type_dict = ExerciseType(**exercise_type.dict()).dict()
    
    # Vérifier si le code_ref existe déjà
    existing = await exercise_types_collection.find_one({"code_ref": exercise_type.code_ref})
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"ExerciseType with code_ref {exercise_type.code_ref} already exists"
        )
    
    await exercise_types_collection.insert_one(exercise_type_dict)
    return ExerciseType(**exercise_type_dict)


@router.get("/exercise-types", response_model=ExerciseTypeListResponse)
async def list_exercise_types(
    niveau: Optional[str] = Query(None, description="Filtrer par niveau"),
    domaine: Optional[str] = Query(None, description="Filtrer par domaine"),
    chapitre_id: Optional[str] = Query(None, description="Filtrer par chapitre (legacy)"),
    chapter_code: Optional[str] = Query(None, description="Filtrer par code chapitre MathALÉA (ex: 6e_G04)"),
    generator_kind: Optional[str] = Query(None, description="Filtrer par type de générateur"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Lister les types d'exercices avec filtres"""
    query = {}
    if niveau:
        query["niveau"] = niveau
    if domaine:
        query["domaine"] = domaine
    if chapitre_id:
        query["chapitre_id"] = chapitre_id
    if chapter_code:
        query["chapter_code"] = chapter_code
    if generator_kind:
        query["generator_kind"] = generator_kind
    
    cursor = exercise_types_collection.find(query, {"_id": 0}).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    total = await exercise_types_collection.count_documents(query)
    
    return ExerciseTypeListResponse(
        total=total,
        items=[ExerciseType(**item) for item in items]
    )


@router.get("/chapters/{chapter_code}/exercise-types", response_model=ExerciseTypeListResponse)
async def get_chapter_exercise_types(
    chapter_code: str,
    domaine: Optional[str] = Query(None, description="Filtrer par domaine (optionnel)"),
    generator_kind: Optional[str] = Query(None, description="Filtrer par type de générateur (optionnel)"),
    skip: int = Query(0, ge=0, description="Pagination: nombre d'éléments à sauter"),
    limit: int = Query(50, ge=1, le=500, description="Pagination: nombre maximum d'éléments")
):
    """
    Récupérer tous les ExerciseType d'un chapitre MathALÉA spécifique
    
    FILTRE STRICT PAR NIVEAU : Seuls les exercices du niveau du chapitre sont retournés
    pour garantir la cohérence niveau/domaine/chapitre.
    
    Args:
        chapter_code: Code MathALÉA du chapitre (ex: 6e_G07, 4e_N02, 2nde_F01)
        domaine: Filtre optionnel sur le domaine
        generator_kind: Filtre optionnel sur le type de générateur
        skip: Nombre d'éléments à sauter (pagination)
        limit: Nombre maximum d'éléments à retourner
        
    Returns:
        Liste des ExerciseType du chapitre avec métadonnées
        
    Raises:
        404: Si le chapter_code n'existe pas dans la collection chapters
        
    Note:
        Cet endpoint est la méthode recommandée pour récupérer les exercices
        d'un chapitre donné, car il valide l'existence du chapitre et utilise
        le système de codes MathALÉA moderne (chapter_code).
    """
    from services.chapter_service import ChapterService
    
    # 1. Vérifier que le chapitre existe
    chapter_service = ChapterService(db)
    chapter = await chapter_service.get_chapter_by_code(chapter_code)
    
    if not chapter:
        raise HTTPException(
            status_code=404,
            detail=f"Chapter with code '{chapter_code}' not found"
        )
    
    # 2. Extraire le niveau du chapitre (FILTRE OBLIGATOIRE)
    chapter_niveau = chapter.get("niveau")
    if not chapter_niveau:
        # Fallback : extraire depuis le code (premiers caractères avant _)
        chapter_niveau = chapter_code.split('_')[0]
    
    # 3. Construire la requête avec FILTRE STRICT PAR NIVEAU + fallback chapitre_id
    query = {
        "$or": [
            {"chapter_code": chapter_code},  # Nouveau système
            {"chapitre_id": chapter_code},   # Fallback : Ancien système
            {"chapitre_id": chapter.get("legacy_code")}  # Fallback : Legacy code
        ],
        "niveau": chapter_niveau  # ⚠️ FILTRE OBLIGATOIRE pour cohérence
    }
    
    # Filtres additionnels optionnels
    if domaine:
        query["domaine"] = domaine
    if generator_kind:
        query["generator_kind"] = generator_kind
    
    logger.info(f"🔍 Recherche exercices: chapter_code={chapter_code}, niveau={chapter_niveau}, filtres={query}")
    
    # 4. Récupérer les exercices
    cursor = exercise_types_collection.find(query, {"_id": 0}).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    total = await exercise_types_collection.count_documents(query)
    
    logger.info(f"✅ {total} exercices trouvés pour {chapter_code} (niveau {chapter_niveau})")
    
    # 5. Retourner la réponse
    return ExerciseTypeListResponse(
        total=total,
        items=[ExerciseType(**item) for item in items]
    )


@router.get("/exercise-types/{exercise_type_id}", response_model=ExerciseType)
async def get_exercise_type(exercise_type_id: str):
    """Récupérer un type d'exercice par ID"""
    exercise_type = await exercise_types_collection.find_one({"id": exercise_type_id}, {"_id": 0})
    if not exercise_type:
        raise HTTPException(status_code=404, detail="ExerciseType not found")
    return ExerciseType(**exercise_type)


@router.patch("/exercise-types/{exercise_type_id}", response_model=ExerciseType)
async def update_exercise_type(exercise_type_id: str, update: ExerciseTypeUpdate):
    """Mettre à jour un type d'exercice"""
    update_data = {k: v for k, v in update.dict(exclude_unset=True).items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Mettre à jour le timestamp
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    result = await exercise_types_collection.update_one(
        {"id": exercise_type_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="ExerciseType not found")
    
    updated = await exercise_types_collection.find_one({"id": exercise_type_id}, {"_id": 0})
    return ExerciseType(**updated)


@router.delete("/exercise-types/{exercise_type_id}", status_code=204)
async def delete_exercise_type(exercise_type_id: str):
    """Supprimer un type d'exercice"""
    result = await exercise_types_collection.delete_one({"id": exercise_type_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="ExerciseType not found")


# ============================================================================
# ENDPOINTS: ExerciseSheet
# ============================================================================

@router.post("/sheets", response_model=ExerciseSheet, status_code=201)
async def create_exercise_sheet(sheet: ExerciseSheetCreate):
    """Créer une nouvelle feuille d'exercices"""
    sheet_dict = ExerciseSheet(**sheet.dict()).dict()
    await exercise_sheets_collection.insert_one(sheet_dict)
    return ExerciseSheet(**sheet_dict)


@router.get("/sheets", response_model=ExerciseSheetListResponse)
async def list_exercise_sheets(
    owner_id: Optional[str] = Query(None, description="Filtrer par propriétaire"),
    niveau: Optional[str] = Query(None, description="Filtrer par niveau"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Lister les feuilles d'exercices"""
    query = {}
    if owner_id:
        query["owner_id"] = owner_id
    if niveau:
        query["niveau"] = niveau
    
    cursor = exercise_sheets_collection.find(query, {"_id": 0}).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    total = await exercise_sheets_collection.count_documents(query)
    
    return ExerciseSheetListResponse(
        total=total,
        items=[ExerciseSheet(**item) for item in items]
    )


@router.get("/sheets/{sheet_id}", response_model=ExerciseSheet)
async def get_exercise_sheet(sheet_id: str):
    """Récupérer une feuille par ID"""
    sheet = await exercise_sheets_collection.find_one({"id": sheet_id}, {"_id": 0})
    if not sheet:
        raise HTTPException(status_code=404, detail="ExerciseSheet not found")
    return ExerciseSheet(**sheet)


@router.patch("/sheets/{sheet_id}", response_model=ExerciseSheet)
async def update_exercise_sheet(sheet_id: str, update: ExerciseSheetUpdate):
    """Mettre à jour une feuille"""
    update_data = {k: v for k, v in update.dict(exclude_unset=True).items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    result = await exercise_sheets_collection.update_one(
        {"id": sheet_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="ExerciseSheet not found")
    
    updated = await exercise_sheets_collection.find_one({"id": sheet_id}, {"_id": 0})
    return ExerciseSheet(**updated)


@router.delete("/sheets/{sheet_id}", status_code=204)
async def delete_exercise_sheet(sheet_id: str):
    """Supprimer une feuille"""
    # Supprimer aussi tous les items de la feuille
    await sheet_items_collection.delete_many({"sheet_id": sheet_id})
    
    result = await exercise_sheets_collection.delete_one({"id": sheet_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="ExerciseSheet not found")


# ============================================================================
# ENDPOINTS: SheetItem
# ============================================================================

@router.post("/sheet-items", response_model=SheetItem, status_code=201)
async def create_sheet_item(item: SheetItemCreate):
    """Ajouter un item à une feuille"""
    # Vérifier que la feuille existe
    sheet = await exercise_sheets_collection.find_one({"id": item.sheet_id})
    if not sheet:
        raise HTTPException(status_code=404, detail="ExerciseSheet not found")
    
    # Vérifier que le type d'exercice existe
    exercise_type_dict = await exercise_types_collection.find_one({"id": item.exercise_type_id}, {"_id": 0})
    if not exercise_type_dict:
        raise HTTPException(status_code=404, detail="ExerciseType not found")
    
    exercise_type = ExerciseType(**exercise_type_dict)
    
    # Valider la configuration
    config = item.config
    
    # Vérifier nb_questions dans les limites
    if config.nb_questions < exercise_type.min_questions:
        raise HTTPException(
            status_code=422,
            detail=f"nb_questions ({config.nb_questions}) must be >= min_questions ({exercise_type.min_questions})"
        )
    if config.nb_questions > exercise_type.max_questions:
        raise HTTPException(
            status_code=422,
            detail=f"nb_questions ({config.nb_questions}) must be <= max_questions ({exercise_type.max_questions})"
        )
    
    # Vérifier difficulty si spécifiée
    if config.difficulty and config.difficulty not in exercise_type.difficulty_levels:
        raise HTTPException(
            status_code=422,
            detail=f"difficulty '{config.difficulty}' not in available levels: {exercise_type.difficulty_levels}"
        )
    
    # Obtenir le prochain ordre
    max_order = await sheet_items_collection.find_one(
        {"sheet_id": item.sheet_id},
        sort=[("order", -1)]
    )
    next_order = (max_order.get("order", 0) + 1) if max_order else 1
    
    item_dict = SheetItem(**item.dict(), order=next_order).dict()
    await sheet_items_collection.insert_one(item_dict)
    return SheetItem(**item_dict)


@router.get("/sheet-items", response_model=SheetItemListResponse)
async def list_sheet_items(
    sheet_id: str = Query(..., description="ID de la feuille"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Lister les items d'une feuille"""
    query = {"sheet_id": sheet_id}
    
    cursor = sheet_items_collection.find(query, {"_id": 0}).sort("order", 1).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    total = await sheet_items_collection.count_documents(query)
    
    return SheetItemListResponse(
        total=total,
        items=[SheetItem(**item) for item in items]
    )


@router.get("/sheet-items/{item_id}", response_model=SheetItem)
async def get_sheet_item(item_id: str):
    """Récupérer un item par ID"""
    item = await sheet_items_collection.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="SheetItem not found")
    return SheetItem(**item)


@router.patch("/sheet-items/{item_id}", response_model=SheetItem)
async def update_sheet_item(item_id: str, update: SheetItemUpdate):
    """Mettre à jour un item"""
    update_data = {k: v for k, v in update.dict(exclude_unset=True).items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Si config est mis à jour, valider
    if "config" in update_data:
        # Récupérer l'item pour obtenir l'exercise_type_id
        item = await sheet_items_collection.find_one({"id": item_id}, {"_id": 0})
        if not item:
            raise HTTPException(status_code=404, detail="SheetItem not found")
        
        exercise_type_dict = await exercise_types_collection.find_one(
            {"id": item["exercise_type_id"]}, 
            {"_id": 0}
        )
        if not exercise_type_dict:
            raise HTTPException(status_code=404, detail="ExerciseType not found")
        
        exercise_type = ExerciseType(**exercise_type_dict)
        config = ExerciseItemConfig(**update_data["config"])
        
        # Valider nb_questions
        if config.nb_questions < exercise_type.min_questions:
            raise HTTPException(
                status_code=422,
                detail=f"nb_questions ({config.nb_questions}) must be >= min_questions ({exercise_type.min_questions})"
            )
        if config.nb_questions > exercise_type.max_questions:
            raise HTTPException(
                status_code=422,
                detail=f"nb_questions ({config.nb_questions}) must be <= max_questions ({exercise_type.max_questions})"
            )
        
        # Valider difficulty
        if config.difficulty and config.difficulty not in exercise_type.difficulty_levels:
            raise HTTPException(
                status_code=422,
                detail=f"difficulty '{config.difficulty}' not in available levels: {exercise_type.difficulty_levels}"
            )
    
    result = await sheet_items_collection.update_one(
        {"id": item_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="SheetItem not found")
    
    updated = await sheet_items_collection.find_one({"id": item_id}, {"_id": 0})
    return SheetItem(**updated)


@router.delete("/sheet-items/{item_id}", status_code=204)
async def delete_sheet_item(item_id: str):
    """Supprimer un item"""
    result = await sheet_items_collection.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="SheetItem not found")


# ============================================================================
# ENDPOINTS: SheetItem (via sheets/{sheet_id}/items)
# ============================================================================

@router.post("/sheets/{sheet_id}/items", response_model=SheetItem, status_code=201)
async def add_item_to_sheet(sheet_id: str, item_data: Dict[str, Any]):
    """
    Ajouter un item à une feuille
    
    Body attendu:
    {
        "exercise_type_id": "...",
        "config": {
            "nb_questions": 5,
            "difficulty": "moyen",
            "seed": 12345,
            "options": {},
            "ai_enonce": false,
            "ai_correction": false
        },
        "order": 1  // optionnel
    }
    """
    # Vérifier que la feuille existe
    sheet = await exercise_sheets_collection.find_one({"id": sheet_id})
    if not sheet:
        raise HTTPException(status_code=404, detail="ExerciseSheet not found")
    
    # Extraire et valider les données
    exercise_type_id = item_data.get("exercise_type_id")
    if not exercise_type_id:
        raise HTTPException(status_code=400, detail="exercise_type_id is required")
    
    config_data = item_data.get("config")
    if not config_data:
        raise HTTPException(status_code=400, detail="config is required")
    
    # Vérifier que le type d'exercice existe
    exercise_type_dict = await exercise_types_collection.find_one({"id": exercise_type_id}, {"_id": 0})
    if not exercise_type_dict:
        raise HTTPException(status_code=404, detail="ExerciseType not found")
    
    exercise_type = ExerciseType(**exercise_type_dict)
    
    # Valider la configuration
    try:
        config = ExerciseItemConfig(**config_data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid config: {str(e)}")
    
    # Vérifier nb_questions dans les limites
    if config.nb_questions < exercise_type.min_questions:
        raise HTTPException(
            status_code=422,
            detail=f"nb_questions ({config.nb_questions}) must be >= min_questions ({exercise_type.min_questions})"
        )
    if config.nb_questions > exercise_type.max_questions:
        raise HTTPException(
            status_code=422,
            detail=f"nb_questions ({config.nb_questions}) must be <= max_questions ({exercise_type.max_questions})"
        )
    
    # Vérifier difficulty si spécifiée
    if config.difficulty and config.difficulty not in exercise_type.difficulty_levels:
        raise HTTPException(
            status_code=422,
            detail=f"difficulty '{config.difficulty}' not in available levels: {exercise_type.difficulty_levels}"
        )
    
    # Obtenir l'ordre (fourni ou automatique)
    order = item_data.get("order")
    if order is None:
        max_order = await sheet_items_collection.find_one(
            {"sheet_id": sheet_id},
            sort=[("order", -1)]
        )
        order = (max_order.get("order", 0) + 1) if max_order else 1
    
    # Créer l'item
    item = SheetItem(
        sheet_id=sheet_id,
        exercise_type_id=exercise_type_id,
        config=config,
        order=order
    )
    
    item_dict = item.dict()
    await sheet_items_collection.insert_one(item_dict)
    return SheetItem(**item_dict)


@router.get("/sheets/{sheet_id}/items", response_model=SheetItemListResponse)
async def get_sheet_items(
    sheet_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Récupérer tous les items d'une feuille (triés par order)"""
    # Vérifier que la feuille existe
    sheet = await exercise_sheets_collection.find_one({"id": sheet_id})
    if not sheet:
        raise HTTPException(status_code=404, detail="ExerciseSheet not found")
    
    query = {"sheet_id": sheet_id}
    cursor = sheet_items_collection.find(query, {"_id": 0}).sort("order", 1).skip(skip).limit(limit)
    items = await cursor.to_list(length=limit)
    total = await sheet_items_collection.count_documents(query)
    
    return SheetItemListResponse(
        total=total,
        items=[SheetItem(**item) for item in items]
    )


@router.patch("/sheets/{sheet_id}/items/{item_id}", response_model=SheetItem)
async def update_sheet_item_in_sheet(sheet_id: str, item_id: str, update_data: Dict[str, Any]):
    """
    Mettre à jour un item d'une feuille
    
    Body attendu:
    {
        "config": { ... },  // optionnel
        "order": 2          // optionnel
    }
    """
    # Vérifier que l'item existe et appartient à la feuille
    item = await sheet_items_collection.find_one({"id": item_id, "sheet_id": sheet_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="SheetItem not found in this sheet")
    
    update_fields = {}
    
    # Si config est mis à jour
    if "config" in update_data:
        exercise_type_dict = await exercise_types_collection.find_one(
            {"id": item["exercise_type_id"]}, 
            {"_id": 0}
        )
        if not exercise_type_dict:
            raise HTTPException(status_code=404, detail="ExerciseType not found")
        
        exercise_type = ExerciseType(**exercise_type_dict)
        
        try:
            config = ExerciseItemConfig(**update_data["config"])
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Invalid config: {str(e)}")
        
        # Valider nb_questions
        if config.nb_questions < exercise_type.min_questions:
            raise HTTPException(
                status_code=422,
                detail=f"nb_questions ({config.nb_questions}) must be >= min_questions ({exercise_type.min_questions})"
            )
        if config.nb_questions > exercise_type.max_questions:
            raise HTTPException(
                status_code=422,
                detail=f"nb_questions ({config.nb_questions}) must be <= max_questions ({exercise_type.max_questions})"
            )
        
        # Valider difficulty
        if config.difficulty and config.difficulty not in exercise_type.difficulty_levels:
            raise HTTPException(
                status_code=422,
                detail=f"difficulty '{config.difficulty}' not in available levels: {exercise_type.difficulty_levels}"
            )
        
        update_fields["config"] = config.dict()
    
    # Si order est mis à jour
    if "order" in update_data:
        update_fields["order"] = update_data["order"]
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await sheet_items_collection.update_one(
        {"id": item_id},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="SheetItem not found")
    
    updated = await sheet_items_collection.find_one({"id": item_id}, {"_id": 0})
    return SheetItem(**updated)


@router.delete("/sheets/{sheet_id}/items/{item_id}", status_code=204)
async def delete_item_from_sheet(sheet_id: str, item_id: str):
    """Supprimer un item d'une feuille"""
    result = await sheet_items_collection.delete_one({"id": item_id, "sheet_id": sheet_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="SheetItem not found in this sheet")


# ============================================================================
# ENDPOINT: Preview de Feuille d'Exercices
# ============================================================================

@router.post("/sheets/{sheet_id}/preview")
async def preview_exercise_sheet(sheet_id: str):
    """
    Générer un aperçu JSON complet d'une feuille d'exercices
    
    Pour chaque SheetItem:
    - Récupère l'ExerciseType associé
    - Appelle generate_exercise() avec les paramètres du config
    - Retourne le JSON structuré avec tous les exercices générés
    
    Note: Aucune IA n'est appelée ici (ai_enonce/ai_correction ignorés)
    """
    from backend.services.exercise_template_service import exercise_template_service
    
    # 1. Récupérer la feuille
    sheet = await exercise_sheets_collection.find_one({"id": sheet_id}, {"_id": 0})
    if not sheet:
        raise HTTPException(status_code=404, detail="ExerciseSheet not found")
    
    # 2. Récupérer tous les items, triés par order
    cursor = sheet_items_collection.find({"sheet_id": sheet_id}, {"_id": 0}).sort("order", 1)
    items = await cursor.to_list(length=1000)
    
    # 3. Générer les exercices pour chaque item
    preview_items = []
    
    for item_dict in items:
        try:
            item = SheetItem(**item_dict)
            
            # Récupérer l'ExerciseType
            exercise_type_dict = await exercise_types_collection.find_one(
                {"id": item.exercise_type_id},
                {"_id": 0}
            )
            
            if not exercise_type_dict:
                # Si l'ExerciseType n'existe plus
                raise HTTPException(
                    status_code=404,
                    detail=f"ExerciseType {item.exercise_type_id} not found for item {item.id}"
                )
            
            exercise_type = ExerciseType(**exercise_type_dict)
            
            # Appeler le générateur (en interne, pas via HTTP)
            generated = await exercise_template_service.generate_exercise(
                exercise_type_id=item.exercise_type_id,
                nb_questions=item.config.nb_questions,
                seed=item.config.seed,
                difficulty=item.config.difficulty,
                options=item.config.options,
                use_ai_enonce=False,  # Pas d'IA dans le preview
                use_ai_correction=False
            )
            
            # Construire l'item de preview
            preview_item = {
                "item_id": item.id,
                "exercise_type_id": item.exercise_type_id,
                "exercise_type_summary": {
                    "code_ref": exercise_type.code_ref,
                    "titre": exercise_type.titre,
                    "niveau": exercise_type.niveau,
                    "domaine": exercise_type.domaine
                },
                "config": item.config.dict(),
                "generated": generated
            }
            
            preview_items.append(preview_item)
            
        except ValueError as e:
            # Erreur de validation (nb_questions hors limites, etc.)
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            # Erreur inattendue
            raise HTTPException(
                status_code=500,
                detail=f"Error generating exercise for item {item.id}: {str(e)}"
            )
    
    # 4. Construire la réponse finale
    response = {
        "sheet_id": sheet_id,
        "titre": sheet["titre"],
        "niveau": sheet["niveau"],
        "description": sheet.get("description"),
        "items": preview_items
    }
    
    return response


# ============================================================================
# ENDPOINT: Génération d'Exercices (TEMPLATE)
# ============================================================================

from pydantic import BaseModel, Field
from backend.services.exercise_template_service import exercise_template_service
import base64


class GenerateExerciseRequest(BaseModel):
    """Requête pour générer un exercice"""
    exercise_type_id: str = Field(..., description="ID du type d'exercice")
    nb_questions: int = Field(..., ge=1, le=50, description="Nombre de questions")
    seed: int = Field(..., description="Graine pour reproductibilité")
    difficulty: Optional[str] = Field(None, description="Niveau de difficulté")
    options: Dict[str, Any] = Field(default_factory=dict, description="Options supplémentaires")
    use_ai_enonce: bool = Field(False, description="Utiliser l'IA pour l'énoncé")
    use_ai_correction: bool = Field(False, description="Utiliser l'IA pour la correction")


@router.post("/generate-exercise")
async def generate_exercise_endpoint(request: GenerateExerciseRequest):
    """
    Générer un exercice complet à partir d'un ExerciseType
    
    Système déterministe : même seed = même exercice
    """
    try:
        result = await exercise_template_service.generate_exercise(
            exercise_type_id=request.exercise_type_id,
            nb_questions=request.nb_questions,
            seed=request.seed,
            difficulty=request.difficulty,
            options=request.options,
            use_ai_enonce=request.use_ai_enonce,
            use_ai_correction=request.use_ai_correction
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating exercise: {str(e)}")


# ============================================================================
# ENDPOINT: Génération PDF pour Fiches
# ============================================================================

@router.post("/sheets/{sheet_id}/generate-pdf")
async def generate_sheet_pdf(
    sheet_id: str,
    request: Request,
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token")
):
    """
    Générer les 3 PDFs pour une feuille d'exercices
    
    Sprint D & E - Pipeline PDF complet avec IA optionnelle:
    1. Récupère la feuille et génère le preview
    2. Si IA activée: enrichit les énoncés/corrections
    3. Génère 3 PDFs: sujet, élève, corrigé
    4. Retourne les PDFs en base64
    
    PR7.1: Export PDF nécessite un compte (Free ou Pro)
    
    Returns:
        Dict avec 3 clés contenant les PDFs en base64:
        - subject_pdf: PDF sujet (pour professeur)
        - student_pdf: PDF élève (pour distribution)
        - correction_pdf: PDF corrigé (avec solutions)
    """
    # PR7.1: Vérifier l'authentification
    from backend.services.access_control import assert_can_export_pdf
    from backend.server import validate_session_token
    
    user_email = None
    if x_session_token:
        user_email = await validate_session_token(x_session_token)
    assert_can_export_pdf(user_email)
    
    from engine.pdf_engine.mathalea_sheet_pdf_builder import (
        build_sheet_subject_pdf,
        build_sheet_student_pdf,
        build_sheet_correction_pdf
    )
    from engine.pdf_engine.sheet_ai_enrichment_helper import (
        apply_ai_enrichment_to_sheet_preview,
        check_if_ai_needed
    )
    
    try:
        # 1. Vérifier que la feuille existe
        sheet = await exercise_sheets_collection.find_one({"id": sheet_id}, {"_id": 0})
        if not sheet:
            raise HTTPException(status_code=404, detail="ExerciseSheet not found")
        
        # 2. Générer le preview (réutilise la logique du endpoint /preview)
        cursor = sheet_items_collection.find({"sheet_id": sheet_id}, {"_id": 0}).sort("order", 1)
        items = await cursor.to_list(length=1000)
        
        preview_items = []
        for item_dict in items:
            try:
                item = SheetItem(**item_dict)
                
                # Récupérer l'ExerciseType
                exercise_type_dict = await exercise_types_collection.find_one(
                    {"id": item.exercise_type_id},
                    {"_id": 0}
                )
                
                if not exercise_type_dict:
                    raise HTTPException(
                        status_code=404,
                        detail=f"ExerciseType {item.exercise_type_id} not found"
                    )
                
                exercise_type = ExerciseType(**exercise_type_dict)
                
                # Générer l'exercice
                generated = await exercise_template_service.generate_exercise(
                    exercise_type_id=item.exercise_type_id,
                    nb_questions=item.config.nb_questions,
                    seed=item.config.seed,
                    difficulty=item.config.difficulty,
                    options=item.config.options,
                    use_ai_enonce=False,
                    use_ai_correction=False
                )
                
                preview_item = {
                    "item_id": item.id,
                    "exercise_type_id": item.exercise_type_id,
                    "exercise_type_summary": {
                        "code_ref": exercise_type.code_ref,
                        "titre": exercise_type.titre,
                        "niveau": exercise_type.niveau,
                        "domaine": exercise_type.domaine
                    },
                    "config": item.config.dict(),
                    "generated": generated
                }
                
                preview_items.append(preview_item)
                
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        preview = {
            "sheet_id": sheet_id,
            "titre": sheet["titre"],
            "niveau": sheet["niveau"],
            "description": sheet.get("description"),
            "items": preview_items
        }
        
        # 3. Enrichissement IA optionnel (Sprint E)
        # Vérifier si au moins un item a l'IA activée
        if check_if_ai_needed(preview):
            logger.info(f"🎨 IA activée pour la feuille {sheet_id}, enrichissement en cours...")
            preview = await apply_ai_enrichment_to_sheet_preview(preview)
            logger.info(f"✅ IA: Enrichissement terminé")
        else:
            logger.info(f"⏭️  IA désactivée pour la feuille {sheet_id}, génération directe")
        
        # 4. Générer les 3 PDFs
        subject_pdf_bytes = build_sheet_subject_pdf(preview)
        student_pdf_bytes = build_sheet_student_pdf(preview)
        correction_pdf_bytes = build_sheet_correction_pdf(preview)
        
        # 5. Encoder en base64
        response = {
            "subject_pdf": base64.b64encode(subject_pdf_bytes).decode('utf-8'),
            "student_pdf": base64.b64encode(student_pdf_bytes).decode('utf-8'),
            "correction_pdf": base64.b64encode(correction_pdf_bytes).decode('utf-8'),
            "metadata": {
                "sheet_id": sheet_id,
                "titre": sheet["titre"],
                "niveau": sheet["niveau"],
                "nb_exercises": len(preview_items),
                "ai_enrichment_applied": check_if_ai_needed(preview),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDFs: {str(e)}"
        )



@router.post("/sheets/{sheet_id}/export-standard")
async def export_standard_pdf(
    sheet_id: str,
    request: Request,
    layout: str = "eco",  # Query param: "eco" ou "classic"
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token")
):
    """
    Export Standard - Génère 2 PDFs simplifiés (Élève + Corrigé)

    P0 BUSINESS: Export PDF nécessite un compte (Free ou Pro)

    SPRINT FUSION PDF - Export standard simplifié:
    1. Génère le preview de la feuille
    2. Crée 2 PDFs uniquement:
       - student_pdf: Énoncé + zones de réponse (pour distribution aux élèves)
       - correction_pdf: Énoncé + corrections détaillées
    3. Pas de logo, pas de personnalisation, design simple et clair

    Guards:
    - X-Session-Token REQUIS (plus de guest - P0 FIX)
    - Free users: quota 10 exports / jour
    - Pro users: pas de quota

    Returns:
        Dict avec 2 clés contenant les PDFs en base64:
        {
            "student_pdf": "<base64>",
            "correction_pdf": "<base64>",
            "filename_base": "LeMaitreMot_<NomFiche>"
        }

    # TEST INSTRUCTIONS (curl):
    # 401 sans session:
    #   curl -X POST http://localhost:8000/api/mathalea/sheets/SHEET_ID/export-standard
    # 200 avec session:
    #   curl -X POST -H "X-Session-Token: TOKEN" http://localhost:8000/api/mathalea/sheets/SHEET_ID/export-standard
    # 429 après 10 exports/jour (free):
    #   Répéter 11 fois l'export avec un compte free
    """
    from engine.pdf_engine.mathalea_sheet_pdf_builder import (
        build_sheet_student_pdf,
        build_sheet_correction_pdf
    )
    from backend.server import validate_session_token, check_user_pro_status

    # Utiliser app.state.db si disponible (pour les tests), sinon db global
    db_to_use = getattr(request.app.state, 'db', db)
    exercise_sheets_collection_local = db_to_use[EXERCISE_SHEETS_COLLECTION]
    sheet_items_collection_local = db_to_use[SHEET_ITEMS_COLLECTION]
    exercise_types_collection_local = db_to_use[EXERCISE_TYPES_COLLECTION]

    # ========================================================================
    # PR7.1: AUTHENTIFICATION REQUISE - Plus de guest exports
    # ========================================================================
    from backend.services.access_control import assert_can_export_pdf
    
    user_email = None
    if x_session_token:
        user_email = await validate_session_token(x_session_token)
    
    # PR7.1: Valider qu'un compte est requis pour exporter (retourne 401 avec code AUTH_REQUIRED_EXPORT)
    assert_can_export_pdf(user_email)

    # Vérifier le statut Pro
    is_pro_user, pro_user_doc = await check_user_pro_status(user_email)
    user_type = "pro" if is_pro_user else "free"
    
    # PR8: Vérifier que l'utilisateur peut utiliser le layout demandé (eco = Premium uniquement)
    from backend.services.access_control import assert_can_use_layout
    assert_can_use_layout(user_email, is_pro_user, layout)

    # ========================================================================
    # P0: QUOTAS - 10 exports/jour pour Free, illimité pour Pro
    # ========================================================================
    exports_today = 0
    max_exports_per_day = 10

    if not is_pro_user:
        # Vérifier le quota journalier pour les utilisateurs Free
        today = datetime.now(timezone.utc).date()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

        # Compter les exports du jour pour cet utilisateur
        exports_today = await db_to_use.user_exports.count_documents({
            "user_email": user_email,
            "created_at": {"$gte": today_start}
        })

        if exports_today >= max_exports_per_day:
            logger.warning(
                f"[EXPORT_QUOTA] user_type=free user_email={user_email} sheet_id={sheet_id} "
                f"exports_today={exports_today} max={max_exports_per_day} - QUOTA_EXCEEDED"
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "daily_quota_exceeded",
                    "action": "upgrade_to_pro",
                    "message": f"Limite de {max_exports_per_day} exports/jour atteinte. Passez à Pro pour des exports illimités.",
                    "exports_today": exports_today,
                    "exports_remaining": 0,
                    "max_exports_per_day": max_exports_per_day,
                    "resets_at": (today_start + timedelta(days=1)).isoformat()
                }
            )

        logger.info(
            f"[EXPORT_QUOTA] user_type=free user_email={user_email} sheet_id={sheet_id} "
            f"exports_today={exports_today} exports_remaining={max_exports_per_day - exports_today} - QUOTA_OK"
        )
    else:
        logger.info(
            f"[EXPORT_QUOTA] user_type=pro user_email={user_email} sheet_id={sheet_id} - pas de quota"
        )
    
    try:
        # 1. Vérifier que la feuille existe
        sheet = await exercise_sheets_collection_local.find_one({"id": sheet_id}, {"_id": 0})
        if not sheet:
            raise HTTPException(status_code=404, detail="ExerciseSheet not found")

        # 2. Récupérer les items
        cursor = sheet_items_collection_local.find({"sheet_id": sheet_id}, {"_id": 0}).sort("order", 1)
        items = await cursor.to_list(length=1000)

        if not items:
            raise HTTPException(
                status_code=400,
                detail="Cannot generate PDF for empty sheet"
            )

        # ====================================================================
        # P0: CACHE CHECK - Vérifier si les PDFs sont déjà en cache
        # ====================================================================
        # Récupérer le layout effectif (forcé à eco pour free users)
        effective_layout = layout
        if not is_pro_user and layout == "classic":
            effective_layout = "eco"

        # Calculer la clé de cache
        cache_key = compute_pdf_cache_key(sheet_id, effective_layout, items)

        # Vérifier le cache
        cached_pdf = await get_cached_pdf(db_to_use, cache_key)
        if cached_pdf:
            # Cache HIT - Retourner les PDFs du cache
            logger.info(f"[PDF_CACHE] Returning cached PDF for sheet_id={sheet_id}")

            # Quand même enregistrer l'export pour les quotas (Free users)
            if not is_pro_user:
                try:
                    export_doc = {
                        "user_email": user_email,
                        "sheet_id": sheet_id,
                        "type": "sheet_export",
                        "layout": effective_layout,
                        "from_cache": True,
                        "created_at": datetime.now(timezone.utc)
                    }
                    await db_to_use.user_exports.insert_one(export_doc)
                except Exception as e:
                    logger.error(f"[EXPORT_QUOTA] Erreur enregistrement export (cache): {e}")

            return {
                "student_pdf": cached_pdf["student_pdf"],
                "correction_pdf": cached_pdf["correction_pdf"],
                "filename_base": f"LeMaitreMot_{sheet['titre'].replace(' ', '_')}",
                "metadata": {
                    "sheet_id": sheet_id,
                    "titre": sheet["titre"],
                    "niveau": sheet["niveau"],
                    "nb_exercises": len(items),
                    "generated_at": cached_pdf.get("created_at", datetime.now(timezone.utc)).isoformat(),
                    "from_cache": True,
                    "user_type": user_type,
                    "user_email": user_email,
                    "exports_today": exports_today + 1 if not is_pro_user else None,
                    "exports_remaining": max_exports_per_day - exports_today - 1 if not is_pro_user else None
                }
            }

        # Cache MISS - Continuer avec la génération
        logger.info(f"[PDF_CACHE] MISS cache_key={cache_key[:16]}... - generating PDF")

        # 3. Générer le preview
        preview_items = []
        for item_dict in items:
            try:
                item = SheetItem(**item_dict)
                
                # Récupérer l'ExerciseType
                exercise_type_dict = await exercise_types_collection_local.find_one(
                    {"id": item.exercise_type_id},
                    {"_id": 0}
                )
                
                if not exercise_type_dict:
                    logger.warning(f"⚠️ ExerciseType {item.exercise_type_id} not found")
                    continue
                
                exercise_type = ExerciseType(**exercise_type_dict)
                
                # Générer l'exercice
                generated = await exercise_template_service.generate_exercise(
                    exercise_type_id=item.exercise_type_id,
                    nb_questions=item.config.nb_questions,
                    seed=item.config.seed,
                    difficulty=item.config.difficulty,
                    options=item.config.options,
                    use_ai_enonce=False,
                    use_ai_correction=False
                )
                
                preview_item = {
                    "item_id": item.id,
                    "exercise_type_id": item.exercise_type_id,
                    "exercise_type_summary": {
                        "code_ref": exercise_type.code_ref,
                        "titre": exercise_type.titre,
                        "niveau": exercise_type.niveau,
                        "domaine": exercise_type.domaine
                    },
                    "config": item.config.dict(),
                    "generated": generated
                }
                
                preview_items.append(preview_item)
                
            except Exception as e:
                logger.error(f"❌ Error generating exercise: {e}")
                continue
        
        preview = {
            "sheet_id": sheet_id,
            "titre": sheet["titre"],
            "niveau": sheet["niveau"],
            "description": sheet.get("description"),
            "items": preview_items
        }
        
        # 3. Récupérer le layout (query param ou default "eco" pour gratuit)
        layout = request.query_params.get("layout", "eco")
        if layout not in ["eco", "classic"]:
            layout = "eco"  # Fallback si valeur invalide
        
        # Si utilisateur Pro, peut choisir classic, sinon default eco
        # Note: effective_layout already computed above (eco forced for free users)

        # 4. Générer les 2 PDFs uniquement
        logger.info(f"📄 Génération export standard pour la feuille {sheet_id} (layout={effective_layout})")
        student_pdf_bytes = build_sheet_student_pdf(preview, layout=effective_layout)
        correction_pdf_bytes = build_sheet_correction_pdf(preview, layout=effective_layout)

        # 5. Encoder en base64
        student_pdf_b64 = base64.b64encode(student_pdf_bytes).decode('utf-8')
        correction_pdf_b64 = base64.b64encode(correction_pdf_bytes).decode('utf-8')

        # 6. Stocker dans le cache
        cache_metadata = {
            "sheet_id": sheet_id,
            "titre": sheet["titre"],
            "niveau": sheet["niveau"],
            "nb_exercises": len(preview_items),
            "layout": effective_layout
        }
        await store_pdf_in_cache(
            db_to_use,
            cache_key,
            student_pdf_b64,
            correction_pdf_b64,
            cache_metadata
        )

        # 7. Créer le nom de fichier base
        filename_base = f"LeMaitreMot_{sheet['titre'].replace(' ', '_')}"

        # 8. P0: Enregistrer l'export dans user_exports (pour quotas Free)
        if not is_pro_user:
            try:
                export_doc = {
                    "user_email": user_email,
                    "sheet_id": sheet_id,
                    "type": "sheet_export",
                    "layout": effective_layout,
                    "from_cache": False,
                    "created_at": datetime.now(timezone.utc)
                }
                await db_to_use.user_exports.insert_one(export_doc)
                logger.info(
                    f"[EXPORT_QUOTA] user_type=free user_email={user_email} sheet_id={sheet_id} "
                    f"- export enregistré ({exports_today + 1}/{max_exports_per_day})"
                )
            except Exception as e:
                logger.error(f"[EXPORT_QUOTA] Erreur enregistrement export: {e}")
                # Ne pas bloquer l'export si l'enregistrement échoue

        # 9. Retourner la réponse
        response = {
            "student_pdf": student_pdf_b64,
            "correction_pdf": correction_pdf_b64,
            "filename_base": filename_base,
            "metadata": {
                "sheet_id": sheet_id,
                "titre": sheet["titre"],
                "niveau": sheet["niveau"],
                "nb_exercises": len(preview_items),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "from_cache": False,
                "user_type": user_type,
                "user_email": user_email,
                "exports_today": exports_today + 1 if not is_pro_user else None,
                "exports_remaining": max_exports_per_day - exports_today - 1 if not is_pro_user else None
            }
        }

        logger.info(f"✅ Export standard généré: 2 PDFs pour la feuille {sheet_id} (user_type={user_type})")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating standard PDF export: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating standard PDF export: {str(e)}"
        )


@router.post("/sheets/{sheet_id}/generate-pdf-pro")
async def generate_pro_pdf(
    sheet_id: str,
    request: ProPdfRequest,
    x_session_token: str = Header(None, alias="X-Session-Token")
):
    """
    Génère un PDF Pro personnalisé pour une fiche d'exercices
    
    ROUTE PRO UNIQUEMENT
    - Vérifie que l'utilisateur est Pro
    - Utilise le template Pro et le logo de l'établissement
    - Retourne 1 PDF personnalisé (énoncés + corrections)
    
    Args:
        sheet_id: ID de la fiche
        request: ProPdfRequest contenant le template ("classique" ou "academique")
        x_session_token: Token de session Pro (requis)
    
    Returns:
        JSON avec le PDF en base64:
        {
            "pro_pdf": "base64...",
            "filename": "LeMaitreMot_Pro_NomFiche.pdf"
        }
    
    Raises:
        403: Si l'utilisateur n'est pas Pro
        404: Si la fiche n'existe pas
        500: En cas d'erreur de génération
    """
    template = request.template
    logger.info(f"📝 Demande de génération PDF Pro pour la fiche {sheet_id} (template: {template})")
    
    # VÉRIFICATION PRO - Validation stricte du token et statut Pro
    if not x_session_token:
        logger.warning("⚠️ Tentative d'accès PDF Pro sans token de session")
        raise HTTPException(
            status_code=401,
            detail={"error": "AUTHENTICATION_REQUIRED", "message": "Token de session requis"}
        )
    
    # Valider le token de session et récupérer l'email
    from backend.server import validate_session_token, check_user_pro_status
    
    user_email = await validate_session_token(x_session_token)
    if not user_email:
        logger.warning(f"⚠️ Token de session invalide ou expiré: {x_session_token[:20]}...")
        raise HTTPException(
            status_code=401,
            detail={"error": "INVALID_SESSION_TOKEN", "message": "Token de session invalide ou expiré"}
        )
    
    # Vérifier que l'utilisateur est Pro actif
    is_pro, user = await check_user_pro_status(user_email)
    if not is_pro:
        logger.warning(f"⚠️ Utilisateur {user_email} n'est pas Pro ou abonnement expiré")
        raise HTTPException(
            status_code=403,
            detail={"error": "PRO_REQUIRED", "message": "Un compte Pro actif est nécessaire pour cette fonctionnalité"}
        )
    
    logger.info(f"✅ Utilisateur Pro authentifié: {user_email}")
    
    try:
        # 1. Récupérer la fiche
        sheet = await exercise_sheets_collection.find_one({"id": sheet_id}, {"_id": 0})
        if not sheet:
            logger.error(f"❌ Fiche {sheet_id} introuvable")
            raise HTTPException(status_code=404, detail=f"Sheet {sheet_id} not found")
        
        # 2. Récupérer les items de la fiche
        items = await sheet_items_collection.find({"sheet_id": sheet_id}, {"_id": 0}).to_list(1000)
        
        if not items:
            logger.warning(f"⚠️ Fiche {sheet_id} sans exercices")
            raise HTTPException(
                status_code=400,
                detail="Cannot generate PDF for empty sheet"
            )
        
        # 3. Générer le preview JSON (nécessaire pour l'adapter)
        preview_items = []
        for item in items:
            # Générer les exercices
            exercise_type_id = item.get("exercise_type_id")
            exercise_type = await exercise_types_collection.find_one(
                {"id": exercise_type_id},
                {"_id": 0}
            )
            
            if not exercise_type:
                logger.warning(f"⚠️ ExerciseType {exercise_type_id} not found")
                continue
            
            config = item.get("config", {})
            nb_questions = config.get("nb_questions", 5)
            seed = config.get("seed", 0)
            difficulty = config.get("difficulty", "moyen")
            
            # Générer l'exercice
            generated_exercise = await exercise_template_service.generate_exercise(
                exercise_type_id=exercise_type_id,
                nb_questions=nb_questions,
                seed=seed,
                difficulty=difficulty
            )
            
            preview_item = {
                "item_id": item.get("id"),
                "exercise_type_id": exercise_type_id,
                "exercise_type_summary": {
                    "code_ref": exercise_type.get("code_ref"),
                    "titre": exercise_type.get("titre"),
                    "niveau": exercise_type.get("niveau"),
                    "domaine": exercise_type.get("domaine"),
                    "generator_kind": exercise_type.get("generator_kind")
                },
                "config": config,
                "generated": generated_exercise
            }
            
            preview_items.append(preview_item)
        
        preview_json = {
            "sheet_id": sheet_id,
            "titre": sheet.get("titre", "Fiche d'exercices"),
            "niveau": sheet.get("niveau", ""),
            "description": sheet.get("description", ""),
            "items": preview_items
        }
        
        # 4. Récupérer la configuration Pro de l'utilisateur depuis MongoDB
        # user_email est déjà validé et récupéré depuis la session DB ci-dessus
        from services.pro_config_service import get_pro_config_for_user
        
        logger.info(f"🔑 Export Pro pour user_email: {user_email}")
        
        # Récupérer la vraie config Pro depuis MongoDB
        pro_config = await get_pro_config_for_user(user_email)
        
        logger.info(f"📋 Config Pro récupérée: professor={pro_config.get('professor_name')}, school={pro_config.get('school_name')}")
        
        # Construire le chemin absolu du logo pour WeasyPrint
        logo_url = pro_config.get("logo_url")
        if logo_url and not logo_url.startswith('http'):
            # Convertir le chemin relatif en chemin absolu pour WeasyPrint
            logo_path = Path("/app/backend") / logo_url.lstrip('/')
            # Vérifier que le fichier existe ET est un fichier (pas un répertoire)
            if logo_path.exists() and logo_path.is_file():
                logo_url = f"file://{logo_path}"
            else:
                logger.warning(f"⚠️ Logo introuvable ou invalide: {logo_path}")
                logo_url = None
        
        template_config = {
            "professor_name": pro_config.get("professor_name", ""),
            "school_name": pro_config.get("school_name", "Le Maître Mot"),
            "school_year": pro_config.get("school_year", "2024-2025"),
            "footer_text": pro_config.get("footer_text", "Document généré par Le Maître Mot"),
            "logo_url": logo_url
        }
        
        logger.info(f"✅ Template config préparée: {template_config}")
        
        # 5. Convertir le preview Builder vers le format Legacy attendu par les templates
        from engine.pdf_engine.builder_to_legacy_converter import convert_builder_to_legacy_pro_format
        
        # Extraire le type_doc de la requête
        type_doc = request.type_doc
        
        document_data = convert_builder_to_legacy_pro_format(
            preview_json=preview_json,
            template_config=template_config,
            type_doc=type_doc
        )
        
        # 6. Générer les 2 PDFs Pro (Sujet + Corrigé) via Jinja2
        from engine.pdf_engine.template_renderer import render_pro_sujet, render_pro_corrige
        import weasyprint
        import asyncio
        
        # Helper pour générer PDF avec timeout
        async def generate_pdf_with_timeout(html_content: str, pdf_name: str, timeout_seconds: int = 30) -> bytes:
            """Génère un PDF avec timeout pour éviter les blocages"""
            try:
                # Exécuter WeasyPrint dans un thread pool avec timeout
                loop = asyncio.get_event_loop()
                pdf_bytes = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: weasyprint.HTML(
                            string=html_content,
                            base_url=str(Path("/app/backend").resolve())
                        ).write_pdf()
                    ),
                    timeout=timeout_seconds
                )
                logger.info(f"✅ PDF {pdf_name} généré avec succès ({len(pdf_bytes)} bytes)")
                return pdf_bytes
            except asyncio.TimeoutError:
                logger.error(f"❌ Timeout lors de la génération du PDF {pdf_name} (> {timeout_seconds}s)")
                raise HTTPException(
                    status_code=504,
                    detail={
                        "error": "PDF_GENERATION_TIMEOUT",
                        "message": f"La génération du PDF {pdf_name} a pris trop de temps (> {timeout_seconds}s). Veuillez réessayer avec moins d'exercices."
                    }
                )
            except Exception as e:
                logger.error(f"❌ Erreur lors de la génération du PDF {pdf_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "PDF_GENERATION_ERROR",
                        "message": f"Erreur lors de la génération du PDF {pdf_name}: {str(e)}"
                    }
                )
        
        # Générer le Sujet Pro (énoncés + zones de réponse)
        html_sujet = render_pro_sujet(
            template_style=template,
            document_data=document_data,
            template_config=template_config
        )
        pro_subject_pdf_bytes = await generate_pdf_with_timeout(html_sujet, "sujet", timeout_seconds=30)
        
        # Générer le Corrigé Pro (énoncés + solutions)
        html_corrige = render_pro_corrige(
            template_style=template,
            document_data=document_data,
            template_config=template_config
        )
        pro_correction_pdf_bytes = await generate_pdf_with_timeout(html_corrige, "corrigé", timeout_seconds=30)
        
        # 7. Encoder les 2 PDFs en base64
        import base64
        pro_subject_pdf_b64 = base64.b64encode(pro_subject_pdf_bytes).decode('utf-8')
        pro_correction_pdf_b64 = base64.b64encode(pro_correction_pdf_bytes).decode('utf-8')
        
        # 8. Créer le nom de fichier base
        base_filename = f"LeMaitreMot_{sheet.get('titre', 'Fiche').replace(' ', '_')}_Pro"
        
        logger.info(f"✅ 2 PDFs Pro générés avec succès pour la fiche {sheet_id} (template: {template})")
        
        return {
            "pro_subject_pdf": pro_subject_pdf_b64,
            "pro_correction_pdf": pro_correction_pdf_b64,
            "base_filename": base_filename,
            "template": template,
            "etablissement": template_config.get("school_name"),
            "professeur": template_config.get("professor_name"),
            "school_year": template_config.get("school_year"),
            "footer_text": template_config.get("footer_text"),
            "logo_url": template_config.get("logo_url")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating Pro PDF: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating Pro PDF: {str(e)}"
        )



# ============================================================================
# ENDPOINTS: Pro User Config
# ============================================================================

@router.get("/pro/config")
async def get_pro_config(
    x_session_token: str = Header(None, alias="X-Session-Token")
):
    """
    Récupère la configuration Pro de l'utilisateur connecté
    
    Args:
        x_session_token: Token de session (requis)
    
    Returns:
        Configuration Pro de l'utilisateur
    
    Raises:
        403: Si pas de token
    """
    if not x_session_token:
        raise HTTPException(status_code=403, detail="Session token required")
    
    from services.pro_config_service import get_pro_config_for_user
    
    # Extraire l'email du token (ou utiliser le token comme identifiant)
    user_email = x_session_token if "@" in x_session_token else "user@lemaitremot.com"
    
    config = await get_pro_config_for_user(user_email)
    
    return {
        "user_email": user_email,
        **config
    }


@router.put("/pro/config")
async def update_pro_config_endpoint(
    updates: Dict[str, Any],
    x_session_token: str = Header(None, alias="X-Session-Token")
):
    """
    Met à jour la configuration Pro de l'utilisateur
    
    Args:
        updates: Dict avec les champs à mettre à jour
        x_session_token: Token de session (requis)
    
    Returns:
        Message de succès
    
    Raises:
        403: Si pas de token
    """
    if not x_session_token:
        raise HTTPException(status_code=403, detail="Session token required")
    
    from services.pro_config_service import update_pro_config
    
    user_email = x_session_token if "@" in x_session_token else "user@lemaitremot.com"
    
    # Filtrer les champs autorisés
    allowed_fields = ["professor_name", "school_name", "school_year", "footer_text", "logo_url", "template_choice"]
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    success = await update_pro_config(user_email, filtered_updates)
    
    if success:
        return {"message": "Configuration Pro mise à jour avec succès"}
    else:
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour")


@router.post("/pro/upload-logo")
async def upload_pro_logo(
    file: UploadFile = File(...),
    x_session_token: str = Header(None, alias="X-Session-Token")
):
    """
    Upload un logo pour la configuration Pro
    
    Args:
        file: Fichier image (PNG, JPG, JPEG)
        x_session_token: Token de session (requis)
    
    Returns:
        URL du logo uploadé
    
    Raises:
        403: Si pas de token
        400: Si le fichier n'est pas une image
    """
    if not x_session_token:
        raise HTTPException(status_code=403, detail="Session token required")
    
    # Vérifier le type de fichier
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image (PNG, JPG, JPEG)")
    
    # Vérifier la taille (max 2MB)
    file_content = await file.read()
    if len(file_content) > 2 * 1024 * 1024:  # 2MB
        raise HTTPException(status_code=400, detail="Le fichier ne doit pas dépasser 2 Mo")
    
    try:
        # Créer le dossier uploads/logos s'il n'existe pas
        upload_dir = Path("/app/backend/uploads/logos")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Générer un nom de fichier unique
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'png'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Sauvegarder le fichier
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Construire l'URL du logo
        logo_url = f"/uploads/logos/{unique_filename}"
        
        logger.info(f"✅ Logo uploadé: {logo_url}")
        
        return {
            "logo_url": logo_url,
            "filename": unique_filename,
            "message": "Logo uploadé avec succès"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur upload logo: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'upload du logo")


@router.get("/template/styles")
async def get_template_styles():
    """
    Retourne la liste des styles de templates disponibles
    
    Returns:
        Liste des styles avec leurs descriptions et couleurs
    """
    try:
        styles = {
            "classique": {
                "name": "Classique",
                "description": "Style traditionnel élégant avec mise en page moderne",
                "preview_colors": {
                    "primary": "#2563eb",
                    "accent": "#7c3aed"
                }
            },
            "academique": {
                "name": "Académique",
                "description": "Style professionnel et sobre pour documents officiels",
                "preview_colors": {
                    "primary": "#1e40af",
                    "accent": "#4b5563"
                }
            }
        }
        
        return {"styles": styles}
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des styles: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des styles")


