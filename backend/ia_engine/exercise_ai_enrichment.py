"""
Module d'enrichissement IA pour exercices MathALÉA
Sprint E - Couche IA premium optionnelle

Fonctionnalités:
- Enrichissement des énoncés (rendre plus pédagogique/clair)
- Enrichissement des corrections (détailler les étapes)
- Respect strict des données mathématiques (data)
- Fallback robuste en cas d'erreur IA
"""

import logging
import json
from typing import Dict, Any, Optional
from backend.utils import get_emergent_key
from backend.emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)


async def enrich_statement(
    enonce_brut: str,
    data: Dict[str, Any],
    niveau: str,
    style: Optional[str] = None
) -> str:
    """
    Enrichit un énoncé d'exercice en le reformulant de manière pédagogique
    
    Règles strictes:
    - NE JAMAIS modifier les valeurs numériques de data
    - Rendre l'énoncé plus clair et pédagogique
    - Contextualiser légèrement si pertinent
    - En cas d'erreur: retourner enonce_brut tel quel
    
    Args:
        enonce_brut: Énoncé original généré
        data: Données mathématiques (IMMUABLES)
        niveau: Niveau scolaire (ex: "6e", "5e")
        style: Style de formulation optionnel
        
    Returns:
        str: Énoncé enrichi ou énoncé brut si erreur
    """
    try:
        logger.info(f"🎨 Enrichissement énoncé (niveau: {niveau})")
        
        # Récupérer la clé Emergent
        emergent_key = get_emergent_key()
        
        # Créer le prompt système
        system_prompt = """Tu es un assistant pédagogique spécialisé en mathématiques.

**TA MISSION** :
Reformuler l'énoncé d'exercice pour le rendre plus clair, plus pédagogique et mieux contextualisé, SANS JAMAIS modifier les valeurs numériques.

**RÈGLES ABSOLUES** :
1. ❌ Ne JAMAIS changer les nombres, valeurs, ou résultats
2. ❌ Ne JAMAIS modifier les noms de points géométriques
3. ❌ Ne JAMAIS ajouter de nouvelles données mathématiques
4. ✅ Rendre la formulation plus claire et pédagogique
5. ✅ Ajouter un léger contexte si pertinent (sans changer les maths)
6. ✅ Adapter le vocabulaire au niveau scolaire

**FORMAT DE RÉPONSE** :
Réponds UNIQUEMENT avec l'énoncé reformulé, sans aucun commentaire ni explication supplémentaire."""

        # Créer le prompt utilisateur
        user_prompt = f"""**Énoncé à reformuler** :
{enonce_brut}

**Niveau scolaire** : {niveau}

**Données mathématiques (À RESPECTER STRICTEMENT)** :
{json.dumps(data, ensure_ascii=False, indent=2)}

Reformule l'énoncé de manière plus pédagogique et claire, en respectant TOUTES les valeurs numériques."""

        # Appel IA
        chat = LlmChat(
            system_message=system_prompt,
            emergent_key=emergent_key
        ).with_model('openai', 'gpt-4o')
        
        response = await chat.run(UserMessage(content=user_prompt))
        enriched = response.strip()
        
        # Validation basique: vérifier que l'énoncé n'est pas vide
        if not enriched or len(enriched) < 10:
            logger.warning("⚠️ Énoncé enrichi trop court, utilisation de l'original")
            return enonce_brut
        
        logger.info(f"✅ Énoncé enrichi avec succès ({len(enriched)} caractères)")
        return enriched
        
    except Exception as e:
        logger.error(f"❌ Erreur enrichissement énoncé: {e}")
        logger.info("🔄 Fallback: utilisation de l'énoncé brut")
        return enonce_brut


async def enrich_correction(
    solution_brut: str,
    data: Dict[str, Any],
    niveau: str
) -> str:
    """
    Enrichit une correction en développant les explications et étapes
    
    Règles strictes:
    - NE JAMAIS modifier les résultats numériques
    - Développer les étapes du raisonnement
    - Ajouter des explications pédagogiques
    - En cas d'erreur: retourner solution_brut tel quel
    
    Args:
        solution_brut: Solution originale générée
        data: Données mathématiques (IMMUABLES)
        niveau: Niveau scolaire
        
    Returns:
        str: Solution enrichie ou solution brute si erreur
    """
    try:
        logger.info(f"📚 Enrichissement correction (niveau: {niveau})")
        
        # Récupérer la clé Emergent
        emergent_key = get_emergent_key()
        
        # Créer le prompt système
        system_prompt = """Tu es un professeur de mathématiques expérimenté.

**TA MISSION** :
Développer et enrichir la correction d'un exercice en détaillant les étapes du raisonnement, SANS JAMAIS modifier les résultats numériques.

**RÈGLES ABSOLUES** :
1. ❌ Ne JAMAIS changer les résultats, calculs finaux, ou valeurs
2. ❌ Ne JAMAIS modifier les données mathématiques
3. ✅ Développer chaque étape du raisonnement
4. ✅ Expliquer les concepts mathématiques utilisés
5. ✅ Ajouter des conseils méthodologiques
6. ✅ Rendre la correction plus pédagogique et compréhensible
7. ✅ Utiliser des phrases complètes et structurées

**FORMAT DE RÉPONSE** :
Réponds UNIQUEMENT avec la correction enrichie, sans aucun commentaire ni explication supplémentaire."""

        # Créer le prompt utilisateur
        user_prompt = f"""**Correction à enrichir** :
{solution_brut}

**Niveau scolaire** : {niveau}

**Données mathématiques (À RESPECTER STRICTEMENT)** :
{json.dumps(data, ensure_ascii=False, indent=2)}

Développe cette correction de manière plus pédagogique et détaillée, en respectant TOUS les résultats numériques."""

        # Appel IA
        chat = LlmChat(
            system_message=system_prompt,
            emergent_key=emergent_key
        ).with_model('openai', 'gpt-4o')
        
        response = await chat.run(UserMessage(content=user_prompt))
        enriched = response.strip()
        
        # Validation basique
        if not enriched or len(enriched) < 10:
            logger.warning("⚠️ Correction enrichie trop courte, utilisation de l'originale")
            return solution_brut
        
        logger.info(f"✅ Correction enrichie avec succès ({len(enriched)} caractères)")
        return enriched
        
    except Exception as e:
        logger.error(f"❌ Erreur enrichissement correction: {e}")
        logger.info("🔄 Fallback: utilisation de la solution brute")
        return solution_brut


# Export des fonctions publiques
__all__ = [
    "enrich_statement",
    "enrich_correction"
]
