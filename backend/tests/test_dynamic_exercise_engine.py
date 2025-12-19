import types

import pytest

from backend.services.dynamic_exercise_engine import choose_template_variant


def _make_variant(id: str, weight: int = 1):
    v = types.SimpleNamespace()
    v.id = id
    v.weight = weight
    v.enonce_template_html = f"énoncé {id}"
    v.solution_template_html = f"solution {id}"
    return v


def test_choose_template_variant_seed_random_is_deterministic():
    variants = [_make_variant("v1"), _make_variant("v2")]
    seed = 12345
    exercise_id = "6e_G07:1"

    first = choose_template_variant(variants, seed=seed, exercise_id=exercise_id)
    second = choose_template_variant(variants, seed=seed, exercise_id=exercise_id)

    assert first.id == second.id


def test_choose_template_variant_changes_with_seed():
    variants = [_make_variant("v1"), _make_variant("v2")]
    exercise_id = "6e_G07:1"

    v_a = choose_template_variant(variants, seed=1, exercise_id=exercise_id)
    v_b = choose_template_variant(variants, seed=2, exercise_id=exercise_id)

    # Pas une garantie absolue, mais très probable que le variant change
    # pour au moins une partie des seeds.
    assert {v_a.id, v_b.id} <= {"v1", "v2"}


def test_choose_template_variant_respects_weights():
    variants = [
        _make_variant("rare", weight=1),
        _make_variant("frequent", weight=10),
    ]
    exercise_id = "6e_G07:weights"

    # On échantillonne plusieurs seeds pour vérifier que "frequent" apparaît
    # beaucoup plus souvent que "rare".
    counts = {"rare": 0, "frequent": 0}
    for seed in range(0, 200):
        v = choose_template_variant(variants, seed=seed, exercise_id=exercise_id)
        counts[v.id] += 1

    assert counts["frequent"] > counts["rare"]


def test_choose_template_variant_fixed_mode_ok():
    variants = [
        _make_variant("v1", weight=1),
        _make_variant("v2", weight=10),
    ]

    v = choose_template_variant(
        variants,
        seed=123,
        exercise_id="6e_G07:fixed",
        mode="fixed",
        fixed_variant_id="v1",
    )

    assert v.id == "v1"


def test_choose_template_variant_fixed_mode_invalid_id_raises():
    variants = [_make_variant("v1"), _make_variant("v2")]

    with pytest.raises(ValueError):
        choose_template_variant(
            variants,
            seed=123,
            exercise_id="6e_G07:fixed",
            mode="fixed",
            fixed_variant_id="v3",
        )




