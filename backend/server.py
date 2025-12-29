from fastapi import FastAPI, APIRouter, HTTPException, Response, Depends, BackgroundTasks, Request, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request as StarletteRequest
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from backend.emergentintegrations.llm.chat import LlmChat, UserMessage
from backend.emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import json
import re
import tempfile
# Import lazy de weasyprint pour éviter les erreurs au démarrage
# weasyprint est importé dans les fonctions qui en ont besoin
from jinja2 import Template
from backend.latex_to_svg import latex_renderer
from backend.geometry_renderer import geometry_renderer
from backend.render_schema import schema_renderer
import sys
import subprocess
# Nouveaux imports pour l'architecture mathématique structurée (réorganisés)
from backend.services.math_generation_service import MathGenerationService
from backend.services.math_text_service import MathTextService
from backend.routes.math_routes import generate_math_exercises_new_architecture
import requests
import latex2mathml.converter
from backend.logger import get_logger, log_execution_time, log_ai_generation, log_schema_processing, log_user_context, log_quota_check
# P0 - Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.curriculum_data import (
    CURRICULUM_DATA, 
    get_available_subjects, 
    get_levels_for_subject, 
    get_all_chapters_for_level,
    build_prompt_context,
    process_math_content_for_pdf
)
from backend.curriculum_complete import (
    CURRICULUM_DATA_COMPLETE, 
    CURRICULUM_STATUS,
    get_all_subjects_with_status,
    get_active_subjects,
    get_subject_by_name,
    is_subject_active,
    get_subjects_by_status,
    get_curriculum_stats,
    log_feature_flag_access,
    process_math_content_for_pdf
)
from document_search import search_educational_document

# ============================================================================
# SYSTEM DEPENDENCIES INITIALIZATION
# ============================================================================
def ensure_system_dependencies():
    """
    Garantit que toutes les dépendances système critiques sont installées.
    Appelé au démarrage de l'application pour résoudre le problème de libpangoft2-1.0-0.
    """
    try:
        scripts_dir = Path(__file__).parent.parent / 'scripts'
        init_script = scripts_dir / 'ensure_system_dependencies.py'
        
        if init_script.exists():
            print("🔧 Vérification des dépendances système...")
            result = subprocess.run(
                [sys.executable, str(init_script)],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.stdout:
                print(result.stdout)
            
            if result.returncode != 0:
                print(f"⚠️  Avertissement: Problème lors de l'initialisation des dépendances système")
                if result.stderr:
                    print(result.stderr)
        else:
            print(f"⚠️  Script d'initialisation non trouvé: {init_script}")
            
    except Exception as e:
        print(f"⚠️  Erreur lors de la vérification des dépendances: {e}")
        # On continue le démarrage même en cas d'erreur

# Exécuter la vérification des dépendances au démarrage
ensure_system_dependencies()

ROOT_DIR = Path(__file__).parent
TEMPLATES_DIR = ROOT_DIR / 'templates'
load_dotenv(ROOT_DIR / '.env')

# Template loading function
def load_template(template_name: str) -> str:
    """Load HTML template from templates directory"""
    template_path = TEMPLATES_DIR / f"{template_name}.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Template {template_name}.html not found in {TEMPLATES_DIR}")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

# Icon mapping for exercises - Professional cascading logic
EXERCISE_ICON_MAPPING = {
    # Priority 1: By exercise type (most robust)
    "geometry": "triangle-ruler",
    "algebra": "calculator",
    "statistics": "bar-chart",
    "probability": "dice-6",
    "text": "file-text",
    
    # NOUVEAU - Physique-Chimie
    "experimental": "atom",
    "physics": "zap",
    "chemistry": "flask",
    "energy": "battery",
    "waves": "radio",
    
    # NOUVEAU - Géographie
    "cartographic": "map",
    "geographic": "compass",
    "demographic": "users",
    "urban": "building-2",
    "analysis": "leaf",
    "biology": "dna",
    "geology": "mountain",
    "ecology": "globe",
    "health": "heart",
    
    # Priority 2: By chapter (fallback)
    "Théorème de Pythagore": "triangle-ruler",
    "Théorème de Thalès": "triangle-ruler", 
    "Trigonométrie": "triangle-ruler",
    "Géométrie": "triangle-ruler",
    "Géométrie dans l'espace": "cube",
    "Géométrie - Triangles et quadrilatères": "triangle-ruler",
    "Fractions": "calculator",
    "Équations": "calculator",
    "Fonctions": "function-square",
    "Statistiques": "bar-chart",
    "Probabilités": "dice-6",
    "Volumes": "cube",
    
    # Physique-Chimie specific chapters
    "Organisation et transformations de la matière": "flask",
    "Constitution et transformations de la matière": "flask",
    "Mouvements et interactions": "zap", 
    "Mouvement et interactions": "zap",
    "L'énergie et ses conversions": "battery",
    "L'énergie : conversions et transferts": "battery",
    "Des signaux pour observer et communiquer": "radio",
    "Ondes et signaux": "radio",
    
    # SVT specific chapters
    "La planète Terre, l'environnement et l'action humaine": "globe",
    "Le vivant et son évolution": "dna",
    "Le corps humain et la santé": "heart",
    "La Terre, la vie et l'organisation du vivant": "leaf",
    "Les enjeux contemporains de la planète": "mountain",
    "Corps humain et santé": "heart",
    
    # Géographie specific chapters
    "Découvrir le(s) lieu(x) où j'habite": "map",
    "Se loger, travailler, se cultiver, avoir des loisirs": "building-2",
    "Satisfaire les besoins en énergie, en eau": "compass",
    "Se déplacer - Moyens de transport": "map",
    "Communiquer d'un bout à l'autre du monde": "globe",
    "Mieux habiter - La ville de demain": "building-2",
    "Mieux habiter - Les espaces ruraux": "mountain",
    "L'urbanisation du monde": "building-2",
    "Les mobilités humaines transnationales": "users",
    "Des espaces transformés par la mondialisation": "globe",
    "Sociétés et environnements : des équilibres fragiles": "compass",
    "Territoires, populations et développement": "users",
    "Des mobilités généralisées": "map",
    "L'Afrique australe : un espace en profonde mutation": "compass",
    "Physique-Chimie": "atom",
    "SVT": "leaf",
    "Géographie": "map",
    
    # Priority 3: Default fallback
    "default": "book-open"
}

def enrich_exercise_with_icon(exercise_data: dict, chapitre: str, matiere: str = None) -> dict:
    """
    Professional cascading icon enrichment logic extended for Physique-Chimie and SVT:
    1. Priority: Use matiere-specific logic first
    2. Fallback: Use type from AI if provided and valid
    3. Detection: Use chapter-based mapping  
    4. Content: Analyze content for type hints
    5. Default: Use generic icon
    """
    logger = get_logger()
    
    # Priority 1: Matiere-specific logic FIRST
    if matiere == "Physique-Chimie":
        logger.info(f"🧪 Enriching Physique-Chimie exercise for chapter: {chapitre}")
        if any(word in chapitre.lower() for word in ["matière", "transformation", "constitution", "chimie"]):
            exercise_data["type"] = "chemistry"
            exercise_data["icone"] = "flask"
        elif any(word in chapitre.lower() for word in ["énergie", "conversion", "transfert"]):
            exercise_data["type"] = "energy"  
            exercise_data["icone"] = "battery"
        elif any(word in chapitre.lower() for word in ["mouvement", "interaction", "force"]):
            exercise_data["type"] = "physics"
            exercise_data["icone"] = "zap"
        elif any(word in chapitre.lower() for word in ["signal", "onde", "communiquer"]):
            exercise_data["type"] = "waves"
            exercise_data["icone"] = "radio"
        else:
            exercise_data["type"] = "experimental"
            exercise_data["icone"] = "atom"
        logger.info(f"🧪 Assigned type: {exercise_data['type']}, icon: {exercise_data['icone']}")
        return exercise_data
            
    elif matiere == "SVT":
        logger.info(f"🌱 Enriching SVT exercise for chapter: {chapitre}")
        if any(word in chapitre.lower() for word in ["vivant", "évolution", "génétique", "vie"]):
            exercise_data["type"] = "biology"
            exercise_data["icone"] = "dna"
        elif any(word in chapitre.lower() for word in ["terre", "planète", "géologique", "enjeux"]):
            exercise_data["type"] = "geology"
            exercise_data["icone"] = "mountain"
        elif any(word in chapitre.lower() for word in ["environnement", "écosystème", "action humaine"]):
            exercise_data["type"] = "ecology"
            exercise_data["icone"] = "globe"
        elif any(word in chapitre.lower() for word in ["corps", "santé", "humain"]):
            exercise_data["type"] = "health"
            exercise_data["icone"] = "heart"
        else:
            exercise_data["type"] = "analysis"
            exercise_data["icone"] = "leaf"
        logger.info(f"🌱 Assigned type: {exercise_data['type']}, icon: {exercise_data['icone']}")
        return exercise_data
    
    elif matiere == "Géographie":
        logger.info(f"🗺️ Enriching Géographie exercise for chapter: {chapitre}")
        if any(word in chapitre.lower() for word in ["ville", "urbain", "habitat", "loger", "bâti"]):
            exercise_data["type"] = "urban"
            exercise_data["icone"] = "building-2"
        elif any(word in chapitre.lower() for word in ["population", "démographi", "mobilité", "humain"]):
            exercise_data["type"] = "demographic"
            exercise_data["icone"] = "users"
        elif any(word in chapitre.lower() for word in ["monde", "mondial", "mondialisation", "planète"]):
            exercise_data["type"] = "geographic"
            exercise_data["icone"] = "globe"
        elif any(word in chapitre.lower() for word in ["territoire", "espace", "lieu", "région"]):
            exercise_data["type"] = "geographic"
            exercise_data["icone"] = "compass"
        else:
            exercise_data["type"] = "cartographic"
            exercise_data["icone"] = "map"
        logger.info(f"🗺️ Assigned type: {exercise_data['type']}, icon: {exercise_data['icone']}")
        return exercise_data
    
    # Priority 2: Use type from AI if provided and valid (existing logic for Mathématiques)
    ai_type = exercise_data.get("type", "").lower()
    if ai_type in EXERCISE_ICON_MAPPING:
        exercise_data["icone"] = EXERCISE_ICON_MAPPING[ai_type]
        exercise_data["type"] = ai_type  # Ensure type is set
        return exercise_data
    
    # Priority 3: Use chapter-based mapping
    if chapitre in EXERCISE_ICON_MAPPING:
        exercise_data["icone"] = EXERCISE_ICON_MAPPING[chapitre]
        # Infer type from chapter for Mathématiques
        if matiere == "Mathématiques":
            if any(geo_word in chapitre.lower() for geo_word in ["géométrie", "pythagore", "thalès", "trigonométrie", "triangle", "volume"]):
                exercise_data["type"] = "geometry"
            elif any(alg_word in chapitre.lower() for alg_word in ["équation", "fonction", "fraction", "algèbre", "calcul"]):
                exercise_data["type"] = "algebra"
            elif any(stat_word in chapitre.lower() for stat_word in ["statistique", "probabilité"]):
                exercise_data["type"] = "statistics"
            else:
                exercise_data["type"] = "text"
        return exercise_data
    
    # Priority 4: Content-based detection (for unknown chapters) - mainly for Mathématiques
    enonce = exercise_data.get("enonce", "").lower()
    if matiere == "Mathématiques":
        if any(geo_word in enonce for geo_word in ["triangle", "cercle", "carré", "rectangle", "géométrique", "angle", "côté", "volume", "aire"]):
            exercise_data["type"] = "geometry"
            exercise_data["icone"] = "triangle-ruler"
        elif any(alg_word in enonce for alg_word in ["équation", "fonction", "fraction", "calcul", "nombre", "résoudre", "simplifier"]):
            exercise_data["type"] = "algebra" 
            exercise_data["icone"] = "calculator"
        elif any(stat_word in enonce for stat_word in ["statistique", "moyenne", "graphique", "données", "probabilité", "hasard"]):
            exercise_data["type"] = "statistics"
            exercise_data["icone"] = "bar-chart"
        else:
            # Priority 5: Default fallback
            exercise_data["type"] = "text"
            exercise_data["icone"] = EXERCISE_ICON_MAPPING["default"]
    else:
        # For non-math subjects, use matiere fallback
        fallback_icon = EXERCISE_ICON_MAPPING.get(matiere, EXERCISE_ICON_MAPPING["default"])
        exercise_data["icone"] = fallback_icon
        exercise_data["type"] = "text"
    
    return exercise_data

# Removed duplicate sanitize_ai_response function - using the newer one below

# Professional content processing function
@log_execution_time("process_schema_to_base64")
def process_schema_to_base64(schema: Optional[dict]) -> Optional[str]:
    """
    Process a geometric schema dictionary to Base64 image for web display.
    Returns Base64 string or None if no schema or processing failed.
    """
    logger = get_logger()
    
    if not schema or not isinstance(schema, dict):
        logger.debug("No schema provided or invalid schema format")
        return None
    
    schema_type = schema.get("type", "unknown")
    logger.debug(
        "Starting schema to Base64 conversion",
        module_name="schema",
        func_name="process_schema_to_base64",
        schema_type=schema_type
    )
    
    try:
        # Convert schema to geometry_renderer format - FIX STRUCTURE
        geometry_schema = {
            "type": "schema_geometrique",
            "figure": schema.get("type", "triangle"),
            # CRITICAL: Pass schema data directly, not nested in "donnees"
            **schema  # Spread all schema properties at root level
        }
        
        # Render to Base64 for web display
        base64_image = geometry_renderer.render_geometry_to_base64(geometry_schema)
        
        if base64_image:
            logger.info(
                "Schema successfully rendered to Base64",
                module_name="schema",
                func_name="process_schema_to_base64",
                schema_type=schema_type,
                base64_length=len(base64_image),
                status="success"
            )
            log_schema_processing(schema_type, True)
            return base64_image
        else:
            logger.warning(
                "Schema rendering failed",
                module_name="schema",
                func_name="process_schema_to_base64",
                schema_type=schema_type,
                status="failed"
            )
            log_schema_processing(schema_type, False)
            return None
            
    except Exception as e:
        logger.error(f"❌ Error processing schema to Base64: {e}")
        return None

def process_exercise_content(content: str) -> str:
    """
    Processes the exercise content to render both LaTeX and geometric schemas.
    This centralizes all content processing logic for consistency.
    """
    if not content or not isinstance(content, str):
        return content if isinstance(content, str) else ""
    
    # 1. Process legacy geometric schemas (for backward compatibility)
    try:
        content = geometry_renderer.process_geometric_schemas_for_web(content)
    except Exception as e:
        logger.error(f"Error processing legacy geometric schemas: {e}")
    
    # 2. Process LaTeX formulas
    try:
        content = latex_renderer.convert_latex_to_svg(content)
    except Exception as e:
        logger.error(f"Error processing LaTeX: {e}")
    
    return content

# MongoDB connection - avec validation des variables d'environnement
def validate_env():
    """Valide les variables d'environnement critiques au démarrage"""
    required_vars = {
        'MONGO_URL': os.environ.get('MONGO_URL'),
        'DB_NAME': os.environ.get('DB_NAME')
    }
    
    missing = [var for var, value in required_vars.items() if not value]
    if missing:
        raise RuntimeError(
            f"Variables d'environnement requises manquantes: {', '.join(missing)}. "
            f"Veuillez configurer ces variables avant de démarrer l'application."
        )
    
    return required_vars['MONGO_URL'], required_vars['DB_NAME']

# Valider les variables d'environnement avant de créer le client MongoDB
mongo_url, db_name = validate_env()
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]


def _compute_build_id() -> str:
    """
    Calcule un identifiant de build simple pour le backend.
    - Essaie de récupérer le git short SHA si disponible
    - Sinon, fallback sur 'nogit'
    - Ajoute un timestamp UTC pour différencier les builds locaux
    """
    from datetime import datetime
    try:
        import subprocess
        # On essaie de se placer à la racine du projet si possible
        repo_root = ROOT_DIR.parent
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_root),
            text=True
        ).strip()
    except Exception:
        sha = "nogit"

    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"{ts}_{sha}"


APP_BUILD_ID = os.environ.get("APP_BUILD_ID", _compute_build_id())

# P0-A2: Rate limiter with dev bypass option
# Set DISABLE_RATE_LIMIT=true in env to disable rate limiting in development
_rate_limit_disabled = os.environ.get("DISABLE_RATE_LIMIT", "").lower() in ("true", "1", "yes")
limiter = Limiter(
    key_func=get_remote_address,
    enabled=not _rate_limit_disabled  # P0-A2: Disable in dev if env var set
)

# Create the main app without a prefix
app = FastAPI()

# P0 - Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================================================
# GLOBAL EXCEPTION HANDLERS - Garantir JSON même en cas d'erreur non catchée
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: StarletteRequest, exc: Exception):
    """
    Handler global pour toutes les exceptions non catchées.
    Garantit que toute erreur renvoie du JSON structuré, jamais du HTML/text.
    """
    import traceback
    from backend.logger import get_logger
    
    logger = get_logger()
    logger.error(f"❌ Unhandled exception: {type(exc).__name__}: {str(exc)}", exc_info=True)
    
    # Si c'est déjà une HTTPException, la traiter séparément
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        detail = exc.detail if hasattr(exc, 'detail') else str(exc)
        status_code = exc.status_code if hasattr(exc, 'status_code') else 500
        
        # Si detail est déjà un dict, l'utiliser tel quel
        if isinstance(detail, dict):
            return JSONResponse(
                status_code=status_code,
                content={
                    "error_code": detail.get("error_code", detail.get("error", "http_error")),
                    "error": detail.get("error", "http_error"),
                    "message": detail.get("message", str(detail)),
                    "details": detail
                }
            )
        else:
            return JSONResponse(
                status_code=status_code,
                content={
                    "error_code": "HTTP_ERROR",
                    "error": "http_error",
                    "message": str(detail),
                    "details": None
                }
            )
    
    # Exception générique non catchée
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "error": "internal_server_error",
            "message": "Une erreur interne s'est produite",
            "details": str(exc)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: StarletteRequest, exc: RequestValidationError):
    """
    Handler pour les erreurs de validation Pydantic.
    Garantit du JSON structuré.
    """
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR",
            "error": "validation_error",
            "message": "Erreur de validation des paramètres",
            "details": exc.errors()
        }
    )


# Create uploads directory and mount static files
uploads_dir = ROOT_DIR / "uploads"
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Log build ID au démarrage
print(f"APP_BUILD_ID={APP_BUILD_ID}")
try:
    _startup_logger = get_logger()
    _startup_logger.info(f"APP_BUILD_ID={APP_BUILD_ID}")
except Exception:
    # En cas de problème de logger au démarrage, on ne bloque pas l'app
    pass


class BuildInfo(BaseModel):
    app_build_id: str


@api_router.get("/debug/build", response_model=BuildInfo, tags=["Debug"])
async def get_build_info():
    """
    Endpoint de debug pour vérifier le build backend en cours.
    Utile pour s'assurer que le frontend pointe sur le bon container.
    """
    return BuildInfo(app_build_id=APP_BUILD_ID)


# Initialize LLM Chat
emergent_key = os.environ.get('EMERGENT_LLM_KEY')

# Initialize Stripe
stripe_secret_key = os.environ.get('STRIPE_SECRET_KEY')

# Define pricing packages (server-side only for security)
PRICING_PACKAGES = {
    "monthly": {
        "name": "Abonnement Mensuel",
        "amount": 9.99,
        "currency": "eur",
        "duration": "monthly",
        "description": "Accès illimité pendant 1 mois"
    },
    "yearly": {
        "name": "Abonnement Annuel", 
        "amount": 99.00,
        "currency": "eur",
        "duration": "yearly",
        "description": "Accès illimité pendant 1 an - Économisez 16%"
    }
}

# Define template styles available for export
EXPORT_TEMPLATE_STYLES = {
    "classique": {
        "name": "Classique",
        "description": "Style traditionnel élégant avec typographie serif",
        "preview_image": "/api/template-previews/classique.png",
        "available_for": ["free", "pro"],
        "sujet_template": "sujet_classique",
        "corrige_template": "corrige_classique"
    },
    "moderne": {
        "name": "Moderne",
        "description": "Style contemporain avec couleurs vives et design épuré",
        "preview_image": "/api/template-previews/moderne.png",
        "available_for": ["pro"],
        "sujet_template": "sujet_moderne",
        "corrige_template": "corrige_moderne"
    },
    "eleve": {
        "name": "Élève",
        "description": "Style coloré et ludique avec couleurs pastel",
        "preview_image": "/api/template-previews/eleve.png",
        "available_for": ["pro"],
        "sujet_template": "sujet_eleve",
        "corrige_template": "corrige_eleve"
    },
    "corrige_detaille": {
        "name": "Corrigé détaillé",
        "description": "Template spécialisé pour corrections avec barème et critères",
        "preview_image": "/api/template-previews/corrige_detaille.png",
        "available_for": ["pro"],
        "sujet_template": "sujet_classique",  # Utilise classique pour les sujets
        "corrige_template": "corrige_detaille"
    },
    "minimal": {
        "name": "Minimal",
        "description": "Style ultra-épuré, focus sur le contenu",
        "preview_image": "/api/template-previews/minimal.png",
        "available_for": ["pro"],
        "sujet_template": "sujet_minimal",
        "corrige_template": "corrige_minimal"
    },
    "academique": {
        "name": "Académique",
        "description": "Style officiel scolaire avec espaces de réponse et barème",
        "preview_image": "/api/template-previews/academique.png",
        "available_for": ["pro"],
        "sujet_template": "sujet_academique",
        "corrige_template": "corrige_academique"
    }
}

# Define Models
class Exercise(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # "ouvert", "qcm", "mixte"
    enonce: str
    donnees: Optional[dict] = None
    difficulte: str  # "facile", "moyen", "difficile"
    solution: dict  # {"etapes": [...], "resultat": "..."}
    bareme: List[dict] = []  # [{"etape": "...", "points": 1.0}]
    version: str = "A"
    seed: Optional[int] = None
    # New fields for UI enhancement
    exercise_type: Optional[str] = "text"  # "geometry", "algebra", "statistics", "text"
    icone: Optional[str] = "book-open"  # Icon identifier for frontend
    # NEW: Separate geometric schema field (clean design) 
    geometric_schema: Optional[dict] = None  # Geometric schema data separate from text
    # CRITICAL: Base64 schema image for frontend display
    schema_img: Optional[str] = None  # Base64 PNG image for web display
    # NEW: SVG figure for geometry rendering
    figure_svg: Optional[str] = None  # SVG string for geometric figures (compatibility field)
    # NEW: Separate SVG fields for question and correction (for symmetries and construction exercises)
    figure_svg_question: Optional[str] = None  # SVG without the solution (for statement)
    figure_svg_correction: Optional[str] = None  # SVG with the complete solution (for correction)
    # NEW: Geographic document for Geography exercises
    document: Optional[dict] = None  # Educational document metadata for Geography
    # NEW: Mathematical specification for new architecture
    spec_mathematique: Optional[dict] = None  # Complete math spec from Python generation
    solution_calculee: Optional[dict] = None  # Calculated solution details

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # For Pro users
    guest_id: Optional[str] = None  # For guest users
    matiere: str
    niveau: str
    chapitre: str
    type_doc: str  # "exercices", "controle", "dm"
    difficulte: str
    nb_exercices: int
    exercises: List[Exercise] = []
    export_count: int = 0  # Track exports for quotas
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    nom: Optional[str] = None
    etablissement: Optional[str] = None
    account_type: str = "pro"
    subscription_type: str  # "monthly" or "yearly"
    subscription_expires: datetime
    stripe_customer_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    payment_id: Optional[str] = None
    amount: float
    currency: str
    package_id: str
    email: Optional[str] = None
    user_id: Optional[str] = None
    payment_status: str = "pending"  # pending, paid, failed, expired
    session_status: str = "initiated"  # initiated, complete, expired
    metadata: Optional[Dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LoginSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_email: EmailStr
    session_token: str
    device_id: str  # Unique identifier for device/browser
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LoginRequest(BaseModel):
    email: EmailStr

class VerifyLoginRequest(BaseModel):
    token: str
    device_id: str | None = None

# P2: Password auth models
class SetPasswordRequest(BaseModel):
    password: str
    password_confirm: str

class LoginPasswordRequest(BaseModel):
    email: EmailStr
    password: str

# P0: Free user registration model
class RegisterFreeRequest(BaseModel):
    email: EmailStr
    password: str
    password_confirm: str
    nom: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirmRequest(BaseModel):
    token: str
    new_password: str

class UserTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_email: EmailStr
    logo_filename: Optional[str] = None
    logo_url: Optional[str] = None
    professor_name: Optional[str] = None
    school_name: Optional[str] = None
    school_year: Optional[str] = None
    footer_text: Optional[str] = None
    template_style: str = "minimaliste"  # minimaliste, classique, moderne
    colors: Optional[Dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GenerateRequest(BaseModel):
    matiere: str
    niveau: str
    chapitre: str
    type_doc: str
    difficulte: str = "moyen"
    nb_exercices: int = 6
    versions: List[str] = ["A"]
    guest_id: Optional[str] = None

class ExportRequest(BaseModel):
    document_id: str
    export_type: str  # "sujet" or "corrige"
    guest_id: Optional[str] = None
    template_style: Optional[str] = "classique"  # Style d'export choisi

class AdvancedPDFOptions(BaseModel):
    page_format: str = "A4"  # A4, A4_compact, US_Letter
    margin_preset: str = "standard"  # standard, compact, generous
    custom_margins: Optional[Dict[str, str]] = None  # Override margin_preset if provided
    show_difficulty: bool = True
    show_creation_date: bool = True
    show_exercise_numbers: bool = True
    show_point_values: bool = True
    include_instructions: bool = True
    page_numbering: str = "bottom_center"  # bottom_center, bottom_right, top_right, none
    exercise_separator: str = "line"  # line, space, box, none
    question_numbering: str = "arabic"  # arabic, roman, letters, none
    color_scheme: str = "professional"  # professional, academic, modern, minimal
    font_scaling: float = 1.0  # 0.8 to 1.2

class EnhancedExportRequest(BaseModel):
    document_id: str
    export_type: str  # "sujet" or "corrige"
    guest_id: Optional[str] = None
    advanced_options: Optional[AdvancedPDFOptions] = None

class CheckoutRequest(BaseModel):
    package_id: str  # "monthly" or "yearly"
    origin_url: str
    email: Optional[str] = None  # P0: Deprecated, use session instead
    nom: Optional[str] = None
    etablissement: Optional[str] = None

class PreCheckoutRequest(BaseModel):
    """P0: Request to initiate secure checkout (email validation first)"""
    email: EmailStr
    package_id: str  # "monthly" or "yearly"

class CatalogItem(BaseModel):
    name: str
    levels: Optional[List[str]] = None
    chapters: Optional[List[str]] = None

class AnalyticsRequest(BaseModel):
    date_from: Optional[str] = None  # ISO date string
    date_to: Optional[str] = None
    user_email: Optional[str] = None  # For Pro users to see their own stats

class TemplateSaveRequest(BaseModel):
    professor_name: Optional[str] = None
    school_name: Optional[str] = None
    school_year: Optional[str] = None
    footer_text: Optional[str] = None
    template_style: str = "minimaliste"

# French curriculum data
# CURRICULUM_DATA is now imported from curriculum_data.py

# PDF Templates - Unified WeasyPrint approach
TEMPLATE_STYLES = {
    "minimaliste": {
        "name": "Minimaliste",
        "description": "Design épuré et moderne",
        "header_font": "Helvetica",
        "header_font_size": 14,
        "content_font": "Helvetica",
        "content_font_size": 11,
        "primary_color": "#2c3e50",
        "secondary_color": "#7f8c8d",
        "accent_color": "#3498db",
        "separator_style": "line",
        "logo_max_height": 40
    },
    "classique": {
        "name": "Classique",
        "description": "Style académique traditionnel",
        "header_font": "Times-Roman",
        "header_font_size": 16,
        "content_font": "Times-Roman", 
        "content_font_size": 12,
        "primary_color": "#1a1a1a",
        "secondary_color": "#4a4a4a",
        "accent_color": "#8b4513",
        "separator_style": "double_line",
        "logo_max_height": 45
    },
    "moderne": {
        "name": "Moderne",
        "description": "Design contemporain et aéré",
        "header_font": "Helvetica-Light",
        "header_font_size": 15,
        "content_font": "Helvetica",
        "content_font_size": 11,
        "primary_color": "#34495e",
        "secondary_color": "#95a5a6",
        "accent_color": "#e74c3c",
        "separator_style": "gradient",
        "logo_max_height": 50
    }
}

# Advanced PDF Layout Options
PDF_LAYOUT_OPTIONS = {
    "page_formats": {
        "A4": {"width": "21cm", "height": "29.7cm"},
        "A4_compact": {"width": "21cm", "height": "29.7cm", "margin": "1.5cm"},
        "US_Letter": {"width": "8.5in", "height": "11in"}
    },
    "margin_presets": {
        "standard": {"top": "2.5cm", "bottom": "2.5cm", "left": "2cm", "right": "2cm"},
        "compact": {"top": "1.5cm", "bottom": "1.5cm", "left": "1.5cm", "right": "1.5cm"},
        "generous": {"top": "3cm", "bottom": "3cm", "left": "2.5cm", "right": "2.5cm"}
    },
    "content_options": {
        "show_difficulty": True,
        "show_creation_date": True,
        "show_exercise_numbers": True,
        "show_point_values": True,
        "include_instructions": True,
        "page_numbering": "bottom_center"  # Options: bottom_center, bottom_right, top_right, none
    },
    "visual_enhancements": {
        "exercise_separator": "line",  # Options: line, space, box, none
        "question_numbering": "arabic",  # Options: arabic, roman, letters, none
        "color_scheme": "professional",  # Options: professional, academic, modern, minimal
        "font_scaling": 1.0  # Multiplier for font sizes (0.8 to 1.2)
    }
}

# Templates are now loaded from external files
#ouss

'''"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #2c3e50;
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            margin: 0;
            padding: 0;
        }
        
        .page-container {
            background: white;
            padding: 30px;
            margin: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            min-height: calc(100vh - 40px);
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 25px;
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(17, 153, 142, 0.3);
        }
        
        .title {
            font-size: 24pt;
            font-weight: bold;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .subtitle {
            font-size: 16pt;
            margin-bottom: 8px;
            opacity: 0.9;
        }
        
        .document-info {
            font-size: 12pt;
            margin-top: 15px;
            padding: 10px;
            background: rgba(255,255,255,0.2);
            border-radius: 8px;
        }
        
        .decoration {
            text-align: center;
            font-size: 20pt;
            color: #27ae60;
            margin: 20px 0;
        }
        
        .solution {
            margin: 25px 0;
            page-break-inside: avoid;
            border-left: 4px solid #27ae60;
            background: #f8f9fa;
            border-radius: 0 10px 10px 0;
            padding: 20px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }
        
        .solution-header {
            background: linear-gradient(90deg, #27ae60, #229954);
            color: white;
            padding: 12px 20px;
            margin: -20px -20px 20px -20px;
            border-radius: 10px 10px 0 0;
            font-size: 16pt;
            font-weight: bold;
        }
        
        .solution-steps {
            background: #e8f5e8;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #27ae60;
        }
        
        .solution-steps h4 {
            color: #27ae60;
            margin: 0 0 10px 0;
            font-size: 14pt;
        }
        
        .solution-steps ol {
            margin: 0;
            padding-left: 20px;
        }
        
        .solution-steps li {
            margin: 8px 0;
            font-size: 13pt;
            line-height: 1.5;
        }
        
        .final-result {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            font-weight: bold;
            text-align: center;
            font-size: 14pt;
            box-shadow: 0 5px 15px rgba(240, 147, 251, 0.3);
        }
        
        .final-result::before {
            content: "🎯 ";
            font-size: 16pt;
        }
        
        .method-tip {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 12px;
            margin: 15px 0;
            font-style: italic;
            color: #856404;
        }
        
        .method-tip::before {
            content: "💡 Astuce : ";
            font-weight: bold;
            color: #f39c12;
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            border-top: 2px solid #ecf0f1;
            color: #7f8c8d;
            font-size: 11pt;
        }
        
        .success-badge {
            display: inline-block;
            background: #27ae60;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12pt;
            margin: 10px 5px;
        }
    </style>
</head>
<body>
    <div class="page-container">
        <div class="header">
            <div class="title">{{ document.type_doc.title() }} - Corrigé ✅</div>
            <div class="subtitle">{{ document.matiere }} - {{ document.niveau }}</div>
            <div class="subtitle">📚 {{ document.chapitre }}</div>
            <div class="document-info">
                🎯 Difficulté: {{ document.difficulte.title() }} | 
                📝 {{ document.nb_exercices }} exercices | 
                📅 {{ date_creation }}
            </div>
        </div>
        
        <div class="decoration">🌟 Solutions détaillées 🌟</div>
        
        <div class="content">
            {% for exercice in document.exercises %}
                <div class="solution">
                    <div class="solution-header">
                        ✅ Exercice {{ loop.index }} - Corrigé
                    </div>
                    
                    {% if exercice.solution.etapes %}
                        <div class="solution-steps">
                            <h4>📋 Méthode étape par étape :</h4>
                            <ol>
                                {% for etape in exercice.solution.etapes %}
                                    <li>{{ etape }}</li>
                                {% endfor %}
                            </ol>
                        </div>
                        
                        <div class="method-tip">
                            Prends ton temps pour comprendre chaque étape avant de passer à la suivante !
                        </div>
                    {% endif %}
                    
                    {% if exercice.solution.resultat %}
                        <div class="final-result">
                            Résultat final : {{ exercice.solution.resultat }}
                        </div>
                    {% endif %}
                </div>
            {% endfor %}
        </div>
        
        <div class="success-badge">✨ Bravo !</div>
        <div class="success-badge">🎓 Bien joué !</div>
        <div class="success-badge">💪 Continue !</div>
        
        <div class="footer">
            🌟 Le Maître Mot - Générateur de documents pédagogiques 🌟<br>
            <small>Utilise ces corrections pour progresser !</small>
        </div>
    </div>
</body>
</html>
"""
'''
#ouss

# Pro Templates - Ultra Professional Design

@log_execution_time("check_guest_quota")
async def check_guest_quota(guest_id: str):
    """Check if guest user can export (3 exports max)"""
    logger = get_logger()
    logger.debug(
        "Starting guest quota check",
        module_name="quota",
        func_name="check_guest_quota",
        user_type="guest",
        guest_id=guest_id[:8] + "..." if guest_id and len(guest_id) > 8 else guest_id
    )
    
    try:
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        export_count = await db.exports.count_documents({
            "guest_id": guest_id,
            "created_at": {"$gte": thirty_days_ago}
        })
        
        remaining = max(0, 3 - export_count)
        
        # Log quota check result
        log_quota_check("guest", export_count, 3, guest_id=guest_id[:8] + "..." if guest_id and len(guest_id) > 8 else guest_id)
        
        logger.info(
            "Guest quota check completed",
            module_name="quota",
            func_name="check_guest_quota",
            user_type="guest",
            exports_used=export_count,
            exports_remaining=remaining,
            quota_exceeded=remaining == 0
        )
        
        return {
            "exports_used": export_count,
            "exports_remaining": remaining,
            "max_exports": 3,
            "quota_exceeded": remaining == 0
        }
        
    except Exception as e:
        logger.error(f"Error checking guest quota: {e}")
        return {
            "exports_used": 0,
            "exports_remaining": 3,
            "max_exports": 3,
            "quota_exceeded": False
        }

async def check_user_pro_status(email: str):
    """Check if user has active Pro subscription"""
    try:
        user = await db.pro_users.find_one({"email": email})
        if user and user.get("subscription_expires"):
            expires = user["subscription_expires"]
            if isinstance(expires, str):
                expires = datetime.fromisoformat(expires).replace(tzinfo=timezone.utc)
            elif isinstance(expires, datetime) and expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            logger.info(f"Checking Pro status for {email}: expires={expires}, now={now}")
            
            if expires > now:
                logger.info(f"User {email} is Pro (expires: {expires})")
                return True, user
            else:
                logger.info(f"User {email} Pro subscription expired")
        
        return False, None
        
    except Exception as e:
        logger.error(f"Error checking pro status: {e}")
        return False, None

async def require_pro_user(request: Request):
    """Middleware to require Pro user authentication"""
    session_token = request.headers.get("X-Session-Token")
    
    if not session_token:
        raise HTTPException(
            status_code=401, 
            detail="Authentification requise pour les fonctionnalités Pro"
        )
    
    email = await validate_session_token(session_token)
    if not email:
        raise HTTPException(
            status_code=401, 
            detail="Session invalide ou expirée"
        )
    
    is_pro, user = await check_user_pro_status(email)
    if not is_pro:
        raise HTTPException(
            status_code=403, 
            detail="Abonnement Pro requis pour cette fonctionnalité"
        )
    
    return email

# ReportLab-dependent functions commented out due to import removal
# These functions were using ReportLab for PDF generation with personalized templates

# class PersonalizedDocTemplate(BaseDocTemplate):
#     """Custom document template with personalized headers and footers"""
#     [COMMENTED OUT - ReportLab dependency removed]

# def create_personalized_styles(template_config):
#     """Create ReportLab styles based on template configuration"""
#     [COMMENTED OUT - ReportLab dependency removed]

# async def create_personalized_pdf(document, template_config, export_type="sujet"):
#     """Create PDF with personalized template using ReportLab Flowables"""
#     [COMMENTED OUT - ReportLab dependency removed]
#     return None

async def send_magic_link_email(email: str, token: str):
    """Send magic link email via Brevo"""
    try:
        brevo_api_key = os.environ.get('BREVO_API_KEY')
        sender_email = os.environ.get('BREVO_SENDER_EMAIL')
        sender_name = os.environ.get('BREVO_SENDER_NAME', 'Le Maître Mot')
        
        if not brevo_api_key or not sender_email:
            logger.error("Brevo credentials not configured")
            return False
        
        # Generate magic link URL
        frontend_url = os.environ.get('FRONTEND_URL', 'https://math-exercise-sync.preview.emergentagent.com')
        magic_link = f"{frontend_url}/login/verify?token={token}"
        
        # Email content
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%); padding: 2rem; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 1.5rem;">Le Maître Mot</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">Connexion à votre compte Pro</p>
            </div>
            
            <div style="background: white; padding: 2rem; border-radius: 0 0 8px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color: #1f2937; margin-top: 0;">Connexion demandée</h2>
                <p style="color: #4b5563; line-height: 1.6;">
                    Vous avez demandé à vous connecter à votre compte Le Maître Mot Pro. 
                    Cliquez sur le bouton ci-dessous pour vous connecter automatiquement.
                </p>
                
                <div style="text-align: center; margin: 2rem 0;">
                    <a href="{magic_link}" 
                       style="background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%); 
                              color: white;
                              text-decoration: none;
                              padding: 1rem 2rem;
                              border-radius: 8px;
                              font-weight: bold;
                              display: inline-block;">
                        🔐 Se connecter à Le Maître Mot Pro
                    </a>
                </div>
                
                <div style="background: #f3f4f6; padding: 1rem; border-radius: 6px; margin: 1.5rem 0;">
                    <p style="margin: 0; font-size: 0.875rem; color: #6b7280;">
                        <strong>⚠️ Important :</strong> Ce lien est valide pendant 15 minutes et ne peut être utilisé qu'une seule fois.
                        Pour des raisons de sécurité, toute autre session active sera automatiquement fermée.
                    </p>
                </div>
                
                <p style="color: #6b7280; font-size: 0.875rem; line-height: 1.4;">
                    Si vous n'avez pas demandé cette connexion, ignorez cet email. 
                    Votre compte reste sécurisé.
                </p>
                
                <div style="border-top: 1px solid #e5e7eb; margin-top: 2rem; padding-top: 1rem;">
                    <p style="color: #9ca3af; font-size: 0.75rem; margin: 0; text-align: center;">
                        Le Maître Mot - Générateur de documents pédagogiques
                    </p>
                </div>
            </div>
        </div>
        """
        
        # Send email using requests (simple approach)
        import requests
        
        headers = {
            'api-key': brevo_api_key,
            'Content-Type': 'application/json'
        }
        
        data = {
            'sender': {
                'name': sender_name,
                'email': sender_email
            },
            'to': [
                {
                    'email': email,
                    'name': email.split('@')[0]
                }
            ],
            'subject': '🔐 Connexion à Le Maître Mot Pro',
            'htmlContent': html_content
        }
        
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 201:
            logger.info(f"Magic link email sent successfully to {email}")
            return True
        else:
            logger.error(f"Failed to send magic link email: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending magic link email: {e}")
        return False

async def send_checkout_confirmation_email(email: str, token: str, package: dict):
    """
    P0: Send checkout confirmation email with magic link.
    User must click link to confirm email before payment.
    """
    try:
        brevo_api_key = os.environ.get('BREVO_API_KEY')
        sender_email = os.environ.get('BREVO_SENDER_EMAIL')
        sender_name = os.environ.get('BREVO_SENDER_NAME', 'Le Maître Mot')
        
        if not brevo_api_key or not sender_email:
            logger.error("Brevo credentials not configured")
            return False
        
        # Generate checkout link URL
        frontend_url = os.environ.get('FRONTEND_URL', 'https://math-exercise-sync.preview.emergentagent.com')
        checkout_link = f"{frontend_url}/checkout?token={token}"
        
        # Email content
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%); padding: 2rem; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 1.5rem;">Le Maître Mot</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">Confirmez votre abonnement Pro</p>
            </div>
            
            <div style="background: white; padding: 2rem; border-radius: 0 0 8px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color: #1f2937; margin-top: 0;">Presque terminé !</h2>
                <p style="color: #4b5563; line-height: 1.6;">
                    Vous avez choisi l'abonnement <strong>{package['name']}</strong> ({package['amount']}€/{package['duration']}).
                </p>
                <p style="color: #4b5563; line-height: 1.6;">
                    Pour finaliser votre inscription, veuillez confirmer votre adresse email en cliquant sur le bouton ci-dessous.
                </p>
                
                <div style="text-align: center; margin: 2rem 0;">
                    <a href="{checkout_link}" 
                       style="background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%); 
                              color: white;
                              text-decoration: none;
                              padding: 1rem 2rem;
                              border-radius: 8px;
                              font-weight: bold;
                              display: inline-block;">
                        ✅ Confirmer mon email et payer
                    </a>
                </div>
                
                <div style="background: #f3f4f6; padding: 1rem; border-radius: 6px; margin: 1.5rem 0;">
                    <p style="margin: 0; font-size: 0.875rem; color: #6b7280;">
                        <strong>⏱️ Important :</strong> Ce lien est valide pendant 15 minutes.
                        Vous serez ensuite redirigé vers le paiement sécurisé Stripe.
                    </p>
                </div>
                
                <div style="background: #dcfce7; padding: 1rem; border-radius: 6px; margin: 1.5rem 0; border-left: 4px solid #22c55e;">
                    <p style="margin: 0; font-size: 0.875rem; color: #166534;">
                        <strong>🔒 Sécurité :</strong> En confirmant votre email d'abord, nous garantissons que votre abonnement
                        sera bien lié à la bonne adresse.
                    </p>
                </div>
                
                <p style="color: #6b7280; font-size: 0.875rem; line-height: 1.4;">
                    Si vous n'avez pas demandé cet abonnement, ignorez cet email.
                </p>
                
                <div style="border-top: 1px solid #e5e7eb; margin-top: 2rem; padding-top: 1rem;">
                    <p style="color: #9ca3af; font-size: 0.75rem; margin: 0; text-align: center;">
                        Le Maître Mot - Générateur de documents pédagogiques
                    </p>
                </div>
            </div>
        </div>
        """
        
        headers = {
            'accept': 'application/json',
            'api-key': brevo_api_key,
            'Content-Type': 'application/json'
        }
        
        data = {
            'sender': {
                'name': sender_name,
                'email': sender_email
            },
            'to': [
                {
                    'email': email,
                    'name': email.split('@')[0]
                }
            ],
            'subject': f'✅ Confirmez votre email - Abonnement {package["name"]}',
            'htmlContent': html_content
        }
        
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 201:
            logger.info(f"Checkout confirmation email sent successfully to {email}")
            return True
        else:
            logger.error(f"Failed to send checkout email: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending checkout confirmation email: {e}")
        return False

async def send_password_reset_email(email: str, token: str):
    """
    P2: Send password reset email with magic link.
    User must click link to reset password.
    """
    try:
        brevo_api_key = os.environ.get('BREVO_API_KEY')
        sender_email = os.environ.get('BREVO_SENDER_EMAIL')
        sender_name = os.environ.get('BREVO_SENDER_NAME', 'Le Maître Mot')
        
        if not brevo_api_key or not sender_email:
            logger.error("Brevo credentials not configured")
            return False
        
        # Generate reset link URL
        frontend_url = os.environ.get('FRONTEND_URL', 'https://math-exercise-sync.preview.emergentagent.com')
        reset_link = f"{frontend_url}/reset-password?token={token}"
        
        # Email content
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%); padding: 2rem; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 1.5rem;">Le Maître Mot</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">Réinitialisation de mot de passe</p>
            </div>
            
            <div style="background: white; padding: 2rem; border-radius: 0 0 8px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color: #1f2937; margin-top: 0;">Réinitialiser votre mot de passe</h2>
                <p style="color: #4b5563; line-height: 1.6;">
                    Vous avez demandé à réinitialiser le mot de passe de votre compte Le Maître Mot Pro.
                    Cliquez sur le bouton ci-dessous pour définir un nouveau mot de passe.
                </p>
                
                <div style="text-align: center; margin: 2rem 0;">
                    <a href="{reset_link}" 
                       style="background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%); 
                              color: white;
                              text-decoration: none;
                              padding: 1rem 2rem;
                              border-radius: 8px;
                              font-weight: bold;
                              display: inline-block;">
                        🔐 Réinitialiser mon mot de passe
                    </a>
                </div>
                
                <div style="background: #f3f4f6; padding: 1rem; border-radius: 6px; margin: 1.5rem 0;">
                    <p style="margin: 0; font-size: 0.875rem; color: #6b7280;">
                        <strong>⏱️ Important :</strong> Ce lien est valide pendant 15 minutes et ne peut être utilisé qu'une seule fois.
                    </p>
                </div>
                
                <div style="background: #fef3c7; padding: 1rem; border-radius: 6px; margin: 1.5rem 0; border-left: 4px solid #f59e0b;">
                    <p style="margin: 0; font-size: 0.875rem; color: #92400e;">
                        <strong>🔒 Sécurité :</strong> Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.
                        Votre compte reste sécurisé.
                    </p>
                </div>
                
                <p style="color: #6b7280; font-size: 0.875rem; line-height: 1.4;">
                    Vous pouvez également continuer à utiliser le lien magique pour vous connecter.
                </p>
                
                <div style="border-top: 1px solid #e5e7eb; margin-top: 2rem; padding-top: 1rem;">
                    <p style="color: #9ca3af; font-size: 0.75rem; margin: 0; text-align: center;">
                        Le Maître Mot - Générateur de documents pédagogiques
                    </p>
                </div>
            </div>
        </div>
        """
        
        headers = {
            'accept': 'application/json',
            'api-key': brevo_api_key,
            'Content-Type': 'application/json'
        }
        
        data = {
            'sender': {
                'name': sender_name,
                'email': sender_email
            },
            'to': [
                {
                    'email': email,
                    'name': email.split('@')[0]
                }
            ],
            'subject': '🔐 Réinitialisation de votre mot de passe Le Maître Mot Pro',
            'htmlContent': html_content
        }
        
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 201:
            logger.info(f"Password reset email sent successfully to {email}")
            return True
        else:
            logger.error(f"Failed to send password reset email: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending password reset email: {e}")
        return False

def extract_device_info(request: Request) -> dict:
    """
    P1: Extract device information from HTTP request headers.
    Returns dict with browser, OS, device_type, ip_address.
    """
    user_agent = request.headers.get("User-Agent", "")
    ip_address = request.client.host if request.client else None
    
    # Simple parsing (can be enhanced with user-agents library if needed)
    device_info = {
        "ip_address": ip_address,
        "user_agent": user_agent
    }
    
    # Detect browser
    if "Chrome" in user_agent and "Edg" not in user_agent:
        device_info["browser"] = "Chrome"
    elif "Firefox" in user_agent:
        device_info["browser"] = "Firefox"
    elif "Safari" in user_agent and "Chrome" not in user_agent:
        device_info["browser"] = "Safari"
    elif "Edg" in user_agent:
        device_info["browser"] = "Edge"
    else:
        device_info["browser"] = "Unknown"
    
    # Detect OS
    if "Windows" in user_agent:
        device_info["os"] = "Windows"
    elif "Mac" in user_agent or "macOS" in user_agent:
        device_info["os"] = "macOS"
    elif "Linux" in user_agent:
        device_info["os"] = "Linux"
    elif "Android" in user_agent:
        device_info["os"] = "Android"
    elif "iOS" in user_agent or "iPhone" in user_agent or "iPad" in user_agent:
        device_info["os"] = "iOS"
    else:
        device_info["os"] = "Unknown"
    
    # Detect device type
    if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
        device_info["device_type"] = "mobile"
    elif "iPad" in user_agent or ("Tablet" in user_agent):
        device_info["device_type"] = "tablet"
    else:
        device_info["device_type"] = "desktop"
    
    return device_info

async def create_login_session(email: str, device_id: str, device_info: Optional[dict] = None):
    """
    P1: Create a new login session with multi-device support (max 3 sessions).
    
    If user already has 3 active sessions, the oldest one is automatically removed.
    """
    try:
        # Generate secure session token
        session_token = str(uuid.uuid4()) + "-" + str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        now = datetime.now(timezone.utc)
        
        # P1: Count active sessions (non-expired) for this user
        active_sessions_count = await db.login_sessions.count_documents({
            "user_email": email,
            "expires_at": {"$gt": now.isoformat()}
        })
        
        logger.info(f"User {email} has {active_sessions_count} active session(s)")
        
        # P1: If user has 3 or more active sessions, remove the oldest one
        if active_sessions_count >= 3:
            # Find oldest session (by created_at)
            oldest_session = await db.login_sessions.find_one(
                {"user_email": email, "expires_at": {"$gt": now.isoformat()}},
                sort=[("created_at", 1)]  # ASC: oldest first
            )
            
            if oldest_session:
                await db.login_sessions.delete_one({"_id": oldest_session["_id"]})
                logger.info(
                    f"P1: Removed oldest session for {email} (device: {oldest_session.get('device_id', 'unknown')}) "
                    f"to make room for new session (max 3 sessions)"
                )
        
        # Create new session data
        session_dict = {
            "user_email": email,
            "session_token": session_token,
            "device_id": device_id,
            "device_info": device_info or {},  # P1: Store device info (browser, OS, etc.)
            "expires_at": expires_at.isoformat(),
            "created_at": now.isoformat(),
            "last_used": now.isoformat()
        }
        
        # Insert new session
        await db.login_sessions.insert_one(session_dict)
        
        logger.info(
            f"P1: Created new session for {email} on device {device_id} "
            f"(total active sessions: {active_sessions_count + 1 if active_sessions_count < 3 else 3})"
        )
        
        # Update user's last_login
        await db.pro_users.update_one(
            {"email": email},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )
        
        return session_token
        
    except Exception as e:
        logger.error(f"Error creating login session: {e}")
        return None

async def validate_session_token(session_token: str):
    """Validate a session token and return user email if valid"""
    try:
        session = await db.login_sessions.find_one({"session_token": session_token})
        
        if not session:
            return None
            
        # Check expiration
        expires_at = session.get('expires_at')
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at).replace(tzinfo=timezone.utc)
        elif isinstance(expires_at, datetime) and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        now = datetime.now(timezone.utc)
        
        if expires_at < now:
            # Session expired, clean it up
            await db.login_sessions.delete_one({"session_token": session_token})
            return None
            
        # Update last_used
        await db.login_sessions.update_one(
            {"session_token": session_token},
            {"$set": {"last_used": datetime.now(timezone.utc)}}
        )
        
        return session.get('user_email')
        
    except Exception as e:
        logger.error(f"Error validating session token: {e}")
        return None

def sanitize_schema_ai_response(response: str) -> str:
    """
    Clean AI responses specifically for geometric schema generation.
    More careful handling to preserve geometric data.
    """
    try:
        # Remove leading/trailing whitespace
        response = response.strip()
        
        # Find JSON boundaries
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            logger.warning(f"No JSON found in schema AI response: {response[:200]}...")
            return '{"schema": null}'
        
        json_content = response[json_start:json_end]
        
        # Gentle cleaning for schemas - avoid aggressive replacements
        # Only fix obvious issues
        json_content = json_content.replace('\\n', ' ')     # Replace literal newlines
        json_content = json_content.replace('\\t', ' ')     # Replace literal tabs
        json_content = re.sub(r'\s+', ' ', json_content)    # Normalize whitespace
        
        # Try to parse as-is first
        try:
            parsed = json.loads(json_content)
            return json.dumps(parsed)  # Re-serialize to ensure valid JSON
        except json.JSONDecodeError as e:
            logger.warning(f"Schema JSON needs cleaning: {e}")
            
            # More aggressive cleaning only if needed
            json_content = json_content.replace('\\\\', '\\')
            json_content = re.sub(r'\\[a-zA-Z]', ' ', json_content)  # Remove problematic escapes
            
            try:
                parsed = json.loads(json_content)
                logger.info("Schema JSON recovered after cleaning")
                return json.dumps(parsed)
            except Exception as e2:
                logger.error(f"Schema JSON still invalid: {e2}")
                return '{"schema": null}'
                
    except Exception as e:
        logger.error(f"Error sanitizing schema AI response: {e}")
        return '{"schema": null}'

def sanitize_ai_response(response: str) -> str:
    """
    Clean and validate AI JSON responses to handle common formatting issues.
    Ensures consistent JSON structure for schema processing.
    """
    try:
        # Remove any leading/trailing whitespace and non-JSON text
        response = response.strip()
        
        # Find JSON boundaries
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            logger.warning(f"No JSON found in AI response: {response[:200]}...")
            return '{"schema": null}'
        
        json_content = response[json_start:json_end]
        
        # PHASE 3 FIX: Clean common JSON formatting issues
        # Fix single quotes to double quotes
        json_content = re.sub(r"'([^']*)':", r'"\1":', json_content)  # Fix keys
        json_content = re.sub(r":\s*'([^']*)'", r': "\1"', json_content)  # Fix values
        
        # Fix missing commas (basic pattern)
        json_content = re.sub(r'}\s*{', '}, {', json_content)
        json_content = re.sub(r']\s*"', '], "', json_content)
        
        # Validate JSON syntax
        try:
            parsed = json.loads(json_content)
            
            # Ensure standard "schema" key (handle various formats)
            if "schéma" in parsed:
                parsed["schema"] = parsed.pop("schéma")
            elif "schema_geometrique" in parsed:
                parsed["schema"] = parsed.pop("schema_geometrique")
            
            # PHASE 3 FIX: Validate schema completeness
            if "schema" in parsed and parsed["schema"] is not None:
                schema = parsed["schema"]
                if isinstance(schema, dict):
                    points = schema.get("points", [])
                    labels = schema.get("labels", {})
                    
                    # Check if all points have coordinates
                    missing_coords = [p for p in points if p not in labels]
                    if missing_coords:
                        logger.warning(
                            "Schema has points without coordinates",
                            module_name="sanitize",
                            func_name="sanitize_ai_response",
                            missing_coords=missing_coords,
                            available_coords=list(labels.keys())
                        )
                        # Try to add default coordinates for missing points
                        for i, point in enumerate(missing_coords):
                            labels[point] = f"({i*2},{i*2})"  # Simple fallback
                        schema["labels"] = labels
                        logger.info(f"Added fallback coordinates for points: {missing_coords}")
            
            # Return cleaned JSON
            return json.dumps(parsed)
            
        except json.JSONDecodeError as e:
            logger.error(
                "Invalid JSON syntax in AI response after cleaning",
                module_name="sanitize",
                func_name="sanitize_ai_response",
                error=str(e),
                json_preview=json_content[:200]
            )
            return '{"schema": null}'
            
    except Exception as e:
        logger.error(f"Error sanitizing AI response: {e}")
        return '{"schema": null}'

@log_execution_time("generate_geometry_schema_with_ai")
async def generate_geometry_schema_with_ai(enonce: str) -> str:
    """
    Makes a second AI call to generate a geometry schema based on the exercise text.
    Returns the JSON string of the schema.
    """
    logger = get_logger()
    logger.debug(
        "Starting geometry schema generation",
        module_name="schema",
        func_name="generate_geometry_schema_with_ai",
        enonce_length=len(enonce),
        enonce_preview=enonce[:100]
    )
    
    try:
        # Create LLM chat instance with faster model
        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"schema_gen_{uuid.uuid4()}",
            system_message="""En tant que moteur de génération de schémas géométriques PRÉCIS, tu dois créer un schéma qui CORRESPOND EXACTEMENT à l'énoncé de l'exercice.

**RÈGLE ABSOLUE** : Le schéma DOIT utiliser les MÊMES noms de points et dimensions que l'énoncé !

**Instructions critiques :**
1. LIS attentivement l'énoncé pour identifier TOUS les noms de points mentionnés
2. UTILISE exactement ces noms dans le schéma (pas de A,B,C génériques !)
3. RESPECTE toutes les dimensions numériques mentionnées
4. RESPECTE les propriétés géométriques (angles droits, etc.)

**Exemples de correspondance correcte :**
- Énoncé: "triangle DEF rectangle en E" → points: ["D", "E", "F"], angle droit en E
- Énoncé: "AB = 5 cm et BC = 12 cm" → segments: [["A","B",{"longueur":"5 cm"}], ["B","C",{"longueur":"12 cm"}]]
- Énoncé: "triangle GHI" → points: ["G", "H", "I"] (pas A, B, C !)

**Format JSON requis :**
{
    "schema": {
        "type": "triangle_rectangle",
        "points": ["points_from_enonce"],
        "segments": [["point1","point2",{"longueur":"value_from_enonce"}]],
        "angles": [["point",{"angle_droit": true}]]
    }
}

**Types supportés** : triangle, triangle_rectangle, carre, rectangle, cercle
**INTERDIT** : Utiliser A,B,C quand l'énoncé mentionne d'autres lettres !
**OBLIGATOIRE** : Correspondance exacte énoncé ↔ schéma"""
        ).with_model("openai", "gpt-4o")
        
        # Create focused prompt for schema generation with STRICT format requirements  
        prompt = f"""
**ÉNONCÉ DE L'EXERCICE :**
"{enonce}"

Tu dois analyser cet énoncé et générer un schéma géométrique qui CORRESPOND EXACTEMENT à l'énoncé.

**RÈGLES CRITIQUES :**
1. UTILISE LES MÊMES NOMS DE POINTS que dans l'énoncé (si l'énoncé dit "triangle DEF", utilise D, E, F)
2. RESPECTE LES DIMENSIONS mentionnées dans l'énoncé
3. RESPECTE LES PROPRIÉTÉS géométriques (angle droit, etc.)

**FORMAT JSON EXACT :**
```json
{{
    "schema": {{
        "type": "triangle_rectangle",
        "points": ["D", "E", "F"],
        "segments": [["D", "E", {{"longueur": "5 cm"}}], ["E", "F", {{"longueur": "12 cm"}}]],
        "angles": [["E", {{"angle_droit": true}}]]
    }}
}}
```

**ANALYSE OBLIGATOIRE :**
1. EXTRAIRE tous les noms de points mentionnés (ex: "triangle DEF" → points D, E, F)
2. EXTRAIRE toutes les dimensions (ex: "DE = 5 cm" → segment DE longueur 5)
3. EXTRAIRE les propriétés géométriques (ex: "rectangle en E" → angle droit en E)
4. DÉTERMINER le type de figure (triangle, triangle_rectangle, rectangle, etc.)

**GÉNÉRATION OBLIGATOIRE :**
Si l'énoncé mentionne une figure géométrique (triangle, rectangle, cercle, etc.), tu DOIS générer un schéma complet.

**RÈGLES TECHNIQUES :**
1. TOUJOURS utiliser la clé "schema" (sans accent)
2. JAMAIS retourner {{"schema": null}} si l'énoncé contient de la géométrie
3. Types valides : "triangle", "triangle_rectangle", "rectangle", "carre", "cercle"
4. Format des segments : [["point1", "point2", {{"longueur": "valeur"}}]]
5. Format des angles : [["point", {{"angle_droit": true}}]]

**EXEMPLE CONCRET :**
Énoncé: "triangle DEF rectangle en E, DE = 5 cm, EF = 12 cm"
→ DOIT générer: {{"schema": {{"type": "triangle_rectangle", "points": ["D","E","F"], "segments": [["D","E",{{"longueur":"5 cm"}}], ["E","F",{{"longueur":"12 cm"}}]], "angles": [["E",{{"angle_droit":true}}]]}}}}

Réponds UNIQUEMENT avec le JSON complet, JAMAIS null pour un énoncé géométrique.
"""

        user_message = UserMessage(text=prompt)
        
        # Set shorter timeout for faster response
        import asyncio
        response = await asyncio.wait_for(
            chat.send_message(user_message), 
            timeout=15.0  # 15 seconds max for schema generation
        )
        
        # Sanitize and validate the AI response with schema-specific cleaning
        sanitized_response = sanitize_schema_ai_response(response)
        
        # Verify we have a valid schema
        try:
            parsed = json.loads(sanitized_response)
            if parsed.get("schema") is not None:
                schema_type = parsed['schema'].get('type', 'unknown')
                logger.info(
                    "Valid schema generated successfully",
                    module_name="schema",
                    func_name="generate_geometry_schema_with_ai",
                    schema_type=schema_type,
                    status="success"
                )
                log_ai_generation("second_pass_success", True, schema_type=schema_type)
            else:
                logger.debug("No schema needed for this exercise")
                
            return sanitized_response
        except json.JSONDecodeError as e:
            logger.warning(
                "Failed to parse sanitized schema response",
                module_name="schema",
                func_name="generate_geometry_schema_with_ai",
                error=str(e),
                status="parse_error"
            )
            return '{"schema": null}'
        
    except Exception as e:
        logger.error(f"Error in AI geometry generation: {e}")
        return "{}"  # Return empty JSON object on error

@log_execution_time("generate_exercises_with_ai")
async def generate_exercises_with_ai(matiere: str, niveau: str, chapitre: str, type_doc: str, difficulte: str, nb_exercices: int) -> List[Exercise]:
    """Generate exercises using AI - New architecture for Mathématiques"""
    logger = get_logger()
    
    # 🎯 NOUVELLE ARCHITECTURE MATHÉMATIQUES
    if matiere == "Mathématiques":
        # This function returns List[Exercise] already
        return await generate_math_exercises_new_architecture(
            niveau, chapitre, difficulte, nb_exercices
        )
    
    # 🎯 RESET DIVERSITY TRACKING for new document generation (autres matières)
    if hasattr(generate_exercises_with_ai, 'used_document_types'):
        generate_exercises_with_ai.used_document_types = []
    
    # Log input parameters
    logger.info(
        "Starting AI exercise generation",
        module_name="generation",
        func_name="generate_exercises_with_ai",
        matiere=matiere,
        niveau=niveau,
        chapitre=chapitre,
        type_doc=type_doc,
        difficulte=difficulte,
        nb_exercices=nb_exercices
    )
    
    # Level-specific guidance
    niveau_guidance = {
        "6e": "Niveau débutant - vocabulaire simple, calculs basiques, exemples concrets du quotidien",
        "5e": "Niveau intermédiaire - introduction de concepts plus abstraits mais restant accessibles", 
        "4e": "Niveau confirmé - calculs plus complexes, raisonnement mathématique développé",
        "3e": "Niveau avancé - préparation au lycée, concepts abstraits, démonstrations"
    }
    
    # PROMPTS IA SPÉCIALISÉS PAR MATIÈRE by subject
    chapter_examples = {
        # Mathématiques
        "Volumes": {
            "6e": "Utiliser des objets du quotidien (boîtes, bouteilles), unités simples (cm³, L), calculs avec nombres entiers ou décimaux simples",
            "5e": "Prismes et cylindres, conversions d'unités, calculs avec fractions simples",
            "4e": "Pyramides et cônes, volumes composés, problèmes de proportionnalité",
            "3e": "Solides de révolution, problèmes d'optimisation, calculs complexes"
        },
        "Nombres relatifs": {
            "5e": "Introduction intuitive avec température, altitude, calculs simples",
            "4e": "Opérations complètes, règles des signes, problèmes contextualisés",
            "3e": "Applications complexes, équations, inéquations"
        },
        
        # Français
        "Récits d'aventures": {
            "6e": "Lecture d'extraits d'aventures, compréhension du schéma narratif, vocabulaire de l'action et du suspense"
        },
        "Grammaire - La phrase": {
            "6e": "Types et formes de phrases, ponctuation, reconnaissance sujet/verbe/complément"
        },
        "Le voyage et l'aventure : pourquoi aller vers l'inconnu ?": {
            "5e": "Analyse de textes narratifs, étude des motifs du départ, expression écrite créative"
        },
        "Dire l'amour": {
            "4e": "Poésie lyrique, registres de langue, figures de style, expression des sentiments"
        },
        "Se raconter, se représenter": {
            "3e": "Autobiographie, mémoires, analyse de l'écriture de soi, réflexion sur l'identité"
        },
        
        # Physique-Chimie
        "Matière, mouvement, énergie, information": {
            "6e": "États de la matière, observations simples, classification des objets"
        },
        "Organisation et transformations de la matière": {
            "5e": "Mélanges et corps purs, changements d'état, transformations chimiques simples",
            "4e": "Atomes et molécules, réactions chimiques, conservation de la masse",
            "3e": "Ions, pH, électrolyse, synthèse chimique"
        },
        "Mouvement et interactions": {
            "5e": "Description du mouvement, vitesse, interactions mécaniques",
            "4e": "Référentiel, relativité du mouvement, forces et effets",
            "3e": "Gravitation, poids et masse, interactions fondamentales"
        }
    }
    
    # Get specific guidance
    level_guide = niveau_guidance.get(niveau, "Adapter au niveau demandé")
    chapter_guide = chapter_examples.get(chapitre, {}).get(niveau, "Respecter le programme officiel")
    
    # Build dynamic prompt context
    prompt_context = build_prompt_context(matiere, niveau, chapitre)
    
    # Math formatting rules for consistent LaTeX output
    MATH_FORMATTING_RULE = """
RÈGLE MATHÉMATIQUES OBLIGATOIRE - RESPECTER ABSOLUMENT:
- Toutes les fractions: \\frac{numérateur}{dénominateur} 
- Toutes les puissances: x^{exposant}
- Toutes les racines: \\sqrt{contenu}
- INTERDICTION ABSOLUE: "X de Y", "X par Y", "X/Y", HTML (<sup>, <sub>, <math>), séparateurs (-->, /)

EXEMPLES CORRECTS:
✅ \\frac{7}{8} + \\frac{4}{5} = \\frac{35+32}{40} = \\frac{67}{40}
✅ Calculer \\frac{15}{20} et simplifier
✅ Résoudre \\frac{2x}{5} = \\frac{3}{10}

EXEMPLES INTERDITS:
❌ 7 de 8, 7 par 8, 7/8
❌ 15 de 20, 2x par 5
❌ <sup>7</sup>/<sub>8</sub>

CRITIQUE: Utilise UNIQUEMENT la notation LaTeX \\frac{}{} pour TOUTES les fractions sans exception.
"""
    
    # Subject-specific instructions with dynamic prompt
    subject_instructions = {
        "Mathématiques": f"""
{prompt_context['prompt_intro']}. 

Crée {nb_exercices} exercices pour un élève de {niveau} en {matiere}, en restant strictement sur le chapitre suivant: "{chapitre}". 
Chaque exercice doit avoir une difficulté {difficulte}. Respecte parfaitement le programme scolaire français pour ce niveau et cette compétence.

{MATH_FORMATTING_RULE}

**Instructions cruciales** :
1. **DIVERSITÉ DES POINTS** : Utilise des lettres DIFFÉRENTES pour chaque exercice (D,E,F puis M,N,P puis X,Y,Z etc.) - JAMAIS tous A,B,C !
2. Utilise des **valeurs numériques différentes et variées** pour chaque exercice (pas de répétition des mêmes données).
3. Le schéma doit toujours être placé dans `"donnees.schema"` et jamais dans `"enonce"`.
4. L’énoncé doit contenir uniquement du texte lisible pour l’élève et sa formulation doit être claire comme il serait lu dans un manuel de mathématique à leur niveau.
5. **COHÉRENCE ÉNONCÉ-SCHÉMA** : Les points mentionnés dans l'énoncé DOIVENT être les mêmes que dans le schéma !
6. Le schéma doit suivre une structure claire (type, points, labels, segments, angles, etc.).
7. Les exercices ne doivent pas être similaires dans la consigne, varier comme dans un manuel d'exercice de mathématique

 

**Format JSON attendu pour chaque exercice** :
{{
  "titre": "Titre concis",
  "enonce": "Dans le triangle DEF rectangle en E, DE = 5 cm et EF = 12 cm. Calculer la longueur DF.",
  "type": "geometry",
  "difficulte": "{difficulte}",
  "donnees": {{
    "schema": {{
      "type": "triangle_rectangle",
      "points": ["D", "E", "F"],
      "labels": {{"D": "(0,8)", "E": "(0,0)", "F": "(6,0)"}},
      "segments": [["D","E", {{"longueur": "5 cm"}}], ["E","F", {{"longueur": "12 cm"}}]],
      "angles": [["E", {{"angle_droit": true}}]]
    }}
  }},
  "solution": {{
    "etapes": ["Appliquer le théorème de Pythagore", "DF² = DE² + EF²", "DF² = 5² + 12² = 25 + 144 = 169", "DF = √169 = 13 cm"],
    "resultat": "DF = 13 cm"
  }},
  "bareme": [
    {{"etape": "Méthode", "points": 2.0}},
    {{"etape": "Résultat", "points": 2.0}}
  ]
}}

Réponds uniquement avec un tableau JSON contenant tous les exercices, sans texte ni explication supplémentaire.
"""
,

        "Français": f"""{prompt_context['prompt_intro']}.

Génère {nb_exercices} exercices pour un élève de {niveau} en {matiere}, sur le chapitre suivant: "{chapitre}".
Chaque exercice doit avoir une difficulté {difficulte}. Respecte parfaitement le programme scolaire français pour ce niveau et cette compétence.

RÈGLES FRANÇAIS:
1. {level_guide}
2. Exercices variés : analyse, grammaire, expression écrite
3. Textes supports courts et adaptés au niveau {niveau}
4. Questions progressives et structurées
5. Respecter les attentes du programme pour "{chapitre}" """,

        "Physique-Chimie": f"""
{prompt_context['prompt_intro']}. 

Crée {nb_exercices} exercices de Physique-Chimie pour un élève de {niveau} sur le chapitre: "{chapitre}".
Chaque exercice doit avoir une difficulté {difficulte}. Respecte parfaitement le programme scolaire français.

RÈGLES PHYSIQUE-CHIMIE OBLIGATOIRES:
- Utilise des SITUATIONS CONCRÈTES et EXPÉRIMENTALES adaptées au niveau {niveau}
- Propose des CALCULS SIMPLES avec unités (m, kg, s, J, V, A, etc.)
- Privilégie l'OBSERVATION et l'EXPÉRIMENTATION
- Utilise le VOCABULAIRE SCIENTIFIQUE approprié au niveau
- Les réponses doivent être en 2-3 étapes maximum
- Donne des valeurs numériques RÉALISTES et VARIÉES

EXEMPLES par chapitre:
- "Organisation et transformations de la matière" : mélanges, corps purs, réactions chimiques, atomes/molécules
- "Mouvements et interactions" : vitesse, forces, frottements, gravité 
- "L'énergie et ses conversions" : énergie cinétique, potentielle, thermique, électrique
- "Des signaux pour observer et communiquer" : lumière, son, signaux électriques

FORMAT JSON REQUIS:
{{
    "exercises": [
        {{
            "type": "experimental",
            "enonce": "Énoncé avec situation expérimentale concrète",
            "icone": "atom",
            "solution": {{
                "etapes": ["Étape 1: Méthode/formule", "Étape 2: Application numérique"],
                "resultat": "Résultat final avec unité"
            }},
            "difficulte": "{difficulte}",
            "bareme": [
                {{"etape": "Méthode", "points": 1.5}},
                {{"etape": "Calcul", "points": 1.5}},
                {{"etape": "Résultat", "points": 1.0}}
            ]
        }}
    ]
}}
""",

        "SVT": f"""
{prompt_context['prompt_intro']}.

Crée {nb_exercices} exercices de SVT pour un élève de {niveau} sur le chapitre: "{chapitre}".
Chaque exercice doit avoir une difficulté {difficulte}. Respecte parfaitement le programme scolaire français.

RÈGLES SVT OBLIGATOIRES:
- Utilise des OBSERVATIONS et DONNÉES SCIENTIFIQUES réelles
- Privilégie l'ANALYSE et le RAISONNEMENT SCIENTIFIQUE
- Propose des SCHÉMAS BIOLOGIQUES simples quand pertinent 
- Utilise le VOCABULAIRE SCIENTIFIQUE adapté au niveau {niveau}
- Développe l'esprit critique et la démarche expérimentale
- Les questions doivent favoriser la RÉFLEXION plus que le calcul

EXEMPLES par chapitre:
- "Le vivant et son évolution" : classification, reproduction, génétique, évolution
- "Le corps humain et la santé" : nutrition, respiration, circulation, immunité
- "La planète Terre, l'environnement" : géologie, écosystèmes, climat, biodiversité

FORMAT JSON REQUIS:
{{
    "exercises": [
        {{
            "type": "analysis",
            "enonce": "Énoncé avec observation/document scientifique à analyser",
            "icone": "leaf",
            "solution": {{
                "etapes": ["Étape 1: Observation", "Étape 2: Analyse", "Étape 3: Conclusion"],
                "resultat": "Conclusion scientifique argumentée"
            }},
            "difficulte": "{difficulte}",
            "bareme": [
                {{"etape": "Observation", "points": 1.0}},
                {{"etape": "Analyse", "points": 2.0}},
                {{"etape": "Conclusion", "points": 1.0}}
            ]
        }}
    ]
}}
""",

        "Géographie": f"""
{prompt_context['prompt_intro']}.

🗺️ SPÉCIALISTE GÉOGRAPHIE - DIVERSIFICATION OBLIGATOIRE DES DOCUMENTS

Crée {nb_exercices} exercices de Géographie pour un élève de {niveau} sur le chapitre: "{chapitre}".
Chaque exercice doit avoir une difficulté {difficulte}. Respecte parfaitement le programme scolaire français.

⚠️ RÈGLE ABSOLUE - DIVERSIFICATION OBLIGATOIRE :
- CHAQUE EXERCICE DOIT UTILISER UN TYPE DE DOCUMENT DIFFÉRENT
- INTERDICTION FORMELLE d'utiliser le même type 2 fois
- ANALYSER le contenu pour choisir le document le PLUS APPROPRIÉ

TYPES DE DOCUMENTS DISPONIBLES (À VARIER OBLIGATOIREMENT) :

1. "carte_france" → Questions sur France, régions, villes françaises
   Exemple : "Localise Paris, Lyon, Marseille sur une carte administrative"

2. "carte_europe" → Questions sur pays européens, capitales, UE
   Exemple : "Identifie l'Allemagne, l'Italie et leurs capitales"

3. "carte_asie" → Questions sur Asie, Chine, Japon, Inde
   Exemple : "Compare Tokyo et Beijing sur une carte d'Asie"

4. "carte_amerique_nord" → Questions USA, Canada, Mexique
   Exemple : "Analyse l'urbanisation de la côte est américaine"

5. "carte_afrique" → Questions Afrique, Sahara, pays africains
   Exemple : "Localise le désert du Sahara et le fleuve Nil"

6. "carte_monde" → Questions globales, continents, océans
   Exemple : "Identifie les 5 océans sur un planisphère"

STRATÉGIE DE DIVERSIFICATION FORCÉE :
- Exercice 1 : Choisir le type le PLUS PERTINENT selon le contenu
- Exercice 2 : Choisir un type DIFFÉRENT du précédent
- Exercice 3 : Encore DIFFÉRENT des 2 précédents
- Exercice 4 : DIFFÉRENT des 3 précédents

EXEMPLES CONCRETS DE DIVERSIFICATION :

Pour "{chapitre}" niveau {niveau} :

BATCH TYPE A - Chapitre sur la France :
- Ex1: carte_france + "Localise ta région sur la carte"
- Ex2: carte_europe + "Situe la France en Europe"  
- Ex3: carte_monde + "Place la France dans le monde"
- Ex4: carte_france + "Analyse les métropoles françaises"

BATCH TYPE B - Chapitre sur l'urbanisation mondiale :
- Ex1: carte_monde + "Identifie les mégalopoles mondiales"
- Ex2: carte_asie + "Étudie l'urbanisation au Japon"
- Ex3: carte_amerique_nord + "Analyse les villes américaines"
- Ex4: carte_europe + "Compare Paris, Londres, Berlin"

FORMAT JSON OBLIGATOIRE AVEC DIVERSIFICATION :
{{
    "exercises": [
        {{
            "type": "cartographic",
            "enonce": "Exercice utilisant un premier type de document géographique approprié",
            "icone": "map",
            "document_attendu": {{
                "type": "carte_france",
                "doit_afficher": ["éléments spécifiques"],
                "langue": "français",
                "description": "Description précise du document"
            }},
            "solution": {{
                "etapes": ["Étape 1: Lecture", "Étape 2: Analyse"],
                "resultat": "Conclusion géographique"
            }},
            "difficulte": "{difficulte}"
        }},
        {{
            "type": "cartographic",
            "enonce": "Exercice utilisant un DEUXIÈME type DIFFÉRENT",
            "icone": "compass",
            "document_attendu": {{
                "type": "carte_europe",
                "doit_afficher": ["pays", "capitales"],
                "langue": "français", 
                "description": "Carte européenne avec focus spécifique"
            }},
            "solution": {{
                "etapes": ["Étape 1: Lecture", "Étape 2: Analyse"],
                "resultat": "Conclusion géographique"
            }},
            "difficulte": "{difficulte}"
        }},
        {{
            "type": "geographic",
            "enonce": "Exercice utilisant un TROISIÈME type DIFFÉRENT",
            "icone": "globe",
            "document_attendu": {{
                "type": "carte_monde",
                "doit_afficher": ["continents", "océans"],
                "langue": "français",
                "description": "Planisphère mondial"
            }},
            "solution": {{
                "etapes": ["Étape 1: Lecture", "Étape 2: Analyse"],
                "resultat": "Conclusion géographique"
            }},
            "difficulte": "{difficulte}"
        }},
        {{
            "type": "urban",
            "enonce": "Exercice utilisant un QUATRIÈME type DIFFÉRENT",
            "icone": "building-2", 
            "document_attendu": {{
                "type": "carte_asie",
                "doit_afficher": ["grandes villes", "densité"],
                "langue": "français",
                "description": "Carte asiatique pour analyse urbaine"
            }},
            "solution": {{
                "etapes": ["Étape 1: Lecture", "Étape 2: Analyse"],
                "resultat": "Conclusion géographique"
            }},
            "difficulte": "{difficulte}"
        }}
    ]
}}

CONTRAINTES ABSOLUES :
✅ JAMAIS le même "type" dans "document_attendu" entre exercices
✅ Analyser le chapitre "{chapitre}" pour choisir les types pertinents
✅ Varier : carte_france, carte_europe, carte_asie, carte_amerique_nord, carte_afrique, carte_monde
✅ Créer des énoncés cohérents avec le type de document choisi
✅ {nb_exercices} exercices = {nb_exercices} types de documents DIFFÉRENTS garantis

RÉSULTAT ATTENDU CRITIQUE :
- PDF avec {nb_exercices} cartes visuellement DIFFÉRENTES
- Chaque exercice avec son document spécifique et approprié
- Diversité géographique maximale dans le même batch
- Fin des répétitions de cartes identiques
"""
    }
    
    
    # Use the instruction (specialized or generic)
    # system_msg is already set above
    # GET THE SPECIALIZED INSTRUCTION FOR THE SUBJECT
    instruction = subject_instructions.get(matiere)
    
    if instruction:
        # Use specialized prompt
        logger.info(
            "🗺️ Geography subject activated with advanced document integration",
            module_name="generation",
            func_name="geography_activation",
            features_enabled=["specialized_prompts", "document_search", "cartographic_exercises"],
            document_sources=["wikimedia_commons", "validated_cache", "fallback_system"],
            supported_document_types=["carte_france", "carte_monde", "carte_europe", "planisphere", "carte_thematique"]
        )
        system_msg = instruction
    else:
        # Fallback: Create a generic prompt for subjects without specialized prompts
        logger.warning(f"⚠️ No specialized prompt found for {matiere}, using generic prompt")
        instruction = f"""
{prompt_context['prompt_intro']}.

Crée {nb_exercices} exercices de {matiere} pour un élève de {niveau} sur le chapitre: "{chapitre}".
Chaque exercice doit avoir une difficulté {difficulte}. Respecte parfaitement le programme scolaire français.

RÈGLES GÉNÉRALES:
- Utilise un vocabulaire adapté au niveau {niveau}
- Propose des questions variées et progressives
- Inclus des situations concrètes quand pertinent
- Structure tes réponses en étapes claires
- Respecte les attentes pédagogiques françaises

FORMAT JSON REQUIS:
{{
    "exercises": [
        {{
            "type": "general",
            "enonce": "Énoncé de l'exercice adapté au niveau",
            "icone": "book-open",
            "solution": {{
                "etapes": ["Étape 1: Méthode", "Étape 2: Application"],
                "resultat": "Réponse finale expliquée"
            }},
            "difficulte": "{difficulte}",
            "bareme": [
                {{"etape": "Méthode", "points": 2.0}},
                {{"etape": "Application", "points": 2.0}}
            ]
        }}
    ]
}}
"""
        system_msg = instruction
    
    # Create LLM chat instance with faster model
    chat = LlmChat(
        api_key=emergent_key,
        session_id=f"exercise_gen_{uuid.uuid4()}",
        system_message=f"""{system_msg}

JSON OBLIGATOIRE:
{{
  "exercises": [
    {{
      "type": "ouvert",
      "enonce": "Énoncé concis et clair",
      "difficulte": "{difficulte}",
      "solution": {{
        "etapes": ["Étape 1", "Étape 2"],
        "resultat": "Résultat final"
      }},
      "bareme": [
        {{"etape": "Méthode", "points": 2.0}},
        {{"etape": "Résultat", "points": 2.0}}
      ]
    }}
  ]
}}"""
    ).with_model("openai", "gpt-4o")
    
    # Create concise prompt for faster generation
    examples = {
        # Mathématiques
        "Volumes": "Calculer volume pavé 4×3×2 cm",
        "Nombres relatifs": "Calculer -5 + 3 - (-2)",
        "Fractions": "Calculer 2/3 + 1/4",
        "Géométrie - Figures planes": "Calculer périmètre rectangle 5×3 cm",
        
        # Français
        "Récits d'aventures": "Analyser un extrait de roman d'aventures",
        "Grammaire - La phrase": "Identifier sujet et verbe dans une phrase",
        "Conjugaison - Présent, passé, futur": "Conjuguer 'aller' au présent",
        "Le voyage et l'aventure : pourquoi aller vers l'inconnu ?": "Analyser les motivations d'un personnage",
        "Dire l'amour": "Étudier une strophe de poème lyrique",
        "Se raconter, se représenter": "Analyser un passage autobiographique",
        
        # Physique-Chimie
        "Organisation et transformations de la matière": "Identifier une transformation chimique",
        "Constitution et transformations de la matière": "Analyser la composition d'un mélange", 
        "Mouvements et interactions": "Calculer une vitesse moyenne",
        "Mouvement et interactions": "Étudier les forces sur un objet",
        "L'énergie et ses conversions": "Convertir différentes formes d'énergie",
        "L'énergie : conversions et transferts": "Calculer l'énergie cinétique",
        "Des signaux pour observer et communiquer": "Analyser la propagation de la lumière",
        "Ondes et signaux": "Étudier les caractéristiques d'une onde",
        
        # SVT
        "La planète Terre, l'environnement et l'action humaine": "Analyser l'impact humain sur un écosystème",
        "Le vivant et son évolution": "Classer des espèces selon leurs caractères",
        "Le corps humain et la santé": "Expliquer le mécanisme de la digestion",
        "La Terre, la vie et l'organisation du vivant": "Observer des cellules au microscope",
        "Les enjeux contemporains de la planète": "Étudier les changements climatiques",
        "Corps humain et santé": "Analyser le système immunitaire",
        
        # Géographie
        "Découvrir le(s) lieu(x) où j'habite": "Localiser sa commune sur une carte de France",
        "Se loger, travailler, se cultiver, avoir des loisirs": "Analyser l'organisation d'une ville française",
        "Satisfaire les besoins en énergie, en eau": "Étudier la répartition des ressources en eau en France",
        "Se déplacer - Moyens de transport": "Analyser les réseaux de transport français",
        "Communiquer d'un bout à l'autre du monde": "Localiser les grandes métropoles mondiales",
        "Mieux habiter - La ville de demain": "Comparer l'urbanisation en France et dans le monde",
        "Mieux habiter - Les espaces ruraux": "Analyser les mutations des espaces ruraux français",
        "L'urbanisation du monde": "Identifier les mégalopoles sur un planisphère",
        "Les mobilités humaines transnationales": "Analyser les flux migratoires sur une carte",
        "Des espaces transformés par la mondialisation": "Étudier les échanges commerciaux mondiaux"
    }
    
    example = examples.get(chapitre, f"Exercice {chapitre}")
    
    try:
        user_message = UserMessage(text=f"Génère {nb_exercices} exercices. Exemple: {example}")
        
        # FIRST PASS: Generate the exercise content
        logger.debug("Starting first AI pass - exercise content generation")
        log_ai_generation("first_pass_start", True)
        
        import asyncio
        response = await asyncio.wait_for(
            chat.send_message(user_message), 
            timeout=20.0  # 20 seconds max
        )
        
        logger.debug(f"First AI pass completed, response length: {len(response)} chars")
        
        # Parse the JSON response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in response")
            
        json_content = response[json_start:json_end]
        
        # JSON parsing with specific math symbol handling
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing error, attempting math symbol fix: {e}")
            
            # Fix common mathematical escape sequences that break JSON
            # These are often generated by AI when describing math formulas
            fixed_content = json_content
            fixed_content = fixed_content.replace('\\sqrt', 'sqrt')      # Remove backslash from sqrt
            fixed_content = fixed_content.replace('\\frac', 'frac')      # Remove backslash from frac
            fixed_content = fixed_content.replace('\\pi', 'π')           # Replace \pi with π
            fixed_content = fixed_content.replace('\\alpha', 'α')        # Replace \alpha with α
            fixed_content = fixed_content.replace('\\beta', 'β')         # Replace \beta with β
            fixed_content = fixed_content.replace('\\degree', '°')       # Replace \degree with °
            
            # Fix other common escapes
            fixed_content = re.sub(r'\\([a-zA-Z])', r'\1', fixed_content)  # Remove backslashes before letters
            
            try:
                data = json.loads(fixed_content)
                logger.info("JSON fixed by removing math symbol escapes")
            except json.JSONDecodeError as e2:
                logger.error(f"JSON still invalid after math fixes: {e2}")
                logger.error(f"Full problematic JSON: {json_content}")
                
                # If still broken, use fallback
                logger.warning("Using fallback exercise generation due to persistent JSON errors")
                return await generate_fallback_exercises(matiere, niveau, chapitre, difficulte, nb_exercices)
        
        # Convert to Exercise objects with professional content processing
        exercises = []
        for i, ex_data in enumerate(data.get("exercises", [])):
            # Enrich with icon before processing - PASS MATIERE FOR NEW SUBJECTS
            ex_data = enrich_exercise_with_icon(ex_data, chapitre, matiere)
            
            # Get the raw enonce
            enonce = ex_data.get("enonce", "").strip()
            
            # SECOND PASS: Generate geometric schema if this is a geometry exercise
            if matiere.lower() == "mathématiques":
                # Check if the exercise might need a geometric schema
                geometry_keywords = ["triangle", "cercle", "carré", "rectangle", "parallélogramme", 
                                   "géométrie", "figure", "pythagore", "thalès", "trigonométrie", 
                                   "angle", "périmètre", "aire", "longueur", "côté", "hypoténuse"]
                
                if any(keyword in enonce.lower() for keyword in geometry_keywords):
                    logger.info(
                        "Geometry keywords detected, starting schema generation",
                        module_name="generation",
                        func_name="schema_detection",
                        enonce_preview=enonce[:100],
                        detected_keywords=[kw for kw in geometry_keywords if kw in enonce.lower()]
                    )
                    
                    # Generate schema with second AI call
                    log_ai_generation("second_pass_start", True)
                    schema_json_str = await generate_geometry_schema_with_ai(enonce)
                    
                    # Add schema to separate field (CLEAN DESIGN - no more JSON in text!)
                    if len(schema_json_str.strip()) > 10:  # More robust check for content
                        try:
                            # Validate the generated schema with STANDARDIZED format
                            schema_data = json.loads(schema_json_str)
                            schema_content = schema_data.get("schema")  # STANDARD KEY: "schema"
                            
                            if schema_content is not None and isinstance(schema_content, dict) and "type" in schema_content:
                                # Store schema in separate field - KEEP ENONCE PURE TEXT!
                                ex_data["geometric_schema"] = schema_content
                                ex_data["type"] = "geometry"
                                
                                log_schema_processing(
                                    schema_type=schema_content.get('type', 'unknown'),
                                    success=True,
                                    exercise_id=str(i+1)
                                )
                                logger.info(
                                    "Schema successfully stored in separate field",
                                    module_name="generation",
                                    func_name="schema_storage",
                                    schema_type=schema_content.get('type'),
                                    exercise_id=i+1
                                )
                            else:
                                logger.debug("No geometric schema needed for this exercise")
                                log_ai_generation("second_pass_skip", True)
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"⚠️ Invalid JSON schema generated: {e}, keeping text-only exercise")
            
            # CRITICAL FIX: Clean the enonce by removing any residual JSON schema blocks
            enonce_clean = re.sub(r'\{\s*"sch[ée]ma".*?\}', "", enonce, flags=re.DOTALL)
            enonce_clean = re.sub(r'\{\s*"geometric_schema".*?\}', "", enonce_clean, flags=re.DOTALL)
            enonce_clean = enonce_clean.strip()
            
            # Remove any trailing newlines or multiple spaces caused by JSON removal
            enonce_clean = re.sub(r'\n\s*\n+', '\n\n', enonce_clean)  # Clean up multiple newlines
            enonce_clean = re.sub(r'\s+$', '', enonce_clean)  # Remove trailing whitespace
            
            if enonce_clean != enonce:
                logger.info(
                    "Cleaned JSON artifacts from enonce",
                    module_name="generation",
                    func_name="enonce_cleaning",
                    original_length=len(enonce),
                    cleaned_length=len(enonce_clean),
                    exercise_id=i+1
                )
            
            # THIRD PASS: Geographic document search for Geography exercises with DIVERSITY TRACKING
            if matiere.lower() == "géographie" and "document_attendu" in ex_data:
                # Initialize document tracking if not exists
                if not hasattr(generate_exercises_with_ai, 'used_document_types'):
                    generate_exercises_with_ai.used_document_types = []
                
                logger.info(
                    "🗺️ Geographic document search started",
                    module_name="generation",
                    func_name="document_search"
                )
                
                try:
                    # Passer l'énoncé à la recherche pour analyse intelligente
                    document_request = ex_data["document_attendu"].copy()
                    document_request["enonce"] = enonce_clean  # Ajouter l'énoncé pour analyse
                    document_request["avoid_types"] = generate_exercises_with_ai.used_document_types.copy()  # Force diversification
                    
                    document_metadata = await search_educational_document(document_request)
                    if document_metadata:
                        # Add document to exercise data
                        ex_data["document"] = document_metadata
                        ex_data["type"] = "cartographic"  # Ensure type is set for Geography
                        
                        # Track the document type used to avoid repetition
                        doc_title = document_metadata.get("titre", "Unknown")
                        generate_exercises_with_ai.used_document_types.append(doc_title)
                        
                        logger.info(
                            "✅ Educational document found and attached",
                            module_name="generation", 
                            func_name="document_attachment",
                            document_title=doc_title,
                            document_type=document_metadata.get("type", "Unknown"),
                            licence=document_metadata.get("licence", {}).get("type", "Unknown"),
                            exercise_id=i+1,
                            diversity_tracking=len(generate_exercises_with_ai.used_document_types),
                            content_based_selection=bool(document_request.get("enonce"))
                        )
                    else:
                        logger.warning(
                            "⚠️ No suitable geographic document found",
                            module_name="generation",
                            func_name="document_search_failure",
                            requested_type=ex_data["document_attendu"].get("type", "unknown")
                        )
                except Exception as e:
                    logger.error(
                        f"❌ Error during document search: {e}",
                        module_name="generation",
                        func_name="document_search_error",
                        exercise_id=i+1
                    )
            
            # Process the CLEANED enonce with centralized content processing
            processed_enonce = process_exercise_content(enonce_clean)
            
            # Process solution steps and result
            solution = ex_data.get("solution", {"etapes": ["Étape 1", "Étape 2"], "resultat": "Résultat"})
            
            # Process each solution step
            if "etapes" in solution and isinstance(solution["etapes"], list):
                solution["etapes"] = [
                    process_exercise_content(step) for step in solution["etapes"]
                ]
            
            # Process solution result
            if "resultat" in solution:
                solution["resultat"] = process_exercise_content(solution["resultat"])
            
            # CRITICAL FIX: Preserve geometric schema data and generate Base64 image
            schema_data = ex_data.get("geometric_schema", None)
            donnees_to_store = None
            schema_img_base64 = None
            
            if schema_data is not None:
                # Store schema in donnees for PDF processing
                donnees_to_store = {"schema": schema_data}
                logger.info(f"✅ Geometric schema data preserved in donnees field: {schema_data.get('type', 'unknown')}")
                
                # CRITICAL: Generate Base64 image for frontend immediately
                schema_img_base64 = process_schema_to_base64(schema_data)
                if schema_img_base64:
                    # Check if Base64 already has data: prefix to avoid double prefix
                    if not schema_img_base64.startswith('data:'):
                        schema_img_base64 = f"data:image/png;base64,{schema_img_base64}"
                    logger.info(
                        "Schema Base64 generated during exercise creation",
                        module_name="generation",
                        func_name="create_exercise",
                        exercise_id=i+1,
                        schema_type=schema_data.get('type'),
                        base64_length=len(schema_img_base64)
                    )
            
            exercise = Exercise(
                type=ex_data.get("type", "ouvert"),
                enonce=processed_enonce,
                donnees=donnees_to_store,  # ✅ PRESERVE SCHEMA DATA
                difficulte=ex_data.get("difficulte", difficulte),
                solution=solution,
                bareme=ex_data.get("bareme", [{"etape": "Méthode", "points": 2.0}, {"etape": "Résultat", "points": 2.0}]),
                seed=hash(processed_enonce) % 1000000,
                # Add icon and exercise type information
                exercise_type=ex_data.get("type", "text"),
                icone=ex_data.get("icone", EXERCISE_ICON_MAPPING["default"]),
                # NEW: Clean geometric schema field (separate from text)
                geometric_schema=ex_data.get("geometric_schema", None),
                # CRITICAL: Base64 schema image for frontend
                schema_img=schema_img_base64,
                # NEW: Geographic document for Geography exercises
                document=ex_data.get("document", None)
            )
            exercises.append(exercise)
        
        if not exercises:
            raise ValueError("No exercises generated")
            
        logger.info(
            "Successfully completed AI exercise generation",
            module_name="generation",
            func_name="generate_exercises_with_ai",
            total_exercises=len(exercises),
            geometry_exercises=sum(1 for ex in exercises if hasattr(ex, 'exercise_type') and ex.exercise_type == 'geometry'),
            approach="two_pass"
        )
        
        # 🗺️ LOGS DE DÉBOGAGE DIVERSITÉ GÉOGRAPHIE (optimisé)
        if matiere == "Géographie" and len(exercises) > 1:
            document_types_requested = []
            for exercise in exercises:
                if hasattr(exercise, 'document_attendu') and exercise.document_attendu:
                    if isinstance(exercise.document_attendu, dict):
                        doc_type = exercise.document_attendu.get('type', 'unknown')
                    else:
                        doc_type = str(exercise.document_attendu)
                    document_types_requested.append(doc_type)
            
            # Vérifier la diversité rapidement
            unique_types = len(set(document_types_requested))
            total_types = len(document_types_requested)
            
            if unique_types < total_types:
                logger.warning(f"🎯 Geography diversity: {unique_types}/{total_types} types uniques")
            else:
                logger.info(f"✅ Geography diversity: {unique_types}/{total_types} types différents")
        
        return exercises
        
    except asyncio.TimeoutError:
        logger.error("AI generation timeout - using fallback")
        return await generate_fallback_exercises(matiere, niveau, chapitre, difficulte, nb_exercices)
    except Exception as e:
        logger.error(f"Error generating exercises: {e}")
        return await generate_fallback_exercises(matiere, niveau, chapitre, difficulte, nb_exercices)


async def generate_math_exercises_new_architecture(
    niveau: str, 
    chapitre: str, 
    difficulte: str, 
    nb_exercices: int
) -> List[Exercise]:
    """
    Nouvelle architecture pour génération d'exercices mathématiques
    Sépare complètement logique mathématique (Python) de la rédaction (IA)
    """
    logger = get_logger()
    logger.info(
        "🎯 NOUVELLE ARCHITECTURE MATHÉMATIQUES - Démarrage",
        module_name="math_generation",
        func_name="generate_math_exercises_new_architecture",
        niveau=niveau,
        chapitre=chapitre,
        difficulte=difficulte,
        nb_exercices=nb_exercices
    )
    
    try:
        # ÉTAPE 1: Génération des specs mathématiques (Python pur, pas d'IA)
        logger.info("📊 ÉTAPE 1: Génération specs mathématiques (Python)")
        math_service = MathGenerationService()
        specs = math_service.generate_math_exercise_specs(
            niveau=niveau,
            chapitre=chapitre,
            difficulte=difficulte,
            nb_exercices=nb_exercices
        )
        
        logger.info(f"✅ {len(specs)} specs mathématiques générées")
        
        # ÉTAPE 2: Génération des textes IA (IA uniquement pour rédaction)
        logger.info("✍️ ÉTAPE 2: Génération textes IA (rédaction uniquement)")
        text_service = MathTextService()
        generated_exercises = await text_service.generate_text_for_specs(specs)
        
        logger.info(f"✅ {len(generated_exercises)} exercices avec texte générés")
        
        # ÉTAPE 3: Conversion vers le format Exercise existant
        logger.info("🔄 ÉTAPE 3: Conversion vers format Exercise")
        exercises = []
        
        for gen_ex in generated_exercises:
            exercise_dict = gen_ex.to_exercise_dict()
            
            # Enrichir avec le rendu SVG de la figure géométrique
            if gen_ex.spec.figure_geometrique:
                try:
                    from services.geometry_render_service import geometry_render_service
                    svg_data = geometry_render_service.render_figure_to_svg(
                        gen_ex.spec.figure_geometrique
                    )
                    if svg_data:
                        # Pour symétries: svg_data est un dict avec question/correction
                        # Pour autres types: svg_data est une string
                        if isinstance(svg_data, dict):
                            # Extraire les strings du dict et les mettre dans exercise_dict
                            exercise_dict["figure_svg"] = svg_data.get("figure_svg", "")
                            exercise_dict["figure_svg_question"] = svg_data.get("figure_svg_question", "")
                            exercise_dict["figure_svg_correction"] = svg_data.get("figure_svg_correction", "")
                            logger.info(f"✅ SVG (question + correction) généré pour {gen_ex.spec.figure_geometrique.type}")
                        else:
                            # Pour les autres types, c'est une string simple
                            exercise_dict["figure_svg"] = svg_data
                            # Pas de différence question/correction pour les autres types
                            exercise_dict["figure_svg_question"] = svg_data
                            exercise_dict["figure_svg_correction"] = svg_data
                            logger.info(f"✅ SVG généré pour {gen_ex.spec.figure_geometrique.type}")
                except Exception as e:
                    logger.warning(f"⚠️ Échec rendu SVG: {e}")
            
            # Créer l'objet Exercise
            exercise = Exercise(**exercise_dict)
            exercises.append(exercise)
        
        logger.info(f"✅ Conversion terminée - {len(exercises)} exercices prêts")
        logger.info("🎉 NOUVELLE ARCHITECTURE - Génération réussie")
        
        return exercises
        
    except ValueError as e:
        # 🚨 Erreurs de validation (ex: chapitre non mappé) → propager
        logger.error(f"❌ Erreur de validation: {e}")
        raise  # Propager l'erreur au lieu de fallback
        
    except Exception as e:
        logger.error(f"❌ Erreur nouvelle architecture: {e}", exc_info=True)
        logger.info("🔄 Fallback vers ancien système")
        
        # Fallback vers l'ancien système si échec
        return await generate_fallback_exercises(
            "Mathématiques", niveau, chapitre, difficulte, nb_exercices
        )


async def generate_fallback_exercises(matiere: str, niveau: str, chapitre: str, difficulte: str, nb_exercices: int) -> List[Exercise]:
    """Generate quick fallback exercises"""
    exercises = []
    
    # Quick templates based on chapter and subject
    templates = {
        # Mathématiques
        "Nombres relatifs": [
            "Calculer : {a} + {b} - ({c})",
            "Déterminer le signe de : {a} × {b}",
            "Résoudre : x + {a} = {b}"
        ],
        "Géométrie - Triangles et quadrilatères": [
            "Dans un triangle ABC, calculer l'aire sachant que AB = {a} cm, AC = {b} cm et l'angle A = 60°.",
            "Un parallélogramme ABCD a une base de {a} cm et une hauteur de {b} cm. Calculer son aire.",
            "Calculer le périmètre d'un rectangle de longueur {a} cm et largeur {b} cm."
        ],
        "Géométrie dans l'espace": [
            "Calculer le volume d'un cube d'arête {a} cm.",
            "Un parallélépipède rectangle a pour dimensions {a} cm × {b} cm × {c} cm. Calculer son volume.",
            "Calculer l'aire totale d'un cube d'arête {a} cm.",
            "Un cylindre a un rayon de {a} cm et une hauteur de {b} cm. Calculer son volume."
        ],
        "Volumes": [
            "Calculer le volume d'un pavé de dimensions {a} cm × {b} cm × {c} cm",
            "Une boîte cubique a une arête de {a} cm. Quel est son volume ?",
            "Convertir {a} L en cm³"
        ],
        "Théorème de Pythagore": [
            "Dans un triangle rectangle ABC rectangle en B, AB = {a} cm et BC = {b} cm. Calculer AC.",
            "Un triangle rectangle a des côtés de {a} cm et {b} cm. Calculer l'hypoténuse.",
            "Utiliser le théorème de Pythagore pour calculer le côté manquant : a = {a} cm, c = {b} cm."
        ],
        "Théorème de Thalès": [
            "Dans un triangle ABC, on trace une droite parallèle à BC. Si AB = {a} cm et la portion coupée = {b} cm, calculer les proportions.",
            "Deux droites parallèles coupent deux sécantes. Si les segments sont {a} cm et {b} cm d'un côté, et {c} cm de l'autre, calculer le quatrième segment.",
            "Utiliser le théorème de Thalès pour calculer une longueur manquante dans une configuration de triangles semblables."
        ],
        "Théorème de Thalès": [
            "Dans un triangle ABC, on trace une droite parallèle à BC. Si AB = {a} cm et la portion coupée = {b} cm, calculer les proportions.",
            "Deux droites parallèles coupent deux sécantes. Si les segments sont {a} cm et {b} cm d'un côté, et {c} cm de l'autre, calculer le quatrième segment.",
            "Utiliser le théorème de Thalès pour calculer une longueur manquante dans une configuration de triangles semblables."
        ],
        "Trigonométrie": [
            "Dans un triangle rectangle ABC rectangle en C, AB = {a} cm et AC = {b} cm. Calculer sin(A), cos(A) et tan(A).",
            "Un triangle rectangle a un angle de {a}° et une hypoténuse de {b} cm. Calculer les côtés adjacents et opposés.",
            "Utiliser les relations trigonométriques pour calculer la hauteur d'un bâtiment sachant que l'angle d'élévation est {a}° à {b} m de distance."
        ],
        "Fractions": [
            "Calculer : 1/{a} + 1/{b}",
            "Simplifier : {a}/{b}",
            "Comparer : 1/{a} et 1/{b}"
        ],
        
        # Français
        "Récits d'aventures": [
            "Identifier les étapes du schéma narratif dans un extrait",
            "Relever le vocabulaire de l'action dans le texte",
            "Expliquer les motivations du héros"
        ],
        "Grammaire - La phrase": [
            "Identifier le sujet et le verbe dans la phrase",
            "Transformer la phrase en phrase interrogative",
            "Corriger les erreurs de ponctuation"
        ],
        "Conjugaison - Présent, passé, futur": [
            "Conjuguer le verbe au temps demandé",
            "Identifier le temps des verbes soulignés",
            "Transformer la phrase au temps indiqué"
        ],
        
        # Physique-Chimie
        "Matière, mouvement, énergie, information": [
            "Classer ces objets selon leur état physique",
            "Identifier les propriétés de la matière observées",
            "Décrire les changements observés"
        ],
        "Organisation et transformations de la matière": [
            "Identifier s'il s'agit d'un mélange ou d'un corps pur",
            "Décrire la transformation observée",
            "Expliquer le changement d'état"
        ],
        "Mouvement et interactions": [
            "Décrire le mouvement de l'objet",
            "Identifier les forces qui s'exercent",
            "Calculer la vitesse moyenne"
        ]
    }
    
    template_list = templates.get(chapitre, [f"Exercice sur {chapitre}"])
    
    for i in range(nb_exercices):
        # Use modulo to cycle through templates
        template = template_list[i % len(template_list)]
        
        # Simple random values
        import random
        a, b, c = random.randint(2, 9), random.randint(2, 9), random.randint(2, 9)
        
        enonce = template.format(a=a, b=b, c=c)
        
        # CRITICAL: Apply content processing to fallback exercises too
        processed_enonce = process_exercise_content(enonce)
        
        # Create fallback exercise data and enrich with icon
        fallback_data = {
            "enonce": processed_enonce,
            "type": "text",
            "icone": "book-open"
        }
        fallback_data = enrich_exercise_with_icon(fallback_data, chapitre, matiere)
        
        exercise = Exercise(
            type="ouvert",
            enonce=fallback_data["enonce"],
            donnees=None,
            difficulte=difficulte,
            solution={
                "etapes": [
                    process_exercise_content("Appliquer la méthode du cours"), 
                    process_exercise_content("Effectuer les calculs")
                ],
                "resultat": process_exercise_content("Résultat à calculer")
            },
            bareme=[
                {"etape": "Méthode", "points": 2.0},
                {"etape": "Calcul", "points": 2.0}
            ],
            seed=random.randint(1000, 9999),
            exercise_type=fallback_data.get("type", "text"),
            icone=fallback_data.get("icone", "book-open")
        )
        exercises.append(exercise)
    
    return exercises

def format_exercises_for_export(exercises: List[dict], options: AdvancedPDFOptions) -> str:
    """Format exercises with advanced options"""
    formatted_content = []
    
    for i, exercise in enumerate(exercises, 1):
        exercise_parts = []
        
        # Exercise number with custom formatting
        if options.show_exercise_numbers:
            if options.question_numbering == "roman":
                number = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"][i-1] if i <= 10 else str(i)
            elif options.question_numbering == "letters":
                number = chr(64 + i) if i <= 26 else str(i)  # A, B, C...
            else:  # arabic or none
                number = str(i) if options.question_numbering == "arabic" else ""
            
            if number:
                exercise_parts.append(f"Exercice {number}")
        
        # Exercise content
        exercise_parts.append(exercise.get("enonce", ""))
        
        # Point values
        if options.show_point_values and exercise.get("bareme"):
            total_points = sum(item.get("points", 0) for item in exercise.get("bareme", []))
            if total_points > 0:
                exercise_parts.append(f"({total_points} points)")
        
        formatted_exercise = "\n".join(exercise_parts)
        
        # Exercise separator
        if options.exercise_separator == "line" and i < len(exercises):
            formatted_exercise += "\n" + "-" * 50 + "\n"
        elif options.exercise_separator == "space" and i < len(exercises):
            formatted_exercise += "\n\n"
        elif options.exercise_separator == "box":
            newline = '\n'
            lines = formatted_exercise.split(newline)
            box_width = len(lines[0]) + 4
            top_border = '┌' + '─' * box_width + '┐'
            bottom_border = '└' + '─' * box_width + '┘'
            content_lines = newline.join([f'│  {line}  │' for line in lines])
            formatted_exercise = f"{top_border}{newline}{content_lines}{newline}{bottom_border}"
        
        formatted_content.append(formatted_exercise)
    
    return "\n\n".join(formatted_content)

def format_solutions_for_export(exercises: List[dict], options: AdvancedPDFOptions) -> str:
    """Format solutions with advanced options"""
    formatted_content = []
    
    for i, exercise in enumerate(exercises, 1):
        solution_parts = []
        
        # Exercise number
        if options.show_exercise_numbers:
            if options.question_numbering == "roman":
                number = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"][i-1] if i <= 10 else str(i)
            elif options.question_numbering == "letters":
                number = chr(64 + i) if i <= 26 else str(i)
            else:
                number = str(i) if options.question_numbering == "arabic" else ""
            
            if number:
                solution_parts.append(f"Solution {number}")
        
        # Solution content
        solution = exercise.get("solution", {})
        if solution.get("etapes"):
            solution_parts.extend(solution["etapes"])
        if solution.get("resultat"):
            solution_parts.append(f"Résultat: {solution['resultat']}")
        
        formatted_solution = "\n".join(solution_parts)
        formatted_content.append(formatted_solution)
    
    return "\n\n".join(formatted_content)

def get_template_colors_and_fonts(template_config: dict) -> dict:
    """Get template colors and fonts based on style"""
    style_name = template_config.get('template_style', 'minimaliste')
    template_style = TEMPLATE_STYLES.get(style_name, TEMPLATE_STYLES['minimaliste'])
    
    return {
        'template_colors': {
            'primary': template_style['primary_color'],
            'secondary': template_style['secondary_color'],
            'accent': template_style['accent_color']
        },
        'template_fonts': {
            'header': template_style['header_font'],
            'content': template_style['content_font']
        }
    }

async def generate_advanced_pdf(document: dict, content: str, export_type: str, template_config: dict, options: AdvancedPDFOptions) -> bytes:
    """Generate PDF with advanced layout options"""
    # Get layout settings
    page_format = PDF_LAYOUT_OPTIONS["page_formats"].get(options.page_format, PDF_LAYOUT_OPTIONS["page_formats"]["A4"])
    margins = options.custom_margins or PDF_LAYOUT_OPTIONS["margin_presets"].get(options.margin_preset, PDF_LAYOUT_OPTIONS["margin_presets"]["standard"])
    
    # Build CSS with advanced options
    advanced_css = f"""
        @page {{
            size: {page_format.get('width', '21cm')} {page_format.get('height', '29.7cm')};
            margin-top: {margins['top']};
            margin-bottom: {margins['bottom']};
            margin-left: {margins['left']};
            margin-right: {margins['right']};
        }}
        
        body {{
            font-size: {11 * options.font_scaling}pt;
            line-height: {1.4 * options.font_scaling};
        }}
        
        .header {{
            font-size: {18 * options.font_scaling}pt;
        }}
        
        .exercise-number {{
            font-weight: bold;
            color: #2c3e50;
            margin-top: 20px;
        }}
    """
    
    # Use Pro template if available
    if template_config:
        template_style = TEMPLATE_STYLES.get(template_config.get('template_style', 'minimaliste'), TEMPLATE_STYLES['minimaliste'])
        template_colors = get_template_colors_and_fonts(template_config)
        
        if export_type == "sujet":
            template_content = load_template("sujet_pro")
        else:
            template_content = load_template("corrige_pro")
        
        html_content = Template(template_content).render(
            document={
                **document,
                'exercices': content,
                'type_doc': export_type.title()
            },
            date_creation=datetime.now().strftime("%d/%m/%Y"),
            **template_config,
            **template_colors,
            advanced_css=advanced_css
        )
    else:
        # Fallback to standard template with advanced options
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                {advanced_css}
                /* Standard styling with advanced options */
                .content {{ white-space: pre-line; }}
                .document-info {{ font-size: {10 * options.font_scaling}pt; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{export_type.title()}</h1>
                <h2>{document['matiere']} - {document['niveau']}</h2>
                <p>{document['chapitre']}</p>
                {f'<p>Difficulté: {document["difficulte"]}</p>' if options.show_difficulty else ''}
                {f'<p>Créé le {datetime.now().strftime("%d/%m/%Y")}</p>' if options.show_creation_date else ''}
            </div>
            <div class="content">{content}</div>
        </body>
        </html>
        """
    
    # Generate PDF (import lazy)
    import weasyprint
    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
    return pdf_bytes

# API Routes
@api_router.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers"""
    return {
        "status": "healthy",
        "service": "le-maitre-mot-api",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@api_router.get("/")
async def root():
    return {"message": "API Le Maître Mot V1 - Générateur de documents pédagogiques"}

@api_router.get("/catalog")
async def get_catalog():
    """Get the complete curriculum catalog with feature flags"""
    logger.info("🗺️ Catalog request - displaying all subjects with feature flags")
    
    # Get all subjects with their status and metadata
    all_subjects = get_all_subjects_with_status()
    
    catalog = []
    for matiere, subject_info in all_subjects.items():
        # Get curriculum data
        config = get_subject_by_name(matiere)
        if not config:
            continue
            
        levels = []
        # Only populate levels for active subjects
        if subject_info["status"] == "active" and config.get("data"):
            for niveau, themes in config["data"].items():
                # Flatten all chapters from all themes for the level
                all_chapters = []
                for theme, chapters in themes.items():
                    all_chapters.extend(chapters)
                    
                levels.append({
                    "name": niveau,
                    "chapters": all_chapters
                })
        
        catalog.append({
            "name": matiere,
            "status": subject_info["status"],
            "status_info": subject_info["status_info"],
            "expected": subject_info.get("expected", "TBD"),
            "description": subject_info.get("description", ""),
            "note": subject_info.get("note", ""),
            "features": subject_info.get("features", []),
            "chapter_count": subject_info["chapter_count"],
            "level_count": subject_info["level_count"],
            "levels": levels
        })
    
    # Get curriculum statistics
    stats = get_curriculum_stats()
    
    logger.info(
        f"🗺️ Catalog served - {stats['total']['subjects']} subjects total, "
        f"{stats['active']['subject_count']} active, "
        f"{stats['total']['chapters']} chapters available"
    )
    
    return {
        "catalog": catalog,
        "stats": stats,
        "roadmap": {
            "active": stats["active"]["subject_count"],
            "coming_soon": stats["coming_soon"]["subject_count"], 
            "planned": stats["planned"]["subject_count"],
            "beta": stats["beta"]["subject_count"],
            "future": stats["future"]["subject_count"],
            "total_subjects": stats["total"]["subjects"],
            "total_chapters": stats["total"]["chapters"]
        }
    }

# Alias v1 pour compatibilité (éviter 404 sur /api/v1/catalog)
@api_router.get("/v1/catalog")
async def get_catalog_v1():
    return await get_catalog()

# Alias v1 pour compatibilité (health)
@api_router.get("/v1/health")
async def health_check_v1():
    return await health_check()

@api_router.get("/roadmap")
async def get_roadmap():
    """Get the public roadmap showing all subjects and their release timeline"""
    logger.info("🗺️ Roadmap request - public transparency page")
    
    # Get subjects organized by status
    roadmap_data = {}
    for status in CURRICULUM_STATUS.keys():
        subjects_for_status = get_subjects_by_status(status)
        if subjects_for_status:
            roadmap_data[status] = {
                "status_info": CURRICULUM_STATUS[status],
                "subjects": []
            }
            
            for matiere, config in subjects_for_status.items():
                chapter_count = 0
                level_count = 0
                if config.get("data"):
                    level_count = len(config["data"])
                    for level_data in config["data"].values():
                        for chapters in level_data.values():
                            chapter_count += len(chapters)
                
                roadmap_data[status]["subjects"].append({
                    "name": matiere,
                    "description": config.get("description", ""),
                    "expected": config.get("expected", "TBD"),
                    "note": config.get("note", ""),
                    "features": config.get("features", []),
                    "chapter_count": chapter_count,
                    "level_count": level_count
                })
    
    # Get global statistics
    stats = get_curriculum_stats()
    
    return {
        "roadmap": roadmap_data,
        "stats": stats,
        "phases": {
            "phase_1": {
                "title": "🔄 Octobre 2025 - Matières Littéraires",
                "description": "Français et EMC avec prompts IA spécialisés", 
                "subjects": ["Français", "EMC"],
                "status": "coming_soon"
            },
            "phase_2": {
                "title": "📋 Nov-Déc 2025 - Sciences Humaines",
                "description": "Histoire, Géographie, SES avec supports documentaires",
                "subjects": ["Histoire", "Géographie", "SES", "Philosophie"],
                "status": "planned"
            },
            "phase_3": {
                "title": "🧪 Jan-Mars 2026 - Matières Pratiques (Beta)",
                "description": "Tests utilisateurs avec retours enseignants",
                "subjects": ["EPS", "Enseignements artistiques", "Technologie"],
                "status": "beta"
            },
            "phase_4": {
                "title": "🔮 2026+ - Spécialités Avancées",
                "description": "Matières complexes nécessitant outils spécialisés",
                "subjects": ["Sciences numériques", "Spécialités lycée"],
                "status": "future"
            }
        }
    }

@api_router.get("/pricing")
async def get_pricing():
    """Get pricing packages"""
    return {"packages": PRICING_PACKAGES}

@api_router.get("/analytics/overview")
async def get_analytics_overview(request: Request):
    """Get basic analytics overview (Pro only)"""
    try:
        user_email = await require_pro_user(request)
        logger.info(f"Analytics overview requested by Pro user: {user_email}")
        
        # Get user's documents count
        user_documents = await db.documents.count_documents({"user_id": user_email})
        guest_documents = await db.documents.count_documents({"guest_id": {"$regex": f".*{user_email.split('@')[0]}.*"}})
        
        # Get user's exports count
        user_exports = await db.exports.count_documents({"user_email": user_email})
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_documents = await db.documents.count_documents({
            "$or": [{"user_id": user_email}, {"guest_id": {"$regex": f".*{user_email.split('@')[0]}.*"}}],
            "created_at": {"$gte": thirty_days_ago}
        })
        
        recent_exports = await db.exports.count_documents({
            "user_email": user_email,
            "created_at": {"$gte": thirty_days_ago}
        })
        
        # Get subject distribution
        subject_pipeline = [
            {"$match": {"$or": [{"user_id": user_email}, {"guest_id": {"$regex": f".*{user_email.split('@')[0]}.*"}}]}},
            {"$group": {"_id": "$matiere", "count": {"$sum": 1}}}
        ]
        subject_stats = await db.documents.aggregate(subject_pipeline).to_list(None)
        
        # Get template usage stats
        template_pipeline = [
            {"$match": {"user_email": user_email}},
            {"$group": {"_id": "$template_used", "count": {"$sum": 1}}}
        ]
        template_stats = await db.exports.aggregate(template_pipeline).to_list(None)
        
        return {
            "user_analytics": {
                "total_documents": user_documents + guest_documents,
                "total_exports": user_exports,
                "recent_activity": {
                    "documents_last_30_days": recent_documents,
                    "exports_last_30_days": recent_exports
                },
                "subject_distribution": [
                    {"subject": stat["_id"], "count": stat["count"]} 
                    for stat in subject_stats
                ],
                "template_usage": [
                    {"template": stat["_id"] or "standard", "count": stat["count"]} 
                    for stat in template_stats
                ],
                "subscription_info": {
                    "type": "Pro",
                    "analytics_enabled": True
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analytics overview: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des analytics")

@api_router.get("/analytics/usage")
async def get_usage_analytics(request: Request, days: int = 30):
    """Get detailed usage analytics over time (Pro only)"""
    try:
        user_email = await require_pro_user(request)
        logger.info(f"Usage analytics requested by Pro user: {user_email} for {days} days")
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Daily document generation
        daily_docs_pipeline = [
            {
                "$match": {
                    "$or": [{"user_id": user_email}, {"guest_id": {"$regex": f".*{user_email.split('@')[0]}.*"}}],
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                    "documents": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        daily_docs = await db.documents.aggregate(daily_docs_pipeline).to_list(None)
        
        # Daily exports
        daily_exports_pipeline = [
            {
                "$match": {
                    "user_email": user_email,
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                    "exports": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        daily_exports = await db.exports.aggregate(daily_exports_pipeline).to_list(None)
        
        # Subject popularity over time
        subject_timeline_pipeline = [
            {
                "$match": {
                    "$or": [{"user_id": user_email}, {"guest_id": {"$regex": f".*{user_email.split('@')[0]}.*"}}],
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                        "subject": "$matiere"
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id.date": 1}}
        ]
        subject_timeline = await db.documents.aggregate(subject_timeline_pipeline).to_list(None)
        
        return {
            "usage_analytics": {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "daily_activity": {
                    "documents": [
                        {"date": doc["_id"], "count": doc["documents"]} 
                        for doc in daily_docs
                    ],
                    "exports": [
                        {"date": exp["_id"], "count": exp["exports"]} 
                        for exp in daily_exports
                    ]
                },
                "subject_timeline": [
                    {
                        "date": item["_id"]["date"], 
                        "subject": item["_id"]["subject"], 
                        "count": item["count"]
                    }
                    for item in subject_timeline
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching usage analytics: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des analytics d'usage")

@api_router.post("/generate")
async def generate_document(request: GenerateRequest):
    """Generate a document with exercises - CORRECTED feature flag validation"""
    try:
        logger = get_logger()
        logger.info(
            "🔥 URGENT GENERATE REQUEST RECEIVED",
            module_name="generation",
            func_name="generate_document_corrected", 
            matiere=request.matiere,
            niveau=request.niveau,
            chapitre=request.chapitre,
            guest_id=request.guest_id
        )
        
        # CORRECTION 1: Vérifier que la matière existe dans le nouveau système
        if request.matiere not in CURRICULUM_DATA_COMPLETE:
            logger.error(f"❌ Unknown subject in CURRICULUM_DATA_COMPLETE: {request.matiere}")
            raise HTTPException(
                status_code=400,
                detail=f"Matière '{request.matiere}' non reconnue dans le système"
            )
        
        # CORRECTION 2: Vérifier le statut avec logs détaillés
        matiere_config = CURRICULUM_DATA_COMPLETE[request.matiere]
        matiere_status = matiere_config.get("status", "inactive")
        
        logger.info(
            f"🔍 Feature flag check for {request.matiere}",
            status=matiere_status,
            expected=matiere_config.get("expected", "N/A"),
            has_data="data" in matiere_config
        )
        
        if matiere_status != "active":
            logger.warning(f"⚠️ Subject {request.matiere} is not active (status: {matiere_status})")
            
            log_feature_flag_access(request.matiere, matiere_status, "guest")
            
            raise HTTPException(
                status_code=423,  # Locked (not 400 Bad Request)
                detail={
                    "error": "subject_not_available", 
                    "message": f"La matière {request.matiere} n'est pas encore disponible",
                    "status": matiere_status,
                    "expected": matiere_config.get("expected", "TBD"),
                    "available_subjects": list(get_active_subjects().keys())
                }
            )
        
        # Log active subject access
        log_feature_flag_access(request.matiere, "active", "guest")
        
        # CORRECTION 3: Utiliser les données du nouveau système directement
        subject_data = matiere_config.get("data", {})
        if not subject_data:
            logger.error(f"❌ No curriculum data for active subject: {request.matiere}")
            raise HTTPException(
                status_code=500,
                detail=f"Données de curriculum manquantes pour {request.matiere}"
            )
        
        # CORRECTION 4: Validation niveau avec le nouveau système
        available_levels = list(subject_data.keys())
        if request.niveau not in available_levels:
            logger.error(
                f"❌ Level not available: {request.niveau} for {request.matiere}",
                available_levels=available_levels
            )
            raise HTTPException(
                status_code=400,
                detail=f"Niveau '{request.niveau}' non disponible pour {request.matiere}. Disponibles: {', '.join(available_levels)}"
            )
        
        # CORRECTION 5: Validation chapitre avec le nouveau système 
        level_data = subject_data[request.niveau]
        all_chapters = []
        for theme, chapters in level_data.items():
            all_chapters.extend(chapters)
        
        if request.chapitre not in all_chapters:
            logger.error(
                f"❌ Chapter not available: {request.chapitre} for {request.matiere} {request.niveau}",
                available_chapters=all_chapters[:3]  # Show first 3 for logs
            )
            raise HTTPException(
                status_code=400, 
                detail=f"Chapitre '{request.chapitre}' non disponible pour {request.matiere} {request.niveau}"
            )
        
        logger.info(
            "✅ All validations passed, starting exercise generation",
            module_name="generation",
            func_name="validation_success"
        )
        
        logger.info(f"🚀 Document generation started - {request.matiere} {request.niveau} {request.chapitre} - {request.type_doc} - {request.difficulte} - {request.nb_exercices} exercises - guest_id: {request.guest_id}")
        
        exercises = await generate_exercises_with_ai(
            request.matiere,
            request.niveau,
            request.chapitre,
            request.type_doc,
            request.difficulte,
            request.nb_exercices
        )
        
        # Create document
        document = Document(
            guest_id=request.guest_id,
            matiere=request.matiere,
            niveau=request.niveau,
            chapitre=request.chapitre,
            type_doc=request.type_doc,
            difficulte=request.difficulte,
            nb_exercices=request.nb_exercices,
            exercises=exercises
        )
        
        # Save to database
        doc_dict = document.dict()
        # Convert datetime for MongoDB
        doc_dict['created_at'] = doc_dict['created_at'].isoformat()
        await db.documents.insert_one(doc_dict)
        
        # Return the document (already processed during generation)
        return {"document": document}
        
    except HTTPException:
        raise
    except ValueError as e:
        # 🚨 Erreurs de validation (ex: chapitre non mappé)
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "chapter_not_implemented",
                "message": str(e),
                "type": "ValueError"
            }
        )
    except Exception as e:
        logger.error(f"Error generating document: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la génération du document")

@api_router.post("/auth/request-login")
@limiter.limit("5/15minutes")  # P0: Rate limit - 5 requests per 15 minutes
async def request_login(request_body: LoginRequest, request: Request):
    """
    Request a magic link for Pro user login.
    P0: Returns neutral response (always 200) to prevent email enumeration.
    P0: Rate limited to 5 req/15min per IP.
    """
    ip_address = request.client.host if request.client else None
    auth_service = SecureAuthService(db)
    
    try:
        # Check if user exists and is Pro
        is_pro, user = await check_user_pro_status(request_body.email)
        
        if is_pro:
            # Generate secure magic link token (hashed in DB)
            raw_token, token_hash = await auth_service.create_magic_link(
                email=request_body.email,
                action="login"
            )
            
            # Send magic link email (or log in local dev)
            environment = os.environ.get('ENVIRONMENT', 'development')
            frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
            magic_link = f"{frontend_url}/login/verify?token={raw_token}"
            
            if environment == 'development':
                # Mode local: Log the magic link and return it in response
                logger.info(f"🔗 MAGIC LINK (dev): {magic_link}")
                logger.info(f"   Email: {request_body.email}")
                # Return magic link in dev mode for easy testing
                await auth_service.log_auth_attempt(
                    email=request_body.email,
                    action="request_login",
                    success=True,
                    ip_address=ip_address
                )
                return {
                    "message": "Si un compte Pro existe pour cette adresse, un lien de connexion a été envoyé",
                    "success": True,
                    "dev_mode": True,
                    "magic_link": magic_link  # P0: Return magic link in dev mode
                }
            else:
                # Production: Send email
                email_sent = await send_magic_link_email(request_body.email, raw_token)
                if not email_sent:
                    logger.error(f"Failed to send magic link to {request_body.email}")
                    # Still return 200 for security
            
            # Log successful attempt
            await auth_service.log_auth_attempt(
                email=request_body.email,
                action="request_login",
                success=True,
                ip_address=ip_address
            )
        else:
            # User not Pro or doesn't exist: Log but don't reveal
            await auth_service.log_auth_attempt(
                email=request_body.email,
                action="request_login",
                success=False,
                ip_address=ip_address,
                error_msg="User not Pro or doesn't exist"
            )
        
        # P0 SECURITY: Always return 200 with neutral message
        # This prevents email enumeration attacks
        return {
            "message": "Si un compte Pro existe pour cette adresse, un lien de connexion a été envoyé",
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in request login: {e}")
        # Log error attempt
        await auth_service.log_auth_attempt(
            email=request_body.email,
            action="request_login",
            success=False,
            ip_address=ip_address,
            error_msg=str(e)
        )
        # Still return 200 for security
        return {
            "message": "Si un compte Pro existe pour cette adresse, un lien de connexion a été envoyé",
            "success": True
        }

@api_router.post("/auth/verify-login")
@limiter.limit("60/15minutes")  # P0-A2: Increased to 60/15min (token required anyway)
async def verify_login(request_body: VerifyLoginRequest, response: Response, request: Request):
    """
    Verify magic link token and create session.
    P0: Uses hashed tokens + sets httpOnly cookie.
    P0-A2: Rate limited to 60 req/15min per IP (higher than request-login because token is required).
    """
    auth_service = SecureAuthService(db)
    
    try:
        logger.info("Attempting to verify login token...")
        
        # Verify token using secure hash comparison
        token_doc = await auth_service.verify_magic_token(
            raw_token=request_body.token,
            expected_action="login"
        )
        
        if not token_doc:
            raise HTTPException(
                status_code=400,
                detail="Token invalide ou expiré"
            )
        
        email = token_doc.get('email')
        logger.info(f"Token valid for email: {email}")
        
        # Verify user is still Pro
        is_pro, user = await check_user_pro_status(email)
        if not is_pro:
            logger.warning(f"User {email} is no longer Pro")
            raise HTTPException(
                status_code=403,
                detail="Abonnement Pro expiré"
            )
        
        # P1: Extract device info from request
        device_info = extract_device_info(request)
        
        # Get device_id from request body (not from request object)
        device_id = request_body.device_id or "unknown"
        
        # Create login session with device info
        session_token = await create_login_session(email, device_id, device_info)
        
        if not session_token:
            logger.error("Failed to create login session")
            raise HTTPException(
                status_code=500,
                detail="Erreur lors de la création de la session"
            )
        
        # P0 SECURITY: Set session in httpOnly cookie
        environment = os.environ.get('ENVIRONMENT', 'development')
        is_secure = environment == 'production'
        
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=is_secure,  # True in production (HTTPS only)
            samesite="lax",  # CSRF protection
            max_age=86400,  # 24 hours
            path="/"
        )
        
        logger.info(f"Login session created successfully for {email} (cookie set)")
        
        # Mark token as used AFTER successful session creation (prevents replay attacks)
        # This ensures we don't mark the token as used if session creation fails
        token_hash = auth_service.hash_token(request_body.token)
        await auth_service.mark_token_used(token_hash)
        logger.info(f"Token marked as used for {email}")
        
        return {
            "message": "Connexion réussie",
            "email": email,
            "session_token": session_token,  # Also return for backward compat
            "expires_in": "24h"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in verify login: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la vérification du token"
        )

@api_router.post("/auth/verify-checkout-token")
@limiter.limit("10/15minutes")  # Rate limit - 10 requests per 15 minutes
async def verify_checkout_token(request_body: VerifyLoginRequest, response: Response, request: Request):
    """
    Verify checkout magic link token (action="pre_checkout") and create temporary session.
    Used for new user registration flow before payment.
    """
    auth_service = SecureAuthService(db)
    
    try:
        logger.info("Attempting to verify checkout token...")
        
        # Verify token with action="pre_checkout" (not "login")
        token_doc = await auth_service.verify_magic_token(
            raw_token=request_body.token,
            expected_action="pre_checkout"  # ✅ Vérifier action="pre_checkout"
        )
        
        if not token_doc:
            raise HTTPException(
                status_code=400,
                detail="Lien invalide ou expiré"
            )
        
        email = token_doc.get('email')
        metadata = token_doc.get('metadata', {})
        package_id = metadata.get('package_id', 'monthly')
        
        logger.info(f"Checkout token valid for email: {email}, package: {package_id}")
        
        # Mark token as used (prevents replay attacks)
        token_hash = auth_service.hash_token(request_body.token)
        await auth_service.mark_token_used(token_hash)
        logger.info(f"Token marked as used for {email}")
        
        # ✅ EN MODE DÉVELOPPEMENT : Créer automatiquement l'utilisateur Pro
        environment = os.environ.get('ENVIRONMENT', 'development')
        if environment == 'development':
            # Vérifier si l'utilisateur existe déjà
            is_pro, existing_user = await check_user_pro_status(email)
            
            if not is_pro:
                # Créer l'utilisateur Pro automatiquement en mode dev
                package = PRICING_PACKAGES[package_id]
                now = datetime.now(timezone.utc)
                
                # Calculer la date d'expiration
                if package["duration"] == "monthly":
                    expires = now + timedelta(days=30)
                else:  # yearly
                    expires = now + timedelta(days=365)
                
                # Créer l'utilisateur Pro
                pro_user = ProUser(
                    email=email,
                    nom=None,
                    etablissement=None,
                    subscription_type=package["duration"],
                    subscription_expires=expires,
                    last_login=None
                )
                
                # Sauvegarder dans la base de données (upsert)
                await db.pro_users.update_one(
                    {"email": email},
                    {"$set": pro_user.dict()},
                    upsert=True
                )
                
                logger.info(f"✅ DEV MODE: Pro user auto-created for {email} - {package['duration']} subscription expires {expires.strftime('%d/%m/%Y %H:%M')}")
        
        # P1: Extract device info from request
        device_info = extract_device_info(request)
        
        # Create session (user now has pro_users account in dev mode)
        session_token = await create_login_session(email, request_body.device_id, device_info)
        
        if not session_token:
            logger.error("Failed to create login session for checkout")
            raise HTTPException(
                status_code=500,
                detail="Erreur lors de la création de la session"
            )
        
        # P0 SECURITY: Set session in httpOnly cookie
        is_secure = environment == 'production'
        
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=86400,  # 24 hours
            path="/"
        )
        
        logger.info(f"Checkout session created successfully for {email} (cookie set)")
        
        return {
            "message": "Token vérifié",
            "email": email,
            "package_id": package_id,
            "session_token": session_token,  # Also return for backward compat
            "expires_in": "24h"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying checkout token: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la vérification du token"
        )

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """
    P0-A3: Logout user by invalidating session and clearing cookie.
    Accepts session token from cookie (preferred) or header (backward compat).
    """
    try:
        # P0-A3: Try cookie first (secure), fallback to header (backward compat)
        session_token = request.cookies.get("session_token")
        if not session_token:
            session_token = request.headers.get("X-Session-Token")

        if not session_token:
            # P0-A3: Still delete cookie even if no token found (clean state)
            response.delete_cookie(
                key="session_token",
                path="/",
                samesite="lax"
            )
            raise HTTPException(
                status_code=400,
                detail="Token de session manquant"
            )

        # Remove session from DB
        result = await db.login_sessions.delete_one({"session_token": session_token})

        # P0-A3: Always delete cookie regardless of DB result (clean state)
        environment = os.environ.get('ENVIRONMENT', 'development')
        is_secure = environment == 'production'
        response.delete_cookie(
            key="session_token",
            path="/",
            secure=is_secure,
            samesite="lax"
        )

        if result.deleted_count == 0:
            logger.warning(f"Logout: session not found in DB (cookie cleared anyway)")

        return {"message": "Déconnexion réussie"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in logout: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la déconnexion"
        )

@api_router.get("/subscription/status/{email}")
async def get_subscription_status(email: str):
    """Get detailed subscription status for an email"""
    try:
        is_pro, user = await check_user_pro_status(email)
        
        if not is_pro or not user:
            return {
                "is_pro": False,
                "message": "Aucun abonnement actif trouvé pour cette adresse email"
            }
        
        subscription_expires = user.get("subscription_expires")
        subscription_type = user.get("subscription_type", "inconnu")
        
        # Format dates
        if isinstance(subscription_expires, str):
            expires_date = datetime.fromisoformat(subscription_expires).replace(tzinfo=timezone.utc)
        elif isinstance(subscription_expires, datetime):
            expires_date = subscription_expires.replace(tzinfo=timezone.utc) if subscription_expires.tzinfo is None else subscription_expires
        else:
            expires_date = datetime.now(timezone.utc)
        
        now = datetime.now(timezone.utc)
        days_remaining = (expires_date - now).days
        
        return {
            "is_pro": True,
            "email": email,
            "subscription_type": subscription_type,
            "subscription_expires": expires_date.isoformat(),
            "expires_date_formatted": expires_date.strftime("%d/%m/%Y"),
            "days_remaining": max(0, days_remaining),
            "is_active": expires_date > now,
            "last_login": user.get("last_login"),
            "created_at": user.get("created_at")
        }
        
    except Exception as e:
        logger.error(f"Error getting subscription status for {email}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la vérification du statut d'abonnement")

@api_router.get("/template/styles")
async def get_template_styles():
    """Get available template styles (public endpoint)"""
    return {
        "styles": {
            style_id: {
                "name": style["name"],
                "description": style["description"],
                "preview_colors": {
                    "primary": style["primary_color"],
                    "secondary": style["secondary_color"], 
                    "accent": style["accent_color"]
                }
            }
            for style_id, style in TEMPLATE_STYLES.items()
        }
    }

@api_router.get("/export/styles")
async def get_export_styles(request: Request):
    """Get available export template styles based on user status"""
    try:
        # Check if user is Pro
        session_token = request.headers.get("X-Session-Token")
        is_pro = False
        
        if session_token:
            email = await validate_session_token(session_token)
            if email:
                is_pro, _ = await check_user_pro_status(email)
        
        # Filter styles based on user status
        available_styles = {}
        for style_id, style in EXPORT_TEMPLATE_STYLES.items():
            if "free" in style["available_for"] or (is_pro and "pro" in style["available_for"]):
                available_styles[style_id] = {
                    "name": style["name"],
                    "description": style["description"],
                    "preview_image": style["preview_image"],
                    "pro_only": "free" not in style["available_for"]
                }
        
        return {
            "styles": available_styles,
            "user_is_pro": is_pro
        }
        
    except Exception as e:
        logger.error(f"Error getting export styles: {e}")
        # Return at least the free style on error
        return {
            "styles": {
                "classique": {
                    "name": "Classique",
                    "description": "Style traditionnel élégant",
                    "preview_image": "/api/template-previews/classique.png",
                    "pro_only": False
                }
            },
            "user_is_pro": False
        }

@api_router.get("/template/get")
async def get_user_template(request: Request):
    """Get user's template configuration (Pro only)"""
    try:
        user_email = await require_pro_user(request)
        
        # Find user template
        template_doc = await db.user_templates.find_one({"user_email": user_email})
        
        if not template_doc:
            # Return default template
            default_template = UserTemplate(
                user_email=user_email,
                template_style="minimaliste"
            )
            return default_template.dict()
        
        # Convert to UserTemplate object
        template = UserTemplate(**template_doc)
        template_dict = template.dict()
        
        # Migrate old logo URLs to new endpoint format
        if template_dict.get('logo_url') and template_dict['logo_url'].startswith('/uploads/logos/'):
            filename = template_dict['logo_url'].split('/')[-1]
            template_dict['logo_url'] = f"/api/logos/{filename}"
            logger.info(f"🔄 Migrated logo URL for {user_email}: /uploads/logos/{filename} -> /api/logos/{filename}")
        
        return template_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user template: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors du chargement du template")

class TemplateSaveRequest(BaseModel):
    professor_name: Optional[str] = None
    school_name: Optional[str] = None
    school_year: Optional[str] = None
    footer_text: Optional[str] = None
    template_style: str = "minimaliste"

@api_router.post("/template/save")
async def save_user_template(
    request: Request,
    professor_name: Optional[str] = Form(None),
    school_name: Optional[str] = Form(None),
    school_year: Optional[str] = Form(None),
    footer_text: Optional[str] = Form(None),
    template_style: str = Form("minimaliste"),
    logo: Optional[UploadFile] = File(None)
):
    """Save user's template configuration (Pro only)"""
    try:
        user_email = await require_pro_user(request)
        
        # Debug logging
        logger.info(f"🔍 Template save request for {user_email}: professor_name={professor_name}, school_name={school_name}, school_year={school_year}, footer_text={footer_text}, template_style={template_style}")
        
        # Handle logo upload
        logo_url = None
        logo_filename = None
        
        if logo and logo.filename:
            logger.info(f"🖼️ Logo upload detected: {logo.filename}, size: {logo.size}, content_type: {logo.content_type}")
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if logo.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail="Type de fichier non supporté. Utilisez JPG, PNG, GIF ou WebP.")
            
            # Validate file size (max 5MB)
            if logo.size and logo.size > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Fichier trop volumineux. Taille maximum: 5MB.")
            
            # Create uploads directory if it doesn't exist
            uploads_dir = ROOT_DIR / "uploads" / "logos"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            import uuid
            file_extension = logo.filename.split('.')[-1].lower()
            logo_filename = f"logo_{user_email.replace('@', '_').replace('.', '_')}_{uuid.uuid4().hex[:8]}.{file_extension}"
            logo_path = uploads_dir / logo_filename
            
            # Save file
            with open(logo_path, "wb") as buffer:
                content = await logo.read()
                buffer.write(content)
            
            # Create URL (relative path for serving)
            logo_url = f"/api/logos/{logo_filename}"
            logger.info(f"✅ Logo saved: {logo_path} -> {logo_url}")
        
        # Validate template style
        if template_style not in TEMPLATE_STYLES:
            raise HTTPException(status_code=400, detail="Style de template invalide")
        
        # Get current template or create new one
        existing_template = await db.user_templates.find_one({"user_email": user_email})
        
        if existing_template:
            # Update existing
            update_data = {
                "professor_name": professor_name,
                "school_name": school_name,
                "school_year": school_year,
                "footer_text": footer_text,
                "template_style": template_style,
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Add logo data if uploaded
            if logo_url:
                update_data["logo_url"] = logo_url
                update_data["logo_filename"] = logo_filename
            
            logger.info(f"🔍 Updating existing template with data: {update_data}")
            
            await db.user_templates.update_one(
                {"user_email": user_email},
                {"$set": update_data}
            )
            
            # Get updated template
            updated_template = await db.user_templates.find_one({"user_email": user_email})
            template = UserTemplate(**updated_template)
        else:
            # Create new template
            template = UserTemplate(
                user_email=user_email,
                professor_name=professor_name,
                school_name=school_name,
                school_year=school_year,
                footer_text=footer_text,
                template_style=template_style,
                logo_url=logo_url,
                logo_filename=logo_filename
            )
            
            logger.info(f"🔍 Creating new template: {template.dict()}")
            
            await db.user_templates.insert_one(template.dict())
        
        logger.info(f"Template saved for user: {user_email}")
        return {
            "message": "Template sauvegardé avec succès",
            "template": template.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving user template: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde du template")

@api_router.get("/pdf/options")
async def get_pdf_options():
    """Get available PDF layout options (public endpoint)"""
    return {
        "layout_options": {
            "page_formats": [
                {"id": "A4", "name": "A4 Standard", "description": "Format A4 classique (21 × 29,7 cm)"},
                {"id": "A4_compact", "name": "A4 Compact", "description": "Format A4 avec marges réduites"},
                {"id": "US_Letter", "name": "US Letter", "description": "Format américain (8,5 × 11 pouces)"}
            ],
            "margin_presets": [
                {"id": "standard", "name": "Standard", "description": "Marges équilibrées (2,5cm haut/bas, 2cm gauche/droite)"},
                {"id": "compact", "name": "Compact", "description": "Marges réduites (1,5cm partout)"},
                {"id": "generous", "name": "Généreux", "description": "Marges importantes (3cm haut/bas, 2,5cm gauche/droite)"}
            ],
            "content_options": [
                {"id": "show_difficulty", "name": "Afficher la difficulté", "default": True},
                {"id": "show_creation_date", "name": "Afficher la date de création", "default": True},
                {"id": "show_exercise_numbers", "name": "Numéroter les exercices", "default": True},
                {"id": "show_point_values", "name": "Afficher les barèmes", "default": True},
                {"id": "include_instructions", "name": "Inclure les consignes", "default": True}
            ],
            "visual_options": [
                {"id": "page_numbering", "name": "Numérotation des pages", "options": [
                    {"value": "bottom_center", "label": "Bas centré"},
                    {"value": "bottom_right", "label": "Bas droite"},
                    {"value": "top_right", "label": "Haut droite"},
                    {"value": "none", "label": "Aucune"}
                ]},
                {"id": "exercise_separator", "name": "Séparateur d'exercices", "options": [
                    {"value": "line", "label": "Ligne"},
                    {"value": "space", "label": "Espace"},
                    {"value": "box", "label": "Encadré"},
                    {"value": "none", "label": "Aucun"}
                ]},
                {"id": "question_numbering", "name": "Numérotation des questions", "options": [
                    {"value": "arabic", "label": "1, 2, 3..."},
                    {"value": "roman", "label": "I, II, III..."},
                    {"value": "letters", "label": "a, b, c..."},
                    {"value": "none", "label": "Aucune"}
                ]}
            ]
        }
    }

@api_router.get("/quota/check")
@log_execution_time("check_quota_status")
async def check_quota_status(guest_id: str):
    """Check current quota status for guest user"""
    logger = get_logger()
    logger.info(
        "Checking quota status",
        module_name="quota",
        func_name="check_quota_status",
        user_type="guest",
        guest_id=guest_id[:8] + "..." if guest_id and len(guest_id) > 8 else guest_id
    )
    
    result = await check_guest_quota(guest_id)
    
    logger.info(
        "Quota check completed",
        module_name="quota",
        func_name="check_quota_status",
        user_type="guest",
        current_count=result.get("current_count", 0),
        limit=result.get("limit", 0),
        can_generate=result.get("can_generate", False)
    )
    
    return result
@api_router.get("/auth/session/validate")
async def validate_session(request: Request):
    """Validate current session and return user info (legacy endpoint)"""
    try:
        session_token = request.headers.get("X-Session-Token")
        
        if not session_token:
            raise HTTPException(
                status_code=401,
                detail="Token de session manquant"
            )
        
        email = await validate_session_token(session_token)
        
        if not email:
            raise HTTPException(
                status_code=401,
                detail="Session invalide ou expirée"
            )
        
        # Check if user is still Pro
        is_pro, user = await check_user_pro_status(email)
        
        if not is_pro:
            # Clean up session if user is no longer Pro
            await db.login_sessions.delete_one({"session_token": session_token})
            raise HTTPException(
                status_code=403,
                detail="Abonnement Pro expiré"
            )
        
        return {
            "email": email,
            "is_pro": True,
            "subscription_expires": user.get('subscription_expires'),
            "last_login": user.get('last_login')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la validation de session"
        )

@api_router.get("/auth/me")
async def get_current_user(request: Request):
    """
    P0: Get current user info from session (cookie or header).
    Supports both Pro and Free users (is_pro=true/false).

    Returns:
        - 401 if no session or invalid session
        - 200 with {email, is_pro, ...} for valid session (Pro or Free)
    """
    try:
        # Try cookie first (P0 secure), fallback to header (backward compat)
        session_token = request.cookies.get("session_token")
        if not session_token:
            session_token = request.headers.get("X-Session-Token")

        if not session_token:
            raise HTTPException(
                status_code=401,
                detail="Non authentifié"
            )

        email = await validate_session_token(session_token)

        if not email:
            raise HTTPException(
                status_code=401,
                detail="Session invalide ou expirée"
            )

        # Check Pro status (but don't reject non-Pro users)
        is_pro, user = await check_user_pro_status(email)

        # P0: Return user info for both Pro and Free users
        if is_pro:
            return {
                "email": email,
                "is_pro": True,
                "subscription_type": user.get('subscription_type'),
                "subscription_expires": user.get('subscription_expires'),
                "nom": user.get('nom'),
                "etablissement": user.get('etablissement'),
                "last_login": user.get('last_login')
            }
        else:
            # Free user - return basic info without Pro fields
            # Check if user exists in free_users collection
            free_user = await db.free_users.find_one({"email": email})
            return {
                "email": email,
                "is_pro": False,
                "nom": free_user.get('nom') if free_user else None,
                "created_at": free_user.get('created_at') if free_user else None
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération de l'utilisateur"
        )

@api_router.get("/auth/sessions")
async def get_user_sessions(request: Request):
    """
    P1: Get all active sessions for the current user.
    Returns list of sessions with device info.
    """
    try:
        # Get session token from cookie or header
        session_token = request.cookies.get("session_token")
        if not session_token:
            session_token = request.headers.get("X-Session-Token")
        
        if not session_token:
            raise HTTPException(
                status_code=401,
                detail="Non authentifié"
            )
        
        # Validate session and get email
        email = await validate_session_token(session_token)
        if not email:
            raise HTTPException(
                status_code=401,
                detail="Session invalide ou expirée"
            )
        
        # Get all active sessions for this user
        now = datetime.now(timezone.utc)
        sessions_cursor = db.login_sessions.find({
            "user_email": email,
            "expires_at": {"$gt": now.isoformat()}
        }).sort("created_at", -1)  # Most recent first
        
        sessions = []
        current_session_id = None
        
        async for session_doc in sessions_cursor:
            # Parse dates
            created_at = session_doc.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            last_used = session_doc.get("last_used")
            if isinstance(last_used, str):
                last_used = datetime.fromisoformat(last_used.replace('Z', '+00:00'))
            
            device_info = session_doc.get("device_info", {})
            
            session_data = {
                "session_id": str(session_doc["_id"]),
                "device_id": session_doc.get("device_id", "unknown"),
                "device_type": device_info.get("device_type", "unknown"),
                "browser": device_info.get("browser", "unknown"),
                "os": device_info.get("os", "unknown"),
                "ip_address": device_info.get("ip_address"),
                "created_at": created_at.isoformat() if created_at else None,
                "last_used": last_used.isoformat() if last_used else None,
                "is_current": session_doc.get("session_token") == session_token
            }
            
            sessions.append(session_data)
            
            # Track current session
            if session_data["is_current"]:
                current_session_id = session_data["session_id"]
        
        logger.info(f"P1: Retrieved {len(sessions)} active sessions for {email}")
        
        return {
            "sessions": sessions,
            "current_session_id": current_session_id,
            "total": len(sessions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des sessions"
        )

@api_router.delete("/auth/sessions/{session_id}")
async def delete_user_session(session_id: str, request: Request):
    """
    P1: Delete a specific session.
    User can only delete their own sessions, and cannot delete the current session.
    """
    try:
        # Get session token from cookie or header
        session_token = request.cookies.get("session_token")
        if not session_token:
            session_token = request.headers.get("X-Session-Token")
        
        if not session_token:
            raise HTTPException(
                status_code=401,
                detail="Non authentifié"
            )
        
        # Validate session and get email
        email = await validate_session_token(session_token)
        if not email:
            raise HTTPException(
                status_code=401,
                detail="Session invalide ou expirée"
            )
        
        # Find the session to delete
        from bson import ObjectId
        try:
            session_obj_id = ObjectId(session_id)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="ID de session invalide"
            )
        
        session_to_delete = await db.login_sessions.find_one({
            "_id": session_obj_id,
            "user_email": email  # P1: Security - only delete own sessions
        })
        
        if not session_to_delete:
            raise HTTPException(
                status_code=404,
                detail="Session non trouvée ou vous n'avez pas l'autorisation"
            )
        
        # P1: Prevent deleting current session
        if session_to_delete.get("session_token") == session_token:
            raise HTTPException(
                status_code=400,
                detail="Impossible de supprimer la session actuelle. Déconnectez-vous depuis un autre appareil."
            )
        
        # Delete the session
        delete_result = await db.login_sessions.delete_one({"_id": session_obj_id})
        
        if delete_result.deleted_count > 0:
            logger.info(
                f"P1: User {email} deleted session {session_id} "
                f"(device: {session_to_delete.get('device_id', 'unknown')})"
            )
            return {
                "message": "Session supprimée avec succès",
                "session_id": session_id
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Session non trouvée"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la suppression de la session"
        )

# ============================================================================
# P2 BUNDLE - HYBRID AUTH (Password optional)
# ============================================================================

@api_router.post("/auth/set-password")
@limiter.limit("5/15minutes")  # P2: Rate limit - 5 requests per 15 minutes
async def set_password(request_body: SetPasswordRequest, request: Request):
    """
    P2: Set password for Pro user account (requires active session).
    Password is optional - magic link remains the default auth method.
    """
    try:
        # Get session token from cookie or header
        session_token = request.cookies.get("session_token")
        if not session_token:
            session_token = request.headers.get("X-Session-Token")
        
        if not session_token:
            raise HTTPException(
                status_code=401,
                detail="Session requise pour définir un mot de passe"
            )
        
        # Validate session and get email
        email = await validate_session_token(session_token)
        if not email:
            raise HTTPException(
                status_code=401,
                detail="Session invalide ou expirée"
            )
        
        # Verify user is Pro
        is_pro, user = await check_user_pro_status(email)
        if not is_pro:
            raise HTTPException(
                status_code=403,
                detail="Abonnement Pro requis"
            )
        
        # P0: Validate password confirmation match
        if request_body.password != request_body.password_confirm:
            raise HTTPException(
                status_code=400,
                detail="Les mots de passe ne correspondent pas"
            )
        
        # P0: Validate password is a string
        if not isinstance(request_body.password, str):
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_password_format", "message": "Le mot de passe doit être une chaîne de caractères"}
            )
        
        # P0: Validate password length (bcrypt max 72 bytes)
        password_bytes = request_body.password.encode("utf-8")
        if len(password_bytes) > 72:
            raise HTTPException(
                status_code=400,
                detail={"error": "password_too_long", "message": "Le mot de passe ne peut pas dépasser 72 caractères"}
            )
        
        # Validate password strength
        is_valid, error_msg = validate_password_strength(request_body.password)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        # P0: Hash password - ensure we hash ONLY the string password
        password_str = str(request_body.password)  # Ensure it's a string
        password_hash = hash_password(password_str)
        
        # Update user in database
        await db.pro_users.update_one(
            {"email": email},
            {
                "$set": {
                    "password_hash": password_hash,
                    "password_set_at": datetime.now(timezone.utc)
                }
            }
        )
        
        logger.info(f"P2: Password set successfully for {email}")
        
        # Log auth attempt (success)
        auth_service = SecureAuthService(db)
        ip_address = request.client.host if request.client else None
        await auth_service.log_auth_attempt(
            email=email,
            action="set_password",
            success=True,
            ip_address=ip_address
        )
        
        return {
            "message": "Mot de passe défini avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting password: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la définition du mot de passe"
        )


# ============================================================================
# P0: FREE USER REGISTRATION
# ============================================================================

@api_router.post("/auth/register-free")
@limiter.limit("5/15minutes")  # Rate limit - 5 registrations per 15 minutes
async def register_free_user(request_body: RegisterFreeRequest, response: Response, request: Request):
    """
    P0: Register a new Free user account.
    Free users can:
    - Preview exercises (unlimited)
    - Export PDFs (10/day quota)

    Returns session token on success.
    """
    auth_service = SecureAuthService(db)
    ip_address = request.client.host if request.client else None

    try:
        # P0: Validate password confirmation
        if request_body.password != request_body.password_confirm:
            raise HTTPException(
                status_code=400,
                detail={"error": "password_mismatch", "message": "Les mots de passe ne correspondent pas"}
            )

        # P0: Validate password is a string (not an object)
        if not isinstance(request_body.password, str):
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_password_format", "message": "Le mot de passe doit être une chaîne de caractères"}
            )

        # P0: Validate password strength (minimum 8 chars)
        if len(request_body.password) < 8:
            raise HTTPException(
                status_code=400,
                detail={"error": "password_too_short", "message": "Le mot de passe doit contenir au moins 8 caractères"}
            )

        # P0: Validate password length (bcrypt max 72 bytes)
        password_bytes = request_body.password.encode("utf-8")
        if len(password_bytes) > 72:
            raise HTTPException(
                status_code=400,
                detail={"error": "password_too_long", "message": "Le mot de passe ne peut pas dépasser 72 caractères"}
            )

        # Check if email already exists in pro_users or free_users
        existing_pro = await db.pro_users.find_one({"email": request_body.email})
        existing_free = await db.free_users.find_one({"email": request_body.email})

        if existing_pro or existing_free:
            # P2: Neutral response (anti-enumeration)
            await auth_service.log_auth_attempt(
                email=request_body.email,
                action="register_free",
                success=False,
                ip_address=ip_address,
                error_msg="Email already exists"
            )
            raise HTTPException(
                status_code=400,
                detail="Un compte existe déjà avec cette adresse email"
            )

        # P0: Hash password - ensure we hash ONLY the string password, not the whole request
        try:
            password_str = str(request_body.password)  # Ensure it's a string
            password_hash = hash_password(password_str)
        except ValueError as e:
            # Handle password validation errors from hash_password
            error_msg = str(e)
            if "cannot exceed 72 bytes" in error_msg.lower():
                raise HTTPException(
                    status_code=400,
                    detail={"error": "password_too_long", "message": "Le mot de passe ne peut pas dépasser 72 caractères"}
                )
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_password", "message": error_msg}
            )

        # Create free user document
        now = datetime.now(timezone.utc)
        free_user_doc = {
            "email": request_body.email,
            "password_hash": password_hash,
            "nom": request_body.nom,
            "created_at": now,
            "updated_at": now,
            "exports_today": 0,
            "last_export_date": None
        }

        # Insert into free_users collection
        await db.free_users.insert_one(free_user_doc)

        # Create login session
        device_id = request.headers.get("X-Device-ID") or f"device-{uuid.uuid4()}"
        device_info = extract_device_info(request)
        session_token = await create_login_session(
            request_body.email,
            device_id,
            device_info
        )

        if not session_token:
            raise HTTPException(
                status_code=500,
                detail="Erreur lors de la création de la session"
            )

        # Set session cookie
        environment = os.environ.get('ENVIRONMENT', 'development')
        is_secure = environment == 'production'

        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=86400 * 7,  # 7 days for free users
            path="/"
        )

        # Log successful registration
        await auth_service.log_auth_attempt(
            email=request_body.email,
            action="register_free",
            success=True,
            ip_address=ip_address
        )

        logger.info(f"P0: Free user registered: {request_body.email}")

        return {
            "message": "Compte créé avec succès",
            "email": request_body.email,
            "session_token": session_token,
            "is_pro": False,
            "exports_per_day": 10
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering free user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la création du compte"
        )


@api_router.post("/auth/login-password")
@limiter.limit("10/15minutes")  # P2: Rate limit - 10 requests per 15 minutes
async def login_password(request_body: LoginPasswordRequest, response: Response, request: Request):
    """
    P0: Login with email + password (hybrid auth).
    Supports both Pro users and Free users.
    Requires password to be set first (via /auth/set-password or /auth/register-free).
    """
    auth_service = SecureAuthService(db)
    ip_address = request.client.host if request.client else None
    is_pro_user = False

    try:
        # P0: First try to find user in pro_users, then in free_users
        user = await db.pro_users.find_one({"email": request_body.email})
        if user:
            is_pro_user = True
        else:
            # Try free_users collection
            user = await db.free_users.find_one({"email": request_body.email})

        if not user:
            # P2: Neutral response (anti-enumeration)
            await auth_service.log_auth_attempt(
                email=request_body.email,
                action="login_password",
                success=False,
                ip_address=ip_address,
                error_msg="User not found"
            )
            raise HTTPException(
                status_code=401,
                detail="Email ou mot de passe incorrect"
            )

        # Check if password is set
        password_hash = user.get("password_hash")
        if not password_hash:
            await auth_service.log_auth_attempt(
                email=request_body.email,
                action="login_password",
                success=False,
                ip_address=ip_address,
                error_msg="Password not set"
            )
            raise HTTPException(
                status_code=400,
                detail="Aucun mot de passe défini pour ce compte. Utilisez le lien magique pour vous connecter."
            )

        # Verify password
        if not verify_password(request_body.password, password_hash):
            await auth_service.log_auth_attempt(
                email=request_body.email,
                action="login_password",
                success=False,
                ip_address=ip_address,
                error_msg="Invalid password"
            )
            raise HTTPException(
                status_code=401,
                detail="Email ou mot de passe incorrect"
            )

        # P0: Only check Pro status if user is from pro_users (Free users can always login)
        if is_pro_user:
            is_pro, _ = await check_user_pro_status(request_body.email)
            if not is_pro:
                # Pro subscription expired - user can still login as Free
                is_pro_user = False
                logger.info(f"P0: Pro subscription expired for {request_body.email}, logging in as Free user")
        
        # Generate device ID (if not provided, create one)
        device_id = request.headers.get("X-Device-ID") or f"device-{uuid.uuid4()}"
        
        # Extract device info
        device_info = extract_device_info(request)
        
        # Create login session (P1: multi-device support)
        session_token = await create_login_session(
            request_body.email,
            device_id,
            device_info
        )
        
        if not session_token:
            raise HTTPException(
                status_code=500,
                detail="Erreur lors de la création de la session"
            )
        
        # P0 SECURITY: Set session in httpOnly cookie
        environment = os.environ.get('ENVIRONMENT', 'development')
        is_secure = environment == 'production'
        
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=86400,  # 24 hours
            path="/"
        )
        
        # Log successful login
        await auth_service.log_auth_attempt(
            email=request_body.email,
            action="login_password",
            success=True,
            ip_address=ip_address
        )
        
        logger.info(f"P2: Password login successful for {request_body.email}")
        
        return {
            "message": "Connexion réussie",
            "email": request_body.email,
            "session_token": session_token,  # Also return for backward compat
            "expires_in": "24h"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in password login: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la connexion"
        )

@api_router.post("/auth/reset-password-request")
@limiter.limit("5/15minutes")  # P2: Rate limit - 5 requests per 15 minutes
async def reset_password_request(request_body: ResetPasswordRequest, request: Request):
    """
    P2: Request password reset (sends magic link with reset action).
    Always returns 200 (neutral response) for security.
    """
    ip_address = request.client.host if request.client else None
    auth_service = SecureAuthService(db)
    
    try:
        # Check if user exists and is Pro
        is_pro, user = await check_user_pro_status(request_body.email)
        
        if is_pro and user:
            # Check if password is set (only reset if password exists)
            password_hash = user.get("password_hash")
            
            if password_hash:
                # Generate secure magic link token for password reset
                raw_token, token_hash = await auth_service.create_magic_link(
                    email=request_body.email,
                    action="reset_password"
                )
                
                # Send reset email
                environment = os.environ.get('ENVIRONMENT', 'development')
                frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
                reset_link = f"{frontend_url}/reset-password?token={raw_token}"
                
                if environment == 'development':
                    # Mode local: Log the reset link
                    logger.info(f"🔗 PASSWORD RESET LINK (dev): {reset_link}")
                    logger.info(f"   Email: {request_body.email}")
                else:
                    # Production: Send email via Brevo
                    email_sent = await send_password_reset_email(
                        email=request_body.email,
                        token=raw_token
                    )
                    if not email_sent:
                        logger.error(f"Failed to send password reset email to {request_body.email}")
                
                # Log successful attempt
                await auth_service.log_auth_attempt(
                    email=request_body.email,
                    action="reset_password_request",
                    success=True,
                    ip_address=ip_address
                )
            else:
                # Password not set - log but don't reveal
                await auth_service.log_auth_attempt(
                    email=request_body.email,
                    action="reset_password_request",
                    success=False,
                    ip_address=ip_address,
                    error_msg="Password not set"
                )
        else:
            # User not Pro or doesn't exist - log but don't reveal
            await auth_service.log_auth_attempt(
                email=request_body.email,
                action="reset_password_request",
                success=False,
                ip_address=ip_address,
                error_msg="User not Pro or doesn't exist"
            )
        
        # P2 SECURITY: Always return 200 (neutral response)
        return {
            "message": "Si un compte Pro avec mot de passe existe pour cette adresse, un lien de réinitialisation a été envoyé",
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in reset password request: {e}")
        await auth_service.log_auth_attempt(
            email=request_body.email,
            action="reset_password_request",
            success=False,
            ip_address=ip_address,
            error_msg=str(e)
        )
        # Still return 200 for security
        return {
            "message": "Si un compte Pro avec mot de passe existe pour cette adresse, un lien de réinitialisation a été envoyé",
            "success": True
        }

@api_router.post("/auth/reset-password-confirm")
@limiter.limit("5/15minutes")  # P2: Rate limit - 5 requests per 15 minutes
async def reset_password_confirm(request_body: ResetPasswordConfirmRequest, request: Request):
    """
    P2: Confirm password reset with token and set new password.
    """
    auth_service = SecureAuthService(db)
    ip_address = request.client.host if request.client else None
    
    try:
        # Verify token using secure hash comparison
        token_doc = await auth_service.verify_magic_token(
            raw_token=request_body.token,
            expected_action="reset_password"
        )
        
        if not token_doc:
            raise HTTPException(
                status_code=400,
                detail="Token invalide ou expiré"
            )
        
        email = token_doc.get('email')
        logger.info(f"P2: Password reset token valid for {email}")
        
        # Verify user is still Pro
        is_pro, user = await check_user_pro_status(email)
        if not is_pro:
            raise HTTPException(
                status_code=403,
                detail="Abonnement Pro expiré"
            )
        
        # P0: Validate password is a string
        if not isinstance(request_body.new_password, str):
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_password_format", "message": "Le mot de passe doit être une chaîne de caractères"}
            )
        
        # P0: Validate password length (bcrypt max 72 bytes)
        password_bytes = request_body.new_password.encode("utf-8")
        if len(password_bytes) > 72:
            raise HTTPException(
                status_code=400,
                detail={"error": "password_too_long", "message": "Le mot de passe ne peut pas dépasser 72 caractères"}
            )
        
        # Validate password strength
        is_valid, error_msg = validate_password_strength(request_body.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        # P0: Hash new password - ensure we hash ONLY the string password
        password_str = str(request_body.new_password)  # Ensure it's a string
        password_hash = hash_password(password_str)
        
        # Mark token as used (prevents replay attacks)
        token_hash = auth_service.hash_token(request_body.token)
        await auth_service.mark_token_used(token_hash)
        
        # Update user password
        await db.pro_users.update_one(
            {"email": email},
            {
                "$set": {
                    "password_hash": password_hash,
                    "password_set_at": datetime.now(timezone.utc)
                }
            }
        )
        
        logger.info(f"P2: Password reset successful for {email}")
        
        # Log successful reset
        await auth_service.log_auth_attempt(
            email=email,
            action="reset_password_confirm",
            success=True,
            ip_address=ip_address
        )
        
        return {
            "message": "Mot de passe réinitialisé avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reset password confirm: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la réinitialisation du mot de passe"
        )
async def check_quota_status(guest_id: str):
    """Check current quota status for guest user"""
    return await check_guest_quota(guest_id)

def get_template_colors_and_fonts(template_config):
    """Get CSS colors and fonts for WeasyPrint templates based on template configuration"""
    style_name = template_config.get('template_style', 'minimaliste')
    template_style = TEMPLATE_STYLES.get(style_name, TEMPLATE_STYLES['minimaliste'])
    
    return {
        'template_colors': {
            'primary': template_style['primary_color'],
            'secondary': template_style['secondary_color'],
            'accent': template_style['accent_color']
        },
        'template_fonts': {
            'header': template_style['header_font'].replace('-', ' '),
            'content': template_style['content_font'].replace('-', ' ')
        }
    }

@api_router.get("/logos/{filename}")
@api_router.head("/logos/{filename}")
async def serve_logo(filename: str):
    """Serve logo files for Pro users"""
    try:
        # Validate filename to prevent directory traversal
        if not filename or '..' in filename or '/' in filename:
            raise HTTPException(status_code=400, detail="Nom de fichier invalide")
        
        # Check if file exists
        logo_path = uploads_dir / "logos" / filename
        if not logo_path.exists():
            raise HTTPException(status_code=404, detail="Logo non trouvé")
        
        # Determine content type based on file extension
        file_extension = filename.split('.')[-1].lower()
        content_type_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        
        content_type = content_type_map.get(file_extension, 'application/octet-stream')
        
        return FileResponse(
            path=str(logo_path),
            media_type=content_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving logo {filename}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors du chargement du logo")

@api_router.post("/export")
@log_execution_time("export_pdf")
async def export_pdf(request: ExportRequest, http_request: Request):
    """Export document as PDF using unified WeasyPrint approach"""
    logger = get_logger()
    
    logger.info(
        "Starting PDF export",
        module_name="export",
        func_name="export_pdf",
        doc_id=request.document_id,
        export_type=request.export_type,
        template_style=getattr(request, 'template_style', 'default')
    )
    
    try:
        # PR7.1: Check authentication - ONLY session token method (no legacy email fallback)
        from backend.services.access_control import assert_can_export_pdf
        
        session_token = http_request.headers.get("X-Session-Token")
        is_pro_user = False
        user_email = None
        template_config = {}
        
        # PR7.1: Récupérer user_email si token présent
        if session_token:
            logger.info(f"Session token provided: {session_token[:20]}...")
            email = await validate_session_token(session_token)
            if email:
                logger.info(f"Session token validated for email: {email}")
                is_pro, user = await check_user_pro_status(email)
                is_pro_user = is_pro
                user_email = email
                logger.info(f"Pro status check result - email: {email}, is_pro: {is_pro}")
                
                # Load user template configuration if Pro
                if is_pro:
                    logger.info(f"Loading template config for Pro user: {email}")
                    try:
                        template_doc = await db.user_templates.find_one({"user_email": email})
                        logger.info(f"🔍 Raw template doc from DB: {template_doc}")
                        if template_doc:
                            template_config = {
                                'template_style': template_doc.get('template_style', 'minimaliste'),
                                'professor_name': template_doc.get('professor_name'),
                                'school_name': template_doc.get('school_name'),
                                'school_year': template_doc.get('school_year'),
                                'footer_text': template_doc.get('footer_text'),
                                'logo_url': template_doc.get('logo_url'),
                                'logo_filename': template_doc.get('logo_filename')
                            }
                            logger.info(f"🔍 Processed template config for {email}: {template_config}")
                            
                            # Vérifier si on a des données réelles
                            has_real_data = any([
                                template_config.get('professor_name'),
                                template_config.get('school_name'),
                                template_config.get('school_year'),
                                template_config.get('footer_text')
                            ])
                            logger.info(f"🔍 Template has real data: {has_real_data}")
                        else:
                            # Default template for Pro users
                            template_config = {'template_style': 'minimaliste'}
                            logger.info(f"Using default template for Pro user {email}")
                    except Exception as e:
                        logger.error(f"Error loading template config: {e}")
                        template_config = {'template_style': 'minimaliste'}
                else:
                    logger.info(f"User {email} is not Pro - using standard PDF generation")
            else:
                logger.info("Session token validation failed - treating as guest")
        else:
            logger.info("No session token provided - treating as guest user")
        
        # PR7.1: Valider qu'un compte est requis pour exporter (AVANT toute génération)
        assert_can_export_pdf(user_email)
        
        # Find the document
        doc = await db.documents.find_one({"id": request.document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        # CRITICAL: Process geometric schemas and LaTeX before PDF generation
        
        if 'exercises' in doc:
            for exercise in doc['exercises']:
                if 'enonce' in exercise and exercise['enonce']:
                    exercise['enonce'] = process_exercise_content(exercise['enonce'])
                    # Convert LaTeX math to MathML for PDF rendering
                    exercise['enonce'] = process_math_content_for_pdf(exercise['enonce'])
                
                # 🔧 FIX CRITIQUE : Copier figure_svg → schema_svg pour templates PDF
                if exercise.get('figure_svg'):
                    exercise['schema_svg'] = exercise['figure_svg']
                    logger.info(
                        "✅ SVG figure copié vers schema_svg pour PDF",
                        module_name="export",
                        func_name="copy_figure_svg",
                        doc_id=request.document_id,
                        svg_length=len(exercise['figure_svg'])
                    )
                
                # NEW: Generate SVG for schema if present in donnees
                if exercise.get('donnees') and isinstance(exercise['donnees'], dict):
                    schema_data = exercise['donnees'].get('schema')
                    if schema_data:
                        schema_type = schema_data.get('type', 'unknown')
                        logger.info(
                            "Generating SVG for PDF schema",
                            module_name="export",
                            func_name="generate_svg",
                            doc_id=request.document_id,
                            schema_type=schema_type
                        )
                        
                        svg_content = schema_renderer.render_to_svg(schema_data)
                        if svg_content:
                            exercise['schema_svg'] = svg_content
                            logger.info(
                                "SVG generated successfully for PDF",
                                module_name="export",
                                func_name="generate_svg",
                                doc_id=request.document_id,
                                schema_type=schema_type,
                                svg_length=len(svg_content),
                                status="success"
                            )
                            log_schema_processing(schema_type, True, doc_id=request.document_id)
                        else:
                            logger.warning(
                                "Failed to generate SVG for PDF schema",
                                module_name="export",
                                func_name="generate_svg",
                                doc_id=request.document_id,
                                schema_type=schema_type,
                                status="failed"
                            )
                            log_schema_processing(schema_type, False, doc_id=request.document_id)
                            exercise['schema_svg'] = ""
                    else:
                        exercise['schema_svg'] = ""
                else:
                    exercise['schema_svg'] = ""
                
                # NOUVEAU: Process geographic document if present
                if exercise.get('document'):
                    doc_data = exercise['document']
                    logger.info(
                        "🗺️ Processing geographic document for PDF export",
                        module_name="export",
                        func_name="process_geographic_document",
                        doc_id=request.document_id,
                        exercise_id=exercise.get('id', 'unknown'),
                        document_title=doc_data.get('titre', 'Unknown'),
                        document_type=doc_data.get('type', 'Unknown'),
                        has_image=bool(doc_data.get('url_fichier_direct')),
                        image_url=doc_data.get('url_fichier_direct', 'No URL')[:100] if doc_data.get('url_fichier_direct') else None,
                        licence_type=doc_data.get('licence', {}).get('type', 'Unknown'),
                        licence_attribution=doc_data.get('licence', {}).get('notice_attribution', 'No attribution')[:50] if doc_data.get('licence', {}).get('notice_attribution') else None
                    )
                    
                    # Validate document data for PDF rendering
                    if not doc_data.get('url_fichier_direct'):
                        logger.warning(
                            "⚠️ Geographic document missing image URL",
                            module_name="export",
                            func_name="document_validation",
                            doc_id=request.document_id,
                            document_title=doc_data.get('titre', 'Unknown')
                        )
                    
                    if not doc_data.get('licence', {}).get('notice_attribution'):
                        logger.warning(
                            "⚠️ Geographic document missing attribution",
                            module_name="export",
                            func_name="document_validation",
                            doc_id=request.document_id,
                            document_title=doc_data.get('titre', 'Unknown')
                        )
                else:
                    logger.debug(
                        "No geographic document for exercise",
                        module_name="export",
                        func_name="process_geographic_document",
                        exercise_id=exercise.get('id', 'unknown')
                    )
                
                # Process solution if it exists
                if exercise.get('solution'):
                    if exercise['solution'].get('resultat'):
                        exercise['solution']['resultat'] = process_exercise_content(exercise['solution']['resultat'])
                        
                    if exercise['solution'].get('etapes') and isinstance(exercise['solution']['etapes'], list):
                        exercise['solution']['etapes'] = [
                            process_exercise_content(step) for step in exercise['solution']['etapes']
                        ]
            

        # Convert to Document object
        if isinstance(doc.get('created_at'), str):
            doc['created_at'] = datetime.fromisoformat(doc['created_at'])
        document = Document(**doc)
        
        # NEW TEMPLATE STYLE SYSTEM - Choose template based on requested style
        requested_style = request.template_style or "classique"
        logger.info(f"🎨 TEMPLATE STYLE EXPORT - Requested style: {requested_style}, Pro user: {is_pro_user}")
        
        # Validate style permission
        if requested_style not in EXPORT_TEMPLATE_STYLES:
            logger.warning(f"Invalid template style: {requested_style}, falling back to classique")
            requested_style = "classique"
        
        style_config = EXPORT_TEMPLATE_STYLES[requested_style]
        
        # Check if user has permission for this style
        if "free" not in style_config["available_for"] and not is_pro_user:
            logger.info(f"Style {requested_style} is Pro-only, user is not Pro. Using classique instead.")
            requested_style = "classique"
            style_config = EXPORT_TEMPLATE_STYLES["classique"]
        
        # Choose the correct template file
        if request.export_type == "sujet":
            template_name = style_config["sujet_template"]
        else:
            template_name = style_config["corrige_template"]
        
        logger.info(f"📄 Using template: {template_name} for style: {requested_style}")
        template_content = load_template(template_name)
        
        # Prepare render context
        render_context = {
            'document': document,
            'date_creation': datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        }
        
        # Add Pro personalization if available
        if is_pro_user and template_config:
            render_context['template_config'] = template_config
            render_context['school_name'] = template_config.get('school_name')
            render_context['professor_name'] = template_config.get('professor_name')
            render_context['school_year'] = template_config.get('school_year')
            render_context['footer_text'] = template_config.get('footer_text')
            render_context['logo_filename'] = template_config.get('logo_filename')
            
            # Convert logo URL to absolute file path for WeasyPrint
            logo_url = template_config.get('logo_url')
            if logo_url and logo_url.startswith('/uploads/'):
                logo_file_path = ROOT_DIR / logo_url[1:]  # Remove leading slash
                if logo_file_path.exists():
                    absolute_logo_url = f"file://{logo_file_path}"
                    render_context['logo_url'] = absolute_logo_url
                    template_config['logo_url'] = absolute_logo_url
                    logger.info(f"✅ Logo converted for WeasyPrint: {logo_file_path}")
                else:
                    logger.warning(f"⚠️ Logo file not found: {logo_file_path}")
                    render_context['logo_url'] = None
                    template_config['logo_url'] = None
            else:
                render_context['logo_url'] = logo_url
            
            logger.info(f"🔍 FINAL RENDER CONTEXT FOR PRO USER:")
            logger.info(f"   school_name: {render_context.get('school_name')}")
            logger.info(f"   professor_name: {render_context.get('professor_name')}")
            logger.info(f"   logo_url: {render_context.get('logo_url')}")
       
        # Generate filename with style suffix
        filename = f"LeMaitremot_{document.type_doc}_{document.matiere}_{document.niveau}_{request.export_type}_{requested_style}.pdf"
        
        # Process LaTeX expressions in document before rendering
        logger.info("🔬 Converting LaTeX expressions to SVG...")
        
        # Convert document to dict for processing (to avoid Pydantic read-only issues)
        document_dict = document.dict()
        
        # Process each exercise and convert LaTeX to SVG
        try:
            for exercise in document_dict.get('exercises', []):
                # Process exercise statement
                if 'enonce' in exercise and exercise['enonce']:
                    # First process geometric schemas, then LaTeX
                    exercise['enonce'] = geometry_renderer.process_geometric_schemas(exercise['enonce'])
                    exercise['enonce'] = latex_renderer.convert_latex_to_svg(exercise['enonce'])
                
                # Process QCM options if they exist
                if (exercise.get('type') == 'qcm' and 
                    exercise.get('donnees') and 
                    exercise['donnees'].get('options')):
                    exercise['donnees']['options'] = [
                        latex_renderer.convert_latex_to_svg(
                            geometry_renderer.process_geometric_schemas(option)
                        )
                        for option in exercise['donnees']['options']
                    ]
                
                # Process solution if it exists
                if exercise.get('solution'):
                    # Process result
                    if exercise['solution'].get('resultat'):
                        processed_result = geometry_renderer.process_geometric_schemas(
                            exercise['solution']['resultat']
                        )
                        exercise['solution']['resultat'] = latex_renderer.convert_latex_to_svg(
                            processed_result
                        )
                    # Process steps
                    if exercise['solution'].get('etapes') and isinstance(exercise['solution']['etapes'], list):
                        exercise['solution']['etapes'] = [
                            latex_renderer.convert_latex_to_svg(
                                geometry_renderer.process_geometric_schemas(step)
                            )
                            for step in exercise['solution']['etapes']
                        ]
        
        except Exception as e:
            logger.error(f"Error during LaTeX to SVG conversion: {e}")
            # Continue with original document if conversion fails
            document_dict = document.dict()
        
        # Update render context with processed document
        render_context['document'] = document_dict
        
        # Generate SVG schemas for each exercise (before template render)
        exercises = document_dict.get('exercises', [])
        for i, exercise in enumerate(exercises, start=1):
            # 🔧 FIX CRITIQUE : Copier figure_svg → schema_svg pour templates PDF
            if exercise.get('figure_svg'):
                exercise['schema_svg'] = exercise['figure_svg']
                logger.info(f"✅ [EXPORT][PDF] SVG figure copié vers schema_svg - Exercice {i} - length = {len(exercise['figure_svg'])}")
            
            schema_data = None
            
            # Check for schema in donnees
            if exercise.get('donnees') and isinstance(exercise.get('donnees'), dict):
                schema_data = exercise.get('donnees').get('schema')
            
            if schema_data:
                try:
                    svg_content = schema_renderer.render_to_svg(schema_data)
                    if svg_content:
                        exercise['schema_svg'] = svg_content
                        logger.info(f"[EXPORT][PDF] Generated SVG for Exercice {i} - schema_svg length = {len(svg_content)}")
                    else:
                        logger.warning(f"[EXPORT][PDF] Failed to render schema for Exercice {i}")
                except Exception as e:
                    logger.error(f"[EXPORT][PDF] Error rendering schema for Exercice {i}: {e}")
        
        # Log schema_svg presence for debugging
        for i, ex in enumerate(exercises, start=1):
            schema_svg_length = len(ex.get('schema_svg', ''))
            logger.info(f"[EXPORT][PDF] Exercice {i} - schema_svg length = {schema_svg_length}")
        
        # Render HTML using Jinja2
        logger.info("🔧 Generating PDF with WeasyPrint...")
        template = Template(template_content)
        html_content = template.render(**render_context)
        
        logger.info("✅ Mathematical expressions converted to SVG")
        
        # Generate PDF with WeasyPrint (import lazy)
        import weasyprint
        pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_bytes)
        temp_file.close()
        
        # Track export for guest quota (only for non-Pro users)
        if not is_pro_user and request.guest_id:
            export_record = {
                "id": str(uuid.uuid4()),
                "document_id": request.document_id,
                "export_type": request.export_type,
                "guest_id": request.guest_id,
                "user_email": user_email,
                "is_pro": is_pro_user,
                "template_used": template_config.get('template_style') if template_config else 'standard',
                "created_at": datetime.now(timezone.utc)
            }
            await db.exports.insert_one(export_record)
        
        logger.info(f"✅ PDF generated successfully: {filename}")
        
        return FileResponse(
            temp_file.name,
            media_type='application/pdf',
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting PDF: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'export PDF")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting PDF: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'export PDF")

@api_router.post("/export/advanced")
async def export_pdf_advanced(request: EnhancedExportRequest, http_request: Request):
    """Export document as PDF with advanced layout options (Pro only)"""
    try:
        # PR7.1: Check authentication using centralized access control
        from backend.services.access_control import assert_can_export_pdf
        
        session_token = http_request.headers.get("X-Session-Token")
        user_email = None
        
        if session_token:
            user_email = await validate_session_token(session_token)
        
        # PR7.1: Valider qu'un compte est requis (retourne 401 avec code AUTH_REQUIRED_EXPORT)
        assert_can_export_pdf(user_email)
        
        # Vérifier que l'utilisateur est Pro
        is_pro, user = await check_user_pro_status(user_email)
        if not is_pro:
            raise HTTPException(status_code=403, detail="Fonctionnalité Pro uniquement")
        
        logger.info(f"Advanced PDF export requested by Pro user: {email}")
        
        # Get document
        document = await db.documents.find_one({"id": request.document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        # CRITICAL: Process geometric schemas and LaTeX before PDF generation
        if 'exercises' in document:
            for exercise in document['exercises']:
                if 'enonce' in exercise and exercise['enonce']:
                    exercise['enonce'] = process_exercise_content(exercise['enonce'])
                
                # Process solution if it exists
                if exercise.get('solution'):
                    if exercise['solution'].get('resultat'):
                        exercise['solution']['resultat'] = process_exercise_content(exercise['solution']['resultat'])
                        # Convert LaTeX math to MathML for PDF rendering
                        exercise['solution']['resultat'] = process_math_content_for_pdf(exercise['solution']['resultat'])
                        
                    if exercise['solution'].get('etapes') and isinstance(exercise['solution']['etapes'], list):
                        processed_steps = []
                        for step in exercise['solution']['etapes']:
                            processed_step = process_exercise_content(step)
                            # Convert LaTeX math to MathML for PDF rendering
                            processed_step = process_math_content_for_pdf(processed_step)
                            processed_steps.append(processed_step)
                        exercise['solution']['etapes'] = processed_steps
        
        # Load user template configuration
        template_config = {}
        template_doc = await db.user_templates.find_one({"user_email": email})
        if template_doc:
            template_config = {
                'template_style': template_doc.get('template_style', 'minimaliste'),
                'professor_name': template_doc.get('professor_name'),
                'school_name': template_doc.get('school_name'),
                'school_year': template_doc.get('school_year'),
                'footer_text': template_doc.get('footer_text'),
                'logo_url': template_doc.get('logo_url'),
                'logo_filename': template_doc.get('logo_filename')
            }
        else:
            template_config = {'template_style': 'minimaliste'}
        
        # Apply advanced options
        advanced_opts = request.advanced_options or AdvancedPDFOptions()
        
        # Generate content with advanced formatting
        if request.export_type == "sujet":
            content = format_exercises_for_export(document["exercises"], advanced_opts)
        else:  # corrige
            content = format_solutions_for_export(document["exercises"], advanced_opts)
        
        # Generate PDF with advanced layout
        pdf_content = await generate_advanced_pdf(
            document, content, request.export_type, template_config, advanced_opts
        )
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_content)
        temp_file.close()
        
        # Generate filename
        filename = f"LeMaitremot_{request.export_type}_{document['matiere']}_{document['niveau']}_advanced.pdf"
        
        # Record export
        export_record = {
            "id": str(uuid.uuid4()),
            "document_id": request.document_id,
            "export_type": request.export_type,
            "user_email": email,
            "is_pro": True,
            "template_used": template_config.get('template_style', 'minimaliste'),
            "advanced_options": advanced_opts.dict(),
            "created_at": datetime.now(timezone.utc)
        }
        await db.exports.insert_one(export_record)
        
        logger.info(f"✅ Advanced PDF generated successfully: {filename}")
        
        return FileResponse(
            temp_file.name,
            media_type='application/pdf',
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting advanced PDF: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'export PDF avancé")

# ============================================================================
# P0 BUNDLE - SECURE CHECKOUT FLOW
# ============================================================================

@api_router.post("/auth/pre-checkout")
@limiter.limit("3/15minutes")  # P0: Rate limit - 3 requests per 15 minutes
async def pre_checkout(request_body: PreCheckoutRequest, request: Request):
    """
    P0: Initiate secure checkout by validating email BEFORE Stripe.
    Sends magic link to user to verify email before payment.
    
    Rate limited to prevent abuse.
    Always returns 200 (neutral response) for security.
    """
    ip_address = request.client.host if request.client else None
    auth_service = SecureAuthService(db)
    
    try:
        # Validate package
        if request_body.package_id not in PRICING_PACKAGES:
            # Still return 200 for security
            logger.warning(f"Invalid package_id attempted: {request_body.package_id}")
            return {
                "message": "Si un compte Pro existe pour cette adresse, un lien de confirmation a été envoyé",
                "success": True
            }
        
        # Check if email is already subscribed
        is_pro, existing_user = await check_user_pro_status(request_body.email)
        
        if is_pro:
            # User already Pro: log but don't reveal
            logger.info(f"Pre-checkout attempted for existing Pro user: {request_body.email}")
            await auth_service.log_auth_attempt(
                email=request_body.email,
                action="pre_checkout",
                success=False,
                ip_address=ip_address,
                error_msg="Already subscribed"
            )
            # Neutral response
            return {
                "message": "Si un compte Pro existe pour cette adresse, un lien de confirmation a été envoyé",
                "success": True
            }
        
        # Generate secure magic link token for checkout
        raw_token, token_hash = await auth_service.create_magic_link(
            email=request_body.email,
            action="pre_checkout",
            metadata={"package_id": request_body.package_id}
        )
        
        # Send email with magic link
        environment = os.environ.get('ENVIRONMENT', 'development')
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        checkout_link = f"{frontend_url}/checkout?token={raw_token}"
        
        logger.info(f"🔍 Environment détecté: {environment}, Frontend URL: {frontend_url}")
        
        if environment == 'development':
            # Mode local: Log the checkout link
            logger.info(f"🔗 CHECKOUT LINK (dev): {checkout_link}")
            logger.info(f"   Email: {request_body.email}")
            logger.info(f"   Package: {request_body.package_id}")
            
            # ✅ Retourner le lien dans la réponse pour le frontend
            # Log successful attempt
            await auth_service.log_auth_attempt(
                email=request_body.email,
                action="pre_checkout",
                success=True,
                ip_address=ip_address
            )
            
            response_data = {
                "message": "Un lien de confirmation a été envoyé à votre adresse email. Veuillez consulter votre boîte de réception.",
                "success": True,
                "dev_mode": True,  # Indicateur pour le frontend
                "checkout_link": checkout_link,  # ✅ Le lien complet
                "email": request_body.email,
                "package_id": request_body.package_id
            }
            logger.info(f"📤 Retour dev mode avec checkout_link: {checkout_link}")
            return response_data
        else:
            # Production: Send email
            package = PRICING_PACKAGES[request_body.package_id]
            email_sent = await send_checkout_confirmation_email(
                email=request_body.email,
                token=raw_token,
                package=package
            )
            if not email_sent:
                logger.error(f"Failed to send checkout email to {request_body.email}")
                # Still return 200 for security
        
        # Log successful attempt
        await auth_service.log_auth_attempt(
            email=request_body.email,
            action="pre_checkout",
            success=True,
            ip_address=ip_address
        )
        
        # Neutral response
        return {
            "message": "Un lien de confirmation a été envoyé à votre adresse email. Veuillez consulter votre boîte de réception.",
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in pre-checkout: {e}")
        await auth_service.log_auth_attempt(
            email=request.email,
            action="pre_checkout",
            success=False,
            ip_address=ip_address,
            error_msg=str(e)
        )
        # Neutral response even on error
        return {
            "message": "Un lien de confirmation a été envoyé à votre adresse email. Veuillez consulter votre boîte de réception.",
            "success": True
        }

@api_router.post("/checkout/session")
@limiter.limit("3/1hour")  # P0: Rate limit - 3 requests per hour
async def create_checkout_session(request_body: CheckoutRequest, request: Request):
    """
    Create Stripe checkout session.
    P0: NOW REQUIRES SESSION (no email in request body).
    Use /auth/pre-checkout first to validate email.
    """
    try:
        # P0: Get email from session (cookie or header)
        session_token = request.cookies.get("session_token")
        if not session_token:
            session_token = request.headers.get("X-Session-Token")
        
        if not session_token:
            raise HTTPException(
                status_code=401,
                detail="Session requise. Veuillez utiliser /auth/pre-checkout d'abord."
            )
        
        # Validate session and get email
        email = await validate_session_token(session_token)
        if not email:
            raise HTTPException(
                status_code=401,
                detail="Session invalide ou expirée"
            )
        
        # Validate package
        if request_body.package_id not in PRICING_PACKAGES:
            raise HTTPException(status_code=400, detail="Package invalide")
        
        # Check if email is already subscribed (anti-duplicate protection)
        is_pro, existing_user = await check_user_pro_status(email)
        if is_pro and existing_user:
                subscription_expires = existing_user.get("subscription_expires")
                subscription_type = existing_user.get("subscription_type", "inconnu")
                
                # Format expiration date for display
                if isinstance(subscription_expires, str):
                    expires_date = datetime.fromisoformat(subscription_expires).replace(tzinfo=timezone.utc)
                elif isinstance(subscription_expires, datetime):
                    expires_date = subscription_expires.replace(tzinfo=timezone.utc) if subscription_expires.tzinfo is None else subscription_expires
                else:
                    expires_date = datetime.now(timezone.utc) + timedelta(days=30)  # fallback
                
                formatted_date = expires_date.strftime("%d/%m/%Y")
                
                logger.info(f"Duplicate subscription attempt for {email} - already Pro until {formatted_date}")
                
                raise HTTPException(
                    status_code=409,  # Conflict
                    detail={
                        "error": "already_subscribed",
                        "message": f"Cette adresse email dispose déjà d'un abonnement {subscription_type} actif jusqu'au {formatted_date}. Pour modifier votre abonnement, veuillez nous contacter.",
                        "subscription_type": subscription_type,
                        "expires_date": formatted_date,
                        "action": "contact_support"
                    }
                )
        
        package = PRICING_PACKAGES[request_body.package_id]
        logger.info(f"Creating checkout session for package: {package} - User: {email}")
        
        # Initialize Stripe
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=stripe_secret_key, webhook_url=webhook_url)
        
        # Build URLs from frontend origin
        success_url = f"{request_body.origin_url}/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{request_body.origin_url}/cancel"
        
        # P0: Prepare metadata with email from session (NOT from request body)
        metadata = {
            "package_id": request_body.package_id,
            "email": email,  # P0: Email from validated session
            "nom": request_body.nom or "",
            "etablissement": request_body.etablissement or "",
            "source": "lemaitremot_web_p0_secure"
        }
        
        # Create checkout session request
        checkout_request = CheckoutSessionRequest(
            amount=package["amount"],
            currency=package["currency"],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata
        )
        
        # Create session
        session = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Store transaction
        # ✅ P0: Email from validated session, NOT from request body
        transaction = PaymentTransaction(
            session_id=session.session_id,
            amount=package["amount"],
            currency=package["currency"],
            package_id=request.package_id,
            email=email,  # ✅ From session, not request.email
            metadata=metadata,
            payment_status="pending",
            session_status="initiated"
        )
        
        # Save to database
        await db.payment_transactions.insert_one(transaction.dict())
        
        logger.info(f"Checkout session created: {session.session_id}")
        
        return {
            "url": session.url,
            "session_id": session.session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création de la session")

@api_router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str):
    """Get checkout session status"""
    try:
        # Initialize Stripe
        stripe_checkout = StripeCheckout(api_key=stripe_secret_key, webhook_url="")
        
        # Get status from Stripe
        status = await stripe_checkout.get_checkout_status(session_id)
        
        # Find transaction in database
        transaction = await db.payment_transactions.find_one({"session_id": session_id})
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction non trouvée")
        
        # Update transaction status if payment completed
        if status.payment_status == "paid" and transaction.get("payment_status") != "paid":
            # Update transaction
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "payment_status": "paid",
                        "session_status": "complete",
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Create or update Pro user
            if transaction.get("email"):
                await create_pro_user_from_transaction(transaction, status)
        
        return {
            "session_id": session_id,
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting checkout status: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la vérification du statut")

async def create_pro_user_from_transaction(transaction: dict, status):
    """Create Pro user from successful transaction"""
    try:
        package = PRICING_PACKAGES[transaction["package_id"]]
        
        # Calculate precise expiration date based on subscription type
        now = datetime.now(timezone.utc)
        if package["duration"] == "monthly":
            # Add exactly 1 month (30 days)
            expires = now + timedelta(days=30)
            logger.info(f"Monthly subscription: expires in 30 days ({expires.strftime('%d/%m/%Y %H:%M')})")
        else:  # yearly
            # Add exactly 1 year (365 days)
            expires = now + timedelta(days=365)
            logger.info(f"Yearly subscription: expires in 365 days ({expires.strftime('%d/%m/%Y %H:%M')})")
        
        # Check if user already exists (upgrade/renewal scenario)
        existing_user = await db.pro_users.find_one({"email": transaction["email"]})
        
        if existing_user:
            # User exists - extend subscription from current expiration or now, whichever is later
            current_expires = existing_user.get("subscription_expires")
            if current_expires:
                if isinstance(current_expires, str):
                    current_expires = datetime.fromisoformat(current_expires).replace(tzinfo=timezone.utc)
                elif isinstance(current_expires, datetime) and current_expires.tzinfo is None:
                    current_expires = current_expires.replace(tzinfo=timezone.utc)
                
                # If current subscription is still active, extend from expiration date
                if current_expires > now:
                    if package["duration"] == "monthly":
                        expires = current_expires + timedelta(days=30)
                    else:  # yearly
                        expires = current_expires + timedelta(days=365)
                    logger.info(f"Extending existing subscription from {current_expires.strftime('%d/%m/%Y')} to {expires.strftime('%d/%m/%Y')}")
        
        # Create/Update Pro user
        pro_user = ProUser(
            email=transaction["email"],
            nom=transaction.get("metadata", {}).get("nom") or existing_user.get("nom") if existing_user else None,
            etablissement=transaction.get("metadata", {}).get("etablissement") or existing_user.get("etablissement") if existing_user else None,
            subscription_type=package["duration"],
            subscription_expires=expires,
            last_login=existing_user.get("last_login") if existing_user else None
        )
        
        # Save to database (upsert)
        result = await db.pro_users.update_one(
            {"email": transaction["email"]},
            {"$set": pro_user.dict()},
            upsert=True
        )
        
        action = "updated" if result.matched_count > 0 else "created"
        logger.info(f"Pro user {action}: {transaction['email']} - {package['duration']} subscription expires {expires.strftime('%d/%m/%Y %H:%M')}")
        
        return expires
        
    except Exception as e:
        logger.error(f"Error creating pro user: {e}")
        return None

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    try:
        body = await request.body()
        stripe_signature = request.headers.get("Stripe-Signature")
        
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        # Initialize Stripe
        stripe_checkout = StripeCheckout(api_key=stripe_secret_key, webhook_url="")
        
        # Handle webhook
        webhook_response = await stripe_checkout.handle_webhook(body, stripe_signature)
        
        logger.info(f"Webhook received: {webhook_response.event_type} for session {webhook_response.session_id}")
        
        # Process the webhook based on event type
        if webhook_response.event_type == "checkout.session.completed":
            # Find and update transaction
            await db.payment_transactions.update_one(
                {"session_id": webhook_response.session_id},
                {
                    "$set": {
                        "payment_status": webhook_response.payment_status,
                        "session_status": "complete",
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Get transaction details for user creation
            transaction = await db.payment_transactions.find_one({"session_id": webhook_response.session_id})
            if transaction and transaction.get("email"):
                # Create Pro user
                await create_pro_user_from_transaction(transaction, webhook_response)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing error")

@api_router.get("/user/status/{email}")
async def get_user_status(email: str):
    """Get user Pro status"""
    try:
        is_pro, user = await check_user_pro_status(email)
        
        if is_pro:
            return {
                "is_pro": True,
                "subscription_type": user.get("subscription_type"),
                "subscription_expires": user.get("subscription_expires"),
                "account_type": "pro"
            }
        else:
            return {
                "is_pro": False,
                "account_type": "guest"
            }
            
    except Exception as e:
        logger.error(f"Error getting user status: {e}")
        return {"is_pro": False, "account_type": "guest"}

# ============================================================================
# P3.0 BUNDLE - USER EXERCISES LIBRARY (Bibliothèque d'exercices)
# ============================================================================

class UserExerciseSaveRequest(BaseModel):
    """Modèle pour sauvegarder un exercice généré"""
    exercise_uid: str = Field(..., description="UUID unique de l'exercice")
    generator_key: Optional[str] = Field(None, description="Clé du générateur utilisé")
    code_officiel: str = Field(..., description="Code officiel du chapitre (ex: 6e_N08)")
    difficulty: str = Field(..., description="Difficulté (facile, moyen, difficile)")
    seed: Optional[int] = Field(None, description="Seed utilisé pour la génération")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Variables générées")
    enonce_html: str = Field(..., description="Énoncé HTML de l'exercice")
    solution_html: str = Field(..., description="Solution HTML de l'exercice")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Métadonnées additionnelles")

@api_router.post("/user/exercises")
async def save_user_exercise(
    request_body: UserExerciseSaveRequest,
    request: Request
):
    """
    P3.0: Sauvegarder un exercice généré dans la bibliothèque utilisateur.
    Requiert une session active.
    P0: Sanitisation HTML pour prévenir XSS.
    """
    try:
        # Valider la session
        session_token = request.headers.get("X-Session-Token")
        if not session_token:
            raise HTTPException(
                status_code=401,
                detail="Authentification requise pour sauvegarder un exercice"
            )
        
        user_email = await validate_session_token(session_token)
        if not user_email:
            raise HTTPException(
                status_code=401,
                detail="Session invalide ou expirée"
            )
        
        # P0: Sanitiser le HTML avant insertion
        from backend.utils.html_sanitizer import sanitize_html
        
        # Sanitiser l'énoncé
        enonce_result = sanitize_html(request_body.enonce_html)
        if enonce_result["rejected"]:
            status_code = 413 if enonce_result["reject_reason"] == "HTML_TOO_LARGE" else 400
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error": "HTML rejeté pour l'énoncé",
                    "reason": enonce_result["reject_reason"],
                    "message": f"Le contenu HTML de l'énoncé a été rejeté: {enonce_result['reject_reason']}"
                }
            )
        
        # Sanitiser la solution
        solution_result = sanitize_html(request_body.solution_html)
        if solution_result["rejected"]:
            status_code = 413 if solution_result["reject_reason"] == "HTML_TOO_LARGE" else 400
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error": "HTML rejeté pour la solution",
                    "reason": solution_result["reject_reason"],
                    "message": f"Le contenu HTML de la solution a été rejeté: {solution_result['reject_reason']}"
                }
            )
        
        # Logger si sanitization a eu lieu
        if enonce_result["changed"] or solution_result["changed"]:
            # Tronquer l'email pour les logs (garder seulement les 3 premiers caractères)
            email_hash = user_email[:3] + "***" if len(user_email) > 3 else "***"
            logger.warning(
                f"[XSS_SANITIZED] HTML sanitized for user {email_hash} - exercise_uid={request_body.exercise_uid}, "
                f"enonce_changed={enonce_result['changed']}, solution_changed={solution_result['changed']}, "
                f"enonce_reasons={enonce_result['reasons']}, solution_reasons={solution_result['reasons']}"
            )
        
        # Vérifier si l'exercice existe déjà (doublon)
        existing = await db.user_exercises.find_one({
            "user_email": user_email,
            "exercise_uid": request_body.exercise_uid
        })
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Cet exercice est déjà sauvegardé"
            )
        
        # Préparer les métadonnées avec info de sanitization
        metadata = request_body.metadata or {}
        if enonce_result["changed"]:
            metadata["sanitized"] = True
            if "sanitize_reasons" not in metadata:
                metadata["sanitize_reasons"] = []
            metadata["sanitize_reasons"].extend([f"enonce: {r}" for r in enonce_result["reasons"]])
        if solution_result["changed"]:
            metadata["sanitized"] = True
            if "sanitize_reasons" not in metadata:
                metadata["sanitize_reasons"] = []
            metadata["sanitize_reasons"].extend([f"solution: {r}" for r in solution_result["reasons"]])
        
        # Créer le document avec HTML sanitized
        exercise_doc = {
            "user_email": user_email,
            "exercise_uid": request_body.exercise_uid,
            "generator_key": request_body.generator_key,
            "code_officiel": request_body.code_officiel,
            "difficulty": request_body.difficulty,
            "seed": request_body.seed,
            "variables": request_body.variables or {},
            "enonce_html": enonce_result["html"],  # Version sanitized
            "solution_html": solution_result["html"],  # Version sanitized
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.user_exercises.insert_one(exercise_doc)
        
        logger.info(
            f"P3.0: Exercice sauvegardé pour {user_email} - exercise_uid={request_body.exercise_uid}, code_officiel={request_body.code_officiel}"
        )
        
        return {
            "success": True,
            "message": "Exercice sauvegardé avec succès",
            "exercise_uid": request_body.exercise_uid
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de l'exercice: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la sauvegarde de l'exercice"
        )

@api_router.get("/user/exercises")
async def get_user_exercises(
    request: Request,
    code_officiel: Optional[str] = None,
    difficulty: Optional[str] = None,
    limit: int = 50
):
    """
    P3.0: Récupérer la liste des exercices sauvegardés de l'utilisateur.
    Requiert une session active.
    """
    try:
        # Valider la session
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
        
        # Construire la requête
        query = {"user_email": user_email}
        
        if code_officiel:
            query["code_officiel"] = code_officiel
        
        if difficulty:
            query["difficulty"] = difficulty
        
        # Récupérer les exercices (triés par date DESC)
        cursor = db.user_exercises.find(query).sort("created_at", -1).limit(limit)
        exercises = await cursor.to_list(length=limit)
        
        # Nettoyer les _id MongoDB pour la réponse
        for ex in exercises:
            ex["id"] = str(ex.pop("_id"))
            # Convertir datetime en ISO string
            if isinstance(ex.get("created_at"), datetime):
                ex["created_at"] = ex["created_at"].isoformat()
            if isinstance(ex.get("updated_at"), datetime):
                ex["updated_at"] = ex["updated_at"].isoformat()
        
        logger.info(
            f"P3.0: Liste exercices récupérée pour {user_email} - count={len(exercises)}, filters={{code_officiel={code_officiel}, difficulty={difficulty}}}"
        )
        
        return {
            "exercises": exercises,
            "count": len(exercises)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des exercices: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des exercices"
        )

@api_router.delete("/user/exercises/{exercise_uid}")
async def delete_user_exercise(
    exercise_uid: str,
    http_request: Request
):
    """
    P3.0: Supprimer un exercice sauvegardé.
    Requiert une session active et ownership de l'exercice.
    """
    try:
        # Valider la session
        session_token = http_request.headers.get("X-Session-Token")
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
        
        # Vérifier ownership et supprimer
        result = await db.user_exercises.delete_one({
            "user_email": user_email,
            "exercise_uid": exercise_uid
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Exercice non trouvé ou vous n'avez pas les droits pour le supprimer"
            )
        
        logger.info(
            f"P3.0: Exercice supprimé pour {user_email}",
            exercise_uid=exercise_uid
        )
        
        return {
            "success": True,
            "message": "Exercice supprimé avec succès",
            "exercise_uid": exercise_uid
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'exercice: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la suppression de l'exercice"
        )

@api_router.get("/documents")
@log_execution_time("get_documents")
async def get_documents(guest_id: str = None):
    """Get user documents"""
    logger = get_logger()
    user_type = "guest" if guest_id else "unknown"
    
    logger.info(
        "Starting document retrieval",
        module_name="documents",
        func_name="get_documents",
        user_type=user_type,
        guest_id=guest_id[:8] + "..." if guest_id and len(guest_id) > 8 else guest_id
    )
    
    try:
        if guest_id:
            # Get documents for guest user
            documents = await db.documents.find({"guest_id": guest_id}).sort("created_at", -1).limit(20).to_list(length=20)
        else:
            return {"documents": []}
        
        for doc in documents:
            if isinstance(doc.get('created_at'), str):
                doc['created_at'] = datetime.fromisoformat(doc['created_at'])
            
            # Apply professional content processing to ensure consistency
            # Process all content systematically to handle both old and new documents
            if 'exercises' in doc:
                for exercise in doc['exercises']:
                    if 'enonce' in exercise and exercise['enonce']:
                        exercise['enonce'] = process_exercise_content(exercise['enonce'])
                    
                    # schema_img is now generated during exercise creation, no need to process again
                    if exercise.get('schema_img'):
                        logger.debug(
                            "Schema image already present from generation",
                            module_name="documents",
                            func_name="check_schemas",
                            doc_id=str(doc.get('id', 'unknown'))[:8],
                            has_schema_img=bool(exercise.get('schema_img'))
                        )

                    # Process solution if it exists
                    if exercise.get('solution'):
                        if exercise['solution'].get('resultat'):
                            exercise['solution']['resultat'] = process_exercise_content(exercise['solution']['resultat'])
                                
                        if exercise['solution'].get('etapes') and isinstance(exercise['solution']['etapes'], list):
                            exercise['solution']['etapes'] = [
                                process_exercise_content(step) for step in exercise['solution']['etapes']
                            ]
        
        # Clean up MongoDB-specific fields that can't be JSON serialized
        for doc in documents:
            # Remove MongoDB ObjectId fields that cause serialization issues
            if '_id' in doc:
                del doc['_id']
        
        # Return raw documents to preserve dynamic fields like schema_img
        # Don't use Pydantic models here as they filter out dynamic fields
        return {"documents": documents}
        
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        return {"documents": []}

@api_router.post("/documents/{document_id}/vary/{exercise_index}")
async def vary_exercise(document_id: str, exercise_index: int):
    """Generate a variation of a specific exercise"""
    try:
        # Find the document
        doc = await db.documents.find_one({"id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        if exercise_index >= len(doc.get("exercises", [])):
            raise HTTPException(status_code=400, detail="Index d'exercice invalide")
        
        # Generate a new variation
        exercises = await generate_exercises_with_ai(
            doc["matiere"],
            doc["niveau"],
            doc["chapitre"],
            doc["type_doc"],
            doc["difficulte"],
            1  # Just one exercise
        )
        
        if exercises:
            # Update the specific exercise
            # Convert Exercise object to dict for MongoDB storage
            exercise_dict = exercises[0].dict() if hasattr(exercises[0], 'dict') else exercises[0]
            doc["exercises"][exercise_index] = exercise_dict
            await db.documents.update_one(
                {"id": document_id},
                {"$set": {"exercises": doc["exercises"]}}
            )
            
            # Return the exercise as dict for JSON serialization
            return {"exercise": exercise_dict}
        
        raise HTTPException(status_code=500, detail="Impossible de générer une variation")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error varying exercise: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la génération de la variation")

# ============================================================================
# P0: Export PDF from selection (for /fiches/nouvelle)
# ============================================================================

class ExportSelectionRequest(BaseModel):
    title: str
    layout: str = "eco"  # "eco" or "classic"
    include_correction: bool = True
    exercises: List[Dict[str, Any]]

@api_router.post("/v1/sheets/export-selection")
@limiter.limit("10/15minutes")  # Rate limit
async def export_selection_pdf(
    request_body: ExportSelectionRequest,
    request: Request,
    response: Response
):
    """
    P0: Export PDF from a selection of exercises (for /fiches/nouvelle).
    
    Requires authentication (X-Session-Token).
    Free users: quota limited (10/day).
    Pro users: unlimited.
    
    Returns PDF binary (Content-Type: application/pdf).
    """
    logger = get_logger()
    
    try:
        # PR7.1: Validate session token and check export permission
        from backend.services.access_control import assert_can_export_pdf
        
        session_token = request.headers.get("X-Session-Token")
        user_email = None
        
        if session_token:
            user_email = await validate_session_token(session_token)
        
        # PR7.1: Valider qu'un compte est requis pour exporter (retourne 401 avec code AUTH_REQUIRED_EXPORT)
        assert_can_export_pdf(user_email)
        
        # P0: Check if user is Pro
        is_pro, _ = await check_user_pro_status(user_email)
        
        # PR8: Vérifier que l'utilisateur peut utiliser le layout demandé (eco = Premium uniquement)
        from backend.services.access_control import assert_can_use_layout
        assert_can_use_layout(user_email, is_pro, layout)
        
        # P0: Check quota for Free users
        if not is_pro:
            # Check Free user quota (10 exports/day)
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            export_count = await db.exports.count_documents({
                "user_email": user_email,
                "created_at": {"$gte": today}
            })
            
            if export_count >= 10:
                raise HTTPException(
                    status_code=429,
                    detail="Quota d'exports quotidien atteint (10/jour). Passez en Pro pour des exports illimités."
                )
        
        # Validate exercises
        if not request_body.exercises or len(request_body.exercises) == 0:
            raise HTTPException(
                status_code=400,
                detail="Aucun exercice fourni"
            )
        
        # P0: Map layout "standard" -> "classic"
        layout = request_body.layout
        if layout == "standard":
            layout = "classic"
        elif layout not in ["eco", "classic"]:
            layout = "eco"  # Default fallback
        
        # Build sheet preview structure compatible with PDF builder
        # Extract niveau from first exercise metadata if available
        niveau = ""
        if request_body.exercises and len(request_body.exercises) > 0:
            first_ex_metadata = request_body.exercises[0].get("metadata", {})
            niveau = first_ex_metadata.get("niveau", "") or ""
        
        sheet_preview = {
            "titre": request_body.title,
            "niveau": niveau,
            "items": []
        }
        
        # P0: Transform exercises to sheet items format (compatible with PDF builder)
        # The PDF builder expects: generated.questions[] with enonce_brut and solution_brut
        for idx, ex in enumerate(request_body.exercises, 1):
            enonce_html = ex.get("enonce_html", "")
            solution_html = ex.get("solution_html", "")
            figure_svg_enonce = ex.get("figure_svg_enonce") or ex.get("figure_svg", "")
            figure_svg_solution = ex.get("figure_svg_solution", "")
            
            # Build figure_html from SVG if present
            figure_html = ""
            if figure_svg_enonce:
                figure_html = figure_svg_enonce
            elif figure_svg_solution and not figure_html:
                figure_html = figure_svg_solution
            
            # P0: Convert HTML to "brut" format
            # The PDF builder's _render_question() now detects HTML and uses it directly
            # We pass the HTML as-is in enonce_brut/solution_brut
            enonce_brut = enonce_html if enonce_html else ""
            solution_brut = solution_html if solution_html else ""
            
            # P0: Debug logging for first exercise
            if idx == 1:
                logger.info(
                    f"[EXPORT_SELECTION] Exercise 1 mapping - "
                    f"enonce_html len={len(enonce_html)}, solution_html len={len(solution_html)}, "
                    f"figure_html len={len(figure_html)}, layout={layout}"
                )
                # Log a preview of the content (first 200 chars)
                if enonce_html:
                    preview = enonce_html[:200].replace('\n', ' ').replace('\r', ' ')
                    logger.info(f"[EXPORT_SELECTION] Exercise 1 enonce preview: {preview}...")
                else:
                    logger.warning(f"[EXPORT_SELECTION] ⚠️ Exercise 1 has EMPTY enonce_html!")
                if solution_html:
                    solution_preview = solution_html[:200].replace('\n', ' ').replace('\r', ' ')
                    logger.info(f"[EXPORT_SELECTION] Exercise 1 solution preview: {solution_preview}...")
                else:
                    logger.warning(f"[EXPORT_SELECTION] ⚠️ Exercise 1 has EMPTY solution_html!")
            
            # The PDF builder expects: generated.questions[] where each question has:
            # - enonce_brut: string (raw text or HTML)
            # - solution_brut: string (raw text or HTML)
            # - figure_html: string (optional SVG/HTML)
            # - data: dict (optional)
            question = {
                "id": f"q_{idx}",
                "enonce_brut": enonce_brut,
                "solution_brut": solution_brut,
                "figure_html": figure_html,
                "data": {}
            }
            
            item = {
                "item_id": f"item_{idx}",
                "order": ex.get("order", idx),
                "generated": {
                    "questions": [question]  # PDF builder expects questions array
                },
                "exercise_type_summary": ex.get("metadata", {})
            }
            sheet_preview["items"].append(item)
        
        # Import PDF builder functions
        from backend.engine.pdf_engine.mathalea_sheet_pdf_builder import (
            build_sheet_student_pdf,
            build_sheet_correction_pdf
        )
        
        # Generate PDF based on include_correction
        if request_body.include_correction:
            # Generate correction PDF (with solutions)
            pdf_bytes = build_sheet_correction_pdf(sheet_preview, layout=layout)
        else:
            # Generate student PDF (without solutions)
            pdf_bytes = build_sheet_student_pdf(sheet_preview, layout=layout)
        
        # Track export for quota (Free users only)
        if not is_pro:
            export_record = {
                "id": str(uuid.uuid4()),
                "document_id": f"selection_{uuid.uuid4()}",
                "export_type": "selection_pdf",
                "user_email": user_email,
                "is_pro": False,
                "created_at": datetime.now(timezone.utc)
            }
            await db.exports.insert_one(export_record)
        
        logger.info(
            f"✅ PDF export-selection généré pour {user_email} "
            f"(is_pro={is_pro}, layout={layout}, include_correction={request_body.include_correction})"
        )
        
        # Return PDF as binary response
        filename = f"{request_body.title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        
        return Response(content=pdf_bytes, media_type="application/pdf")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'export PDF selection: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la génération du PDF"
        )

# Include the router in the main app
app.include_router(api_router)

# Include MathALÉA system router (Sprint A - non-destructive extension)
from backend.routes.mathalea_routes import router as mathalea_router
from backend.routes.catalogue_routes import router as catalogue_router
app.include_router(mathalea_router)
app.include_router(catalogue_router)

# Include Exercises v1 API router (V1-BE-002)
from backend.routes.exercises_routes import router as exercises_router
app.include_router(exercises_router, prefix="/api/v1/exercises", tags=["Exercises v1"])

# Include Admin Curriculum router (V1 - READ-ONLY)
from backend.routes.admin_curriculum_routes import router as admin_curriculum_router, legacy_router as admin_curriculum_legacy_router
app.include_router(admin_curriculum_router, tags=["Admin Curriculum"])
app.include_router(admin_curriculum_legacy_router, tags=["Admin Curriculum Legacy"])

# Routes admin exercices (CRUD pour exercices figés)
from backend.routes.admin_exercises_routes import router as admin_exercises_router
app.include_router(admin_exercises_router, tags=["Admin Exercises"])

# Routes admin package (PR10 - Import/Export global)
from backend.routes.admin_package_routes import router as admin_package_router
app.include_router(admin_package_router, tags=["Admin Package"])

# Route catalogue curriculum (pour /generate)
from backend.routes.curriculum_catalog_routes import router as curriculum_catalog_router, legacy_router as curriculum_catalog_legacy_router
app.include_router(curriculum_catalog_router, tags=["Curriculum Catalog"])
app.include_router(curriculum_catalog_legacy_router, tags=["Curriculum Catalog"])

# Routes générateurs dynamiques (P0.2 + P2 - Variables schema & Preview)
from backend.routes.generators_routes import router as generators_router
app.include_router(generators_router, prefix="/api/v1/exercises", tags=["Generators"])
app.include_router(generators_router, prefix="/api/admin/exercises", tags=["Admin Generators"])

# Routes admin templates éditables (P1 - Templates MVP)
from backend.routes.admin_template_routes import router as admin_template_router
app.include_router(admin_template_router, tags=["Admin Templates"])

# Routes admin exercices statiques (P1.5 - Partie 2/3)
from backend.routes.admin_static_exercises_routes import router as admin_static_exercises_router
app.include_router(admin_static_exercises_router, tags=["Admin Static Exercises"])

# P4.B - Admin Chapter Generators
from backend.routes.admin_chapter_generators_routes import router as admin_chapter_generators_router
app.include_router(admin_chapter_generators_router, tags=["Admin - Chapter Generators"])

# P4.D - Debug routes (DEV-only)
from backend.routes.debug_routes import router as debug_router
app.include_router(debug_router, tags=["Debug"])

# Routes user sheets (P3.1 - Mes fiches)
from backend.routes.user_sheets_routes import router as user_sheets_router
app.include_router(user_sheets_router, tags=["User Sheets"])

# P0 - Import secure auth service
from backend.services.secure_auth_service import SecureAuthService

# P2 - Import password auth service
from backend.services.auth_password_service import (
    hash_password,
    verify_password,
    validate_password_strength
)

# Middleware request_id pour traçabilité
from backend.middleware.request_id import RequestIDMiddleware
app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
