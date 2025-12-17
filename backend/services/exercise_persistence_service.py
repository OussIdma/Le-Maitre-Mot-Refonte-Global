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
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# Collection MongoDB pour les exercices
EXERCISES_COLLECTION = "admin_exercises"

# Chemin vers le dossier data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


# =============================================================================
# MODÈLES PYDANTIC
# =============================================================================

class ExerciseCreateRequest(BaseModel):
    """Modèle pour la création d'un exercice"""
    family: str = Field(..., description="Famille: CONVERSION, COMPARAISON, PERIMETRE, PROBLEME, DUREES, etc.")
    exercise_type: Optional[str] = Field(None, description="Type d'exercice (optionnel): LECTURE_HEURE, PLACER_AIGUILLES, etc.")
    difficulty: str = Field(..., description="Difficulté: facile, moyen, difficile")
    offer: str = Field(default="free", description="Offre: free ou pro")
    # Flag dynamique EN PREMIER pour que les validateurs puissent le lire
    is_dynamic: bool = Field(default=False, description="Exercice dynamique (template)")
    # Exercices statiques
    enonce_html: Optional[str] = Field(default="", description="Énoncé en HTML pur (requis si non dynamique)")
    solution_html: Optional[str] = Field(default="", description="Solution en HTML pur (requis si non dynamique)")
    needs_svg: bool = Field(default=False, description="Nécessite un SVG")
    variables: Optional[Dict[str, Any]] = Field(None, description="Variables pour le SVG (ex: {hour: 8, minute: 0})")
    svg_enonce_brief: Optional[str] = Field(None, description="Description du SVG pour l'énoncé")
    svg_solution_brief: Optional[str] = Field(None, description="Description du SVG pour la solution")
    # Exercices dynamiques
    generator_key: Optional[str] = Field(None, description="Clé du générateur (ex: THALES_V1)")
    enonce_template_html: Optional[str] = Field(None, description="Template énoncé avec {{variables}}")
    solution_template_html: Optional[str] = Field(None, description="Template solution avec {{variables}}")
    variables_schema: Optional[Dict[str, str]] = Field(None, description="Schéma des variables")
    
    @validator('enonce_html', always=True)
    def validate_enonce(cls, v, values):
        is_dynamic = values.get('is_dynamic', False)
        if not is_dynamic and not v:
            raise ValueError('enonce_html est requis pour les exercices statiques')
        return v or ''
    
    @validator('solution_html', always=True)
    def validate_solution(cls, v, values):
        is_dynamic = values.get('is_dynamic', False)
        if not is_dynamic and not v:
            raise ValueError('solution_html est requis pour les exercices statiques')
        return v or ''
    
    @validator('generator_key', always=True)
    def validate_generator(cls, v, values):
        is_dynamic = values.get('is_dynamic', False)
        if is_dynamic and not v:
            raise ValueError('generator_key est requis pour les exercices dynamiques')
        return v


class ExerciseUpdateRequest(BaseModel):
    """Modèle pour la mise à jour d'un exercice"""
    family: Optional[str] = None
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


class ExerciseResponse(BaseModel):
    """Réponse pour un exercice"""
    id: int
    chapter_code: str
    family: str
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
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[EXERCISES_COLLECTION]
        self._initialized = {}
    
    async def initialize_chapter(self, chapter_code: str) -> None:
        """
        Initialise la collection pour un chapitre si nécessaire.
        Charge les exercices depuis le fichier Python existant.
        """
        chapter_upper = chapter_code.upper().replace("-", "_")
        
        if chapter_upper in self._initialized:
            return
        
        # Compter les exercices existants pour ce chapitre
        count = await self.collection.count_documents({"chapter_code": chapter_upper})
        
        if count == 0:
            # Charger depuis le fichier Python existant
            await self._load_from_python_file(chapter_upper)
        
        # Créer les index
        await self.collection.create_index([("chapter_code", 1), ("id", 1)], unique=True)
        await self.collection.create_index("chapter_code")
        await self.collection.create_index("difficulty")
        await self.collection.create_index("offer")
        
        self._initialized[chapter_upper] = True
        logger.info(f"Exercices service initialisé pour {chapter_upper} avec {count} exercices")
    
    async def _load_from_python_file(self, chapter_code: str) -> None:
        """Charge les exercices depuis le fichier Python existant"""
        # Déterminer le fichier source
        file_mapping = {
            "6E_GM07": "gm07_exercises.py",
            "6E_GM08": "gm08_exercises.py",
            "6E_TESTS_DYN": "tests_dyn_exercises.py",
        }
        
        filename = file_mapping.get(chapter_code)
        if not filename:
            logger.warning(f"Pas de fichier source pour {chapter_code}")
            return
        
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            logger.warning(f"Fichier non trouvé: {filepath}")
            return
        
        # Importer dynamiquement le module
        try:
            if chapter_code == "6E_GM07":
                from data.gm07_exercises import GM07_EXERCISES as exercises
            elif chapter_code == "6E_GM08":
                from data.gm08_exercises import GM08_EXERCISES as exercises
            elif chapter_code == "6E_TESTS_DYN":
                from data.tests_dyn_exercises import TESTS_DYN_EXERCISES as exercises
            else:
                logger.warning(f"Import non supporté pour {chapter_code}")
                return
            
            # Insérer les exercices
            docs = []
            for ex in exercises:
                doc = {
                    "chapter_code": chapter_code,
                    "id": ex["id"],
                    "family": ex["family"],
                    "difficulty": ex["difficulty"],
                    "offer": ex["offer"],
                    "enonce_html": ex.get("enonce_html", ""),
                    "solution_html": ex.get("solution_html", ""),
                    "needs_svg": ex.get("needs_svg", False),
                    "variables": ex.get("variables"),
                    "exercise_type": ex.get("exercise_type"),
                    "svg_enonce_brief": ex.get("svg_enonce_brief"),
                    "svg_solution_brief": ex.get("svg_solution_brief"),
                    # Champs dynamiques
                    "is_dynamic": ex.get("is_dynamic", False),
                    "generator_key": ex.get("generator_key"),
                    "enonce_template_html": ex.get("enonce_template_html"),
                    "solution_template_html": ex.get("solution_template_html"),
                    "variables_schema": ex.get("variables_schema"),
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
                docs.append(doc)
            
            if docs:
                await self.collection.insert_many(docs)
                logger.info(f"Chargé {len(docs)} exercices pour {chapter_code}")
        
        except Exception as e:
            logger.error(f"Erreur chargement exercices {chapter_code}: {e}")
    
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
        
        family = ex["family"]
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
        chapter_upper = chapter_code.upper().replace("-", "_")
        await self.initialize_chapter(chapter_upper)
        
        query = {"chapter_code": chapter_upper}
        
        if offer:
            query["offer"] = offer.lower()
        if difficulty:
            query["difficulty"] = difficulty.lower()
        
        exercises = await self.collection.find(
            query,
            {"_id": 0}
        ).sort("id", 1).to_list(100)
        
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
        
        # Trouver le prochain ID
        max_doc = await self.collection.find_one(
            {"chapter_code": chapter_upper},
            sort=[("id", -1)]
        )
        next_id = (max_doc["id"] + 1) if max_doc else 1
        
        # Créer le document
        doc = {
            "chapter_code": chapter_upper,
            "id": next_id,
            "family": request.family.upper(),
            "exercise_type": request.exercise_type.upper() if request.exercise_type else None,
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
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await self.collection.insert_one(doc)
        
        # Synchroniser avec le fichier Python (seulement pour GM07/GM08)
        if chapter_upper in ["6E_GM07", "6E_GM08"]:
            await self._sync_to_python_file(chapter_upper)
            await self._reload_handler(chapter_upper)
        
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
            update_data["family"] = request.family.upper()
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
        
        if not update_data:
            del existing["_id"]
            return existing
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await self.collection.update_one(
            {"chapter_code": chapter_upper, "id": exercise_id},
            {"$set": update_data}
        )
        
        # Synchroniser avec le fichier Python
        await self._sync_to_python_file(chapter_upper)
        
        # Recharger le handler
        await self._reload_handler(chapter_upper)
        
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
            
            logger.info(f"Exercice supprimé: {chapter_upper} #{exercise_id}")
            return True
        
        return False
    
    async def get_stats(self, chapter_code: str) -> Dict[str, Any]:
        """Statistiques sur les exercices d'un chapitre"""
        chapter_upper = chapter_code.upper().replace("-", "_")
        await self.initialize_chapter(chapter_upper)
        
        total = await self.collection.count_documents({"chapter_code": chapter_upper})
        
        # Agrégations
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
        
        return {
            "chapter_code": chapter_upper,
            "total": total,
            "by_offer": by_offer,
            "by_difficulty": by_difficulty,
            "by_family": by_family
        }
    
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
            # Exercice dynamique - vérifier les templates
            if not request.generator_key:
                raise ValueError("generator_key est requis pour les exercices dynamiques")
            
            if not request.enonce_template_html or not request.enonce_template_html.strip():
                raise ValueError("Le template énoncé ne peut pas être vide pour un exercice dynamique")
            
            if not request.solution_template_html or not request.solution_template_html.strip():
                raise ValueError("Le template solution ne peut pas être vide pour un exercice dynamique")
        else:
            # Exercice statique - vérifier le HTML
            if not request.enonce_html or not request.enonce_html.strip():
                raise ValueError("L'énoncé ne peut pas être vide")
            
            if not request.solution_html or not request.solution_html.strip():
                raise ValueError("La solution ne peut pas être vide")
            
            # Vérifier pas de LaTeX
            if "$" in request.enonce_html or "$" in request.solution_html:
                raise ValueError("Le contenu ne doit pas contenir de LaTeX ($). Utilisez du HTML pur.")
    
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
