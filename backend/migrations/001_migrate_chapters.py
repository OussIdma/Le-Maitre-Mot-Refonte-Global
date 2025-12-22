"""
Migration des chapitres MathALÉA vers MongoDB

Cette migration :
1. Importe CHAPITRES_STRUCTURE existant avec des codes legacy
2. Importe tous les chapitres depuis le CSV fourni
3. Crée les index nécessaires
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

# Ajouter le dossier parent au path pour importer les modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.chapter_service import ChapterService
from models.chapter_model import get_domaine_legacy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CSV des chapitres MathALÉA (fourni par l'utilisateur)
CHAPTERS_CSV = """niveau;domaine;code;libelle
6e;Nombres et calculs;6e_N01;Lire et écrire les nombres entiers
6e;Nombres et calculs;6e_N02;Comparer et ranger des nombres entiers
6e;Nombres et calculs;6e_N03;Droite numérique et repérage
6e;Nombres et calculs;6e_N04;Addition et soustraction de nombres entiers
6e;Nombres et calculs;6e_N05;Multiplication de nombres entiers
6e;Nombres et calculs;6e_N06;Division euclidienne
6e;Nombres et calculs;6e_N07;Multiples et diviseurs, critères de divisibilité
6e;Nombres et calculs;6e_N08;Fractions comme partage et quotient
6e;Nombres et calculs;6e_N09;Fractions simples de l'unité
6e;Nombres et calculs;6e_N10;Problèmes à étapes avec les quatre opérations
6e;Géométrie;6e_G01;Points, segments, droites, demi-droites
6e;Géométrie;6e_G02;Alignement, milieu d'un segment
6e;Géométrie;6e_G03;Perpendiculaires et parallèles à la règle et à l'équerre
6e;Géométrie;6e_G04;Triangles (construction et classification)
6e;Géométrie;6e_G05;Quadrilatères usuels (carré, rectangle, losange, parallélogramme)
6e;Géométrie;6e_G06;Cercle et disque (vocabulaire et constructions)
6e;Géométrie;6e_G07;Symétrie axiale (points, segments, figures)
6e;Grandeurs et mesures;6e_GM01;Mesurer et comparer des longueurs
6e;Grandeurs et mesures;6e_GM02;Périmètre de figures usuelles
6e;Grandeurs et mesures;6e_GM03;Aire du rectangle et du carré
6e;Grandeurs et mesures;6e_GM04;Aire du triangle rectangle
6e;Grandeurs et mesures;6e_GM05;Durées et lecture de l'heure
6e;Grandeurs et mesures;6e_GM06;Masses, contenances et conversions simples
6e;Organisation et gestion de données;6e_SP01;Lire et compléter des tableaux de données
6e;Organisation et gestion de données;6e_SP02;Diagrammes en barres et pictogrammes
6e;Organisation et gestion de données;6e_SP03;Proportionnalité simple dans des tableaux
6e;Organisation et gestion de données;6e_SP04;Moyenne arithmétique simple
5e;Nombres et calculs;5e_N01;Nombres décimaux (lecture, écriture, comparaison)
5e;Nombres et calculs;5e_N02;Addition et soustraction de nombres décimaux
5e;Nombres et calculs;5e_N03;Multiplication avec des nombres décimaux
5e;Nombres et calculs;5e_N04;Division décimale (quotients décimaux)
5e;Nombres et calculs;5e_N05;Fractions : fractions décimales et équivalences
5e;Nombres et calculs;5e_N06;Addition et soustraction de fractions (même dénominateur)
5e;Nombres et calculs;5e_N07;Multiplication d'un nombre par une fraction
5e;Nombres et calculs;5e_N08;Nombres relatifs : repérage et comparaison
5e;Nombres et calculs;5e_N09;Addition de nombres relatifs
5e;Nombres et calculs;5e_N10;Soustraction de nombres relatifs
5e;Proportionnalité et pourcentages;5e_PF01;Proportionnalité dans des tableaux et graphiques
5e;Proportionnalité et pourcentages;5e_PF02;Pourcentages simples
5e;Proportionnalité et pourcentages;5e_PF03;Échelles et plans
5e;Proportionnalité et pourcentages;5e_PF04;Vitesses moyennes
5e;Géométrie;5e_G01;Angles : mesure et comparaison
5e;Géométrie;5e_G02;Construction d'angles (rapporteur)
5e;Géométrie;5e_G03;Triangles particuliers (isocèles, rectangles, équilatéraux)
5e;Géométrie;5e_G04;Parallélogrammes (définition et propriétés)
5e;Géométrie;5e_G05;Symétrie centrale (points et figures)
5e;Géométrie;5e_G06;Agrandissement et réduction (homothétie intuitive)
5e;Grandeurs et mesures;5e_GM01;Aire de figures composées simples
5e;Grandeurs et mesures;5e_GM02;Périmètre et aire du cercle (intuition)
5e;Grandeurs et mesures;5e_GM03;Volumes des pavés droits (introductions)
5e;Organisation et gestion de données;5e_SP01;Tableaux et graphiques (barres, lignes)
5e;Organisation et gestion de données;5e_SP02;Fréquences et pourcentages
5e;Organisation et gestion de données;5e_SP03;Moyenne pondérée simple
4e;Nombres et calculs;4e_N01;Nombres relatifs : opérations
4e;Nombres et calculs;4e_N02;Priorités de calcul et parenthèses
4e;Nombres et calculs;4e_N03;Puissances de 10
4e;Nombres et calculs;4e_N04;Notation scientifique
4e;Calcul littéral et équations;4e_CL01;Expressions littérales : simplifier, réduire
4e;Calcul littéral et équations;4e_CL02;Développer une expression (distributivité simple)
4e;Calcul littéral et équations;4e_CL03;Factoriser une expression simple
4e;Calcul littéral et équations;4e_CL04;Équations du premier degré (ax + b = c)
4e;Proportionnalité et fonctions;4e_PF01;Proportionnalité et coefficient de proportionnalité
4e;Proportionnalité et fonctions;4e_PF02;Fonctions linéaires : tableaux et graphiques
4e;Proportionnalité et fonctions;4e_PF03;Pourcentages de hausse et de baisse
4e;Proportionnalité et fonctions;4e_PF04;Vitesses, échelles et grandeurs composées
4e;Géométrie;4e_G01;Triangles : médiatrices et bissectrices
4e;Géométrie;4e_G02;Cercle circonscrit à un triangle
4e;Géométrie;4e_G03;Parallélogrammes et propriétés des diagonales
4e;Géométrie;4e_G04;Symétries et translations
4e;Grandeurs et mesures;4e_GM01;Aire du disque
4e;Grandeurs et mesures;4e_GM02;Volume du pavé droit et du prisme droit
4e;Grandeurs et mesures;4e_GM03;Problèmes de conversions de volumes et capacités
4e;Statistiques et probabilités;4e_SP01;Séries statistiques : effectifs, fréquences
4e;Statistiques et probabilités;4e_SP02;Représentations graphiques (diagrammes, histogrammes simples)
4e;Statistiques et probabilités;4e_SP03;Moyenne, étendue, médiane (intro)
4e;Statistiques et probabilités;4e_SP04;Expériences aléatoires simples et vocabulaire
3e;Nombres et calculs;3e_N01;Révisions sur les nombres relatifs et décimaux
3e;Nombres et calculs;3e_N02;Puissances entières positives et négatives
3e;Nombres et calculs;3e_N03;Notation scientifique et ordres de grandeur
3e;Calcul littéral et équations;3e_CL01;Développer et réduire des expressions
3e;Calcul littéral et équations;3e_CL02;Identités remarquables (a+b)², (a-b)², (a+b)(a-b)
3e;Calcul littéral et équations;3e_CL03;Équations du premier degré et problèmes
3e;Calcul littéral et équations;3e_CL04;Inéquations du premier degré
3e;Fonctions;3e_F01;Fonctions linéaires : coefficient directeur
3e;Fonctions;3e_F02;Fonctions affines : y = ax + b
3e;Fonctions;3e_F03;Lecture graphique et interprétation de variations
3e;Fonctions;3e_F04;Problèmes de proportionnalité via les fonctions
3e;Géométrie;3e_G01;Théorème de Pythagore (direct et réciproque)
3e;Géométrie;3e_G02;Contraposée du théorème de Pythagore
3e;Géométrie;3e_G03;Triangles rectangles et distances
3e;Géométrie;3e_G04;Théorème de Thalès (direct)
3e;Géométrie;3e_G05;Réciproque et contraposée du théorème de Thalès
3e;Géométrie;3e_G06;Sections de solides simples
3e;Géométrie;3e_G07;Trigonométrie dans le triangle rectangle (sin, cos, tan)
3e;Grandeurs et mesures;3e_GM01;Volumes des cylindres
3e;Grandeurs et mesures;3e_GM02;Problèmes de pourcentages successifs et coefficients multiplicateurs
3e;Statistiques et probabilités;3e_SP01;Statistiques à une variable : moyenne, médiane, quartiles
3e;Statistiques et probabilités;3e_SP02;Diagrammes en boîte et interprétation
3e;Statistiques et probabilités;3e_SP03;Probabilités sur un univers fini
3e;Statistiques et probabilités;3e_SP04;Arbres de probabilités simples
3e;Algorithmique et programmation;3e_AP01;Notion d'algorithme et de programme
3e;Algorithmique et programmation;3e_AP02;Boucles et conditions (pseudo-code ou langage choisi)
2nde;Nombres et calculs;2nde_N01;Ensembles de nombres (N, Z, D, Q, R)
2nde;Nombres et calculs;2nde_N02;Intervalles et inégalités
2nde;Nombres et calculs;2nde_N03;Valeur absolue (introduction)
2nde;Nombres et calculs;2nde_N04;Puissances et racines carrées
2nde;Calcul littéral et équations;2nde_CL01;Expressions algébriques complexes
2nde;Calcul littéral et équations;2nde_CL02;Équations du premier degré et systèmes simples
2nde;Calcul littéral et équations;2nde_CL03;Inéquations du premier degré
2nde;Fonctions;2nde_F01;Notion de fonction, image et antécédent
2nde;Fonctions;2nde_F02;Représentations graphiques de fonctions
2nde;Fonctions;2nde_F03;Fonctions affines : variations et résolution graphique
2nde;Fonctions;2nde_F04;Fonction carré et courbe représentative
2nde;Fonctions;2nde_F05;Fonction racine carrée (intuition)
2nde;Géométrie repérée;2nde_G01;Repérage dans le plan, distance
2nde;Géométrie repérée;2nde_G02;Vecteurs : définition et opérations
2nde;Géométrie repérée;2nde_G03;Translation et vecteurs
2nde;Géométrie repérée;2nde_G04;Alignement et parallélisme avec les vecteurs
2nde;Géométrie de l'espace;2nde_GE01;Solides usuels et sections
2nde;Géométrie de l'espace;2nde_GE02;Perspective et représentations
2nde;Statistiques et probabilités;2nde_SP01;Séries statistiques à une variable
2nde;Statistiques et probabilités;2nde_SP02;Centre et dispersion (moyenne, écart interquartile)
2nde;Statistiques et probabilités;2nde_SP03;Probabilités sur un univers fini et événements
2nde;Statistiques et probabilités;2nde_SP04;Diagrammes, nuages de points et corrélation intuitive
2nde;Algorithmique et programmation;2nde_AP01;Algorithmique et variables
2nde;Algorithmique et programmation;2nde_AP02;Boucles, conditions, fonctions simples en programmation
1re;Fonctions et calcul différentiel;1re_FD01;Variations et extremums de fonctions
1re;Fonctions et calcul différentiel;1re_FD02;Nombre dérivé en un point
1re;Fonctions et calcul différentiel;1re_FD03;Fonction dérivée et tableau de variations
1re;Fonctions et calcul différentiel;1re_FD04;Tangente à une courbe
1re;Fonctions;1re_F01;Fonctions polynômes du second degré
1re;Fonctions;1re_F02;Forme canonique et résolution d'inéquations du second degré
1re;Fonctions;1re_F03;Fonctions exponentielles (introduction si programme)
1re;Suites;1re_S01;Suites numériques : définition et exemples
1re;Suites;1re_S02;Suites arithmétiques
1re;Suites;1re_S03;Suites géométriques
1re;Suites;1re_S04;Interprétation graphique de suites simples
1re;Géométrie et vecteurs;1re_GV01;Vecteurs dans le plan : coordonnées
1re;Géométrie et vecteurs;1re_GV02;Droites du plan : équations cartésiennes
1re;Géométrie et vecteurs;1re_GV03;Position relative de deux droites
1re;Produit scalaire;1re_PS01;Produit scalaire dans le plan
1re;Produit scalaire;1re_PS02;Norme d'un vecteur et angle entre deux vecteurs
1re;Statistiques et probabilités;1re_SP01;Probabilités conditionnelles
1re;Statistiques et probabilités;1re_SP02;Formule des probabilités totales
1re;Statistiques et probabilités;1re_SP03;Variables aléatoires discrètes simples
1re;Statistiques et probabilités;1re_SP04;Espérance mathématique
1re;Algorithmique et programmation;1re_AP01;Algorithmes sur les suites
1re;Algorithmique et programmation;1re_AP02;Programmation pour l'étude de fonctions
Tale;Limites et continuité;Tale_LC01;Limite d'une fonction en un point
Tale;Limites et continuité;Tale_LC02;Limites en l'infini
Tale;Limites et continuité;Tale_LC03;Continuité d'une fonction
Tale;Fonctions et dérivation;Tale_FD01;Dérivation de fonctions usuelles
Tale;Fonctions et dérivation;Tale_FD02;Étude complète de fonctions
Tale;Fonctions et dérivation;Tale_FD03;Optimisation et problèmes de maxima/minima
Tale;Fonctions exponentielles et logarithmes;Tale_EL01;Fonction exponentielle
Tale;Fonctions exponentielles et logarithmes;Tale_EL02;Fonction logarithme népérien
Tale;Fonctions exponentielles et logarithmes;Tale_EL03;Équations et inéquations avec exp et ln
Tale;Suites;Tale_S01;Suites monotones et convergence
Tale;Suites;Tale_S02;Suites définies par récurrence
Tale;Suites;Tale_S03;Suites géométriques et intérêts composés
Tale;Géométrie et espace;Tale_GE01;Repérage dans l'espace
Tale;Géométrie et espace;Tale_GE02;Vecteurs de l'espace, droites et plans
Tale;Géométrie et espace;Tale_GE03;Position relative de droites et de plans
Tale;Statistiques et probabilités;Tale_SP01;Lois de probabilité discrètes (dont loi binomiale)
Tale;Statistiques et probabilités;Tale_SP02;Loi normale (si au programme)
Tale;Statistiques et probabilités;Tale_SP03;Espérance, variance et écart-type
Tale;Statistiques et probabilités;Tale_SP04;Intervalle de confiance
Tale;Statistiques et probabilités;Tale_SP05;Tests de comparaison simples
Tale;Algorithmique et programmation;Tale_AP01;Simulation de lois de probabilité
Tale;Algorithmique et programmation;Tale_AP02;Algorithmes d'approximation et recherche de zéros"""


async def migrate_chapters():
    """Migration principale des chapitres"""
    # Connexion à MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client.mathalea_db
    
    # Initialiser le service
    chapter_service = ChapterService(db)
    
    logger.info("🔧 Création des index...")
    await chapter_service.initialize_indexes()
    
    logger.info("📥 Import des chapitres depuis le CSV...")
    
    # Parser le CSV
    lines = CHAPTERS_CSV.strip().split('\n')[1:]  # Ignorer la ligne d'en-tête
    chapters_imported = 0
    
    # Compter l'ordre par niveau/domaine
    ordre_counter = {}
    
    for line in lines:
        parts = line.split(';')
        if len(parts) != 4:
            continue
        
        niveau, domaine, code, libelle = parts
        
        # Générer la clé pour le compteur d'ordre
        key = f"{niveau}_{domaine}"
        if key not in ordre_counter:
            ordre_counter[key] = 0
        ordre_counter[key] += 1
        
        # Construire le document
        chapter_data = {
            "code": code,
            "niveau": niveau,
            "domaine": domaine,
            "domaine_legacy": get_domaine_legacy(domaine),
            "titre": libelle,
            "ordre": ordre_counter[key],
            "legacy_code": None  # Sera ajouté pour les chapitres existants
        }
        
        await chapter_service.upsert_chapter(chapter_data)
        chapters_imported += 1
    
    logger.info(f"✅ {chapters_imported} chapitres importés depuis le CSV")
    
    # Compter le total
    total_chapters = await chapter_service.count_chapters()
    logger.info(f"📊 Total de chapitres dans la base: {total_chapters}")
    
    # Fermer la connexion
    client.close()
    
    logger.info("✅ Migration terminée avec succès!")


if __name__ == "__main__":
    asyncio.run(migrate_chapters())
