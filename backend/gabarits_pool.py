"""
POOL DE GABARITS PRÉGÉNÉRÉS - Le Maître Mot

Collection de gabarits d'énoncés prêts à l'emploi pour chaque chapitre.

OBJECTIF : Éliminer 90%+ des appels IA en réutilisant des gabarits validés.

STRUCTURE :
    - Un gabarit = énoncé avec placeholders {variable}
    - 20+ gabarits par (chapitre, type_exercice, difficulte, style)
    - Sélection aléatoire pour éviter répétitions
    - Interpolation des valeurs au moment de la génération

MAINTENANCE :
    - Ajouter de nouveaux gabarits au fil du temps
    - Valider la qualité pédagogique
    - Tester la variabilité lexicale
"""

from typing import Dict, List
from style_manager import StyleFormulation
import random


class GabaritsPool:
    """
    Pool de gabarits d'énoncés prégénérés.
    
    Organisé par : chapitre → type_exercice → difficulte → style → [gabarits]
    """
    
    def __init__(self):
        """Initialise le pool avec les gabarits prédéfinis."""
        self._pool = self._build_pool()
    
    def get_gabarit(
        self, 
        chapitre: str, 
        type_exercice: str, 
        difficulte: str, 
        style: StyleFormulation
    ) -> str:
        """
        Récupère un gabarit aléatoire depuis le pool.
        
        Args:
            chapitre: Nom du chapitre
            type_exercice: Type d'exercice
            difficulte: Niveau de difficulté
            style: Style de formulation
        
        Returns:
            Un gabarit aléatoire, ou None si aucun n'est disponible
        """
        # Normaliser les clés
        chapitre_key = chapitre.lower().replace(" ", "_")
        type_key = type_exercice.lower()
        diff_key = difficulte.lower()
        style_key = style.value
        
        # Parcourir le pool
        gabarits = (
            self._pool
            .get(chapitre_key, {})
            .get(type_key, {})
            .get(diff_key, {})
            .get(style_key, [])
        )
        
        if not gabarits:
            return None
        
        return random.choice(gabarits)
    
    def has_gabarits(
        self, 
        chapitre: str, 
        type_exercice: str, 
        difficulte: str, 
        style: StyleFormulation
    ) -> bool:
        """Vérifie si des gabarits existent pour cette combinaison."""
        gabarit = self.get_gabarit(chapitre, type_exercice, difficulte, style)
        return gabarit is not None
    
    def _build_pool(self) -> Dict:
        """
        Construit le pool complet de gabarits.
        
        Returns:
            Structure : {chapitre: {type_ex: {diff: {style: [gabarits]}}}}
        """
        return {
            "symetrie_axiale": self._build_symetrie_axiale(),
            "symetrie_centrale": self._build_symetrie_centrale(),
            # 🔮 FUTURE: Ajouter d'autres chapitres
        }
    
    def _build_symetrie_axiale(self) -> Dict:
        """Gabarits pour le chapitre Symétrie axiale."""
        return {
            "trouver_valeur": {
                "facile": {
                    StyleFormulation.CONCIS.value: [
                        "Point {pointA} en {coordA}. Axe {axeType} = {axeValue}. Trouve {pointB}.",
                        "{pointA}{coordA}. Symétrie : {axeType} = {axeValue}. Détermine {pointB}.",
                        "Coordonnées {pointA} : {coordA}. Axe : {axeType} = {axeValue}. Calcule {pointB}.",
                        "{pointA} en {coordA}. {axeType} = {axeValue}. Où est {pointB} ?",
                        "Position : {pointA}{coordA}. Axe : {axeType} = {axeValue}. Trouve son symétrique {pointB}.",
                    ],
                    
                    StyleFormulation.SCOLAIRE.value: [
                        "Soit le point {pointA} de coordonnées {coordA}. Détermine les coordonnées du point {pointB} symétrique de {pointA} par rapport à l'axe {axeType} d'équation {axeType} = {axeValue}.",
                        "Dans un repère orthonormé, on considère le point {pointA}{coordA}. Calcule les coordonnées de son symétrique {pointB} par rapport à l'axe {axeType} = {axeValue}.",
                        "Soit {pointA}{coordA}. On trace l'axe de symétrie {axeType} = {axeValue}. Trouve les coordonnées du point image {pointB}.",
                        "On place le point {pointA} aux coordonnées {coordA}. Détermine les coordonnées de {pointB}, symétrique de {pointA} par rapport à {axeType} = {axeValue}.",
                        "Considère le point {pointA} situé en {coordA}. En utilisant la symétrie axiale d'axe {axeType} = {axeValue}, trouve les coordonnées de {pointB}.",
                    ],
                    
                    StyleFormulation.NARRATIF.value: [
                        "Emma place un point {pointA} aux coordonnées {coordA} sur son cahier. Elle veut dessiner son symétrique {pointB} par rapport à la ligne {axeType} = {axeValue}. Aide-la à trouver où placer {pointB}.",
                        "Lucas a tracé un point {pointA} en {coordA}. Son professeur lui demande de trouver le symétrique {pointB} par rapport à l'axe {axeType} = {axeValue}. Peux-tu l'aider ?",
                        "Dans son exercice, Sarah doit placer {pointA} en {coordA}, puis tracer son symétrique {pointB} par rapport à {axeType} = {axeValue}. Où doit-elle positionner {pointB} ?",
                        "Tom dessine {pointA} aux coordonnées {coordA}. Il souhaite construire son symétrique {pointB} relativement à l'axe {axeType} = {axeValue}. Quelle est la position de {pointB} ?",
                        "Marie a placé le point {pointA} en {coordA}. Elle cherche maintenant les coordonnées de son image {pointB} par la symétrie d'axe {axeType} = {axeValue}. Aide-la dans sa recherche.",
                    ],
                    
                    StyleFormulation.GUIDE.value: [
                        "Observe le point {pointA} placé en {coordA}. Aide-toi du schéma pour repérer l'axe {axeType} = {axeValue}. À ton avis, où se situe le symétrique {pointB} ?",
                        "Repère d'abord {pointA} aux coordonnées {coordA}. Identifie ensuite l'axe {axeType} = {axeValue}. Maintenant, trouve les coordonnées de {pointB}.",
                        "Commence par localiser {pointA} en {coordA}. Utilise la grille pour visualiser l'axe {axeType} = {axeValue}. Déduis-en la position de {pointB}.",
                        "Regarde bien : {pointA} est en {coordA}. L'axe de symétrie est la droite {axeType} = {axeValue}. En t'aidant de ces informations, détermine {pointB}.",
                        "Première étape : situe {pointA}{coordA}. Deuxième étape : identifie l'axe {axeType} = {axeValue}. Troisième étape : trouve {pointB}.",
                    ],
                    
                    StyleFormulation.DEFI.value: [
                        "Défi géométrie ! Le point {pointA} est en {coordA}, l'axe est {axeType} = {axeValue}. Sauras-tu trouver rapidement les coordonnées de {pointB} ?",
                        "Challenge : {pointA}{coordA}, axe {axeType} = {axeValue}. Trouve {pointB} en moins de 2 minutes !",
                        "Mission symétrie ! Point de départ : {pointA}{coordA}. Axe : {axeType} = {axeValue}. Objectif : localiser {pointB}. Prêt ?",
                        "Test de rapidité ! {pointA} est en {coordA}. Axe de symétrie : {axeType} = {axeValue}. À toi de jouer : trouve {pointB} !",
                        "Défi du jour : partir de {pointA}{coordA}, utiliser l'axe {axeType} = {axeValue}, et calculer {pointB}. Go !",
                    ],
                },
                
                "moyen": {
                    StyleFormulation.CONCIS.value: [
                        "{pointA}{coordA}, {pointB}{coordB}. Axe {axeType} = {axeValue}. Vérifie la symétrie.",
                        "Points : {pointA}{coordA}, {pointB}{coordB}. Axe : {axeType} = {axeValue}. Sont-ils symétriques ?",
                        "{pointA}{coordA} et {pointB}{coordB}. {axeType} = {axeValue}. Symétrie respectée ?",
                        "Données : {pointA}{coordA}, {pointB}{coordB}, axe {axeType} = {axeValue}. Valide la symétrie.",
                        "{pointA}{coordA} ↔ {pointB}{coordB} ? Axe : {axeType} = {axeValue}. Confirme.",
                    ],
                    
                    StyleFormulation.SCOLAIRE.value: [
                        "Soient les points {pointA}{coordA} et {pointB}{coordB}. Vérifie si ces deux points sont symétriques par rapport à l'axe {axeType} d'équation {axeType} = {axeValue}.",
                        "On considère {pointA}{coordA} et {pointB}{coordB}. Détermine si {pointB} est le symétrique de {pointA} par rapport à {axeType} = {axeValue}.",
                        "Deux points sont placés : {pointA} en {coordA} et {pointB} en {coordB}. Vérifie s'ils sont symétriques relativement à l'axe {axeType} = {axeValue}.",
                        "Dans un repère, on a {pointA}{coordA} et {pointB}{coordB}. Sont-ils symétriques par rapport à la droite {axeType} = {axeValue} ?",
                        "Les points {pointA} et {pointB} ont respectivement pour coordonnées {coordA} et {coordB}. Vérifie leur symétrie par rapport à {axeType} = {axeValue}.",
                    ],
                },
            },
            
            "completer_structure": {
                "moyen": {
                    StyleFormulation.CONCIS.value: [
                        "Triangle {triangle1}. Axe {axeType} = {axeValue}. Complète par symétrie.",
                        "{triangle1}. Symétrie : {axeType} = {axeValue}. Trace {triangle2}.",
                        "Figure initiale : {triangle1}. Axe : {axeType} = {axeValue}. Construis le symétrique.",
                        "{triangle1}. {axeType} = {axeValue}. Complète la figure symétrique.",
                        "Donnée : {triangle1}. Consigne : symétrie d'axe {axeType} = {axeValue}. Trace l'image.",
                    ],
                    
                    StyleFormulation.SCOLAIRE.value: [
                        "Soit le triangle {triangle1}. Complète la figure en traçant le triangle {triangle2}, image de {triangle1} par la symétrie d'axe {axeType} = {axeValue}.",
                        "On considère le triangle {triangle1}. Construis son symétrique {triangle2} par rapport à l'axe {axeType} = {axeValue}.",
                        "Le triangle {triangle1} est tracé. Détermine et dessine son image {triangle2} par symétrie axiale d'axe {axeType} = {axeValue}.",
                        "Dans un repère, le triangle {triangle1} est donné. Trace le triangle {triangle2}, symétrique de {triangle1} relativement à {axeType} = {axeValue}.",
                        "À partir du triangle {triangle1}, construis par symétrie d'axe {axeType} = {axeValue} le triangle image {triangle2}.",
                    ],
                },
            },
        }
    
    def _build_symetrie_centrale(self) -> Dict:
        """Gabarits pour le chapitre Symétrie centrale."""
        # 🔮 FUTURE: À remplir avec 20+ gabarits pour chaque combinaison
        return {
            "trouver_valeur": {
                "facile": {
                    StyleFormulation.CONCIS.value: [
                        "Point {pointA}{coordA}. Centre {centre}{coordCentre}. Trouve {pointB}.",
                        "{pointA}{coordA}, centre {centre}{coordCentre}. Détermine le symétrique {pointB}.",
                        "Symétrie centrale : {pointA}{coordA} autour de {centre}{coordCentre}. Calcule {pointB}.",
                    ],
                },
            },
        }


# Instance globale
gabarits_pool = GabaritsPool()


# Export des symboles publics
__all__ = [
    "GabaritsPool",
    "gabarits_pool"
]
