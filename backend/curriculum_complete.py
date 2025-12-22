# CURRICULUM COMPLET - Système de Feature Flags
# Toutes les matières du système éducatif français avec statuts d'activation

from logger import get_logger
import latex2mathml.converter

logger = get_logger()

# Statuts des matières avec descriptions
CURRICULUM_STATUS = {
    "active": {"emoji": "✅", "label": "Disponible", "color": "green"},
    "coming_soon": {"emoji": "🔄", "label": "Bientôt disponible", "color": "orange"}, 
    "planned": {"emoji": "📋", "label": "En développement", "color": "blue"},
    "beta": {"emoji": "🧪", "label": "Version test", "color": "purple"},
    "future": {"emoji": "🔮", "label": "Prochainement", "color": "gray"}
}

# CURRICULUM COMPLET avec feature flags
CURRICULUM_DATA_COMPLETE = {
    # ✅ ACTIFS (fonctionnels)
    "Mathématiques": {
        "status": "active",
        "description": "Générateur d'exercices avec schémas géométriques et rendu LaTeX",
        "features": ["geometric_schemas", "latex_rendering", "ai_generation"],
        "data": {
            "CP": {"Nombres, calcul et résolution de problèmes": [
                "Décomposer et représenter les nombres entiers jusqu'à 20",
                "Comparer et ranger les nombres entiers jusqu'à 20", 
                "Addition et soustraction des nombres entiers jusqu'à 20",
                "La résolution de problèmes avec les nombres jusqu'à 20"
            ], "Grandeurs et mesures": [
                "Les longueurs et résolution de problèmes avec les longueurs",
                "Les masses et la résolution de problèmes avec les masses",
                "Les contenances et la résolution de problèmes avec les contenances",
                "La résolution de problèmes avec dates et durées",
                "La monnaie et résolution de problèmes avec la monnaie"
            ], "Espace et géométrie": [
                "Le repérage et déplacement dans l'espace",
                "Les instruments de tracé",
                "Les segments et les droites",
                "Figures géométriques simples (carré, rectangle, triangles et cercles)",
                "La symétrie",
                "Les solides"
            ]},
            "CE1": {"Nombres, calcul et résolution de problèmes": [
                "Décomposer et représenter les nombres entiers jusqu'à 999",
                "Comparer et ranger les nombres entiers",
                "Addition et soustraction des nombres entiers", 
                "La résolution de problèmes",
                "Multiplication de nombres entiers",
                "Les doubles et les moitiés"
            ], "Grandeurs et mesures": [
                "Les longueurs et résolution de problèmes avec les longueurs",
                "Les masses et la résolution de problèmes avec les masses",
                "Les contenances et la résolution de problèmes avec les contenances",
                "La résolution de problèmes avec dates et durées",
                "La monnaie et résolution de problèmes avec la monnaie"
            ], "Espace et géométrie": [
                "Le repérage et déplacement dans l'espace",
                "Les instruments de tracé", 
                "Les segments et les droites",
                "Figures géométriques simples (carré, rectangle, triangles et cercles)",
                "La symétrie",
                "Les solides"
            ]},
            "CE2": {"Nombres, calcul et résolution de problèmes": [
                "Décomposer et représenter les nombres entiers jusqu'à 999",
                "Comparer et ranger les nombres entiers",
                "Addition et soustraction des nombres entiers",
                "La résolution de problèmes",
                "Multiplication de nombres entiers", 
                "Les doubles et les moitiés"
            ], "Grandeurs et mesures": [
                "Les longueurs et résolution de problèmes avec les longueurs",
                "Les masses et la résolution de problèmes avec les masses",
                "Les contenances et la résolution de problèmes avec les contenances",
                "La résolution de problèmes avec dates et durées",
                "La monnaie et résolution de problèmes avec la monnaie"
            ], "Espace et géométrie": [
                "Le repérage et déplacement dans l'espace",
                "Les instruments de tracé",
                "Les segments et les droites", 
                "Figures géométriques simples (carré, rectangle, triangles et cercles)",
                "La symétrie",
                "Les solides"
            ]},
            "CM1": {"Nombres, calcul et résolution de problèmes": [
                "Nombres entiers",
                "Fractions",
                "Calculs avec les nombres entiers",
                "Calculs avec les fractions",
                "Résolution de problèmes"
            ], "Grandeurs et mesures": [
                "Mesures de longueurs",
                "Mesures de masses",
                "Mesures de capacités", 
                "Mesures d'aires",
                "Mesures de temps",
                "Mesures d'angles"
            ], "Espace et géométrie": [
                "Géométrie du plan",
                "Géométrie dans l'espace",
                "Propriétés géométriques",
                "Constructions géométriques"
            ]},
            "CM2": {"Nombres, calcul et résolution de problèmes": [
                "Nombres entiers",
                "Nombres décimaux",
                "Fractions",
                "Calculs avec les nombres entiers",
                "Calculs avec les nombres décimaux",
                "Calculs avec les fractions",
                "Résolution de problèmes"
            ], "Grandeurs et mesures": [
                "Mesures de longueurs",
                "Mesures de masses",
                "Mesures de capacités",
                "Mesures d'aires",
                "Mesures de temps", 
                "Mesures d'angles"
            ], "Espace et géométrie": [
                "Géométrie du plan",
                "Géométrie dans l'espace", 
                "Propriétés géométriques",
                "Constructions géométriques"
            ]},
            "6e": {"Nombres et calculs": [
                "Nombres entiers et décimaux",
                "Fractions",
                "Nombres en écriture fractionnaire",
                "Calcul mental",
                "Calculs posés",
                "Calculs instrumentés"
            ], "Grandeurs et mesures": [
                "Longueurs, masses, durées",
                "Aires",
                "Périmètres et aires",
                "Volumes", 
                "Angles"
            ], "Espace et géométrie": [
                "Géométrie dans l'espace",
                "Géométrie dans le plan",
                "Symétrie axiale"
            ], "Organisation et gestion de données": [
                "Proportionnalité"
            ]},
            "5e": {"Nombres et calculs": [
                "Nombres relatifs",
                "Nombres rationnels",
                "Calcul littéral",
                "Puissances"
            ], "Grandeurs et mesures": [
                "Aires et périmètres",
                "Volumes",
                "Angles et triangles"
            ], "Espace et géométrie": [
                "Triangles",
                "Parallélogrammes",
                "Symétrie centrale",
                "Homothétie"
            ], "Organisation et gestion de données, fonctions": [
                "Proportionnalité",
                "Statistiques",
                "Probabilités"
            ]},
            "4e": {"Nombres et calculs": [
                "Nombres relatifs",
                "Fractions", 
                "Calcul littéral",
                "Équations et inéquations",
                "Puissances"
            ], "Grandeurs et mesures": [
                "Théorème de Pythagore",
                "Distances et tangentes",
                "Cosinus"
            ], "Espace et géométrie": [
                "Triangles et droites remarquables",
                "Translation et rotation",
                "Géométrie dans l'espace"
            ], "Organisation et gestion de données, fonctions": [
                "Proportionnalité",
                "Statistiques",
                "Probabilités",
                "Fonctions linéaires"
            ]},
            "3e": {"Nombres et calculs": [
                "Nombres entiers et rationnels",
                "Nombres réels",
                "Calcul littéral",
                "Équations et inéquations",
                "Arithmétique"
            ], "Grandeurs et mesures": [
                "Théorème de Thalès",
                "Trigonométrie",
                "Aires et volumes"
            ], "Espace et géométrie": [
                "Géométrie dans l'espace",
                "Transformations du plan",
                "Configurations du plan"
            ], "Organisation et gestion de données, fonctions": [
                "Fonctions",
                "Statistiques et probabilités",
                "Algorithmique et programmation"
            ]}
        }
    },
    
    "Physique-Chimie": {
        "status": "active",
        "description": "Exercices expérimentaux avec calculs et situations concrètes",
        "features": ["experimental_situations", "unit_calculations", "scientific_vocabulary"],
        "data": {
            "5e": {"Physique-Chimie": [
                "Organisation et transformations de la matière",
                "Mouvements et interactions",
                "L'énergie et ses conversions",
                "Des signaux pour observer et communiquer"
            ]},
            "4e": {"Physique-Chimie": [
                "Organisation et transformations de la matière",
                "Mouvements et interactions", 
                "L'énergie et ses conversions",
                "Des signaux pour observer et communiquer"
            ]},
            "3e": {"Physique-Chimie": [
                "Organisation et transformations de la matière",
                "Mouvements et interactions",
                "L'énergie et ses conversions", 
                "Des signaux pour observer et communiquer"
            ]},
            "Seconde": {"Physique-Chimie": [
                "Constitution et transformations de la matière",
                "Mouvement et interactions",
                "Ondes et signaux"
            ]},
            "Première": {"Physique-Chimie": [
                "Constitution et transformations de la matière",
                "Mouvement et interactions",
                "L'énergie : conversions et transferts",
                "Ondes et signaux"
            ]},
            "Terminale": {"Physique-Chimie": [
                "Constitution et transformations de la matière", 
                "Mouvement et interactions",
                "L'énergie : conversions et transferts",
                "Ondes et signaux"
            ]}
        }
    },
    
    "SVT": {
        "status": "active",
        "description": "Exercices d'analyse et d'observation scientifique",
        "features": ["scientific_analysis", "observation_exercises", "biological_reasoning"],
        "data": {
            "5e": {"Sciences de la vie et de la Terre": [
                "La planète Terre, l'environnement et l'action humaine",
                "Le vivant et son évolution",
                "Le corps humain et la santé"
            ]},
            "4e": {"Sciences de la vie et de la Terre": [
                "La planète Terre, l'environnement et l'action humaine",
                "Le vivant et son évolution", 
                "Le corps humain et la santé"
            ]},
            "3e": {"Sciences de la vie et de la Terre": [
                "La planète Terre, l'environnement et l'action humaine",
                "Le vivant et son évolution",
                "Le corps humain et la santé"
            ]},
            "Seconde": {"Sciences de la vie et de la Terre": [
                "La Terre, la vie et l'organisation du vivant",
                "Les enjeux contemporains de la planète", 
                "Corps humain et santé"
            ]}
        }
    },

    # 🔄 COMING SOON - Octobre 2025
    "Français": {
        "status": "active",
        "expected": "Octobre 2025",
        "description": "Grammaire, vocabulaire, expression écrite, compréhension de lecture",
        "features": ["grammar_analysis", "text_comprehension", "writing_exercises"],
        "note": "Prompts IA spécialisés en cours de développement",
        "data": {
            "CP": {"Français": [
                "Lecture - Décodage et automatisation",
                "Lecture - Compréhension de textes",
                "Lecture à voix haute",
                "Écriture - Geste graphique et copie",
                "Écriture - Dictée",
                "Écriture - Production d'écrits",
                "Oral - Comprendre un énoncé oral",
                "Oral - Parler en continu",
                "Oral - Parler en interaction",
                "Vocabulaire - Acquisition et structuration",
                "Grammaire et orthographe - Classes de mots",
                "Grammaire et orthographe - Fonctions grammaticales",
                "Grammaire et orthographe - Orthographe lexicale",
                "Grammaire et orthographe - Orthographe grammaticale"
            ]},
            "CE1": {"Français": [
                "Lecture - Décodage et automatisation",
                "Lecture - Compréhension de textes",
                "Lecture à voix haute",
                "Écriture - Geste graphique et copie",
                "Écriture - Dictée",
                "Écriture - Production d'écrits",
                "Oral - Comprendre un énoncé oral",
                "Oral - Parler en continu",
                "Oral - Parler en interaction",
                "Vocabulaire - Acquisition et structuration",
                "Grammaire et orthographe - Classes de mots",
                "Grammaire et orthographe - Fonctions grammaticales",
                "Grammaire et orthographe - Orthographe lexicale",
                "Grammaire et orthographe - Orthographe grammaticale"
            ]},
            "CE2": {"Français": [
                "Lecture - Décodage et automatisation",
                "Lecture - Compréhension de textes",
                "Lecture à voix haute",
                "Écriture - Geste graphique et copie",
                "Écriture - Dictée",
                "Écriture - Production d'écrits",
                "Oral - Comprendre un énoncé oral",
                "Oral - Parler en continu",
                "Oral - Parler en interaction",
                "Vocabulaire - Acquisition et structuration",
                "Grammaire et orthographe - Classes de mots",
                "Grammaire et orthographe - Fonctions grammaticales",
                "Grammaire et orthographe - Orthographe lexicale",
                "Grammaire et orthographe - Orthographe grammaticale"
            ]},
            "CM1": {"Français": [
                "Langage oral - Écouter pour comprendre",
                "Langage oral - Parler en prenant appui sur des notes",
                "Langage oral - Participer à des échanges",
                "Lecture et compréhension de l'écrit - Maintenir l'automatisation",
                "Lecture et compréhension de l'écrit - Comprendre des textes littéraires",
                "Lecture et compréhension de l'écrit - Comprendre des textes documentaires",
                "Lecture et compréhension de l'écrit - Contrôler sa compréhension",
                "Écriture - Écrire à la main de manière fluide",
                "Écriture - Maîtriser le fonctionnement du traitement de texte",
                "Écriture - Recourir à l'écriture pour réfléchir et apprendre",
                "Écriture - Produire des écrits variés",
                "Étude de la langue - Classes grammaticales",
                "Étude de la langue - Fonctions grammaticales",
                "Étude de la langue - Le verbe",
                "Étude de la langue - L'orthographe lexicale",
                "Étude de la langue - L'orthographe grammaticale",
                "Culture littéraire et artistique - Héros et héroïnes",
                "Culture littéraire et artistique - La morale en question",
                "Culture littéraire et artistique - Se confronter au merveilleux",
                "Culture littéraire et artistique - Vivre des aventures"
            ]},
            "CM2": {"Français": [
                "Langage oral - Écouter pour comprendre",
                "Langage oral - Parler en prenant appui sur des notes",
                "Langage oral - Participer à des échanges",
                "Lecture et compréhension de l'écrit - Maintenir l'automatisation",
                "Lecture et compréhension de l'écrit - Comprendre des textes littéraires",
                "Lecture et compréhension de l'écrit - Comprendre des textes documentaires",
                "Lecture et compréhension de l'écrit - Contrôler sa compréhension",
                "Écriture - Écrire à la main de manière fluide",
                "Écriture - Maîtriser le fonctionnement du traitement de texte",
                "Écriture - Recourir à l'écriture pour réfléchir et apprendre",
                "Écriture - Produire des écrits variés",
                "Étude de la langue - Classes grammaticales",
                "Étude de la langue - Fonctions grammaticales",
                "Étude de la langue - Le verbe",
                "Étude de la langue - L'orthographe lexicale",
                "Étude de la langue - L'orthographe grammaticale",
                "Culture littéraire et artistique - Héros et héroïnes",
                "Culture littéraire et artistique - La morale en question",
                "Culture littéraire et artistique - Se confronter au merveilleux",
                "Culture littéraire et artistique - Vivre des aventures"
            ]},
            "6e": {"Français": [
                "Langage oral - Écouter pour comprendre",
                "Langage oral - Parler en prenant appui sur des notes", 
                "Langage oral - Participer à des échanges",
                "Lecture et compréhension de l'écrit - Maintenir l'automatisation",
                "Lecture et compréhension de l'écrit - Comprendre des textes littéraires",
                "Lecture et compréhension de l'écrit - Comprendre des textes documentaires",
                "Lecture et compréhension de l'écrit - Contrôler sa compréhension",
                "Écriture - Écrire à la main de manière fluide",
                "Écriture - Maîtriser le fonctionnement du traitement de texte",
                "Écriture - Recourir à l'écriture pour réfléchir et apprendre",
                "Écriture - Produire des écrits variés",
                "Étude de la langue - Classes grammaticales",
                "Étude de la langue - Fonctions grammaticales",
                "Étude de la langue - Le verbe",
                "Étude de la langue - L'orthographe lexicale",
                "Étude de la langue - L'orthographe grammaticale",
                "Culture littéraire et artistique - Héros et héroïnes",
                "Culture littéraire et artistique - La morale en question",
                "Culture littéraire et artistique - Se confronter au merveilleux",
                "Culture littéraire et artistique - Vivre des aventures"
            ]},
            "5e": {"Français": [
                "Langage oral - Comprendre et interpréter des discours oraux",
                "Langage oral - Produire une parole continue",
                "Langage oral - Interagir dans un débat",
                "Lecture et compréhension - Lire et comprendre l'implicite",
                "Lecture et compréhension - Adapter sa lecture aux supports",
                "Lecture et compréhension - Élaborer une interprétation",
                "Écriture - Exploiter les principales fonctions de l'écrit",
                "Écriture - Adopter des stratégies d'écriture efficaces",
                "Écriture - Exploiter des lectures pour enrichir son écrit",
                "Étude de la langue - Maîtriser la forme des mots",
                "Étude de la langue - Maîtriser le fonctionnement du verbe",
                "Étude de la langue - Maîtriser la syntaxe de la phrase",
                "Culture littéraire - Se chercher, se construire",
                "Culture littéraire - Vivre en société, participer à la société",
                "Culture littéraire - Regarder le monde, inventer des mondes",
                "Culture littéraire - Agir sur le monde"
            ]},
            "4e": {"Français": [
                "Langage oral - Comprendre et interpréter des discours oraux",
                "Langage oral - Produire une parole continue",
                "Langage oral - Interagir dans un débat",
                "Lecture et compréhension - Lire et comprendre l'implicite",
                "Lecture et compréhension - Adapter sa lecture aux supports",
                "Lecture et compréhension - Élaborer une interprétation",
                "Écriture - Exploiter les principales fonctions de l'écrit",
                "Écriture - Adopter des stratégies d'écriture efficaces",
                "Écriture - Exploiter des lectures pour enrichir son écrit",
                "Étude de la langue - Maîtriser la forme des mots",
                "Étude de la langue - Maîtriser le fonctionnement du verbe",
                "Étude de la langue - Maîtriser la syntaxe de la phrase",
                "Culture littéraire - Se chercher, se construire",
                "Culture littéraire - Vivre en société, participer à la société",
                "Culture littéraire - Regarder le monde, inventer des mondes",
                "Culture littéraire - Agir sur le monde"
            ]},
            "3e": {"Français": [
                "Langage oral - Comprendre et interpréter des discours oraux",
                "Langage oral - Produire une parole continue",
                "Langage oral - Interagir dans un débat",
                "Lecture et compréhension - Lire et comprendre l'implicite",
                "Lecture et compréhension - Adapter sa lecture aux supports",
                "Lecture et compréhension - Élaborer une interprétation",
                "Écriture - Exploiter les principales fonctions de l'écrit",
                "Écriture - Adopter des stratégies d'écriture efficaces",
                "Écriture - Exploiter des lectures pour enrichir son écrit",
                "Étude de la langue - Maîtriser la forme des mots",
                "Étude de la langue - Maîtriser le fonctionnement du verbe",
                "Étude de la langue - Maîtriser la syntaxe de la phrase",
                "Culture littéraire - Se chercher, se construire",
                "Culture littéraire - Vivre en société, participer à la société",
                "Culture littéraire - Regarder le monde, inventer des mondes",
                "Culture littéraire - Agir sur le monde"
            ]},
            "Seconde": {"Français": [
                "La poésie du XIXe au XXe siècle",
                "La littérature d'idées du XVIe au XVIIIe siècle",
                "Le roman et le récit du Moyen Âge au XXIe siècle",
                "Le théâtre du XVIIe au XXIe siècle"
            ]},
            "Première": {"Français": [
                "La poésie du XIXe au XXIe siècle",
                "La littérature d'idées du XVIe au XVIIIe siècle",
                "Le roman et le récit du Moyen Âge au XXIe siècle",
                "Le théâtre du XVIIe au XXIe siècle"
            ]}
        }
    },

    "EMC": {
        "status": "coming_soon",
        "expected": "Octobre 2025",
        "description": "Réflexion civique, débats moraux, situations d'éthique",
        "features": ["civic_reflection", "moral_debates", "ethical_situations"],
        "note": "Adaptation pédagogique française en cours",
        "data": {
            "CP": {"EMC": [
                "La sensibilité : soi et les autres",
                "Le droit et la règle",
                "Le jugement : penser par soi-même",
                "L'engagement : agir individuellement et collectivement"
            ]},
            "CE1": {"EMC": [
                "La sensibilité : soi et les autres",
                "Le droit et la règle", 
                "Le jugement : penser par soi-même",
                "L'engagement : agir individuellement et collectivement"
            ]},
            "CE2": {"EMC": [
                "La sensibilité : soi et les autres",
                "Le droit et la règle",
                "Le jugement : penser par soi-même",
                "L'engagement : agir individuellement et collectivement"
            ]},
            "CM1": {"EMC": [
                "La sensibilité - Identifier et partager des émotions",
                "Le droit et la règle - Comprendre les raisons de l'obéissance",
                "Le jugement - Développer les aptitudes au discernement",
                "L'engagement - Pouvoir expliquer ses choix et ses actes"
            ]},
            "CM2": {"EMC": [
                "La sensibilité - Identifier et partager des émotions",
                "Le droit et la règle - Comprendre les raisons de l'obéissance",
                "Le jugement - Développer les aptitudes au discernement",
                "L'engagement - Pouvoir expliquer ses choix et ses actes"
            ]},
            "6e": {"EMC": [
                "La sensibilité - Identifier et partager des émotions",
                "Le droit et la règle - Comprendre les raisons de l'obéissance",
                "Le jugement - Développer les aptitudes au discernement", 
                "L'engagement - Pouvoir expliquer ses choix et ses actes"
            ]},
            "5e": {"EMC": [
                "La sensibilité - Exprimer ses sentiments moraux",
                "Le droit et la règle - Comprendre la diversité des sentiments",
                "Le jugement - Comprendre que la laïcité accorde à chacun un droit égal",
                "L'engagement - Connaître les principes, valeurs et symboles de la République"
            ]},
            "4e": {"EMC": [
                "La sensibilité - Exprimer ses sentiments moraux",
                "Le droit et la règle - Comprendre la diversité des sentiments",
                "Le jugement - Comprendre que la laïcité accorde à chacun un droit égal",
                "L'engagement - Connaître les principes, valeurs et symboles de la République"
            ]},
            "3e": {"EMC": [
                "La sensibilité - Exprimer ses sentiments moraux",
                "Le droit et la règle - Comprendre la diversité des sentiments",
                "Le jugement - Comprendre que la laïcité accorde à chacun un droit égal",
                "L'engagement - Connaître les principes, valeurs et symboles de la République"
            ]},
            "Seconde": {"EMC": [
                "Des libertés pour la liberté",
                "Égaux et fraternels",
                "La laïcité"
            ]},
            "Première": {"EMC": [
                "Fondements et fragilités du lien social",
                "Les recompositions du lien social"
            ]},
            "Terminale": {"EMC": [
                "Démocratie et participation politique",
                "Souveraineté nationale et construction européenne"
            ]}
        }
    },

    # 📋 PLANNED - Nov-Déc 2025
    "Histoire": {
        "status": "planned",
        "expected": "Novembre 2025",
        "description": "Chronologies, personnages historiques, causes et conséquences",
        "features": ["chronological_analysis", "historical_figures", "cause_effect"],
        "note": "Intégration progressive des supports documentaires",
        "data": {
            "CM1": {"Histoire": [
                "Et avant la France ? - Traces d'occupation ancienne",
                "Et avant la France ? - Celtes, Gaulois, Grecs et Romains",
                "Et avant la France ? - Les grands mouvements de populations",
                "Le temps des rois - Louis IX, le roi chrétien",
                "Le temps des rois - François Ier, Renaissance",
                "Le temps des rois - Henri IV et l'édit de Nantes",
                "Le temps des rois - Louis XIV, le roi Soleil",
                "Le temps de la Révolution et de l'Empire",
                "Le temps de la République - 1870 à 1914",
                "L'âge industriel en France",
                "La France, des guerres mondiales à l'Union européenne"
            ]},
            "CM2": {"Histoire": [
                "Et avant la France ? - Traces d'occupation ancienne",
                "Et avant la France ? - Celtes, Gaulois, Grecs et Romains",
                "Et avant la France ? - Les grands mouvements de populations",
                "Le temps des rois - Louis IX, le roi chrétien",
                "Le temps des rois - François Ier, Renaissance",
                "Le temps des rois - Henri IV et l'édit de Nantes",
                "Le temps des rois - Louis XIV, le roi Soleil",
                "Le temps de la Révolution et de l'Empire",
                "Le temps de la République - 1870 à 1914",
                "L'âge industriel en France",
                "La France, des guerres mondiales à l'Union européenne"
            ]},
            "6e": {"Histoire": [
                "Et avant la France ? - Traces d'occupation ancienne",
                "Et avant la France ? - Celtes, Gaulois, Grecs et Romains",
                "Et avant la France ? - Les grands mouvements de populations",
                "Le temps des rois - Louis IX, le roi chrétien",
                "Le temps des rois - François Ier, Renaissance",
                "Le temps des rois - Henri IV et l'édit de Nantes",
                "Le temps des rois - Louis XIV, le roi Soleil",
                "Le temps de la Révolution et de l'Empire",
                "Le temps de la République - 1870 à 1914",
                "L'âge industriel en France",
                "La France, des guerres mondiales à l'Union européenne"
            ]},
            "5e": {"Histoire": [
                "Chrétientés et islam (VIe-XIIIe siècles)",
                "Société, Église et pouvoir politique dans l'Occident féodal",
                "Transformations de l'Europe et ouverture sur le monde",
                "Le XVIIIe siècle. Expansions, Lumières et révolutions",
                "L'Europe et le monde au XIXe siècle",
                "Société, culture et politique dans la France du XIXe siècle",
                "L'Europe, un théâtre majeur des guerres totales",
                "Le monde depuis 1945",
                "Françaises et Français dans une République repensée"
            ]},
            "4e": {"Histoire": [
                "Chrétientés et islam (VIe-XIIIe siècles)",
                "Société, Église et pouvoir politique dans l'Occident féodal",
                "Transformations de l'Europe et ouverture sur le monde",
                "Le XVIIIe siècle. Expansions, Lumières et révolutions",
                "L'Europe et le monde au XIXe siècle",
                "Société, culture et politique dans la France du XIXe siècle",
                "L'Europe, un théâtre majeur des guerres totales",
                "Le monde depuis 1945",
                "Françaises et Français dans une République repensée"
            ]},
            "3e": {"Histoire": [
                "Chrétientés et islam (VIe-XIIIe siècles)",
                "Société, Église et pouvoir politique dans l'Occident féodal",
                "Transformations de l'Europe et ouverture sur le monde",
                "Le XVIIIe siècle. Expansions, Lumières et révolutions",
                "L'Europe et le monde au XIXe siècle",
                "Société, culture et politique dans la France du XIXe siècle",
                "L'Europe, un théâtre majeur des guerres totales",
                "Le monde depuis 1945",
                "Françaises et Français dans une République repensée"
            ]},
            "Seconde": {"Histoire": [
                "Le monde méditerranéen : empreintes de l'Antiquité",
                "XVe-XVIe siècles : un nouveau rapport au monde",
                "L'État à l'époque moderne : France et Angleterre",
                "Révolutions, libertés, nations, à l'aube de l'époque contemporaine",
                "Sociétés et environnements : des équilibres fragiles",
                "Territoires, populations et développement",
                "Des mobilités généralisées",
                "L'Afrique australe : un espace en profonde mutation"
            ]},
            "Première": {"Histoire": [
                "L'Europe face aux révolutions",
                "La France dans l'Europe des nationalités",
                "La Troisième République",
                "Totalitarismes et Seconde Guerre mondiale",
                "La recomposition du monde (1945-1991)",
                "La métropolisation : un processus mondial différencié",
                "Une diversification des espaces et des acteurs de la production",
                "Les espaces ruraux : multifonctionnalité ou fragmentation ?"
            ]},
            "Terminale": {"Histoire": [
                "Fragilités des démocraties, totalitarismes (1929-1945)",
                "La multiplication des acteurs internationaux (1945-1991)",
                "Nouvelles conflictualités depuis la fin de la guerre froide",
                "L'Asie du Sud et de l'Est : les enjeux de la croissance",
                "L'Afrique : défis du développement et de la mondialisation",
                "L'océan Indien : nouvel espace stratégique"
            ]}
        }
    },

    "Géographie": {
        "status": "active",
        "expected": "Décembre 2025",
        "description": "Cartes interactives, données statistiques, études de cas",
        "features": ["interactive_maps", "statistical_data", "case_studies"],
        "note": "Intégration progressive des cartes IGN",
        "data": {
            "CM1": {"Géographie": [
                "Découvrir le(s) lieu(x) où j'habite",
                "Se loger, travailler, se cultiver, avoir des loisirs",
                "Satisfaire les besoins en énergie, en eau",
                "Se déplacer - Moyens de transport",
                "Communiquer d'un bout à l'autre du monde",
                "Mieux habiter - La ville de demain",
                "Mieux habiter - Les espaces ruraux"
            ]},
            "CM2": {"Géographie": [
                "Découvrir le(s) lieu(x) où j'habite",
                "Se loger, travailler, se cultiver, avoir des loisirs",
                "Satisfaire les besoins en énergie, en eau",
                "Se déplacer - Moyens de transport",
                "Communiquer d'un bout à l'autre du monde",
                "Mieux habiter - La ville de demain",
                "Mieux habiter - Les espaces ruraux"
            ]},
            "6e": {"Géographie": [
                "Découvrir le(s) lieu(x) où j'habite",
                "Se loger, travailler, se cultiver, avoir des loisirs",
                "Satisfaire les besoins en énergie, en eau",
                "Se déplacer - Moyens de transport",
                "Communiquer d'un bout à l'autre du monde",
                "Mieux habiter - La ville de demain",
                "Mieux habiter - Les espaces ruraux"
            ]},
            "5e": {"Géographie": [
                "La planète Terre, l'environnement et l'action humaine",
                "Des ressources limitées, à gérer et à renouveler",
                "Prévenir les risques, s'adapter au changement global",
                "L'urbanisation du monde",
                "Les mobilités humaines transnationales",
                "Des espaces transformés par la mondialisation"
            ]},
            "4e": {"Géographie": [
                "La planète Terre, l'environnement et l'action humaine",
                "Des ressources limitées, à gérer et à renouveler",
                "Prévenir les risques, s'adapter au changement global",
                "L'urbanisation du monde",
                "Les mobilités humaines transnationales",
                "Des espaces transformés par la mondialisation"
            ]},
            "3e": {"Géographie": [
                "La planète Terre, l'environnement et l'action humaine",
                "Des ressources limitées, à gérer et à renouveler",
                "Prévenir les risques, s'adapter au changement global",
                "L'urbanisation du monde",
                "Les mobilités humaines transnationales",
                "Des espaces transformés par la mondialisation"
            ]},
            "Seconde": {"Géographie": [
                "Le monde méditerranéen : empreintes de l'Antiquité",
                "XVe-XVIe siècles : un nouveau rapport au monde",
                "L'État à l'époque moderne : France et Angleterre",
                "Révolutions, libertés, nations, à l'aube de l'époque contemporaine",
                "Sociétés et environnements : des équilibres fragiles",
                "Territoires, populations et développement",
                "Des mobilités généralisées",
                "L'Afrique australe : un espace en profonde mutation"
            ]},
            "Première": {"Géographie": [
                "L'Europe face aux révolutions",
                "La France dans l'Europe des nationalités",
                "La Troisième République",
                "Totalitarismes et Seconde Guerre mondiale",
                "La recomposition du monde (1945-1991)",
                "La métropolisation : un processus mondial différencié",
                "Une diversification des espaces et des acteurs de la production",
                "Les espaces ruraux : multifonctionnalité ou fragmentation ?"
            ]},
            "Terminale": {"Géographie": [
                "Fragilités des démocraties, totalitarismes (1929-1945)",
                "La multiplication des acteurs internationaux (1945-1991)",
                "Nouvelles conflictualités depuis la fin de la guerre froide",
                "L'Asie du Sud et de l'Est : les enjeux de la croissance",
                "L'Afrique : défis du développement et de la mondialisation",
                "L'océan Indien : nouvel espace stratégique"
            ]}
        }
    },

    "SES": {
        "status": "planned", 
        "expected": "Décembre 2025",
        "description": "Analyses économiques, sociologiques et politiques",
        "features": ["economic_analysis", "sociological_reasoning", "political_concepts"],
        "note": "Adaptation aux nouveaux programmes 2025",
        "data": {
            "Seconde": {"SES": [
                "Comment les économistes, les sociologues et les politistes raisonnent-ils ?",
                "Comment crée-t-on des richesses et comment les mesure-t-on ?",
                "Comment se forment les prix sur un marché ?",
                "Comment devenons-nous des acteurs sociaux ?",
                "Comment s'organise la vie politique ?",
                "Quelles relations entre le diplôme, l'emploi et les salaires ?"
            ]},
            "Première": {"SES (Spécialité)": [
                "Science économique - Les marchés",
                "Science économique - La monnaie et le financement",
                "Science économique - Les politiques économiques",
                "Sociologie et science politique - Socialisation",
                "Sociologie et science politique - Groupes et réseaux sociaux",
                "Sociologie et science politique - Contrôle social",
                "Regards croisés - Entreprise et production"
            ]},
            "Terminale": {"SES (Spécialité)": [
                "Science économique - Croissance, fluctuations et crises",
                "Science économique - Mondialisation, finance internationale",
                "Science économique - Politiques publiques et régulation",
                "Sociologie et science politique - Classes et stratification",
                "Sociologie et science politique - Intégration et solidarité",
                "Sociologie et science politique - Mutations du travail",
                "Regards croisés - Justice sociale et inégalités",
                "Regards croisés - Travail, emploi, chômage"
            ]}
        }
    },

    "Philosophie": {
        "status": "planned",
        "expected": "Janvier 2026",
        "description": "Réflexions conceptuelles, dissertations, commentaires de textes",
        "features": ["conceptual_analysis", "dissertation_structure", "text_commentary"],
        "note": "Adaptation aux épreuves du baccalauréat",
        "data": {
            "Terminale": {"Philosophie": [
                "La conscience",
                "L'inconscient", 
                "La perception",
                "Autrui",
                "Le désir",
                "L'existence et le temps",
                "La culture",
                "Le langage",
                "L'art",
                "La technique",
                "Le travail",
                "La religion",
                "La société",
                "Les échanges",
                "La justice",
                "L'État",
                "Le droit",
                "La liberté",
                "Le devoir",
                "Le bonheur",
                "La morale",
                "La politique",
                "La raison et le réel",
                "Théorie et expérience",
                "La démonstration",
                "L'interprétation",
                "Le vivant",
                "La matière et l'esprit",
                "La vérité"
            ]}
        }
    },

    # 🧪 BETA - Jan-Mars 2026
    "Questionner le monde": {
        "status": "beta",
        "expected": "Février 2026",
        "description": "Découverte scientifique et géographique pour les plus jeunes",
        "features": ["discovery_exercises", "simple_experiments", "world_exploration"],
        "note": "Version test avec retours enseignants",
        "data": {
            "CP": {"Questionner le monde": [
                "Qu'est-ce que la matière ?",
                "Comment reconnaître le monde vivant ?",
                "Les objets techniques",
                "Se situer dans l'espace",
                "Se situer dans le temps",
                "Explorer les organisations du monde"
            ]},
            "CE1": {"Questionner le monde": [
                "Qu'est-ce que la matière ?",
                "Comment reconnaître le monde vivant ?",
                "Les objets techniques",
                "Se situer dans l'espace",
                "Se situer dans le temps",
                "Explorer les organisations du monde"
            ]},
            "CE2": {"Questionner le monde": [
                "Qu'est-ce que la matière ?",
                "Comment reconnaître le monde vivant ?",
                "Les objets techniques",
                "Se situer dans l'espace",
                "Se situer dans le temps",
                "Explorer les organisations du monde"
            ]}
        }
    },

    "Sciences et technologie": {
        "status": "beta",
        "expected": "Mars 2026",
        "description": "Approche interdisciplinaire sciences et technologie",
        "features": ["interdisciplinary_approach", "technological_projects", "scientific_method"],
        "note": "Tests avec établissements pilotes",
        "data": {
            "CM1": {"Sciences et technologie": [
                "Matière, mouvement, énergie, information - États de la matière",
                "Matière, mouvement, énergie, information - Mélanges et solutions",
                "Matière, mouvement, énergie, information - Mouvements",
                "Le vivant, sa diversité et les fonctions - Classification du vivant",
                "Le vivant, sa diversité et les fonctions - Évolution des espèces",
                "Le vivant, sa diversité et les fonctions - Fonctions de nutrition",
                "Matériaux et objets techniques - L'évolution des objets",
                "Matériaux et objets techniques - Familles de matériaux",
                "La planète Terre - Volcans et séismes",
                "La planète Terre - Météorologie et climatologie"
            ]},
            "CM2": {"Sciences et technologie": [
                "Matière, mouvement, énergie, information - États de la matière",
                "Matière, mouvement, énergie, information - Mélanges et solutions",
                "Matière, mouvement, énergie, information - Mouvements",
                "Le vivant, sa diversité et les fonctions - Classification du vivant",
                "Le vivant, sa diversité et les fonctions - Évolution des espèces",
                "Le vivant, sa diversité et les fonctions - Fonctions de nutrition",
                "Matériaux et objets techniques - L'évolution des objets",
                "Matériaux et objets techniques - Familles de matériaux",
                "La planète Terre - Volcans et séismes",
                "La planète Terre - Météorologie et climatologie"
            ]},
            "6e": {"Sciences et technologie": [
                "Matière, mouvement, énergie, information - États de la matière",
                "Matière, mouvement, énergie, information - Mélanges et solutions",
                "Matière, mouvement, énergie, information - Mouvements",
                "Le vivant, sa diversité et les fonctions - Classification du vivant",
                "Le vivant, sa diversité et les fonctions - Évolution des espèces",
                "Le vivant, sa diversité et les fonctions - Fonctions de nutrition",
                "Matériaux et objets techniques - L'évolution des objets",
                "Matériaux et objets techniques - Familles de matériaux",
                "La planète Terre - Volcans et séismes",
                "La planète Terre - Météorologie et climatologie"
            ]}
        }
    },

    "EPS": {
        "status": "beta",
        "expected": "Mars 2026",
        "description": "Exercices théoriques sur le sport et l'activité physique",
        "features": ["sports_theory", "physical_preparation", "health_concepts"],
        "note": "Focus sur les aspects théoriques de l'EPS",
        "data": {
            "CP": {"EPS": [
                "Produire une performance maximale",
                "Adapter ses déplacements",
                "S'exprimer devant les autres",
                "Conduire et maîtriser un affrontement"
            ]},
            "CE1": {"EPS": [
                "Produire une performance maximale",
                "Adapter ses déplacements",
                "S'exprimer devant les autres",
                "Conduire et maîtriser un affrontement"
            ]},
            "CE2": {"EPS": [
                "Produire une performance maximale",
                "Adapter ses déplacements",
                "S'exprimer devant les autres",
                "Conduire et maîtriser un affrontement"
            ]}
        }
    },

    "Enseignements artistiques": {
        "status": "beta",
        "expected": "Mars 2026",
        "description": "Arts plastiques et éducation musicale théoriques",
        "features": ["art_analysis", "music_theory", "creative_exercises"],
        "note": "Aspects théoriques des enseignements artistiques",
        "data": {
            "CP": {"Enseignements artistiques": [
                "Arts plastiques - Expression et création",
                "Arts plastiques - Mise en œuvre",
                "Éducation musicale - Chanter",
                "Éducation musicale - Écouter, comparer",
                "Éducation musicale - Explorer, imaginer"
            ]},
            "CE1": {"Enseignements artistiques": [
                "Arts plastiques - Expression et création",
                "Arts plastiques - Mise en œuvre",
                "Éducation musicale - Chanter",
                "Éducation musicale - Écouter, comparer",
                "Éducation musicale - Explorer, imaginer"
            ]},
            "CE2": {"Enseignements artistiques": [
                "Arts plastiques - Expression et création",
                "Arts plastiques - Mise en œuvre",
                "Éducation musicale - Chanter",
                "Éducation musicale - Écouter, comparer",
                "Éducation musicale - Explorer, imaginer"
            ]}
        }
    },

    # 🔮 FUTURE - 2026+
    "Technologie": {
        "status": "future",
        "expected": "2026",
        "description": "Innovation, programmation, design technique",
        "features": ["technical_innovation", "programming_logic", "design_thinking"],
        "note": "Intégration avec outils techniques à développer",
        "data": {
            "5e": {"Technologie": [
                "Design, innovation et créativité",
                "Les objets techniques, les services et les changements",
                "La modélisation et la simulation des objets techniques",
                "L'informatique et la programmation"
            ]},
            "4e": {"Technologie": [
                "Design, innovation et créativité",
                "Les objets techniques, les services et les changements",
                "La modélisation et la simulation des objets techniques",
                "L'informatique et la programmation"
            ]},
            "3e": {"Technologie": [
                "Design, innovation et créativité",
                "Les objets techniques, les services et les changements",
                "La modélisation et la simulation des objets techniques",
                "L'informatique et la programmation"
            ]}
        }
    },

    "Sciences numériques et technologie": {
        "status": "future",
        "expected": "2026",
        "description": "Informatique, numérique, algorithmes",
        "features": ["digital_literacy", "algorithmic_thinking", "data_analysis"],
        "note": "Nécessite intégration outils de programmation",
        "data": {
            "Seconde": {"Sciences numériques et technologie": [
                "Internet",
                "Le Web",
                "Les réseaux sociaux",
                "Les données structurées et leur traitement",
                "Localisation, cartographie et mobilité",
                "Informatique embarquée et objets connectés",
                "La photographie numérique"
            ]}
        }
    }
}

# Fonctions utilitaires pour le système de feature flags
def get_all_subjects_with_status():
    """Retourne toutes les matières avec leur statut et métadonnées"""
    subjects = {}
    for matiere, config in CURRICULUM_DATA_COMPLETE.items():
        chapter_count = 0
        level_count = 0
        
        if config.get("data"):
            level_count = len(config["data"])
            for level_data in config["data"].values():
                for chapters in level_data.values():
                    chapter_count += len(chapters)
        
        subjects[matiere] = {
            "status": config["status"],
            "expected": config.get("expected", "TBD"),
            "description": config.get("description", ""),
            "note": config.get("note", ""),
            "features": config.get("features", []),
            "chapter_count": chapter_count,
            "level_count": level_count,
            "status_info": CURRICULUM_STATUS[config["status"]]
        }
    
    return subjects

def get_active_subjects():
    """Retourne uniquement les matières actives pour la génération"""
    return {name: config["data"] for name, config in CURRICULUM_DATA_COMPLETE.items() 
            if config["status"] == "active"}

def get_subject_by_name(subject_name: str):
    """Retourne les informations complètes d'une matière"""
    return CURRICULUM_DATA_COMPLETE.get(subject_name)

def is_subject_active(subject_name: str):
    """Vérifie si une matière est active"""
    config = CURRICULUM_DATA_COMPLETE.get(subject_name)
    return config and config.get("status") == "active"

def get_subjects_by_status(status: str):
    """Retourne les matières ayant un statut donné"""
    return {name: config for name, config in CURRICULUM_DATA_COMPLETE.items() 
            if config.get("status") == status}

def get_curriculum_stats():
    """Retourne des statistiques globales du curriculum"""
    stats = {}
    total_chapters = 0
    total_levels = 0
    
    for status in CURRICULUM_STATUS.keys():
        subjects = get_subjects_by_status(status)
        subject_count = len(subjects)
        status_chapters = 0
        status_levels = 0
        
        for config in subjects.values():
            if config.get("data"):
                status_levels += len(config["data"])
                for level_data in config["data"].values():
                    for chapters in level_data.values():
                        status_chapters += len(chapters)
        
        stats[status] = {
            "subject_count": subject_count,
            "chapter_count": status_chapters,
            "level_count": status_levels,
            "info": CURRICULUM_STATUS[status]
        }
        
        total_chapters += status_chapters
        total_levels += status_levels
    
    stats["total"] = {
        "subjects": len(CURRICULUM_DATA_COMPLETE),
        "chapters": total_chapters,
        "levels": total_levels
    }
    
    return stats

# Fonction de logging spécialisée pour le feature flag system
def log_feature_flag_access(subject_name: str, status: str, user_type: str = "guest"):
    """Log les accès aux matières selon leur statut"""
    logger.info(
        "🗺️ Feature flag access",
        module_name="curriculum",
        func_name="feature_flag_access", 
        subject=subject_name,
        status=status,
        user_type=user_type,
        status_emoji=CURRICULUM_STATUS.get(status, {}).get("emoji", "❓")
    )

# Backward compatibility avec l'ancien système
def get_available_subjects():
    """Compatibilité : retourne uniquement les noms des matières actives"""
    return list(get_active_subjects().keys())

def get_levels_for_subject(subject):
    """Compatibilité : retourne les niveaux pour une matière active"""
    active_data = get_active_subjects().get(subject, {})
    return list(active_data.keys())

def get_all_chapters_for_level(subject, level):
    """Compatibilité : retourne les chapitres pour un niveau donné"""
    active_data = get_active_subjects().get(subject, {})
    level_data = active_data.get(level, {})
    all_chapters = []
    for theme, chapters in level_data.items():
        all_chapters.extend(chapters)
    return all_chapters

def build_prompt_context(subject, level, chapter):
    """Compatibilité : contexte pour les prompts IA"""
    return {
        "matiere": subject,
        "niveau": level,
        "chapitre": chapter,
        "prompt_intro": f"Tu es un professeur de {subject} pour le niveau {level}, chapitre : {chapter}"
    }

# Garde la fonction de processing mathématique existante
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