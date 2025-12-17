"""
STYLE MANAGER - Le Maître Mot

Gestion des styles de formulation d'énoncés pour :
    1. Réduire les coûts d'appels IA (variabilité sans IA)
    2. Augmenter la diversité des énoncés
    3. Améliorer l'engagement des élèves

ARCHITECTURE EXTENSIBLE :
    - Support futur du mode thématique premium (ninja, foot, espace, etc.)
    - Cache intégré pour éviter les appels IA redondants
    - Gabarits prégénérés réutilisables
"""

from enum import Enum
from typing import Dict, List, Optional, Any
import random


class StyleFormulation(str, Enum):
    """
    10 styles obligatoires de formulation d'énoncés.
    
    Chaque style impose une structure et un ton différents,
    permettant une forte variabilité sans appel IA supplémentaire.
    """
    
    CONCIS = "concis"
    """
    Style direct, minimaliste, va à l'essentiel.
    
    Exemple :
        "Point M(3, 5). Axe x = 7. Trouve M'."
    """
    
    SCOLAIRE = "scolaire"
    """
    Style académique classique, structure traditionnelle.
    
    Exemple :
        "Soit le point M de coordonnées (3, 5). 
         Détermine les coordonnées du point M' symétrique de M 
         par rapport à l'axe vertical d'équation x = 7."
    """
    
    ACADEMIQUE = "academique"
    """
    Style formel, vocabulaire précis, ton professionnel.
    
    Exemple :
        "Dans un repère orthonormé, considère le point M(3, 5). 
         En appliquant les propriétés de la symétrie axiale, 
         détermine les coordonnées du point image M' 
         relativement à l'axe x = 7."
    """
    
    NARRATIF = "narratif"
    """
    Style contextualisé, mise en situation, storytelling.
    
    Exemple :
        "Emma dessine un point M aux coordonnées (3, 5) sur son cahier. 
         Elle souhaite tracer son symétrique par rapport à la ligne x = 7. 
         Aide-la à trouver où placer le point M'."
    """
    
    GUIDE = "guide"
    """
    Style guidé, indices, orientation de l'élève.
    
    Exemple :
        "Observe le point M placé en (3, 5). 
         Aide-toi du schéma pour repérer l'axe x = 7. 
         À ton avis, où se situera le point M' symétrique ?"
    """
    
    DEFI = "defi"
    """
    Style challenge, motivation, défi intellectuel.
    
    Exemple :
        "Défi géométrie ! Le point M est en (3, 5). 
         Sauras-tu trouver rapidement où se place son symétrique 
         par rapport à l'axe x = 7 ?"
    """
    
    ORAL = "oral"
    """
    Style oral, conversationnel, naturel.
    
    Exemple :
        "Tu vois le point M là, en (3, 5) ? 
         Bon, maintenant on a un axe en x = 7. 
         Trouve-moi le symétrique M', vas-y !"
    """
    
    ETAPES = "etapes"
    """
    Style structuré en étapes, procédural.
    
    Exemple :
        "Étape 1 : Repère le point M(3, 5)
         Étape 2 : Identifie l'axe de symétrie x = 7
         Étape 3 : Calcule les coordonnées de M'"
    """
    
    INDUCTIF = "inductif"
    """
    Style inductif, part du particulier vers le général.
    
    Exemple :
        "Tu as déjà tracé des symétriques. 
         Applique la même méthode : 
         M est en (3, 5), l'axe est en x = 7. 
         Que peux-tu en déduire pour M' ?"
    """
    
    QR = "qr"
    """
    Style Question-Réponse, dialogue pédagogique.
    
    Exemple :
        "Question : Où se trouve M ? 
         Réponse : En (3, 5).
         Question : Où est l'axe ? 
         Réponse : x = 7.
         Question : Où placer M' ?"
    """


class StyleManager:
    """
    Gestionnaire central des styles de formulation.
    
    Responsabilités :
        - Sélectionner un style aléatoire
        - Fournir les directives de style pour l'IA
        - Gérer le cache des gabarits par style
        - Préparer l'architecture pour les thèmes futurs
    """
    
    def __init__(self):
        """Initialise le gestionnaire de styles."""
        self._all_styles = list(StyleFormulation)
        self._style_directives = self._build_style_directives()
    
    def get_random_style(self, exclude: Optional[List[str]] = None) -> StyleFormulation:
        """
        Sélectionne un style aléatoire.
        
        Args:
            exclude: Liste de styles à exclure (éviter répétition)
        
        Returns:
            Un style de formulation aléatoire
        """
        available_styles = [
            s for s in self._all_styles 
            if exclude is None or s.value not in exclude
        ]
        
        if not available_styles:
            available_styles = self._all_styles
        
        return random.choice(available_styles)
    
    def get_style_directive(self, style: StyleFormulation) -> str:
        """
        Retourne les directives à envoyer à l'IA pour un style donné.
        
        Args:
            style: Le style de formulation souhaité
        
        Returns:
            Directives textuelles pour l'IA
        """
        return self._style_directives.get(style, self._style_directives[StyleFormulation.SCOLAIRE])
    
    def _build_style_directives(self) -> Dict[StyleFormulation, str]:
        """
        Construit les directives de style pour l'IA.
        
        Ces directives sont insérées dans le prompt IA pour
        influencer la génération du texte d'énoncé.
        """
        return {
            StyleFormulation.CONCIS: """
Style CONCIS requis :
- Phrases courtes, directes
- Aucun mot superflu
- Structure minimaliste
- Maximum 2 phrases
Exemple : "Point M(3, 5). Axe x = 7. Trouve M'."
""",
            
            StyleFormulation.SCOLAIRE: """
Style SCOLAIRE requis :
- Vocabulaire académique classique
- Structure "Soit... Détermine..."
- Ton formel mais accessible
- 2-3 phrases complètes
Exemple : "Soit le point M(3, 5). Détermine les coordonnées de son symétrique M' par rapport à x = 7."
""",
            
            StyleFormulation.ACADEMIQUE: """
Style ACADÉMIQUE requis :
- Vocabulaire mathématique précis
- Ton professionnel, scientifique
- Références aux propriétés
- 3-4 phrases structurées
Exemple : "Dans un repère orthonormé, considère M(3, 5). En appliquant les propriétés de la symétrie, détermine M'."
""",
            
            StyleFormulation.NARRATIF: """
Style NARRATIF requis :
- Mise en situation contextualisée
- Personnage anonyme (Emma, Lucas, un élève, etc.)
- Storytelling léger
- 3-4 phrases engageantes
Exemple : "Emma dessine M(3, 5). Elle veut tracer son symétrique par rapport à x = 7. Aide-la à trouver M'."
""",
            
            StyleFormulation.GUIDE: """
Style GUIDÉ requis :
- Indices et orientation
- Verbes d'action : "Observe", "Aide-toi", "Repère"
- Ton bienveillant
- 2-3 phrases avec indices
Exemple : "Observe M en (3, 5). Aide-toi du schéma avec l'axe x = 7. Où placer M' ?"
""",
            
            StyleFormulation.DEFI: """
Style DÉFI requis :
- Ton motivant, énergique
- Mots clés : "Défi", "Challenge", "Sauras-tu"
- Courte mise au défi
- 2 phrases dynamiques
Exemple : "Défi ! M est en (3, 5), axe x = 7. Sauras-tu trouver M' rapidement ?"
""",
            
            StyleFormulation.ORAL: """
Style ORAL requis :
- Ton conversationnel, naturel
- Tournures orales : "Tu vois...", "Bon..."
- Phrases simples, familières
- 2-3 phrases parlées
Exemple : "Tu vois M en (3, 5) ? Maintenant, axe en x = 7. Trouve M', vas-y !"
""",
            
            StyleFormulation.ETAPES: """
Style ÉTAPES requis :
- Structure numérotée : "Étape 1:", "Étape 2:"
- Procédure claire, séquentielle
- Chaque étape = 1 action
- 3-4 étapes maximum
Exemple : "Étape 1: Repère M(3, 5). Étape 2: Identifie x = 7. Étape 3: Calcule M'."
""",
            
            StyleFormulation.INDUCTIF: """
Style INDUCTIF requis :
- Part d'une expérience passée
- Tournure : "Tu as déjà...", "Applique la même..."
- Lien avec connaissances antérieures
- 3 phrases progressives
Exemple : "Tu as déjà tracé des symétriques. Applique : M(3, 5), axe x = 7. Que déduis-tu ?"
""",
            
            StyleFormulation.QR: """
Style Q/R requis :
- Dialogue Question-Réponse
- Structure : "Q: ... R: ... Q: ..."
- Progression par questions
- 3-4 échanges courts
Exemple : "Q: Où est M ? R: En (3, 5). Q: L'axe ? R: x = 7. Q: Où M' ?"
"""
        }
    
    def build_cache_key(
        self, 
        chapitre: str, 
        type_exercice: str, 
        difficulte: str, 
        style: StyleFormulation,
        theme: Optional[str] = None  # 🔮 FUTURE: Mode thématique premium
    ) -> str:
        """
        Construit une clé de cache unique pour un gabarit d'énoncé.
        
        Architecture extensible : supporte les thèmes futurs.
        
        Args:
            chapitre: Nom du chapitre
            type_exercice: Type d'exercice (trouver_valeur, etc.)
            difficulte: Niveau de difficulté
            style: Style de formulation
            theme: [FUTURE] Thème narratif (ninja, foot, espace, etc.)
        
        Returns:
            Clé de cache unique
        
        Examples:
            >>> build_cache_key("Symétrie axiale", "trouver_valeur", "moyen", StyleFormulation.NARRATIF)
            "symetrie_axiale__trouver_valeur__moyen__narratif"
            
            >>> build_cache_key("Symétrie axiale", "trouver_valeur", "moyen", StyleFormulation.NARRATIF, "ninja")
            "symetrie_axiale__trouver_valeur__moyen__narratif__theme_ninja"
        """
        # Normaliser les noms
        chapitre_clean = chapitre.lower().replace(" ", "_").replace("é", "e").replace("è", "e")
        type_clean = type_exercice.lower()
        diff_clean = difficulte.lower()
        style_clean = style.value
        
        # Construire la clé de base
        base_key = f"{chapitre_clean}__{type_clean}__{diff_clean}__{style_clean}"
        
        # 🔮 FUTURE: Ajouter le thème si présent
        if theme:
            theme_clean = theme.lower().replace(" ", "_")
            base_key += f"__theme_{theme_clean}"
        
        return base_key
    
    def get_variability_score(self, enonces: List[str]) -> float:
        """
        Calcule un score de variabilité lexicale entre plusieurs énoncés.
        
        Utilisé pour valider que les énoncés générés sont suffisamment différents.
        
        Args:
            enonces: Liste d'énoncés à comparer
        
        Returns:
            Score de 0 à 1 (1 = totalement différents)
        """
        if len(enonces) < 2:
            return 1.0
        
        # Tokeniser et compter les mots uniques
        all_words = set()
        total_words = 0
        
        for enonce in enonces:
            words = enonce.lower().split()
            all_words.update(words)
            total_words += len(words)
        
        # Score = ratio mots uniques / mots totaux
        if total_words == 0:
            return 0.0
        
        variability = len(all_words) / total_words
        return min(variability, 1.0)


# Instance globale
style_manager = StyleManager()


# Export des symboles publics
__all__ = [
    "StyleFormulation",
    "StyleManager",
    "style_manager"
]
