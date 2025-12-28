"""
Tests d'invariants - NOMBRES_ENTIERS_V1
=======================================

Ces tests verifient des proprietes mathematiques stables
qui ne doivent JAMAIS etre violees.

Invariants testes:
1. Les nombres generes sont dans les bornes specifiees
2. L'ordre des nombres est correct (comparaison, tri)
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


class TestNombresEntiersV1Invariants:
    """Tests d'invariants pour NOMBRES_ENTIERS_V1."""

    GENERATOR_KEY = "NOMBRES_ENTIERS_V1"
    NUM_SEEDS_TO_TEST = 30

    @pytest.fixture(autouse=True)
    def setup(self):
        """Import tardif pour eviter les problemes de chargement."""
        from backend.generators.factory import GeneratorFactory
        self.factory = GeneratorFactory

    # =========================================================================
    # INVARIANT 1: Les nombres sont dans les bornes
    # =========================================================================

    def test_numbers_within_bounds(self):
        """
        Les nombres generes doivent respecter max_value.
        """
        max_value = 1000
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"max_value": max_value, "exercise_type": "ecrire_lettres"},
                seed=seed
            )
            variables = result.get("variables", {})

            nombre = variables.get("nombre")
            if nombre is not None:
                assert 1 <= nombre <= max_value, (
                    f"seed={seed}: nombre={nombre} hors bornes [1, {max_value}]"
                )

    # =========================================================================
    # INVARIANT 2: L'ordre des nombres est correct
    # =========================================================================

    def test_comparison_correctness(self):
        """
        Pour les exercices de comparaison, le signe doit etre correct.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "comparer"},
                seed=seed
            )
            variables = result.get("variables", {})

            nombre_a = variables.get("nombre_a")
            nombre_b = variables.get("nombre_b")
            signe = variables.get("signe")

            if all(v is not None for v in [nombre_a, nombre_b, signe]):
                if signe == "<":
                    assert nombre_a < nombre_b, (
                        f"seed={seed}: {nombre_a} < {nombre_b} est faux"
                    )
                elif signe == ">":
                    assert nombre_a > nombre_b, (
                        f"seed={seed}: {nombre_a} > {nombre_b} est faux"
                    )
                elif signe == "=":
                    assert nombre_a == nombre_b, (
                        f"seed={seed}: {nombre_a} = {nombre_b} est faux"
                    )

    def test_ordering_correctness(self):
        """
        Pour les exercices d'ordre, la liste triee doit etre correcte.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "ranger"},
                seed=seed
            )
            variables = result.get("variables", {})

            nombres = variables.get("nombres", [])
            ordre = variables.get("ordre")
            nombres_tries = variables.get("nombres_tries", [])

            if nombres and nombres_tries:
                expected = sorted(nombres, reverse=(ordre == "decroissant"))
                assert nombres_tries == expected, (
                    f"seed={seed}: tri incorrect\n"
                    f"  nombres: {nombres}\n"
                    f"  attendu: {expected}\n"
                    f"  obtenu: {nombres_tries}"
                )

    # =========================================================================
    # INVARIANT 3: Pas de placeholders {{ }} non resolus
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
    # INVARIANT 4: Reproductibilite (meme seed = memes variables)
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
    # INVARIANT 5: Pas de HTML dangereux (XSS)
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
    # INVARIANT 6: Structure de sortie valide
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

        # Variables obligatoires
        assert "enonce" in variables, "Variable obligatoire manquante: enonce"
        assert "reponse_finale" in variables, "Variable obligatoire manquante: reponse_finale"

    # =========================================================================
    # INVARIANT 7: Tous les types d'exercices fonctionnent
    # =========================================================================

    @pytest.mark.parametrize("exercise_type", ["ecrire_lettres", "ecrire_chiffres", "comparer", "ranger"])
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
