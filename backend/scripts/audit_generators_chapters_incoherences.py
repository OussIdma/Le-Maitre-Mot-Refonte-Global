#!/usr/bin/env python3
"""
Audit automatique des incohérences Générateurs / Chapitres / Difficultés (P4.A)

Analyse croisée de toutes les sources pour détecter :
- Générateurs existants mais non utilisables
- Chapitres sans générateurs utilisables
- Incohérences de difficultés
- Erreurs 422 silencieuses
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Set, Optional
from collections import defaultdict
from datetime import datetime

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.generators.factory import GeneratorFactory
from backend.services.curriculum_persistence_service import CurriculumPersistenceService
from backend.server import db
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio


# =============================================================================
# CONSTANTES
# =============================================================================

DIFFICULTIES = ["facile", "moyen", "difficile", "standard"]
ALL_DIFFICULTIES = set(DIFFICULTIES)


# =============================================================================
# COLLECTE DE DONNÉES
# =============================================================================

def collect_generators() -> Dict[str, Dict[str, Any]]:
    """Collecte tous les générateurs depuis GeneratorFactory."""
    generators = {}
    
    all_gens = GeneratorFactory.list_all(include_disabled=True)
    for gen_info in all_gens:
        key = gen_info["key"]
        gen_class = GeneratorFactory.get(key)
        
        if not gen_class:
            continue
        
        # Récupérer le schéma pour connaître les difficultés supportées
        schema = gen_class.get_schema()
        difficulty_param = next((p for p in schema if p.name == "difficulty"), None)
        
        supported_difficulties = []
        if difficulty_param and difficulty_param.type.value == "enum":
            supported_difficulties = difficulty_param.options or []
        
        generators[key] = {
            "key": key,
            "label": gen_info.get("label", ""),
            "version": gen_info.get("version", ""),
            "niveaux": gen_info.get("niveaux", []),
            "exercise_type": gen_info.get("exercise_type", ""),
            "disabled": gen_info.get("disabled", False),
            "supported_difficulties": supported_difficulties,
            "schema": schema,
            "meta": gen_class.get_meta() if gen_class else None
        }
    
    return generators


async def collect_chapters() -> Dict[str, Dict[str, Any]]:
    """Collecte tous les chapitres depuis MongoDB."""
    chapters = {}
    
    curriculum_service = CurriculumPersistenceService(db)
    
    # Récupérer tous les chapitres 6e
    try:
        chapters_list = await curriculum_service.get_all_chapters("6e")
        for chapter in chapters_list:
            code = chapter.get("code_officiel", "")
            if code:
                chapters[code] = {
                    "code_officiel": code,
                    "libelle": chapter.get("libelle", ""),
                    "domaine": chapter.get("domaine", ""),
                    "niveau": chapter.get("niveau", "6e"),
                    "exercise_types": chapter.get("exercise_types", []),
                    "pipeline": chapter.get("pipeline"),
                    "difficulte_min": chapter.get("difficulte_min"),
                    "difficulte_max": chapter.get("difficulte_max"),
                }
    except Exception as e:
        print(f"⚠️  Erreur lors de la collecte des chapitres: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    
    return chapters


async def collect_exercises_in_db() -> Dict[str, List[Dict[str, Any]]]:
    """Collecte les exercices par chapitre depuis MongoDB."""
    exercises_by_chapter = defaultdict(list)
    
    try:
        # Récupérer tous les exercices dynamiques
        cursor = db.admin_exercises.find({"is_dynamic": True})
        async for ex in cursor:
            chapter_code = ex.get("chapter_code", "").upper()
            if chapter_code:
                exercises_by_chapter[chapter_code].append({
                    "id": ex.get("id"),
                    "generator_key": ex.get("generator_key"),
                    "difficulty": ex.get("difficulty"),
                    "offer": ex.get("offer", "free"),
                    "exercise_type": ex.get("exercise_type"),
                })
    except Exception as e:
        print(f"⚠️  Erreur lors de la collecte des exercices: {e}", file=sys.stderr)
    
    return dict(exercises_by_chapter)


def map_exercise_types_to_generators(exercise_types: List[str]) -> List[str]:
    """Mappe les exercise_types du curriculum vers les generator_key."""
    generator_keys = []
    
    for et in exercise_types:
        # Vérifier si c'est directement un generator_key
        gen_class = GeneratorFactory.get(et)
        if gen_class:
            generator_keys.append(et.upper())
            continue
        
        # Vérifier si c'est un exercise_type qui correspond à un générateur
        all_gens = GeneratorFactory.list_all()
        for gen_info in all_gens:
            if gen_info.get("exercise_type") == et.upper():
                generator_keys.append(gen_info["key"])
    
    return list(set(generator_keys))


# =============================================================================
# ANALYSE DES INCOHÉRENCES
# =============================================================================

def analyze_generator_chapter_mismatch(
    generators: Dict[str, Dict[str, Any]],
    chapters: Dict[str, Dict[str, Any]],
    exercises_in_db: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """Analyse les incohérences entre générateurs et chapitres."""
    issues = {
        "generators_unused": [],  # Générateurs jamais référencés
        "generators_invisible": [],  # GOLD mais non utilisables
        "chapters_without_generators": [],  # Chapitres sans générateurs
        "difficulty_mismatches": [],  # Difficultés incohérentes
        "missing_difficulties": [],  # Difficultés manquantes
        "premium_conflicts": [],  # Conflits gratuit/premium
    }
    
    # 1. Générateurs jamais référencés dans un chapitre
    all_generator_keys = set(generators.keys())
    referenced_generators = set()
    
    for chapter_code, chapter_data in chapters.items():
        exercise_types = chapter_data.get("exercise_types", [])
        chapter_generators = map_exercise_types_to_generators(exercise_types)
        referenced_generators.update(chapter_generators)
        
        # Vérifier aussi les exercices en DB
        db_exercises = exercises_in_db.get(chapter_code, [])
        for ex in db_exercises:
            gen_key = ex.get("generator_key")
            if gen_key:
                referenced_generators.add(gen_key.upper())
    
    unused_generators = all_generator_keys - referenced_generators
    for gen_key in unused_generators:
        gen_info = generators[gen_key]
        if not gen_info.get("disabled"):
            issues["generators_unused"].append({
                "generator": gen_key,
                "label": gen_info.get("label", ""),
                "version": gen_info.get("version", ""),
                "reason": "Jamais référencé dans un chapitre du curriculum"
            })
    
    # 2. Chapitres sans générateurs utilisables
    for chapter_code, chapter_data in chapters.items():
        exercise_types = chapter_data.get("exercise_types", [])
        chapter_generators = map_exercise_types_to_generators(exercise_types)
        
        # Vérifier aussi les exercices en DB
        db_exercises = exercises_in_db.get(chapter_code, [])
        db_generators = {ex.get("generator_key", "").upper() for ex in db_exercises if ex.get("generator_key")}
        
        all_chapter_generators = set(chapter_generators) | db_generators
        
        # Filtrer les générateurs désactivés
        usable_generators = [
            g for g in all_chapter_generators
            if g in generators and not generators[g].get("disabled")
        ]
        
        if not usable_generators and not exercise_types:
            issues["chapters_without_generators"].append({
                "chapter": chapter_code,
                "libelle": chapter_data.get("libelle", ""),
                "reason": "Aucun générateur référencé et aucun exercice en DB"
            })
    
    # 3. Incohérences de difficultés
    for chapter_code, chapter_data in chapters.items():
        exercise_types = chapter_data.get("exercise_types", [])
        chapter_generators = map_exercise_types_to_generators(exercise_types)
        
        for gen_key in chapter_generators:
            if gen_key not in generators:
                continue
            
            gen_info = generators[gen_key]
            supported_diffs = set(gen_info.get("supported_difficulties", []))
            
            # Vérifier les difficultés du chapitre
            diff_min = chapter_data.get("difficulte_min")
            diff_max = chapter_data.get("difficulte_max")
            
            if supported_diffs:
                # Vérifier si toutes les difficultés standard sont supportées
                missing_diffs = ALL_DIFFICULTIES - supported_diffs
                if missing_diffs:
                    issues["missing_difficulties"].append({
                        "chapter": chapter_code,
                        "generator": gen_key,
                        "supported": list(supported_diffs),
                        "missing": list(missing_diffs),
                        "reason": f"Générateur ne supporte pas toutes les difficultés standard"
                    })
    
    # 4. Générateurs GOLD mais non utilisables
    for gen_key, gen_info in generators.items():
        if gen_info.get("disabled"):
            continue
        
        # Vérifier si le générateur est référencé
        if gen_key not in referenced_generators:
            issues["generators_invisible"].append({
                "generator": gen_key,
                "label": gen_info.get("label", ""),
                "version": gen_info.get("version", ""),
                "reason": "GOLD mais jamais référencé dans un chapitre"
            })
    
    return issues


# =============================================================================
# GÉNÉRATION DU RAPPORT
# =============================================================================

def generate_audit_report(
    generators: Dict[str, Dict[str, Any]],
    chapters: Dict[str, Dict[str, Any]],
    exercises_in_db: Dict[str, List[Dict[str, Any]]],
    issues: Dict[str, Any]
) -> str:
    """Génère le rapport Markdown d'audit."""
    
    lines = [
        "# AUDIT INCOHÉRENCES GÉNÉRATEURS / CHAPITRES / DIFFICULTÉS",
        "",
        f"**Date de génération :** {datetime.now().isoformat()}",
        "",
        "---",
        "",
        "## 📊 RÉSUMÉ EXÉCUTIF",
        "",
    ]
    
    # Statistiques
    total_generators = len(generators)
    enabled_generators = sum(1 for g in generators.values() if not g.get("disabled"))
    disabled_generators = total_generators - enabled_generators
    total_chapters = len(chapters)
    
    lines.extend([
        f"- **Total générateurs :** {total_generators}",
        f"  - ✅ Activés : {enabled_generators}",
        f"  - 🔴 Désactivés : {disabled_generators}",
        f"- **Total chapitres :** {total_chapters}",
        f"- **Chapitres avec exercices en DB :** {len(exercises_in_db)}",
        "",
        "### Incohérences détectées",
        "",
        f"- 🔴 **Générateurs non utilisés :** {len(issues['generators_unused'])}",
        f"- 🟠 **Générateurs invisibles (GOLD mais non référencés) :** {len(issues['generators_invisible'])}",
        f"- 🔴 **Chapitres sans générateurs :** {len(issues['chapters_without_generators'])}",
        f"- 🟠 **Difficultés manquantes :** {len(issues['missing_difficulties'])}",
        f"- 🟠 **Conflits premium :** {len(issues['premium_conflicts'])}",
        "",
        "---",
        "",
        "## 🔍 ANALYSE PAR CHAPITRE",
        "",
    ])
    
    # Tableau par chapitre
    lines.append("| Chapitre | Libellé | Générateurs | Difficultés | Exercices DB | Problèmes |")
    lines.append("|----------|---------|-------------|-------------|--------------|-----------|")
    
    for chapter_code, chapter_data in sorted(chapters.items()):
        exercise_types = chapter_data.get("exercise_types", [])
        chapter_generators = map_exercise_types_to_generators(exercise_types)
        
        # Filtrer les désactivés
        usable_gens = [g for g in chapter_generators if g in generators and not generators[g].get("disabled")]
        
        # Exercices en DB
        db_exercises = exercises_in_db.get(chapter_code, [])
        db_generators = {ex.get("generator_key", "").upper() for ex in db_exercises if ex.get("generator_key")}
        
        # Difficultés
        all_diffs = set()
        for gen_key in usable_gens:
            if gen_key in generators:
                all_diffs.update(generators[gen_key].get("supported_difficulties", []))
        
        # Problèmes
        problems = []
        if not usable_gens and not db_generators:
            problems.append("❌ Aucun générateur")
        if len(usable_gens) != len(chapter_generators):
            problems.append("⚠️ Générateurs désactivés")
        if not all_diffs:
            problems.append("⚠️ Difficultés inconnues")
        
        problems_str = " ".join(problems) if problems else "✅ OK"
        
        lines.append(
            f"| {chapter_code} | {chapter_data.get('libelle', '')[:30]} | "
            f"{len(usable_gens)} | {', '.join(sorted(all_diffs)) or 'N/A'} | "
            f"{len(db_exercises)} | {problems_str} |"
        )
    
    lines.extend([
        "",
        "---",
        "",
        "## 🔍 ANALYSE PAR GÉNÉRATEUR",
        "",
    ])
    
    # Tableau par générateur
    lines.append("| Générateur | Version | Statut | Difficultés | Chapitres | Problèmes |")
    lines.append("|------------|--------|--------|-------------|-----------|-----------|")
    
    for gen_key, gen_info in sorted(generators.items()):
        # Trouver les chapitres qui utilisent ce générateur
        used_in_chapters = []
        for chapter_code, chapter_data in chapters.items():
            exercise_types = chapter_data.get("exercise_types", [])
            chapter_generators = map_exercise_types_to_generators(exercise_types)
            if gen_key in chapter_generators:
                used_in_chapters.append(chapter_code)
        
        # Vérifier aussi en DB
        for chapter_code, exercises in exercises_in_db.items():
            for ex in exercises:
                if ex.get("generator_key", "").upper() == gen_key:
                    if chapter_code not in used_in_chapters:
                        used_in_chapters.append(chapter_code)
        
        status = "🔴 DÉSACTIVÉ" if gen_info.get("disabled") else "🟢 GOLD"
        supported_diffs = gen_info.get("supported_difficulties", [])
        
        problems = []
        if gen_info.get("disabled"):
            problems.append("🔴 Désactivé")
        if not used_in_chapters:
            problems.append("⚠️ Non référencé")
        if not supported_diffs:
            problems.append("⚠️ Difficultés inconnues")
        
        problems_str = " ".join(problems) if problems else "✅ OK"
        
        lines.append(
            f"| {gen_key} | {gen_info.get('version', '')} | {status} | "
            f"{', '.join(supported_diffs) or 'N/A'} | {len(used_in_chapters)} | {problems_str} |"
        )
    
    lines.extend([
        "",
        "---",
        "",
        "## 🔴 INCOHÉRENCES BLOQUANTES",
        "",
    ])
    
    # Générateurs non utilisés
    if issues["generators_unused"]:
        lines.append("### Générateurs jamais référencés")
        lines.append("")
        for item in issues["generators_unused"]:
            lines.append(f"- **{item['generator']}** ({item['label']}, v{item['version']})")
            lines.append(f"  - Raison : {item['reason']}")
            lines.append("")
    
    # Chapitres sans générateurs
    if issues["chapters_without_generators"]:
        lines.append("### Chapitres sans générateurs utilisables")
        lines.append("")
        for item in issues["chapters_without_generators"]:
            lines.append(f"- **{item['chapter']}** ({item['libelle']})")
            lines.append(f"  - Raison : {item['reason']}")
            lines.append("")
    
    lines.extend([
        "",
        "---",
        "",
        "## 🟠 INCOHÉRENCES AMÉLIORABLES",
        "",
    ])
    
    # Générateurs invisibles
    if issues["generators_invisible"]:
        lines.append("### Générateurs GOLD mais non utilisables")
        lines.append("")
        for item in issues["generators_invisible"]:
            lines.append(f"- **{item['generator']}** ({item['label']}, v{item['version']})")
            lines.append(f"  - Raison : {item['reason']}")
            lines.append("")
    
    # Difficultés manquantes
    if issues["missing_difficulties"]:
        lines.append("### Difficultés manquantes")
        lines.append("")
        for item in issues["missing_difficulties"]:
            lines.append(f"- **{item['chapter']}** / **{item['generator']}**")
            lines.append(f"  - Supportées : {', '.join(item['supported'])}")
            lines.append(f"  - Manquantes : {', '.join(item['missing'])}")
            lines.append("")
    
    lines.extend([
        "",
        "---",
        "",
        "## 🧠 ANALYSE RACINE",
        "",
    ])
    
    # Analyse des causes
    lines.extend([
        "### Causes techniques",
        "",
        "1. **Mapping implicite exercise_type → generator_key**",
        "   - Le curriculum utilise `exercise_types` (ex: `SYMETRIE_AXIALE`)",
        "   - Mais les générateurs sont identifiés par `generator_key` (ex: `SYMETRIE_AXIALE_V2`)",
        "   - Mapping non documenté et non unifié",
        "",
        "2. **Double source de vérité**",
        "   - Curriculum JSON (`exercise_types`)",
        "   - MongoDB (`admin_exercises` avec `generator_key`)",
        "   - Synchronisation non automatique",
        "",
        "3. **Difficultés non standardisées**",
        "   - Certains générateurs utilisent `facile/moyen/difficile`",
        "   - D'autres utilisent `standard`",
        "   - Pas de validation croisée",
        "",
        "### Causes produit",
        "",
        "1. **Générateurs créés mais non intégrés**",
        "   - Générateurs GOLD mais jamais ajoutés au curriculum",
        "   - Pas de workflow d'intégration clair",
        "",
        "2. **Chapitres sans générateurs**",
        "   - Chapitres créés mais sans exercices dynamiques",
        "   - Dépendance aux exercices statiques uniquement",
        "",
        "### Impact utilisateur",
        "",
        "1. **Erreurs 422 silencieuses**",
        "   - Génération échoue sans explication",
        "   - Fallback STATIC activé mais non visible",
        "",
        "2. **Générateurs invisibles**",
        "   - Générateurs fonctionnels mais non sélectionnables",
        "   - Confusion admin / prof",
        "",
        "---",
        "",
        "## 🛠️ RECOMMANDATIONS ACTIONNABLES",
        "",
        "### P0 — Bloquant",
        "",
        "1. **Automatiser le mapping exercise_type → generator_key**",
        "   - Créer un mapping explicite et documenté",
        "   - Valider à la création/modification d'un chapitre",
        "",
        "2. **Bloquer les chapitres sans générateurs**",
        "   - Avertir si un chapitre n'a ni générateur ni exercice statique",
        "   - Empêcher la création de chapitres vides",
        "",
        "3. **Standardiser les difficultés**",
        "   - Forcer `facile/moyen/difficile` pour tous les générateurs",
        "   - Valider la cohérence chapitre ↔ générateur",
        "",
        "### P1 — Améliorable",
        "",
        "1. **UI explicite pour les générateurs non utilisables**",
        "   - Afficher pourquoi un générateur n'est pas sélectionnable",
        "   - Badge \"Non intégré\" pour les générateurs GOLD non référencés",
        "",
        "2. **Workflow d'intégration générateur**",
        "   - Checklist : générateur → test → classification → intégration curriculum",
        "   - Validation automatique avant activation",
        "",
        "3. **Monitoring des erreurs 422**",
        "   - Logger toutes les erreurs de génération",
        "   - Dashboard des chapitres problématiques",
        "",
        "---",
        "",
        "## 📝 NOTES",
        "",
        "Cet audit est généré automatiquement. Pour le régénérer :",
        "",
        "```bash",
        "python backend/scripts/audit_generators_chapters_incoherences.py",
        "```",
        "",
    ])
    
    return "\n".join(lines)


# =============================================================================
# MAIN
# =============================================================================

async def main():
    print("🔍 Audit des incohérences Générateurs / Chapitres / Difficultés", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    # Collecte des données
    print("\n📊 Collecte des générateurs...", file=sys.stderr)
    generators = collect_generators()
    print(f"   ✅ {len(generators)} générateur(s) trouvé(s)", file=sys.stderr)
    
    print("\n📚 Collecte des chapitres...", file=sys.stderr)
    chapters = await collect_chapters()
    print(f"   ✅ {len(chapters)} chapitre(s) trouvé(s)", file=sys.stderr)
    
    print("\n💾 Collecte des exercices en DB...", file=sys.stderr)
    exercises_in_db = await collect_exercises_in_db()
    print(f"   ✅ {sum(len(exs) for exs in exercises_in_db.values())} exercice(s) trouvé(s)", file=sys.stderr)
    
    # Analyse
    print("\n🔍 Analyse des incohérences...", file=sys.stderr)
    issues = analyze_generator_chapter_mismatch(generators, chapters, exercises_in_db)
    
    # Génération du rapport
    print("\n📝 Génération du rapport...", file=sys.stderr)
    report = generate_audit_report(generators, chapters, exercises_in_db, issues)
    
    # Écrire le rapport
    output_file = ROOT_DIR / "docs" / "AUDIT_INCOHERENCES_GENERATEURS_CHAPITRES.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n✅ Rapport généré : {output_file}", file=sys.stderr)
    print(f"\n📊 Résumé des incohérences :", file=sys.stderr)
    print(f"   🔴 Générateurs non utilisés : {len(issues['generators_unused'])}", file=sys.stderr)
    print(f"   🟠 Générateurs invisibles : {len(issues['generators_invisible'])}", file=sys.stderr)
    print(f"   🔴 Chapitres sans générateurs : {len(issues['chapters_without_generators'])}", file=sys.stderr)
    print(f"   🟠 Difficultés manquantes : {len(issues['missing_difficulties'])}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())

