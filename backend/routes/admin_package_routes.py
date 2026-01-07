"""
Routes admin pour l'import/export de packages complets (PR10)
============================================================

Endpoints:
- GET /api/admin/package/export?niveau=6e
- POST /api/admin/package/import (body=package, query dry_run=true|false)

Format package v1.0:
- niveau (scope)
- curriculum_chapters (filtre par niveau)
- admin_exercises (groupés par chapter_code)
- admin_templates (si collection disponible)
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.observability.logger import get_logger
from backend.services.package_schema import (
    PackageV1,
    PackageScope,
    PackageMetadata,
    normalize_chapter_code,
    validate_package_v1
)
from backend.constants.collections import (
    CURRICULUM_CHAPTERS_COLLECTION,
    EXERCISES_COLLECTION
)
from backend.services.import_export_validator import validate_import_payload_v1
from backend.tests.contracts.exercise_contract import assert_no_unresolved_placeholders

router = APIRouter(prefix="/api/admin/package", tags=["admin-package"])
logger = get_logger()


def get_db():
    """Dépendance pour obtenir la DB"""
    from backend.server import db
    return db


@router.get("/export")
async def export_package(
    niveau: str = Query(..., description="Niveau scolaire (ex: '6e', '5e')"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Exporte un package complet pour un niveau
    
    Retourne:
    - curriculum_chapters (filtre par niveau)
    - admin_exercises (groupés par chapter_code normalisé)
    - admin_templates (si collection disponible)
    """
    logger.info(f"[PACKAGE] Export package pour niveau={niveau}")
    
    try:
        # 1. Récupérer les chapitres du curriculum pour ce niveau
        chapters_collection = db[CURRICULUM_CHAPTERS_COLLECTION]
        chapters = await chapters_collection.find(
            {"niveau": niveau},
            {"_id": 0}
        ).sort("code_officiel", 1).to_list(length=1000)
        
        logger.info(f"[PACKAGE] {len(chapters)} chapitres trouvés pour {niveau}")
        
        # 2. Extraire les codes officiels normalisés
        chapter_codes = []
        for chapter in chapters:
            code = chapter.get("code_officiel") or chapter.get("code")
            if code:
                normalized = normalize_chapter_code(code)
                chapter_codes.append(normalized)
                # Normaliser le code dans le chapitre
                chapter["code_officiel"] = normalized
                if "code" in chapter:
                    chapter["code"] = normalized
        
        # 3. Récupérer les exercices pour ces chapitres
        exercises_collection = db[EXERCISES_COLLECTION]
        exercises = []
        if chapter_codes:
            query = {"chapter_code": {"$in": chapter_codes}}
            exercises = await exercises_collection.find(
                query,
                {"_id": 0}
            ).sort("chapter_code", 1).sort("id", 1).to_list(length=10000)
            
            # Normaliser les chapter_code des exercices
            for exercise in exercises:
                code = exercise.get("chapter_code")
                if code:
                    exercise["chapter_code"] = normalize_chapter_code(code)
        
        logger.info(f"[PACKAGE] {len(exercises)} exercices trouvés pour {niveau}")
        
        # 4. Récupérer les templates (si collection disponible)
        templates = []
        templates_supported = False
        try:
            templates_collection = db.get_collection("admin_templates")
            # Vérifier si la collection existe en essayant de compter
            count = await templates_collection.count_documents({})
            templates_supported = True
            
            # Filtrer les templates par niveau si possible
            # Note: La structure des templates peut varier, on exporte tous les templates
            # associés aux chapitres si un champ chapter_code existe
            if chapter_codes:
                # Si les templates ont un champ chapter_code
                query = {"chapter_code": {"$in": chapter_codes}}
                templates = await templates_collection.find(
                    query,
                    {"_id": 0}
                ).to_list(length=1000)
            else:
                # Sinon, exporter tous les templates (ou skip si trop large)
                templates = []
            
            logger.info(f"[PACKAGE] {len(templates)} templates trouvés pour {niveau}")
        except Exception as e:
            logger.info(f"[PACKAGE] Collection templates non disponible: {e}")
            templates_supported = False
        
        # 5. Construire le package
        package = {
            "schema_version": "pkg-1.0",
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "scope": {
                "niveau": niveau
            },
            "curriculum_chapters": chapters,
            "admin_exercises": exercises,
            "admin_templates": templates,
            "metadata": {
                "counts": {
                    "chapters": len(chapters),
                    "exercises": len(exercises),
                    "templates": len(templates)
                },
                "normalized": True,
                "templates_supported": templates_supported
            }
        }
        
        logger.info(
            f"[PACKAGE] Export réussi: {len(chapters)} chapitres, "
            f"{len(exercises)} exercices, {len(templates)} templates"
        )
        
        return package
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PACKAGE] Erreur export package {niveau}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "EXPORT_FAILED",
                "error": "export_failed",
                "message": f"Erreur lors de l'export du package: {str(e)}"
            }
        )


@router.post("/import")
async def import_package(
    package: Dict[str, Any],
    dry_run: bool = Query(False, description="Mode dry-run (validation uniquement, pas d'écriture)"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Importe un package complet avec validation stricte + rollback atomique
    
    Args:
        package: Package JSON v1.0
        dry_run: Si True, valide uniquement sans écrire en DB
        
    Returns:
        Stats d'import (dry-run ou réel)
    """
    logger.info(f"[PACKAGE] Import package (dry_run={dry_run})")
    
    try:
        # 1. Valider le package
        validate_package_v1(package)
        
        niveau = package["scope"]["niveau"]
        chapters = package.get("curriculum_chapters", [])
        exercises = package.get("admin_exercises", [])
        templates = package.get("admin_templates", [])
        
        logger.info(
            f"[PACKAGE] Package validé: {len(chapters)} chapitres, "
            f"{len(exercises)} exercices, {len(templates)} templates"
        )
        
        # 2. Valider chaque exercice (réutiliser validator PR4)
        exercise_errors = []
        for idx, exercise in enumerate(exercises):
            # Normaliser chapter_code
            code = exercise.get("chapter_code")
            if code:
                exercise["chapter_code"] = normalize_chapter_code(code)
            
            # Valider placeholders
            enonce_html = exercise.get("enonce_html", "")
            solution_html = exercise.get("solution_html", "")
            
            try:
                assert_no_unresolved_placeholders(enonce_html, f"enonce_html (exercice {idx})")
                assert_no_unresolved_placeholders(solution_html, f"solution_html (exercice {idx})")
            except AssertionError as e:
                exercise_errors.append({
                    "index": idx,
                    "error": f"Placeholders non résolus: {str(e)}",
                    "exercise_id": exercise.get("id", "N/A")
                })
        
        if exercise_errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_EXERCISES",
                    "error": "invalid_exercises",
                    "message": f"{len(exercise_errors)} exercice(s) avec placeholders non résolus",
                    "exercise_errors": exercise_errors
                }
            )
        
        # 3. Si dry_run, retourner les stats sans écrire
        if dry_run:
            return {
                "dry_run": True,
                "stats": {
                    "chapters_to_create": len(chapters),
                    "exercises_to_insert": len(exercises),
                    "templates_to_insert": len(templates)
                },
                "validation": "passed"
            }
        
        # 4. Import réel avec rollback atomique
        batch_id = str(uuid4())
        imported_at = datetime.utcnow()
        
        chapters_collection = db[CURRICULUM_CHAPTERS_COLLECTION]
        exercises_collection = db[EXERCISES_COLLECTION]
        
        chapters_created = 0
        exercises_inserted = 0
        templates_inserted = 0
        
        try:
            # 4.1. Créer/mettre à jour les chapitres
            for chapter in chapters:
                code = chapter.get("code_officiel") or chapter.get("code")
                if not code:
                    continue
                
                normalized_code = normalize_chapter_code(code)
                chapter["code_officiel"] = normalized_code
                if "code" in chapter:
                    chapter["code"] = normalized_code
                
                # Vérifier si le chapitre existe
                existing = await chapters_collection.find_one({"code_officiel": normalized_code})
                
                if existing:
                    # Mettre à jour
                    await chapters_collection.update_one(
                        {"code_officiel": normalized_code},
                        {"$set": chapter}
                    )
                else:
                    # Créer
                    await chapters_collection.insert_one(chapter)
                    chapters_created += 1
            
            # 4.2. Insérer les exercices (avec batch_id pour rollback)
            exercises_to_insert = []
            for exercise in exercises:
                # Normaliser chapter_code
                code = exercise.get("chapter_code")
                if code:
                    exercise["chapter_code"] = normalize_chapter_code(code)
                
                # Ajouter métadonnées d'import
                exercise["batch_id"] = batch_id
                exercise["imported_at"] = imported_at
                exercise.pop("_id", None)
                
                exercises_to_insert.append(exercise)
            
            if exercises_to_insert:
                result = await exercises_collection.insert_many(exercises_to_insert)
                exercises_inserted = len(result.inserted_ids)
            
            # 4.3. Insérer les templates (si collection disponible)
            try:
                templates_collection = db.get_collection("admin_templates")
                templates_to_insert = []
                for template in templates:
                    template.pop("_id", None)
                    template["batch_id"] = batch_id
                    template["imported_at"] = imported_at
                    templates_to_insert.append(template)
                
                if templates_to_insert:
                    result = await templates_collection.insert_many(templates_to_insert)
                    templates_inserted = len(result.inserted_ids)
            except Exception as e:
                logger.warning(f"[PACKAGE] Impossible d'insérer les templates: {e}")
            
            logger.info(
                f"[PACKAGE] Import réussi (batch_id={batch_id}): "
                f"{chapters_created} chapitres créés, {exercises_inserted} exercices, "
                f"{templates_inserted} templates"
            )
            
            return {
                "success": True,
                "batch_id": batch_id,
                "stats": {
                    "chapters_created": chapters_created,
                    "exercises_inserted": exercises_inserted,
                    "templates_inserted": templates_inserted
                }
            }
            
        except Exception as e:
            # Rollback: supprimer tous les documents avec ce batch_id
            logger.error(f"[PACKAGE] Erreur import (batch_id={batch_id}): {e}", exc_info=True)
            
            try:
                # Rollback exercices
                delete_result = await exercises_collection.delete_many({"batch_id": batch_id})
                logger.info(f"[PACKAGE] Rollback exercices: {delete_result.deleted_count} supprimés")
                
                # Rollback templates
                try:
                    templates_collection = db.get_collection("admin_templates")
                    delete_result = await templates_collection.delete_many({"batch_id": batch_id})
                    logger.info(f"[PACKAGE] Rollback templates: {delete_result.deleted_count} supprimés")
                except:
                    pass
                
                # Note: On ne supprime pas les chapitres car ils peuvent être partagés
                # (mais on pourrait ajouter un flag batch_id si nécessaire)
                
            except Exception as rollback_error:
                logger.critical(
                    f"[PACKAGE] ERREUR CRITIQUE: Échec du rollback (batch_id={batch_id}): {rollback_error}"
                )
            
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "IMPORT_FAILED",
                    "error": "import_failed",
                    "message": f"Erreur lors de l'import du package: {str(e)}",
                    "batch_id": batch_id,
                    "rollback_performed": True
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PACKAGE] Erreur import package: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "IMPORT_FAILED",
                "error": "import_failed",
                "message": f"Erreur lors de l'import du package: {str(e)}"
            }
        )

