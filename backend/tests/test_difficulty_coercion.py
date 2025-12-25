"""
Tests pour la coercition des difficultés (P4.C)
"""

import pytest
from backend.utils.difficulty_utils import (
    coerce_to_supported_difficulty,
    auto_complete_presets,
    normalize_difficulty,
)


class TestCoerceToSupportedDifficulty:
    """Tests pour coerce_to_supported_difficulty()"""
    
    def test_difficile_to_moyen_fallback(self):
        """Test que difficile → moyen si moyen supporté"""
        result = coerce_to_supported_difficulty("difficile", ["facile", "moyen"])
        assert result == "moyen"
    
    def test_difficile_to_facile_fallback(self):
        """Test que difficile → facile si seulement facile supporté"""
        result = coerce_to_supported_difficulty("difficile", ["facile"])
        assert result == "facile"
    
    def test_moyen_to_facile_fallback(self):
        """Test que moyen → facile si facile supporté"""
        result = coerce_to_supported_difficulty("moyen", ["facile"])
        assert result == "facile"
    
    def test_supported_difficulty_no_coercion(self):
        """Test qu'une difficulté supportée n'est pas coercée"""
        result = coerce_to_supported_difficulty("facile", ["facile", "moyen", "difficile"])
        assert result == "facile"
        
        result = coerce_to_supported_difficulty("moyen", ["facile", "moyen"])
        assert result == "moyen"
    
    def test_normalizes_before_coercion(self):
        """Test que la normalisation est appliquée avant la coercition"""
        result = coerce_to_supported_difficulty("standard", ["facile", "moyen"])
        # "standard" → "moyen" (normalisé), puis "moyen" est supporté → pas de coercition
        assert result == "moyen"
        
        result = coerce_to_supported_difficulty("hard", ["facile", "moyen"])
        # "hard" → "difficile" (normalisé), puis "difficile" → "moyen" (coercé)
        assert result == "moyen"
    
    def test_logs_coercion(self, caplog):
        """Test que la coercition est loggée"""
        import logging
        logger = logging.getLogger("test")
        
        coerce_to_supported_difficulty("difficile", ["facile", "moyen"], logger=logger)
        
        assert "[DIFFICULTY_COERCED]" in caplog.text
        assert "requested=difficile" in caplog.text
        assert "coerced_to=moyen" in caplog.text


class TestAutoCompletePresets:
    """Tests pour auto_complete_presets()"""
    
    def test_completes_missing_difficulties(self):
        """Test que les difficultés manquantes sont ajoutées"""
        result = auto_complete_presets(["facile"], ["facile", "moyen", "difficile"])
        assert "facile" in result
        assert "moyen" in result
        assert "difficile" in result
        assert len(result) == 3
    
    def test_preserves_order(self):
        """Test que l'ordre canonique est préservé"""
        result = auto_complete_presets(["difficile", "facile"], ["facile", "moyen", "difficile"])
        assert result == ["facile", "moyen", "difficile"]
    
    def test_normalizes_before_completion(self):
        """Test que la normalisation est appliquée avant la complétion"""
        result = auto_complete_presets(["standard"], ["facile", "moyen", "difficile"])
        # "standard" → "moyen" (normalisé), puis complétion
        assert "facile" in result
        assert "moyen" in result
        assert "difficile" in result
    
    def test_handles_empty_list(self):
        """Test avec une liste vide"""
        result = auto_complete_presets([], ["facile", "moyen", "difficile"])
        assert len(result) == 3
        assert "facile" in result
        assert "moyen" in result
        assert "difficile" in result
    
    def test_deduplicates(self):
        """Test que les doublons sont supprimés"""
        result = auto_complete_presets(["facile", "facile", "moyen"], ["facile", "moyen", "difficile"])
        assert result.count("facile") == 1
        assert result.count("moyen") == 1
        assert result.count("difficile") == 1




