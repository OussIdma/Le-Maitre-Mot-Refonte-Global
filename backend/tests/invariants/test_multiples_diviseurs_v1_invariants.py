"""
Tests d'invariants - MULTIPLES_DIVISEURS_V1
===========================================

Ces tests verifient des proprietes mathematiques stables
qui ne doivent JAMAIS etre violees.

Invariants testes:
1. Les multiples sont corrects (multiple = n * k)
2. Les diviseurs sont corrects (n % d == 0)
3. La verification multiple/diviseur est correcte
4. Pas de placeholders {{ }} dans les variables
5. Reproductibilite: meme seed = memes variables
6. Pas de HTML dangereux (XSS)
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


def get_divisors(n: int) -> list:
    """Retourne la liste des diviseurs de n."""
    divisors = []
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            divisors.append(i)
            if i != n // i:
                divisors.append(n // i)
    return sorted(divisors)


class TestMultiplesDiviseursV1Invariants:
    """Tests d'invariants pour MULTIPLES_DIVISEURS_V1."""

    GENERATOR_KEY = "MULTIPLES_DIVISEURS_V1"
    NUM_SEEDS_TO_TEST = 30

    @pytest.fixture(autouse=True)
    def setup(self):
        """Import tardif pour eviter les problemes de chargement."""
        from backend.generators.factory import GeneratorFactory
        self.factory = GeneratorFactory

    # =========================================================================
    # INVARIANT 1: Les multiples sont corrects
    # =========================================================================

    def test_multiples_correctness(self):
        """
        Chaque multiple doit etre divisible par le nombre de base.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "multiples"},
                seed=seed
            )
            variables = result.get("variables", {})

            nombre = variables.get("nombre")
            multiples = variables.get("multiples", [])

            if nombre and multiples:
                for i, m in enumerate(multiples):
                    assert m % nombre == 0, (
                        f"seed={seed}: {m} n'est pas un multiple de {nombre}"
                    )
                    # Verifier que c'est le (i+1)eme multiple
                    assert m == nombre * (i + 1), (
                        f"seed={seed}: multiple #{i+1} devrait etre {nombre * (i + 1)}, "
                        f"obtenu: {m}"
                    )

    # =========================================================================
    # INVARIANT 2: Les diviseurs sont corrects
    # =========================================================================

    def test_divisors_correctness(self):
        """
        Chaque diviseur doit diviser exactement le nombre.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "diviseurs"},
                seed=seed
            )
            variables = result.get("variables", {})

            nombre = variables.get("nombre")
            diviseurs = variables.get("diviseurs", [])

            if nombre and diviseurs:
                # Tous les diviseurs donnes doivent etre corrects
                for d in diviseurs:
                    assert nombre % d == 0, (
                        f"seed={seed}: {d} ne divise pas {nombre}"
                    )

                # Tous les vrais diviseurs doivent etre presents
                expected_divisors = get_divisors(nombre)
                assert sorted(diviseurs) == expected_divisors, (
                    f"seed={seed}: diviseurs incomplets\n"
                    f"  attendu: {expected_divisors}\n"
                    f"  obtenu: {sorted(diviseurs)}"
                )

    # =========================================================================
    # INVARIANT 3: Verification multiple/diviseur correcte
    # =========================================================================

    def test_verification_correctness(self):
        """
        La verification multiple/diviseur doit etre mathematiquement correcte.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": "verifier"},
                seed=seed
            )
            variables = result.get("variables", {})

            nombre_a = variables.get("nombre_a")
            nombre_b = variables.get("nombre_b")
            operation = variables.get("operation")
            est_vrai = variables.get("est_vrai")

            if all(v is not None for v in [nombre_a, nombre_b, operation, est_vrai]):
                if operation == "multiple":
                    # a est-il multiple de b?
                    expected = (nombre_a % nombre_b == 0)
                else:  # diviseur
                    # a est-il diviseur de b?
                    expected = (nombre_b % nombre_a == 0)

                assert est_vrai == expected, (
                    f"seed={seed}: verification incorrecte\n"
                    f"  operation: {operation}\n"
                    f"  a={nombre_a}, b={nombre_b}\n"
                    f"  attendu: {expected}, obtenu: {est_vrai}"
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

    @pytest.mark.parametrize("exercise_type", ["multiples", "diviseurs", "verifier"])
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
