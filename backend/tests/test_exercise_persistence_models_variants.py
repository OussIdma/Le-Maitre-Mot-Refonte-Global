import asyncio
import pytest
from pydantic import ValidationError

from backend.services.exercise_persistence_service import (
    ExerciseCreateRequest,
    TemplateVariant,
    ExercisePersistenceService,
    ExerciseUpdateRequest,
)


def test_static_exercise_requires_enonce_and_solution():
    with pytest.raises(ValidationError):
        ExerciseCreateRequest(
            family="CONVERSION",
            exercise_type=None,
            difficulty="facile",
            offer="free",
            is_dynamic=False,
            enonce_html="",
            solution_html="",
        )


def test_dynamic_legacy_templates_only_is_valid():
    req = ExerciseCreateRequest(
        family="GEOMETRIE",
        exercise_type="THALES",
        difficulty="moyen",
        offer="free",
        is_dynamic=True,
        generator_key="THALES_V1",
        enonce_template_html="<div>{{a}}</div>",
        solution_template_html="<div>{{b}}</div>",
    )
    # La simple construction ne doit pas lever
    assert req.is_dynamic is True
    assert req.template_variants is None


def test_dynamic_with_variants_only_is_valid():
    variant = TemplateVariant(
        id="v1",
        enonce_template_html="<div>{{a}}</div>",
        solution_template_html="<div>{{b}}</div>",
    )
    req = ExerciseCreateRequest(
        family="GEOMETRIE",
        exercise_type="THALES",
        difficulty="moyen",
        offer="free",
        is_dynamic=True,
        generator_key="THALES_V1",
        enonce_template_html=None,
        solution_template_html=None,
        template_variants=[variant],
    )
    assert req.template_variants is not None
    assert len(req.template_variants) == 1


def test_dynamic_without_any_template_fails_in_service_validator():
    """
    La validation métier finale est effectuée dans ExercisePersistenceService._validate_exercise_data.
    On vérifie qu'elle lève si aucun template n'est fourni (ni legacy, ni variants).
    """

    # Construction Pydantic OK (les champs sont optionnels),
    # mais la validation métier doit refuser la requête.
    req = ExerciseCreateRequest(
        family="GEOMETRIE",
        exercise_type="THALES",
        difficulty="moyen",
        offer="free",
        is_dynamic=True,
        generator_key="THALES_V1",
        enonce_template_html=None,
        solution_template_html=None,
        template_variants=None,
    )

    # On instancie le service sans exécuter __init__ (db non utilisée par le validateur)
    service = ExercisePersistenceService.__new__(ExercisePersistenceService)

    with pytest.raises(ValueError):
        service._validate_exercise_data(req)


def test_update_persists_template_variants():
    """
    Vérifie que update_exercise écrit bien template_variants et les champs dynamiques.
    """

    class FakeCollection:
        def __init__(self, doc):
            self.doc = doc

        async def find_one(self, filter, projection=None):
            if (
                filter.get("id") == self.doc.get("id")
                and filter.get("chapter_code") == self.doc.get("chapter_code")
            ):
                return dict(self.doc)
            return None

        async def update_one(self, filter, update):
            if (
                filter.get("id") == self.doc.get("id")
                and filter.get("chapter_code") == self.doc.get("chapter_code")
            ):
                updates = update.get("$set", {})
                self.doc.update(updates)

    async def noop(*args, **kwargs):
        return None

    # Document initial sans template_variants
    initial_doc = {
        "chapter_code": "6E_TESTS_DYN",
        "id": 42,
        "family": "CONVERSION",
        "exercise_type": "THALES",
        "difficulty": "difficile",
        "offer": "free",
        "enonce_html": "",
        "solution_html": "",
        "needs_svg": True,
        "is_dynamic": True,
        "generator_key": "THALES_V1",
        "enonce_template_html": "<p>Legacy</p>",
        "solution_template_html": "<p>Legacy sol</p>",
        "template_variants": None,
    }

    service = ExercisePersistenceService.__new__(ExercisePersistenceService)
    service.collection = FakeCollection(initial_doc)
    service.initialize_chapter = noop
    service._sync_to_python_file = noop
    service._reload_handler = noop

    update_request = ExerciseUpdateRequest(
        family="conversion",
        exercise_type="thales",
        difficulty="difficile",
        offer="free",
        enonce_html="",
        solution_html="",
        needs_svg=True,
        is_dynamic=True,
        generator_key="THALES_V1",
        enonce_template_html="<p>V1</p>",
        solution_template_html="<p>S1</p>",
        template_variants=[
            TemplateVariant(
                id="v1",
                enonce_template_html="<p>Variant 1</p>",
                solution_template_html="<p>Sol 1</p>",
                weight=1,
            )
        ],
    )

    updated = asyncio.run(
        service.update_exercise("6e_tests_dyn", 42, update_request)
    )

    assert updated["template_variants"] is not None
    assert len(updated["template_variants"]) == 1
    assert updated["template_variants"][0]["id"] == "v1"
    assert updated["enonce_template_html"] == "<p>V1</p>"
    assert updated["solution_template_html"] == "<p>S1</p>"
    assert updated["is_dynamic"] is True
    assert updated["generator_key"] == "THALES_V1"

