"""
Migration 005: Correction des templates pour SIMPLIFICATION_FRACTIONS_V1
==========================================================================

Ce script corrige les templates des exercices dynamiques qui utilisent
SIMPLIFICATION_FRACTIONS_V1 mais ont des placeholders incorrects (ex: SYMETRIE_AXIALE).

Problème identifié:
- Les exercices avec generator_key=SIMPLIFICATION_FRACTIONS_V1 utilisent des templates
  avec des placeholders de SYMETRIE_AXIALE (axe_equation, axe_label, etc.)
- Ces placeholders ne sont pas générés par SIMPLIFICATION_FRACTIONS_V1
- Erreur UNRESOLVED_PLACEHOLDERS → fallback vers pipeline statique → "CHAPITRE NON MAPPÉ"

Solution:
- Remplacer les templates par ceux corrects pour SIMPLIFICATION_FRACTIONS_V1

Script idempotent: peut être relancé sans erreur.
"""

import asyncio
import sys
import os
import re

# Ajouter le chemin du backend au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from backend.logger import get_logger

logger = get_logger()

# Configuration MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("DB_NAME", "lemaitremot")

# Templates corrects pour SIMPLIFICATION_FRACTIONS_V1
CORRECT_ENONCE_TEMPLATE = "<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>"

CORRECT_SOLUTION_TEMPLATE = """<ol>
  <li>{{step1}}</li>
  <li>{{step2}}</li>
  <li>{{step3}}</li>
  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>
</ol>"""

# Placeholders incorrects (SYMETRIE_AXIALE) à détecter
INCORRECT_PLACEHOLDERS = [
    "axe_equation",
    "axe_label",
    "figure_description",
    "points_labels",
    "points_symmetric_labels"
]


def has_incorrect_placeholders(template: str) -> bool:
    """
    Vérifie si un template contient des placeholders incorrects.
    
    Args:
        template: Template HTML à vérifier
        
    Returns:
        True si le template contient des placeholders incorrects
    """
    if not template:
        return False
    
    for placeholder in INCORRECT_PLACEHOLDERS:
        if f"{{{{{placeholder}}}}}" in template or f"{{{{ {placeholder} }}}}" in template:
            return True
    
    return False


def needs_correction(exercise: dict) -> bool:
    """
    Vérifie si un exercice a besoin d'être corrigé.
    
    Args:
        exercise: Document exercice depuis MongoDB
        
    Returns:
        True si l'exercice doit être corrigé
    """
    # Vérifier que c'est un exercice dynamique avec SIMPLIFICATION_FRACTIONS_V1
    if not exercise.get("is_dynamic"):
        return False
    
    generator_key = exercise.get("generator_key", "").upper()
    if generator_key != "SIMPLIFICATION_FRACTIONS_V1":
        return False
    
    # Vérifier si les templates contiennent des placeholders incorrects
    enonce_template = exercise.get("enonce_template_html", "")
    solution_template = exercise.get("solution_template_html", "")
    
    if has_incorrect_placeholders(enonce_template) or has_incorrect_placeholders(solution_template):
        return True
    
    # Vérifier aussi dans template_variants
    template_variants = exercise.get("template_variants", [])
    for variant in template_variants:
        if isinstance(variant, dict):
            enonce = variant.get("enonce_template_html", "")
            solution = variant.get("solution_template_html", "")
            if has_incorrect_placeholders(enonce) or has_incorrect_placeholders(solution):
                return True
    
    return False


async def fix_simplification_fractions_templates():
    """
    Migration one-shot: corrige les templates pour SIMPLIFICATION_FRACTIONS_V1.
    """
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    exercises_collection = db.admin_exercises
    
    logger.info("🚀 Début migration: correction templates SIMPLIFICATION_FRACTIONS_V1")
    
    # Trouver tous les exercices avec SIMPLIFICATION_FRACTIONS_V1
    query = {
        "is_dynamic": True,
        "generator_key": {"$regex": "^SIMPLIFICATION_FRACTIONS", "$options": "i"}
    }
    
    exercises = await exercises_collection.find(query).to_list(1000)
    logger.info(f"📚 {len(exercises)} exercices avec SIMPLIFICATION_FRACTIONS_V1 trouvés")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for exercise in exercises:
        chapter_code = exercise.get("chapter_code", "")
        exercise_id = exercise.get("id")
        
        try:
            # Vérifier si correction nécessaire
            if not needs_correction(exercise):
                logger.debug(
                    f"⏭️  Exercice {chapter_code}/{exercise_id} n'a pas besoin de correction"
                )
                skipped_count += 1
                continue
            
            logger.info(
                f"🔧 Correction de l'exercice {chapter_code}/{exercise_id} "
                f"(generator_key={exercise.get('generator_key')})"
            )
            
            # Préparer les mises à jour
            update_data = {}
            
            # Corriger enonce_template_html
            enonce_template = exercise.get("enonce_template_html", "")
            if has_incorrect_placeholders(enonce_template):
                update_data["enonce_template_html"] = CORRECT_ENONCE_TEMPLATE
                logger.info(f"  ✅ Énoncé corrigé")
            
            # Corriger solution_template_html
            solution_template = exercise.get("solution_template_html", "")
            if has_incorrect_placeholders(solution_template):
                update_data["solution_template_html"] = CORRECT_SOLUTION_TEMPLATE
                logger.info(f"  ✅ Solution corrigée")
            
            # Corriger template_variants si présents
            template_variants = exercise.get("template_variants", [])
            if template_variants:
                corrected_variants = []
                for variant in template_variants:
                    if isinstance(variant, dict):
                        corrected_variant = variant.copy()
                        
                        enonce = variant.get("enonce_template_html", "")
                        solution = variant.get("solution_template_html", "")
                        
                        if has_incorrect_placeholders(enonce):
                            corrected_variant["enonce_template_html"] = CORRECT_ENONCE_TEMPLATE
                            logger.info(f"  ✅ Variant {variant.get('id', 'unknown')} énoncé corrigé")
                        
                        if has_incorrect_placeholders(solution):
                            corrected_variant["solution_template_html"] = CORRECT_SOLUTION_TEMPLATE
                            logger.info(f"  ✅ Variant {variant.get('id', 'unknown')} solution corrigée")
                        
                        corrected_variants.append(corrected_variant)
                    else:
                        corrected_variants.append(variant)
                
                if corrected_variants != template_variants:
                    update_data["template_variants"] = corrected_variants
            
            # Mettre à jour l'exercice
            if update_data:
                result = await exercises_collection.update_one(
                    {"chapter_code": chapter_code, "id": exercise_id},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    updated_count += 1
                    logger.info(
                        f"✅ Exercice {chapter_code}/{exercise_id} mis à jour "
                        f"(champs: {list(update_data.keys())})"
                    )
                else:
                    logger.warning(f"⚠️  Aucune modification pour {chapter_code}/{exercise_id}")
            else:
                logger.debug(f"⏭️  Aucune correction nécessaire pour {chapter_code}/{exercise_id}")
                skipped_count += 1
        
        except Exception as e:
            error_count += 1
            logger.error(
                f"❌ Erreur lors de la correction de {chapter_code}/{exercise_id}: {e}",
                exc_info=True
            )
    
    logger.info(
        f"✅ Migration terminée: {updated_count} exercices corrigés, "
        f"{skipped_count} ignorés, {error_count} erreurs"
    )
    
    client.close()
    return updated_count, skipped_count, error_count


if __name__ == "__main__":
    asyncio.run(fix_simplification_fractions_templates())

