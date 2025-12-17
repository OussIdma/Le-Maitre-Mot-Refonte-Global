"""
Générateur PREMIUM - Durées et Lecture de l'heure (6e_GM07)

Générateur de qualité MANUEL SCOLAIRE PROFESSIONNEL.
Activé uniquement pour l'offre PRO.

Familles d'exercices :
- LECTURE_HORLOGE : Lecture d'horloge analogique (SVG obligatoire)
- CONVERSION : Conversions de durées (h↔min↔sec, heures décimales)
- CALCUL_DUREE : Calcul de durées entre deux instants (avec/sans report, minuit)
- PROBLEME_DUREES : Problèmes contextualisés de planification

Chaque exercice inclut :
- Énoncé contextualisé de qualité
- Solution détaillée avec étapes pédagogiques
- Alertes sur les pièges classiques
- SVG quand nécessaire
"""

import random
import math
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass


class DureesFamily(Enum):
    """Familles d'exercices pour le générateur premium durées."""
    LECTURE_HORLOGE = "lecture_horloge"
    CONVERSION = "conversion"
    CALCUL_DUREE = "calcul_duree"
    PROBLEME_DUREES = "probleme_durees"


@dataclass
class DureesExercise:
    """Structure d'un exercice premium durées."""
    family: DureesFamily
    difficulty: str
    enonce_html: str
    solution_html: str
    needs_svg: bool
    svg_content: Optional[str] = None
    metadata: Dict[str, Any] = None


class DureesPremiumGenerator:
    """
    Générateur PREMIUM pour le chapitre 6e_GM07 : Durées et lecture de l'heure.
    
    Qualité : Manuel scolaire professionnel
    Activation : Offre PRO uniquement
    """
    
    def __init__(self):
        # Contextes variés pour les énoncés
        self.contextes_horloge = [
            ("cuisine", "L'horloge de la cuisine indique l'heure du repas"),
            ("gare", "L'horloge murale de la gare affiche l'heure de départ d'un TGV"),
            ("école", "L'horloge de la salle de classe indique l'heure de la récréation"),
            ("réveil", "Le réveil de {prenom} affiche l'heure de son entraînement"),
            ("CDI", "L'horloge du CDI indique l'heure de fermeture"),
            ("salon", "La pendule du salon affiche l'heure du goûter"),
            ("gymnase", "L'horloge du gymnase indique le début du match"),
            ("piscine", "L'horloge de la piscine affiche l'heure du cours de natation"),
        ]
        
        self.prenoms = [
            "Léo", "Emma", "Lucas", "Chloé", "Hugo", "Inès", "Nathan", "Léa",
            "Louis", "Manon", "Raphaël", "Camille", "Jules", "Zoé", "Arthur", "Sarah"
        ]
        
        self.contextes_conversion = [
            ("cours", "Le cours de {matiere} de {prof}"),
            ("film", "Le film \"{titre}\""),
            ("trajet", "Le trajet en {transport} entre {ville1} et {ville2}"),
            ("sport", "L'entraînement de {sport}"),
            ("devoirs", "Le temps passé par {prenom} à faire ses devoirs"),
            ("chanson", "Une chanson de {artiste}"),
            ("jeu", "Une partie de {jeu}"),
            ("cuisine", "La préparation du {plat}"),
        ]
        
        self.matieres = ["technologie", "français", "mathématiques", "histoire", "SVT", "anglais"]
        self.profs = ["Monsieur Martin", "Madame Dupont", "Monsieur Bernard", "Madame Leroy"]
        self.films = ["Le Voyage Fantastique", "L'Aventure Spatiale", "Le Secret de la Forêt", "Mission Océan"]
        self.transports = ["train", "bus", "métro", "voiture"]
        self.villes = [("Paris", "Lyon"), ("Marseille", "Nice"), ("Bordeaux", "Toulouse"), ("Lille", "Bruxelles")]
        self.sports = ["basketball", "football", "natation", "tennis", "gymnastique", "handball"]
        self.artistes = ["un groupe célèbre", "un chanteur populaire", "une chanteuse connue"]
        self.jeux = ["jeu vidéo", "jeu de société", "échecs", "puzzle"]
        self.plats = ["gâteau au chocolat", "tarte aux pommes", "pizza maison", "gratin"]
        
        self.contextes_calcul = [
            ("vol", "un vol qui décolle", "et atterrit"),
            ("film", "un documentaire sur la nature commence", "et se termine"),
            ("récréation", "le temps de récréation de l'après-midi commence", "et se termine"),
            ("jeu", "une partie de jeu vidéo commence", "et se termine"),
            ("trajet", "un trajet en train part", "et arrive"),
            ("cours", "le cours de mathématiques commence", "et se termine"),
            ("concert", "le concert commence", "et se termine"),
            ("spectacle", "le spectacle de danse débute", "et prend fin"),
        ]
        
        self.contextes_probleme = [
            ("bus", "Le bus scolaire arrive à l'école", "Le trajet dure"),
            ("cinéma", "Le film au cinéma dure {duree}. Il se termine", ""),
            ("randonnée", "Une randonnée pédestre commence", "Elle est prévue pour durer"),
            ("devoirs", "{prenom} a un devoir de maths à rendre", "Il lui faut"),
            ("préparation", "Pour la fête de l'école, on prépare la salle", ""),
            ("cuisinier", "Un cuisinier prépare un plat", ""),
        ]
    
    def generate(self, difficulty: str = "moyen", family: Optional[str] = None) -> DureesExercise:
        """
        Génère un exercice premium.
        
        Args:
            difficulty: "facile", "moyen", ou "difficile"
            family: Famille spécifique ou None pour aléatoire
            
        Returns:
            DureesExercise avec énoncé, solution et SVG si nécessaire
        """
        if family:
            family_enum = DureesFamily(family)
        else:
            # Distribution pondérée selon la difficulté
            if difficulty == "facile":
                weights = [0.35, 0.30, 0.20, 0.15]  # Plus de lecture et conversion
            elif difficulty == "difficile":
                weights = [0.15, 0.25, 0.30, 0.30]  # Plus de calculs et problèmes
            else:
                weights = [0.25, 0.25, 0.25, 0.25]  # Équilibré
            
            family_enum = random.choices(
                list(DureesFamily),
                weights=weights
            )[0]
        
        generators = {
            DureesFamily.LECTURE_HORLOGE: self._generate_lecture_horloge,
            DureesFamily.CONVERSION: self._generate_conversion,
            DureesFamily.CALCUL_DUREE: self._generate_calcul_duree,
            DureesFamily.PROBLEME_DUREES: self._generate_probleme_durees,
        }
        
        return generators[family_enum](difficulty)
    
    # =========================================================================
    # GÉNÉRATION SVG HORLOGE PREMIUM
    # =========================================================================
    
    def _generate_clock_svg(
        self,
        hours: int,
        minutes: int,
        size: int = 200,
        label: Optional[str] = None,
        show_time: bool = False
    ) -> str:
        """
        Génère une horloge analogique SVG de qualité premium.
        
        Features:
        - Cadran élégant avec graduations
        - Aiguilles proportionnelles et lisibles
        - Chiffres romains ou arabes
        - Label optionnel
        """
        cx, cy = size // 2, size // 2
        radius = size // 2 - 15
        
        # Convertir en format 12h
        h12 = hours % 12
        
        # Calculer les angles (0° = 12h, sens horaire)
        hour_angle = (h12 * 30) + (minutes * 0.5) - 90
        minute_angle = (minutes * 6) - 90
        
        hour_rad = math.radians(hour_angle)
        minute_rad = math.radians(minute_angle)
        
        # Longueurs des aiguilles
        hour_length = radius * 0.5
        minute_length = radius * 0.75
        
        # Coordonnées des extrémités
        hour_x = cx + hour_length * math.cos(hour_rad)
        hour_y = cy + hour_length * math.sin(hour_rad)
        minute_x = cx + minute_length * math.cos(minute_rad)
        minute_y = cy + minute_length * math.sin(minute_rad)
        
        svg_height = size + (35 if label or show_time else 0)
        
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {svg_height}" width="{size}" height="{svg_height}">
  <!-- Fond du cadran avec dégradé subtil -->
  <defs>
    <radialGradient id="clockFace" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:#ffffff"/>
      <stop offset="100%" style="stop-color:#f5f5f5"/>
    </radialGradient>
  </defs>
  
  <!-- Cadran principal -->
  <circle cx="{cx}" cy="{cy}" r="{radius}" fill="url(#clockFace)" stroke="#2c3e50" stroke-width="3"/>
  <circle cx="{cx}" cy="{cy}" r="{radius-3}" fill="none" stroke="#95a5a6" stroke-width="1"/>
'''
        
        # Graduations (60 pour les minutes, 12 grandes pour les heures)
        for i in range(60):
            angle = math.radians(i * 6 - 90)
            if i % 5 == 0:
                # Grande graduation (heures)
                inner_r = radius - 15
                outer_r = radius - 5
                stroke_width = 2.5
                color = "#2c3e50"
            else:
                # Petite graduation (minutes)
                inner_r = radius - 10
                outer_r = radius - 5
                stroke_width = 1
                color = "#7f8c8d"
            
            x1 = cx + inner_r * math.cos(angle)
            y1 = cy + inner_r * math.sin(angle)
            x2 = cx + outer_r * math.cos(angle)
            y2 = cy + outer_r * math.sin(angle)
            
            svg += f'  <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{stroke_width}"/>\n'
        
        # Chiffres des heures
        number_radius = radius - 28
        for i in range(1, 13):
            angle = math.radians(i * 30 - 90)
            num_x = cx + number_radius * math.cos(angle)
            num_y = cy + number_radius * math.sin(angle) + 5
            svg += f'  <text x="{num_x:.1f}" y="{num_y:.1f}" text-anchor="middle" font-family="Georgia, serif" font-size="14" font-weight="bold" fill="#2c3e50">{i}</text>\n'
        
        # Aiguille des heures (épaisse, avec extrémité arrondie)
        svg += f'''  <!-- Aiguille des heures -->
  <line x1="{cx}" y1="{cy}" x2="{hour_x:.1f}" y2="{hour_y:.1f}" stroke="#2c3e50" stroke-width="6" stroke-linecap="round"/>
'''
        
        # Aiguille des minutes (plus fine)
        svg += f'''  <!-- Aiguille des minutes -->
  <line x1="{cx}" y1="{cy}" x2="{minute_x:.1f}" y2="{minute_y:.1f}" stroke="#34495e" stroke-width="4" stroke-linecap="round"/>
'''
        
        # Centre de l'horloge (point décoratif)
        svg += f'''  <!-- Centre -->
  <circle cx="{cx}" cy="{cy}" r="6" fill="#2c3e50"/>
  <circle cx="{cx}" cy="{cy}" r="3" fill="#ecf0f1"/>
'''
        
        # Label ou heure affichée
        if label or show_time:
            text_y = size + 20
            if label:
                svg += f'  <text x="{cx}" y="{text_y}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#7f8c8d">{label}</text>\n'
            if show_time:
                time_str = f"{hours:02d}h{minutes:02d}"
                svg += f'  <text x="{cx}" y="{text_y + (15 if label else 0)}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#95a5a6">{time_str}</text>\n'
        
        svg += '</svg>'
        return svg
    
    def _generate_dual_clock_svg(
        self,
        h1: int, m1: int,
        h2: int, m2: int,
        label1: str = "Début",
        label2: str = "Fin"
    ) -> str:
        """Génère deux horloges côte à côte avec une flèche."""
        clock1 = self._generate_clock_svg(h1, m1, size=160, label=label1)
        clock2 = self._generate_clock_svg(h2, m2, size=160, label=label2)
        
        # Extraire le contenu interne des SVG
        def extract_content(svg: str) -> str:
            start = svg.find('>') + 1
            end = svg.rfind('</svg>')
            return svg[start:end]
        
        content1 = extract_content(clock1)
        content2 = extract_content(clock2)
        
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 220" width="400" height="220">
  <g transform="translate(10, 10)">
    {content1}
  </g>
  <g transform="translate(220, 10)">
    {content2}
  </g>
  <!-- Flèche de transition -->
  <path d="M 175 100 L 205 100 L 195 90 M 205 100 L 195 110" fill="none" stroke="#3498db" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''
    
    # =========================================================================
    # FAMILLE 1: LECTURE D'HORLOGE
    # =========================================================================
    
    def _generate_lecture_horloge(self, difficulty: str) -> DureesExercise:
        """
        Génère un exercice de lecture d'horloge.
        
        Facile: Heures rondes, demi-heures, quarts
        Moyen: Minutes précises (5 en 5), format 24h
        Difficile: Position des aiguilles, anticipation, ambiguïtés
        """
        prenom = random.choice(self.prenoms)
        contexte_type, contexte_base = random.choice(self.contextes_horloge)
        contexte = contexte_base.format(prenom=prenom)
        
        if difficulty == "facile":
            variant = random.choice(["heure_ronde", "demi_heure", "quart"])
            
            if variant == "heure_ronde":
                hours = random.randint(1, 12)
                minutes = 0
                
                enonce = f'''<p><strong>Lecture d'heure exacte :</strong> {contexte}. 
L'aiguille des heures est sur le {hours} et l'aiguille des minutes est sur le 12. 
Quelle heure est-il ? (Format HHhMM)</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>L'aiguille des heures est sur le <strong>{hours}</strong>.</li>
<li>L'aiguille des minutes est sur le 12, ce qui signifie 00 minute.</li>
<li>L'heure affichée est <strong>{hours:02d}h00</strong>.</li>
</ol>'''
                
            elif variant == "demi_heure":
                hours = random.randint(1, 12)
                minutes = 30
                
                enonce = f'''<p><strong>Lecture de la demi-heure :</strong> {contexte}. 
L'aiguille des heures est entre le {hours} et le {(hours % 12) + 1}, plus proche du {hours}. 
L'aiguille des minutes est sur le 6. 
Quelle heure est-il ? (Format HHhMM)</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>L'aiguille des heures est entre {hours} et {(hours % 12) + 1}, proche du {hours} → il est <strong>{hours} heures</strong> passées.</li>
<li>L'aiguille des minutes est sur le 6, ce qui correspond à $6 \\times 5 = 30$ minutes.</li>
<li>L'heure affichée est <strong>{hours:02d}h30</strong>.</li>
</ol>'''
                
            else:  # quart
                hours = random.randint(1, 12)
                minutes = random.choice([15, 45])
                minute_pos = 3 if minutes == 15 else 9
                
                if minutes == 15:
                    enonce = f'''<p><strong>Lecture simple de l'heure :</strong> {contexte}. 
L'aiguille des heures (courte) est sur le {hours} et l'aiguille des minutes (longue) est sur le {minute_pos}. 
Quelle heure est-il ? (Format HHhMM)</p>'''
                else:
                    enonce = f'''<p><strong>Lecture 'moins le quart' :</strong> {contexte}. 
L'aiguille des heures (courte) est juste avant le {(hours % 12) + 1} et l'aiguille des minutes (longue) est sur le 9. 
Quelle heure est-il ? (Format HHhMM)</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>L'aiguille des heures pointe vers le <strong>{hours}</strong>.</li>
<li>L'aiguille des minutes est sur le {minute_pos}, ce qui correspond à ${minute_pos} \\times 5 = {minutes}$ minutes.</li>
<li>L'heure affichée est <strong>{hours:02d}h{minutes:02d}</strong>.</li>
</ol>
<p style="color: orange;"><strong>Piège classique :</strong> Ne confondez pas l'aiguille des heures et celle des minutes, surtout quand l'aiguille des minutes est sur un nombre.</p>'''
            
        elif difficulty == "moyen":
            variant = random.choice(["minute_precise", "format_24h", "moins_le_quart"])
            
            if variant == "minute_precise":
                hours = random.randint(1, 12)
                minutes = random.choice([7, 13, 22, 38, 47, 53])
                
                enonce = f'''<p><strong>Lecture à la minute près :</strong> Le réveil de {prenom} affiche l'heure de son entraînement. 
L'aiguille des heures est entre le {hours} et le {(hours % 12) + 1}, et l'aiguille des minutes est sur la {minutes}ème petite graduation. 
Quelle heure est-il ? (Format HHhMM)</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>L'aiguille des heures se rapproche du {(hours % 12) + 1} mais n'y est pas encore → il est <strong>{hours} heures</strong>.</li>
<li>L'aiguille des minutes indique la {minutes}ème minute, soit <strong>{minutes} min</strong>.</li>
<li>L'heure complète est <strong>{hours:02d}h{minutes:02d}</strong>.</li>
</ol>'''
                
            elif variant == "format_24h":
                hours_24 = random.randint(14, 22)
                hours_12 = hours_24 - 12
                minutes = random.choice([10, 20, 35, 40, 50])
                
                enonce = f'''<p><strong>Lecture format 24h :</strong> {contexte} en fin d'après-midi. 
L'aiguille des heures est entre le {hours_12} et le {(hours_12 % 12) + 1}. L'aiguille des minutes pointe vers le {minutes // 5}. 
Quelle est l'heure au format 24h ? (Format HHhMM)</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>L'heure indiquée est en soirée, nous utilisons le format 24h.</li>
<li>L'aiguille des heures indique {hours_12} heures (soit {hours_24}h en format 24h).</li>
<li>L'aiguille des minutes pointe vers le {minutes // 5}, soit ${minutes // 5} \\times 5 = {minutes}$ minutes.</li>
<li>L'heure complète est <strong>{hours_24}h{minutes:02d}</strong>.</li>
</ol>'''
                
                hours = hours_24
                
            else:  # moins_le_quart avec ambiguïté
                hours_aff = random.randint(2, 11)
                hours = hours_aff
                minutes = 45
                pm_hours = hours + 12
                
                enonce = f'''<p><strong>Lecture 'moins le quart' et ambiguïté :</strong> 
Quelle heure est-il lorsque l'aiguille des heures est juste avant le {hours_aff + 1} et que l'aiguille des minutes est sur le 9 ? 
On suppose que c'est l'après-midi. Quelle est l'heure au format 24h ? (Format HHhMM)</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>L'aiguille des minutes est sur le 9, ce qui signifie $9 \\times 5 = 45$ minutes.</li>
<li>L'aiguille des heures est <strong>avant le {hours_aff + 1}</strong>, l'heure est donc {hours_aff} heures et 45 minutes.</li>
<li>Puisque l'on suppose l'après-midi, on ajoute 12 heures : ${hours_aff} + 12 = {pm_hours}$ h.</li>
<li>L'heure affichée est <strong>{pm_hours}h45</strong>.</li>
</ol>'''
                
                hours = pm_hours
                
        else:  # difficile
            variant = random.choice(["anticipation", "position_inverse", "proche_heure"])
            
            if variant == "anticipation":
                hours = random.randint(8, 11)
                minutes = random.randint(51, 58)
                
                enonce = f'''<p><strong>Anticipation de l'heure :</strong> L'horloge du CDI affiche {hours:02d}h{minutes:02d}. 
Décris précisément où se situent les aiguilles à cet instant. 
(On attend la position de l'aiguille des heures et des minutes).</p>'''
                
                fraction = minutes / 60
                proche_de = hours + 1 if hours < 12 else 1
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li><strong>Aiguille des minutes :</strong> Elle pointe exactement vers la {minutes}ème graduation après le 12 (légèrement après le {minutes // 5} sur le cadran).</li>
<li><strong>Aiguille des heures :</strong> Elle a fait $\\frac{{{minutes}}}{{60}}$ du trajet entre le {hours} et le {proche_de}. Elle est donc <strong>très proche du {proche_de}</strong>, mais ne l'a pas encore atteint.</li>
<li>L'heure affichée est <strong>{hours:02d}h{minutes:02d}</strong>.</li>
</ol>
<p style="color: orange;"><strong>Piège classique :</strong> Quand l'heure est proche de l'heure pile suivante, l'aiguille des heures doit être très avancée. L'élève doit comprendre la rotation continue.</p>'''
                
            elif variant == "position_inverse":
                hours = random.randint(2, 10)
                minutes = hours * 5  # Minutes égales à position de l'heure × 5
                
                enonce = f'''<p><strong>Position inverse :</strong> 
Sur une horloge, l'aiguille des minutes est exactement sur le {hours}. 
Sachant que l'aiguille des heures est entre le {hours} et le {hours + 1}, à quelle heure correspond cette configuration ?</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>L'aiguille des minutes sur le {hours} indique ${hours} \\times 5 = {minutes}$ minutes.</li>
<li>L'aiguille des heures entre {hours} et {hours + 1} indique qu'il est {hours} heures passées.</li>
<li>L'heure est <strong>{hours:02d}h{minutes:02d}</strong>.</li>
</ol>
<p style="color: orange;"><strong>Piège classique :</strong> Ne pas confondre la position du chiffre avec les minutes qu'il représente.</p>'''
                
            else:  # proche_heure
                hours = random.randint(1, 11)
                minutes = random.choice([58, 59, 1, 2])
                
                if minutes >= 58:
                    proche = hours + 1
                    enonce = f'''<p><strong>Heure presque atteinte :</strong> 
L'horloge indique une heure très proche de {proche}h00. L'aiguille des minutes est {60 - minutes} graduation(s) avant le 12. 
Quelle heure exacte indique l'horloge ?</p>'''
                else:
                    proche = hours
                    enonce = f'''<p><strong>Heure à peine passée :</strong> 
L'horloge indique une heure très proche de {proche}h00. L'aiguille des minutes est {minutes} graduation(s) après le 12. 
Quelle heure exacte indique l'horloge ?</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>L'aiguille des minutes à {minutes} graduation(s) du 12 indique <strong>{minutes} minutes</strong>.</li>
<li>L'aiguille des heures est sur (ou très proche de) {hours}.</li>
<li>L'heure exacte est <strong>{hours:02d}h{minutes:02d}</strong>.</li>
</ol>'''
        
        svg = self._generate_clock_svg(hours, minutes, label=f"{hours:02d}h{minutes:02d}")
        
        return DureesExercise(
            family=DureesFamily.LECTURE_HORLOGE,
            difficulty=difficulty,
            enonce_html=enonce,
            solution_html=solution,
            needs_svg=True,
            svg_content=svg,
            metadata={"hours": hours, "minutes": minutes, "variant": variant if 'variant' in locals() else "standard"}
        )
    
    # =========================================================================
    # FAMILLE 2: CONVERSIONS DE DURÉES
    # =========================================================================
    
    def _generate_conversion(self, difficulty: str) -> DureesExercise:
        """
        Génère un exercice de conversion de durées.
        
        Facile: h→min simple, sec→min simple
        Moyen: min→h+min avec reste, h+min+sec→sec
        Difficile: Heures décimales, conversions complexes
        """
        prenom = random.choice(self.prenoms)
        
        if difficulty == "facile":
            variant = random.choice(["h_vers_min", "min_vers_sec", "sec_vers_min"])
            
            if variant == "h_vers_min":
                hours = random.randint(2, 6)
                result = hours * 60
                matiere = random.choice(self.matieres)
                prof = random.choice(self.profs)
                
                enonce = f'''<p><strong>Conversion simple (h vers min) :</strong> 
Le cours de {matiere} de {prof} dure <strong>{hours} heures</strong>. 
Exprime cette durée uniquement en minutes.</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>On sait que $1 \\text{{ h}} = 60 \\text{{ min}}$.</li>
<li>On effectue la multiplication : ${hours} \\times 60 = {result}$.</li>
<li>La durée est de <strong>{result} minutes</strong>.</li>
</ol>'''
                
            elif variant == "min_vers_sec":
                minutes = random.choice([2, 3, 4, 5, 10])
                result = minutes * 60
                
                enonce = f'''<p><strong>Conversion simple (min vers sec) :</strong> 
Un exercice de respiration dure <strong>{minutes} minutes</strong>. 
Exprime cette durée en secondes.</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>On sait que $1 \\text{{ min}} = 60 \\text{{ secondes}}$.</li>
<li>On effectue la multiplication : ${minutes} \\times 60 = {result}$.</li>
<li>La durée est de <strong>{result} secondes</strong>.</li>
</ol>'''
                
            else:  # sec_vers_min
                minutes = random.choice([3, 4, 5, 6, 10])
                seconds = minutes * 60
                
                enonce = f'''<p><strong>Conversion inverse (sec vers min) :</strong> 
Une chanson dure <strong>{seconds} secondes</strong>. 
Exprime cette durée uniquement en minutes.</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>On sait que $60 \\text{{ secondes}} = 1 \\text{{ minute}}$.</li>
<li>On effectue la division : ${seconds} \\div 60 = {minutes}$.</li>
<li>La durée est de <strong>{minutes} minutes</strong>.</li>
</ol>'''
                
        elif difficulty == "moyen":
            variant = random.choice(["min_vers_h_min", "h_min_sec_vers_sec", "sec_vers_min_sec"])
            
            if variant == "min_vers_h_min":
                hours = random.randint(2, 5)
                mins = random.randint(10, 55)
                total_min = hours * 60 + mins
                sport = random.choice(self.sports)
                
                enonce = f'''<p><strong>Conversion min vers h et min :</strong> 
Le temps passé par un athlète à s'entraîner au {sport} est de <strong>{total_min} minutes</strong>. 
Convertis cette durée en heures et minutes.</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>On cherche combien de fois 60 minutes (1 heure) sont contenues dans {total_min} minutes.</li>
<li>${total_min} \\div 60$. On trouve ${hours}$ heures (${hours} \\times 60 = {hours * 60}$).</li>
<li>On calcule le reste : ${total_min} - {hours * 60} = {mins}$ minutes.</li>
<li>La durée est de <strong>{hours} h {mins} min</strong>.</li>
</ol>'''
                
            elif variant == "h_min_sec_vers_sec":
                hours = random.choice([1, 2])
                mins = random.randint(5, 30)
                secs = random.randint(10, 50)
                total_sec = hours * 3600 + mins * 60 + secs
                
                enonce = f'''<p><strong>Conversion composée (h, min vers sec) :</strong> 
Un élève a mis <strong>{hours} heure{'s' if hours > 1 else ''}, {mins} minutes et {secs} secondes</strong> pour faire ses devoirs. 
Convertis cette durée totale en secondes.</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>Conversion des heures : ${hours} \\text{{ h}} = {hours} \\times 3600 = {hours * 3600}$ secondes.</li>
<li>Conversion des minutes : ${mins} \\text{{ min}} = {mins} \\times 60 = {mins * 60}$ secondes.</li>
<li>Addition de toutes les secondes : ${hours * 3600} + {mins * 60} + {secs} = {total_sec}$.</li>
<li>La durée totale est de <strong>{total_sec} secondes</strong>.</li>
</ol>'''
                
            else:  # sec_vers_min_sec
                mins = random.randint(2, 8)
                secs = random.randint(10, 55)
                total_sec = mins * 60 + secs
                
                enonce = f'''<p><strong>Conversion sec vers min et sec :</strong> 
Une vidéo dure <strong>{total_sec} secondes</strong>. 
Convertis cette durée en minutes et secondes.</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>On divise par 60 : ${total_sec} \\div 60 = {mins}$ (quotient) reste ${secs}$.</li>
<li>Quotient = <strong>{mins} minutes</strong>.</li>
<li>Reste = <strong>{secs} secondes</strong>.</li>
<li>La durée est de <strong>{mins} min {secs} s</strong>.</li>
</ol>'''
                
        else:  # difficile
            variant = random.choice(["heure_decimale", "double_conversion", "inverse_complexe"])
            
            if variant == "heure_decimale":
                hours = random.randint(1, 4)
                decimal_part = random.choice([0.25, 0.5, 0.75])
                decimal_hours = hours + decimal_part
                minutes = int(decimal_part * 60)
                
                enonce = f'''<p><strong>Piège de l'heure décimale (h vers h et min) :</strong> 
Un système informatique indique qu'un processus a duré <strong>{decimal_hours} heures</strong>. 
Convertis cette durée en heures et minutes.</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>La partie entière est {hours}, soit <strong>{hours} heures</strong>.</li>
<li>La partie décimale est {decimal_part}. Il faut la convertir en minutes en multipliant par 60.</li>
<li>Calcul : ${decimal_part} \\times 60 = {minutes}$.</li>
<li>La durée est de <strong>{hours} h {minutes} min</strong>.</li>
</ol>
<p style="color: orange;"><strong>Piège classique :</strong> Attention ! ${decimal_part} \\text{{ h}}$ n'est PAS ${int(decimal_part * 100)}$ minutes. Les élèves doivent comprendre que le temps n'est pas en base 100.</p>'''
                
            elif variant == "double_conversion":
                hours = random.choice([1, 2])
                mins = random.randint(15, 45)
                total_min = hours * 60 + mins
                total_sec = total_min * 60
                
                enonce = f'''<p><strong>Double conversion :</strong> 
Un film dure <strong>{hours} h {mins} min</strong>. 
Exprime cette durée en secondes.</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>D'abord, convertir en minutes : ${hours} \\text{{ h}} = {hours * 60}$ min. Total : ${hours * 60} + {mins} = {total_min}$ min.</li>
<li>Ensuite, convertir en secondes : ${total_min} \\times 60 = {total_sec}$.</li>
<li>La durée est de <strong>{total_sec} secondes</strong>.</li>
</ol>'''
                
            else:  # inverse_complexe
                total_sec = random.randint(4000, 8000)
                hours = total_sec // 3600
                remaining = total_sec % 3600
                mins = remaining // 60
                secs = remaining % 60
                
                enonce = f'''<p><strong>Conversion inverse complexe :</strong> 
Un téléchargement a duré <strong>{total_sec} secondes</strong>. 
Exprime cette durée en heures, minutes et secondes.</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>Division par 3600 (secondes dans 1h) : ${total_sec} \\div 3600 = {hours}$ h (reste {remaining} s).</li>
<li>Division du reste par 60 : ${remaining} \\div 60 = {mins}$ min (reste {secs} s).</li>
<li>La durée est de <strong>{hours} h {mins} min {secs} s</strong>.</li>
</ol>'''
        
        return DureesExercise(
            family=DureesFamily.CONVERSION,
            difficulty=difficulty,
            enonce_html=enonce,
            solution_html=solution,
            needs_svg=False,
            metadata={"variant": variant}
        )
    
    # =========================================================================
    # FAMILLE 3: CALCUL DE DURÉES
    # =========================================================================
    
    def _generate_calcul_duree(self, difficulty: str) -> DureesExercise:
        """
        Génère un exercice de calcul de durée entre deux instants.
        
        Facile: Même heure, sans report
        Moyen: Avec report (emprunt), méthode par paliers
        Difficile: Passage de jour (minuit), événements fractionnés
        """
        
        if difficulty == "facile":
            variant = random.choice(["meme_heure", "sans_report"])
            
            if variant == "meme_heure":
                hour = random.randint(8, 18)
                m1 = random.randint(0, 30)
                m2 = m1 + random.randint(10, 25)
                
                duree = m2 - m1
                
                contextes = [
                    ("récréation", "le temps de récréation de l'après-midi"),
                    ("pause", "la pause café"),
                    ("exercice", "l'exercice de mathématiques"),
                ]
                ctx_type, ctx_text = random.choice(contextes)
                
                enonce = f'''<p><strong>Durée sans report d'heure :</strong> 
{ctx_text.capitalize()} commence à <strong>{hour}h{m1:02d}</strong> et se termine à <strong>{hour}h{m2:02d}</strong>. 
Quelle est la durée ? (Format X min)</p>'''
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li>Puisque l'heure de début et de fin est la même ({hour}h), on ne calcule que la différence des minutes.</li>
<li>Calcul : ${m2} \\text{{ min}} - {m1} \\text{{ min}} = {duree}$ minutes.</li>
<li>La durée est de <strong>{duree} minutes</strong>.</li>
</ol>'''
                
                h1, m1_svg = hour, m1
                h2, m2_svg = hour, m2
                
            else:  # sans_report
                h1 = random.randint(8, 17)
                h2 = h1 + random.randint(1, 4)
                m1 = random.randint(5, 30)
                m2 = m1 + random.randint(10, 25)
                
                duree_h = h2 - h1
                duree_m = m2 - m1
                
                ctx = random.choice(self.contextes_calcul)
                
                enonce = f'''<p><strong>Calcul de durée sans emprunt :</strong> 
{ctx[0].capitalize()} {ctx[1]} à <strong>{h1}h{m1:02d}</strong> {ctx[2]} à <strong>{h2}h{m2:02d}</strong>. 
Quelle est la durée totale ? (Format X h Y min)</p>'''
                
                solution = f'''<h4>Correction détaillée (Soustraction sans emprunt)</h4>
<ol>
<li>On soustrait les heures : ${h2} \\text{{ h}} - {h1} \\text{{ h}} = {duree_h}$ heures.</li>
<li>On soustrait les minutes : ${m2} \\text{{ min}} - {m1} \\text{{ min}} = {duree_m}$ minutes.</li>
<li>L'absence de report simplifie le calcul.</li>
<li>La durée totale est de <strong>{duree_h} h {duree_m} min</strong>.</li>
</ol>'''
                
                h1_svg, m1_svg = h1, m1
                h2_svg, m2_svg = h2, m2
                
        elif difficulty == "moyen":
            variant = random.choice(["avec_report", "methode_paliers"])
            
            if variant == "avec_report":
                h1 = random.randint(14, 18)
                m1 = random.randint(40, 55)
                h2 = h1 + random.randint(1, 2)
                m2 = random.randint(5, 35)
                
                # Calcul par méthode directe avec emprunt
                if m2 < m1:
                    duree_h = h2 - h1 - 1
                    duree_m = m2 + 60 - m1
                else:
                    duree_h = h2 - h1
                    duree_m = m2 - m1
                
                ctx = random.choice(self.contextes_calcul)
                
                enonce = f'''<p><strong>Piège de la soustraction des minutes :</strong> 
Quelle est la durée d'une partie de jeu vidéo qui commence à <strong>{h1}h{m1:02d}</strong> et se termine à <strong>{h2}h{m2:02d}</strong> ? 
(Format X h Y min)</p>'''
                
                solution = f'''<h4>Correction détaillée (Méthode par soustraction - attention aux retenues)</h4>
<ol>
<li>On essaie de soustraire les minutes : ${m2} \\text{{ min}} - {m1} \\text{{ min}}$. IMPOSSIBLE car {m2} < {m1}.</li>
<li>On prend 1 heure à {h2}h, soit 60 minutes : ${h2} \\text{{ h }} {m2} \\text{{ min}} = {h2-1} \\text{{ h }} ({m2}+60) \\text{{ min}} = {h2-1} \\text{{ h }} {m2+60} \\text{{ min}}$.</li>
<li>On soustrait : $({h2-1} \\text{{ h }} {m2+60} \\text{{ min}}) - ({h1} \\text{{ h }} {m1} \\text{{ min}})$.</li>
<li>Résultat : ${duree_h} \\text{{ h }} {duree_m} \\text{{ min}}$.</li>
</ol>
<p style="color: orange;"><strong>Piège classique :</strong> Les élèves essaient de soustraire {m2}-{m1} et mettent un signe moins, ou échouent à convertir 1h en 60 min.</p>
<p>La durée est de <strong>{duree_h} h {duree_m} min</strong>.</p>'''
                
            else:  # methode_paliers
                h1 = random.randint(10, 16)
                m1 = random.randint(30, 55)
                h2 = h1 + random.randint(2, 4)
                m2 = random.randint(5, 30)
                
                # Calcul par paliers
                palier1 = 60 - m1  # jusqu'à l'heure pleine
                palier2 = (h2 - h1 - 1) * 60  # heures pleines
                palier3 = m2  # dernières minutes
                total_min = palier1 + palier2 + palier3
                duree_h = total_min // 60
                duree_m = total_min % 60
                
                ctx = random.choice(self.contextes_calcul)
                
                enonce = f'''<p><strong>Calcul de durée avec report :</strong> 
Quelle est la durée d'{ctx[0]} qui {ctx[1]} à <strong>{h1}h{m1:02d}</strong> et {ctx[2]} à <strong>{h2}h{m2:02d}</strong> ? 
(Format X h Y min)</p>'''
                
                solution = f'''<h4>Correction détaillée (Méthode par paliers)</h4>
<ol>
<li><strong>Palier 1 :</strong> De {h1}h{m1:02d} à l'heure pleine suivante ({h1+1}h00) : $60 \\text{{ min}} - {m1} \\text{{ min}} = {palier1}$ minutes.</li>
<li><strong>Palier 2 :</strong> De {h1+1}h00 à {h2}h00 : ${h2 - h1 - 1}$ heures = {palier2} minutes.</li>
<li><strong>Palier 3 :</strong> De {h2}h00 à l'heure d'arrivée ({h2}h{m2:02d}) : {palier3} minutes.</li>
<li><strong>Total :</strong> ${palier1} + {palier2} + {palier3} = {total_min}$ minutes = {duree_h} h {duree_m} min.</li>
</ol>
<p>La durée est de <strong>{duree_h} h {duree_m} min</strong>.</p>'''
            
            h1_svg, m1_svg = h1, m1
            h2_svg, m2_svg = h2, m2
            
        else:  # difficile
            variant = random.choice(["passage_minuit", "fractionne"])
            
            if variant == "passage_minuit":
                h1 = random.randint(22, 23)
                m1 = random.randint(10, 45)
                h2 = random.randint(6, 10)
                m2 = random.randint(15, 50)
                
                # Calcul avec passage minuit
                palier1 = 60 - m1  # jusqu'à l'heure pleine
                heures_avant_minuit = 24 - h1 - 1
                palier2 = heures_avant_minuit * 60
                palier3 = h2 * 60  # heures après minuit
                palier4 = m2
                total_min = palier1 + palier2 + palier3 + palier4
                duree_h = total_min // 60
                duree_m = total_min % 60
                
                enonce = f'''<p><strong>Calcul de durée avec passage de jour :</strong> 
Une famille prend l'avion pour la Réunion. Le vol part à <strong>{h1}h{m1:02d}</strong> (J1) et arrive à <strong>{h2:02d}h{m2:02d}</strong> (J2). 
Quelle est la durée totale du vol ? (Format X h Y min)</p>'''
                
                solution = f'''<h4>Correction détaillée (Méthode par paliers avec minuit)</h4>
<ol>
<li><strong>Palier 1 :</strong> De {h1}h{m1:02d} à {h1+1}h00 : $60 - {m1} = {palier1}$ minutes.</li>
<li><strong>Palier 2 :</strong> De {h1+1}h00 à minuit (00h00) : ${24 - h1 - 1}$ heures = {palier2} minutes.</li>
<li><strong>Palier 3 :</strong> De 00h00 à {h2}h00 : {h2} heures = {palier3} minutes.</li>
<li><strong>Palier 4 :</strong> De {h2}h00 à {h2}h{m2:02d} : {palier4} minutes.</li>
<li><strong>Total :</strong> ${palier1} + {palier2} + {palier3} + {palier4} = {total_min}$ minutes = {duree_h} h {duree_m} min.</li>
</ol>
<p style="color: orange;"><strong>Piège classique :</strong> Le passage à minuit demande une vigilance particulière. Ne pas oublier de compter les heures jusqu'à minuit ET après minuit.</p>
<p>La durée totale est de <strong>{duree_h} h {duree_m} min</strong>.</p>'''
                
            else:  # fractionne
                h1_1 = random.randint(9, 11)
                m1_1 = random.randint(5, 30)
                h1_2 = h1_1
                m1_2 = m1_1 + random.randint(20, 35)
                
                h2_1 = h1_1 + 1
                m2_1 = random.randint(5, 20)
                h2_2 = h2_1
                m2_2 = m2_1 + random.randint(30, 50)
                
                duree1 = m1_2 - m1_1
                duree2 = m2_2 - m2_1
                total_min = duree1 + duree2
                duree_h = total_min // 60
                duree_m = total_min % 60
                
                enonce = f'''<p><strong>Durée d'un événement fractionné :</strong> 
Un cuisinier prépare un plat. Il travaille de <strong>{h1_1}h{m1_1:02d} à {h1_2}h{m1_2:02d}</strong>, puis fait une pause, et reprend de <strong>{h2_1}h{m2_1:02d} à {h2_2}h{m2_2:02d}</strong>. 
Combien de temps total a-t-il cuisiné ? (Format X h Y min)</p>'''
                
                result_str = f"{duree_h} h {duree_m} min" if duree_h > 0 else f"{duree_m} min"
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li><strong>Première période :</strong> De {h1_1}h{m1_1:02d} à {h1_2}h{m1_2:02d}. Durée : ${m1_2} - {m1_1} = {duree1}$ minutes.</li>
<li><strong>Deuxième période :</strong> De {h2_1}h{m2_1:02d} à {h2_2}h{m2_2:02d}. Durée : ${m2_2} - {m2_1} = {duree2}$ minutes.</li>
<li><strong>Durée totale :</strong> ${duree1} \\text{{ min}} + {duree2} \\text{{ min}} = {total_min}$ minutes.</li>
<li>Conversion : ${total_min} \\text{{ min}} = {result_str}$.</li>
</ol>
<p>Le temps total de cuisine est de <strong>{result_str}</strong>.</p>'''
                
                h1_svg, m1_svg = h1_1, m1_1
                h2_svg, m2_svg = h2_2, m2_2
            
            h1_svg = h1 if 'h1_svg' not in locals() else h1_svg
            m1_svg = m1 if 'm1_svg' not in locals() else m1_svg
            h2_svg = h2 if 'h2_svg' not in locals() else h2_svg
            m2_svg = m2 if 'm2_svg' not in locals() else m2_svg
        
        svg = self._generate_dual_clock_svg(h1_svg, m1_svg, h2_svg, m2_svg)
        
        return DureesExercise(
            family=DureesFamily.CALCUL_DUREE,
            difficulty=difficulty,
            enonce_html=enonce,
            solution_html=solution,
            needs_svg=True,
            svg_content=svg,
            metadata={"variant": variant, "h1": h1_svg, "m1": m1_svg, "h2": h2_svg, "m2": m2_svg}
        )
    
    # =========================================================================
    # FAMILLE 4: PROBLÈMES CONTEXTUALISÉS
    # =========================================================================
    
    def _generate_probleme_durees(self, difficulty: str) -> DureesExercise:
        """
        Génère un problème contextualisé sur les durées.
        
        Facile: Recherche heure de fin (addition), heure de début (soustraction simple)
        Moyen: Avec emprunt, addition de plusieurs durées
        Difficile: Planification multi-étapes, contraintes temporelles
        """
        prenom = random.choice(self.prenoms)
        
        if difficulty == "facile":
            variant = random.choice(["heure_fin", "heure_debut_simple"])
            
            if variant == "heure_fin":
                h_debut = random.randint(8, 14)
                m_debut = random.randint(0, 45)
                duree_h = random.randint(1, 3)
                duree_m = random.choice([0, 15, 30, 45])
                
                total_m = m_debut + duree_m
                h_fin = h_debut + duree_h + total_m // 60
                m_fin = total_m % 60
                
                activites = [
                    ("randonnée pédestre", "Les randonneurs arriveront"),
                    ("cours de piano", f"{prenom} finira"),
                    ("visite du musée", "La visite se terminera"),
                    ("trajet en bus", "Le bus arrivera"),
                ]
                activite, fin_phrase = random.choice(activites)
                
                enonce = f'''<p><strong>Problème : Recherche d'heure de fin (Addition simple) :</strong> 
Une {activite} commence à <strong>{h_debut}h{m_debut:02d}</strong>. 
Elle est prévue pour durer <strong>{duree_h} h {duree_m:02d} min</strong>. 
À quelle heure {fin_phrase.lower()} ? (Format HHhMM)</p>'''
                
                if total_m < 60:
                    solution = f'''<h4>Correction détaillée (Addition)</h4>
<ol>
<li><strong>Addition des heures :</strong> ${h_debut} \\text{{ h}} + {duree_h} \\text{{ h}} = {h_debut + duree_h}$ heures.</li>
<li><strong>Addition des minutes :</strong> ${m_debut} \\text{{ min}} + {duree_m} \\text{{ min}} = {total_m}$ minutes.</li>
<li>Puisque {total_m} min est inférieur à 60 min, il n'y a pas de report.</li>
<li>{fin_phrase} à <strong>{h_fin}h{m_fin:02d}</strong>.</li>
</ol>'''
                else:
                    solution = f'''<h4>Correction détaillée (Addition avec report)</h4>
<ol>
<li><strong>Addition des heures :</strong> ${h_debut} \\text{{ h}} + {duree_h} \\text{{ h}} = {h_debut + duree_h}$ heures.</li>
<li><strong>Addition des minutes :</strong> ${m_debut} \\text{{ min}} + {duree_m} \\text{{ min}} = {m_debut + duree_m}$ minutes.</li>
<li>Report : ${m_debut + duree_m}$ min = 1 h {m_fin} min. Total : {h_fin} h {m_fin} min.</li>
<li>{fin_phrase} à <strong>{h_fin}h{m_fin:02d}</strong>.</li>
</ol>'''
                
            else:  # heure_debut_simple
                h_fin = random.randint(8, 12)
                m_fin = random.randint(0, 30)
                duree_min = random.choice([15, 20, 25, 30, 40])
                
                total_m = m_fin - duree_min
                if total_m < 0:
                    h_debut = h_fin - 1
                    m_debut = total_m + 60
                else:
                    h_debut = h_fin
                    m_debut = total_m
                
                enonce = f'''<p><strong>Problème : Recherche d'heure de début :</strong> 
Le bus scolaire arrive à l'école à <strong>{h_fin:02d}h{m_fin:02d}</strong>. 
Le trajet dure <strong>{duree_min} minutes</strong>. 
À quelle heure le bus doit-il partir ? (Format HHhMM)</p>'''
                
                if m_fin >= duree_min:
                    solution = f'''<h4>Correction détaillée (Soustraction)</h4>
<ol>
<li>On part de l'heure d'arrivée : {h_fin}h{m_fin:02d}.</li>
<li>On retire la durée du trajet : {duree_min} minutes.</li>
<li>Soustraction : ${m_fin} - {duree_min} = {m_debut}$ minutes.</li>
<li>Le bus doit partir à <strong>{h_debut:02d}h{m_debut:02d}</strong>.</li>
</ol>'''
                else:
                    solution = f'''<h4>Correction détaillée (Soustraction avec emprunt)</h4>
<ol>
<li>On part de l'heure d'arrivée : {h_fin}h{m_fin:02d}.</li>
<li>On retire la durée du trajet : {duree_min} minutes.</li>
<li>On ne peut pas faire ${m_fin} \\text{{ min}} - {duree_min} \\text{{ min}}$. On emprunte 1 heure.</li>
<li>${h_fin} \\text{{ h }} {m_fin} \\text{{ min}} = {h_fin - 1} \\text{{ h }} {m_fin + 60} \\text{{ min}}$.</li>
<li>Soustraction : ${m_fin + 60} - {duree_min} = {m_debut}$ minutes.</li>
<li>Le bus doit partir à <strong>{h_debut:02d}h{m_debut:02d}</strong>.</li>
</ol>'''
                
        elif difficulty == "moyen":
            variant = random.choice(["heure_debut_complexe", "addition_trois_durees"])
            
            if variant == "heure_debut_complexe":
                h_fin = random.randint(19, 22)
                m_fin = random.randint(5, 30)
                duree_h = random.choice([1, 2])
                duree_m = random.randint(40, 55)
                
                # Calcul de l'heure de début
                total_fin_min = h_fin * 60 + m_fin
                duree_total_min = duree_h * 60 + duree_m
                debut_total_min = total_fin_min - duree_total_min
                h_debut = debut_total_min // 60
                m_debut = debut_total_min % 60
                
                films = ["Le Voyage Fantastique", "Mission Spatiale", "Les Mystères de la Forêt"]
                film = random.choice(films)
                
                enonce = f'''<p><strong>Problème : Recherche de l'heure de début :</strong> 
Le film « {film} » dure <strong>{duree_h} h {duree_m} min</strong>. 
Il se termine à <strong>{h_fin}h{m_fin:02d}</strong>. 
À quelle heure la séance a-t-elle commencé ? (Format HHhMM)</p>'''
                
                solution = f'''<h4>Correction détaillée (Soustraction par paliers)</h4>
<ol>
<li>On retire d'abord les heures : ${h_fin} \\text{{ h }} {m_fin} \\text{{ min}} - {duree_h} \\text{{ h}} = {h_fin - duree_h} \\text{{ h }} {m_fin} \\text{{ min}}$.</li>
<li>On retire les minutes restantes ({duree_m} min). On ne peut pas faire ${m_fin}-{duree_m}$.</li>
<li>On prend 1 heure à {h_fin - duree_h}h : ${h_fin - duree_h} \\text{{ h }} {m_fin} \\text{{ min}} = {h_fin - duree_h - 1} \\text{{ h }} ({m_fin}+60) \\text{{ min}} = {h_fin - duree_h - 1} \\text{{ h }} {m_fin + 60} \\text{{ min}}$.</li>
<li>Soustraction des minutes : ${m_fin + 60} \\text{{ min}} - {duree_m} \\text{{ min}} = {m_debut}$ minutes.</li>
<li>Le film a commencé à <strong>{h_debut}h{m_debut:02d}</strong>.</li>
</ol>
<p style="color: orange;"><strong>Piège classique :</strong> La soustraction ${h_fin}h{m_fin:02d} - {duree_h}h{duree_m}$ nécessite deux 'emprunts'. Il est vital de bien convertir 1h en 60 min avant de soustraire.</p>'''
                
            else:  # addition_trois_durees
                d1 = random.randint(30, 50)
                d2_h = 1
                d2_m = random.randint(10, 30)
                d3_h = 1
                d3_m = random.randint(0, 20)
                
                total_h = d2_h + d3_h
                total_m = d1 + d2_m + d3_m
                final_h = total_h + total_m // 60
                final_m = total_m % 60
                
                enonce = f'''<p><strong>Problème : Addition de trois durées :</strong> 
Pour la fête de l'école, on prépare la salle. 
L'équipe A travaille <strong>{d1} minutes</strong>, l'équipe B travaille <strong>{d2_h} h {d2_m} min</strong> et l'équipe C travaille <strong>{d3_h} h {d3_m:02d} min</strong>. 
Quel est le temps de travail total de préparation ? (Format X h Y min)</p>'''
                
                solution = f'''<h4>Correction détaillée (Addition)</h4>
<ol>
<li><strong>Addition des heures :</strong> ${d2_h} \\text{{ h}} + {d3_h} \\text{{ h}} = {total_h}$ heures.</li>
<li><strong>Addition des minutes :</strong> ${d1} \\text{{ min}} + {d2_m} \\text{{ min}} + {d3_m} \\text{{ min}} = {total_m}$ minutes.</li>
<li><strong>Conversion des minutes :</strong> ${total_m} \\text{{ min}} = {total_m // 60} \\text{{ h }} {final_m} \\text{{ min}}$.</li>
<li><strong>Total :</strong> ${total_h} \\text{{ h}} + {total_m // 60} \\text{{ h }} {final_m} \\text{{ min}} = {final_h} \\text{{ h }} {final_m} \\text{{ min}}$.</li>
</ol>
<p>Le temps de travail total est de <strong>{final_h} h {final_m} min</strong>.</p>'''
                
        else:  # difficile
            variant = random.choice(["planification", "contrainte_horaire"])
            
            if variant == "planification":
                h_limite = random.randint(17, 19)
                m_limite = random.randint(0, 30)
                
                travail_h = 1
                travail_m = random.randint(30, 50)
                relecture_m = random.randint(15, 30)
                
                # Calcul
                total_travail_min = travail_h * 60 + travail_m + relecture_m
                total_h = total_travail_min // 60
                total_m = total_travail_min % 60
                
                limite_total_min = h_limite * 60 + m_limite
                debut_total_min = limite_total_min - total_travail_min
                h_debut = debut_total_min // 60
                m_debut = debut_total_min % 60
                
                enonce = f'''<p><strong>Problème de planification :</strong> 
{prenom} a un devoir de maths à rendre à <strong>{h_limite}h{m_limite:02d}</strong>. 
Il lui faut <strong>{travail_h} h {travail_m} min</strong> pour le faire et <strong>{relecture_m} minutes</strong> pour le relire. 
À quelle heure doit-il commencer son travail au plus tard pour être dans les temps ? (Format HHhMM)</p>'''
                
                solution = f'''<h4>Correction détaillée (Soustraction en deux étapes)</h4>
<ol>
<li><strong>Durée totale de travail :</strong> ${travail_h} \\text{{ h }} {travail_m} \\text{{ min}} + {relecture_m} \\text{{ min}} = {travail_h} \\text{{ h }} {travail_m + relecture_m} \\text{{ min}}$. Soit <strong>{total_h} h {total_m:02d} min</strong>.</li>
<li><strong>Heure de début (Soustraction) :</strong> ${h_limite} \\text{{ h }} {m_limite} \\text{{ min}} - {total_h} \\text{{ h }} {total_m} \\text{{ min}}$.</li>
<li><strong>Soustraction des heures :</strong> ${h_limite} - {total_h} = {h_limite - total_h}$ heures.</li>
<li>{'Soustraction des minutes : $' + str(m_limite) + ' - ' + str(total_m) + ' = ' + str(m_debut) + '$ minutes.' if m_limite >= total_m else 'On emprunte 1h : $' + str(m_limite + 60) + ' - ' + str(total_m) + ' = ' + str(m_debut) + '$ minutes.'}</li>
<li>{prenom} doit commencer au plus tard à <strong>{h_debut}h{m_debut:02d}</strong>.</li>
</ol>
<p style="color: orange;"><strong>Piège classique :</strong> L'élève doit d'abord additionner les deux durées avant de les soustraire de l'heure de fin. L'addition peut elle-même nécessiter une conversion.</p>'''
                
            else:  # contrainte_horaire
                h_debut_journee = 8
                m_debut_journee = random.randint(0, 30)
                
                activites = [
                    ("trajet aller", random.randint(20, 35)),
                    ("cours", random.randint(180, 240)),
                    ("déjeuner", random.randint(45, 60)),
                    ("activités", random.randint(90, 120)),
                    ("trajet retour", random.randint(20, 35)),
                ]
                
                total_min = sum(a[1] for a in activites)
                h_fin = h_debut_journee + (m_debut_journee + total_min) // 60
                m_fin = (m_debut_journee + total_min) % 60
                
                activites_str = "\n".join([f"• {nom} : {duree} min" for nom, duree in activites])
                
                enonce = f'''<p><strong>Problème : Calcul d'emploi du temps :</strong> 
{prenom} part de chez lui à <strong>{h_debut_journee}h{m_debut_journee:02d}</strong> pour une journée complète. 
Voici son planning :
<br/>{activites_str}
<br/>À quelle heure {prenom} sera-t-il de retour chez lui ? (Format HHhMM)</p>'''
                
                calc_str = " + ".join([str(a[1]) for a in activites])
                
                solution = f'''<h4>Correction détaillée</h4>
<ol>
<li><strong>Additionner toutes les durées :</strong>
<br/>{calc_str} = {total_min} min.</li>
<li><strong>Conversion :</strong> ${total_min} \\text{{ min}} = {total_min // 60} \\text{{ h }} {total_min % 60} \\text{{ min}}$.</li>
<li><strong>Heure de fin :</strong>
<br/>${h_debut_journee} \\text{{ h }} {m_debut_journee} \\text{{ min}} + {total_min // 60} \\text{{ h }} {total_min % 60} \\text{{ min}} = {h_fin} \\text{{ h }} {m_fin} \\text{{ min}}$.</li>
</ol>
<p>{prenom} sera de retour à <strong>{h_fin}h{m_fin:02d}</strong>.</p>'''
        
        return DureesExercise(
            family=DureesFamily.PROBLEME_DUREES,
            difficulty=difficulty,
            enonce_html=enonce,
            solution_html=solution,
            needs_svg=False,
            metadata={"variant": variant}
        )


# Instance globale du générateur
_durees_premium_generator = None


def get_durees_premium_generator() -> DureesPremiumGenerator:
    """Retourne l'instance singleton du générateur premium."""
    global _durees_premium_generator
    if _durees_premium_generator is None:
        _durees_premium_generator = DureesPremiumGenerator()
    return _durees_premium_generator
