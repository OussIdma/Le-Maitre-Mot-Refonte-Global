import re
from copy import deepcopy

import pytest

from backend.data.tests_dyn_exercises import get_tests_dyn_exercises
from backend.services.tests_dyn_handler import format_dynamic_exercise


def _inject_variants(exercise_template, label_suffix_1="V1", label_suffix_2="V2"):
    """
    Crée deux variants à partir du template existant en modifiant légèrement le texte,
    sans toucher aux placeholders.
    """
    base_enonce = exercise_template["enonce_template_html"]
    base_solution = exercise_template["solution_template_html"]

    v1_enonce = base_enonce.replace("<p><strong", f"<p><strong ({label_suffix_1})", 1)
    v2_enonce = base_enonce.replace("<p><strong", f"<p><strong ({label_suffix_2})", 1)

    return [
        {
            "id": "v1",
            "enonce_template_html": v1_enonce,
            "solution_template_html": base_solution,
            "weight": 1,
        },
        {
            "id": "v2",
            "enonce_template_html": v2_enonce,
            "solution_template_html": base_solution,
            "weight": 10,
        },
    ]


def test_tests_dyn_variant_selection_is_deterministic_for_seed():
    # On part du premier exercice TESTS_DYN en "facile"
    base_ex = get_tests_dyn_exercises(offer="free", difficulty="facile")[0]
    ex = deepcopy(base_ex)
    ex["template_variants"] = _inject_variants(ex)

    seed = 42
    timestamp = 1700000000

    ex1 = format_dynamic_exercise(ex, timestamp=timestamp, seed=seed)
    ex2 = format_dynamic_exercise(ex, timestamp=timestamp, seed=seed)

    assert ex1["enonce_html"] == ex2["enonce_html"]
    assert "{{" not in ex1["enonce_html"]


def test_tests_dyn_variant_distribution_with_weights():
    base_ex = get_tests_dyn_exercises(offer="free", difficulty="facile")[0]
    ex = deepcopy(base_ex)
    ex["template_variants"] = _inject_variants(ex, label_suffix_1="RARE", label_suffix_2="FREQUENT")

    timestamp = 1700000000
    counts = {"RARE": 0, "FREQUENT": 0}

    for seed in range(0, 100):
        rendered = format_dynamic_exercise(ex, timestamp=timestamp, seed=seed)
        enonce_html = rendered["enonce_html"]
        if "RARE" in enonce_html:
            counts["RARE"] += 1
        if "FREQUENT" in enonce_html:
            counts["FREQUENT"] += 1

    # Le variant "FREQUENT" (weight=10) doit apparaître plus souvent que "RARE" (weight=1)
    assert counts["FREQUENT"] > counts["RARE"]


def test_tests_dyn_no_unresolved_placeholders_with_variants():
    base_ex = get_tests_dyn_exercises(offer="free", difficulty="facile")[0]
    ex = deepcopy(base_ex)
    ex["template_variants"] = _inject_variants(ex)

    timestamp = 1700000000
    rendered = format_dynamic_exercise(ex, timestamp=timestamp, seed=123)

    assert "{{" not in rendered["enonce_html"]
    assert "{{" not in rendered["solution_html"]


