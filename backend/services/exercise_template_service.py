"""
Service de génération d'exercices par TEMPLATE
Système MathALÉA-like avec seed déterministe

Architecture :
- Génération 100% reproductible via seed
- Pas d'appel IA (génération pure template)
- Structure standardisée pour pipeline PDF/IA
"""

import random
import logging
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
import os

from backend.models.mathalea_models import ExerciseType
from backend.models.math_models import MathExerciseSpec, GeometricFigure, MathExerciseType

logger = logging.getLogger(__name__)

# Import du service de génération mathématique (SPRINT generators)
from backend.services.math_generation_service import MathGenerationService


class ExerciseTemplateService:
    """
    Service de génération d'exercices par templates
    Reproductible et déterministe via seed
    """
    
    def __init__(self):
        # Connexion MongoDB
        mongo_url = os.environ.get('MONGO_URL')
        if not mongo_url:
            raise ValueError("MONGO_URL environment variable is required")
        
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client.mathalea_db  # Use same DB as catalogue and routes
        self.exercise_types_collection = self.db.exercise_types
    
    async def generate_exercise(
        self,
        exercise_type_id: str,
        nb_questions: int,
        seed: int,
        difficulty: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        use_ai_enonce: bool = False,
        use_ai_correction: bool = False
    ) -> Dict[str, Any]:
        """
        Génère un exercice complet à partir d'un ExerciseType
        
        Args:
            exercise_type_id: ID du type d'exercice
            nb_questions: Nombre de questions à générer
            seed: Graine pour reproductibilité
            difficulty: Niveau de difficulté (optionnel)
            options: Options supplémentaires (optionnel)
            use_ai_enonce: Utiliser l'IA pour l'énoncé (non implémenté ici)
            use_ai_correction: Utiliser l'IA pour la correction (non implémenté ici)
        
        Returns:
            Dict contenant l'exercice généré avec ses questions
        
        Raises:
            ValueError: Si l'ExerciseType n'existe pas ou est invalide
        """
        # 1. Charger l'ExerciseType depuis la DB
        exercise_type_dict = await self.exercise_types_collection.find_one(
            {"id": exercise_type_id},
            {"_id": 0}
        )
        
        if not exercise_type_dict:
            raise ValueError(f"ExerciseType with id {exercise_type_id} not found")
        
        exercise_type = ExerciseType(**exercise_type_dict)
        
        # 2. Valider le nombre de questions
        if nb_questions < exercise_type.min_questions:
            raise ValueError(
                f"nb_questions ({nb_questions}) must be >= min_questions ({exercise_type.min_questions})"
            )
        if nb_questions > exercise_type.max_questions:
            raise ValueError(
                f"nb_questions ({nb_questions}) must be <= max_questions ({exercise_type.max_questions})"
            )
        
        # 3. Valider la difficulté
        if difficulty and difficulty not in exercise_type.difficulty_levels:
            raise ValueError(
                f"difficulty '{difficulty}' not in available levels: {exercise_type.difficulty_levels}"
            )
        
        # Utiliser la difficulté par défaut si non spécifiée
        if not difficulty:
            difficulty = exercise_type.difficulty_levels[0] if exercise_type.difficulty_levels else "moyen"
        
        # 4. Initialiser le générateur aléatoire avec la seed
        rng = random.Random(seed)
        
        # 5. Générer les questions selon le type de générateur
        if exercise_type.generator_kind.value == "legacy":
            # Générateur LEGACY (Sprint F.1)
            questions = await self._generate_legacy_questions(
                exercise_type=exercise_type,
                nb_questions=nb_questions,
                difficulty=difficulty,
                seed=seed,
                rng=rng,
                options=options or {}
            )
        elif exercise_type.generator_kind.value == "template" and hasattr(exercise_type, 'chapter_code') and exercise_type.chapter_code:
            # ✅ FIX: Générateur SPRINT (template avec chapter_code)
            # Utiliser math_generation_service pour les générateurs spécifiques par chapitre
            math_gen_service = MathGenerationService()
            
            # Récupérer le chapitre depuis MongoDB
            chapter = await self.db.chapters.find_one(
                {"code": exercise_type.chapter_code},
                {"_id": 0, "titre": 1}
            )
            
            if chapter:
                chapter_title = chapter["titre"]
                
                # Générer les specs via math_generation_service
                specs = math_gen_service.generate_math_exercise_specs(
                    niveau=exercise_type.niveau,
                    chapitre=chapter_title,
                    difficulte=difficulty,
                    nb_exercices=nb_questions
                )
                
                # Convertir les specs en questions
                questions = []
                for i, spec in enumerate(specs, 1):
                    question = self._convert_math_spec_to_question(spec, i)
                    questions.append(question)
            else:
                # Fallback si chapitre non trouvé
                logger.warning(f"⚠️  Chapitre {exercise_type.chapter_code} non trouvé, utilisation du générateur template standard")
                questions = []
                for i in range(nb_questions):
                    question = self._generate_question(
                        exercise_type=exercise_type,
                        question_number=i + 1,
                        difficulty=difficulty,
                        rng=rng,
                        options=options or {}
                    )
                    questions.append(question)
        else:
            # Générateur TEMPLATE standard (sans chapter_code)
            questions = []
            for i in range(nb_questions):
                question = self._generate_question(
                    exercise_type=exercise_type,
                    question_number=i + 1,
                    difficulty=difficulty,
                    rng=rng,
                    options=options or {}
                )
                questions.append(question)
        
        # 6. Construire la réponse standardisée
        result = {
            "exercise_type_id": exercise_type_id,
            "exercise_type": {
                "code_ref": exercise_type.code_ref,
                "titre": exercise_type.titre,
                "niveau": exercise_type.niveau,
                "domaine": exercise_type.domaine
            },
            "seed": seed,
            "difficulty": difficulty,
            "nb_questions": nb_questions,
            "questions": questions,
            "metadata": {
                "generator_kind": exercise_type.generator_kind.value,
                "supports_seed": exercise_type.supports_seed,
                "competences_ids": exercise_type.competences_ids
            }
        }
        
        logger.info(
            f"✅ Exercice généré: {exercise_type.code_ref}, "
            f"{nb_questions} questions, seed={seed}, difficulty={difficulty}"
        )
        
        return result
    
    def _generate_question(
        self,
        exercise_type: ExerciseType,
        question_number: int,
        difficulty: str,
        rng: random.Random,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Génère une question individuelle
        
        Args:
            exercise_type: Type d'exercice
            question_number: Numéro de la question
            difficulty: Niveau de difficulté
            rng: Générateur aléatoire
            options: Options de génération
        
        Returns:
            Dict contenant la question générée
        """
        # Extraire la configuration aléatoire
        random_config = exercise_type.random_config or {}
        
        # Générer les valeurs selon le type d'exercice
        # Cette logique dépend du contenu de random_config
        data = self._generate_question_data(
            exercise_type=exercise_type,
            difficulty=difficulty,
            random_config=random_config,
            rng=rng,
            options=options
        )
        
        # Générer l'énoncé et la solution
        enonce_brut, solution_brut = self._generate_enonce_and_solution(
            exercise_type=exercise_type,
            data=data,
            difficulty=difficulty
        )
        
        question = {
            "id": f"q{question_number}",
            "enonce_brut": enonce_brut,
            "data": data,
            "solution_brut": solution_brut,
            "metadata": {
                "difficulty": difficulty,
                "competences": exercise_type.competences_ids,
                "question_number": question_number
            }
        }
        
        return question
    
    def _generate_question_data(
        self,
        exercise_type: ExerciseType,
        difficulty: str,
        random_config: Dict[str, Any],
        rng: random.Random,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Génère les données mathématiques de la question
        Selon le type d'exercice et la configuration
        
        Cette fonction est extensible pour supporter différents types d'exercices
        """
        data = {}
        
        # Déterminer les plages de valeurs selon la difficulté
        difficulty_multiplier = {
            "facile": 1.0,
            "moyen": 1.5,
            "difficile": 2.0
        }.get(difficulty, 1.0)
        
        # Extraire les paramètres de random_config
        min_value = random_config.get("min_value", 1)
        max_value = random_config.get("max_value", 10)
        
        # Ajuster selon la difficulté
        adjusted_max = int(max_value * difficulty_multiplier)
        
        # Générer selon le type d'exercice (basé sur question_kinds)
        question_kinds = exercise_type.question_kinds or {}
        
        if question_kinds.get("trouver_valeur"):
            # Type : Trouver une valeur (ex: calcul, géométrie)
            data = self._generate_trouver_valeur_data(
                min_value, adjusted_max, rng, random_config, options
            )
        
        elif question_kinds.get("verifier_propriete"):
            # Type : Vérifier une propriété
            data = self._generate_verifier_propriete_data(
                min_value, adjusted_max, rng, random_config, options
            )
        
        else:
            # Type générique : génération simple
            data = {
                "value_a": rng.randint(min_value, adjusted_max),
                "value_b": rng.randint(min_value, adjusted_max),
                "operation": rng.choice(random_config.get("operations", ["+", "-", "*"]))
            }
        
        return data
    
    def _generate_trouver_valeur_data(
        self,
        min_value: int,
        max_value: int,
        rng: random.Random,
        random_config: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Génère des données pour type 'trouver_valeur'"""
        data = {
            "type": "trouver_valeur",
            "value_a": rng.randint(min_value, max_value),
            "value_b": rng.randint(min_value, max_value)
        }
        
        # Ajouter des paramètres géométriques si spécifié
        if random_config.get("geometry"):
            data["point_a"] = {
                "x": rng.randint(min_value, max_value),
                "y": rng.randint(min_value, max_value)
            }
            data["point_b"] = {
                "x": rng.randint(min_value, max_value),
                "y": rng.randint(min_value, max_value)
            }
        
        return data
    
    def _generate_verifier_propriete_data(
        self,
        min_value: int,
        max_value: int,
        rng: random.Random,
        random_config: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Génère des données pour type 'verifier_propriete'"""
        # Générer une propriété à vérifier (vraie ou fausse)
        is_correct = rng.choice([True, False])
        
        value_a = rng.randint(min_value, max_value)
        
        if is_correct:
            # Générer une valeur qui vérifie la propriété
            value_b = value_a * 2  # Exemple : double
        else:
            # Générer une valeur qui ne vérifie pas la propriété
            value_b = value_a * 2 + rng.randint(1, 3)
        
        data = {
            "type": "verifier_propriete",
            "value_a": value_a,
            "value_b": value_b,
            "expected_answer": is_correct,
            "property_type": random_config.get("property_type", "egalite")
        }
        
        return data
    
    def _generate_enonce_and_solution(
        self,
        exercise_type: ExerciseType,
        data: Dict[str, Any],
        difficulty: str
    ) -> tuple[str, str]:
        """
        Génère l'énoncé et la solution à partir des données
        
        Cette fonction utilise des templates simples
        Pour une vraie implémentation, il faudrait des templates plus sophistiqués
        """
        question_type = data.get("type", "generic")
        
        if question_type == "trouver_valeur":
            enonce = self._generate_enonce_trouver_valeur(data, exercise_type)
            solution = self._generate_solution_trouver_valeur(data, exercise_type)
        
        elif question_type == "verifier_propriete":
            enonce = self._generate_enonce_verifier_propriete(data, exercise_type)
            solution = self._generate_solution_verifier_propriete(data, exercise_type)
        
        else:
            # Template générique
            enonce = (
                f"Question de type {exercise_type.titre}. "
                f"Valeurs : a = {data.get('value_a')}, b = {data.get('value_b')}. "
                f"Opération : {data.get('operation', '+')}."
            )
            
            # Calcul simple
            a = data.get('value_a', 0)
            b = data.get('value_b', 0)
            op = data.get('operation', '+')
            
            if op == '+':
                result = a + b
            elif op == '-':
                result = a - b
            elif op == '*':
                result = a * b
            else:
                result = a
            
            solution = f"Résultat : {result}"
        
        return enonce, solution
    
    def _generate_enonce_trouver_valeur(
        self,
        data: Dict[str, Any],
        exercise_type: ExerciseType
    ) -> str:
        """Génère l'énoncé pour type 'trouver_valeur'"""
        if "point_a" in data and "point_b" in data:
            # Exercice de géométrie
            enonce = (
                f"Soit A({data['point_a']['x']}, {data['point_a']['y']}) "
                f"et B({data['point_b']['x']}, {data['point_b']['y']}). "
                f"Calculer la distance AB."
            )
        else:
            # Exercice numérique
            enonce = (
                f"Calculer : {data['value_a']} + {data['value_b']}"
            )
        
        return enonce
    
    def _generate_solution_trouver_valeur(
        self,
        data: Dict[str, Any],
        exercise_type: ExerciseType
    ) -> str:
        """Génère la solution pour type 'trouver_valeur'"""
        if "point_a" in data and "point_b" in data:
            # Distance euclidienne
            import math
            dx = data['point_b']['x'] - data['point_a']['x']
            dy = data['point_b']['y'] - data['point_a']['y']
            distance = math.sqrt(dx**2 + dy**2)
            
            solution = (
                f"Distance AB = √((x_B - x_A)² + (y_B - y_A)²)\n"
                f"= √(({dx})² + ({dy})²)\n"
                f"= √({dx**2 + dy**2})\n"
                f"≈ {distance:.2f}"
            )
        else:
            # Calcul simple
            result = data['value_a'] + data['value_b']
            solution = f"Résultat : {result}"
        
        return solution
    
    def _generate_enonce_verifier_propriete(
        self,
        data: Dict[str, Any],
        exercise_type: ExerciseType
    ) -> str:
        """Génère l'énoncé pour type 'verifier_propriete'"""
        property_type = data.get("property_type", "egalite")
        
        if property_type == "egalite":
            enonce = (
                f"Vérifier si {data['value_b']} = 2 × {data['value_a']}. "
                f"Répondre par Vrai ou Faux."
            )
        else:
            enonce = (
                f"Vérifier la propriété pour a = {data['value_a']}, b = {data['value_b']}."
            )
        
        return enonce
    
    def _generate_solution_verifier_propriete(
        self,
        data: Dict[str, Any],
        exercise_type: ExerciseType
    ) -> str:
        """Génère la solution pour type 'verifier_propriete'"""
        expected = data.get("expected_answer", False)
        value_a = data['value_a']
        value_b = data['value_b']
        
        solution = (
            f"Calcul : 2 × {value_a} = {2 * value_a}\n"
            f"Comparaison : {value_b} {'=' if expected else '≠'} {2 * value_a}\n"
            f"Réponse : {'Vrai' if expected else 'Faux'}"
        )
        
        return solution

    async def _generate_legacy_questions(
        self,
        exercise_type: ExerciseType,
        nb_questions: int,
        difficulty: str,
        seed: int,
        rng: random.Random,
        options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Génère des questions en utilisant un générateur legacy
        
        Sprint F.1: Intégration des générateurs legacy dans le système MathALÉA
        
        Args:
            exercise_type: ExerciseType avec generator_kind="legacy"
            nb_questions: Nombre de questions à générer
            difficulty: Niveau de difficulté
            seed: Seed pour reproductibilité
            rng: Générateur aléatoire
            options: Options supplémentaires
        
        Returns:
            Liste de questions au format standardisé
        """
        from backend.services.math_generation_service import MathGenerationService
        from backend.models.math_models import MathExerciseType, MathExerciseSpec
        
        logger.info(
            f"🔄 Génération legacy: {exercise_type.legacy_generator_id}, "
            f"{nb_questions} questions, seed={seed}"
        )
        
        if not exercise_type.legacy_generator_id:
            raise ValueError(
                f"ExerciseType {exercise_type.id} has generator_kind=LEGACY "
                f"but no legacy_generator_id"
            )
        
        # Créer le service legacy
        legacy_service = MathGenerationService()
        
        # Mapper le legacy_generator_id vers MathExerciseType
        try:
            legacy_type = MathExerciseType(exercise_type.legacy_generator_id)
        except ValueError:
            raise ValueError(
                f"Invalid legacy_generator_id: {exercise_type.legacy_generator_id}"
            )
        
        # Les générateurs legacy génèrent généralement 1 question à la fois
        # On appelle le générateur nb_questions fois
        questions = []
        
        for i in range(nb_questions):
            try:
                # Utiliser une seed unique par question pour variété
                question_seed = seed + i
                question_rng = random.Random(question_seed)
                
                # NOUVEAU: Essayer d'utiliser le vrai générateur legacy avec figures
                try:
                    # Générer l'exercice avec le service legacy
                    # Note: generate_math_exercise_specs génère plusieurs exercices,
                    # on prend le premier pour cette question
                    # Utilise chapitre_id qui contient le nom précis du chapitre (ex: "Symétrie axiale")
                    # et non le domaine général (ex: "Espace et géométrie")
                    specs = legacy_service.generate_math_exercise_specs(
                        niveau=exercise_type.niveau,
                        chapitre=exercise_type.chapitre_id,
                        difficulte=difficulty,
                        nb_exercices=1
                    )
                    
                    if specs and len(specs) > 0:
                        spec = specs[0]
                        # Convertir MathExerciseSpec → Question avec figure_html
                        question = self._convert_math_spec_to_question(spec, i+1)
                        logger.info(f"✅ Question legacy avec figure générée: {exercise_type.code_ref}")
                    else:
                        raise ValueError("Aucune spec générée par le service legacy")
                    
                except Exception as legacy_error:
                    # Si le générateur legacy échoue, utiliser le fallback
                    logger.warning(
                        f"⚠️  Générateur legacy failed, using fallback for {exercise_type.code_ref}: {legacy_error}"
                    )
                    question = self._generate_legacy_fallback_question(
                        exercise_type=exercise_type,
                        question_number=i+1,
                        seed=question_seed,
                        difficulty=difficulty,
                        rng=question_rng
                    )
                
                questions.append(question)
                
            except Exception as e:
                # Log détaillé côté serveur uniquement
                logger.error(
                    f"Error generating legacy question {i+1} for {exercise_type.code_ref}: {e}",
                    exc_info=True  # Log la stacktrace complète côté serveur
                )
                
                # JAMAIS afficher de stacktrace ou message technique au professeur
                # Fallback propre
                questions.append({
                    "id": f"q{i+1}",
                    "enonce_brut": "Exercice temporairement indisponible (erreur technique)",
                    "data": {},
                    "solution_brut": "Correction temporairement indisponible",
                    "metadata": {
                        "generator": "legacy",
                        "error_occurred": True,  # Indicateur générique sans détail
                        "fallback": True
                    }
                })
        
        logger.info(f"✅ {len(questions)} questions legacy générées")
        return questions
    
    def _generate_legacy_fallback_question(
        self,
        exercise_type: ExerciseType,
        question_number: int,
        seed: int,
        difficulty: str,
        rng: random.Random
    ) -> Dict[str, Any]:
        """
        Génère une question de fallback pour les exercices legacy
        en attendant l'implémentation complète des générateurs legacy
        
        Cette fonction crée des questions mathématiques réalistes
        basées sur le type d'exercice et le niveau
        """
        legacy_type = exercise_type.legacy_generator_id
        niveau = exercise_type.niveau
        
        # Génération selon le type d'exercice legacy
        # Normaliser le legacy_type pour faciliter la détection
        legacy_type_lower = legacy_type.lower() if legacy_type else ""
        
        if "prop" in legacy_type_lower:
            # Proportionnalité
            a = rng.randint(2, 10)
            b = rng.randint(2, 15)
            c = rng.randint(2, 20)
            d = round((b * c) / a, 2)
            
            enonce = f"Dans un tableau de proportionnalité, on sait que {a} correspond à {b}, et {c} correspond à une valeur inconnue. Quelle est cette valeur ?"
            solution = f"On utilise le produit en croix : (valeur inconnue) × {a} = {b} × {c}\n" \
                      f"valeur inconnue = ({b} × {c}) / {a} = {d}"
        
        elif "sym" in legacy_type_lower and "ax" in legacy_type_lower:
            # Symétrie axiale
            points = ["A", "B", "C", "D", "E", "F"]
            point = rng.choice(points)
            x = rng.randint(-10, 10)
            y = rng.randint(-10, 10)
            
            if seed % 2 == 0:
                # Symétrie par rapport à l'axe des ordonnées
                enonce = f"Le point {point}({x} ; {y}) a pour symétrique {point}' par rapport à l'axe des ordonnées. Quelles sont les coordonnées de {point}' ?"
                solution = f"Par symétrie axiale par rapport à l'axe des ordonnées (droite d'équation x = 0), l'abscisse change de signe et l'ordonnée reste identique.\n" \
                          f"Les coordonnées de {point}' sont ({-x} ; {y})."
            else:
                # Symétrie par rapport à l'axe des abscisses
                enonce = f"Le point {point}({x} ; {y}) a pour symétrique {point}' par rapport à l'axe des abscisses. Quelles sont les coordonnées de {point}' ?"
                solution = f"Par symétrie axiale par rapport à l'axe des abscisses (droite d'équation y = 0), l'abscisse reste identique et l'ordonnée change de signe.\n" \
                          f"Les coordonnées de {point}' sont ({x} ; {-y})."
        
        elif "pourc" in legacy_type_lower:
            # Pourcentages
            total = rng.randint(100, 1000)
            percent = rng.choice([10, 15, 20, 25, 30, 40, 50, 75])
            result = round((total * percent) / 100, 2)
            
            enonce = f"Calculer {percent}% de {total}."
            solution = f"Pour calculer {percent}% de {total}, on effectue : ({percent} × {total}) / 100 = {result}"
        
        elif "calc" in legacy_type_lower and "dec" in legacy_type_lower:
            # Calculs avec décimaux
            a = round(rng.uniform(1, 50), 1)
            b = round(rng.uniform(1, 30), 1)
            operation = rng.choice(["+", "-", "×"])
            
            if operation == "+":
                result = round(a + b, 2)
                enonce = f"Calculer : {a} + {b}"
                solution = f"{a} + {b} = {result}"
            elif operation == "-":
                result = round(a - b, 2)
                enonce = f"Calculer : {a} - {b}"
                solution = f"{a} - {b} = {result}"
            else:  # multiplication
                result = round(a * b, 2)
                enonce = f"Calculer : {a} × {b}"
                solution = f"{a} × {b} = {result}"
        
        else:
            # Type inconnu ou générique - fournir une question générique mais professionnelle
            enonce = f"Question d'exercice de géométrie ou de calcul (niveau {niveau})"
            solution = f"La correction de cet exercice est en cours de développement."
        
        return {
            "id": f"q{question_number}",
            "enonce_brut": enonce,
            "data": {
                "seed": seed,
                "difficulty": difficulty
            },
            "solution_brut": solution,
            "metadata": {
                "generator": "legacy_fallback",
                "legacy_type": legacy_type,
                "seed": seed,
                "difficulty": difficulty,
                "note": "Question générée par fallback en attendant implémentation complète"
            }
        }
    
    def _generate_contextual_enonce(self, spec: MathExerciseSpec) -> str:
        """
        Génère un énoncé contextuel basé sur le type d'exercice et les paramètres disponibles
        (Fix pour remplacer les énoncés génériques "Question 1, Question 2...")
        
        Args:
            spec: MathExerciseSpec contenant les données de l'exercice
        
        Returns:
            Énoncé contextuel en français
        """
        params = spec.parametres
        type_ex = spec.type_exercice.value if hasattr(spec.type_exercice, 'value') else str(spec.type_exercice)
        
        # Énoncés contextuels par type d'exercice
        if type_ex == "calcul_decimaux":
            if "expression" in params:
                return f"Calculer : {params['expression']}"
            elif "a" in params and "b" in params and "operation" in params:
                op_text = {"*": "×", "+": "+", "-": "-", "/": "÷"}.get(params["operation"], params["operation"])
                return f"Calculer : {params['a']} {op_text} {params['b']}"
            return "Effectuer le calcul suivant."
        
        elif type_ex == "calcul_fractions":
            if "expression" in params:
                return f"Calculer : {params['expression']}"
            elif "fraction1" in params and "fraction2" in params:
                op = params.get("operation", "+")
                return f"Calculer : {params['fraction1']} {op} {params['fraction2']}"
            return "Effectuer l'opération avec les fractions."
        
        elif type_ex == "calcul_relatifs":
            if "expression" in params:
                return f"Calculer : {params['expression']}"
            return "Effectuer le calcul avec les nombres relatifs."
        
        elif type_ex == "equation_1er_degre":
            if "equation" in params:
                return f"Résoudre l'équation : {params['equation']}"
            return "Résoudre l'équation du premier degré."
        
        elif type_ex == "triangle_rectangle":
            if "triangle" in params:
                triangle = params["triangle"]
                angle_droit = params.get("angle_droit", "")
                return f"Le triangle {triangle} est rectangle en {angle_droit}. Calculer la longueur manquante."
            return "Utiliser le théorème de Pythagore pour trouver la longueur manquante."
        
        elif type_ex == "triangle_quelconque":
            if "triangle" in params:
                return f"Dans le triangle {params['triangle']}, calculer le troisième angle."
            return "Calculer l'angle manquant du triangle."
        
        elif type_ex == "proportionnalite":
            if "coefficient" in params:
                return "Compléter le tableau de proportionnalité suivant."
            return "Résoudre le problème de proportionnalité."
        
        elif type_ex == "perimetre_aire":
            figure = params.get("figure", "figure")
            if figure == "rectangle" and "longueur" in params and "largeur" in params:
                return f"Calculer le périmètre et l'aire d'un rectangle de longueur {params['longueur']} cm et largeur {params['largeur']} cm."
            elif figure == "carre" and "cote" in params:
                return f"Calculer le périmètre et l'aire d'un carré de côté {params['cote']} cm."
            elif figure == "cercle" and "rayon" in params:
                return f"Calculer le périmètre et l'aire d'un cercle de rayon {params['rayon']} cm."
            return f"Calculer le périmètre et l'aire de la figure."
        
        elif type_ex == "rectangle":
            if "longueur" in params and "largeur" in params:
                return f"Un rectangle a pour dimensions {params['longueur']} cm et {params['largeur']} cm. Calculer son périmètre et son aire."
            return "Calculer le périmètre et l'aire du rectangle."
        
        elif type_ex == "volume":
            solide = params.get("solide", "solide")
            if solide == "cube" and "arete" in params:
                return f"Calculer le volume d'un cube d'arête {params['arete']} cm."
            elif solide == "pave" and "longueur" in params:
                return f"Calculer le volume d'un pavé droit de dimensions {params['longueur']} cm × {params['largeur']} cm × {params['hauteur']} cm."
            elif solide == "cylindre" and "rayon" in params:
                return f"Calculer le volume d'un cylindre de rayon {params['rayon']} cm et hauteur {params['hauteur']} cm."
            return "Calculer le volume du solide."
        
        elif type_ex == "statistiques":
            if "valeurs" in params:
                valeurs_str = ", ".join(map(str, params["valeurs"][:5]))
                if len(params["valeurs"]) > 5:
                    valeurs_str += ", ..."
                return f"Série de données : {valeurs_str}. Calculer la moyenne, la médiane et l'étendue."
            return "Calculer les indicateurs statistiques de la série."
        
        elif type_ex == "probabilites":
            contexte = params.get("contexte", "expérience")
            question = params.get("question", "un événement")
            return f"Quelle est la probabilité d'{question} dans l'expérience suivante : {contexte} ?"
        
        elif type_ex == "puissances":
            type_calc = params.get("type", "")
            if type_calc == "calcul_simple" and "base" in params and "exposant" in params:
                return f"Calculer {params['base']}^{{{params['exposant']}}}"
            elif type_calc == "produit" and "base" in params:
                return f"Calculer {params['base']}^{{{params['exposant1']}}} × {params['base']}^{{{params['exposant2']}}}"
            elif type_calc == "quotient" and "base" in params:
                return f"Calculer {params['base']}^{{{params['exposant1']}}} ÷ {params['base']}^{{{params['exposant2']}}}"
            return "Effectuer le calcul avec les puissances."
        
        elif type_ex == "cercle":
            type_calc = params.get("type", "")
            if type_calc == "perimetre" and "rayon" in params:
                return f"Calculer le périmètre d'un cercle de rayon {params['rayon']} cm."
            elif type_calc == "aire" and "rayon" in params:
                return f"Calculer l'aire d'un cercle de rayon {params['rayon']} cm."
            elif type_calc == "rayon_depuis_perimetre" and "perimetre" in params:
                return f"Un cercle a un périmètre de {params['perimetre']} cm. Calculer son rayon."
            return "Calculer les dimensions du cercle."
        
        elif type_ex == "thales":
            if "points" in params and len(params["points"]) >= 5:
                points = params["points"]
                return f"Dans la configuration de Thalès avec le triangle {points[0]}{points[1]}{points[2]}, calculer les longueurs manquantes."
            return "Utiliser le théorème de Thalès pour calculer les longueurs."
        
        elif type_ex == "trigonometrie":
            if "triangle" in params and "angle" in params:
                return f"Dans le triangle rectangle {params['triangle']}, calculer la longueur manquante en utilisant la trigonométrie (angle = {params['angle']}°)."
            return "Utiliser les relations trigonométriques pour calculer la longueur."
        
        elif type_ex == "symetrie_axiale":
            return "Construire le symétrique de la figure par rapport à l'axe."
        
        elif type_ex == "symetrie_centrale":
            return "Construire le symétrique de la figure par symétrie centrale."
        
        # Fallback final avec le chapitre si disponible
        if spec.chapitre:
            return f"Exercice de {spec.chapitre.lower()}."
        
        return "Résoudre l'exercice suivant."
    
    def _convert_math_spec_to_question(
        self,
        spec: MathExerciseSpec,
        question_number: int
    ) -> Dict[str, Any]:
        """
        Convertit un MathExerciseSpec (legacy avec figure_geometrique)
        en question au format standardisé (avec figure_html pour preview/PDF)
        
        Args:
            spec: MathExerciseSpec du générateur legacy
            question_number: Numéro de la question (pour l'ID)
        
        Returns:
            Dict au format question standardisé avec figure_html si présente
        """
        # Construire l'énoncé à partir des paramètres
        enonce_parts = []
        if spec.parametres:
            # Extraire l'énoncé depuis les paramètres (format legacy)
            if "enonce" in spec.parametres:
                enonce_parts.append(spec.parametres["enonce"])
            elif "type" in spec.parametres:
                # Construire un énoncé générique basé sur le type
                type_ex = spec.parametres["type"]
                if type_ex == "trouver_symetrique":
                    point_orig = spec.parametres.get("point_original", "A")
                    coords = spec.parametres.get("point_original_coords", {})
                    axe_desc = spec.parametres.get("axe_description", "l'axe")
                    enonce_parts.append(
                        f"Trouver le symétrique du point {point_orig}({coords.get('x', 0)}, {coords.get('y', 0)}) "
                        f"par rapport à {axe_desc}."
                    )
        
        # ✅ FIX P1: Si aucun énoncé n'est trouvé, générer un énoncé contextuel basé sur le type d'exercice
        enonce = " ".join(enonce_parts) if enonce_parts else self._generate_contextual_enonce(spec)
        
        # Construire la solution
        solution_parts = []
        if spec.etapes_calculees:
            solution_parts.extend(spec.etapes_calculees)
        if spec.resultat_final:
            solution_parts.append(f"Résultat final : {spec.resultat_final}")
        
        solution = "\n".join(solution_parts) if solution_parts else "Solution à compléter"
        
        question = {
            "id": f"q{question_number}",
            "enonce_brut": enonce,
            "data": {},
            "solution_brut": solution,
            "metadata": {
                "generator": "legacy",
                "has_figure": spec.figure_geometrique is not None,
                "type_exercice": spec.type_exercice.value if hasattr(spec.type_exercice, 'value') else str(spec.type_exercice)
            }
        }
        
        # GÉNÉRER LE SVG si figure présente
        if spec.figure_geometrique:
            try:
                # Obtenir le résultat complet du rendu (peut être string ou dict)
                result = self._get_figure_render_result(spec.figure_geometrique)
                
                if result:
                    # Gérer les deux versions (question et correction)
                    if isinstance(result, dict):
                        # Version question (sans solution)
                        question["figure_html"] = result.get("figure_svg_question", result.get("figure_svg", ""))
                        # Version correction (avec solution)
                        question["figure_html_correction"] = result.get("figure_svg_correction", result.get("figure_svg", ""))
                    else:
                        # Format simple (string) - utiliser pour les deux
                        question["figure_html"] = result
                        question["figure_html_correction"] = result
                    
                    question["data"]["figure"] = spec.figure_geometrique.dict()
                    logger.info(f"✅ Figure SVG générée pour question {question_number}")
                else:
                    logger.warning(f"⚠️  Figure SVG vide pour question {question_number}")
            except Exception as e:
                logger.error(f"❌ Erreur génération SVG pour question {question_number}: {e}")
                # Continue sans figure plutôt que de crasher
        
        return question
    
    def _get_figure_render_result(self, figure: GeometricFigure):
        """
        Obtient le résultat complet du rendu (dict ou string)
        Utilisé en interne pour accéder aux versions question et correction
        """
        try:
            from services.geometry_render_service import GeometryRenderService
            service = GeometryRenderService()
            return service.render_figure_to_svg(figure)
        except Exception as e:
            logger.error(f"❌ Erreur lors du rendu SVG: {e}", exc_info=True)
            return None
    
    def _render_figure_to_svg(self, figure: GeometricFigure) -> str:
        """
        Convertit une GeometricFigure en SVG HTML
        
        Args:
            figure: GeometricFigure à convertir
        
        Returns:
            String SVG HTML ou chaîne vide si échec
        """
        try:
            # Utiliser GeometryRenderService pour tous les types de figures
            from services.geometry_render_service import GeometryRenderService
            
            service = GeometryRenderService()
            result = service.render_figure_to_svg(figure)
            
            if result is None:
                logger.warning(f"⚠️  Rendu SVG None pour figure type: {figure.type}")
                return ""
            
            # Gérer les différents types de retour
            if isinstance(result, dict):
                # Pour symétrie axiale/centrale/droite_numerique: retourne un dict
                # ✅ CORRECTION PÉDAGOGIQUE: Utiliser figure_svg_question pour l'énoncé
                # (pas de solution visible dans la question)
                svg = result.get("figure_svg_question", "")
                if not svg:
                    # Fallback sur figure_svg si figure_svg_question n'existe pas (rétrocompatibilité)
                    svg = result.get("figure_svg", "")
                return svg
            elif isinstance(result, str):
                # Pour les autres types de figures: retourne directement le SVG
                return result
            else:
                logger.warning(f"⚠️  Type de retour inattendu: {type(result)}")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du rendu SVG: {e}", exc_info=True)
            return ""


# Instance globale
exercise_template_service = ExerciseTemplateService()

# Export
__all__ = [
    "ExerciseTemplateService",
    "exercise_template_service"
]
