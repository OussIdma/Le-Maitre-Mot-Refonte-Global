"""
Repository pour les exercices statiques (GM07, GM08, etc.)

Ce repository fournit un accès unifié aux exercices statiques stockés en DB.
Remplace l'ancienne dépendance aux fichiers Python (data/gm07_exercises.py, etc.).
"""

from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.constants.collections import EXERCISES_COLLECTION


class StaticExerciseRepository:
    """
    Repository pour accéder aux exercices statiques depuis MongoDB.
    
    Remplace l'ancienne dépendance aux fichiers Python générés.
    DB = source de vérité unique.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialise le repository.
        
        Args:
            db: Instance de la base de données MongoDB (AsyncIOMotorDatabase)
        """
        self.db = db
        self.collection = db[EXERCISES_COLLECTION]
    
    async def list_by_chapter(
        self,
        chapter_code: str,
        offer: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Liste les exercices d'un chapitre avec filtres optionnels.
        
        Args:
            chapter_code: Code du chapitre (ex: "6E_GM07", "6E_GM08")
            offer: Filtre par offre ("free" ou "pro"). Si "pro", inclut aussi "free"
            difficulty: Filtre par difficulté ("facile", "moyen", "difficile")
        
        Returns:
            Liste des exercices correspondants (sans _id)
        """
        # Normaliser le code du chapitre
        chapter_upper = chapter_code.upper().replace("-", "_")
        
        # Construire la requête
        query = {"chapter_code": chapter_upper}
        
        # Filtre par offre (pro voit free + pro, free ne voit que free)
        if offer:
            offer_lower = offer.lower()
            if offer_lower == "pro":
                # PRO voit tous les exercices (free + pro)
                query["offer"] = {"$in": ["free", "pro"]}
            else:
                # FREE ne voit que les exercices free
                query["offer"] = "free"
        
        # Filtre par difficulté
        if difficulty:
            query["difficulty"] = difficulty.lower()
        
        # Récupérer les exercices (sans _id, triés par id)
        exercises = await self.collection.find(
            query,
            {"_id": 0}
        ).sort("id", 1).to_list(length=None)
        
        return exercises

