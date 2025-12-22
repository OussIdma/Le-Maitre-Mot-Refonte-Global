"""
Service pour gérer les chapitres MathALÉA
"""

import logging
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.models.chapter_model import Chapter, ChapterCreate, get_domaine_legacy
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ChapterService:
    """Service de gestion des chapitres"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.chapters
    
    async def initialize_indexes(self):
        """Créer les index nécessaires"""
        try:
            # Index unique sur le code
            await self.collection.create_index("code", unique=True)
            # Index sur niveau et domaine pour les recherches
            await self.collection.create_index([("niveau", 1), ("domaine", 1)])
            # Index sur legacy_code pour la migration
            await self.collection.create_index("legacy_code", sparse=True)
            logger.info("✅ Index créés pour la collection chapters")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création des index: {e}")
    
    async def upsert_chapter(self, chapter_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insérer ou mettre à jour un chapitre
        
        Args:
            chapter_data: Données du chapitre
            
        Returns:
            Chapitre créé ou mis à jour
        """
        try:
            code = chapter_data["code"]
            
            # Ajouter domaine_legacy si absent
            if "domaine_legacy" not in chapter_data and "domaine" in chapter_data:
                chapter_data["domaine_legacy"] = get_domaine_legacy(chapter_data["domaine"])
            
            # Ajouter updated_at
            chapter_data["updated_at"] = datetime.now(timezone.utc)
            
            # Upsert
            result = await self.collection.update_one(
                {"code": code},
                {
                    "$set": chapter_data,
                    "$setOnInsert": {"created_at": datetime.now(timezone.utc)}
                },
                upsert=True
            )
            
            # Récupérer le document
            chapter = await self.collection.find_one({"code": code}, {"_id": 0})
            
            if result.upserted_id:
                logger.info(f"✅ Chapitre créé: {code}")
            else:
                logger.info(f"🔄 Chapitre mis à jour: {code}")
            
            return chapter
        
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'upsert du chapitre {chapter_data.get('code')}: {e}")
            raise
    
    async def get_chapters_by_niveau(self, niveau: str) -> List[Dict[str, Any]]:
        """
        Récupérer les chapitres d'un niveau
        
        Args:
            niveau: Niveau scolaire (ex: "6e", "2nde")
            
        Returns:
            Liste des chapitres triés par domaine et ordre
        """
        try:
            chapters = await self.collection.find(
                {"niveau": niveau},
                {"_id": 0}
            ).sort([("domaine", 1), ("ordre", 1)]).to_list(None)
            
            return chapters
        
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des chapitres du niveau {niveau}: {e}")
            return []
    
    async def get_chapters_by_niveau_and_domaine(
        self,
        niveau: str,
        domaine: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupérer les chapitres d'un niveau et optionnellement d'un domaine
        
        Args:
            niveau: Niveau scolaire
            domaine: Domaine (optionnel)
            
        Returns:
            Liste des chapitres triés par ordre
        """
        try:
            query = {"niveau": niveau}
            if domaine:
                query["domaine"] = domaine
            
            chapters = await self.collection.find(
                query,
                {"_id": 0}
            ).sort("ordre", 1).to_list(None)
            
            return chapters
        
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des chapitres: {e}")
            return []
    
    async def get_chapter_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Récupérer un chapitre par son code
        
        Args:
            code: Code MathALÉA du chapitre
            
        Returns:
            Chapitre ou None
        """
        try:
            chapter = await self.collection.find_one({"code": code}, {"_id": 0})
            return chapter
        
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération du chapitre {code}: {e}")
            return None
    
    async def get_chapter_by_legacy_code(self, legacy_code: str) -> Optional[Dict[str, Any]]:
        """
        Récupérer un chapitre par son code legacy
        
        Args:
            legacy_code: Code legacy (ex: "6G20")
            
        Returns:
            Chapitre ou None
        """
        try:
            chapter = await self.collection.find_one({"legacy_code": legacy_code}, {"_id": 0})
            return chapter
        
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération du chapitre legacy {legacy_code}: {e}")
            return None
    
    async def count_chapters(self) -> int:
        """Compter le nombre total de chapitres"""
        try:
            count = await self.collection.count_documents({})
            return count
        except Exception as e:
            logger.error(f"❌ Erreur lors du comptage des chapitres: {e}")
            return 0
    
    async def get_all_niveaux(self) -> List[str]:
        """Récupérer la liste de tous les niveaux disponibles"""
        try:
            niveaux = await self.collection.distinct("niveau")
            # Trier les niveaux dans l'ordre logique
            ordre_niveaux = ["6e", "5e", "4e", "3e", "2nde", "1re", "Tale"]
            niveaux_sorted = sorted(
                niveaux,
                key=lambda x: ordre_niveaux.index(x) if x in ordre_niveaux else 999
            )
            return niveaux_sorted
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des niveaux: {e}")
            return []


__all__ = ["ChapterService"]
