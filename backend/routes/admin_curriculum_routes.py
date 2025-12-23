"""
Routes admin pour la gestion du curriculum (P1.2 Simplifié)

Permet l'ajout/retrait de générateurs à un chapitre via UI,
en modifiant directement le curriculum JSON de manière sécurisée.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import json
import os
from pathlib import Path

from backend.generators.factory import GeneratorFactory
from backend.observability.logger import get_logger

router = APIRouter(prefix="/api/v1/admin/curriculum", tags=["admin-curriculum"])
obs_logger = get_logger()

# Chemin vers les fichiers curriculum
CURRICULUM_DIR = Path(__file__).parent.parent / "curriculum"


class ExerciseTypesUpdateRequest(BaseModel):
    """Request pour modifier les exercise_types d'un chapitre."""
    add: Optional[List[str]] = Field(default_factory=list, description="Générateurs à ajouter")
    remove: Optional[List[str]] = Field(default_factory=list, description="Générateurs à retirer")


def _get_curriculum_file_path(code_officiel: str) -> Path:
    """
    Détermine le fichier curriculum correspondant au code_officiel.
    
    Ex: "6e_SP03" → curriculum_6e.json
    """
    grade = code_officiel.split("_")[0]  # "6e", "5e", etc.
    filename = f"curriculum_{grade}.json"
    filepath = CURRICULUM_DIR / filename
    
    if not filepath.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "CURRICULUM_FILE_NOT_FOUND",
                "message": f"Fichier curriculum introuvable : {filename}",
                "grade": grade,
                "hint": f"Créez le fichier {filepath}"
            }
        )
    
    return filepath


def _validate_generator_keys(generator_keys: List[str]) -> None:
    """
    Valide que tous les generator_keys existent dans la factory.
    
    Raises:
        HTTPException 422 si un générateur est inconnu
    """
    unknown_keys = []
    
    for key in generator_keys:
        gen_class = GeneratorFactory.get(key)
        if gen_class is None:
            unknown_keys.append(key)
    
    if unknown_keys:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "UNKNOWN_GENERATOR_KEYS",
                "message": f"Générateurs inconnus : {', '.join(unknown_keys)}",
                "unknown_keys": unknown_keys,
                "hint": "Vérifiez l'orthographe ou enregistrez ces générateurs dans GeneratorFactory"
            }
        )


@router.post("/chapters/{code_officiel}/exercise-types")
async def update_chapter_exercise_types(
    code_officiel: str,
    request: ExerciseTypesUpdateRequest
):
    """
    Modifie les exercise_types d'un chapitre en éditant le curriculum JSON.
    
    **Opérations idempotentes** :
    - `add`: Ajoute les générateurs s'ils ne sont pas déjà présents
    - `remove`: Retire les générateurs s'ils sont présents
    
    **Validation** :
    - Refuse si generator_key inconnu dans GeneratorFactory
    - Log explicite de chaque modification
    
    **Exemple** :
    ```json
    {
        "add": ["CALCUL_NOMBRES_V1", "RAISONNEMENT_MULTIPLICATIF_V1"],
        "remove": ["ANCIEN_GENERATEUR"]
    }
    ```
    
    **Sécurité** :
    - Backup automatique du fichier original (curriculum_XX.json.bak)
    - Validation JSON avant sauvegarde
    - Atomic write (écrit dans .tmp puis rename)
    """
    # Validation des clés
    all_keys = (request.add or []) + (request.remove or [])
    if all_keys:
        _validate_generator_keys(all_keys)
    
    # Charger le fichier curriculum
    filepath = _get_curriculum_file_path(code_officiel)
    
    obs_logger.info(
        "event=update_exercise_types_start",
        code_officiel=code_officiel,
        add=request.add,
        remove=request.remove,
        filepath=str(filepath)
    )
    
    # Lire le curriculum actuel
    with open(filepath, 'r', encoding='utf-8') as f:
        curriculum = json.load(f)
    
    # Créer un backup
    backup_path = filepath.with_suffix(filepath.suffix + '.bak')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(curriculum, f, indent=2, ensure_ascii=False)
    
    obs_logger.info(
        "event=backup_created",
        backup_path=str(backup_path)
    )
    
    # Trouver le chapitre dans le curriculum
    chapter_found = False
    modified = False
    
    for domain in curriculum.get("domains", []):
        for chapter in domain.get("chapters", []):
            if chapter.get("code_officiel") == code_officiel:
                chapter_found = True
                
                # Récupérer les exercise_types actuels
                current_types = chapter.get("exercise_types", [])
                original_types = current_types.copy()
                
                # Opération ADD (idempotente)
                for gen_key in (request.add or []):
                    if gen_key not in current_types:
                        current_types.append(gen_key)
                        obs_logger.info(
                            "event=generator_added",
                            code_officiel=code_officiel,
                            generator_key=gen_key
                        )
                        modified = True
                    else:
                        obs_logger.info(
                            "event=generator_already_present",
                            code_officiel=code_officiel,
                            generator_key=gen_key
                        )
                
                # Opération REMOVE (idempotente)
                for gen_key in (request.remove or []):
                    if gen_key in current_types:
                        current_types.remove(gen_key)
                        obs_logger.info(
                            "event=generator_removed",
                            code_officiel=code_officiel,
                            generator_key=gen_key
                        )
                        modified = True
                    else:
                        obs_logger.info(
                            "event=generator_not_present",
                            code_officiel=code_officiel,
                            generator_key=gen_key
                        )
                
                # Mettre à jour
                chapter["exercise_types"] = current_types
                
                obs_logger.info(
                    "event=chapter_updated",
                    code_officiel=code_officiel,
                    original_count=len(original_types),
                    new_count=len(current_types),
                    modified=modified
                )
                
                break
        
        if chapter_found:
            break
    
    if not chapter_found:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "CHAPTER_NOT_FOUND",
                "message": f"Chapitre {code_officiel} introuvable dans {filepath.name}",
                "code_officiel": code_officiel,
                "hint": "Vérifiez que le code_officiel existe dans le curriculum JSON"
            }
        )
    
    # Sauvegarder (atomic write)
    if modified:
        tmp_path = filepath.with_suffix('.tmp')
        
        try:
            # Écrire dans fichier temporaire
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(curriculum, f, indent=2, ensure_ascii=False)
            
            # Valider que c'est du JSON valide
            with open(tmp_path, 'r', encoding='utf-8') as f:
                json.load(f)
            
            # Remplacer l'original (atomic sur la plupart des OS)
            os.replace(tmp_path, filepath)
            
            obs_logger.info(
                "event=curriculum_saved",
                filepath=str(filepath),
                modified=True
            )
        
        except Exception as e:
            # Rollback : restaurer depuis le backup
            if tmp_path.exists():
                tmp_path.unlink()
            
            obs_logger.error(
                "event=save_failed",
                error=str(e),
                filepath=str(filepath)
            )
            
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "SAVE_FAILED",
                    "message": f"Erreur lors de la sauvegarde : {str(e)}",
                    "hint": f"Le backup est disponible ici : {backup_path}"
                }
            )
    
    # Retourner le résultat
    return {
        "code_officiel": code_officiel,
        "modified": modified,
        "added": [k for k in (request.add or []) if k not in original_types] if modified else [],
        "removed": [k for k in (request.remove or []) if k in original_types] if modified else [],
        "current_exercise_types": current_types,
        "backup_path": str(backup_path)
    }


@router.get("/chapters/{code_officiel}/exercise-types")
async def get_chapter_exercise_types(code_officiel: str):
    """
    Récupère les exercise_types actuels d'un chapitre.
    
    **Retourne** :
    - Liste des generator_keys configurés
    - Métadonnées enrichies (label, is_dynamic, supported_grades)
    """
    # Charger le fichier curriculum
    filepath = _get_curriculum_file_path(code_officiel)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        curriculum = json.load(f)
    
    # Trouver le chapitre
    for domain in curriculum.get("domains", []):
        for chapter in domain.get("chapters", []):
            if chapter.get("code_officiel") == code_officiel:
                exercise_types = chapter.get("exercise_types", [])
                
                # Enrichir avec métadonnées
                enriched = []
                for gen_key in exercise_types:
                    gen_class = GeneratorFactory.get(gen_key)
                    
                    if gen_class:
                        meta = gen_class.get_meta()
                        enriched.append({
                            "key": gen_key,
                            "label": meta.label,
                            "is_dynamic": getattr(meta, 'is_dynamic', True),
                            "supported_grades": getattr(meta, 'supported_grades', meta.niveaux),
                            "exists": True
                        })
                    else:
                        # Générateur configuré mais introuvable
                        enriched.append({
                            "key": gen_key,
                            "label": f"⚠️ {gen_key} (introuvable)",
                            "is_dynamic": None,
                            "supported_grades": [],
                            "exists": False
                        })
                
                return {
                    "code_officiel": code_officiel,
                    "exercise_types": enriched,
                    "total": len(enriched)
                }
    
        raise HTTPException(
            status_code=404,
            detail={
            "error_code": "CHAPTER_NOT_FOUND",
            "message": f"Chapitre {code_officiel} introuvable",
            "code_officiel": code_officiel
        }
    )
