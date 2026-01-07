"""
Service de validation du curriculum
Utilise curriculum_complete.py comme source de vérité
"""
from typing import List, Optional, Dict, Any
from backend.curriculum_complete import CURRICULUM_DATA_COMPLETE
from backend.logger import get_logger

logger = get_logger()


class CurriculumService:
    """Service pour valider et interroger le curriculum"""
    
    def __init__(self):
        """Initialise le service avec les données du curriculum"""
        self.curriculum = CURRICULUM_DATA_COMPLETE.get("Mathématiques", {}).get("data", {})
        self._niveaux_cache = None
        self._chapitres_cache: Dict[str, List[str]] = {}
    
    def get_niveaux_disponibles(self) -> List[str]:
        """
        Retourne la liste des niveaux disponibles
        
        Returns:
            Liste des niveaux (ex: ["CP", "CE1", "6e", "5e", ...])
        """
        if self._niveaux_cache is None:
            self._niveaux_cache = list(self.curriculum.keys())
            logger.info(f"Niveaux disponibles chargés: {len(self._niveaux_cache)}")
        
        return self._niveaux_cache
    
    def validate_niveau(self, niveau: str) -> bool:
        """
        Valide qu'un niveau existe dans le curriculum
        
        Args:
            niveau: Niveau à valider (ex: "5e", "CP")
        
        Returns:
            True si le niveau est valide, False sinon
        """
        niveaux = self.get_niveaux_disponibles()
        is_valid = niveau in niveaux
        
        if not is_valid:
            logger.warning(f"Niveau invalide: '{niveau}'. Valides: {niveaux}")
        
        return is_valid
    
    def get_chapitres_disponibles(self, niveau: str) -> List[str]:
        """
        Retourne la liste des chapitres disponibles pour un niveau
        
        Args:
            niveau: Niveau scolaire (ex: "5e")
        
        Returns:
            Liste des chapitres pour ce niveau
        """
        # Cache par niveau
        if niveau in self._chapitres_cache:
            return self._chapitres_cache[niveau]
        
        if niveau not in self.curriculum:
            logger.warning(f"Niveau '{niveau}' non trouvé dans le curriculum")
            return []
        
        # Récupérer tous les chapitres (clés des domaines)
        chapitres = []
        niveau_data = self.curriculum[niveau]
        
        for domaine, chapitres_list in niveau_data.items():
            if isinstance(chapitres_list, list):
                chapitres.extend(chapitres_list)
        
        # Filtrer les doublons et trier
        chapitres = sorted(list(set(chapitres)))
        
        # Mise en cache
        self._chapitres_cache[niveau] = chapitres
        
        logger.info(f"Chapitres pour {niveau}: {len(chapitres)}")
        return chapitres
    
    def validate_chapitre(self, niveau: str, chapitre: str) -> bool:
        """
        Valide qu'un chapitre existe pour un niveau donné
        
        Args:
            niveau: Niveau scolaire (ex: "5e")
            chapitre: Chapitre à valider (ex: "Symétrie axiale")
        
        Returns:
            True si le chapitre existe pour ce niveau, False sinon
        """
        if not self.validate_niveau(niveau):
            logger.warning(f"Validation chapitre impossible: niveau '{niveau}' invalide")
            return False
        
        chapitres = self.get_chapitres_disponibles(niveau)
        is_valid = chapitre in chapitres
        
        if not is_valid:
            logger.warning(
                f"Chapitre invalide: '{chapitre}' pour niveau '{niveau}'. "
                f"Valides: {chapitres[:5]}..."
            )
        
        return is_valid
    
    def get_domaine_by_chapitre(self, niveau: str, chapitre: str) -> Optional[str]:
        """
        Retourne le domaine d'un chapitre pour un niveau donné
        
        Args:
            niveau: Niveau scolaire
            chapitre: Chapitre recherché
        
        Returns:
            Nom du domaine ou None si non trouvé
        """
        if niveau not in self.curriculum:
            return None
        
        niveau_data = self.curriculum[niveau]
        
        for domaine, chapitres_list in niveau_data.items():
            if isinstance(chapitres_list, list) and chapitre in chapitres_list:
                return domaine
        
        return None
    
    def get_curriculum_info(self) -> Dict[str, Any]:
        """
        Retourne des informations générales sur le curriculum
        
        Returns:
            Dict avec statistiques du curriculum
        """
        niveaux = self.get_niveaux_disponibles()
        total_chapitres = sum(
            len(self.get_chapitres_disponibles(niveau))
            for niveau in niveaux
        )
        
        return {
            "total_niveaux": len(niveaux),
            "niveaux": niveaux,
            "total_chapitres": total_chapitres,
            "domaines": list(set(
                domaine
                for niveau in niveaux
                for domaine in self.curriculum[niveau].keys()
            ))
        }


# Instance globale pour réutilisation
curriculum_service = CurriculumService()
