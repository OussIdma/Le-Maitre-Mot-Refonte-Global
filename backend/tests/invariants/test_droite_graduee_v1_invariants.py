"""
Tests d'invariants - DROITE_GRADUEE_V1
======================================

Ces tests verifient des proprietes mathematiques stables
qui ne doivent JAMAIS etre violees.

Invariants testes:
1. Les graduations sont regulierement espacees
2. L'encadrement est correct (borne_inf < nombre < borne_sup)
3. Pas de placeholders {{ }} dans les variables
4. Reproductibilite: meme seed = memes variables
5. Pas de HTML dangereux (XSS)
"""

import re
import pytest
from typing import Any


# Patterns de detection
PLACEHOLDER_PATTERN = re.compile(r'\{\{[^}]+\}\}')
DANGEROUS_HTML_PATTERN = re.compile(
    r'<\s*script|javascript\s*:|onerror\s*=|onload\s*=',
    re.IGNORECASE
)


def check_no_placeholders_recursive(obj: Any, path: str = "") -> list:
    """Verifie recursivement qu'aucun placeholder {{ }} n'est present."""
    found = []
    if isinstance(obj, str):
        if PLACEHOLDER_PATTERN.search(obj):
            found.append(f"{path}: '{obj[:50]}...'")
    elif isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}" if path else key
            found.extend(check_no_placeholders_recursive(value, child_path))
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            child_path = f"{path}[{i}]"
            found.extend(check_no_placeholders_recursive(item, child_path))
    return found


def check_no_dangerous_html_recursive(obj: Any, path: str = "") -> list:
    """Verifie recursivement qu'aucun HTML dangereux n'est present."""
    found = []
    if isinstance(obj, str):
        if DANGEROUS_HTML_PATTERN.search(obj):
            found.append(f"{path}: pattern dangereux detecte")
    elif isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}" if path else key
            found.extend(check_no_dangerous_html_recursive(value, child_path))
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            child_path = f"{path}[{i}]"
            found.extend(check_no_dangerous_html_recursive(item, child_path))
    return found


class TestDroiteGradueeV1Invariants:
    """Tests d'invariants pour DROITE_GRADUEE_V1."""

    GENERATOR_KEY = "DROITE_GRADUEE_V1"
    NUM_SEEDS_TO_TEST = 30

    @pytest.fixture(autouse=True)
    def setup(self):
        """Import tardif pour eviter les problemes de chargement."""
        from backend.generators.factory import GeneratorFactory
        self.factory = GeneratorFactory

    # =========================================================================
    # INVARIANT 1: Graduations regulierement espacees
    # =========================================================================

    def test_graduations_regular_spacing(self):
        """
        Les graduations doivent etre regulierement espacees.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "lire"},
                seed=seed
            )
            variables = result.get("variables", {})

            graduations = variables.get("graduations", [])
            step = variables.get("step")

            if len(graduations) >= 2 and step is not None:
                for i in range(1, len(graduations)):
                    diff = graduations[i] - graduations[i - 1]
                    assert diff == step, (
                        f"seed={seed}: espacement irregulier\n"
                        f"  graduations[{i}] - graduations[{i-1}] = {diff} != {step}"
                    )

    # =========================================================================
    # INVARIANT 2: Encadrement correct
    # =========================================================================

    def test_encadrement_correctness(self):
        """
        Pour les exercices d'encadrement: borne_inf < nombre < borne_sup.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "encadrer"},
                seed=seed
            )
            variables = result.get("variables", {})

            nombre = variables.get("nombre")
            borne_inf = variables.get("borne_inf")
            borne_sup = variables.get("borne_sup")

            if all(v is not None for v in [nombre, borne_inf, borne_sup]):
                assert borne_inf < nombre < borne_sup, (
                    f"seed={seed}: encadrement incorrect\n"
                    f"  {borne_inf} < {nombre} < {borne_sup} est faux"
                )

                # Les bornes doivent etre des entiers consecutifs
                assert borne_sup == borne_inf + 1, (
                    f"seed={seed}: bornes non consecutives\n"
                    f"  {borne_inf} et {borne_sup}"
                )

    # =========================================================================
    # INVARIANT 3: Nombre sur droite dans les graduations
    # =========================================================================

    def test_number_within_graduations(self):
        """
        Le nombre a lire/placer doit etre dans la plage des graduations.
        """
        for exercise_type in ["lire", "placer"]:
            for seed in range(self.NUM_SEEDS_TO_TEST):
                result = self.factory.generate(
                    key=self.GENERATOR_KEY,
                    overrides={"exercise_type": exercise_type},
                    seed=seed
                )
                variables = result.get("variables", {})

                nombre = variables.get("nombre")
                graduations = variables.get("graduations", [])

                if nombre is not None and len(graduations) >= 2:
                    min_grad = min(graduations)
                    max_grad = max(graduations)
                    assert min_grad <= nombre <= max_grad, (
                        f"seed={seed}, type={exercise_type}: "
                        f"nombre={nombre} hors graduations [{min_grad}, {max_grad}]"
                    )

    # =========================================================================
    # INVARIANT 4: Pas de placeholders {{ }} non resolus
    # =========================================================================

    def test_no_unresolved_placeholders(self):
        """
        Aucun placeholder {{ }} ne doit rester dans les variables.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            variables = result.get("variables", {})

            placeholders = check_no_placeholders_recursive(variables, "variables")
            assert len(placeholders) == 0, (
                f"seed={seed}: placeholders non resolus trouves:\n"
                + "\n".join(placeholders[:5])
            )

    # =========================================================================
    # INVARIANT 5: Reproductibilite (meme seed = memes variables)
    # =========================================================================

    def test_reproducibility_same_seed_same_result(self):
        """
        Avec la meme seed et les memes parametres, le resultat doit etre identique.
        """
        test_seeds = [0, 42, 123, 999]

        for seed in test_seeds:
            result1 = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            result2 = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )

            vars1 = result1.get("variables", {})
            vars2 = result2.get("variables", {})

            assert vars1 == vars2, (
                f"seed={seed}: resultats differents:\n"
                f"  1: {vars1}\n"
                f"  2: {vars2}"
            )

    # =========================================================================
    # INVARIANT 6: Pas de HTML dangereux (XSS)
    # =========================================================================

    def test_no_dangerous_html_in_variables(self):
        """
        Les variables string ne doivent pas contenir de HTML dangereux.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            variables = result.get("variables", {})

            dangerous = check_no_dangerous_html_recursive(variables, "variables")
            assert len(dangerous) == 0, (
                f"seed={seed}: HTML dangereux detecte:\n"
                + "\n".join(dangerous[:5])
            )

    # =========================================================================
    # INVARIANT 7: Structure de sortie valide
    # =========================================================================

    def test_output_structure(self):
        """
        Le output doit contenir les cles obligatoires.
        """
        result = self.factory.generate(
            key=self.GENERATOR_KEY,
            overrides={},
            seed=42
        )

        assert "variables" in result, "Le output doit contenir 'variables'"
        variables = result["variables"]

        assert "enonce" in variables, "Variable obligatoire manquante: enonce"
        assert "reponse_finale" in variables, "Variable obligatoire manquante: reponse_finale"

    # =========================================================================
    # INVARIANT 8: Tous les types d'exercices fonctionnent
    # =========================================================================

    @pytest.mark.parametrize("exercise_type", ["lire", "placer", "encadrer"])
    def test_all_exercise_types_work(self, exercise_type):
        """
        Tous les types d'exercices doivent produire des resultats valides.
        """
        for seed in range(10):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": exercise_type},
                seed=seed
            )
            variables = result.get("variables", {})

            assert "enonce" in variables, (
                f"exercise_type={exercise_type}, seed={seed}: "
                "enonce manquant"
            )
            assert "reponse_finale" in variables, (
                f"exercise_type={exercise_type}, seed={seed}: "
                "reponse_finale manquante"
            )
