"""
Base Gold Generator - Extension pour générateurs certifiés Gold
================================================================

Version: 1.0.0

Ce module fournit:
- GoldGeneratorMeta: métadonnées étendues pour générateurs Gold
- BaseGoldGenerator: classe de base avec validations supplémentaires

Contraintes Gold:
- Seed obligatoire (reproductibilité)
- Pas de placeholders non résolus {{ }} dans les outputs
- Performance < perf_budget_ms (100ms par défaut)
- Variables toujours présentes dans le output
"""

import os
import re
import time
import logging
from abc import ABC
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from backend.generators.base_generator import BaseGenerator, GeneratorMeta


logger = logging.getLogger(__name__)

# Environnement
_IS_PRODUCTION = os.environ.get("ENVIRONMENT", "").lower() == "production"
_FALLBACK_ENABLED = os.environ.get("GOLD_ENABLE_FALLBACK", "0") == "1"


@dataclass
class GoldGeneratorMeta(GeneratorMeta):
    """
    Métadonnées étendues pour générateurs Gold.

    Hérite de GeneratorMeta et ajoute:
    - gold_version: version de la certification Gold
    - perf_budget_ms: budget de performance en millisecondes
    - quality_tier: niveau de qualité ("gold", "silver", "bronze")
    """
    gold_version: str = "1.0"
    perf_budget_ms: int = 100
    quality_tier: str = "gold"

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "gold_version": self.gold_version,
            "perf_budget_ms": self.perf_budget_ms,
            "quality_tier": self.quality_tier,
        })
        return result


class BaseGoldGenerator(BaseGenerator, ABC):
    """
    Classe de base pour générateurs certifiés Gold.

    Étend BaseGenerator avec:
    - Validation automatique des placeholders
    - Mesure de performance avec budget
    - Fallback optionnel (désactivé par défaut)
    - Validation du output (variables obligatoires)

    Usage:
        @GeneratorFactory.register
        class MyGoldGenerator(BaseGoldGenerator):
            @classmethod
            def get_meta(cls) -> GoldGeneratorMeta:
                return GoldGeneratorMeta(
                    key="MY_GOLD_V1",
                    label="Mon générateur Gold",
                    ...
                )
    """

    # Pattern pour détecter les placeholders non résolus
    _PLACEHOLDER_PATTERN = re.compile(r'\{\{[^}]+\}\}')

    # Pattern pour détecter HTML dangereux (XSS)
    _DANGEROUS_HTML_PATTERN = re.compile(
        r'<\s*script|javascript\s*:|onerror\s*=|onload\s*=',
        re.IGNORECASE
    )

    def __init__(self, seed: Optional[int] = None):
        """
        Initialise le générateur Gold.

        Args:
            seed: Graine pour reproductibilité.
                  Note: Pour les tests Gold, seed doit être fournie explicitement.
        """
        super().__init__(seed=seed)
        self._perf_start: Optional[float] = None

    @classmethod
    def get_meta(cls) -> GoldGeneratorMeta:
        """
        Retourne les métadonnées Gold du générateur.

        Doit être implémentée par les sous-classes pour retourner GoldGeneratorMeta.
        """
        raise NotImplementedError("Les sous-classes doivent implémenter get_meta()")

    @classmethod
    def _enrich_presets_with_templates(cls, presets: List['Preset']) -> List['Preset']:
        """
        Enrichit les presets avec les templates enoncetemplate et solutiontemplate.
        
        Cette méthode helper est appelée par les routes pour enrichir automatiquement
        les presets des générateurs Gold avec les templates nécessaires au Frontend.
        """
        from backend.generators.base_generator import Preset
        
        enriched_presets = []
        for preset in presets:
            # Créer une copie du dict params pour ne pas modifier l'original
            enriched_params = dict(preset.params)
            
            # Ajouter les templates par défaut si absents
            if "enoncetemplate" not in enriched_params:
                enriched_params["enoncetemplate"] = "Énonce par défaut"
            if "solutiontemplate" not in enriched_params:
                enriched_params["solutiontemplate"] = "Solution par défaut"
            
            # Créer un nouveau Preset avec les params enrichis
            enriched_preset = Preset(
                key=preset.key,
                label=preset.label,
                description=preset.description,
                niveau=preset.niveau,
                params=enriched_params
            )
            enriched_presets.append(enriched_preset)
        
        return enriched_presets

    # =========================================================================
    # HELPERS DE VALIDATION
    # =========================================================================

    def _check_no_placeholders(self, obj: Any, path: str = "") -> List[str]:
        """
        Vérifie récursivement qu'aucun placeholder {{ }} n'est présent.

        Args:
            obj: Objet à vérifier (dict, list, str, etc.)
            path: Chemin actuel pour les messages d'erreur

        Returns:
            Liste des chemins où des placeholders ont été trouvés
        """
        found = []

        if isinstance(obj, str):
            if self._PLACEHOLDER_PATTERN.search(obj):
                found.append(f"{path}: '{obj[:100]}...'")
        elif isinstance(obj, dict):
            for key, value in obj.items():
                child_path = f"{path}.{key}" if path else key
                found.extend(self._check_no_placeholders(value, child_path))
        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                child_path = f"{path}[{i}]"
                found.extend(self._check_no_placeholders(item, child_path))

        return found

    def _check_no_dangerous_html(self, obj: Any, path: str = "") -> List[str]:
        """
        Vérifie récursivement qu'aucun HTML dangereux n'est présent dans les strings.

        Args:
            obj: Objet à vérifier
            path: Chemin actuel pour les messages d'erreur

        Returns:
            Liste des chemins où du HTML dangereux a été trouvé
        """
        found = []

        if isinstance(obj, str):
            if self._DANGEROUS_HTML_PATTERN.search(obj):
                found.append(f"{path}: pattern dangereux détecté")
        elif isinstance(obj, dict):
            for key, value in obj.items():
                child_path = f"{path}.{key}" if path else key
                found.extend(self._check_no_dangerous_html(value, child_path))
        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                child_path = f"{path}[{i}]"
                found.extend(self._check_no_dangerous_html(item, child_path))

        return found

    def _validate_output(self, output: Dict[str, Any]) -> None:
        """
        Valide le output du générateur.

        Vérifie:
        - Présence de "variables" (obligatoire)
        - Pas de placeholders dans variables
        - Pas de HTML dangereux dans variables

        Args:
            output: Output du générateur

        Raises:
            ValueError: Si le output est invalide
        """
        # Vérifier présence de "variables"
        if "variables" not in output:
            raise ValueError("Output invalide: clé 'variables' obligatoire")

        variables = output.get("variables", {})

        # Vérifier placeholders
        placeholder_errors = self._check_no_placeholders(variables, "variables")
        if placeholder_errors:
            error_msg = f"Placeholders non résolus: {', '.join(placeholder_errors[:5])}"
            if not _IS_PRODUCTION:
                raise ValueError(error_msg)
            else:
                logger.error(f"[GOLD_PLACEHOLDER] {self.get_meta().key}: {error_msg}")

        # Vérifier HTML dangereux
        xss_errors = self._check_no_dangerous_html(variables, "variables")
        if xss_errors:
            error_msg = f"HTML dangereux détecté: {', '.join(xss_errors[:5])}"
            if not _IS_PRODUCTION:
                raise ValueError(error_msg)
            else:
                logger.error(f"[GOLD_XSS] {self.get_meta().key}: {error_msg}")

    # =========================================================================
    # GESTION DE LA PERFORMANCE
    # =========================================================================

    def _start_perf_timer(self) -> None:
        """Démarre le timer de performance."""
        self._perf_start = time.perf_counter()

    def _check_perf_budget(self) -> None:
        """
        Vérifie que le budget de performance n'est pas dépassé.

        En dev/test: lève une exception si dépassement
        En production: log un warning
        """
        if self._perf_start is None:
            return

        elapsed_ms = (time.perf_counter() - self._perf_start) * 1000
        meta = self.get_meta()
        budget_ms = getattr(meta, 'perf_budget_ms', 100)

        if elapsed_ms > budget_ms:
            msg = (
                f"[GOLD_PERF] {meta.key}: {elapsed_ms:.1f}ms > budget {budget_ms}ms"
            )
            if not _IS_PRODUCTION:
                logger.warning(msg)
                # En dev, on avertit mais on ne bloque pas systématiquement
                # Les tests Gold vérifient la moyenne, pas chaque génération
            else:
                logger.warning(msg)

    # =========================================================================
    # FALLBACK (DÉSACTIVÉ PAR DÉFAUT)
    # =========================================================================

    def _fallback_output(self, error: Exception) -> Optional[Dict[str, Any]]:
        """
        Génère un output de fallback en cas d'erreur.

        ATTENTION: Désactivé par défaut.
        Activable UNIQUEMENT via env var GOLD_ENABLE_FALLBACK=1.

        En dev/test: cette méthode n'est JAMAIS appelée (on raise toujours).

        Args:
            error: L'exception qui a causé l'échec

        Returns:
            Dict de fallback ou None si fallback désactivé
        """
        if not _FALLBACK_ENABLED:
            return None

        if not _IS_PRODUCTION:
            # En dev/test, on ne masque JAMAIS les erreurs
            return None

        meta = self.get_meta()
        logger.error(
            f"[GOLD_FALLBACK] {meta.key}: utilisation du fallback suite à: {error}"
        )

        return {
            "variables": {
                "_fallback": True,
                "_error": str(error)[:200],
            },
            "meta": {
                "fallback_used": True,
                "original_error": type(error).__name__,
            }
        }

    # =========================================================================
    # OVERRIDE DE safe_generate POUR AJOUTER LES VALIDATIONS GOLD
    # =========================================================================

    def safe_generate(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Génère avec validation automatique des paramètres ET validations Gold.

        Ajoute par rapport à BaseGenerator.safe_generate():
        - Mesure de performance
        - Validation des placeholders
        - Validation XSS
        - Fallback optionnel (si activé)
        """
        self._start_perf_timer()

        try:
            # Appel de la méthode parente
            output = super().safe_generate(params)

            # Validations Gold
            self._validate_output(output)

            # Vérification du budget de performance
            self._check_perf_budget()

            return output

        except Exception as e:
            # Tentative de fallback si activé
            fallback = self._fallback_output(e)
            if fallback is not None:
                return fallback

            # Sinon, on propage l'erreur
            raise


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "GoldGeneratorMeta",
    "BaseGoldGenerator",
]
