#!/usr/bin/env python3
"""
Script P4.B - Activation des générateurs GOLD identifiés dans l'audit

Active les 4 générateurs GOLD jamais référencés dans des chapitres :
- THALES_V2
- SYMETRIE_AXIALE_V2
- SIMPLIFICATION_FRACTIONS_V1
- SIMPLIFICATION_FRACTIONS_V2 (premium)

Usage:
    python backend/scripts/activate_gold_generators_p4b.py --dry-run
    python backend/scripts/activate_gold_generators_p4b.py --apply
"""

import sys
import argparse
from pathlib import Path

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.server import db
from backend.services.curriculum_persistence_service import (
    CurriculumPersistenceService,
    EnabledGeneratorConfig,
)
from backend.generators.factory import GeneratorFactory
from backend.utils.difficulty_utils import get_all_canonical_difficulties


# Générateurs GOLD à activer
GOLD_GENERATORS_TO_ACTIVATE = [
    {
        "generator_key": "THALES_V2",
        "suggested_chapters": ["6e_G07"],  # Géométrie - Agrandissements/Réductions
        "reason": "Générateur GOLD pour agrandissements/réductions"
    },
    {
        "generator_key": "SYMETRIE_AXIALE_V2",
        "suggested_chapters": ["6e_G07"],  # Géométrie - Symétrie axiale
        "reason": "Générateur GOLD pour symétrie axiale"
    },
    {
        "generator_key": "SIMPLIFICATION_FRACTIONS_V1",
        "suggested_chapters": ["6e_N08", "6e_N09"],  # Nombres - Fractions
        "reason": "Générateur GOLD pour simplification de fractions"
    },
    {
        "generator_key": "SIMPLIFICATION_FRACTIONS_V2",
        "suggested_chapters": ["6e_N08", "6e_N09"],  # Nombres - Fractions (premium)
        "reason": "Générateur GOLD PREMIUM pour simplification de fractions"
    },
]


async def get_generator_info(generator_key: str):
    """Récupère les informations d'un générateur"""
    gen_class = GeneratorFactory.get(generator_key)
    if not gen_class:
        return None
    
    all_gens = GeneratorFactory.list_all(include_disabled=True)
    gen_meta = next((g for g in all_gens if g["key"] == generator_key.upper()), None)
    
    if not gen_meta:
        return None
    
    # Récupérer les difficultés supportées
    schema = gen_class.get_schema()
    supported_difficulties = []
    if schema:
        difficulty_param = next((p for p in schema if p.name == "difficulty"), None)
        if difficulty_param and hasattr(difficulty_param, 'options'):
            supported_difficulties = difficulty_param.options or []
    
    # Normaliser les difficultés
    from backend.utils.difficulty_utils import normalize_difficulty
    normalized_difficulties = []
    for diff in supported_difficulties:
        try:
            normalized = normalize_difficulty(diff)
            if normalized not in normalized_difficulties:
                normalized_difficulties.append(normalized)
        except ValueError:
            pass
    
    # Si aucune difficulté, utiliser les canoniques
    if not normalized_difficulties:
        normalized_difficulties = get_all_canonical_difficulties()
    
    return {
        "key": generator_key.upper(),
        "label": gen_meta.get("label", generator_key),
        "version": gen_meta.get("version", ""),
        "min_offer": gen_meta.get("min_offer", "free"),
        "supported_difficulties": normalized_difficulties,
        "disabled": gen_meta.get("disabled", False),
    }


async def activate_generators(dry_run: bool = True):
    """Active les générateurs GOLD dans les chapitres suggérés"""
    service = CurriculumPersistenceService(db)
    
    print("🔍 Activation des générateurs GOLD (P4.B)")
    print("=" * 70)
    print()
    
    total_activated = 0
    total_skipped = 0
    
    for gen_config in GOLD_GENERATORS_TO_ACTIVATE:
        generator_key = gen_config["generator_key"]
        suggested_chapters = gen_config["suggested_chapters"]
        reason = gen_config["reason"]
        
        print(f"\n📦 Générateur: {generator_key}")
        print(f"   Raison: {reason}")
        
        # Vérifier que le générateur existe
        gen_info = await get_generator_info(generator_key)
        if not gen_info:
            print(f"   ❌ Générateur introuvable ou désactivé")
            total_skipped += 1
            continue
        
        if gen_info["disabled"]:
            print(f"   ❌ Générateur désactivé (ne sera pas activé)")
            total_skipped += 1
            continue
        
        print(f"   ✅ Label: {gen_info['label']}")
        print(f"   ✅ Version: {gen_info['version']}")
        print(f"   ✅ Difficultés: {', '.join(gen_info['supported_difficulties'])}")
        print(f"   ✅ Offre min: {gen_info['min_offer']}")
        
        # Activer dans les chapitres suggérés
        for chapter_code in suggested_chapters:
            print(f"\n   📚 Chapitre: {chapter_code}")
            
            try:
                chapter = await service.get_chapter_by_code(chapter_code)
                if not chapter:
                    print(f"      ⚠️  Chapitre introuvable (skip)")
                    continue
                
                # Récupérer les générateurs déjà activés
                enabled_generators_data = chapter.get("enabled_generators", [])
                enabled_keys = {eg.get("generator_key", "").upper() for eg in enabled_generators_data}
                
                if generator_key in enabled_keys:
                    print(f"      ✅ Déjà activé (skip)")
                    continue
                
                # Ajouter le générateur
                new_enabled_gen = EnabledGeneratorConfig(
                    generator_key=generator_key,
                    difficulty_presets=gen_info["supported_difficulties"],
                    min_offer=gen_info["min_offer"],
                    is_enabled=True,
                )
                
                updated_enabled = [
                    EnabledGeneratorConfig(**eg) for eg in enabled_generators_data
                ] + [new_enabled_gen]
                
                if not dry_run:
                    from backend.services.curriculum_persistence_service import ChapterUpdateRequest
                    update_request = ChapterUpdateRequest(
                        enabled_generators=updated_enabled
                    )
                    await service.update_chapter(chapter_code, update_request)
                    print(f"      ✅ Activé avec succès")
                    total_activated += 1
                else:
                    print(f"      🔍 [DRY-RUN] Serait activé")
                    total_activated += 1
            
            except Exception as e:
                print(f"      ❌ Erreur: {e}")
                total_skipped += 1
    
    print()
    print("=" * 70)
    print(f"📊 Résumé:")
    print(f"   ✅ Activés: {total_activated}")
    print(f"   ⏭️  Skippés: {total_skipped}")
    print()
    
    if dry_run:
        print("🔍 Mode DRY-RUN: aucun changement effectué")
        print("   Pour appliquer: python backend/scripts/activate_gold_generators_p4b.py --apply")
    else:
        print("✅ Modifications appliquées avec succès")


async def main():
    parser = argparse.ArgumentParser(
        description="Activer les générateurs GOLD identifiés dans l'audit P4.A"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Afficher ce qui serait fait sans modifier la DB"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Appliquer les modifications en DB"
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.apply:
        print("❌ Vous devez spécifier --dry-run ou --apply")
        sys.exit(1)
    
    import asyncio
    await activate_generators(dry_run=args.dry_run)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())




