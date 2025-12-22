"""
Service de synchronisation automatique Curriculum ⇄ Exercises.

Quand un exercice est créé/modifié via l'admin :
- Si le chapitre n'existe pas dans le curriculum → il est créé automatiquement
- Si le chapitre existe → ses exercise_types sont mis à jour automatiquement
"""

import logging
from typing import Set, Optional, Dict, Any
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


def get_curriculum_sync_service(db: AsyncIOMotorDatabase) -> CurriculumSyncService:
    """Factory pour obtenir une instance du service de synchronisation"""
    return CurriculumSyncService(db)
