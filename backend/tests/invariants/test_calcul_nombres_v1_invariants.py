"""
Tests d'invariants - CALCUL_NOMBRES_V1
======================================

Ces tests vérifient des propriétés stables et mathématiquement correctes
qui ne doivent JAMAIS être violées, indépendamment des variations d'énoncé.

Invariants testés:
1. La reponse_finale doit être un nombre valide
2. Pas de placeholders {{ }} dans les variables
3. Reproductibilité: même seed = mêmes variables
4. Pas de HTML dangereux (XSS)
"""

import re
import math
import pytest
from typing import Dict, Any


# Patterns de détection
PLACEHOLDER_PATTERN = re.compile(r'\{\{[^}]+\}\}')
DANGEROUS_HTML_PATTERN = re.compile(
    r'<\s*script|javascript\s*:|onerror\s*=|onload\s*=',
    re.IGNORECASE
)


def check_no_placeholders_recursive(obj: Any, path: str = "") -> list:
    """Vérifie récursivement qu'aucun placeholder {{ }} n'est présent."""
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
    """Vérifie récursivement qu'aucun HTML dangereux n'est présent."""
    found = []
    if isinstance(obj, str):
        if DANGEROUS_HTML_PATTERN.search(obj):
            found.append(f"{path}: pattern dangereux détecté")
    elif isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}" if path else key
            found.extend(check_no_dangerous_html_recursive(value, child_path))
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            child_path = f"{path}[{i}]"
            found.extend(check_no_dangerous_html_recursive(item, child_path))
    return found


class TestCalculNombresV1Invariants:
    """Tests d'invariants pour CALCUL_NOMBRES_V1."""

    GENERATOR_KEY = "CALCUL_NOMBRES_V1"
    NUM_SEEDS_TO_TEST = 30

    @pytest.fixture(autouse=True)
    def setup(self):
        """Import tardif pour éviter les problèmes de chargement."""
        from backend.generators.factory import GeneratorFactory
        self.factory = GeneratorFactory

    # =========================================================================
    # INVARIANT 1: reponse_finale est un nombre valide
    # =========================================================================

    def test_reponse_finale_is_valid_number(self):
        """
        La reponse_finale doit pouvoir être convertie en nombre.

        Cet invariant garantit que le générateur produit des résultats
        mathématiquement valides.
        """
        for seed in range(self.NUM_SEEDS_TO_TEST):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={},
                seed=seed
            )
            variables = result.get("variables", {})
            reponse = variables.get("reponse_finale", "")

            # La réponse doit être convertible en nombre
            try:
                val = float(reponse.replace(",", "."))
                # Le résultat doit être fini
                assert math.isfinite(val), f"seed={seed}: résultat infini {reponse}"
            except (ValueError, AttributeError) as e:
                pytest.fail(
                    f"seed={seed}: reponse_finale '{reponse}' n'est pas un nombre valide: {e}"
                )

    # =========================================================================
    # INVARIANT 2: Pas de placeholders {{ }} non résolus
    # =========================================================================

    def test_no_unresolved_placeholders(self):
        """
        Aucun placeholder {{ }} ne doit rester dans les variables.

        Cet invariant garantit que tous les templates sont correctement
        résolus avant de retourner le résultat.
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
                f"seed={seed}: placeholders non résolus trouvés:\n"
                + "\n".join(placeholders[:5])
            )

    # =========================================================================
    # INVARIANT 3: Reproductibilité (même seed = mêmes variables)
    # =========================================================================

    def test_reproducibility_same_seed_same_result(self):
        """
        Avec la même seed et les mêmes paramètres, le résultat doit être identique.

        Cet invariant garantit le déterminisme du générateur.
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

            # Comparer les clés importantes
            for key in ["enonce", "reponse_finale", "solution"]:
                assert vars1.get(key) == vars2.get(key), (
                    f"seed={seed}: résultats différents pour '{key}':\n"
                    f"  1: {vars1.get(key)}\n"
                    f"  2: {vars2.get(key)}"
                )

    # =========================================================================
    # INVARIANT 4: Pas de HTML dangereux (XSS)
    # =========================================================================

    def test_no_dangerous_html_in_variables(self):
        """
        Les variables string ne doivent pas contenir de HTML dangereux.

        Patterns interdits: <script>, javascript:, onerror=, onload=
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
                f"seed={seed}: HTML dangereux détecté:\n"
                + "\n".join(dangerous[:5])
            )

    # =========================================================================
    # INVARIANT 5: Structure de sortie valide
    # =========================================================================

    def test_output_structure(self):
        """
        Le output doit contenir les clés obligatoires.
        """
        result = self.factory.generate(
            key=self.GENERATOR_KEY,
            overrides={},
            seed=42
        )

        # Clé obligatoire
        assert "variables" in result, "Le output doit contenir 'variables'"

        variables = result["variables"]

        # Variables obligatoires pour ce générateur
        required_vars = ["enonce", "reponse_finale"]
        for var in required_vars:
            assert var in variables, f"Variable obligatoire manquante: {var}"

    # =========================================================================
    # INVARIANT 6: Cohérence avec les différents types d'exercice
    # =========================================================================

    @pytest.mark.parametrize("exercise_type,grade", [
        ("operations_simples", "6e"),
        ("priorites_operatoires", "6e"),
        ("decimaux", "5e"),  # Les décimaux ne sont disponibles qu'en 5e
    ])
    def test_all_exercise_types_produce_valid_output(self, exercise_type, grade):
        """
        Tous les types d'exercice doivent produire un output valide.
        """
        for seed in range(10):
            result = self.factory.generate(
                key=self.GENERATOR_KEY,
                overrides={"exercise_type": exercise_type, "grade": grade},
                seed=seed
            )
            variables = result.get("variables", {})

            # Vérifier que reponse_finale existe et est valide
            reponse = variables.get("reponse_finale", "")
            assert reponse, f"type={exercise_type}, seed={seed}: reponse_finale vide"

            # Pour les décimaux, la réponse peut être une comparaison ("a < b")
            # ou un nombre simple. On vérifie juste qu'elle n'est pas vide.
            if exercise_type != "decimaux":
                # Vérifier convertibilité en nombre
                try:
                    float(reponse.replace(",", "."))
                except ValueError:
                    pytest.fail(
                        f"type={exercise_type}, seed={seed}: "
                        f"reponse_finale '{reponse}' n'est pas un nombre"
                    )
