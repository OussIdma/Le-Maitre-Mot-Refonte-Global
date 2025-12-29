"""
Validateur strict pour l'import/export versionné d'exercices
=============================================================

Valide le format canonique v1.0 pour l'import/export d'exercices.
Garantit l'intégrité des données avant insertion en DB.
"""

from fastapi import HTTPException
from typing import Dict, Any, List
from datetime import datetime
from backend.tests.contracts.exercise_contract import assert_no_unresolved_placeholders


def validate_import_payload_v1(payload: Dict[str, Any]) -> None:
    """
    Valide strictement un payload d'import versionné v1.0.
    
    Args:
        payload: Payload JSON à valider
    
    Raises:
        HTTPException(400): Si le payload est invalide
    """
    # 1. Vérifier les clés racines requises
    required_keys = ["schema_version", "chapter_code", "exercises", "metadata"]
    missing_keys = [key for key in required_keys if key not in payload]
    if missing_keys:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_PAYLOAD",
                "error": "missing_required_keys",
                "message": f"Clés manquantes dans le payload: {', '.join(missing_keys)}",
                "missing_keys": missing_keys
            }
        )
    
    # 2. Vérifier schema_version
    schema_version = payload.get("schema_version")
    if schema_version != "1.0":
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_SCHEMA_VERSION",
                "error": "invalid_schema_version",
                "message": f"Version de schéma invalide: '{schema_version}'. Version attendue: '1.0'",
                "provided_version": schema_version,
                "expected_version": "1.0"
            }
        )
    
    # 3. Vérifier chapter_code
    chapter_code = payload.get("chapter_code")
    if not chapter_code or not isinstance(chapter_code, str) or not chapter_code.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_CHAPTER_CODE",
                "error": "invalid_chapter_code",
                "message": "chapter_code doit être une chaîne non vide",
                "provided_value": chapter_code
            }
        )
    
    # Normaliser chapter_code
    normalized_chapter_code = chapter_code.upper().replace("-", "_")
    
    # 4. Vérifier exercises
    exercises = payload.get("exercises")
    if not isinstance(exercises, list):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_EXERCISES",
                "error": "invalid_exercises",
                "message": "exercises doit être une liste",
                "provided_type": type(exercises).__name__
            }
        )
    
    if len(exercises) == 0:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "EMPTY_EXERCISES",
                "error": "empty_exercises",
                "message": "La liste d'exercices ne peut pas être vide"
            }
        )
    
    # 5. Vérifier metadata.total_exercises
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_METADATA",
                "error": "invalid_metadata",
                "message": "metadata doit être un dictionnaire",
                "provided_type": type(metadata).__name__
            }
        )
    
    total_exercises = metadata.get("total_exercises")
    if total_exercises != len(exercises):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "METADATA_MISMATCH",
                "error": "metadata_mismatch",
                "message": f"metadata.total_exercises ({total_exercises}) ne correspond pas au nombre d'exercices ({len(exercises)})",
                "metadata_total": total_exercises,
                "actual_count": len(exercises)
            }
        )
    
    # 6. Valider chaque exercice
    exercise_errors = []
    for idx, exercise in enumerate(exercises):
        if not isinstance(exercise, dict):
            exercise_errors.append({
                "index": idx,
                "error": "L'exercice doit être un dictionnaire",
                "provided_type": type(exercise).__name__
            })
            continue
        
        # 6.1. Vérifier chapter_code (ou l'imposer depuis payload)
        if "chapter_code" not in exercise or not exercise.get("chapter_code"):
            exercise["chapter_code"] = normalized_chapter_code
        else:
            # Normaliser le chapter_code de l'exercice
            exercise["chapter_code"] = str(exercise["chapter_code"]).upper().replace("-", "_")
        
        # 6.2. Vérifier enonce_html
        enonce_html = exercise.get("enonce_html", "")
        if not enonce_html or not isinstance(enonce_html, str) or not enonce_html.strip():
            exercise_errors.append({
                "index": idx,
                "error": "enonce_html est requis et ne peut pas être vide",
                "exercise_id": exercise.get("id", "N/A")
            })
            continue
        
        # 6.3. Vérifier solution_html
        solution_html = exercise.get("solution_html", "")
        if not solution_html or not isinstance(solution_html, str) or not solution_html.strip():
            exercise_errors.append({
                "index": idx,
                "error": "solution_html est requis et ne peut pas être vide",
                "exercise_id": exercise.get("id", "N/A")
            })
            continue
        
        # 6.4. Vérifier placeholders non résolus
        try:
            assert_no_unresolved_placeholders(enonce_html, f"enonce_html (exercice {idx})")
            assert_no_unresolved_placeholders(solution_html, f"solution_html (exercice {idx})")
        except AssertionError as e:
            exercise_errors.append({
                "index": idx,
                "error": f"Placeholders non résolus: {str(e)}",
                "exercise_id": exercise.get("id", "N/A")
            })
            continue
        
        # 6.5. Vérifier offer
        offer = exercise.get("offer", "free")
        if offer not in {"free", "pro"}:
            exercise_errors.append({
                "index": idx,
                "error": f"offer invalide: '{offer}'. Valeurs acceptées: 'free', 'pro'",
                "exercise_id": exercise.get("id", "N/A"),
                "provided_offer": offer
            })
            continue
        
        # 6.6. Vérifier difficulty
        difficulty = exercise.get("difficulty", "")
        if difficulty and difficulty not in {"facile", "moyen", "difficile"}:
            exercise_errors.append({
                "index": idx,
                "error": f"difficulty invalide: '{difficulty}'. Valeurs acceptées: 'facile', 'moyen', 'difficile'",
                "exercise_id": exercise.get("id", "N/A"),
                "provided_difficulty": difficulty
            })
            continue
    
    # 7. Si erreurs dans les exercices, lever une exception
    if exercise_errors:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_EXERCISES",
                "error": "invalid_exercises",
                "message": f"{len(exercise_errors)} exercice(s) invalide(s) sur {len(exercises)}",
                "exercise_errors": exercise_errors,
                "total_exercises": len(exercises),
                "invalid_count": len(exercise_errors)
            }
        )

