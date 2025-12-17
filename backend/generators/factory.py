"""
Dynamic Factory - Registry Central des Générateurs
===================================================

Version: 2.0.0 (Dynamic Factory v1)

Ce module fournit:
- Un registry central unique pour tous les générateurs
- L'API publique pour lister, récupérer les schémas et générer
- La fusion des paramètres (defaults + exercise + overrides)

Endpoints exposés:
- GET /api/v1/exercises/generators
- GET /api/v1/exercises/generators/{key}/schema
"""

from typing import Dict, Any, List, Optional, Type
from generators.base_generator import BaseGenerator, GeneratorMeta, ParamSchema, Preset


# =============================================================================
# REGISTRY CENTRAL
# =============================================================================

class GeneratorFactory:
    """Factory centrale pour tous les générateurs."""
    
    _generators: Dict[str, Type[BaseGenerator]] = {}
    
    @classmethod
    def register(cls, generator_class: Type[BaseGenerator]) -> Type[BaseGenerator]:
        """
        Enregistre un générateur dans le registry.
        
        Utilisable comme décorateur:
        @GeneratorFactory.register
        class MyGenerator(BaseGenerator):
            ...
        """
        meta = generator_class.get_meta()
        cls._generators[meta.key] = generator_class
        return generator_class
    
    @classmethod
    def get(cls, key: str) -> Optional[Type[BaseGenerator]]:
        """Récupère une classe de générateur par sa clé."""
        return cls._generators.get(key.upper())
    
    @classmethod
    def list_all(cls) -> List[Dict[str, Any]]:
        """Liste tous les générateurs avec leurs métadonnées."""
        result = []
        for key, gen_class in cls._generators.items():
            meta = gen_class.get_meta()
            result.append({
                "key": meta.key,
                "label": meta.label,
                "description": meta.description,
                "version": meta.version,
                "niveaux": meta.niveaux,
                "exercise_type": meta.exercise_type,
                "svg_mode": meta.svg_mode,
                "supports_double_svg": meta.supports_double_svg,
                "param_count": len(gen_class.get_schema()),
                "preset_count": len(gen_class.get_presets())
            })
        return result
    
    @classmethod
    def get_schema(cls, key: str) -> Optional[Dict[str, Any]]:
        """Récupère le schéma complet d'un générateur."""
        gen_class = cls.get(key)
        if not gen_class:
            return None
        
        meta = gen_class.get_meta()
        schema = gen_class.get_schema()
        defaults = gen_class.get_defaults()
        presets = gen_class.get_presets()
        
        return {
            "generator_key": meta.key,
            "meta": meta.to_dict(),
            "defaults": defaults,
            "schema": [p.to_dict() for p in schema],
            "presets": [p.to_dict() for p in presets]
        }
    
    @classmethod
    def create_instance(cls, key: str, seed: Optional[int] = None) -> Optional[BaseGenerator]:
        """Crée une instance d'un générateur."""
        gen_class = cls.get(key)
        if not gen_class:
            return None
        return gen_class(seed=seed)
    
    @classmethod
    def generate(
        cls,
        key: str,
        exercise_params: Optional[Dict[str, Any]] = None,
        overrides: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Génère un exercice avec fusion des paramètres.
        
        Ordre de fusion: defaults < exercise_params < overrides
        
        Args:
            key: Clé du générateur
            exercise_params: Params stockés dans l'exercice (admin)
            overrides: Params du prof (live)
            seed: Graine pour reproductibilité
        
        Returns:
            Exercice généré complet
        """
        gen_class = cls.get(key)
        if not gen_class:
            raise ValueError(f"Générateur inconnu: {key}. Disponibles: {list(cls._generators.keys())}")
        
        # Fusion des paramètres
        merged = gen_class.merge_params(exercise_params or {}, overrides or {})
        
        # Validation
        valid, result = gen_class.validate_params(merged)
        if not valid:
            raise ValueError(f"Paramètres invalides: {result}")
        
        # Génération
        generator = gen_class(seed=seed)
        output = generator.generate(result)
        
        # Ajouter les métadonnées de génération
        meta = gen_class.get_meta()
        output["generation_meta"] = {
            "generator_key": meta.key,
            "generator_version": meta.version,
            "exercise_type": meta.exercise_type,
            "svg_mode": meta.svg_mode,
            "params_used": result,
            "seed": seed
        }
        
        return output


# =============================================================================
# API FONCTIONS PUBLIQUES
# =============================================================================

def get_generators_list() -> List[Dict[str, Any]]:
    """Liste tous les générateurs disponibles."""
    return GeneratorFactory.list_all()


def get_generator_schema(key: str) -> Optional[Dict[str, Any]]:
    """Récupère le schéma complet d'un générateur."""
    return GeneratorFactory.get_schema(key)


def generate_exercise(
    generator_key: str,
    exercise_params: Optional[Dict[str, Any]] = None,
    overrides: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    API principale pour générer un exercice.
    
    Params effectifs = defaults + exercise_params + overrides
    """
    return GeneratorFactory.generate(
        key=generator_key,
        exercise_params=exercise_params,
        overrides=overrides,
        seed=seed
    )


def validate_exercise_params(generator_key: str, params: Dict[str, Any]) -> tuple:
    """Valide des paramètres pour un générateur."""
    gen_class = GeneratorFactory.get(generator_key)
    if not gen_class:
        return False, [f"Générateur inconnu: {generator_key}"]
    return gen_class.validate_params(params)


# =============================================================================
# AUTO-IMPORT DES GÉNÉRATEURS
# =============================================================================

def _register_all_generators():
    """Importe et enregistre tous les générateurs."""
    # Import des générateurs existants et nouveaux
    try:
        from generators.thales_v2 import ThalesV2Generator
    except ImportError:
        pass
    
    try:
        from generators.symetrie_axiale_v2 import SymetrieAxialeV2Generator
    except ImportError:
        pass


# Auto-register au chargement du module
_register_all_generators()
