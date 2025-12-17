"""
GM08 - Exercices figés : Grandeurs et Mesures (Longueurs, Périmètres)
=========================================================================

Chapitre pilote avec 21 exercices validés.
- FREE: ids 1-10
- PREMIUM (PRO): ids 11-20

Ce fichier est la SOURCE UNIQUE pour GM08.
Aucune génération aléatoire - exercices figés et validés.

IMPORTANT: Tout le contenu est en HTML PUR.
- Pas de Markdown (**texte**)
- Pas de LaTeX ($...$)
- Utiliser <strong>, <em>, ×, ÷, etc.

⚠️ FICHIER GÉNÉRÉ AUTOMATIQUEMENT PAR L'ADMIN
   Ne pas modifier manuellement - utiliser /admin/curriculum
"""

from typing import List, Dict, Any, Optional
import random


# =============================================================================
# 21 EXERCICES GM08 VALIDÉS - HTML PUR (sans Markdown ni LaTeX)
# =============================================================================

GM08_EXERCISES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "family": "CONVERSION",
        "difficulty": "facile",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Conversion simple (m vers cm) :</strong> Une table mesure <strong>2 mètres</strong> de long. Exprime cette longueur en centimètres.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> On veut convertir des mètres en centimètres.</li><li><strong>Méthode :</strong> On sait que 1 m = 100 cm.</li><li><strong>Calculs :</strong> 2 × 100 = 200.</li><li><strong>Conclusion :</strong> La table mesure <strong>200 cm</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 2,
        "family": "CONVERSION",
        "difficulty": "facile",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Conversion simple (cm vers mm) :</strong> Un crayon mesure <strong>15 centimètres</strong>. Exprime cette longueur en millimètres.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> On veut convertir des centimètres en millimètres.</li><li><strong>Méthode :</strong> On sait que 1 cm = 10 mm.</li><li><strong>Calculs :</strong> 15 × 10 = 150.</li><li><strong>Conclusion :</strong> Le crayon mesure <strong>150 mm</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 3,
        "family": "COMPARAISON",
        "difficulty": "facile",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Comparaison simple :</strong> Marie a un ruban de <strong>50 cm</strong> et Paul a un ruban de <strong>0,5 m</strong>. Qui a le ruban le plus long ?</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> On doit comparer deux longueurs exprimées dans des unités différentes.</li><li><strong>Méthode :</strong> Convertir dans la même unité. 0,5 m = 0,5 × 100 = 50 cm.</li><li><strong>Calculs :</strong> Marie : 50 cm, Paul : 50 cm.</li><li><strong>Conclusion :</strong> Les deux rubans ont <strong>la même longueur</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 4,
        "family": "PERIMETRE",
        "difficulty": "facile",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Périmètre d'un carré :</strong> Un carré a un côté de <strong>5 cm</strong>. Calcule son périmètre.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> Le périmètre est la somme des longueurs des côtés.</li><li><strong>Méthode :</strong> Un carré a 4 côtés égaux. Périmètre = 4 × côté.</li><li><strong>Calculs :</strong> P = 4 × 5 = 20.</li><li><strong>Conclusion :</strong> Le périmètre est de <strong>20 cm</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 5,
        "family": "CONVERSION",
        "difficulty": "moyen",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Conversion composée (km vers m) :</strong> La distance entre deux villages est de <strong>3,5 kilomètres</strong>. Exprime cette distance en mètres.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> On veut convertir des kilomètres en mètres.</li><li><strong>Méthode :</strong> On sait que 1 km = 1000 m.</li><li><strong>Calculs :</strong> 3,5 × 1000 = 3500.</li><li><strong>Conclusion :</strong> La distance est de <strong>3500 m</strong>.</li></ol><p class="trap" style="color: orange;"><strong>Piège classique :</strong> Ne pas oublier de déplacer la virgule de 3 rangs vers la droite.</p>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 6,
        "family": "CONVERSION",
        "difficulty": "moyen",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Conversion inverse (mm vers cm) :</strong> Une vis mesure <strong>35 millimètres</strong>. Exprime cette longueur en centimètres.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> On veut convertir des millimètres en centimètres (unité plus grande).</li><li><strong>Méthode :</strong> On divise par 10 car 1 cm = 10 mm.</li><li><strong>Calculs :</strong> 35 ÷ 10 = 3,5.</li><li><strong>Conclusion :</strong> La vis mesure <strong>3,5 cm</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 7,
        "family": "PERIMETRE",
        "difficulty": "moyen",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Périmètre d'un rectangle :</strong> Un rectangle a une longueur de <strong>8 cm</strong> et une largeur de <strong>5 cm</strong>. Calcule son périmètre.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> Le périmètre d'un rectangle est la somme de tous ses côtés.</li><li><strong>Méthode :</strong> P = 2 × (longueur + largeur) ou P = 2 × L + 2 × l.</li><li><strong>Calculs :</strong> P = 2 × (8 + 5) = 2 × 13 = 26.</li><li><strong>Conclusion :</strong> Le périmètre est de <strong>26 cm</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 8,
        "family": "COMPARAISON",
        "difficulty": "moyen",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Comparaison avec conversion :</strong> Range dans l'ordre croissant : <strong>2,5 m</strong>, <strong>250 cm</strong>, <strong>2500 mm</strong>, <strong>0,025 km</strong>.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> On doit comparer 4 longueurs dans des unités différentes.</li><li><strong>Méthode :</strong> Tout convertir en mètres : 2,5 m = 2,5 m ; 250 cm = 2,5 m ; 2500 mm = 2,5 m ; 0,025 km = 25 m.</li><li><strong>Calculs :</strong> 2,5 m = 2,5 m = 2,5 m < 25 m.</li><li><strong>Conclusion :</strong> Ordre : <strong>2,5 m = 250 cm = 2500 mm < 0,025 km</strong> (les trois premiers sont égaux).</li></ol><p class="trap" style="color: orange;"><strong>Piège classique :</strong> Attention, 0,025 km = 25 m, pas 0,025 m !</p>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 9,
        "family": "PROBLEME",
        "difficulty": "difficile",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Problème de trajet :</strong> Lucas fait le tour de son quartier en passant par 4 rues. La première rue mesure <strong>350 m</strong>, la deuxième <strong>0,5 km</strong>, la troisième <strong>425 m</strong> et la quatrième <strong>0,225 km</strong>. Quelle est la distance totale parcourue en mètres ?</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> On doit additionner 4 distances exprimées en unités différentes.</li><li><strong>Méthode :</strong> Convertir tout en mètres puis additionner. 0,5 km = 500 m ; 0,225 km = 225 m.</li><li><strong>Calculs :</strong> 350 + 500 + 425 + 225 = 1500.</li><li><strong>Conclusion :</strong> Lucas a parcouru <strong>1500 m</strong> (soit 1,5 km).</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 10,
        "family": "PERIMETRE",
        "difficulty": "difficile",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Périmètre complexe :</strong> Un terrain rectangulaire mesure <strong>45 m</strong> de long et <strong>30 m</strong> de large. On veut l'entourer d'une clôture. Quelle longueur de clôture faut-il acheter ? Donne le résultat en mètres puis en kilomètres.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> La clôture fait le tour du terrain, c'est donc le périmètre.</li><li><strong>Méthode :</strong> P = 2 × (L + l) puis convertir en km.</li><li><strong>Calculs :</strong> P = 2 × (45 + 30) = 2 × 75 = 150 m. En km : 150 ÷ 1000 = 0,15 km.</li><li><strong>Conclusion :</strong> Il faut <strong>150 m</strong> de clôture, soit <strong>0,15 km</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 11,
        "family": "CONVERSION",
        "difficulty": "facile",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Conversion rapide (m vers km) :</strong> Un athlète court sur une piste de <strong>400 mètres</strong>. Exprime cette distance en kilomètres.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> On veut convertir des mètres en kilomètres (unité plus grande).</li><li><strong>Méthode :</strong> On divise par 1000 car 1 km = 1000 m.</li><li><strong>Calculs :</strong> 400 ÷ 1000 = 0,4.</li><li><strong>Conclusion :</strong> La piste mesure <strong>0,4 km</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 12,
        "family": "PERIMETRE",
        "difficulty": "facile",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Périmètre d'un triangle équilatéral :</strong> Un triangle équilatéral a un côté de <strong>7 cm</strong>. Calcule son périmètre.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> Un triangle équilatéral a 3 côtés égaux.</li><li><strong>Méthode :</strong> Périmètre = 3 × côté.</li><li><strong>Calculs :</strong> P = 3 × 7 = 21.</li><li><strong>Conclusion :</strong> Le périmètre est de <strong>21 cm</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 13,
        "family": "CONVERSION",
        "difficulty": "moyen",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Double conversion :</strong> Une ficelle mesure <strong>2,75 m</strong>. Exprime cette longueur en millimètres.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> On veut passer des mètres aux millimètres.</li><li><strong>Méthode :</strong> On peut passer par les cm ou multiplier directement par 1000. 1 m = 100 cm = 1000 mm.</li><li><strong>Calculs :</strong> 2,75 × 1000 = 2750.</li><li><strong>Conclusion :</strong> La ficelle mesure <strong>2750 mm</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 14,
        "family": "COMPARAISON",
        "difficulty": "moyen",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Comparaison de périmètres :</strong> Quel polygone a le plus grand périmètre : un carré de côté <strong>6 cm</strong> ou un rectangle de <strong>7 cm</strong> sur <strong>4 cm</strong> ?</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> On doit calculer et comparer deux périmètres.</li><li><strong>Méthode :</strong> P(carré) = 4 × côté ; P(rectangle) = 2 × (L + l).</li><li><strong>Calculs :</strong> P(carré) = 4 × 6 = 24 cm. P(rectangle) = 2 × (7 + 4) = 2 × 11 = 22 cm.</li><li><strong>Conclusion :</strong> Le <strong>carré</strong> a le plus grand périmètre (24 cm > 22 cm).</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 15,
        "family": "PROBLEME",
        "difficulty": "moyen",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Problème de ruban :</strong> Léa veut entourer un cadeau rectangulaire de <strong>30 cm</strong> de long et <strong>20 cm</strong> de large avec un ruban. Elle fait un nœud qui nécessite <strong>25 cm</strong> de ruban en plus. Quelle longueur de ruban lui faut-il ?</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> Le ruban fait le tour du cadeau (périmètre) + longueur pour le nœud.</li><li><strong>Méthode :</strong> P = 2 × (L + l), puis ajouter 25 cm.</li><li><strong>Calculs :</strong> P = 2 × (30 + 20) = 2 × 50 = 100 cm. Total = 100 + 25 = 125 cm.</li><li><strong>Conclusion :</strong> Il faut <strong>125 cm</strong> de ruban (soit 1,25 m).</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 16,
        "family": "CONVERSION",
        "difficulty": "difficile",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Conversion avec décimaux :</strong> Convertis <strong>4567 mm</strong> en mètres. Donne le résultat sous forme décimale.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> On passe d'une petite unité (mm) à une grande unité (m).</li><li><strong>Méthode :</strong> 1 m = 1000 mm, donc on divise par 1000.</li><li><strong>Calculs :</strong> 4567 ÷ 1000 = 4,567.</li><li><strong>Conclusion :</strong> 4567 mm = <strong>4,567 m</strong>.</li></ol><p class="trap" style="color: orange;"><strong>Piège classique :</strong> Déplacer la virgule de 3 rangs vers la gauche (÷1000), pas vers la droite.</p>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 17,
        "family": "PERIMETRE",
        "difficulty": "difficile",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Périmètre d'une figure composée :</strong> Une figure est formée d'un carré de côté <strong>4 cm</strong> auquel on a accolé un triangle équilatéral sur l'un de ses côtés. Calcule le périmètre de cette figure.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> La figure a le périmètre du carré (sans le côté commun) + le périmètre du triangle (sans le côté commun).</li><li><strong>Méthode :</strong> P = 3 côtés du carré + 2 côtés du triangle = 3 × 4 + 2 × 4.</li><li><strong>Calculs :</strong> P = 12 + 8 = 20.</li><li><strong>Conclusion :</strong> Le périmètre est de <strong>20 cm</strong>.</li></ol><p class="trap" style="color: orange;"><strong>Piège classique :</strong> Ne pas compter le côté commun deux fois !</p>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 18,
        "family": "PROBLEME",
        "difficulty": "difficile",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Problème de course :</strong> Un coureur fait <strong>3 tours</strong> d'un stade rectangulaire de <strong>120 m</strong> de long et <strong>80 m</strong> de large, puis parcourt encore <strong>0,5 km</strong>. Quelle distance totale a-t-il parcourue en mètres ?</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> Distance = 3 × périmètre du stade + 500 m.</li><li><strong>Méthode :</strong> Calculer le périmètre du stade, multiplier par 3, ajouter 500 m.</li><li><strong>Calculs :</strong> P = 2 × (120 + 80) = 400 m. Distance tours = 3 × 400 = 1200 m. Total = 1200 + 500 = 1700 m.</li><li><strong>Conclusion :</strong> Le coureur a parcouru <strong>1700 m</strong> (soit 1,7 km).</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 19,
        "family": "COMPARAISON",
        "difficulty": "difficile",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Comparaison complexe :</strong> Un jardinier a trois parcelles : un carré de <strong>10 m</strong> de côté, un rectangle de <strong>15 m × 6 m</strong>, et un triangle équilatéral de <strong>14 m</strong> de côté. Laquelle nécessite le plus de clôture ?</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> Comparer les périmètres des trois figures.</li><li><strong>Méthode :</strong> P(carré) = 4 × 10 ; P(rectangle) = 2 × (15 + 6) ; P(triangle) = 3 × 14.</li><li><strong>Calculs :</strong> P(carré) = 40 m. P(rectangle) = 42 m. P(triangle) = 42 m.</li><li><strong>Conclusion :</strong> Le <strong>rectangle et le triangle</strong> nécessitent autant de clôture (42 m chacun), plus que le carré (40 m).</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 20,
        "family": "PROBLEME",
        "difficulty": "difficile",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Problème de planification :</strong> Pour un projet d'arts plastiques, Emma doit découper des bandes de papier de <strong>5 cm</strong> de large dans une feuille de <strong>1,2 m</strong> de long. Combien de bandes peut-elle découper ? Quelle longueur de papier restera-t-il ?</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Compréhension :</strong> On découpe des bandes de 5 cm dans 1,2 m = 120 cm.</li><li><strong>Méthode :</strong> Division euclidienne : 120 ÷ 5 = quotient (nombre de bandes) + reste.</li><li><strong>Calculs :</strong> 120 ÷ 5 = 24 exactement. 24 × 5 = 120, reste = 0.</li><li><strong>Conclusion :</strong> Emma peut découper <strong>24 bandes</strong> et il ne restera <strong>pas de papier</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 21,
        "family": "CALCUL_DUREE",
        "difficulty": "difficile",
        "offer": "free",
        "variables": None,
        "enonce_html": """test ouss""",
        "solution_html": """<h4>Correction détaillée</h4>
<ol>
  <li><strong>Compréhension :</strong> </li>
  <li><strong>Méthode :</strong> </li>
  <li><strong>Calculs :</strong> </li>
  <li><strong>Conclusion :</strong> </li>
</ol>""",
        "needs_svg": True,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
]


# =============================================================================
# FONCTIONS D'ACCÈS AUX EXERCICES (Compatible avec handlers)
# =============================================================================


def get_gm08_exercises(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filtre les exercices selon les critères.
    
    Args:
        offer: "free" ou "pro" (None = tous selon règles)
        difficulty: "facile", "moyen", "difficile" (None = tous)
    
    Returns:
        Liste d'exercices filtrés
    """
    exercises = GM08_EXERCISES
    
    # Filtrer par offer
    if offer:
        offer = offer.lower()
        if offer == "free":
            exercises = [ex for ex in exercises if ex["offer"] == "free"]
        elif offer == "pro":
            pass  # PRO voit tout
    else:
        # Par défaut, FREE ne voit que free
        exercises = [ex for ex in exercises if ex["offer"] == "free"]
    
    # Filtrer par difficulté
    if difficulty:
        difficulty = difficulty.lower()
        exercises = [ex for ex in exercises if ex["difficulty"] == difficulty]
    
    return exercises


def get_random_gm08_exercise(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    seed: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Sélectionne UN exercice aléatoire.
    
    Args:
        offer: "free" ou "pro" (None = free par défaut)
        difficulty: "facile", "moyen", "difficile" (None = tous)
        seed: graine pour reproductibilité (optionnel)
    
    Returns:
        Un exercice aléatoire ou None si aucun disponible
    """
    available = get_gm08_exercises(offer=offer, difficulty=difficulty)
    
    if not available:
        return None
    
    if seed is not None:
        random.seed(seed)
    
    return random.choice(available)


def get_gm08_batch(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    count: int = 1,
    seed: Optional[int] = None
) -> tuple:
    """
    Génère un batch d'exercices SANS DOUBLONS.
    
    Args:
        offer: "free" ou "pro"
        difficulty: filtre optionnel
        count: nombre d'exercices demandés
        seed: graine pour reproductibilité
    
    Returns:
        Tuple (exercices: List, batch_metadata: Dict)
    """
    available = get_gm08_exercises(offer=offer, difficulty=difficulty)
    pool_size = len(available)
    
    batch_meta = {
        "requested": count,
        "available": pool_size,
        "returned": 0,
        "filters": {
            "offer": offer or "free",
            "difficulty": difficulty
        }
    }
    
    if pool_size == 0:
        batch_meta["warning"] = f"Aucun exercice disponible pour les filtres sélectionnés."
        return [], batch_meta
    
    # Mélanger avec seed pour reproductibilité
    if seed is not None:
        random.seed(seed)
    
    shuffled = available.copy()
    random.shuffle(shuffled)
    
    # Prendre au maximum ce qui est disponible
    actual_count = min(count, pool_size)
    selected = shuffled[:actual_count]
    
    batch_meta["returned"] = actual_count
    
    if actual_count < count:
        batch_meta["warning"] = f"Seulement {pool_size} exercices disponibles pour les filtres sélectionnés ({count} demandés)."
    
    return selected, batch_meta


def get_exercise_by_seed_index(
    offer: Optional[str] = None,
    difficulty: Optional[str] = None,
    seed: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Sélectionne UN exercice de manière déterministe.
    """
    available = get_gm08_exercises(offer=offer, difficulty=difficulty)
    
    if not available:
        return None
    
    if seed is not None:
        random.seed(seed)
        index = random.randint(0, len(available) - 1)
    else:
        index = random.randint(0, len(available) - 1)
    
    return available[index]


def get_gm08_stats() -> Dict[str, Any]:
    """Statistiques sur les exercices"""
    exercises = GM08_EXERCISES
    
    stats = {
        "total": len(exercises),
        "by_offer": {"free": 0, "pro": 0},
        "by_difficulty": {"facile": 0, "moyen": 0, "difficile": 0},
        "by_family": {}
    }
    
    for ex in exercises:
        stats["by_offer"][ex["offer"]] = stats["by_offer"].get(ex["offer"], 0) + 1
        stats["by_difficulty"][ex["difficulty"]] = stats["by_difficulty"].get(ex["difficulty"], 0) + 1
        
        family = ex["family"]
        stats["by_family"][family] = stats["by_family"].get(family, 0) + 1
    
    return stats
