"""
Routes API v1 pour la génération d'exercices
Endpoint: POST /api/v1/exercises/generate
Endpoint batch: POST /api/v1/exercises/generate/batch (GM07 uniquement)

Modes de fonctionnement:
1. Mode GM07 (chapitre pilote): exercices figés depuis gm07_exercises.py
2. Mode legacy: niveau + chapitre (comportement existant)
3. Mode officiel: code_officiel (basé sur le référentiel 6e)
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from html import escape
import time
import re

from backend.models.exercise_models import (
    ExerciseGenerateRequest,
    ExerciseGenerateResponse,
    ErrorDetail
)
from backend.models.math_models import MathExerciseType
from backend.services.curriculum_service import curriculum_service
from backend.services.math_generation_service import MathGenerationService
from backend.services.geometry_render_service import GeometryRenderService
from curriculum.loader import get_chapter_by_official_code, CurriculumChapter
# P0 - SUPPRESSION IMPORTS LEGACY : GM07/GM08 gérés par pipeline normal
# from backend.services.gm07_handler import is_gm07_request, generate_gm07_exercise, generate_gm07_batch
# from backend.services.gm08_handler import is_gm08_request, generate_gm08_exercise, generate_gm08_batch
from backend.services.tests_dyn_handler import is_tests_dyn_request, generate_tests_dyn_exercise, generate_tests_dyn_batch, get_available_generators
from backend.generators.factory import GeneratorFactory  # P0.3 - Dispatch premium générique
from backend.services.template_renderer import render_template  # P0.3 - Rendu HTML templates
from backend.services.generator_template_service import get_template_service  # P1 - Templates DB
from logger import get_logger
from backend.observability import (
    get_request_context,
    get_logger as get_obs_logger,
    safe_random_choice,
    safe_randrange,
    ensure_request_id,
    set_request_context,
)

logger = get_logger()
obs_logger = get_obs_logger('PIPELINE')

router = APIRouter()

# ============================================================================
# P0 - HELPER PIPELINE SIMPLIFIÉ : DYNAMIC → STATIC fallback
# ============================================================================

async def generate_exercise_with_fallback(
    chapter_code: str,
    exercise_service,
    request: ExerciseGenerateRequest,
    ctx: dict,
    request_start: float
) -> dict:
    """
    Pipeline simplifié P0 : Essaie DYNAMIC, fallback STATIC si échec.
    
    Returns:
        Exercice généré (dynamique ou statique)
    
    Raises:
        HTTPException si aucun exercice disponible
    """
    from backend.services.tests_dyn_handler import format_dynamic_exercise
    
    # 1. Essayer DYNAMIC d'abord
    try:
        exercises = await exercise_service.get_exercises(
            chapter_code=chapter_code,
            offer=request.offer if hasattr(request, 'offer') else None,
            difficulty=request.difficulte if hasattr(request, 'difficulte') else None
        )
        dynamic_exercises = [ex for ex in exercises if ex.get("is_dynamic") is True]
        
        if len(dynamic_exercises) > 0:
            selected_exercise = safe_random_choice(dynamic_exercises, ctx, obs_logger)
            timestamp = int(time.time() * 1000)
            dyn_exercise = format_dynamic_exercise(
                exercise_template=selected_exercise,
                timestamp=timestamp,
                seed=request.seed
            )
            
            duration_ms = int((time.time() - request_start) * 1000)
            obs_logger.info(
                "event=dynamic_generated",
                event="dynamic_generated",
                outcome="success",
                duration_ms=duration_ms,
                exercise_id=selected_exercise.get('id'),
                generator_key=selected_exercise.get('generator_key'),
                **ctx
            )
            logger.info(
                f"[P0] ✅ Exercice DYNAMIQUE généré: "
                f"chapter={chapter_code}, id={selected_exercise.get('id')}, "
                f"generator={selected_exercise.get('generator_key')}"
            )
            return dyn_exercise
    
    except Exception as e:
        logger.warning(f"[P0] Erreur génération DYNAMIC pour {chapter_code}: {e}. Fallback STATIC.")
        obs_logger.warning(
            "event=dynamic_failed",
            event="dynamic_failed",
            outcome="fallback",
            reason="exception",
            exception_type=type(e).__name__,
            **ctx
        )
    
    # 2. Fallback STATIC
    try:
        exercises = await exercise_service.get_exercises(
            chapter_code=chapter_code,
            offer=request.offer if hasattr(request, 'offer') else None,
            difficulty=request.difficulte if hasattr(request, 'difficulte') else None
        )
        static_exercises = [ex for ex in exercises if ex.get("is_dynamic") is not True]
        
        if len(static_exercises) > 0:
            selected_static = safe_random_choice(static_exercises, ctx, obs_logger)
            timestamp = int(time.time() * 1000)
            
            # Récupérer le chapitre pour les métadonnées
            curriculum_chapter = get_chapter_by_official_code(chapter_code)
            
            static_exercise = {
                "id_exercice": f"static_{chapter_code}_{selected_static.get('id')}_{timestamp}",
                "niveau": curriculum_chapter.niveau if curriculum_chapter else "6e",
                "chapitre": curriculum_chapter.libelle if curriculum_chapter else chapter_code,
                "enonce_html": selected_static.get("enonce_html") or "",
                "solution_html": selected_static.get("solution_html") or "",
                "needs_svg": selected_static.get("needs_svg") or False,
                "exercise_type": selected_static.get("exercise_type"),
                "pdf_token": f"static_{chapter_code}_{selected_static.get('id')}_{timestamp}",
                "metadata": {
                    "offer": selected_static.get("offer"),
                    "difficulty": selected_static.get("difficulty"),
                    "source": "admin_exercises_static",
                    "is_fallback": True,
                    "fallback_reason": "dynamic_unavailable"
                }
            }
            
            duration_ms = int((time.time() - request_start) * 1000)
            obs_logger.info(
                "event=static_fallback_used",
                event="static_fallback_used",
                outcome="success",
                duration_ms=duration_ms,
                exercise_id=selected_static.get('id'),
                **ctx
            )
            logger.info(
                f"[P0] ✅ Exercice STATIQUE (fallback): "
                f"chapter={chapter_code}, id={selected_static.get('id')}"
            )
            return static_exercise
    
    except Exception as e:
        logger.error(f"[P0] Erreur fallback STATIC pour {chapter_code}: {e}")
        obs_logger.error(
            "event=static_fallback_failed",
            event="static_fallback_failed",
            outcome="error",
            exception_type=type(e).__name__,
            **ctx
        )
    
    # 3. Aucun exercice disponible
    raise HTTPException(
        status_code=422,
        detail={
            "error_code": "NO_EXERCISE_AVAILABLE",
            "error": "no_exercise_available",
            "message": f"Aucun exercice disponible pour le chapitre '{chapter_code}' avec les critères demandés.",
            "chapter_code": chapter_code,
            "hint": "Vérifiez que des exercices existent en DB pour ce chapitre."
        }
    )

# ============================================================================
# INSTANCES GLOBALES DES SERVICES (V1-BE-002-FIX: Performance)
# Instanciation unique pour éviter de recréer les services à chaque requête
# ============================================================================

_math_service = MathGenerationService()
_geom_service = GeometryRenderService()


# ============================================================================
# MODÈLES POUR L'ENDPOINT BATCH GM07
# ============================================================================

class GM07BatchRequest(BaseModel):
    """Request model pour le batch GM07"""
    code_officiel: str = Field(default="6e_GM07", description="Code officiel (doit être 6e_GM07)")
    difficulte: Optional[str] = Field(default=None, description="facile, moyen, difficile")
    offer: Optional[str] = Field(default="free", description="free ou pro")
    nb_exercices: int = Field(default=1, ge=1, le=20, description="Nombre d'exercices (1-20)")
    seed: Optional[int] = Field(default=None, description="Seed pour reproductibilité")


class GM07BatchResponse(BaseModel):
    """Response model pour le batch GM07"""
    exercises: List[dict] = Field(description="Liste des exercices générés")
    batch_metadata: dict = Field(description="Métadonnées du batch")


# ============================================================================
# MODÈLES POUR L'ENDPOINT BATCH GM08
# ============================================================================

class GM08BatchRequest(BaseModel):
    """Request model pour le batch GM08"""
    code_officiel: str = Field(default="6e_GM08", description="Code officiel (doit être 6e_GM08)")
    difficulte: Optional[str] = Field(default=None, description="facile, moyen, difficile")
    offer: Optional[str] = Field(default="free", description="free ou pro")
    nb_exercices: int = Field(default=1, ge=1, le=20, description="Nombre d'exercices (1-20)")
    seed: Optional[int] = Field(default=None, description="Seed pour reproductibilité")


class GM08BatchResponse(BaseModel):
    """Response model pour le batch GM08"""
    exercises: List[dict] = Field(description="Liste des exercices générés")
    batch_metadata: dict = Field(description="Métadonnées du batch")


# ============================================================================
# MODÈLES POUR L'ENDPOINT BATCH TESTS_DYN (Exercices Dynamiques)
# ============================================================================

class TestsDynBatchRequest(BaseModel):
    """Request model pour le batch TESTS_DYN (dynamique)"""
    code_officiel: str = Field(default="6e_TESTS_DYN", description="Code officiel")
    difficulte: Optional[str] = Field(default=None, description="facile, moyen, difficile")
    offer: Optional[str] = Field(default="free", description="free ou pro")
    nb_exercices: int = Field(default=1, ge=1, le=20, description="Nombre d'exercices (1-20)")
    seed: Optional[int] = Field(default=None, description="Seed pour reproductibilité")


class TestsDynBatchResponse(BaseModel):
    """Response model pour le batch TESTS_DYN"""
    exercises: List[dict] = Field(description="Liste des exercices générés dynamiquement")
    batch_metadata: dict = Field(description="Métadonnées du batch")


# ============================================================================
# ENDPOINTS BATCH DÉDIÉS GM07 / GM08 / TESTS_DYN
# ============================================================================

@router.post("/generate/batch/tests_dyn", response_model=TestsDynBatchResponse, tags=["Dynamic"])
async def generate_tests_dyn_batch_endpoint(request: TestsDynBatchRequest):
    """
    Génère un lot d'exercices DYNAMIQUES (templates + générateur THALES_V1).
    
    **Comportement:**
    - Les exercices sont générés à la volée avec des valeurs différentes
    - Chaque appel avec un seed différent produit des exercices différents
    - Le même seed reproduit exactement les mêmes exercices
    
    **Générateur THALES_V1:**
    - Agrandissements et réductions de figures géométriques
    - Variables: coefficient, dimensions initiales/finales
    - SVG générés dynamiquement pour chaque exercice
    """
    logger.info(f"🎲 TESTS_DYN Batch Request: offer={request.offer}, difficulty={request.difficulte}, count={request.nb_exercices}, seed={request.seed}")
    
    # Générer le batch dynamique
    exercises, batch_meta = generate_tests_dyn_batch(
        offer=request.offer,
        difficulty=request.difficulte,
        count=request.nb_exercices,
        seed=request.seed
    )
    
    if not exercises:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "no_exercises_found",
                "message": "Aucun exercice disponible pour les filtres sélectionnés.",
                "batch_metadata": batch_meta
            }
        )
    
    logger.info(f"✅ TESTS_DYN Batch generated: {len(exercises)} dynamic exercises")
    
    return TestsDynBatchResponse(
        exercises=exercises,
        batch_metadata=batch_meta
    )


@router.get("/generators", tags=["Dynamic"])
async def list_available_generators():
    """
    Liste les générateurs dynamiques disponibles.
    
    **Générateurs actuels:**
    - THALES_V1: Agrandissements/réductions de figures (6e)
    """
    generators = get_available_generators()
    return {
        "generators": generators,
        "count": len(generators),
        "details": {
            "THALES_V1": {
                "name": "Agrandissements et Réductions",
                "niveau": "6e",
                "description": "Génère des exercices sur les transformations de figures géométriques",
                "figure_types": ["carre", "rectangle", "triangle"],
                "difficulties": ["facile", "moyen", "difficile"]
            }
        }
    }


@router.post("/generate/batch/gm07", response_model=GM07BatchResponse, tags=["GM07"])
async def generate_gm07_batch_endpoint(request: GM07BatchRequest):
    """
    Génère un lot d'exercices GM07 SANS DOUBLONS.
    
    **Comportement produit:**
    - Si pool_size >= N: retourne exactement N exercices UNIQUES
    - Si pool_size < N: retourne pool_size exercices avec metadata.warning
    - JAMAIS de doublons
    
    **Exemple de réponse:**
    ```json
    {
        "exercises": [...],
        "batch_metadata": {
            "requested": 5,
            "returned": 4,
            "available": 4,
            "warning": "Seulement 4 exercices disponibles pour difficulté 'facile' et offre 'free'."
        }
    }
    ```
    """
    # Vérifier que c'est bien GM07
    if request.code_officiel.upper() != "6E_GM07":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_chapter",
                "message": "Cet endpoint est réservé au chapitre GM07",
                "hint": "Utilisez code_officiel='6e_GM07'"
            }
        )
    
    logger.info(f"🎯 GM07 Batch Request: offer={request.offer}, difficulty={request.difficulte}, count={request.nb_exercices}")
    
    # Générer le batch
    exercises, batch_meta = generate_gm07_batch(
        offer=request.offer,
        difficulty=request.difficulte,
        count=request.nb_exercices,
        seed=request.seed
    )
    
    if not exercises:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "no_exercises_found",
                "message": batch_meta.get("warning", "Aucun exercice disponible"),
                "batch_metadata": batch_meta
            }
        )
    
    # Log le résultat
    warning = batch_meta.get("warning", "")
    logger.info(f"✅ GM07 Batch generated: {len(exercises)} exercises. {warning}")
    
    return GM07BatchResponse(
        exercises=exercises,
        batch_metadata=batch_meta
    )


@router.post("/generate/batch/gm08", response_model=GM08BatchResponse, tags=["GM08"])
async def generate_gm08_batch_endpoint(request: GM08BatchRequest):
    """
    Génère un lot d'exercices GM08 SANS DOUBLONS.
    
    **Thème:** Grandeurs et Mesures - Longueurs, Périmètres
    
    **Comportement produit:**
    - Si pool_size >= N: retourne exactement N exercices UNIQUES
    - Si pool_size < N: retourne pool_size exercices avec metadata.warning
    - JAMAIS de doublons
    
    **Exemple de réponse:**
    ```json
    {
        "exercises": [...],
        "batch_metadata": {
            "requested": 5,
            "returned": 4,
            "available": 4,
            "warning": "Seulement 4 exercices disponibles pour difficulté 'facile' et offre 'free'."
        }
    }
    ```
    """
    # Vérifier que c'est bien GM08
    if request.code_officiel.upper() != "6E_GM08":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_chapter",
                "message": "Cet endpoint est réservé au chapitre GM08",
                "hint": "Utilisez code_officiel='6e_GM08'"
            }
        )
    
    logger.info(f"🎯 GM08 Batch Request: offer={request.offer}, difficulty={request.difficulte}, count={request.nb_exercices}")
    
    # Générer le batch
    exercises, batch_meta = generate_gm08_batch(
        offer=request.offer,
        difficulty=request.difficulte,
        count=request.nb_exercices,
        seed=request.seed
    )
    
    if not exercises:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "no_exercises_found",
                "message": batch_meta.get("warning", "Aucun exercice disponible"),
                "batch_metadata": batch_meta
            }
        )
    
    # Log le résultat
    warning = batch_meta.get("warning", "")
    logger.info(f"✅ GM08 Batch generated: {len(exercises)} exercises. {warning}")
    
    return GM08BatchResponse(
        exercises=exercises,
        batch_metadata=batch_meta
    )


def generate_exercise_id(niveau: str, chapitre: str) -> str:
    """
    Génère un identifiant unique pour l'exercice
    
    Format: ex_{niveau}_{chapitre_slug}_{timestamp}
    Exemple: ex_5e_symetrie-axiale_1702401234
    
    Args:
        niveau: Niveau scolaire
        chapitre: Nom du chapitre
    
    Returns:
        Identifiant unique
    """
    # Convertir le chapitre en slug (minuscules, tirets)
    chapitre_slug = re.sub(r'[^a-z0-9]+', '-', chapitre.lower()).strip('-')
    
    # Timestamp pour unicité
    timestamp = int(time.time())
    
    return f"ex_{niveau}_{chapitre_slug}_{timestamp}"


def build_enonce_html(enonce: str, svg: Optional[str] = None) -> str:
    """
    Construit l'énoncé HTML à partir de l'énoncé texte et du SVG
    
    NOTE: L'énoncé n'est PAS échappé car il peut contenir du HTML valide
    (tableaux de proportionnalité, etc.) généré par notre code interne.
    
    Args:
        enonce: Énoncé textuel (peut contenir du HTML de tableaux, etc.)
        svg: SVG optionnel (non échappé car généré par notre code interne)
    
    Returns:
        HTML de l'énoncé
    """
    # NOTE: On n'échappe PAS l'énoncé car il peut contenir du HTML valide
    # (tableaux, formules, etc.) généré par notre propre code backend.
    # Ce HTML est de confiance car il provient de math_generation_service.py
    
    html = f"<div class='exercise-enonce'><p>{enonce}</p>"
    
    # Le SVG n'est PAS échappé car il est généré par notre code interne de confiance
    if svg:
        html += f"<div class='exercise-figure'>{svg}</div>"
    
    html += "</div>"
    
    return html


def build_solution_html(etapes: list, resultat_final: str, svg_correction: Optional[str] = None) -> str:
    """
    Construit la solution HTML à partir des étapes et du résultat
    
    NOTE: Les étapes et le résultat ne sont PAS échappés car ils peuvent
    contenir des formules LaTeX ou du HTML généré par notre code interne.
    
    Args:
        etapes: Liste des étapes de résolution (peuvent contenir LaTeX/HTML)
        resultat_final: Résultat final (peut contenir LaTeX/HTML)
        svg_correction: SVG de correction optionnel (non échappé car généré par notre code interne)
    
    Returns:
        HTML de la solution
    """
    html = "<div class='exercise-solution'>"
    html += "<p><strong>Solution :</strong></p>"
    
    if etapes:
        html += "<ol>"
        for etape in etapes:
            # NOTE: On n'échappe PAS les étapes car elles peuvent contenir
            # des formules LaTeX (\\frac{}{}) ou du HTML de confiance
            html += f"<li>{etape}</li>"
        html += "</ol>"
    
    # NOTE: On n'échappe PAS le résultat car il peut contenir du LaTeX
    html += f"<p><strong>Résultat final :</strong> {resultat_final}</p>"
    
    # Le SVG n'est PAS échappé car il est généré par notre code interne de confiance
    if svg_correction:
        html += f"<div class='exercise-figure-correction'>{svg_correction}</div>"
    
    html += "</div>"
    
    return html


def _build_fallback_enonce(spec, chapitre: str) -> str:
    """
    Génère un énoncé pédagogique de fallback basé sur les paramètres de l'exercice
    
    Args:
        spec: Spécification de l'exercice (MathExerciseSpec)
        chapitre: Nom du chapitre
    
    Returns:
        Énoncé lisible pour l'élève
    """
    params = spec.parametres or {}
    
    # 1. Si expression mathématique présente, l'utiliser
    expression = params.get("expression", "")
    if expression:
        return f"Calculer : {expression}"
    
    # 2. Fallback spécifique par type d'exercice
    type_exercice = str(spec.type_exercice).lower() if spec.type_exercice else ""
    
    # Fractions
    if "fractions" in chapitre.lower() or "fraction" in type_exercice:
        frac1 = params.get("fraction1", "")
        frac2 = params.get("fraction2", "")
        operation = params.get("operation", "+")
        if frac1 and frac2:
            op_text = "la somme" if operation == "+" else "la différence"
            return f"Calculer {op_text} des fractions {frac1} et {frac2}. Donner le résultat sous forme de fraction irréductible."
    
    # Équations
    if "equation" in type_exercice or "équation" in chapitre.lower():
        equation = params.get("equation", "")
        if equation:
            return f"Résoudre l'équation suivante : {equation}"
    
    # Calculs décimaux
    if "decimaux" in type_exercice or "décimaux" in chapitre.lower():
        a = params.get("a", "")
        b = params.get("b", "")
        if a and b:
            return f"Effectuer le calcul suivant : {a} et {b}"
    
    # Géométrie - triangles
    if "triangle" in type_exercice or "triangle" in chapitre.lower():
        if params.get("points"):
            return f"Soit le triangle {params.get('points', 'ABC')}. Calculer les mesures demandées."
    
    # Périmètre/Aire
    if "perimetre" in type_exercice or "aire" in type_exercice:
        figure = params.get("figure", params.get("type_figure", "figure"))
        return f"Calculer le périmètre et/ou l'aire de la {figure} donnée."
    
    # Volume - CORRIGÉ P0-001: Toujours inclure les dimensions dans l'énoncé
    if "volume" in type_exercice:
        solide = params.get("solide", params.get("type_solide", "solide"))
        
        # Cube : inclure l'arête
        if solide == "cube":
            arete = params.get("arete", params.get("cote", ""))
            if arete:
                return f"Calculer le volume d'un cube d'arête {arete} cm."
        
        # Pavé droit : inclure les 3 dimensions
        elif solide == "pave" or solide == "pavé" or solide == "pave_droit":
            longueur = params.get("longueur", params.get("L", ""))
            largeur = params.get("largeur", params.get("l", ""))
            hauteur = params.get("hauteur", params.get("h", ""))
            if longueur and largeur and hauteur:
                return f"Calculer le volume d'un pavé droit de dimensions {longueur} cm × {largeur} cm × {hauteur} cm."
        
        # Cylindre : inclure rayon et hauteur
        elif solide == "cylindre":
            rayon = params.get("rayon", params.get("r", ""))
            hauteur = params.get("hauteur", params.get("h", ""))
            if rayon and hauteur:
                return f"Calculer le volume d'un cylindre de rayon {rayon} cm et de hauteur {hauteur} cm."
        
        # Prisme : inclure base et hauteur
        elif solide == "prisme":
            base_longueur = params.get("base_longueur", "")
            base_largeur = params.get("base_largeur", "")
            hauteur = params.get("hauteur", "")
            if base_longueur and base_largeur and hauteur:
                return f"Calculer le volume d'un prisme droit à base rectangulaire de dimensions {base_longueur} cm × {base_largeur} cm et de hauteur {hauteur} cm."
            elif hauteur:
                aire_base = params.get("aire_base", "")
                if aire_base:
                    return f"Calculer le volume d'un prisme d'aire de base {aire_base} cm² et de hauteur {hauteur} cm."
        
        # Fallback avec dimensions si disponibles
        dimensions = []
        for key, label in [("longueur", "L"), ("largeur", "l"), ("hauteur", "h"), 
                           ("arete", "arête"), ("rayon", "r"), ("base_longueur", "base L"),
                           ("base_largeur", "base l")]:
            if key in params and params[key]:
                dimensions.append(f"{label}={params[key]} cm")
        
        if dimensions:
            dims_str = ", ".join(dimensions)
            return f"Calculer le volume du {solide} ({dims_str})."
        
        return f"Calculer le volume du {solide}."
    
    # Probabilités
    if "probabilite" in type_exercice:
        return "Calculer la probabilité demandée."
    
    # Statistiques
    if "statistique" in type_exercice:
        return "Analyser les données statistiques ci-dessous et répondre aux questions."
    
    # 3. Fallback générique amélioré
    # Essayer de construire quelque chose d'utile avec les paramètres disponibles
    if params:
        # Chercher des indices dans les clés des paramètres
        param_keys = list(params.keys())
        if any("nombre" in k.lower() for k in param_keys):
            return "Effectuer les calculs demandés sur les nombres suivants."
        if any("point" in k.lower() for k in param_keys):
            return "Réaliser la construction géométrique demandée."
    
    # 4. Dernier recours : message générique mais informatif
    return f"Exercice de {chapitre}. Répondre aux questions ci-dessous."


@router.post(
    "/generate",
    response_model=ExerciseGenerateResponse,
    responses={
        422: {
            "model": ErrorDetail,
            "description": "Niveau, chapitre ou code_officiel invalide"
        },
        500: {
            "description": "Erreur lors de la génération de l'exercice"
        }
    },
    summary="Générer un exercice mathématique",
    description="""
    Génère un exercice personnalisé avec énoncé, figure géométrique et solution.
    
    **Deux modes de fonctionnement :**
    
    1. **Mode legacy** : Utiliser `niveau` + `chapitre`
       ```json
       {"niveau": "6e", "chapitre": "Fractions", "difficulte": "moyen"}
       ```
    
    2. **Mode officiel** : Utiliser `code_officiel` (référentiel 6e)
       ```json
       {"code_officiel": "6e_N08", "difficulte": "moyen"}
       ```
    
    Si `code_officiel` est fourni, il a priorité sur `chapitre`.
    """
)
async def generate_exercise(request: ExerciseGenerateRequest):
    """
    Génère un exercice mathématique complet.
    
    Args:
        request: Requête avec niveau/chapitre (legacy) ou code_officiel (nouveau)
    
    Returns:
        Exercice généré avec énoncé HTML, SVG, solution et pdf_token
    """
    request_start = time.time()
    ensure_request_id()
    set_request_context(
        chapter_code=getattr(request, 'code_officiel', None),
        niveau=getattr(request, 'niveau', None),
        chapitre=getattr(request, 'chapitre', None),
        difficulty=getattr(request, 'difficulte', None),
        offer=getattr(request, 'offer', None),
        seed=getattr(request, 'seed', None),
    )
    obs_logger.info(
        "event=request_in",
        event="request_in",
        outcome="in_progress",
        chapter_code=getattr(request, 'code_officiel', None),
        niveau=getattr(request, 'niveau', None),
        difficulty=getattr(request, 'difficulte', None),
        offer=getattr(request, 'offer', None),
    )
    
    # ============================================================================
    # P0 - SUPPRESSION INTERCEPTS LEGACY GM07/GM08
    # ============================================================================
    # Les exercices GM07/GM08 sont maintenant en DB (migration P3.2).
    # Ils sont gérés par le pipeline normal (DYNAMIC → STATIC fallback).
    # Plus besoin d'intercepts hardcodés.
    # ============================================================================
    
    # ============================================================================
    # TESTS_DYN INTERCEPT: Chapitre de test pour exercices dynamiques
    # ============================================================================
    
    if is_tests_dyn_request(request.code_officiel):
        nb = request.nb_exercices if hasattr(request, 'nb_exercices') else 1
        logger.info(f"🎲 TESTS_DYN Request intercepted: offer={request.offer}, difficulty={request.difficulte}, count={nb}")
        
        # Si on demande 1 seul exercice
        if nb == 1:
            dyn_exercise = generate_tests_dyn_exercise(
                offer=request.offer,
                difficulty=request.difficulte,
                seed=request.seed
            )
            
            if not dyn_exercise:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": "NO_EXERCISE_AVAILABLE",
                        "error": "no_tests_dyn_exercise_found",
                        "message": f"Aucun exercice disponible pour offer='{request.offer}' et difficulty='{request.difficulte}'. Le fallback vers 'free' a été tenté mais aucun exercice n'a été trouvé.",
                        "hint": "Vérifiez les filtres (difficulty) ou utilisez /generate/batch/tests_dyn pour les lots"
                    }
                )
            
            logger.info(f"✅ TESTS_DYN Exercise generated: id={dyn_exercise['id_exercice']}, "
                       f"generator={dyn_exercise['metadata'].get('generator_key')}")
            
            return dyn_exercise
        
        # Si on demande plusieurs exercices via cet endpoint
        exercises, batch_meta = generate_tests_dyn_batch(
            offer=request.offer,
            difficulty=request.difficulte,
            count=nb,
            seed=request.seed
        )
        
        if not exercises:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "no_tests_dyn_exercise_found",
                    "message": "Aucun exercice dynamique trouvé",
                    "hint": "Utilisez /generate/batch/tests_dyn pour les lots"
                }
            )
        
        logger.info(f"✅ TESTS_DYN Batch via /generate: {len(exercises)} exercises")
        
        return exercises[0]
    
    # ============================================================================
    # 0. RÉSOLUTION DU MODE (code_officiel vs legacy) - Pour autres chapitres
    # ============================================================================
    
    curriculum_chapter: Optional[CurriculumChapter] = None
    exercise_types_override: Optional[List[MathExerciseType]] = None
    filtered_premium_generators: List[str] = []  # P2.1 - Track des générateurs premium exclus
    
    if request.code_officiel:
        # Mode code_officiel : chercher dans le référentiel
        curriculum_chapter = get_chapter_by_official_code(request.code_officiel)
        
        if not curriculum_chapter:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "code_officiel_invalide",
                    "message": f"Le code officiel '{request.code_officiel}' n'existe pas dans le référentiel.",
                    "hint": "Utilisez un code au format 6e_N01, 6e_G01, etc."
                }
            )
        
        # Vérifier si c'est un chapitre de test (interdit en mode public)
        from curriculum.loader import is_test_chapter, should_show_test_chapters
        if is_test_chapter(request.code_officiel) and not should_show_test_chapters():
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "TEST_CHAPTER_FORBIDDEN",
                    "error": "test_chapter_forbidden",
                    "message": f"Le code officiel '{request.code_officiel}' est un chapitre de test et n'est pas accessible en mode public.",
                    "hint": "Les chapitres de test sont réservés au développement. Activez SHOW_TEST_CHAPTERS=true pour y accéder.",
                    "context": {
                        "code_officiel": request.code_officiel,
                        "is_test_chapter": True
                    }
                }
            )
        
        # Extraire les informations du référentiel
        request.niveau = curriculum_chapter.niveau
        # Toujours utiliser le libellé/officiel comme chapitre lisible, ne pas basculer sur un alias backend
        request.chapitre = curriculum_chapter.libelle or curriculum_chapter.code_officiel
        
        # ============================================================================
        # DÉTECTION CHAPITRES DE TEST - Routage déterministe pour chapitres de test
        # ============================================================================
        # Chapitres de test connus qui utilisent le pipeline MIXED (exercices dynamiques)
        TEST_CHAPTER_CODES = ["6E_AA_TEST", "6E_TESTS_DYN", "6E_MIXED_QA"]
        normalized_code = request.code_officiel.upper().replace("-", "_")
        
        if normalized_code in TEST_CHAPTER_CODES:
            # Chapitre de test connu : utiliser directement le pipeline MIXED
            logger.info(f"[TEST_CHAPTER] Chapitre de test détecté: {request.code_officiel} → pipeline=MIXED")
            pipeline_mode = "MIXED"
        else:
            # Vérifier si c'est un chapitre de test inconnu (pattern AA_* ou *_TEST)
            if "_AA_" in normalized_code or normalized_code.endswith("_TEST") or "_TESTS_" in normalized_code:
                # Chapitre de test inconnu : retourner 422 avec hint clair
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": "TEST_CHAPTER_UNKNOWN",
                        "error": "test_chapter_unknown",
                        "message": f"Le code officiel '{request.code_officiel}' semble être un chapitre de test mais n'est pas configuré.",
                        "hint": f"Chapitres de test connus: {', '.join(TEST_CHAPTER_CODES)}. Ajoutez '{normalized_code}' à la liste TEST_CHAPTER_CODES dans exercises_routes.py si c'est un nouveau chapitre de test.",
                        "context": {
                            "code_officiel": request.code_officiel,
                            "normalized_code": normalized_code,
                            "known_test_chapters": TEST_CHAPTER_CODES
                        }
                    }
                )
            
            # ============================================================================
            # P0: PIPELINE EXPLICITE - Routage selon pipeline du chapitre
            # ============================================================================
            # Si le chapitre a un pipeline défini, l'utiliser explicitement.
            # Sinon, fallback sur l'ancien comportement (détection automatique).
            
            pipeline_mode = curriculum_chapter.pipeline if hasattr(curriculum_chapter, 'pipeline') and curriculum_chapter.pipeline else None
        
        if pipeline_mode:
            logger.info(f"[PIPELINE] Chapitre {request.code_officiel} → pipeline={pipeline_mode} (explicite)")
            
            from server import db
            from backend.services.curriculum_sync_service import get_curriculum_sync_service
            from backend.services.exercise_persistence_service import get_exercise_persistence_service
            from backend.services.tests_dyn_handler import format_dynamic_exercise
            
            sync_service = get_curriculum_sync_service(db)
            exercise_service = get_exercise_persistence_service(db)
            
            # Normaliser le code_officiel pour la recherche
            chapter_code_for_db = request.code_officiel.upper().replace("-", "_")
            
            if pipeline_mode == "TEMPLATE":
                # Pipeline dynamique uniquement
                ctx = get_request_context()
                ctx.update({
                    'pipeline': 'TEMPLATE',
                    'chapter_code': chapter_code_for_db,
                })
                obs_logger.info(
                    "event=mixed_decision",
                    event="mixed_decision",
                    outcome="in_progress",
                    chosen_path="TEMPLATE",
                    chapter=chapter_code_for_db,
                    **ctx
                )
                try:
                    has_exercises = await sync_service.has_exercises_in_db(chapter_code_for_db)
                    if not has_exercises:
                        raise HTTPException(
                            status_code=422,
                            detail={
                                "error_code": "TEMPLATE_PIPELINE_NO_DYNAMIC_EXERCISES",
                                "error": "template_pipeline_no_exercises",
                                "message": (
                                    f"Le chapitre '{request.code_officiel}' est configuré avec pipeline='TEMPLATE' "
                                    f"mais aucun exercice dynamique n'existe en DB pour ce chapitre."
                                ),
                                "chapter_code": request.code_officiel,
                                "pipeline": "TEMPLATE",
                                "hint": "Créez au moins un exercice dynamique pour ce chapitre ou changez le pipeline à 'SPEC' ou 'MIXED'."
                            }
                        )
                    
                    exercises = await exercise_service.get_exercises(
                        chapter_code=chapter_code_for_db,
                        offer=request.offer if hasattr(request, 'offer') else None,
                        difficulty=request.difficulte if hasattr(request, 'difficulte') else None
                    )
                    dynamic_exercises = [ex for ex in exercises if ex.get("is_dynamic") is True]
                    
                    if len(dynamic_exercises) == 0:
                        raise HTTPException(
                            status_code=422,
                            detail={
                                "error_code": "TEMPLATE_PIPELINE_NO_DYNAMIC_EXERCISES",
                                "error": "template_pipeline_no_dynamic_exercises",
                                "message": (
                                    f"Le chapitre '{request.code_officiel}' est configuré avec pipeline='TEMPLATE' "
                                    f"mais aucun exercice dynamique (is_dynamic=true) n'existe en DB pour ce chapitre."
                                ),
                                "chapter_code": request.code_officiel,
                                "pipeline": "TEMPLATE",
                                "hint": "Créez au moins un exercice dynamique pour ce chapitre ou changez le pipeline à 'SPEC' ou 'MIXED'."
                            }
                        )
                    
                    # Sélectionner un exercice dynamique aléatoire (avec seed pour reproductibilité)
                    selected_exercise = safe_random_choice(dynamic_exercises, ctx, obs_logger)
                    
                    # Générer l'exercice dynamique
                    timestamp = int(time.time() * 1000)
                    dyn_exercise = format_dynamic_exercise(
                        exercise_template=selected_exercise,
                        timestamp=timestamp,
                        seed=request.seed
                    )
                    
                    duration_ms = int((time.time() - request_start) * 1000)
                    obs_logger.info(
                        "event=request_complete",
                        event="request_complete",
                        outcome="success",
                        duration_ms=duration_ms,
                        chosen_path="TEMPLATE",
                        exercise_id=selected_exercise.get('id'),
                        generator_key=selected_exercise.get('generator_key'),
                        **ctx
                    )
                    logger.info(
                        f"[PIPELINE] ✅ Exercice dynamique généré (TEMPLATE): "
                        f"chapter_code={chapter_code_for_db}, exercise_id={selected_exercise.get('id')}, "
                        f"generator_key={selected_exercise.get('generator_key')}"
                    )
                    
                    return dyn_exercise
                except HTTPException as e:
                    duration_ms = int((time.time() - request_start) * 1000)
                    obs_logger.error(
                        "event=request_error",
                        event="request_error",
                        outcome="error",
                        duration_ms=duration_ms,
                        reason="http_exception",
                        error_code=e.detail.get('error_code', None) if isinstance(e.detail, dict) else None,
                        **ctx
                    )
                    raise
                except Exception as e:
                    duration_ms = int((time.time() - request_start) * 1000)
                    obs_logger.error(
                        "event=request_exception",
                        event="request_exception",
                        outcome="error",
                        duration_ms=duration_ms,
                        reason="template_pipeline_error",
                        exception_type=type(e).__name__,
                        **ctx,
                        exc_info=True
                    )
                    logger.error(
                        f"[PIPELINE] Erreur pipeline TEMPLATE pour {chapter_code_for_db}: {e}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail={
                            "error_code": "TEMPLATE_PIPELINE_ERROR",
                            "error": "template_pipeline_error",
                            "message": f"Erreur lors de la génération avec pipeline TEMPLATE: {str(e)}"
                        }
                    )
            
            elif pipeline_mode == "MIXED":
                # P0 - SIMPLIFICATION : Utiliser le pipeline DYNAMIC → STATIC fallback
                ctx = get_request_context()
                ctx.update({
                    'pipeline': 'MIXED',
                    'chapter_code': chapter_code_for_db,
                })
                obs_logger.info(
                    "event=mixed_decision",
                    event="mixed_decision",
                    outcome="in_progress",
                    chosen_path="MIXED",
                    chapter=chapter_code_for_db,
                    **ctx
                )
                try:
                    # Utiliser le pipeline simplifié : DYNAMIC → STATIC fallback
                    return await generate_exercise_with_fallback(
                        chapter_code=chapter_code_for_db,
                        exercise_service=exercise_service,
                        request=request,
                        ctx=ctx,
                        request_start=request_start
                    )
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"[P0] Erreur pipeline MIXED pour {chapter_code_for_db}: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail={
                            "error_code": "MIXED_PIPELINE_ERROR",
                            "error": "mixed_pipeline_error",
                            "message": f"Erreur lors de la génération avec pipeline MIXED: {str(e)}"
                        }
                    )
                
                # ANCIEN CODE MIXED (désactivé - trop complexe)
                # try:
                    has_exercises = await sync_service.has_exercises_in_db(chapter_code_for_db)
                    if has_exercises:
                        # Récupérer les exercices avec filtres
                        exercises = await exercise_service.get_exercises(
                            chapter_code=chapter_code_for_db,
                            offer=request.offer if hasattr(request, 'offer') else None,
                            difficulty=request.difficulte if hasattr(request, 'difficulte') else None
                        )
                        dynamic_exercises = [ex for ex in exercises if ex.get("is_dynamic") is True]
                        static_exercises = [ex for ex in exercises if ex.get("is_dynamic") is not True]
                        
                        # Log du pool filtré pour diagnostic
                        obs_logger.debug(
                            "event=mixed_pool_filtered",
                            event="mixed_pool_filtered",
                            outcome="in_progress",
                            filters_applied={
                                "offer": request.offer if hasattr(request, 'offer') else None,
                                "difficulty": request.difficulte if hasattr(request, 'difficulte') else None
                            },
                            dynamic_count=len(dynamic_exercises),
                            static_count=len(static_exercises),
                            total_count=len(exercises),
                            **ctx
                        )
                        
                        # Si aucun exercice avec filtres, retenter sans filtres (dégradé)
                        if len(dynamic_exercises) == 0 and len(static_exercises) == 0:
                            obs_logger.warning(
                                "event=mixed_no_filtered_exercises",
                                event="mixed_no_filtered_exercises",
                                outcome="warning",
                                reason="no_exercises_with_filters",
                                filters_applied={
                                    "offer": request.offer if hasattr(request, 'offer') else None,
                                    "difficulty": request.difficulte if hasattr(request, 'difficulte') else None
                                },
                                **ctx
                            )
                            exercises = await exercise_service.get_exercises(
                                chapter_code=chapter_code_for_db,
                                offer=None,
                                difficulty=None
                            )
                            dynamic_exercises = [ex for ex in exercises if ex.get("is_dynamic") is True]
                            static_exercises = [ex for ex in exercises if ex.get("is_dynamic") is not True]
                        # 1) Dyn filtré
                        if len(dynamic_exercises) > 0:
                            selected_exercise = safe_random_choice(dynamic_exercises, ctx, obs_logger)
                            timestamp = int(time.time() * 1000)
                            dyn_exercise = format_dynamic_exercise(
                                exercise_template=selected_exercise,
                                timestamp=timestamp,
                                seed=request.seed
                            )
                            duration_ms = int((time.time() - request_start) * 1000)
                            obs_logger.info(
                                "event=request_complete",
                                event="request_complete",
                                outcome="success",
                                duration_ms=duration_ms,
                                chosen_path="MIXED_dynamic_filtered",
                                exercise_id=selected_exercise.get('id'),
                                **ctx
                            )
                            logger.info(
                                f"[PIPELINE] ✅ Exercice dynamique généré (MIXED, priorité dynamique): "
                                f"chapter_code={chapter_code_for_db}, exercise_id={selected_exercise.get('id')}"
                            )
                            return dyn_exercise
                        
                        # 2) Dyn sans filtre (dégradé)
                        dynamic_all = [ex for ex in exercises if ex.get("is_dynamic") is True]
                        if dynamic_all:
                            obs_logger.warning(
                                "event=fallback",
                                event="fallback",
                                outcome="success",
                                reason="no_filtered_dynamic",
                                pool_size=len(dynamic_all),
                                **ctx
                            )
                            selected_exercise = safe_random_choice(dynamic_all, ctx, obs_logger)
                            timestamp = int(time.time() * 1000)
                            dyn_exercise = format_dynamic_exercise(
                                exercise_template=selected_exercise,
                                timestamp=timestamp,
                                seed=request.seed
                            )
                            dyn_exercise.setdefault("metadata", {}).update({"fallback_filters": True})
                            duration_ms = int((time.time() - request_start) * 1000)
                            obs_logger.info(
                                "event=request_complete",
                                event="request_complete",
                                outcome="success",
                                duration_ms=duration_ms,
                                chosen_path="MIXED_dynamic_degraded",
                                exercise_id=selected_exercise.get('id'),
                                **ctx
                            )
                            logger.info(
                                f"[PIPELINE] ✅ Exercice dynamique généré (MIXED dégradé, sans filtre offer/difficulty): "
                                f"chapter_code={chapter_code_for_db}, exercise_id={selected_exercise.get('id')}"
                            )
                            return dyn_exercise
                        
                        # Pool vide : aucun exercice dynamique disponible
                        obs_logger.error(
                            "event=pool_empty",
                            event="pool_empty",
                            outcome="error",
                            reason="no_dynamic_exercises_available",
                            pool_size=0,
                            **ctx
                        )
                        raise HTTPException(
                            status_code=422,
                            detail={
                                "error_code": "POOL_EMPTY",
                                "error": "pool_empty",
                                "message": f"Aucun exercice dynamique disponible pour ce chapitre avec les critères demandés.",
                                "hint": f"Vérifiez que des exercices dynamiques existent pour le chapitre '{chapter_code_for_db}' avec difficulty='{request.difficulte}' et offer='{request.offer}'. Vous pouvez essayer une autre difficulté ou contacter l'administrateur.",
                                "context": {
                                    "chapter": chapter_code_for_db,
                                    "difficulty": request.difficulte,
                                    "offer": request.offer,
                                    "pipeline": "MIXED"
                                }
                            }
                        )
                        
                        # 3) Statiques filtrés
                        if len(static_exercises) > 0:
                            obs_logger.warning(
                                "event=fallback",
                                event="fallback",
                                outcome="success",
                                reason="no_dynamic_fallback_static",
                                pool_size=len(static_exercises),
                                **ctx
                            )
                            selected_static = safe_random_choice(static_exercises, ctx, obs_logger)
                            timestamp = int(time.time() * 1000)
                            static_exercise = {
                                "id_exercice": f"admin_static_{chapter_code_for_db}_{selected_static.get('id')}_{timestamp}",
                                "niveau": curriculum_chapter.niveau,
                                "chapitre": curriculum_chapter.libelle or curriculum_chapter.code_officiel,
                                "enonce_html": selected_static.get("enonce_html") or "",
                                "solution_html": selected_static.get("solution_html") or "",
                                "needs_svg": selected_static.get("needs_svg") or False,
                                "pdf_token": f"admin_static_{chapter_code_for_db}_{selected_static.get('id')}_{timestamp}",
                                "metadata": {
                                    "offer": selected_static.get("offer"),
                                    "difficulty": selected_static.get("difficulty"),
                                    "source": "admin_exercises_static",
                                    "is_fallback": False
                                }
                            }
                            duration_ms = int((time.time() - request_start) * 1000)
                            obs_logger.info(
                                "event=request_complete",
                                event="request_complete",
                                outcome="success",
                                duration_ms=duration_ms,
                                chosen_path="MIXED_static_fallback",
                                exercise_id=selected_static.get('id'),
                                **ctx
                            )
                            logger.info(
                                f"[PIPELINE] ✅ Exercice statique (admin) généré (MIXED fallback statique): "
                                f"chapter_code={chapter_code_for_db}, exercise_id={selected_static.get('id')}"
                            )
                            return static_exercise
                        
                        # 4) Aucun exo → 422 explicite avec logs détaillés
                        # Récupérer les statistiques pour diagnostic
                        all_exercises = await exercise_service.get_exercises(
                            chapter_code=chapter_code_for_db,
                            offer=None,
                            difficulty=None
                        )
                        all_dynamic = [ex for ex in all_exercises if ex.get("is_dynamic") is True]
                        all_static = [ex for ex in all_exercises if ex.get("is_dynamic") is not True]
                        
                        # Compter par difficulty/offer pour diagnostic
                        by_difficulty = {}
                        by_offer = {}
                        for ex in all_exercises:
                            diff = ex.get("difficulty", "unknown")
                            off = ex.get("offer", "unknown")
                            by_difficulty[diff] = by_difficulty.get(diff, 0) + 1
                            by_offer[off] = by_offer.get(off, 0) + 1
                        
                        obs_logger.error(
                            "event=mixed_no_exercises",
                            event="mixed_no_exercises",
                            outcome="error",
                            reason="list_empty",
                            filters_applied={
                                "offer": request.offer if hasattr(request, 'offer') else None,
                                "difficulty": request.difficulte if hasattr(request, 'difficulte') else None
                            },
                            total_exercises_in_db=len(all_exercises),
                            total_dynamic_in_db=len(all_dynamic),
                            total_static_in_db=len(all_static),
                            by_difficulty=by_difficulty,
                            by_offer=by_offer,
                            **ctx
                        )
                        
                        raise HTTPException(
                            status_code=422,
                            detail={
                                "error_code": "MIXED_PIPELINE_NO_EXERCISES_OR_TYPES",
                                "error": "mixed_pipeline_no_exercises_or_types",
                                "message": (
                                    f"Aucun exercice (dynamique ou statique) pour {chapter_code_for_db} "
                                    f"avec offer='{request.offer}' et difficulte='{request.difficulte}'. "
                                    "Ajoutez un exercice pour ces filtres ou changez de difficulté/offre."
                                ),
                                "chapter_code": chapter_code_for_db,
                                "pipeline": "MIXED",
                                "filters": {
                                    "offer": getattr(request, 'offer', None),
                                    "difficulty": getattr(request, 'difficulte', None)
                                },
                                "diagnostic": {
                                    "total_exercises_in_db": len(all_exercises),
                                    "total_dynamic": len(all_dynamic),
                                    "total_static": len(all_static),
                                    "by_difficulty": by_difficulty,
                                    "by_offer": by_offer
                                }
                            }
                        )
                    
                    # Fallback sur pipeline statique
                    obs_logger.warning(
                        "event=fallback",
                        event="fallback",
                        outcome="in_progress",
                        reason="no_exercises_fallback_static",
                        **ctx
                    )
                    logger.info(
                        f"[PIPELINE] Pipeline MIXED pour {chapter_code_for_db}: pas d'exercices dynamiques, "
                        f"utilisation du pipeline STATIQUE."
                    )
                    # Continue vers pipeline statique (code ci-dessous)
                except Exception as e:
                    obs_logger.warning(
                        "event=fallback",
                        event="fallback",
                        outcome="in_progress",
                        reason="exception_fallback_static",
                        exception_type=type(e).__name__,
                        **ctx
                    )
                    logger.warning(
                        f"[PIPELINE] Erreur vérification exercices dynamiques (MIXED) pour {chapter_code_for_db}: {e}. "
                        f"Fallback sur pipeline STATIQUE."
                    )
                    # Continue vers pipeline statique (code ci-dessous)
            
            elif pipeline_mode == "SPEC":
                # Pipeline statique uniquement - continue vers le code ci-dessous
                ctx = get_request_context()
                ctx.update({
                    'pipeline': 'SPEC',
                    'chapter_code': chapter_code_for_db,
                })
                obs_logger.info(
                    "event=mixed_decision",
                    event="mixed_decision",
                    outcome="in_progress",
                    chosen_path="SPEC",
                    chapter=chapter_code_for_db,
                    **ctx
                )
                logger.info(f"[PIPELINE] Pipeline SPEC pour {chapter_code_for_db}: utilisation du pipeline STATIQUE.")
                try:
                    # Utiliser en priorité les exercices statiques saisis en admin
                    exercises = await exercise_service.get_exercises(
                        chapter_code=chapter_code_for_db,
                        offer=request.offer if hasattr(request, 'offer') else None,
                        difficulty=request.difficulte if hasattr(request, 'difficulte') else None
                    )
                    static_exercises = [ex for ex in exercises if ex.get("is_dynamic") is not True]
                    if not static_exercises:
                        raise HTTPException(
                            status_code=422,
                            detail={
                                "error_code": "NO_EXERCISE_AVAILABLE",
                                "error": "no_exercise_available",
                                "message": (
                                    f"Aucun exercice statique saisi pour {chapter_code_for_db} "
                                    f"avec offer='{request.offer}' et difficulte='{request.difficulte}'. "
                                    "Ajoutez un exercice statique ou définissez exercise_types pour la génération SPEC."
                                ),
                                "chapter_code": chapter_code_for_db,
                                "pipeline": "SPEC",
                                "filters": {
                                    "offer": getattr(request, 'offer', None),
                                    "difficulty": getattr(request, 'difficulte', None)
                                }
                            }
                        )
                        if static_exercises:
                            selected_static = safe_random_choice(static_exercises, ctx, obs_logger)
                        timestamp = int(time.time() * 1000)
                        static_exercise = {
                            "id_exercice": f"admin_static_{chapter_code_for_db}_{selected_static.get('id')}_{timestamp}",
                            "niveau": curriculum_chapter.niveau,
                            "chapitre": curriculum_chapter.libelle or curriculum_chapter.code_officiel,
                            "enonce_html": selected_static.get("enonce_html") or "",
                            "solution_html": selected_static.get("solution_html") or "",
                            "needs_svg": selected_static.get("needs_svg") or False,
                            "exercise_type": selected_static.get("exercise_type"),
                            "pdf_token": f"admin_static_{chapter_code_for_db}_{selected_static.get('id')}_{timestamp}",
                            "metadata": {
                                "offer": selected_static.get("offer"),
                                "difficulty": selected_static.get("difficulty"),
                                "source": "admin_exercises_static",
                                "is_fallback": False
                            }
                        }
                        logger.info(
                            f"[PIPELINE] ✅ Exercice statique (admin) généré (SPEC): "
                            f"chapter_code={chapter_code_for_db}, exercise_id={selected_static.get('id')}"
                        )
                        return static_exercise
                except Exception as e:
                    logger.warning(
                        f"[PIPELINE] Erreur récupération exercices statiques (SPEC) pour {chapter_code_for_db}: {e}. "
                        f"Fallback sur pipeline STATIQUE legacy."
                    )
                # Continue vers pipeline statique (code ci-dessous)
        
        else:
            # P0 - Pipeline absent : utiliser le pipeline AUTO (DYNAMIC → STATIC fallback)
            logger.info(
                f"[P0] Chapitre {request.code_officiel} n'a pas de pipeline défini. "
                f"Utilisation du pipeline AUTO (DYNAMIC → STATIC fallback)."
            )
            
            from server import db
            from backend.services.curriculum_sync_service import get_curriculum_sync_service
            from backend.services.exercise_persistence_service import get_exercise_persistence_service
            
            sync_service = get_curriculum_sync_service(db)
            exercise_service = get_exercise_persistence_service(db)
            
            chapter_code_for_db = request.code_officiel.upper().replace("-", "_")
            
            ctx = get_request_context()
            ctx.update({
                'pipeline': 'AUTO',
                'chapter_code': chapter_code_for_db,
            })
            
            # Utiliser le pipeline simplifié : DYNAMIC → STATIC fallback
            return await generate_exercise_with_fallback(
                chapter_code=chapter_code_for_db,
                exercise_service=exercise_service,
                request=request,
                ctx=ctx,
                request_start=request_start
            )
        
        # Convertir les types d'exercices du référentiel en enum
        # IMPORTANT:
        # - En mode gratuit, filtrer les générateurs premium
        # - Ne JAMAIS faire de fallback silencieux vers le mapping legacy
        #   si des exercise_types configurés sont inconnus.
        if curriculum_chapter.exercise_types:
            try:
                # P2.1 - FILTRAGE DATA-DRIVEN DES GÉNÉRATEURS PREMIUM
                # Au lieu d'une liste hardcodée, vérifier meta.min_offer pour chaque générateur
                if request.offer == "pro":
                    # Mode PRO: tous les générateurs disponibles
                    filtered_types = curriculum_chapter.exercise_types
                else:
                    # Mode gratuit: exclure dynamiquement les générateurs avec min_offer="pro"
                    filtered_types = []
                    for et in curriculum_chapter.exercise_types:
                        # Vérifier si c'est un générateur Factory
                        gen_class = GeneratorFactory.get(et)
                        if gen_class:
                            gen_meta = gen_class.get_meta()
                            required_offer = getattr(gen_meta, 'min_offer', 'free')
                            if required_offer == "free":
                                filtered_types.append(et)
                            else:
                                filtered_premium_generators.append(et)
                                logger.info(f"[FILTER] Générateur {et} exclu (min_offer={required_offer}, user_offer=free)")
                        else:
                            # Pas un générateur Factory, inclure par défaut
                            filtered_types.append(et)
                
                # Conversion stricte vers MathExerciseType
                valid_types = []
                invalid_types = []
                for et in filtered_types:
                    if hasattr(MathExerciseType, et):
                        valid_types.append(MathExerciseType[et])
                    else:
                        invalid_types.append(et)
                
                exercise_types_override = valid_types
                
                # Si au moins un type est valide mais certains sont inconnus:
                # - on log un warning explicite,
                # - mais on continue avec les types valides uniquement.
                if invalid_types and valid_types:
                    logger.warning(
                        f"Certains exercise_types sont inconnus pour {request.code_officiel} "
                        f"(ignorés): {invalid_types}"
                    )
                
                # P0: Validation BLOQUANTE pour pipeline SPEC
                # Si TOUS les types configurés sont inconnus, lever une erreur claire
                # plutôt que de retomber silencieusement sur le mapping legacy.
                if filtered_types and not valid_types:
                    # Vérifier si le pipeline est SPEC (validation bloquante)
                    pipeline_mode = curriculum_chapter.pipeline if hasattr(curriculum_chapter, 'pipeline') and curriculum_chapter.pipeline else None
                    if pipeline_mode == "SPEC":
                        raise HTTPException(
                            status_code=422,
                            detail={
                                "error_code": "SPEC_PIPELINE_INVALID_EXERCISE_TYPES",
                                "error": "spec_pipeline_invalid_exercise_types",
                                "message": (
                                    f"Le chapitre '{request.code_officiel}' est configuré avec pipeline='SPEC' "
                                    f"mais tous les exercise_types configurés ne correspondent à aucun "
                                    f"MathExerciseType connu: {filtered_types}."
                                ),
                                "chapter_code": request.code_officiel,
                                "pipeline": "SPEC",
                                "exercise_types_configured": filtered_types,
                                "hint": (
                                    "Ajoutez ces types dans MathExerciseType, corrigez le référentiel curriculum_6e, "
                                    "ou changez le pipeline à 'TEMPLATE' ou 'MIXED'."
                                ),
                            },
                        )
                    else:
                        # Comportement legacy pour compatibilité
                        raise HTTPException(
                            status_code=422,
                            detail={
                                "error_code": "INVALID_CURRICULUM_EXERCISE_TYPES",
                                "error": "invalid_exercise_types",
                                "message": (
                                    f"Les exercise_types configurés pour le chapitre "
                                    f"'{request.code_officiel}' ne correspondent à aucun "
                                    f"MathExerciseType connu: {filtered_types}."
                                ),
                                "chapter_code": request.code_officiel,
                                "exercise_types_configured": filtered_types,
                                "hint": (
                                    "Ajoutez ces types dans MathExerciseType ou corrigez "
                                    "le référentiel curriculum_6e."
                                ),
                            },
                        )
                
                logger.info(
                    f"Types d'exercices filtrés pour {request.code_officiel} "
                    f"(offer={request.offer}): {filtered_types}"
                )
            except HTTPException:
                # Propager l'erreur structurée telle quelle
                raise
            except Exception as e:
                logger.warning(
                    f"Erreur conversion exercise_types pour {request.code_officiel}: {e}"
                )
        
        logger.info(
            f"Génération exercice (mode officiel): code={request.code_officiel}, "
            f"chapitre_backend={request.chapitre}, exercise_types={curriculum_chapter.exercise_types}"
        )
    else:
        # Mode legacy : utiliser niveau + chapitre directement
        logger.info(
            f"Génération exercice (mode legacy): niveau={request.niveau}, "
            f"chapitre={request.chapitre}, difficulté={request.difficulte}"
        )
    
    # ============================================================================
    # 1. VALIDATION DU NIVEAU
    # ============================================================================
    
    if not curriculum_service.validate_niveau(request.niveau):
        niveaux_disponibles = curriculum_service.get_niveaux_disponibles()
        
        logger.warning(f"Niveau invalide: {request.niveau}")
        
        raise HTTPException(
            status_code=422,
            detail={
                "error": "niveau_invalide",
                "message": (
                    f"Le niveau '{request.niveau}' n'est pas reconnu. "
                    f"Niveaux disponibles : {', '.join(niveaux_disponibles)}."
                ),
                "niveaux_disponibles": niveaux_disponibles
            }
        )
    
    # ============================================================================
    # 2. VALIDATION DU CHAPITRE (sauf si code_officiel a été résolu)
    # ============================================================================
    
    if not curriculum_chapter:
        # Mode legacy : valider le chapitre
        if not curriculum_service.validate_chapitre(request.niveau, request.chapitre):
            chapitres_disponibles = curriculum_service.get_chapitres_disponibles(request.niveau)
            
            logger.warning(
                f"Chapitre invalide: {request.chapitre} pour niveau {request.niveau}"
            )
            
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "chapitre_invalide",
                    "message": (
                        f"Le chapitre '{request.chapitre}' n'existe pas pour le niveau '{request.niveau}'. "
                        f"Chapitres disponibles : {', '.join(chapitres_disponibles[:10])}"
                        + ("..." if len(chapitres_disponibles) > 10 else ".")
                    ),
                    "niveau": request.niveau,
                    "chapitres_disponibles": chapitres_disponibles
                }
            )
    
    # ============================================================================
    # 3. GÉNÉRATION DE L'EXERCICE
    # ============================================================================
    
    try:
        # V1-BE-002-FIX: Utiliser l'instance globale (performance)
        # Générer l'exercice avec le service math
        
        # P0.3 - PREMIUM DISPATCH GÉNÉRIQUE via GeneratorFactory
        use_premium_factory = False
        selected_premium_generator = None
        premium_result = None
        
        if request.offer == "pro" and request.code_officiel:
            # Récupérer les informations du chapitre
            chapter_info = get_chapter_by_official_code(request.code_officiel)
            
            if chapter_info and hasattr(chapter_info, 'exercise_types'):
                # Filtrer les exercise_types pour ne garder que ceux enregistrés dans GeneratorFactory
                available_factory_generators = list(GeneratorFactory._generators.keys())
                factory_generator_keys = [gen_key for gen_key in chapter_info.exercise_types 
                                         if gen_key in available_factory_generators]
                
                if factory_generator_keys:
                    # Sélectionner un générateur de façon déterministe si seed fourni
                    if request.seed is not None:
                        # Déterministe : même seed → même générateur
                        generator_index = request.seed % len(factory_generator_keys)
                        selected_premium_generator = factory_generator_keys[generator_index]
                    else:
                        # Aléatoire (mais cohérent avec le comportement attendu)
                        import random
                        selected_premium_generator = random.choice(factory_generator_keys)
                    
                    # P2.1 - VÉRIFICATION DATA-DRIVEN DE L'OFFRE MINIMALE REQUISE
                    generator_class = GeneratorFactory.get(selected_premium_generator)
                    generator_meta = generator_class.get_meta() if generator_class else None
                    required_offer = getattr(generator_meta, 'min_offer', 'free') if generator_meta else 'free'
                    
                    if required_offer == "pro" and request.offer != "pro":
                        # Utilisateur free tente d'accéder à un générateur premium
                        obs_logger.warning(
                            "event=premium_required",
                            event="premium_required",
                            outcome="error",
                            generator_key=selected_premium_generator,
                            required_offer=required_offer,
                            user_offer=request.offer,
                            **ctx
                        )
                        raise HTTPException(
                            status_code=403,
                            detail={
                                "error_code": "PREMIUM_REQUIRED",
                                "error": "premium_required",
                                "message": f"Ce générateur ({generator_meta.label}) est réservé à l'offre Pro.",
                                "hint": "Passez à l'offre Pro pour accéder à ce contenu.",
                                "context": {
                                    "generator_key": selected_premium_generator,
                                    "required_offer": required_offer,
                                    "current_offer": request.offer
                                }
                            }
                        )
                    
                    logger.info(f"🌟 Mode PREMIUM Factory activé pour {request.code_officiel} → {selected_premium_generator}")
                    obs_logger.info(
                        "event=premium_factory_selected",
                        event="premium_factory_selected",
                        outcome="in_progress",
                        generator_key=selected_premium_generator,
                        available_generators=factory_generator_keys,
                        **ctx
                    )
                    
                    try:
                        # Appeler GeneratorFactory.generate()
                        premium_result = GeneratorFactory.generate(
                            key=selected_premium_generator,
                            exercise_params={},
                            overrides={
                                'seed': request.seed,
                                'grade': request.niveau,
                                'difficulty': request.difficulte,
                            },
                            seed=request.seed
                        )
                        use_premium_factory = True
                        
                        obs_logger.info(
                            "event=premium_factory_success",
                            event="premium_factory_success",
                            outcome="success",
                            generator_key=selected_premium_generator,
                            **ctx
                        )
                    except Exception as e:
                        # Log l'erreur mais ne pas bloquer (fallback sur legacy)
                        obs_logger.error(
                            "event=premium_factory_error",
                            event="premium_factory_error",
                            outcome="error",
                            reason="generation_failed",
                            generator_key=selected_premium_generator,
                            error_message=str(e),
                            **ctx
                        )
                        logger.error(f"Erreur Factory {selected_premium_generator}: {e}")
                        use_premium_factory = False
        
        if use_premium_factory and premium_result:
            # P0.3 - Construire la réponse directement depuis le générateur Factory
            obs_logger.info(
                "event=mixed_decision",
                event="mixed_decision",
                outcome="in_progress",
                chosen_path="premium_factory",
                **ctx
            )
            
            # Récupérer les variables depuis premium_result
            variables = premium_result.get("variables", {})
            
            # ============================================================================
            # P1 - SÉLECTION TEMPLATE DB-FIRST + FALLBACK LEGACY
            # ============================================================================
            # Tenter de récupérer un template depuis la DB.
            # Si trouvé : utiliser ce template (template_source="db")
            # Sinon : fallback sur templates hardcodés legacy (template_source="legacy")
            
            template_source = "legacy"  # Par défaut
            template_db_id = None
            variant_id = premium_result.get("variant_id", "default")  # Extraire variant_id si disponible
            
            # Tenter de récupérer un template DB
            try:
                from server import db
                template_service = get_template_service(db)
                
                db_template = await template_service.get_best_template(
                    generator_key=selected_premium_generator,
                    variant_id=variant_id,
                    grade=request.niveau,
                    difficulty=request.difficulte
                )
                
                if db_template:
                    # Template DB trouvé : utiliser celui-ci
                    enonce_template = db_template.enonce_template_html
                    solution_template = db_template.solution_template_html
                    template_source = "db"
                    template_db_id = db_template.id
                    
                    logger.info(
                        f"[TEMPLATE_DB] Template DB trouvé: id={db_template.id}, "
                        f"generator={selected_premium_generator}, variant={variant_id}, "
                        f"grade={request.niveau}, difficulty={request.difficulte}"
                    )
                    obs_logger.info(
                        "event=template_db_selected",
                        event="template_db_selected",
                        outcome="success",
                        template_id=db_template.id,
                        generator_key=selected_premium_generator,
                        variant_id=variant_id,
                        **ctx
                    )
                else:
                    # Pas de template DB : fallback legacy
                    logger.info(
                        f"[TEMPLATE_LEGACY] Aucun template DB trouvé, fallback sur legacy pour "
                        f"generator={selected_premium_generator}, variant={variant_id}"
                    )
                    obs_logger.info(
                        "event=template_legacy_fallback",
                        event="template_legacy_fallback",
                        outcome="success",
                        reason="no_db_template",
                        generator_key=selected_premium_generator,
                        variant_id=variant_id,
                        **ctx
                    )
                    
                    # P0.4 - Templates inline sécurisés (pas de {{{enonce}}}, seulement {{{tableau_html}}})
                    # Ces templates sont cohérents avec ChapterExercisesAdminPage.js
                    enonce_template = """<div class="exercise-enonce">
  <p><strong>{{consigne}}</strong></p>
  <p>{{enonce}}</p>
  {{{tableau_html}}}
</div>"""
                    
                    solution_template = """<div class="exercise-solution">
  <h4 style="color: #2563eb; margin-bottom: 1rem;">{{methode}}</h4>
  <div class="calculs" style="background: #f1f5f9; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
    <pre style="white-space: pre-line; font-family: inherit; margin: 0;">{{calculs_intermediaires}}</pre>
  </div>
  <div class="solution-text" style="margin-bottom: 1rem;">
    <p>{{solution}}</p>
  </div>
  <div class="reponse-finale" style="background: #dcfce7; padding: 0.75rem; border-left: 4px solid #22c55e; border-radius: 0.25rem;">
    <p style="margin: 0;"><strong>Réponse finale :</strong> {{reponse_finale}}</p>
  </div>
</div>"""
            
            except Exception as e:
                # En cas d'erreur DB, fallback silencieux sur legacy
                logger.warning(
                    f"[TEMPLATE_DB_ERROR] Erreur lors de la récupération du template DB, "
                    f"fallback sur legacy: {e}"
                )
                obs_logger.warning(
                    "event=template_db_error",
                    event="template_db_error",
                    outcome="warning",
                    reason="db_error",
                    error_message=str(e),
                    generator_key=selected_premium_generator,
                    **ctx
                )
                
                # Templates legacy en fallback
                enonce_template = """<div class="exercise-enonce">
  <p><strong>{{consigne}}</strong></p>
  <p>{{enonce}}</p>
  {{{tableau_html}}}
</div>"""
                
                solution_template = """<div class="exercise-solution">
  <h4 style="color: #2563eb; margin-bottom: 1rem;">{{methode}}</h4>
  <div class="calculs" style="background: #f1f5f9; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
    <pre style="white-space: pre-line; font-family: inherit; margin: 0;">{{calculs_intermediaires}}</pre>
  </div>
  <div class="solution-text" style="margin-bottom: 1rem;">
    <p>{{solution}}</p>
  </div>
  <div class="reponse-finale" style="background: #dcfce7; padding: 0.75rem; border-left: 4px solid #22c55e; border-radius: 0.25rem;">
    <p style="margin: 0;"><strong>Réponse finale :</strong> {{reponse_finale}}</p>
  </div>
</div>"""
            
            # Rendu HTML avec les variables du générateur
            enonce_html = render_template(enonce_template, variables)
            solution_html = render_template(solution_template, variables)
            
            # Pas besoin de specs, on construit directement la réponse
            duration_ms = int((time.time() - request_start) * 1000)
            obs_logger.info(
                "event=request_complete",
                event="request_complete",
                outcome="success",
                duration_ms=duration_ms,
                chosen_path="premium_factory",
                generator_key=selected_premium_generator,
                **ctx
            )
            
            # Construire l'enonce_html et solution_html depuis premium_result
            id_exercice = generate_exercise_id(request.niveau, request.chapitre)
            pdf_token = id_exercice
            
            # Retourner immédiatement la réponse Factory
            metadata = {
                "is_premium": True,
                "generator_key": selected_premium_generator,
                "generator_code": f"{request.niveau}_{selected_premium_generator}",
                "difficulte": request.difficulte,
                "generation_duration_ms": duration_ms,
                "seed": request.seed,
                "variables": variables,  # Ajout des variables pour debug
                "template_source": template_source,  # P1 - Traçabilité template (db | legacy)
            }
            
            # Ajouter template_db_id si template DB utilisé
            if template_db_id:
                metadata["template_db_id"] = template_db_id
            
            return ExerciseGenerateResponse(
                id_exercice=id_exercice,
                niveau=request.niveau,
                chapitre=request.chapitre,
                enonce_html=enonce_html,
                solution_html=solution_html,
                figure_svg=premium_result.get("figure_svg_enonce"),
                figure_svg_enonce=premium_result.get("figure_svg_enonce"),
                figure_svg_solution=premium_result.get("figure_svg_solution"),
                pdf_token=pdf_token,
                metadata=metadata
            )
        elif exercise_types_override and len(exercise_types_override) > 0:
            # Mode code_officiel : utiliser les types spécifiés dans le référentiel
            obs_logger.info(
                "event=mixed_decision",
                event="mixed_decision",
                outcome="in_progress",
                chosen_path="exercise_types_override",
                exercise_types_count=len(exercise_types_override),
                **ctx
            )
            specs = _math_service.generate_math_exercise_specs_with_types(
                niveau=request.niveau,
                chapitre=request.chapitre,
                difficulte=request.difficulte,
                exercise_types=exercise_types_override,
                nb_exercices=1
            )
        else:
            # Mode legacy : utiliser le mapping par chapitre
            # Vérifier si le chapitre a un pipeline TEMPLATE (ne doit jamais passer par MathGenerationService)
            if curriculum_chapter and hasattr(curriculum_chapter, 'pipeline') and curriculum_chapter.pipeline == "TEMPLATE":
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": "TEMPLATE_PIPELINE_NO_DYNAMIC_EXERCISES",
                        "error": "template_pipeline_no_exercises",
                        "message": (
                            f"Le chapitre '{request.code_officiel}' est configuré avec pipeline='TEMPLATE' "
                            f"mais aucun exercice dynamique n'existe en DB pour ce chapitre."
                        ),
                        "chapter_code": request.code_officiel,
                        "pipeline": "TEMPLATE",
                        "hint": "Créez au moins un exercice dynamique pour ce chapitre ou changez le pipeline à 'SPEC' ou 'MIXED'."
                    }
                )
            
            specs = _math_service.generate_math_exercise_specs(
                niveau=request.niveau,
                chapitre=request.chapitre,
                difficulte=request.difficulte,
                nb_exercices=1
            )
        
        if not specs or len(specs) == 0:
            raise ValueError(f"Aucun exercice généré pour {request.niveau} - {request.chapitre}")
        
        spec = specs[0]  # Prendre le premier exercice
        
        duration_ms = int((time.time() - request_start) * 1000)
        obs_logger.info(
            "event=request_complete",
            event="request_complete",
            outcome="success",
            duration_ms=duration_ms,
            chosen_path="legacy_static",
            exercise_type=str(spec.type_exercice) if spec.type_exercice else None,
            **ctx
        )
        logger.info(f"Exercice généré: type={spec.type_exercice}, has_figure={spec.figure_geometrique is not None}")
        
    except HTTPException as e:
        # Propager les erreurs structurées déjà construites
        duration_ms = int((time.time() - request_start) * 1000)
        obs_logger.error(
            "event=request_error",
            event="request_error",
            outcome="error",
            duration_ms=duration_ms,
            reason="http_exception",
            error_code=e.detail.get('error_code', None) if isinstance(e.detail, dict) else None,
            **ctx
        )
        raise
    except ValueError as e:
        duration_ms = int((time.time() - request_start) * 1000)
        obs_logger.error(
            "event=request_error",
            event="request_error",
            outcome="error",
            duration_ms=duration_ms,
            reason="validation_error",
            exception_type="ValueError",
            **ctx
        )
        logger.error(f"Validation génération exercice: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "CHAPTER_OR_TYPE_INVALID",
                "error": "chapter_not_mapped",
                "message": str(e),
                "hint": "Ajoutez le chapitre dans MathGenerationService._get_exercise_types_for_chapter ou configurez un pipeline dynamique/statique avec des exercices disponibles."
            }
        )
    except Exception as e:
        duration_ms = int((time.time() - request_start) * 1000)
        obs_logger.error(
            "event=request_exception",
            event="request_exception",
            outcome="error",
            duration_ms=duration_ms,
            reason="generation_error",
            exception_type=type(e).__name__,
            **ctx,
            exc_info=True
        )
        logger.error(f"Erreur lors de la génération de l'exercice: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération de l'exercice : {str(e)}"
        )
    
    # ============================================================================
    # 4. GÉNÉRATION DU SVG (si figure géométrique présente OU figure_svg dans paramètres)
    # ============================================================================
    
    svg_question = None
    svg_correction = None
    
    # D'abord vérifier si un SVG est directement fourni dans les paramètres
    if spec.parametres and spec.parametres.get("figure_svg"):
        svg_question = spec.parametres.get("figure_svg")
        svg_correction = spec.parametres.get("figure_svg_correction", svg_question)
        logger.info(f"SVG fourni dans paramètres: {len(svg_question or '')} chars")
    
    elif spec.figure_geometrique:
        try:
            # V1-BE-002-FIX: Utiliser l'instance globale (performance)
            result = _geom_service.render_figure_to_svg(spec.figure_geometrique)
            
            # Gérer les deux formats de retour (dict ou string)
            if isinstance(result, dict):
                svg_question = result.get("figure_svg_question", result.get("figure_svg"))
                svg_correction = result.get("figure_svg_correction", result.get("figure_svg"))
            else:
                # Format string simple
                svg_question = result
                svg_correction = result
            
            logger.info(f"SVG généré: question={len(svg_question or '')} chars, correction={len(svg_correction or '')} chars")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du SVG: {e}", exc_info=True)
            # Continue sans SVG plutôt que de crasher
            svg_question = None
            svg_correction = None
    
    # ============================================================================
    # 5. CONSTRUCTION DE L'ÉNONCÉ ET DE LA SOLUTION HTML
    # ============================================================================
    
    # Énoncé - Priorité : enonce > expression > fallback intelligent
    enonce_text = spec.parametres.get("enonce", "") if spec.parametres else ""
    is_fallback = False
    
    if not enonce_text:
        # Fallback intelligent : générer un énoncé pédagogique à partir des paramètres
        enonce_text = _build_fallback_enonce(spec, request.chapitre)
        is_fallback = True
    
    enonce_html = build_enonce_html(enonce_text, svg_question)
    
    # Solution
    etapes = spec.etapes_calculees or []
    resultat_final = spec.resultat_final or "Solution à compléter"
    solution_html = build_solution_html(etapes, resultat_final, svg_correction)
    
    # ============================================================================
    # 6. GÉNÉRATION DE L'ID ET DU PDF TOKEN
    # ============================================================================
    
    id_exercice = generate_exercise_id(request.niveau, request.chapitre)
    
    # Pour la v1, le pdf_token est simplement l'id_exercice
    # v2: génération de tokens temporaires avec expiration
    pdf_token = id_exercice
    
    # ============================================================================
    # 7. MÉTADONNÉES
    # ============================================================================
    
    # Générer un code de générateur pour debug (ex: "6e_CALCUL_FRACTIONS")
    generator_code = f"{request.niveau}_{spec.type_exercice.name if spec.type_exercice else 'UNKNOWN'}"
    
    metadata = {
        "type_exercice": request.type_exercice,
        "difficulte": request.difficulte,
        "duree_estimee": 5,  # minutes (valeur par défaut)
        "points": 2.0,  # points de barème (valeur par défaut)
        "domaine": curriculum_service.get_domaine_by_chapitre(request.niveau, request.chapitre),
        "has_figure": spec.figure_geometrique is not None or svg_question is not None,
        # Nouveaux champs pour debug/identification du générateur
        "is_fallback": is_fallback,
        "generator_code": generator_code,
        # Champs PREMIUM
        "is_premium": use_premium if 'use_premium' in locals() else False,
        "offer": request.offer,
        # P2.1 - Metadata de fallback premium
        "premium_available": len(filtered_premium_generators) > 0,
    }
    
    # P2.1 - Ajouter les générateurs filtrés si présents
    if filtered_premium_generators:
        metadata["filtered_premium_generators"] = filtered_premium_generators
        metadata["hint"] = "Certaines variantes premium ont été exclues (offre Pro requise)."
    
    # ============================================================================
    # 8. CONSTRUCTION DE LA RÉPONSE
    # ============================================================================
    
    response = ExerciseGenerateResponse(
        id_exercice=id_exercice,
        niveau=request.niveau,
        chapitre=request.chapitre,
        enonce_html=enonce_html,
        svg=svg_question,
        solution_html=solution_html,
        pdf_token=pdf_token,
        metadata=metadata
    )
    
    logger.info(f"Exercice généré avec succès: id={id_exercice}")
    
    return response


# Route de santé pour vérifier que le service fonctionne
@router.get(
    "/api/v1/exercises/health",
    summary="Vérifier l'état du service exercises",
    tags=["Health"]
)
async def health_check():
    """Vérifie que le service exercises est opérationnel"""
    
    curriculum_info = curriculum_service.get_curriculum_info()
    
    return {
        "status": "healthy",
        "service": "exercises_v1",
        "curriculum": curriculum_info
    }
