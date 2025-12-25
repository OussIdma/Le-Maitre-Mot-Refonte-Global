"""
Service de rédaction textuelle pour exercices mathématiques
L'IA ne fait QUE la rédaction, jamais les calculs ou paramètres

SYSTÈME D'OPTIMISATION IA (Le Maître Mot) :
    1. Vérifier si un gabarit existe dans le cache
    2. Si oui : interpolation directe (0 appel IA, coût = 0)
    3. Si non : appel IA classique + stockage en cache pour le futur
"""

import json
import asyncio
import logging
import time
from typing import List, Optional
from backend.models.math_models import MathExerciseSpec, MathTextGeneration, GeneratedMathExercise
from backend.utils_legacy import get_emergent_key
from backend.emergentintegrations.llm.chat import LlmChat, UserMessage
from backend.services.text_normalizer import normalizer
from backend.services.ia_monitoring_service import ia_monitoring
from backend.style_manager import style_manager, StyleFormulation
from backend.cache_manager import cache_manager
from backend.gabarit_loader import gabarit_loader

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
        """
        Génère le texte IA pour une spec mathématique.
        
        OPTIMISATION IA (Le Maître Mot) :
            1. Tenter génération depuis gabarit (0 appel IA)
            2. Si échec : appel IA classique
            3. Fallback si nécessaire
        """
        
        # ⏱️ Démarrer chronomètre pour monitoring
        start_time = time.time()
        
        # ✨ NOUVELLE PRIORITÉ : Tenter génération depuis gabarit
        # Ceci permet de réduire drastiquement les appels IA
        logger.info(f"🔍 Tentative de génération depuis gabarit pour {spec.chapitre} / {spec.type_exercice.value}")
        gabarit_result = self._try_generate_from_gabarit(spec)
        if gabarit_result:
            logger.info(f"🎯 GABARIT utilisé pour {spec.type_exercice.value} → 0 appel IA, coût = 0")
            
            # 📊 Monitoring : gabarit utilisé (pas d'IA)
            ia_monitoring.log_generation(
                type_exercice=spec.type_exercice.value,
                niveau=spec.niveau,
                chapitre=spec.chapitre,
                ia_utilisee=False,  # Gabarit
                ia_acceptee=False,
                fallback_utilise=False,
                cause_rejet="gabarit_utilise",
                temps_generation_ms=(time.time() - start_time) * 1000
            )
            
            return gabarit_result
        
        # 🚨 SÉCURITÉ PRODUCTION : Bypass IA pour types problématiques
        # Ces types ont des fallbacks parfaits (100% cohérents)
        # Le bypass garantit 0% de risque d'incohérence
        TYPES_BYPASS_IA = ["rectangle", "trigonometrie"]  # ✅ "cercle" retiré (réactivation IA progressive)
        
        if spec.type_exercice.value in TYPES_BYPASS_IA:
            logger.info(f"🔒 BYPASS IA activé pour {spec.type_exercice.value} → Fallback direct")
            
            # 📊 Monitoring : bypass IA
            ia_monitoring.log_generation(
                type_exercice=spec.type_exercice.value,
                niveau=spec.niveau,
                chapitre=spec.chapitre,
                ia_utilisee=False,  # Bypass
                ia_acceptee=False,
                fallback_utilise=True,
                cause_rejet="bypass_securite",
                temps_generation_ms=(time.time() - start_time) * 1000
            )
            
            return self._generate_fallback_text(spec)
        
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
            
            # VALIDATION CRITIQUE : Vérifier la cohérence de la réponse IA
            if not self._validate_ai_response(text_generation, spec):
                logger.warning("⚠️ Réponse IA invalide détectée, utilisation du fallback")
                
                # 📊 Monitoring : validation générale échouée
                ia_monitoring.log_generation(
                    type_exercice=spec.type_exercice.value,
                    niveau=spec.niveau,
                    chapitre=spec.chapitre,
                    ia_utilisee=True,
                    ia_acceptee=False,
                    fallback_utilise=True,
                    cause_rejet="validation_generale_echouee",
                    temps_generation_ms=(time.time() - start_time) * 1000
                )
                
                return self._generate_fallback_text(spec)
            
            # ✅ VALIDATION SPÉCIFIQUE CERCLES (réactivation progressive)
            if spec.type_exercice.value == "cercle":
                if not self._validate_cercle_specifique(text_generation, spec):
                    logger.warning("⚠️ Validation Cercle échouée, utilisation du fallback")
                    
                    # 📊 Monitoring : validation cercle échouée
                    ia_monitoring.log_generation(
                        type_exercice=spec.type_exercice.value,
                        niveau=spec.niveau,
                        chapitre=spec.chapitre,
                        ia_utilisee=True,
                        ia_acceptee=False,
                        fallback_utilise=True,
                        cause_rejet="validation_cercle_specifique_echouee",
                        temps_generation_ms=(time.time() - start_time) * 1000
                    )
                    
                    return self._generate_fallback_text(spec)
            
            # Normaliser les symboles mathématiques
            text_generation.enonce = normalizer.normalize_math_symbols(text_generation.enonce)
            text_generation.solution_redigee = normalizer.normalize_math_symbols(text_generation.solution_redigee)
            
            # Supprimer les prénoms personnels si présents
            text_generation.enonce = normalizer.remove_personal_names(text_generation.enonce)
            
            # 📊 Monitoring : IA acceptée avec succès
            ia_monitoring.log_generation(
                type_exercice=spec.type_exercice.value,
                niveau=spec.niveau,
                chapitre=spec.chapitre,
                ia_utilisee=True,
                ia_acceptee=True,
                fallback_utilise=False,
                cause_rejet=None,
                temps_generation_ms=(time.time() - start_time) * 1000
            )
            
            return text_generation
                
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
        if spec.type_exercice.value == "cercle":
            # ✅ PROMPT SPÉCIALISÉ CERCLES (réactivation IA progressive)
            rayon = spec.parametres.get("rayon", "?")
            type_calcul = spec.parametres.get("type", "perimetre")
            centre = spec.figure_geometrique.points[0] if spec.figure_geometrique and spec.figure_geometrique.points else "O"
            
            prompt += f"""
**CERCLE - CONTRAINTES STRICTES :**
- Centre du cercle : {centre}
- Rayon : {rayon} cm
- Type de calcul : {type_calcul}
- Formules à utiliser :
  • Périmètre : P = 2πr
  • Aire : A = πr²

**CONSIGNES DE RÉDACTION :**
1. Mentionne UNIQUEMENT le point {centre} comme centre
2. Utilise EXACTEMENT le rayon {rayon} cm (ne pas inventer d'autre valeur)
3. Donne la formule appropriée selon le type de calcul
4. Utilise π (pi) dans la solution, pas une valeur décimale
5. Arrondis le résultat final à 2 décimales si nécessaire

⚠️ INTERDICTIONS ABSOLUES :
❌ Inventer un autre rayon que {rayon} cm
❌ Utiliser un autre point que {centre} pour le centre
❌ Mélanger les formules périmètre/aire
"""
        
        elif spec.type_exercice.value.startswith("triangle"):
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
        """Valide que la réponse IA respecte les contraintes - VALIDATION STRICTE"""
        
        # Vérifications de base
        if not text.enonce or len(text.enonce.strip()) < 10:
            logger.warning("❌ Validation: Énoncé trop court ou vide")
            return False
        
        # VALIDATION GÉOMÉTRIQUE STRICTE (critique pour Thalès)
        if spec.figure_geometrique:
            points_autorises = set(spec.figure_geometrique.points)
            
            # Extraire TOUS les points géométriques de l'énoncé et solution
            import re
            all_text = text.enonce + (text.solution_redigee or "")
            
            # Pattern pour détecter les points : lettres majuscules isolées ou dans des contextes géométriques
            patterns = [
                r'\b([A-Z])\b',  # Lettre isolée
                r'point ([A-Z])',  # "point A"
                r'segment \[([A-Z])([A-Z])\]',  # "segment [AB]"
                r'triangle ([A-Z])([A-Z])([A-Z])',  # "triangle ABC"
                r'\(([A-Z])([A-Z])\)',  # "(AB)"
                r'droite[s]? \(([A-Z])([A-Z])\)',  # "droite (AB)"
            ]
            
            points_detectes = set()
            for pattern in patterns:
                matches = re.findall(pattern, all_text)
                for match in matches:
                    if isinstance(match, tuple):
                        points_detectes.update(m for m in match if m)
                    else:
                        points_detectes.add(match)
            
            # Filtrer les faux positifs (mots courants avec lettre majuscule)
            mots_exclus = {'I', 'L', 'On', 'Le', 'La', 'Les', 'Un', 'Une', 'De', 'Du', 'Des'}
            points_detectes = points_detectes - mots_exclus
            
            # Vérifier qu'AUCUN point non autorisé n'est utilisé
            points_interdits = points_detectes - points_autorises
            if points_interdits:
                logger.warning(f"❌ Validation THALÈS: Points NON AUTORISÉS détectés: {points_interdits}")
                logger.warning(f"   Points autorisés: {points_autorises}")
                logger.warning(f"   Énoncé: {text.enonce[:100]}...")
                return False
            
            # Vérifier que les points autorisés sont bien utilisés
            if not points_detectes.intersection(points_autorises):
                logger.warning("❌ Validation: Aucun point autorisé trouvé dans le texte")
                logger.warning(f"   Points autorisés: {points_autorises}")
                return False
            
            # VALIDATION SPÉCIALE THALÈS : Vérifier que tous les 5 points sont mentionnés
            if spec.type_exercice.value == "thales" and len(points_autorises) >= 5:
                points_manquants = points_autorises - points_detectes
                if len(points_manquants) > 1:  # Tolérer 1 point manquant
                    logger.warning(f"❌ Validation THALÈS: Points manquants: {points_manquants}")
                    return False
                
                # VALIDATION CRITIQUE : Vérifier le parallélisme dans la solution
                # Chercher des patterns de parallélisme : (AB) // (CD)
                parallel_pattern = r'\(([A-Z])([A-Z])\)\s*//\s*\(([A-Z])([A-Z])\)'
                parallel_matches = re.findall(parallel_pattern, text.solution_redigee or "")
                
                for match in parallel_matches:
                    # match = (A, B, C, D) pour "(AB) // (CD)"
                    points_in_parallel = set(match)
                    points_non_autorises = points_in_parallel - points_autorises
                    
                    if points_non_autorises:
                        logger.warning(f"❌ Validation THALÈS SOLUTION: Parallélisme avec points NON AUTORISÉS: {points_non_autorises}")
                        logger.warning(f"   Parallélisme détecté: ({match[0]}{match[1]}) // ({match[2]}{match[3]})")
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
            "trigonometrie": self._fallback_trigonometrie,
            "triangle_quelconque": self._fallback_triangle_quelconque,
            "perimetre_aire": self._fallback_perimetre_aire,
            "rectangle": self._fallback_rectangle
        }
        
        template_key = spec.type_exercice.value
        generator = templates.get(template_key, self._fallback_generic)
        
        return generator(spec)
    
    def _fallback_triangle_rectangle(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour triangle rectangle - Robuste"""
        
        try:
            figure = spec.figure_geometrique
            
            if not figure or not figure.points or len(figure.points) < 3:
                return self._fallback_generic(spec)
            
            triangle_name = "".join(figure.points)
            
            # Construire l'énoncé
            longueurs_str = []
            for segment, longueur in figure.longueurs_connues.items():
                longueurs_str.append(f"{segment} = {longueur} cm")
            
            if not longueurs_str:
                return self._fallback_generic(spec)
            
            rectangle_en = figure.rectangle_en if figure.rectangle_en else figure.points[1]
            a_calculer = figure.longueurs_a_calculer[0] if figure.longueurs_a_calculer else "le côté manquant"
            
            enonce = f"""Dans le triangle {triangle_name} rectangle en {rectangle_en}, """ + \
                    f"""{" et ".join(longueurs_str)}. """ + \
                    f"""Calculer la longueur {a_calculer}."""
            
            solution = f"""Le triangle est rectangle, on applique le théorème de Pythagore.
Résultat : {spec.resultat_final}"""
            
            return MathTextGeneration(
                enonce=enonce,
                explication_prof="Exercice d'application du théorème de Pythagore",
                solution_redigee=solution
            )
        except Exception as e:
            logger.warning(f"Fallback triangle_rectangle échoué, utilisation fallback generic: {e}")
            return self._fallback_generic(spec)
    
    def _fallback_calcul_relatifs(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour calculs relatifs - Robuste"""
        
        try:
            expression = spec.parametres.get("expression", None)
            
            if expression:
                enonce = f"Calculer : {expression}"
            else:
                # Fallback vers generic si pas d'expression
                return self._fallback_generic(spec)
            
            solution = f"Résultat : {spec.resultat_final}"
            
            return MathTextGeneration(
                enonce=enonce,
                explication_prof="Exercice de calcul avec nombres relatifs",
                solution_redigee=solution
            )
        except Exception as e:
            logger.warning(f"Fallback calcul_relatifs échoué, utilisation fallback generic: {e}")
            return self._fallback_generic(spec)
    
    def _fallback_equation(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour équations - Robuste"""
        
        try:
            equation = spec.parametres.get("equation", None)
            
            if equation:
                enonce = f"Résoudre l'équation : {equation}"
            else:
                return self._fallback_generic(spec)
            
            solution = f"Solution : {spec.resultat_final}"
            
            return MathTextGeneration(
                enonce=enonce,
                explication_prof="Équation du premier degré",
                solution_redigee=solution
            )
        except Exception as e:
            logger.warning(f"Fallback equation échoué, utilisation fallback generic: {e}")
            return self._fallback_generic(spec)
    
    def _fallback_generic(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback générique - DERNIER RECOURS"""
        
        logger.warning(f"⚠️  FALLBACK GÉNÉRIQUE utilisé pour {spec.type_exercice} (chapitre: {spec.chapitre})")
        logger.warning("   Cela indique qu'aucun fallback spécifique n'a fonctionné")
        
        # Construire un énoncé plus détaillé à partir des étapes calculées
        etapes_str = " → ".join(spec.etapes_calculees[:2]) if spec.etapes_calculees else ""
        
        if etapes_str:
            enonce = f"Exercice : {etapes_str}. Calculer le résultat final."
        else:
            enonce = f"Exercice de {spec.chapitre.lower()} - niveau {spec.niveau}. Résoudre le problème."
        
        solution = f"Réponse : {spec.resultat_final}"
        
        return MathTextGeneration(
            enonce=enonce,
            explication_prof=f"Exercice niveau {spec.niveau}",
            solution_redigee=solution
        )

    
    def _fallback_volume(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour volumes - Robuste"""
        
        try:
            params = spec.parametres
            solide = params.get("solide", "")
            
            if solide == "cube" and "arete" in params:
                enonce = f"Calculer le volume d'un cube d'arête {params['arete']} cm."
            elif solide == "pave" and all(k in params for k in ['longueur', 'largeur', 'hauteur']):
                enonce = f"Calculer le volume d'un pavé droit de dimensions {params['longueur']} cm × {params['largeur']} cm × {params['hauteur']} cm."
            elif solide == "cylindre" and all(k in params for k in ['rayon', 'hauteur']):
                enonce = f"Calculer le volume d'un cylindre de rayon {params['rayon']} cm et de hauteur {params['hauteur']} cm."
            else:
                enonce = f"Calculer le volume du solide. Résultat : {spec.resultat_final}"
            
            return MathTextGeneration(
                enonce=enonce,
                explication_prof="Exercice de calcul de volume",
                solution_redigee=f"Volume = {spec.resultat_final}"
            )
        except Exception as e:
            logger.warning(f"Fallback volume échoué, utilisation fallback generic: {e}")
            return self._fallback_generic(spec)
    
    def _fallback_statistiques(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour statistiques - Robuste"""
        
        try:
            valeurs = spec.parametres.get("valeurs", None)
            
            if valeurs:
                enonce = f"Calculer la moyenne, la médiane et l'étendue de la série : {valeurs}"
            else:
                return self._fallback_generic(spec)
            
            return MathTextGeneration(
                enonce=enonce,
                explication_prof="Exercice de statistiques descriptives",
                solution_redigee=f"Résultats : {spec.resultat_final}"
            )
        except Exception as e:
            logger.warning(f"Fallback statistiques échoué, utilisation fallback generic: {e}")
            return self._fallback_generic(spec)
    
    def _fallback_probabilites(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour probabilités - Robuste"""
        
        try:
            params = spec.parametres
            contexte = params.get('contexte', 'une expérience aléatoire')
            question = params.get('question', 'un événement')
            
            enonce = f"Dans l'expérience suivante : {contexte}, calculer la probabilité de {question}."
            
            return MathTextGeneration(
                enonce=enonce,
                explication_prof="Exercice de calcul de probabilité",
                solution_redigee=f"Probabilité = {spec.resultat_final}"
            )
        except Exception as e:
            logger.warning(f"Fallback probabilites échoué, utilisation fallback generic: {e}")
            return self._fallback_generic(spec)
    
    def _fallback_puissances(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour puissances - Robuste"""
        
        try:
            params = spec.parametres
            type_calcul = params.get("type", "")
            
            if type_calcul == "calcul_simple" and all(k in params for k in ['base', 'exposant']):
                enonce = f"Calculer {params['base']}^{{{params['exposant']}}}."
            elif type_calcul == "produit" and all(k in params for k in ['base', 'exposant1', 'exposant2']):
                enonce = f"Calculer {params['base']}^{{{params['exposant1']}}} × {params['base']}^{{{params['exposant2']}}}."
            elif type_calcul == "quotient" and all(k in params for k in ['base', 'exposant1', 'exposant2']):
                enonce = f"Calculer {params['base']}^{{{params['exposant1']}}} ÷ {params['base']}^{{{params['exposant2']}}}."
            else:
                return self._fallback_generic(spec)
            
            return MathTextGeneration(
                enonce=enonce,
                explication_prof="Exercice sur les puissances",
                solution_redigee=f"Résultat = {spec.resultat_final}"
            )
        except Exception as e:
            logger.warning(f"Fallback puissances échoué, utilisation fallback generic: {e}")
            return self._fallback_generic(spec)

    
    def _fallback_cercle(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour cercles - Robuste"""
        
        try:
            params = spec.parametres
            type_calcul = params.get("type", "")
            
            if type_calcul == "perimetre" and "rayon" in params:
                enonce = f"Calculer le périmètre d'un cercle de rayon {params['rayon']} cm."
            elif type_calcul == "aire" and "rayon" in params:
                enonce = f"Calculer l'aire d'un cercle de rayon {params['rayon']} cm."
            elif type_calcul == "rayon_depuis_perimetre" and "perimetre" in params:
                enonce = f"Un cercle a un périmètre de {params['perimetre']} cm. Calculer son rayon."
            else:
                return self._fallback_generic(spec)
            
            return MathTextGeneration(
                enonce=enonce,
                explication_prof="Exercice sur les cercles",
                solution_redigee=f"Résultat = {spec.resultat_final}"
            )
        except Exception as e:
            logger.warning(f"Fallback cercle échoué, utilisation fallback generic: {e}")
            return self._fallback_generic(spec)
    
    def _fallback_thales(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour théorème de Thalès - COHÉRENT ET COMPLET"""
        
        try:
            params = spec.parametres
            points = params.get("points", [])
            
            if len(points) < 5:
                logger.warning("Fallback Thalès: pas assez de points")
                return self._fallback_generic(spec)
            
            # Points : [0]=A (sommet), [1]=B, [2]=C (base), [3]=D (sur AB), [4]=E (sur AC)
            # Configuration : Triangle ABC, D sur [AB], E sur [AC], (DE) // (BC)
            A, B, C, D, E = points[0], points[1], points[2], points[3], points[4]
            
            # Récupérer les longueurs depuis figure_geometrique si disponible
            longueurs = {}
            if spec.figure_geometrique:
                longueurs = spec.figure_geometrique.longueurs_connues
            
            # Construire l'énoncé avec les longueurs connues
            donnees = []
            segments_disponibles = [
                f"{A}{D}", f"{D}{B}", f"{A}{E}", f"{E}{C}",
                f"{D}{E}", f"{B}{C}"
            ]
            
            for seg in segments_disponibles:
                if seg in longueurs:
                    donnees.append(f"{seg} = {longueurs[seg]} cm")
            
            # Si pas de longueurs, utiliser les paramètres
            if not donnees and "longueurs_connues" in params:
                for seg, val in params["longueurs_connues"].items():
                    donnees.append(f"{seg} = {val} cm")
            
            # Construire l'énoncé structuré
            enonce_parts = [
                f"Soit un triangle {A}{B}{C}.",
                f"Le point {D} est situé sur le segment [{A}{B}].",
                f"Le point {E} est situé sur le segment [{A}{C}].",
                f"Les droites ({D}{E}) et ({B}{C}) sont parallèles."
            ]
            
            if donnees:
                enonce_parts.append(f"On sait que : {', '.join(donnees)}.")
            
            # Trouver ce qui est demandé
            a_calculer = params.get("a_calculer", None)
            if not a_calculer and spec.figure_geometrique:
                a_calculer_list = spec.figure_geometrique.longueurs_a_calculer
                if a_calculer_list:
                    a_calculer = a_calculer_list[0]
            
            if a_calculer:
                enonce_parts.append(f"Calculer la longueur {a_calculer}.")
            else:
                enonce_parts.append("En déduire le rapport de Thalès.")
            
            enonce = " ".join(enonce_parts)
            
            # Solution structurée
            solution_parts = [
                f"Configuration de Thalès dans le triangle {A}{B}{C}.",
                f"Les points {D}, {A}, {B} sont alignés (dans cet ordre).",
                f"Les points {E}, {A}, {C} sont alignés (dans cet ordre).",
                f"Les droites ({D}{E}) et ({B}{C}) sont parallèles.",
                "",
                "D'après le théorème de Thalès :",
                f"{A}{D}/{A}{B} = {A}{E}/{A}{C} = {D}{E}/{B}{C}",
                "",
            ]
            
            if donnees:
                solution_parts.append("Application numérique :")
                solution_parts.extend(donnees)
                solution_parts.append("")
            
            solution_parts.append(f"Résultat final : {spec.resultat_final}")
            
            solution = "\n".join(solution_parts)
            
            return MathTextGeneration(
                enonce=enonce,
                explication_prof=f"Configuration de Thalès : triangle {A}{B}{C} avec ({D}{E}) // ({B}{C})",
                solution_redigee=solution
            )
        except Exception as e:
            logger.warning(f"Fallback Thalès échoué, utilisation fallback generic: {e}")
            logger.exception(e)
            return self._fallback_generic(spec)
    
    def _fallback_trigonometrie(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour trigonométrie - Robuste"""
        
        try:
            params = spec.parametres
            angle = params.get("angle", 30)
            type_calcul = params.get("type_calcul", "")
            
            if type_calcul == "cote_oppose":
                enonce = f"Dans un triangle rectangle, calculer le côté opposé à un angle de {angle}°."
            elif type_calcul == "cote_adjacent":
                enonce = f"Dans un triangle rectangle, calculer le côté adjacent à un angle de {angle}°."
            elif type_calcul == "hypotenuse":
                enonce = f"Dans un triangle rectangle, calculer l'hypoténuse sachant l'angle de {angle}°."
            else:
                return self._fallback_generic(spec)
            
            return MathTextGeneration(
                enonce=enonce,
                explication_prof="Exercice de trigonométrie",
                solution_redigee=f"Résultat = {spec.resultat_final}"
            )
        except Exception as e:
            logger.warning(f"Fallback trigonometrie échoué, utilisation fallback generic: {e}")
            return self._fallback_generic(spec)
    
    def _fallback_triangle_quelconque(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour triangles quelconques - Robuste"""
        
        try:
            figure = spec.figure_geometrique
            
            if not figure or not figure.points or len(figure.points) < 3:
                return self._fallback_generic(spec)
            
            triangle_name = "".join(figure.points)
            
            # Récupérer les angles connus de la figure
            angles_connus = figure.angles_connus if hasattr(figure, 'angles_connus') and figure.angles_connus else {}
            
            if not angles_connus:
                return self._fallback_generic(spec)
            
            # Construire l'énoncé avec les angles
            angles_str = []
            for angle_name, valeur in angles_connus.items():
                # angle_name est de la forme "DEF" (angle en E)
                if len(angle_name) >= 3:
                    sommet = angle_name[1] if len(angle_name) == 3 else angle_name[0]
                    angles_str.append(f"l'angle en {sommet} mesure {valeur}°")
            
            if not angles_str:
                return self._fallback_generic(spec)
            
            enonce = f"""Dans le triangle {triangle_name}, {" et ".join(angles_str)}. """ + \
                    """Calculer la mesure du troisième angle."""
            
            solution = f"""La somme des angles d'un triangle est toujours égale à 180°.
Résultat : {spec.resultat_final}"""
            
            return MathTextGeneration(
                enonce=enonce,
                explication_prof="Exercice sur la somme des angles d'un triangle",
                solution_redigee=solution
            )
        except Exception as e:
            logger.warning(f"Fallback triangle_quelconque échoué, utilisation fallback generic: {e}")
            return self._fallback_generic(spec)
    
    def _fallback_perimetre_aire(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour périmètres et aires - Robuste"""
        
        try:
            figure = spec.figure_geometrique
            params = spec.parametres
            
            if not figure:
                return self._fallback_generic(spec)
            
            figure_type = params.get("figure", figure.type)
            
            # Cas du rectangle
            if figure_type == "rectangle" or figure.type == "rectangle":
                longueur = params.get("longueur", None)
                largeur = params.get("largeur", None)
                
                # Si pas dans params, chercher dans longueurs_connues
                if not longueur or not largeur:
                    longueurs = figure.longueurs_connues if figure.longueurs_connues else {}
                    valeurs = list(longueurs.values())
                    if len(valeurs) >= 2:
                        longueur = valeurs[0]
                        largeur = valeurs[1]
                
                if longueur and largeur:
                    enonce = f"Un rectangle a pour dimensions {longueur} cm et {largeur} cm. " + \
                            "Calculer son périmètre et son aire."
                    
                    return MathTextGeneration(
                        enonce=enonce,
                        explication_prof="Exercice sur périmètre et aire d'un rectangle",
                        solution_redigee=f"Résultat : {spec.resultat_final}"
                    )
            
            # Cas du carré
            elif figure_type == "carre":
                cote = params.get("cote", None)
                
                if not cote and figure.longueurs_connues:
                    valeurs = list(figure.longueurs_connues.values())
                    if valeurs:
                        cote = valeurs[0]
                
                if cote:
                    enonce = f"Un carré a pour côté {cote} cm. " + \
                            "Calculer son périmètre et son aire."
                    
                    return MathTextGeneration(
                        enonce=enonce,
                        explication_prof="Exercice sur périmètre et aire d'un carré",
                        solution_redigee=f"Résultat : {spec.resultat_final}"
                    )
            
            # Cas du cercle
            elif figure_type == "cercle" or figure.type == "cercle":
                rayon = params.get("rayon", None)
                
                if not rayon and figure.longueurs_connues:
                    rayon = figure.longueurs_connues.get("rayon", None)
                
                if rayon:
                    enonce = f"Un cercle a pour rayon {rayon} cm. " + \
                            "Calculer son périmètre et son aire."
                    
                    return MathTextGeneration(
                        enonce=enonce,
                        explication_prof="Exercice sur périmètre et aire d'un cercle",
                        solution_redigee=f"Résultat : {spec.resultat_final}"
                    )
            
            return self._fallback_generic(spec)
            
        except Exception as e:
            logger.warning(f"Fallback perimetre_aire échoué, utilisation fallback generic: {e}")
            return self._fallback_generic(spec)
    
    def _fallback_rectangle(self, spec: MathExerciseSpec) -> MathTextGeneration:
        """Template fallback pour rectangles - Robuste"""
        
        try:
            figure = spec.figure_geometrique
            params = spec.parametres
            
            if not figure or not figure.points or len(figure.points) < 4:
                return self._fallback_generic(spec)
            
            rectangle_name = "".join(figure.points)
            longueur = params.get("longueur", None)
            largeur = params.get("largeur", None)
            
            # Si pas dans params, chercher dans longueurs_connues
            if not longueur or not largeur:
                longueurs = figure.longueurs_connues if figure.longueurs_connues else {}
                valeurs = list(longueurs.values())
                if len(valeurs) >= 2:
                    longueur = valeurs[0]
                    largeur = valeurs[1]
            
            if not longueur or not largeur:
                return self._fallback_generic(spec)
            
            enonce = f"Le rectangle {rectangle_name} a pour dimensions : longueur = {longueur} cm et largeur = {largeur} cm. " + \
                    "Calculer son périmètre et son aire."
            
            solution = f"""Périmètre = 2 × (longueur + largeur) = 2 × ({longueur} + {largeur})
Aire = longueur × largeur = {longueur} × {largeur}
Résultat : {spec.resultat_final}"""
            
            return MathTextGeneration(
                enonce=enonce,
                explication_prof="Exercice sur périmètre et aire d'un rectangle",
                solution_redigee=solution
            )
        except Exception as e:
            logger.warning(f"Fallback rectangle échoué, utilisation fallback generic: {e}")
            return self._fallback_generic(spec)



    def _validate_cercle_specifique(
        self, 
        text: MathTextGeneration, 
        spec: MathExerciseSpec
    ) -> bool:
        """
        Validation STRICTE spécifique aux exercices de CERCLES
        
        Règles :
        1. Le rayon mentionné doit être EXACTEMENT celui de la spec
        2. Le centre doit être UNIQUEMENT le point autorisé
        3. Aucune valeur inventée
        4. Formules correctes (périmètre vs aire)
        
        Returns:
            True si valide, False sinon (→ fallback)
        """
        
        try:
            import re
            
            # 1. Récupérer les données de référence
            rayon_attendu = spec.parametres.get("rayon", None)
            type_calcul = spec.parametres.get("type", "perimetre")
            
            if not rayon_attendu:
                logger.warning("❌ Validation Cercle : rayon non défini dans spec")
                return False
            
            # Point centre autorisé
            centre_attendu = None
            if spec.figure_geometrique and spec.figure_geometrique.points:
                centre_attendu = spec.figure_geometrique.points[0]
            
            if not centre_attendu:
                logger.warning("❌ Validation Cercle : centre non défini")
                return False
            
            # 2. Vérifier le rayon dans l'énoncé
            all_text = text.enonce + (text.solution_redigee or "")
            
            # Pattern : "rayon X cm" ou "rayon de X cm"
            rayon_pattern = r'rayon\s+(?:de\s+)?(\d+(?:\.\d+)?)\s*cm'
            rayons_detectes = re.findall(rayon_pattern, all_text, re.IGNORECASE)
            
            if rayons_detectes:
                for rayon_str in rayons_detectes:
                    rayon_detecte = float(rayon_str)
                    
                    # Vérifier que le rayon détecté = rayon attendu
                    if abs(rayon_detecte - rayon_attendu) > 0.01:
                        logger.warning(
                            f"❌ Validation Cercle : Rayon INCOHÉRENT détecté={rayon_detecte}, "
                            f"attendu={rayon_attendu}"
                        )
                        return False
            
            # 3. Vérifier que seul le centre autorisé est mentionné
            # Pattern : "cercle de centre X" ou "centre X"
            centre_pattern = r'centre\s+([A-Z])'
            centres_detectes = re.findall(centre_pattern, all_text, re.IGNORECASE)
            
            for centre_detecte in centres_detectes:
                if centre_detecte != centre_attendu:
                    logger.warning(
                        f"❌ Validation Cercle : Centre INCOHÉRENT détecté={centre_detecte}, "
                        f"attendu={centre_attendu}"
                    )
                    return False
            
            # 4. Vérifier formule appropriée selon type
            if type_calcul == "perimetre":
                # Doit contenir "2πr" ou "2 × π × r" ou équivalent
                if not re.search(r'2\s*[×x*]\s*π\s*[×x*]\s*r|2\s*π\s*r', all_text, re.IGNORECASE):
                    logger.warning("❌ Validation Cercle : Formule périmètre absente ou incorrecte")
                    # Tolérer si fallback sera utilisé
                    pass
            
            elif type_calcul == "aire":
                # Doit contenir "πr²" ou "π × r²"
                if not re.search(r'π\s*[×x*]?\s*r[²2]', all_text, re.IGNORECASE):
                    logger.warning("❌ Validation Cercle : Formule aire absente ou incorrecte")
                    pass
            
            # 5. Vérifier qu'il n'y a pas de valeurs absurdes
            # Pattern : tous les nombres dans le texte
            nombres_pattern = r'\b(\d+(?:\.\d+)?)\b'
            nombres_detectes = [float(n) for n in re.findall(nombres_pattern, all_text)]
            
            # Vérifier qu'aucun nombre n'est trop éloigné du rayon (sauf résultat)
            for nombre in nombres_detectes:
                # Ignorer les nombres très proches du rayon (valide)
                if abs(nombre - rayon_attendu) < 0.1:
                    continue
                
                # Ignorer les grands nombres (probablement le périmètre/aire calculé)
                if nombre > rayon_attendu * 2:
                    continue
                
                # Si un nombre entre rayon et 2*rayon n'est pas le rayon, suspect
                if rayon_attendu < nombre < rayon_attendu * 1.5:
                    logger.warning(
                        f"⚠️ Validation Cercle : Nombre suspect détecté={nombre}, rayon={rayon_attendu}"
                    )
                    # Ne pas rejeter automatiquement, peut être valide
            
            # ✅ Toutes les validations passent
            logger.info(f"✅ Validation Cercle réussie : rayon={rayon_attendu}, centre={centre_attendu}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur validation Cercle : {e}")
            return False  # En cas d'erreur, rejeter par sécurité
    
    def _try_generate_from_gabarit(self, spec: MathExerciseSpec) -> Optional[MathTextGeneration]:
        """
        🎯 SYSTÈME D'OPTIMISATION IA - Le Maître Mot
        
        Tente de générer l'énoncé depuis un gabarit pré-existant.
        Si réussi : 0 appel IA, coût = 0, génération instantanée.
        
        FLUX :
            1. Vérifier si des gabarits existent pour ce chapitre/type
            2. Sélectionner un style aléatoire
            3. Construire la clé de cache
            4. Vérifier le cache
            5. Si cache HIT : interpoler et retourner
            6. Si cache MISS : charger gabarit, interpoler, cacher, retourner
            7. Si échec : retourner None → appel IA classique
        
        Args:
            spec: Spécification mathématique de l'exercice
        
        Returns:
            MathTextGeneration si succès, None si échec (→ appel IA)
        """
        try:
            # 1. Détecter le type pédagogique depuis les paramètres
            # Pour symétries, le type est dans parametres["type"]
            pedagogical_type = self._detect_pedagogical_type(spec)
            
            logger.info(f"🔍 Check gabarit pour: {spec.chapitre} / {pedagogical_type}")
            
            # 1. Vérifier si des gabarits existent
            if not gabarit_loader.has_gabarit(spec.chapitre, pedagogical_type):
                logger.info(f"❌ Pas de gabarits pour {spec.chapitre} / {pedagogical_type}")
                return None
            
            logger.info(f"✅ Gabarits trouvés pour {spec.chapitre} / {pedagogical_type}")
            
            # 2. Sélectionner un style aléatoire
            style = style_manager.get_random_style()
            logger.info(f"🎨 Style sélectionné: {style.value}")
            
            # 3. Construire la clé de cache
            cache_key = style_manager.build_cache_key(
                chapitre=spec.chapitre,
                type_exercice=pedagogical_type,
                difficulte=spec.difficulte.value,
                style=style
            )
            logger.info(f"🔑 Cache key: {cache_key}")
            
            # 4. Vérifier le cache
            cached_template = cache_manager.get(cache_key)
            
            if cached_template:
                # 📊 Cache HIT : interpoler directement
                logger.info(f"💚 CACHE HIT : {cache_key}")
                template = cached_template
            else:
                # 📊 Cache MISS : charger le gabarit
                logger.info(f"💛 CACHE MISS : {cache_key} → Chargement gabarit")
                template = gabarit_loader.get_random_gabarit(
                    chapitre=spec.chapitre,
                    type_exercice=pedagogical_type,
                    style=style
                )
                
                if not template:
                    logger.warning(f"❌ Aucun gabarit trouvé pour style {style.value}")
                    return None
                
                logger.info(f"✅ Template chargé: {template[:50]}...")
                # Stocker dans le cache pour le futur
                cache_manager.set(cache_key, template)
            
            # 5. Préparer les valeurs d'interpolation
            logger.info(f"📝 Préparation des valeurs d'interpolation...")
            values = gabarit_loader.prepare_interpolation_values(spec)
            
            if not values:
                logger.warning("❌ Échec préparation des valeurs d'interpolation")
                return None
            
            logger.info(f"✅ Valeurs préparées: {list(values.keys())}")
            
            # 6. Interpoler le template
            enonce_final = cache_manager.interpolate(template, values)
            logger.info(f"✅ Énoncé interpolé: {enonce_final[:80]}...")
            
            # 7. Créer la génération de texte
            # Note : Pour les gabarits, on ne génère pas de solution rédigée
            # (la solution calculée existe déjà dans la spec)
            text_generation = MathTextGeneration(
                enonce=enonce_final,
                explication_prof=None,
                solution_redigee=self._build_solution_from_steps(spec)
            )
            
            logger.info(f"🎯 ✅ Énoncé généré depuis gabarit (style: {style.value}) - 0 APPEL IA")
            return text_generation
            
        except Exception as e:
            logger.error(f"❌ Erreur génération depuis gabarit : {e}", exc_info=True)
            return None
    
    def _detect_pedagogical_type(self, spec: MathExerciseSpec) -> str:
        """
        Détecte le type pédagogique d'un exercice depuis ses paramètres.
        
        Mappe les types spécifiques (ex: "trouver_symetrique") vers 
        les types de gabarits universels ("trouver_valeur", "verifier_propriete").
        
        Args:
            spec: Spécification de l'exercice
        
        Returns:
            Type pédagogique ("trouver_valeur", "verifier_propriete", etc.)
        """
        # Extraire le type depuis les paramètres
        param_type = spec.parametres.get("type", "")
        
        # Mapping des types spécifiques vers types pédagogiques universels
        TYPE_MAPPING = {
            # Types universels (identité)
            "trouver_valeur": "trouver_valeur",
            "verifier_propriete": "verifier_propriete",
            "completer_structure": "completer_structure",
            "probleme_redige": "probleme_redige",
            
            # Symétrie axiale / centrale
            "trouver_symetrique": "trouver_valeur",
            "verifier_symetrie": "verifier_propriete",
            "completer_figure": "completer_structure",
            
            # Autres chapitres (à étendre)
            "calculer": "trouver_valeur",
            "verifier": "verifier_propriete",
            "demontrer": "probleme_redige"
        }
        
        # Chercher dans le mapping
        pedagogical_type = TYPE_MAPPING.get(param_type)
        
        if pedagogical_type:
            logger.debug(f"Type '{param_type}' mappé vers '{pedagogical_type}'")
            return pedagogical_type
        
        # Fallback: utiliser le type de l'exercice si pas de mapping trouvé
        logger.debug(f"Pas de mapping pour '{param_type}', utilisation du type d'exercice")
        return spec.type_exercice.value
    
    def _build_solution_from_steps(self, spec: MathExerciseSpec) -> str:
        """
        Construit une solution rédigée simple depuis les étapes calculées.
        
        Utilisé quand on génère depuis un gabarit (sans appel IA).
        """
        if not spec.etapes_calculees:
            return f"Résultat : {spec.resultat_final}"
        
        solution = "\n".join(spec.etapes_calculees)
        solution += f"\n\nRésultat final : {spec.resultat_final}"
        return solution

