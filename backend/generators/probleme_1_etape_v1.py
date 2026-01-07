"""backend.generators.probleme_1_etape_v1

Générateur PROBLEME_1_ETAPE_V1 - Problèmes (1 étape) 6e
======================================================

Version: 1.0.0

Chapitre cible: 6e_N10 (résolution de problèmes à une étape)

Ce générateur produit des problèmes courts et réalistes, en 1 étape, dans 3 familles:
  A) Achat / prix / quantité (× ou ÷)
  B) Distance / temps / "par heure" (× ou ÷)
  C) Partage / quotient (÷, exact ou avec reste selon la difficulté)

Contrat variables (stables):
  - titre
  - consigne
  - contexte
  - donnees
  - question
  - reponse_finale
  - steps
  - problem_type
  - operation
  - difficulty

Note: Les variables supplémentaires (prix_unitaire, quantite, etc.) sont incluses
pour faciliter l'écriture de templates plus riches, mais les templates par défaut
doivent s'appuyer uniquement sur le contrat stable ci-dessus.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from backend.generators.base_generator import (
    BaseGenerator,
    GeneratorMeta,
    ParamSchema,
    Preset,
    ParamType,
)
from backend.generators.factory import GeneratorFactory


def _fmt_fr_number(x: float) -> str:
    """Format court en français (virgule), sans .0."""
    if isinstance(x, int):
        return str(x)
    if abs(x - int(x)) < 1e-9:
        return str(int(x))
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def _fmt_money(euros: float) -> str:
    """Format euro français (2 décimales, virgule)."""
    s = f"{euros:.2f}".replace(".", ",")
    return f"{s} €"


def _html_ul(items: List[str]) -> str:
    lis = "\n".join([f"<li>{it}</li>" for it in items])
    return f"<ul>\n{lis}\n</ul>"


def _html_ol(items: List[str]) -> str:
    lis = "\n".join([f"<li>{it}</li>" for it in items])
    return f"<ol>\n{lis}\n</ol>"


@dataclass
class _Problem:
    problem_type: str
    operation: str
    titre: str
    contexte: str
    donnees_items: List[str]
    question: str
    reponse_finale: str
    steps_items: List[str]
    extra_vars: Dict[str, Any]


@GeneratorFactory.register
class Probleme1EtapeV1Generator(BaseGenerator):
    """Générateur de problèmes à 1 étape (6e_N10)."""

    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="PROBLEME_1_ETAPE_V1",
            label="Problèmes (1 étape)",
            description="Problèmes courts à 1 étape (achat, distance/temps, partage)",
            version="1.0.0",
            niveaux=["6e"],
            exercise_type="PROBLEMES",
            svg_mode="AUTO",
            supports_double_svg=False,
            is_dynamic=True,
            supported_grades=["6e"],
            supported_chapters=["6e_N10"],
            pedagogical_tips=(
                "6e_N10: choisir l'opération adaptée (× ou ÷), "
                "soigner l'unité et rédiger une phrase de conclusion."
            ),
            min_offer="free",
        )

    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        return [
            ParamSchema(
                name="problem_type",
                type=ParamType.ENUM,
                description="Famille de problème",
                default="auto",
                options=["auto", "achat", "distance_temps", "partage"],
            ),
            ParamSchema(
                name="difficulty",
                type=ParamType.ENUM,
                description="Difficulté",
                default="moyen",
                options=["facile", "moyen", "difficile"],
            ),
            ParamSchema(
                name="allow_reste",
                type=ParamType.BOOL,
                description="Autoriser une division avec reste (surtout difficile)",
                default=False,
            ),
        ]

    @classmethod
    def get_presets(cls) -> List[Preset]:
        return [
            Preset(
                key="6e_N10_facile",
                label="6e N10 - Problèmes 1 étape (facile)",
                description="Entiers petits, division exacte",
                niveau="6e",
                params={"problem_type": "auto", "difficulty": "facile", "allow_reste": False, "seed": 42},
            ),
            Preset(
                key="6e_N10_moyen",
                label="6e N10 - Problèmes 1 étape (moyen)",
                description="Entiers + décimaux simples selon contexte",
                niveau="6e",
                params={"problem_type": "auto", "difficulty": "moyen", "allow_reste": False, "seed": 42},
            ),
            Preset(
                key="6e_N10_difficile",
                label="6e N10 - Problèmes 1 étape (difficile)",
                description="Décimaux plus fréquents, division possible avec reste",
                niveau="6e",
                params={"problem_type": "auto", "difficulty": "difficile", "allow_reste": True, "seed": 42},
            ),
        ]

    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        difficulty = params.get("difficulty", "moyen")
        requested_type = params.get("problem_type", "auto")
        allow_reste = bool(params.get("allow_reste", False))

        if requested_type == "auto":
            problem_type = self.rng_choice(
                ["achat", "distance_temps", "partage"], ctx={"difficulty": difficulty}
            )
        else:
            problem_type = requested_type

        if problem_type == "achat":
            p = self._gen_achat(difficulty)
        elif problem_type == "distance_temps":
            p = self._gen_distance_temps(difficulty)
        else:
            p = self._gen_partage(difficulty, allow_reste=allow_reste)

        variables: Dict[str, Any] = {
            "titre": p.titre,
            "consigne": "Choisis l'opération adaptée, calcule, puis écris une phrase de conclusion.",
            "contexte": p.contexte,
            "donnees": _html_ul(p.donnees_items),
            "question": p.question,
            "reponse_finale": p.reponse_finale,
            # clé stable pour templates admin
            "steps": _html_ol(p.steps_items),
            # compat future (pas obligatoire)
            "steps_html": _html_ol(p.steps_items),
            "problem_type": p.problem_type,
            "operation": p.operation,
            "difficulty": difficulty,
        }
        variables.update(p.extra_vars)

        return {
            "variables": variables,
            "geo_data": None,
            "figure_svg_enonce": "",
            "figure_svg_solution": "",
            "meta": {"generator_key": "PROBLEME_1_ETAPE_V1"},
        }

    def _gen_achat(self, difficulty: str) -> _Problem:
        items = [
            ("cahier", "cahiers"),
            ("stylo", "stylos"),
            ("gomme", "gommes"),
            ("crayon", "crayons"),
            ("livre", "livres"),
        ]
        obj_sing, obj_plur = self.rng_choice(items)

        op = self.rng_choice(["*", "/"], ctx={"family": "achat", "difficulty": difficulty})

        if difficulty == "facile":
            qty = self.rng_randint(2, 9)
            unit_price = float(self.rng_choice([1, 2, 3, 4, 5]))
        elif difficulty == "moyen":
            qty = self.rng_randint(2, 12)
            unit_price = float(self.rng_choice([0.5, 1.0, 1.5, 2.5, 3.0, 4.0]))
        else:
            qty = self.rng_randint(3, 20)
            unit_price = float(self.rng_choice([0.75, 1.25, 1.5, 2.75, 3.5, 4.25]))

        if op == "*":
            total = unit_price * qty
            titre = "Problème - Achat"
            contexte = f"Au magasin, {obj_sing} coûte {_fmt_money(unit_price)}."
            donnees = [
                f"Prix d'un {obj_sing} : {_fmt_money(unit_price)}",
                f"Quantité achetée : {qty} {obj_plur}",
            ]
            question = f"Combien paie-t-on pour {qty} {obj_plur} ?"
            reponse = _fmt_money(total)
            steps = [
                "On cherche le prix total : on multiplie le prix unitaire par la quantité.",
                f"Calcul : {_fmt_fr_number(unit_price)} × {qty} = {_fmt_fr_number(total)}",
                f"Conclusion : on paie {reponse}.",
            ]
            extra = {"prix_unitaire": unit_price, "quantite": qty, "total": total, "unite": "€"}
            return _Problem("achat", "*", titre, contexte, donnees, question, reponse, steps, extra)

        # division: total connu -> prix unitaire (choisir total cohérent)
        if difficulty == "facile":
            qty = self.rng_randint(2, 10)
            unit_price = float(self.rng_choice([1, 2, 3, 4, 5]))
        elif difficulty == "moyen":
            qty = self.rng_randint(2, 12)
            unit_price = float(self.rng_choice([0.5, 1.0, 1.5, 2.0, 2.5]))
        else:
            qty = self.rng_randint(3, 20)
            unit_price = float(self.rng_choice([0.75, 1.25, 1.5, 2.0, 2.5]))

        total = unit_price * qty
        titre = "Problème - Achat"
        contexte = f"On achète {qty} {obj_plur} pour un total de {_fmt_money(total)}."
        donnees = [f"Quantité : {qty} {obj_plur}", f"Prix total : {_fmt_money(total)}"]
        question = f"Quel est le prix d'un {obj_sing} ?"
        reponse = _fmt_money(unit_price)
        steps = [
            "On cherche le prix d'un objet : on divise le prix total par la quantité.",
            f"Calcul : {_fmt_fr_number(total)} ÷ {qty} = {_fmt_fr_number(unit_price)}",
            f"Conclusion : un {obj_sing} coûte {reponse}.",
        ]
        extra = {"prix_unitaire": unit_price, "quantite": qty, "total": total, "unite": "€"}
        return _Problem("achat", "/", titre, contexte, donnees, question, reponse, steps, extra)

    def _gen_distance_temps(self, difficulty: str) -> _Problem:
        op = self.rng_choice(["*", "/"], ctx={"family": "distance_temps", "difficulty": difficulty})

        if difficulty == "facile":
            vitesse = float(self.rng_choice([3, 4, 5, 6, 8, 10]))
            temps = self.rng_randint(2, 6)
        elif difficulty == "moyen":
            vitesse = float(self.rng_choice([2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0]))
            temps = self.rng_randint(2, 8)
        else:
            vitesse = float(self.rng_choice([2.25, 2.5, 3.75, 4.5, 5.25, 6.5]))
            temps = self.rng_randint(3, 12)

        if op == "*":
            distance = vitesse * temps
            titre = "Problème - Distance"
            contexte = "Un randonneur marche à vitesse constante."
            donnees = [
                f"Il parcourt {_fmt_fr_number(vitesse)} km par heure.",
                f"Il marche pendant {temps} h.",
            ]
            question = "Quelle distance parcourt-il ?"
            reponse = f"{_fmt_fr_number(distance)} km"
            steps = [
                "On cherche la distance parcourue : on multiplie la distance en 1 heure par le nombre d'heures.",
                f"Calcul : {_fmt_fr_number(vitesse)} × {temps} = {_fmt_fr_number(distance)}",
                f"Conclusion : il parcourt {reponse}.",
            ]
            extra = {"vitesse": vitesse, "temps": temps, "distance": distance, "unite": "km"}
            return _Problem("distance_temps", "*", titre, contexte, donnees, question, reponse, steps, extra)

        # division: vitesse = distance ÷ temps
        if difficulty == "facile":
            temps = self.rng_randint(2, 6)
            vitesse = float(self.rng_choice([3, 4, 5, 6, 8, 10]))
        elif difficulty == "moyen":
            temps = self.rng_randint(2, 8)
            vitesse = float(self.rng_choice([2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0]))
        else:
            temps = self.rng_randint(3, 12)
            vitesse = float(self.rng_choice([2.25, 2.5, 3.75, 4.5, 5.25, 6.5]))

        distance = vitesse * temps
        titre = "Problème - Vitesse"
        contexte = "Un cycliste roule à vitesse constante."
        donnees = [f"Il parcourt {_fmt_fr_number(distance)} km en {temps} h."]
        question = "Quelle distance parcourt-il en 1 heure (sa vitesse) ?"
        reponse = f"{_fmt_fr_number(vitesse)} km/h"
        steps = [
            "On cherche une distance 'par heure' : on divise la distance totale par le nombre d'heures.",
            f"Calcul : {_fmt_fr_number(distance)} ÷ {temps} = {_fmt_fr_number(vitesse)}",
            f"Conclusion : sa vitesse est {reponse}.",
        ]
        extra = {"vitesse": vitesse, "temps": temps, "distance": distance, "unite": "km/h"}
        return _Problem("distance_temps", "/", titre, contexte, donnees, question, reponse, steps, extra)

    def _gen_partage(self, difficulty: str, allow_reste: bool) -> _Problem:
        objet_sing, objet_plur = self.rng_choice(
            [("bonbon", "bonbons"), ("crayon", "crayons"), ("jeton", "jetons"), ("sticker", "stickers")]
        )
        personnes = self.rng_randint(2, 8 if difficulty != "difficile" else 12)

        if difficulty == "facile":
            part = self.rng_randint(2, 9)
            total = personnes * part
            reste = 0
        elif difficulty == "moyen":
            part = self.rng_randint(3, 15)
            total = personnes * part
            reste = 0
        else:
            part = self.rng_randint(4, 20)
            total = personnes * part
            reste = 0
            if allow_reste and self.rng_choice([True, False], ctx={"difficulty": difficulty}):
                reste = self.rng_randint(1, personnes - 1)
                total = total + reste

        titre = "Problème - Partage"
        contexte = "On veut partager équitablement."
        donnees = [f"Nombre de {objet_plur} : {total}", f"Nombre de personnes : {personnes}"]

        if reste == 0:
            question = f"Combien de {objet_plur} reçoit chaque personne ?"
            reponse = f"{part} {objet_plur}"
            steps = [
                "Pour partager équitablement, on fait une division.",
                f"Calcul : {total} ÷ {personnes} = {part}",
                f"Conclusion : chaque personne reçoit {reponse}.",
            ]
        else:
            question = f"Combien de {objet_plur} reçoit chaque personne et combien en reste-t-il ?"
            reponse = f"{part} {objet_plur} chacun, reste {reste}"
            steps = [
                "Pour partager, on fait la division euclidienne.",
                f"Calcul : {total} ÷ {personnes} = {part} et il reste {reste}",
                f"Conclusion : chacun reçoit {part} {objet_plur} et il reste {reste} {objet_plur}.",
            ]

        extra = {"total": total, "personnes": personnes, "part": part, "reste": reste, "unite": objet_plur}
        return _Problem("partage", "/", titre, contexte, donnees, question, reponse, steps, extra)
