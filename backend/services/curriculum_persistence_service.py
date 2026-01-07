"""
Service de persistance du curriculum en MongoDB.

Gère les opérations CRUD sur les chapitres du curriculum.
Maintient la synchronisation entre MongoDB et le fichier JSON local.
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Chemin vers le fichier JSON du curriculum
CURRICULUM_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "curriculum")
CURRICULUM_6E_PATH = os.path.join(CURRICULUM_DIR, "curriculum_6e.json")

# Collection MongoDB pour le curriculum
CURRICULUM_COLLECTION = "curriculum_chapters"


import re
from pydantic import field_validator
from typing import Literal as PyLiteral


def _is_truthy_dynamic(value) -> bool:
    """
    [P0_FIX] Helper robuste pour détecter is_dynamic.
    Gère bool, int, str ("true", "1", etc.)
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value == 1
    if isinstance(value, str):
        return value.lower().strip() in ("true", "1", "yes")
    return False


def normalize_code_officiel(code: str) -> str:
    """
    Normalise le code officiel au format canonique.
    Accepte 6E_N99 ou 6e_N99 et retourne 6e_N99.
    Le niveau (6e, 5e, 4e, 3e) est en minuscules, le reste en majuscules.
    """
    code = code.strip()
    if not code:
        return code
    
    # Pattern: niveau_reste (ex: 6e_N01, 5e_G02)
    match = re.match(r'^(\d+[eE])_(.+)$', code)
    if match:
        niveau = match.group(1).lower()  # 6e, 5e, etc. en minuscules
        reste = match.group(2).upper()    # N01, G02, etc. en majuscules
        return f"{niveau}_{reste}"
    
    return code  # Retourne tel quel si le format n'est pas reconnu


# P4.B - Modèles pour enabled_generators
class EnabledGeneratorConfig(BaseModel):
    """Configuration d'un générateur activé dans un chapitre"""
    generator_key: str = Field(..., description="Clé du générateur (ex: THALES_V2)")
    difficulty_presets: List[str] = Field(
        default_factory=lambda: ["facile", "moyen", "difficile"],
        description="Liste des difficultés activées pour ce générateur"
    )
    min_offer: str = Field(
        default="free",
        description="Offre minimum requise: 'free' ou 'pro'"
    )
    is_enabled: bool = Field(
        default=True,
        description="Si le générateur est activé dans ce chapitre"
    )


class ChapterCreateRequest(BaseModel):
    """Modèle pour la création d'un chapitre"""
    code_officiel: str = Field(..., description="Code officiel unique (ex: 6e_N01)")
    libelle: str = Field(..., description="Intitulé du chapitre")
    subject: str = Field(default="math", description="Matière (math, physics, chemistry, etc.)")
    domaine: str = Field(default="Nombres et calculs", description="Domaine mathématique")
    chapitre_backend: str = Field(default="", description="Nom du chapitre backend correspondant")
    exercise_types: List[str] = Field(default_factory=list, description="Types d'exercices associés")
    schema_requis: bool = Field(default=False, description="Si un schéma est requis")
    difficulte_min: int = Field(default=1, ge=1, le=3, description="Difficulté minimum")
    difficulte_max: int = Field(default=3, ge=1, le=3, description="Difficulté maximum")
    statut: str = Field(default="beta", description="Statut: prod, beta, hidden")
    tags: List[str] = Field(default_factory=list, description="Tags pour filtrage")
    contexts: List[str] = Field(default_factory=list, description="Contextes disponibles")
    pipeline: Optional[Literal["SPEC", "TEMPLATE", "MIXED"]] = Field(
        default="SPEC",
        description="Pipeline de génération: SPEC (statique), TEMPLATE (dynamique), MIXED (les deux)"
    )
    enabled_generators: List[EnabledGeneratorConfig] = Field(
        default_factory=list,
        description="Liste des générateurs activés dans ce chapitre (P4.B)"
    )
    
    @field_validator('code_officiel', mode='before')
    @classmethod
    def normalize_code(cls, v: str) -> str:
        """Normalise le code_officiel au format canonique"""
        return normalize_code_officiel(v)


class ChapterUpdateRequest(BaseModel):
    """Modèle pour la mise à jour d'un chapitre"""
    libelle: Optional[str] = None
    subject: Optional[str] = Field(default=None, description="Matière (math, physics, chemistry, etc.)")
    domaine: Optional[str] = None
    chapitre_backend: Optional[str] = None
    exercise_types: Optional[List[str]] = None
    schema_requis: Optional[bool] = None
    difficulte_min: Optional[int] = Field(default=None, ge=1, le=3)
    difficulte_max: Optional[int] = Field(default=None, ge=1, le=3)
    statut: Optional[str] = None
    tags: Optional[List[str]] = None
    contexts: Optional[List[str]] = None
    pipeline: Optional[Literal["SPEC", "TEMPLATE", "MIXED"]] = Field(
        default=None,
        description="Pipeline de génération: SPEC (statique), TEMPLATE (dynamique), MIXED (les deux)"
    )
    enabled_generators: Optional[List[EnabledGeneratorConfig]] = Field(
        default=None,
        description="Liste des générateurs activés dans ce chapitre (P4.B)"
    )


class CurriculumPersistenceService:
    """
    Service de persistance pour le curriculum.
    Gère la synchronisation MongoDB <-> fichier JSON.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[CURRICULUM_COLLECTION]
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialise la collection MongoDB avec les données du fichier JSON.
        Ne fait rien si déjà initialisé.
        """
        if self._initialized:
            return
        
        # Vérifier si la collection existe et a des données
        count = await self.collection.count_documents({"niveau": "6e"})
        
        if count == 0:
            # Charger depuis le fichier JSON
            logger.info("Initialisation de la collection curriculum depuis le fichier JSON")
            await self._load_from_json()
        
        # Créer les index
        await self.collection.create_index("code_officiel", unique=True)
        await self.collection.create_index("niveau")
        await self.collection.create_index("domaine")
        await self.collection.create_index("statut")
        # P4.2: Index pour la recherche par matière et niveau
        await self.collection.create_index([("subject", 1), ("niveau", 1), ("code_officiel", 1)])
        await self.collection.create_index("subject")
        
        self._initialized = True
        logger.info(f"Curriculum persistence service initialisé avec {count} chapitres")
    
    async def _load_from_json(self) -> None:
        """Charge les chapitres depuis le fichier JSON vers MongoDB"""
        if not os.path.exists(CURRICULUM_6E_PATH):
            logger.warning(f"Fichier curriculum non trouvé: {CURRICULUM_6E_PATH}")
            return
        
        with open(CURRICULUM_6E_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        chapters = data.get("chapitres", [])
        
        if chapters:
            # Ajouter des métadonnées
            for chapter in chapters:
                chapter["created_at"] = datetime.now(timezone.utc)
                chapter["updated_at"] = datetime.now(timezone.utc)
            
            await self.collection.insert_many(chapters)
            logger.info(f"Chargé {len(chapters)} chapitres depuis le fichier JSON")
    
    async def _sync_to_json(self) -> None:
        """
        Synchronise les données MongoDB vers le fichier JSON.
        Maintient la compatibilité avec le système existant.
        """
        chapters = await self.collection.find(
            {"niveau": "6e"},
            {"_id": 0, "created_at": 0, "updated_at": 0}
        ).to_list(1000)
        
        # Trier par code_officiel
        chapters.sort(key=lambda x: x.get("code_officiel", ""))
        
        data = {
            "version": 1,
            "niveau": "6e",
            "description": "Référentiel pédagogique officiel 6e basé sur le programme de mathématiques",
            "chapitres": chapters
        }
        
        with open(CURRICULUM_6E_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Fichier JSON synchronisé avec {len(chapters)} chapitres")
    
    async def get_all_chapters(self, niveau: str = "6e") -> List[Dict[str, Any]]:
        """Récupère tous les chapitres d'un niveau"""
        await self.initialize()
        
        chapters = await self.collection.find(
            {"niveau": niveau},
            {"_id": 0}
        ).sort("code_officiel", 1).to_list(1000)
        
        return chapters
    
    async def get_chapter_by_code(self, code_officiel: str) -> Optional[Dict[str, Any]]:
        """Récupère un chapitre par son code officiel"""
        await self.initialize()

        # P0_FIX : Lookup case-insensitive avec regex
        # Échapper les caractères spéciaux regex dans le code
        escaped_code = re.escape(code_officiel)

        logger.info(
            f"[P0_FIX] get_chapter_by_code() appelé avec code_officiel='{code_officiel}' "
            f"(regex: ^{escaped_code}$, options: i)"
        )

        # P0_FIX : Recherche case-insensitive
        chapter = await self.collection.find_one(
            {"code_officiel": {"$regex": f"^{escaped_code}$", "$options": "i"}},
            {"_id": 0}
        )

        if chapter:
            # P0_FIX : Defaults pour chapitres incomplets
            if "enabled_generators" not in chapter or chapter.get("enabled_generators") is None:
                chapter["enabled_generators"] = []
                logger.info(
                    f"[P0_FIX] enabled_generators absent pour '{code_officiel}', défaut=[]"
                )

            # Log du pipeline pour diagnostic
            pipeline_value = chapter.get('pipeline')
            logger.info(
                f"[P0_FIX] ✅ Chapitre trouvé: code_officiel='{chapter.get('code_officiel')}', "
                f"pipeline='{pipeline_value}' (type: {type(pipeline_value).__name__}), "
                f"enabled_generators_count={len(chapter.get('enabled_generators', []))}"
            )
        else:
            logger.warning(
                f"[P0_FIX] ❌ Chapitre NON TROUVÉ avec code_officiel='{code_officiel}' "
                f"(regex case-insensitive). Vérifier que le code existe en DB."
            )

        return chapter
    
    async def create_chapter(self, request: ChapterCreateRequest) -> Dict[str, Any]:
        """
        Crée un nouveau chapitre.
        
        Args:
            request: Données du nouveau chapitre
            
        Returns:
            Le chapitre créé
            
        Raises:
            ValueError: Si le code_officiel existe déjà ou validation échoue
        """
        await self.initialize()
        
        # Vérifier l'unicité du code
        existing = await self.collection.find_one({"code_officiel": request.code_officiel})
        if existing:
            raise ValueError(f"Le code officiel '{request.code_officiel}' existe déjà")
        
        # P0: Validations BLOQUANTES
        pipeline_mode = request.pipeline or "SPEC"
        
        # Validation 1: TEMPLATE sans exercice dynamique → ERREUR
        if pipeline_mode == "TEMPLATE":
            from backend.services.curriculum_sync_service import get_curriculum_sync_service
            sync_service = get_curriculum_sync_service(self.db)
            chapter_code_upper = request.code_officiel.upper().replace("-", "_")
            
            has_exercises = await sync_service.has_exercises_in_db(chapter_code_upper)
            if not has_exercises:
                raise ValueError(
                    f"Le chapitre '{request.code_officiel}' est configuré avec pipeline='TEMPLATE' "
                    f"mais aucun exercice dynamique n'existe en DB pour ce chapitre. "
                    f"Créez au moins un exercice dynamique ou changez le pipeline à 'SPEC' ou 'MIXED'."
                )
            
            # Vérifier qu'il y a au moins un exercice dynamique
            from backend.services.exercise_persistence_service import get_exercise_persistence_service
            exercise_service = get_exercise_persistence_service(self.db)
            exercises = await exercise_service.get_exercises(chapter_code=chapter_code_upper)
            # P0_FIX : Utiliser helper robuste
            dynamic_exercises = [ex for ex in exercises if _is_truthy_dynamic(ex.get("is_dynamic"))]
            
            if len(dynamic_exercises) == 0:
                raise ValueError(
                    f"Le chapitre '{request.code_officiel}' est configuré avec pipeline='TEMPLATE' "
                    f"mais aucun exercice dynamique (is_dynamic=true) n'existe en DB. "
                    f"Créez au moins un exercice dynamique ou changez le pipeline à 'SPEC' ou 'MIXED'."
                )
        
        # Validation 2: SPEC avec exercise_types invalides → ERREUR
        # Permet à la fois les MathExerciseType (statiques) et les generator_keys (dynamiques)
        if pipeline_mode == "SPEC" and request.exercise_types:
            from backend.models.math_models import MathExerciseType
            from backend.generators.factory import GeneratorFactory
            
            invalid_types = []
            for et in request.exercise_types:
                # Vérifier si c'est un MathExerciseType (statique)
                is_math_type = hasattr(MathExerciseType, et)
                # Vérifier si c'est un generator_key (dynamique)
                is_generator = GeneratorFactory.get(et) is not None
                
                if not is_math_type and not is_generator:
                    invalid_types.append(et)
            
            if len(invalid_types) == len(request.exercise_types) and len(invalid_types) > 0:
                # Tous les types sont invalides
                raise ValueError(
                    f"Le chapitre '{request.code_officiel}' est configuré avec pipeline='SPEC' "
                    f"mais tous les exercise_types configurés ne correspondent à aucun "
                    f"MathExerciseType connu ni à aucun générateur dynamique: {invalid_types}. "
                    f"Ajoutez ces types dans MathExerciseType ou enregistrez ces générateurs dans GeneratorFactory, "
                    f"corrigez le référentiel, ou changez le pipeline à 'TEMPLATE' ou 'MIXED'."
                )
        
        # Construire le document
        chapter = {
            "niveau": "6e",  # Hardcodé pour l'instant (V2 = 6e uniquement)
            **request.model_dump(),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await self.collection.insert_one(chapter)
        
        # Synchroniser avec le fichier JSON
        await self._sync_to_json()
        
        # Recharger le curriculum en mémoire
        await self._reload_curriculum_index()
        
        logger.info(f"Chapitre créé: {request.code_officiel}")
        
        # Retourner sans _id
        del chapter["_id"]
        return chapter
    
    async def update_chapter(self, code_officiel: str, request: ChapterUpdateRequest) -> Dict[str, Any]:
        """
        Met à jour un chapitre existant.
        
        Args:
            code_officiel: Code du chapitre à modifier
            request: Données à mettre à jour (seuls les champs non-None sont mis à jour)
            
        Returns:
            Le chapitre mis à jour
            
        Raises:
            ValueError: Si le chapitre n'existe pas
        """
        await self.initialize()
        
        # Vérifier l'existence
        existing = await self.collection.find_one({"code_officiel": code_officiel})
        if not existing:
            raise ValueError(f"Le code officiel '{code_officiel}' n'existe pas")
        
        # Construire les champs à mettre à jour
        update_data = request.model_dump(exclude_none=True)
        
        if not update_data:
            # Rien à mettre à jour
            del existing["_id"]
            return existing
        
        # P0: Validations BLOQUANTES
        # Déterminer le pipeline (nouveau ou existant)
        pipeline_mode = update_data.get("pipeline") or existing.get("pipeline") or "SPEC"
        
        # Déterminer les exercise_types (nouveaux ou existants)
        exercise_types = update_data.get("exercise_types") or existing.get("exercise_types", [])
        
        # Validation 1: TEMPLATE sans exercice dynamique → ERREUR
        if pipeline_mode == "TEMPLATE":
            from backend.services.curriculum_sync_service import get_curriculum_sync_service
            sync_service = get_curriculum_sync_service(self.db)
            chapter_code_upper = code_officiel.upper().replace("-", "_")
            
            has_exercises = await sync_service.has_exercises_in_db(chapter_code_upper)
            if not has_exercises:
                raise ValueError(
                    f"Le chapitre '{code_officiel}' est configuré avec pipeline='TEMPLATE' "
                    f"mais aucun exercice dynamique n'existe en DB pour ce chapitre. "
                    f"Créez au moins un exercice dynamique ou changez le pipeline à 'SPEC' ou 'MIXED'."
                )
            
            # Vérifier qu'il y a au moins un exercice dynamique
            from backend.services.exercise_persistence_service import get_exercise_persistence_service
            exercise_service = get_exercise_persistence_service(self.db)
            exercises = await exercise_service.get_exercises(chapter_code=chapter_code_upper)
            # P0_FIX : Utiliser helper robuste
            dynamic_exercises = [ex for ex in exercises if _is_truthy_dynamic(ex.get("is_dynamic"))]
            
            if len(dynamic_exercises) == 0:
                raise ValueError(
                    f"Le chapitre '{code_officiel}' est configuré avec pipeline='TEMPLATE' "
                    f"mais aucun exercice dynamique (is_dynamic=true) n'existe en DB. "
                    f"Créez au moins un exercice dynamique ou changez le pipeline à 'SPEC' ou 'MIXED'."
                )
        
        # Validation 2: SPEC avec exercise_types invalides → ERREUR
        # Permet à la fois les MathExerciseType (statiques) et les generator_keys (dynamiques)
        if pipeline_mode == "SPEC" and exercise_types:
            from backend.models.math_models import MathExerciseType
            from backend.generators.factory import GeneratorFactory
            
            invalid_types = []
            for et in exercise_types:
                # Vérifier si c'est un MathExerciseType (statique)
                is_math_type = hasattr(MathExerciseType, et)
                # Vérifier si c'est un generator_key (dynamique)
                is_generator = GeneratorFactory.get(et) is not None
                
                if not is_math_type and not is_generator:
                    invalid_types.append(et)
            
            if len(invalid_types) == len(exercise_types) and len(invalid_types) > 0:
                # Tous les types sont invalides
                raise ValueError(
                    f"Le chapitre '{code_officiel}' est configuré avec pipeline='SPEC' "
                    f"mais tous les exercise_types configurés ne correspondent à aucun "
                    f"MathExerciseType connu ni à aucun générateur dynamique: {invalid_types}. "
                    f"Ajoutez ces types dans MathExerciseType ou enregistrez ces générateurs dans GeneratorFactory, "
                    f"corrigez le référentiel, ou changez le pipeline à 'TEMPLATE' ou 'MIXED'."
                )
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        await self.collection.update_one(
            {"code_officiel": code_officiel},
            {"$set": update_data}
        )
        
        # Synchroniser avec le fichier JSON
        await self._sync_to_json()
        
        # Recharger le curriculum en mémoire
        await self._reload_curriculum_index()
        
        logger.info(f"Chapitre mis à jour: {code_officiel}")
        
        # Récupérer le chapitre mis à jour
        updated = await self.collection.find_one(
            {"code_officiel": code_officiel},
            {"_id": 0}
        )
        
        return updated
    
    async def delete_chapter(self, code_officiel: str) -> bool:
        """
        Supprime un chapitre.
        
        Args:
            code_officiel: Code du chapitre à supprimer
            
        Returns:
            True si supprimé, False sinon
            
        Raises:
            ValueError: Si le chapitre n'existe pas
        """
        await self.initialize()
        
        # Vérifier l'existence
        existing = await self.collection.find_one({"code_officiel": code_officiel})
        if not existing:
            raise ValueError(f"Le code officiel '{code_officiel}' n'existe pas")
        
        result = await self.collection.delete_one({"code_officiel": code_officiel})
        
        if result.deleted_count > 0:
            # Synchroniser avec le fichier JSON
            await self._sync_to_json()
            
            # Recharger le curriculum en mémoire
            await self._reload_curriculum_index()
            
            logger.info(f"Chapitre supprimé: {code_officiel}")
            return True
        
        return False
    
    async def _reload_curriculum_index(self) -> None:
        """
        Recharge l'index du curriculum en mémoire.
        Nécessaire après chaque modification pour que les changements soient pris en compte.
        """
        try:
            from backend.curriculum.loader import load_curriculum_6e, _curriculum_index
            import curriculum.loader as loader_module
            
            # Réinitialiser le singleton
            loader_module._curriculum_index = None
            
            # Recharger
            load_curriculum_6e()
            
            logger.info("Index curriculum rechargé en mémoire")
        except Exception as e:
            logger.error(f"Erreur lors du rechargement de l'index: {e}")
    
    async def get_available_generators(self) -> List[str]:
        """
        Récupère la liste de tous les générateurs disponibles.
        
        **Source de vérité enrichie** :
        - Générateurs statiques : MathExerciseType (source principale)
        - Générateurs dynamiques : exercise_types extraits depuis GeneratorFactory
          via le mapping GENERATOR_TO_EXERCISE_TYPE (utilise les exercise_types du curriculum,
          pas ceux des métadonnées)
        
        Utile pour le formulaire d'édition dans l'admin.
        """
        generators = set()
        
        # 1. Générateurs statiques (MathExerciseType)
        try:
            from models.math_models import MathExerciseType
            for e in MathExerciseType:
                generators.add(e.name)
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des générateurs statiques: {e}")
        
        # 2. Générateurs dynamiques (GeneratorFactory) - source unique via meta.exercise_type
        try:
            from backend.generators.factory import GeneratorFactory
            
            # Récupérer tous les générateurs Factory
            factory_generators = GeneratorFactory.list_all()
            
            for gen_info in factory_generators:
                generator_key = gen_info.get("key")
                if generator_key:
                    exercise_type = gen_info.get("exercise_type")
                    if exercise_type:
                        generators.add(exercise_type)
                        logger.debug(
                            f"[AVAILABLE_GENERATORS] Générateur dynamique {generator_key} → "
                            f"exercise_type: {exercise_type}"
                        )
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des générateurs dynamiques: {e}")
        
        # Retourner la liste triée
        return sorted(list(generators))
    
    async def get_available_domaines(self) -> List[str]:
        """
        Récupère la liste des domaines uniques depuis la base.
        """
        await self.initialize()
        
        domaines = await self.collection.distinct("domaine")
        return sorted(domaines)
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur le curriculum.
        """
        await self.initialize()
        
        total = await self.collection.count_documents({"niveau": "6e"})
        by_status = {}
        by_domaine = {}
        
        # Agrégation par statut
        status_agg = await self.collection.aggregate([
            {"$match": {"niveau": "6e"}},
            {"$group": {"_id": "$statut", "count": {"$sum": 1}}}
        ]).to_list(100)
        
        for item in status_agg:
            by_status[item["_id"]] = item["count"]
        
        # Agrégation par domaine
        domaine_agg = await self.collection.aggregate([
            {"$match": {"niveau": "6e"}},
            {"$group": {"_id": "$domaine", "count": {"$sum": 1}}}
        ]).to_list(100)
        
        for item in domaine_agg:
            by_domaine[item["_id"]] = item["count"]
        
        return {
            "total": total,
            "by_status": by_status,
            "by_domaine": by_domaine
        }


# Singleton pour le service (sera initialisé avec la DB)
_curriculum_persistence_service: Optional[CurriculumPersistenceService] = None


def get_curriculum_persistence_service(db: AsyncIOMotorDatabase) -> CurriculumPersistenceService:
    """
    Factory pour obtenir le service de persistance.
    Crée une instance unique par base de données.
    """
    global _curriculum_persistence_service
    
    if _curriculum_persistence_service is None:
        _curriculum_persistence_service = CurriculumPersistenceService(db)
    
    return _curriculum_persistence_service
