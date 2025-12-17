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
from backend.services.gm07_handler import is_gm07_request, generate_gm07_exercise, generate_gm07_batch
from backend.services.gm08_handler import is_gm08_request, generate_gm08_exercise, generate_gm08_batch
from backend.services.tests_dyn_handler import is_tests_dyn_request, generate_tests_dyn_exercise, generate_tests_dyn_batch, get_available_generators
from logger import get_logger

logger = get_logger()

router = APIRouter()

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
    
    # ============================================================================
    # GM07 INTERCEPT: Chapitre pilote avec exercices figés
    # ============================================================================
    
    if is_gm07_request(request.code_officiel):
        from services.gm07_handler import generate_gm07_batch
        
        nb = request.nb_exercices if hasattr(request, 'nb_exercices') else 1
        logger.info(f"🎯 GM07 Request intercepted: offer={request.offer}, difficulty={request.difficulte}, count={nb}")
        
        # Si on demande 1 seul exercice, utiliser la fonction simple
        if nb == 1:
            gm07_exercise = generate_gm07_exercise(
                offer=request.offer,
                difficulty=request.difficulte,
                seed=request.seed
            )
            
            if not gm07_exercise:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "no_gm07_exercise_found",
                        "message": f"Aucun exercice GM07 trouvé pour offer='{request.offer}' et difficulty='{request.difficulte}'",
                        "hint": "Vérifiez les filtres: offer='free'|'pro', difficulty='facile'|'moyen'|'difficile'"
                    }
                )
            
            logger.info(f"✅ GM07 Exercise generated: id={gm07_exercise['metadata']['exercise_id']}, "
                       f"family={gm07_exercise['metadata']['family']}, "
                       f"is_premium={gm07_exercise['metadata']['is_premium']}")
            
            return gm07_exercise
        
        # Si on demande plusieurs exercices via cet endpoint, utiliser le batch
        # Note: Le frontend devrait utiliser /generate/batch/gm07 pour les lots
        exercises, batch_meta = generate_gm07_batch(
            offer=request.offer,
            difficulty=request.difficulte,
            count=nb,
            seed=request.seed
        )
        
        if not exercises:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "no_gm07_exercise_found",
                    "message": batch_meta.get("warning", "Aucun exercice GM07 trouvé"),
                    "hint": "Vérifiez les filtres ou utilisez /generate/batch/gm07 pour les lots"
                }
            )
        
        # Log le résultat
        logger.info(f"✅ GM07 Batch via /generate: {len(exercises)} exercises, "
                   f"available={batch_meta.get('available')}, "
                   f"warning={batch_meta.get('warning', 'none')}")
        
        # Retourner le premier exercice pour compatibilité avec l'API actuelle
        # Le warning est inclus dans les metadata
        return exercises[0]
    
    # ============================================================================
    # GM08 INTERCEPT: Chapitre pilote #2 avec exercices figés
    # ============================================================================
    
    if is_gm08_request(request.code_officiel):
        nb = request.nb_exercices if hasattr(request, 'nb_exercices') else 1
        logger.info(f"🎯 GM08 Request intercepted: offer={request.offer}, difficulty={request.difficulte}, count={nb}")
        
        # Si on demande 1 seul exercice, utiliser la fonction simple
        if nb == 1:
            gm08_exercise = generate_gm08_exercise(
                offer=request.offer,
                difficulty=request.difficulte,
                seed=request.seed
            )
            
            if not gm08_exercise:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "no_gm08_exercise_found",
                        "message": f"Aucun exercice GM08 trouvé pour offer='{request.offer}' et difficulty='{request.difficulte}'",
                        "hint": "Vérifiez les filtres: offer='free'|'pro', difficulty='facile'|'moyen'|'difficile'"
                    }
                )
            
            logger.info(f"✅ GM08 Exercise generated: id={gm08_exercise['metadata']['exercise_id']}, "
                       f"family={gm08_exercise['metadata']['family']}, "
                       f"is_premium={gm08_exercise['metadata']['is_premium']}")
            
            return gm08_exercise
        
        # Si on demande plusieurs exercices via cet endpoint, utiliser le batch
        # Note: Le frontend devrait utiliser /generate/batch/gm08 pour les lots
        exercises, batch_meta = generate_gm08_batch(
            offer=request.offer,
            difficulty=request.difficulte,
            count=nb,
            seed=request.seed
        )
        
        if not exercises:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "no_gm08_exercise_found",
                    "message": batch_meta.get("warning", "Aucun exercice GM08 trouvé"),
                    "hint": "Vérifiez les filtres ou utilisez /generate/batch/gm08 pour les lots"
                }
            )
        
        # Log le résultat
        logger.info(f"✅ GM08 Batch via /generate: {len(exercises)} exercises, "
                   f"available={batch_meta.get('available')}, "
                   f"warning={batch_meta.get('warning', 'none')}")
        
        # Retourner le premier exercice pour compatibilité avec l'API actuelle
        # Le warning est inclus dans les metadata
        return exercises[0]
    
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
                        "error": "no_tests_dyn_exercise_found",
                        "message": f"Aucun exercice dynamique trouvé pour offer='{request.offer}' et difficulty='{request.difficulte}'",
                        "hint": "Vérifiez les filtres ou utilisez /generate/batch/tests_dyn pour les lots"
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
        
        # Extraire les informations du référentiel
        request.niveau = curriculum_chapter.niveau
        request.chapitre = curriculum_chapter.chapitre_backend
        
        # Convertir les types d'exercices du référentiel en enum
        # IMPORTANT: En mode gratuit, filtrer les générateurs premium
        if curriculum_chapter.exercise_types:
            try:
                # Liste des générateurs premium à exclure en mode gratuit
                premium_only_generators = ["DUREES_PREMIUM"]
                
                # Filtrer selon l'offre
                if request.offer == "pro":
                    # Mode PRO: tous les générateurs disponibles
                    filtered_types = curriculum_chapter.exercise_types
                else:
                    # Mode gratuit: exclure les générateurs premium
                    filtered_types = [
                        et for et in curriculum_chapter.exercise_types
                        if et not in premium_only_generators
                    ]
                
                exercise_types_override = [
                    MathExerciseType[et] for et in filtered_types
                    if hasattr(MathExerciseType, et)
                ]
                
                logger.info(f"Types d'exercices filtrés pour {request.code_officiel} (offer={request.offer}): {filtered_types}")
            except Exception as e:
                logger.warning(f"Erreur conversion exercise_types pour {request.code_officiel}: {e}")
        
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
        
        # PREMIUM CHECK: Si offer=pro et générateur premium disponible
        use_premium = False
        premium_generators = []
        
        if request.offer == "pro" and request.code_officiel:
            # Vérifier si le chapitre a des générateurs premium
            # Note: get_chapter_by_official_code est déjà importé en haut du fichier
            chapter_info = get_chapter_by_official_code(request.code_officiel)
            if chapter_info and hasattr(chapter_info, 'exercise_types'):
                # Chercher DUREES_PREMIUM dans les types
                if "DUREES_PREMIUM" in chapter_info.exercise_types:
                    use_premium = True
                    premium_generators = ["DUREES_PREMIUM"]
                    logger.info(f"🌟 Mode PREMIUM activé pour {request.code_officiel}")
        
        if use_premium and premium_generators:
            # Utiliser le générateur premium
            # Note: MathExerciseType est déjà importé en haut via math_models
            specs = _math_service.generate_math_exercise_specs_with_types(
                niveau=request.niveau,
                chapitre=request.chapitre,
                difficulte=request.difficulte,
                exercise_types=[MathExerciseType[g] for g in premium_generators],  # Accès par nom (clé)
                nb_exercices=1
            )
        elif exercise_types_override and len(exercise_types_override) > 0:
            # Mode code_officiel : utiliser les types spécifiés dans le référentiel
            specs = _math_service.generate_math_exercise_specs_with_types(
                niveau=request.niveau,
                chapitre=request.chapitre,
                difficulte=request.difficulte,
                exercise_types=exercise_types_override,
                nb_exercices=1
            )
        else:
            # Mode legacy : utiliser le mapping par chapitre
            specs = _math_service.generate_math_exercise_specs(
                niveau=request.niveau,
                chapitre=request.chapitre,
                difficulte=request.difficulte,
                nb_exercices=1
            )
        
        if not specs or len(specs) == 0:
            raise ValueError(f"Aucun exercice généré pour {request.niveau} - {request.chapitre}")
        
        spec = specs[0]  # Prendre le premier exercice
        
        logger.info(f"Exercice généré: type={spec.type_exercice}, has_figure={spec.figure_geometrique is not None}")
        
    except Exception as e:
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
        "offer": request.offer
    }
    
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
