"""
Utilitaires pour la normalisation et la gestion des difficultés.

P4.B - Standardisation des difficultés : facile / moyen / difficile
Mapping : standard -> moyen (pour compatibilité)
"""

from typing import Literal

# Difficultés canoniques (affichées dans l'UI)
CANONICAL_DIFFICULTIES = ["facile", "moyen", "difficile"]

# Mapping de compatibilité (anciennes valeurs -> canoniques)
DIFFICULTY_MAPPING = {
    "standard": "moyen",  # P4.B: standard est mappé vers moyen
    "facile": "facile",
    "moyen": "moyen",
    "difficile": "difficile",
    # P4.C - Mappings supplémentaires
    "hard": "difficile",
    "advanced": "difficile",
    "easy": "facile",
    "medium": "moyen",
}


def normalize_difficulty(difficulty: str) -> str:
    """
    Normalise une difficulté vers la forme canonique.
    
    Mapping:
    - "standard" -> "moyen"
    - "facile" -> "facile"
    - "moyen" -> "moyen"
    - "difficile" -> "difficile"
    
    Args:
        difficulty: Difficulté à normaliser (peut être "standard", "facile", "moyen", "difficile")
    
    Returns:
        Difficulté canonique ("facile", "moyen", ou "difficile")
    
    Raises:
        ValueError: Si la difficulté n'est pas reconnue
    """
    if not difficulty:
        return "moyen"  # Par défaut
    
    difficulty_lower = difficulty.lower().strip()
    
    # Mapping explicite
    if difficulty_lower in DIFFICULTY_MAPPING:
        return DIFFICULTY_MAPPING[difficulty_lower]
    
    # Si déjà canonique, retourner tel quel
    if difficulty_lower in CANONICAL_DIFFICULTIES:
        return difficulty_lower
    
    # Valeur non reconnue
    raise ValueError(
        f"Difficulté non reconnue: '{difficulty}'. "
        f"Valeurs acceptées: {', '.join(CANONICAL_DIFFICULTIES + ['standard'])}"
    )


def is_canonical_difficulty(difficulty: str) -> bool:
    """
    Vérifie si une difficulté est canonique (facile, moyen, difficile).
    
    Args:
        difficulty: Difficulté à vérifier
    
    Returns:
        True si la difficulté est canonique, False sinon
    """
    return difficulty.lower() in CANONICAL_DIFFICULTIES


def get_all_canonical_difficulties() -> list[str]:
    """
    Retourne la liste de toutes les difficultés canoniques.
    
    Returns:
        Liste des difficultés canoniques: ["facile", "moyen", "difficile"]
    """
    return CANONICAL_DIFFICULTIES.copy()


def coerce_to_supported_difficulty(
    requested: str,
    supported: list[str],
    logger=None
) -> str:
    """
    Coerce une difficulté demandée vers une difficulté supportée par le générateur.
    
    Règle de fallback :
    - Si requested ∈ supported → retourne requested (normalisée)
    - Sinon fallback par défaut :
      - difficile → moyen (si moyen ∈ supported)
      - moyen → facile (si facile ∈ supported)
      - facile → facile (toujours supporté)
    
    Args:
        requested: Difficulté demandée (sera normalisée d'abord)
        supported: Liste des difficultés supportées par le générateur (doivent être canoniques)
        logger: Logger optionnel pour enregistrer la coercition
    
    Returns:
        Difficulté supportée (canonique)
    
    Example:
        >>> coerce_to_supported_difficulty("difficile", ["facile", "moyen"])
        "moyen"  # Fallback difficile → moyen
    """
    # Normaliser la difficulté demandée
    requested_normalized = normalize_difficulty(requested)
    
    # Normaliser les difficultés supportées
    supported_normalized = [normalize_difficulty(d) for d in supported]
    
    # Si la difficulté demandée est supportée, la retourner
    if requested_normalized in supported_normalized:
        return requested_normalized
    
    # Fallback hiérarchique
    if requested_normalized == "difficile":
        # difficile → moyen (si disponible)
        if "moyen" in supported_normalized:
            if logger:
                logger.info(
                    f"[DIFFICULTY_COERCED] requested=difficile coerced_to=moyen "
                    f"(generator supports: {supported_normalized})"
                )
            return "moyen"
        # Sinon → facile
        if "facile" in supported_normalized:
            if logger:
                logger.info(
                    f"[DIFFICULTY_COERCED] requested=difficile coerced_to=facile "
                    f"(generator supports: {supported_normalized})"
                )
            return "facile"
    
    elif requested_normalized == "moyen":
        # moyen → facile (si disponible)
        if "facile" in supported_normalized:
            if logger:
                logger.info(
                    f"[DIFFICULTY_COERCED] requested=moyen coerced_to=facile "
                    f"(generator supports: {supported_normalized})"
                )
            return "facile"
    
    # Si aucune difficulté n'est supportée (cas théorique), retourner facile par défaut
    if logger:
        logger.warning(
            f"[DIFFICULTY_COERCED] requested={requested_normalized} coerced_to=facile "
            f"(fallback ultime, generator supports: {supported_normalized})"
        )
    return "facile"


def map_ui_difficulty_to_generator(
    generator_key: str,
    ui_difficulty: str,
    logger=None
) -> str:
    """
    P4.D HOTFIX - Mappe une difficulté UI (canonique) vers la difficulté réelle du générateur.
    
    Problème résolu :
    - UI utilise facile/moyen/difficile (canoniques)
    - Certains générateurs utilisent facile/standard (non canonique)
    - normalize_difficulty() convertit standard -> moyen (pour l'UI)
    - Mais le générateur attend "standard", pas "moyen"
    
    Solution :
    - Récupère les difficultés réellement supportées par le générateur
    - Mappe intelligemment :
      - ui_difficulty == "moyen" et générateur supporte "standard" -> retourne "standard"
      - ui_difficulty == "difficile" et non supporté -> fallback vers "standard" si présent, sinon "facile"
      - Sinon retourne ui_difficulty normalisée
    
    Args:
        generator_key: Clé du générateur (ex: "CALCUL_NOMBRES_V1")
        ui_difficulty: Difficulté UI canonique (facile/moyen/difficile)
        logger: Logger optionnel pour enregistrer le mapping
    
    Returns:
        Difficulté réelle à utiliser pour le générateur (peut être "standard" au lieu de "moyen")
    
    Example:
        >>> map_ui_difficulty_to_generator("CALCUL_NOMBRES_V1", "moyen")
        "standard"  # Car CALCUL_NOMBRES_V1 supporte facile/standard, pas moyen
    """
    from backend.generators.factory import GeneratorFactory
    
    # Normaliser la difficulté UI
    ui_normalized = normalize_difficulty(ui_difficulty)
    
    # Récupérer le générateur
    gen_class = GeneratorFactory.get(generator_key)
    if not gen_class:
        # Générateur introuvable, retourner la difficulté normalisée
        if logger:
            logger.warning(
                f"[DIFFICULTY_MAPPING] Générateur '{generator_key}' introuvable, "
                f"utilisation de la difficulté UI normalisée: {ui_normalized}"
            )
        return ui_normalized
    
    # Récupérer les difficultés supportées depuis le schéma
    schema = gen_class.get_schema()
    supported_difficulties = []
    
    if schema:
        difficulty_param = next((p for p in schema if p.name == "difficulty"), None)
        if difficulty_param and hasattr(difficulty_param, 'options'):
            supported_difficulties = difficulty_param.options or []
    
    # Si aucune difficulté supportée trouvée, retourner la difficulté normalisée
    if not supported_difficulties:
        if logger:
            logger.warning(
                f"[DIFFICULTY_MAPPING] Aucune difficulté supportée trouvée pour '{generator_key}', "
                f"utilisation de la difficulté UI normalisée: {ui_normalized}"
            )
        return ui_normalized
    
    # Convertir les difficultés supportées en minuscules pour comparaison
    supported_lower = [d.lower().strip() for d in supported_difficulties]
    
    # Si la difficulté UI normalisée est directement supportée, la retourner
    if ui_normalized in supported_lower:
        return ui_normalized
    
    # Mapping spécial : "moyen" UI -> "standard" générateur
    if ui_normalized == "moyen" and "standard" in supported_lower:
        if logger:
            logger.info(
                f"[DIFFICULTY_MAPPED] generator={generator_key} ui=moyen -> generator=standard "
                f"(supported: {supported_difficulties})"
            )
        return "standard"
    
    # Fallback pour "difficile" UI
    if ui_normalized == "difficile":
        # Essayer "standard" d'abord
        if "standard" in supported_lower:
            if logger:
                logger.info(
                    f"[DIFFICULTY_MAPPED] generator={generator_key} ui=difficile -> generator=standard "
                    f"(fallback, supported: {supported_difficulties})"
                )
            return "standard"
        # Sinon "facile"
        if "facile" in supported_lower:
            if logger:
                logger.info(
                    f"[DIFFICULTY_MAPPED] generator={generator_key} ui=difficile -> generator=facile "
                    f"(fallback, supported: {supported_difficulties})"
                )
            return "facile"
    
    # Fallback pour "moyen" UI si "standard" n'est pas supporté
    if ui_normalized == "moyen" and "facile" in supported_lower:
        if logger:
            logger.info(
                f"[DIFFICULTY_MAPPED] generator={generator_key} ui=moyen -> generator=facile "
                f"(fallback, supported: {supported_difficulties})"
            )
        return "facile"
    
    # Aucun mapping trouvé, retourner la difficulté normalisée (générera probablement une erreur)
    if logger:
        logger.warning(
            f"[DIFFICULTY_MAPPED] generator={generator_key} ui={ui_normalized} -> generator={ui_normalized} "
            f"(aucun mapping trouvé, supported: {supported_difficulties})"
        )
    return ui_normalized


def auto_complete_presets(
    requested_presets: list[str],
    supported_difficulties: list[str]
) -> list[str]:
    """
    Auto-complète les presets de difficultés en ajoutant les manquantes.
    
    Si une difficulté canonique manque dans requested_presets, elle est ajoutée
    en clonant la difficulté la plus proche disponible.
    
    Règle :
    - facile, moyen, difficile sont toujours présents dans le résultat
    - Si "difficile" manque → ajouter "difficile" (même si non supportée nativement)
    - Si "moyen" manque → ajouter "moyen"
    - Si "facile" manque → ajouter "facile"
    
    Args:
        requested_presets: Liste des difficultés demandées (seront normalisées)
        supported_difficulties: Liste des difficultés supportées par le générateur
    
    Returns:
        Liste complétée avec toutes les difficultés canoniques
    """
    # Normaliser les presets demandés
    requested_normalized = [normalize_difficulty(d) for d in requested_presets]
    
    # Normaliser les difficultés supportées
    supported_normalized = [normalize_difficulty(d) for d in supported_difficulties]
    
    # Commencer avec les presets demandés
    result = list(set(requested_normalized))  # Dédupliquer
    
    # Ajouter les difficultés canoniques manquantes
    for canonical in CANONICAL_DIFFICULTIES:
        if canonical not in result:
            result.append(canonical)
    
    # Trier pour avoir un ordre cohérent
    result.sort(key=lambda x: CANONICAL_DIFFICULTIES.index(x))
    
    return result

