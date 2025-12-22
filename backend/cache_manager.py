"""
CACHE MANAGER - Le Maître Mot

Système de cache intelligent pour les gabarits d'énoncés.

OBJECTIF : Réduire les appels IA de 90% à quasi 0%

FONCTIONNEMENT :
    1. Gabarit stocké avec placeholders : {coordA}, {longueurBC}, etc.
    2. Lors de la génération, on remplace les placeholders par les valeurs réelles
    3. Aucun appel IA nécessaire si le gabarit existe

ARCHITECTURE :
    - Cache en mémoire (dict)
    - Persistence sur disque (JSON) pour survie aux redémarrages
    - Invalidation intelligente
    - Métriques de performance
"""

import json
import os
from typing import Dict, Optional, Any, List
from pathlib import Path
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Gestionnaire de cache pour les gabarits d'énoncés.
    
    Responsabilités :
        - Stocker et récupérer des gabarits
        - Persister sur disque
        - Suivre les métriques (hit/miss rate)
        - Invalider le cache si nécessaire
    """
    
    def __init__(self, cache_dir: str = "/app/backend/cache"):
        """
        Initialise le gestionnaire de cache.
        
        Args:
            cache_dir: Répertoire de stockage du cache sur disque
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache en mémoire : {cache_key: gabarit}
        self._cache: Dict[str, str] = {}
        
        # Métriques
        self._hits = 0
        self._misses = 0
        self._total_cost_saved = 0.0  # En tokens économisés
        
        # Charger le cache depuis le disque
        self._load_from_disk()
    
    def get(self, cache_key: str) -> Optional[str]:
        """
        Récupère un gabarit depuis le cache.
        
        Args:
            cache_key: Clé de cache unique
        
        Returns:
            Le gabarit si trouvé, None sinon
        """
        gabarit = self._cache.get(cache_key)
        
        if gabarit:
            self._hits += 1
            self._total_cost_saved += self._estimate_tokens(gabarit)
            logger.info(f"Cache HIT: {cache_key}")
            return gabarit
        else:
            self._misses += 1
            logger.info(f"Cache MISS: {cache_key}")
            return None
    
    def set(self, cache_key: str, gabarit: str):
        """
        Stocke un gabarit dans le cache.
        
        Args:
            cache_key: Clé de cache unique
            gabarit: Gabarit d'énoncé avec placeholders
        """
        self._cache[cache_key] = gabarit
        logger.info(f"Cache SET: {cache_key}")
        
        # Persister sur disque
        self._save_to_disk()
    
    def has(self, cache_key: str) -> bool:
        """
        Vérifie si un gabarit existe dans le cache.
        
        Args:
            cache_key: Clé de cache
        
        Returns:
            True si le gabarit existe
        """
        return cache_key in self._cache
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Retourne les métriques de performance du cache.
        
        Returns:
            Dict contenant hits, misses, hit_rate, tokens_saved
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
            "estimated_tokens_saved": self._total_cost_saved,
            "estimated_cost_saved_usd": round(self._total_cost_saved * 0.000002, 4),  # ~$0.002 per 1K tokens
            "cache_size": len(self._cache)
        }
    
    def clear(self):
        """Vide complètement le cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        self._total_cost_saved = 0.0
        self._save_to_disk()
        logger.warning("Cache cleared")
    
    def invalidate_pattern(self, pattern: str):
        """
        Invalide toutes les clés correspondant à un pattern.
        
        Args:
            pattern: Pattern regex pour matcher les clés
        
        Example:
            >>> cache.invalidate_pattern("symetrie_axiale.*")
        """
        keys_to_remove = [
            key for key in self._cache.keys()
            if re.match(pattern, key)
        ]
        
        for key in keys_to_remove:
            del self._cache[key]
        
        if keys_to_remove:
            self._save_to_disk()
            logger.info(f"Invalidated {len(keys_to_remove)} cache entries matching '{pattern}'")
    
    def interpolate(self, gabarit: str, values: Dict[str, Any]) -> str:
        """
        Remplace les placeholders dans un gabarit par les valeurs réelles.
        
        Args:
            gabarit: Gabarit avec placeholders {coordA}, {longueurBC}, etc.
            values: Dict des valeurs à insérer
        
        Returns:
            Énoncé final avec valeurs interpolées
        
        Examples:
            >>> gabarit = "Le point M est en {coordM}. Trouve son symétrique."
            >>> interpolate(gabarit, {"coordM": "(3, 5)"})
            "Le point M est en (3, 5). Trouve son symétrique."
        """
        enonce = gabarit
        
        for placeholder, value in values.items():
            # Chercher {placeholder} dans le texte
            pattern = "{" + placeholder + "}"
            if pattern in enonce:
                enonce = enonce.replace(pattern, str(value))
        
        return enonce
    
    def extract_placeholders(self, gabarit: str) -> List[str]:
        """
        Extrait tous les placeholders d'un gabarit.
        
        Args:
            gabarit: Gabarit avec placeholders
        
        Returns:
            Liste des noms de placeholders
        
        Examples:
            >>> extract_placeholders("Point {pointA} et axe {axeType} = {axeValue}")
            ["pointA", "axeType", "axeValue"]
        """
        return re.findall(r'\{([^}]+)\}', gabarit)
    
    def _load_from_disk(self):
        """Charge le cache depuis le fichier JSON sur disque."""
        cache_file = self.cache_dir / "gabarits_cache.json"
        
        if not cache_file.exists():
            logger.info("No cache file found, starting with empty cache")
            return
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache = data.get("cache", {})
                self._hits = data.get("hits", 0)
                self._misses = data.get("misses", 0)
                self._total_cost_saved = data.get("total_cost_saved", 0.0)
            
            logger.info(f"Cache loaded: {len(self._cache)} entries")
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            self._cache = {}
    
    def _save_to_disk(self):
        """Sauvegarde le cache dans un fichier JSON sur disque."""
        cache_file = self.cache_dir / "gabarits_cache.json"
        
        try:
            data = {
                "cache": self._cache,
                "hits": self._hits,
                "misses": self._misses,
                "total_cost_saved": self._total_cost_saved,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Cache saved: {len(self._cache)} entries")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estime le nombre de tokens dans un texte.
        
        Approximation : 1 token ≈ 4 caractères en français
        """
        return len(text) // 4


# Instance globale
cache_manager = CacheManager()


# Export des symboles publics
__all__ = [
    "CacheManager",
    "cache_manager"
]
