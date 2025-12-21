"""
Handler pour les exercices dynamiques (TESTS_DYN)
=================================================

Ce handler gère la génération d'exercices dynamiques utilisant des templates
et des générateurs de variables (comme THALES_V1).

Workflow:
1. Sélectionner un exercice template depuis tests_dyn_exercises.py
2. Appeler le générateur (generator_key) pour obtenir les variables
3. Enrichir les variables (mappings alias) pour compatibilité template/générateur
4. Rendre les templates avec les variables
5. Générer les SVG depuis les variables
6. Retourner l'exercice complet, ou une erreur JSON propre si placeholders non résolus
"""

import time
import random
import re
from types import SimpleNamespace
from typing import Dict, Any, Optional, List, Set

from fastapi import HTTPException

from backend.data.tests_dyn_exercises import (
    get_tests_dyn_exercises,
    get_tests_dyn_batch,
    get_tests_dyn_stats,
    get_random_tests_dyn_exercise
)
from backend.generators.thales_generator import generate_dynamic_exercise, GENERATORS_REGISTRY
from backend.generators.factory import GeneratorFactory
from backend.services.template_renderer import render_template, get_template_variables
from backend.services.dynamic_exercise_engine import choose_template_variant
from backend.services.variants_config import is_chapter_template_based
from backend.logger import get_logger
from backend.observability import (
    get_logger as get_obs_logger,
    set_request_context,
    get_request_context,
)

logger = get_logger()
obs_logger = get_obs_logger('TESTS_DYN')


def is_tests_dyn_request(code_officiel: Optional[str]) -> bool:
    """Vérifie si la requête concerne le chapitre TESTS_DYN."""
    if not code_officiel:
        return False
    return code_officiel.upper() in ["6E_TESTS_DYN", "TESTS_DYN"]


def _extract_placeholders(template_str: str) -> Set[str]:
    """
    Extrait les placeholders {{variable}} d'un template.
    Utilisé uniquement pour debug / garde anti-placeholders.
    """
    if not template_str:
        return set()
    pattern = r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}"
    return set(re.findall(pattern, template_str))


def _normalize_figure_type(raw: Optional[str]) -> Optional[str]:
    """
    Normalise le type de figure pour THALES_V1.
    - lower + trim
    - enlève les accents simples
    - mappe quelques synonymes évidents (square -> carre, etc.)
    """
    if not raw:
        return None

    v = str(raw).strip().lower()
    # Normalisation minimale pour les cas connus
    mapping = {
        "carré": "carre",
        "square": "carre",
    }
    return mapping.get(v, v)


def format_dynamic_exercise(
    exercise_template: Dict[str, Any],
    timestamp: int,
    seed: Optional[int] = None,
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Formate un exercice dynamique complet.
    
    Args:
        exercise_template: Template d'exercice depuis la DB
        timestamp: Timestamp pour l'ID unique
        seed: Seed pour le générateur (reproductibilité)
        overrides: Paramètres à écraser (ex: difficulty de la requête HTTP)
    
    Returns:
        Exercice formaté avec HTML rendu et SVG générés.

    Important:
    - Ajoute des alias de variables pour compatibilité template/générateur
      (rectangle / triangle / carré)
    - Garde déterminisme via le seed (aucun random global ajouté ici)
    - Si des placeholders {{...}} restent après rendu, lève une HTTPException
      422 UNRESOLVED_PLACEHOLDERS pour éviter d'envoyer un énoncé cassé.
    """
    handler_start = time.time()
    chapter_code = (exercise_template.get("chapter_code") or "6E_TESTS_DYN").upper()
    exercise_id = f"ex_{chapter_code.lower()}_{exercise_template['id']}_{timestamp}"
    is_premium = exercise_template["offer"] == "pro"
    
    # Récupérer le générateur
    generator_key = exercise_template.get("generator_key", "THALES_V1")
    difficulty = exercise_template.get("difficulty", "moyen")
    template_id = exercise_template.get("id")
    
    # Mettre à jour le contexte partagé
    ctx = get_request_context()
    ctx.update({
        'chapter_code': chapter_code,
        'generator_key': generator_key,
        'template_id': template_id,
        'exercise_id': exercise_id,
        'admin_exercise_id': template_id,
        'difficulty': difficulty,
        'seed': seed,
    })
    # Nettoyer les clés réservées du contexte pour éviter des erreurs de logging
    ctx.pop("exc_info", None)
    ctx.pop("stack_info", None)
    set_request_context(**ctx)
    
    # Log début handler
    obs_logger.info(
        "event=handler_in",
        event="handler_in",
        outcome="in_progress",
        **ctx
    )
    
    # Récupérer les paramètres de l'exercice (configurés dans l'admin)
    exercise_params = exercise_template.get("variables") or {}
    
    # S'assurer que le difficulty de l'exercice est inclus dans les paramètres
    # (si non présent dans variables, utiliser celui de l'exercice)
    if "difficulty" not in exercise_params:
        exercise_params["difficulty"] = difficulty
    
    # Générer les variables et SVG (dépend uniquement du seed + difficulty)
    # Ordre de fusion: defaults < exercise_params < overrides
    gen_start = time.time()
    factory_gen = GeneratorFactory.get(generator_key)
    if factory_gen:
        try:
            gen_result = GeneratorFactory.generate(
                key=generator_key,
                exercise_params=exercise_params,
                overrides=overrides,
                seed=seed,
            )
            variables = gen_result.get("variables", {})
            results = gen_result.get("results", {})
        except ValueError as e:
            obs_logger.error(
                "event=generate_exception",
                event="generate_exception",
                outcome="error",
                reason="params_invalid",
                **ctx
            )
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "GENERATOR_PARAMS_INVALID",
                    "error": "generator_params_invalid",
                    "message": str(e),
                }
            )
    else:
        gen_result = generate_dynamic_exercise(
            generator_key=generator_key,
            seed=seed,
            difficulty=difficulty
        )
        variables = gen_result["variables"]
        results = gen_result["results"]
    
    gen_duration_ms = int((time.time() - gen_start) * 1000)
    obs_logger.debug(
        "event=generator_complete",
        event="generator_complete",
        outcome="success",
        duration_ms=gen_duration_ms,
        variables_count=len(variables),
        results_count=len(results),
        **ctx
    )
    
    # Fusionner variables et results pour le rendu
    all_vars: Dict[str, Any] = {**variables, **results}

    # Alias THALES_V1 : mapping explicite et déterministe (éviter placeholders résiduels)
    if generator_key.startswith("THALES"):
        alias_actions = []

        def apply_alias(target: str, candidates: List[str]) -> None:
            if target in all_vars and all_vars[target] is not None:
                return
            for cand in candidates:
                if cand in all_vars and all_vars[cand] is not None:
                    all_vars[target] = all_vars[cand]
                    alias_actions.append((target, cand))
                    return

        apply_alias("cote_initial", ["cote_initial", "base_initiale", "longueur_initiale", "largeur_initiale"])
        apply_alias("cote_final", ["cote_final", "base_finale", "longueur_finale", "largeur_finale"])

        missing_alias = [k for k in ("cote_initial", "cote_final") if k not in all_vars or all_vars[k] is None]
        if missing_alias:
            obs_logger.error(
                "event=alias_missing",
                event="alias_missing",
                outcome="error",
                reason="placeholder_alias_missing",
                missing_placeholders=",".join(missing_alias),
                available_keys_count=len(all_vars),
                **ctx
            )
            logger.error(
                f"[PLACEHOLDER_ALIAS] Impossible de résoudre {missing_alias} pour {generator_key} "
                f"(candidats présents: {[k for k in all_vars.keys()]})"
            )
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "PLACEHOLDER_ALIAS_MISSING",
                    "error": "placeholder_alias_missing",
                    "message": f"Impossible de résoudre les placeholders {missing_alias} pour {generator_key}",
                    "missing": missing_alias,
                    "generator_key": generator_key
                }
            )
        if alias_actions:
            obs_logger.info(
                "event=alias_applied",
                event="alias_applied",
                outcome="success",
                alias_count=len(alias_actions),
                **ctx
            )
            logger.info(f"[PLACEHOLDER_ALIAS] Aliases appliqués pour {generator_key}: {alias_actions}")

    raw_figure_type = all_vars.get("figure_type")
    figure_type = _normalize_figure_type(raw_figure_type)
    if figure_type:
        all_vars["figure_type"] = figure_type

    obs_logger.debug(
        "event=render_prepare",
        event="render_prepare",
        outcome="in_progress",
        figure_type_raw=raw_figure_type,
        available_keys_count=len(all_vars),
        **ctx
    )
    logger.info(
        f"[TESTS_DYN] format_dynamic_exercise: template_id={exercise_template.get('id')}, "
        f"exercise_id={exercise_id}, seed={seed}, generator={generator_key}, "
        f"difficulty={difficulty}, figure_type_raw={raw_figure_type}, figure_type={figure_type}"
    )
    logger.info(
        f"[TESTS_DYN] keys variables={sorted(list(variables.keys()))}, "
        f"results={sorted(list(results.keys()))}"
    )

    # =========================================================================
    # MAPPINGS DE COMPATIBILITÉ THALES (triangle / rectangle / carré)
    # =========================================================================
    # Objectif: ne JAMAIS laisser un template sans variable attendue,
    # uniquement en ajoutant des alias, sans modifier les valeurs sources.
    #
    # 1) triangle → rectangle (base/hauteur -> longueur/largeur)
    if figure_type == "triangle":
        if "base_initiale" in all_vars:
            all_vars.setdefault("longueur_initiale", all_vars["base_initiale"])
        if "hauteur_initiale" in all_vars:
            all_vars.setdefault("largeur_initiale", all_vars["hauteur_initiale"])
        if "base_finale" in all_vars:
            all_vars.setdefault("longueur_finale", all_vars["base_finale"])
        if "hauteur_finale" in all_vars:
            all_vars.setdefault("largeur_finale", all_vars["hauteur_finale"])

    # 2) rectangle → triangle (longueur/largeur -> base/hauteur)
    if figure_type == "rectangle":
        if "longueur_initiale" in all_vars:
            all_vars.setdefault("base_initiale", all_vars["longueur_initiale"])
        if "largeur_initiale" in all_vars:
            all_vars.setdefault("hauteur_initiale", all_vars["largeur_initiale"])
        if "longueur_finale" in all_vars:
            all_vars.setdefault("base_finale", all_vars["longueur_finale"])
        if "largeur_finale" in all_vars:
            all_vars.setdefault("hauteur_finale", all_vars["largeur_finale"])

    # 3) carré → rectangle + triangle (cote -> longueur/largeur/base/hauteur)
    if figure_type == "carre":
        # Supporter quelques variantes de nommage éventuelles côté générateur
        cote_initial = (
            all_vars.get("cote_initial")
            or all_vars.get("cote_initiale")
            or all_vars.get("side_initial")
            or all_vars.get("side")
        )
        cote_final = (
            all_vars.get("cote_final")
            or all_vars.get("cote_finale")
            or all_vars.get("side_final")
        )

        # Back-fill des clés canoniques si seules les variantes existent
        if cote_initial is not None:
            all_vars.setdefault("cote_initial", cote_initial)
        if cote_final is not None:
            all_vars.setdefault("cote_final", cote_final)

        if cote_initial is not None:
            # Aliases rectangle
            all_vars.setdefault("longueur_initiale", cote_initial)
            all_vars.setdefault("largeur_initiale", cote_initial)
            # Aliases triangle
            all_vars.setdefault("base_initiale", cote_initial)
            all_vars.setdefault("hauteur_initiale", cote_initial)

        if cote_final is not None:
            # Aliases rectangle
            all_vars.setdefault("longueur_finale", cote_final)
            all_vars.setdefault("largeur_finale", cote_final)
            # Aliases triangle
            all_vars.setdefault("base_finale", cote_final)
            all_vars.setdefault("hauteur_finale", cote_final)

    # =========================================================================
    # GÉNÉRATION DES PLACEHOLDERS MÉTIER (answer, question)
    # =========================================================================
    # Placeholders métier génériques pour THALES : question/answer
    if generator_key and generator_key.startswith("THALES"):
        try:
            fig = all_vars.get("figure_type", "")
            # Valeurs fallback sûres
            cote_final = all_vars.get("cote_final")
            longueur_finale = all_vars.get("longueur_finale")
            largeur_finale = all_vars.get("largeur_finale")
            base_finale = all_vars.get("base_finale")
            hauteur_finale = all_vars.get("hauteur_finale")
            coef = all_vars.get("coefficient_str") or all_vars.get("coefficient")

            if fig == "carre" and cote_final is not None:
                all_vars["question"] = f"Quelle est la mesure du côté final ?"
                all_vars["answer"] = f"{cote_final} cm"
            elif fig == "rectangle" and longueur_finale is not None and largeur_finale is not None:
                all_vars["question"] = "Quelles sont les dimensions du rectangle final ?"
                all_vars["answer"] = f"longueur {longueur_finale} cm, largeur {largeur_finale} cm"
            elif fig == "triangle" and base_finale is not None and hauteur_finale is not None:
                all_vars["question"] = "Quelles sont les dimensions du triangle final ?"
                all_vars["answer"] = f"base {base_finale} cm, hauteur {hauteur_finale} cm"
            else:
                # fallback générique pour ne pas bloquer le rendu
                all_vars["question"] = "Calcule les dimensions après transformation."
                all_vars["answer"] = f"coefficient {coef}" if coef is not None else "Voir calculs"
            logger.info(f"[TESTS_DYN] Placeholders métier générés (question/answer) pour {generator_key} / figure={fig}")
        except Exception as e:
            logger.warning(f"[TESTS_DYN] Impossible de générer question/answer pour {generator_key}: {e}")

    # =========================================================================
    # SÉLECTION DU TEMPLATE (SINGLE OU VARIANTS)
    # =========================================================================
    # stable_key métier pour la sélection de variant:
    # - soit fourni explicitement dans exercise_template["stable_key"]
    # - soit dérivé du chapitre pilote + id local
    stable_key = exercise_template.get("stable_key") or f"6E_TESTS_DYN:{exercise_template.get('id')}"

    template_variants = exercise_template.get("template_variants") or []
    if template_variants:
        # =====================================================================
        # EXTRACTION chapter_code (obligatoire pour variants)
        # =====================================================================
        # Ne pas inventer chapter_code : soit présent dans exercise_template,
        # soit dérivé depuis stable_key (format "{chapter_code}:{id}"),
        # sinon erreur explicite.
        chapter_code = exercise_template.get("chapter_code")
        
        # Dérivation depuis stable_key si absent (format "{chapter_code}:{id}")
        if not chapter_code and stable_key:
            if ":" in stable_key:
                chapter_code = stable_key.split(":")[0]
        
        # Si toujours absent et variants présents → erreur explicite
        if not chapter_code:
            logger.error(
                f"[VARIANTS_ALLOWLIST] chapter_code manquant pour template_variants. "
                f"Exercise template id={exercise_template.get('id')}, stable_key={stable_key}"
            )
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "MISSING_CHAPTER_CODE_FOR_VARIANTS",
                    "error": "missing_chapter_code_for_variants",
                    "message": (
                        "Le champ 'chapter_code' est requis pour utiliser template_variants. "
                        "Il doit être présent dans exercise_template ou dérivable depuis stable_key."
                    ),
                    "exercise_template_id": exercise_template.get("id"),
                    "stable_key": stable_key,
                    "hint": "Ajoutez 'chapter_code' dans le template d'exercice ou utilisez un stable_key au format '{chapter_code}:{id}'."
                },
            )
        
        # =====================================================================
        # DÉTECTION AUTOMATIQUE TEMPLATE-BASED (Phase Finale)
        # =====================================================================
        # Détection automatique : chapitre template-based (compatible template_variants)
        # Zéro fallback silencieux : si spec-based → erreur JSON explicite
        if not is_chapter_template_based(chapter_code, exercise_template):
            logger.error(
                f"[VARIANTS_AUTO_DETECTION] Chapitre '{chapter_code}' non template-based (spec-based). "
                f"Exercise template id={exercise_template.get('id')}, stable_key={stable_key}"
            )
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "VARIANTS_NOT_SUPPORTED",
                    "error": "variants_not_supported",
                    "message": (
                        f"Les template_variants ne sont pas supportés pour le chapitre '{chapter_code}'. "
                        f"Ce chapitre utilise une génération spec-based (MathGenerationService) "
                        f"et non template-based (is_dynamic=True + generator_key + enonce_template_html)."
                    ),
                    "chapter_code": chapter_code,
                    "exercise_template_id": exercise_template.get("id"),
                    "stable_key": stable_key,
                    "hint": "Les template_variants sont uniquement disponibles pour les chapitres template-based (avec is_dynamic=True + generator_key + enonce_template_html)."
                },
            )
        # IMPORTANT:
        # - Dès que template_variants est non vide, ils deviennent la SEULE source de vérité
        #   pour le choix du template énoncé/solution côté élève.
        # - Les champs legacy "enonce_template_html"/"solution_template_html" ne sont plus
        #   utilisés pour le rendu (uniquement miroir/compat éventuel côté admin/DB).
        # On construit une liste d'objets avec les attributs attendus par choose_template_variant
        # IMPORTANT: Le champ 'id' est utilisé pour la sélection fixed, il doit correspondre à variant_id
        variant_objs: List[SimpleNamespace] = []
        for v in template_variants:
            if isinstance(v, dict):
                # Utiliser variant_id comme id si présent, sinon id
                variant_id = v.get("variant_id") or v.get("id")
                variant_objs.append(
                    SimpleNamespace(
                        id=variant_id,  # Utilisé pour la sélection fixed
                        variant_id=variant_id,  # Pour traçabilité
                        enonce_template_html=v.get("enonce_template_html", ""),
                        solution_template_html=v.get("solution_template_html", ""),
                        weight=v.get("weight", 1),
                    )
                )
            else:
                # Si déjà un objet avec les bons attributs, on le garde tel quel
                variant_objs.append(v)  # type: ignore[arg-type]

        # Sélection déterministe si variant_id présent dans exercise_params
        variant_id_from_params = exercise_params.get("variant_id")
        if variant_id_from_params:
            # Sélection déterministe via mode="fixed"
            try:
                chosen_variant = choose_template_variant(
                    variants=variant_objs,
                    seed=seed,
                    exercise_id=stable_key,
                    mode="fixed",
                    fixed_variant_id=variant_id_from_params
                )
                variant_id = variant_id_from_params  # Utiliser celui fourni
                obs_logger.info(
                    "event=variant_fixed_selected",
                    event="variant_fixed_selected",
                    outcome="success",
                    variant_id=variant_id,
                    variants_count=len(variant_objs),
                    **ctx
                )
            except ValueError as e:
                # Variant non trouvé → erreur explicite
                obs_logger.error(
                    "event=variant_fixed_error",
                    event="variant_fixed_error",
                    outcome="error",
                    reason="variant_id_not_found",
                    variant_id_requested=variant_id_from_params,
                    available_variant_ids=[getattr(v, 'id', None) for v in variant_objs],
                    **ctx
                )
                available_variant_ids = [getattr(v, 'id', None) for v in variant_objs]
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": "VARIANT_ID_NOT_FOUND",
                        "error": "variant_id_not_found",
                        "message": f"Le variant_id '{variant_id_from_params}' n'a pas été trouvé dans les template_variants.",
                        "hint": f"Les variants disponibles sont : {', '.join(map(str, available_variant_ids))}. Vérifiez que le variant_id demandé existe pour cet exercice.",
                        "context": {
                            "exercise_id": exercise_template.get("id"),
                            "variant_id_requested": variant_id_from_params,
                            "variants_present": available_variant_ids
                        }
                    }
                )
        else:
            # Fallback déterministe quand variant_id absent (compatibilité legacy)
            # Sélectionner le premier variant disponible de manière déterministe
            if not variant_objs:
                # Aucun variant disponible → erreur explicite
                obs_logger.error(
                    "event=variant_no_variants_available",
                    event="variant_no_variants_available",
                    outcome="error",
                    reason="no_variants_in_template",
                    **ctx
                )
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": "NO_VARIANTS_AVAILABLE",
                        "error": "no_variants_available",
                        "message": "Aucun template_variant disponible pour cet exercice.",
                        "exercise_template_id": exercise_template.get("id"),
                    }
                )
            
            # Sélectionner le premier variant de manière déterministe (mode="fixed")
            available_variant_ids = [getattr(v, 'id', None) for v in variant_objs]
            fallback_variant_id = available_variant_ids[0] if available_variant_ids else None
            
            if fallback_variant_id:
                chosen_variant = choose_template_variant(
                    variants=variant_objs,
                    seed=seed,
                    exercise_id=stable_key,
                    mode="fixed",
                    fixed_variant_id=fallback_variant_id
                )
                variant_id = getattr(chosen_variant, 'variant_id', None) or fallback_variant_id
                obs_logger.info(
                    "event=variant_fallback_selected",
                    event="variant_fallback_selected",
                    outcome="success",
                    reason="variant_id_absent",
                    variant_id=variant_id,
                    fallback_variant_id=fallback_variant_id,
                    variants_count=len(variant_objs),
                    **ctx
                )
            else:
                # Cas de sécurité : aucun variant_id disponible
                obs_logger.error(
                    "event=variant_no_id_available",
                    event="variant_no_id_available",
                    outcome="error",
                    reason="no_variant_id_in_variants",
                    **ctx
                )
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": "NO_VARIANT_ID_AVAILABLE",
                        "error": "no_variant_id_available",
                        "message": "Aucun variant_id disponible dans les template_variants.",
                        "exercise_template_id": exercise_template.get("id"),
                    }
                )

        # Log variant sélectionné (après sélection fixe ou fallback)
        obs_logger.info(
            "event=variant_selected",
            event="variant_selected",
            outcome="success",
            variant_id=variant_id,
            variants_count=len(variant_objs),
            **ctx
        )

        enonce_template = chosen_variant.enonce_template_html
        solution_template = chosen_variant.solution_template_html
    else:
        # Fallback: comportement legacy, un seul template par exercice
        enonce_template = exercise_template.get("enonce_template_html", "")
        solution_template = exercise_template.get("solution_template_html", "")
    
    # =========================================================================
    # DEBUG: placeholders attendus vs variables fournies
    # =========================================================================
    placeholders_enonce = _extract_placeholders(enonce_template)
    placeholders_solution = _extract_placeholders(solution_template)
    expected_placeholders = placeholders_enonce.union(placeholders_solution)
    provided_keys = set(all_vars.keys())
    missing_before_render = sorted(expected_placeholders - provided_keys)

    if expected_placeholders:
        obs_logger.debug(
            "event=placeholders_analysis",
            event="placeholders_analysis",
            outcome="in_progress",
            expected_count=len(expected_placeholders),
            provided_count=len(provided_keys),
            missing_before_render_count=len(missing_before_render),
            **ctx
        )
        logger.info(
            f"[TESTS_DYN] Placeholders attendus (ex {exercise_template.get('id')} "
            f"/ {generator_key} / {figure_type}): {sorted(expected_placeholders)} | "
            f"clés fournies avant mapping: {sorted(provided_keys)} | "
            f"manquantes avant rendu: {missing_before_render}"
        )

    # Rendu HTML
    enonce_html = render_template(enonce_template, all_vars)
    solution_html = render_template(solution_template, all_vars)
    
    # =========================================================================
    # GUARDE ANTI-PLACEHOLDERS: ne jamais renvoyer {{...}} côté élève
    # =========================================================================
    unresolved_enonce = re.findall(r"\{\{\s*(\w+)\s*\}\}", enonce_html or "")
    unresolved_solution = re.findall(r"\{\{\s*(\w+)\s*\}\}", solution_html or "")
    unresolved = sorted(set(unresolved_enonce + unresolved_solution))

    if unresolved:
        # Log unresolved placeholders avec les bonnes informations
        obs_logger.error(
            "event=unresolved_placeholders",
            event="unresolved_placeholders",
            outcome="error",
            reason="placeholders_422",
            missing_placeholders=",".join(unresolved),
            available_keys_count=len(provided_keys),
            expected_count=len(expected_placeholders),
            **ctx
        )
        
        details = {
            "unknown_placeholders": unresolved,
            "placeholders_expected": sorted(expected_placeholders),
            "keys_provided": sorted(provided_keys),
            "template_id": exercise_template.get("id"),
            "generator_key": generator_key,
            "figure_type": figure_type,
            "exercise_id": exercise_id,
        }

        logger.error(
            f"[TESTS_DYN] UNRESOLVED_PLACEHOLDERS pour ex {exercise_id} "
            f"(template {exercise_template.get('id')}, generator={generator_key}, figure_type={figure_type}) - "
            f"restants: {unresolved} | attendus: {sorted(expected_placeholders)} | clés: {sorted(provided_keys)}"
        )

        # Remonter une erreur structurée JSON-safe, interceptée par FastAPI
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "UNRESOLVED_PLACEHOLDERS",
                "error": "UNRESOLVED_PLACEHOLDERS",
                "message": "Un ou plusieurs placeholders n'ont pas été résolus pour 6e_TESTS_DYN.",
                "details": details,
            },
        )
    
    # Log succès handler
    handler_duration_ms = int((time.time() - handler_start) * 1000)
    obs_logger.info(
        "event=handler_complete",
        event="handler_complete",
        outcome="success",
        duration_ms=handler_duration_ms,
        **ctx
    )
    
    return {
        "id_exercice": exercise_id,
        "niveau": "6e",
        "chapitre": chapter_code,
        "enonce_html": enonce_html,
        "solution_html": solution_html,
        "figure_svg": gen_result.get("figure_svg_enonce"),
        "figure_svg_enonce": gen_result.get("figure_svg_enonce"),
        "figure_svg_solution": gen_result.get("figure_svg_solution"),
        "svg": gen_result.get("figure_svg_enonce"),
        "pdf_token": exercise_id,
        "metadata": {
            "code_officiel": chapter_code,
            "difficulte": difficulty,
            "difficulty": difficulty,
            "is_premium": is_premium,
            "offer": "pro" if is_premium else "free",
            "generator_code": f"{chapter_code}_{generator_key}",
            "family": exercise_template["family"],
            "exercise_type": exercise_template.get("exercise_type"),
            "exercise_id": exercise_template["id"],
            "is_dynamic": True,
            "generator_key": generator_key,
            "seed_used": seed,
            "variables": variables,
            "variables_used": {"source": "generator", **variables},
            "source": "dynamic_generator",
            "needs_svg": exercise_template.get("needs_svg", True)
        }
    }


def generate_tests_dyn_exercise(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    seed: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Génère UN exercice dynamique.
    
    Args:
        offer: "free" ou "pro" (fallback automatique vers "free" si aucun exercice "pro")
        difficulty: "facile", "moyen", "difficile"
        seed: Graine pour reproductibilité (utilisée tel quel, sans dérivation)
    
    Returns:
        Exercice formaté pour l'API ou None si aucun exercice disponible
    """
    offer = (offer or "free").lower()
    if difficulty:
        difficulty = difficulty.lower()
    
    # Sélectionner un template (le fallback pro→free est géré dans get_tests_dyn_exercises)
    exercise_template = get_random_tests_dyn_exercise(
        offer=offer,
        difficulty=difficulty,
        seed=seed
    )
    
    if not exercise_template:
        return None
    
    timestamp = int(time.time() * 1000)
    
    # Utiliser le seed tel quel pour garantir le déterminisme
    # Même seed + mêmes params = même résultat
    gen_seed = seed if seed is not None else timestamp
    
    return format_dynamic_exercise(exercise_template, timestamp, seed=gen_seed)


def generate_tests_dyn_batch(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    count: int = 1,
    seed: Optional[int] = None
) -> tuple:
    """
    Génère un batch d'exercices dynamiques.
    
    Chaque exercice utilise un seed différent pour des variantes uniques.
    
    Args:
        offer: "free" ou "pro"
        difficulty: "facile", "moyen", "difficile"
        count: Nombre d'exercices souhaités
        seed: Graine de base pour reproductibilité
    
    Returns:
        Tuple (exercises, batch_info)
    """
    offer = (offer or "free").lower()
    if difficulty:
        difficulty = difficulty.lower()
    
    # Récupérer les templates disponibles
    templates, info = get_tests_dyn_batch(
        offer=offer,
        difficulty=difficulty,
        count=count,
        seed=seed
    )
    
    if not templates:
        return [], {
            "requested": count,
            "available": 0,
            "returned": 0,
            "filters": {"offer": offer, "difficulty": difficulty},
            "is_dynamic": True
        }
    
    timestamp = int(time.time() * 1000)
    exercises = []
    
    for i, template in enumerate(templates):
        # Seed unique pour chaque exercice, mais déterministe
        # Utiliser seed + i pour garantir l'unicité tout en restant déterministe
        ex_seed = (seed + i) if seed is not None else (timestamp + i)
        
        formatted = format_dynamic_exercise(template, timestamp + i, seed=ex_seed)
        exercises.append(formatted)
    
    batch_info = {
        "requested": count,
        "available": info["available"],
        "returned": len(exercises),
        "filters": {"offer": offer, "difficulty": difficulty},
        "is_dynamic": True,
        "generator_used": "THALES_V1"
    }
    
    return exercises, batch_info


def get_available_generators() -> List[str]:
    """Retourne la liste des générateurs disponibles."""
    # Récupérer les générateurs legacy
    legacy_generators = list(GENERATORS_REGISTRY.keys())
    
    # Récupérer les générateurs de la Factory
    try:
        from backend.generators.factory import get_generators_list
        factory_generators = get_generators_list()
        factory_keys = [g["key"] for g in factory_generators]
    except Exception:
        factory_keys = []
    
    # Fusionner et dédupliquer
    all_generators = list(set(legacy_generators + factory_keys))
    return sorted(all_generators)


if __name__ == "__main__":
    # Test rapide
    print("=== TEST HANDLER TESTS_DYN ===")
    
    # Test single
    ex = generate_tests_dyn_exercise(offer="free", difficulty="moyen", seed=42)
    if ex:
        print(f"✅ Single: {ex['id_exercice']}")
        print(f"   Énoncé: {ex['enonce_html'][:100]}...")
        print(f"   Variables: {ex['metadata']['variables']}")
    
    # Test batch
    exercises, info = generate_tests_dyn_batch(offer="free", count=3, seed=123)
    print(f"\n✅ Batch: {info['returned']}/{info['requested']} exercices")
    for ex in exercises:
        print(f"   - {ex['id_exercice']}: {ex['metadata']['variables'].get('coefficient', 'N/A')}")
