"""
Service de rédaction textuelle pour exercices mathématiques
L'IA ne fait QUE la rédaction, jamais les calculs ou paramètres
"""

import json
import asyncio
import logging
from typing import List, Optional
from math_models import MathExerciseSpec, MathTextGeneration, GeneratedMathExercise
from backend.utils import get_emergent_key
from backend.emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

class MathTextService:
    """Service de rédaction IA pour exercices mathématiques"""
    
    def __init__(self):
        self.emergent_key = get_emergent_key()
    
    async def generate_text_for_specs(
        self, 
        specs: List[MathExerciseSpec]
    ) -> List[GeneratedMathExercise]:
        """Génère le texte IA pour une liste de specs mathématiques"""
        
        exercises = []
        
        for i, spec in enumerate(specs):
            try:
                # Générer le texte IA pour cette spec
                text_generation = await self._generate_text_for_single_spec(spec)
                
                # Créer l'exercice complet
                exercise = GeneratedMathExercise(
                    spec=spec,
                    texte=text_generation
                )
                
                exercises.append(exercise)
                
                logger.info(f"✅ Exercice {i+1}/{len(specs)} - Texte généré avec succès")
                
            except Exception as e:
                logger.error(f"❌ Erreur génération texte exercice {i+1}: {e}")
                
                # Fallback sans IA
                fallback_text = self._generate_fallback_text(spec)
                exercise = GeneratedMathExercise(
                    spec=spec,
                    texte=fallback_text
                )
                exercises.append(exercise)
                
                logger.info(f"🔄 Exercice {i+1}/{len(specs)} - Utilisé fallback textuel")
        
        return exercises
    
    async def _generate_text_for_single_spec(
        self, 
        spec: MathExerciseSpec
    ) -> MathTextGeneration:
        """Génère le texte IA pour une spec mathématique"""
        
        # Construire le prompt structuré
        prompt_data = spec.to_ai_prompt_data()
        
        # Créer le prompt IA spécialisé
        system_message = self._create_system_message()
        user_prompt = self._create_user_prompt(spec, prompt_data)
        
        # Appel IA
        try:
            chat = LlmChat(
                api_key=self.emergent_key,
                session_id=f"math_text_{hash(str(spec.parametres))}",
                system_message=system_message
            ).with_model('openai', 'gpt-4o')
            
            user_message = UserMessage(text=user_prompt)
            response = await asyncio.wait_for(
                chat.send_message(user_message),
                timeout=30.0
            )
            
            # Parser la réponse JSON
            text_generation = self._parse_ai_response(response, spec)
            
            # Valider la réponse
            if self._validate_ai_response(text_generation, spec):
                return text_generation
            else:
                raise ValueError("Réponse IA invalide après validation")
                
        except Exception as e:
            logger.warning(f"Échec génération IA: {e}")
            raise e
    
    def _create_system_message(self) -> str:
        """Message système pour l'IA de rédaction mathématique"""
        return """Tu es un assistant de rédaction pour exercices de mathématiques scolaires.

**RÈGLES ABSOLUES** :
1. Tu ne peux JAMAIS modifier les nombres, points géométriques, ou résultats fournis
2. Tu ne fais QUE la rédaction textuelle claire et pédagogique  
3. Tu utilises EXACTEMENT les paramètres fournis dans le JSON
4. Pour la géométrie, tu utilises UNIQUEMENT les points spécifiés (jamais d'autres lettres)

**INTERDICTIONS** :
❌ Changer un nombre ou calcul
❌ Inventer de nouveaux points géométriques  
❌ Modifier le résultat attendu
❌ Ajouter des données non fournies

**AUTORISATIONS** :
✅ Rédiger un énoncé clair et pédagogique
✅ Adapter le vocabulaire au niveau scolaire
✅ Expliquer la méthode de résolution
✅ Donner des conseils pédagogiques

Tu réponds UNIQUEMENT en JSON avec les champs : "enonce", "explication_prof", "solution_redigee"."""
    
    def _create_user_prompt(self, spec: MathExerciseSpec, prompt_data: dict) -> str:
        """Crée le prompt utilisateur pour une spec donnée"""
        
        prompt = f"""**EXERCICE DE MATHÉMATIQUES À RÉDIGER**

**Métadonnées :**
- Niveau : {spec.niveau}
- Chapitre : {spec.chapitre}  
- Type : {spec.type_exercice}
- Difficulté : {spec.difficulte}

**Paramètres mathématiques (À UTILISER EXACTEMENT) :**
{json.dumps(spec.parametres, indent=2, ensure_ascii=False)}

**Solution calculée (À NE PAS MODIFIER) :**
- Résultat attendu : {spec.resultat_final}
- Étapes de calcul : {spec.etapes_calculees}

"""
        
        # Instructions spécifiques selon le type
        if spec.type_exercice.value.startswith("triangle"):
            prompt += f"""
**GÉOMÉTRIE - CONTRAINTES STRICTES :**
- Points autorisés : {spec.figure_geometrique.points}
- Type de figure : {spec.figure_geometrique.type}
- Angle droit en : {spec.figure_geometrique.rectangle_en}
- Longueurs données : {spec.figure_geometrique.longueurs_connues}
- À calculer : {spec.figure_geometrique.longueurs_a_calculer}

⚠️ INTERDICTION d'utiliser d'autres points que : {spec.figure_geometrique.points}
"""
        
        prompt += """
**CONSIGNES DE RÉDACTION :**
1. **Énoncé** : Rédige un énoncé clair utilisant EXACTEMENT les paramètres fournis
2. **Explication prof** : Brève note pédagogique (optionnel)
3. **Solution rédigée** : Explication en français des étapes calculées

**Format de réponse (JSON uniquement) :**
```json
{
  "enonce": "Énoncé clair pour l'élève utilisant les paramètres exacts",
  "explication_prof": "Conseils pédagogiques (optionnel)",
  "solution_redigee": "Explication des étapes de résolution"
}
```

⚠️ RAPPEL : N'altère AUCUN chiffre, AUCUNE lettre géométrique, AUCUN résultat !
"""
        
        return prompt
    
    def _parse_ai_response(
        self, 
        response: str, 
        spec: MathExerciseSpec
    ) -> MathTextGeneration:
        """Parse la réponse JSON de l'IA"""
        
        try:
            # Nettoyer la réponse
            response_clean = response.strip()
            
            # Extraire le JSON
            if "```json" in response_clean:
                start = response_clean.find("```json") + 7
                end = response_clean.find("```", start)
                json_str = response_clean[start:end].strip()
            elif response_clean.startswith("{"):
                json_str = response_clean
            else:
                # Chercher le premier JSON
                start = response_clean.find("{")
                end = response_clean.rfind("}") + 1
                json_str = response_clean[start:end]
            
            # Parser le JSON
            data = json.loads(json_str)
            
            return MathTextGeneration(
                enonce=data.get("enonce", ""),
                explication_prof=data.get("explication_prof"),
                solution_redigee=data.get("solution_redigee")
            )
            
        except Exception as e:
            logger.error(f"Erreur parsing réponse IA: {e}")
            logger.error(f"Réponse brute: {response[:500]}...")
            raise ValueError(f"Impossible de parser la réponse IA: {e}")
    
    def _validate_ai_response(
        self, 
        text: MathTextGeneration, 
        spec: MathExerciseSpec
    ) -> bool:
        """Valide que la réponse IA respecte les contraintes"""
        
        # Vérifications de base
        if not text.enonce or len(text.enonce.strip()) < 10:
            logger.warning("Énoncé trop court ou vide")
            return False
        
        # Validation géométrie
        if spec.figure_geometrique:
            points_autorises = spec.figure_geometrique.points
            
            # Vérifier qu'aucun point non autorisé n'apparaît
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                if letter not in points_autorises and letter in text.enonce:
                    # Vérifier que c'est vraiment un point géométrique
                    if f" {letter} " in text.enonce or f"triangle {letter}" in text.enonce:
                        logger.warning(f"Point non autorisé détecté: {letter}")
                        return False
            
            # Vérifier que les points autorisés sont utilisés
            points_found = any(point in text.enonce for point in points_autorises)
            if not points_found:
                logger.warning("Aucun point géométrique autorisé trouvé dans l'énoncé")
                return False
        
        return True
    
    def _generate_fallback_text(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Génère un texte de fallback sans IA"""
        
        # Templates d'énoncés selon le type
        templates = {
            "triangle_rectangle": self._fallback_triangle_rectangle,
            "calcul_relatifs": self._fallback_calcul_relatifs,
            "equation_1er_degre": self._fallback_equation,
            "volume": self._fallback_volume,
            "statistiques": self._fallback_statistiques,
            "probabilites": self._fallback_probabilites,
            "puissances": self._fallback_puissances,
            "cercle": self._fallback_cercle,
            "thales": self._fallback_thales,
            "trigonometrie": self._fallback_trigonometrie
        }
        
        template_key = spec.type_exercice.value
        generator = templates.get(template_key, self._fallback_generic)
        
        return generator(spec)
    
    def _fallback_triangle_rectangle(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour triangle rectangle"""
        
        figure = spec.figure_geometrique
        triangle_name = "".join(figure.points)
        
        # Construire l'énoncé
        longueurs_str = []
        for segment, longueur in figure.longueurs_connues.items():
            longueurs_str.append(f"{segment} = {longueur} cm")
        
        enonce = f"""Dans le triangle {triangle_name} rectangle en {figure.rectangle_en}, """ + \
                f"""{" et ".join(longueurs_str)}. """ + \
                f"""Calculer la longueur {figure.longueurs_a_calculer[0]}."""
        
        solution = f"""Le triangle est rectangle, on applique le théorème de Pythagore.
Résultat : {spec.resultat_final}"""
        
        return MathTextGeneration(
            enonce=enonce,
            explication_prof="Exercice d'application du théorème de Pythagore",
            solution_redigee=solution
        )
    
    def _fallback_calcul_relatifs(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour calculs relatifs"""
        
        expression = spec.parametres["expression"]
        
        enonce = f"Calculer : {expression}"
        solution = f"Résultat : {spec.resultat_final}"
        
        return MathTextGeneration(
            enonce=enonce,
            explication_prof="Exercice de calcul avec nombres relatifs",
            solution_redigee=solution
        )
    
    def _fallback_equation(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour équations"""
        
        equation = spec.parametres["equation"]
        
        enonce = f"Résoudre l'équation : {equation}"
        solution = f"Solution : {spec.resultat_final}"
        
        return MathTextGeneration(
            enonce=enonce,
            explication_prof="Équation du premier degré",
            solution_redigee=solution
        )
    
    def _fallback_generic(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback générique"""
        
        enonce = f"Exercice de {spec.chapitre.lower()} - niveau {spec.niveau}"
        
        return MathTextGeneration(
            enonce=enonce,
            explication_prof=f"Exercice de type {spec.type_exercice}",
            solution_redigee=f"Résultat : {spec.resultat_final}"
        )

    
    def _fallback_volume(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour volumes"""
        params = spec.parametres
        solide = params["solide"]
        
        if solide == "cube":
            enonce = f"Calculer le volume d'un cube d'arête {params['arete']} cm."
        elif solide == "pave":
            enonce = f"Calculer le volume d'un pavé droit de dimensions {params['longueur']} cm × {params['largeur']} cm × {params['hauteur']} cm."
        elif solide == "cylindre":
            enonce = f"Calculer le volume d'un cylindre de rayon {params['rayon']} cm et de hauteur {params['hauteur']} cm."
        else:
            enonce = "Calculer le volume du solide donné."
        
        return MathTextGeneration(
            enonce=enonce,
            explication_prof="Exercice de calcul de volume",
            solution_redigee=f"Volume = {spec.resultat_final}"
        )
    
    def _fallback_statistiques(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour statistiques"""
        valeurs = spec.parametres["valeurs"]
        
        enonce = f"Calculer la moyenne, la médiane et l'étendue de la série : {valeurs}"
        
        return MathTextGeneration(
            enonce=enonce,
            explication_prof="Exercice de statistiques descriptives",
            solution_redigee=f"Résultats : {spec.resultat_final}"
        )
    
    def _fallback_probabilites(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour probabilités"""
        params = spec.parametres
        
        enonce = f"Dans l'expérience suivante : {params['contexte']}, calculer la probabilité de {params['question']}."
        
        return MathTextGeneration(
            enonce=enonce,
            explication_prof="Exercice de calcul de probabilité",
            solution_redigee=f"Probabilité = {spec.resultat_final}"
        )
    
    def _fallback_puissances(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour puissances"""
        params = spec.parametres
        type_calcul = params["type"]
        
        if type_calcul == "calcul_simple":
            enonce = f"Calculer {params['base']}^{{{params['exposant']}}}."
        elif type_calcul == "produit":
            enonce = f"Calculer {params['base']}^{{{params['exposant1']}}} × {params['base']}^{{{params['exposant2']}}}."
        else:
            enonce = f"Calculer {params['base']}^{{{params['exposant1']}}} ÷ {params['base']}^{{{params['exposant2']}}}."
        
        return MathTextGeneration(
            enonce=enonce,
            explication_prof="Exercice sur les puissances",
            solution_redigee=f"Résultat = {spec.resultat_final}"
        )

    
    def _fallback_cercle(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour cercles"""
        params = spec.parametres
        type_calcul = params["type"]
        
        if type_calcul == "perimetre":
            enonce = f"Calculer le périmètre d'un cercle de rayon {params['rayon']} cm."
        elif type_calcul == "aire":
            enonce = f"Calculer l'aire d'un cercle de rayon {params['rayon']} cm."
        else:
            enonce = f"Un cercle a un périmètre de {params['perimetre']} cm. Calculer son rayon."
        
        return MathTextGeneration(
            enonce=enonce,
            explication_prof="Exercice sur les cercles",
            solution_redigee=f"Résultat = {spec.resultat_final}"
        )
    
    def _fallback_thales(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour théorème de Thalès"""
        params = spec.parametres
        points = params["points"]
        
        enonce = f"Dans le triangle {points[0]}{points[1]}{points[2]}, ({points[3]}{points[4]}) // ({points[1]}{points[2]}). Appliquer le théorème de Thalès."
        
        return MathTextGeneration(
            enonce=enonce,
            explication_prof="Exercice sur le théorème de Thalès",
            solution_redigee=f"Rapport = {spec.resultat_final}"
        )
    
    def _fallback_trigonometrie(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour trigonométrie"""
        params = spec.parametres
        angle = params["angle"]
        type_calcul = params["type_calcul"]
        
        if type_calcul == "cote_oppose":
            enonce = f"Dans un triangle rectangle, calculer le côté opposé à un angle de {angle}°."
        elif type_calcul == "cote_adjacent":
            enonce = f"Dans un triangle rectangle, calculer le côté adjacent à un angle de {angle}°."
        else:
            enonce = f"Dans un triangle rectangle, calculer l'hypoténuse sachant l'angle de {angle}°."
        
        return MathTextGeneration(
            enonce=enonce,
            explication_prof="Exercice de trigonométrie",
            solution_redigee=f"Résultat = {spec.resultat_final}"
        )

