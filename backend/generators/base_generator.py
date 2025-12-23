"""
Base Generator - Interface abstraite pour tous les générateurs
==============================================================

Version: 2.0.0 (Dynamic Factory v1)

Ce module définit:
- L'interface abstraite BaseGenerator
- Les structures de données pour schema/defaults/presets
- La validation des paramètres
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import random
from backend.observability import (
    get_logger as get_obs_logger,
    safe_random_choice,
    safe_randrange,
    get_request_context,
)


class ParamType(str, Enum):
    """Types de paramètres supportés."""
    INT = "int"
    FLOAT = "float"  
    BOOL = "bool"
    ENUM = "enum"
    STRING = "string"


@dataclass
class ParamSchema:
    """Schéma d'un paramètre de générateur."""
    name: str
    type: ParamType
    description: str
    default: Any
    min: Optional[float] = None  # Pour INT/FLOAT
    max: Optional[float] = None  # Pour INT/FLOAT
    options: Optional[List[Any]] = None  # Pour ENUM
    required: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['type'] = self.type.value
        return d
    
    def validate(self, value: Any) -> tuple:
        """Valide une valeur contre le schéma. Retourne (valid, value_or_error)."""
        if value is None:
            if self.required:
                return False, f"Paramètre requis: {self.name}"
            return True, self.default
        
        try:
            if self.type == ParamType.INT:
                v = int(value)
                if self.min is not None and v < self.min:
                    return False, f"{self.name} doit être >= {self.min}"
                if self.max is not None and v > self.max:
                    return False, f"{self.name} doit être <= {self.max}"
                return True, v
            
            elif self.type == ParamType.FLOAT:
                v = float(value)
                if self.min is not None and v < self.min:
                    return False, f"{self.name} doit être >= {self.min}"
                if self.max is not None and v > self.max:
                    return False, f"{self.name} doit être <= {self.max}"
                return True, v
            
            elif self.type == ParamType.BOOL:
                if isinstance(value, bool):
                    return True, value
                if isinstance(value, str):
                    return True, value.lower() in ('true', '1', 'yes', 'oui')
                return True, bool(value)
            
            elif self.type == ParamType.ENUM:
                if self.options and value not in self.options:
                    return False, f"{self.name} doit être parmi: {self.options}"
                return True, value
            
            elif self.type == ParamType.STRING:
                return True, str(value)
            
            return True, value
            
        except (ValueError, TypeError) as e:
            return False, f"Erreur de conversion pour {self.name}: {str(e)}"


@dataclass
class Preset:
    """Preset pédagogique prédéfini."""
    key: str
    label: str
    description: str
    niveau: str
    params: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GeneratorMeta:
    """Métadonnées complètes d'un générateur."""
    key: str
    label: str
    description: str
    version: str
    niveaux: List[str]
    exercise_type: str
    svg_mode: str = "AUTO"
    supports_double_svg: bool = True
    pedagogical_tips: Optional[str] = None
    is_dynamic: bool = True  # P1.2 - Indique si c'est un générateur dynamique
    supported_grades: Optional[List[str]] = None  # P1.2 - Grades supportés (ex: ["6e", "5e"])
    supported_chapters: Optional[List[str]] = None  # P1.2 - Chapitres recommandés (ex: ["6e_SP03"])
    min_offer: str = "free"  # P2.1 - Offre minimale requise : "free" | "pro"
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # P1.2 - Si supported_grades n'est pas défini, utiliser niveaux par défaut
        if self.supported_grades is None:
            result['supported_grades'] = self.niveaux
        return result


class BaseGenerator(ABC):
    """
    Classe abstraite pour tous les générateurs d'exercices dynamiques.
    
    Chaque générateur doit implémenter:
    - get_meta(): métadonnées du générateur
    - get_schema(): schéma des paramètres
    - get_defaults(): valeurs par défaut
    - get_presets(): presets pédagogiques
    - generate(params): génération de l'exercice
    """
    
    def __init__(self, seed: Optional[int] = None):
        self._seed = seed
        self._rng = random.Random(seed)
        self._obs_logger = get_obs_logger('GENERATOR')
    
    @property
    def seed(self) -> Optional[int]:
        return self._seed
    
    def set_seed(self, seed: int):
        """Change le seed et réinitialise le RNG."""
        self._seed = seed
        self._rng = random.Random(seed)
    
    # ========================================================================
    # HELPERS RNG DETERMINISTES (à utiliser dans les générateurs)
    # ========================================================================
    
    def rng_choice(self, items, ctx: Optional[Dict[str, Any]] = None):
        """
        Choisit un élément aléatoire dans items en utilisant le RNG dédié.
        
        Args:
            items: Liste/tuple à choisir
            ctx: Contexte optionnel pour logging
        
        Returns:
            Un élément de items
        
        Raises:
            ValueError: Si items est vide
        
        Usage:
            type_exo = self.rng_choice(["type_a", "type_b", "type_c"])
        """
        if not items:
            raise ValueError(f"rng_choice() appelé sur une liste vide: context={ctx}")
        
        if len(items) == 1:
            return items[0]
        
        return self._rng.choice(items)
    
    def rng_randrange(self, start: int, stop: Optional[int] = None, step: int = 1, ctx: Optional[Dict[str, Any]] = None) -> int:
        """
        Génère un entier aléatoire dans [start, stop) en utilisant le RNG dédié.
        
        Args:
            start: Début du range (ou fin si stop est None)
            stop: Fin du range (optionnel)
            step: Pas (défaut 1)
            ctx: Contexte optionnel pour logging
        
        Returns:
            Un entier dans [start, stop)
        
        Raises:
            ValueError: Si range est vide (start >= stop)
        
        Usage:
            valeur = self.rng_randrange(10, 50)  # Entre 10 et 49
            valeur = self.rng_randrange(100)     # Entre 0 et 99
        """
        # Normalisation comme random.randrange
        if stop is None:
            stop = start
            start = 0
        
        if start >= stop:
            raise ValueError(f"rng_randrange() appelé avec range vide: start={start}, stop={stop}, context={ctx}")
        
        return self._rng.randrange(start, stop, step)
    
    def rng_randint(self, a: int, b: int, ctx: Optional[Dict[str, Any]] = None) -> int:
        """
        Génère un entier aléatoire dans [a, b] (inclus) en utilisant le RNG dédié.
        
        Args:
            a: Borne inférieure (incluse)
            b: Borne supérieure (incluse)
            ctx: Contexte optionnel pour logging
        
        Returns:
            Un entier dans [a, b]
        
        Raises:
            ValueError: Si a > b
        
        Usage:
            valeur = self.rng_randint(1, 10)  # Entre 1 et 10 inclus
        """
        if not isinstance(a, int) or not isinstance(b, int):
            raise TypeError(f"rng_randint(a, b) attend a:int et b:int, reçu a:{type(a).__name__}, b:{type(b).__name__}")
        
        if a > b:
            raise ValueError(f"rng_randint(a, b) requiert a <= b, reçu a={a}, b={b}")
        
        return self._rng.randint(a, b)
    
    # Fin des helpers RNG
    # ========================================================================
    
    @classmethod
    @abstractmethod
    def get_meta(cls) -> GeneratorMeta:
        """Retourne les métadonnées du générateur."""
        pass
    
    @classmethod
    @abstractmethod
    def get_schema(cls) -> List[ParamSchema]:
        """Retourne le schéma des paramètres."""
        pass
    
    @classmethod
    def get_defaults(cls) -> Dict[str, Any]:
        """Retourne les valeurs par défaut depuis le schéma."""
        return {p.name: p.default for p in cls.get_schema()}
    
    @classmethod
    @abstractmethod
    def get_presets(cls) -> List[Preset]:
        """Retourne les presets pédagogiques."""
        pass
    
    @classmethod
    def validate_params(cls, params: Dict[str, Any]) -> tuple:
        """
        Valide et normalise les paramètres.
        
        Returns:
            (valid: bool, result: Dict ou List[str])
            Si valid=True, result contient les params validés
            Si valid=False, result contient la liste des erreurs
        """
        schema = cls.get_schema()
        validated = {}
        errors = []
        
        for param_schema in schema:
            value = params.get(param_schema.name)
            valid, result = param_schema.validate(value)
            
            if valid:
                validated[param_schema.name] = result
            else:
                errors.append(result)
        
        if errors:
            return False, errors
        return True, validated
    
    @classmethod
    def merge_params(cls, *param_dicts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fusionne plusieurs dicts de paramètres (gauche à droite).
        Ordre: defaults < exercise_params < overrides
        """
        merged = cls.get_defaults().copy()
        for d in param_dicts:
            if d:
                merged.update({k: v for k, v in d.items() if v is not None})
        return merged
    
    @abstractmethod
    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un exercice avec les paramètres donnés.
        
        Args:
            params: Paramètres validés
            
        Returns:
            Dict avec:
            - variables: dict pour les templates
            - geo_data: données géométriques JSON-safe
            - figure_svg_enonce: SVG de l'énoncé (si applicable)
            - figure_svg_solution: SVG de la solution (si applicable)
            - meta: métadonnées de l'exercice généré
        """
        pass
    
    def safe_generate(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Génère avec validation automatique des paramètres.
        
        Fusionne defaults + params fournis, valide, puis génère.
        """
        merged = self.merge_params(params or {})
        valid, result = self.validate_params(merged)
        
        if not valid:
            raise ValueError(f"Paramètres invalides: {result}")
        
        return self.generate(result)


# =============================================================================
# FONCTIONS UTILITAIRES POUR SVG
# =============================================================================

def create_svg_wrapper(content: str, width: int, height: int, viewbox: str = None) -> str:
    """Crée un wrapper SVG avec les attributs standards."""
    vb = viewbox or f"0 0 {width} {height}"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{width}" height="{height}" style="max-width: 100%; height: auto;">
{content}
</svg>'''
