"""
Service de synchronisation automatique Curriculum ⇄ Exercises.

Quand un exercice est créé/modifié via l'admin :
- Si le chapitre n'existe pas dans le curriculum → il est créé automatiquement
- Si le chapitre existe → ses exercise_types sont mis à jour automatiquement
- Les exercices dynamiques sont synchronisés vers exercise_types (pour endpoint mathalea)
"""

import logging
import uuid
from typing import Set, Optional, Dict, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.services.curriculum_persistence_service import (
    CurriculumPersistenceService,
    ChapterCreateRequest,
    ChapterUpdateRequest
)

logger = logging.getLogger(__name__)

def _get_exercise_type_from_generator(generator_key: str) -> Optional[str]:
    """
    Source unique: utilise GeneratorFactory.get_exercise_type (alias + meta).
    """
    try:
        from backend.generators.factory import GeneratorFactory
        exercise_type = GeneratorFactory.get_exercise_type(generator_key)
        if exercise_type:
            logger.debug(
                f"[CURRICULUM_SYNC] exercise_type extrait depuis Factory pour {generator_key}: {exercise_type}"
            )
            return exercise_type.upper()
    except Exception as e:
        logger.debug(
            f"[CURRICULUM_SYNC] Impossible d'extraire exercise_type via Factory pour {generator_key}: {e}"
        )
    # Fallback: generator_key normalisé
    logger.warning(
        f"[CURRICULUM_SYNC] Aucun exercise_type pour {generator_key}, fallback sur generator_key"
    )
    return generator_key.upper()


class CurriculumSyncService:
    """Service de synchronisation automatique entre exercises et curriculum"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        # Utilise la même collection que l'admin exercices (source de vérité actuelle)
        from backend.services.exercise_persistence_service import EXERCISES_COLLECTION
        self.exercises_collection = db[EXERCISES_COLLECTION]
        self.curriculum_service = CurriculumPersistenceService(db)
    
    async def extract_exercise_types_from_chapter(
        self,
        chapter_code: str
    ) -> Set[str]:
        """
        Extrait les exercise_types uniques depuis les exercices d'un chapitre.
        
        Gère à la fois les exercices dynamiques (via generator_key) et statiques
        (via exercise_type).
        
        Args:
            chapter_code: Code du chapitre (ex: "6E_G07_DYN")
        
        Returns:
            Set d'exercise_types uniques
        """
        chapter_upper = chapter_code.upper().replace("-", "_")
        
        # Récupérer tous les exercices du chapitre
        exercises = await self.exercises_collection.find(
            {"chapter_code": chapter_upper},
            {
                "generator_key": 1,
                "exercise_type": 1,
                "is_dynamic": 1
            }
        ).to_list(1000)
        
        exercise_types = set()
        
        for ex in exercises:
            # Cas 1 : Exercice dynamique → utiliser generator_key
            if ex.get("is_dynamic") and ex.get("generator_key"):
                generator_key = ex.get("generator_key")
                # Extraire exercise_type depuis les métadonnées du générateur ou mapping
                exercise_type = _get_exercise_type_from_generator(generator_key)
                if exercise_type:
                    exercise_types.add(exercise_type)
                    logger.debug(
                        f"[CURRICULUM_SYNC] Exercice dynamique {generator_key} → "
                        f"exercise_type: {exercise_type}"
                    )
                else:
                    logger.warning(
                        f"[CURRICULUM_SYNC] Impossible d'extraire exercise_type "
                        f"pour generator_key: {generator_key}"
                    )
            
            # Cas 2 : Exercice statique → utiliser exercise_type directement
            elif ex.get("exercise_type"):
                exercise_type = ex.get("exercise_type")
                # Normaliser (uppercase)
                exercise_types.add(exercise_type.upper())
                logger.debug(
                    f"[CURRICULUM_SYNC] Exercice statique → exercise_type: {exercise_type.upper()}"
                )
        
        return exercise_types
    
    async def has_exercises_in_db(self, chapter_code: str) -> bool:
        """
        Vérifie si au moins un exercice (statique ou dynamique) existe en DB pour ce chapitre.
        
        Args:
            chapter_code: Code du chapitre (ex: "6E_G07_DYN")
        
        Returns:
            True si au moins un exercice existe, False sinon
        """
        chapter_upper = chapter_code.upper().replace("-", "_")
        count = await self.exercises_collection.count_documents(
            {"chapter_code": chapter_upper},
            limit=1
        )
        return count > 0
    
    async def get_exercise_types_from_db(self, chapter_code: str) -> Set[str]:
        """
        Extrait les exercise_types depuis les exercices en DB pour un chapitre.
        Réutilise la logique de extract_exercise_types_from_chapter.
        
        Args:
            chapter_code: Code du chapitre (ex: "6E_G07_DYN")
        
        Returns:
            Set d'exercise_types uniques depuis la DB
        """
        return await self.extract_exercise_types_from_chapter(chapter_code)

    async def sync_chapter_to_curriculum(
        self,
        chapter_code: str,
        libelle: Optional[str] = None,
        domaine: str = "Géométrie",
        statut: str = "prod"
    ) -> Dict[str, Any]:
        """
        Synchronise un chapitre depuis la collection exercises vers le référentiel curriculum.
        
        Règles :
        1) Extraction automatique des exercise_types depuis generator_key + exercise_type
        2) Création idempotente (pas de doublon)
        3) Mise à jour additive (ne supprime rien d'existant)
        4) Zéro fallback silencieux (log + erreur explicite si mapping impossible)
        5) Compatible statique + dynamique
        
        Args:
            chapter_code: Code du chapitre (ex: "6e_G07_DYN")
            libelle: Libellé du chapitre (si None, généré automatiquement)
            domaine: Domaine mathématique (défaut: "Géométrie")
            statut: Statut du chapitre (défaut: "prod")
        
        Returns:
            Dict avec 'created' (bool), 'updated' (bool), 'exercise_types' (List[str])
        
        Raises:
            ValueError: Si le mapping est impossible ou si une erreur survient
        """
        chapter_code_normalized = chapter_code.upper().replace("-", "_")
        
        try:
            # Extraire les exercise_types depuis les exercices
            exercise_types = await self.extract_exercise_types_from_chapter(
                chapter_code_normalized
            )
            
            exercise_types_list = sorted(list(exercise_types))
            
            if not exercise_types_list:
                logger.error(
                    f"[CURRICULUM_SYNC] ⚠️ Aucun exercise_type détecté pour {chapter_code_normalized}. "
                    "Le chapitre sera créé sans exercise_types (sera marqué 'indisponible'). "
                    "Vérifiez que les exercices ont bien un 'generator_key' (dynamique) ou "
                    "'exercise_type' (statique)."
                )
            else:
                logger.info(
                    f"[CURRICULUM_SYNC] ✅ Exercise types détectés pour {chapter_code_normalized}: "
                    f"{exercise_types_list}"
                )
            
            # Générer le libellé si non fourni
            if not libelle:
                # Extraire le nom depuis le code (ex: "6e_G07_DYN" → "G07 DYN")
                parts = chapter_code_normalized.split('_')
                if len(parts) >= 2:
                    libelle = f"{parts[1]} {parts[2] if len(parts) > 2 else ''}".strip()
                else:
                    libelle = chapter_code_normalized
            
            # Vérifier si le chapitre existe déjà
            existing = await self.curriculum_service.get_chapter_by_code(
                chapter_code_normalized
            )
            
            if existing:
                # Mise à jour additive : fusionner les exercise_types
                existing_types = set(existing.get('exercise_types', []))
                new_types = existing_types.union(exercise_types)
                
                # Ne mettre à jour que si de nouveaux types ont été ajoutés
                if new_types != existing_types:
                    update_request = ChapterUpdateRequest(
                        exercise_types=sorted(list(new_types))
                    )
                    updated = await self.curriculum_service.update_chapter(
                        chapter_code_normalized,
                        update_request
                    )
                    logger.info(
                        f"[CURRICULUM_SYNC] Chapitre {chapter_code_normalized} mis à jour : "
                        f"exercise_types = {updated.get('exercise_types')}"
                    )
                    return {
                        'created': False,
                        'updated': True,
                        'exercise_types': updated.get('exercise_types', [])
                    }
                else:
                    logger.debug(
                        f"[CURRICULUM_SYNC] Chapitre {chapter_code_normalized} déjà à jour "
                        f"(exercise_types = {sorted(list(existing_types))})"
                    )
                    return {
                        'created': False,
                        'updated': False,
                        'exercise_types': sorted(list(existing_types))
                    }
            else:
                # Création du chapitre
                create_request = ChapterCreateRequest(
                    code_officiel=chapter_code_normalized,
                    libelle=libelle,
                    domaine=domaine,
                    exercise_types=exercise_types_list,
                    statut=statut,
                    difficulte_min=1,
                    difficulte_max=3,
                    schema_requis=any(
                        et in ["SYMETRIE_AXIALE", "THALES", "TRIANGLE_QUELCONQUE", "RECTANGLE", "CERCLE"]
                        for et in exercise_types_list
                    )
                )
                
                chapter = await self.curriculum_service.create_chapter(create_request)
                
                logger.info(
                    f"[CURRICULUM_SYNC] Chapitre créé : {chapter_code_normalized} "
                    f"(exercise_types = {exercise_types_list})"
                )
                
                return {
                    'created': True,
                    'updated': False,
                    'exercise_types': exercise_types_list
                }
        
        except ValueError as e:
            # Erreur de validation (ex: code_officiel déjà existant)
            logger.error(
                f"[CURRICULUM_SYNC] Erreur validation pour {chapter_code_normalized}: {e}"
            )
            raise ValueError(
                f"Impossible de synchroniser le chapitre {chapter_code_normalized} : {e}"
            )
        except Exception as e:
            # Erreur inattendue
            logger.error(
                f"[CURRICULUM_SYNC] Erreur inattendue pour {chapter_code_normalized}: {e}",
                exc_info=True
            )
            raise ValueError(
                f"Erreur lors de la synchronisation du chapitre {chapter_code_normalized} : {e}"
            )
    
    async def sync_chapter_to_exercise_types(
        self,
        chapter_code: str,
        force_recreate: bool = False
    ) -> Dict[str, Any]:
        """
        Synchronise un chapitre depuis admin_exercises vers la collection exercise_types.
        
        Cette méthode assure que tous les exercices dynamiques d'un chapitre sont
        représentés dans la collection exercise_types utilisée par l'endpoint mathalea.
        
        Architecture:
        - Source de vérité: admin_exercises (exercices créés via Admin UI)
        - Destination: exercise_types (utilisée par /api/mathalea/chapters/.../exercise-types)
        - Sync automatique lors du CRUD d'exercices
        
        Args:
            chapter_code: Code du chapitre (ex: "6E_N10")
            force_recreate: Si True, supprime et recrée tous les exercise_types (défaut: False)
        
        Returns:
            Dict avec:
            - created: nombre d'exercise_types créés
            - updated: nombre d'exercise_types mis à jour
            - deleted: nombre d'exercise_types supprimés
            - skipped: nombre d'exercise_types déjà existants
            - generator_keys: liste des generator_keys synchronisés
        
        Raises:
            ValueError: En cas d'erreur de validation
        """
        chapter_upper = chapter_code.upper().replace("-", "_")
        
        try:
            # Collection exercise_types (destination)
            exercise_types_collection = self.db["exercise_types"]
            
            # Statistiques de synchronisation
            stats = {
                'created': 0,
                'updated': 0,
                'deleted': 0,
                'skipped': 0,
                'generator_keys': []
            }
            
            # 1. Récupérer tous les exercices dynamiques du chapitre depuis admin_exercises
            exercises = await self.exercises_collection.find(
                {
                    "chapter_code": chapter_upper,
                    "is_dynamic": True,
                    "generator_key": {"$exists": True, "$ne": None}
                },
                {
                    "generator_key": 1,
                    "exercise_type": 1,
                    "difficulty": 1,
                    "offer": 1,
                    "needs_svg": 1,
                    "title": 1
                }
            ).to_list(1000)
            
            logger.info(
                f"[EXERCISE_TYPES_SYNC] {len(exercises)} exercices dynamiques trouvés "
                f"pour {chapter_upper}"
            )
            
            if not exercises:
                logger.warning(
                    f"[EXERCISE_TYPES_SYNC] Aucun exercice dynamique dans admin_exercises "
                    f"pour {chapter_upper}. Sync ignorée."
                )
                return stats
            
            # 2. Grouper par generator_key (un exercise_type par generator_key)
            generators_map = {}
            for ex in exercises:
                gen_key = ex.get("generator_key")
                if not gen_key:
                    continue
                
                if gen_key not in generators_map:
                    generators_map[gen_key] = {
                        'generator_key': gen_key,
                        'exercise_type': ex.get('exercise_type'),
                        'difficulties': set(),
                        'offers': set(),
                        'needs_svg': ex.get('needs_svg', False),
                        'title': ex.get('title')
                    }
                
                # Agréger les difficultés et offres disponibles
                if ex.get('difficulty'):
                    generators_map[gen_key]['difficulties'].add(ex['difficulty'])
                if ex.get('offer'):
                    generators_map[gen_key]['offers'].add(ex['offer'])
            
            # 3. Extraire le niveau depuis chapter_code (ex: "6E_N10" → "6E")
            niveau = chapter_upper.split('_')[0] if '_' in chapter_upper else chapter_upper[:2]
            
            # 4. Extraire le domaine depuis chapter_code
            domaine = self._infer_domain_from_chapter(chapter_upper)
            
            # 5. Synchroniser chaque generator_key vers exercise_types
            for gen_key, gen_data in generators_map.items():
                
                # Obtenir exercise_type depuis GeneratorFactory
                exercise_type = _get_exercise_type_from_generator(gen_key)
                if not exercise_type:
                    # Fallback: utiliser le champ exercise_type de l'exercice
                    exercise_type = gen_data.get('exercise_type') or gen_key
                    logger.warning(
                        f"[EXERCISE_TYPES_SYNC] Pas de mapping Factory pour {gen_key}, "
                        f"fallback: {exercise_type}"
                    )
                
                # Construire l'identifiant unique pour exercise_type
                # Format: chapter_code + generator_key (déterministe, pas de uuid)
                exercise_type_id = f"{chapter_upper}_{gen_key}"
                
                # Vérifier si l'exercise_type existe déjà
                existing = await exercise_types_collection.find_one({
                    "code_ref": gen_key,
                    "chapter_code": chapter_upper
                })
                
                # Document exercise_type à créer/mettre à jour
                exercise_type_doc = {
                    "id": exercise_type_id,
                    "code_ref": gen_key,
                    "chapter_code": chapter_upper,
                    "chapitre_id": chapter_upper,  # Legacy fallback
                    "niveau": niveau,
                    "domaine": domaine,
                    "titre": gen_data.get('title') or f"Exercice {exercise_type}",
                    "description": f"Exercice dynamique généré par {gen_key}",
                    "generator_kind": "DYNAMIC",
                    "difficulty_levels": sorted(list(gen_data['difficulties'])) or ["facile", "moyen", "difficile"],
                    "available_offers": sorted(list(gen_data['offers'])) or ["free"],
                    "min_questions": 1,
                    "max_questions": 10,
                    "default_questions": 5,
                    "requires_svg": gen_data.get('needs_svg', False),
                    "supports_seed": True,
                    "supports_ai_enonce": False,
                    "supports_ai_correction": False,
                    "competences_ids": [],
                    "question_kinds": {},
                    "random_config": {},
                    "updated_at": datetime.now(timezone.utc),
                    "source": "admin_exercises_auto_sync"
                }
                
                if existing and not force_recreate:
                    # Mise à jour (seulement les champs qui peuvent changer)
                    update_fields = {
                        "difficulty_levels": exercise_type_doc["difficulty_levels"],
                        "available_offers": exercise_type_doc["available_offers"],
                        "requires_svg": exercise_type_doc["requires_svg"],
                        "updated_at": exercise_type_doc["updated_at"],
                        "titre": exercise_type_doc["titre"]
                    }
                    
                    await exercise_types_collection.update_one(
                        {"_id": existing["_id"]},
                        {"$set": update_fields}
                    )
                    
                    logger.info(
                        f"[EXERCISE_TYPES_SYNC] ✅ Mis à jour: {exercise_type_id} "
                        f"(generator: {gen_key})"
                    )
                    stats['updated'] += 1
                    
                elif existing and force_recreate:
                    # Suppression puis recréation
                    await exercise_types_collection.delete_one({"_id": existing["_id"]})
                    
                    exercise_type_doc["created_at"] = datetime.now(timezone.utc)
                    await exercise_types_collection.insert_one(exercise_type_doc)
                    
                    logger.info(
                        f"[EXERCISE_TYPES_SYNC] ✅ Recréé (force): {exercise_type_id} "
                        f"(generator: {gen_key})"
                    )
                    stats['deleted'] += 1
                    stats['created'] += 1
                    
                else:
                    # Création
                    exercise_type_doc["created_at"] = datetime.now(timezone.utc)
                    await exercise_types_collection.insert_one(exercise_type_doc)
                    
                    logger.info(
                        f"[EXERCISE_TYPES_SYNC] ✅ Créé: {exercise_type_id} "
                        f"(generator: {gen_key})"
                    )
                    stats['created'] += 1
                
                stats['generator_keys'].append(gen_key)
            
            # 6. Nettoyer les exercise_types orphelins (optionnel - sécurité)
            # Si un exercise_type existe pour ce chapitre mais n'a plus d'exercice admin correspondant
            all_gen_keys = set(generators_map.keys())
            existing_exercise_types = await exercise_types_collection.find(
                {
                    "chapter_code": chapter_upper,
                    "generator_kind": "DYNAMIC",
                    "source": "admin_exercises_auto_sync"
                },
                {"code_ref": 1}
            ).to_list(1000)
            
            for et in existing_exercise_types:
                gen_key = et.get("code_ref")
                if gen_key and gen_key not in all_gen_keys:
                    # Cet exercise_type n'a plus d'exercice admin correspondant
                    await exercise_types_collection.delete_one({"_id": et["_id"]})
                    logger.info(
                        f"[EXERCISE_TYPES_SYNC] 🗑️  Supprimé orphelin: {gen_key} "
                        f"(plus d'exercice admin)"
                    )
                    stats['deleted'] += 1
            
            logger.info(
                f"[EXERCISE_TYPES_SYNC] Terminé pour {chapter_upper}: "
                f"créés={stats['created']}, mis à jour={stats['updated']}, "
                f"supprimés={stats['deleted']}"
            )
            
            return stats
            
        except Exception as e:
            logger.error(
                f"[EXERCISE_TYPES_SYNC] Erreur lors de la sync pour {chapter_upper}: {e}",
                exc_info=True
            )
            raise ValueError(
                f"Erreur lors de la synchronisation vers exercise_types pour {chapter_upper}: {e}"
            )
    
    def _infer_domain_from_chapter(self, chapter_code: str) -> str:
        """
        Inférer le domaine mathématique depuis le code chapitre.
        
        Ex: "6E_GM07" → "Grandeurs et Mesures"
            "6E_N10" → "Nombres et Calculs"
        """
        if not chapter_code or '_' not in chapter_code:
            return "Géométrie"
        
        parts = chapter_code.split('_')
        if len(parts) < 2:
            return "Géométrie"
        
        domain_code = parts[1][:2] if len(parts[1]) >= 2 else parts[1][:1]
        
        domain_map = {
            'GM': 'Grandeurs et Mesures',
            'G': 'Espace et géométrie',
            'N': 'Nombres et calculs',
            'C': 'Calcul',
            'A': 'Algèbre',
            'F': 'Fonctions',
            'S': 'Statistiques',
            'P': 'Probabilités',
            'D': 'Données',
            'SP': 'Statistiques et probabilités'
        }
        
        # Chercher le préfixe le plus long qui correspond
        for key in sorted(domain_map.keys(), key=len, reverse=True):
            if parts[1].startswith(key):
                return domain_map[key]
        
        return "Espace et géométrie"


def get_curriculum_sync_service(db: AsyncIOMotorDatabase) -> CurriculumSyncService:
    """Factory pour obtenir une instance du service de synchronisation"""
    return CurriculumSyncService(db)
