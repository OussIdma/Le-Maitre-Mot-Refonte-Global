"""
Tests unitaires pour la détection automatique template-based (Phase Finale).

Vérifie :
- La fonction is_chapter_template_based() (détection automatique)
- L'enforcement dans format_dynamic_exercise() (erreur si chapitre spec-based)
- Non-régression : 6e_TESTS_DYN fonctionne toujours
- Exclusion explicite : GM07/GM08
"""

import pytest
from fastapi import HTTPException
from backend.services.variants_config import is_chapter_template_based, EXCLUDED_CHAPTERS
from backend.services.tests_dyn_handler import format_dynamic_exercise


def test_is_chapter_template_based_handler():
    """Test la détection via handler dédié (tests_dyn_handler)."""
    # Cas template-based (handler dédié)
    assert is_chapter_template_based("6E_TESTS_DYN") is True
    assert is_chapter_template_based("6e_TESTS_DYN") is True
    assert is_chapter_template_based(" 6E_TESTS_DYN ") is True
    assert is_chapter_template_based("6e_tests_dyn") is True


def test_is_chapter_template_based_exercise_template():
    """Test la détection via exercise_template (is_dynamic + generator_key + enonce_template_html)."""
    # Cas template-based (exercice dynamique avec templates)
    template = {
        "is_dynamic": True,
        "generator_key": "THALES_V1",
        "enonce_template_html": "<p>{{var}}</p>"
    }
    assert is_chapter_template_based("6E_G07", template) is True
    
    # Cas spec-based (pas de templates)
    template_no_html = {
        "is_dynamic": True,
        "generator_key": "THALES_V1",
        # Pas de enonce_template_html
    }
    assert is_chapter_template_based("6E_G07", template_no_html) is False


def test_is_chapter_template_based_excluded():
    """Test l'exclusion explicite GM07/GM08."""
    # Exclusion explicite
    assert is_chapter_template_based("6E_GM07") is False
    assert is_chapter_template_based("6e_GM08") is False
    assert "6E_GM07" in EXCLUDED_CHAPTERS
    assert "6E_GM08" in EXCLUDED_CHAPTERS


def test_is_chapter_template_based_spec_based():
    """Test que les chapitres spec-based sont détectés comme incompatibles."""
    # Cas spec-based (pas de handler, pas de template)
    assert is_chapter_template_based("6E_G07") is False
    assert is_chapter_template_based("6e_N08") is False
    assert is_chapter_template_based("") is False
    assert is_chapter_template_based(None) is False


def test_format_dynamic_exercise_variants_not_supported():
    """
    Test réaliste : format_dynamic_exercise() lève HTTPException si :
    - template_variants non vide
    - chapitre spec-based (6E_G07, pas de handler dédié, pas de template dans exercise_template)
    
    Vérifie que l'erreur JSON contient bien error_code="VARIANTS_NOT_SUPPORTED".
    """
    # Template réaliste avec variants mais chapitre spec-based
    exercise_template = {
        "id": 42,
        "chapter_code": "6E_G07",  # Spec-based (pas de handler dédié)
        "offer": "free",
        "difficulty": "moyen",
        "generator_key": "THALES_V1",
        # Pas de enonce_template_html → pas template-based
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
    
    # Doit lever HTTPException avec error_code VARIANTS_NOT_SUPPORTED
    with pytest.raises(HTTPException) as exc_info:
        format_dynamic_exercise(exercise_template, timestamp, seed=42)
    
    # Vérification du statut HTTP
    assert exc_info.value.status_code == 422
    
    # Vérification du JSON d'erreur (structure complète)
    detail = exc_info.value.detail
    assert isinstance(detail, dict), "detail doit être un dict (JSON)"
    assert detail["error_code"] == "VARIANTS_NOT_SUPPORTED", f"error_code attendu: VARIANTS_NOT_SUPPORTED, reçu: {detail.get('error_code')}"
    assert detail["error"] == "variants_not_supported"
    assert "6E_G07" in detail["message"]
    assert "spec-based" in detail["message"].lower()
    assert detail["chapter_code"] == "6E_G07"
    assert detail["exercise_template_id"] == 42
    assert "hint" in detail


def test_format_dynamic_exercise_variants_supported():
    """
    Test que format_dynamic_exercise() fonctionne si :
    - template_variants non vide
    - chapitre template-based (6E_TESTS_DYN, handler dédié)
    """
    # Template avec variants et chapitre template-based
    exercise_template = {
        "id": 1,
        "chapter_code": "6E_TESTS_DYN",  # Template-based (handler dédié)
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
    
    # Ne doit PAS lever d'exception (chapitre template-based)
    # Note: peut lever UNRESOLVED_PLACEHOLDERS si générateur ne fournit pas les variables,
    # mais pas VARIANTS_NOT_SUPPORTED
    try:
        result = format_dynamic_exercise(exercise_template, timestamp, seed=42)
        # Si on arrive ici, pas d'erreur VARIANTS_NOT_SUPPORTED (OK)
        assert result is not None
    except HTTPException as e:
        # Acceptable si c'est UNRESOLVED_PLACEHOLDERS (générateur), mais pas VARIANTS_NOT_SUPPORTED
        assert e.detail.get("error_code") != "VARIANTS_NOT_SUPPORTED"


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
    
    # Ne doit PAS lever VARIANTS_NOT_SUPPORTED (pas de variants)
    try:
        result = format_dynamic_exercise(exercise_template, timestamp, seed=42)
        # Si on arrive ici, pas d'erreur VARIANTS_NOT_SUPPORTED (OK)
        assert result is not None
    except HTTPException as e:
        # Acceptable si c'est UNRESOLVED_PLACEHOLDERS (générateur), mais pas VARIANTS_NOT_SUPPORTED
        assert e.detail.get("error_code") != "VARIANTS_NOT_SUPPORTED"


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
    # Ne doit PAS lever VARIANTS_NOT_SUPPORTED (6E_TESTS_DYN template-based)
    try:
        result = format_dynamic_exercise(exercise_template, timestamp, seed=42)
        # Si on arrive ici, pas d'erreur MISSING_CHAPTER_CODE ni VARIANTS_NOT_SUPPORTED (OK)
        assert result is not None
    except HTTPException as e:
        # Acceptable si c'est UNRESOLVED_PLACEHOLDERS (générateur), mais pas les erreurs de chapter_code/variants
        assert e.detail.get("error_code") not in ["MISSING_CHAPTER_CODE_FOR_VARIANTS", "VARIANTS_NOT_SUPPORTED"]


def test_excluded_chapters():
    """Test que les chapitres exclus (GM07/GM08) sont bien dans EXCLUDED_CHAPTERS."""
    assert "6E_GM07" in EXCLUDED_CHAPTERS
    assert "6E_GM08" in EXCLUDED_CHAPTERS
    assert len(EXCLUDED_CHAPTERS) >= 2

