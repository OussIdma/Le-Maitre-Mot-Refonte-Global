"""
Service de persistance des exercices figés en MongoDB.

Gère les opérations CRUD sur les exercices pilotes (GM07, GM08, etc.).
Maintient la synchronisation entre MongoDB et les fichiers Python de données.

Architecture:
- MongoDB: Source de vérité pour les exercices
- Fichiers Python: Générés automatiquement pour compatibilité avec les handlers
"""

import os
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, validator

from backend.generators.factory import GeneratorFactory
from backend.services.template_renderer import get_template_variables
from backend.utils.difficulty_utils import (
    normalize_difficulty,
    coerce_to_supported_difficulty,
    get_all_canonical_difficulties,
    map_ui_difficulty_to_generator,  # P4.D HOTFIX
)
from backend.observability import get_request_context
from backend.observability.logger import get_logger as get_obs_logger
from fastapi import HTTPException
import re

logger = logging.getLogger(__name__)

# Collection MongoDB pour les exercices
EXERCISES_COLLECTION = "admin_exercises"

# Chemin vers le dossier data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _extract_placeholders(template_str: Optional[str]) -> set:
    """Extrait les placeholders {{variable}} d'un template."""
    if not template_str:
        return set()
    pattern = r'\{\{\s*(\w+)\s*\}\}'
    matches = re.findall(pattern, template_str)
    return set(matches)


# =============================================================================
# MODÈLES PYDANTIC
# =============================================================================

class TemplateVariant(BaseModel):
    """
    Variant de template pour un exercice dynamique.
    """

    id: str = Field(..., description="Identifiant stable du variant (ex: 'v1', 'A', ...)")
    label: Optional[str] = Field(
        default=None, description="Label lisible du variant (optionnel)"
    )
    enonce_template_html: str = Field(
        ..., description="Template énoncé avec {{variables}}"
    )
    solution_template_html: str = Field(
        ..., description="Template solution avec {{variables}}"
    )
    weight: int = Field(
        default=1,
        ge=1,
        description="Poids relatif du variant pour la sélection future",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Métadonnées optionnelles (tags, notes pédagogiques, ...)",
    )


class ExerciseCreateRequest(BaseModel):
    """Modèle pour la création d'un exercice"""

    title: Optional[str] = Field(
        default=None, description="Titre lisible (optionnel, surtout pour les exercices dynamiques)"
    )
    family: Optional[str] = Field(
        default=None,
        description="Famille (déprécié): CONVERSION, COMPARAISON, PERIMETRE, PROBLEME, DUREES, etc.",
    )
    exercise_type: Optional[str] = Field(
        None, description="Type d'exercice (optionnel): LECTURE_HEURE, PLACER_AIGUILLES, etc."
    )
    difficulty: str = Field(..., description="Difficulté: facile, moyen, difficile")
    offer: str = Field(default="free", description="Offre: free ou pro")
    # Flag dynamique EN PREMIER pour que les validateurs puissent le lire
    is_dynamic: bool = Field(default=False, description="Exercice dynamique (template)")
    # Exercices statiques
    enonce_html: Optional[str] = Field(
        default="", description="Énoncé en HTML pur (requis si non dynamique)"
    )
    solution_html: Optional[str] = Field(
        default="", description="Solution en HTML pur (requis si non dynamique)"
    )
    needs_svg: bool = Field(default=False, description="Nécessite un SVG")
    variables: Optional[Dict[str, Any]] = Field(
        None, description="Variables pour le SVG (ex: {hour: 8, minute: 0})"
    )
    svg_enonce_brief: Optional[str] = Field(
        None, description="Description du SVG pour l'énoncé"
    )
    svg_solution_brief: Optional[str] = Field(
        None, description="Description du SVG pour la solution"
    )
    # Exercices dynamiques
    generator_key: Optional[str] = Field(
        None, description="Clé du générateur (ex: THALES_V1)"
    )
    enonce_template_html: Optional[str] = Field(
        None, description="Template énoncé avec {{variables}}"
    )
    solution_template_html: Optional[str] = Field(
        None, description="Template solution avec {{variables}}"
    )
    variables_schema: Optional[Dict[str, str]] = Field(
        None, description="Schéma des variables"
    )
    template_variants: Optional[List[TemplateVariant]] = Field(
        default=None,
        description=(
            "Liste des variantes de templates pour les exercices dynamiques. "
            "Si renseigné, devient la source de vérité pour le rendu dynamique."
        ),
    )

    @validator("enonce_html", always=True)
    def validate_enonce(cls, v, values):
        is_dynamic = values.get("is_dynamic", False)
        if not is_dynamic and not v:
            raise ValueError("enonce_html est requis pour les exercices statiques")
        return v or ""

    @validator("solution_html", always=True)
    def validate_solution(cls, v, values):
        is_dynamic = values.get("is_dynamic", False)
        if not is_dynamic and not v:
            raise ValueError("solution_html est requis pour les exercices statiques")
        return v or ""

    @validator("generator_key", always=True)
    def validate_generator(cls, v, values):
        is_dynamic = values.get("is_dynamic", False)
        if is_dynamic and not v:
            raise ValueError("generator_key est requis pour les exercices dynamiques")
        return v


class ExerciseUpdateRequest(BaseModel):
    """Modèle pour la mise à jour d'un exercice"""
    title: Optional[str] = None
    family: Optional[str] = None  # Déprécié
    exercise_type: Optional[str] = None
    difficulty: Optional[str] = None
    offer: Optional[str] = None
    enonce_html: Optional[str] = None
    solution_html: Optional[str] = None
    needs_svg: Optional[bool] = None
    variables: Optional[Dict[str, Any]] = None
    svg_enonce_brief: Optional[str] = None
    svg_solution_brief: Optional[str] = None
    is_dynamic: Optional[bool] = None
    generator_key: Optional[str] = None
    enonce_template_html: Optional[str] = None
    solution_template_html: Optional[str] = None
    variables_schema: Optional[Dict[str, str]] = None
    template_variants: Optional[List[TemplateVariant]] = None


class ExerciseResponse(BaseModel):
    """Réponse pour un exercice"""
    id: int
    chapter_code: str
    title: Optional[str] = None
    family: Optional[str] = None  # Déprécié
    exercise_type: Optional[str] = None
    difficulty: str
    offer: str
    enonce_html: Optional[str] = None
    solution_html: Optional[str] = None
    needs_svg: bool
    variables: Optional[Dict[str, Any]] = None
    svg_enonce_brief: Optional[str] = None
    svg_solution_brief: Optional[str] = None
    is_dynamic: Optional[bool] = None
    generator_key: Optional[str] = None
    enonce_template_html: Optional[str] = None
    solution_template_html: Optional[str] = None
    template_variants: Optional[List[TemplateVariant]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# SERVICE DE PERSISTANCE
# =============================================================================

class ExercisePersistenceService:
    """
    Service de persistance pour les exercices figés.
    Gère la synchronisation MongoDB <-> fichiers Python.
    """
    
    # Chapitres pilotes avec exercices figés
    PILOT_CHAPTERS = ["6e_GM07", "6e_GM08", "6e_TESTS_DYN"]
    
    # Cache TTL pour get_stats (5 minutes)
    STATS_CACHE_TTL = timedelta(minutes=5)
    # Helper interne pour invalider le cache stats
    def _invalidate_stats_cache(self, chapter_code: str) -> None:
        cache_key = f"{chapter_code.upper().replace('-', '_')}_stats"
        if cache_key in self._stats_cache:
            self._stats_cache.pop(cache_key, None)
            logger.debug(f"[CACHE] Stats invalidated for {cache_key}")
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[EXERCISES_COLLECTION]
        self._initialized = {}
        # Cache stats par instance (singleton, mais sécurité)
        self._stats_cache: Dict[str, Tuple[Dict[str, Any], datetime]] = {}
    
    async def initialize_chapter(self, chapter_code: str) -> None:
        """
        Initialise la collection pour un chapitre si nécessaire.
        Charge les exercices depuis le fichier Python existant.
        
        Cache : Utilise self._initialized pour éviter requêtes DB répétées.
        """
        chapter_upper = chapter_code.upper().replace("-", "_")
        
        # Cache check AVANT requête DB
        if chapter_upper in self._initialized:
            logger.debug(f"[CACHE HIT] Chapter {chapter_upper} déjà initialisé")
            return
        
        logger.info(f"[CACHE MISS] Initialisation {chapter_upper}")
        
        # Compter les exercices existants pour ce chapitre
        count = await self.collection.count_documents({"chapter_code": chapter_upper})
        
        # P0 - DÉSACTIVATION LEGACY : Ne plus charger depuis fichiers Python
        # Les exercices legacy ont été migrés en DB (migration P3.2)
        # DB est maintenant la source de vérité unique
        # if count == 0:
        #     await self._load_from_python_file(chapter_upper)
        #     count = await self.collection.count_documents({"chapter_code": chapter_upper})
        
        if count == 0:
            logger.info(f"[P0] Aucun exercice en DB pour {chapter_upper}. DB est la source unique (legacy désactivé).")
        
        # Créer les index (idempotent, mais coûteux → éviter si possible)
        try:
            await self.collection.create_index([("chapter_code", 1), ("id", 1)], unique=True)
            await self.collection.create_index("chapter_code")
            await self.collection.create_index("difficulty")
            await self.collection.create_index("offer")
        except Exception as e:
            # Index peut déjà exister → OK
            logger.debug(f"Index peut déjà exister pour {chapter_upper}: {e}")
        
        self._initialized[chapter_upper] = True
        logger.info(f"Exercices service initialisé pour {chapter_upper} avec {count} exercices")
    
    async def _load_from_python_file(self, chapter_code: str) -> None:
        """
        P0 - DÉSACTIVÉ : Chargement depuis fichiers Python legacy
        
        Les exercices legacy ont été migrés en DB (migration P3.2).
        DB est maintenant la source de vérité unique.
        
        Cette méthode est conservée pour référence mais ne fait plus rien.
        """
        logger.warning(
            f"[P0] _load_from_python_file désactivé pour {chapter_code}. "
            f"Les exercices doivent être en DB (migration P3.2 terminée)."
        )
        return
    
    async def _sync_to_python_file(self, chapter_code: str) -> None:
        """
        Synchronise les exercices MongoDB vers le fichier Python.
        Génère le code Python compatible avec les handlers existants.
        """
        exercises = await self.get_exercises(chapter_code)
        
        # Déterminer le nom du fichier et de la variable
        file_mapping = {
            "6E_GM07": ("gm07_exercises.py", "GM07_EXERCISES", "Durées et lecture de l'heure"),
            "6E_GM08": ("gm08_exercises.py", "GM08_EXERCISES", "Grandeurs et Mesures (Longueurs, Périmètres)"),
        }
        
        info = file_mapping.get(chapter_code)
        if not info:
            logger.warning(f"Pas de mapping fichier pour {chapter_code}")
            return
        
        filename, var_name, description = info
        filepath = os.path.join(DATA_DIR, filename)
        
        # Générer le contenu Python
        content = self._generate_python_file(chapter_code, var_name, description, exercises)
        
        # Écrire le fichier
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Fichier Python synchronisé: {filepath} ({len(exercises)} exercices)")
    
    def _generate_python_file(self, chapter_code: str, var_name: str, description: str, exercises: List[Dict]) -> str:
        """Génère le contenu du fichier Python pour les exercices"""
        code = chapter_code.split("_")[1]  # GM07, GM08
        
        header = f'''"""
{code} - Exercices figés : {description}
{'=' * (len(code) + len(description) + 25)}

Chapitre pilote avec {len(exercises)} exercices validés.
- FREE: ids 1-10
- PREMIUM (PRO): ids 11-20

Ce fichier est la SOURCE UNIQUE pour {code}.
Aucune génération aléatoire - exercices figés et validés.

IMPORTANT: Tout le contenu est en HTML PUR.
- Pas de Markdown (**texte**)
- Pas de LaTeX ($...$)
- Utiliser <strong>, <em>, ×, ÷, etc.

⚠️ FICHIER GÉNÉRÉ AUTOMATIQUEMENT PAR L'ADMIN
   Ne pas modifier manuellement - utiliser /admin/curriculum
"""

from typing import List, Dict, Any, Optional
import random


# =============================================================================
# {len(exercises)} EXERCICES {code} VALIDÉS - HTML PUR (sans Markdown ni LaTeX)
# =============================================================================

{var_name}: List[Dict[str, Any]] = [
'''
        
        # Ajouter chaque exercice
        for ex in exercises:
            # Construire les champs optionnels
            exercise_type_str = f'"{ex["exercise_type"]}"' if ex.get('exercise_type') else 'None'
            variables_str = repr(ex.get('variables')) if ex.get('variables') else 'None'
            svg_enonce_brief_str = f'"{ex["svg_enonce_brief"]}"' if ex.get('svg_enonce_brief') else 'None'
            svg_solution_brief_str = f'"{ex["svg_solution_brief"]}"' if ex.get('svg_solution_brief') else 'None'
            
            content = f'''    {{
        "id": {ex['id']},
        "family": "{ex['family']}",
        "difficulty": "{ex['difficulty']}",
        "offer": "{ex['offer']}",
        "variables": {variables_str},
        "enonce_html": """{ex['enonce_html']}""",
        "solution_html": """{ex['solution_html']}""",
        "needs_svg": {str(ex.get('needs_svg', False))},
        "exercise_type": {exercise_type_str},
        "svg_enonce_brief": {svg_enonce_brief_str},
        "svg_solution_brief": {svg_solution_brief_str}
    }},
'''
            header += content
        
        header += ''']


# =============================================================================
# FONCTIONS D'ACCÈS AUX EXERCICES (Compatible avec handlers)
# =============================================================================

'''
        
        # Ajouter les fonctions utilitaires
        header += f'''
def get_{code.lower()}_exercises(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filtre les exercices selon les critères.
    
    Args:
        offer: "free" ou "pro" (None = tous selon règles)
        difficulty: "facile", "moyen", "difficile" (None = tous)
    
    Returns:
        Liste d'exercices filtrés
    """
    exercises = {var_name}
    
    # Filtrer par offer
    if offer:
        offer = offer.lower()
        if offer == "free":
            exercises = [ex for ex in exercises if ex["offer"] == "free"]
        elif offer == "pro":
            pass  # PRO voit tout
    else:
        # Par défaut, FREE ne voit que free
        exercises = [ex for ex in exercises if ex["offer"] == "free"]
    
    # Filtrer par difficulté
    if difficulty:
        difficulty = difficulty.lower()
        exercises = [ex for ex in exercises if ex["difficulty"] == difficulty]
    
    return exercises


def get_random_{code.lower()}_exercise(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    seed: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Sélectionne UN exercice aléatoire.
    
    Args:
        offer: "free" ou "pro" (None = free par défaut)
        difficulty: "facile", "moyen", "difficile" (None = tous)
        seed: graine pour reproductibilité (optionnel)
    
    Returns:
        Un exercice aléatoire ou None si aucun disponible
    """
    available = get_{code.lower()}_exercises(offer=offer, difficulty=difficulty)
    
    if not available:
        return None
    
    if seed is not None:
        random.seed(seed)
    
    return random.choice(available)


def get_{code.lower()}_batch(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    count: int = 1,
    seed: Optional[int] = None
) -> tuple:
    """
    Génère un batch d'exercices SANS DOUBLONS.
    
    Args:
        offer: "free" ou "pro"
        difficulty: filtre optionnel
        count: nombre d'exercices demandés
        seed: graine pour reproductibilité
    
    Returns:
        Tuple (exercices: List, batch_metadata: Dict)
    """
    available = get_{code.lower()}_exercises(offer=offer, difficulty=difficulty)
    pool_size = len(available)
    
    batch_meta = {{
        "requested": count,
        "available": pool_size,
        "returned": 0,
        "filters": {{
            "offer": offer or "free",
            "difficulty": difficulty
        }}
    }}
    
    if pool_size == 0:
        batch_meta["warning"] = f"Aucun exercice disponible pour les filtres sélectionnés."
        return [], batch_meta
    
    # Mélanger avec seed pour reproductibilité
    if seed is not None:
        random.seed(seed)
    
    shuffled = available.copy()
    random.shuffle(shuffled)
    
    # Prendre au maximum ce qui est disponible
    actual_count = min(count, pool_size)
    selected = shuffled[:actual_count]
    
    batch_meta["returned"] = actual_count
    
    if actual_count < count:
        batch_meta["warning"] = f"Seulement {{pool_size}} exercices disponibles pour les filtres sélectionnés ({{count}} demandés)."
    
    return selected, batch_meta


def get_exercise_by_seed_index(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    seed: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Sélectionne UN exercice de manière déterministe.
    """
    available = get_{code.lower()}_exercises(offer=offer, difficulty=difficulty)
    
    if not available:
        return None
    
    if seed is not None:
        random.seed(seed)
        index = random.randint(0, len(available) - 1)
    else:
        index = random.randint(0, len(available) - 1)
    
    return available[index]


def get_{code.lower()}_stats() -> Dict[str, Any]:
    """Statistiques sur les exercices"""
    exercises = {var_name}
    
    stats = {{
        "total": len(exercises),
        "by_offer": {{"free": 0, "pro": 0}},
        "by_difficulty": {{"facile": 0, "moyen": 0, "difficile": 0}},
        "by_family": {{}}
    }}
    
    for ex in exercises:
        stats["by_offer"][ex["offer"]] = stats["by_offer"].get(ex["offer"], 0) + 1
        stats["by_difficulty"][ex["difficulty"]] = stats["by_difficulty"].get(ex["difficulty"], 0) + 1
        
        family = ex.get("family")
        if family:
            stats["by_family"][family] = stats["by_family"].get(family, 0) + 1
    
    return stats
'''
        
        return header
    
    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================
    
    async def get_exercises(
        self,
        chapter_code: str,
        offer: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Récupère les exercices d'un chapitre avec filtres optionnels"""
        from logger import get_logger
        diag_logger = get_logger()

        chapter_upper = chapter_code.upper().replace("-", "_")
        await self.initialize_chapter(chapter_upper)

        # P0_FIX : Normaliser difficulty avant la query MongoDB (standard → moyen)
        effective_difficulty = difficulty
        if difficulty:
            try:
                effective_difficulty = normalize_difficulty(difficulty)
                if effective_difficulty != difficulty:
                    logger.info(
                        f"[P0_FIX] difficulty normalisée: '{difficulty}' → '{effective_difficulty}' pour query"
                    )
            except ValueError as e:
                logger.warning(f"[P0_FIX] difficulty invalide '{difficulty}', ignorée: {e}")
                effective_difficulty = None

        query = {"chapter_code": chapter_upper}

        # P0_FIX : Logique d'offre hiérarchique
        # - pro a accès aux exercices free ET pro
        # - free n'a accès qu'aux exercices free
        if offer:
            offer_lower = offer.lower()
            if offer_lower == 'pro':
                query["offer"] = {"$in": ["free", "pro"]}
                logger.info(f"[P0_FIX] offer=pro → query inclut free ET pro")
            else:
                query["offer"] = offer_lower
        if effective_difficulty:
            query["difficulty"] = effective_difficulty.lower()

        # P0_FIX : Log de la requête MongoDB exacte avec difficulty effective
        diag_logger.info(
            f"[P0_FIX] MongoDB query: collection='{self.collection.name}', "
            f"query={query}, difficulty_input='{difficulty}', difficulty_effective='{effective_difficulty}'"
        )

        exercises = await self.collection.find(
            query,
            {"_id": 0}
        ).sort("id", 1).to_list(1000)  # Augmenter la limite pour les chapitres avec beaucoup d'exercices

        diag_logger.info(
            f"[P0_FIX] MongoDB result: {len(exercises)} exercices trouvés pour {chapter_upper}"
        )

        return exercises
    
    async def get_exercise_by_id(self, chapter_code: str, exercise_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un exercice par son ID"""
        chapter_upper = chapter_code.upper().replace("-", "_")
        await self.initialize_chapter(chapter_upper)
        
        exercise = await self.collection.find_one(
            {"chapter_code": chapter_upper, "id": exercise_id},
            {"_id": 0}
        )
        
        return exercise
    
    async def create_exercise(self, chapter_code: str, request: ExerciseCreateRequest) -> Dict[str, Any]:
        """
        Crée un nouvel exercice.
        L'ID est automatiquement assigné (max_id + 1).
        """
        chapter_upper = chapter_code.upper().replace("-", "_")
        await self.initialize_chapter(chapter_upper)
        
        # Valider les données
        self._validate_exercise_data(request)
        
        # Validation des placeholders pour exercices dynamiques
        if request.is_dynamic and request.generator_key:
            self._validate_template_placeholders(
                generator_key=request.generator_key,
                enonce_template_html=request.enonce_template_html,
                solution_template_html=request.solution_template_html,
                template_variants=request.template_variants,
                exercise_params=request.variables or {}
            )
        
        # Déterminer exercise_type pour les dynamiques (source de vérité GeneratorFactory)
        exercise_type_resolved = request.exercise_type.upper() if request.exercise_type else None
        if request.is_dynamic and request.generator_key:
            gen_type = GeneratorFactory.get_exercise_type(request.generator_key)
            if not gen_type:
                raise ValueError(f"generator_key inconnu ou sans exercise_type: {request.generator_key}")
            # Verrou collision : si un exercise_type est fourni et diffère, on refuse
            if exercise_type_resolved and exercise_type_resolved != gen_type:
                raise ValueError(
                    f"collision exercise_type/generator_key: exercise_type='{exercise_type_resolved}' "
                    f"mais {request.generator_key} correspond à '{gen_type}'. "
                    "Retirez l'exercise_type manuel ou choisissez le generator_key adéquat."
                )
            exercise_type_resolved = gen_type
        
        # Trouver le prochain ID
        max_doc = await self.collection.find_one(
            {"chapter_code": chapter_upper},
            sort=[("id", -1)]
        )
        next_id = (max_doc["id"] + 1) if max_doc else 1
        
        # P0 - Calculer exercise_uid pour éviter l'erreur E11000 (duplicate key sur null)
        # Pour les exercices dynamiques, utiliser les templates
        # Pour les exercices statiques, utiliser l'énoncé/solution HTML
        if request.is_dynamic:
            # Exercice dynamique : utiliser les templates
            enonce_content = request.enonce_template_html or ""
            solution_content = request.solution_template_html or ""
        else:
            # Exercice statique : utiliser l'énoncé/solution HTML
            enonce_content = request.enonce_html or ""
            solution_content = request.solution_html or ""
        
        # Calculer l'UID stable (même logique que migration)
        normalized_enonce = enonce_content.strip().lower()
        normalized_solution = solution_content.strip().lower()
        unique_string = f"{chapter_upper}|{normalized_enonce}|{normalized_solution}|{request.difficulty.lower()}"
        exercise_uid = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()
        
        # Vérifier si un exercice avec le même UID existe déjà
        existing = await self.collection.find_one({"exercise_uid": exercise_uid})
        if existing:
            raise ValueError(
                f"Un exercice identique existe déjà (UID={exercise_uid[:8]}...). "
                f"Modifiez légèrement l'énoncé ou la solution pour créer un nouvel exercice."
            )
        
        # Créer le document
        doc = {
            "chapter_code": chapter_upper,
            "id": next_id,
            "exercise_uid": exercise_uid,  # P0 - UID calculé pour éviter duplicate key
            "title": request.title,
            "family": request.family.upper() if request.family else None,
            "exercise_type": exercise_type_resolved,
            "difficulty": request.difficulty.lower(),
            "offer": request.offer.lower(),
            "enonce_html": request.enonce_html or "",
            "solution_html": request.solution_html or "",
            "needs_svg": request.needs_svg,
            "variables": request.variables,
            "svg_enonce_brief": request.svg_enonce_brief,
            "svg_solution_brief": request.svg_solution_brief,
            # Champs dynamiques
            "is_dynamic": request.is_dynamic,
            "generator_key": request.generator_key,
            "enonce_template_html": request.enonce_template_html,
            "solution_template_html": request.solution_template_html,
            "variables_schema": request.variables_schema,
            "template_variants": [
                variant.dict() for variant in (request.template_variants or [])
            ] or None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await self.collection.insert_one(doc)
        if request.family:
            logger.warning(f"[DEPRECATED] Champ family utilisé lors de la création (chapter={chapter_upper}, family={request.family.upper()}). Migrer vers exercise_type.")
        
        # Synchroniser avec le fichier Python (seulement pour GM07/GM08)
        if chapter_upper in ["6E_GM07", "6E_GM08"]:
            await self._sync_to_python_file(chapter_upper)
            await self._reload_handler(chapter_upper)
        
        # Invalidate stats cache
        self._invalidate_stats_cache(chapter_upper)
        # Invalidate catalog cache (6e)
        try:
            from curriculum.loader import invalidate_catalog_cache
            invalidate_catalog_cache("6e")
        except Exception as e:
            logger.warning(f"[CATALOG] Impossible d'invalider le cache catalogue: {e}")
        
        logger.info(f"Exercice créé: {chapter_upper} #{next_id} (dynamic={request.is_dynamic})")
        
        del doc["_id"]
        return doc
    
    async def update_exercise(
        self,
        chapter_code: str,
        exercise_id: int,
        request: ExerciseUpdateRequest
    ) -> Dict[str, Any]:
        """Met à jour un exercice existant"""
        chapter_upper = chapter_code.upper().replace("-", "_")
        await self.initialize_chapter(chapter_upper)
        
        # Vérifier l'existence
        existing = await self.collection.find_one({
            "chapter_code": chapter_upper,
            "id": exercise_id
        })
        
        if not existing:
            raise ValueError(f"Exercice #{exercise_id} non trouvé dans {chapter_upper}")
        
        # Construire les champs à mettre à jour
        update_data = {}
        
        if request.family is not None:
            update_data["family"] = request.family.upper() if request.family else None
            if request.family:
                logger.warning(f"[DEPRECATED] Champ family utilisé en update (chapter={chapter_upper}, family={request.family.upper()}). Migrer vers exercise_type.")
        if request.exercise_type is not None:
            update_data["exercise_type"] = request.exercise_type.upper() if request.exercise_type else None
        if request.difficulty is not None:
            update_data["difficulty"] = request.difficulty.lower()
        if request.offer is not None:
            update_data["offer"] = request.offer.lower()
        if request.enonce_html is not None:
            update_data["enonce_html"] = request.enonce_html
        if request.solution_html is not None:
            update_data["solution_html"] = request.solution_html
        if request.needs_svg is not None:
            update_data["needs_svg"] = request.needs_svg
        if request.title is not None:
            update_data["title"] = request.title
        # Champs dynamiques
        if request.enonce_template_html is not None:
            update_data["enonce_template_html"] = request.enonce_template_html
        if request.solution_template_html is not None:
            update_data["solution_template_html"] = request.solution_template_html
        if request.is_dynamic is not None:
            update_data["is_dynamic"] = request.is_dynamic
        if request.generator_key is not None:
            update_data["generator_key"] = request.generator_key
        
        # Validation des placeholders pour exercices dynamiques (si template ou generator_key modifié)
        is_dynamic = update_data.get("is_dynamic", existing.get("is_dynamic", False))
        generator_key = update_data.get("generator_key", existing.get("generator_key"))
        enonce_template = update_data.get("enonce_template_html", existing.get("enonce_template_html"))
        solution_template = update_data.get("solution_template_html", existing.get("solution_template_html"))
        template_variants = update_data.get("template_variants", existing.get("template_variants"))
        exercise_params = update_data.get("variables", existing.get("variables", {}))
        
        if is_dynamic and generator_key and (enonce_template or solution_template or template_variants):
            self._validate_template_placeholders(
                generator_key=generator_key,
                enonce_template_html=enonce_template,
                solution_template_html=solution_template,
                template_variants=template_variants,
                exercise_params=exercise_params or {}
            )
        
        # Sauvegarder variables même si c'est un objet vide (pour permettre de réinitialiser)
        # Note: request.variables peut être None (non fourni), {} (vide), ou un dict avec des valeurs
        if hasattr(request, 'variables') and request.variables is not None:
            # Si c'est un objet vide {}, on le sauvegarde quand même (pour réinitialiser les paramètres)
            update_data["variables"] = request.variables if isinstance(request.variables, dict) else {}
            logger.debug(f"[UPDATE] Variables mises à jour: {update_data['variables']}")
        if request.variables_schema is not None:
            update_data["variables_schema"] = request.variables_schema
        if request.template_variants is not None:
            update_data["template_variants"] = [
                variant.dict() if hasattr(variant, 'dict') else variant
                for variant in request.template_variants
            ] if request.template_variants else None
        # Synchroniser exercise_type si dynamique et generator_key présent (nouveau ou existant)
        if (update_data.get("is_dynamic", existing.get("is_dynamic")) and
            update_data.get("generator_key", existing.get("generator_key"))):
            gen_key = update_data.get("generator_key", existing.get("generator_key"))
            gen_type = GeneratorFactory.get_exercise_type(gen_key)
            if not gen_type:
                raise ValueError(f"generator_key inconnu ou sans exercise_type: {gen_key}")
            # Verrou collision : si un exercise_type est fourni et diffère, on refuse
            if request.exercise_type is not None:
                requested_type = request.exercise_type.upper() if request.exercise_type else None
                if requested_type and requested_type != gen_type:
                    raise ValueError(
                        f"collision exercise_type/generator_key: exercise_type='{requested_type}' "
                        f"mais {gen_key} correspond à '{gen_type}'. "
                        "Retirez l'exercise_type manuel ou choisissez le generator_key adéquat."
                    )
            update_data["exercise_type"] = gen_type
        
        if not update_data:
            del existing["_id"]
            return existing
        
        # P0 - Recalculer exercise_uid si le contenu a changé
        # (pour éviter les doublons et maintenir la cohérence)
        content_changed = any(key in update_data for key in [
            "enonce_html", "solution_html", "enonce_template_html", 
            "solution_template_html", "difficulty", "is_dynamic"
        ])
        
        if content_changed or not existing.get("exercise_uid"):
            # Recalculer l'UID avec les nouvelles valeurs
            is_dynamic = update_data.get("is_dynamic", existing.get("is_dynamic", False))
            if is_dynamic:
                enonce_content = update_data.get("enonce_template_html", existing.get("enonce_template_html", "")) or ""
                solution_content = update_data.get("solution_template_html", existing.get("solution_template_html", "")) or ""
            else:
                enonce_content = update_data.get("enonce_html", existing.get("enonce_html", "")) or ""
                solution_content = update_data.get("solution_html", existing.get("solution_html", "")) or ""
            
            normalized_enonce = enonce_content.strip().lower()
            normalized_solution = solution_content.strip().lower()
            difficulty = update_data.get("difficulty", existing.get("difficulty", "moyen")).lower()
            unique_string = f"{chapter_upper}|{normalized_enonce}|{normalized_solution}|{difficulty}"
            new_exercise_uid = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()
            
            # Vérifier si le nouvel UID existe déjà (sauf pour cet exercice)
            existing_uid = await self.collection.find_one({
                "exercise_uid": new_exercise_uid,
                "_id": {"$ne": existing.get("_id")}
            })
            if existing_uid:
                logger.warning(
                    f"[UPDATE] UID collision détectée pour exercice #{exercise_id} "
                    f"(nouvel UID={new_exercise_uid[:8]}... existe déjà). "
                    "L'UID ne sera pas mis à jour pour éviter les doublons."
                )
            else:
                update_data["exercise_uid"] = new_exercise_uid
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await self.collection.update_one(
            {"chapter_code": chapter_upper, "id": exercise_id},
            {"$set": update_data}
        )
        
        # Synchroniser avec le fichier Python
        await self._sync_to_python_file(chapter_upper)
        
        # Recharger le handler
        await self._reload_handler(chapter_upper)
        
        # Invalidate stats cache
        self._invalidate_stats_cache(chapter_upper)
        
        # Invalider le cache catalogue pour refléter l'ajout/modif
        try:
            from curriculum.loader import invalidate_catalog_cache
            invalidate_catalog_cache("6e")
        except Exception as e:
            logger.warning(f"[CATALOG] Impossible d'invalider le cache catalogue: {e}")
        
        logger.info(f"Exercice mis à jour: {chapter_upper} #{exercise_id}")
        
        # Récupérer l'exercice mis à jour
        updated = await self.collection.find_one(
            {"chapter_code": chapter_upper, "id": exercise_id},
            {"_id": 0}
        )
        
        return updated
    
    async def delete_exercise(self, chapter_code: str, exercise_id: int) -> bool:
        """Supprime un exercice"""
        chapter_upper = chapter_code.upper().replace("-", "_")
        await self.initialize_chapter(chapter_upper)
        
        # Vérifier l'existence
        existing = await self.collection.find_one({
            "chapter_code": chapter_upper,
            "id": exercise_id
        })
        
        if not existing:
            raise ValueError(f"Exercice #{exercise_id} non trouvé dans {chapter_upper}")
        
        result = await self.collection.delete_one({
            "chapter_code": chapter_upper,
            "id": exercise_id
        })
        
        if result.deleted_count > 0:
            # Synchroniser avec le fichier Python
            await self._sync_to_python_file(chapter_upper)
            
            # Recharger le handler
            await self._reload_handler(chapter_upper)
            
            # Invalidate stats cache
            self._invalidate_stats_cache(chapter_upper)
            
            # Invalider le cache catalogue (6e) pour refléter la suppression
            try:
                from curriculum.loader import invalidate_catalog_cache
                invalidate_catalog_cache("6e")
            except Exception as e:
                logger.warning(f"[CATALOG] Impossible d'invalider le cache catalogue: {e}")
            
            logger.info(f"Exercice supprimé: {chapter_upper} #{exercise_id}")
            return True
        
        return False
    
    async def find_exercise_by_id_anywhere(self, exercise_id: int) -> Optional[Dict[str, Any]]:
        """Trouve un exercice par son ID dans n'importe quel chapitre"""
        exercise = await self.collection.find_one(
            {"id": exercise_id},
            {"_id": 0}
        )
        return exercise
    
    async def get_stats(self, chapter_code: str) -> Dict[str, Any]:
        """
        Statistiques sur les exercices d'un chapitre.
        
        Cache TTL 5 minutes pour éviter agrégations MongoDB répétées.
        """
        chapter_upper = chapter_code.upper().replace("-", "_")
        
        # Check cache TTL
        cache_key = f"{chapter_upper}_stats"
        now = datetime.now(timezone.utc)
        
        if cache_key in self._stats_cache:
            cached_stats, cached_time = self._stats_cache[cache_key]
            if now - cached_time < self.STATS_CACHE_TTL:
                logger.debug(f"[CACHE HIT] Stats pour {chapter_upper}")
                return cached_stats
        
        logger.info(f"[CACHE MISS] Calcul stats pour {chapter_upper}")
        
        await self.initialize_chapter(chapter_upper)
        
        total = await self.collection.count_documents({"chapter_code": chapter_upper})
        
        # Agrégations MongoDB (coûteuses)
        by_offer = {}
        by_difficulty = {}
        by_family = {}
        
        offer_agg = await self.collection.aggregate([
            {"$match": {"chapter_code": chapter_upper}},
            {"$group": {"_id": "$offer", "count": {"$sum": 1}}}
        ]).to_list(10)
        
        for item in offer_agg:
            by_offer[item["_id"]] = item["count"]
        
        diff_agg = await self.collection.aggregate([
            {"$match": {"chapter_code": chapter_upper}},
            {"$group": {"_id": "$difficulty", "count": {"$sum": 1}}}
        ]).to_list(10)
        
        for item in diff_agg:
            by_difficulty[item["_id"]] = item["count"]
        
        family_agg = await self.collection.aggregate([
            {"$match": {"chapter_code": chapter_upper}},
            {"$group": {"_id": "$family", "count": {"$sum": 1}}}
        ]).to_list(20)
        
        for item in family_agg:
            by_family[item["_id"]] = item["count"]
        
        stats = {
            "chapter_code": chapter_upper,
            "total": total,
            "by_offer": by_offer,
            "by_difficulty": by_difficulty,
            "by_family": by_family
        }
        
        # Mettre en cache
        self._stats_cache[cache_key] = (stats, now)
        
        return stats
    
    def _validate_exercise_data(self, request: ExerciseCreateRequest) -> None:
        """Valide les données d'un exercice"""
        # Vérifier la difficulté
        if request.difficulty.lower() not in ["facile", "moyen", "difficile"]:
            raise ValueError(f"Difficulté invalide: {request.difficulty}")
        
        # Vérifier l'offer
        if request.offer.lower() not in ["free", "pro"]:
            raise ValueError(f"Offer invalide: {request.offer}")
        
        # Validation spécifique selon le type (dynamique ou statique)
        if request.is_dynamic:
            # Exercice dynamique - vérifier le générateur
            if not request.generator_key:
                raise ValueError("generator_key est requis pour les exercices dynamiques")

            # Un exercice dynamique doit avoir AU MOINS un template :
            # - soit en mode legacy (enonce_template_html + solution_template_html),
            # - soit via une ou plusieurs TemplateVariant.
            has_legacy_templates = bool(
                request.enonce_template_html
                and request.enonce_template_html.strip()
                and request.solution_template_html
                and request.solution_template_html.strip()
            )
            has_variants = bool(request.template_variants and len(request.template_variants) > 0)

            if not has_legacy_templates and not has_variants:
                raise ValueError(
                    "Au moins un template (legacy ou variant) est requis pour un exercice dynamique"
                )

            # Si des variants sont fournis, vérifier qu'ils sont complets et cohérents
            if request.template_variants:
                for idx, variant in enumerate(request.template_variants):
                    # id non vide
                    if not variant.id or not str(variant.id).strip():
                        raise ValueError(
                            f"Le variant #{idx + 1} doit avoir un id non vide"
                        )

                    # weight >= 1 (double garde-fou en plus de la contrainte Pydantic)
                    if variant.weight is None or variant.weight < 1:
                        raise ValueError(
                            f"Le variant #{idx + 1} ({variant.id}) doit avoir un weight >= 1"
                        )

                    # templates non vides
                    if (
                        not variant.enonce_template_html
                        or not variant.enonce_template_html.strip()
                    ):
                        raise ValueError(
                            f"Le variant #{idx + 1} ({variant.id}) doit avoir un template énoncé non vide"
                        )
                    if (
                        not variant.solution_template_html
                        or not variant.solution_template_html.strip()
                    ):
                        raise ValueError(
                            f"Le variant #{idx + 1} ({variant.id}) doit avoir un template solution non vide"
                        )
        else:
            # Exercice statique - vérifier le HTML
            if not request.enonce_html or not request.enonce_html.strip():
                raise ValueError("L'énoncé ne peut pas être vide")
            
            if not request.solution_html or not request.solution_html.strip():
                raise ValueError("La solution ne peut pas être vide")
            
            # Vérifier pas de LaTeX
            if "$" in request.enonce_html or "$" in request.solution_html:
                raise ValueError("Le contenu ne doit pas contenir de LaTeX ($). Utilisez du HTML pur.")
    
    def _validate_template_placeholders(
        self,
        generator_key: str,
        enonce_template_html: Optional[str],
        solution_template_html: Optional[str],
        template_variants: Optional[List[Any]],  # Peut être List[TemplateVariant] ou List[Dict]
        exercise_params: Dict[str, Any]
    ) -> None:
        """
        Valide que tous les placeholders des templates peuvent être résolus par le générateur.
        Teste pour chaque difficulté (facile, moyen, difficile).
        
        Lève HTTPException(422) avec error_code="ADMIN_TEMPLATE_MISMATCH" si mismatch.
        """
        # Extraire tous les placeholders attendus
        placeholders_expected = set()
        
        # Templates principaux
        if enonce_template_html:
            placeholders_expected.update(_extract_placeholders(enonce_template_html))
        if solution_template_html:
            placeholders_expected.update(_extract_placeholders(solution_template_html))
        
        # Templates variants
        if template_variants:
            for variant in template_variants:
                # Gérer les objets Pydantic TemplateVariant ou les dictionnaires
                if hasattr(variant, 'dict'):
                    # Objet Pydantic TemplateVariant
                    variant_dict = variant.dict()
                elif isinstance(variant, dict):
                    # Dictionnaire déjà
                    variant_dict = variant
                else:
                    # Type inattendu, skip
                    logger.warning(f"Type de variant inattendu: {type(variant)}, skip")
                    continue
                
                if variant_dict.get("enonce_template_html"):
                    placeholders_expected.update(_extract_placeholders(variant_dict["enonce_template_html"]))
                if variant_dict.get("solution_template_html"):
                    placeholders_expected.update(_extract_placeholders(variant_dict["solution_template_html"]))
        
        if not placeholders_expected:
            # Pas de placeholders à valider
            return
        
        # Récupérer le générateur
        gen_class = GeneratorFactory.get(generator_key)
        if not gen_class:
            # Le générateur sera validé ailleurs, on skip ici
            return
        
        # P4.D HOTFIX - Tester pour chaque difficulté canonique avec mapping UI -> générateur
        difficulties_to_test = ["facile", "moyen", "difficile"]
        all_mismatches = []
        obs_logger = get_obs_logger('EXERCISE_PERSISTENCE')
        ctx = get_request_context()
        ctx.update({'generator_key': generator_key})
        
        for requested_difficulty in difficulties_to_test:
            # P4.D HOTFIX - Mapper la difficulté UI vers la difficulté réelle du générateur
            generator_difficulty = map_ui_difficulty_to_generator(
                generator_key,
                requested_difficulty,
                obs_logger
            )
            
            try:
                
                # Préparer les paramètres de génération avec la difficulté mappée
                gen_params = exercise_params.copy()
                gen_params["difficulty"] = generator_difficulty
                
                # Générer un exercice de test
                generator = gen_class(seed=42)  # Seed fixe pour reproductibilité
                result = generator.generate(gen_params)
                
                # Récupérer les clés fournies
                keys_provided = set(result.get("variables", {}).keys())
                
                # Comparer
                missing = sorted(placeholders_expected - keys_provided)
                extra = sorted(keys_provided - placeholders_expected)
                
                if missing:
                    all_mismatches.append({
                        "difficulty": requested_difficulty,
                        "difficulty_used": generator_difficulty,  # P4.D HOTFIX - Difficulté réellement utilisée
                        "missing": missing,
                        "extra": extra,
                        "placeholders_expected": sorted(placeholders_expected),
                        "keys_provided": sorted(keys_provided)
                    })
            except ValueError as e:
                # P4.D HOTFIX - Distinguer les erreurs de difficulté invalide des autres erreurs
                error_msg = str(e)
                if "difficulté" in error_msg.lower() or "difficulty" in error_msg.lower() or "INVALID_DIFFICULTY" in error_msg:
                    # Erreur de difficulté invalide - ne pas considérer comme mismatch
                    logger.warning(
                        f"[GENERATOR_INVALID_DIFFICULTY] Validation placeholder pour {generator_key} "
                        f"(ui={requested_difficulty}, generator={generator_difficulty}): {error_msg}"
                    )
                    # Ne pas ajouter à all_mismatches - c'est une erreur de difficulté, pas de template
                    continue
                else:
                    # Autre erreur - considérer comme mismatch
                    logger.warning(f"Erreur lors de la validation placeholder pour {generator_key} (ui={requested_difficulty}, generator={generator_difficulty}): {e}")
                    all_mismatches.append({
                        "difficulty": requested_difficulty,
                        "difficulty_used": generator_difficulty,
                        "missing": sorted(placeholders_expected),
                        "extra": [],
                        "error": str(e)
                    })
            except Exception as e:
                # Si la génération échoue pour une autre raison, on considère comme mismatch
                logger.warning(f"Erreur lors de la validation placeholder pour {generator_key} (ui={requested_difficulty}, generator={generator_difficulty}): {e}")
                all_mismatches.append({
                    "difficulty": requested_difficulty,
                    "difficulty_used": generator_difficulty,
                    "missing": sorted(placeholders_expected),
                    "extra": [],
                    "error": str(e)
                })
        
        # Si des mismatches sont détectés, lever une erreur
        if all_mismatches:
            # Construire le message d'erreur
            missing_summary = set()
            for mismatch in all_mismatches:
                missing_summary.update(mismatch["missing"])
            
            missing_list = ", ".join(sorted(missing_summary)[:5])
            if len(missing_summary) > 5:
                missing_list += f" et {len(missing_summary) - 5} autre(s)"
            
            hint = (
                f"Les placeholders suivants ne peuvent pas être résolus par le générateur '{generator_key}': {missing_list}. "
                f"Vérifiez que le générateur fournit toutes les variables nécessaires pour les templates. "
                f"Difficultés affectées: {', '.join([m['difficulty'] for m in all_mismatches])}."
            )
            
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "ADMIN_TEMPLATE_MISMATCH",
                    "error": "admin_template_mismatch",
                    "message": f"Les templates contiennent des placeholders qui ne peuvent pas être résolus par le générateur '{generator_key}'.",
                    "hint": hint,
                    "context": {
                        "generator_key": generator_key,
                        "mismatches": all_mismatches,
                        "missing_summary": sorted(missing_summary),
                        "placeholders_expected": sorted(placeholders_expected)
                    }
                }
            )
    
    async def _reload_handler(self, chapter_code: str) -> None:
        """Recharge le handler en mémoire après modification"""
        try:
            import importlib
            
            if chapter_code == "6E_GM07":
                import data.gm07_exercises as module
                importlib.reload(module)
            elif chapter_code == "6E_GM08":
                import data.gm08_exercises as module
                importlib.reload(module)
            
            logger.info(f"Handler {chapter_code} rechargé")
        except Exception as e:
            logger.error(f"Erreur rechargement handler {chapter_code}: {e}")


# =============================================================================
# SINGLETON
# =============================================================================

_exercise_persistence_service: Optional[ExercisePersistenceService] = None


def get_exercise_persistence_service(db: AsyncIOMotorDatabase) -> ExercisePersistenceService:
    """Factory pour obtenir le service de persistance des exercices"""
    global _exercise_persistence_service
    
    if _exercise_persistence_service is None:
        _exercise_persistence_service = ExercisePersistenceService(db)
    
    return _exercise_persistence_service
