"""
Service de mapping entre chapitre_id (legacy) et chapter_code (MathALÉA)

Ce service aide à gérer la transition douce entre les deux systèmes de référencement des chapitres.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class ChapterMappingService:
    """Service pour gérer le mapping chapitre_id ↔ chapter_code"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.chapters_collection = db.chapters
    
    async def get_chapter_code_for_exercise_type(
        self,
        exercise_type: dict
    ) -> Optional[str]:
        """
        Récupère le chapter_code pour un ExerciseType donné
        
        Args:
            exercise_type: Dictionnaire représentant un ExerciseType
                          (ou objet Pydantic avec .dict())
        
        Returns:
            chapter_code si trouvé, sinon None
        
        Stratégie :
        1. Si chapter_code est déjà présent dans l'ExerciseType, le retourner
        2. Sinon, tenter de trouver le chapitre correspondant via :
           - chapitre_id (legacy_code)
           - titre + niveau
        """
        # Cas 1 : chapter_code déjà présent
        if isinstance(exercise_type, dict):
            chapter_code = exercise_type.get("chapter_code")
        else:
            # Pydantic model
            chapter_code = getattr(exercise_type, "chapter_code", None)
        
        if chapter_code:
            return chapter_code
        
        # Cas 2 : Recherche dans la collection chapters
        chapitre_id = exercise_type.get("chapitre_id") if isinstance(exercise_type, dict) else getattr(exercise_type, "chapitre_id", None)
        niveau = exercise_type.get("niveau") if isinstance(exercise_type, dict) else getattr(exercise_type, "niveau", None)
        
        if not chapitre_id:
            return None
        
        try:
            # Stratégie 1 : Par legacy_code
            chapter = await self.chapters_collection.find_one(
                {"legacy_code": chapitre_id},
                {"_id": 0, "code": 1}
            )
            
            if chapter:
                return chapter["code"]
            
            # Stratégie 2 : Par code directement
            chapter = await self.chapters_collection.find_one(
                {"code": chapitre_id},
                {"_id": 0, "code": 1}
            )
            
            if chapter:
                return chapter["code"]
            
            # Stratégie 3 : Par titre + niveau
            if niveau:
                chapter = await self.chapters_collection.find_one(
                    {
                        "niveau": niveau,
                        "titre": {"$regex": f".*{chapitre_id}.*", "$options": "i"}
                    },
                    {"_id": 0, "code": 1}
                )
                
                if chapter:
                    return chapter["code"]
            
            # Aucune correspondance trouvée
            logger.debug(f"Aucun chapter_code trouvé pour chapitre_id='{chapitre_id}', niveau='{niveau}'")
            return None
        
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de chapter_code: {e}")
            return None
    
    async def get_chapitre_id_for_chapter_code(
        self,
        chapter_code: str
    ) -> Optional[str]:
        """
        Récupère le chapitre_id (legacy) pour un chapter_code donné
        
        Args:
            chapter_code: Code MathALÉA du chapitre (ex: "6e_G04")
        
        Returns:
            chapitre_id (legacy) si trouvé, sinon None
        
        Note: Cette fonction est moins critique car on privilégie chapter_code,
        mais elle peut être utile pour la rétrocompatibilité.
        """
        try:
            chapter = await self.chapters_collection.find_one(
                {"code": chapter_code},
                {"_id": 0, "legacy_code": 1, "titre": 1}
            )
            
            if not chapter:
                return None
            
            # Préférer legacy_code si présent
            if chapter.get("legacy_code"):
                return chapter["legacy_code"]
            
            # Sinon, retourner le titre (c'est ce qui est souvent dans chapitre_id)
            return chapter.get("titre")
        
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de chapitre_id: {e}")
            return None
    
    async def get_chapter_info(self, chapter_code: str) -> Optional[dict]:
        """
        Récupère les informations complètes d'un chapitre par son code
        
        Args:
            chapter_code: Code MathALÉA du chapitre
        
        Returns:
            Dictionnaire avec les infos du chapitre, ou None
        """
        try:
            chapter = await self.chapters_collection.find_one(
                {"code": chapter_code},
                {"_id": 0}
            )
            return chapter
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du chapitre {chapter_code}: {e}")
            return None
    
    async def find_possible_chapters_for_exercise_type(
        self,
        exercise_type: dict,
        max_results: int = 5
    ) -> list[dict]:
        """
        Trouve les chapitres possibles pour un ExerciseType sans chapter_code
        
        Utile pour diagnostiquer les 7 ExerciseType non migrés.
        
        Args:
            exercise_type: ExerciseType à analyser
            max_results: Nombre maximum de suggestions
        
        Returns:
            Liste de chapitres possibles avec score de pertinence
        """
        chapitre_id = exercise_type.get("chapitre_id") if isinstance(exercise_type, dict) else getattr(exercise_type, "chapitre_id", None)
        niveau = exercise_type.get("niveau") if isinstance(exercise_type, dict) else getattr(exercise_type, "niveau", None)
        domaine = exercise_type.get("domaine") if isinstance(exercise_type, dict) else getattr(exercise_type, "domaine", None)
        
        if not chapitre_id:
            return []
        
        possible_chapters = []
        
        try:
            # Recherche par niveau et similarité de titre
            if niveau:
                cursor = self.chapters_collection.find(
                    {
                        "niveau": niveau,
                        "titre": {"$regex": f".*{chapitre_id}.*", "$options": "i"}
                    },
                    {"_id": 0}
                ).limit(max_results)
                
                chapters = await cursor.to_list(max_results)
                
                for chapter in chapters:
                    possible_chapters.append({
                        "chapter": chapter,
                        "match_type": "titre_exact",
                        "confidence": "high"
                    })
            
            # Si pas assez de résultats, élargir la recherche au domaine
            if len(possible_chapters) < max_results and domaine:
                # Extraire les mots-clés du chapitre_id
                keywords = chapitre_id.split()
                
                for keyword in keywords:
                    if len(keyword) > 3:  # Ignorer les mots trop courts
                        cursor = self.chapters_collection.find(
                            {
                                "niveau": niveau,
                                "titre": {"$regex": f".*{keyword}.*", "$options": "i"}
                            },
                            {"_id": 0}
                        ).limit(max_results - len(possible_chapters))
                        
                        chapters = await cursor.to_list(max_results - len(possible_chapters))
                        
                        for chapter in chapters:
                            # Éviter les doublons
                            if not any(p["chapter"]["code"] == chapter["code"] for p in possible_chapters):
                                possible_chapters.append({
                                    "chapter": chapter,
                                    "match_type": "keyword",
                                    "confidence": "medium"
                                })
            
            return possible_chapters
        
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de chapitres possibles: {e}")
            return []


__all__ = ["ChapterMappingService"]
