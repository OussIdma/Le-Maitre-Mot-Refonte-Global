import pytest
from fastapi import HTTPException

from backend.services.tests_dyn_handler import format_dynamic_exercise


def _make_template():
    return {
        "id": 99,
        "offer": "free",
        "generator_key": "THALES_V1",
        "difficulty": "facile",
        "enonce_template_html": "<p>{{cote_initial}} → {{cote_final}} ({{figure_type_article}})</p>",
        "solution_template_html": "<p>{{cote_final}}</p>",
        "template_variants": None,
        "is_dynamic": True,
    }


def test_thales_alias_applied(monkeypatch):
    # Simule un générateur THALES qui ne fournit pas cote_initial/cote_final
    def fake_generate(*args, **kwargs):
        return {
            "variables": {
                "base_initiale": 5,
                "base_finale": 10,
                "figure_type_article": "un triangle",
                "coefficient_str": "x2",
                "transformation": "agrandissement",
                "transformation_verbe": "agrandi",
            },
            "results": {},
        }

    monkeypatch.setattr(
        "backend.generators.factory.GeneratorFactory.get",
        lambda key: True,
    )
    monkeypatch.setattr(
        "backend.generators.factory.GeneratorFactory.generate",
        lambda key, exercise_params=None, overrides=None, seed=None: fake_generate(),
    )

    exercise = format_dynamic_exercise(_make_template(), timestamp=1234567890, seed=42)

    assert "{{" not in exercise["enonce_html"]
    assert "{{" not in exercise["solution_html"]
    assert "5" in exercise["enonce_html"]
    assert "10" in exercise["enonce_html"]


def test_thales_alias_missing_raises(monkeypatch):
    # Générateur ne fournit aucune des clés mappables -> doit lever HTTPException explicite
    def fake_generate(*args, **kwargs):
        return {"variables": {}, "results": {}}

    monkeypatch.setattr(
        "backend.generators.factory.GeneratorFactory.get",
        lambda key: True,
    )
    monkeypatch.setattr(
        "backend.generators.factory.GeneratorFactory.generate",
        lambda key, exercise_params=None, overrides=None, seed=None: fake_generate(),
    )

    with pytest.raises(HTTPException) as exc:
        format_dynamic_exercise(_make_template(), timestamp=1234567890, seed=42)

    detail = exc.value.detail
    assert detail["error_code"] == "PLACEHOLDER_ALIAS_MISSING"
    assert "cote_initial" in detail["missing"] and "cote_final" in detail["missing"]
