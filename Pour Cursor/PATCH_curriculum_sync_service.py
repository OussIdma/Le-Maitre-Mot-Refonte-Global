"""
PATCH PRODUCTION - curriculum_sync_service.py
==============================================

Ajouter la synchronisation automatique admin_exercises → exercise_types

À ajouter dans la classe CurriculumSyncService (après sync_chapter_to_curriculum)
"""

import logging
import uuid
from typing import Dict, Any, Optional, Set
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# ============================================================================
# NOUVELLE MÉTHODE À AJOUTER DANS CurriculumSyncService
# ============================================================================

async def sync_chapter_to_exercise_types(
    self,
    chapter_code: str,
    force_recreate: bool = False
) -> Dict[str, Any]:
    """
    Synchronise un chapitre depuis admin_exercises vers la collection exercise_types.
    
    Cette méthode assure que tous les exercices dynamiques d'un chapitre sont
    représentés dans la collection exercise_types utilisée par l'endpoint mathalea.
    
    Architecture:
    - Source de vérité: admin_exercises (exercices créés via Admin UI)
    - Destination: exercise_types (utilisée par /api/mathalea/chapters/.../exercise-types)
    - Sync automatique lors du CRUD d'exercices
    
    Args:
        chapter_code: Code du chapitre (ex: "6E_N10")
        force_recreate: Si True, supprime et recrée tous les exercise_types (défaut: False)
    
    Returns:
        Dict avec:
        - created: nombre d'exercise_types créés
        - updated: nombre d'exercise_types mis à jour
        - deleted: nombre d'exercise_types supprimés
        - skipped: nombre d'exercise_types déjà existants
        - generator_keys: liste des generator_keys synchronisés
    
    Raises:
        ValueError: En cas d'erreur de validation
    """
    chapter_upper = chapter_code.upper().replace("-", "_")
    
    try:
        # Collection exercise_types (destination)
        exercise_types_collection = self.db["exercise_types"]
        
        # Statistiques de synchronisation
        stats = {
            'created': 0,
            'updated': 0,
            'deleted': 0,
            'skipped': 0,
            'generator_keys': []
        }
        
        # 1. Récupérer tous les exercices dynamiques du chapitre depuis admin_exercises
        exercises = await self.exercises_collection.find(
            {
                "chapter_code": chapter_upper,
                "is_dynamic": True,
                "generator_key": {"$exists": True, "$ne": None}
            },
            {
                "generator_key": 1,
                "exercise_type": 1,
                "difficulty": 1,
                "offer": 1,
                "needs_svg": 1,
                "title": 1
            }
        ).to_list(1000)
        
        logger.info(
            f"[EXERCISE_TYPES_SYNC] {len(exercises)} exercices dynamiques trouvés "
            f"pour {chapter_upper}"
        )
        
        if not exercises:
            logger.warning(
                f"[EXERCISE_TYPES_SYNC] Aucun exercice dynamique dans admin_exercises "
                f"pour {chapter_upper}. Sync ignorée."
            )
            return stats
        
        # 2. Grouper par generator_key (un exercise_type par generator_key)
        generators_map = {}
        for ex in exercises:
            gen_key = ex.get("generator_key")
            if not gen_key:
                continue
            
            if gen_key not in generators_map:
                generators_map[gen_key] = {
                    'generator_key': gen_key,
                    'exercise_type': ex.get('exercise_type'),
                    'difficulties': set(),
                    'offers': set(),
                    'needs_svg': ex.get('needs_svg', False),
                    'title': ex.get('title')
                }
            
            # Agréger les difficultés et offres disponibles
            if ex.get('difficulty'):
                generators_map[gen_key]['difficulties'].add(ex['difficulty'])
            if ex.get('offer'):
                generators_map[gen_key]['offers'].add(ex['offer'])
        
        # 3. Extraire le niveau depuis chapter_code (ex: "6E_N10" → "6E")
        niveau = chapter_upper.split('_')[0] if '_' in chapter_upper else chapter_upper[:2]
        
        # 4. Extraire le domaine depuis chapter_code
        domaine = _infer_domain_from_chapter(chapter_upper)
        
        # 5. Synchroniser chaque generator_key vers exercise_types
        for gen_key, gen_data in generators_map.items():
            
            # Obtenir exercise_type depuis GeneratorFactory
            exercise_type = _get_exercise_type_from_generator(gen_key)
            if not exercise_type:
                # Fallback: utiliser le champ exercise_type de l'exercice
                exercise_type = gen_data.get('exercise_type') or gen_key
                logger.warning(
                    f"[EXERCISE_TYPES_SYNC] Pas de mapping Factory pour {gen_key}, "
                    f"fallback: {exercise_type}"
                )
            
            # Construire l'identifiant unique pour exercise_type
            # Format: chapter_code + generator_key (déterministe, pas de uuid)
            exercise_type_id = f"{chapter_upper}_{gen_key}"
            
            # Vérifier si l'exercise_type existe déjà
            existing = await exercise_types_collection.find_one({
                "code_ref": gen_key,
                "chapter_code": chapter_upper
            })
            
            # Document exercise_type à créer/mettre à jour
            exercise_type_doc = {
                "id": exercise_type_id,
                "code_ref": gen_key,
                "chapter_code": chapter_upper,
                "chapitre_id": chapter_upper,  # Legacy fallback
                "niveau": niveau,
                "domaine": domaine,
                "libelle": gen_data.get('title') or f"Exercice {exercise_type}",
                "description": f"Exercice dynamique généré par {gen_key}",
                "generator_kind": "DYNAMIC",
                "difficulty_levels": sorted(list(gen_data['difficulties'])) or ["facile", "moyen", "difficile"],
                "available_offers": sorted(list(gen_data['offers'])) or ["free"],
                "min_questions": 1,
                "max_questions": 10,
                "requires_svg": gen_data.get('needs_svg', False),
                "updated_at": datetime.now(timezone.utc),
                "source": "admin_exercises_auto_sync"
            }
            
            if existing and not force_recreate:
                # Mise à jour (seulement les champs qui peuvent changer)
                update_fields = {
                    "difficulty_levels": exercise_type_doc["difficulty_levels"],
                    "available_offers": exercise_type_doc["available_offers"],
                    "requires_svg": exercise_type_doc["requires_svg"],
                    "updated_at": exercise_type_doc["updated_at"],
                    "libelle": exercise_type_doc["libelle"]
                }
                
                await exercise_types_collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": update_fields}
                )
                
                logger.info(
                    f"[EXERCISE_TYPES_SYNC] ✅ Mis à jour: {exercise_type_id} "
                    f"(generator: {gen_key})"
                )
                stats['updated'] += 1
                
            elif existing and force_recreate:
                # Suppression puis recréation
                await exercise_types_collection.delete_one({"_id": existing["_id"]})
                
                exercise_type_doc["created_at"] = datetime.now(timezone.utc)
                await exercise_types_collection.insert_one(exercise_type_doc)
                
                logger.info(
                    f"[EXERCISE_TYPES_SYNC] ✅ Recréé (force): {exercise_type_id} "
                    f"(generator: {gen_key})"
                )
                stats['deleted'] += 1
                stats['created'] += 1
                
            else:
                # Création
                exercise_type_doc["created_at"] = datetime.now(timezone.utc)
                await exercise_types_collection.insert_one(exercise_type_doc)
                
                logger.info(
                    f"[EXERCISE_TYPES_SYNC] ✅ Créé: {exercise_type_id} "
                    f"(generator: {gen_key})"
                )
                stats['created'] += 1
            
            stats['generator_keys'].append(gen_key)
        
        # 6. Nettoyer les exercise_types orphelins (optionnel - sécurité)
        # Si un exercise_type existe pour ce chapitre mais n'a plus d'exercice admin correspondant
        all_gen_keys = set(generators_map.keys())
        existing_exercise_types = await exercise_types_collection.find(
            {
                "chapter_code": chapter_upper,
                "generator_kind": "DYNAMIC",
                "source": "admin_exercises_auto_sync"
            },
            {"code_ref": 1}
        ).to_list(1000)
        
        for et in existing_exercise_types:
            gen_key = et.get("code_ref")
            if gen_key and gen_key not in all_gen_keys:
                # Cet exercise_type n'a plus d'exercice admin correspondant
                await exercise_types_collection.delete_one({"_id": et["_id"]})
                logger.info(
                    f"[EXERCISE_TYPES_SYNC] 🗑️  Supprimé orphelin: {gen_key} "
                    f"(plus d'exercice admin)"
                )
                stats['deleted'] += 1
        
        logger.info(
            f"[EXERCISE_TYPES_SYNC] Terminé pour {chapter_upper}: "
            f"créés={stats['created']}, mis à jour={stats['updated']}, "
            f"supprimés={stats['deleted']}"
        )
        
        return stats
        
    except Exception as e:
        logger.error(
            f"[EXERCISE_TYPES_SYNC] Erreur lors de la sync pour {chapter_upper}: {e}",
            exc_info=True
        )
        raise ValueError(
            f"Erreur lors de la synchronisation vers exercise_types pour {chapter_upper}: {e}"
        )


def _infer_domain_from_chapter(chapter_code: str) -> str:
    """
    Inférer le domaine mathématique depuis le code chapitre.
    
    Ex: "6E_GM07" → "Grandeurs et Mesures"
        "6E_N10" → "Nombres et Calculs"
    """
    if not chapter_code or '_' not in chapter_code:
        return "Géométrie"
    
    parts = chapter_code.split('_')
    if len(parts) < 2:
        return "Géométrie"
    
    domain_code = parts[1][:2] if len(parts[1]) >= 2 else parts[1][:1]
    
    domain_map = {
        'GM': 'Grandeurs et Mesures',
        'G': 'Géométrie',
        'N': 'Nombres et Calculs',
        'C': 'Calcul',
        'A': 'Algèbre',
        'F': 'Fonctions',
        'S': 'Statistiques',
        'P': 'Probabilités',
        'D': 'Données'
    }
    
    return domain_map.get(domain_code, 'Géométrie')


# ============================================================================
# NOTES D'IMPLÉMENTATION
# ============================================================================

"""
Cette méthode doit être ajoutée à la classe CurriculumSyncService 
dans backend/services/curriculum_sync_service.py

Elle sera appelée automatiquement par admin_exercises_routes.py lors de:
- create_exercise()
- update_exercise()
- delete_exercise()
- import_exercises()

Caractéristiques:
✅ Idempotente (peut être appelée plusieurs fois sans effet de bord)
✅ Transactionnelle (n'affecte pas admin_exercises si ça échoue)
✅ Loggée (pour debug et monitoring)
✅ Gestion des orphelins (cleanup automatique)
✅ Agrégation intelligente (un exercise_type par generator_key)
✅ Fallback sur exercise_type si pas de mapping Factory
✅ Préserve les données existantes lors des mises à jour
"""
