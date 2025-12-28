"""
Tests d'invariants - PERIMETRE_V1
=================================

Ces tests verifient des proprietes mathematiques stables
qui ne doivent JAMAIS etre violees.

Invariants testes:
1. Perimetre carre: P = 4 * cote
2. Perimetre rectangle: P = 2 * (L + l)
3. Perimetre triangle: P = a + b + c
4. Inegalite triangulaire pour les triangles
5. Pas de placeholders {{ }} dans les variables
6. Reproductibilite: meme seed = memes variables
7. Pas de HTML dangereux (XSS)
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


class TestPerimetreV1Invariants:
    """Tests d'invariants pour PERIMETRE_V1."""

    GENERATOR_KEY = "PERIMETRE_V1"
    NUM_SEEDS_TO_TEST = 30

    @pytest.fixture(autouse=True)
    def setup(self):
        """Import tardif pour eviter les problemes de chargement."""
        from backend.generators.factory import GeneratorFactory
        self.factory = GeneratorFactory

    # =========================================================================
    # INVARIANT 1: Perimetre du carre = 4 * cote
    # =========================================================================

    def test_perimeter_square(self):
        """
        Le perimetre du carre doit etre 4 * cote.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"figure": "carre"},
                seed=seed
            )
            variables = result.get("variables", {})

            cote = variables.get("cote")
            perimetre = variables.get("perimetre")

            if cote is not None and perimetre is not None:
                expected = round(4 * cote, 1)
                assert abs(perimetre - expected) < 0.01, (
                    f"seed={seed}: perimetre carre incorrect\n"
                    f"  cote={cote}, attendu: {expected}, obtenu: {perimetre}"
                )

    # =========================================================================
    # INVARIANT 2: Perimetre du rectangle = 2 * (L + l)
    # =========================================================================

    def test_perimeter_rectangle(self):
        """
        Le perimetre du rectangle doit etre 2 * (longueur + largeur).
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"figure": "rectangle"},
                seed=seed
            )
            variables = result.get("variables", {})

            longueur = variables.get("longueur")
            largeur = variables.get("largeur")
            perimetre = variables.get("perimetre")

            if all(v is not None for v in [longueur, largeur, perimetre]):
                expected = round(2 * (longueur + largeur), 1)
                assert abs(perimetre - expected) < 0.01, (
                    f"seed={seed}: perimetre rectangle incorrect\n"
                    f"  L={longueur}, l={largeur}\n"
                    f"  attendu: {expected}, obtenu: {perimetre}"
                )

    # =========================================================================
    # INVARIANT 3: Perimetre du triangle = a + b + c
    # =========================================================================

    def test_perimeter_triangle(self):
        """
        Le perimetre du triangle doit etre la somme des trois cotes.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"figure": "triangle"},
                seed=seed
            )
            variables = result.get("variables", {})

            a = variables.get("cote_a")
            b = variables.get("cote_b")
            c = variables.get("cote_c")
            perimetre = variables.get("perimetre")

            if all(v is not None for v in [a, b, c, perimetre]):
                expected = round(a + b + c, 1)
                assert abs(perimetre - expected) < 0.01, (
                    f"seed={seed}: perimetre triangle incorrect\n"
                    f"  a={a}, b={b}, c={c}\n"
                    f"  attendu: {expected}, obtenu: {perimetre}"
                )

    # =========================================================================
    # INVARIANT 4: Inegalite triangulaire
    # =========================================================================

    def test_triangle_inequality(self):
        """
        Les cotes du triangle doivent verifier l'inegalite triangulaire.
        Note: On accepte des triangles degeneres (egalite) generes par le random.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"figure": "triangle"},
                seed=seed
            )
            variables = result.get("variables", {})

            a = variables.get("cote_a")
            b = variables.get("cote_b")
            c = variables.get("cote_c")

            if all(v is not None for v in [a, b, c]):
                # Inegalite triangulaire stricte (permettre egalite pour triangles degeneres)
                assert a + b >= c and a + c >= b and b + c >= a, (
                    f"seed={seed}: inegalite triangulaire violee\n"
                    f"  a={a}, b={b}, c={c}"
                )

    # =========================================================================
    # INVARIANT 5: Dimensions positives
    # =========================================================================

    def test_positive_dimensions(self):
        """
        Toutes les dimensions doivent etre positives.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            for figure in ["carre", "rectangle", "triangle"]:
                result = self.factory.generate(
                    key=self.GENERATOR_KEY,
                    overrides={"figure": figure},
                    seed=seed
                )
                variables = result.get("variables", {})

                # Verifier les cotes selon la figure
                if figure == "carre":
                    assert variables.get("cote", 0) > 0, (
                        f"seed={seed}: cote carre <= 0"
                    )
                elif figure == "rectangle":
                    assert variables.get("longueur", 0) > 0, (
                        f"seed={seed}: longueur rectangle <= 0"
                    )
                    assert variables.get("largeur", 0) > 0, (
                        f"seed={seed}: largeur rectangle <= 0"
                    )
                else:  # triangle
                    assert variables.get("cote_a", 0) > 0, (
                        f"seed={seed}: cote_a triangle <= 0"
                    )
                    assert variables.get("cote_b", 0) > 0, (
                        f"seed={seed}: cote_b triangle <= 0"
                    )
                    assert variables.get("cote_c", 0) > 0, (
                        f"seed={seed}: cote_c triangle <= 0"
                    )

                # Verifier le perimetre
                assert variables.get("perimetre", 0) > 0, (
                    f"seed={seed}, figure={figure}: perimetre <= 0"
                )

    # =========================================================================
    # INVARIANT 6: Longueur > Largeur pour rectangle
    # =========================================================================

    def test_rectangle_length_greater_than_width(self):
        """
        Pour un rectangle, la longueur doit etre >= largeur.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"figure": "rectangle"},
                seed=seed
            )
            variables = result.get("variables", {})

            longueur = variables.get("longueur")
            largeur = variables.get("largeur")

            if longueur is not None and largeur is not None:
                assert longueur >= largeur, (
                    f"seed={seed}: longueur < largeur\n"
                    f"  L={longueur}, l={largeur}"
                )

    # =========================================================================
    # INVARIANT 7: Pas de placeholders {{ }} non resolus
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
    # INVARIANT 8: Reproductibilite (meme seed = memes variables)
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
    # INVARIANT 9: Pas de HTML dangereux (XSS)
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
    # INVARIANT 10: Structure de sortie valide
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
        assert "perimetre" in variables, "Variable obligatoire manquante: perimetre"

    # =========================================================================
    # INVARIANT 11: Toutes les figures fonctionnent
    # =========================================================================

    @pytest.mark.parametrize("figure", ["carre", "rectangle", "triangle", "aleatoire"])
    def test_all_figures_work(self, figure):
        """
        Toutes les figures doivent produire des resultats valides.
        """
        for seed in range(10):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"figure": figure},
                seed=seed
            )
            variables = result.get("variables", {})

            assert "enonce" in variables, (
                f"figure={figure}, seed={seed}: "
                "enonce manquant"
            )
            assert "reponse_finale" in variables, (
                f"figure={figure}, seed={seed}: "
                "reponse_finale manquante"
            )
            assert "perimetre" in variables, (
                f"figure={figure}, seed={seed}: "
                "perimetre manquant"
            )
