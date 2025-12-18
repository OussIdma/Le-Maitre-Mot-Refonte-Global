import hashlib
from typing import Any, List, Optional


def choose_template_variant(
    variants: List[Any],
    seed: Optional[int],
    exercise_id: str,
    mode: str = "seed_random",
    fixed_variant_id: Optional[str] = None,
) -> Any:
    """
    Sélectionne un variant de template de manière déterministe.

    CONTRAT:
    - variants: liste d'objets possédant au minimum les attributs
      - id: str
      - weight: int (>= 1, mais on protège contre les valeurs invalides)
    - seed: seed de génération (peut être None)
    - exercise_id: identifiant logique stable de l'exercice (ex: "6e_G07:3")
    - mode:
        - "seed_random": sélection pondérée via hash(seed, exercise_id)
        - "fixed": sélection directe par fixed_variant_id
    - fixed_variant_id:
        - si renseigné et mode="fixed", on retourne le variant correspondant ou on lève ValueError.

    REMARQUES:
    - AUCUNE utilisation de random / RNG global.
    - Le résultat est une fonction pure de (variants, seed, exercise_id, mode, fixed_variant_id).
    """

    if not variants:
        raise ValueError("Aucun variant disponible pour la sélection.")

    # Mode fixed: priorité si demandé explicitement
    if mode == "fixed":
        if not fixed_variant_id:
            raise ValueError("fixed_variant_id est requis en mode 'fixed'.")
        for variant in variants:
            vid = getattr(variant, "id", None)
            if vid == fixed_variant_id:
                return variant
        raise ValueError(f"Variant id '{fixed_variant_id}' introuvable parmi les variants fournis.")

    # Mode seed_random (par défaut)
    if mode != "seed_random":
        raise ValueError(f"Mode de sélection inconnu: {mode}")

    # 1. Construire une clé déterministe à partir de l'exercice et de la seed
    base = f"{exercise_id}:{seed if seed is not None else 'no-seed'}"

    # 2. Hachage stable (sans RNG global)
    h = hashlib.sha256(base.encode("utf-8")).hexdigest()
    val = int(h[:8], 16)  # 32 bits suffisent pour l'index

    # 3. Sélection pondérée en fonction de weight
    weights = []
    total_weight = 0
    for v in variants:
        w = getattr(v, "weight", 1)
        try:
            w_int = int(w)
        except Exception:
            w_int = 1
        if w_int < 1:
            w_int = 1
        weights.append(w_int)
        total_weight += w_int

    if total_weight <= 0:
        # Protection défensive, ne devrait pas arriver avec la validation amont
        raise ValueError("Somme des poids des variants invalide (<= 0).")

    index = val % total_weight

    acc = 0
    for variant, w in zip(variants, weights):
        acc += w
        if index < acc:
            return variant

    # Par construction on ne devrait jamais atteindre ce point
    # mais on garde une sécurité explicite.
    raise RuntimeError("Échec inattendu de la sélection de variant.")


