"""
Helper pour l'enrichissement IA des fiches d'exercices
Sprint E - Application de l'IA au preview avant génération PDF

Fonction principale:
- apply_ai_enrichment_to_sheet_preview(): Applique l'IA au preview selon les flags
"""

import logging
import asyncio
from typing import Dict, Any, List
from copy import deepcopy

logger = logging.getLogger(__name__)


async def apply_ai_enrichment_to_sheet_preview(sheet_preview: dict) -> dict:
    """
    Applique l'enrichissement IA au preview d'une feuille d'exercices
    
    Parcourt tous les items et questions:
    - Si config.ai_enonce: enrichit enonce_brut
    - Si config.ai_correction: enrichit solution_brut
    
    En cas d'erreur IA:
    - Log l'erreur
    - Continue pour les autres questions
    - Conserve les versions brutes (fallback)
    
    Args:
        sheet_preview: Preview complet de la feuille (dict)
        
    Returns:
        dict: Preview avec énoncés/corrections enrichis (nouveau dict)
    """
    from ia_engine.exercise_ai_enrichment import enrich_statement, enrich_correction
    
    logger.info("🎨 Début de l'enrichissement IA du preview")
    
    # Créer une copie profonde pour ne pas modifier l'original
    enriched_preview = deepcopy(sheet_preview)
    
    items = enriched_preview.get("items", [])
    niveau = enriched_preview.get("niveau", "")
    
    # Statistiques
    total_questions = 0
    enonces_enrichis = 0
    corrections_enrichies = 0
    erreurs = 0
    
    # Parcourir tous les items
    for item_idx, item in enumerate(items):
        try:
            config = item.get("config", {})
            generated = item.get("generated", {})
            questions = generated.get("questions", [])
            
            # Vérifier si l'IA est activée pour cet item
            ai_enonce = config.get("ai_enonce", False)
            ai_correction = config.get("ai_correction", False)
            
            if not ai_enonce and not ai_correction:
                logger.info(f"⏭️  Item {item_idx + 1}: IA désactivée, skip")
                continue
            
            logger.info(
                f"🔄 Item {item_idx + 1}: IA activée "
                f"(énoncé={ai_enonce}, correction={ai_correction})"
            )
            
            # Parcourir toutes les questions de cet item
            for q_idx, question in enumerate(questions):
                total_questions += 1
                
                try:
                    enonce_brut = question.get("enonce_brut", "")
                    solution_brut = question.get("solution_brut", "")
                    data = question.get("data", {})
                    
                    # Enrichissement de l'énoncé si demandé
                    if ai_enonce and enonce_brut:
                        try:
                            enriched_enonce = await enrich_statement(
                                enonce_brut=enonce_brut,
                                data=data,
                                niveau=niveau,
                                style=None
                            )
                            
                            # Remplacer l'énoncé brut par la version enrichie
                            question["enonce_brut"] = enriched_enonce
                            enonces_enrichis += 1
                            
                            logger.info(
                                f"  ✅ Q{q_idx + 1}: Énoncé enrichi "
                                f"({len(enonce_brut)}→{len(enriched_enonce)} chars)"
                            )
                        except Exception as e:
                            logger.error(f"  ❌ Q{q_idx + 1}: Erreur enrichissement énoncé: {e}")
                            erreurs += 1
                            # Conserver l'énoncé brut (déjà en place)
                    
                    # Enrichissement de la correction si demandé
                    if ai_correction and solution_brut:
                        try:
                            enriched_solution = await enrich_correction(
                                solution_brut=solution_brut,
                                data=data,
                                niveau=niveau
                            )
                            
                            # Remplacer la solution brute par la version enrichie
                            question["solution_brut"] = enriched_solution
                            corrections_enrichies += 1
                            
                            logger.info(
                                f"  ✅ Q{q_idx + 1}: Correction enrichie "
                                f"({len(solution_brut)}→{len(enriched_solution)} chars)"
                            )
                        except Exception as e:
                            logger.error(f"  ❌ Q{q_idx + 1}: Erreur enrichissement correction: {e}")
                            erreurs += 1
                            # Conserver la solution brute (déjà en place)
                
                except Exception as e:
                    logger.error(f"  ❌ Q{q_idx + 1}: Erreur traitement question: {e}")
                    erreurs += 1
                    # Continuer avec les autres questions
        
        except Exception as e:
            logger.error(f"❌ Item {item_idx + 1}: Erreur traitement item: {e}")
            erreurs += 1
            # Continuer avec les autres items
    
    # Log des statistiques finales
    logger.info("=" * 60)
    logger.info(f"✅ Enrichissement IA terminé:")
    logger.info(f"  - Questions traitées: {total_questions}")
    logger.info(f"  - Énoncés enrichis: {enonces_enrichis}")
    logger.info(f"  - Corrections enrichies: {corrections_enrichies}")
    logger.info(f"  - Erreurs rencontrées: {erreurs}")
    logger.info("=" * 60)
    
    return enriched_preview


def check_if_ai_needed(sheet_preview: dict) -> bool:
    """
    Vérifie si au moins un item de la feuille a l'IA activée
    
    Args:
        sheet_preview: Preview de la feuille
        
    Returns:
        bool: True si l'IA est activée pour au moins un item
    """
    items = sheet_preview.get("items", [])
    
    for item in items:
        config = item.get("config", {})
        
        if config.get("ai_enonce", False) or config.get("ai_correction", False):
            return True
    
    return False


# Export des fonctions publiques
__all__ = [
    "apply_ai_enrichment_to_sheet_preview",
    "check_if_ai_needed"
]
