"""
Schéma PACKAGE v1.0 pour import/export global (niveau → chapitres → exercices → templates)
===========================================================================================

Format canonique pour exporter/importer un package complet d'un niveau.
Source de vérité: MongoDB (curriculum_chapters, admin_exercises, templates si disponible).
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class PackageScope(BaseModel):
    """Scope du package (niveau)"""
    niveau: str = Field(..., description="Niveau scolaire (ex: '6e', '5e', '4e')")


class PackageMetadata(BaseModel):
    """Métadonnées du package"""
    counts: Dict[str, int] = Field(..., description="Compteurs: chapters, exercises, templates")
    normalized: bool = Field(True, description="Tous les chapter_code sont normalisés")
    templates_supported: bool = Field(False, description="Si la collection templates est disponible")


class PackageV1(BaseModel):
    """
    Package complet v1.0 pour un niveau
    
    Structure:
    - schema_version: "pkg-1.0"
    - exported_at: ISO-8601
    - scope: { niveau: "6e" }
    - curriculum_chapters: [docs DB...]
    - admin_exercises: [docs DB...]
    - admin_templates: [docs DB...] (optionnel)
    - metadata: { counts, normalized, templates_supported }
    """
    schema_version: str = Field("pkg-1.0", description="Version du schéma package")
    exported_at: str = Field(..., description="Date d'export ISO-8601")
    scope: PackageScope = Field(..., description="Scope du package (niveau)")
    curriculum_chapters: List[Dict[str, Any]] = Field(default_factory=list, description="Chapitres du curriculum")
    admin_exercises: List[Dict[str, Any]] = Field(default_factory=list, description="Exercices admin")
    admin_templates: List[Dict[str, Any]] = Field(default_factory=list, description="Templates (optionnel)")
    metadata: PackageMetadata = Field(..., description="Métadonnées du package")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_version": "pkg-1.0",
                "exported_at": "2024-01-15T10:30:00Z",
                "scope": {"niveau": "6e"},
                "curriculum_chapters": [
                    {
                        "code_officiel": "6E_N01",
                        "titre": "Nombres entiers",
                        "domaine": "Nombres",
                        "niveau": "6e"
                    }
                ],
                "admin_exercises": [
                    {
                        "id": "ex1",
                        "chapter_code": "6E_N01",
                        "enonce_html": "<p>Exercice...</p>",
                        "solution_html": "<p>Solution...</p>",
                        "difficulty": "moyen",
                        "offer": "free"
                    }
                ],
                "admin_templates": [],
                "metadata": {
                    "counts": {"chapters": 1, "exercises": 1, "templates": 0},
                    "normalized": True,
                    "templates_supported": False
                }
            }
        }


def normalize_chapter_code(code: str) -> str:
    """
    Normalise un chapter_code au format canonique (UPPER + "-"→"_")
    
    Args:
        code: Code du chapitre (ex: "6e-gm07", "6E_GM07")
        
    Returns:
        Code normalisé (ex: "6E_GM07")
    """
    if not code:
        return code
    return code.upper().replace("-", "_")


def validate_package_v1(package: Dict[str, Any]) -> None:
    """
    Valide un package v1.0
    
    Args:
        package: Package JSON à valider
        
    Raises:
        ValueError: Si le package est invalide
    """
    from fastapi import HTTPException
    
    # 1. Vérifier schema_version
    schema_version = package.get("schema_version")
    if schema_version != "pkg-1.0":
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_SCHEMA_VERSION",
                "error": "invalid_schema_version",
                "message": f"Version de schéma invalide: '{schema_version}'. Version attendue: 'pkg-1.0'",
                "provided_version": schema_version,
                "expected_version": "pkg-1.0"
            }
        )
    
    # 2. Vérifier scope
    scope = package.get("scope")
    if not scope or not isinstance(scope, dict):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_SCOPE",
                "error": "invalid_scope",
                "message": "scope est requis et doit être un dictionnaire"
            }
        )
    
    niveau = scope.get("niveau")
    if not niveau or not isinstance(niveau, str):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_NIVEAU",
                "error": "invalid_niveau",
                "message": "scope.niveau est requis et doit être une chaîne"
            }
        )
    
    # 3. Vérifier metadata.counts
    metadata = package.get("metadata", {})
    if not isinstance(metadata, dict):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_METADATA",
                "error": "invalid_metadata",
                "message": "metadata doit être un dictionnaire"
            }
        )
    
    counts = metadata.get("counts", {})
    if not isinstance(counts, dict):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_COUNTS",
                "error": "invalid_counts",
                "message": "metadata.counts doit être un dictionnaire"
            }
        )
    
    # 4. Vérifier cohérence counts
    chapters = package.get("curriculum_chapters", [])
    exercises = package.get("admin_exercises", [])
    templates = package.get("admin_templates", [])
    
    expected_chapters = counts.get("chapters", 0)
    expected_exercises = counts.get("exercises", 0)
    expected_templates = counts.get("templates", 0)
    
    if len(chapters) != expected_chapters:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "METADATA_MISMATCH",
                "error": "metadata_mismatch",
                "message": f"metadata.counts.chapters ({expected_chapters}) ne correspond pas au nombre de chapitres ({len(chapters)})",
                "metadata_count": expected_chapters,
                "actual_count": len(chapters)
            }
        )
    
    if len(exercises) != expected_exercises:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "METADATA_MISMATCH",
                "error": "metadata_mismatch",
                "message": f"metadata.counts.exercises ({expected_exercises}) ne correspond pas au nombre d'exercices ({len(exercises)})",
                "metadata_count": expected_exercises,
                "actual_count": len(exercises)
            }
        )
    
    if len(templates) != expected_templates:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "METADATA_MISMATCH",
                "error": "metadata_mismatch",
                "message": f"metadata.counts.templates ({expected_templates}) ne correspond pas au nombre de templates ({len(templates)})",
                "metadata_count": expected_templates,
                "actual_count": len(templates)
            }
        )
    
    # 5. Vérifier normalisation chapter_code
    normalized = metadata.get("normalized", False)
    if normalized:
        for chapter in chapters:
            code = chapter.get("code_officiel") or chapter.get("code")
            if code and normalize_chapter_code(code) != code:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error_code": "NORMALIZATION_ERROR",
                        "error": "normalization_error",
                        "message": f"Chapitre avec code non normalisé: '{code}' (attendu: '{normalize_chapter_code(code)}')",
                        "chapter_code": code,
                        "expected": normalize_chapter_code(code)
                    }
                )
        
        for exercise in exercises:
            code = exercise.get("chapter_code")
            if code and normalize_chapter_code(code) != code:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error_code": "NORMALIZATION_ERROR",
                        "error": "normalization_error",
                        "message": f"Exercice avec chapter_code non normalisé: '{code}' (attendu: '{normalize_chapter_code(code)}')",
                        "chapter_code": code,
                        "expected": normalize_chapter_code(code)
                    }
                )

