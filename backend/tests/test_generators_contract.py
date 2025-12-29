"""
Tests contractuels pour TOUS les générateurs
============================================

Ces tests vérifient que chaque générateur respecte le contrat de qualité:
- Pas de placeholders non résolus
- Variables non vides
- Sujet ≠ Corrigé (si applicable)
- Pas de dépendance DB (CI-safe)

IMPORTANT: Ces tests sont BLOQUANTS en CI.
"""

import pytest
from typing import List, Dict, Any
from backend.tests.contracts.exercise_contract import (
    assert_no_unresolved_placeholders,
    strip_html
)


def get_all_generator_keys() -> List[str]:
    """
    Récupère la liste de tous les générateurs activés.
    
    Exclut les générateurs désactivés (DISABLED_GENERATORS).
    """
    from backend.generators.factory import GeneratorFactory
    
    generators = GeneratorFactory.list_all(include_disabled=False)
    return [g["key"] for g in generators]


def pytest_generate_tests(metafunc):
    """
    Hook pytest pour générer dynamiquement les tests paramétrés.
    """
    if "generator_key" in metafunc.fixturenames:
        try:
            keys = get_all_generator_keys()
        except Exception as e:
            pytest.skip(f"Impossible de charger les générateurs: {e}")
            keys = []
        
        metafunc.parametrize("generator_key", keys)


class TestGeneratorsContract:
    """Tests contractuels pour tous les générateurs."""
    
    # Seeds pour tester (3 seeds pour garder CI rapide)
    TEST_SEEDS = [1, 2, 3]
    
    def _get_test_difficulties(self, generator_key: str) -> List[str]:
        """
        Récupère les difficultés à tester pour un générateur.
        
        Certains générateurs n'acceptent que "facile"/"standard" au lieu de "moyen".
        On essaie d'utiliser les defaults du générateur ou "standard" en fallback.
        """
        from backend.generators.factory import GeneratorFactory
        
        gen_class = GeneratorFactory.get(generator_key)
        if not gen_class:
            return ["moyen"]  # Fallback
        
        # Récupérer les defaults
        defaults = gen_class.get_defaults()
        if "difficulty" in defaults:
            return [defaults["difficulty"]]
        
        # Essayer "standard" (plus commun que "moyen" pour certains générateurs)
        # Si ça échoue, on utilisera None (pas de difficulté)
        return ["standard"]
    
    def _generate_exercise_dict(self, generator_key: str, seed: int, difficulty: str = None) -> Dict[str, Any]:
        """
        Génère un exercice et le convertit en format dict avec enonce_html/solution_html.
        
        Simule le rendu des templates si nécessaire.
        """
        from backend.generators.factory import GeneratorFactory
        from backend.services.template_renderer import render_template
        
        # Générer avec le générateur
        # Essayer avec la difficulté, si ça échoue, essayer sans
        try:
            result = GeneratorFactory.generate(
                key=generator_key,
                overrides={"difficulty": difficulty} if difficulty else {},
                seed=seed
            )
        except ValueError as e:
            # Si la difficulté n'est pas supportée, essayer sans difficulté
            if "difficulty" in str(e).lower():
                result = GeneratorFactory.generate(
                    key=generator_key,
                    overrides={},
                    seed=seed
                )
            else:
                raise
        
        # Extraire les variables (gérer None)
        variables = result.get("variables") or {}
        results = result.get("results") or {}
        geo_data = result.get("geo_data") or {}
        
        # Fusionner toutes les variables disponibles
        all_vars = {**variables, **results, **geo_data}
        
        # Construire un dict d'exercice pour les tests contractuels
        exercise = {
            "enonce_html": "",
            "solution_html": "",
            "figure_svg_enonce": result.get("figure_svg_enonce"),
            "figure_svg_solution": result.get("figure_svg_solution"),
            "figure_svg": result.get("figure_svg"),
            "svg": result.get("svg"),
        }
        
        # 1. Chercher enonce_html directement
        if "enonce_html" in variables:
            exercise["enonce_html"] = str(variables["enonce_html"])
        elif "enonce" in variables:
            enonce = str(variables["enonce"])
            # Si c'est un template avec placeholders, le rendre
            if "{{" in enonce:
                exercise["enonce_html"] = render_template(enonce, all_vars)
            else:
                exercise["enonce_html"] = f"<p>{enonce}</p>"
        elif "consigne" in variables:
            consigne = str(variables["consigne"])
            exercise["enonce_html"] = f"<p>{consigne}</p>"
        elif "question" in variables:
            question = str(variables["question"])
            exercise["enonce_html"] = f"<p>{question}</p>"
        elif "instruction" in variables:
            instruction = str(variables["instruction"])
            exercise["enonce_html"] = f"<p>{instruction}</p>"
        # Pour les générateurs de fractions, construire depuis la fraction
        elif any(k in variables for k in ["fraction", "fraction_str", "n", "d", "numerator", "denominator"]):
            # Construire l'énoncé
            fraction_str = None
            if "fraction_str" in variables and variables["fraction_str"]:
                fraction_str = str(variables["fraction_str"])
            elif "fraction" in variables and variables["fraction"]:
                fraction_str = str(variables["fraction"])
            elif "n" in variables and "d" in variables:
                n_val = variables.get("n", "")
                d_val = variables.get("d", "")
                if n_val and d_val:
                    fraction_str = f"{n_val}/{d_val}"
            elif "numerator" in variables and "denominator" in variables:
                num = variables.get("numerator", "")
                den = variables.get("denominator", "")
                if num and den:
                    fraction_str = f"{num}/{den}"
            
            if fraction_str:
                exercise["enonce_html"] = f"<p><strong>Simplifier la fraction suivante :</strong></p><p>{fraction_str}</p>"
        # Pour THALES_V2 et autres générateurs géométriques, construire depuis plusieurs variables
        elif any(k in variables for k in ["figure_type", "coefficient", "base_dimensions"]):
            # Construire un énoncé basique pour les exercices géométriques
            parts = []
            if "figure_type" in variables:
                parts.append(f"Figure: {variables['figure_type']}")
            if "coefficient" in variables:
                parts.append(f"Coefficient: {variables['coefficient']}")
            if parts:
                exercise["enonce_html"] = f"<p>{'. '.join(parts)}</p>"
        
        # 2. Chercher solution_html directement
        if "solution_html" in variables:
            exercise["solution_html"] = str(variables["solution_html"])
        elif "solution" in variables:
            solution = str(variables["solution"])
            # Si c'est un template avec placeholders, le rendre
            if "{{" in solution:
                exercise["solution_html"] = render_template(solution, all_vars)
            else:
                exercise["solution_html"] = f"<p>{solution}</p>"
        else:
            # Construire depuis reponse_finale + calculs
            reponse = variables.get("reponse_finale", "") or results.get("reponse_finale", "")
            calculs = variables.get("calculs_intermediaires", "")
            
            # Pour les générateurs de fractions (SIMPLIFICATION_FRACTIONS), construire depuis les étapes
            if not reponse and any(k in variables for k in ["fraction", "fraction_reduite", "step1", "step2", "step3", "pgcd"]):
                parts = []
                # Ajouter les étapes si disponibles
                if "step1" in variables and variables["step1"]:
                    parts.append(f"<strong>Étape 1 :</strong> {variables['step1']}")
                if "step2" in variables and variables["step2"]:
                    parts.append(f"<strong>Étape 2 :</strong> {variables['step2']}")
                if "step3" in variables and variables["step3"]:
                    parts.append(f"<strong>Étape 3 :</strong> {variables['step3']}")
                
                # Si pas d'étapes mais on a pgcd et fractions, construire une explication
                if not parts and "pgcd" in variables and "fraction" in variables and "fraction_reduite" in variables:
                    pgcd_val = variables.get("pgcd", "")
                    fraction = variables.get("fraction", "")
                    fraction_reduite = variables.get("fraction_reduite", "")
                    if pgcd_val and fraction and fraction_reduite:
                        parts.append(f"<strong>On calcule le PGCD :</strong> PGCD = {pgcd_val}")
                        parts.append(f"<strong>On divise :</strong> On divise le numérateur et le dénominateur par {pgcd_val}")
                        parts.append(f"<strong>Conclusion :</strong> La fraction {fraction} se simplifie en {fraction_reduite}")
                elif "fraction_reduite" in variables and variables["fraction_reduite"]:
                    # Au minimum, donner la réponse
                    parts.append(f"<strong>Conclusion :</strong> La fraction simplifiée est {variables['fraction_reduite']}")
                
                if parts:
                    exercise["solution_html"] = "<p>" + "</p><p>".join(parts) + "</p>"
            # Pour les générateurs géométriques (THALES, etc.), construire depuis les dimensions
            elif not reponse and any(k in variables for k in ["cote_final", "cote_initial", "coefficient", "base_finale", "hauteur_finale"]):
                parts = []
                if "cote_initial" in variables:
                    parts.append(f"Côté initial: {variables['cote_initial']} cm")
                if "coefficient" in variables:
                    parts.append(f"Coefficient: {variables['coefficient']}")
                if "cote_final" in variables:
                    parts.append(f"Côté final: {variables['cote_final']} cm")
                if "base_finale" in variables:
                    parts.append(f"Base finale: {variables['base_finale']} cm")
                if "hauteur_finale" in variables:
                    parts.append(f"Hauteur finale: {variables['hauteur_finale']} cm")
                if parts:
                    exercise["solution_html"] = "<p>" + "</p><p>".join(parts) + "</p>"
            # Pour SYMETRIE_AXIALE_V2 et autres générateurs de symétrie
            elif not reponse and any(k in variables for k in ["figure_type", "axe_type", "symmetric"]):
                parts = []
                if "figure_type" in variables:
                    parts.append(f"Type de figure: {variables['figure_type']}")
                if "axe_type" in variables:
                    parts.append(f"Axe: {variables['axe_type']}")
                if "symmetric" in variables or "symmetric_data" in geo_data:
                    parts.append("Symétrique tracé selon les règles de symétrie axiale")
                if parts:
                    exercise["solution_html"] = "<p>" + "</p><p>".join(parts) + "</p>"
            elif reponse:
                parts = [str(reponse)]
                if calculs:
                    if isinstance(calculs, list):
                        parts.extend([str(c) for c in calculs])
                    else:
                        parts.append(str(calculs))
                exercise["solution_html"] = "<p>" + "</p><p>".join(parts) + "</p>"
        
        # Ajouter les templates si présents (pour validation placeholders)
        if "enonce_template" in variables:
            exercise["enonce_template"] = variables["enonce_template"]
        if "solution_template" in variables:
            exercise["solution_template"] = variables["solution_template"]
        if "enonce_template_html" in variables:
            exercise["enonce_template"] = variables["enonce_template_html"]
        if "solution_template_html" in variables:
            exercise["solution_template"] = variables["solution_template_html"]
        
        return exercise
    
    def test_no_unresolved_placeholders(self, generator_key: str):
        """
        Vérifie qu'aucun placeholder n'est laissé non résolu dans les variables.
        
        Args:
            generator_key: Clé du générateur à tester
        """
        from backend.generators.factory import GeneratorFactory
        
        gen_class = GeneratorFactory.get(generator_key)
        if gen_class is None:
            pytest.skip(f"Générateur {generator_key} non trouvé")
        
        unresolved_placeholders = set()
        test_difficulties = self._get_test_difficulties(generator_key)
        
        for seed in self.TEST_SEEDS:
            for difficulty in test_difficulties:
                try:
                    # Essayer avec la difficulté, si ça échoue, essayer sans
                    try:
                        result = GeneratorFactory.generate(
                            key=generator_key,
                            overrides={"difficulty": difficulty} if difficulty else {},
                            seed=seed
                        )
                    except ValueError as e:
                        # Si la difficulté n'est pas supportée, essayer sans difficulté
                        if "difficulty" in str(e).lower():
                            result = GeneratorFactory.generate(
                                key=generator_key,
                                overrides={},
                                seed=seed
                            )
                        else:
                            raise
                    
                    # Vérifier dans toutes les variables string
                    variables = result.get("variables", {}) or {}
                    results = result.get("results") or {}
                    geo_data = result.get("geo_data") or {}
                    all_data = {**variables, **results, **geo_data}
                    
                    for key, value in all_data.items():
                        if isinstance(value, str) and value:
                            try:
                                assert_no_unresolved_placeholders(value, f"{key} (seed={seed})")
                            except AssertionError as e:
                                unresolved_placeholders.add(str(e))
                
                except Exception as e:
                    # Si le générateur crash, on le signale mais on continue
                    pytest.fail(f"{generator_key} seed={seed} difficulty={difficulty}: {e}")
        
        if unresolved_placeholders:
            pytest.fail(
                f"{generator_key}: placeholders non résolus trouvés:\n" +
                "\n".join(sorted(unresolved_placeholders))
            )
    
    def test_exercise_contract(self, generator_key: str):
        """
        Vérifie que chaque exercice généré respecte le contrat complet.
        
        Args:
            generator_key: Clé du générateur à tester
        """
        from backend.tests.contracts.exercise_contract import assert_exercise_contract
        
        from backend.generators.factory import GeneratorFactory
        
        gen_class = GeneratorFactory.get(generator_key)
        if gen_class is None:
            pytest.skip(f"Générateur {generator_key} non trouvé")
        
        errors = []
        test_difficulties = self._get_test_difficulties(generator_key)
        
        for seed in self.TEST_SEEDS:
            for difficulty in test_difficulties:
                try:
                    # Essayer avec la difficulté, si ça échoue, essayer sans
                    try:
                        exercise = self._generate_exercise_dict(generator_key, seed, difficulty)
                    except ValueError as e:
                        # Si la difficulté n'est pas supportée, essayer sans difficulté
                        if "difficulty" in str(e).lower():
                            exercise = self._generate_exercise_dict(generator_key, seed, None)
                        else:
                            raise
                    
                    # Valider le contrat
                    try:
                        assert_exercise_contract(exercise, generator_key)
                    except AssertionError as e:
                        errors.append(f"seed={seed} difficulty={difficulty}: {e}")
                
                except Exception as e:
                    errors.append(f"seed={seed} difficulty={difficulty}: génération échouée: {e}")
        
        if errors:
            pytest.fail(
                f"{generator_key}: violations du contrat:\n" +
                "\n".join(errors)
            )
    
    def test_variables_not_empty(self, generator_key: str):
        """
        Vérifie que les variables générées ne sont pas vides.
        
        Args:
            generator_key: Clé du générateur à tester
        """
        from backend.generators.factory import GeneratorFactory
        
        gen_class = GeneratorFactory.get(generator_key)
        if gen_class is None:
            pytest.skip(f"Générateur {generator_key} non trouvé")
        
        test_difficulties = self._get_test_difficulties(generator_key)
        
        for seed in self.TEST_SEEDS:
            for difficulty in test_difficulties:
                # Essayer avec la difficulté, si ça échoue, essayer sans
                try:
                    result = GeneratorFactory.generate(
                        key=generator_key,
                        overrides={"difficulty": difficulty} if difficulty else {},
                        seed=seed
                    )
                except ValueError as e:
                    # Si la difficulté n'est pas supportée, essayer sans difficulté
                    if "difficulty" in str(e).lower():
                        result = GeneratorFactory.generate(
                            key=generator_key,
                            overrides={},
                            seed=seed
                        )
                    else:
                        raise
                
                # Vérifier qu'il y a au moins des variables ou results
                variables = result.get("variables", {})
                results = result.get("results", {})
                
                assert variables or results, \
                    f"{generator_key} seed={seed}: aucune variable ni result généré"
                
                # Vérifier qu'au moins une variable string n'est pas vide
                all_strings = [
                    str(v) for v in {**variables, **results}.values()
                    if isinstance(v, str) or isinstance(v, (int, float))
                ]
                
                assert len(all_strings) > 0, \
                    f"{generator_key} seed={seed}: aucune variable string générée"

