# Curriculum data extracted from FlashExo Excel file
# Structure: Matière -> Classe (Niveau) -> Chapitre Appli (Compétence)

import latex2mathml.converter
from logger import get_logger

logger = get_logger()

CURRICULUM_DATA = {
    "Mathématiques": {
        "CP": {
            "Nombres, calcul et résolution de problèmes": [
                "Décomposer et représenter les nombres entiers jusqu'à 20",
                "Comparer et ranger les nombres entiers jusqu'à 20",
                "Addition et soustraction des nombres entiers jusqu'à 20",
                "La résolution de problèmes avec les nombres jusqu'à 20"
            ],
            "Grandeurs et mesures": [
                "Les longueurs et résolution de problèmes avec les longueurs",
                "Les masses et la résolution de problèmes avec les masses",
                "Les contenances et la résolution de problèmes avec les contenances",
                "La résolution de problèmes avec dates et durées",
                "La monnaie et résolution de problèmes avec la monnaie"
            ],
            "Espace et géométrie": [
                "Le repérage et déplacement dans l'espace",
                "Les instruments de tracé",
                "Les segments et les droites",
                "Figures géométriques simples (carré, rectangle, triangles et cercles)",
                "La symétrie",
                "Les solides"
            ]
        },
        "CE1": {
            "Nombres, calcul et résolution de problèmes": [
                "Décomposer et représenter les nombres entiers jusqu'à 999",
                "Comparer et ranger les nombres entiers",
                "Addition et soustraction des nombres entiers",
                "La résolution de problèmes",
                "Multiplication de nombres entiers",
                "Les doubles et les moitiés"
            ],
            "Grandeurs et mesures": [
                "Les longueurs et résolution de problèmes avec les longueurs",
                "Les masses et la résolution de problèmes avec les masses",
                "Les contenances et la résolution de problèmes avec les contenances",
                "La résolution de problèmes avec dates et durées",
                "La monnaie et résolution de problèmes avec la monnaie"
            ],
            "Espace et géométrie": [
                "Le repérage et déplacement dans l'espace",
                "Les instruments de tracé",
                "Les segments et les droites",
                "Figures géométriques simples (carré, rectangle, triangles et cercles)",
                "La symétrie",
                "Les solides"
            ]
        },
        "CE2": {
            "Nombres, calcul et résolution de problèmes": [
                "Décomposer et représenter les nombres entiers jusqu'à 999",
                "Comparer et ranger les nombres entiers",
                "Addition et soustraction des nombres entiers",
                "La résolution de problèmes",
                "Multiplication de nombres entiers",
                "Les doubles et les moitiés"
            ],
            "Grandeurs et mesures": [
                "Les longueurs et résolution de problèmes avec les longueurs",
                "Les masses et la résolution de problèmes avec les masses",
                "Les contenances et la résolution de problèmes avec les contenances",
                "La résolution de problèmes avec dates et durées",
                "La monnaie et résolution de problèmes avec la monnaie"
            ],
            "Espace et géométrie": [
                "Le repérage et déplacement dans l'espace",
                "Les instruments de tracé",
                "Les segments et les droites",
                "Figures géométriques simples (carré, rectangle, triangles et cercles)",
                "La symétrie",
                "Les solides"
            ]
        },
        "CM1": {
            "Nombres, calcul et résolution de problèmes": [
                "Nombres entiers",
                "Fractions",
                "Calculs avec les nombres entiers",
                "Calculs avec les fractions",
                "Résolution de problèmes"
            ],
            "Grandeurs et mesures": [
                "Mesures de longueurs",
                "Mesures de masses",
                "Mesures de capacités",
                "Mesures d'aires",
                "Mesures de temps",
                "Mesures d'angles"
            ],
            "Espace et géométrie": [
                "Géométrie du plan",
                "Géométrie dans l'espace",
                "Propriétés géométriques",
                "Constructions géométriques"
            ]
        },
        "CM2": {
            "Nombres, calcul et résolution de problèmes": [
                "Nombres entiers",
                "Nombres décimaux",
                "Fractions",
                "Calculs avec les nombres entiers",
                "Calculs avec les nombres décimaux",
                "Calculs avec les fractions",
                "Résolution de problèmes"
            ],
            "Grandeurs et mesures": [
                "Mesures de longueurs",
                "Mesures de masses",
                "Mesures de capacités",
                "Mesures d'aires",
                "Mesures de temps",
                "Mesures d'angles"
            ],
            "Espace et géométrie": [
                "Géométrie du plan",
                "Géométrie dans l'espace",
                "Propriétés géométriques",
                "Constructions géométriques"
            ]
        },
        "6e": {
            "Nombres et calculs": [
                "Nombres entiers et décimaux",
                "Fractions",
                "Nombres en écriture fractionnaire",
                "Calcul mental",
                "Calculs posés",
                "Calculs instrumentés"
            ],
            "Grandeurs et mesures": [
                "Longueurs, masses, durées",
                "Aires",
                "Périmètres et aires",
                "Volumes",
                "Angles"
            ],
            "Espace et géométrie": [
                "Géométrie dans l'espace",
                "Géométrie dans le plan",
                "Symétrie axiale"
            ],
            "Organisation et gestion de données": [
                "Proportionnalité"
            ]
        },
        "5e": {
            "Nombres et calculs": [
                "Nombres relatifs",
                "Nombres rationnels",
                "Calcul littéral",
                "Puissances"
            ],
            "Grandeurs et mesures": [
                "Aires et périmètres",
                "Volumes",
                "Angles et triangles"
            ],
            "Espace et géométrie": [
                "Triangles",
                "Parallélogrammes",
                "Symétrie centrale",
                "Homothétie"
            ],
            "Organisation et gestion de données, fonctions": [
                "Proportionnalité",
                "Statistiques",
                "Probabilités"
            ]
        },
        "4e": {
            "Nombres et calculs": [
                "Nombres relatifs",
                "Fractions",
                "Calcul littéral",
                "Équations et inéquations",
                "Puissances"
            ],
            "Grandeurs et mesures": [
                "Théorème de Pythagore",
                "Distances et tangentes",
                "Cosinus"
            ],
            "Espace et géométrie": [
                "Triangles et droites remarquables",
                "Translation et rotation",
                "Géométrie dans l'espace"
            ],
            "Organisation et gestion de données, fonctions": [
                "Proportionnalité",
                "Statistiques",
                "Probabilités",
                "Fonctions linéaires"
            ]
        },
        "3e": {
            "Nombres et calculs": [
                "Nombres entiers et rationnels",
                "Nombres réels",
                "Calcul littéral",
                "Équations et inéquations",
                "Arithmétique"
            ],
            "Grandeurs et mesures": [
                "Théorème de Thalès",
                "Trigonométrie",
                "Aires et volumes"
            ],
            "Espace et géométrie": [
                "Géométrie dans l'espace",
                "Transformations du plan",
                "Configurations du plan"
            ],
            "Organisation et gestion de données, fonctions": [
                "Fonctions",
                "Statistiques et probabilités",
                "Algorithmique et programmation"
            ]
        }
    },
    "Physique-Chimie": {
        "5e": {
            "Physique-Chimie": [
                "Organisation et transformations de la matière",
                "Mouvements et interactions",
                "L'énergie et ses conversions",
                "Des signaux pour observer et communiquer"
            ]
        },
        "4e": {
            "Physique-Chimie": [
                "Organisation et transformations de la matière",
                "Mouvements et interactions", 
                "L'énergie et ses conversions",
                "Des signaux pour observer et communiquer"
            ]
        },
        "3e": {
            "Physique-Chimie": [
                "Organisation et transformations de la matière",
                "Mouvements et interactions",
                "L'énergie et ses conversions", 
                "Des signaux pour observer et communiquer"
            ]
        },
        "Seconde": {
            "Physique-Chimie": [
                "Constitution et transformations de la matière",
                "Mouvement et interactions",
                "Ondes et signaux"
            ]
        },
        "Première": {
            "Physique-Chimie": [
                "Constitution et transformations de la matière",
                "Mouvement et interactions",
                "L'énergie : conversions et transferts",
                "Ondes et signaux"
            ]
        },
        "Terminale": {
            "Physique-Chimie": [
                "Constitution et transformations de la matière", 
                "Mouvement et interactions",
                "L'énergie : conversions et transferts",
                "Ondes et signaux"
            ]
        }
    },
    "SVT": {
        "5e": {
            "Sciences de la vie et de la Terre": [
                "La planète Terre, l'environnement et l'action humaine",
                "Le vivant et son évolution",
                "Le corps humain et la santé"
            ]
        },
        "4e": {
            "Sciences de la vie et de la Terre": [
                "La planète Terre, l'environnement et l'action humaine",
                "Le vivant et son évolution", 
                "Le corps humain et la santé"
            ]
        },
        "3e": {
            "Sciences de la vie et de la Terre": [
                "La planète Terre, l'environnement et l'action humaine",
                "Le vivant et son évolution",
                "Le corps humain et la santé"
            ]
        },
        "Seconde": {
            "Sciences de la vie et de la Terre": [
                "La Terre, la vie et l'organisation du vivant",
                "Les enjeux contemporains de la planète", 
                "Corps humain et santé"
            ]
        }
    }
}

def get_available_subjects():
    """Get list of available subjects"""
    return list(CURRICULUM_DATA.keys())

def get_levels_for_subject(subject):
    """Get list of levels for a given subject"""
    return list(CURRICULUM_DATA.get(subject, {}).keys())

def get_themes_for_level(subject, level):
    """Get list of themes for a given subject and level"""
    return list(CURRICULUM_DATA.get(subject, {}).get(level, {}).keys())

def get_chapters_for_theme(subject, level, theme):
    """Get list of chapters for a given subject, level and theme"""
    return CURRICULUM_DATA.get(subject, {}).get(level, {}).get(theme, [])

def get_all_chapters_for_level(subject, level):
    """Get all chapters for a given subject and level (flattened)"""
    themes = CURRICULUM_DATA.get(subject, {}).get(level, {})
    all_chapters = []
    for theme, chapters in themes.items():
        all_chapters.extend(chapters)
    return all_chapters

def build_prompt_context(subject, level, chapter):
    """Build dynamic prompt context for AI generation"""
    return {
        "matiere": subject,
        "niveau": level,
        "chapitre": chapter,
        "prompt_intro": f"Tu es un professeur de {subject} pour le niveau {level}, chapitre : {chapter}"
    }

def process_math_content_for_pdf(text: str) -> str:
    """Convert LaTeX mathematical expressions to MathML for PDF rendering"""
    if not text:
        return text
    
    try:
        # Regex patterns for common LaTeX expressions
        import re
        
        # CRITICAL FIX: Convert broken fraction formats to LaTeX FIRST
        # Fix "X de Y" patterns
        text = re.sub(r'(\d+)\s+de\s+(\d+)', r'\\frac{\1}{\2}', text)
        # Fix "X par Y" patterns  
        text = re.sub(r'(\d+)\s+par\s+(\d+)', r'\\frac{\1}{\2}', text)
        # Fix simple "X/Y" patterns (but preserve URLs)
        text = re.sub(r'(?<!http:)(?<!https:)(\d+)/(\d+)', r'\\frac{\1}{\2}', text)
        
        logger.info(f"🔧 Fixed broken fraction formats in text: {text[:100]}...")
        
        # Pattern for fractions: \frac{numerator}{denominator}
        frac_pattern = r'\\frac\{([^}]+)\}\{([^}]+)\}'
        
        # Pattern for square roots: \sqrt{content}
        sqrt_pattern = r'\\sqrt\{([^}]+)\}'
        
        # Pattern for powers: x^{exponent}
        power_pattern = r'([a-zA-Z0-9]+)\^\{([^}]+)\}'
        
        def convert_frac(match):
            """Convert \frac{a}{b} to MathML"""
            numerator = match.group(1)
            denominator = match.group(2)
            try:
                latex_expr = f"\\frac{{{numerator}}}{{{denominator}}}"
                mathml = latex2mathml.converter.convert(latex_expr)
                return mathml
            except Exception as e:
                logger.warning(f"Failed to convert fraction {match.group(0)}: {e}")
                return f"{numerator}/{denominator}"  # Fallback
        
        def convert_sqrt(match):
            """Convert \sqrt{content} to MathML"""
            content = match.group(1)
            try:
                latex_expr = f"\\sqrt{{{content}}}"
                mathml = latex2mathml.converter.convert(latex_expr)
                return mathml
            except Exception as e:
                logger.warning(f"Failed to convert sqrt {match.group(0)}: {e}")
                return f"√({content})"  # Fallback
        
        def convert_power(match):
            """Convert x^{exp} to MathML"""
            base = match.group(1)
            exponent = match.group(2)
            try:
                latex_expr = f"{base}^{{{exponent}}}"
                mathml = latex2mathml.converter.convert(latex_expr)
                return mathml
            except Exception as e:
                logger.warning(f"Failed to convert power {match.group(0)}: {e}")
                return f"{base}^{exponent}"  # Fallback
        
        # Apply conversions
        result = re.sub(frac_pattern, convert_frac, text)
        result = re.sub(sqrt_pattern, convert_sqrt, result)
        result = re.sub(power_pattern, convert_power, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing math content for PDF: {e}")
        return text  # Return original text on error