"""
Script de migration des exercices "pseudo-statiques" legacy vers MongoDB.

Migre les exercices depuis:
- Fichiers Python (gm07_exercises.py, gm08_exercises.py, tests_dyn_exercises.py)
- Vers la collection admin_exercises avec is_dynamic=False

Usage:
    python backend/scripts/migrate_pseudo_static_to_db.py [--dry-run] [--apply] [--chapter 6E_GM07] [--unlock]
"""

import argparse
import asyncio
import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# Ajouter le chemin du backend au PYTHONPATH
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Charger les variables d'environnement
load_dotenv(backend_dir / '.env')

# Import du loader legacy
from backend.services.legacy_exercise_loader import (
    discover_legacy_sources,
    load_all_legacy_exercises
)

# Import de la normalisation
from backend.services.curriculum_persistence_service import normalize_code_officiel

# Collection MongoDB
EXERCISES_COLLECTION = "admin_exercises"

# Logger simple
class SimpleLogger:
    def info(self, msg: str):
        print(f"[INFO] {msg}")
    
    def warning(self, msg: str):
        print(f"[WARN] {msg}")
    
    def error(self, msg: str):
        print(f"[ERROR] {msg}")

logger = SimpleLogger()


def compute_exercise_uid(
    chapter_code: str,
    enonce_html: str,
    solution_html: str,
    difficulty: str = "moyen"
) -> str:
    """
    Calcule un UID stable pour un exercice basé sur son contenu.
    
    Args:
        chapter_code: Code du chapitre
        enonce_html: Énoncé HTML (normalisé)
        solution_html: Solution HTML (normalisé)
        difficulty: Difficulté
    
    Returns:
        SHA256 hash en hexadécimal
    """
    # Normaliser les chaînes (strip, lowercase pour comparaison)
    normalized_enonce = enonce_html.strip().lower()
    normalized_solution = solution_html.strip().lower()
    
    # Créer une chaîne unique
    unique_string = f"{chapter_code}|{normalized_enonce}|{normalized_solution}|{difficulty}"
    
    # Calculer le hash SHA256
    return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()


def validate_exercise(ex: Dict[str, Any]) -> tuple:
    """
    Valide qu'un exercice peut être migré.
    
    Returns:
        (is_valid, error_message)
    """
    if not ex.get("enonce_html") or not ex["enonce_html"].strip():
        return False, "enonce_html vide"
    
    if not ex.get("solution_html") or not ex["solution_html"].strip():
        return False, "solution_html vide"
    
    if not ex.get("chapter_code"):
        return False, "chapter_code manquant"
    
    return True, None


def prepare_exercise_document(
    ex: Dict[str, Any],
    exercise_uid: str,
    locked: bool = True
) -> Dict[str, Any]:
    """
    Prépare un document MongoDB à partir d'un exercice legacy.
    
    Args:
        ex: Exercice legacy
        exercise_uid: UID calculé
        locked: Si True, l'exercice est verrouillé
    
    Returns:
        Document MongoDB prêt à être inséré
    """
    now = datetime.now(timezone.utc)
    
    # Générer un titre si absent
    title = ex.get("title")
    if not title:
        # Extraire un titre depuis l'énoncé (première phrase ou "Exercice N")
        enonce_text = ex.get("enonce_html", "")
        if enonce_text:
            # Essayer d'extraire le texte entre <strong> ou la première phrase
            import re
            strong_match = re.search(r'<strong>(.*?)</strong>', enonce_text)
            if strong_match:
                title = strong_match.group(1).strip()[:100]
            else:
                # Prendre les premiers 50 caractères
                text_only = re.sub(r'<[^>]+>', '', enonce_text).strip()
                title = text_only[:50] if text_only else f"Exercice {ex.get('id', '?')}"
        else:
            title = f"Exercice {ex.get('id', '?')}"
    
    doc = {
        "chapter_code": ex["chapter_code"],
        "id": ex.get("id"),  # Conserver l'ID legacy si présent
        "exercise_uid": exercise_uid,  # UID stable pour déduplication
        "title": title,
        "difficulty": ex.get("difficulty", "moyen"),
        "offer": ex.get("offer", "free"),
        "enonce_html": ex["enonce_html"],
        "solution_html": ex["solution_html"],
        "needs_svg": ex.get("needs_svg", False),
        "exercise_type": ex.get("exercise_type"),
        "family": ex.get("family"),
        "variables": ex.get("variables"),
        "svg_enonce_brief": ex.get("svg_enonce_brief"),
        "svg_solution_brief": ex.get("svg_solution_brief"),
        # Métadonnées de migration
        "source": "legacy_migration",
        "legacy_ref": ex.get("legacy_ref", "unknown"),
        "locked": locked,
        # Forcer is_dynamic=False pour les statiques
        "is_dynamic": False,
        "generator_key": None,  # Pas de générateur pour les statiques
        # Timestamps
        "created_at": now,
        "updated_at": now
    }
    
    # Ajouter order si présent
    if ex.get("order") is not None:
        doc["order"] = ex["order"]
    
    # Gérer needs_solution si solution_html est vide ou placeholder
    solution = ex.get("solution_html", "").strip().lower()
    if not solution or "à compléter" in solution or "solution à compléter" in solution:
        doc["needs_solution"] = True
        if not solution:
            doc["solution_html"] = "<p>Solution à compléter</p>"
    else:
        doc["needs_solution"] = False
    
    return doc


async def analyze_legacy_exercises(
    db,
    chapter_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyse préalable des exercices legacy avant migration.
    
    Génère un rapport détaillé :
    - CHAPITRE | FOUND | DYNAMIC | PSEUDO_STATIC | ALREADY_IN_DB
    
    Args:
        db: Base de données MongoDB
        chapter_code: Code du chapitre (None pour tous)
    
    Returns:
        Dict avec le rapport d'analyse
    """
    logger.info("\n" + "="*80)
    logger.info("📊 ANALYSE PRÉALABLE DES EXERCICES LEGACY")
    logger.info("="*80)
    
    collection = db[EXERCISES_COLLECTION]
    report = {
        "chapters": {},
        "summary": {
            "total_found": 0,
            "total_dynamic": 0,
            "total_pseudo_static": 0,
            "total_already_in_db": 0
        }
    }
    
    # Charger tous les exercices legacy
    sources = discover_legacy_sources()
    all_exercises = load_all_legacy_exercises(chapter_code=chapter_code)
    
    if not all_exercises:
        logger.warning("⚠️ Aucun exercice legacy trouvé")
        return report
    
    # En-tête du tableau
    logger.info("\nCHAPITRE              | FOUND | DYNAMIC | PSEUDO_STATIC | ALREADY_IN_DB")
    logger.info("-" * 80)
    
    # Analyser chaque chapitre
    for normalized_code, exercises in all_exercises.items():
        # Le code est déjà normalisé par load_all_legacy_exercises
        chapter_stats = {
            "legacy_code": normalized_code,  # Pour compatibilité
            "normalized_code": normalized_code,
            "found": len(exercises),
            "dynamic": 0,
            "pseudo_static": 0,
            "already_in_db": 0,
            "invalid": 0
        }
        
        # Compter les exercices dynamiques vs pseudo-statiques
        for ex in exercises:
            is_dynamic = ex.get("is_dynamic", False)
            if is_dynamic:
                chapter_stats["dynamic"] += 1
            else:
                chapter_stats["pseudo_static"] += 1
            
            # Valider l'exercice
            is_valid, _ = validate_exercise(ex)
            if not is_valid:
                chapter_stats["invalid"] += 1
                continue
            
            # Vérifier si déjà en DB
            exercise_uid = compute_exercise_uid(
                chapter_code=normalized_code,
                enonce_html=ex.get("enonce_html", ""),
                solution_html=ex.get("solution_html", ""),
                difficulty=ex.get("difficulty", "moyen")
            )
            
            existing = await collection.find_one({"exercise_uid": exercise_uid})
            if existing:
                chapter_stats["already_in_db"] += 1
        
        # Mettre à jour les totaux
        report["summary"]["total_found"] += chapter_stats["found"]
        report["summary"]["total_dynamic"] += chapter_stats["dynamic"]
        report["summary"]["total_pseudo_static"] += chapter_stats["pseudo_static"]
        report["summary"]["total_already_in_db"] += chapter_stats["already_in_db"]
        
        report["chapters"][normalized_code] = chapter_stats
        
        # Afficher la ligne du tableau
        logger.info(
            f"{normalized_code:20} | {chapter_stats['found']:5} | "
            f"{chapter_stats['dynamic']:7} | {chapter_stats['pseudo_static']:13} | "
            f"{chapter_stats['already_in_db']:13}"
        )
        
        if chapter_stats["invalid"] > 0:
            logger.warning(f"  ⚠️ {chapter_stats['invalid']} exercice(s) invalide(s) dans {normalized_code}")
    
    # Résumé
    logger.info("-" * 80)
    logger.info(
        f"{'TOTAL':20} | {report['summary']['total_found']:5} | "
        f"{report['summary']['total_dynamic']:7} | {report['summary']['total_pseudo_static']:13} | "
        f"{report['summary']['total_already_in_db']:13}"
    )
    logger.info("="*80)
    
    return report


async def migrate_exercises(
    db,
    chapter_code: Optional[str] = None,
    dry_run: bool = False,
    unlock: bool = False
) -> Dict[str, int]:
    """
    Migre les exercices legacy vers MongoDB.
    
    Args:
        db: Base de données MongoDB
        chapter_code: Code du chapitre (None pour tous)
        dry_run: Si True, ne fait que simuler
        unlock: Si True, locked=False (sinon locked=True)
    
    Returns:
        Dict avec les statistiques: {"inserted": X, "skipped": Y, "errors": Z}
    """
    stats = {
        "inserted": 0,
        "skipped": 0,
        "errors": 0,
        "chapters": {}
    }
    
    # Charger tous les exercices legacy
    logger.info("🔍 Découverte des sources legacy...")
    sources = discover_legacy_sources()
    logger.info(f"✅ Trouvé {len(sources['python_files'])} fichier(s) Python, {len(sources['json_files'])} fichier(s) JSON")
    
    logger.info("📦 Chargement des exercices legacy...")
    all_exercises = load_all_legacy_exercises(chapter_code=chapter_code)
    
    if not all_exercises:
        logger.warning("⚠️ Aucun exercice legacy trouvé")
        return stats
    
    logger.info(f"✅ {len(all_exercises)} chapitre(s) trouvé(s)")
    
    collection = db[EXERCISES_COLLECTION]
    
    # Créer l'index unique sur exercise_uid si nécessaire
    if not dry_run:
        try:
            await collection.create_index("exercise_uid", unique=True, background=True)
            logger.info("✅ Index exercise_uid créé/vérifié")
        except Exception as e:
            logger.warning(f"⚠️ Erreur création index (peut déjà exister): {e}")
    
    # Traiter chaque chapitre
    for normalized_code, exercises in all_exercises.items():
        # Le code est déjà normalisé par load_all_legacy_exercises
        logger.info(f"\n📚 Chapitre: {normalized_code} ({len(exercises)} exercices)")
        stats["chapters"][normalized_code] = {"inserted": 0, "skipped": 0, "errors": 0}
        
        for ex in exercises:
            # Valider l'exercice
            is_valid, error_msg = validate_exercise(ex)
            if not is_valid:
                logger.warning(f"  ⚠️ Exercice {ex.get('id', '?')} ignoré: {error_msg}")
                stats["errors"] += 1
                stats["chapters"][normalized_code]["errors"] += 1
                continue
            
            # Mettre à jour le chapter_code avec le code normalisé
            ex["chapter_code"] = normalized_code
            
            # Calculer l'UID
            exercise_uid = compute_exercise_uid(
                chapter_code=normalized_code,
                enonce_html=ex["enonce_html"],
                solution_html=ex["solution_html"],
                difficulty=ex.get("difficulty", "moyen")
            )
            
            # Vérifier si l'exercice existe déjà
            existing = await collection.find_one({"exercise_uid": exercise_uid})
            
            if existing:
                logger.info(f"  ⏭️  UID={exercise_uid[:8]}... déjà existant (skip)")
                stats["skipped"] += 1
                stats["chapters"][normalized_code]["skipped"] += 1
                continue
            
            # Préparer le document
            doc = prepare_exercise_document(ex, exercise_uid, locked=not unlock)
            
            if dry_run:
                logger.info(f"  🔍 [DRY-RUN] UID={exercise_uid[:8]}... titre='{doc['title'][:50]}'")
                stats["inserted"] += 1
                stats["chapters"][normalized_code]["inserted"] += 1
            else:
                try:
                    await collection.insert_one(doc)
                    logger.info(f"  ✅ UID={exercise_uid[:8]}... titre='{doc['title'][:50]}' inséré")
                    stats["inserted"] += 1
                    stats["chapters"][normalized_code]["inserted"] += 1
                except Exception as e:
                    logger.error(f"  ❌ Erreur insertion UID={exercise_uid[:8]}...: {e}")
                    stats["errors"] += 1
                    stats["chapters"][normalized_code]["errors"] += 1
    
    return stats


async def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description="Migre les exercices pseudo-statiques legacy vers MongoDB"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simule la migration sans écrire en DB"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Applique la migration (écrit en DB)"
    )
    parser.add_argument(
        "--chapter",
        type=str,
        help="Migre uniquement un chapitre (ex: 6E_GM07)"
    )
    parser.add_argument(
        "--unlock",
        action="store_true",
        help="Déverrouille les exercices migrés (locked=false)"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Affiche uniquement l'analyse préalable (rapport détaillé)"
    )
    
    args = parser.parse_args()
    
    # Validation des arguments
    if not args.dry_run and not args.apply:
        logger.error("❌ Vous devez spécifier --dry-run ou --apply")
        sys.exit(1)
    
    if args.dry_run and args.apply:
        logger.error("❌ Vous ne pouvez pas utiliser --dry-run et --apply en même temps")
        sys.exit(1)
    
    # Connexion MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME', 'le_maitre_mot_db')
    
    if not mongo_url:
        logger.error("❌ Variable d'environnement MONGO_URL manquante")
        sys.exit(1)
    
    logger.info(f"🔌 Connexion MongoDB: {db_name}")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Mode analyse uniquement
        if args.analyze:
            await analyze_legacy_exercises(db=db, chapter_code=args.chapter)
            return
        
        # Lancer la migration
        mode = "DRY-RUN" if args.dry_run else "APPLY"
        logger.info(f"\n🚀 Mode: {mode}")
        if args.chapter:
            logger.info(f"📌 Chapitre ciblé: {args.chapter}")
        if args.unlock:
            logger.info("🔓 Mode unlock activé (locked=false)")
        
        # Afficher l'analyse préalable avant la migration
        logger.info("\n📊 Analyse préalable...")
        await analyze_legacy_exercises(db=db, chapter_code=args.chapter)
        
        stats = await migrate_exercises(
            db=db,
            chapter_code=args.chapter,
            dry_run=args.dry_run,
            unlock=args.unlock
        )
        
        # Afficher les statistiques
        logger.info("\n" + "="*60)
        logger.info("📊 RÉSULTATS")
        logger.info("="*60)
        logger.info(f"✅ Insérés: {stats['inserted']}")
        logger.info(f"⏭️  Ignorés (déjà existants): {stats['skipped']}")
        logger.info(f"❌ Erreurs: {stats['errors']}")
        
        if stats["chapters"]:
            logger.info("\n📚 Par chapitre:")
            for chapter, chapter_stats in stats["chapters"].items():
                logger.info(f"  {chapter}: +{chapter_stats['inserted']} / ⏭️{chapter_stats['skipped']} / ❌{chapter_stats['errors']}")
        
        logger.info("\n✅ Migration terminée!")
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())

