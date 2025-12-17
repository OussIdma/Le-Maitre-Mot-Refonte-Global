"""
GM07 - Exercices figés : Durées et lecture de l'heure
=========================================================

Chapitre pilote avec 22 exercices validés.
- FREE: ids 1-10
- PREMIUM (PRO): ids 11-20

Ce fichier est la SOURCE UNIQUE pour GM07.
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
# 22 EXERCICES GM07 VALIDÉS - HTML PUR (sans Markdown ni LaTeX)
# =============================================================================

GM07_EXERCISES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "family": "LECTURE_HORLOGE",
        "difficulty": "facile",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Lecture simple de l'heure :</strong> L'horloge de la cuisine indique l'heure à laquelle le repas de midi est prêt. L'aiguille des heures (courte) est sur le 12 et l'aiguille des minutes (longue) est sur le 3. Quelle heure est-il ? (Format HHhMM)</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>L'aiguille des heures pointe vers le <strong>12</strong>.</li><li>L'aiguille des minutes est sur le 3, ce qui correspond à 3 × 5 = 15 minutes.</li><li>L'heure affichée est <strong>12h15</strong>.</li></ol><p style="color: orange;"><strong>Piège classique (facile) :</strong> Ne confondez pas l'aiguille des heures et celle des minutes, surtout quand l'aiguille des minutes est sur un nombre (ex: le 3 pour 15 min).</p>""",
        "needs_svg": True,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 2,
        "family": "LECTURE_HORLOGE",
        "difficulty": "moyen",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Lecture à la minute près :</strong> Le réveil de Léo affiche l'heure de son entraînement de basket, qui a lieu en fin d'après-midi. L'aiguille des heures est entre le 5 et le 6, et l'aiguille des minutes est sur la 47ème petite graduation. Quelle heure est-il ? (Format HHhMM sur 24h)</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>L'heure indiquée est en soirée, nous utilisons le format 24h. L'aiguille des heures se rapproche du 6 (pour 18h).</li><li>L'aiguille des minutes indique la 47ème minute, soit <strong>47 min</strong>.</li><li>L'heure complète est <strong>17h47</strong>.</li></ol>""",
        "needs_svg": True,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 3,
        "family": "LECTURE_HORLOGE",
        "difficulty": "difficile",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Anticipation de l'heure :</strong> L'horloge du CDI affiche 09h53. Décris précisément où se situent les aiguilles à cet instant. (On attend la position de l'aiguille des heures et des minutes).</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li><strong>Aiguille des minutes :</strong> Elle pointe exactement vers la 53ème graduation après le 12 (légèrement après le 10 sur le cadran).</li><li><strong>Aiguille des heures :</strong> Elle a fait 53/60 du trajet entre le 9 et le 10. Elle est donc <strong>très proche du 10</strong>, mais ne l'a pas encore atteint.</li><li>L'heure affichée est <strong>09h53</strong>.</li></ol><p style="color: orange;"><strong>Piège classique (difficile) :</strong> Quand l'heure est proche de l'heure pile suivante (ex: 09h53), l'aiguille des heures doit être très avancée. L'élève doit comprendre la rotation continue.</p>""",
        "needs_svg": True,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 4,
        "family": "LECTURE_HORLOGE",
        "difficulty": "moyen",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Lecture 'moins le quart' et ambiguïté :</strong> Quelle heure est-il lorsque l'aiguille des heures est juste avant le 4 et que l'aiguille des minutes est sur le 9 ? On suppose que c'est l'après-midi. Quelle est l'heure au format 24h ? (Format HHhMM)</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>L'aiguille des minutes est sur le 9, ce qui signifie 9 × 5 = 45 minutes.</li><li>L'aiguille des heures est <strong>avant le 4</strong>, l'heure est donc 3 heures et 45 minutes.</li><li>Puisque l'on suppose l'après-midi, on ajoute 12 heures : 3 h + 12 h = 15 h.</li><li>L'heure affichée est <strong>15h45</strong>.</li></ol>""",
        "needs_svg": True,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 5,
        "family": "LECTURE_HORLOGE",
        "difficulty": "facile",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Lecture d'heure exacte :</strong> L'horloge murale de la gare affiche l'heure de départ d'un TGV. L'aiguille des heures est sur le 7 et l'aiguille des minutes est sur le 12. Quelle heure est-il ? (Format HHhMM)</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>L'aiguille des heures est sur le <strong>7</strong>.</li><li>L'aiguille des minutes est sur le 12, ce qui signifie 00 minute.</li><li>L'heure affichée est <strong>07h00</strong>.</li></ol>""",
        "needs_svg": True,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 6,
        "family": "CONVERSION",
        "difficulty": "facile",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Conversion simple (h vers min) :</strong> Le cours de technologie de Monsieur Martin dure <strong>3 heures</strong>. Exprime cette durée uniquement en minutes.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>On sait que 1 h = 60 min.</li><li>On effectue la multiplication : 3 × 60 = 180.</li><li>La durée est de <strong>180 minutes</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 7,
        "family": "CONVERSION",
        "difficulty": "moyen",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Conversion min vers h et min :</strong> Le temps passé par un athlète à courir est de <strong>215 minutes</strong>. Convertis cette durée en heures et minutes.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>On cherche combien de fois 60 minutes (1 heure) sont contenues dans 215 minutes.</li><li>215 ÷ 60. On trouve 3 heures (3 × 60 = 180).</li><li>On calcule le reste : 215 − 180 = 35 minutes.</li><li>La durée est de <strong>3 h 35 min</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 8,
        "family": "CONVERSION",
        "difficulty": "moyen",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Conversion composée (h, min vers sec) :</strong> Un élève a mis <strong>1 heure, 10 minutes et 30 secondes</strong> pour faire ses devoirs. Convertis cette durée totale en secondes.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>Conversion des heures : 1 h = 1 × 3600 = 3600 secondes.</li><li>Conversion des minutes : 10 min = 10 × 60 = 600 secondes.</li><li>Addition de toutes les secondes : 3600 + 600 + 30 = 4230.</li><li>La durée totale est de <strong>4230 secondes</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 9,
        "family": "CONVERSION",
        "difficulty": "difficile",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Piège de l'heure décimale (h vers h et min) :</strong> Un système informatique indique qu'un processus a duré <strong>2,75 heures</strong>. Convertis cette durée en heures et minutes.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>La partie entière est 2, soit <strong>2 heures</strong>.</li><li>La partie décimale est 0,75. Il faut la convertir en minutes en multipliant par 60.</li><li>Calcul : 0,75 × 60 = 45.</li><li>La durée est de <strong>2 h 45 min</strong>.</li></ol><p style="color: orange;"><strong>Piège classique (difficile) :</strong> Attention ! 0,75 h n'est PAS 75 minutes. Les élèves doivent comprendre que le temps n'est pas en base 100.</p>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 10,
        "family": "CONVERSION",
        "difficulty": "facile",
        "offer": "free",
        "variables": None,
        "enonce_html": """<p><strong>Conversion inverse (sec vers min) :</strong> Une chanson dure <strong>300 secondes</strong>. Exprime cette durée uniquement en minutes.</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>On sait que 60 secondes = 1 minute.</li><li>On effectue la division : 300 ÷ 60 = 5.</li><li>La durée est de <strong>5 minutes</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 11,
        "family": "CALCUL_DUREE",
        "difficulty": "moyen",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Calcul de durée simple avec report :</strong> Quelle est la durée d'un vol qui décolle à <strong>14h40</strong> et atterrit à <strong>17h05</strong> ? (Format X h Y min)</p>""",
        "solution_html": """<h4>Correction détaillée (Méthode par paliers)</h4><ol><li><strong>Palier 1 :</strong> De 14h40 à 15h00 : 20 minutes.</li><li><strong>Palier 2 :</strong> De 15h00 à 17h00 : 2 heures.</li><li><strong>Palier 3 :</strong> De 17h00 à 17h05 : 5 minutes.</li><li><strong>Total :</strong> 2 h 25 min.</li></ol><p>La durée du vol est de <strong>2 h 25 min</strong>.</p>""",
        "needs_svg": True,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 12,
        "family": "CALCUL_DUREE",
        "difficulty": "moyen",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Calcul de durée sans passage de jour :</strong> Un documentaire sur la nature commence à <strong>18h10</strong> et se termine à <strong>21h55</strong>. Quelle est la durée totale du documentaire ? (Format X h Y min)</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>Heures : 21 − 18 = 3 h.</li><li>Minutes : 55 − 10 = 45 min.</li><li>Durée totale : <strong>3 h 45 min</strong>.</li></ol>""",
        "needs_svg": True,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 13,
        "family": "CALCUL_DUREE",
        "difficulty": "difficile",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Calcul de durée avec passage de jour :</strong> Une famille prend l'avion pour la Réunion. Le vol part à <strong>23h15</strong> (J1) et arrive à <strong>08h45</strong> (J2). Quelle est la durée totale du vol ? (Format X h Y min)</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>De 23h15 à 00h00 : 45 min.</li><li>De 00h00 à 08h00 : 8 h.</li><li>De 08h00 à 08h45 : 45 min.</li><li>Total : 8 h + (45 + 45) = 8 h 90 min = <strong>9 h 30 min</strong>.</li></ol>""",
        "needs_svg": True,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 14,
        "family": "CALCUL_DUREE",
        "difficulty": "facile",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Durée sans report d'heure :</strong> Le temps de récréation de l'après-midi commence à <strong>15h30</strong> et se termine à <strong>15h50</strong>. Quelle est la durée de la récréation ? (Format X min)</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>On garde la même heure (15h).</li><li>50 − 30 = <strong>20 minutes</strong>.</li></ol>""",
        "needs_svg": True,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 15,
        "family": "CALCUL_DUREE",
        "difficulty": "moyen",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Piège de la soustraction des minutes :</strong> Quelle est la durée d'une partie de jeu vidéo qui commence à <strong>16h55</strong> et se termine à <strong>17h35</strong> ? (Format X h Y min)</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>De 16h55 à 17h00 : 5 min.</li><li>De 17h00 à 17h35 : 35 min.</li><li>Total : <strong>40 minutes</strong>.</li></ol>""",
        "needs_svg": True,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 16,
        "family": "CALCUL_DUREE",
        "difficulty": "difficile",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Durée d'un événement fractionné :</strong> Un cuisinier travaille de <strong>10h10 à 10h40</strong>, puis reprend de <strong>11h05 à 11h55</strong>. Combien de temps total a-t-il cuisiné ? (Format X h Y min)</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>Période 1 : 30 min.</li><li>Période 2 : 50 min.</li><li>Total : 80 min = <strong>1 h 20 min</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 17,
        "family": "PROBLEME_DUREES",
        "difficulty": "facile",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Problème : Recherche d'heure de début :</strong> Le bus scolaire arrive à l'école à <strong>08h05</strong>. Le trajet dure <strong>30 minutes</strong>. À quelle heure le bus doit-il partir ? (Format HHhMM)</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>08h05 − 30 min.</li><li>On emprunte 1 h : 07h65 − 30 = 07h35.</li><li>Départ : <strong>07h35</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 18,
        "family": "PROBLEME_DUREES",
        "difficulty": "moyen",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Problème : Recherche de l'heure de début :</strong> Le film dure <strong>1 h 55 min</strong> et se termine à <strong>21h10</strong>. À quelle heure a-t-il commencé ? (Format HHhMM)</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>21h10 − 1h = 20h10.</li><li>20h10 − 55 min : emprunt → 19h70 − 55 = 19h15.</li><li>Début : <strong>19h15</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 19,
        "family": "PROBLEME_DUREES",
        "difficulty": "difficile",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Problème : Addition de trois durées :</strong> Équipe A : <strong>45 min</strong>, équipe B : <strong>1 h 20</strong>, équipe C : <strong>1 h 05</strong>. Quel est le temps total ? (Format X h Y min)</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>Heures : 1 + 1 = 2 h.</li><li>Minutes : 45 + 20 + 5 = 70 min = 1 h 10.</li><li>Total : 2 h + 1 h 10 = <strong>3 h 10</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 20,
        "family": "PROBLEME_DUREES",
        "difficulty": "difficile",
        "offer": "pro",
        "variables": None,
        "enonce_html": """<p><strong>Problème de planification :</strong> Devoir à rendre à <strong>18h30</strong>. Il faut <strong>1 h 40</strong> pour le faire et <strong>25 min</strong> pour relire. À quelle heure commencer au plus tard ? (Format HHhMM)</p>""",
        "solution_html": """<h4>Correction détaillée</h4><ol><li>Durée totale : 1h40 + 25 = 2h05.</li><li>18h30 − 2h05 = 16h25.</li><li>Début au plus tard : <strong>16h25</strong>.</li></ol>""",
        "needs_svg": False,
        "exercise_type": None,
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 21,
        "family": "LECTURE_HORLOGE",
        "difficulty": "moyen",
        "offer": "free",
        "variables": None,
        "enonce_html": """Test énoncé ici""",
        "solution_html": """<h4>test Correction détaillée</h4>
<ol>
  <li><strong>Compréhension :</strong> </li>
  <li><strong>Méthode :</strong> </li>
  <li><strong>Calculs :</strong> </li>
  <li><strong>Conclusion :</strong> </li>
</ol>""",
        "needs_svg": True,
        "exercise_type": "PLACER_AIGUILLES",
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
    {
        "id": 22,
        "family": "DUREES",
        "difficulty": "difficile",
        "offer": "free",
        "variables": None,
        "enonce_html": """Test 2 Ouss""",
        "solution_html": """<h4>Correction détaillée test 2</h4>
<ol>
  <li><strong>Compréhension :</strong> </li>
  <li><strong>Méthode :</strong> </li>
  <li><strong>Calculs :</strong> </li>
  <li><strong>Conclusion :</strong> </li>
</ol>""",
        "needs_svg": True,
        "exercise_type": "PERIMETRE",
        "svg_enonce_brief": None,
        "svg_solution_brief": None
    },
]


# =============================================================================
# FONCTIONS D'ACCÈS AUX EXERCICES (Compatible avec handlers)
# =============================================================================


def get_gm07_exercises(
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
    exercises = GM07_EXERCISES
    
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


def get_random_gm07_exercise(
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
    available = get_gm07_exercises(offer=offer, difficulty=difficulty)
    
    if not available:
        return None
    
    if seed is not None:
        random.seed(seed)
    
    return random.choice(available)


def get_gm07_batch(
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
    available = get_gm07_exercises(offer=offer, difficulty=difficulty)
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
    available = get_gm07_exercises(offer=offer, difficulty=difficulty)
    
    if not available:
        return None
    
    if seed is not None:
        random.seed(seed)
        index = random.randint(0, len(available) - 1)
    else:
        index = random.randint(0, len(available) - 1)
    
    return available[index]


def get_gm07_stats() -> Dict[str, Any]:
    """Statistiques sur les exercices"""
    exercises = GM07_EXERCISES
    
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
