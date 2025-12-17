"""
Service de rendu SVG pour les figures pédagogiques.

Ce service génère des figures SVG basées sur le type d'exercice.
V1: Génération simple basée sur des mots-clés (horloge, timeline, etc.)

Usage:
    from services.svg_render_service import render_svg_from_brief
    
    svg = render_svg_from_brief("horloge montrant 12h15", hour=12, minute=15)
"""

import math
from typing import Optional


def render_svg_from_brief(
    brief: str,
    hour: Optional[int] = None,
    minute: Optional[int] = None,
    **kwargs
) -> str:
    """
    Génère un SVG basé sur le brief de l'exercice.
    
    Args:
        brief: Description de la figure attendue
        hour: Heure à afficher (pour horloge)
        minute: Minute à afficher (pour horloge)
        **kwargs: Paramètres additionnels selon le type
    
    Returns:
        String SVG complet ou placeholder si type inconnu
    """
    brief_lower = brief.lower() if brief else ""
    
    # Détection du type de figure basée sur mots-clés
    if any(word in brief_lower for word in ["horloge", "montre", "cadran", "aiguille", "heure"]):
        return _render_clock_svg(hour or 12, minute or 0)
    
    elif any(word in brief_lower for word in ["droite du temps", "timeline", "frise", "chronologie"]):
        return _render_timeline_svg(**kwargs)
    
    elif any(word in brief_lower for word in ["règle", "graduation", "longueur"]):
        return _render_ruler_svg(**kwargs)
    
    elif any(word in brief_lower for word in ["périmètre", "rectangle", "carré"]):
        return _render_shape_svg(**kwargs)
    
    else:
        # Fallback: placeholder propre avec le brief
        return _render_placeholder_svg(brief)


def _render_clock_svg(hour: int, minute: int) -> str:
    """
    Génère un SVG d'horloge analogique.
    
    L'horloge affiche l'heure spécifiée avec :
    - Un cadran avec les 12 chiffres
    - Une aiguille des heures (courte, épaisse)
    - Une aiguille des minutes (longue, fine)
    """
    # Normaliser l'heure (format 12h)
    hour = hour % 12
    
    # Calcul des angles (0° = 12h, sens horaire)
    # L'aiguille des heures avance aussi en fonction des minutes
    hour_angle = (hour + minute / 60) * 30 - 90  # 30° par heure
    minute_angle = minute * 6 - 90  # 6° par minute
    
    # Conversion en radians
    hour_rad = math.radians(hour_angle)
    minute_rad = math.radians(minute_angle)
    
    # Centre et rayons
    cx, cy = 100, 100
    radius = 80
    
    # Position des aiguilles
    hour_length = 45
    minute_length = 65
    
    hour_x = cx + hour_length * math.cos(hour_rad)
    hour_y = cy + hour_length * math.sin(hour_rad)
    
    minute_x = cx + minute_length * math.cos(minute_rad)
    minute_y = cy + minute_length * math.sin(minute_rad)
    
    # Générer les chiffres du cadran
    numbers_svg = ""
    for i in range(1, 13):
        angle = math.radians(i * 30 - 90)
        num_x = cx + (radius - 15) * math.cos(angle)
        num_y = cy + (radius - 15) * math.sin(angle) + 5
        numbers_svg += f'    <text x="{num_x:.1f}" y="{num_y:.1f}" text-anchor="middle" font-size="14" font-weight="500" fill="#333">{i}</text>\n'
    
    # Générer les graduations
    ticks_svg = ""
    for i in range(60):
        angle = math.radians(i * 6 - 90)
        if i % 5 == 0:
            # Grande graduation (heures)
            inner_r = radius - 10
            outer_r = radius - 3
            stroke_width = 2
        else:
            # Petite graduation (minutes)
            inner_r = radius - 5
            outer_r = radius - 3
            stroke_width = 1
        
        x1 = cx + inner_r * math.cos(angle)
        y1 = cy + inner_r * math.sin(angle)
        x2 = cx + outer_r * math.cos(angle)
        y2 = cy + outer_r * math.sin(angle)
        
        ticks_svg += f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#666" stroke-width="{stroke_width}"/>\n'
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200" style="max-width: 100%; height: auto;">
  <!-- Fond du cadran -->
  <circle cx="{cx}" cy="{cy}" r="{radius}" fill="#fefefe" stroke="#333" stroke-width="3"/>
  
  <!-- Graduations -->
{ticks_svg}
  <!-- Chiffres -->
{numbers_svg}
  <!-- Aiguille des heures (courte, épaisse) -->
  <line x1="{cx}" y1="{cy}" x2="{hour_x:.1f}" y2="{hour_y:.1f}" 
        stroke="#1a1a1a" stroke-width="5" stroke-linecap="round"/>
  
  <!-- Aiguille des minutes (longue, fine) -->
  <line x1="{cx}" y1="{cy}" x2="{minute_x:.1f}" y2="{minute_y:.1f}" 
        stroke="#333" stroke-width="3" stroke-linecap="round"/>
  
  <!-- Centre -->
  <circle cx="{cx}" cy="{cy}" r="5" fill="#333"/>
  
  <!-- Légende -->
  <text x="{cx}" y="190" text-anchor="middle" font-size="10" fill="#666">
    Figure : Horloge analogique
  </text>
</svg>'''
    
    return svg


def _render_timeline_svg(**kwargs) -> str:
    """
    Génère un SVG de droite du temps / timeline.
    """
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 100" width="400" height="100" style="max-width: 100%; height: auto;">
  <!-- Ligne principale -->
  <line x1="20" y1="50" x2="380" y2="50" stroke="#333" stroke-width="2"/>
  
  <!-- Flèche droite -->
  <polygon points="380,50 370,45 370,55" fill="#333"/>
  
  <!-- Graduations et labels -->
  <g font-size="12" text-anchor="middle" fill="#333">
    <line x1="50" y1="45" x2="50" y2="55" stroke="#333" stroke-width="2"/>
    <text x="50" y="70">0</text>
    
    <line x1="130" y1="45" x2="130" y2="55" stroke="#333" stroke-width="2"/>
    <text x="130" y="70">1h</text>
    
    <line x1="210" y1="45" x2="210" y2="55" stroke="#333" stroke-width="2"/>
    <text x="210" y="70">2h</text>
    
    <line x1="290" y1="45" x2="290" y2="55" stroke="#333" stroke-width="2"/>
    <text x="290" y="70">3h</text>
    
    <line x1="370" y1="45" x2="370" y2="55" stroke="#333" stroke-width="2"/>
    <text x="370" y="70">4h</text>
  </g>
  
  <!-- Titre -->
  <text x="200" y="20" text-anchor="middle" font-size="12" fill="#666">
    Droite du temps (graduée en heures)
  </text>
</svg>'''
    
    return svg


def _render_ruler_svg(**kwargs) -> str:
    """
    Génère un SVG de règle graduée.
    """
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 70" width="320" height="70" style="max-width: 100%; height: auto;">
  <!-- Corps de la règle -->
  <rect x="10" y="20" width="300" height="35" fill="#f5f5dc" stroke="#333" stroke-width="2" rx="2"/>
  
  <!-- Graduations cm -->
  <g stroke="#333" stroke-width="1">
    <line x1="20" y1="20" x2="20" y2="35"/><text x="20" y="15" font-size="10" text-anchor="middle">0</text>
    <line x1="50" y1="20" x2="50" y2="35"/><text x="50" y="15" font-size="10" text-anchor="middle">1</text>
    <line x1="80" y1="20" x2="80" y2="35"/><text x="80" y="15" font-size="10" text-anchor="middle">2</text>
    <line x1="110" y1="20" x2="110" y2="35"/><text x="110" y="15" font-size="10" text-anchor="middle">3</text>
    <line x1="140" y1="20" x2="140" y2="35"/><text x="140" y="15" font-size="10" text-anchor="middle">4</text>
    <line x1="170" y1="20" x2="170" y2="35"/><text x="170" y="15" font-size="10" text-anchor="middle">5</text>
    <line x1="200" y1="20" x2="200" y2="35"/><text x="200" y="15" font-size="10" text-anchor="middle">6</text>
    <line x1="230" y1="20" x2="230" y2="35"/><text x="230" y="15" font-size="10" text-anchor="middle">7</text>
    <line x1="260" y1="20" x2="260" y2="35"/><text x="260" y="15" font-size="10" text-anchor="middle">8</text>
    <line x1="290" y1="20" x2="290" y2="35"/><text x="290" y="15" font-size="10" text-anchor="middle">9</text>
  </g>
  
  <!-- Graduations mm (petites) -->
  <g stroke="#666" stroke-width="0.5">
    <line x1="23" y1="20" x2="23" y2="27"/>
    <line x1="26" y1="20" x2="26" y2="27"/>
    <line x1="29" y1="20" x2="29" y2="27"/>
    <line x1="32" y1="20" x2="32" y2="27"/>
    <line x1="35" y1="20" x2="35" y2="30"/>
    <line x1="38" y1="20" x2="38" y2="27"/>
    <line x1="41" y1="20" x2="41" y2="27"/>
    <line x1="44" y1="20" x2="44" y2="27"/>
    <line x1="47" y1="20" x2="47" y2="27"/>
  </g>
  
  <!-- Légende -->
  <text x="160" y="65" text-anchor="middle" font-size="9" fill="#666">
    Règle graduée en centimètres (cm)
  </text>
</svg>'''
    
    return svg


def _render_shape_svg(**kwargs) -> str:
    """
    Génère un SVG de forme géométrique (rectangle par défaut).
    """
    width = kwargs.get('width', 120)
    height = kwargs.get('height', 80)
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150" width="200" height="150" style="max-width: 100%; height: auto;">
  <!-- Rectangle -->
  <rect x="40" y="30" width="{width}" height="{height}" fill="none" stroke="#2563eb" stroke-width="2"/>
  
  <!-- Cotations -->
  <!-- Largeur (haut) -->
  <line x1="40" y1="20" x2="{40 + width}" y2="20" stroke="#666" stroke-width="1"/>
  <line x1="40" y1="15" x2="40" y2="25" stroke="#666" stroke-width="1"/>
  <line x1="{40 + width}" y1="15" x2="{40 + width}" y2="25" stroke="#666" stroke-width="1"/>
  <text x="{40 + width/2}" y="15" text-anchor="middle" font-size="11" fill="#333">L</text>
  
  <!-- Hauteur (droite) -->
  <line x1="{40 + width + 10}" y1="30" x2="{40 + width + 10}" y2="{30 + height}" stroke="#666" stroke-width="1"/>
  <line x1="{40 + width + 5}" y1="30" x2="{40 + width + 15}" y2="30" stroke="#666" stroke-width="1"/>
  <line x1="{40 + width + 5}" y1="{30 + height}" x2="{40 + width + 15}" y2="{30 + height}" stroke="#666" stroke-width="1"/>
  <text x="{40 + width + 25}" y="{30 + height/2 + 4}" font-size="11" fill="#333">l</text>
  
  <!-- Légende -->
  <text x="100" y="140" text-anchor="middle" font-size="10" fill="#666">
    Rectangle (L × l)
  </text>
</svg>'''
    
    return svg


def _render_placeholder_svg(brief: str) -> str:
    """
    Génère un SVG placeholder avec le brief affiché.
    """
    # Tronquer le brief si trop long
    display_brief = brief[:80] + "..." if len(brief) > 80 else brief
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 120" width="300" height="120" style="max-width: 100%; height: auto;">
  <!-- Fond -->
  <rect x="5" y="5" width="290" height="110" fill="#f8fafc" stroke="#e2e8f0" stroke-width="2" rx="8"/>
  
  <!-- Icône figure -->
  <g transform="translate(130, 25)">
    <rect x="0" y="0" width="40" height="30" fill="none" stroke="#94a3b8" stroke-width="2" rx="2"/>
    <circle cx="12" cy="12" r="5" fill="#94a3b8"/>
    <polygon points="5,25 20,15 28,22 35,12 40,25" fill="#94a3b8"/>
  </g>
  
  <!-- Texte -->
  <text x="150" y="75" text-anchor="middle" font-size="11" fill="#64748b">
    Figure à visualiser :
  </text>
  <text x="150" y="95" text-anchor="middle" font-size="10" fill="#94a3b8" font-style="italic">
    {display_brief}
  </text>
</svg>'''
    
    return svg


def _render_clock_empty_svg() -> str:
    """
    Génère un SVG d'horloge VIDE (sans aiguilles).
    Pour les exercices de type PLACER_AIGUILLES.
    """
    cx, cy = 100, 100
    radius = 80
    
    # Générer les chiffres du cadran
    numbers_svg = ""
    for i in range(1, 13):
        angle = math.radians(i * 30 - 90)
        num_x = cx + (radius - 15) * math.cos(angle)
        num_y = cy + (radius - 15) * math.sin(angle) + 5
        numbers_svg += f'    <text x="{num_x:.1f}" y="{num_y:.1f}" text-anchor="middle" font-size="14" font-weight="500" fill="#333">{i}</text>\n'
    
    # Générer les graduations
    ticks_svg = ""
    for i in range(60):
        angle = math.radians(i * 6 - 90)
        if i % 5 == 0:
            inner_r = radius - 10
            outer_r = radius - 3
            stroke_width = 2
        else:
            inner_r = radius - 5
            outer_r = radius - 3
            stroke_width = 1
        
        x1 = cx + inner_r * math.cos(angle)
        y1 = cy + inner_r * math.sin(angle)
        x2 = cx + outer_r * math.cos(angle)
        y2 = cy + outer_r * math.sin(angle)
        
        ticks_svg += f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#666" stroke-width="{stroke_width}"/>\n'
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200" style="max-width: 100%; height: auto;">
  <!-- Fond du cadran -->
  <circle cx="{cx}" cy="{cy}" r="{radius}" fill="#fefefe" stroke="#333" stroke-width="3"/>
  
  <!-- Graduations -->
{ticks_svg}
  <!-- Chiffres -->
{numbers_svg}
  <!-- Centre (sans aiguilles) -->
  <circle cx="{cx}" cy="{cy}" r="5" fill="#333"/>
  
  <!-- Instruction -->
  <text x="{cx}" y="190" text-anchor="middle" font-size="9" fill="#666" font-style="italic">
    Place les aiguilles pour indiquer l'heure
  </text>
</svg>'''
    
    return svg


def render_clock_for_exercise(exercise: dict) -> Optional[str]:
    """
    Génère le SVG approprié pour un exercice donné.
    
    Analyse l'énoncé pour extraire l'heure si possible,
    sinon utilise une heure par défaut basée sur l'ID.
    
    Args:
        exercise: Dictionnaire de l'exercice
    
    Returns:
        SVG string ou None si needs_svg est False
    """
    if not exercise.get("needs_svg", False):
        return None
    
    family = exercise.get("family", "").upper()
    enonce = exercise.get("enonce_html", "")
    exercise_id = exercise.get("id", 1)
    
    # Si c'est un exercice de lecture d'horloge
    if family == "LECTURE_HORLOGE":
        # Essayer d'extraire l'heure depuis l'énoncé
        hour, minute = _extract_time_from_enonce(enonce, exercise_id)
        return _render_clock_svg(hour, minute)
    
    # Si c'est un exercice de durées (peut nécessiter timeline)
    elif family == "DUREES":
        return _render_timeline_svg()
    
    # Fallback générique
    brief = f"Figure pour exercice {family}"
    return render_svg_from_brief(brief)


def _extract_time_from_enonce(enonce: str, exercise_id: int) -> tuple:
    """
    Tente d'extraire l'heure depuis l'énoncé.
    Retourne une heure par défaut basée sur l'ID si extraction échoue.
    """
    import re
    
    # Patterns pour extraire l'heure
    # Pattern 1: "HHhMM" ou "HH h MM"
    match = re.search(r'(\d{1,2})\s*h\s*(\d{1,2})', enonce, re.IGNORECASE)
    if match:
        return int(match.group(1)), int(match.group(2))
    
    # Pattern 2: "sur le X" pour l'aiguille des heures
    hour_match = re.search(r"aiguille des heures.*?(?:sur le|pointe vers le?)\s*(\d{1,2})", enonce, re.IGNORECASE)
    minute_match = re.search(r"aiguille des minutes.*?(?:sur le|pointe vers le?)\s*(\d{1,2})", enonce, re.IGNORECASE)
    
    hour = 12
    minute = 0
    
    if hour_match:
        hour = int(hour_match.group(1))
    
    if minute_match:
        # Si "sur le 3" -> 15 minutes
        min_val = int(minute_match.group(1))
        if min_val <= 12:
            minute = min_val * 5
        else:
            minute = min_val
    
    # Si rien trouvé, utiliser des heures variées basées sur l'ID
    if hour == 12 and minute == 0:
        default_times = [
            (12, 15), (5, 47), (9, 53), (3, 45), (7, 0),
            (10, 30), (2, 20), (8, 35), (11, 5), (4, 50),
            (1, 15), (6, 25), (9, 40), (3, 10), (7, 55),
            (12, 45), (5, 30), (8, 15), (11, 50), (2, 5)
        ]
        idx = (exercise_id - 1) % len(default_times)
        return default_times[idx]
    
    return hour, minute


# =============================================================================
# GÉNÉRATION SVG AVEC TYPES D'EXERCICES
# =============================================================================

import logging
_svg_logger = logging.getLogger("svg_render_service")

def generate_exercise_svgs(exercise: dict) -> dict:
    """
    Génère les SVG pour l'énoncé et la solution selon le type d'exercice.
    
    ORDRE DE PRIORITÉ (source de vérité unique):
    1. variables (dict) - SOURCE DE VÉRITÉ ABSOLUE si présent
    2. svg_enonce_brief / svg_solution_brief - Briefs personnalisés
    3. exercise_type + family - Comportement par défaut
    4. Parsing HTML - DERNIER RECOURS avec WARNING
    
    Args:
        exercise: Dictionnaire de l'exercice avec les champs:
            - needs_svg: bool
            - variables: Optional[dict] - SOURCE DE VÉRITÉ (ex: {"hour": 8, "minute": 0})
            - exercise_type: Optional[str] - Type explicite
            - svg_enonce_brief: Optional[str] - Brief pour SVG énoncé
            - svg_solution_brief: Optional[str] - Brief pour SVG solution
            - family: str - Famille (fallback)
            - enonce_html: str
            - id: int
    
    Returns:
        Dict avec:
            - figure_svg_enonce: str|None
            - figure_svg_solution: str|None
            - figure_svg: str|None (compatibilité)
            - variables_used: dict|None (variables utilisées pour le rendu)
    """
    from models.exercise_types import get_svg_behavior
    
    result = {
        "figure_svg_enonce": None,
        "figure_svg_solution": None,
        "figure_svg": None,  # Compatibilité avec l'existant
        "variables_used": None  # Variables utilisées pour le rendu
    }
    
    # Si needs_svg est False, pas de SVG
    if not exercise.get("needs_svg", False):
        return result
    
    exercise_type = exercise.get("exercise_type")
    family = exercise.get("family", "")
    exercise_id = exercise.get("id", 1)
    
    # =========================================================================
    # PRIORITÉ 1: Variables explicites (SOURCE DE VÉRITÉ)
    # =========================================================================
    variables = exercise.get("variables")
    
    if variables and isinstance(variables, dict):
        hour = variables.get("hour")
        minute = variables.get("minute", 0)
        
        if hour is not None:
            result["variables_used"] = {"hour": hour, "minute": minute, "source": "variables"}
            
            # Générer SVG selon le type d'exercice
            if exercise_type == "PLACER_AIGUILLES":
                # Énoncé: horloge VIDE, Solution: horloge avec aiguilles
                result["figure_svg_enonce"] = _render_clock_empty_svg()
                result["figure_svg_solution"] = _render_clock_svg(hour, minute)
            else:
                # Par défaut: horloge avec aiguilles dans l'énoncé
                result["figure_svg_enonce"] = _render_clock_svg(hour, minute)
                # Pas de SVG solution pour LECTURE_HEURE classique
            
            result["figure_svg"] = result["figure_svg_enonce"]
            return result
    
    # =========================================================================
    # PRIORITÉ 2: Briefs personnalisés
    # =========================================================================
    svg_enonce_brief = exercise.get("svg_enonce_brief")
    svg_solution_brief = exercise.get("svg_solution_brief")
    
    if svg_enonce_brief or svg_solution_brief:
        # Extraire l'heure depuis le brief si possible
        hour, minute = _extract_time_from_brief(svg_enonce_brief or svg_solution_brief)
        result["variables_used"] = {"hour": hour, "minute": minute, "source": "brief"}
        
        if svg_enonce_brief:
            result["figure_svg_enonce"] = render_svg_from_brief(
                svg_enonce_brief, hour=hour, minute=minute
            )
        
        if svg_solution_brief:
            result["figure_svg_solution"] = render_svg_from_brief(
                svg_solution_brief, hour=hour, minute=minute
            )
        elif svg_enonce_brief and exercise_type == "PLACER_AIGUILLES":
            result["figure_svg_solution"] = _render_clock_svg(hour, minute)
        
        result["figure_svg"] = result["figure_svg_enonce"]
        return result
    
    # =========================================================================
    # PRIORITÉ 3: Comportement basé sur exercise_type / family
    # =========================================================================
    behavior = get_svg_behavior(exercise_type, family)
    
    # =========================================================================
    # PRIORITÉ 4 (DERNIER RECOURS): Parsing HTML - avec WARNING
    # =========================================================================
    enonce = exercise.get("enonce_html", "")
    hour, minute = _extract_time_from_enonce(enonce, exercise_id)
    
    # Émettre un warning car on utilise le parsing HTML (fragile)
    if family.upper() in ["LECTURE_HORLOGE", "CALCUL_DUREE", "DUREES"]:
        _svg_logger.warning(
            f"⚠️ Exercice #{exercise_id}: SVG généré par parsing HTML (fragile). "
            f"Ajoutez 'variables' pour garantir la cohérence texte/figure."
        )
    
    result["variables_used"] = {"hour": hour, "minute": minute, "source": "html_parsing"}
    
    # Générer le SVG de l'énoncé
    if behavior.svg_in_enonce:
        svg_type = behavior.enonce_svg_type
        result["figure_svg_enonce"] = _generate_svg_by_type(
            svg_type, exercise_type, family, hour, minute, exercise
        )
    
    # Générer le SVG de la solution
    if behavior.svg_in_solution:
        svg_type = behavior.solution_svg_type
        result["figure_svg_solution"] = _generate_svg_by_type(
            svg_type, exercise_type, family, hour, minute, exercise
        )
    
    # Compatibilité: figure_svg = figure_svg_enonce (comportement précédent)
    result["figure_svg"] = result["figure_svg_enonce"]
    
    return result


def _extract_time_from_brief(brief: str) -> tuple:
    """
    Extrait l'heure depuis un brief SVG.
    Ex: "Horloge à 9h20" -> (9, 20)
    """
    import re
    
    if not brief:
        return (12, 0)
    
    # Pattern: "HHhMM" ou "HH h MM"
    match = re.search(r'(\d{1,2})\s*h\s*(\d{1,2})', brief, re.IGNORECASE)
    if match:
        return int(match.group(1)), int(match.group(2))
    
    return (12, 0)


def _generate_svg_by_type(
    svg_type: str,
    exercise_type: Optional[str],
    family: str,
    hour: int,
    minute: int,
    exercise: dict
) -> Optional[str]:
    """
    Génère un SVG selon le type demandé.
    """
    # Types d'horloge
    if svg_type == "clock_with_hands":
        return _render_clock_svg(hour, minute)
    
    elif svg_type == "clock_empty":
        return _render_clock_empty_svg()
    
    # Timeline
    elif svg_type == "timeline":
        return _render_timeline_svg()
    
    # Formes géométriques
    elif svg_type == "shape":
        return _render_shape_svg()
    
    # Règle
    elif svg_type == "ruler":
        return _render_ruler_svg()
    
    # Symétrie axiale
    elif svg_type == "axis_only":
        return _render_axis_svg(with_symmetric=False)
    
    elif svg_type == "axis_with_symmetric":
        return _render_axis_svg(with_symmetric=True)
    
    # Auto: déduire depuis family/exercise_type
    elif svg_type == "auto":
        family_upper = family.upper()
        
        if family_upper == "LECTURE_HORLOGE":
            return _render_clock_svg(hour, minute)
        elif family_upper in ["DUREES", "CALCUL_DUREE"]:
            return _render_timeline_svg()
        elif family_upper == "PERIMETRE":
            return _render_shape_svg()
        else:
            return _render_placeholder_svg(f"Figure {family}")
    
    # Fallback
    return None


def _render_axis_svg(with_symmetric: bool = False) -> str:
    """
    Génère un SVG pour un exercice de symétrie axiale.
    
    Args:
        with_symmetric: Si True, affiche aussi la figure symétrique
    """
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200" width="300" height="200" style="max-width: 100%; height: auto;">
  <!-- Grille de fond -->
  <defs>
    <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e5e7eb" stroke-width="0.5"/>
    </pattern>
  </defs>
  <rect width="300" height="200" fill="url(#grid)"/>
  
  <!-- Axe de symétrie (vertical au centre) -->
  <line x1="150" y1="10" x2="150" y2="190" stroke="#dc2626" stroke-width="2" stroke-dasharray="8,4"/>
  <text x="155" y="25" font-size="12" fill="#dc2626">(d)</text>
  
  <!-- Figure originale (triangle à gauche) -->
  <polygon points="50,150 100,50 120,150" fill="#3b82f620" stroke="#3b82f6" stroke-width="2"/>
  <text x="85" y="170" font-size="10" fill="#3b82f6" text-anchor="middle">Figure</text>'''
    
    if with_symmetric:
        # Ajouter la figure symétrique
        svg += '''
  
  <!-- Figure symétrique (triangle à droite) -->
  <polygon points="250,150 200,50 180,150" fill="#22c55e20" stroke="#22c55e" stroke-width="2"/>
  <text x="210" y="170" font-size="10" fill="#22c55e" text-anchor="middle">Image</text>'''
    else:
        svg += '''
  
  <!-- Zone pour la figure symétrique (pointillés) -->
  <rect x="180" y="50" width="70" height="100" fill="none" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,4"/>
  <text x="215" y="105" font-size="10" fill="#94a3b8" text-anchor="middle">?</text>'''
    
    svg += '''
</svg>'''
    
    return svg

