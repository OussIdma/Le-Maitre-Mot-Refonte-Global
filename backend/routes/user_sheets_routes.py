"""
Routes API pour la gestion des fiches utilisateur (P3.1)

Endpoints:
- POST /api/user/sheets - Créer une fiche
- GET /api/user/sheets - Lister les fiches
- GET /api/user/sheets/{sheet_uid} - Récupérer une fiche
- PUT /api/user/sheets/{sheet_uid} - Modifier une fiche
- DELETE /api/user/sheets/{sheet_uid} - Supprimer une fiche
- POST /api/user/sheets/{sheet_uid}/add-exercise - Ajouter un exercice
- DELETE /api/user/sheets/{sheet_uid}/remove-exercise/{exercise_uid} - Retirer un exercice
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
import io
import asyncio
from pathlib import Path

from backend.server import db, validate_session_token

logger = logging.getLogger(__name__)

# P3.1: Router avec prefix /api/user/sheets pour cohérence avec /api/user/exercises
router = APIRouter(prefix="/api/user/sheets", tags=["user_sheets"])


# ============================================================================
# MODÈLES PYDANTIC
# ============================================================================

class SheetExercise(BaseModel):
    """Exercice dans une fiche"""
    exercise_uid: str = Field(..., description="UID de l'exercice (référence user_exercises)")
    order: int = Field(..., description="Ordre dans la fiche (1, 2, 3, ...)")


class SheetCreateRequest(BaseModel):
    """Requête pour créer une fiche"""
    title: str = Field(..., description="Titre de la fiche")
    description: Optional[str] = Field(default="", description="Description optionnelle")


class SheetUpdateRequest(BaseModel):
    """Requête pour modifier une fiche"""
    title: Optional[str] = Field(None, description="Nouveau titre")
    description: Optional[str] = Field(None, description="Nouvelle description")
    exercises: Optional[List[SheetExercise]] = Field(None, description="Nouvelle liste d'exercices ordonnée")


class SheetAddExerciseRequest(BaseModel):
    """Requête pour ajouter un exercice à une fiche"""
    exercise_uid: str = Field(..., description="UID de l'exercice à ajouter")


class SheetResponse(BaseModel):
    """Réponse pour une fiche"""
    sheet_uid: str
    user_email: str
    title: str
    description: str
    exercises: List[SheetExercise]
    created_at: str
    updated_at: str


# ============================================================================
# HELPERS
# ============================================================================

async def get_user_email(request: Request) -> str:
    """Récupère l'email de l'utilisateur depuis la session"""
    session_token = request.headers.get("X-Session-Token")
    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Authentification requise"
        )
    
    user_email = await validate_session_token(session_token)
    if not user_email:
        raise HTTPException(
            status_code=401,
            detail="Session invalide ou expirée"
        )
    
    return user_email


async def verify_sheet_ownership(sheet_uid: str, user_email: str) -> Dict[str, Any]:
    """Vérifie que la fiche appartient à l'utilisateur"""
    sheet = await db.user_sheets.find_one({
        "sheet_uid": sheet_uid,
        "user_email": user_email
    })
    
    if not sheet:
        raise HTTPException(
            status_code=404,
            detail="Fiche non trouvée ou vous n'avez pas accès à cette fiche"
        )
    
    return sheet


async def get_exercise_count(sheet: Dict[str, Any]) -> int:
    """Récupère le nombre réel d'exercices (vérifie existence dans user_exercises)"""
    exercises = sheet.get("exercises", [])
    if not exercises:
        return 0
    
    # Vérifier combien d'exercices existent réellement
    exercise_uids = [ex.get("exercise_uid") for ex in exercises]
    existing = await db.user_exercises.count_documents({
        "exercise_uid": {"$in": exercise_uids}
    })
    
    return existing


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("", response_model=SheetResponse, status_code=201)
async def create_sheet(
    request_body: SheetCreateRequest,
    user_email: str = Depends(get_user_email)
):
    """Créer une nouvelle fiche vide"""
    sheet_uid = f"sheet_{uuid.uuid4().hex[:16]}"
    
    sheet_doc = {
        "sheet_uid": sheet_uid,
        "user_email": user_email,
        "title": request_body.title,
        "description": request_body.description or "",
        "exercises": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.user_sheets.insert_one(sheet_doc)
    
    logger.info(f"P3.1: Fiche créée pour {user_email} - sheet_uid={sheet_uid}")
    
    return SheetResponse(
        sheet_uid=sheet_uid,
        user_email=user_email,
        title=request_body.title,
        description=request_body.description or "",
        exercises=[],
        created_at=sheet_doc["created_at"].isoformat(),
        updated_at=sheet_doc["updated_at"].isoformat()
    )


@router.get("", response_model=List[SheetResponse])
async def list_sheets(
    user_email: str = Depends(get_user_email)
):
    """Lister toutes les fiches de l'utilisateur"""
    cursor = db.user_sheets.find({"user_email": user_email}).sort("updated_at", -1)
    sheets = await cursor.to_list(length=100)
    
    result = []
    for sheet in sheets:
        # Compter les exercices réels
        exercise_count = await get_exercise_count(sheet)
        
        result.append(SheetResponse(
            sheet_uid=sheet["sheet_uid"],
            user_email=sheet["user_email"],
            title=sheet["title"],
            description=sheet.get("description", ""),
            exercises=sheet.get("exercises", []),
            created_at=sheet["created_at"].isoformat() if isinstance(sheet["created_at"], datetime) else sheet["created_at"],
            updated_at=sheet["updated_at"].isoformat() if isinstance(sheet["updated_at"], datetime) else sheet["updated_at"]
        ))
    
    logger.info(f"P3.1: Liste fiches récupérée pour {user_email} - count={len(result)}")
    
    return result


@router.get("/{sheet_uid}", response_model=SheetResponse)
async def get_sheet(
    sheet_uid: str,
    user_email: str = Depends(get_user_email)
):
    """Récupérer une fiche complète"""
    sheet = await verify_sheet_ownership(sheet_uid, user_email)
    
    return SheetResponse(
        sheet_uid=sheet["sheet_uid"],
        user_email=sheet["user_email"],
        title=sheet["title"],
        description=sheet.get("description", ""),
        exercises=sheet.get("exercises", []),
        created_at=sheet["created_at"].isoformat() if isinstance(sheet["created_at"], datetime) else sheet["created_at"],
        updated_at=sheet["updated_at"].isoformat() if isinstance(sheet["updated_at"], datetime) else sheet["updated_at"]
    )


@router.put("/{sheet_uid}", response_model=SheetResponse)
async def update_sheet(
    sheet_uid: str,
    request_body: SheetUpdateRequest,
    user_email: str = Depends(get_user_email)
):
    """Modifier une fiche (titre, description, ordre des exercices)"""
    sheet = await verify_sheet_ownership(sheet_uid, user_email)
    
    update_data = {
        "updated_at": datetime.now(timezone.utc)
    }
    
    if request_body.title is not None:
        update_data["title"] = request_body.title
    
    if request_body.description is not None:
        update_data["description"] = request_body.description
    
    if request_body.exercises is not None:
        # Vérifier que tous les exercices existent
        exercise_uids = [ex.exercise_uid for ex in request_body.exercises]
        existing_count = await db.user_exercises.count_documents({
            "exercise_uid": {"$in": exercise_uids},
            "user_email": user_email  # Vérifier ownership
        })
        
        if existing_count != len(exercise_uids):
            raise HTTPException(
                status_code=400,
                detail="Un ou plusieurs exercices n'existent pas ou ne vous appartiennent pas"
            )
        
        update_data["exercises"] = [ex.dict() for ex in request_body.exercises]
    
    await db.user_sheets.update_one(
        {"sheet_uid": sheet_uid},
        {"$set": update_data}
    )
    
    # Récupérer la fiche mise à jour
    updated_sheet = await db.user_sheets.find_one({"sheet_uid": sheet_uid})
    
    logger.info(f"P3.1: Fiche mise à jour - sheet_uid={sheet_uid}")
    
    return SheetResponse(
        sheet_uid=updated_sheet["sheet_uid"],
        user_email=updated_sheet["user_email"],
        title=updated_sheet["title"],
        description=updated_sheet.get("description", ""),
        exercises=updated_sheet.get("exercises", []),
        created_at=updated_sheet["created_at"].isoformat() if isinstance(updated_sheet["created_at"], datetime) else updated_sheet["created_at"],
        updated_at=updated_sheet["updated_at"].isoformat() if isinstance(updated_sheet["updated_at"], datetime) else updated_sheet["updated_at"]
    )


@router.delete("/{sheet_uid}", status_code=204)
async def delete_sheet(
    sheet_uid: str,
    user_email: str = Depends(get_user_email)
):
    """Supprimer une fiche"""
    await verify_sheet_ownership(sheet_uid, user_email)
    
    result = await db.user_sheets.delete_one({"sheet_uid": sheet_uid})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Fiche non trouvée")
    
    logger.info(f"P3.1: Fiche supprimée - sheet_uid={sheet_uid}")
    
    return None


@router.post("/{sheet_uid}/add-exercise", response_model=SheetResponse)
async def add_exercise_to_sheet(
    sheet_uid: str,
    request_body: SheetAddExerciseRequest,
    user_email: str = Depends(get_user_email)
):
    """Ajouter un exercice à une fiche"""
    sheet = await verify_sheet_ownership(sheet_uid, user_email)
    
    # Vérifier que l'exercice existe et appartient à l'utilisateur
    exercise = await db.user_exercises.find_one({
        "exercise_uid": request_body.exercise_uid,
        "user_email": user_email
    })
    
    if not exercise:
        raise HTTPException(
            status_code=404,
            detail="Exercice non trouvé ou ne vous appartient pas"
        )
    
    # Vérifier que l'exercice n'est pas déjà dans la fiche
    exercises = sheet.get("exercises", [])
    if any(ex.get("exercise_uid") == request_body.exercise_uid for ex in exercises):
        raise HTTPException(
            status_code=400,
            detail="Cet exercice est déjà dans la fiche"
        )
    
    # Ajouter l'exercice à la fin
    new_order = len(exercises) + 1
    exercises.append({
        "exercise_uid": request_body.exercise_uid,
        "order": new_order
    })
    
    await db.user_sheets.update_one(
        {"sheet_uid": sheet_uid},
        {
            "$set": {
                "exercises": exercises,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Récupérer la fiche mise à jour
    updated_sheet = await db.user_sheets.find_one({"sheet_uid": sheet_uid})
    
    logger.info(f"P3.1: Exercice ajouté à la fiche - sheet_uid={sheet_uid}, exercise_uid={request_body.exercise_uid}")
    
    return SheetResponse(
        sheet_uid=updated_sheet["sheet_uid"],
        user_email=updated_sheet["user_email"],
        title=updated_sheet["title"],
        description=updated_sheet.get("description", ""),
        exercises=updated_sheet.get("exercises", []),
        created_at=updated_sheet["created_at"].isoformat() if isinstance(updated_sheet["created_at"], datetime) else updated_sheet["created_at"],
        updated_at=updated_sheet["updated_at"].isoformat() if isinstance(updated_sheet["updated_at"], datetime) else updated_sheet["updated_at"]
    )


@router.delete("/{sheet_uid}/remove-exercise/{exercise_uid}", response_model=SheetResponse)
async def remove_exercise_from_sheet(
    sheet_uid: str,
    exercise_uid: str,
    user_email: str = Depends(get_user_email)
):
    """Retirer un exercice d'une fiche"""
    sheet = await verify_sheet_ownership(sheet_uid, user_email)
    
    exercises = sheet.get("exercises", [])
    
    # Retirer l'exercice
    exercises = [ex for ex in exercises if ex.get("exercise_uid") != exercise_uid]
    
    # Réordonner (1, 2, 3, ...)
    for i, ex in enumerate(exercises, 1):
        ex["order"] = i
    
    await db.user_sheets.update_one(
        {"sheet_uid": sheet_uid},
        {
            "$set": {
                "exercises": exercises,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Récupérer la fiche mise à jour
    updated_sheet = await db.user_sheets.find_one({"sheet_uid": sheet_uid})
    
    logger.info(f"P3.1: Exercice retiré de la fiche - sheet_uid={sheet_uid}, exercise_uid={exercise_uid}")
    
    return SheetResponse(
        sheet_uid=updated_sheet["sheet_uid"],
        user_email=updated_sheet["user_email"],
        title=updated_sheet["title"],
        description=updated_sheet.get("description", ""),
        exercises=updated_sheet.get("exercises", []),
        created_at=updated_sheet["created_at"].isoformat() if isinstance(updated_sheet["created_at"], datetime) else updated_sheet["created_at"],
        updated_at=updated_sheet["updated_at"].isoformat() if isinstance(updated_sheet["updated_at"], datetime) else updated_sheet["updated_at"]
    )


@router.post("/{sheet_uid}/export-pdf")
async def export_sheet_pdf(
    sheet_uid: str,
    include_solutions: bool = False,
    user_email: str = Depends(get_user_email)
):
    """Exporter une fiche en PDF (P3.1)"""
    sheet = await verify_sheet_ownership(sheet_uid, user_email)
    
    # Charger les exercices complets
    exercises = sheet.get("exercises", [])
    if not exercises:
        raise HTTPException(
            status_code=400,
            detail="La fiche ne contient aucun exercice"
        )
    
    # Récupérer les exercices depuis user_exercises
    exercise_uids = [ex.get("exercise_uid") for ex in exercises]
    exercises_docs = await db.user_exercises.find({
        "exercise_uid": {"$in": exercise_uids},
        "user_email": user_email
    }).to_list(length=100)
    
    # Créer un mapping
    exercises_map = {ex["exercise_uid"]: ex for ex in exercises_docs}
    
    # Construire le HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{sheet["title"]}</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: 'Times New Roman', serif;
                font-size: 12pt;
                line-height: 1.6;
            }}
            h1 {{
                font-size: 18pt;
                margin-bottom: 1cm;
                text-align: center;
            }}
            .exercise {{
                margin-bottom: 1.5cm;
                page-break-inside: avoid;
            }}
            .exercise-number {{
                font-weight: bold;
                font-size: 14pt;
                margin-bottom: 0.5cm;
            }}
            .enonce {{
                margin-bottom: 1cm;
            }}
            .solution {{
                margin-top: 1cm;
                padding: 0.5cm;
                background-color: #f5f5f5;
                border-left: 3px solid #2563eb;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 0.5cm 0;
            }}
            table, th, td {{
                border: 1px solid #ddd;
            }}
            th, td {{
                padding: 8px;
                text-align: left;
            }}
        </style>
    </head>
    <body>
        <h1>{sheet["title"]}</h1>
    """
    
    # P0: Compter les exercices manquants
    missing_exercises = []
    exercises_added = 0
    
    # Ajouter les exercices dans l'ordre
    for idx, sheet_ex in enumerate(sorted(exercises, key=lambda x: x.get("order", 0)), 1):
        exercise_uid = sheet_ex.get("exercise_uid")
        exercise = exercises_map.get(exercise_uid)
        
        if not exercise:
            # P0: Exercice manquant - logger et ajouter un placeholder explicite
            logger.warning(
                f"[SHEETS_EXPORT] missing_exercise - sheet_uid={sheet_uid}, user_email={user_email}, exercise_uid={exercise_uid}"
            )
            missing_exercises.append(exercise_uid)
            
            # Ajouter un bloc HTML explicite dans le PDF
            html_content += f"""
        <div class="exercise">
            <div class="exercise-number">Exercice {idx}</div>
            <div class="enonce" style="color: #dc2626; font-style: italic;">
                ⚠️ Exercice introuvable (supprimé ou non accessible). UID: {exercise_uid}
            </div>
        </div>
        """
            continue
        
        exercises_added += 1
        html_content += f"""
        <div class="exercise">
            <div class="exercise-number">Exercice {idx}</div>
            <div class="enonce">
                {exercise.get("enonce_html", "")}
            </div>
        """
        
        if include_solutions and exercise.get("solution_html"):
            html_content += f"""
            <div class="solution">
                <strong>Solution :</strong>
                {exercise.get("solution_html", "")}
            </div>
            """
        
        html_content += "</div>"
    
    # P0: Si tous les exercices sont manquants, retourner une erreur 409
    if exercises_added == 0 and len(exercises) > 0:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "all_exercises_missing",
                "message": "Tous les exercices de cette fiche sont introuvables (supprimés ou non accessibles). Impossible de générer le PDF.",
                "missing_exercises": missing_exercises
            }
        )
    
    html_content += """
    </body>
    </html>
    """
    
    # Générer le PDF avec WeasyPrint
    try:
        import weasyprint
        
        loop = asyncio.get_event_loop()
        pdf_bytes = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: weasyprint.HTML(
                    string=html_content,
                    base_url=str(Path("/app/backend").resolve())
                ).write_pdf()
            ),
            timeout=30
        )
        
        logger.info(f"P3.1: PDF généré pour fiche {sheet_uid} - {len(pdf_bytes)} bytes")
        
        # Retourner le PDF
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{sheet["title"]}.pdf"'
            }
        )
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="WeasyPrint n'est pas installé"
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Timeout lors de la génération du PDF"
        )
    except Exception as e:
        logger.error(f"Erreur génération PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du PDF: {str(e)}"
        )

