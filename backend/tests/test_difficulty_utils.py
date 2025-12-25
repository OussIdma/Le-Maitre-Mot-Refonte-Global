"""
Tests pour le helper normalize_difficulty() (P4.B)
"""

import pytest
from backend.utils.difficulty_utils import (
    normalize_difficulty,
    is_canonical_difficulty,
    get_all_canonical_difficulties,
)


class TestNormalizeDifficulty:
    """Tests pour normalize_difficulty()"""
    
    def test_standard_to_moyen(self):
        """Test que 'standard' est mappé vers 'moyen'"""
        assert normalize_difficulty("standard") == "moyen"
        assert normalize_difficulty("STANDARD") == "moyen"
        assert normalize_difficulty("  standard  ") == "moyen"
    
    def test_canonical_difficulties(self):
        """Test que les difficultés canoniques restent inchangées"""
        assert normalize_difficulty("facile") == "facile"
        assert normalize_difficulty("moyen") == "moyen"
        assert normalize_difficulty("difficile") == "difficile"
        assert normalize_difficulty("FACILE") == "facile"
        assert normalize_difficulty("MOYEN") == "moyen"
        assert normalize_difficulty("DIFFICILE") == "difficile"
    
    def test_empty_string_defaults_to_moyen(self):
        """Test que la chaîne vide retourne 'moyen' par défaut"""
        assert normalize_difficulty("") == "moyen"
    
    def test_invalid_difficulty_raises_error(self):
        """Test qu'une difficulté invalide lève une ValueError"""
        with pytest.raises(ValueError, match="Difficulté non reconnue"):
            normalize_difficulty("invalid")
        
        with pytest.raises(ValueError, match="Difficulté non reconnue"):
            normalize_difficulty("hard")


class TestIsCanonicalDifficulty:
    """Tests pour is_canonical_difficulty()"""
    
    def test_canonical_difficulties(self):
        """Test que les difficultés canoniques sont reconnues"""
        assert is_canonical_difficulty("facile") is True
        assert is_canonical_difficulty("moyen") is True
        assert is_canonical_difficulty("difficile") is True
    
    def test_non_canonical_difficulties(self):
        """Test que les difficultés non canoniques ne sont pas reconnues"""
        assert is_canonical_difficulty("standard") is False
        assert is_canonical_difficulty("invalid") is False
        assert is_canonical_difficulty("") is False


class TestGetAllCanonicalDifficulties:
    """Tests pour get_all_canonical_difficulties()"""
    
    def test_returns_all_canonical(self):
        """Test que toutes les difficultés canoniques sont retournées"""
        difficulties = get_all_canonical_difficulties()
        assert len(difficulties) == 3
        assert "facile" in difficulties
        assert "moyen" in difficulties
        assert "difficile" in difficulties
    
    def test_returns_copy(self):
        """Test que c'est une copie (modification ne change pas l'original)"""
        difficulties1 = get_all_canonical_difficulties()
        difficulties2 = get_all_canonical_difficulties()
        
        difficulties1.append("test")
        assert "test" not in difficulties2




