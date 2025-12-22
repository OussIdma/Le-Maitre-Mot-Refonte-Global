"""
Générateur RAISONNEMENT_MULTIPLICATIF_V1 - Raisonnement multiplicatif (PREMIUM)
===============================================================================

Version: 1.0.0

Générateur premium pour le raisonnement multiplicatif :
- Proportionnalité (tableaux)
- Pourcentages
- Vitesse
- Échelle

Caractéristiques :
- Variables toujours présentes (aucun placeholder non résolu)
- Solutions "prof" : étapes numérotées + justifications
- Erreurs 422 structurées avec error_code
- Presets pédagogiques pour 6e et 5e
- Déterministe (seed fixe → même résultat)
- Batch-compatible
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from backend.generators.base_generator import (
    BaseGenerator,
    GeneratorMeta,
    ParamSchema,
    Preset,
    ParamType,
)
from backend.generators.factory import GeneratorFactory
from backend.observability import (
    get_request_context,
    safe_random_choice,
    safe_randrange,
)


@GeneratorFactory.register
class RaisonnementMultiplicatifV1Generator(BaseGenerator):
    """Générateur premium d'exercices de raisonnement multiplicatif pour 6e et 5e."""
    
    @classmethod
    def get_meta(cls) -> GeneratorMeta:
        return GeneratorMeta(
            key="RAISONNEMENT_MULTIPLICATIF_V1",
            label="Raisonnement multiplicatif (PREMIUM)",
            description="Exercices de raisonnement multiplicatif : proportionnalité, pourcentages, vitesse, échelle",
            version="1.0.0",
            niveaux=["6e", "5e"],
            exercise_type="RAISONNEMENT_MULTIPLICATIF",
            svg_mode="NONE",
            supports_double_svg=False,
            pedagogical_tips="⚠️ Rappeler : le coefficient de proportionnalité se trouve en divisant une valeur de la 2e ligne par la valeur correspondante de la 1re ligne. Erreur fréquente : confusion entre multiplication et division."
        )
    
    @classmethod
    def get_schema(cls) -> List[ParamSchema]:
        return [
            ParamSchema(
                name="exercise_type",
                type=ParamType.ENUM,
                description="Type d'exercice",
                default="proportionnalite_tableau",
                options=["proportionnalite_tableau", "pourcentage", "vitesse", "echelle"],
                required=False
            ),
            ParamSchema(
                name="difficulty",
                type=ParamType.ENUM,
                description="Niveau de difficulté",
                default="moyen",
                options=["facile", "moyen", "difficile"],
                required=False
            ),
            ParamSchema(
                name="grade",
                type=ParamType.ENUM,
                description="Niveau scolaire",
                default="6e",
                options=["6e", "5e"],
                required=False
            ),
            ParamSchema(
                name="preset",
                type=ParamType.ENUM,
                description="Preset pédagogique",
                default="standard",
                options=["simple", "standard"],
                required=False
            ),
            ParamSchema(
                name="seed",
                type=ParamType.INT,
                description="Seed pour reproductibilité (obligatoire)",
                default=None,
                required=True
            ),
        ]
    
    @classmethod
    def get_presets(cls) -> List[Preset]:
        return [
            # 6e - Proportionnalité
            Preset(
                key="6e_proportionnalite_facile",
                label="6e Facile - Proportionnalité",
                description="Tableaux de proportionnalité simples",
                niveau="6e",
                params={
                    "exercise_type": "proportionnalite_tableau",
                    "difficulty": "facile",
                    "grade": "6e",
                    "preset": "simple",
                    "seed": 42
                }
            ),
            Preset(
                key="6e_proportionnalite_moyen",
                label="6e Moyen - Proportionnalité",
                description="Tableaux de proportionnalité avec coefficients variés",
                niveau="6e",
                params={
                    "exercise_type": "proportionnalite_tableau",
                    "difficulty": "moyen",
                    "grade": "6e",
                    "preset": "standard",
                    "seed": 42
                }
            ),
            # 6e - Pourcentages
            Preset(
                key="6e_pourcentage_facile",
                label="6e Facile - Pourcentages",
                description="Pourcentages simples (10%, 25%, 50%, 75%)",
                niveau="6e",
                params={
                    "exercise_type": "pourcentage",
                    "difficulty": "facile",
                    "grade": "6e",
                    "preset": "simple",
                    "seed": 42
                }
            ),
            # 5e - Proportionnalité
            Preset(
                key="5e_proportionnalite_moyen",
                label="5e Moyen - Proportionnalité",
                description="Tableaux de proportionnalité avec décimaux",
                niveau="5e",
                params={
                    "exercise_type": "proportionnalite_tableau",
                    "difficulty": "moyen",
                    "grade": "5e",
                    "preset": "standard",
                    "seed": 42
                }
            ),
            # 5e - Pourcentages
            Preset(
                key="5e_pourcentage_moyen",
                label="5e Moyen - Pourcentages",
                description="Pourcentages variés avec décimaux",
                niveau="5e",
                params={
                    "exercise_type": "pourcentage",
                    "difficulty": "moyen",
                    "grade": "5e",
                    "preset": "standard",
                    "seed": 42
                }
            ),
            # 5e - Vitesse
            Preset(
                key="5e_vitesse_moyen",
                label="5e Moyen - Vitesse",
                description="Calculs de vitesse moyenne",
                niveau="5e",
                params={
                    "exercise_type": "vitesse",
                    "difficulty": "moyen",
                    "grade": "5e",
                    "preset": "standard",
                    "seed": 42
                }
            ),
            # 5e - Échelle
            Preset(
                key="5e_echelle_moyen",
                label="5e Moyen - Échelle",
                description="Calculs d'échelle et de distances",
                niveau="5e",
                params={
                    "exercise_type": "echelle",
                    "difficulty": "moyen",
                    "grade": "5e",
                    "preset": "standard",
                    "seed": 42
                }
            ),
        ]
    
    def _validate_exercise_type(self, exercise_type: str) -> None:
        """Valide le type d'exercice."""
        valid_types = ["proportionnalite_tableau", "pourcentage", "vitesse", "echelle"]
        if exercise_type not in valid_types:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "INVALID_EXERCISE_TYPE",
                    "error": "invalid_exercise_type",
                    "message": f"Type d'exercice invalide: {exercise_type}",
                    "hint": f"Types valides: {', '.join(valid_types)}",
                    "context": {
                        "exercise_type": exercise_type,
                        "valid_types": valid_types
                    }
                }
            )
    
    def _validate_grade(self, grade: str) -> None:
        """Valide le niveau scolaire."""
        valid_grades = ["6e", "5e"]
        if grade not in valid_grades:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "INVALID_GRADE",
                    "error": "invalid_grade",
                    "message": f"Niveau scolaire invalide: {grade}",
                    "hint": f"Niveaux valides: {', '.join(valid_grades)}",
                    "context": {
                        "grade": grade,
                        "valid_grades": valid_grades
                    }
                }
            )
    
    def _validate_difficulty(self, difficulty: str) -> None:
        """Valide la difficulté."""
        valid_difficulties = ["facile", "moyen", "difficile"]
        if difficulty not in valid_difficulties:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "INVALID_DIFFICULTY",
                    "error": "invalid_difficulty",
                    "message": f"Difficulté invalide: {difficulty}",
                    "hint": f"Difficultés valides: {', '.join(valid_difficulties)}",
                    "context": {
                        "difficulty": difficulty,
                        "valid_difficulties": valid_difficulties
                    }
                }
            )
    
    def _generate_proportionnalite_tableau(self, difficulty: str, grade: str) -> Dict[str, Any]:
        """Génère un exercice de proportionnalité avec tableau."""
        # Générer un coefficient de proportionnalité
        if difficulty == "facile":
            coeff = safe_randrange(self._rng, 2, 6)  # Coefficient entier simple
            valeurs_base = [safe_randrange(self._rng, 1, 10) for _ in range(3)]
        elif difficulty == "moyen":
            coeff = safe_randrange(self._rng, 2, 10)
            if grade == "5e" and self._rng.random() < 0.3:
                coeff = round(self._rng.uniform(1.5, 5), 1)  # Coefficient décimal
            valeurs_base = [safe_randrange(self._rng, 1, 15) for _ in range(4)]
        else:  # difficile
            coeff = safe_randrange(self._rng, 3, 15)
            if grade == "5e":
                coeff = round(self._rng.uniform(2, 10), 1)
            valeurs_base = [safe_randrange(self._rng, 2, 20) for _ in range(5)]
        
        # Calculer les valeurs proportionnelles
        valeurs_proportionnelles = []
        for val in valeurs_base:
            if isinstance(coeff, float):
                result = round(val * coeff, 1)
            else:
                result = val * coeff
            valeurs_proportionnelles.append(result)
        
        # Choisir une valeur à trouver (pas la première)
        index_a_trouver = safe_randrange(self._rng, 1, len(valeurs_base))
        valeur_a_trouver = valeurs_proportionnelles[index_a_trouver]
        
        # Créer une copie pour l'affichage avec "?"
        valeurs_affichage = valeurs_proportionnelles.copy()
        valeurs_affichage[index_a_trouver] = "?"
        
        # Construire le tableau
        tableau = {
            "ligne1": valeurs_base,
            "ligne2": valeurs_proportionnelles
        }
        
        # Trouver un index valide pour calculer le coefficient (pas celui à trouver)
        index_reference = 0 if index_a_trouver != 0 else 1
        
        # Construire l'énoncé
        enonce = f"Complète le tableau de proportionnalité suivant :\n\n"
        enonce += f"Ligne 1 : {', '.join(map(str, valeurs_base))}\n"
        enonce += f"Ligne 2 : {', '.join(map(str, valeurs_affichage))}\n"
        enonce += f"\nQuelle est la valeur manquante ?"
        
        # Solution détaillée
        calculs = f"Étape 1 : On calcule le coefficient de proportionnalité.\n"
        calculs += f"   Coefficient = {valeurs_proportionnelles[index_reference]} ÷ {valeurs_base[index_reference]} = {coeff}\n"
        calculs += f"Étape 2 : On multiplie la valeur de la ligne 1 par le coefficient.\n"
        calculs += f"   Valeur manquante = {valeurs_base[index_a_trouver]} × {coeff} = {valeur_a_trouver}\n"
        
        solution = f"Pour compléter le tableau de proportionnalité, on calcule d'abord le coefficient de proportionnalité en divisant une valeur de la ligne 2 par la valeur correspondante de la ligne 1. Ensuite, on multiplie la valeur de la ligne 1 par ce coefficient pour obtenir la valeur manquante."
        
        donnees = {
            "tableau": tableau,
            "coefficient": coeff,
            "valeur_base": valeurs_base[index_a_trouver],
            "index_manquant": index_a_trouver
        }
        
        return {
            "enonce": enonce,
            "consigne": "Complète le tableau de proportionnalité en calculant la valeur manquante.",
            "solution": solution,
            "calculs_intermediaires": calculs,
            "reponse_finale": str(valeur_a_trouver),
            "donnees": donnees,
            "methode": "coefficient_de_proportionnalite",
            "niveau": grade,
            "type_exercice": "proportionnalite_tableau"
        }
    
    def _generate_pourcentage(self, difficulty: str, grade: str) -> Dict[str, Any]:
        """Génère un exercice sur les pourcentages."""
        # Choisir un type d'exercice
        type_exo = safe_random_choice(self._rng, ["calcul_pourcentage", "trouver_pourcentage", "trouver_valeur"])
        
        if type_exo == "calcul_pourcentage":
            # Calculer X% de Y
            if difficulty == "facile":
                pourcentage = safe_random_choice(self._rng, [10, 25, 50, 75])
                valeur = safe_randrange(self._rng, 20, 100)
            elif difficulty == "moyen":
                pourcentage = safe_randrange(self._rng, 5, 100)
                valeur = safe_randrange(self._rng, 50, 200)
            else:  # difficile
                pourcentage = safe_randrange(self._rng, 1, 200)
                valeur = safe_randrange(self._rng, 100, 500)
            
            resultat = round(valeur * pourcentage / 100, 2)
            if resultat == int(resultat):
                resultat = int(resultat)
            
            enonce = f"Calcule {pourcentage}% de {valeur}."
            calculs = f"Étape 1 : On convertit le pourcentage en fraction.\n"
            calculs += f"   {pourcentage}% = {pourcentage}/100 = {pourcentage/100}\n"
            calculs += f"Étape 2 : On multiplie la valeur par cette fraction.\n"
            calculs += f"   {pourcentage}% de {valeur} = {valeur} × {pourcentage}/100 = {valeur} × {pourcentage/100} = {resultat}\n"
            solution = f"Pour calculer {pourcentage}% de {valeur}, on multiplie {valeur} par {pourcentage}/100, ce qui donne {resultat}."
            reponse_finale = str(resultat)
            
        elif type_exo == "trouver_pourcentage":
            # Quel pourcentage représente X par rapport à Y ?
            if difficulty == "facile":
                partie = safe_randrange(self._rng, 5, 50)
                total = safe_randrange(self._rng, 20, 100)
            elif difficulty == "moyen":
                partie = safe_randrange(self._rng, 10, 100)
                total = safe_randrange(self._rng, 50, 200)
            else:  # difficile
                partie = safe_randrange(self._rng, 20, 200)
                total = safe_randrange(self._rng, 100, 500)
            
            # S'assurer que partie <= total
            if partie > total:
                partie, total = total, partie
            
            pourcentage = round(partie / total * 100, 1)
            if pourcentage > 200:
                pourcentage = 100  # Limiter à 200%
            
            enonce = f"Quel pourcentage représente {partie} par rapport à {total} ?"
            calculs = f"Étape 1 : On calcule le rapport partie/total.\n"
            calculs += f"   Rapport = {partie}/{total} = {partie/total}\n"
            calculs += f"Étape 2 : On multiplie par 100 pour obtenir le pourcentage.\n"
            calculs += f"   Pourcentage = {partie}/{total} × 100 = {pourcentage}%\n"
            solution = f"Pour trouver le pourcentage que représente {partie} par rapport à {total}, on calcule {partie}/{total} × 100 = {pourcentage}%."
            reponse_finale = f"{pourcentage}%"
            
        else:  # trouver_valeur
            # Si X% = Y, quelle est la valeur totale ?
            if difficulty == "facile":
                pourcentage = safe_random_choice(self._rng, [10, 25, 50, 75])
                valeur_partie = safe_randrange(self._rng, 10, 50)
            elif difficulty == "moyen":
                pourcentage = safe_randrange(self._rng, 5, 100)
                valeur_partie = safe_randrange(self._rng, 20, 100)
            else:  # difficile
                pourcentage = safe_randrange(self._rng, 1, 200)
                valeur_partie = safe_randrange(self._rng, 50, 200)
            
            if pourcentage == 0:
                pourcentage = 10  # Éviter division par 0
            
            total = round(valeur_partie / pourcentage * 100, 2)
            if total == int(total):
                total = int(total)
            
            enonce = f"Si {pourcentage}% d'une quantité vaut {valeur_partie}, quelle est cette quantité totale ?"
            calculs = f"Étape 1 : On exprime la relation.\n"
            calculs += f"   {pourcentage}% de la quantité totale = {valeur_partie}\n"
            calculs += f"Étape 2 : On divise par le pourcentage pour trouver le total.\n"
            calculs += f"   Quantité totale = {valeur_partie} ÷ {pourcentage}% = {valeur_partie} ÷ ({pourcentage}/100) = {valeur_partie} × 100/{pourcentage} = {total}\n"
            solution = f"Si {pourcentage}% d'une quantité vaut {valeur_partie}, alors la quantité totale est {valeur_partie} ÷ ({pourcentage}/100) = {total}."
            reponse_finale = str(total)
        
        # Construire donnees selon le type
        if type_exo == "calcul_pourcentage":
            donnees = {
                "type": type_exo,
                "pourcentage": pourcentage,
                "valeur": valeur
            }
        elif type_exo == "trouver_pourcentage":
            donnees = {
                "type": type_exo,
                "partie": partie,
                "total": total
            }
        else:  # trouver_valeur
            donnees = {
                "type": type_exo,
                "pourcentage": pourcentage,
                "valeur_partie": valeur_partie,
                "total": total
            }
        
        return {
            "enonce": enonce,
            "consigne": "Effectue le calcul de pourcentage demandé.",
            "solution": solution,
            "calculs_intermediaires": calculs,
            "reponse_finale": reponse_finale,
            "donnees": donnees,
            "methode": "regle_de_trois_pourcentage",
            "niveau": grade,
            "type_exercice": "pourcentage"
        }
    
    def _generate_vitesse(self, difficulty: str, grade: str) -> Dict[str, Any]:
        """Génère un exercice sur la vitesse."""
        if grade == "6e":
            # 6e : vitesse simple avec entiers
            type_exo = safe_random_choice(self._rng, ["calcul_vitesse", "calcul_distance", "calcul_temps"])
        else:  # 5e
            type_exo = safe_random_choice(self._rng, ["calcul_vitesse", "calcul_distance", "calcul_temps"])
        
        if type_exo == "calcul_vitesse":
            # v = d/t
            if difficulty == "facile":
                distance = safe_randrange(self._rng, 10, 100)  # km
                temps = safe_randrange(self._rng, 1, 5)  # heures
            elif difficulty == "moyen":
                distance = safe_randrange(self._rng, 50, 300)  # km
                temps = safe_randrange(self._rng, 1, 10)  # heures
            else:  # difficile
                distance = safe_randrange(self._rng, 100, 500)  # km
                temps = safe_randrange(self._rng, 2, 12)  # heures
            
            if temps == 0:
                temps = 1  # Éviter division par 0
            
            vitesse = round(distance / temps, 1)
            if vitesse == int(vitesse):
                vitesse = int(vitesse)
            
            enonce = f"Un véhicule parcourt {distance} km en {temps} heures. Quelle est sa vitesse moyenne en km/h ?"
            calculs = f"Étape 1 : On applique la formule vitesse = distance ÷ temps.\n"
            calculs += f"   Vitesse = {distance} km ÷ {temps} h = {vitesse} km/h\n"
            solution = f"La vitesse moyenne se calcule en divisant la distance par le temps : {distance} km ÷ {temps} h = {vitesse} km/h."
            reponse_finale = f"{vitesse} km/h"
            
        elif type_exo == "calcul_distance":
            # d = v × t
            if difficulty == "facile":
                vitesse = safe_randrange(self._rng, 20, 80)  # km/h
                temps = safe_randrange(self._rng, 1, 5)  # heures
            elif difficulty == "moyen":
                vitesse = safe_randrange(self._rng, 30, 120)  # km/h
                temps = safe_randrange(self._rng, 1, 8)  # heures
            else:  # difficile
                vitesse = safe_randrange(self._rng, 50, 150)  # km/h
                temps = safe_randrange(self._rng, 2, 10)  # heures
            
            distance = vitesse * temps
            if distance == int(distance):
                distance = int(distance)
            
            enonce = f"Un véhicule roule à {vitesse} km/h pendant {temps} heures. Quelle distance parcourt-il ?"
            calculs = f"Étape 1 : On applique la formule distance = vitesse × temps.\n"
            calculs += f"   Distance = {vitesse} km/h × {temps} h = {distance} km\n"
            solution = f"La distance parcourue se calcule en multipliant la vitesse par le temps : {vitesse} km/h × {temps} h = {distance} km."
            reponse_finale = f"{distance} km"
            
        else:  # calcul_temps
            # t = d/v
            if difficulty == "facile":
                distance = safe_randrange(self._rng, 20, 100)  # km
                vitesse = safe_randrange(self._rng, 20, 80)  # km/h
            elif difficulty == "moyen":
                distance = safe_randrange(self._rng, 50, 300)  # km
                vitesse = safe_randrange(self._rng, 30, 120)  # km/h
            else:  # difficile
                distance = safe_randrange(self._rng, 100, 500)  # km
                vitesse = safe_randrange(self._rng, 50, 150)  # km/h
            
            if vitesse == 0:
                vitesse = 20  # Éviter division par 0
            
            temps = round(distance / vitesse, 1)
            if temps == int(temps):
                temps = int(temps)
            
            enonce = f"Un véhicule doit parcourir {distance} km à la vitesse de {vitesse} km/h. Combien de temps lui faut-il ?"
            calculs = f"Étape 1 : On applique la formule temps = distance ÷ vitesse.\n"
            calculs += f"   Temps = {distance} km ÷ {vitesse} km/h = {temps} h\n"
            solution = f"Le temps nécessaire se calcule en divisant la distance par la vitesse : {distance} km ÷ {vitesse} km/h = {temps} h."
            reponse_finale = f"{temps} h"
        
        # Construire donnees selon le type
        if type_exo == "calcul_vitesse":
            donnees = {
                "type": type_exo,
                "distance": distance,
                "temps": temps
            }
        elif type_exo == "calcul_distance":
            donnees = {
                "type": type_exo,
                "vitesse": vitesse,
                "temps": temps
            }
        else:  # calcul_temps
            donnees = {
                "type": type_exo,
                "distance": distance,
                "vitesse": vitesse
            }
        
        return {
            "enonce": enonce,
            "consigne": "Calcule en utilisant la formule appropriée (vitesse = distance ÷ temps).",
            "solution": solution,
            "calculs_intermediaires": calculs,
            "reponse_finale": reponse_finale,
            "donnees": donnees,
            "methode": "formule_vitesse",
            "niveau": grade,
            "type_exercice": "vitesse"
        }
    
    def _generate_echelle(self, difficulty: str, grade: str) -> Dict[str, Any]:
        """Génère un exercice sur l'échelle."""
        if grade == "6e":
            # 6e : échelle simple
            type_exo = safe_random_choice(self._rng, ["calcul_distance_reelle", "calcul_distance_carte"])
        else:  # 5e
            type_exo = safe_random_choice(self._rng, ["calcul_distance_reelle", "calcul_distance_carte", "calcul_echelle"])
        
        # Générer une échelle
        if difficulty == "facile":
            echelle_num = safe_random_choice(self._rng, [100, 500, 1000, 2000])
        elif difficulty == "moyen":
            echelle_num = safe_random_choice(self._rng, [250, 500, 1000, 2000, 5000])
        else:  # difficile
            echelle_num = safe_random_choice(self._rng, [100, 250, 500, 1000, 2000, 5000, 10000])
        
        echelle = f"1:{echelle_num}"
        
        if type_exo == "calcul_distance_reelle":
            # Distance réelle = distance carte × échelle
            if difficulty == "facile":
                distance_carte = safe_randrange(self._rng, 1, 10)  # cm
            elif difficulty == "moyen":
                distance_carte = round(self._rng.uniform(0.5, 15), 1)  # cm
            else:  # difficile
                distance_carte = round(self._rng.uniform(1, 20), 1)  # cm
            
            distance_reelle = distance_carte * echelle_num  # en cm
            distance_reelle_km = round(distance_reelle / 100000, 2)  # conversion en km
            
            enonce = f"Sur une carte à l'échelle {echelle}, une distance mesure {distance_carte} cm. Quelle est la distance réelle en km ?"
            calculs = f"Étape 1 : On calcule la distance réelle en cm.\n"
            calculs += f"   Distance réelle = {distance_carte} cm × {echelle_num} = {distance_reelle} cm\n"
            calculs += f"Étape 2 : On convertit en km (1 km = 100 000 cm).\n"
            calculs += f"   Distance réelle = {distance_reelle} cm = {distance_reelle_km} km\n"
            solution = f"Sur une carte à l'échelle {echelle}, {distance_carte} cm représentent {distance_carte} × {echelle_num} = {distance_reelle} cm en réalité, soit {distance_reelle_km} km."
            reponse_finale = f"{distance_reelle_km} km"
            
        elif type_exo == "calcul_distance_carte":
            # Distance carte = distance réelle ÷ échelle
            if difficulty == "facile":
                distance_reelle_km = safe_randrange(self._rng, 1, 50)  # km
            elif difficulty == "moyen":
                distance_reelle_km = round(self._rng.uniform(0.5, 100), 1)  # km
            else:  # difficile
                distance_reelle_km = round(self._rng.uniform(1, 200), 1)  # km
            
            distance_reelle_cm = distance_reelle_km * 100000  # conversion en cm
            distance_carte = round(distance_reelle_cm / echelle_num, 2)  # cm
            
            enonce = f"Sur une carte à l'échelle {echelle}, quelle distance sur la carte représente {distance_reelle_km} km en réalité ?"
            calculs = f"Étape 1 : On convertit la distance réelle en cm.\n"
            calculs += f"   Distance réelle = {distance_reelle_km} km = {distance_reelle_cm} cm\n"
            calculs += f"Étape 2 : On divise par l'échelle pour obtenir la distance sur la carte.\n"
            calculs += f"   Distance sur la carte = {distance_reelle_cm} cm ÷ {echelle_num} = {distance_carte} cm\n"
            solution = f"Sur une carte à l'échelle {echelle}, {distance_reelle_km} km (soit {distance_reelle_cm} cm) sont représentés par {distance_reelle_cm} ÷ {echelle_num} = {distance_carte} cm."
            reponse_finale = f"{distance_carte} cm"
            
        else:  # calcul_echelle (5e uniquement)
            # Échelle = distance réelle ÷ distance carte
            distance_carte = round(self._rng.uniform(1, 10), 1)  # cm
            distance_reelle_km = round(self._rng.uniform(1, 50), 1)  # km
            distance_reelle_cm = distance_reelle_km * 100000
            
            echelle_calculee = round(distance_reelle_cm / distance_carte)
            # Arrondir à une valeur d'échelle standard
            echelles_standards = [100, 250, 500, 1000, 2000, 5000, 10000]
            echelle_approx = min(echelles_standards, key=lambda x: abs(x - echelle_calculee))
            
            enonce = f"Sur une carte, {distance_carte} cm représentent {distance_reelle_km} km en réalité. Quelle est l'échelle de cette carte ?"
            calculs = f"Étape 1 : On convertit la distance réelle en cm.\n"
            calculs += f"   Distance réelle = {distance_reelle_km} km = {distance_reelle_cm} cm\n"
            calculs += f"Étape 2 : On calcule l'échelle.\n"
            calculs += f"   Échelle = {distance_reelle_cm} cm ÷ {distance_carte} cm = {echelle_calculee} ≈ 1:{echelle_approx}\n"
            solution = f"L'échelle de la carte est {distance_reelle_cm} ÷ {distance_carte} ≈ 1:{echelle_approx}."
            reponse_finale = f"1:{echelle_approx}"
        
        # Construire donnees selon le type
        if type_exo == "calcul_distance_reelle":
            donnees = {
                "type": type_exo,
                "echelle": echelle,
                "distance_carte": distance_carte
            }
        elif type_exo == "calcul_distance_carte":
            donnees = {
                "type": type_exo,
                "echelle": echelle,
                "distance_reelle_km": distance_reelle_km
            }
        else:  # calcul_echelle
            donnees = {
                "type": type_exo,
                "distance_carte": distance_carte,
                "distance_reelle_km": distance_reelle_km,
                "echelle_calculee": f"1:{echelle_approx}"
            }
        
        return {
            "enonce": enonce,
            "consigne": "Calcule en utilisant la relation entre distance réelle et distance sur la carte.",
            "solution": solution,
            "calculs_intermediaires": calculs,
            "reponse_finale": reponse_finale,
            "donnees": donnees,
            "methode": "calcul_echelle",
            "niveau": grade,
            "type_exercice": "echelle"
        }
    
    def generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un exercice de raisonnement multiplicatif.
        
        Args:
            params: Paramètres validés
            
        Returns:
            Dict avec variables, geo_data, meta
        """
        # Extraire et valider les paramètres
        exercise_type = params.get("exercise_type", "proportionnalite_tableau")
        difficulty = params.get("difficulty", "moyen")
        grade = params.get("grade", "6e")
        seed = params.get("seed")
        
        # Validation explicite
        if seed is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "GENERATION_FAILED",
                    "error": "seed_required",
                    "message": "Le paramètre 'seed' est obligatoire",
                    "hint": "Fournissez un seed (nombre entier) pour garantir la reproductibilité",
                    "context": {
                        "missing_param": "seed"
                    }
                }
            )
        
        self._validate_exercise_type(exercise_type)
        self._validate_grade(grade)
        self._validate_difficulty(difficulty)
        
        # Générer selon le type
        try:
            if exercise_type == "proportionnalite_tableau":
                variables = self._generate_proportionnalite_tableau(difficulty, grade)
            elif exercise_type == "pourcentage":
                variables = self._generate_pourcentage(difficulty, grade)
            elif exercise_type == "vitesse":
                variables = self._generate_vitesse(difficulty, grade)
            else:  # echelle
                variables = self._generate_echelle(difficulty, grade)
        except HTTPException:
            # Propager les HTTPException telles quelles
            raise
        except Exception as e:
            # Autres erreurs → 422 GENERATION_FAILED
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "GENERATION_FAILED",
                    "error": "generation_failed",
                    "message": f"Erreur lors de la génération de l'exercice: {str(e)}",
                    "hint": "Vérifiez les paramètres fournis et réessayez",
                    "context": {
                        "exercise_type": exercise_type,
                        "difficulty": difficulty,
                        "grade": grade,
                        "exception_type": type(e).__name__
                    }
                }
            )
        
        # S'assurer que TOUTES les variables sont présentes
        required_vars = [
            "enonce", "consigne", "solution", "calculs_intermediaires",
            "reponse_finale", "donnees", "methode", "niveau", "type_exercice"
        ]
        for var in required_vars:
            if var not in variables:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": "GENERATION_FAILED",
                        "error": "missing_variable",
                        "message": f"Variable manquante: {var}",
                        "hint": "Erreur interne du générateur. Contactez l'administrateur.",
                        "context": {
                            "missing_variable": var,
                            "available_variables": list(variables.keys())
                        }
                    }
                )
        
        # Retourner le résultat standard
        return {
            "variables": variables,
            "geo_data": None,  # Pas de géométrie pour ce générateur
            "figure_svg_enonce": None,
            "figure_svg_solution": None,
            "meta": {
                "generator_key": "RAISONNEMENT_MULTIPLICATIF_V1",
                "exercise_type": exercise_type,
                "difficulty": difficulty,
                "grade": grade
            }
        }

