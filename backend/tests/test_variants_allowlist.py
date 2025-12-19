"""
Tests unitaires pour l'allowlist des template_variants (Phase A).

Vérifie :
- La fonction is_variants_allowed() (normalisation)
- L'enforcement dans format_dynamic_exercise() (erreur si chapitre non autorisé)
- Non-régression : 6e_TESTS_DYN fonctionne toujours
"""

import pytest
from fastapi import HTTPException
from backend.services.variants_config import is_variants_allowed, VARIANTS_ALLOWED_CHAPTERS
from backend.services.tests_dyn_handler import format_dynamic_exercise


def test_is_variants_allowed_normalization():
    """Test la normalisation (uppercase, trim) de is_variants_allowed()."""
    # Cas autorisé (pilote)
    assert is_variants_allowed("6E_TESTS_DYN") is True
    assert is_variants_allowed("6e_TESTS_DYN") is True
    assert is_variants_allowed(" 6E_TESTS_DYN ") is True
    assert is_variants_allowed("6e_tests_dyn") is True
    
    # Cas non autorisé
    assert is_variants_allowed("6E_G07") is False
    assert is_variants_allowed("6e_N08") is False
    assert is_variants_allowed("") is False
    assert is_variants_allowed(None) is False


def test_format_dynamic_exercise_variants_not_allowed():
    """
    Test réaliste : format_dynamic_exercise() lève HTTPException si :
    - template_variants non vide
    - chapitre non autorisé (6E_G07)
    
    Vérifie que l'erreur JSON contient bien error_code="VARIANTS_NOT_ALLOWED".
    """
    # Template réaliste avec variants mais chapitre non autorisé
    exercise_template = {
        "id": 42,
        "chapter_code": "6E_G07",  # Non autorisé
        "offer": "free",
        "difficulty": "moyen",
        "generator_key": "THALES_V1",
        "template_variants": [
            {
                "id": "v1",
                "enonce_template_html": "<p>Variant 1: {{cote_initial}}</p>",
                "solution_template_html": "<p>Sol 1: {{cote_final}}</p>",
                "weight": 1,
            }
        ],
    }
    
    timestamp = 1234567890
    
    # Doit lever HTTPException avec error_code VARIANTS_NOT_ALLOWED
    with pytest.raises(HTTPException) as exc_info:
        format_dynamic_exercise(exercise_template, timestamp, seed=42)
    
    # Vérification du statut HTTP
    assert exc_info.value.status_code == 422
    
    # Vérification du JSON d'erreur (structure complète)
    detail = exc_info.value.detail
    assert isinstance(detail, dict), "detail doit être un dict (JSON)"
    assert detail["error_code"] == "VARIANTS_NOT_ALLOWED", f"error_code attendu: VARIANTS_NOT_ALLOWED, reçu: {detail.get('error_code')}"
    assert detail["error"] == "variants_not_allowed"
    assert "6E_G07" in detail["message"]
    assert detail["chapter_code"] == "6E_G07"
    assert detail["exercise_template_id"] == 42
    assert "allowed_chapters" in detail
    assert isinstance(detail["allowed_chapters"], list)
    assert "6E_TESTS_DYN" in detail["allowed_chapters"]
    assert "hint" in detail


def test_format_dynamic_exercise_variants_allowed():
    """
    Test que format_dynamic_exercise() fonctionne si :
    - template_variants non vide
    - chapitre autorisé (6E_TESTS_DYN)
    """
    # Template avec variants et chapitre autorisé
    exercise_template = {
        "id": 1,
        "chapter_code": "6E_TESTS_DYN",  # Autorisé
        "offer": "free",
        "difficulty": "moyen",
        "generator_key": "THALES_V1",
        "template_variants": [
            {
                "id": "v1",
                "enonce_template_html": "<p>Variant 1: {{cote_initial}}</p>",
                "solution_template_html": "<p>Sol 1: {{cote_final}}</p>",
                "weight": 1,
            }
        ],
    }
    
    timestamp = 1234567890
    
    # Ne doit PAS lever d'exception (chapitre autorisé)
    # Note: peut lever UNRESOLVED_PLACEHOLDERS si générateur ne fournit pas les variables,
    # mais pas VARIANTS_NOT_ALLOWED
    try:
        result = format_dynamic_exercise(exercise_template, timestamp, seed=42)
        # Si on arrive ici, pas d'erreur VARIANTS_NOT_ALLOWED (OK)
        assert result is not None
    except HTTPException as e:
        # Acceptable si c'est UNRESOLVED_PLACEHOLDERS (générateur), mais pas VARIANTS_NOT_ALLOWED
        assert e.detail.get("error_code") != "VARIANTS_NOT_ALLOWED"


def test_format_dynamic_exercise_no_variants():
    """
    Test que format_dynamic_exercise() fonctionne si :
    - template_variants vide ou absent
    - chapitre non autorisé (mais pas de variants donc pas de vérification)
    """
    # Template sans variants (même si chapitre non autorisé, pas de vérification)
    exercise_template = {
        "id": 42,
        "chapter_code": "6E_G07",  # Non autorisé, mais pas de variants
        "offer": "free",
        "difficulty": "moyen",
        "generator_key": "THALES_V1",
        "enonce_template_html": "<p>Legacy template: {{cote_initial}}</p>",
        "solution_template_html": "<p>Legacy sol: {{cote_final}}</p>",
        "template_variants": [],  # Vide
    }
    
    timestamp = 1234567890
    
    # Ne doit PAS lever VARIANTS_NOT_ALLOWED (pas de variants)
    try:
        result = format_dynamic_exercise(exercise_template, timestamp, seed=42)
        # Si on arrive ici, pas d'erreur VARIANTS_NOT_ALLOWED (OK)
        assert result is not None
    except HTTPException as e:
        # Acceptable si c'est UNRESOLVED_PLACEHOLDERS (générateur), mais pas VARIANTS_NOT_ALLOWED
        assert e.detail.get("error_code") != "VARIANTS_NOT_ALLOWED"


def test_format_dynamic_exercise_missing_chapter_code():
    """
    Test que format_dynamic_exercise() lève HTTPException si :
    - template_variants non vide
    - chapter_code absent (ni dans exercise_template, ni dérivable depuis stable_key)
    """
    # Template avec variants mais sans chapter_code
    exercise_template = {
        "id": 42,
        # Pas de chapter_code
        "offer": "free",
        "difficulty": "moyen",
        "generator_key": "THALES_V1",
        "template_variants": [
            {
                "id": "v1",
                "enonce_template_html": "<p>Variant 1: {{cote_initial}}</p>",
                "solution_template_html": "<p>Sol 1: {{cote_final}}</p>",
                "weight": 1,
            }
        ],
        # stable_key sans format "{chapter_code}:{id}" (non dérivable)
        "stable_key": "invalid_format",
    }
    
    timestamp = 1234567890
    
    # Doit lever HTTPException avec error_code MISSING_CHAPTER_CODE_FOR_VARIANTS
    with pytest.raises(HTTPException) as exc_info:
        format_dynamic_exercise(exercise_template, timestamp, seed=42)
    
    assert exc_info.value.status_code == 422
    detail = exc_info.value.detail
    assert detail["error_code"] == "MISSING_CHAPTER_CODE_FOR_VARIANTS"
    assert detail["error"] == "missing_chapter_code_for_variants"
    assert "chapter_code" in detail["message"].lower()


def test_format_dynamic_exercise_chapter_code_from_stable_key():
    """
    Test que format_dynamic_exercise() dérive chapter_code depuis stable_key
    si absent dans exercise_template (format "{chapter_code}:{id}").
    """
    # Template avec variants, chapter_code absent mais stable_key dérivable
    exercise_template = {
        "id": 42,
        # Pas de chapter_code explicite
        "offer": "free",
        "difficulty": "moyen",
        "generator_key": "THALES_V1",
        "template_variants": [
            {
                "id": "v1",
                "enonce_template_html": "<p>Variant 1: {{cote_initial}}</p>",
                "solution_template_html": "<p>Sol 1: {{cote_final}}</p>",
                "weight": 1,
            }
        ],
        # stable_key avec format "{chapter_code}:{id}" → dérivable
        "stable_key": "6E_TESTS_DYN:42",
    }
    
    timestamp = 1234567890
    
    # Ne doit PAS lever MISSING_CHAPTER_CODE_FOR_VARIANTS
    # (chapter_code dérivé depuis stable_key = "6E_TESTS_DYN")
    # Ne doit PAS lever VARIANTS_NOT_ALLOWED (6E_TESTS_DYN autorisé)
    try:
        result = format_dynamic_exercise(exercise_template, timestamp, seed=42)
        # Si on arrive ici, pas d'erreur MISSING_CHAPTER_CODE ni VARIANTS_NOT_ALLOWED (OK)
        assert result is not None
    except HTTPException as e:
        # Acceptable si c'est UNRESOLVED_PLACEHOLDERS (générateur), mais pas les erreurs de chapter_code/variants
        assert e.detail.get("error_code") not in ["MISSING_CHAPTER_CODE_FOR_VARIANTS", "VARIANTS_NOT_ALLOWED"]


def test_allowlist_contains_tests_dyn():
    """Test que l'allowlist contient bien 6E_TESTS_DYN (pilote)."""
    assert "6E_TESTS_DYN" in VARIANTS_ALLOWED_CHAPTERS
    assert len(VARIANTS_ALLOWED_CHAPTERS) >= 1  # Au moins le pilote

