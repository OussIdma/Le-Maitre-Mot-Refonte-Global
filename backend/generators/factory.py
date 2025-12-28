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
import time
import logging
from backend.generators.base_generator import BaseGenerator, GeneratorMeta, ParamSchema, Preset
from backend.observability import (
    get_logger as get_obs_logger,
    get_request_context,
)

logger = logging.getLogger(__name__)
obs_logger = get_obs_logger('GENERATOR_FACTORY')


# =============================================================================
# REGISTRY CENTRAL
# =============================================================================

class GeneratorFactory:
    """Factory centrale pour tous les générateurs."""

    _generators: Dict[str, Type[BaseGenerator]] = {}

    # P0 Gold - Paramètres globaux acceptés pour tous les générateurs (exemptés de validation schema)
    _GLOBAL_PARAMS: set = {"seed"}

    # P0 Gold - Champs UI/meta à ignorer lors de la validation stricte (transmis par l'UI mais non utilisés par le générateur)
    _UI_META_FIELDS: set = {
        "grade", "niveau", "chapter", "chapitre", "chapter_code", "code_officiel",
        "exercise_type", "type_exercice", "figure_type", "is_dynamic",
        "offer", "difficulte", "difficulty", "nb_exercices",
    }
    
    # P4.1 - Générateurs désactivés (non utilisables)
    # Cette liste est mise à jour manuellement après classification
    # Pour mettre à jour : exécuter test_dynamic_generators.py puis classify_generators.py
    DISABLED_GENERATORS: List[str] = [
        # Exemple (à remplacer par les résultats réels de classification) :
        # "SIMPLIFICATION_FRACTIONS_V1",
    ]
    
    # Aliases pour compatibilité arrière (clés legacy -> nouveaux générateurs)
    _ALIASES: Dict[str, str] = {
        # Ancienne clé générique pour la symétrie axiale → nouveau générateur Factory
        "SYMETRIE_AXIALE": "SYMETRIE_AXIALE_V2",
        # Alias Thalès (saisie avec espace ou sans suffixe)
        "THALES": "THALES_V2",
        "THALES V1": "THALES_V2",
        "THALES_V1": "THALES_V2",
    }

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
        normalized = key.upper()
        # Appliquer les alias pour compatibilité arrière
        normalized = cls._ALIASES.get(normalized, normalized)
        
        # P4.1 - Vérifier si le générateur est désactivé
        if normalized in cls.DISABLED_GENERATORS:
            logger.warning(
                f"[GENERATOR_DISABLED] Tentative d'utilisation du générateur désactivé: {normalized}"
            )
            return None
        
        return cls._generators.get(normalized)
    
    @classmethod
    def list_all(cls, include_disabled: bool = False) -> List[Dict[str, Any]]:
        """
        Liste tous les générateurs avec leurs métadonnées.
        
        P1.2: Inclut is_dynamic, supported_grades, supported_chapters pour le filtrage UI.
        P4.1: Exclut les générateurs désactivés par défaut.
        
        Args:
            include_disabled: Si True, inclut aussi les générateurs désactivés
        """
        result = []
        for key, gen_class in cls._generators.items():
            # P4.1 - Filtrer les générateurs désactivés
            if not include_disabled and key in cls.DISABLED_GENERATORS:
                continue
            
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
                "preset_count": len(gen_class.get_presets()),
                # P1.2 - Métadonnées pour filtrage
                "is_dynamic": getattr(meta, 'is_dynamic', True),  # Par défaut True pour compatibilité
                "supported_grades": getattr(meta, 'supported_grades', meta.niveaux),  # Fallback sur niveaux
                "supported_chapters": getattr(meta, 'supported_chapters', []),  # Optionnel
                # P4.1 - Statut de désactivation
                "disabled": key in cls.DISABLED_GENERATORS
            })
        return result
    
    @classmethod
    def get_schema(cls, key: str) -> Optional[Dict[str, Any]]:
        """Récupère le schéma complet d'un générateur."""
        normalized = key.upper()
        normalized = cls._ALIASES.get(normalized, normalized)
        
        # P4.1 - Vérifier si le générateur est désactivé
        if normalized in cls.DISABLED_GENERATORS:
            logger.warning(
                f"[GENERATOR_DISABLED] Tentative de récupération du schéma d'un générateur désactivé: {normalized}"
            )
            return None
        
        gen_class = cls.get(normalized)
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
    def get_exercise_type(cls, key: str) -> Optional[str]:
        """
        Source de vérité unique: récupère l'exercise_type déclaré dans le GeneratorMeta.
        Applique les alias avant de résoudre la classe.
        """
        normalized = key.upper()
        normalized = cls._ALIASES.get(normalized, normalized)
        gen_class = cls._generators.get(normalized)
        if not gen_class:
            return None
        meta = gen_class.get_meta()
        return meta.exercise_type if meta else None
    
    @classmethod
    def create_instance(cls, key: str, seed: Optional[int] = None) -> Optional[BaseGenerator]:
        """Crée une instance d'un générateur."""
        gen_class = cls.get(key)
        if not gen_class:
            return None
        return gen_class(seed=seed)

    @classmethod
    def _validate_params_strict(
        cls,
        generator_key: str,
        params: Dict[str, Any],
        allow_global: Optional[set] = None
    ) -> Dict[str, Any]:
        """
        P0 Gold - Validation STRICTE des paramètres contre le schéma du générateur.

        STRICT: paramètre inconnu => ValueError (pas de fallback silencieux).

        Args:
            generator_key: Clé du générateur (normalisée)
            params: Paramètres à valider
            allow_global: Clés autorisées hors schéma (ex: {"seed"})

        Returns:
            params validés (inchangés si tout est OK)

        Raises:
            ValueError: si param inconnu OU obligatoire manquant
        """
        allow_global = allow_global or cls._GLOBAL_PARAMS

        gen_class = cls._generators.get(generator_key)
        if not gen_class:
            raise ValueError(f"Générateur '{generator_key}' non trouvé")

        schema = gen_class.get_schema()
        schema_keys = {param.name for param in schema}

        # Unknown = tout ce qui n'est pas dans schema, ni global, ni UI_META_FIELDS
        # Les UI_META_FIELDS sont transmis par l'UI mais ignorés par le générateur
        unknown_params = set(params.keys()) - schema_keys - allow_global - cls._UI_META_FIELDS
        if unknown_params:
            raise ValueError(
                f"Paramètres non déclarés : {', '.join(sorted(unknown_params))}. "
                f"Valides : {', '.join(sorted(schema_keys | allow_global))}"
            )

        # Vérifier obligatoires (schema seulement)
        for param_schema in schema:
            if param_schema.required and param_schema.name not in params:
                raise ValueError(f"Paramètre obligatoire manquant : '{param_schema.name}'")

        return params

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
        
        P4.1 - Lève une exception si le générateur est désactivé.
        
        Args:
            key: Clé du générateur
            exercise_params: Params stockés dans l'exercice (admin)
            overrides: Params du prof (live)
            seed: Graine pour reproductibilité
        
        Returns:
            Exercice généré complet
        """
        normalized = key.upper()
        normalized = cls._ALIASES.get(normalized, normalized)
        
        # P4.1 - Vérifier si le générateur est désactivé
        if normalized in cls.DISABLED_GENERATORS:
            logger.error(
                f"[GENERATOR_DISABLED] Tentative de génération avec générateur désactivé: {normalized}"
            )
            raise ValueError(
                f"Le générateur '{normalized}' est désactivé et ne peut pas être utilisé. "
                f"Consultez docs/CLASSIFICATION_GENERATEURS.md pour plus d'informations."
            )
        
        gen_start = time.time()
        obs_logger = get_obs_logger('GENERATOR')
        ctx = get_request_context()
        ctx.update({
            'generator_key': normalized,
            'seed': seed,
        })
        ctx.pop("exc_info", None)
        ctx.pop("stack_info", None)
        
        # Log début génération
        obs_logger.info(
            "event=generate_in",
            event="generate_in",
            outcome="in_progress",
            **ctx
        )
        
        # Log params (DEBUG uniquement si LOG_VERBOSE=1)
        if exercise_params or overrides:
            obs_logger.debug(
                "event=params",
                event="params",
                outcome="in_progress",
                exercise_params_keys=list(exercise_params.keys()) if exercise_params else [],
                overrides_keys=list(overrides.keys()) if overrides else [],
                **ctx
            )
        
        try:
            gen_class = cls.get(normalized)
            if not gen_class:
                obs_logger.error(
                    "event=generator_unknown",
                    event="generator_unknown",
                    outcome="error",
                    reason="generator_key_unknown",
                    available_generators=list(cls._generators.keys()),
                    **ctx  # ctx contient déjà generator_key
                )
                raise ValueError(f"Générateur inconnu: {key}. Disponibles: {list(cls._generators.keys())}")
            
            # Fusion des paramètres
            merged = gen_class.merge_params(exercise_params or {}, overrides or {})

            # P0 Gold - Récupérer seed depuis merged si non fourni directement
            # Priorité: argument seed > overrides.seed > exercise_params.seed
            effective_seed = seed
            if effective_seed is None and "seed" in merged:
                effective_seed = merged.get("seed")
                if effective_seed is not None:
                    try:
                        effective_seed = int(effective_seed)
                    except (ValueError, TypeError):
                        effective_seed = None

            # P0 Gold - Validation STRICTE des paramètres (unknown => ValueError)
            # Inclure seed dans merged pour validation
            if effective_seed is not None:
                merged["seed"] = effective_seed
            cls._validate_params_strict(normalized, merged)

            # Validation des types et valeurs
            valid, result = gen_class.validate_params(merged)
            if not valid:
                ctx.pop("exc_info", None)
                ctx.pop("stack_info", None)
                obs_logger.error(
                    "event=params_invalid",
                    event="params_invalid",
                    outcome="error",
                    reason="validation_failed",
                    validation_errors=result if isinstance(result, list) else [str(result)],
                    **ctx
                )
                raise ValueError(f"Paramètres invalides: {result}")

            # Génération avec effective_seed
            generator = gen_class(seed=effective_seed)
            output = generator.generate(result)
            
            # Ajouter les métadonnées de génération
            meta = gen_class.get_meta()
            output["generation_meta"] = {
                "generator_key": meta.key,
                "generator_version": meta.version,
                "exercise_type": meta.exercise_type,
                "svg_mode": meta.svg_mode,
                "params_used": result,
                "seed": effective_seed
            }
            
            # Log succès
            gen_duration_ms = int((time.time() - gen_start) * 1000)
            ctx.update({
                'variant_id': result.get('variant_id'),
                'pedagogy_mode': result.get('pedagogy_mode'),
            })
            logger.info(
                f"[GENERATOR_OK] ✅ Génération réussie: generator={key}, "
                f"duration_ms={gen_duration_ms}, variables={len(output.get('variables', {}))}, "
                f"svg_enonce={output.get('figure_svg_enonce') is not None}, "
                f"svg_solution={output.get('figure_svg_solution') is not None}"
            )
            obs_logger.info(
                "event=generate_complete",
                event="generate_complete",
                outcome="success",
                duration_ms=gen_duration_ms,
                variables_count=len(output.get('variables', {})),
                has_svg_enonce=output.get('figure_svg_enonce') is not None,
                has_svg_solution=output.get('figure_svg_solution') is not None,
                **ctx
            )
            
            return output
            
        except Exception as e:
            gen_duration_ms = int((time.time() - gen_start) * 1000)
            logger.error(
                f"[GENERATOR_FAIL] ❌ Génération échouée: generator={key}, "
                f"duration_ms={gen_duration_ms}, exception={type(e).__name__}, "
                f"message={str(e)[:200]}"
            )
            obs_logger.error(
                "event=generate_exception",
                event="generate_exception",
                outcome="error",
                duration_ms=gen_duration_ms,
                reason="generation_failed",
                exception_type=type(e).__name__,
                exception_message=str(e)[:200],
                **ctx,
                exc_info=True
            )
            raise


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
    # generate() applique déjà l'aliasing via GeneratorFactory.get()
    return GeneratorFactory.generate(
        key=generator_key,
        exercise_params=exercise_params,
        overrides=overrides,
        seed=seed,
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
        from backend.generators.thales_v2 import ThalesV2Generator  # noqa:F401
    except ImportError:
        pass
    
    try:
        from backend.generators.symetrie_axiale_v2 import SymetrieAxialeV2Generator  # noqa:F401
    except ImportError:
        pass

    try:
        from backend.generators.thales_generator import ThalesGenerator  # noqa:F401
    except ImportError:
        pass
    
    try:
        from backend.generators.simplification_fractions_v1 import SimplificationFractionsV1Generator  # noqa:F401
    except ImportError:
        pass
    
    try:
        from backend.generators.simplification_fractions_v2 import SimplificationFractionsV2Generator  # noqa:F401
    except ImportError:
        pass
    
    try:
        from backend.generators.calcul_nombres_v1 import CalculNombresV1Generator  # noqa:F401
    except ImportError:
        pass
    
    try:
        from backend.generators.raisonnement_multiplicatif_v1 import RaisonnementMultiplicatifV1Generator  # noqa:F401
    except ImportError:
        pass

    # P1-PHASE2 Batch 1: Nouveaux générateurs Gold
    try:
        from backend.generators.nombres_entiers_v1 import NombresEntiersV1Generator  # noqa:F401
    except ImportError:
        pass

    try:
        from backend.generators.droite_graduee_v1 import DroiteGradueeV1Generator  # noqa:F401
    except ImportError:
        pass

    try:
        from backend.generators.criteres_divisibilite_v1 import CriteresDivisibiliteV1Generator  # noqa:F401
    except ImportError:
        pass

    try:
        from backend.generators.multiples_diviseurs_v1 import MultiplesDiviseursV1Generator  # noqa:F401
    except ImportError:
        pass

    try:
        from backend.generators.perimetre_v1 import PerimetreV1Generator  # noqa:F401
    except ImportError:
        pass


# Auto-register au chargement du module
_register_all_generators()
